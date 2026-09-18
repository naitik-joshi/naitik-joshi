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
.status-on-dark{{fill:#F4F0E8;font-size:12px;font-weight:950}}
.status-on-light{{fill:#111318;font-size:12px;font-weight:950}}
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


def _project_art(project: dict[str, Any], x: int, y: int) -> str:
    repo = project["repo"].lower()
    accent = _accent(project)
    frame = (
        f'<rect x="{x+8}" y="{y+18}" width="204" height="150" '
        'fill="none" class="line" stroke-width="3"/>'
    )
    if "prodtag" in repo:
        bars = [22, 41, 66, 88, 47, 31, 73, 94, 58]
        items = "".join(
            f'<rect x="{x + 25 + i * 18}" y="{y + 139 - bar}" width="10" height="{bar}" class="{accent}" opacity="{.42 + i * .05:.2f}"/>'
            for i, bar in enumerate(bars)
        )
        return f'<g>{frame}{items}<path d="M{x+23} {y+143}H{x+197}" class="line" stroke-width="3"/></g>'
    if "hackathon" in repo:
        return f"""
<g>
  {frame}
  <path d="M{x+35} {y+51}L{x+106} {y+82}L{x+62} {y+139}L{x+162} {y+127}L{x+184} {y+61}L{x+106} {y+82}" fill="none" class="line" stroke-width="3"/>
  <circle cx="{x+35}" cy="{y+51}" r="10" class="{accent}"/><circle cx="{x+106}" cy="{y+82}" r="15" class="blue"/>
  <circle cx="{x+62}" cy="{y+139}" r="9" class="mint"/><circle cx="{x+162}" cy="{y+127}" r="11" class="red"/>
  <circle cx="{x+184}" cy="{y+61}" r="8" class="yellow"/>
</g>
""".strip()
    if "api-escape" in repo:
        return f"""
<g>
  {frame}
  <rect x="{x+27}" y="{y+46}" width="52" height="38" fill="none" class="line" stroke-width="3"/>
  <rect x="{x+141}" y="{y+46}" width="52" height="38" fill="none" class="line" stroke-width="3"/>
  <rect x="{x+84}" y="{y+111}" width="52" height="38" fill="none" class="line" stroke-width="3"/>
  <path d="M{x+79} {y+65}H{x+141}M{x+167} {y+84}V{y+103}H{x+110}V{y+111}" fill="none" class="line" stroke-width="3"/>
  <circle cx="{x+110}" cy="{y+65}" r="7" class="{accent}"/><circle cx="{x+167}" cy="{y+103}" r="7" class="yellow"/>
  <circle cx="{x+110}" cy="{y+130}" r="7" class="red"/>
</g>
""".strip()
    return f"""
<g>
  {frame}
  <rect x="{x+24}" y="{y+37}" width="172" height="112" fill="none" class="line" stroke-width="3"/>
  <rect x="{x+24}" y="{y+37}" width="172" height="24" class="{accent}"/>
  <circle cx="{x+39}" cy="{y+49}" r="4" class="paper"/><circle cx="{x+52}" cy="{y+49}" r="4" class="paper"/>
  <path d="M{x+45} {y+86}H{x+172}M{x+45} {y+107}H{x+149}M{x+45} {y+128}H{x+161}" class="line" stroke-width="5"/>
  <path d="M{x+163} {y+117}l17 17m0-17l-17 17" fill="none" stroke="#FF5A5F" stroke-width="6"/>
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
    status_class = "status-on-dark" if accent in {"blue", "red"} else "status-on-light"
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
  {svg_text(text_x+12, status_y, project['status'], status_class)}
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
  {svg_text(510, 134, 'PROJECT TRANSMISSION', 'status-on-dark mono')}
  {svg_text(1136, 134, 'AUTO / 16 SEC LOOP', 'status-on-dark mono', 'end')}
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
  {svg_text(55, 296, 'PROJECT TRANSMISSION', 'status-on-dark mono')}
  {svg_text(664, 296, '16 SEC LOOP', 'status-on-dark mono', 'end')}
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


def render_quote_svg(theme_name: str) -> str:
    colors = THEMES[theme_name]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="176" viewBox="0 0 1200 176" role="img" aria-labelledby="title desc">
<title id="title">Naitik Joshi operating principle</title>
<desc id="desc">If the platform says it cannot be done, I look for the part it forgot to forbid.</desc>
<style>
text{{font-family:'Arial Narrow','Helvetica Neue',Arial,sans-serif;letter-spacing:0}}
.mono{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace}}
.quote{{fill:{colors['ink']};font-size:28px;font-weight:900}}
.label{{fill:{colors['ink']};font-size:12px;font-weight:900}}
</style>
<rect width="1200" height="176" fill="{colors['paper']}"/>
<rect x="12" y="12" width="1176" height="152" fill="{colors['paper_alt']}" stroke="{colors['line']}" stroke-width="3"/>
<rect x="28" y="28" width="150" height="120" fill="{colors['red']}"/>
<text x="103" y="120" fill="#111318" font-family="Georgia,serif" font-size="126" font-weight="900" text-anchor="middle">&quot;</text>
<text x="211" y="58" class="label mono">OPERATING PRINCIPLE / KTM 05:45</text>
<text x="211" y="100" class="quote">IF THE PLATFORM SAYS IT CAN'T BE DONE,</text>
<text x="211" y="136" class="quote">I LOOK FOR THE PART IT FORGOT TO FORBID.</text>
<rect x="1118" y="28" width="42" height="42" fill="{colors['blue']}"/>
<rect x="1139" y="49" width="21" height="99" fill="{colors['yellow']}"/>
</svg>
"""


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
        quote = output_dir / f"quote-{theme_name}.svg"
        quote.write_text(render_quote_svg(theme_name), encoding="utf-8")
        outputs.extend([desktop, mobile, quote])
        print(f"[profile] wrote {desktop}")
        print(f"[profile] wrote {mobile}")
        print(f"[profile] wrote {quote}")
    return outputs
