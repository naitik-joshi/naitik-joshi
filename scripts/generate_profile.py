#!/usr/bin/env python3
"""Generate theme-aware GitHub profile artwork from profile.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from profile_core import (  # noqa: E402,F401
    PROJECT_POSITIONS,
    THEMES,
    fetch_telemetry,
    load_config,
    safe,
)
from profile_renderer import generate, render_svg  # noqa: E402,F401


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "profile.json")
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    parser.add_argument("--offline", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    generate(arguments.config, arguments.output, offline=arguments.offline)
