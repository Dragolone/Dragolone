"""Render projects.json as SVG project cards (light + dark), stdlib only.

    python scripts/cards/make_cards.py --out dist

Text uses the viewer's system font (the same stack GitHub's UI uses), so the
cards look native. Layout is measured with Helvetica widths from metrics.json,
with a little slack because Segoe UI and SF run slightly wider.
"""

import argparse
import json
import os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 600, 236
PAD = 24
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
SLACK = 1.06

THEMES = {
    "light": {"bg": "#ffffff", "border": "#d0d7de", "fg": "#1f2328", "muted": "#59636e",
              "chip": "#f6f8fa", "chip_border": "#d0d7de", "rule": "#d8dee4", "tile_alpha": "0.14"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "fg": "#e6edf3", "muted": "#8b949e",
             "chip": "#161b22", "chip_border": "#30363d", "rule": "#21262d", "tile_alpha": "0.22"},
}
TONES = {
    "light": {"green": "#1a7f37", "amber": "#9a6700", "grey": "#59636e"},
    "dark": {"green": "#3fb950", "amber": "#d29922", "grey": "#8b949e"},
}

with open(os.path.join(HERE, "metrics.json")) as f:
    METRICS = json.load(f)


def width(text, size, bold=False):
    table = METRICS["bold" if bold else "regular"]
    return sum(table.get(ch, 0.55) for ch in text) * size * SLACK


def wrap(text, size, max_w, max_lines=2):
    lines, line = [], ""
    for word in text.split():
        cand = f"{line} {word}".strip()
        if width(cand, size) <= max_w or not line:
            line = cand
        else:
            lines.append(line)
            line = word
    lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while width(lines[-1] + "…", size) > max_w and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    return lines


def text(x, y, s, size, color, bold=False, anchor="start", extra=""):
    weight = ' font-weight="600"' if bold else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}"{weight} text-anchor="{anchor}"{extra}>{escape(s)}</text>'


def card(p, theme):
    t, tones = THEMES[theme], TONES[theme]
    out = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>']

    # Monogram tile.
    out.append(f'<rect x="{PAD}" y="20" width="40" height="40" rx="10" fill="{p["accent"]}" fill-opacity="{t["tile_alpha"]}"/>')
    out.append(text(PAD + 20, 46, p["monogram"], 16, p["accent"], bold=True, anchor="middle", extra=' letter-spacing="0.5"'))

    # Status pill, right-aligned.
    label = p["status"]["label"]
    color = tones[p["status"]["tone"]]
    pill_w = width(label, 11, bold=True) + 1.2 * len(label) + 20
    px = W - PAD - pill_w
    out.append(f'<rect x="{px:.1f}" y="21" width="{pill_w:.1f}" height="22" rx="11" fill="{color}" fill-opacity="0.13"/>')
    out.append(text(px + pill_w / 2, 36, label, 11, color, bold=True, anchor="middle", extra=' letter-spacing="1.2"'))

    # Title, shrunk if it would run into the pill.
    tx = PAD + 56
    title_w = px - 12 - tx
    size = 19
    while width(p["title"], size, bold=True) > title_w and size > 14:
        size -= 1
    out.append(text(tx, 38, p["title"], size, t["fg"], bold=True))

    # Tagline, up to two lines.
    for i, line in enumerate(wrap(p["tagline"], 13, W - tx - PAD)):
        out.append(text(tx, 60 + i * 18, line, 13, t["muted"]))

    # Metrics row.
    cols = len(p["metrics"])
    col_w = (W - 2 * PAD) / cols
    for i, (value, label) in enumerate(p["metrics"]):
        x = PAD + i * col_w
        out.append(text(x, 136, value, 22, t["fg"], bold=True))
        out.append(text(x, 156, label, 12, t["muted"]))

    out.append(f'<line x1="{PAD}" y1="174" x2="{W - PAD}" y2="174" stroke="{t["rule"]}"/>')

    # Tech chips; drop the ones that would overflow.
    x = PAD
    for tag in p["tags"]:
        w = width(tag, 12) + 20
        if x + w > W - PAD:
            break
        out.append(f'<rect x="{x:.1f}" y="188" width="{w:.1f}" height="24" rx="12" fill="{t["chip"]}" stroke="{t["chip_border"]}"/>')
        out.append(text(x + w / 2, 204, tag, 12, t["muted"], anchor="middle"))
        x += w + 8

    desc = f'{p["title"]}: {p["tagline"]}'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(desc)}" font-family="{FONT}">'
            f"<title>{escape(desc)}</title>" + "".join(out) + "</svg>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    args = ap.parse_args()
    with open(os.path.join(HERE, "projects.json")) as f:
        projects = json.load(f)
    os.makedirs(args.out, exist_ok=True)
    for p in projects:
        for theme, suffix in (("light", ""), ("dark", "-dark")):
            path = os.path.join(args.out, f"project-{p['id']}{suffix}.svg")
            with open(path, "w") as f:
                f.write(card(p, theme))
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
