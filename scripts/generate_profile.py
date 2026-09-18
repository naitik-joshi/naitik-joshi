#!/usr/bin/env python3
"""Generate the Kathmandu Network Node profile SVG assets."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]

THEMES = {
    "dark": {
        "bg": "#071419", "panel": "#0D2026", "panel_alt": "#102A31",
        "border": "#28505A", "mountain_far": "#102A32",
        "mountain_near": "#15343A", "city": "#091217",
        "window": "#F0B84B", "mint": "#72E2C4", "cyan": "#59C3DA",
        "amber": "#F0B84B", "red": "#DB5A57", "text": "#EAF3F2",
        "muted": "#8DA9AD",
    },
    "light": {
        "bg": "#EDF4F1", "panel": "#F8FBF9", "panel_alt": "#E1ECE8",
        "border": "#91AAA7", "mountain_far": "#D5E3DF",
        "mountain_near": "#C3D6D1", "city": "#B1C6C1",
        "window": "#9B6200", "mint": "#087D70", "cyan": "#0B748B",
        "amber": "#9B6200", "red": "#B33E3B", "text": "#142426",
        "muted": "#536B6D",
    },
}

PROJECT_POSITIONS = {
    "northwest": (372, 206),
    "southwest": (372, 410),
    "northeast": (828, 206),
    "southeast": (828, 410),
}


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if len(config.get("projects", [])) != 4:
        raise ValueError("Phase 1 layout requires exactly four projects")
    positions = {project["position"] for project in config["projects"]}
    if positions != set(PROJECT_POSITIONS):
        raise ValueError("Each project position must be used exactly once")
    return config


def github_json(url: str, token: str | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "naitik-profile-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.URLError:
        # Some macOS Python installs lack a usable CA bundle. The system curl
        # trust store is a dependency-free fallback for these public endpoints.
        result = subprocess.run(
            [
                "curl", "--fail", "--silent", "--show-error",
                "--max-time", "15",
                "--header", f"Accept: {headers['Accept']}",
                "--header", f"User-Agent: {headers['User-Agent']}",
                "--header", f"X-GitHub-Api-Version: {headers['X-GitHub-Api-Version']}",
                url,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)


def fetch_telemetry(config: dict[str, Any], offline: bool = False) -> dict[str, Any]:
    fallback = dict(config["fallback_telemetry"])
    if offline:
        return fallback

    username = config["username"]
    token = os.environ.get("GITHUB_TOKEN")
    try:
        user = github_json(f"https://api.github.com/users/{username}", token)
        repos = github_json(
            f"https://api.github.com/users/{username}/repos"
            "?per_page=100&sort=updated&type=owner",
            token,
        )
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        print(f"[profile] GitHub telemetry unavailable: {exc}", file=sys.stderr)
        return fallback

    owned = [repo for repo in repos if not repo.get("fork")]
    latest = owned[0] if owned else {}
    return {
        "public_repos": user.get("public_repos", fallback["public_repos"]),
        "followers": user.get("followers", fallback["followers"]),
        "stars": sum(int(repo.get("stargazers_count", 0)) for repo in owned),
        "latest_repo": latest.get("name", fallback["latest_repo"]),
        "latest_repo_date": str(
            latest.get("pushed_at", fallback["latest_repo_date"])
        )[:10],
    }


def safe(value: Any) -> str:
    return escape(str(value), quote=True)


def svg_text(
    x: int, y: int, value: Any, css_class: str, anchor: str = "start"
) -> str:
    return (
        f'<text x="{x}" y="{y}" class="{css_class}" '
        f'text-anchor="{anchor}">{safe(value)}</text>'
    )


def panel(x: int, y: int, width: int, height: int, label: str) -> str:
    return "\n".join([
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="4" class="panel"/>',
        svg_text(x + 16, y + 25, label, "label"),
        f'<line x1="{x + 14}" y1="{y + 35}" x2="{x + width - 14}" y2="{y + 35}" class="rule"/>',
    ])


def render_mountains() -> str:
    return """
<path class="mountain-far" d="M18 526 L84 452 L124 486 L183 414 L237 475 L304 397 L368 474 L432 425 L493 481 L553 401 L615 472 L680 421 L744 482 L814 398 L873 463 L934 420 L998 478 L1063 408 L1122 470 L1182 426 L1182 632 L18 632 Z"/>
<path class="mountain-near" d="M18 565 L96 504 L148 547 L220 472 L286 550 L351 502 L425 558 L509 482 L582 552 L653 509 L726 561 L805 481 L877 547 L945 500 L1014 558 L1090 492 L1182 551 L1182 632 L18 632 Z"/>
""".strip()


def render_skyline() -> str:
    buildings = [
        (22, 574, 54, 58), (82, 548, 45, 84), (134, 585, 64, 47),
        (205, 556, 52, 76), (264, 579, 67, 53), (338, 540, 54, 92),
        (399, 568, 70, 64), (477, 550, 42, 82), (527, 581, 58, 51),
        (594, 552, 62, 80), (664, 574, 70, 58), (742, 542, 48, 90),
        (798, 568, 69, 64), (875, 551, 58, 81), (941, 580, 65, 52),
        (1014, 548, 51, 84), (1072, 575, 52, 57), (1131, 557, 47, 75),
    ]
    parts = ['<g class="city">']
    for index, (x, y, width, height) in enumerate(buildings):
        parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}"/>'
        )
        if index % 3 != 1:
            parts.append(
                f'<rect x="{x + 10}" y="{y + 14}" width="5" height="5" class="window"/>'
            )
            parts.append(
                f'<rect x="{x + 26}" y="{y + 28}" width="5" height="5" class="window"/>'
            )
    parts.extend([
        '<rect x="173" y="526" width="88" height="106"/>',
        '<polygon points="160,546 217,510 274,546"/>',
        '<polygon points="174,520 217,490 260,520"/>',
        '<line x1="217" y1="490" x2="217" y2="472" class="city-line"/>',
        '<rect x="914" y="576" width="124" height="56"/>',
        '<path d="M930 576 Q976 515 1022 576 Z"/>',
        '<rect x="972" y="526" width="8" height="40"/>',
        '<circle cx="976" cy="518" r="5" class="beacon-static"/>',
        '</g>',
    ])
    return "\n".join(parts)


def render_project_node(project: dict[str, Any]) -> str:
    x, y = PROJECT_POSITIONS[project["position"]]
    accent = project.get("accent", "cyan")
    box_x, box_y = x - 92, y - 42
    return "\n".join([
        f'<g class="project-node" aria-label="{safe(project["name"])}">',
        f'<rect x="{box_x}" y="{box_y}" width="184" height="84" rx="4" class="node-box {accent}-stroke"/>',
        f'<rect x="{box_x + 14}" y="{box_y + 16}" width="28" height="34" rx="2" class="node-machine"/>',
        f'<line x1="{box_x + 20}" y1="{box_y + 25}" x2="{box_x + 36}" y2="{box_y + 25}" class="{accent}-stroke"/>',
        f'<line x1="{box_x + 20}" y1="{box_y + 34}" x2="{box_x + 36}" y2="{box_y + 34}" class="{accent}-stroke"/>',
        f'<circle cx="{box_x + 22}" cy="{box_y + 43}" r="2" class="{accent}-fill"/>',
        svg_text(box_x + 52, box_y + 26, project["name"], "node-title"),
        svg_text(box_x + 52, box_y + 47, project["status"], f"node-status {accent}-text"),
        svg_text(box_x + 14, box_y + 70, project["stack"], "node-stack"),
        '</g>',
    ])


def render_connections(projects: list[dict[str, Any]]) -> str:
    parts = ['<g class="routes">']
    for index, project in enumerate(projects, start=1):
        x, y = PROJECT_POSITIONS[project["position"]]
        mid_x = int((600 + x) / 2)
        path = f"M 600 330 C {mid_x} 330, {mid_x} {y}, {x} {y}"
        parts.append(f'<path d="{path}" class="route"/>')
        parts.append(f'<circle r="4" class="packet packet-{index}"/>')
    parts.append('</g>')
    return "\n".join(parts)


def render_central_node() -> str:
    return "\n".join([
        '<g class="central-node">',
        '<circle cx="600" cy="330" r="72" class="node-halo"/>',
        '<circle cx="600" cy="330" r="55" class="node-core"/>',
        '<rect x="573" y="304" width="54" height="48" rx="3" class="tower"/>',
        '<line x1="585" y1="317" x2="615" y2="317" class="mint-stroke"/>',
        '<line x1="585" y1="329" x2="615" y2="329" class="cyan-stroke"/>',
        '<line x1="585" y1="341" x2="605" y2="341" class="amber-stroke"/>',
        '<line x1="600" y1="304" x2="600" y2="275" class="tower-line"/>',
        '<circle cx="600" cy="270" r="5" class="beacon pulse"/>',
        '<circle cx="600" cy="270" r="12" class="beacon-ring pulse-ring"/>',
        svg_text(600, 372, "KTM-NP-0545", "central-title", "middle"),
        svg_text(600, 391, "NETWORK NODE", "central-subtitle", "middle"),
        '</g>',
    ])


def render_style(colors: dict[str, str], projects: list[dict[str, Any]]) -> str:
    packet_keyframes = []
    for index, project in enumerate(projects, start=1):
        x, y = PROJECT_POSITIONS[project["position"]]
        packet_keyframes.append(
            f"@keyframes packet{index} {{0%{{transform:translate(600px,330px);opacity:0}}"
            f"12%{{opacity:.95}}88%{{opacity:.95}}"
            f"100%{{transform:translate({x}px,{y}px);opacity:0}}}}"
        )
    return f"""
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.outer{{fill:{colors['bg']};stroke:{colors['border']}}}
.panel{{fill:{colors['panel']};stroke:{colors['border']}}}
.rule{{stroke:{colors['border']};stroke-width:1}}
.label{{fill:{colors['mint']};font-size:13px;font-weight:700;letter-spacing:1px}}
.identity{{fill:{colors['text']};font-size:31px;font-weight:800}}
.identity-role{{fill:{colors['muted']};font-size:14px}}
.header-signal{{fill:{colors['text']};font-size:13px;font-weight:700}}
.header-muted{{fill:{colors['muted']};font-size:12px}}
.body{{fill:{colors['text']};font-size:14px}}
.body-strong{{fill:{colors['text']};font-size:16px;font-weight:700}}
.body-muted{{fill:{colors['muted']};font-size:12px}}
.signal{{fill:{colors['mint']};font-size:12px;font-weight:700}}
.route{{fill:none;stroke:{colors['cyan']};stroke-width:1.5;stroke-dasharray:5 7;opacity:.75}}
.packet{{fill:{colors['mint']};filter:url(#glow)}}
.packet-1{{animation:packet1 5.2s linear infinite}}.packet-2{{animation:packet2 6.1s linear .8s infinite}}
.packet-3{{animation:packet3 5.7s linear 1.4s infinite}}.packet-4{{animation:packet4 6.4s linear 2.1s infinite}}
{''.join(packet_keyframes)}
.node-box{{fill:{colors['panel']};stroke-width:1.5}}.node-machine{{fill:{colors['panel_alt']};stroke:{colors['border']}}}
.node-title{{fill:{colors['text']};font-size:15px;font-weight:700}}.node-status{{font-size:10px;font-weight:700}}
.node-stack{{fill:{colors['muted']};font-size:10px}}
.mint-stroke{{stroke:{colors['mint']};fill:none}}.cyan-stroke{{stroke:{colors['cyan']};fill:none}}.amber-stroke{{stroke:{colors['amber']};fill:none}}
.mint-fill{{fill:{colors['mint']}}}.cyan-fill{{fill:{colors['cyan']}}}.amber-fill{{fill:{colors['amber']}}}
.mint-text{{fill:{colors['mint']}}}.cyan-text{{fill:{colors['cyan']}}}.amber-text{{fill:{colors['amber']}}}
.node-halo{{fill:{colors['panel']};stroke:{colors['cyan']};opacity:.9}}.node-core{{fill:{colors['panel_alt']};stroke:{colors['mint']};stroke-width:2}}
.tower{{fill:{colors['bg']};stroke:{colors['border']}}}.tower-line{{stroke:{colors['amber']};stroke-width:2}}
.beacon{{fill:{colors['red']}}}.beacon-ring{{fill:none;stroke:{colors['red']}}}
.central-title{{fill:{colors['cyan']};font-size:15px;font-weight:800}}.central-subtitle{{fill:{colors['muted']};font-size:10px;letter-spacing:1px}}
.mountain-far{{fill:{colors['mountain_far']}}}.mountain-near{{fill:{colors['mountain_near']}}}
.city{{fill:{colors['city']}}}.city-line{{stroke:{colors['city']};stroke-width:3}}.window{{fill:{colors['window']};opacity:.8}}.beacon-static{{fill:{colors['red']}}}
.terminal{{fill:{colors['panel']};stroke:{colors['border']}}}.prompt{{fill:{colors['mint']};font-size:14px;font-weight:700}}
.command{{fill:{colors['text']};font-size:14px}}.cursor{{fill:{colors['cyan']};animation:blink 1.1s steps(1) infinite}}
.pulse{{animation:pulse 2.2s ease-out infinite;transform-origin:600px 270px}}.pulse-ring{{animation:ring 2.2s ease-out infinite;transform-origin:600px 270px}}
@keyframes blink{{50%{{opacity:0}}}}@keyframes pulse{{50%{{transform:scale(1.45);opacity:.65}}}}
@keyframes ring{{0%{{transform:scale(.4);opacity:.9}}100%{{transform:scale(1.7);opacity:0}}}}
@media(prefers-reduced-motion:reduce){{.packet,.pulse,.pulse-ring,.cursor{{animation:none!important}}}}
</style>
""".strip()


def render_svg(
    config: dict[str, Any], telemetry: dict[str, Any], theme_name: str,
    generated_at: datetime,
) -> str:
    colors = THEMES[theme_name]
    identity = config["identity"]
    local = generated_at.astimezone(ZoneInfo(identity["timezone"]))
    stamp = local.strftime("%Y-%m-%d NPT")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720" role="img" aria-labelledby="title desc">',
        '<title id="title">Naitik Joshi - Kathmandu Network Node</title>',
        '<desc id="desc">Four software projects connected to a Kathmandu network node above a city and mountain skyline.</desc>',
        '<defs><filter id="glow"><feGaussianBlur stdDeviation="2" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
        render_style(colors, config["projects"]),
        '<rect x="12" y="12" width="1176" height="696" rx="5" class="outer"/>',
        '<line x1="24" y1="86" x2="1176" y2="86" class="rule"/>',
        svg_text(36, 50, identity["name"], "identity"),
        svg_text(38, 72, identity["role"], "identity-role"),
        svg_text(1164, 42, identity["node"], "header-signal", "end"),
        svg_text(1164, 62, f"NPT +05:45 / {stamp}", "header-muted", "end"),
        render_mountains(), render_connections(config["projects"]),
        render_central_node(),
    ]
    parts.extend(render_project_node(project) for project in config["projects"])
    parts.extend([
        panel(34, 112, 245, 184, "CURRENT BUILD"),
        svg_text(52, 170, config["current_build"], "body-strong"),
        svg_text(52, 195, "ACTIVE DEVELOPMENT", "signal"),
        svg_text(52, 226, "AI SYSTEMS / DEVTOOLS", "body-muted"),
        svg_text(52, 250, identity["location"], "body-muted"),
        svg_text(52, 274, "LOCAL NODE / UTC +05:45", "body-muted"),
        panel(930, 112, 236, 184, "PUBLIC SIGNAL"),
        svg_text(948, 164, "LATEST REPOSITORY", "body-muted"),
        svg_text(948, 187, telemetry["latest_repo"], "body-strong"),
        svg_text(948, 208, telemetry["latest_repo_date"], "body-muted"),
        svg_text(948, 242, f"REPOS  {telemetry['public_repos']}", "body"),
        svg_text(1060, 242, f"STARS  {telemetry['stars']}", "body"),
        svg_text(948, 267, f"FOLLOWERS  {telemetry['followers']}", "body"),
        render_skyline(),
        '<rect x="24" y="650" width="1152" height="43" rx="3" class="terminal"/>',
        svg_text(42, 677, "naitik@ktm:~$", "prompt"),
        svg_text(177, 677, identity["tagline"], "command"),
        '<rect x="500" y="663" width="8" height="18" class="cursor"/>',
        svg_text(1158, 677, "PYTHON / SVG / GITHUB ACTIONS", "body-muted", "end"),
        '</svg>',
    ])
    return "\n".join(parts)


def generate(config_path: Path, output_dir: Path, offline: bool = False) -> list[Path]:
    config = load_config(config_path)
    telemetry = fetch_telemetry(config, offline=offline)
    generated_at = datetime.now(tz=ZoneInfo("UTC"))
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for theme_name in THEMES:
        destination = output_dir / f"profile-{theme_name}.svg"
        destination.write_text(
            render_svg(config, telemetry, theme_name, generated_at), encoding="utf-8"
        )
        outputs.append(destination)
        print(f"[profile] wrote {destination}")
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "profile.json")
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    parser.add_argument("--offline", action="store_true")
    return parser.parse_args()


# Phase 2/3 renderer. The Phase 1 implementation above remains available as a
# readable migration reference while this entry point exports the refined API.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_renderer import (  # noqa: E402
    PROJECT_POSITIONS,
    THEMES,
    fetch_telemetry,
    generate,
    load_config,
    render_svg,
    safe,
)


if __name__ == "__main__":
    arguments = parse_args()
    generate(arguments.config, arguments.output, offline=arguments.offline)
