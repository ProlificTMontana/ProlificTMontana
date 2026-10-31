"""Design system for the profile: themes, typography, icons and SVG primitives.

Every asset is rendered twice (dark + light) from the same code path so the
README can swap them with <picture> + prefers-color-scheme. Fonts are
subset per-file to only the glyphs that file uses and embedded as WOFF2, so
each SVG renders identically everywhere without network access (GitHub's
image proxy blocks external font loads).
"""

from __future__ import annotations

import base64
import io
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "fonts"

# --------------------------------------------------------------------------
# Themes
# --------------------------------------------------------------------------

# Palette aligned with tony-github-io.vercel.app (lime #BEFF3D) and
# tonylinktech.co.za (neon #39FF14, mint #ABFF9C) on green-black.
THEMES: dict[str, dict] = {
    "dark": {
        "bg": "#0a0f0d",
        "surface": "#0f1613",
        "surface2": "#131c17",
        "border": "#1a2620",
        "border2": "#28392e",
        "text": "#ecf5e9",
        "muted": "#97a89b",
        "dim": "#5c6d61",
        "grid": "#1a2820",
        "primary": "#beff3d",  # portfolio lime
        "neon": "#39ff14",  # TLT neon green
        "soft": "#abff9c",  # TLT mint
        "signal": "#39ff14",  # live / status / cursor
        "warn": "#ffc247",
        "on_accent": "#08110a",  # text on filled accent surfaces
        "glow": 0.22,
        "chip": "#0e1511",
        # monochrome ramp for data series (languages)
        "ramp": ("#beff3d", "#39ff14", "#abff9c", "#7cc42a", "#22b60c", "#6e9c74", "#3d5a45"),
    },
    "light": {
        "bg": "#ffffff",
        "surface": "#f6faf3",
        "surface2": "#edf5e8",
        "border": "#dce8d5",
        "border2": "#c2d5b7",
        "text": "#0a140c",
        "muted": "#4b5d4f",
        "dim": "#84958a",
        "grid": "#d9e6d1",
        "primary": "#4c7a00",
        "neon": "#14930a",
        "soft": "#0d7a45",
        "signal": "#11990f",
        "warn": "#b06a00",
        "on_accent": "#ffffff",
        "glow": 0.13,
        "chip": "#f1f8ec",
        "ramp": ("#4c7a00", "#14930a", "#0d7a45", "#8bb83a", "#5fa356", "#2f5e36", "#a8bfa2"),
    },
}

MOTION_CSS = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


# --------------------------------------------------------------------------
# Typography
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Face:
    key: str  # css class
    family: str  # css family name used inside the SVG
    weight: int
    file: str
    fallback: str

    @property
    def path(self) -> Path:
        return FONT_DIR / self.file


FACES = {
    "display": Face("d7", "TT Display", 700, "SpaceGrotesk-700.woff2", "'Segoe UI',Helvetica,Arial,sans-serif"),
    "body": Face("d5", "TT Display", 500, "SpaceGrotesk-500.woff2", "'Segoe UI',Helvetica,Arial,sans-serif"),
    "mono": Face("m4", "TT Mono", 400, "JetBrainsMono-400.woff2", "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"),
    "monob": Face("m7", "TT Mono", 700, "JetBrainsMono-700.woff2", "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"),
}


@lru_cache(maxsize=None)
def _font(face_name: str) -> TTFont:
    return TTFont(FACES[face_name].path)


@lru_cache(maxsize=None)
def _metrics(face_name: str) -> tuple[dict[int, int], int]:
    font = _font(face_name)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"].metrics
    upm = font["head"].unitsPerEm
    advances = {cp: hmtx[g][0] for cp, g in cmap.items()}
    return advances, upm


def has_glyph(face_name: str, ch: str) -> bool:
    return ord(ch) in _metrics(face_name)[0]


def text_width(s: str, face_name: str, size: float, ls: float = 0.0) -> float:
    advances, upm = _metrics(face_name)
    fallback = advances.get(ord("M"), upm // 2)
    units = sum(advances.get(ord(c), fallback) for c in s)
    return units * size / upm + ls * max(len(s) - 1, 0)


def wrap(s: str, face_name: str, size: float, max_width: float) -> list[str]:
    words, lines, line = s.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if line and text_width(trial, face_name, size) > max_width:
            lines.append(line)
            line = w
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


@lru_cache(maxsize=None)
def _font_face_css(face_name: str, chars: str) -> str:
    face = FACES[face_name]
    missing = [c for c in chars if not c.isspace() and not has_glyph(face_name, c)]
    if missing:
        raise ValueError(f"{face.file} is missing glyphs for {missing!r}")
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern"]
    opts.name_IDs = []
    opts.notdef_outline = True
    opts.hinting = False
    opts.desubroutinize = True
    font = TTFont(face.path, recalcTimestamp=False)  # keep output byte-for-byte reproducible
    sub = subset.Subsetter(options=opts)
    sub.populate(text=chars)
    sub.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (
        f"@font-face{{font-family:'{face.family}';font-weight:{face.weight};"
        f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
    )


# --------------------------------------------------------------------------
# Icons (simple-icons, CC0) and colour helpers
# --------------------------------------------------------------------------


@lru_cache(maxsize=None)
def icons() -> dict[str, dict[str, str]]:
    return json.loads((ROOT / "icons.json").read_text())["icons"]


def _rgb(hex_: str) -> tuple[float, float, float]:
    h = hex_.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _lum(hex_: str) -> float:
    def ch(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (ch(c) for c in _rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_palette() -> None:
    """Fail the build if a theme edit breaks WCAG contrast on card surfaces."""
    rules = {"text": 4.5, "muted": 4.5, "primary": 3.0, "neon": 3.0, "soft": 3.0, "signal": 3.0, "warn": 3.0}
    for name, t in THEMES.items():
        for key, minimum in rules.items():
            ratio = contrast(t[key], t["surface"])
            if ratio < minimum:
                raise ValueError(f"{name}.{key} {t[key]} is {ratio:.2f}:1 on surface (needs {minimum}:1)")
        if contrast(t["on_accent"], t["primary"]) < 4.5:
            raise ValueError(f"{name}.on_accent is not legible on primary")


# --------------------------------------------------------------------------
# SVG document
# --------------------------------------------------------------------------


def fmt(n: float) -> str:
    return f"{n:.2f}".rstrip("0").rstrip(".")


@dataclass
class SVG:
    width: int
    height: int
    theme: str
    title: str
    desc: str = ""
    css: list[str] = field(default_factory=list)
    defs: list[str] = field(default_factory=list)
    body: list[str] = field(default_factory=list)
    _used: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    @property
    def t(self) -> dict:
        return THEMES[self.theme]

    def add(self, *parts: str) -> None:
        self.body.extend(parts)

    def text(
        self,
        x: float,
        y: float,
        s: str,
        face: str = "body",
        size: float = 16,
        fill: str | None = None,
        anchor: str = "start",
        ls: float = 0,
        attrs: str = "",
    ) -> str:
        self._used[face].update(s)
        fill = fill or self.t["text"]
        spacing = f' letter-spacing="{fmt(ls)}"' if ls else ""
        anch = f' text-anchor="{anchor}"' if anchor != "start" else ""
        return (
            f'<text x="{fmt(x)}" y="{fmt(y)}" class="{FACES[face].key}" font-size="{fmt(size)}"'
            f' fill="{fill}"{anch}{spacing}{(" " + attrs) if attrs else ""}>{escape(s)}</text>'
        )

    def spans(
        self,
        x: float,
        y: float,
        parts: list[tuple[str, str]],
        face: str = "mono",
        size: float = 16,
        attrs: str = "",
        xml_space: bool = True,
    ) -> str:
        """A single line made of differently coloured runs."""
        inner = []
        for s, fill in parts:
            self._used[face].update(s)
            inner.append(f'<tspan fill="{fill}">{escape(s)}</tspan>')
        space = ' xml:space="preserve"' if xml_space else ""
        return (
            f'<text x="{fmt(x)}" y="{fmt(y)}" class="{FACES[face].key}" font-size="{fmt(size)}"'
            f'{space}{(" " + attrs) if attrs else ""}>{"".join(inner)}</text>'
        )

    def use_chars(self, face: str, s: str) -> None:
        self._used[face].update(s)

    def render(self) -> str:
        font_css = []
        classes = []
        for name in sorted(self._used):
            chars = "".join(sorted(self._used[name] - {" "})) + " "
            font_css.append(_font_face_css(name, chars))
            f = FACES[name]
            classes.append(f".{f.key}{{font-family:'{f.family}',{f.fallback};font-weight:{f.weight}}}")
        style = "".join(font_css + classes + self.css + [MOTION_CSS])
        desc = f"<desc>{escape(self.desc)}</desc>" if self.desc else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}"'
            f' viewBox="0 0 {self.width} {self.height}" fill="none" role="img" aria-labelledby="t">'
            f'<title id="t">{escape(self.title)}</title>{desc}'
            f"<style>{style}</style>"
            f"<defs>{''.join(self.defs)}</defs>"
            f"{''.join(self.body)}</svg>\n"
        )


# --------------------------------------------------------------------------
# Reusable building blocks
# --------------------------------------------------------------------------


def card(doc: SVG, x: float, y: float, w: float, h: float, r: float = 20, fill: str | None = None) -> None:
    t = doc.t
    doc.add(
        f'<rect x="{fmt(x + 0.5)}" y="{fmt(y + 0.5)}" width="{fmt(w - 1)}" height="{fmt(h - 1)}" rx="{r}"'
        f' fill="{fill or t["bg"]}" stroke="{t["border"]}"/>'
    )


def gradient(doc: SVG, gid: str, stops: list[tuple[float, str, float]], x2: float = 1, y2: float = 0) -> None:
    s = "".join(f'<stop offset="{fmt(o)}" stop-color="{c}" stop-opacity="{fmt(a)}"/>' for o, c, a in stops)
    doc.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="{fmt(x2)}" y2="{fmt(y2)}">{s}</linearGradient>')


def brand_gradient(doc: SVG, gid: str = "brand") -> str:
    t = doc.t
    gradient(doc, gid, [(0, t["primary"], 1), (0.5, t["neon"], 1), (1, t["soft"], 1)])
    return f"url(#{gid})"


def glow(doc: SVG, gid: str, cx: float, cy: float, r: float, color: str, strength: float = 1.0) -> None:
    a = float(doc.t["glow"]) * strength
    doc.defs.append(
        f'<radialGradient id="{gid}" cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{color}" stop-opacity="{fmt(a)}"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'
    )
    doc.add(f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="url(#{gid})"/>')


def dot_grid(doc: SVG, clip_id: str, x: float, y: float, w: float, h: float, cx: float, cy: float, r: float) -> None:
    """Dot grid that fades out radially from (cx, cy)."""
    t = doc.t
    doc.defs.append(
        f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
        f'<circle cx="1.5" cy="1.5" r="1.2" fill="{t["grid"]}"/></pattern>'
        f'<radialGradient id="dotfade" cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        f'<mask id="dotmask"><rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="url(#dotfade)"/></mask>'
    )
    doc.add(
        f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="url(#dots)"'
        f' mask="url(#dotmask)" clip-path="url(#{clip_id})"/>'
    )


def clip_round(doc: SVG, cid: str, x: float, y: float, w: float, h: float, r: float) -> None:
    doc.defs.append(
        f'<clipPath id="{cid}"><rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="{fmt(r)}"/></clipPath>'
    )


def chip(
    doc: SVG, x: float, y: float, label: str, face: str = "mono", size: float = 12.5,
    color: str | None = None, pad: float = 10, h: float = 26, stroke: str | None = None,
) -> float:
    """Draw a pill and return its width."""
    t = doc.t
    w = text_width(label, face, size) + pad * 2
    doc.add(
        f'<rect x="{fmt(x + 0.5)}" y="{fmt(y + 0.5)}" width="{fmt(w - 1)}" height="{fmt(h - 1)}" rx="{fmt(h / 2)}"'
        f' fill="{t["chip"]}" stroke="{stroke or t["border2"]}"/>',
        doc.text(x + w / 2, y + h / 2 + size * 0.36, label, face, size, color or t["muted"], anchor="middle"),
    )
    return w


def icon(doc: SVG, slug: str, x: float, y: float, size: float, color: str) -> None:
    path = icons()[slug]["path"]
    s = size / 24
    doc.add(f'<path transform="translate({fmt(x)} {fmt(y)}) scale({fmt(s)})" fill="{color}" d="{path}"/>')


def monogram(doc: SVG, label: str, x: float, y: float, size: float, color: str) -> None:
    doc.add(
        f'<rect x="{fmt(x + 0.75)}" y="{fmt(y + 0.75)}" width="{fmt(size - 1.5)}" height="{fmt(size - 1.5)}"'
        f' rx="{fmt(size * 0.26)}" stroke="{color}" stroke-width="1.5"/>'
    )
    fs = size * (0.5 if len(label) <= 2 else 0.4)
    doc.add(doc.text(x + size / 2, y + size / 2 + fs * 0.36, label, "monob", fs, color, anchor="middle"))


def pulse_dot(doc: SVG, cx: float, cy: float, color: str, r: float = 4.5, delay: float = 0) -> None:
    doc.add(
        f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="{color}"/>'
        f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="none" stroke="{color}" stroke-width="1.5">'
        f'<animate attributeName="r" values="{fmt(r)};{fmt(r * 3)}" dur="2s" begin="{fmt(delay)}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0.9;0" dur="2s" begin="{fmt(delay)}s" repeatCount="indefinite"/>'
        f"</circle>"
    )


def polar(cx: float, cy: float, r: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)
