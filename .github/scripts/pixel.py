"""Shared helpers for the profile's pixel art: palettes, shapes and text drawn as vector paths."""
import html
import os
import re

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))

NIGHT, INK = "#140c2b", "#f4f1ff"
PINK, CYAN, GOLD, LIME, RED = "#ff3ea5", "#2de2e6", "#ffd319", "#7cff6b", "#ff5a4e"

THEMES = {
    "dark": dict(name="dark", panel=NIGHT, card="#22174d", line="#3a2d70", ink=INK, sub="#b9addf",
                 gold=GOLD, pink=PINK, cyan=CYAN, lime=LIME, empty="#3a2d70"),
    "light": dict(name="light", panel="#fff4d6", card="#ffffff", line="#ecd9a6", ink="#1b1340", sub="#6b5f99",
                  gold="#a35a00", pink="#c0156a", cyan="#0b6f80", lime="#2f8f1f", empty="#e8dcb8"),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def notch(x, y, w, h, s):
    """Rectangle path with stepped pixel corners."""
    return (f"M{x+2*s} {y}H{x+w-2*s}V{y+s}H{x+w-s}V{y+2*s}H{x+w}V{y+h-2*s}H{x+w-s}V{y+h-s}H{x+w-2*s}V{y+h}"
            f"H{x+2*s}V{y+h-s}H{x+s}V{y+h-2*s}H{x}V{y+2*s}H{x+s}V{y+s}H{x+2*s}Z")


def pix(rows, colors, x0, y0, s, extra=""):
    out = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in colors:
                out.append(f'<rect x="{x0+c*s}" y="{y0+r*s}" width="{s}" height="{s}" fill="{colors[ch]}"{extra}/>')
    return "".join(out)


class _Glyphs:
    def __init__(self, file, key):
        self.font = TTFont(os.path.join(HERE, "fonts", file))
        self.key = key
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.upem = self.font["head"].unitsPerEm
        self.cache = {}

    def path(self, name):
        if name not in self.cache:
            pen = SVGPathPen(self.glyphs)
            self.glyphs[name].draw(pen)
            self.cache[name] = pen.getCommands()
        return self.cache[name]


_FONTS = {"p": _Glyphs("ps2p.woff2", "a"), "v": _Glyphs("vt.woff2", "b")}
_TEXT = re.compile(r"<text([^>]*)>(.*?)</text>", re.S)


def _attr(a, k, default=None):
    m = re.search(rf'(?<![\w-]){k}="([^"]*)"', a)
    return m.group(1) if m else default


def text_width(s, size, font="p"):
    g = _FONTS[font]
    hm = g.font["hmtx"]
    return sum(hm[g.cmap[ord(c)]][0] for c in s if ord(c) in g.cmap) * size / g.upem


def to_paths(svg):
    """Turn every <text class="p|v"> into glyph paths, so it renders the same everywhere."""
    used = {}

    def rep(m):
        a, content = m.group(1), html.unescape(m.group(2))
        classes = _attr(a, "class", "v").split()
        fk = "p" if "p" in classes else "v"
        extra = " ".join(c for c in classes if c not in ("p", "v"))
        g = _FONTS[fk]
        size = float(_attr(a, "font-size"))
        k = size / g.upem
        x, y = float(_attr(a, "x", "0")), float(_attr(a, "y", "0"))
        hm = g.font["hmtx"]
        adv, uses = 0, []
        for ch in content:
            name = g.cmap.get(ord(ch))
            if name is None:
                continue
            if g.path(name):
                gid = f"{g.key}{name}"
                used[gid] = g.path(name)
                uses.append(f'<use href="#{gid}" x="{adv}"/>')
            adv += hm[name][0]
        anchor = _attr(a, "text-anchor", "start")
        if anchor == "middle":
            x -= adv * k / 2
        elif anchor == "end":
            x -= adv * k
        op = _attr(a, "opacity")
        o = f' opacity="{op}"' if op else ""
        c = f' class="{extra}"' if extra else ""
        return (f'<g{c}{o} fill="{_attr(a, "fill", "#000")}"><g transform="translate({x:.1f} {y:.1f}) '
                f'scale({k:.5f} {-k:.5f})">{"".join(uses)}</g></g>')

    svg = _TEXT.sub(rep, svg)
    defs = "<defs>" + "".join(f'<path id="{i}" d="{d}"/>' for i, d in used.items()) + "</defs>"
    head = re.match(r"<svg[^>]*>", svg).group(0)
    return head + defs + svg[len(head):]


def save(path, svg):
    with open(path, "w") as f:
        f.write(to_paths(svg))
