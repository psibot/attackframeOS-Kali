#!/usr/bin/env python3
"""AttackFrame wallpaper pack, Kali edition: 10 original designs (16:9).
Mood: Kali-blue cyberpunk — deep navy, electric blue, AttackFrame cyan/magenta accents,
terminal culture and the Kali + BlackArch dual-layer idea. All artwork is original
(no Kali logo / dragon mark is reproduced).
Run after gen-wallpapers{,2,3}.py (appends to assets/wallpapers/names.tsv)."""
import importlib.util
import math
import random
from pathlib import Path


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wp1 = _load("wp1", "gen-wallpapers.py")
wp2 = _load("wp2", "gen-wallpapers2.py")
W, H, svg, t, brackets, tag = wp1.W, wp1.H, wp1.svg, wp1.t, wp1.brackets, wp1.tag
lin, rad, stars = wp2.lin, wp2.rad, wp2.stars
VOID, CYAN, MAG, YEL, TEXT, DIM, VIOLET = wp1.VOID, wp1.CYAN, wp1.MAG, wp1.YEL, wp1.TEXT, wp1.DIM, wp1.VIOLET

# Kali-edition palette
NAVY, DEEP, KBLUE, SKY, ICE = "#030814", "#06122b", "#2f7bff", "#5aa9ff", "#d6e8ff"
BARED = "#ff2a3d"   # BlackArch-layer red accent

ED = "KALI EDITION"


def kmark(x=60, y=H - 50, color=SKY, anchor="start"):
    return t(x, y, f"ATTACK//FRAME  ·  {ED}", 15, color, .8, anchor, 'letter-spacing="6" font-weight="700"')


def kword(cx, cy, size=96, sub=None, col=KBLUE):
    out = [t(cx + 4, cy, "ATTACK//FRAME", size, MAG, .5, "middle", 'font-weight="800" letter-spacing="10"'),
           t(cx - 3, cy, "ATTACK//FRAME", size, col, .6, "middle", 'font-weight="800" letter-spacing="10"'),
           t(cx, cy, "ATTACK//FRAME", size, ICE, 1, "middle", 'font-weight="800" letter-spacing="10" filter="url(#glow)"')]
    if sub:
        out.append(t(cx, cy + size * .52, sub, size * .17, SKY, .9, "middle", f'letter-spacing="{size * .08:.0f}"'))
    return "".join(out)


def floor_grid(hz, color, n_long=40, n_lat=22, op=.5, spread=4.0, sw=1.3):
    cx, out = W / 2, []
    for i in range(-n_long, n_long + 1):
        out.append(f'<line x1="{cx + i * 6:.1f}" y1="{hz}" x2="{cx + i * (W * spread / n_long / 2):.1f}" y2="{H}" '
                   f'stroke="{color}" stroke-width="{sw}" opacity="{op}"/>')
    for k in range(1, n_lat + 1):
        y = hz + (H - hz) * (k / n_lat) ** 2.2
        out.append(f'<line x1="0" y1="{y:.1f}" x2="{W}" y2="{y:.1f}" stroke="{color}" stroke-width="{sw}" '
                   f'opacity="{op * (.35 + .65 * k / n_lat):.2f}"/>')
    return "".join(out)


# ------------------------------------------------------------------ 01 root shell
def root_shell():
    """A giant operator terminal floating over a blue grid."""
    r = random.Random(1101)
    defs = lin("rsbg", [(0, "#020611", 1), (1, "#071a3d", 1)])
    body = [f'<rect width="{W}" height="{H}" fill="url(#rsbg)"/>', floor_grid(760, KBLUE, op=.35)]
    body.append(stars(r, 90, 700, (.1, .5)))
    x0, y0, w, h = 300, 150, 1320, 640
    body.append(f'<rect x="{x0 + 14}" y="{y0 + 18}" width="{w}" height="{h}" rx="14" fill="#000" opacity=".55"/>')
    body.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="14" fill="#040b1c" opacity=".93" stroke="{KBLUE}" stroke-width="2" filter="url(#softglow)"/>')
    body.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="42" rx="14" fill="#0b1a3a"/>')
    body.append(f'<rect x="{x0}" y="{y0 + 28}" width="{w}" height="14" fill="#0b1a3a"/>')
    for i, c in enumerate([BARED, YEL, "#39ff88"]):
        body.append(f'<circle cx="{x0 + 28 + i * 26}" cy="{y0 + 21}" r="7" fill="{c}" opacity=".85"/>')
    body.append(t(x0 + w / 2, y0 + 27, "ghost@attackframe: ~/engagement", 15, ICE, .7, "middle"))
    lines = [
        (SKY, "┌──(ghost㉿attackframe)-[~/engagement]"),
        (SKY, "└─$ sudo nmap -sC -sV -p- --min-rate 5000 $TGT"),
        (DIM, "Starting Nmap ( https://nmap.org )"),
        (TEXT, "Nmap scan report for target.lab (10.10.11.5)"),
        (TEXT, "PORT      STATE SERVICE       VERSION"),
        ("#39ff88", "22/tcp    open  ssh           OpenSSH (protocol 2.0)"),
        ("#39ff88", "80/tcp    open  http          nginx"),
        ("#39ff88", "445/tcp   open  microsoft-ds"),
        ("#39ff88", "5985/tcp  open  http          Microsoft HTTPAPI 2.0"),
        (DIM, "Service detection performed. 1 IP address (1 host up)"),
        (SKY, "┌──(ghost㉿attackframe)-[~/engagement]"),
        (SKY, "└─$ blackarch katana -u http://$TGT -d 3 -silent"),
        (MAG, "[ba] http://10.10.11.5/login"),
        (MAG, "[ba] http://10.10.11.5/api/v1/users"),
        (SKY, "┌──(ghost㉿attackframe)-[~/engagement]"),
        (SKY, "└─$ █"),
    ]
    for i, (c, s) in enumerate(lines):
        body.append(t(x0 + 34, y0 + 86 + i * 34, s, 20, c, .95, extra='filter="url(#softglow)"' if c in (SKY, MAG) else ""))
    body.append(t(W / 2, 108, "ROOT // SHELL", 30, ICE, .9, "middle", 'font-weight="700" letter-spacing="22" filter="url(#glow)"'))
    body.append(kmark(W / 2, H - 46, anchor="middle"))
    body.append(brackets(28, 70, KBLUE))
    svg("kali-root-shell", "".join(body), extra_defs=defs)


# ------------------------------------------------------------------ 02 blue horizon
def blue_horizon():
    """Outrun horizon in Kali blue: striped sun, mountains, grid."""
    r = random.Random(1102)
    hz = 640
    defs = (lin("bhsky", [(0, "#01030a", 1), (.6, "#0a1f52", 1), (1, "#1b3f9e", 1)]) +
            lin("bhsun", [(0, ICE, 1), (.45, SKY, 1), (1, MAG, 1)]) +
            lin("bhfl", [(0, "#051238", 1), (1, "#000", 1)]))
    body = [f'<rect width="{W}" height="{hz}" fill="url(#bhsky)"/>', stars(r, 220, 520)]
    cx, cy, rr = W / 2, hz - 40, 300
    clip = "".join(f'<rect x="{cx - rr}" y="{cy - rr + k * 34 + (k * k) * .9:.0f}" width="{2 * rr}" height="{max(4, 30 - k * 2.2):.0f}"/>' for k in range(16))
    defs += f'<clipPath id="bhcut">{clip}</clipPath>'
    body.append(f'<circle cx="{cx}" cy="{cy}" r="{rr + 40}" fill="{KBLUE}" opacity=".25" filter="url(#bigglow)"/>')
    body.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="url(#bhsun)" clip-path="url(#bhcut)"/>')
    for layer, (col, op, amp, seed) in enumerate([("#0a1a45", 1, 170, 7), ("#04102c", 1, 110, 9)]):
        rr2 = random.Random(seed)
        pts, x = [(0, hz)], 0
        while x < W:
            x += rr2.uniform(60, 160)
            pts.append((x, hz - rr2.uniform(.2, 1) * amp))
        pts.append((W, hz))
        body.append(f'<polygon points="{" ".join(f"{a:.0f},{b:.0f}" for a, b in pts)}" fill="{col}" stroke="{SKY}" stroke-width="1.5" stroke-opacity="{.5 - layer * .2}"/>')
    body.append(f'<rect y="{hz}" width="{W}" height="{H - hz}" fill="url(#bhfl)"/>')
    body.append(floor_grid(hz, KBLUE, op=.55, sw=1.6))
    body.append(f'<rect y="{hz - 2}" width="{W}" height="4" fill="{SKY}" filter="url(#bigglow)"/>')
    body.append(t(W / 2, 150, "ATTACK//FRAME", 72, ICE, .95, "middle", 'font-weight="300" letter-spacing="38" filter="url(#glow)"'))
    body.append(t(W / 2, 198, f"{ED}  ·  ROLLING", 18, SKY, .85, "middle", 'letter-spacing="10"'))
    svg("kali-blue-horizon", "".join(body), extra_defs=defs)


# ------------------------------------------------------------------ 03 neon wyrm
def neon_wyrm():
    """An original serpent of glowing hex scales coiling through a data sky."""
    r = random.Random(1103)
    defs = rad("nwbg", [(0, "#0b1f4f", 1), (1, NAVY, 1)], cy="40%", r="80%")
    body = [f'<rect width="{W}" height="{H}" fill="url(#nwbg)"/>', stars(r, 200)]
    for k in range(14):  # faint data streams
        x = r.uniform(0, W)
        body.append(f'<line x1="{x:.0f}" y1="0" x2="{x - 120:.0f}" y2="{H}" stroke="{KBLUE}" stroke-width="1" opacity=".12"/>')
    n = 150
    pts = []
    for i in range(n):
        s = i / (n - 1)
        x = 180 + s * (W - 360)
        y = H * .52 + math.sin(s * math.pi * 2.6 + .4) * 250 * (1 - .35 * s) + math.sin(s * 11) * 18
        pts.append((x, y))
    # body: hexagonal scales, tapering from head (right) to tail (left)
    for i in range(0, n, 1):
        x, y = pts[i]
        s = i / (n - 1)
        size = 6 + 34 * math.sin(min(1, s * 1.15) * math.pi * .5) ** 1.4
        if i > n - 8:
            size *= .8
        col = [KBLUE, SKY, CYAN][i % 3] if i % 9 else MAG
        hexp = " ".join(f"{x + size * math.cos(a):.1f},{y + size * math.sin(a):.1f}" for a in [math.pi / 3 * k + math.pi / 6 for k in range(6)])
        body.append(f'<polygon points="{hexp}" fill="{col}" fill-opacity="{.05 + .18 * s:.2f}" stroke="{col}" stroke-width="1.6" stroke-opacity="{.35 + .55 * s:.2f}"/>')
    spine = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    body.append(f'<polyline points="{spine}" fill="none" stroke="{ICE}" stroke-width="2.4" opacity=".75" filter="url(#glow)"/>')
    # fins along the back
    for i in range(20, n - 6, 7):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        ang = math.atan2(y1 - y0, x1 - x0) - math.pi / 2
        L = 18 + 46 * (i / n)
        body.append(f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x0 + L * math.cos(ang):.0f}" y2="{y0 + L * math.sin(ang):.0f}" stroke="{SKY}" stroke-width="2" opacity=".7" filter="url(#softglow)"/>')
    # head: abstract wedge with a single magenta eye
    hx, hy = pts[-1]
    (px, py) = pts[-4]
    a = math.atan2(hy - py, hx - px)
    def rot(u, v):
        return hx + u * math.cos(a) - v * math.sin(a), hy + u * math.sin(a) + v * math.cos(a)
    head = [rot(-20, -46), rot(70, -16), rot(118, 4), rot(70, 22), rot(-20, 44)]
    body.append(f'<polygon points="{" ".join(f"{u:.0f},{v:.0f}" for u, v in head)}" fill="#071636" stroke="{ICE}" stroke-width="3" filter="url(#glow)"/>')
    for u0, v0, u1, v1 in [(-20, -46, -70, -96), (10, -34, -20, -110)]:
        (ax, ay), (bx, by) = rot(u0, v0), rot(u1, v1)
        body.append(f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{bx:.0f}" y2="{by:.0f}" stroke="{SKY}" stroke-width="3" filter="url(#softglow)"/>')
    ex, ey = rot(52, -8)
    body.append(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="7" fill="{MAG}" filter="url(#bigglow)"/>')
    body.append(t(70, 110, "NEON//WYRM", 44, ICE, .9, extra='font-weight="800" letter-spacing="14" filter="url(#glow)"'))
    body.append(t(72, 146, "the rolling serpent never sleeps", 16, SKY, .75, extra='letter-spacing="4"'))
    body.append(kmark())
    svg("kali-neon-wyrm", "".join(body), extra_defs=defs)


# ------------------------------------------------------------------ 04 dual layer
def dual_layer():
    """Kali (blue, native) and BlackArch (red, container) split by a glowing seam."""
    r = random.Random(1104)
    defs = (lin("dlk", [(0, "#071a46", 1), (1, "#020713", 1)], x2=1, y2=1) +
            lin("dlb", [(0, "#2a0710", 1), (1, "#080205", 1)], x2=1, y2=1) +
            f'<clipPath id="dlL"><polygon points="0,0 {W * .58:.0f},0 {W * .42:.0f},{H} 0,{H}"/></clipPath>'
            f'<clipPath id="dlR"><polygon points="{W * .58:.0f},0 {W},0 {W},{H} {W * .42:.0f},{H}"/></clipPath>')
    body = [f'<rect width="{W}" height="{H}" fill="url(#dlk)" clip-path="url(#dlL)"/>',
            f'<rect width="{W}" height="{H}" fill="url(#dlb)" clip-path="url(#dlR)"/>']
    hexes_l, hexes_r = [], []
    for row in range(-1, H // 52 + 2):
        for col in range(-1, W // 60 + 2):
            x, y, s = col * 60 + (30 if row % 2 else 0), row * 52, 30
            p = " ".join(f"{x + s * math.cos(a):.0f},{y + s * math.sin(a):.0f}" for a in [math.pi / 3 * k + math.pi / 6 for k in range(6)])
            op = r.uniform(.05, .22) if r.random() > .1 else .5
            hexes_l.append(f'<polygon points="{p}" fill="none" stroke="{KBLUE}" stroke-width="1.2" opacity="{op:.2f}"/>')
            hexes_r.append(f'<polygon points="{p}" fill="none" stroke="{BARED}" stroke-width="1.2" opacity="{op:.2f}"/>')
    body.append(f'<g clip-path="url(#dlL)">{"".join(hexes_l)}</g><g clip-path="url(#dlR)">{"".join(hexes_r)}</g>')
    body.append(f'<line x1="{W * .58:.0f}" y1="0" x2="{W * .42:.0f}" y2="{H}" stroke="{ICE}" stroke-width="5" filter="url(#bigglow)"/>')
    body.append(f'<line x1="{W * .58:.0f}" y1="0" x2="{W * .42:.0f}" y2="{H}" stroke="#fff" stroke-width="2"/>')
    for k in range(18):  # packets crossing the seam
        s = r.uniform(.05, .95)
        x, y = W * .58 + (W * .42 - W * .58) * s, H * s
        body.append(f'<rect x="{x - 40:.0f}" y="{y - 2:.0f}" width="80" height="4" fill="{[SKY, BARED, MAG][k % 3]}" opacity=".85" filter="url(#softglow)"/>')
    body.append(t(W * .24, H * .45, "KALI", 120, ICE, .95, "middle", 'font-weight="800" letter-spacing="24" filter="url(#glow)"'))
    body.append(t(W * .24, H * .45 + 54, "NATIVE  ·  APT  ·  HOST", 20, SKY, .85, "middle", 'letter-spacing="8"'))
    body.append(t(W * .76, H * .62, "BLACKARCH", 104, "#ffd6da", .95, "middle", 'font-weight="800" letter-spacing="14" filter="url(#glow)"'))
    body.append(t(W * .76, H * .62 + 52, "DOCKER  ·  PACMAN  ·  BOX", 20, BARED, .9, "middle", 'letter-spacing="8"'))
    body.append(t(70, 80, "ATTACK//FRAME  ·  DUAL LAYER", 20, ICE, .85, "start", 'letter-spacing="10" font-weight="700"'))
    body.append(brackets(28, 70, ICE))
    svg("kali-dual-layer", "".join(body), extra_defs=defs)


# ------------------------------------------------------------------ 05 recon map
def recon_map():
    """Network graph of discovered hosts with scan rings radiating from the operator."""
    r = random.Random(1105)
    defs = rad("rmbg", [(0, "#0a1f4a", 1), (1, NAVY, 1)], r="70%")
    body = [f'<rect width="{W}" height="{H}" fill="url(#rmbg)"/>']
    cx, cy = W * .5, H * .54
    for k in range(1, 9):
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{k * 120}" fill="none" stroke="{KBLUE}" stroke-width="1.2" opacity="{.4 - k * .04:.2f}" stroke-dasharray="{4 + k} {8 + k * 2}"/>')
    for a in range(0, 360, 15):
        body.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + 1100 * math.cos(math.radians(a)):.0f}" y2="{cy + 1100 * math.sin(math.radians(a)):.0f}" stroke="{KBLUE}" stroke-width="1" opacity=".08"/>')
    body.append(f'<path d="M{cx},{cy} L{cx + 900 * math.cos(-.5):.0f},{cy + 900 * math.sin(-.5):.0f} A900,900 0 0,1 {cx + 900:.0f},{cy:.0f} Z" fill="{SKY}" opacity=".08"/>')
    nodes = [(cx, cy, "OPERATOR", CYAN, 14)]
    subnets = [(-1.1, "10.10.11.0/24"), (.4, "10.10.14.0/24"), (2.3, "172.16.5.0/24"), (3.6, "192.168.56.0/24")]
    labels = ["DC01", "WEB01", "SQL01", "FS01", "VPN", "DEV", "MAIL", "BACKUP", "PRINT", "CAM-3", "IOT-7", "JUMP"]
    li = 0
    for ang, net in subnets:
        gx, gy = cx + 460 * math.cos(ang), cy + 330 * math.sin(ang)
        body.append(f'<line x1="{cx}" y1="{cy}" x2="{gx:.0f}" y2="{gy:.0f}" stroke="{SKY}" stroke-width="2.4" opacity=".7" filter="url(#softglow)"/>')
        body.append(t(gx, gy - 30, net, 14, SKY, .85, "middle", 'letter-spacing="2"'))
        nodes.append((gx, gy, "", SKY, 10))
        for j in range(r.randint(3, 5)):
            a2 = ang + r.uniform(-1.1, 1.1)
            d = r.uniform(130, 230)
            hx, hy = gx + d * math.cos(a2), gy + d * .8 * math.sin(a2)
            if not (60 < hx < W - 60 and 80 < hy < H - 80):
                continue
            pwn = r.random() < .3
            col = MAG if pwn else KBLUE
            body.append(f'<line x1="{gx:.0f}" y1="{gy:.0f}" x2="{hx:.0f}" y2="{hy:.0f}" stroke="{col}" stroke-width="1.4" opacity=".6"/>')
            nodes.append((hx, hy, labels[li % len(labels)] + (" ★" if pwn else ""), col, 7))
            li += 1
    for x, y, lab, col, s in nodes:
        body.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{s * 2.2:.0f}" fill="{col}" opacity=".15"/>')
        body.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{s}" fill="{NAVY}" stroke="{col}" stroke-width="2.5" filter="url(#softglow)"/>')
        if lab:
            body.append(t(x + s + 8, y + 5, lab, 14, ICE, .85, extra='letter-spacing="2"'))
    body.append(t(70, 100, "RECON//MAP", 46, ICE, .92, extra='font-weight="800" letter-spacing="14" filter="url(#glow)"'))
    body.append(t(72, 136, "hosts up: 19   owned: ★   lhost: tun0", 15, SKY, .8, extra='letter-spacing="3"'))
    body.append(kmark())
    body.append(brackets(28, 70, KBLUE))
    svg("kali-recon-map", "".join(body), extra_defs=defs)


# ------------------------------------------------------------------ 06 blue rain city
def blue_rain_city():
    """Rain-soaked megacity in electric blue with neon signs."""
    r = random.Random(1106)
    defs = lin("bcsky", [(0, "#01030b", 1), (1, "#0d2a66", 1)]) + lin("bcwet", [(0, "#081c45", 1), (1, "#010309", 1)])
    hz = 860
    body = [f'<rect width="{W}" height="{H}" fill="url(#bcsky)"/>']
    body.append(f'<circle cx="{W * .7:.0f}" cy="260" r="140" fill="{SKY}" opacity=".12" filter="url(#bigglow)"/>')
    for layer, (dark, lit, hmin, hmax, wmin, wmax) in enumerate([("#071533", KBLUE, 300, 620, 70, 150), ("#040d22", SKY, 200, 520, 90, 190), ("#02060f", CYAN, 120, 380, 110, 220)]):
        x = -40
        while x < W:
            w = r.uniform(wmin, wmax)
            h = r.uniform(hmin, hmax)
            top = hz - h
            body.append(f'<rect x="{x:.0f}" y="{top:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{dark}"/>')
            for wy in range(int(top) + 14, hz - 10, 16 + layer * 4):
                for wx in range(int(x) + 8, int(x + w) - 8, 12 + layer * 4):
                    if r.random() < .16 - layer * .03:
                        body.append(f'<rect x="{wx}" y="{wy}" width="{4 + layer}" height="{3 + layer}" fill="{lit}" opacity="{r.uniform(.3, .9):.2f}"/>')
            if layer == 2 and r.random() < .45:
                word, col = r.choice([("ROOT", MAG), ("0DAY", CYAN), ("PWN", YEL), ("SHELL", SKY), ("ROOT", SKY), ("SUDO", MAG), ("NMAP", CYAN)])
                sy = top + r.uniform(30, 120)
                body.append(f'<rect x="{x + w / 2 - 14:.0f}" y="{sy - 4:.0f}" width="28" height="{len(word) * 30 + 8}" fill="#000" opacity=".6" stroke="{col}" stroke-width="2" filter="url(#glow)"/>')
                for ci, ch in enumerate(word):
                    body.append(t(x + w / 2, sy + 22 + ci * 30, ch, 24, col, .95, "middle", 'font-weight="800" filter="url(#softglow)"'))
            x += w + r.uniform(4, 24)
    body.append(f'<rect y="{hz}" width="{W}" height="{H - hz}" fill="url(#bcwet)"/>')
    for k in range(60):  # reflections
        x = r.uniform(0, W)
        body.append(f'<rect x="{x:.0f}" y="{hz + r.uniform(4, 180):.0f}" width="{r.uniform(20, 90):.0f}" height="2" fill="{r.choice([KBLUE, SKY, MAG, CYAN])}" opacity="{r.uniform(.2, .6):.2f}"/>')
    for k in range(700):  # rain
        x, y, L = r.uniform(0, W + 200), r.uniform(-50, H), r.uniform(18, 44)
        body.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x - L * .25:.0f}" y2="{y + L:.0f}" stroke="{ICE}" stroke-width="1" opacity="{r.uniform(.08, .3):.2f}"/>')
    body.append(t(W / 2, 150, "ATTACK//FRAME", 64, ICE, .92, "middle", 'font-weight="800" letter-spacing="18" filter="url(#glow)"'))
    body.append(t(W / 2, 192, f"{ED}  ·  AFTER DARK", 17, SKY, .85, "middle", 'letter-spacing="9"'))
    svg("kali-blue-rain-city", "".join(body), extra_defs=defs)


# ------------------------------------------------------------------ 07 rolling hud
def rolling_hud():
    """Circular targeting HUD with rotating rings and a 'KALI // ROLLING' text ring."""
    r = random.Random(1107)
    defs = rad("rhbg", [(0, "#0c2560", 1), (.6, "#040b1f", 1), (1, "#010309", 1)])
    cx, cy = W / 2, H / 2
    body = [f'<rect width="{W}" height="{H}" fill="url(#rhbg)"/>']
    for x in range(0, W + 1, 64):
        body.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{KBLUE}" stroke-width="1" opacity=".07"/>')
    for y in range(0, H + 1, 64):
        body.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{KBLUE}" stroke-width="1" opacity=".07"/>')
    for rr, sw, dash, col, op in [(440, 2, "2 10", KBLUE, .5), (400, 6, "60 20 10 20", SKY, .7), (290, 1.5, "", KBLUE, .6),
                                 (250, 14, "4 6", KBLUE, .35), (200, 3, "120 40", CYAN, .8), (130, 1.5, "", SKY, .6)]:
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="{col}" stroke-width="{sw}" opacity="{op}" '
                    + (f'stroke-dasharray="{dash}" ' if dash else "") + 'filter="url(#softglow)"/>')
    for a in range(0, 360, 5):
        L = 22 if a % 30 == 0 else 10
        x0, y0 = cx + 455 * math.cos(math.radians(a)), cy + 455 * math.sin(math.radians(a))
        x1, y1 = cx + (455 + L) * math.cos(math.radians(a)), cy + (455 + L) * math.sin(math.radians(a))
        body.append(f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{SKY}" stroke-width="2" opacity=".6"/>')
    # text ring, one rotated glyph at a time (librsvg ignores textPath)
    ring = "KALI // ROLLING  ·  ATTACK//FRAME  ·  NATIVE TOOLS  ·  BLACKARCH LAYER  ·  "
    rr_t = 338
    for i, ch in enumerate(ring):
        a = -math.pi / 2 + 2 * math.pi * i / len(ring)
        x, y = cx + rr_t * math.cos(a), cy + rr_t * math.sin(a)
        if ch.strip():
            body.append(t(x, y, ch, 19, MAG if i < 15 else ICE, .85, "middle",
                          f'transform="rotate({math.degrees(a) + 90:.1f} {x:.1f} {y:.1f})" dominant-baseline="middle"'))
    body.append(f'<line x1="{cx - 560}" y1="{cy}" x2="{cx - 150}" y2="{cy}" stroke="{SKY}" stroke-width="1.5" opacity=".6"/>')
    body.append(f'<line x1="{cx + 150}" y1="{cy}" x2="{cx + 560}" y2="{cy}" stroke="{SKY}" stroke-width="1.5" opacity=".6"/>')
    body.append(f'<line x1="{cx}" y1="{cy - 520}" x2="{cx}" y2="{cy - 150}" stroke="{SKY}" stroke-width="1.5" opacity=".6"/>')
    body.append(f'<line x1="{cx}" y1="{cy + 150}" x2="{cx}" y2="{cy + 520}" stroke="{SKY}" stroke-width="1.5" opacity=".6"/>')
    body.append(f'<path d="M{cx},{cy} L{cx + 290 * math.cos(-.9):.0f},{cy + 290 * math.sin(-.9):.0f} A290,290 0 0,1 {cx + 290 * math.cos(-.25):.0f},{cy + 290 * math.sin(-.25):.0f} Z" fill="{SKY}" opacity=".18"/>')
    for k in range(7):
        a, d = r.uniform(0, 6.28), r.uniform(150, 280)
        body.append(f'<circle cx="{cx + d * math.cos(a):.0f}" cy="{cy + d * math.sin(a):.0f}" r="5" fill="{MAG if k < 2 else CYAN}" filter="url(#glow)"/>')
    body.append(t(cx, cy - 8, "ROOT", 64, ICE, 1, "middle", 'font-weight="800" letter-spacing="16" filter="url(#glow)"'))
    body.append(t(cx, cy + 34, "uid=0(root) gid=0(root)", 16, SKY, .85, "middle", 'letter-spacing="2"'))
    for i, s in enumerate(["SYS ......... ONLINE", "LAYER/KALI .. NATIVE", "LAYER/BA .... STANDBY", "VPN ......... tun0", "TGT ......... 10.10.11.5"]):
        body.append(t(80, 120 + i * 30, s, 16, [SKY, SKY, YEL, CYAN, MAG][i], .85, extra='letter-spacing="2"'))
    for i, s in enumerate(["▮▮▮▮▮▮▮▮▯▯ CPU", "▮▮▮▮▮▯▯▯▯▯ MEM", "▮▮▮▮▮▮▮▮▮▯ NET"]):
        body.append(t(W - 80, 120 + i * 30, s, 16, SKY, .8, "end", 'letter-spacing="2"'))
    body.append(kmark(W / 2, H - 46, anchor="middle"))
    body.append(brackets(28, 70, KBLUE))
    svg("kali-rolling-hud", "".join(body), extra_defs=defs)


# ------------------------------------------------------------------ 08 deep blue rain
def deep_blue_rain():
    """Glyph rain in Kali blue, with the edition wordmark."""
    r = random.Random(1108)
    glyphs = "0123456789abcdef<>/\\|=+*#$%{}[]:;~"
    body, step, size = [], 22, 19
    for col in range(W // step + 1):
        x = col * step + r.uniform(-2, 2)
        head, length = r.uniform(-200, H + 300), r.randint(10, 40)
        color = MAG if r.random() < .08 else (CYAN if r.random() < .25 else KBLUE)
        for k in range(length):
            y = head - k * (size + 2)
            if -20 < y < H + 20:
                op = max(.05, 1 - k / length)
                body.append(t(x, y, r.choice(glyphs), size, ICE if k == 0 else color, op * r.uniform(.6, 1),
                              extra='filter="url(#softglow)"' if k == 0 else ""))
    body.append(f'<rect x="{W / 2 - 560}" y="{H / 2 - 115}" width="1120" height="210" fill="{NAVY}" opacity=".82"/>')
    body.append(f'<rect x="{W / 2 - 560}" y="{H / 2 - 115}" width="1120" height="210" fill="none" stroke="{KBLUE}" stroke-width="2" opacity=".8"/>')
    body.append(kword(W / 2, H / 2 + 16, 92, f"{ED}  ·  DATA STREAM"))
    body.append(brackets(28, 70, KBLUE))
    svg("kali-deep-blue-rain", "".join(body), bg="#02040c")


# ------------------------------------------------------------------ 09 glitch edition
def glitch_edition():
    """Big glitched wordmark with RGB-split slices and scanline tears."""
    r = random.Random(1109)
    defs = lin("gebg", [(0, "#020513", 1), (1, "#0a1638", 1)], x2=1, y2=1)
    body = [f'<rect width="{W}" height="{H}" fill="url(#gebg)"/>']
    for k in range(40):
        y, h = r.uniform(0, H), r.uniform(2, 26)
        body.append(f'<rect x="{r.uniform(-200, W * .6):.0f}" y="{y:.0f}" width="{r.uniform(200, 1200):.0f}" height="{h:.0f}" fill="{r.choice([KBLUE, SKY, MAG, CYAN])}" opacity="{r.uniform(.04, .18):.2f}"/>')
    cy = H / 2 + 30
    for dx, col, op in [(-10, MAG, .55), (10, CYAN, .55), (0, ICE, 1)]:
        extra = 'font-weight="900" letter-spacing="6"' + (' filter="url(#glow)"' if col == ICE else "")
        body.append(t(W / 2 + dx, cy, "ATTACKFRAME", 190, col, op, "middle", extra))
    for k in range(9):  # displaced slices
        y = cy - 150 + r.uniform(0, 170)
        h = r.uniform(6, 22)
        off = r.uniform(-60, 60)
        defs += f'<clipPath id="ges{k}"><rect x="0" y="{y:.0f}" width="{W}" height="{h:.0f}"/></clipPath>'
        body.append(f'<g clip-path="url(#ges{k})"><rect x="0" y="{y:.0f}" width="{W}" height="{h:.0f}" fill="#020513"/>'
                    + t(W / 2 + off, cy, "ATTACKFRAME", 190, r.choice([SKY, MAG, ICE]), .95, "middle", 'font-weight="900" letter-spacing="6"') + '</g>')
    body.append(f'<rect x="{W / 2 - 420}" y="{cy + 50}" width="840" height="56" fill="{KBLUE}"/>')
    body.append(t(W / 2, cy + 88, f"//  {ED}  //", 30, "#ffffff", 1, "middle", 'font-weight="800" letter-spacing="16"'))
    body.append(t(W / 2, cy + 150, "debian roots · rolling release · offensive by design", 17, SKY, .75, "middle", 'letter-spacing="5"'))
    body.append(tag(60, 60, "SIGNAL CORRUPT // 0x41414141", MAG))
    body.append(tag(W - 60, H - 50, "build kali-rolling amd64", SKY, "end"))
    body.append(brackets(28, 70, SKY))
    svg("kali-glitch-edition", "".join(body), extra_defs=defs)


# ------------------------------------------------------------------ 10 minimal
def kali_minimal():
    """Quiet, low-distraction: navy with a thin blue horizon line and small mark."""
    r = random.Random(1110)
    defs = lin("kmbg", [(0, "#020611", 1), (1, "#081733", 1)])
    body = [f'<rect width="{W}" height="{H}" fill="url(#kmbg)"/>', stars(r, 120, H * .7, (.08, .45))]
    y = H * .68
    body.append(f'<rect x="0" y="{y - 1:.0f}" width="{W}" height="2" fill="{KBLUE}" opacity=".9" filter="url(#glow)"/>')
    body.append(f'<ellipse cx="{W / 2}" cy="{y:.0f}" rx="700" ry="40" fill="{KBLUE}" opacity=".18" filter="url(#bigglow)"/>')
    for k in range(1, 6):
        body.append(f'<rect x="0" y="{y + k * k * 12:.0f}" width="{W}" height="1" fill="{KBLUE}" opacity="{.35 / k:.2f}"/>')
    body.append(t(W / 2, y - 40, "ATTACK//FRAME", 30, ICE, .85, "middle", 'font-weight="300" letter-spacing="26"'))
    body.append(t(W / 2, y + 60, ED, 13, SKY, .6, "middle", 'letter-spacing="14"'))
    svg("kali-minimal", "".join(body), extra_defs=defs, scan=False)


WALLPAPERS = [
    ("kali-root-shell", "Root Shell", root_shell), ("kali-blue-horizon", "Blue Horizon", blue_horizon),
    ("kali-neon-wyrm", "Neon Wyrm", neon_wyrm), ("kali-dual-layer", "Dual Layer", dual_layer),
    ("kali-recon-map", "Recon Map", recon_map), ("kali-blue-rain-city", "Blue Rain City", blue_rain_city),
    ("kali-rolling-hud", "Rolling HUD", rolling_hud), ("kali-deep-blue-rain", "Deep Blue Rain", deep_blue_rain),
    ("kali-glitch-edition", "Glitch Edition", glitch_edition), ("kali-minimal", "Minimal", kali_minimal),
]

if __name__ == "__main__":
    for _, _, fn in WALLPAPERS:
        fn()
    names = wp1.OUT / "names.tsv"
    existing = names.read_text() if names.exists() else ""
    extra = "".join(f"af-{s}\tKali {n}\n" for s, n, _ in WALLPAPERS if f"af-{s}\t" not in existing)
    names.write_text(existing + extra)
    print(f"wrote {len(WALLPAPERS)} Kali-edition wallpapers to {wp1.OUT}")
