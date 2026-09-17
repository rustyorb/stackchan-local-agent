"""Check pinned startup ordering without models, network listeners, or Docker.

Execute the actual upstream main and service constructors with external work
substituted. This specifically covers PR #2's missing-auth_key review finding;
it does not claim a full server startup or validate transport security.
"""
import ast
import asyncio
import os
import subprocess
import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from bridge.host_settings import HostSettings, render_server_config

PIN = '6afc54a17def47578a4b3efc4680873689d3168b'


def test_main_initializes_auth_before_websocket_and_http_handlers():
    source = os.getenv('STAKIA_SERVER_SOURCE')
    if not source:
        pytest.skip('Set STAKIA_SERVER_SOURCE to check pinned upstream startup')

    def read(path):
        return subprocess.check_output(
            ['git', '-C', source, 'show', f'{PIN}:main/xiaozhi-server/{path}'],
            text=True,
        )

    config = render_server_config(HostSettings(), lan_host='192.168.1.20')
    assert 'auth_key' not in config['server']
    logger = Mock()
    logger.bind.return_value = logger
    created = {}
    ns = {'asyncio': asyncio, 'uuid': uuid, 'os': os, 'TAG': 'test',
          'setup_logging': lambda *_: logger, 'logger': logger,
          'initialize_modules': lambda *_: {},
          'check_ffmpeg_installed': Mock(), 'load_config': AsyncMock(return_value=config),
          'monitor_stdin': AsyncMock(), 'wait_for_exit': AsyncMock(),
          'get_gc_manager': lambda **_: Mock(start=AsyncMock(), stop=AsyncMock()),
          'get_local_ip': lambda: '192.168.1.20',
          'validate_mcp_endpoint': lambda _: False}
    exec(compile(read('core/auth.py'), '<pinned-auth>', 'exec'), ns)

    class BaseHandler:
        def __init__(self, cfg):
            self.config = cfg

    ns['BaseHandler'] = BaseHandler
    ns['VisionHandler'] = Mock()  # No image-provider initialization in this check.

    def install_constructor(path, name):
        cls = next(n for n in ast.parse(read(path)).body
                   if isinstance(n, ast.ClassDef) and n.name == name)
        cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef)
                    and n.name == '__init__']
        exec(compile(ast.Module(body=[cls], type_ignores=[]), path, 'exec'), ns)
        actual = ns[name]

        def construct(cfg):
            key = cfg['server']['auth_key']
            assert len(key) == 32 and int(key, 16) >= 0
            instance = actual(cfg)
            instance.start = AsyncMock()
            created[name] = instance
            return instance

        ns[name] = construct

    install_constructor('core/websocket_server.py', 'WebSocketServer')
    install_constructor('core/api/ota_handler.py', 'OTAHandler')
    install_constructor('core/http_server.py', 'SimpleHttpServer')
    main = next(n for n in ast.parse(read('app.py')).body
                if isinstance(n, ast.AsyncFunctionDef) and n.name == 'main')
    exec(compile(ast.Module(body=[main], type_ignores=[]), '<pinned-main>', 'exec'), ns)
    asyncio.run(ns['main']())

    key = config['server']['auth_key']
    assert created['WebSocketServer'].auth.secret_key == key
    assert created['OTAHandler'].auth.secret_key == key
    assert created['SimpleHttpServer'].ota_handler is created['OTAHandler']
    assert created['WebSocketServer'].auth_enable is False
