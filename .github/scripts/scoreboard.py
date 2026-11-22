"""Draws assets/scoreboard.svg: a cricket scoreboard built from live GitHub numbers.

Runs = contributions in the last year, overs = days with at least one contribution.
Run with GITHUB_TOKEN set (the daily workflow does this), or pass a saved GraphQL
response as the first argument to draw from that instead.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

from pixel import GOLD, LIME, RED, esc, notch, save, text_width

LOGIN = "raj06872436"
OUT = os.path.join(os.environ.get("OUT_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "assets")), "scoreboard.svg")
QUERY = """query($login:String!){user(login:$login){
  contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
  repositories(privacy:PUBLIC, ownerAffiliations:OWNER, first:5, orderBy:{field:PUSHED_AT, direction:DESC}){
    totalCount nodes{name pushedAt}}}}"""

NAMES = {"AI_Farming_Project": "AGRI-X", "MARKET_PULSE": "MARKETPULSE", "restaurant_ai": "TABLESENSE",
         "cricket-speed-gun": "SPEED GUN", "AI-final-project-": "FRAUD LAB", "history-research-helper": "HISTORY",
         "leetcode-github-sync": "LC SYNC", "leetcode-solutions": "LEETCODE", "SOULPRINT": "SOULPRINT"}


def fetch():
    if len(sys.argv) > 1:
        return json.load(open(sys.argv[1]))
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req))


def stats(data):
    user = data["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    active = [d for d in days if d[1] > 0]
    best = max(days, key=lambda d: d[1])
    streak, i = 0, len(days) - 1
    if days[i][1] == 0:
        i -= 1  # today isn't over yet
    while i >= 0 and days[i][1] > 0:
        streak += 1
        i -= 1
    repos = user["repositories"]
    last = next((r for r in repos["nodes"] if r["name"] != LOGIN), None)
    return dict(runs=cal["totalContributions"], overs=len(active), best=best, streak=streak,
                repos=repos["totalCount"], last=last)


def fmt_date(iso):
    d = dt.date.fromisoformat(iso[:10])
    return d.strftime("%d %b").upper()


def cell(x, y, w, label, value, col, big=False):
    h = 120 if big else 96
    fs = 52 if big else 26
    fs = min(fs, int(fs * (w - 36) / max(text_width(value, fs), 1)))
    return (f'<path d="{notch(x, y, w, h, 4)}" fill="#0a2418" stroke="#1f5c3f" stroke-width="2"/>'
            f'<text x="{x+16}" y="{y+28}" class="p" font-size="11" fill="#9fd8b4">{esc(label)}</text>'
            f'<text x="{x+16}" y="{y+h-20}" class="p" font-size="{fs}" fill="{col}" filter="url(#bulb)">{esc(value)}</text>')


def draw(s):
    W, H = 1200, 420
    rate = s["runs"] / s["overs"] if s["overs"] else 0
    last = s["last"]
    last_txt = f'{NAMES.get(last["name"], last["name"].upper())[:12]}  {fmt_date(last["pushedAt"])}' if last else "-"
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30)))
    cells = (
        cell(40, 92, 380, "TOTAL RUNS (CONTRIBUTIONS)", f'{s["runs"]}', GOLD, big=True)
        + cell(436, 92, 230, "OVERS (ACTIVE DAYS)", f'{s["overs"]}', "#ffffff", big=True)
        + cell(682, 92, 230, "RUN RATE", f"{rate:.1f}", LIME, big=True)
        + cell(928, 92, 232, "TEAM (REPOS)", f'{s["repos"]}', "#ffffff", big=True)
        + cell(40, 228, 330, "BEST OVER (ONE DAY)", f'{s["best"][1]} ON {fmt_date(s["best"][0])}', GOLD)
        + cell(386, 228, 250, "CURRENT STREAK", (f'{s["streak"]} DAY{"" if s["streak"] == 1 else "S"}' if s["streak"] else "WARMING UP"), LIME)
        + cell(652, 228, 508, "LAST BALL (LATEST PUSH)", last_txt, "#ffffff")
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.live{{animation:lv 1.2s steps(1) infinite}}@keyframes lv{{50%{{opacity:.15}}}}
.scan{{animation:sc 4s linear infinite}}@keyframes sc{{from{{transform:translateY(-40px)}}to{{transform:translateY(420px)}}}}
</style>
<defs>
<filter id="bulb" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<pattern id="dots" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="2" height="2" fill="#ffffff" opacity=".05"/></pattern>
<clipPath id="c"><path d="{notch(10, 10, W-20, 370, 10)}"/></clipPath>
</defs>
<rect x="150" y="370" width="30" height="50" fill="#5b3a1e"/><rect x="1020" y="370" width="30" height="50" fill="#5b3a1e"/>
<path d="{notch(16, 18, W-20, 370, 10)}" fill="#000" opacity=".3"/>
<path d="{notch(10, 10, W-20, 370, 10)}" fill="#0f3d2a"/>
<g clip-path="url(#c)">
<rect x="10" y="10" width="{W-20}" height="370" fill="url(#dots)"/>
<rect class="scan" x="10" y="0" width="{W-20}" height="30" fill="#ffffff" opacity=".03"/>
</g>
<path d="{notch(10, 10, W-20, 370, 10)}" fill="none" stroke="#e8c36a" stroke-width="5"/>
<text x="40" y="66" class="p" font-size="24" fill="#ffffff">RAJ XI</text>
<text x="224" y="66" class="p" font-size="14" fill="#9fd8b4">VS</text>
<text x="272" y="66" class="p" font-size="24" fill="#ffffff">THE BUGS</text>
<circle class="live" cx="824" cy="56" r="8" fill="{RED}"/>
<text x="842" y="64" class="p" font-size="16" fill="{RED}">LIVE</text>
<text x="1160" y="64" text-anchor="end" class="v" font-size="22" fill="#9fd8b4">last 12 months</text>
{cells}
<text x="40" y="358" class="v" font-size="22" fill="#9fd8b4">Updated {now.strftime('%d %b %Y, %I:%M %p')} IST from GitHub. Scores update every day.</text>
</svg>"""
    save(OUT, svg)


if __name__ == "__main__":
    draw(stats(fetch()))
    print("scoreboard ok")
