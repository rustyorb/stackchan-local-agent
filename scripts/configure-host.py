#!/usr/bin/env python3
"""Render runtime Xiaozhi YAML without leaving ${SECRET} literals."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.host_settings import SettingsStore, validate_local_assets, write_server_config


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and name.replace("_", "a").isalnum():
            os.environ.setdefault(name, value)


def main():
    root = ROOT
    load_env_file(root / ".env.local")
    parser = argparse.ArgumentParser()
    parser.add_argument("--lan-host", default=os.getenv("STAKIA_LAN_HOST", ""))
    parser.add_argument("--settings", type=Path, default=root / "data/host-settings.json")
    parser.add_argument("--output", type=Path, default=root / "data/xiaozhi.generated.yaml")
    parser.add_argument("--model-root", type=Path, default=root / "data/models")
    args = parser.parse_args()
    validate_local_assets(args.model_root)
    write_server_config(SettingsStore(args.settings).load(), lan_host=args.lan_host, path=args.output)
    print(f"Rendered {args.output} (secrets redacted)")


if __name__ == "__main__":
    main()
