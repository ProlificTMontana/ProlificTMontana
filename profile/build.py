"""Render every static profile asset (dark + light) into ../assets.

    python profile/build.py

Output is deterministic, so CI can verify committed assets are up to date.
"""

from __future__ import annotations

import html
import math
import sys
from collections.abc import Callable
from pathlib import Path
from xml.dom import minidom

import content as C
from design import (
    SVG,
    brand_gradient,
    card,
    check_palette,
    chip,
    clip_round,
    dot_grid,
    fmt,
    glow,
    gradient,
    icon,
    monogram,
    polar,
    pulse_dot,
    text_width,
    wrap,
)

ASSETS = Path(__file__).resolve().parent.parent / "assets"
BLINK_CSS = "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:blink 1.1s steps(1) infinite}"


# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------


def hero(theme: str) -> SVG:
    W, H = 1200, 420
    doc = SVG(W, H, theme, f"{C.NAME} — {C.ROLES[0]} & {C.ROLES[1]}",
              f"{C.LOCATION}. " + " ".join(C.TAGLINES))
    t = doc.t
    doc.css += [BLINK_CSS]
    clip_round(doc, "cc", 0, 0, W, H, 24)
    card(doc, 0, 0, W, H, 24)
    doc.add('<g clip-path="url(#cc)">')
    glow(doc, "g1", 120, -40, 560, t["neon"], 1.0)
    glow(doc, "g2", 1060, 470, 600, t["neon"], 1.0)
    glow(doc, "g3", 940, 210, 260, t["soft"], 0.7)
    dot_grid(doc, "cc", 0, 0, W, H, 940, 210, 560)
    # slow scanline
    gradient(doc, "scan", [(0, t["signal"], 0), (0.5, t["signal"], 0.07), (1, t["signal"], 0)], x2=0, y2=1)
    doc.add(
        f'<rect x="0" y="-140" width="{W}" height="140" fill="url(#scan)">'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {H + 140}" dur="7s" repeatCount="indefinite"/></rect>'
    )
    doc.add("</g>")

    # ---- status pill
    x0 = 64
    label = C.STATUS
    pw = text_width(label, "mono", 13.5, 1.4) + 50
    doc.add(
        f'<rect x="{x0}.5" y="50.5" width="{fmt(pw)}" height="35" rx="17.5" fill="{t["surface"]}" stroke="{t["border2"]}"/>'
    )
    pulse_dot(doc, x0 + 19, 68, t["signal"], 4.2)
    doc.add(doc.text(x0 + 34, 72.8, label, "mono", 13.5, t["muted"], ls=1.4))

    # ---- name + roles
    first, _, last = C.NAME.partition(" ")
    lead = text_width(first + " ", "display", 88, -3)
    blur = 7 if theme == "dark" else 0
    if blur:
        doc.defs.append(
            f'<filter id="neon" x="-20%" y="-40%" width="140%" height="180%">'
            f'<feGaussianBlur stdDeviation="{blur}" result="b"/>'
            f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        )
    doc.add(doc.text(x0 - 4, 180, first, "display", 88, t["text"], ls=-3))
    doc.add(doc.text(x0 - 4 + lead, 180, last, "display", 88, t["primary"], ls=-3,
                     attrs='filter="url(#neon)"' if blur else ""))
    brand = brand_gradient(doc, "brand")
    doc.add(doc.spans(x0, 232, [(C.ROLES[0], brand), ("  /  ", t["dim"]), (C.ROLES[1], brand)], "body", 30))

    # ---- typing prompt
    py, ph = 272, 52
    prompt = [("tony@tlt", t["signal"]), (":", t["dim"]), ("~", t["soft"]), ("$ ", t["muted"])]
    psize = 18
    prompt_w = text_width("".join(s for s, _ in prompt), "mono", psize)
    adv = text_width("M", "mono", psize)
    longest = max(len(s) for s in C.TAGLINES)
    box_w = 22 + prompt_w + adv * (longest + 1) + 22
    doc.add(
        f'<rect x="{x0}.5" y="{py}.5" width="{fmt(box_w)}" height="{ph - 1}" rx="12" fill="{t["surface"]}"'
        f' fill-opacity="0.85" stroke="{t["border2"]}"/>'
    )
    base_y = py + ph / 2 + psize * 0.36
    doc.add(doc.spans(x0 + 22, base_y, prompt, "mono", psize))
    tx = x0 + 22 + prompt_w
    T, slot = 15.0, 5.0
    step = 0.055
    cursor_kf: list[tuple[float, float]] = []
    for i, line in enumerate(C.TAGLINES):
        n = len(line)
        start = i * slot
        kf = [(0.0, 0.0)] if i else []
        for k in range(1, n + 1):
            kf.append((start + k * step, adv * k))
        kf.append((start + slot - 0.6, 0.0))
        if i == 0:
            kf.insert(0, (0.0, 0.0))
        cursor_kf += [(tm, w) for tm, w in kf if not (i and tm == 0.0)]
        times = ";".join(fmt(tm / T) for tm, _ in kf)
        vals = ";".join(fmt(w) for _, w in kf)
        static_w = fmt(adv * n + 2) if i == 0 else "0"
        doc.defs.append(
            f'<clipPath id="tl{i}"><rect x="{fmt(tx)}" y="{py}" height="{ph}" width="{static_w}">'
            f'<animate attributeName="width" calcMode="discrete" dur="{fmt(T)}s" repeatCount="indefinite"'
            f' keyTimes="{times}" values="{vals}"/></rect></clipPath>'
        )
        doc.add(doc.text(tx, base_y, line, "mono", psize, t["text"], attrs=f'clip-path="url(#tl{i})"'))
    cursor_kf.sort()
    ck_t = ";".join(fmt(tm / T) for tm, _ in cursor_kf)
    ck_v = ";".join(fmt(tx + w + 2) for _, w in cursor_kf)
    doc.add(
        f'<rect class="cur" x="{fmt(tx + adv * len(C.TAGLINES[0]) + 2)}" y="{fmt(base_y - psize * 0.8)}" width="{fmt(adv * 0.62)}"'
        f' height="{fmt(psize * 1.05)}" rx="1.5" fill="{t["signal"]}">'
        f'<animate attributeName="x" calcMode="discrete" dur="{fmt(T)}s" repeatCount="indefinite" keyTimes="{ck_t}" values="{ck_v}"/></rect>'
    )

    # ---- capability row
    cx = x0
    for label, color in (("RED TEAM", t["primary"]), ("SECURE SAAS", t["neon"]), ("AUTOMATION", t["soft"]), ("DEVSECOPS", t["signal"])):
        doc.add(f'<rect x="{cx}" y="{366}" width="8" height="8" rx="2" fill="{color}" transform="rotate(45 {cx + 4} 370)"/>')
        doc.add(doc.text(cx + 18, 375, label, "mono", 14, t["muted"], ls=1.6))
        cx += 18 + text_width(label, "mono", 14, 1.6) + 28

    # ---- radar
    rcx, rcy, R = 952, 212, 168
    doc.defs.append(f'<clipPath id="rc"><circle cx="{rcx}" cy="{rcy}" r="{R}"/></clipPath>')
    doc.add(f'<circle cx="{rcx}" cy="{rcy}" r="{R}" fill="{t["bg"]}" fill-opacity="0.55"/>')
    for r in (R, R * 0.75, R * 0.5, R * 0.25):
        sw = 1.4 if r == R else 1
        doc.add(f'<circle cx="{rcx}" cy="{rcy}" r="{fmt(r)}" stroke="{t["border2"]}" stroke-width="{sw}"/>')
    doc.add(
        f'<path d="M{rcx - R} {rcy}H{rcx + R}M{rcx} {rcy - R}V{rcy + R}" stroke="{t["border2"]}" stroke-dasharray="2 6"/>'
    )
    ticks = []
    for d in range(0, 360, 6):
        inner = R - (9 if d % 30 == 0 else 4)
        x1, y1 = polar(rcx, rcy, inner, d)
        x2, y2 = polar(rcx, rcy, R, d)
        ticks.append(f"M{fmt(x1)} {fmt(y1)}L{fmt(x2)} {fmt(y2)}")
    doc.add(f'<path d="{"".join(ticks)}" stroke="{t["dim"]}" stroke-width="1"/>')
    # sweep: fan of thin wedges with falling opacity, trailing behind 0°
    sweep, period = [], 6.0
    for k in range(36):
        a0, a1 = -(k + 1) * 1.6, -k * 1.6
        p0, p1 = polar(rcx, rcy, R, a0), polar(rcx, rcy, R, a1)
        op = 0.34 * (1 - k / 36) ** 1.6
        sweep.append(
            f'<path d="M{rcx} {rcy}L{fmt(p0[0])} {fmt(p0[1])}A{R} {R} 0 0 1 {fmt(p1[0])} {fmt(p1[1])}Z"'
            f' fill="{t["signal"]}" fill-opacity="{fmt(op)}"/>'
        )
    doc.add(
        f'<g clip-path="url(#rc)"><g>{"".join(sweep)}'
        f'<path d="M{rcx} {rcy}H{rcx + R}" stroke="{t["signal"]}" stroke-width="1.6" stroke-opacity="0.9"/>'
        f'<animateTransform attributeName="transform" type="rotate" from="0 {rcx} {rcy}" to="360 {rcx} {rcy}"'
        f' dur="{fmt(period)}s" repeatCount="indefinite"/></g></g>'
    )
    blips = ((38, 0.62, "443/https", t["signal"]), (128, 0.82, "22/ssh", t["warn"]),
             (212, 0.55, "5432/pg", t["soft"]), (300, 0.78, "3389/rdp", t["primary"]))
    for deg, rr, lab, color in blips:
        bx, by = polar(rcx, rcy, R * rr, deg)
        begin = fmt(deg / 360 * period)
        doc.add(
            f'<g opacity="0.35"><circle cx="{fmt(bx)}" cy="{fmt(by)}" r="4" fill="{color}"/>'
            f'<circle cx="{fmt(bx)}" cy="{fmt(by)}" r="9" stroke="{color}" stroke-opacity="0.5"/>'
            + doc.text(bx + 14, by + 4.5, lab, "mono", 13, t["muted"])
            + f'<animate attributeName="opacity" values="1;0.35;0.35" keyTimes="0;0.55;1" dur="{fmt(period)}s"'
            f' begin="{begin}s" repeatCount="indefinite"/></g>'
        )
    # core
    hexp = " ".join(f"{fmt(px)},{fmt(py_)}" for px, py_ in (polar(rcx, rcy, 15, a) for a in range(-90, 270, 60)))
    doc.add(f'<polygon points="{hexp}" fill="{t["bg"]}" stroke="url(#brand)" stroke-width="2"/>')
    doc.add(f'<circle cx="{rcx}" cy="{rcy}" r="3.5" fill="{t["signal"]}"/>')
    # HUD corners
    for x, y, sx, sy in ((752, 28, 1, 1), (1172, 28, -1, 1), (752, 392, 1, -1), (1172, 392, -1, -1)):
        doc.add(f'<path d="M{x} {y + 16 * sy}V{y}H{x + 16 * sx}" stroke="{t["dim"]}" stroke-width="1.5"/>')
    doc.add(doc.text(1150, 50, "SCOPE 10.0.0.0/24", "mono", 12, t["dim"], anchor="end", ls=1.2))
    doc.add(doc.text(1150, 396, "4 SERVICES · 0 UNPATCHED", "mono", 12, t["dim"], anchor="end", ls=1.2))
    return doc


# --------------------------------------------------------------------------
# Section header
# --------------------------------------------------------------------------


def header(theme: str, index: int, title: str, command: str) -> SVG:
    W, H = 1200, 76
    doc = SVG(W, H, theme, f"{index:02d} — {title}")
    t = doc.t
    clip_round(doc, "cc", 0, 0, W, H, 16)
    card(doc, 0, 0, W, H, 16)
    doc.add('<g clip-path="url(#cc)">')
    glow(doc, "g1", 0, H / 2, 300, t["neon"], 0.7)
    doc.add("</g>")
    cy = H / 2
    doc.add(f'<rect x="22.5" y="{fmt(cy - 16.5)}" width="51" height="33" rx="9" fill="{t["surface"]}" stroke="{t["border2"]}"/>')
    doc.add(doc.text(48, cy + 5.5, f"{index:02d}", "monob", 15, t["primary"], anchor="middle"))
    doc.add(doc.text(92, cy + 10.5, title, "display", 30, t["text"], ls=-0.6))
    lx = 92 + text_width(title, "display", 30, -0.6) + 26
    cmd = f"$ {command}"
    cw = text_width(cmd, "mono", 15.5)
    rx = W - 28 - cw - 26
    gradient(doc, "ln", [(0, t["primary"], 0.9), (0.45, t["neon"], 0.45), (1, t["soft"], 0.05)])
    doc.add(f'<rect x="{fmt(lx)}" y="{fmt(cy - 0.75)}" width="{fmt(rx - lx)}" height="1.5" fill="url(#ln)"/>')
    gradient(doc, "spark", [(0, t["signal"], 0), (0.5, t["signal"], 1), (1, t["signal"], 0)])
    doc.defs.append(f'<clipPath id="rule"><rect x="{fmt(lx)}" y="{fmt(cy - 6)}" width="{fmt(rx - lx)}" height="12"/></clipPath>')
    doc.add(
        f'<rect x="{fmt(lx - 70)}" y="{fmt(cy - 1.25)}" width="70" height="2.5" fill="url(#spark)" clip-path="url(#rule)">'
        f'<animate attributeName="x" values="{fmt(lx - 70)};{fmt(rx)}" dur="5.5s" begin="{fmt(index * 0.7)}s" repeatCount="indefinite"/></rect>'
    )
    doc.add(doc.text(W - 28, cy + 5.5, cmd, "mono", 15.5, t["muted"], anchor="end"))
    return doc


# --------------------------------------------------------------------------
# neofetch profile
# --------------------------------------------------------------------------


def terminal(theme: str) -> SVG:
    W = 1200
    row_h, key_w = 35, 12
    rows_top = 178
    H = rows_top + row_h * len(C.FETCH) + 128
    doc = SVG(W, H, theme, f"neofetch — {C.NAME}",
              "; ".join(f"{k}: {v}" for k, v in C.FETCH if k))
    t = doc.t
    doc.css += [BLINK_CSS]
    clip_round(doc, "cc", 0, 0, W, H, 18)
    card(doc, 0, 0, W, H, 18)
    doc.add('<g clip-path="url(#cc)">')
    glow(doc, "g1", 210, 330, 340, t["neon"], 0.9)
    doc.add(f'<rect x="0" y="0" width="{W}" height="46" fill="{t["surface2"]}"/>')
    doc.add(f'<path d="M0 46.5H{W}" stroke="{t["border"]}"/>')
    doc.add("</g>")
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        doc.add(f'<circle cx="{26 + i * 20}" cy="23" r="6" fill="{c}" fill-opacity="0.9"/>')
    doc.add(doc.text(W / 2, 28.5, "tony@tlt: ~ — zsh — 120×32", "mono", 13.5, t["dim"], anchor="middle"))

    # command
    doc.add(doc.spans(40, 92, [("tony@tlt", t["signal"]), (" ~ ", t["soft"]), ("❯ ", t["neon"]),
                               ("neofetch", t["text"]), (" --profile", t["muted"])], "mono", 18))

    # shield logo
    cx, top = 200, 176
    sw, sh = 104, 250

    def shield(scale: float) -> str:
        w, h = sw * scale, sh * scale
        tp = top + (sh - h) / 2 + 6 * (1 - scale)
        return (
            f"M{fmt(cx)} {fmt(tp)}L{fmt(cx + w)} {fmt(tp + h * 0.13)}V{fmt(tp + h * 0.5)}"
            f"C{fmt(cx + w)} {fmt(tp + h * 0.78)} {fmt(cx + w * 0.45)} {fmt(tp + h * 0.93)} {fmt(cx)} {fmt(tp + h)}"
            f"C{fmt(cx - w * 0.45)} {fmt(tp + h * 0.93)} {fmt(cx - w)} {fmt(tp + h * 0.78)} {fmt(cx - w)} {fmt(tp + h * 0.5)}"
            f"V{fmt(tp + h * 0.13)}Z"
        )

    brand = brand_gradient(doc, "brand")
    gradient(doc, "sfill", [(0, t["primary"], 0.10), (1, t["soft"], 0.04)], x2=0.4, y2=1)
    doc.add(f'<path d="{shield(1)}" fill="url(#sfill)" stroke="{brand}" stroke-width="2.5" stroke-linejoin="round"/>')
    doc.add(f'<path d="{shield(0.8)}" stroke="{t["border2"]}" stroke-dasharray="3 5" stroke-linejoin="round"/>')
    gy = top + sh * 0.53
    doc.add(doc.text(cx - 6, gy, ">", "monob", 64, brand, anchor="end"))
    doc.add(f'<rect class="cur" x="{cx + 2}" y="{fmt(gy - 6)}" width="36" height="8" rx="2" fill="{t["signal"]}"/>')
    doc.add(doc.text(cx, top + sh + 40, "SECURE · BY · DESIGN", "mono", 13, t["dim"], anchor="middle", ls=2.2))

    # info block
    ix = 400
    doc.add(doc.spans(ix, 146, [("tony", t["primary"]), ("@", t["dim"]), ("tabwa", t["soft"])], "monob", 24))
    doc.add(f'<rect x="{ix}" y="159" width="{fmt(text_width("tony@tabwa", "monob", 24))}" height="2" rx="1" fill="{t["border2"]}"/>')
    for i, (k, v) in enumerate(C.FETCH):
        y = rows_top + 22 + i * row_h
        key = (k + " ").ljust(key_w, ".") if k else " " * key_w
        parts = [(key[: len(k)], t["primary"]), (key[len(k):], t["dim"]), (" " + v, t["text"])]
        if k == "Mindset":
            parts[-1] = (" " + v, t["signal"])
        doc.add(doc.spans(ix, y, parts, "mono", 18))
    # palette
    py = rows_top + row_h * len(C.FETCH) + 22
    for i, c in enumerate((t["primary"], t["warn"], t["signal"], t["soft"], t["neon"], t["muted"], t["text"], t["border2"])):
        doc.add(f'<rect x="{ix + i * 40}" y="{py}" width="32" height="16" rx="4" fill="{c}"/>')
    # trailing prompt
    ly = H - 34
    doc.add(doc.spans(40, ly, [("tony@tlt", t["signal"]), (" ~ ", t["soft"]), ("❯ ", t["neon"])], "mono", 18))
    px = 40 + text_width("tony@tlt ~ ❯ ", "mono", 18)
    doc.add(f'<rect class="cur" x="{fmt(px)}" y="{ly - 15}" width="10.5" height="20" rx="1.5" fill="{t["text"]}"/>')
    return doc


# --------------------------------------------------------------------------
# Arsenal
# --------------------------------------------------------------------------


def arsenal(theme: str) -> SVG:
    W = 1200
    pad_x, label_w = 36, 214
    tile_h, gap, row_gap = 48, 10, 10
    x_start, x_end = pad_x + label_w, W - pad_x
    # layout pass: greedy wrap, then shrink the row width until the row count
    # would grow, so rows come out balanced instead of leaving an orphan tile.
    def pack(items: list[tuple[str, str | None, str | None, float]], limit: float) -> list[list]:
        rows, row, rw = [], [], 0.0
        for it in items:
            w = it[3]
            if row and rw + gap + w > limit:
                rows.append(row)
                row, rw = [], 0.0
            row.append(it)
            rw += (gap if len(row) > 1 else 0) + w
        rows.append(row)
        return rows

    blocks, y = [], 36
    avail = x_end - x_start
    for cat, tools in C.ARSENAL:
        items = [(n, slug, mono, 14 + 21 + 11 + text_width(n, "body", 17) + 16) for n, slug, mono in tools]
        target = len(pack(items, avail))
        limit = avail
        while limit > 0 and len(pack(items, limit - 4)) == target:
            limit -= 4
        rows = pack(items, limit)
        blocks.append((cat, len(tools), rows, y))
        y += len(rows) * tile_h + (len(rows) - 1) * row_gap + 36
    H = y
    names = ", ".join(n for _, tools in C.ARSENAL for n, _, _ in tools)
    doc = SVG(W, H, theme, "Arsenal — tools, frameworks and languages", names)
    t = doc.t
    clip_round(doc, "cc", 0, 0, W, H, 18)
    card(doc, 0, 0, W, H, 18)
    doc.add('<g clip-path="url(#cc)">')
    glow(doc, "g1", W, 0, 520, t["soft"], 0.7)
    glow(doc, "g2", 0, H, 480, t["neon"], 0.6)
    doc.add("</g>")
    accents = (t["primary"], t["neon"], t["soft"])
    for bi, (cat, count, rows, by) in enumerate(blocks):
        if bi:
            doc.add(f'<path d="M{pad_x} {by - 18}.5H{W - pad_x}" stroke="{t["border"]}" stroke-dasharray="2 4"/>')
        ac = accents[bi % len(accents)]
        doc.add(f'<rect x="{pad_x}" y="{by + 6}" width="3" height="38" rx="1.5" fill="{ac}"/>')
        doc.add(doc.text(pad_x + 16, by + 22, cat, "display", 18.5, t["text"]))
        doc.add(doc.text(pad_x + 16, by + 42, f"{count:02d} tools", "mono", 13, t["dim"], ls=0.6))
        for ri, row in enumerate(rows):
            x = x_start
            ty = by + ri * (tile_h + row_gap)
            for name, slug, mono, w in row:
                doc.add(
                    f'<rect x="{fmt(x + 0.5)}" y="{ty + 0.5}" width="{fmt(w - 1)}" height="{tile_h - 1}" rx="11"'
                    f' fill="{t["surface"]}" stroke="{t["border"]}"/>'
                )
                if slug:
                    icon(doc, slug, x + 14, ty + 13.5, 21, t["primary"])  # monochrome, like the portfolio
                else:
                    monogram(doc, mono, x + 14, ty + 13.5, 21, t["primary"])
                doc.add(doc.text(x + 46, ty + 30, name, "body", 17, t["text"]))
                x += w + gap
    return doc


# --------------------------------------------------------------------------
# Project cards
# --------------------------------------------------------------------------


def project(theme: str, p: dict) -> SVG:
    W, H, m = 600, 372, 8
    doc = SVG(W, H, theme, f"{p['name']} — {p['kind']}", p["desc"])
    t = doc.t
    ac = t[p["accent"]]
    cw, ch = W - 2 * m, H - 2 * m
    clip_round(doc, "cc", m, m, cw, ch, 18)
    card(doc, m, m, cw, ch, 18)
    doc.add('<g clip-path="url(#cc)">')
    glow(doc, "g1", W - 40, 0, 360, t["neon"], 1.0)  # lime haze reads olive; use neon
    gradient(doc, "top", [(0, ac, 0), (0.5, ac, 0.9), (1, ac, 0)])
    doc.add(f'<rect x="{m}" y="{m}" width="{cw}" height="2" fill="url(#top)"/>')
    # faint oversized mark watermark
    doc.add(doc.text(W - 26, H - m - 62, p["mark"], "display", 150, ac, anchor="end", attrs='opacity="0.05"'))
    doc.add("</g>")

    x0, y0 = m + 30, m + 30
    gradient(doc, "mk", [(0, ac, 1), (1, t["neon"] if p["accent"] != "neon" else t["primary"], 1)], x2=1, y2=1)
    doc.add(f'<rect x="{x0}" y="{y0}" width="52" height="52" rx="14" fill="url(#mk)"/>')
    doc.add(doc.text(x0 + 26, y0 + 33.5, p["mark"], "display", 20, t["on_accent"], anchor="middle", ls=0.4))
    doc.add(doc.text(x0 + 68, y0 + 18, p["kind"].upper(), "mono", 13, t["muted"], ls=1.2))
    doc.add(doc.text(x0 + 68, y0 + 48, p["name"], "display", 25, t["text"], ls=-0.4))
    # status
    status = p["status"]
    sw = text_width(status, "mono", 12.5, 1.2) + 42
    sx = W - m - 26 - sw
    dot = t["signal"] if status == "LIVE" else t["warn"]
    doc.add(f'<rect x="{fmt(sx + 0.5)}" y="{y0 - 8}.5" width="{fmt(sw - 1)}" height="29" rx="14.5" fill="{t["surface"]}" stroke="{t["border2"]}"/>')
    pulse_dot(doc, sx + 16, y0 + 6.5, dot, 3.6)
    doc.add(doc.text(sx + 29, y0 + 11, status, "mono", 12.5, t["muted"], ls=1.2))

    # description
    lines = wrap(p["desc"], "body", 17.5, cw - 60)
    if len(lines) > 4:
        raise ValueError(f"{p['name']}: description wraps to {len(lines)} lines (max 4)")
    for i, ln in enumerate(lines):
        doc.add(doc.text(x0, y0 + 100 + i * 27, ln, "body", 17.5, t["muted"]))
    # stack chips
    cx = x0
    cy = m + ch - 108
    for s in p["stack"]:
        cx += chip(doc, cx, cy, s, size=13.5, h=30, pad=11) + 8
    # footer
    fy = m + ch - 56
    doc.add(f'<path d="M{m} {fy}.5H{m + cw}" stroke="{t["border"]}"/>')
    doc.add(doc.text(x0, fy + 34, p["label"], "mono", 14.5, ac))
    cta = "visit ↗" if status == "LIVE" else "source ↗"
    doc.add(doc.text(W - m - 30, fy + 34, cta, "mono", 14.5, t["muted"], anchor="end"))
    return doc


# --------------------------------------------------------------------------
# Experience timeline + impact
# --------------------------------------------------------------------------


def timeline(theme: str) -> SVG:
    W = 1200
    px, gap = 34, 26
    n = len(C.EXPERIENCE)
    col = (W - 2 * px - (n - 1) * gap) / n
    rail_y = 78
    # layout
    cols, bottom = [], 0.0
    for e in C.EXPERIENCE:
        title = wrap(e["role"], "display", 22, col - 4)
        summ = wrap(e["summary"], "body", 16.5, col - 4)
        top = rail_y + 56
        sy = top + len(title) * 28 + 24
        cols.append((title, summ, top, sy))
        bottom = max(bottom, sy + len(summ) * 25)
    H = int(bottom + 34)
    doc = SVG(W, H, theme, "Experience — career progression",
              " → ".join(e["role"] for e in C.EXPERIENCE))
    t = doc.t
    clip_round(doc, "cc", 0, 0, W, H, 18)
    card(doc, 0, 0, W, H, 18)
    doc.add('<g clip-path="url(#cc)">')
    glow(doc, "g1", W - 100, 40, 420, t["signal"], 0.7)
    doc.add("</g>")
    gradient(doc, "rail", [(0, t["border2"], 1), (0.6, t["neon"], 0.9), (1, t["signal"], 1)])
    doc.add(f'<rect x="{px}" y="{rail_y - 1}" width="{W - 2 * px}" height="2" rx="1" fill="url(#rail)"/>')
    for i, (e, (title, summ, top, sy)) in enumerate(zip(C.EXPERIENCE, cols)):
        x = px + i * (col + gap)
        now = i == n - 1
        color = t["signal"] if now else t["neon"] if i == n - 2 else t["dim"]
        stage = "NOW" if now else f"STAGE {i + 1:02d}"
        doc.add(doc.text(x, rail_y - 24, stage, "mono", 13, t["signal"] if now else t["muted"], ls=1.6))
        if now:
            pulse_dot(doc, x + 7, rail_y, t["signal"], 6)
        else:
            doc.add(f'<circle cx="{fmt(x + 7)}" cy="{rail_y}" r="6" fill="{t["bg"]}" stroke="{color}" stroke-width="2.5"/>')
        chip(doc, x, top - 30, e["tag"], size=12.5, h=26, pad=10, color=t["signal"] if now else t["muted"])
        for j, ln in enumerate(title):
            doc.add(doc.text(x, top + 22 + j * 28, ln, "display", 22, t["text"], ls=-0.3))
        for j, ln in enumerate(summ):
            doc.add(doc.text(x, sy + j * 25, ln, "body", 16.5, t["muted"]))
    return doc


def impact(theme: str) -> SVG:
    W, H, gap = 1200, 150, 18
    n = len(C.IMPACT)
    cw = (W - (n - 1) * gap) / n
    doc = SVG(W, H, theme, "Impact highlights",
              "; ".join(f"{a} {b} {c}" for a, b, c in C.IMPACT))
    t = doc.t
    brand = brand_gradient(doc, "brand")
    for i, (num, l1, l2) in enumerate(C.IMPACT):
        x = i * (cw + gap)
        clip_round(doc, f"c{i}", x, 0, cw, H, 18)
        card(doc, x, 0, cw, H, 18)
        doc.add(f'<g clip-path="url(#c{i})">')
        glow(doc, f"g{i}", x + cw, 0, 260, (t["neon"], t["soft"], t["neon"])[i % 3], 0.9)
        doc.add("</g>")
        doc.add(doc.text(x + 28, 88, num, "display", 54, brand, ls=-2))
        nx = x + 28 + text_width(num, "display", 54, -2) + 18
        for label in (l1, l2):
            if nx + text_width(label, "body", 17) > x + cw - 16:
                raise ValueError(f"impact label too long for its tile: {label!r}")
        doc.add(doc.text(nx, 66, l1, "body", 17, t["muted"]))
        doc.add(doc.text(nx, 91, l2, "body", 17, t["text"]))
        doc.add(f'<rect x="{x + 30}" y="112" width="40" height="3" rx="1.5" fill="{t["border2"]}"/>')
    return doc


# --------------------------------------------------------------------------
# Buttons
# --------------------------------------------------------------------------


def _glyph(doc: SVG, kind: str, x: float, y: float, color: str) -> None:
    s = f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    if kind == "portfolio":
        doc.add(f'<g {s}><circle cx="{x + 10}" cy="{y + 10}" r="9"/><ellipse cx="{x + 10}" cy="{y + 10}" rx="4" ry="9"/>'
                f'<path d="M{x + 1} {y + 10}H{x + 19}"/></g>')
    elif kind == "company":
        doc.add(f'<g {s}><path d="M{x + 10} {y}L{x + 18} {y + 3.5}V{y + 10}C{x + 18} {y + 15} {x + 14} {y + 18.5} {x + 10} {y + 20}'
                f'C{x + 6} {y + 18.5} {x + 2} {y + 15} {x + 2} {y + 10}V{y + 3.5}Z"/><path d="M{x + 6.5} {y + 10}l2.5 2.5 4.5-5"/></g>')
    elif kind == "linkedin":
        doc.add(f'<rect x="{x + 0.9}" y="{y + 0.9}" width="18.2" height="18.2" rx="4.5" {s}/>')
        doc.add(f'<g {s}><path d="M{x + 6} {y + 9}V{y + 15}M{x + 9.5} {y + 15}V{y + 9}M{x + 9.5} {y + 11.5}'
                f'C{x + 9.5} {y + 9.5} {x + 14} {y + 8.5} {x + 14} {y + 11.5}V{y + 15}"/>'
                f'<circle cx="{x + 6}" cy="{y + 5.8}" r="0.6" fill="{color}"/></g>')
    elif kind == "email":
        doc.add(f'<g {s}><rect x="{x + 1}" y="{y + 3}" width="18" height="14" rx="3"/><path d="M{x + 2} {y + 5}l8 6 8-6"/></g>')


def button(theme: str, key: str, primary: bool) -> SVG:
    label, _ = C.LINKS[key]
    W, H, m = 252, 64, 5
    doc = SVG(W, H, theme, label)
    t = doc.t
    bw, bh = W - 2 * m, H - 2 * m
    if primary:
        brand = brand_gradient(doc, "brand")
        doc.add(f'<rect x="{m}" y="{m}" width="{bw}" height="{bh}" rx="14" fill="{brand}"/>')
        fg, sub = t["on_accent"], t["on_accent"]
    else:
        doc.add(f'<rect x="{m + 0.5}" y="{m + 0.5}" width="{bw - 1}" height="{bh - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border2"]}"/>')
        fg, sub = t["text"], t["muted"]
    size = 19 if text_width(label, "body", 19) < 150 else 15.5
    lw = text_width(label, "body", size)
    arrow_w = 7 + text_width("↗", "mono", 15)
    total = 20 + 11 + lw + arrow_w
    x = (W - total) / 2
    _glyph(doc, key, x, H / 2 - 10, fg)
    doc.add(doc.text(x + 31, H / 2 + size * 0.36, label, "body", size, fg))
    doc.add(doc.text(x + 31 + lw + 7, H / 2 + 5.5, "↗", "mono", 15, sub, attrs='opacity="0.8"'))
    return doc


# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------


def footer(theme: str) -> SVG:
    W, H = 1200, 330
    doc = SVG(W, H, theme, "Let's build something secure", " ".join(C.QUOTE))
    t = doc.t
    clip_round(doc, "cc", 0, 0, W, H, 24)
    card(doc, 0, 0, W, H, 24)
    doc.add('<g clip-path="url(#cc)">')
    glow(doc, "g1", W / 2, H + 60, 520, t["neon"], 1.1)
    glow(doc, "g2", 0, 0, 380, t["neon"], 0.7)
    dot_grid(doc, "cc", 0, 0, W, H, W / 2, H, 640)
    # signal wave with travelling highlight
    pts = []
    for i in range(0, W + 1, 8):
        y = H - 46 + 9 * math.sin(i / 46) * math.sin(i / 190)
        pts.append(f"{'M' if i == 0 else 'L'}{i} {fmt(y)}")
    wave = "".join(pts)
    doc.add(f'<path d="{wave}" stroke="{t["border2"]}" stroke-width="1.2"/>')
    brand = brand_gradient(doc, "brand")
    doc.add(
        f'<path d="{wave}" stroke="{brand}" stroke-width="2" stroke-linecap="round" stroke-dasharray="160 1400">'
        f'<animate attributeName="stroke-dashoffset" values="1560;0" dur="6s" repeatCount="indefinite"/></path>'
    )
    doc.add("</g>")
    doc.add(doc.text(W / 2, 92, "“", "display", 84, brand, anchor="middle"))
    doc.add(doc.text(W / 2, 128, C.QUOTE[0], "display", 30, t["text"], anchor="middle", ls=-0.5))
    doc.add(doc.text(W / 2, 168, C.QUOTE[1], "display", 30, brand, anchor="middle", ls=-0.5))
    doc.add(doc.text(W / 2, 202, f"— {C.NAME.upper()}", "mono", 13.5, t["muted"], anchor="middle", ls=2.4))
    # open-to chips
    widths = [text_width(s, "mono", 14.5) + 22 + 20 for s in C.OPEN_TO]
    total = sum(widths) + 12 * (len(widths) - 1)
    x = (W - total) / 2
    for s, w in zip(C.OPEN_TO, widths):
        doc.add(f'<rect x="{fmt(x + 0.5)}" y="224.5" width="{fmt(w - 1)}" height="35" rx="17.5" fill="{t["surface"]}" stroke="{t["border2"]}"/>')
        doc.add(f'<circle cx="{fmt(x + 17)}" cy="242" r="3.6" fill="{t["signal"]}"/>')
        doc.add(doc.text(x + 29, 247, s, "mono", 14.5, t["muted"]))
        x += w + 12
    return doc


# --------------------------------------------------------------------------


SECTIONS = (
    (1, "Profile", "neofetch --profile"),
    (2, "Arsenal", "ls ~/toolchain"),
    (3, "Featured Work", "git log --featured"),
    (4, "Experience", "history | tail -4"),
    (5, "Telemetry", "watch -n 86400 gh stats"),
    (6, "Connect", "ping tony"),
)


def assets() -> dict[str, Callable[[str], SVG]]:
    out = {
        "hero": hero,
        "profile": terminal,
        "arsenal": arsenal,
        "timeline": timeline,
        "impact": impact,
        "footer": footer,
    }
    for i, title, cmd in SECTIONS:
        out[f"h{i:02d}-{title.lower().replace(' ', '-')}"] = (lambda th, i=i, title=title, cmd=cmd: header(th, i, title, cmd))
    for p in C.PROJECTS:
        out[f"project-{p['slug']}"] = (lambda th, p=p: project(th, p))
    for i, key in enumerate(C.LINKS):
        out[f"btn-{key}"] = (lambda th, key=key, primary=(i == 0): button(th, key, primary))
    return out


# --------------------------------------------------------------------------
# README
# --------------------------------------------------------------------------

RAW = f"https://raw.githubusercontent.com/{C.LOGIN}/{C.LOGIN}/output"


def picture(name: str, alt: str, width: str = "100%", base: str = "assets") -> str:
    return (
        f'<picture><source media="(prefers-color-scheme: dark)" srcset="{base}/{name}-dark.svg">'
        f'<source media="(prefers-color-scheme: light)" srcset="{base}/{name}-light.svg">'
        f'<img alt="{html.escape(alt)}" src="{base}/{name}-dark.svg" width="{width}"></picture>'
    )


def linked(url: str, pic: str) -> str:
    return f'<a href="{url}">{pic}</a>'


def readme() -> str:
    def head(i: int) -> str:
        n, title, cmd = SECTIONS[i - 1]
        return picture(f"h{n:02d}-{title.lower().replace(' ', '-')}", f"{n:02d} {title}")

    buttons = "".join(
        linked(url, picture(f"btn-{key}", label, "24%")) for key, (label, url) in C.LINKS.items()
    )
    fetch_alt = "; ".join(f"{k}: {v}" for k, v in C.FETCH if k)
    tools = " · ".join(n for _, ts in C.ARSENAL for n, _, _ in ts)
    cards = [linked(p["url"], picture(f"project-{p['slug']}", f"{p['name']}: {p['desc']}", "49%")) for p in C.PROJECTS]
    rows = "\n".join(f'<p align="center">{"".join(cards[i:i + 2])}</p>' for i in range(0, len(cards), 2))
    exp = "\n\n".join(
        f"**{e['role']}**{' · _current_' if i == 0 else ''}\n"
        + "\n".join(f"- {b}" for b in e["bullets"])
        for i, e in enumerate(reversed(C.EXPERIENCE))
    )
    impact_alt = "; ".join(f"{a} {b} {c}" for a, b, c in C.IMPACT)
    return f"""<!--
  Generated by profile/build.py. Edit profile/content.py, then run:
    pip install -r profile/requirements.txt && python profile/build.py
-->
<a id="top"></a>

{picture("hero", f"{C.NAME}: {C.ROLES[0]} and {C.ROLES[1]} based in {C.LOCATION}")}

<p align="center">{buttons}</p>

<br>

{head(1)}

{picture("profile", fetch_alt)}

<br>

{head(2)}

{picture("arsenal", tools)}

<br>

{head(3)}

{rows}

<br>

{head(4)}

{picture("timeline", " → ".join(e["role"] for e in C.EXPERIENCE))}

{picture("impact", impact_alt)}

<details>
<summary><b>Full experience breakdown</b></summary>
<br>

{exp}

</details>

<br>

{head(5)}

<a href="https://github.com/{C.LOGIN}?tab=repositories">{picture("telemetry", f"Live GitHub telemetry for @{C.LOGIN}", base=RAW)}</a>

<br>

{head(6)}

{picture("footer", " ".join(C.QUOTE))}

<p align="center">{buttons}</p>

<p align="center"><sub>Designed in code: every visual is generated by <a href="profile/"><code>profile/</code></a> · live stats refresh daily via GitHub Actions</sub></p>
"""


def main() -> int:
    check_palette()
    ASSETS.mkdir(exist_ok=True)
    written = []
    for name, fn in assets().items():
        for theme in ("dark", "light"):
            path = ASSETS / f"{name}-{theme}.svg"
            svg = fn(theme).render()
            minidom.parseString(svg)  # fail loudly on malformed XML
            path.write_text(svg, encoding="utf-8")
            written.append(path)
    (ASSETS.parent / "README.md").write_text(readme(), encoding="utf-8")
    total = sum(p.stat().st_size for p in written)
    print(f"wrote README.md and {len(written)} assets ({total / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
