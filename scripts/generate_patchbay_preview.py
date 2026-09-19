"""Generate a script-free animated README teaser for the actual Patchbay app."""
from pathlib import Path

def render(mobile=False):
    width, height = (600, 370) if mobile else (1100, 270)
    y = 177 if mobile else 65
    xs = [32, 222, 412] if mobile else [490, 690, 890]
    size = 156
    out = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">KTM Patchbay: open the interactive JSON and text workbench</title>
<desc id="desc">An animated example sends JSON through a transformation circuit into CSV. Click the preview to open the working tool on GitHub Pages.</desc>
<style>text{{font-family:monospace;fill:#e7ebed}}.muted{{fill:#9ca7b7}}.packet{{animation:pulse 3s infinite}}@keyframes pulse{{0%,100%{{opacity:.4}}50%{{opacity:1}}}}@media(prefers-reduced-motion:reduce){{.packet{{animation:none}}.moving{{display:none}}}}</style>
<defs><pattern id="grid" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".8" fill="#303745"/></pattern></defs>
<rect width="100%" height="100%" rx="6" fill="#0d1117"/>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="5" fill="url(#grid)" stroke="#46505e"/>
<path d="M1 33H{width-1}" stroke="#46505e"/>
<circle cx="20" cy="17" r="4" fill="#ff6569"/><circle cx="35" cy="17" r="4" fill="#ffcf58"/><circle cx="50" cy="17" r="4" fill="#71e3ba"/>
<text x="72" y="22" font-size="11" class="muted">NAITIK'S OPEN CIRCUIT LAB</text>
<text x="{width-20}" y="22" text-anchor="end" font-size="11" class="muted">02 / EXPERIMENT</text>
<text x="30" y="83" font-size="{32 if mobile else 37}" font-weight="700">KTM <tspan fill="#ff6569">//</tspan> PATCHBAY</text>
<text x="32" y="112" font-size="15" class="muted">Small modules. Useful transformations.</text>
''']
    if not mobile:
        out.append('<text x="32" y="142" font-size="14" class="muted">JSON / TEXT / YOUR BROWSER</text>')
    by=129 if mobile else 173
    out.append(f'<rect x="32" y="{by}" width="220" height="32" fill="#71e3ba"/><text x="48" y="{by+21}" style="fill:#0d1117" font-size="14" font-weight="700">OPEN THE WORKBENCH &#8599;</text>')
    for i,(x,label,color) in enumerate(zip(xs,['INPUT','TRANSFORM','OUTPUT'],['#ff6569','#ffcf58','#71e3ba'])):
        out.append(f'<rect x="{x+4}" y="{y+5}" width="{size}" height="139" fill="#05070a"/><rect x="{x}" y="{y}" width="{size}" height="139" rx="3" fill="#191e27" stroke="#46505e"/><path d="M{x} {y+1}h{size}" stroke="{color}" stroke-width="3"/><text x="{x+13}" y="{y+24}" font-size="13" style="fill:{color}" font-weight="700">{label}</text><path d="M{x} {y+36}h{size}" stroke="#343e4b"/>')
        if i==0:
            out.append(f'<text x="{x+14}" y="{y+65}" font-size="13">[{{"city":"KTM",</text><text x="{x+14}" y="{y+87}" font-size="13"> "offset":545}}]</text><text x="{x+14}" y="{y+122}" font-size="11" class="muted">JSON PAYLOAD</text>')
        elif i==1:
            for j,h in enumerate([14,25,39,22,46,33,20,35]):
                out.append(f'<rect class="packet" x="{x+15+j*16}" y="{y+90-h}" width="9" height="{h}" fill="{color}" style="animation-delay:{j*.14}s"/>')
            out.append(f'<text x="{x+14}" y="{y+122}" font-size="11" class="muted">PARSE / SELECT / CSV</text>')
        else:
            out.append(f'<text x="{x+14}" y="{y+65}" font-size="14">city,offset</text><text x="{x+14}" y="{y+88}" font-size="14" style="fill:{color}">KTM,545</text><text x="{x+14}" y="{y+122}" font-size="11" class="muted">CSV RESULT</text>')
        if i<2:
            start=x+size;end=xs[i+1];cy=y+69
            path=f'M{start} {cy}H{end}'
            out.append(f'<path d="{path}" stroke="{color}" stroke-width="2"/><circle cx="{start}" cy="{cy}" r="4" fill="#0d1117" stroke="{color}" stroke-width="2"/><circle cx="{end}" cy="{cy}" r="4" fill="#0d1117" stroke="{color}" stroke-width="2"/><circle class="moving" r="4" fill="{color}"><animateMotion dur="1.8s" begin="{i*.9}s" repeatCount="indefinite" path="{path}"/></circle>')
    out.append(f'<path d="M20 {height-39}H{width-20}" stroke="#343e4b"/><text x="32" y="{height-16}" font-size="12" class="muted">ANIMATED PREVIEW / FULL TOOL ON GITHUB PAGES</text><circle cx="{width-30}" cy="{height-20}" r="4" fill="#71e3ba"/></svg>')
    return ''.join(out)

if __name__ == '__main__':
    import sys
    root=Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=True)
    for mobile in (False,True):
        (root / ('patchbay-preview-mobile.svg' if mobile else 'patchbay-preview.svg')).write_text(render(mobile))
