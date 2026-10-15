"""Hand-drawn project panels (a 2x2 comic strip) for the Featured Projects section.

Each panel is its own SVG so the README can link every one to its repo.
"""

import math

import xkcd

W, H = 420, 310
RED = "#dd4528"
BLUE = "#28a3dd"
GREEN = "#4ab74e"


class Panel:
    def __init__(self, theme, title, subtitle, tech):
        self.c = xkcd.Canvas(W, H, theme, xkcd.default_font())
        self.fg, self.muted, self.bg = self.c.t["fg"], self.c.t["muted"], self.c.t["bg"]
        self.title = title
        c = self.c
        c.rect(8, 8, W - 16, H - 16, fill=self.bg, stroke=self.fg, width=3, rx=3)
        c.text(26, 42, title, size=21, bold=True)
        c.text(26, 63, subtitle, size=14, color=self.muted)
        c.text(26, H - 26, tech, size=13.5, color=self.muted)

    # Drawing helpers -----------------------------------------------------------

    def box(self, x, y, w, h, label=None, size=16, fill=None, dashed=False):
        extra = ' stroke-dasharray="7 6"' if dashed else ""
        self.c.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill or self.bg}" '
            f'stroke="{self.fg}" stroke-width="2.5" filter="url(#xkcdify)"{extra}/>')
        if label:
            self.c.text(x + w / 2, y + h / 2 + size * 0.35, label, size=size, anchor="middle")

    def ring(self, cx, cy, r, fill="none", width=2.5, stroke=None):
        self.c.path(f"M{cx - r},{cy} a{r},{r} 0 1,0 {2 * r},0 a{r},{r} 0 1,0 {-2 * r},0", fill=fill,
                    width=width, stroke=stroke)

    def arrow(self, x1, y1, x2, y2, label=None, bend=0, ly=None, size=14, color=None, both=False):
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + bend
        self.c.path(f"M{x1},{y1} Q{mx},{my} {x2},{y2}", width=2.5, stroke=color)
        for ax, ay in [(x2, y2)] + ([(x1, y1)] if both else []):
            ang = math.atan2(ay - my, ax - mx)
            for d in (0.45, -0.45):
                self.c.path(f"M{ax},{ay} L{ax - 11 * math.cos(ang + d):.1f},{ay - 11 * math.sin(ang + d):.1f}",
                            width=2.5, stroke=color)
        if label:
            self.c.text(mx, (my - 9) if ly is None else ly, label, size=size, anchor="middle")

    def note(self, tx, ty, text, px=None, py=None, anchor="start", size=15):
        """Red xkcd annotation, optionally with a curved leader line to (px, py)."""
        self.c.text(tx, ty, text, size=size, color=RED, anchor=anchor)
        if px is None:
            return
        tw = self.c.font.width(text, size)
        left = tx - (tw if anchor == "end" else tw / 2 if anchor == "middle" else 0)
        sx = min(max(px, left + 6), left + tw - 6)
        sy = ty - size - 2 if py < ty else ty + 6
        self.c.path(f"M{sx:.1f},{sy} Q{sx:.1f},{(sy + py) / 2:.1f} {px},{py}", stroke=RED, width=2)

    def render(self):
        return self.c.render(self.title)


# Panels -------------------------------------------------------------------------


def robot_station(theme, stars):
    p = Panel(theme, "Robot Charging Station", "WeChat mini program for robot fleet teleop",
              "uni-app · Vue 3 · uniCloud · MQTT · WebSocket")
    c = p.c
    # Phone with a joystick.
    p.box(40, 92, 66, 118, fill=p.bg)
    c.path("M62,102 H84", width=2.5)
    p.ring(73, 168, 20)
    p.ring(80, 162, 8, fill=p.fg)
    c.text(73, 132, "drive", size=13, anchor="middle", color=p.muted)
    # Robot.
    p.box(282, 130, 82, 52, fill=p.bg)
    p.ring(300, 190, 9, fill=p.bg)
    p.ring(346, 190, 9, fill=p.bg)
    c.path("M323,130 V112", width=2.5)
    p.ring(323, 107, 5, fill=RED, stroke=RED)
    c.circle(306, 152, 4, fill=p.fg)
    c.circle(340, 152, 4, fill=p.fg)
    c.path("M310,166 Q323,173 336,166", width=2.5)
    p.arrow(116, 146, 274, 146, "5 Hz commands", bend=-16, ly=128)
    p.note(194, 240, "let go = robot stops in 1s", 196, 152, anchor="middle")
    p.note(394, 92, f"{stars} stars", 360, 124, anchor="end")
    p.note(150, 92, "80+ beta users", 108, 104)
    return p.render()


def ecs_gateway(theme):
    p = Panel(theme, "ECS Gateway", "the IoT gateway behind the fleet",
              "Python · Flask · paho-mqtt · EMQX · Render")
    c = p.c
    # Robots on the left.
    for i, y in enumerate((100, 146, 192)):
        p.box(30, y - 14, 36, 28, fill=p.bg)
        c.circle(42, y, 3, fill=p.fg)
        c.circle(54, y, 3, fill=p.fg)
        p.arrow(70, y, 150, 150 + (i - 1) * 14)
    c.text(48, 226, "robots", size=13, anchor="middle", color=p.muted)
    c.text(108, 98, "MQTT", size=14, anchor="middle")
    # The one process.
    p.box(152, 108, 104, 92, fill=p.bg)
    c.text(204, 132, "ECS", size=19, anchor="middle", bold=True)
    for i, line in enumerate(("persist", "dispatch", "broadcast")):
        c.text(204, 154 + i * 17, line, size=13.5, anchor="middle", color=p.muted)
    # Outputs: database and live clients.
    c.path("M318,100 v28 a20,6 0 0,0 40,0 v-28", width=2.5)
    c.path("M318,100 a20,6 0 0,1 40,0 a20,6 0 0,1 -40,0", width=2.5)
    p.arrow(260, 128, 312, 112)
    p.box(304, 166, 64, 40, "apps", size=15)
    p.arrow(260, 178, 298, 184, "WS", ly=168)
    # The service it replaced.
    p.box(306, 230, 78, 30, dashed=True)
    c.text(345, 250, "service 2", size=13, anchor="middle", color=p.muted)
    c.path("M308,232 L382,258 M382,232 L308,258", stroke=RED, width=2.5)
    p.note(110, 252, "two services, now one", 300, 244)
    p.note(394, 82, "latency: 10s -> 1s", anchor="end")
    return p.render()


def smart_helmet(theme):
    p = Panel(theme, "AI Smart Helmet", "cloud backend · private repo",
              "NestJS · Prisma · PostgreSQL 16 · EMQX · Docker")
    c = p.c
    # Helmet with an SOS shout.
    c.path("M34,176 Q34,116 86,116 Q138,116 138,176 Z", fill=p.bg, width=2.5)
    c.path("M26,176 H150", width=3)
    c.path("M66,132 Q86,124 108,134", width=2)
    p.box(92, 82, 54, 26, fill=p.bg)
    c.text(119, 101, "SOS!", size=15, anchor="middle", color=RED, bold=True)
    c.path("M108,108 L100,118", width=2.5)
    # State machine.
    states = [("pending", 228, 112), ("delivered", 330, 112), ("success", 330, 186)]
    for name, x, y in states:
        p.box(x - 42, y - 15, 84, 30, fill=p.bg)
        c.text(x, y + 5, name, size=14, anchor="middle")
    p.arrow(152, 150, 184, 118)
    p.arrow(272, 112, 286, 112)
    p.arrow(330, 128, 330, 168)
    c.text(228, 196, "failed / offline", size=13.5, anchor="middle", color=p.muted)
    p.arrow(290, 124, 262, 182, bend=0)
    p.note(214, 250, "survives restarts. 209 e2e tests.", 328, 204, anchor="middle")
    p.note(394, 82, "MQTT / webhook / BLE in", anchor="end")
    return p.render()


def company_site(theme):
    p = Panel(theme, "ZeroOne Website", "01web · trilingual company site, live",
              "Next.js · TypeScript · Nginx · Tencent Cloud")
    c = p.c
    # Browser window.
    p.box(36, 86, 228, 150, fill=p.bg)
    c.path("M36,110 H264", width=2.5)
    for i, col in enumerate((RED, "#f3db52", GREEN)):
        c.circle(50 + i * 14, 98, 4, fill=col)
    c.text(176, 103, "01weichuang.com", size=13, anchor="middle", color=p.muted)
    c.path("M56,132 H190 M56,150 H226 M56,168 H160", width=2.5, stroke=p.muted)
    for i, lang in enumerate(("CN", "TW", "EN")):
        p.box(56 + i * 52, 192, 42, 26, lang, size=14, fill=p.bg)
    # Spam bot bouncing off.
    p.box(326, 140, 54, 40, "bot", size=15, fill=p.bg)
    p.arrow(320, 150, 272, 150, color=RED)
    c.text(296, 136, "429", size=14, anchor="middle", color=RED, bold=True)
    p.note(394, 82, "rate limits spam bots", 352, 136, anchor="end")
    p.note(394, 252, "308s keep old links alive", anchor="end")
    return p.render()


PANELS = {
    "project-robot-station": lambda theme, stars: robot_station(theme, stars),
    "project-ecs": lambda theme, stars: ecs_gateway(theme),
    "project-helmet": lambda theme, stars: smart_helmet(theme),
    "project-01web": lambda theme, stars: company_site(theme),
}
