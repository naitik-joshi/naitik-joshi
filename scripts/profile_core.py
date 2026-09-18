#!/usr/bin/env python3
"""Shared configuration, telemetry, and SVG helpers for profile artwork."""

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
        "paper": "#101217",
        "paper_alt": "#171A21",
        "ink": "#F4F0E8",
        "muted": "#AAA7A0",
        "line": "#F4F0E8",
        "shadow": "#050608",
        "red": "#FF5A5F",
        "blue": "#3B6CFF",
        "yellow": "#FFD447",
        "mint": "#63E6BE",
        "skyline": "#242936",
    },
    "light": {
        "paper": "#F5F0E7",
        "paper_alt": "#FFFCF6",
        "ink": "#111318",
        "muted": "#5E6066",
        "line": "#111318",
        "shadow": "#111318",
        "red": "#E84A50",
        "blue": "#2456E8",
        "yellow": "#F3BF25",
        "mint": "#26B892",
        "skyline": "#D7D0C5",
    },
}

PROJECT_POSITIONS = {"northwest", "southwest", "northeast", "southeast"}
REQUIRED_IDENTITY = {"name", "role", "location", "timezone", "node", "tagline"}
REQUIRED_PROJECT = {"name", "repo", "status", "stack", "summary", "position", "accent"}


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    missing_root = {"username", "identity", "projects", "fallback_telemetry"} - set(config)
    if missing_root:
        raise ValueError(f"Missing profile fields: {', '.join(sorted(missing_root))}")
    missing_identity = REQUIRED_IDENTITY - set(config["identity"])
    if missing_identity:
        raise ValueError(f"Missing identity fields: {', '.join(sorted(missing_identity))}")
    projects = config.get("projects", [])
    if len(projects) != 4:
        raise ValueError("The broadcast layout requires exactly four projects")
    positions = {project.get("position") for project in projects}
    if positions != PROJECT_POSITIONS:
        raise ValueError("Each project position must be used exactly once")
    for project in projects:
        missing = REQUIRED_PROJECT - set(project)
        if missing:
            raise ValueError(
                f"Project {project.get('name', '<unknown>')} is missing: "
                f"{', '.join(sorted(missing))}"
            )
        if project["accent"] not in {"red", "blue", "yellow", "mint", "amber", "cyan"}:
            raise ValueError(f"Unsupported accent: {project['accent']}")
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
        command = [
            "curl", "--fail", "--silent", "--show-error", "--max-time", "15",
            "--header", f"Accept: {headers['Accept']}",
            "--header", f"User-Agent: {headers['User-Agent']}",
            "--header", f"X-GitHub-Api-Version: {headers['X-GitHub-Api-Version']}",
        ]
        if token:
            command.extend(["--header", f"Authorization: Bearer {token}"])
        command.append(url)
        result = subprocess.run(command, check=True, capture_output=True, text=True)
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
            f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed&type=owner",
            token,
        )
    except (urllib.error.URLError, subprocess.SubprocessError, TimeoutError, ValueError, OSError) as exc:
        print(f"[profile] GitHub telemetry unavailable: {exc}", file=sys.stderr)
        return fallback

    owned = [repo for repo in repos if not repo.get("fork")]
    project_repos = [
        repo for repo in owned
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
            "open_issues": int(repo.get("open_issues_count", saved.get("open_issues", 0))),
            "pushed_date": str(repo.get("pushed_at", saved.get("pushed_date", "unknown")))[:10],
        }

    return {
        "public_repos": user.get("public_repos", fallback["public_repos"]),
        "followers": user.get("followers", fallback["followers"]),
        "stars": sum(int(repo.get("stargazers_count", 0)) for repo in owned),
        "latest_repo": latest.get("name", fallback["latest_repo"]),
        "latest_repo_date": str(latest.get("pushed_at", fallback["latest_repo_date"]))[:10],
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


def short_date(value: Any) -> str:
    text = str(value)
    return text[5:] if len(text) == 10 else text


def write_profile_data(
    output_dir: Path,
    config: dict[str, Any],
    telemetry: dict[str, Any],
) -> Path:
    path = output_dir / "profile-data.json"
    data = {
        "identity": config["identity"],
        "current_build": config.get("current_build"),
        "public": telemetry,
        "projects": [
            {**project, "signal": telemetry.get("projects", {}).get(project["repo"], {})}
            for project in config["projects"]
        ],
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path
