#!/usr/bin/env python3
"""Register this documentation MCP server in the user-level Grok config.

After registration the server is available from any working directory.
Only the local user config is updated. No account names or clone paths
are written into the repository.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

SERVER_NAME = "autocad-sdk"
DEFAULT_SOURCE = "arxmgd"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def venv_python(root: Path) -> Path:
    windows = root / "venv" / "Scripts" / "python.exe"
    posix = root / "venv" / "bin" / "python"
    if windows.is_file():
        return windows
    if posix.is_file():
        return posix
    raise SystemExit(
        "No venv Python found. Create one first:\n"
        "  py -3.12 -m venv venv\n"
        "  venv/Scripts/python.exe -m pip install -r requirements-runtime.txt"
        if os.name == "nt"
        else "  python3.12 -m venv venv && venv/bin/python -m pip install -r requirements-runtime.txt"
    )


def user_config_path() -> Path:
    return Path.home() / ".grok" / "config.toml"


def as_toml_path(path: Path) -> str:
    return path.resolve().as_posix()


def strip_server_blocks(text: str, name: str) -> str:
    pattern = re.compile(
        rf"^\[mcp_servers\.{re.escape(name)}(?:\.[^\]]+)?\][^\n]*\n"
        rf"(?:(?!\[)[^\n]*\n)*",
        re.MULTILINE,
    )
    cleaned = pattern.sub("", text)
    return cleaned.rstrip() + ("\n\n" if cleaned.strip() else "")


def server_block(name: str, python: Path, root: Path, source: str) -> str:
    py = as_toml_path(python)
    script = as_toml_path(root / "server" / "mcp_server.py")
    root_s = as_toml_path(root)
    return (
        f"[mcp_servers.{name}]\n"
        f'command = "{py}"\n'
        f'args = ["-u", "{script}", "--source", "{source}"]\n'
        f"enabled = true\n"
        f"startup_timeout_sec = 180\n"
        f'env = {{ PYTHONPATH = "{root_s}", PYTHONUNBUFFERED = "1" }}\n'
    )


def register(name: str, source: str) -> Path:
    root = repo_root()
    python = venv_python(root)
    config = user_config_path()
    config.parent.mkdir(parents=True, exist_ok=True)
    existing = config.read_text(encoding="utf-8") if config.exists() else ""
    updated = strip_server_blocks(existing, name) + server_block(name, python, root, source)
    if not updated.endswith("\n"):
        updated += "\n"
    config.write_text(updated, encoding="utf-8")
    return config


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Register {SERVER_NAME} in the user Grok config so it works in every folder."
    )
    parser.add_argument("--name", default=SERVER_NAME, help="Grok MCP server id")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Default CHM source folder name")
    args = parser.parse_args()
    register(args.name, args.source)
    print(
        f"Registered {args.name} in the user Grok config. "
        "It is available in every folder. Start a new Grok session or refresh /mcps."
    )


if __name__ == "__main__":
    main()
