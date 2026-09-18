#!/usr/bin/env python3
"""Render deterministic desktop and mobile Kathmandu profile artwork."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from copy import deepcopy
from html import escape
from pathlib import Path
from typing import Any


THEMES = {
    "dark": {
        "bg": "#071419", "panel": "#0D2026", "panel_alt": "#102A31",
        "border": "#315D66", "mountain_far": "#102A32",
        "mountain_near": "#17363D", "city": "#091217",
        "window": "#F0B84B", "mint": "#72E2C4", "cyan": "#59C3DA",
        "amber": "#F0B84B", "red": "#DB5A57", "text": "#EAF3F2",
        "muted": "#8DA9AD", "grid": "#173139",
    },
    "light": {
        "bg": "#EDF4F1", "panel": "#F8FBF9", "panel_alt": "#E1ECE8",
        "border": "#789995", "mountain_far": "#D5E3DF",
        "mountain_near": "#C3D6D1", "city": "#AFC4BF",
        "window": "#9B6200", "mint": "#087D70", "cyan": "#0B748B",
        "amber": "#9B6200", "red": "#B33E3B", "text": "#142426",
        "muted": "#536B6D", "grid": "#D3E1DD",
    },
}

DESKTOP_POSITIONS = {
    "northwest": (390, 235), "southwest": (390, 455),
    "northeast": (810, 235), "southeast": (810, 455),
}
MOBILE_POSITIONS = {
    "northwest": (190, 300), "southwest": (190, 548),
    "northeast": (530, 300), "southeast": (530, 548),
}
PROJECT_POSITIONS = DESKTOP_POSITIONS


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if len(config.get("projects", [])) != 4:
        raise ValueError("The network layout requires exactly four projects")
    positions = {project["position"] for project in config["projects"]}
    if positions != set(DESKTOP_POSITIONS):
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
    fallback = deepcopy(config["fallback_telemetry"])
    if offline:
        return fallback

    username = config["username"]
    token = os.environ.get("GITHUB_TOKEN")
    try:
        user = github_json(f"https://api.github.com/users/{username}", token)
        repos = github_json(
            f"https://api.github.com/users/{username}/repos"
            "?per_page=100&sort=pushed&type=owner",
            token,
        )
    except (
        urllib.error.URLError,
        subprocess.SubprocessError,
        TimeoutError,
        ValueError,
        OSError,
    ) as exc:
        print(f"[profile] GitHub telemetry unavailable: {exc}", file=sys.stderr)
        return fallback

    owned = [repo for repo in repos if not repo.get("fork")]
    project_repos = [
        repo
        for repo in owned
        if str(repo.get("name", "")).lower() != username.lower()
    ]
    latest = project_repos[0] if project_repos else {}
    repo_index = {str(repo.get("name", "")).lower(): repo for repo in owned}
    project_signals: dict[str, dict[str, Any]] = {}

    for project in config["projects"]:
        repo_name = project["repo"]
        repo = repo_index.get(repo_name.lower())
        saved = fallback.get("projects", {}).get(repo_name, {})
        if repo is None:
            project_signals[repo_name] = saved
            continue
        project_signals[repo_name] = {
            "language": repo.get("language") or saved.get("language", "Mixed"),
            "stars": int(repo.get("stargazers_count", saved.get("stars", 0))),
            "forks": int(repo.get("forks_count", saved.get("forks", 0))),
            "open_issues": int(
                repo.get("open_issues_count", saved.get("open_issues", 0))
            ),
            "pushed_date": str(
                repo.get("pushed_at", saved.get("pushed_date", "unknown"))
            )[:10],
        }

    return {
        "public_repos": user.get("public_repos", fallback["public_repos"]),
        "followers": user.get("followers", fallback["followers"]),
        "stars": sum(int(repo.get("stargazers_count", 0)) for repo in owned),
        "latest_repo": latest.get("name", fallback["latest_repo"]),
        "latest_repo_date": str(
            latest.get("pushed_at", fallback["latest_repo_date"])
        )[:10],
        "projects": project_signals,
    }


def safe(value: Any) -> str:
    return escape(str(value), quote=True)


def svg_text(
    x: int | float,
    y: int | float,
    value: Any,
    css_class: str,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x}" y="{y}" class="{css_class}" '
        f'text-anchor="{anchor}">{safe(value)}</text>'
    )


def panel(x: int, y: int, width: int, height: int, label: str) -> str:
    return "\n".join([
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" class="panel"/>',
        svg_text(x + 16, y + 25, label, "label"),
        f'<line x1="{x + 14}" y1="{y + 36}" x2="{x + width - 14}" y2="{y + 36}" class="rule"/>',
    ])


def telemetry_line(signal: dict[str, Any]) -> str:
    pushed = str(signal.get("pushed_date", "unknown"))
    if len(pushed) == 10:
        pushed = pushed[5:]
    return f"UPDATED {pushed}"


def render_grid(width: int, height: int) -> str:
    return (
        '<defs>'
        '<filter id="glow"><feGaussianBlur stdDeviation="2" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/>'
        '</feMerge></filter>'
        '<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">'
        '<path d="M 28 0 L 0 0 0 28" class="grid-line"/>'
        '</pattern></defs>'
        f'<rect width="{width}" height="{height}" fill="url(#grid)" opacity=".28"/>'
    )


def render_desktop_mountains() -> str:
    return """
<path class="mountain-far" d="M18 530 L84 458 L124 491 L183 421 L237 480 L304 404 L368 480 L432 432 L493 486 L553 408 L615 478 L680 428 L744 488 L814 405 L873 469 L934 427 L998 484 L1063 415 L1122 476 L1182 433 L1182 634 L18 634 Z"/>
<path class="mountain-near" d="M18 569 L96 510 L148 552 L220 479 L286 555 L351 508 L425 563 L509 489 L582 557 L653 515 L726 566 L805 488 L877 552 L945 506 L1014 563 L1090 499 L1182 556 L1182 634 L18 634 Z"/>
""".strip()


def render_desktop_skyline() -> str:
    buildings = [
        (22, 579, 54, 55), (82, 552, 45, 82), (134, 589, 64, 45),
        (205, 560, 52, 74), (264, 583, 67, 51), (338, 545, 54, 89),
        (399, 572, 70, 62), (477, 554, 42, 80), (527, 585, 58, 49),
        (594, 556, 62, 78), (664, 578, 70, 56), (742, 547, 48, 87),
        (798, 572, 69, 62), (875, 555, 58, 79), (941, 584, 65, 50),
        (1014, 552, 51, 82), (1072, 579, 52, 55), (1131, 561, 47, 73),
    ]
    parts = ['<g class="city">']
    for index, (x, y, width, height) in enumerate(buildings):
        parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}"/>')
        if index % 3 != 1:
            parts.append(f'<rect x="{x + 10}" y="{y + 14}" width="5" height="5" class="window"/>')
            parts.append(f'<rect x="{x + 26}" y="{y + 28}" width="5" height="5" class="window"/>')
    parts.extend([
        '<rect x="173" y="531" width="88" height="103"/>',
        '<polygon points="160,551 217,515 274,551"/>',
        '<polygon points="174,525 217,495 260,525"/>',
        '<line x1="217" y1="495" x2="217" y2="476" class="city-line"/>',
        '<rect x="354" y="529" width="22" height="15" rx="2"/>',
        '<line x1="358" y1="529" x2="358" y2="522" class="city-line thin"/>',
        '<line x1="372" y1="529" x2="372" y2="522" class="city-line thin"/>',
        '<rect x="914" y="580" width="124" height="54"/>',
        '<path d="M930 580 Q976 520 1022 580 Z"/>',
        '<rect x="972" y="531" width="8" height="39"/>',
        '<circle cx="976" cy="523" r="5" class="beacon-static"/>',
        '</g>',
    ])
    return "\n".join(parts)


def render_mobile_landscape() -> str:
    return """
<path class="mountain-far" d="M12 731 L69 670 L113 705 L172 635 L231 706 L293 646 L354 709 L416 628 L478 702 L542 646 L604 707 L662 659 L708 698 L708 895 L12 895 Z"/>
<path class="mountain-near" d="M12 778 L82 719 L143 766 L215 699 L282 770 L355 712 L428 772 L506 695 L577 766 L644 718 L708 762 L708 895 L12 895 Z"/>
<g class="city">
  <rect x="14" y="828" width="51" height="67"/><rect x="72" y="802" width="48" height="93"/>
  <rect x="128" y="839" width="64" height="56"/><rect x="201" y="790" width="58" height="105"/>
  <rect x="267" y="823" width="56" height="72"/><rect x="331" y="805" width="66" height="90"/>
  <rect x="405" y="836" width="58" height="59"/><rect x="471" y="797" width="51" height="98"/>
  <rect x="530" y="829" width="67" height="66"/><rect x="605" y="808" width="43" height="87"/>
  <rect x="656" y="835" width="50" height="60"/>
  <rect x="166" y="778" width="84" height="117"/><polygon points="151,798 208,762 265,798"/>
  <polygon points="168,769 208,741 248,769"/><line x1="208" y1="741" x2="208" y2="724" class="city-line"/>
  <rect x="520" y="823" width="112" height="72"/><path d="M532 823 Q576 766 620 823 Z"/>
  <rect x="572" y="774" width="8" height="39"/><circle cx="576" cy="766" r="5" class="beacon-static"/>
  <rect x="91" y="816" width="22" height="15" rx="2"/>
  <rect x="223" y="810" width="5" height="5" class="window"/><rect x="346" y="825" width="5" height="5" class="window"/>
  <rect x="486" y="815" width="5" height="5" class="window"/><rect x="670" y="849" width="5" height="5" class="window"/>
</g>
""".strip()


def render_connections(
    projects: list[dict[str, Any]],
    positions: dict[str, tuple[int, int]],
    central: tuple[int, int],
    node_width: int = 214,
) -> str:
    cx, cy = central
    parts = ['<g class="routes">']
    for index, project in enumerate(projects, start=1):
        x, y = positions[project["position"]]
        edge_x = x + (node_width // 2) if x < cx else x - (node_width // 2)
        mid_x = int((cx + edge_x) / 2)
        path = f"M {cx} {cy} C {mid_x} {cy}, {mid_x} {y}, {edge_x} {y}"
        parts.append(f'<path id="route-{index}" d="{path}" class="route"/>')
        parts.append(
            f'<circle r="4" class="packet packet-{index}">'
            f'<animateMotion dur="{5.8 + (index * .7):.1f}s" '
            f'begin="{(index - 1) * .65:.2f}s" repeatCount="indefinite">'
            f'<mpath href="#route-{index}"/>'
            '</animateMotion></circle>'
        )
    parts.append('</g>')
    return "\n".join(parts)


def render_project_node(
    project: dict[str, Any],
    telemetry: dict[str, Any],
    positions: dict[str, tuple[int, int]],
    mobile: bool = False,
) -> str:
    x, y = positions[project["position"]]
    accent = project.get("accent", "cyan")
    signal = telemetry.get("projects", {}).get(project["repo"], {})
    width = 258 if mobile else 214
    height = 92
    box_x, box_y = x - width // 2, y - height // 2
    icon_x = box_x + 14
    text_x = box_x + 52
    return "\n".join([
        f'<g class="project-node" aria-label="{safe(project["name"])}">',
        f'<rect x="{box_x}" y="{box_y}" width="{width}" height="{height}" rx="3" class="node-box {accent}-stroke"/>',
        f'<rect x="{icon_x}" y="{box_y + 14}" width="28" height="32" rx="2" class="node-machine"/>',
        f'<line x1="{icon_x + 6}" y1="{box_y + 23}" x2="{icon_x + 22}" y2="{box_y + 23}" class="{accent}-stroke"/>',
        f'<line x1="{icon_x + 6}" y1="{box_y + 32}" x2="{icon_x + 22}" y2="{box_y + 32}" class="{accent}-stroke"/>',
        f'<circle cx="{icon_x + 8}" cy="{box_y + 41}" r="2" class="{accent}-fill"/>',
        svg_text(text_x, box_y + 26, project["name"], "node-title"),
        svg_text(text_x, box_y + 47, project["status"], f"node-status {accent}-text"),
        svg_text(
            box_x + 14,
            box_y + 74,
            f"{project['stack']} / {telemetry_line(signal)}",
            "node-stack",
        ),
        '</g>',
    ])


def render_central_node(x: int, y: int, scale: float = 1.0) -> str:
    outer, core = int(72 * scale), int(55 * scale)
    tower_w, tower_h = int(54 * scale), int(48 * scale)
    tx, ty = x - tower_w // 2, y - tower_h // 2
    antenna_top = ty - int(29 * scale)
    return "\n".join([
        '<g class="central-node">',
        f'<circle cx="{x}" cy="{y}" r="{outer}" class="node-halo"/>',
        f'<circle cx="{x}" cy="{y}" r="{core}" class="node-core"/>',
        f'<rect x="{tx}" y="{ty}" width="{tower_w}" height="{tower_h}" rx="3" class="tower"/>',
        f'<line x1="{tx + int(12 * scale)}" y1="{ty + int(13 * scale)}" x2="{tx + int(42 * scale)}" y2="{ty + int(13 * scale)}" class="mint-stroke"/>',
        f'<line x1="{tx + int(12 * scale)}" y1="{ty + int(25 * scale)}" x2="{tx + int(42 * scale)}" y2="{ty + int(25 * scale)}" class="cyan-stroke"/>',
        f'<line x1="{tx + int(12 * scale)}" y1="{ty + int(37 * scale)}" x2="{tx + int(32 * scale)}" y2="{ty + int(37 * scale)}" class="amber-stroke"/>',
        f'<line x1="{x}" y1="{ty}" x2="{x}" y2="{antenna_top + int(5 * scale)}" class="tower-line"/>',
        f'<circle cx="{x}" cy="{antenna_top}" r="{max(4, int(5 * scale))}" class="beacon pulse"/>',
        f'<circle cx="{x}" cy="{antenna_top}" r="{max(9, int(12 * scale))}" class="beacon-ring pulse-ring"/>',
        svg_text(x, y + int(42 * scale), "KTM-NP-0545", "central-title", "middle"),
        svg_text(x, y + int(61 * scale), "NETWORK NODE", "central-subtitle", "middle"),
        '</g>',
    ])


def render_style(
    colors: dict[str, str],
    projects: list[dict[str, Any]],
    positions: dict[str, tuple[int, int]],
    central: tuple[int, int],
    mobile: bool = False,
) -> str:
    del projects, positions, central
    title_size, status_size = (17, 11) if mobile else (15, 9)
    stack_size = 11 if mobile else 10
    return f"""
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.outer{{fill:{colors['bg']};stroke:{colors['border']};stroke-width:1.5}}
.grid-line{{fill:none;stroke:{colors['grid']};stroke-width:1}}
.panel{{fill:{colors['panel']};stroke:{colors['border']};stroke-width:1.25}}
.rule{{stroke:{colors['border']};stroke-width:1}}
.label{{fill:{colors['mint']};font-size:13px;font-weight:700;letter-spacing:1px}}
.identity{{fill:{colors['text']};font-size:31px;font-weight:800}}
.identity-role{{fill:{colors['muted']};font-size:14px}}
.header-signal{{fill:{colors['text']};font-size:13px;font-weight:700}}
.header-muted{{fill:{colors['muted']};font-size:12px}}
.body{{fill:{colors['text']};font-size:14px}}.body-strong{{fill:{colors['text']};font-size:16px;font-weight:700}}
.body-muted{{fill:{colors['muted']};font-size:12px}}.signal{{fill:{colors['mint']};font-size:12px;font-weight:700}}
.route{{fill:none;stroke:{colors['cyan']};stroke-width:1.5;stroke-dasharray:5 7;opacity:.7}}
.packet{{fill:{colors['mint']};filter:url(#glow)}}
.node-box{{fill:{colors['panel']};stroke-width:1.5}}.node-machine{{fill:{colors['panel_alt']};stroke:{colors['border']}}}
.node-title{{fill:{colors['text']};font-size:{title_size}px;font-weight:700}}.node-status{{font-size:{status_size}px;font-weight:700}}
.node-stack{{fill:{colors['muted']};font-size:{stack_size}px}}
.mint-stroke{{stroke:{colors['mint']};fill:none}}.cyan-stroke{{stroke:{colors['cyan']};fill:none}}.amber-stroke{{stroke:{colors['amber']};fill:none}}
.mint-fill{{fill:{colors['mint']}}}.cyan-fill{{fill:{colors['cyan']}}}.amber-fill{{fill:{colors['amber']}}}
.mint-text{{fill:{colors['mint']}}}.cyan-text{{fill:{colors['cyan']}}}.amber-text{{fill:{colors['amber']}}}
.node-halo{{fill:{colors['panel']};stroke:{colors['cyan']};opacity:.94}}.node-core{{fill:{colors['panel_alt']};stroke:{colors['mint']};stroke-width:2}}
.tower{{fill:{colors['bg']};stroke:{colors['border']}}}.tower-line{{stroke:{colors['amber']};stroke-width:2}}
.beacon{{fill:{colors['red']}}}.beacon-ring{{fill:none;stroke:{colors['red']}}}
.central-title{{fill:{colors['cyan']};font-size:15px;font-weight:800}}.central-subtitle{{fill:{colors['muted']};font-size:10px;letter-spacing:1px}}
.mountain-far{{fill:{colors['mountain_far']}}}.mountain-near{{fill:{colors['mountain_near']}}}
.city{{fill:{colors['city']}}}.city-line{{stroke:{colors['city']};stroke-width:3}}.city-line.thin{{stroke-width:1.5}}
.window{{fill:{colors['window']};opacity:.85}}.beacon-static{{fill:{colors['red']}}}
.terminal{{fill:{colors['panel']};stroke:{colors['border']}}}.prompt{{fill:{colors['mint']};font-size:14px;font-weight:700}}
.command{{fill:{colors['text']};font-size:14px}}.cursor{{fill:{colors['cyan']};animation:blink 1.1s steps(1) infinite}}
.pulse{{animation:pulse 2.6s ease-out infinite;transform-box:fill-box;transform-origin:center}}
.pulse-ring{{animation:ring 2.6s ease-out infinite;transform-box:fill-box;transform-origin:center}}
@keyframes blink{{50%{{opacity:0}}}}@keyframes pulse{{50%{{transform:scale(1.35);opacity:.65}}}}
@keyframes ring{{0%{{transform:scale(.45);opacity:.9}}100%{{transform:scale(1.75);opacity:0}}}}
@media(prefers-reduced-motion:reduce){{.packet{{display:none}}.pulse,.pulse-ring,.cursor{{animation:none!important}}}}
</style>
""".strip()


def render_desktop_svg(
    config: dict[str, Any], telemetry: dict[str, Any], theme_name: str
) -> str:
    colors, identity = THEMES[theme_name], config["identity"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720" role="img" aria-labelledby="title desc">',
        '<title id="title">Naitik Joshi - Kathmandu Network Node</title>',
        '<desc id="desc">Four software projects with public repository signals connect to a Kathmandu network node above a city and mountain skyline.</desc>',
        render_style(colors, config["projects"], DESKTOP_POSITIONS, (600, 350)),
        '<rect x="12" y="12" width="1176" height="696" rx="4" class="outer"/>',
        render_grid(1200, 720),
        '<line x1="24" y1="86" x2="1176" y2="86" class="rule"/>',
        svg_text(36, 50, identity["name"], "identity"),
        svg_text(38, 72, identity["role"], "identity-role"),
        svg_text(1164, 42, identity["node"], "header-signal", "end"),
        svg_text(1164, 62, "NPT +05:45 / PUBLIC API / WEEKLY", "header-muted", "end"),
        render_desktop_mountains(),
        render_connections(config["projects"], DESKTOP_POSITIONS, (600, 350)),
        render_central_node(600, 350),
    ]
    parts.extend(
        render_project_node(project, telemetry, DESKTOP_POSITIONS)
        for project in config["projects"]
    )
    parts.extend([
        '<rect x="34" y="108" width="1132" height="62" rx="3" class="panel"/>',
        '<line x1="390" y1="108" x2="390" y2="170" class="rule"/>',
        '<line x1="810" y1="108" x2="810" y2="170" class="rule"/>',
        svg_text(52, 132, "CURRENT BUILD", "label"),
        svg_text(52, 158, config["current_build"], "body-strong"),
        svg_text(142, 158, "ACTIVE", "signal"),
        svg_text(410, 132, "LATEST PUSH", "label"),
        svg_text(410, 158, telemetry["latest_repo"], "body-strong"),
        svg_text(782, 158, telemetry["latest_repo_date"], "body-muted", "end"),
        svg_text(830, 132, "PUBLIC GITHUB", "label"),
        svg_text(
            830,
            158,
            f"{telemetry['public_repos']} REPOS / {telemetry['stars']} STARS / {telemetry['followers']} FOLLOWERS",
            "body",
        ),
        render_desktop_skyline(),
        '<rect x="24" y="650" width="1152" height="43" rx="2" class="terminal"/>',
        svg_text(42, 677, "naitik@ktm:~$", "prompt"),
        svg_text(177, 677, identity["tagline"], "command"),
        '<rect x="500" y="663" width="8" height="18" class="cursor"/>',
        svg_text(1158, 677, "PYTHON / SVG / GITHUB ACTIONS", "body-muted", "end"),
        '</svg>',
    ])
    return "\n".join(parts)


def render_mobile_svg(
    config: dict[str, Any], telemetry: dict[str, Any], theme_name: str
) -> str:
    colors, identity = THEMES[theme_name], config["identity"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="960" viewBox="0 0 720 960" role="img" aria-labelledby="title desc">',
        '<title id="title">Naitik Joshi - Kathmandu Network Node mobile profile</title>',
        '<desc id="desc">A mobile layout of four software projects connected to a Kathmandu network node.</desc>',
        render_style(colors, config["projects"], MOBILE_POSITIONS, (360, 423), mobile=True),
        '<rect x="10" y="10" width="700" height="940" rx="4" class="outer"/>',
        render_grid(720, 960),
        svg_text(30, 49, identity["name"], "identity"),
        svg_text(31, 73, identity["role"], "identity-role"),
        svg_text(690, 42, identity["node"], "header-signal", "end"),
        svg_text(690, 64, "NPT +05:45", "header-muted", "end"),
        '<line x1="22" y1="91" x2="698" y2="91" class="rule"/>',
        '<rect x="24" y="108" width="672" height="76" rx="3" class="panel"/>',
        svg_text(42, 133, "CURRENT BUILD", "label"),
        svg_text(42, 161, f"{config['current_build']} / ACTIVE DEVELOPMENT", "body-strong"),
        svg_text(678, 133, "PUBLIC SIGNAL", "label", "end"),
        svg_text(678, 161, f"{telemetry['public_repos']} REPOS / {telemetry['stars']} STARS / {telemetry['followers']} FOLLOWERS", "body", "end"),
        render_mobile_landscape(),
        render_connections(
            config["projects"], MOBILE_POSITIONS, (360, 423), node_width=258
        ),
        render_central_node(360, 423, .84),
    ]
    parts.extend(
        render_project_node(project, telemetry, MOBILE_POSITIONS, mobile=True)
        for project in config["projects"]
    )
    parts.extend([
        '<rect x="24" y="902" width="672" height="36" rx="2" class="terminal"/>',
        svg_text(39, 926, "naitik@ktm:~$", "prompt"),
        svg_text(177, 926, "building useful and unusual software", "command"),
        '<rect x="516" y="913" width="8" height="17" class="cursor"/>',
        '</svg>',
    ])
    return "\n".join(parts)


def render_svg(
    config: dict[str, Any], telemetry: dict[str, Any], theme_name: str,
    generated_at: Any = None,
) -> str:
    """Backward-compatible desktop renderer with deterministic output."""
    del generated_at
    return render_desktop_svg(config, telemetry, theme_name)


def generate(config_path: Path, output_dir: Path, offline: bool = False) -> list[Path]:
    config = load_config(config_path)
    telemetry = fetch_telemetry(config, offline=offline)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for theme_name in THEMES:
        variants = {
            f"profile-{theme_name}.svg": render_desktop_svg(config, telemetry, theme_name),
            f"profile-{theme_name}-mobile.svg": render_mobile_svg(config, telemetry, theme_name),
        }
        for filename, content in variants.items():
            destination = output_dir / filename
            destination.write_text(content, encoding="utf-8")
            outputs.append(destination)
            print(f"[profile] wrote {destination}")
    data_destination = output_dir / "profile-data.json"
    data_destination.write_text(
        json.dumps(
            {
                "username": config["username"],
                "current_build": config["current_build"],
                "public": {
                    key: telemetry[key]
                    for key in (
                        "public_repos", "followers", "stars",
                        "latest_repo", "latest_repo_date",
                    )
                },
                "projects": telemetry.get("projects", {}),
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    outputs.append(data_destination)
    print(f"[profile] wrote {data_destination}")
    return outputs
