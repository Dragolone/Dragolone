"""Build xkcd-style profile charts (light + dark) from GitHub data.

    GH_TOKEN=... python scripts/xkcd/make_charts.py --user Dragolone --out dist

Config (flags or env):
  --tz / CHART_TZ              timezone for the commit clock and week buckets
  --alias / REPO_ALIASES       "repo=Label;repo2=Label 2" -- names to show for private repos.
                               Private repos without an alias are merged into "private repos".
  --hide-langs / HIDE_LANGS    comma-separated languages left out of the language chart
  --cache FILE                 reuse (or write) the raw API data, handy while tweaking charts
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import xkcd  # noqa: E402
from github_data import collect  # noqa: E402

GREEN, RED, GREY, BLUE = "#4ab74e", "#dd4528", "#949494", "#28a3dd"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def hour_label(h):
    return {0: "12am", 12: "noon"}.get(h, f"{h % 12}{'am' if h < 12 else 'pm'}")


def build(data, tz, aliases, hide_langs):
    now = ts(data["fetched_at"])
    login = data["login"]
    private = {r["name"] for r in data["repos"] if r["private"]}

    def repo_label(name):
        if name in aliases:
            return aliases[name]
        return "private repos" if name in private else name

    charts = {}

    # 1. Contributions, cumulative -- the star-history curve, but for you.
    cal = [(datetime.fromisoformat(d).replace(tzinfo=timezone.utc), n) for d, n in data["calendar"] if n]
    start = ts(data["created_at"])
    charts["contributions"] = dict(
        kind="line",
        series=[{"label": f"{login}", "points": xkcd.cumulative(cal, start, now, samples=80)}],
        title="Contribution History", subtitle=f"{sum(n for _, n in cal):,} contributions since {start:%b %Y}",
        x_label="Date", y_label="Contributions", legend=None,
    )

    # 2. Stars on repos that have a real following (>= 5 stars).
    by_repo = defaultdict(list)
    for s in data["stars"]:
        by_repo[s["repo"]].append((ts(s["starred_at"]), 1))
    starred = sorted((r for r in by_repo if len(by_repo[r]) >= 5), key=lambda r: -len(by_repo[r]))[:4]
    if starred:
        first = min(t for r in starred for t, _ in by_repo[r]) - timedelta(days=7)
        charts["stars"] = dict(
            kind="line",
            series=[{"label": repo_label(r), "points": xkcd.cumulative(by_repo[r], first, now)} for r in starred],
            title="Star History", subtitle=f"{len(data['stars']):,} stars across all repos",
            x_label="Date", y_label="GitHub Stars",
        )

    runs = [r for r in data["runs"] if r["conclusion"] is not None]
    if runs:
        # 3. Actions runs per week, red vs green.
        def week_of(t):
            local = t.astimezone(tz)
            return (local - timedelta(days=local.weekday())).date()

        first_week = week_of(min(ts(r["created_at"]) for r in runs))
        this_week = week_of(now)
        n_weeks = min((this_week - first_week).days // 7 + 1, 26)
        weeks = [this_week - timedelta(weeks=n_weeks - 1 - i) for i in range(n_weeks)]
        index = {w: i for i, w in enumerate(weeks)}
        ok, bad, other = [0] * n_weeks, [0] * n_weeks, [0] * n_weeks
        for r in runs:
            i = index.get(week_of(ts(r["created_at"])))
            if i is None:
                continue
            {"success": ok, "failure": bad}.get(r["conclusion"], other)[i] += 1
        datasets = [{"label": f"passed ({sum(ok)})", "values": ok, "color": GREEN},
                    {"label": f"failed ({sum(bad)})", "values": bad, "color": RED}]
        if any(other):
            datasets.append({"label": f"cancelled ({sum(other)})", "values": other, "color": GREY})
        fail_rate = sum(bad) / max(sum(ok) + sum(bad), 1)
        charts["actions-runs"] = dict(
            kind="bar", labels=[f"{w:%b} {w.day}" for w in weeks], datasets=datasets,
            title="GitHub Actions Runs per Week",
            subtitle=f"{len(runs):,} runs, and CI said no {fail_rate:.0%} of the time", x_label="Week",
            y_label="Runs", label_every=max(1, n_weeks // 5),
        )

        # 4. CI minutes burned, cumulative per repo.
        minutes = defaultdict(list)
        for r in runs:
            m = (ts(r["updated_at"]) - ts(r["started_at"])).total_seconds() / 60
            if m > 0:
                minutes[repo_label(r["repo"])].append((ts(r["started_at"]), m))
        top = [k for k in sorted(minutes, key=lambda k: -sum(m for _, m in minutes[k]))[:4]
               if sum(m for _, m in minutes[k]) >= 10]
        total = sum(m for k in minutes for _, m in minutes[k])
    if runs and top:
        first_run = min(t for k in top for t, _ in minutes[k]) - timedelta(days=3)
        charts["actions-minutes"] = dict(
            kind="line",
            series=[{"label": k, "points": xkcd.cumulative(minutes[k], first_run, now)} for k in top],
            title="CI Minutes Burned", subtitle=f"{total:,.0f} min of runner time, about {total / 60:,.0f} hours",
            x_label="Date",
            y_label="Minutes",
        )

    # 5. Commit clock.
    hours = Counter(ts(c["date"]).astimezone(tz).hour for c in data["commits"])
    counts = [hours[h] for h in range(24)]
    peak = max(range(24), key=lambda h: counts[h])
    night = sum(counts[h] for h in range(0, 6))
    note = f"{hour_label(peak)}: peak commit o'clock"
    charts["commit-clock"] = dict(
        kind="bar", labels=[hour_label(h) for h in range(24)],
        datasets=[{"label": "commits", "values": counts,
                   "colors": [RED if h == peak else (BLUE if 6 <= h < 24 else "#9179c0") for h in range(24)]}],
        title="When Do I Commit?", y_label="Commits", label_every=3, annotate=(peak, note),
        subtitle=f"{night / max(sum(counts), 1):.0%} of commits land between midnight and 6am (purple)",
        x_label=f"Hour of day ({now.astimezone(tz):%Z})",
    )

    # 6. Languages by bytes.
    langs = Counter()
    for per_repo in data["languages"].values():
        langs.update({k: v for k, v in per_repo.items() if k not in hide_langs})
    top_langs = langs.most_common(6)
    rest = sum(langs.values()) - sum(v for _, v in top_langs)
    labels = [k for k, _ in top_langs] + (["Other"] if rest else [])
    values = [v for _, v in top_langs] + ([rest] if rest else [])
    charts["languages"] = dict(kind="pie", labels=labels, values=values, title="What I Write",
                               subtitle=f"bytes of code across {len(data['languages'])} repos")
    return charts


def render(name, spec, theme, footer):
    spec = dict(spec)
    kind = spec.pop("kind")
    desc = f"{spec['title']} (xkcd-style chart)"
    if kind == "line":
        return xkcd.line_chart(spec.pop("series"), theme=theme, footer=footer, desc=desc, **spec)
    if kind == "bar":
        return xkcd.bar_chart(spec.pop("labels"), spec.pop("datasets"), theme=theme, footer=footer, desc=desc, **spec)
    return xkcd.pie_chart(spec.pop("labels"), spec.pop("values"), theme=theme, footer=footer, desc=desc, **spec)


def parse_aliases(s):
    out = {}
    for part in filter(None, (p.strip() for p in (s or "").split(";"))):
        repo, _, label = part.partition("=")
        out[repo.strip()] = label.strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("CHART_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER"))
    ap.add_argument("--out", default="dist")
    ap.add_argument("--tz", default=os.environ.get("CHART_TZ") or "UTC")
    ap.add_argument("--alias", default=os.environ.get("REPO_ALIASES", ""))
    ap.add_argument("--hide-langs", default=os.environ.get("HIDE_LANGS", "HTML,TeX,Jupyter Notebook,BibTeX Style"))
    ap.add_argument("--cache")
    args = ap.parse_args()

    if args.cache and os.path.exists(args.cache):
        with open(args.cache) as f:
            data = json.load(f)
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token or not args.user:
            sys.exit("need GH_TOKEN and --user")
        data = collect(token, args.user)
        if args.cache:
            with open(args.cache, "w") as f:
                json.dump(data, f)

    tz = ZoneInfo(args.tz)
    hide = {s.strip() for s in args.hide_langs.split(",") if s.strip()}
    charts = build(data, tz, parse_aliases(args.alias), hide)
    footer = f"updated {ts(data['fetched_at']).astimezone(tz):%Y-%m-%d}"

    os.makedirs(args.out, exist_ok=True)
    for name, spec in charts.items():
        for theme, suffix in (("light", ""), ("dark", "-dark")):
            path = os.path.join(args.out, f"{name}{suffix}.svg")
            with open(path, "w") as f:
                f.write(render(name, spec, theme, footer))
            print(f"wrote {path} ({os.path.getsize(path) // 1024} KB)")


if __name__ == "__main__":
    main()
