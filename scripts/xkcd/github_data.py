"""Collect the raw GitHub data behind the xkcd charts (stdlib only).

Everything is read with one token. In Actions that has to be a PAT stored as a
secret, because the built-in GITHUB_TOKEN can only see the profile repo.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api.github.com"


class GitHub:
    def __init__(self, token):
        self.token = token

    def _request(self, url, body=None, accept="application/vnd.github+json"):
        headers = {
            "Accept": accept,
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "xkcd-profile-charts",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp), resp.headers

    def get(self, path, **params):
        url = f"{API}{path}?{urllib.parse.urlencode(params)}" if params else f"{API}{path}"
        return self._request(url)[0]

    def paginate(self, path, key=None, accept="application/vnd.github+json", max_pages=50, **params):
        params.setdefault("per_page", 100)
        url = f"{API}{path}?{urllib.parse.urlencode(params)}"
        out = []
        for _ in range(max_pages):
            try:
                page, headers = self._request(url, accept=accept)
            except urllib.error.HTTPError as e:
                # 409 = empty repo, 404/403 = no access; just skip that repo.
                if e.code in (403, 404, 409):
                    return out
                raise
            out.extend(page[key] if key else page)
            nxt = _next_link(headers.get("Link", ""))
            if not nxt:
                break
            url = nxt
        return out

    def graphql(self, query, **variables):
        res, _ = self._request(f"{API}/graphql", body={"query": query, "variables": variables})
        if res.get("errors"):
            raise RuntimeError(res["errors"])
        return res["data"]


def _next_link(link_header):
    for part in link_header.split(","):
        if 'rel="next"' in part:
            return part[part.index("<") + 1 : part.index(">")]
    return None


CALENDAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def collect(token, login):
    gh = GitHub(token)
    user = gh.get(f"/users/{login}")
    now = datetime.now(timezone.utc)

    # The authenticated user's own repos include private ones; anyone else only gets public.
    # (GITHUB_TOKEN isn't a user token, so /user fails and we fall back to public data.)
    try:
        viewer = gh.get("/user")["login"]
    except urllib.error.HTTPError:
        viewer = ""
    if viewer.lower() == login.lower():
        repos = gh.paginate("/user/repos", affiliation="owner")
    else:
        repos = gh.paginate(f"/users/{login}/repos", type="owner")
    repos = [r for r in repos if not r["fork"]]
    log(f"{len(repos)} repos")

    # Contribution calendar, one year per query (the API's maximum span).
    calendar = {}
    start = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    while start < now:
        end = min(start + timedelta(days=365), now)
        data = gh.graphql(CALENDAR_QUERY, login=login, **{"from": start.isoformat(), "to": end.isoformat()})
        for week in data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                calendar[day["date"]] = day["contributionCount"]
        start = end
    log(f"{sum(calendar.values())} contributions")

    runs, commits, stars, languages = [], [], [], {}
    for r in repos:
        name = r["name"]
        full = r["full_name"]
        for run in gh.paginate(f"/repos/{full}/actions/runs", key="workflow_runs"):
            runs.append({
                "repo": name,
                "created_at": run["created_at"],
                "started_at": run.get("run_started_at") or run["created_at"],
                "updated_at": run["updated_at"],
                "conclusion": run["conclusion"],
            })
        for c in gh.paginate(f"/repos/{full}/commits", author=login):
            commits.append({"repo": name, "date": c["commit"]["author"]["date"]})
        if r["stargazers_count"]:
            for s in gh.paginate(f"/repos/{full}/stargazers", accept="application/vnd.github.star+json"):
                stars.append({"repo": name, "starred_at": s["starred_at"]})
        languages[name] = gh.get(f"/repos/{full}/languages")
        log(f"  {name}: done")

    return {
        "login": user["login"],
        "created_at": user["created_at"],
        "fetched_at": now.isoformat(),
        "repos": [{"name": r["name"], "private": r["private"], "stars": r["stargazers_count"]} for r in repos],
        "calendar": sorted(calendar.items()),
        "runs": runs,
        "commits": commits,
        "stars": stars,
        "languages": languages,
    }
