"""Use the patched production listener and handshake on a real TLS socket.

Only speech/model work and logging are substituted. TLS, WebSocket protocol,
upstream routing, credential checks, and the service's start() are executed.
"""
import ast
import asyncio
from contextlib import asynccontextmanager
import importlib.util
import os
from pathlib import Path
import ssl
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import websockets

from bridge.host_settings import HostSettings, render_server_config
from bridge.security import ensure_security

PIN = '6afc54a17def47578a4b3efc4680873689d3168b'
ROOT = Path(__file__).resolve().parents[1]


def test_patched_listener_authenticates_before_voice_handler(tmp_path):
    source = os.getenv('STAKIA_SERVER_SOURCE')
    if not source:
        pytest.skip('Set STAKIA_SERVER_SOURCE for real upstream TLS integration')
    path = 'main/xiaozhi-server/core/websocket_server.py'
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_bytes(subprocess.check_output(['git', '-C', source, 'show', f'{PIN}:{path}']))
    connection_path = 'main/xiaozhi-server/core/connection.py'
    (tmp_path / connection_path).write_bytes(subprocess.check_output(
        ['git', '-C', source, 'show', f'{PIN}:{connection_path}']))
    subprocess.run(['git', 'apply', str(ROOT / 'custom-providers/xiaozhi-patches/secure-transport.patch')],
                   cwd=tmp_path, check=True)
    spec = importlib.util.spec_from_file_location('stakia_transport', ROOT / 'custom-providers/stakia_transport.py')
    transport = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transport)
    security = tmp_path / 'security'
    identity = ensure_security(security, '192.168.1.20')
    config = render_server_config(HostSettings(), lan_host='192.168.1.20', device_token=identity['device_token'])
    config['server'].update(ip='127.0.0.1', port=0, auth_key='initialized-by-main',
                           tls={'certfile': str(security / 'server-cert.pem'),
                                'keyfile': str(security / 'server-key.pem')})
    called = []
    class VoiceHandler:
        def __init__(self, *_):
            called.append(True)
        async def handle_connection(self, socket):
            await socket.send(await socket.recv())
    logger = Mock()
    logger.bind.return_value = logger

    async def run():
        ready = asyncio.get_running_loop().create_future()
        @asynccontextmanager
        async def serve(*args, **kwargs):
            async with websockets.serve(*args, **kwargs) as instance:
                ready.set_result(instance)
                yield instance
        ns = {'asyncio': asyncio, 'websockets': SimpleNamespace(serve=serve, ServerConnection=websockets.ServerConnection),
              'setup_logging': lambda *_: logger, 'initialize_modules': lambda *_: {},
              'ConnectionHandler': VoiceHandler, 'TAG': 'test',
              'authorized': transport.authorized, 'server_context': transport.server_context}
        auth_source = subprocess.check_output(['git', '-C', source, 'show', f'{PIN}:main/xiaozhi-server/core/auth.py'], text=True)
        exec(compile(auth_source, '<pinned-auth>', 'exec'), ns)
        cls = next(n for n in ast.parse(target.read_text()).body
                   if isinstance(n, ast.ClassDef) and n.name == 'WebSocketServer')
        exec(compile(ast.Module(body=[cls], type_ignores=[]), '<patched-listener>', 'exec'), ns)
        service = ns['WebSocketServer'](config)
        task = asyncio.create_task(service.start())
        try:
            listener = await asyncio.wait_for(ready, 5)
            port = listener.sockets[0].getsockname()[1]
            client = ssl.create_default_context(cafile=str(security / 'ca.pem'))
            url = f'wss://127.0.0.1:{port}/xiaozhi/v1/'
            for token in [None, 'wrong', identity['device_token']]:
                headers = {'Device-Id': 'test-device', 'Client-Id': 'test-client'}
                if token is not None:
                    headers['Authorization'] = 'Bearer ' + token
                if token != identity['device_token']:
                    with pytest.raises(websockets.exceptions.InvalidStatus) as exc:
                        async with websockets.connect(url, ssl=client, server_hostname='192.168.1.20',
                                                      additional_headers=headers):
                            pass
                    assert exc.value.response.status_code == 401
                    assert not called
                else:
                    async with websockets.connect(url, ssl=client, server_hostname='192.168.1.20',
                                                  additional_headers=headers) as socket:
                        await socket.send('authorized audio path')
                        assert await socket.recv() == 'authorized audio path'
            assert called == [True]
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
    asyncio.run(run())


def test_connection_logging_does_not_include_credentials(tmp_path):
    source = os.getenv('STAKIA_SERVER_SOURCE')
    if not source:
        pytest.skip('Set STAKIA_SERVER_SOURCE for pinned connection logging')
    prefix = 'main/xiaozhi-server/core/'
    for filename in ('connection.py', 'websocket_server.py'):
        path = tmp_path / prefix / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(['git', '-C', source, 'show', f'{PIN}:{prefix}{filename}']))
    subprocess.run(['git', 'apply', str(ROOT / 'custom-providers/xiaozhi-patches/secure-transport.patch')],
                   cwd=tmp_path, check=True)
    tree = ast.parse((tmp_path / prefix / 'connection.py').read_text())
    method = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == 'handle_connection')
    # Execute the actual initial block through the connection log, before audio tasks.
    statements = method.body[0].body
    end = next(i for i, n in enumerate(statements) if isinstance(n, ast.Assign)
               and isinstance(n.targets[0], ast.Attribute) and n.targets[0].attr == 'device_id')
    method.body = statements[:end]
    logger = Mock(); logger.bind.return_value = logger
    self = SimpleNamespace(logger=logger)
    ws = SimpleNamespace(request=SimpleNamespace(headers={'authorization': 'Bearer secret-robot-token'}),
                         remote_address=('192.168.1.30', 1234))
    ns = {'asyncio': asyncio, 'websockets': websockets, 'TAG': 'test'}
    exec(compile(ast.Module(body=[method], type_ignores=[]), '<patched-connection-log>', 'exec'), ns)
    asyncio.run(ns['handle_connection'](self, ws))
    logged = ' '.join(str(call) for call in logger.info.call_args_list)
    assert '192.168.1.30' in logged
    assert 'secret-robot-token' not in logged
    assert 'authorization' not in logged.lower()
