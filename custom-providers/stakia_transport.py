"""Fail-closed TLS and robot credential validation for the standalone server."""
import hmac
import ssl


def authorized(config, headers):
    auth = config['server'].get('auth', {})
    token = auth.get('token', '')
    if auth.get('enabled') is not True or len(token) != 64:
        return False
    try:
        provided = headers.get('Authorization', '')
        return hmac.compare_digest(provided.encode('utf-8'), ('Bearer ' + token).encode('ascii'))
    except (ValueError, UnicodeError):
        # Multiple authorization fields and malformed credentials never authorize.
        return False


def server_context(config):
    server = config['server']
    auth = server.get('auth', {})
    if auth.get('enabled') is not True or len(auth.get('token', '')) != 64:
        raise ValueError('A provisioned robot credential is required')
    tls = server['tls']
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(tls['certfile'], tls['keyfile'])
    return context
