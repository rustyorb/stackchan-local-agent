"""Create and reuse private local TLS material; never contact a certificate service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import ipaddress
import json
import os
from pathlib import Path
import secrets
import ssl
import tempfile


def private_ipv4(host: str) -> str:
    address = ipaddress.IPv4Address(host)
    if not any(address in ipaddress.ip_network(net) for net in
               ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
        raise ValueError('Use the PC private LAN IPv4 address')
    return str(address)


def load_security(root: Path, host: str) -> dict:
    host = private_ipv4(host)
    required = ('identity.json', 'ca.pem', 'server-cert.pem', 'server-key.pem')
    if any(not (root / name).is_file() for name in required):
        raise ValueError('Local security identity is incomplete; restore its files or explicitly reprovision and rebuild firmware')
    identity = json.loads((root / 'identity.json').read_text(encoding='utf-8'))
    if identity.get('host') != host:
        raise ValueError('PC address differs from the provisioned identity; explicitly reprovision and rebuild firmware')
    token = identity.get('device_token', '')
    if len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
        raise ValueError('Invalid local device credential')
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(root / 'server-cert.pem', root / 'server-key.pem')
    return identity


def ensure_security(root: Path, host: str) -> dict:
    root = Path(root)
    host = private_ipv4(host)
    if root.exists():
        return load_security(root, host)
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    now = datetime.now(timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Stakia local CA ' + secrets.token_hex(8))])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=825))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), critical=True)
          .sign(ca_key, hashes.SHA256()))
    server = (x509.CertificateBuilder()
              .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)]))
              .issuer_name(ca_name).public_key(server_key.public_key())
              .serial_number(x509.random_serial_number())
              .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=825))
              # DNS form also supports embedded TLS stacks matching numeric hosts as names.
              .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(host)), x509.DNSName(host)]), critical=False)
              .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
              .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
              .add_extension(x509.KeyUsage(True, False, True, False, False, False, False, False, False), critical=True)
              .sign(ca_key, hashes.SHA256()))
    identity = {'host': host, 'device_token': secrets.token_hex(32)}
    root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.stakia-security-', dir=root.parent) as tmp:
        stage = Path(tmp) / 'identity'
        stage.mkdir(mode=0o700)
        files = {'ca.pem': ca.public_bytes(serialization.Encoding.PEM),
                 'server-cert.pem': server.public_bytes(serialization.Encoding.PEM),
                 'server-key.pem': server_key.private_bytes(serialization.Encoding.PEM,
                     serialization.PrivateFormat.PKCS8, serialization.NoEncryption()),
                 'identity.json': (json.dumps(identity, indent=2) + '\n').encode()}
        for name, content in files.items():
            with (stage / name).open('xb') as output:
                os.chmod(stage / name, 0o600)
                output.write(content)
        stage.rename(root)
    # CA signing key is deliberately never written to disk.
    return load_security(root, host)


def write_private_text(path: Path, content: str) -> None:
    """Atomically replace a secret-bearing file with a private temporary file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
            output.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
