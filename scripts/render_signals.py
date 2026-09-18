#!/usr/bin/env python3
"""Render a moderated GitHub Issue guestbook into repository-owned SVG assets."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from profile_core import THEMES, github_json, safe, svg_text  # noqa: E402


PREFIX = "[profile-signal]"
MAX_SIGNALS = 3
MAX_MESSAGE_LENGTH = 80


def load_allowlist(path: Path) -> list[int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    values = data.get("approved_issue_numbers", [])
    if not isinstance(values, list) or any(not isinstance(value, int) for value in values):
        raise ValueError("approved_issue_numbers must be a list of issue numbers")
    return values[:20]


def extract_signal(body: str | None, title: str) -> str:
    body = body or ""
    match = re.search(r"### Signal\s*(.*?)(?:\n### |\Z)", body, flags=re.DOTALL | re.IGNORECASE)
    value = match.group(1) if match else title.removeprefix(PREFIX)
    value = " ".join(value.split())
    return value[:MAX_MESSAGE_LENGTH].rstrip()


def wrap_signal(value: str, max_chars: int = 42) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in value.split():
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:2]


def fetch_approved_signals(
    owner: str,
    repo: str,
    issue_numbers: list[int],
    token: str | None = None,
) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    seen_authors: set[str] = set()
    for number in issue_numbers:
        issue = github_json(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{number}", token
        )
        title = str(issue.get("title", ""))
        author = str(issue.get("user", {}).get("login", "unknown"))
        if issue.get("pull_request") or not title.lower().startswith(PREFIX):
            continue
        if author.lower() in seen_authors:
            continue
        message = extract_signal(issue.get("body"), title)
        if not message:
            continue
        seen_authors.add(author.lower())
        signals.append({
            "author": author,
            "message": message,
            "url": str(issue.get("html_url", "")),
        })
        if len(signals) == MAX_SIGNALS:
            break
    return signals


def render_signals(signals: list[dict[str, str]], theme_name: str) -> str:
    colors = THEMES[theme_name]
    columns: list[str] = []
    if signals:
        for index, signal in enumerate(signals):
            x = 40 + index * 386
            message = wrap_signal(signal["message"])
            columns.extend([
                f'<rect x="{x}" y="75" width="8" height="66" fill="{colors[["mint", "yellow", "red"][index]]}"/>',
                svg_text(x + 24, 98, f"@{signal['author']}", "author mono"),
                *[
                    svg_text(x + 24, 126 + line_index * 21, line, "message")
                    for line_index, line in enumerate(message)
                ],
            ])
    else:
        columns.extend([
            svg_text(40, 111, "NO APPROVED SIGNALS YET", "empty mono"),
            svg_text(40, 140, "Open the channel through GitHub Issues. Messages are reviewed before broadcast.", "message"),
        ])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="180" viewBox="0 0 1200 180" role="img" aria-labelledby="title desc">
<title id="title">Naitik's moderated visitor channel</title>
<desc id="desc">Up to three approved GitHub Issue messages from profile visitors.</desc>
<style>
text{{font-family:'Arial Narrow','Helvetica Neue',Arial,sans-serif;letter-spacing:0}}
.mono{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace}}
.author{{fill:{colors['ink']};font-size:15px;font-weight:900}}.message{{fill:{colors['ink']};font-size:15px;font-weight:650}}
.empty{{fill:{colors['ink']};font-size:18px;font-weight:900}}.pulse{{animation:pulse 2.2s ease-out infinite;transform-origin:1140px 39px}}
@keyframes pulse{{0%{{transform:scale(.5);opacity:1}}100%{{transform:scale(1.8);opacity:0}}}}
@media(prefers-reduced-motion:reduce){{.pulse{{animation:none}}}}
</style>
<rect width="1200" height="180" fill="{colors['paper']}"/>
<rect x="10" y="10" width="1180" height="160" fill="{colors['paper_alt']}" stroke="{colors['line']}" stroke-width="3"/>
<rect x="24" y="24" width="1152" height="35" fill="{colors['blue']}"/>
{svg_text(40, 48, 'VISITOR CHANNEL / MODERATED', 'author mono')}
{svg_text(1155, 48, f'{len(signals):02d} SIGNALS', 'author mono', 'end')}
<circle cx="1140" cy="39" r="6" fill="{colors['red']}"/><circle cx="1140" cy="39" r="11" fill="none" stroke="{colors['red']}" stroke-width="3" class="pulse"/>
{"".join(columns)}
</svg>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="naitik-joshi")
    parser.add_argument("--repo", default="naitik-joshi")
    parser.add_argument("--allowlist", type=Path, default=ROOT / "signals-approved.json")
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    parser.add_argument("--offline", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    numbers = load_allowlist(arguments.allowlist)
    signals = [] if arguments.offline else fetch_approved_signals(
        arguments.owner,
        arguments.repo,
        numbers,
        os.environ.get("GITHUB_TOKEN"),
    )
    arguments.output.mkdir(parents=True, exist_ok=True)
    for theme_name in THEMES:
        path = arguments.output / f"community-signals-{theme_name}.svg"
        path.write_text(render_signals(signals, theme_name), encoding="utf-8")
        print(f"[signals] wrote {path}")


if __name__ == "__main__":
    main()
