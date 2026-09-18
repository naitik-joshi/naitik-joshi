#!/usr/bin/env python3
"""Render the KTM Project Broadcast profile artwork."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from profile_core import (
    THEMES,
    fetch_telemetry,
    load_config,
    safe,
    short_date,
    svg_text,
    write_profile_data,
)


ACCENT_MAP = {"amber": "yellow", "cyan": "blue"}


def _accent(project: dict[str, Any]) -> str:
    return ACCENT_MAP.get(project["accent"], project["accent"])


def _wrap_words(value: str, max_chars: int) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _style(colors: dict[str, str]) -> str:
    return f"""
<style>
text{{font-family:'Arial Narrow','Roboto Condensed','Helvetica Neue',Arial,sans-serif;letter-spacing:0}}
.mono{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace}}
.paper{{fill:{colors['paper']}}}.paper-alt{{fill:{colors['paper_alt']}}}
.ink{{fill:{colors['ink']}}}.muted{{fill:{colors['muted']}}}.line{{stroke:{colors['line']}}}
.outline{{fill:{colors['paper_alt']};stroke:{colors['line']};stroke-width:3}}
.shadow{{fill:{colors['shadow']}}}.red{{fill:{colors['red']}}}.blue{{fill:{colors['blue']}}}
.yellow{{fill:{colors['yellow']}}}.mint{{fill:{colors['mint']}}}.skyline{{fill:{colors['skyline']}}}
.display{{fill:{colors['ink']};font-size:66px;font-weight:950}}
.display-small{{fill:{colors['ink']};font-size:52px;font-weight:950}}
.role{{fill:{colors['ink']};font-size:17px;font-weight:800}}
.eyebrow{{fill:{colors['muted']};font-size:13px;font-weight:800}}
.label{{fill:{colors['ink']};font-size:14px;font-weight:900}}
.project-name{{fill:{colors['ink']};font-size:47px;font-weight:950}}
.project-name-mobile{{fill:{colors['ink']};font-size:38px;font-weight:950}}
.project-copy{{fill:{colors['ink']};font-size:18px;font-weight:650}}
.project-copy-mobile{{fill:{colors['ink']};font-size:16px;font-weight:650}}
.meta{{fill:{colors['muted']};font-size:13px;font-weight:800}}
.status{{fill:{colors['paper']};font-size:12px;font-weight:950}}
.number{{fill:{colors['ink']};font-size:112px;font-weight:950;opacity:.08}}
.stat{{fill:{colors['ink']};font-size:17px;font-weight:900}}
.tiny{{fill:{colors['muted']};font-size:11px;font-weight:800}}
.feature{{opacity:0;visibility:hidden;animation:featureCycle 16s infinite}}
.indicator{{opacity:.25;animation:indicatorCycle 16s infinite}}
.scene-2,.indicator-2{{animation-delay:4s}}.scene-3,.indicator-3{{animation-delay:8s}}
.scene-4,.indicator-4{{animation-delay:12s}}
.scan{{transform-origin:center;animation:scan 5s linear infinite}}
.dash{{stroke-dasharray:9 11;animation:dash 6s linear infinite}}
.pulse{{transform-origin:center;animation:pulse 2.4s ease-out infinite}}
.cursor{{animation:blink 1s steps(1) infinite}}
@keyframes featureCycle{{0%,22%{{opacity:1;visibility:visible;transform:translateY(0)}}24%,98%{{opacity:0;visibility:hidden;transform:translateY(10px)}}99%,100%{{opacity:0;visibility:hidden}}}}
@keyframes indicatorCycle{{0%,22%{{opacity:1}}24%,100%{{opacity:.25}}}}
@keyframes scan{{to{{transform:rotate(360deg)}}}}@keyframes dash{{to{{stroke-dashoffset:-80}}}}
@keyframes pulse{{0%{{transform:scale(.55);opacity:.9}}100%{{transform:scale(1.55);opacity:0}}}}
@keyframes blink{{50%{{opacity:0}}}}
@media(prefers-reduced-motion:reduce){{.feature,.indicator,.scan,.dash,.pulse,.cursor{{animation:none!important}}.feature{{opacity:0;visibility:hidden}}.scene-1{{opacity:1;visibility:visible}}.indicator{{opacity:.25}}.indicator-1{{opacity:1}}}}
</style>
""".strip()


def _defs(colors: dict[str, str]) -> str:
    return f"""
<defs>
  <pattern id="micro-grid" width="26" height="26" patternUnits="userSpaceOnUse">
    <path d="M26 0H0V26" fill="none" stroke="{colors['line']}" stroke-width="1" opacity=".055"/>
  </pattern>
  <clipPath id="stage-clip"><rect x="486" y="103" width="674" height="418"/></clipPath>
  <clipPath id="stage-clip-mobile"><rect x="34" y="267" width="652" height="438"/></clipPath>
</defs>
""".strip()


def _signal_mark(cx: int, cy: int, accent: str, scale: float = 1.0) -> str:
    r1, r2, r3 = 37 * scale, 54 * scale, 72 * scale
    return f"""
<g>
  <circle cx="{cx}" cy="{cy}" r="{r3}" fill="none" class="line" stroke-width="2" opacity=".18"/>
  <path d="M{cx} {cy-r3} A{r3} {r3} 0 0 1 {cx+r3} {cy}" fill="none" class="{accent} scan" stroke="currentColor" stroke-width="7"/>
  <circle cx="{cx}" cy="{cy}" r="{r2}" fill="none" class="line dash" stroke-width="2" opacity=".55"/>
  <circle cx="{cx}" cy="{cy}" r="{r1}" class="outline"/>
  <path d="M{cx-15} {cy+9} L{cx-4} {cy-13} L{cx+5} {cy+2} L{cx+16} {cy-18}" fill="none" class="line" stroke-width="5" stroke-linecap="square" stroke-linejoin="miter"/>
  <circle cx="{cx+16}" cy="{cy-18}" r="7" class="{accent}"/>
  <circle cx="{cx+16}" cy="{cy-18}" r="12" fill="none" class="{accent} pulse" stroke="currentColor" stroke-width="3"/>
</g>
""".strip()


def _project_art(project: dict[str, Any], x: int, y: int) -> str:
    repo = project["repo"].lower()
    accent = _accent(project)
    if "prodtag" in repo:
        bars = [26, 48, 70, 94, 54, 33, 78, 102, 64]
        items = "".join(
            f'<rect x="{x + 24 + i * 18}" y="{y + 126 - bar}" width="10" height="{bar}" class="{accent}" opacity="{.35 + i * .055:.2f}"/>'
            for i, bar in enumerate(bars)
        )
        return f'<g>{items}<path d="M{x+22} {y+138}H{x+202}" class="line" stroke-width="3"/></g>'
    if "hackathon" in repo:
        return f"""
<g fill="none" class="line" stroke-width="3">
  <path d="M{x+30} {y+40}L{x+102} {y+76}L{x+54} {y+138}L{x+156} {y+122}L{x+184} {y+54}L{x+102} {y+76}"/>
  <circle cx="{x+30}" cy="{y+40}" r="12" class="{accent}" stroke="none"/><circle cx="{x+102}" cy="{y+76}" r="17" class="blue" stroke="none"/>
  <circle cx="{x+54}" cy="{y+138}" r="10" class="mint" stroke="none"/><circle cx="{x+156}" cy="{y+122}" r="13" class="red" stroke="none"/>
  <circle cx="{x+184}" cy="{y+54}" r="9" class="yellow" stroke="none"/>
</g>
""".strip()
    if "api-escape" in repo:
        return f"""
<g fill="none" class="line" stroke-width="4">
  <rect x="{x+27}" y="{y+35}" width="58" height="44"/><rect x="{x+125}" y="{y+106}" width="58" height="44"/>
  <path d="M{x+85} {y+57}H{x+144}V{x+106}"/><path d="M{x+125} {y+128}H{x+66}V{x+79}"/>
  <path d="M{x+132} {y+98}L{x+144} {y+106}L{x+156} {y+98}"/><path d="M{x+78} {y+87}L{x+66} {y+79}L{x+54} {y+87}"/>
  <circle cx="{x+144}" cy="{y+57}" r="10" class="{accent}" stroke="none"/><circle cx="{x+66}" cy="{y+128}" r="10" class="red" stroke="none"/>
</g>
""".strip()
    return f"""
<g>
  <rect x="{x+22}" y="{y+32}" width="170" height="122" class="outline"/>
  <rect x="{x+22}" y="{y+32}" width="170" height="25" class="{accent}"/>
  <circle cx="{x+38}" cy="{y+45}" r="4" class="paper"/><circle cx="{x+52}" cy="{y+45}" r="4" class="paper"/>
  <path d="M{x+47} {y+82}H{x+166}M{x+47} {y+103}H{x+142}M{x+47} {y+124}H{x+155}" class="line" stroke-width="5"/>
  <path d="M{x+158} {y+127}l20 20m0-20l-20 20" class="red" stroke="currentColor" stroke-width="6"/>
</g>
""".strip()


def _scene(project: dict[str, Any], signal: dict[str, Any], index: int, mobile: bool = False) -> str:
    accent = _accent(project)
    number = f"0{index}"
    if mobile:
        name_class, copy_class = "project-name-mobile", "project-copy-mobile"
        name_y, status_y, copy_y = 342, 386, 441
        line_gap, max_chars = 24, 52
        art = _project_art(project, 430, 452)
        meta_y = 626
        number_x, number_y = 620, 378
        text_x = 64
    else:
        name_class, copy_class = "project-name", "project-copy"
        name_y, status_y, copy_y = 205, 250, 318
        line_gap, max_chars = 27, 34
        art = _project_art(project, 916, 285)
        meta_y = 472
        number_x, number_y = 1106, 230
        text_x = 526
    status_width = min(275, 26 + len(project["status"]) * 8)
    lines = _wrap_words(project["summary"], max_chars)[:3]
    copy = "\n".join(
        svg_text(text_x, copy_y + line_gap * offset, line, copy_class)
        for offset, line in enumerate(lines)
    )
    stars = signal.get("stars", 0)
    forks = signal.get("forks", 0)
    updated = short_date(signal.get("pushed_date", "unknown"))
    return f"""
<g class="feature scene-{index}">
  {svg_text(number_x, number_y, number, 'number', 'end')}
  {svg_text(text_x, name_y, project['name'], name_class)}
  <rect x="{text_x}" y="{status_y-19}" width="{status_width}" height="27" class="{accent}"/>
  {svg_text(text_x+12, status_y, project['status'], 'status')}
  {copy}
  {svg_text(text_x, meta_y, f"{project['stack']}  /  {signal.get('language', 'Mixed')}", 'meta mono')}
  {svg_text(text_x, meta_y+25, f"ST {stars}  /  FK {forks}  /  UPDATED {updated}", 'meta mono')}
  {art}
</g>
""".strip()


def _project_index(projects: list[dict[str, Any]], mobile: bool = False) -> str:
    parts: list[str] = []
    if mobile:
        for index, project in enumerate(projects, start=1):
            x = 50 + (index - 1) * 155
            accent = _accent(project)
            parts.extend([
                f'<rect x="{x}" y="670" width="143" height="7" class="{accent} indicator indicator-{index}"/>',
                svg_text(x, 695, f"0{index}", "tiny mono"),
            ])
    else:
        for index, project in enumerate(projects, start=1):
            y = 348 + (index - 1) * 46
            accent = _accent(project)
            parts.extend([
                f'<rect x="48" y="{y-24}" width="318" height="38" class="paper-alt line" stroke-width="2"/>',
                f'<rect x="48" y="{y-24}" width="8" height="38" class="{accent} indicator indicator-{index}"/>',
                svg_text(70, y, f"0{index}", "label mono"),
                svg_text(113, y, project["name"], "label"),
                f'<rect x="340" y="{y-10}" width="8" height="8" class="{accent} indicator indicator-{index}"/>',
            ])
    return "\n".join(parts)


def _skyline(width: int, baseline: int, mobile: bool = False) -> str:
    if mobile:
        buildings = [(10, 54), (74, 88), (137, 63), (203, 104), (278, 72), (352, 91), (425, 58), (491, 111), (568, 76), (636, 96)]
        bwidth = 62
    else:
        buildings = [(0, 45), (66, 76), (132, 52), (198, 92), (264, 64), (330, 108), (396, 59), (462, 82), (528, 48), (594, 96), (660, 69), (726, 113), (792, 58), (858, 88), (924, 51), (990, 103), (1056, 68), (1122, 91)]
        bwidth = 58
    parts = ['<g class="skyline" opacity=".9">']
    for i, (x, height) in enumerate(buildings):
        width_now = bwidth if x + bwidth <= width else width - x
        parts.append(f'<rect x="{x}" y="{baseline-height}" width="{width_now}" height="{height}"/>')
        if i % 3 == 1:
            parts.append(f'<rect x="{x+12}" y="{baseline-height+16}" width="7" height="7" class="yellow"/>')
    if not mobile:
        parts.extend([
            f'<path d="M170 {baseline}V{baseline-78}L226 {baseline-121}L282 {baseline-78}V{baseline}Z"/>',
            f'<path d="M185 {baseline-93}L226 {baseline-128}L267 {baseline-93}Z"/>',
            f'<line x1="226" y1="{baseline-128}" x2="226" y2="{baseline-145}" class="line" stroke-width="5"/>',
            f'<path d="M915 {baseline}Q974 {baseline-88} 1033 {baseline}Z"/>',
            f'<rect x="970" y="{baseline-106}" width="8" height="28"/>',
            f'<circle cx="974" cy="{baseline-112}" r="6" class="red"/>',
        ])
    parts.append("</g>")
    return "\n".join(parts)


def render_desktop_svg(config: dict[str, Any], telemetry: dict[str, Any], theme_name: str) -> str:
    colors = THEMES[theme_name]
    identity = config["identity"]
    projects = config["projects"]
    scenes = "\n".join(
        _scene(project, telemetry.get("projects", {}).get(project["repo"], {}), index)
        for index, project in enumerate(projects, start=1)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="640" viewBox="0 0 1200 640" role="img" aria-labelledby="title desc">
<title id="title">Naitik Joshi - KTM Project Broadcast</title>
<desc id="desc">Animated profile poster broadcasting four selected software projects from Kathmandu.</desc>
{_defs(colors)}
{_style(colors)}
<rect width="1200" height="640" class="paper"/><rect width="1200" height="640" fill="url(#micro-grid)"/>
<rect x="18" y="18" width="1164" height="604" fill="none" class="line" stroke-width="3"/>
<rect x="30" y="29" width="1140" height="46" class="paper-alt line" stroke-width="2"/>
<rect x="30" y="29" width="248" height="46" class="red"/>
{svg_text(49, 59, 'LIVE FROM KATHMANDU', 'label mono')}
{svg_text(301, 59, identity['node'], 'label mono')}
{svg_text(1148, 59, f"{telemetry['public_repos']} REPOS  /  {telemetry['stars']} STARS  /  {telemetry['followers']} FOLLOWERS", 'label mono', 'end')}
{_skyline(1200, 597)}
{svg_text(48, 142, 'NAITIK', 'display')}
{svg_text(48, 207, 'JOSHI', 'display')}
<rect x="51" y="223" width="309" height="8" class="blue"/>
{svg_text(49, 265, identity['role'], 'role')}
{svg_text(49, 294, identity['tagline'].upper(), 'eyebrow mono')}
{svg_text(49, 317, 'SELECTED WORK / AUTO-CYCLING', 'tiny mono')}
{_project_index(projects)}
<rect x="498" y="115" width="674" height="418" class="shadow"/>
<rect x="486" y="103" width="674" height="418" class="outline"/>
<g clip-path="url(#stage-clip)">
  <rect x="486" y="103" width="674" height="48" class="blue"/>
  {svg_text(510, 134, 'PROJECT TRANSMISSION', 'status mono')}
  {svg_text(1136, 134, 'AUTO / 16 SEC LOOP', 'status mono', 'end')}
  <path d="M511 286H897" class="line dash" stroke-width="3" opacity=".16"/>
  {scenes}
</g>
<rect x="30" y="552" width="1140" height="49" class="paper-alt line" stroke-width="2"/>
{svg_text(52, 583, 'naitik@ktm:~$', 'label mono')}
{svg_text(218, 583, 'broadcast --selected-work', 'role mono')}
<rect x="450" y="567" width="10" height="19" class="mint cursor"/>
{svg_text(1148, 583, f"LATEST / {telemetry['latest_repo']} / {telemetry['latest_repo_date']}", 'label mono', 'end')}
</svg>
"""


def render_mobile_svg(config: dict[str, Any], telemetry: dict[str, Any], theme_name: str) -> str:
    colors = THEMES[theme_name]
    identity = config["identity"]
    projects = config["projects"]
    scenes = "\n".join(
        _scene(project, telemetry.get("projects", {}).get(project["repo"], {}), index, mobile=True)
        for index, project in enumerate(projects, start=1)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="960" viewBox="0 0 720 960" role="img" aria-labelledby="title desc">
<title id="title">Naitik Joshi - KTM Project Broadcast</title>
<desc id="desc">Mobile profile poster broadcasting four selected software projects from Kathmandu.</desc>
{_defs(colors)}
{_style(colors)}
<rect width="720" height="960" class="paper"/><rect width="720" height="960" fill="url(#micro-grid)"/>
<rect x="14" y="14" width="692" height="932" fill="none" class="line" stroke-width="3"/>
<rect x="27" y="28" width="666" height="46" class="paper-alt line" stroke-width="2"/>
<rect x="27" y="28" width="232" height="46" class="red"/>
{svg_text(44, 58, 'LIVE FROM KATHMANDU', 'label mono')}
{svg_text(674, 58, identity['node'], 'label mono', 'end')}
{svg_text(34, 139, 'NAITIK JOSHI', 'display-small')}
<rect x="36" y="161" width="326" height="8" class="blue"/>
{svg_text(35, 204, identity['role'], 'role')}
{svg_text(35, 235, identity['tagline'].upper(), 'eyebrow mono')}
<rect x="45" y="278" width="652" height="438" class="shadow"/>
<rect x="34" y="267" width="652" height="438" class="outline"/>
<g clip-path="url(#stage-clip-mobile)">
  <rect x="34" y="267" width="652" height="45" class="blue"/>
  {svg_text(55, 296, 'PROJECT TRANSMISSION', 'status mono')}
  {svg_text(664, 296, '16 SEC LOOP', 'status mono', 'end')}
  {scenes}
  {_project_index(projects, mobile=True)}
</g>
<rect x="34" y="739" width="652" height="61" class="yellow line" stroke-width="3"/>
{svg_text(54, 766, 'PUBLIC SIGNAL', 'tiny mono')}
{svg_text(54, 787, f"{telemetry['public_repos']} REPOS / {telemetry['stars']} STARS / {telemetry['followers']} FOLLOWERS", 'label mono')}
{svg_text(665, 787, 'NPT +05:45', 'label mono', 'end')}
{_skyline(720, 914, mobile=True)}
<rect x="26" y="866" width="668" height="54" class="paper-alt line" stroke-width="2"/>
{svg_text(46, 899, 'naitik@ktm:~$', 'label mono')}
{svg_text(674, 899, 'broadcast --work', 'label mono', 'end')}
</svg>
"""


def render_svg(config: dict[str, Any], telemetry: dict[str, Any], theme_name: str) -> str:
    """Compatibility entry point for the desktop renderer."""
    return render_desktop_svg(config, telemetry, theme_name)


def generate(config_path: Path, output_dir: Path, offline: bool = False) -> list[Path]:
    config = load_config(config_path)
    telemetry = fetch_telemetry(config, offline=offline)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = [write_profile_data(output_dir, config, telemetry)]
    for theme_name in THEMES:
        desktop = output_dir / f"profile-{theme_name}.svg"
        mobile = output_dir / f"profile-{theme_name}-mobile.svg"
        desktop.write_text(render_desktop_svg(config, telemetry, theme_name), encoding="utf-8")
        mobile.write_text(render_mobile_svg(config, telemetry, theme_name), encoding="utf-8")
        outputs.extend([desktop, mobile])
        print(f"[profile] wrote {desktop}")
        print(f"[profile] wrote {mobile}")
    return outputs
