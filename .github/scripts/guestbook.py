"""Keeps the guestbook (guestbook.json) and draws guestbook-dark.svg and guestbook-light.svg.

Visitors open a "Guestbook:" issue from the form. It only appears on the profile once Raj
adds the "approved" label, so nothing shows up without his say.
"""
import datetime as dt
import json
import os
import re
import sys

from pixel import GOLD, LIME, PINK, CYAN, THEMES, esc, notch, save

OUT_DIR = os.environ.get("OUT_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
DATA = os.path.join(OUT_DIR, "guestbook.json")
KEEP = 8


def clean(s, n):
    s = re.sub(r"[^A-Za-z0-9 .,!?'&:()+#@-]", "", s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s[:n]


def field(body, label):
    m = re.search(rf"###\s*{label}\s*\n+(.*?)(?:\n###|\Z)", body or "", re.S | re.I)
    v = m.group(1).strip() if m else ""
    return "" if v == "_No response_" else v


def add_from_event():
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or os.environ.get("GITHUB_EVENT_NAME") != "issues":
        return False
    ev = json.load(open(path))
    issue = ev.get("issue", {})
    if ev.get("label", {}).get("name") != "approved" or not issue.get("title", "").lower().startswith("guestbook"):
        return False
    login = issue["user"]["login"]
    name = clean(field(issue.get("body"), "Name"), 12) or clean(login, 12)
    msg = clean(field(issue.get("body"), "Message"), 34) or "Was here!"
    entries = load()
    if any(e.get("issue") == issue["number"] for e in entries):
        return False
    entries.insert(0, {"name": name.upper(), "msg": msg, "login": login,
                       "date": issue["created_at"][:10], "issue": issue["number"]})
    json.dump(entries[:50], open(DATA, "w"), indent=1)
    return True


def load():
    try:
        return json.load(open(DATA))
    except (OSError, ValueError):
        return []


def draw(entries, T):
    W, H = 1200, 450
    cols = [GOLD, CYAN, PINK, LIME]
    rows = ""
    for i in range(KEEP):
        y = 150 + i * 36
        col = T["acc"](cols[i % 4]) if "acc" in T else cols[i % 4]
        if i < len(entries):
            e = entries[i]
            d = dt.date.fromisoformat(e["date"]).strftime("%d %b").upper()
            rows += (f'<text x="60" y="{y}" class="p" font-size="16" fill="{col}">{i+1:>2}.</text>'
                     f'<text x="130" y="{y}" class="p" font-size="16" fill="{col}">{esc(e["name"])}</text>'
                     f'<text x="380" y="{y}" class="v" font-size="28" fill="{T["ink"]}">{esc(e["msg"])}</text>'
                     f'<text x="1140" y="{y}" text-anchor="end" class="p" font-size="13" fill="{T["sub"]}">{d}</text>')
        else:
            blink = ' class="p blink"' if i == len(entries) else ' class="p"'
            label = "YOUR NAME HERE" if i == len(entries) else "- - - - - -"
            rows += (f'<text x="60" y="{y}" class="p" font-size="16" fill="{T["sub"]}" opacity=".6">{i+1:>2}.</text>'
                     f'<text x="130" y="{y}"{blink} font-size="16" fill="{T["sub"]}" opacity=".8">{label}</text>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>.blink{{animation:b 1s steps(1) infinite}}@keyframes b{{50%{{opacity:0}}}}</style>
<path d="{notch(6, 10, W-6, H-10, 12)}" fill="#000" opacity=".2"/>
<path d="{notch(0, 0, W-6, H-10, 12)}" fill="{T["panel"]}" stroke="{GOLD}" stroke-width="4"/>
<text x="{(W-6)//2}" y="60" text-anchor="middle" class="p" font-size="26" fill="{T["gold"]}">GUESTBOOK HIGH SCORES</text>
<text x="{(W-6)//2}" y="96" text-anchor="middle" class="v" font-size="26" fill="{T["sub"]}">sign it and your name joins the board</text>
<rect x="40" y="112" width="{W-86}" height="3" fill="{T["line"]}"/>
{rows}
</svg>"""
    save(os.path.join(OUT_DIR, f"guestbook-{T['name']}.svg"), svg)


if __name__ == "__main__":
    changed = add_from_event()
    entries = load()
    acc = {"light": {GOLD: "#a35a00", CYAN: "#0b6f80", PINK: "#c0156a", LIME: "#2f8f1f"}}
    for name, T in THEMES.items():
        T = dict(T, acc=lambda c, n=name: acc.get(n, {}).get(c, c))
        draw(entries[:KEEP], T)
    print("guestbook updated" if changed else "guestbook drawn")
    if changed and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write("added=true\n")
