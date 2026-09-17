"""Exercise real TLS handshakes and credential checks without speech models."""
import asyncio
import importlib.util
from pathlib import Path
import ssl

import pytest
import websockets

from bridge import security

TRANSPORT = Path(__file__).resolve().parents[1] / 'custom-providers/stakia_transport.py'


def transport_module():
    spec = importlib.util.spec_from_file_location('stakia_transport', TRANSPORT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_identity_is_stable_and_rejects_changed_host(tmp_path):
    root = tmp_path / 'security'
    first = security.ensure_security(root, '192.168.1.20')
    assert len(first['device_token']) == 64
    assert security.ensure_security(root, '192.168.1.20') == first
    with pytest.raises(ValueError, match='address'):
        security.ensure_security(root, '192.168.1.21')


def test_incomplete_identity_does_not_silently_rotate(tmp_path):
    root = tmp_path / 'security'
    security.ensure_security(root, '192.168.1.20')
    (root / 'server-key.pem').unlink()
    with pytest.raises(ValueError, match='incomplete'):
        security.ensure_security(root, '192.168.1.20')


def test_tls_and_bearer_auth_accept_only_provisioned_client(tmp_path):
    root = tmp_path / 'security'
    identity = security.ensure_security(root, '192.168.1.20')
    transport = transport_module()
    config = {'server': {'tls': {'certfile': str(root / 'server-cert.pem'),
                                'keyfile': str(root / 'server-key.pem')},
                         'auth': {'enabled': True, 'token': identity['device_token']}}}
    context = transport.server_context(config)
    client = ssl.create_default_context(cafile=str(root / 'ca.pem'))
    accepted = []

    async def run():
        async def process(connection, request):
            if not transport.authorized(config, request.headers):
                return connection.respond(401, 'Unauthorized\n')
        async def echo(socket):
            accepted.append(True)
            await socket.send(await socket.recv())
        async with websockets.serve(echo, '127.0.0.1', 0, ssl=context,
                                    process_request=process) as server:
            port = server.sockets[0].getsockname()[1]
            url = f'wss://127.0.0.1:{port}/xiaozhi/v1/'
            for token in [None, 'incorrect']:
                headers = {} if token is None else {'Authorization': 'Bearer ' + token}
                with pytest.raises(websockets.exceptions.InvalidStatus) as failure:
                    async with websockets.connect(url, ssl=client,
                            server_hostname='192.168.1.20', additional_headers=headers):
                        pass
                assert failure.value.response.status_code == 401
            with pytest.raises(ssl.SSLCertVerificationError):
                async with websockets.connect(url, ssl=client,
                        server_hostname='192.168.1.99'):
                    pass
            with pytest.raises(ssl.SSLCertVerificationError):
                async with websockets.connect(url, ssl=ssl.create_default_context(),
                        server_hostname='192.168.1.20'):
                    pass
            async with websockets.connect(url, ssl=client, server_hostname='192.168.1.20',
                    additional_headers={'Authorization': 'Bearer ' + identity['device_token']}) as socket:
                await socket.send('hello stakia')
                assert await socket.recv() == 'hello stakia'
        assert accepted == [True]
    asyncio.run(run())


def test_missing_tls_or_disabled_auth_fails_closed(tmp_path):
    module = transport_module()
    with pytest.raises((KeyError, ValueError)):
        module.server_context({'server': {}})
    assert not module.authorized({'server': {'auth': {'enabled': False}}}, {})


def test_generated_config_and_replacements_keep_credentials_private(tmp_path):
    import os
    import stat
    from bridge.host_settings import HostSettings, write_server_config
    output = tmp_path / 'generated.yaml'
    output.write_text('old public file')
    if os.name != 'nt':
        output.chmod(0o644)
    write_server_config(HostSettings(), lan_host='192.168.1.20', path=output)
    for path in (output, tmp_path / '.config.yaml', tmp_path / 'security/identity.json'):
        if os.name != 'nt':
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
