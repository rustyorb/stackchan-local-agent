"""Exercise the real patched idle functions without speech models or a socket.

Set STAKIA_SERVER_SOURCE to a checkout of the pinned upstream revision.
Only the clock, logger, connection side effects, and sleep are substituted.
"""
import ast
import asyncio
from pathlib import Path
import os
import subprocess
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

PIN = '6afc54a17def47578a4b3efc4680873689d3168b'

@pytest.fixture(scope='module')
def patched_functions(tmp_path_factory):
    source = os.getenv('STAKIA_SERVER_SOURCE')
    if not source:
        pytest.skip('Set STAKIA_SERVER_SOURCE to test the actual pinned upstream patch')
    source = Path(source)
    dest = tmp_path_factory.mktemp('pinned-server')
    files = ['main/xiaozhi-server/config/config_loader.py',
             'main/xiaozhi-server/core/connection.py',
             'main/xiaozhi-server/core/handle/receiveAudioHandle.py']
    for name in files:
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        original = subprocess.check_output(['git', '-C', str(source), 'show', f'{PIN}:{name}'])
        target.write_bytes(original)
    patch = Path(__file__).resolve().parents[1] / 'custom-providers/xiaozhi-patches/never-idle.patch'
    subprocess.run(['git', 'apply', str(patch)], cwd=dest, check=True)
    functions = {}
    for name in files:
        module = ast.parse((dest / name).read_text())
        for node in ast.walk(module):
            if isinstance(node, ast.AsyncFunctionDef) and node.name in ('no_voice_close_connect', '_check_timeout'):
                functions[node.name] = node
    assert len(functions) == 2
    return functions


def connection(idle, farewell=False):
    logger = SimpleNamespace(info=lambda *_: None, error=lambda *_: None)
    logger.bind = lambda **_: logger
    return SimpleNamespace(config={'close_connection_no_voice_time': idle, 'end_prompt': {'enable': farewell, 'prompt': 'Bye'}},
        last_activity_time=1000.0, first_activity_time=1000.0, need_bind=False,
        close_after_chat=False, client_abort=False, logger=logger, close=AsyncMock(),
        stop_event=threading.Event(), websocket=object(), timeout_seconds=None if idle is None else idle + 60)


def load_function(node, conn):
    async def one_tick(_):
        conn.stop_event.set()
    ns = {'time': SimpleNamespace(time=lambda: 3600.0), 'TAG': 'test',
          'asyncio': SimpleNamespace(sleep=one_tick), 'startToChat': AsyncMock()}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<patched-upstream>', 'exec'), ns)
    return ns[node.name], ns


@pytest.mark.parametrize('idle', [None, 0])
def test_actual_audio_handler_does_not_exit_after_hour_of_silence(patched_functions, idle):
    conn = connection(idle)
    fn, ns = load_function(patched_functions['no_voice_close_connect'], conn)
    asyncio.run(fn(conn, False))
    assert not conn.close_after_chat
    conn.close.assert_not_called()
    ns['startToChat'].assert_not_called()


@pytest.mark.parametrize('farewell', [False, True])
def test_actual_audio_handler_honors_finite_timeout_and_farewell(patched_functions, farewell):
    conn = connection(300, farewell)
    fn, ns = load_function(patched_functions['no_voice_close_connect'], conn)
    asyncio.run(fn(conn, False))
    assert conn.close_after_chat
    if farewell:
        ns['startToChat'].assert_awaited_once_with(conn, 'Bye')
        conn.close.assert_not_called()
    else:
        conn.close.assert_awaited_once()
        ns['startToChat'].assert_not_called()


@pytest.mark.parametrize('idle,closes', [(None, False), (300, True)])
def test_actual_watchdog_preserves_never_and_finite_behavior(patched_functions, idle, closes):
    conn = connection(idle)
    fn, _ = load_function(patched_functions['_check_timeout'], conn)
    asyncio.run(fn(conn))
    assert conn.close.await_count == int(closes)
