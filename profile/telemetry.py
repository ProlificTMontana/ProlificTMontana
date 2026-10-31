"""Render the live "Telemetry" card from the GitHub GraphQL API.

Runs daily in GitHub Actions (see .github/workflows/telemetry.yml) and
publishes telemetry-{dark,light}.svg to the ``output`` branch, so the README
always shows fresh numbers without third-party stat services.

    GITHUB_TOKEN=... python profile/telemetry.py --out dist
    python profile/telemetry.py --sample --out /tmp/preview   # offline design check

Environment:
    GITHUB_TOKEN       token used for the API (Actions' token is enough for public data)
    INCLUDE_PRIVATE    "1" to count private repositories in language stats (needs a PAT)
    EXCLUDE_LANGUAGES  comma-separated languages to leave out, e.g. "HTML,CSS"
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from xml.dom import minidom

import content as C
from design import SVG, brand_gradient, card, clip_round, fmt, glow, gradient, legible, text_width

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        isPrivate
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""


@dataclass
class Stats:
    total: int
    commits: int
    prs: int
    issues: int
    repos: int
    stars: int
    current_streak: int
    longest_streak: int
    weeks: list[tuple[dt.date, int]]
    languages: list[tuple[str, str, float]]  # name, colour, share
    synced: dt.datetime


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------


def fetch(login: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": f"{login}-profile-telemetry"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]["user"]


def streaks(days: list[tuple[dt.date, int]]) -> tuple[int, int]:
    longest = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    tail = days[:-1] if days and days[-1][1] == 0 else days  # today may not have activity yet
    for _, n in reversed(tail):
        if not n:
            break
        current += 1
    return current, longest


def summarise(user: dict, include_private: bool, exclude: set[str]) -> Stats:
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    weeks = [(dt.date.fromisoformat(w["contributionDays"][0]["date"]), sum(d["contributionCount"] for d in w["contributionDays"]))
             for w in cal["weeks"]]
    repos = [r for r in user["repositories"]["nodes"] if include_private or not r["isPrivate"]]
    sizes: dict[str, int] = {}
    colours: dict[str, str] = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            if name in exclude:
                continue
            sizes[name] = sizes.get(name, 0) + e["size"]
            colours[name] = e["node"]["color"] or "#8b949e"
    total = sum(sizes.values()) or 1
    langs = sorted(((n, colours[n], s / total) for n, s in sizes.items()), key=lambda x: -x[2])
    cur, best = streaks(days)
    return Stats(
        total=cal["totalContributions"], commits=cc["totalCommitContributions"],
        prs=cc["totalPullRequestContributions"], issues=cc["totalIssueContributions"],
        repos=len(repos), stars=sum(r["stargazerCount"] for r in repos),
        current_streak=cur, longest_streak=best, weeks=weeks, languages=langs,
        synced=dt.datetime.now(dt.timezone.utc),
    )


def sample() -> Stats:
    """Deterministic fake data for offline design previews. Never published."""
    rnd = random.Random(7)
    start = dt.date(2025, 11, 2)
    weeks = [(start + dt.timedelta(weeks=i), max(0, int(18 + 14 * rnd.random() + 10 * (i / 52) - (8 if i % 9 == 0 else 0)))) for i in range(53)]
    langs = [("TypeScript", "#3178c6", 0.58), ("Python", "#3572A5", 0.21), ("HTML", "#e34c26", 0.08),
             ("CSS", "#663399", 0.06), ("JavaScript", "#f1e05a", 0.04), ("Shell", "#89e051", 0.03)]
    return Stats(sum(w for _, w in weeks), 812, 64, 11, 13, 4, 12, 37, weeks, langs,
                 dt.datetime(2026, 10, 31, 3, 17, tzinfo=dt.timezone.utc))


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _smooth(points: list[tuple[float, float]]) -> str:
    """Catmull-Rom → cubic Bézier path through ``points``."""
    d = f"M{fmt(points[0][0])} {fmt(points[0][1])}"
    for i in range(len(points) - 1):
        p0 = points[max(i - 1, 0)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p2[0])} {fmt(p2[1])}"
    return d


def render(s: Stats, theme: str) -> SVG:
    W, H = 1200, 392
    doc = SVG(W, H, theme, f"GitHub telemetry for @{C.LOGIN}",
              f"{s.total} contributions in the last year, {s.commits} commits, current streak {s.current_streak} days, "
              f"longest streak {s.longest_streak} days, {s.repos} repositories. Top languages: "
              + ", ".join(f"{n} {p:.0%}" for n, _, p in s.languages[:6]))
    t = doc.t
    clip_round(doc, "cc", 0, 0, W, H, 18)
    card(doc, 0, 0, W, H, 18)
    doc.add('<g clip-path="url(#cc)">')
    glow(doc, "g1", 900, H, 520, t["violet"], 0.9)
    glow(doc, "g2", 0, 0, 380, t["red"], 0.6)
    doc.add("</g>")
    brand = brand_gradient(doc, "brand")

    # ---- KPI tiles (2 × 2)
    kpis = (
        ("CONTRIBUTIONS", f"{s.total:,}", "last 12 months"),
        ("CURRENT STREAK", f"{s.current_streak}d", f"longest: {s.longest_streak} days"),
        ("COMMITS", f"{s.commits:,}", f"{s.prs} PRs · {s.issues} issues"),
        ("REPOSITORIES", f"{s.repos}", f"{s.stars} stars earned"),
    )
    tx, ty, tw, th, g = 32, 32, 252, 144, 14
    for i, (label, value, sub) in enumerate(kpis):
        x = tx + (i % 2) * (tw + g)
        y = ty + (i // 2) * (th + g)
        doc.add(f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{tw - 1}" height="{th - 1}" rx="14" fill="{t["surface"]}" stroke="{t["border"]}"/>')
        doc.add(doc.text(x + 22, y + 35, label, "mono", 13, t["muted"], ls=1.4))
        doc.add(doc.text(x + 20, y + 90, value, "display", 48, brand if i == 0 else t["text"], ls=-1.5))
        doc.add(doc.text(x + 22, y + 121, sub, "mono", 13.5, t["muted"]))

    # ---- weekly activity
    ax0, ax1 = 580, W - 40
    ay_top, ay_base = 78, 214
    doc.add(doc.text(ax0, 50, "WEEKLY ACTIVITY", "mono", 13, t["muted"], ls=1.4))
    doc.add(doc.text(ax1, 50, f"{len(s.weeks)} weeks", "mono", 13, t["dim"], anchor="end"))
    peak = max((n for _, n in s.weeks), default=0) or 1
    n = len(s.weeks)
    pts = [(ax0 + i * (ax1 - ax0) / max(n - 1, 1), ay_base - v / peak * (ay_base - ay_top)) for i, (_, v) in enumerate(s.weeks)]
    for gy in (ay_top, (ay_top + ay_base) / 2, ay_base):
        doc.add(f'<path d="M{ax0} {fmt(gy)}H{ax1}" stroke="{t["border"]}" stroke-dasharray="{"0" if gy == ay_base else "2 5"}"/>')
    line = _smooth(pts)
    gradient(doc, "area", [(0, t["violet"], 0.32), (1, t["violet"], 0)], x2=0, y2=1)
    doc.add(f'<path d="{line}L{ax1} {ay_base}L{ax0} {ay_base}Z" fill="url(#area)"/>')
    doc.add(f'<path d="{line}" stroke="{brand}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')
    pi = max(range(n), key=lambda i: s.weeks[i][1])
    px, py = pts[pi]
    doc.add(f'<circle cx="{fmt(px)}" cy="{fmt(py)}" r="4.5" fill="{t["bg"]}" stroke="{t["mint"]}" stroke-width="2.2"/>')
    lab = f"peak {s.weeks[pi][1]}"
    anchor = "end" if px > ax1 - 80 else "start"
    doc.add(doc.text(px + (-10 if anchor == "end" else 10), py - 10, lab, "mono", 13, t["mint"], anchor=anchor))
    last_x = -99.0
    for i, (d, _) in enumerate(s.weeks):
        if i == 0 or d.month != s.weeks[i - 1][0].month:
            x = pts[i][0]
            if x - last_x >= 44 and x <= ax1 - 24:
                doc.add(doc.text(x, ay_base + 20, d.strftime("%b"), "mono", 12.5, t["dim"]))
                last_x = x

    # ---- languages
    ly = 272
    doc.add(doc.text(ax0, ly, "TOP LANGUAGES", "mono", 13, t["muted"], ls=1.4))
    langs = s.languages[:6]
    other = 1 - sum(p for _, _, p in langs)
    if other > 0.005:
        langs = langs + [("Other", t["dim"], other)]
    bx, bw, by = ax0, ax1 - ax0, ly + 14
    clip_round(doc, "bar", bx, by, bw, 10, 5)
    doc.add('<g clip-path="url(#bar)">')
    x = bx
    for name, colour, p in langs:
        w = bw * p
        doc.add(f'<rect x="{fmt(x)}" y="{by}" width="{fmt(w + 0.6)}" height="10" fill="{colour}"/>')
        x += w
    doc.add("</g>")
    x, y = ax0, by + 40
    for name, colour, p in langs:
        label = f"{name} {p * 100:.1f}%"
        w = 16 + text_width(label, "mono", 13.5) + 22
        if x + w > ax1:
            x, y = ax0, y + 26
        doc.add(f'<circle cx="{fmt(x + 5)}" cy="{fmt(y - 4)}" r="5" fill="{legible(colour, t["bg"], colour, 0)}"/>')
        doc.add(doc.spans(x + 16, y, [(name + " ", t["text"]), (f"{p * 100:.1f}%", t["muted"])], "mono", 13.5))
        x += w

    # ---- footer
    doc.add(doc.text(32, H - 26, f"synced {s.synced:%Y-%m-%d %H:%M} UTC · GitHub GraphQL API", "mono", 12.5, t["dim"]))
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path("dist"))
    ap.add_argument("--sample", action="store_true", help="render with deterministic fake data (offline)")
    args = ap.parse_args()

    if args.sample:
        stats = sample()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("GITHUB_TOKEN is required (or pass --sample)", file=sys.stderr)
            return 2
        exclude = {x.strip() for x in os.environ.get("EXCLUDE_LANGUAGES", "").split(",") if x.strip()}
        stats = summarise(fetch(C.LOGIN, token), os.environ.get("INCLUDE_PRIVATE") == "1", exclude)

    args.out.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        svg = render(stats, theme).render()
        minidom.parseString(svg)
        (args.out / f"telemetry-{theme}.svg").write_text(svg, encoding="utf-8")
    print(f"telemetry: {stats.total} contributions, streak {stats.current_streak}d → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
