"""Hand-drawn map of how the featured projects connect, for the Featured Projects section."""

import math

import xkcd

RED = "#dd4528"


def render(theme, stars, footer=None):
    c = xkcd.Canvas(820, 470, theme, xkcd.default_font())
    fg, muted = c.t["fg"], c.t["muted"]

    c.text(410, 36, "How My Projects Fit Together", size=23, anchor="middle", bold=True)
    c.text(410, 60, "one person, from the device to the dashboard", size=15, anchor="middle", color=muted)
    if footer:
        c.text(810, 462, footer, size=12, anchor="end", color=muted)

    def box(x, y, title, sub, w=170, h=62):
        c.rect(x, y, w, h, fill=c.t["bg"], stroke=fg, width=2.5, rx=6)
        c.text(x + w / 2, y + 28, title, size=19, anchor="middle")
        c.text(x + w / 2, y + 48, sub, size=13.5, anchor="middle", color=muted)

    def arrow(x1, y1, x2, y2, label, lx=None, ly=None, both=False, bend=0):
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + bend
        c.path(f"M{x1},{y1} Q{mx},{my} {x2},{y2}", width=2.5)
        heads = [(x2, y2)] + ([(x1, y1)] if both else [])
        for ax, ay in heads:
            ang = math.atan2(ay - my, ax - mx)
            for d in (0.45, -0.45):
                c.path(f"M{ax},{ay} L{ax - 12 * math.cos(ang + d):.1f},{ay - 12 * math.sin(ang + d):.1f}", width=2.5)
        c.text(mx if lx is None else lx, my - 8 if ly is None else ly, label, size=15, anchor="middle")

    def note(tx, ty, text, px, py):
        """Red annotation with a curved leader line to (px, py)."""
        c.text(tx, ty, text, size=15, color=RED)
        sx, sy = tx + 12, ty - 17 if py < ty else ty + 7
        c.path(f"M{sx},{sy} Q{sx},{(sy + py) / 2} {px},{py}", stroke=RED, width=2)

    # Robot platform: robots <-> ECS gateway -> mini program / admin panel.
    box(30, 125, "Robots", "the fleet")
    box(320, 125, "ECS gateway", "Python + EMQX")
    box(620, 90, "Mini Program", "uni-app + Vue 3")
    box(620, 190, "Admin panel", "Vue 3 + uniCloud")
    arrow(200, 156, 320, 156, "MQTT", both=True)
    arrow(490, 145, 620, 121, "WebSocket", ly=118, bend=-14)
    arrow(490, 170, 620, 221, "HTTP", lx=560, ly=228, bend=14)
    note(318, 236, "10s -> 1s latency", 372, 188)
    note(560, 70, f"{stars} stars, 80+ users", 640, 98)

    # Helmet platform.
    box(30, 320, "Helmets", "AI smart helmet")
    box(320, 320, "Helmet backend", "NestJS + Postgres")
    arrow(200, 351, 320, 351, "MQTT / BLE")
    note(520, 300, "SOS state machine survives restarts", 492, 336)
    note(520, 400, "209 e2e tests (private repo)", 470, 382)

    c.text(30, 448, "side quests:", size=15, color=muted)
    c.text(118, 448, "01web (company site, live)  ·  Elec1601 maze car (top 8 of 200+)", size=15, color=muted)
    return c.render("How my projects fit together: robots, ECS gateway, mini program, admin panel, helmet backend")
