#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$ROOT_DIR/.stackchan-xz.pid"
LOG_FILE="$ROOT_DIR/.stackchan-xz.log"
ERR_FILE="$ROOT_DIR/.stackchan-xz.err.log"

PUBLIC_URL="${PUBLIC_URL:-http://192.168.0.250:8080}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "StackChan XZ server already running: $(cat "$PID_FILE")"
  exit 0
fi

cd "$ROOT_DIR"
nohup python app.py --host "$HOST" --port "$PORT" --public-url "$PUBLIC_URL" >"$LOG_FILE" 2>"$ERR_FILE" &
echo $! > "$PID_FILE"
echo "StackChan XZ server started: $(cat "$PID_FILE")"
echo "Public URL: $PUBLIC_URL"
echo "Log: $LOG_FILE"
echo "Error log: $ERR_FILE"
