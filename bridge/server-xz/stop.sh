#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$ROOT_DIR/.stackchan-xz.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "StackChan XZ server is not running"
  exit 0
fi

pid="$(cat "$PID_FILE")"
if kill -0 "$pid" 2>/dev/null; then
  kill "$pid"
  echo "StackChan XZ server stopped: $pid"
else
  echo "StackChan XZ server pid was stale"
fi

rm -f "$PID_FILE"
