"""Hand-drawn SVG charts in the style of chart.xkcd (the look of star-history.com).

Pure stdlib. If fontTools is installed, the embedded xkcd font is subset to the
glyphs each chart uses (~180 KB -> ~15 KB) and text is measured exactly.
"""

import base64
import bisect
import io
import logging
import math
import os
from datetime import datetime, timedelta
from html import escape

PALETTE = ["#dd4528", "#28a3dd", "#f3db52", "#ed84b5", "#4ab74e", "#9179c0", "#8e6d5a", "#f19839", "#949494"]

THEMES = {
    "light": {"bg": "#ffffff", "fg": "#000000", "muted": "#777777"},
    "dark": {"bg": "#0d1117", "fg": "#e6edf3", "muted": "#8b949e"},
}

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "xkcd-script.woff")


class Font:
    def __init__(self, path=FONT_PATH):
        self.path = path
        with open(path, "rb") as f:
            self.raw = f.read()
        try:
            from fontTools.ttLib import TTFont
        except ImportError:
            self.tt = None
            return
        self.tt = TTFont(path)
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]
        self.upm = self.tt["head"].unitsPerEm

    def width(self, text, size):
        if self.tt is None:
            return len(text) * size * 0.55
        units = 0
        for ch in text:
            glyph = self.cmap.get(ord(ch))
            units += self.hmtx[glyph][0] if glyph else self.upm * 0.5
        return units * size / self.upm

    def css(self, chars):
        data = self.raw
        if self.tt is not None:
            from fontTools import subset
            from fontTools.ttLib import TTFont

            logging.getLogger("fontTools.subset").setLevel(logging.ERROR)
            opts = subset.Options()
            opts.flavor = "woff"
            sub = subset.Subsetter(opts)
            sub.populate(text="".join(sorted(chars)) + " ")
            font = TTFont(self.path)
            sub.subset(font)
            buf = io.BytesIO()
            font.save(buf)
            data = buf.getvalue()
        b64 = base64.b64encode(data).decode()
        return f'@font-face{{font-family:"xkcd";src:url(data:font/woff;base64,{b64}) format("woff");}}'


_FONT = None


def default_font():
    global _FONT
    if _FONT is None:
        _FONT = Font()
    return _FONT


class Canvas:
    def __init__(self, width, height, theme, font):
        self.w, self.h = width, height
        self.t = THEMES[theme]
        self.font = font
        self.parts = []
        self.chars = set()

    def text(self, x, y, s, size=16, anchor="start", color=None, bold=False, rotate=None, baseline="auto"):
        s = str(s)
        self.chars.update(s)
        attrs = f'font-size="{size}" text-anchor="{anchor}" fill="{color or self.t["fg"]}"'
        if bold:
            attrs += ' font-weight="bold"'
        if baseline != "auto":
            attrs += f' dominant-baseline="{baseline}"'
        if rotate is not None:
            pos = f'transform="translate({x:.1f},{y:.1f}) rotate({rotate})"'
        else:
            pos = f'x="{x:.1f}" y="{y:.1f}"'
        self.parts.append(f"<text {pos} {attrs}>{escape(s)}</text>")

    def path(self, d, stroke=None, width=3, fill="none", wobble=True, extra=""):
        flt = ' filter="url(#xkcdify)"' if wobble else ""
        self.parts.append(
            f'<path d="{d}" fill="{fill}" stroke="{stroke or self.t["fg"]}" stroke-width="{width}"'
            f' stroke-linecap="round" stroke-linejoin="round"{flt}{extra}/>'
        )

    def rect(self, x, y, w, h, fill, stroke=None, width=2, rx=2, wobble=True):
        flt = ' filter="url(#xkcdify)"' if wobble else ""
        stroke_attr = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
        self.parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" rx="{rx}"'
            f' fill="{fill}"{stroke_attr}{flt}/>'
        )

    def circle(self, x, y, r, fill):
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" filter="url(#xkcdify)"/>')

    def render(self, desc=""):
        w, h = self.w, self.h
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"'
            f' font-family="xkcd, \'Comic Sans MS\', cursive" role="img">'
            f"<title>{escape(desc)}</title>"
            f"<style>{self.font.css(self.chars)}</style>"
            f'<defs><filter id="xkcdify" filterUnits="userSpaceOnUse" x="-10" y="-10" width="{w + 20}" height="{h + 20}">'
            '<feTurbulence type="fractalNoise" baseFrequency="0.05" result="noise"/>'
            '<feDisplacementMap scale="5" xChannelSelector="R" yChannelSelector="G" in="SourceGraphic" in2="noise"/>'
            "</filter></defs>"
            f'<rect width="{w}" height="{h}" fill="{self.t["bg"]}"/>'
            + "".join(self.parts)
            + "</svg>"
        )


# ---------------------------------------------------------------- scales & ticks


def _tick_step(lo, hi, count):
    step0 = abs(hi - lo) / max(count, 1)
    step1 = 10 ** math.floor(math.log10(step0))
    err = step0 / step1
    if err >= math.sqrt(50):
        step1 *= 10
    elif err >= math.sqrt(10):
        step1 *= 5
    elif err >= math.sqrt(2):
        step1 *= 2
    return step1


def nice_ticks(lo, hi, count=5, integer=True):
    if hi <= lo:
        hi = lo + 1
    step = _tick_step(lo, hi, count)
    if integer:
        step = max(step, 1)
    lo2, hi2 = math.floor(lo / step) * step, math.ceil(hi / step) * step
    n = int(round((hi2 - lo2) / step))
    return [lo2 + i * step for i in range(n + 1)]


def fmt_num(v):
    for div, suffix in ((1e6, "M"), (1e3, "K")):
        if abs(v) >= div:
            return f"{v / div:.1f}".rstrip("0").rstrip(".") + suffix
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:.1f}"


def _add_months(d, n):
    m = d.month - 1 + n
    return d.replace(year=d.year + m // 12, month=m % 12 + 1, day=1)


def time_ticks(t0, t1, max_ticks=6):
    """Calendar-aligned ticks between t0 and t1, labelled like star-history."""
    day0 = t0.replace(hour=0, minute=0, second=0, microsecond=0)
    options = [("day", 1), ("day", 2), ("week", 1), ("week", 2), ("month", 1), ("month", 2), ("month", 3),
               ("month", 6), ("year", 1), ("year", 2), ("year", 5)]
    for unit, step in options:
        if unit == "day":
            cur, nxt = day0, lambda d: d + timedelta(days=step)
        elif unit == "week":
            cur, nxt = day0 - timedelta(days=day0.weekday()), lambda d: d + timedelta(weeks=step)
        elif unit == "month":
            cur = day0.replace(day=1)
            cur = _add_months(cur, -((cur.month - 1) % step))
            nxt = lambda d: _add_months(d, step)
        else:
            cur = day0.replace(month=1, day=1)
            cur = cur.replace(year=cur.year - cur.year % step)
            nxt = lambda d: d.replace(year=d.year + step)
        ticks = []
        while cur <= t1:
            if cur >= t0:
                ticks.append(cur)
            cur = nxt(cur)
        if len(ticks) <= max_ticks:
            break
    years = {d.year for d in ticks}
    labels = []
    for i, d in enumerate(ticks):
        if unit in ("day", "week"):
            labels.append(f"{d:%b} {d.day}")
        elif unit == "month" and step < 3:
            name = f"{d:%B}" if len(ticks) <= 4 else f"{d:%b}"
            labels.append(f"{d:%b} {d.year}" if len(years) > 1 and (d.month == 1 or i == 0) else name)
        elif unit == "month":
            labels.append(f"{d:%b} {d.year}")
        else:
            labels.append(f"{d.year}")
    return ticks, labels


def monotone_path(pts):
    """d3.curveMonotoneX as an SVG path (no overshoot on cumulative data)."""
    if len(pts) == 1:
        return f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    n = len(pts)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) if xs[i + 1] != xs[i] else 0.0 for i in range(n - 1)]
    m = [0.0] * n
    sign = lambda v: -1 if v < 0 else 1
    for i in range(1, n - 1):
        h0, h1 = xs[i] - xs[i - 1], xs[i + 1] - xs[i]
        s0, s1 = d[i - 1], d[i]
        if h0 + h1 == 0:
            continue
        p = (s0 * h1 + s1 * h0) / (h0 + h1)
        m[i] = (sign(s0) + sign(s1)) * min(abs(s0), abs(s1), 0.5 * abs(p))
    m[0] = (3 * d[0] - m[1]) / 2 if n > 2 else d[0]
    m[-1] = (3 * d[-1] - m[-2]) / 2 if n > 2 else d[-1]
    out = [f"M{xs[0]:.1f},{ys[0]:.1f}"]
    for i in range(n - 1):
        dx = (xs[i + 1] - xs[i]) / 3
        out.append(
            f"C{xs[i] + dx:.1f},{ys[i] + dx * m[i]:.1f} {xs[i + 1] - dx:.1f},{ys[i + 1] - dx * m[i + 1]:.1f}"
            f" {xs[i + 1]:.1f},{ys[i + 1]:.1f}"
        )
    return "".join(out)


# ---------------------------------------------------------------- shared pieces


def _header(c, title, subtitle):
    """Draw title + optional muted subtitle; return where the plot may start."""
    if not title:
        return 24
    c.text(c.w / 2, 32, title, size=21, anchor="middle", bold=True)
    if not subtitle:
        return 58
    c.text(c.w / 2, 54, subtitle, size=15, anchor="middle", color=c.t["muted"])
    return 76


class _Plot:
    """Title, axis labels, axes and y ticks; gives back the plot rectangle."""

    def __init__(self, c, y_max, title, subtitle, x_label, y_label, footer):
        self.c = c
        self.y_ticks = nice_ticks(0, max(y_max, 1), 5)
        self.y_top = self.y_ticks[-1]
        tick_w = max(c.font.width(fmt_num(v), 16) for v in self.y_ticks)
        self.left = (34 if y_label else 12) + tick_w + 10
        self.right = c.w - 24
        self.top = _header(c, title, subtitle)
        self.bottom = c.h - (60 if x_label else 40)
        if x_label:
            c.text((self.left + self.right) / 2, c.h - 14, x_label, size=17, anchor="middle")
        if y_label:
            c.text(20, (self.top + self.bottom) / 2, y_label, size=17, anchor="middle", rotate=-90)
        if footer:
            c.text(c.w - 10, c.h - 10, footer, size=12, anchor="end", color=c.t["muted"])

    def y(self, v):
        return self.bottom - (v / self.y_top) * (self.bottom - self.top)

    def axes(self):
        c = self.c
        for v in self.y_ticks[1:]:
            yy = self.y(v)
            c.path(f"M{self.left - 5:.1f},{yy:.1f}H{self.left:.1f}", width=2)
            c.text(self.left - 10, yy, fmt_num(v), size=16, anchor="end", baseline="central")
        c.path(f"M{self.left:.1f},{self.top - 6:.1f}V{self.bottom:.1f}H{self.right + 6:.1f}")

    def legend(self, items, corner="top-left"):
        if not items:
            return
        c = self.c
        size, row = 15, 21
        w = 34 + max(c.font.width(label, size) for label, _ in items)
        h = 10 + row * len(items)
        x = self.left + 14 if corner == "top-left" else self.right - w - 10
        y = self.top + 4
        c.rect(x, y, w, h, fill=c.t["bg"], stroke=c.t["fg"], width=2, rx=5)
        for i, (label, color) in enumerate(items):
            cy = y + 5 + row * i + row / 2
            c.rect(x + 10, cy - 5, 10, 10, fill=color, rx=2, wobble=False)
            c.text(x + 26, cy, label, size=size, baseline="central")


def _sample_indices(n, k):
    if n <= k:
        return list(range(n))
    return sorted({round(i * (n - 1) / (k - 1)) for i in range(k)})


# ---------------------------------------------------------------- chart types


def line_chart(series, *, title=None, subtitle=None, x_label=None, y_label=None, theme="light", width=600, height=400,
               legend="top-left", dots=24, footer=None, desc=None, font=None):
    """series: [{"label", "points": [(datetime, value), ...], "color"?}] -- an xkcd XY chart over time."""
    c = Canvas(width, height, theme, font or default_font())
    xs = [p[0] for s in series for p in s["points"]]
    t0, t1 = min(xs), max(xs)
    y_max = max(p[1] for s in series for p in s["points"])
    plot = _Plot(c, y_max, title, subtitle, x_label, y_label, footer)
    span = (t1 - t0).total_seconds() or 1

    def px(t):
        return plot.left + (t - t0).total_seconds() / span * (plot.right - plot.left)

    ticks, labels = time_ticks(t0, t1)
    for t, label in zip(ticks, labels):
        c.text(px(t), plot.bottom + 24, label, size=16, anchor="middle")
    plot.axes()

    for i, s in enumerate(series):
        color = s.get("color") or PALETTE[i % len(PALETTE)]
        pts = [(px(t), plot.y(v)) for t, v in s["points"]]
        c.path(monotone_path(pts), stroke=color, width=3)
        if dots:
            for j in _sample_indices(len(pts), dots):
                c.circle(*pts[j], r=3.5, fill=color)
    if legend:
        plot.legend([(s["label"], s.get("color") or PALETTE[i % len(PALETTE)]) for i, s in enumerate(series)], legend)
    return c.render(desc or title or "")


def bar_chart(labels, datasets, *, title=None, subtitle=None, x_label=None, y_label=None, theme="light", width=600, height=400,
              legend="top-left", label_every=1, annotate=None, footer=None, desc=None, font=None):
    """Stacked bars. datasets: [{"label", "values", "color"? , "colors"?}]; annotate: (index, text)."""
    c = Canvas(width, height, theme, font or default_font())
    n = len(labels)
    totals = [sum(ds["values"][i] for ds in datasets) for i in range(n)]
    plot = _Plot(c, max(totals), title, subtitle, x_label, y_label, footer)
    band = (plot.right - plot.left - 8) / n
    bar_w = band * (0.62 if n > 12 else 0.55)
    stroke_w = 2 if bar_w < 22 else 3

    for i in range(n):
        x = plot.left + 8 + band * i + (band - bar_w) / 2
        base = 0
        for k, ds in enumerate(datasets):
            v = ds["values"][i]
            if v <= 0:
                continue
            color = ds["colors"][i] if ds.get("colors") else ds.get("color") or PALETTE[k % len(PALETTE)]
            y0, y1 = plot.y(base), plot.y(base + v)
            c.rect(x, y1, bar_w, y0 - y1, fill=color, stroke=c.t["fg"], width=stroke_w)
            base += v
        if i % label_every == 0:
            c.text(x + bar_w / 2, plot.bottom + 24, labels[i], size=15, anchor="middle")
    plot.axes()

    if annotate:
        i, text = annotate
        bx = plot.left + 8 + band * (i + 0.5)
        by = plot.y(totals[i]) - 8
        to_left = bx > (plot.left + plot.right) / 2
        tw = c.font.width(text, 16)
        tx = bx - 60 if to_left else bx + 60
        ty = max(plot.top + 14, by - 46)
        c.text(tx, ty, text, size=16, anchor="end" if to_left else "start")
        sx = tx + (-tw / 2 if to_left else tw / 2)
        sy = ty + 8
        c.path(f"M{sx:.1f},{sy:.1f}Q{bx:.1f},{sy:.1f} {bx:.1f},{by:.1f}", width=2)
        c.path(f"M{bx - 5:.1f},{by - 9:.1f}L{bx:.1f},{by:.1f}L{bx + 5:.1f},{by - 9:.1f}", width=2)

    if legend and len(datasets) > 1:
        plot.legend([(ds["label"], ds.get("color") or PALETTE[k % len(PALETTE)]) for k, ds in enumerate(datasets)],
                    legend)
    return c.render(desc or title or "")


def pie_chart(labels, values, *, title=None, subtitle=None, theme="light", width=600, height=400, donut=0.5, footer=None,
              desc=None, font=None):
    c = Canvas(width, height, theme, font or default_font())
    top = _header(c, title, subtitle)
    if footer:
        c.text(width - 10, height - 10, footer, size=12, anchor="end", color=c.t["muted"])
    r = (height - top - 30) / 2
    cx, cy = 40 + r, top + r + 4
    total = sum(values) or 1
    angle = -math.pi / 2
    for i, v in enumerate(values):
        sweep = v / total * 2 * math.pi
        a0, a1 = angle, angle + sweep
        large = 1 if sweep > math.pi else 0
        ri = r * donut
        p = lambda rad, a: (cx + rad * math.cos(a), cy + rad * math.sin(a))
        (x0, y0), (x1, y1) = p(r, a0), p(r, a1)
        (x2, y2), (x3, y3) = p(ri, a1), p(ri, a0)
        d = (f"M{x0:.1f},{y0:.1f}A{r:.1f},{r:.1f} 0 {large} 1 {x1:.1f},{y1:.1f}"
             f"L{x2:.1f},{y2:.1f}A{ri:.1f},{ri:.1f} 0 {large} 0 {x3:.1f},{y3:.1f}Z")
        c.path(d, fill=PALETTE[i % len(PALETTE)], width=3)
        angle = a1

    size, row = 16, 30
    lx = cx + r + 50
    ly = cy - row * len(labels) / 2 + row / 2
    for i, (label, v) in enumerate(zip(labels, values)):
        yy = ly + row * i
        c.rect(lx, yy - 7, 14, 14, fill=PALETTE[i % len(PALETTE)], stroke=c.t["fg"], width=2, rx=2)
        c.text(lx + 24, yy, label, size=size, baseline="central")
        c.text(width - 30, yy, f"{v / total:.0%}", size=size, anchor="end", baseline="central", color=c.t["muted"])
    return c.render(desc or title or "")


def cumulative(events, start, end, samples=60):
    """events: [(datetime, weight)] -> evenly spaced running totals [(datetime, total)] from start to end."""
    events = sorted(events)
    times = [t for t, _ in events]
    running, acc = [], 0
    for _, w in events:
        acc += w
        running.append(acc)
    step = (end - start) / (samples - 1)
    out = []
    for i in range(samples):
        t = start + step * i
        k = bisect.bisect_right(times, t)
        out.append((t, running[k - 1] if k else 0))
    return out
