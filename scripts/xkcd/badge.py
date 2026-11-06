"""Flat-square badges in the shields.io style, so live numbers can sit inline with the About Me badges."""

from html import escape

FONT = "Verdana,Geneva,DejaVu Sans,sans-serif"


def _width(text):
    # Rough Verdana 11px advances; shields pads 5px either side.
    w = 0
    for ch in text:
        if ch.isdigit():
            w += 7
        elif ch.isupper():
            w += 8
        elif ch in " .,:":
            w += 3.8
        else:
            w += 6.4
    return round(w) + 10


def badge(label, value, color="#2ea44f", label_color="#555"):
    lw, vw = _width(label), _width(value)
    w = lw + vw
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{escape(label)}: {escape(value)}">'
            f'<title>{escape(label)}: {escape(value)}</title>'
            f'<rect width="{lw}" height="20" fill="{label_color}"/><rect x="{lw}" width="{vw}" height="20" fill="{color}"/>'
            f'<g fill="#fff" font-family="{FONT}" font-size="11" text-anchor="middle">'
            f'<text x="{lw / 2:.1f}" y="14">{escape(label)}</text>'
            f'<text x="{lw + vw / 2:.1f}" y="14">{escape(value)}</text></g></svg>')
