#!/usr/bin/env python3
"""Generate the profile and serve a local browser preview."""

from __future__ import annotations

import argparse
import contextlib
import http.server
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from profile_renderer import generate  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "profile.json")
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    generate(arguments.config, arguments.output, offline=arguments.offline)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", arguments.port), handler) as server:
        url = f"http://127.0.0.1:{arguments.port}/preview.html"
        print(f"[profile] preview ready at {url}")
        if not arguments.no_open:
            threading.Timer(0.4, webbrowser.open, args=(url,)).start()
        with contextlib.suppress(KeyboardInterrupt):
            server.serve_forever()


if __name__ == "__main__":
    main()
