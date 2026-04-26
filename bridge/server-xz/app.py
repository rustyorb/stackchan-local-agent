"""Minimal xiaozhi-protocol backend for StackChan fork firmware.

Two endpoints:

  GET/POST /xiaozhi/ota/
      Returns the xiaozhi bootstrap JSON. Crucially, we omit the
      `activation` block, so the device skips the cloud pairing flow
      (see firmware/xiaozhi-esp32/main/ota.cc line 476). We also point
      the `websocket.url` at ourselves, so the device keeps talking to
      us after boot instead of api.tenclass.net.

  WS /xiaozhi/v1/
      Implements the server side of the xiaozhi WebSocket protocol to
      the bare minimum needed to keep the device happy:
        - respond to the client "hello" with our own "hello"
        - keep the connection open, log anything that arrives
      No TTS/STT/LLM yet — this is the bridgehead for that work.

Usage:
  pip install aiohttp
  python server-xz/app.py --host 0.0.0.0 --port 8003 \
      --public-url http://192.168.0.250:8003
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web

log = logging.getLogger("xiaozhi-srv")

# Server audio params sent in the hello reply. Clients adapt to this.
SERVER_SAMPLE_RATE = 16000
SERVER_FRAME_DURATION_MS = 60
ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"
CONFIG_PATH = ROOT_DIR / "config.local.json"

DEFAULT_BRIDGE_CONFIG: dict[str, Any] = {
    "provider": "stub",
    "api_base_url": "",
    "model": "",
    "stt_model": "",
    "tts_model": "",
    "voice": "marin",
    "agent_name": "StackChan",
    "system_prompt": "You are a cute desktop AI assistant. Keep replies short, warm, and useful.",
    "api_key": "",
}


@dataclass
class DeviceSession:
    session_id: str
    reply_task: asyncio.Task[None] | None = None
    binary_frames: int = 0
    binary_bytes: int = 0
    listen_started_at: float | None = None
    last_text: str = ""
    seen_types: set[str] = field(default_factory=set)


def load_bridge_config() -> dict[str, Any]:
    config = dict(DEFAULT_BRIDGE_CONFIG)
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                for key in DEFAULT_BRIDGE_CONFIG:
                    if key in saved and isinstance(saved[key], str):
                        config[key] = saved[key]
        except Exception:
            log.exception("failed to read %s", CONFIG_PATH)
    return config


def save_bridge_config(updates: dict[str, Any]) -> dict[str, Any]:
    current = load_bridge_config()
    for key in DEFAULT_BRIDGE_CONFIG:
        if key == "api_key":
            continue
        value = updates.get(key)
        if isinstance(value, str):
            current[key] = value.strip() if key != "system_prompt" else value

    api_key = updates.get("api_key")
    if isinstance(api_key, str) and api_key:
        current["api_key"] = api_key.strip()
    if updates.get("clear_api_key") is True:
        current["api_key"] = ""

    CONFIG_PATH.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
    return current


def public_bridge_config(config: dict[str, Any]) -> dict[str, Any]:
    api_key = str(config.get("api_key") or "")
    public = {key: value for key, value in config.items() if key != "api_key"}
    public["api_key_present"] = bool(api_key)
    public["api_key_preview"] = f"...{api_key[-4:]}" if len(api_key) >= 4 else ""
    return public


def build_ota_response(public_url: str, protocol_version: int, firmware_version: str, websocket_path: str) -> dict[str, Any]:
    """Build the OTA bootstrap JSON the device expects.

    Deliberately no "activation" block -> device skips pairing.
    Deliberately no "mqtt" block -> device uses websocket path only.
    """
    return {
        "server_time": {
            "timestamp": int(time.time() * 1000),
            "timezone_offset": 0,
        },
        "firmware": {
            # Must match what the device is already running, otherwise the
            # device will mark has_new_version_ (our fork's
            # STACKCHAN_DISABLE_VENDOR_FIRMWARE_OTA define would suppress the
            # actual download, but echoing the same version keeps the log
            # clean).
            "version": firmware_version,
            "url": "",
        },
        "websocket": {
            # Strip the "http" scheme and replace with "ws" for the websocket
            # endpoint. Keep the trailing "/" — the device appends nothing.
            "url": public_url.replace("http://", "ws://").replace("https://", "wss://").rstrip("/") + websocket_path,
            "token": "dev",
            "version": protocol_version,
        },
    }


async def ota_handler(request: web.Request) -> web.Response:
    cfg: AppConfig = request.app["cfg"]
    body_preview = (await request.text())[:300] if request.can_read_body else ""
    device_id = request.headers.get("Device-Id", "?")
    client_id = request.headers.get("Client-Id", "?")
    log.info(
        "OTA %s from device=%s client=%s body=%s",
        request.method,
        device_id,
        client_id,
        body_preview,
    )
    websocket_path = "/v1/" if request.path.startswith("/v1/") else "/xiaozhi/v1/"
    payload = build_ota_response(cfg.public_url, cfg.protocol_version, cfg.firmware_version, websocket_path)
    return web.json_response(payload)


async def send_json(ws: web.WebSocketResponse, payload: dict[str, Any]) -> None:
    await ws.send_str(json.dumps(payload, separators=(",", ":")))
    log.info("WS text -> %s", payload)


async def send_stub_reply(ws: web.WebSocketResponse, session: DeviceSession, reason: str) -> None:
    # This intentionally does not synthesize audio yet. It drives the device UI
    # through normal XiaoZhi JSON messages so the local loop is observable.
    await asyncio.sleep(0.6)
    if ws.closed:
        return

    if session.binary_frames:
        user_text = f"Heard {session.binary_frames} audio frames locally."
    elif session.last_text:
        user_text = session.last_text
    else:
        user_text = "Wake word received."

    cfg = load_bridge_config()
    agent_name = cfg.get("agent_name") or "StackChan"
    provider = cfg.get("provider") or "stub"
    voice = cfg.get("voice") or "default"
    assistant_text = f"{agent_name} is connected to the local bridge. Provider is {provider}, voice is {voice}."

    await send_json(ws, {"session_id": session.session_id, "type": "stt", "text": user_text})
    await send_json(ws, {"session_id": session.session_id, "type": "llm", "emotion": "neutral"})
    await send_json(ws, {"session_id": session.session_id, "type": "tts", "state": "start"})
    await send_json(
        ws,
        {
            "session_id": session.session_id,
            "type": "tts",
            "state": "sentence_start",
            "text": assistant_text,
        },
    )
    await asyncio.sleep(1.2)
    if not ws.closed:
        await send_json(ws, {"session_id": session.session_id, "type": "tts", "state": "stop"})
        await asyncio.sleep(0.2)
        await ws.close()
    log.info(
        "local stub reply sent reason=%s frames=%d bytes=%d",
        reason,
        session.binary_frames,
        session.binary_bytes,
    )


async def index_handler(request: web.Request) -> web.FileResponse:
    return web.FileResponse(WEB_DIR / "index.html")


async def get_config_handler(request: web.Request) -> web.Response:
    return web.json_response(public_bridge_config(load_bridge_config()))


async def save_config_handler(request: web.Request) -> web.Response:
    try:
        updates = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "invalid json"}, status=400)
    if not isinstance(updates, dict):
        return web.json_response({"error": "expected object"}, status=400)
    config = save_bridge_config(updates)
    log.info(
        "config saved provider=%s base_url=%s model=%s voice=%s agent=%s key_present=%s",
        config.get("provider"),
        config.get("api_base_url"),
        config.get("model"),
        config.get("voice"),
        config.get("agent_name"),
        bool(config.get("api_key")),
    )
    return web.json_response(public_bridge_config(config))


def schedule_stub_reply(ws: web.WebSocketResponse, session: DeviceSession, reason: str, delay: float = 1.5) -> None:
    if session.reply_task and not session.reply_task.done():
        session.reply_task.cancel()

    async def runner() -> None:
        try:
            await asyncio.sleep(delay)
            await send_stub_reply(ws, session, reason)
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("stub reply failed")

    session.reply_task = asyncio.create_task(runner())


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    device_id = request.headers.get("Device-Id", "?")
    client_id = request.headers.get("Client-Id", "?")
    protocol_version = request.headers.get("Protocol-Version", "?")
    log.info("WS open device=%s client=%s proto=%s", device_id, client_id, protocol_version)

    session = DeviceSession(session_id=uuid.uuid4().hex[:16])

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            log.info("WS text <- %s", msg.data[:500])
            try:
                obj = json.loads(msg.data)
            except json.JSONDecodeError:
                log.warning("WS non-json text payload")
                continue
            msg_type = obj.get("type", "?")
            session.seen_types.add(str(msg_type))
            if msg_type == "hello":
                # Reply with server hello
                server_hello = {
                    "type": "hello",
                    "transport": "websocket",
                    "session_id": session.session_id,
                    "audio_params": {
                        "sample_rate": SERVER_SAMPLE_RATE,
                        "frame_duration": SERVER_FRAME_DURATION_MS,
                    },
                }
                await send_json(ws, server_hello)
                log.info("WS hello complete session=%s", session.session_id)
            elif msg_type == "listen":
                state = obj.get("state")
                text = obj.get("text")
                if isinstance(text, str):
                    session.last_text = text
                log.info("WS listen state=%s mode=%s text=%r", state, obj.get("mode"), text)
                if state == "start":
                    session.listen_started_at = time.monotonic()
                    session.binary_frames = 0
                    session.binary_bytes = 0
                    schedule_stub_reply(ws, session, "listen-start", delay=4.0)
                elif state == "detect":
                    schedule_stub_reply(ws, session, "wake-detect", delay=2.0)
                elif state == "stop":
                    schedule_stub_reply(ws, session, "listen-stop", delay=0.2)
            elif msg_type == "abort":
                log.info("WS abort reason=%s", obj.get("reason"))
                if session.reply_task and not session.reply_task.done():
                    session.reply_task.cancel()
            elif msg_type == "mcp":
                log.info("WS mcp <- %s", json.dumps(obj.get("payload"), ensure_ascii=False)[:500])
            else:
                log.info("WS unhandled type=%s", msg_type)
        elif msg.type == WSMsgType.BINARY:
            session.binary_frames += 1
            session.binary_bytes += len(msg.data)
            if session.binary_frames == 1 or session.binary_frames % 25 == 0:
                log.info("WS binary audio <- frames=%d bytes=%d", session.binary_frames, session.binary_bytes)
        elif msg.type == WSMsgType.ERROR:
            log.warning("WS error: %s", ws.exception())
            break

    if session.reply_task and not session.reply_task.done():
        session.reply_task.cancel()
    log.info(
        "WS close device=%s session=%s seen=%s frames=%d bytes=%d",
        device_id,
        session.session_id,
        sorted(session.seen_types),
        session.binary_frames,
        session.binary_bytes,
    )
    return ws


class AppConfig:
    def __init__(self, public_url: str, protocol_version: int, firmware_version: str) -> None:
        self.public_url = public_url
        self.protocol_version = protocol_version
        self.firmware_version = firmware_version


def build_app(cfg: AppConfig) -> web.Application:
    app = web.Application()
    app["cfg"] = cfg
    app.router.add_route("GET", "/", index_handler)
    app.router.add_route("GET", "/api/config", get_config_handler)
    app.router.add_route("POST", "/api/config", save_config_handler)
    app.router.add_static("/assets/", WEB_DIR, show_index=False)
    app.router.add_route("GET", "/xiaozhi/ota/", ota_handler)
    app.router.add_route("POST", "/xiaozhi/ota/", ota_handler)
    app.router.add_route("GET", "/xiaozhi/ota", ota_handler)
    app.router.add_route("POST", "/xiaozhi/ota", ota_handler)
    app.router.add_route("GET", "/xiaozhi/v1/ota", ota_handler)
    app.router.add_route("POST", "/xiaozhi/v1/ota", ota_handler)
    app.router.add_route("GET", "/v1/ota", ota_handler)
    app.router.add_route("POST", "/v1/ota", ota_handler)
    app.router.add_route("GET", "/xiaozhi/v1/", ws_handler)
    # Path trailing-slash tolerance:
    app.router.add_route("GET", "/xiaozhi/v1", ws_handler)
    app.router.add_route("GET", "/v1/", ws_handler)
    app.router.add_route("GET", "/v1", ws_handler)
    return app


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8003)
    p.add_argument(
        "--public-url",
        required=True,
        help="URL the device should use to reach this server (e.g. http://192.168.0.250:8003)",
    )
    p.add_argument("--protocol-version", type=int, default=3)
    p.add_argument("--firmware-version", default="1.2.6-dev")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    cfg = AppConfig(args.public_url, args.protocol_version, args.firmware_version)
    app = build_app(cfg)
    log.info("starting on %s:%d  public=%s", args.host, args.port, cfg.public_url)
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
