#!/usr/bin/env python3
"""Compile KTM//NIGHTSHIFT into SVG frames and linked Markdown states."""

from __future__ import annotations

import argparse
import json
import math
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADINGS = (
    ("E", 0.0, (1, 0)),
    ("S", math.pi / 2, (0, 1)),
    ("W", math.pi, (-1, 0)),
    ("N", -math.pi / 2, (0, -1)),
)
WALL_COLORS = {
    "1": "#8C96A8",
    "2": "#FF5A5F",
    "3": "#3B6CFF",
    "4": "#FFD447",
}
VIEW_WIDTH = 960
VIEW_HEIGHT = 540
HORIZON = 270
RAY_COUNT = 120
FOV = math.radians(66)


def load_map(path: Path) -> tuple[list[str], tuple[int, int], tuple[int, int]]:
    rows = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or len({len(row) for row in rows}) != 1:
        raise ValueError("Map must be a non-empty rectangle")
    allowed = set(".SX1234")
    if any(character not in allowed for row in rows for character in row):
        raise ValueError("Map contains unsupported tiles")
    starts = [(x, y) for y, row in enumerate(rows) for x, value in enumerate(row) if value == "S"]
    exits = [(x, y) for y, row in enumerate(rows) for x, value in enumerate(row) if value == "X"]
    if len(starts) != 1 or len(exits) != 1:
        raise ValueError("Map requires exactly one S spawn and one X uplink")
    return rows, starts[0], exits[0]


def is_walkable(level: list[str], x: int, y: int) -> bool:
    return 0 <= y < len(level) and 0 <= x < len(level[0]) and level[y][x] in ".SX"


def walkable_cells(level: list[str]) -> list[tuple[int, int]]:
    return [
        (x, y)
        for y, row in enumerate(level)
        for x, value in enumerate(row)
        if value in ".SX"
    ]


def shortest_path(
    level: list[str],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    queue = deque([start])
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (current[0] + dx, current[1] + dy)
            if neighbor not in previous and is_walkable(level, *neighbor):
                previous[neighbor] = current
                queue.append(neighbor)
    if goal not in previous:
        raise ValueError("Uplink is not reachable from spawn")
    path: list[tuple[int, int]] = []
    current: tuple[int, int] | None = goal
    while current is not None:
        path.append(current)
        current = previous[current]
    return list(reversed(path))


def state_name(x: int, y: int, heading_index: int) -> str:
    return f"x{x:02d}-y{y:02d}-{HEADINGS[heading_index][0]}"


def cast_ray(
    level: list[str],
    px: float,
    py: float,
    angle: float,
    max_distance: float = 24.0,
) -> tuple[float, str, int, float]:
    ray_x, ray_y = math.cos(angle), math.sin(angle)
    map_x, map_y = int(px), int(py)
    delta_x = abs(1 / ray_x) if abs(ray_x) > 1e-9 else 1e30
    delta_y = abs(1 / ray_y) if abs(ray_y) > 1e-9 else 1e30
    if ray_x < 0:
        step_x = -1
        side_x = (px - map_x) * delta_x
    else:
        step_x = 1
        side_x = (map_x + 1 - px) * delta_x
    if ray_y < 0:
        step_y = -1
        side_y = (py - map_y) * delta_y
    else:
        step_y = 1
        side_y = (map_y + 1 - py) * delta_y

    side = 0
    distance = 0.0
    tile = "1"
    while distance < max_distance:
        if side_x < side_y:
            side_x += delta_x
            map_x += step_x
            side = 0
            distance = side_x - delta_x
        else:
            side_y += delta_y
            map_y += step_y
            side = 1
            distance = side_y - delta_y
        if not (0 <= map_y < len(level) and 0 <= map_x < len(level[0])):
            break
        tile = level[map_y][map_x]
        if tile in WALL_COLORS:
            hit_x = px + distance * ray_x
            hit_y = py + distance * ray_y
            texture = hit_y % 1 if side == 0 else hit_x % 1
            return max(distance, 0.01), tile, side, texture
    return max_distance, tile, side, 0.0


def normalize_angle(value: float) -> float:
    while value > math.pi:
        value -= math.tau
    while value < -math.pi:
        value += math.tau
    return value


def clear_line(level: list[str], start: tuple[float, float], end: tuple[float, float]) -> bool:
    distance = math.dist(start, end)
    steps = max(2, int(distance * 24))
    for index in range(1, steps):
        amount = index / steps
        x = start[0] + (end[0] - start[0]) * amount
        y = start[1] + (end[1] - start[1]) * amount
        if level[int(y)][int(x)] in WALL_COLORS:
            return False
    return True


def render_uplink(
    level: list[str],
    px: float,
    py: float,
    heading: float,
    exit_cell: tuple[int, int],
    depth_buffer: list[float],
) -> str:
    target = (exit_cell[0] + 0.5, exit_cell[1] + 0.5)
    dx, dy = target[0] - px, target[1] - py
    distance = math.hypot(dx, dy)
    relative = normalize_angle(math.atan2(dy, dx) - heading)
    if abs(relative) > FOV * 0.56 or distance < 0.15:
        return ""
    if not clear_line(level, (px, py), target):
        return ""
    screen_ratio = 0.5 + math.tan(relative) / (2 * math.tan(FOV / 2))
    screen_x = screen_ratio * VIEW_WIDTH
    ray_index = min(RAY_COUNT - 1, max(0, int(screen_ratio * RAY_COUNT)))
    if distance > depth_buffer[ray_index] + 0.3:
        return ""
    size = max(30, min(160, 230 / max(distance, 0.5)))
    x = screen_x - size / 2
    y = HORIZON - size * 0.52
    return f"""
<g>
  <rect x="{x-7:.1f}" y="{y-7:.1f}" width="{size+14:.1f}" height="{size+14:.1f}" fill="#63E6BE" opacity=".18"/>
  <rect x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" height="{size:.1f}" fill="#0E141D" stroke="#63E6BE" stroke-width="4"/>
  <rect x="{x+size*.16:.1f}" y="{y+size*.18:.1f}" width="{size*.68:.1f}" height="{size*.26:.1f}" fill="#63E6BE"/>
  <text x="{screen_x:.1f}" y="{y+size*.37:.1f}" class="terminal" text-anchor="middle">05:45</text>
  <path d="M{x+size*.24:.1f} {y+size*.67:.1f}H{x+size*.76:.1f}M{x+size*.24:.1f} {y+size*.80:.1f}H{x+size*.58:.1f}" stroke="#FFD447" stroke-width="4"/>
</g>
""".strip()


def render_frame(
    level: list[str],
    x: int,
    y: int,
    heading_index: int,
    exit_cell: tuple[int, int],
) -> str:
    heading_name, heading, _ = HEADINGS[heading_index]
    px, py = x + 0.5, y + 0.5
    wall_slices: list[str] = []
    depth_buffer: list[float] = []
    slice_width = VIEW_WIDTH / RAY_COUNT
    for ray in range(RAY_COUNT):
        camera = (ray + 0.5) / RAY_COUNT - 0.5
        angle = heading + camera * FOV
        distance, tile, side, texture = cast_ray(level, px, py, angle)
        corrected = max(0.08, distance * math.cos(angle - heading))
        depth_buffer.append(corrected)
        height = min(VIEW_HEIGHT * 1.45, VIEW_HEIGHT * 0.92 / corrected)
        top = HORIZON - height / 2
        opacity = max(0.28, min(1.0, 1.08 - corrected / 13))
        if side:
            opacity *= 0.72
        if texture < 0.07 or texture > 0.93:
            opacity *= 0.74
        wall_slices.append(
            f'<rect x="{ray*slice_width:.2f}" y="{top:.2f}" width="{slice_width+0.4:.2f}" '
            f'height="{height:.2f}" fill="{WALL_COLORS.get(tile, WALL_COLORS["1"])}" opacity="{opacity:.3f}"/>'
        )

    uplink = render_uplink(level, px, py, heading, exit_cell, depth_buffer)
    at_exit = (x, y) == exit_cell
    floor_lines = "".join(
        f'<line x1="0" y1="{line}" x2="960" y2="{line}" stroke="#354052" stroke-width="1" opacity="{0.16 + (line-HORIZON)/1000:.2f}"/>'
        for line in range(HORIZON + 28, VIEW_HEIGHT, 30)
    )
    success = ""
    if at_exit:
        success = """
<g>
  <rect x="118" y="112" width="724" height="280" fill="#0B0E14" stroke="#63E6BE" stroke-width="5"/>
  <rect x="138" y="132" width="684" height="42" fill="#63E6BE"/>
  <text x="160" y="160" class="bar dark">UPLINK ACQUIRED / KTM 05:45</text>
  <text x="480" y="244" class="complete" text-anchor="middle">TRANSMISSION FOUND</text>
  <text x="480" y="291" class="copy" text-anchor="middle">THE PLATFORM SAID STATIC. YOU KEPT MOVING.</text>
  <text x="480" y="339" class="hud muted" text-anchor="middle">LEVEL COMPLETE / RETURN OR KEEP EXPLORING</text>
</g>
""".strip()

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-labelledby="title desc">
<title id="title">KTM Nightshift position {x}, {y}, facing {heading_name}</title>
<desc id="desc">A first-person view inside a GitHub-native raycasted maze.</desc>
<style>
text{{font-family:'Arial Narrow','Helvetica Neue',Arial,sans-serif;letter-spacing:0}}
.mono,.hud,.bar,.terminal{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace}}
.hud{{fill:#F4F0E8;font-size:13px;font-weight:800}}.muted{{fill:#9AA4B6}}
.bar{{fill:#F4F0E8;font-size:14px;font-weight:900}}.dark{{fill:#0B0E14}}
.terminal{{fill:#0B0E14;font-size:{max(9, int(24 / max(math.dist((x, y), exit_cell), 1)))}px;font-weight:950}}
.complete{{fill:#F4F0E8;font-size:38px;font-weight:950}}.copy{{fill:#FFD447;font-size:17px;font-weight:900}}
</style>
<rect width="960" height="270" fill="#090B10"/>
<rect y="270" width="960" height="270" fill="#121722"/>
<path d="M0 270L480 338L960 270M0 420L480 338L960 420" fill="none" stroke="#20293A" stroke-width="2"/>
{floor_lines}
{"".join(wall_slices)}
{uplink}
<rect x="0" y="0" width="960" height="48" fill="#0B0E14" opacity=".94"/>
<rect x="0" y="0" width="242" height="48" fill="#FF5A5F"/>
<text x="20" y="31" class="bar dark">KTM//NIGHTSHIFT</text>
<text x="266" y="31" class="hud">SECTOR {x:02d}:{y:02d} / FACING {heading_name}</text>
<text x="938" y="31" class="hud" text-anchor="end">FIND THE 05:45 UPLINK</text>
<path d="M468 270h24M480 258v24" stroke="#F4F0E8" stroke-width="2" opacity=".82"/>
<path d="M411 540L438 454H522L549 540Z" fill="#0B0E14" stroke="#3B6CFF" stroke-width="4"/>
<rect x="459" y="448" width="42" height="67" fill="#171D28" stroke="#FFD447" stroke-width="3"/>
<circle cx="480" cy="474" r="7" fill="#63E6BE"/>
<rect x="0" y="506" width="960" height="34" fill="#0B0E14" opacity=".94"/>
<text x="18" y="528" class="hud">100 // SIGNAL</text>
<text x="480" y="528" class="hud muted" text-anchor="middle">STATE {state_name(x, y, heading_index)}</text>
<text x="942" y="528" class="hud" text-anchor="end">NO JS / NO SERVER</text>
{success}
</svg>
"""


def linked_state(
    level: list[str],
    x: int,
    y: int,
    heading_index: int,
) -> dict[str, tuple[int, int, int]]:
    _, _, (dx, dy) = HEADINGS[heading_index]
    forward = (x + dx, y + dy)
    backward = (x - dx, y - dy)
    if not is_walkable(level, *forward):
        forward = (x, y)
    if not is_walkable(level, *backward):
        backward = (x, y)
    return {
        "left": (x, y, (heading_index - 1) % 4),
        "forward": (*forward, heading_index),
        "right": (x, y, (heading_index + 1) % 4),
        "back": (*backward, heading_index),
    }


def render_state_page(
    level: list[str],
    x: int,
    y: int,
    heading_index: int,
    spawn: tuple[int, int],
    exit_cell: tuple[int, int],
) -> str:
    name = state_name(x, y, heading_index)
    links = linked_state(level, x, y, heading_index)

    def target(action: str) -> str:
        tx, ty, th = links[action]
        return f"./{state_name(tx, ty, th)}.md"

    forward_label = "W / WALL" if links["forward"][:2] == (x, y) else "W / STEP FORWARD"
    back_label = "S / WALL" if links["back"][:2] == (x, y) else "S / STEP BACK"
    completed = (x, y) == exit_cell
    completion = (
        "<p><strong>UPLINK ACQUIRED.</strong> The level is complete. The maze remains open.</p>"
        if completed else ""
    )
    return f"""<div align="center">

<h1>KTM//NIGHTSHIFT</h1>

<a href="{target('forward')}"><img src="../frames/{name}.svg" alt="KTM Nightshift first-person state {name}" width="100%"></a>

<table>
  <tr>
    <td align="center"><a href="{target('left')}"><strong>A / TURN LEFT</strong></a></td>
    <td align="center"><a href="{target('forward')}"><strong>{forward_label}</strong></a></td>
    <td align="center"><a href="{target('right')}"><strong>D / TURN RIGHT</strong></a></td>
  </tr>
  <tr>
    <td align="center"><a href="../../README.md">RETURN TO PROFILE</a></td>
    <td align="center"><a href="{target('back')}">{back_label}</a></td>
    <td align="center"><a href="./{state_name(spawn[0], spawn[1], 0)}.md">RESTART</a></td>
  </tr>
</table>

{completion}
<sub>STATE {name} // Each move loads another committed Markdown frame. No JavaScript or server.</sub>

</div>
"""


def render_game_readme(spawn: tuple[int, int]) -> str:
    start = state_name(spawn[0], spawn[1], 0)
    return f"""# KTM//NIGHTSHIFT

An original first-person maze compiled into GitHub Markdown. The level contains no runtime game engine: every valid position and facing direction is a pre-rendered SVG connected to the next state with ordinary hyperlinks.

<div align="center">

<a href="./play/{start}.md"><img src="./frames/{start}.svg" alt="Enter KTM Nightshift" width="100%"></a>

<h2><a href="./play/{start}.md">ENTER THE 05:45 RELAY</a></h2>

Find the uplink terminal. Click the viewport to step forward, or use the controls below each frame.

</div>

## Architecture

- Python raycaster with no third-party runtime dependencies.
- One SVG and one Markdown document per `(x, y, heading)` state.
- A finite navigation graph instead of JavaScript, WebAssembly, or a backend.
- Original map, interface, and vector artwork.

Regenerate the complete level with:

```bash
python3 scripts/generate_nightshift.py
```
"""


def generate(map_path: Path, output_dir: Path) -> dict[str, object]:
    level, spawn, exit_cell = load_map(map_path)
    path = shortest_path(level, spawn, exit_cell)
    frames_dir = output_dir / "frames"
    play_dir = output_dir / "play"
    frames_dir.mkdir(parents=True, exist_ok=True)
    play_dir.mkdir(parents=True, exist_ok=True)
    cells = walkable_cells(level)
    generated: list[str] = []
    for x, y in cells:
        for heading_index in range(len(HEADINGS)):
            name = state_name(x, y, heading_index)
            (frames_dir / f"{name}.svg").write_text(
                render_frame(level, x, y, heading_index, exit_cell),
                encoding="utf-8",
            )
            (play_dir / f"{name}.md").write_text(
                render_state_page(level, x, y, heading_index, spawn, exit_cell),
                encoding="utf-8",
            )
            generated.append(name)
    manifest: dict[str, object] = {
        "title": "KTM//NIGHTSHIFT",
        "map_width": len(level[0]),
        "map_height": len(level),
        "walkable_cells": len(cells),
        "headings": [heading[0] for heading in HEADINGS],
        "state_count": len(generated),
        "spawn": {"x": spawn[0], "y": spawn[1], "heading": "E"},
        "uplink": {"x": exit_cell[0], "y": exit_cell[1]},
        "shortest_path_steps": len(path) - 1,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(render_game_readme(spawn), encoding="utf-8")
    print(
        f"[nightshift] compiled {len(generated)} states from {len(cells)} cells; "
        f"uplink path is {len(path) - 1} steps"
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=ROOT / "game" / "map.txt")
    parser.add_argument("--output", type=Path, default=ROOT / "game")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    generate(arguments.map, arguments.output)
