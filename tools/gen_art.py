#!/usr/bin/env python3
"""Many Waters - procedural pixel-art generator.

Draws every pixel-art asset for the game (tiles, people, animals, props,
decor, parallax backgrounds) and writes RGBA PNGs into ../assets/.
Deterministic: all randomness comes from seeded NumPy generators.

    python tools/gen_art.py
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'assets')
SEED = 1938

# ----------------------------------------------------------------------------
# PALETTE  (hue-shifted ramps: shadows lean blue/violet, highlights warm)
# ----------------------------------------------------------------------------
PAL = {
    # outlines
    'ink': '#140c1c', 'ink2': '#241a30',
    # rock (blue slate)
    'rock0': '#0f1424', 'rock1': '#1c2438', 'rock2': '#2a3550', 'rock3': '#3b4a6a', 'rock4': '#566a8c',
    'false_tell': '#4a4a62',
    # moss
    'moss0': '#1e3a2a', 'moss1': '#3a6232', 'moss2': '#68903a', 'moss3': '#a8c458',
    # dirt / loam
    'dirt0': '#2a160f', 'dirt1': '#4a2a1a', 'dirt2': '#6a4026', 'dirt3': '#8a5a34', 'dirt4': '#ae7c4a',
    'root0': '#3a2214', 'root1': '#7a5634', 'root2': '#b08a5a',
    'worm': '#c86a78', 'worm_hl': '#f0a4a4', 'bone': '#ece0c4', 'bone_dk': '#a4967a',
    'peb0': '#3e3c50', 'peb1': '#6e6c82', 'peb2': '#a6a4b6',
    # wood / bark
    'wood0': '#1e0e0c', 'wood1': '#43241a', 'wood2': '#6c3e22', 'wood3': '#965e2e', 'wood4': '#c48a48', 'wood5': '#e8bc72',
    'bark0': '#1a1210', 'bark1': '#36261c', 'bark2': '#55402c', 'bark3': '#7a6044',
    # granite (pink-grey)
    'gran0': '#4e4250', 'gran1': '#7a6a76', 'gran2': '#a08e94', 'gran3': '#c4b0ae', 'gran4': '#e6d4c8',
    'gran_pink': '#d49a8a', 'gran_blk': '#2a2232', 'lichen': '#b4c070',
    # concrete (green-grey)
    'conc0': '#2a332e', 'conc1': '#46524a', 'conc2': '#647068', 'conc3': '#848f84', 'conc4': '#a8b0a0',
    'rust0': '#5e2e18', 'rust1': '#9a5222', 'rust2': '#c8782e',
    # cliff (wet, dark)
    'cliff0': '#06080f', 'cliff1': '#0e1320', 'cliff2': '#172034', 'cliff3': '#22304a',
    'cliff_wet': '#4c7c96', 'cliff_glint': '#a8e0f0',
    # boards
    'board0': '#1a1416', 'board1': '#3e3430', 'board2': '#5e5248', 'board3': '#82735f', 'board4': '#a89a80',
    'rot0': '#232a1c', 'rot1': '#3e4a2a', 'nail': '#9a9aa8', 'nail_dk': '#3a3440',
    # grass & flora
    'grass0': '#16301e', 'grass1': '#245026', 'grass2': '#3e7e2c', 'grass3': '#70b23a', 'grass4': '#b8e05e',
    'leaf_red': '#c8242a', 'leaf_org': '#e8701e', 'leaf_gold': '#f2bc2a',
    'flower_w': '#f6f2fa', 'flower_v': '#9a78e0', 'flower_vd': '#5e44a0', 'flower_y': '#f8d848', 'flower_p': '#ec8ab4',
    # glow
    'glow0': '#126464', 'glow1': '#36c8bc', 'glow2': '#b0fff2',
    'vglow0': '#4a2a7a', 'vglow1': '#a060e0', 'vglow2': '#e8c0ff',
    'gold0': '#8a5410', 'gold1': '#e0a830', 'gold2': '#ffe48a',
    # water
    'foam': '#e6fff8', 'water_hi': '#7ce6dc', 'water1': '#2a9ca4', 'water0': '#12606e', 'water_deep': '#0a3448',
    'spring0': '#0c7488', 'spring1': '#1eb0bc', 'spring2': '#5ce4dc', 'spring3': '#cafff6',
    # cave background
    'cave0': '#07060c', 'cave1': '#0f0d18', 'cave2': '#171424', 'cave3': '#211d32', 'cave4': '#2e2944',
    # flesh (the creature's spread)
    'flesh0': '#4a0a1a', 'flesh1': '#8e1630', 'flesh2': '#d23a4c', 'flesh3': '#ff8a8a',
    # people
    'skin0': '#8a4636', 'skin1': '#d0845e', 'skin2': '#f4bc92',
    'hair0': '#3a2216', 'hair1': '#6a3e22', 'hairR': '#8a3a1a', 'hairG': '#8a8478',
    'plaid_r': '#c4222a', 'plaid_rl': '#e84a3a', 'plaid_k': '#24141c', 'plaid_kr': '#5a1420',
    'jean0': '#1e2440', 'jean1': '#2e3a64', 'jean2': '#46598a',
    'boot0': '#1e120e', 'boot1': '#3e261a', 'boot2': '#6a4a30',
    'knit0': '#1e2e48', 'knit1': '#2e4a70', 'knit2': '#e8dcc0',
    'shirtw0': '#8c8a98', 'shirtw1': '#cfc8b4', 'shirtw2': '#f4eedc',
    'over0': '#3a2416', 'over1': '#6a4428', 'over2': '#946a40',
    'cap0': '#2e2a2a', 'cap1': '#55504a', 'cap2': '#7c766a',
    'khaki0': '#6a5a34', 'khaki1': '#ac9460', 'khaki2': '#d8c48c',
    'blue0': '#2a3a78', 'blue1': '#4a6ab8', 'blue2': '#80a4e0',
    'grey0': '#2a2a36', 'grey1': '#4a4a5c', 'grey2': '#6e6e84',
    'tie': '#b0202e', 'tie_dk': '#6a1020',
    'fed0': '#2e221e', 'fed1': '#54443a', 'fed2': '#7a6656',
    'green0': '#1c3a24', 'green1': '#2e5e34', 'green2': '#4e8a48',
    'camp0': '#6a4a22', 'camp1': '#a8803e', 'camp2': '#d8b46a',
    'dress0': '#2a3a70', 'dress1': '#4a68b0', 'dress2': '#86a6e0',
    'bonnet0': '#9a907e', 'bonnet1': '#dcd2bc', 'bonnet2': '#fff8e6', 'ribbon': '#d8607a',
    'stock0': '#2a2230', 'stock1': '#4a3e4a',
    'steel0': '#3a3e4c', 'steel1': '#7a8294', 'steel2': '#c4ccdc', 'steel3': '#f0f6ff',
    'rod_r': '#d02a2a', 'rod_w': '#f4f0e6',
    'plan0': '#3a68b0', 'plan1': '#78a8e8', 'plan2': '#d0e4ff',
    'dyn': '#c82a20', 'dyn_dk': '#7a1414', 'spark0': '#ff8a1e', 'spark1': '#fff27a',
    'mouth': '#4a0e18', 'eye_w': '#f4f4ff',
    # animals
    'deer0': '#4a2a16', 'deer1': '#82522a', 'deer2': '#b07a42', 'deer3': '#d4a466', 'deer_w': '#f0e8dc',
    'wool0': '#8a8070', 'wool1': '#c8bca4', 'wool2': '#ece2cc', 'wool3': '#fffaee', 'sheep_face': '#2a2028',
    # slate headstones
    'slate0': '#1c202c', 'slate1': '#2e3444', 'slate2': '#434c62', 'slate3': '#5c6882', 'slate4': '#828ea8',
    # white clapboard (shadows violet, light warm)
    'wht0': '#3e3e5e', 'wht1': '#6c6c8e', 'wht2': '#9e9eb8', 'wht3': '#c8c8d6', 'wht4': '#e8e6e0', 'wht5': '#fffcf0',
    'glass0': '#121828', 'glass1': '#2a3a5a', 'glass2': '#5a7aa0', 'lit_win': '#ffd27a',
    'roof0': '#141824', 'roof1': '#262c3c', 'roof2': '#3a4256', 'roof3': '#566078',
    'red0': '#3a0e12', 'red1': '#6e1a1a', 'red2': '#a02a22', 'red3': '#c84a32', 'red4': '#e07a4e',
    'brick0': '#3a1612', 'brick1': '#6e2a1e', 'brick2': '#9a4430',
    'fstone0': '#2a2630', 'fstone1': '#4a4450', 'fstone2': '#6e6670', 'fstone3': '#948a8e', 'fstone4': '#bab0aa',
    'algae0': '#0e2420', 'algae1': '#1e4434', 'algae2': '#3a6a44', 'algae3': '#6a9a52',
    # tree ramps
    'mr0': '#2a0a1e', 'mr1': '#5a0f24', 'mr2': '#9a1a26', 'mr3': '#d0302a', 'mr4': '#f0642c', 'mr5': '#ffaa48',
    'mo0': '#2e1018', 'mo1': '#6a2418', 'mo2': '#b04412', 'mo3': '#e47414', 'mo4': '#f8a42c', 'mo5': '#ffdc62',
    'mg0': '#2a1c18', 'mg1': '#5e3c14', 'mg2': '#a07010', 'mg3': '#dcaa18', 'mg4': '#f6d63a', 'mg5': '#fff4a0',
    'pine0': '#08161a', 'pine1': '#0e2824', 'pine2': '#16402e', 'pine3': '#24603a', 'pine4': '#3e8248', 'pine5': '#74a85a',
    'sg0': '#14281c', 'sg1': '#1e4226', 'sg2': '#326230', 'sg3': '#4e8a3a', 'sg4': '#80b44e',
    'bloom0': '#c86a90', 'bloom1': '#f0a2c0', 'bloom2': '#ffd8e6', 'bloom3': '#ffffff',
    'birch0': '#3a3a4a', 'birch1': '#b8b4c0', 'birch2': '#e8e6e8', 'birch3': '#fffef6',
    # burners / foreman (rubberised coats, leather hoods, brass)
    'rub0': '#18241f', 'rub1': '#2f4234', 'rub2': '#4e6650', 'rub3': '#7e9474',
    'lea0': '#24140e', 'lea1': '#4e2c1a', 'lea2': '#7a4a28', 'lea3': '#a8743e',
    'gog0': '#10262a', 'gog1': '#4aa8a0', 'gog2': '#d4fff2',
    'brass0': '#4a2e0e', 'brass1': '#8e6420', 'brass2': '#cca042', 'brass3': '#fbe490',
    'amber0': '#7a2e06', 'amber1': '#ff9a1e', 'amber2': '#ffe890',
    'pilot0': '#2a4ad0', 'pilot1': '#8ac4ff', 'pilot2': '#f0faff',
    'fire0': '#7a160a', 'fire1': '#d2441a', 'fire2': '#ff9628', 'fire3': '#ffe476',
    # char / smoke
    'char0': '#0c080c', 'char1': '#211a20', 'char2': '#3a3036', 'char3': '#5c4e4e', 'ash': '#9a9096',
    'smoke0': '#3a3644', 'smoke1': '#6a6676', 'smoke2': '#a4a0ae',
    # bloodhound
    'dog0': '#4a2410', 'dog1': '#8a4e22', 'dog2': '#bc7e3a', 'dog3': '#e4ae68',
    'dogk0': '#140e14', 'dogk1': '#2e2228', 'dogk2': '#4e3c3e',
    # steam shovel (oxide-red house, black iron running gear)
    'ox0': '#2a0e14', 'ox1': '#561c1c', 'ox2': '#863022', 'ox3': '#b0502e', 'ox4': '#d67e48',
    'iron0': '#0e0e14', 'iron1': '#20202a', 'iron2': '#363644', 'iron3': '#555566', 'iron4': '#7c7c90',
    # ---- expansion 2: railroad trestle, living root, diver, houndmaster, locomotive boss
    # creosote-stained timber (violet shadows, warm amber-brown lights)
    'cre0': '#110a12', 'cre1': '#241820', 'cre2': '#3a2a2a', 'cre3': '#574234', 'cre4': '#7c6248', 'cre5': '#a48660',
    # living root / sinew (crimson-brown)
    'lr0': '#1c0614', 'lr1': '#3e0e1e', 'lr2': '#6c1c2a', 'lr3': '#9a3236', 'lr4': '#c45a46', 'lr5': '#ec9a74',
    # diving-helmet copper
    'cop0': '#3a1418', 'cop1': '#76321e', 'cop2': '#b45e2a', 'cop3': '#e4964a', 'cop4': '#ffd286',
    # diving-suit canvas
    'cnv0': '#3e3640', 'cnv1': '#6e6458', 'cnv2': '#a09478', 'cnv3': '#d0c4a0',
    # waxed-cotton coat (olive)
    'wax0': '#151a18', 'wax1': '#2a3024', 'wax2': '#474c30', 'wax3': '#6c6c40',
    # verdigris, signal green
    'verd0': '#1e4448', 'verd1': '#3a8478', 'verd2': '#7cc8a4',
    'sig_g0': '#16603a', 'sig_g1': '#3ed07a', 'sig_g2': '#c8ffd4',
    # coal smoke (grey-violet)
    'smk0': '#3c3448', 'smk1': '#625a72', 'smk2': '#8e869c', 'smk3': '#bcb4c4',
}

# ----------------------------------------------------------------------------
# core helpers
# ----------------------------------------------------------------------------
_CC = {}


def C(c, a=None):
    """Colour from palette name / hex / tuple -> RGBA tuple."""
    if isinstance(c, tuple):
        t = c if len(c) == 4 else (*c, 255)
    else:
        key = c
        if key in _CC:
            t = _CC[key]
        else:
            h = PAL.get(c, c).lstrip('#')
            t = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
            _CC[key] = t
    if a is not None:
        t = (t[0], t[1], t[2], a)
    return t


def mix(c1, c2, t, a=None):
    p, q = C(c1), C(c2)
    r = tuple(int(round(p[i] * (1 - t) + q[i] * t)) for i in range(4))
    return C(r, a)


def shade(c, f, blue=0.0):
    """Darken by f with a hue shift toward blue/violet."""
    p = C(c)
    r, g, b = p[0] * f, p[1] * f, p[2] * f
    b = b + (255 - b) * blue * 0.25
    r = r * (1 - blue * 0.25)
    return (int(min(255, r)), int(min(255, g)), int(min(255, b)), p[3])


def bayer(n):
    m = np.array([[0, 2], [3, 1]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / m.size


B4 = bayer(4)
B8 = bayer(8)


def blend(dst, src):
    sa = src[3] / 255.0
    da = dst[3] / 255.0
    oa = sa + da * (1 - sa)
    if oa <= 0:
        return (0, 0, 0, 0)
    rgb = [(src[i] * sa + dst[i] * da * (1 - sa)) / oa for i in range(3)]
    return (int(rgb[0] + .5), int(rgb[1] + .5), int(rgb[2] + .5), int(oa * 255 + .5))


def bres(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


class Canvas:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        if fill is not None:
            self.a[:, :] = C(fill)

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def px(self, x, y, col):
        x, y = int(math.floor(x)), int(math.floor(y))
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        col = C(col)
        if col[3] >= 255 or self.a[y, x, 3] == 0:
            self.a[y, x] = col
        elif col[3] > 0:
            self.a[y, x] = blend(tuple(int(v) for v in self.a[y, x]), col)

    def pxw(self, x, y, col):
        self.px(int(math.floor(x)) % self.w, y, col)

    def get(self, x, y):
        x, y = int(math.floor(x)), int(math.floor(y))
        if not self.inb(x, y):
            return (0, 0, 0, 0)
        return tuple(int(v) for v in self.a[y, x])

    def solid(self, x, y):
        return self.get(x, y)[3] > 0

    def rect(self, x0, y0, x1, y1, col):
        col = C(col)
        if col[3] == 255:
            xa, xb = max(0, int(x0)), min(self.w - 1, int(x1))
            ya, yb = max(0, int(y0)), min(self.h - 1, int(y1))
            if xa <= xb and ya <= yb:
                self.a[ya:yb + 1, xa:xb + 1] = col
            return
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.px(x, y, col)

    def line(self, x0, y0, x1, y1, col, wrap=False):
        for (x, y) in bres(x0, y0, x1, y1):
            (self.pxw if wrap else self.px)(x, y, col)

    def thick(self, x0, y0, x1, y1, col, col2=None, wrap=False):
        col2 = col2 or col
        vert = abs(y1 - y0) >= abs(x1 - x0)
        f = self.pxw if wrap else self.px
        for (x, y) in bres(x0, y0, x1, y1):
            f(x, y, col)
            if vert:
                f(x + 1, y, col2)
            else:
                f(x, y + 1, col2)

    def ellipse(self, cx, cy, rx, ry, col, wrap=False):
        f = self.pxw if wrap else self.px
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0:
                    f(x, y, col)

    def poly(self, pts, col):
        m = Image.new('L', (self.w, self.h), 0)
        ImageDraw.Draw(m).polygon([(float(x), float(y)) for x, y in pts], fill=255)
        mask = np.array(m) > 0
        col = C(col)
        if col[3] == 255:
            self.a[mask] = col
        else:
            for y, x in zip(*np.nonzero(mask)):
                self.px(x, y, col)
        return mask

    def mask_fill(self, mask, col):
        self.a[mask] = C(col)

    def blit(self, src, x, y):
        s = src.a if isinstance(src, Canvas) else src
        sh, sw = s.shape[:2]
        x, y = int(x), int(y)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + sw), min(self.h, y + sh)
        if x1 <= x0 or y1 <= y0:
            return
        ss = s[y0 - y:y1 - y, x0 - x:x1 - x].astype(float)
        dd = self.a[y0:y1, x0:x1].astype(float)
        sa, da = ss[..., 3:4] / 255, dd[..., 3:4] / 255
        oa = sa + da * (1 - sa)
        rgb = (ss[..., :3] * sa + dd[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6)
        out = np.concatenate([rgb, oa * 255], -1)
        self.a[y0:y1, x0:x1] = np.clip(out + 0.5, 0, 255).astype(np.uint8)

    def image(self):
        return Image.fromarray(self.a, 'RGBA')

    def save(self, name):
        self.image().save(os.path.join(OUT, name))


def shift(arr, dy, dx):
    out = np.zeros_like(arr)
    h, w = arr.shape[:2]
    ys0, ys1 = max(0, dy), h + min(0, dy)
    xs0, xs1 = max(0, dx), w + min(0, dx)
    out[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx] = arr[ys0:ys1, xs0:xs1]
    return out


N4 = [(0, 1), (0, -1), (1, 0), (-1, 0)]


def outline(cv, col=None, diag=False, mul=(0.30, 0.28, 0.42), skip_bottom=False, wrap_x=False):
    """1px outline around opaque pixels. col=None -> selective (darkened neighbour)."""
    a = cv.a
    m = a[..., 3] > 200
    offs = N4 + ([(1, 1), (1, -1), (-1, 1), (-1, -1)] if diag else [])
    acc = np.zeros(a.shape[:2] + (3,), float)
    cnt = np.zeros(a.shape[:2], float)
    for dy, dx in offs:
        if wrap_x:
            sm = np.roll(shift(m, dy, 0), -dx, axis=1)
            sc = np.roll(shift(a[..., :3].astype(float), dy, 0), -dx, axis=1)
        else:
            sm = shift(m, dy, dx)
            sc = shift(a[..., :3].astype(float), dy, dx)
        acc += sc * sm[..., None]
        cnt += sm
    edge = (a[..., 3] == 0) & (cnt > 0)
    if skip_bottom:
        pass
    if col is not None:
        a[edge] = C(col)
    else:
        avg = acc / np.maximum(cnt, 1)[..., None]
        dark = avg * np.array(mul) + np.array([6, 4, 14])
        a[edge, :3] = np.clip(dark[edge], 0, 255).astype(np.uint8)
        a[edge, 3] = 255
    return cv


def dramp(t, ramp, x0=0, y0=0, B=B4):
    """Ordered-dither a float field t (0..1) onto a colour ramp."""
    t = np.clip(t, 0, 1) * (len(ramp) - 1)
    h, w = t.shape
    i = np.floor(t).astype(int)
    f = t - i
    yy, xx = np.mgrid[0:h, 0:w]
    thr = B[(yy + y0) % B.shape[0], (xx + x0) % B.shape[1]]
    i = np.clip(i + (f > thr), 0, len(ramp) - 1)
    R = np.array([C(c) for c in ramp], np.uint8)
    return R[i]


def dpick(ramp, t, x, y, B=B4):
    t = min(max(t, 0.0), 1.0) * (len(ramp) - 1)
    i = int(t)
    if i >= len(ramp) - 1:
        return C(ramp[-1])
    return C(ramp[i + 1]) if (t - i) > B[y % B.shape[0], x % B.shape[1]] else C(ramp[i])


def vnoise(w, h, cx, cy, rng):
    """Periodic value noise (period = w, h)."""
    g = rng.random((cy, cx))
    xs = (np.arange(w) + .5) * cx / w
    ys = (np.arange(h) + .5) * cy / h
    x0 = np.floor(xs).astype(int)
    y0 = np.floor(ys).astype(int)
    fx, fy = xs - x0, ys - y0
    x1, y1 = (x0 + 1) % cx, (y0 + 1) % cy
    x0, y0 = x0 % cx, y0 % cy
    sx = (fx * fx * (3 - 2 * fx))[None, :]
    sy = (fy * fy * (3 - 2 * fy))[:, None]
    a, b = g[np.ix_(y0, x0)], g[np.ix_(y0, x1)]
    c, d = g[np.ix_(y1, x0)], g[np.ix_(y1, x1)]
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy


def fbm(w, h, cx, cy, rng, octaves=3, gain=0.5):
    tot = np.zeros((h, w))
    amp, s = 1.0, 0.0
    for o in range(octaves):
        tot += amp * vnoise(w, h, cx * 2 ** o, cy * 2 ** o, rng)
        s += amp
        amp *= gain
    tot /= s
    return (tot - tot.min()) / (tot.max() - tot.min() + 1e-9)


def poisson_pts(rng, w, h, n, mind, tries=3000):
    pts = []
    for _ in range(tries):
        if len(pts) >= n:
            break
        p = (rng.uniform(0, w), rng.uniform(0, h))
        ok = True
        for q in pts:
            dx = abs(p[0] - q[0]); dx = min(dx, w - dx)
            dy = abs(p[1] - q[1]); dy = min(dy, h - dy)
            if dx * dx + dy * dy < mind * mind:
                ok = False
                break
        if ok:
            pts.append(p)
    return pts


def vor(w, h, pts):
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    xx += .5
    yy += .5
    D, VX, VY = [], [], []
    for (px_, py_) in pts:
        dx = (px_ - xx + w / 2) % w - w / 2
        dy = (py_ - yy + h / 2) % h - h / 2
        D.append(np.hypot(dx, dy)); VX.append(dx); VY.append(dy)
    D, VX, VY = np.stack(D), np.stack(VX), np.stack(VY)
    o = np.argsort(D, 0)
    d1 = np.take_along_axis(D, o[:1], 0)[0]
    d2 = np.take_along_axis(D, o[1:2], 0)[0]
    vx = np.take_along_axis(VX, o[:1], 0)[0]
    vy = np.take_along_axis(VY, o[:1], 0)[0]
    n = np.maximum(d1, 1e-6)
    return o[0], d1, d2, vx / n, vy / n


def blob_field(cv, cx, cy, rx, ry, ramp, rng, light=(-0.6, -0.8), bias=0.0, rough=0.8,
               wrap=False, contrast=0.45, gl=None, noise_amp=0.12, idmap=None, ident=0):
    """Draw a shaded leafy/rocky blob. gl = (gcx, gcy, gr) adds a global light term."""
    W = cv.w
    xs_off = [0] if not wrap else [-W, 0, W]
    x0, x1 = int(cx - rx - 2), int(cx + rx + 3)
    y0, y1 = max(0, int(cy - ry - 2)), min(cv.h, int(cy + ry + 3))
    if y1 <= y0:
        return
    hh, ww = y1 - y0, x1 - x0
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(float)
    nx, ny = (xx + .5 - cx) / rx, (yy + .5 - cy) / ry
    d = np.sqrt(nx * nx + ny * ny)
    jag = rng.random((hh, ww))
    inside = d <= 1.0 - (jag - 0.5) * rough * (2.0 / max(rx, 2))
    lit = -(nx * light[0] + ny * light[1])
    t = 0.5 + bias + contrast * lit * np.clip(d, 0, 1) ** 0.7
    if gl is not None:
        gx, gy, gr = gl
        t += 0.22 * (-((xx - gx) * light[0] + (yy - gy) * light[1]) / gr)
    t += (rng.random((hh, ww)) - 0.5) * noise_amp
    cols = dramp(t, ramp, x0, y0)
    for off in xs_off:
        for j in range(hh):
            for i in range(ww):
                if inside[j, i]:
                    X = x0 + i + off
                    if wrap:
                        X %= W
                    if 0 <= X < W:
                        cv.a[y0 + j, X] = cols[j, i]
                        if idmap is not None:
                            idmap[y0 + j, X] = ident


def save_img(img, name):
    img.save(os.path.join(OUT, name))


# ============================================================================
# TILES  (128x224, 16x16 cells)
# ============================================================================
T = 16
ROCK_RAMP = ['rock1', 'rock2', 'rock3', 'rock4']


def border_ids(i1):
    return set(np.unique(np.concatenate([i1[0], i1[-1], i1[:, 0], i1[:, -1]])).tolist())


def rock_base(rng, npts=7, mind=4.6):
    pts = poisson_pts(rng, T, T, npts, mind)
    i1, d1, d2, vx, vy = vor(T, T, pts)
    return dict(pts=pts, i1=i1, d1=d1, d2=d2, vx=vx, vy=vy,
                tone=rng.uniform(-0.07, 0.07, len(pts)), n=fbm(T, T, 4, 4, rng, 2))


def render_chunks(b, tone, ramp, crack_col, base=0.40, hl=0.40, noise=0.16, crack_w=1.0):
    e = np.clip((b['d2'] - b['d1']) / 2, 0, 3) / 3
    L = b['vx'] * 0.6 + b['vy'] * 0.8
    t = base + tone[b['i1']] + hl * L * (1 - e) ** 1.4 + (b['n'] - .5) * noise
    arr = dramp(t, ramp)
    crack = (b['d2'] - b['d1']) < crack_w
    arr[crack] = C(crack_col)
    return arr, crack


def moss_fleck(cv, x, y, rng):
    shapes = [[(0, 0), (1, 0), (2, 0), (1, -1)], [(0, 0), (1, 0), (0, -1)],
              [(0, 0), (1, 0), (2, 0), (3, 0), (1, -1), (2, -1)], [(0, 0), (1, 0)]]
    s = shapes[int(rng.integers(len(shapes)))]
    for dx, dy in s:
        cv.px(x + dx, y + dy, 'moss3' if dy < 0 else ('moss2' if (dx + x) % 2 else 'moss1'))
    for dx, dy in s:
        if dy == 0 and rng.random() < .6:
            cv.px(x + dx, y + 1, 'moss0')


def small_crack(cv, x, y, rng, n=4, dark='rock0', lite='rock3'):
    for _ in range(n):
        cv.px(x, y, dark)
        if rng.random() < .5:
            cv.px(x + 1, y + 1, lite)
        x += int(rng.integers(-1, 2))
        y += 1
        x = min(max(x, 2), 13)
        if y > 13:
            break


def interior_pts(rng, k, cond=None):
    out = []
    for _ in range(300):
        x, y = int(rng.integers(2, 13)), int(rng.integers(2, 13))
        if cond is None or cond(x, y):
            out.append((x, y))
            if len(out) >= k:
                break
    return out


def rock_tiles(rng, false_tell=False, base=None):
    b = base
    border = border_ids(b['i1'])
    tiles = []
    for v in range(4):
        r = np.random.default_rng(100 + v)
        tone = b['tone'].copy()
        for k in range(len(tone)):
            if k not in border:
                tone[k] += r.uniform(-0.12, 0.12)
        arr, crack = render_chunks(b, tone, ROCK_RAMP, 'rock0')
        cv = Canvas(T, T)
        cv.a[:] = arr

        def top_edge(x, y):
            return (not crack[y, x]) and crack[y - 1, x] and not crack[y, x + 1]
        for (x, y) in interior_pts(r, [2, 1, 3, 1][v], top_edge):
            moss_fleck(cv, x, y, r)
        if v == 1:
            small_crack(cv, 5, 3, r, 5)
            small_crack(cv, 10, 8, r, 4)
        if v == 3:   # thin quartz vein
            for i in range(6):
                cv.px(4 + i, 10 - i // 2, 'rock4' if i % 2 else '#7e92b4')
        if v == 2:
            small_crack(cv, 8, 6, r, 3)
        if v == 0:
            cv.px(11, 11, 'rock4')
            cv.px(12, 11, 'rock3')
        if false_tell:
            # the tell: a 2-pixel seam on the right edge, a hair warmer than real rock
            cv.px(15, 7, 'false_tell')
            cv.px(15, 8, mix('false_tell', 'rock2', .5))
        tiles.append(cv)
    return tiles


def pebble(cv, x, y, big=False, shadow='dirt0'):
    cv.px(x, y, 'peb2'); cv.px(x + 1, y, 'peb1'); cv.px(x, y + 1, 'peb1'); cv.px(x + 1, y + 1, 'peb0')
    if big:
        cv.px(x + 2, y, 'peb1'); cv.px(x + 2, y + 1, 'peb0')
    cv.px(x, y + 2, shadow); cv.px(x + 1, y + 2, shadow)


def dirt_tiles(rng):
    n = fbm(T, T, 4, 4, rng, 2)
    n2 = rng.random((T, T))
    tiles = []
    for v in range(4):
        t = 0.40 + 0.45 * (n - .5) + (n2 - .5) * 0.14
        cv = Canvas(T, T)
        cv.a[:] = dramp(t, ['dirt1', 'dirt2', 'dirt3', 'dirt4'])
        for (x, y) in [(3, 2), (11, 5), (6, 12), (14, 13), (0, 8)]:
            cv.px(x, y, 'dirt4'); cv.px((x + 1) % 16, y, 'dirt3'); cv.px((x + 1) % 16, y + 1, 'dirt1')
        for (x, y) in [(8, 1), (1, 14), (13, 9), (9, 7)]:
            cv.px(x, y, 'dirt0')
        if v == 0:
            pebble(cv, 4, 5, True); pebble(cv, 10, 10)
        if v == 1:  # root
            pts = [(2, 4), (3, 4), (4, 5), (5, 5), (6, 6), (7, 6), (8, 6), (9, 7), (10, 8), (11, 8), (12, 9)]
            for (x, y) in pts:
                cv.px(x, y, 'root1')
                if x % 3 == 0:
                    cv.px(x, y - 1, 'root2')
                cv.px(x, y + 1, 'root0')
            cv.px(7, 7, 'root1'); cv.px(7, 8, 'root1'); cv.px(6, 9, 'root0')
            pebble(cv, 10, 12)
        if v == 2:  # worm
            for i, (x, y) in enumerate([(5, 9), (6, 9), (7, 8), (8, 8), (9, 9), (10, 9)]):
                cv.px(x, y, 'worm_hl' if i in (2, 3) else 'worm')
                cv.px(x, y + 1, 'dirt0')
            pebble(cv, 3, 3)
        if v == 3:  # bone bit
            for (x, y, c) in [(6, 6, 'bone'), (7, 6, 'bone'), (8, 7, 'bone'), (9, 7, 'bone'), (5, 5, 'bone'),
                              (5, 7, 'bone_dk'), (10, 8, 'bone_dk'), (10, 6, 'bone'), (7, 7, 'bone_dk'),
                              (8, 8, 'dirt0'), (9, 8, 'dirt0')]:
                cv.px(x, y, c)
            pebble(cv, 11, 11)
        tiles.append(cv)
    return tiles


def log_end(cv, cx, cy, r, rng, weathered=False, ox=0.0, oy=0.0, check=False):
    ring = ['wood3', 'wood4'] if not weathered else ['board2', 'board3']
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x + .5 - cx, y + .5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            if d > r - 1.0:
                lit = -(dx * .6 + dy * .8) / max(d, .1)
                cv.px(x, y, 'bark2' if lit > .3 else ('bark1' if lit > -.4 else 'bark0'))
                continue
            dr = math.hypot(dx - ox, dy - oy)
            k = int(dr * 1.1)
            c = ring[k % 2]
            if dr < .9:
                c = 'wood2'
            if (k % 2 == 1) and (dx * .6 + dy * .8) < -r * .3:
                c = 'wood5' if not weathered else 'board4'
            cv.px(x, y, c)
    if check:
        ang = rng.uniform(0, 2 * math.pi)
        for s in range(1, int(r)):
            cv.px(cx + math.cos(ang) * s - .5, cy + math.sin(ang) * s - .5, 'wood1')


def timber_tiles(rng):
    tiles = []
    for v in range(4):
        r = np.random.default_rng(300 + v)
        cv = Canvas(T, T, 'wood0')
        quads = [(4, 4), (12, 4), (4, 12), (12, 12)]
        for qi, (cx, cy) in enumerate(quads):
            if v == 3 and qi < 2:
                continue
            log_end(cv, cx, cy, 4.0, r, weathered=(v == 2 and qi == 1) or (v == 1 and qi == 2),
                    ox=r.uniform(-1, 1), oy=r.uniform(-1, 1), check=(v + qi) % 3 == 0)
        if v == 3:  # a side-on log lying across the top half
            for x in range(16):
                cv.px(x, 0, 'bark0')
                cv.px(x, 1, 'bark3' if x % 4 else 'bark2')
                cv.px(x, 2, 'bark2')
                for y in (3, 4, 5):
                    cv.px(x, y, 'bark1' if (x + y * 3) % 5 else 'bark0')
                cv.px(x, 6, 'bark0')
                cv.px(x, 7, 'wood0')
            cv.px(6, 3, 'wood2'); cv.px(7, 3, 'wood3'); cv.px(6, 4, 'wood1'); cv.px(7, 4, 'wood2')
        if v == 1:  # axe notch
            cv.px(11, 3, 'wood5'); cv.px(12, 4, 'wood5')
        tiles.append(cv)
    return tiles


def granite_tiles(rng):
    tiles = []
    for v in range(4):
        r = np.random.default_rng(400 + v)
        cv = Canvas(T, T)
        sp = r.random((T, T))
        for y in range(T):
            for x in range(T):
                s = sp[y, x]
                c = 'gran3' if (x + y) % 2 else 'gran2'
                if s < .08:
                    c = 'gran_blk'
                elif s < .16:
                    c = 'gran1'
                elif s > .93:
                    c = 'gran4'
                elif s > .86:
                    c = 'gran_pink'
                cv.px(x, y, c)
        for x in range(T):
            cv.px(x, 7, 'gran0'); cv.px(x, 15, 'gran0')
            cv.px(x, 0, 'gran4' if x % 3 else 'gran3'); cv.px(x, 8, 'gran4' if x % 3 != 1 else 'gran3')
            cv.px(x, 6, 'gran1' if x % 2 else 'gran2'); cv.px(x, 14, 'gran1' if x % 2 else 'gran2')
        for y in range(0, 7):
            cv.px(15, y, 'gran0'); cv.px(0, y, 'gran4' if y % 2 else 'gran3'); cv.px(14, y, 'gran1')
        for y in range(8, 15):
            cv.px(7, y, 'gran0'); cv.px(8, y, 'gran4' if y % 2 else 'gran3'); cv.px(6, y, 'gran1')
        spots = [[(3, 1), (6, 1), (9, 1)], [(10, 9), (13, 9)], [(2, 9), (4, 9)], [(5, 1), (8, 1), (11, 1)]][v]
        for (x, y) in spots:
            for k in range(3):
                cv.px(x, y + k, 'gran1'); cv.px(x + 1, y + k, 'gran4')
        if v == 2:
            for (x, y) in [(10, 3), (11, 3), (11, 4), (12, 4), (10, 4)]:
                cv.px(x, y, 'lichen')
        if v == 1:
            cv.px(13, 5, 'gran1'); cv.px(14, 5, 'gran0'); cv.px(14, 4, 'gran1')
        tiles.append(cv)
    return tiles


def concrete_tiles(rng):
    n = fbm(T, T, 2, 4, rng, 2)
    tiles = []
    for v in range(4):
        t = 0.48 + (n - .5) * 0.35
        cv = Canvas(T, T)
        cv.a[:] = dramp(t, ['conc1', 'conc2', 'conc3'])
        for x in range(T):
            for y in (3, 7, 11, 15):
                if (x * 7 + y) % 9 != 0:
                    cv.px(x, y, 'conc1' if (x + y) % 2 else 'conc2')
            for y in (0, 4, 8, 12):
                if (x + y) % 3 == 0:
                    cv.px(x, y, 'conc3')
        for (x, y) in [(2, 5), (9, 1), (13, 10), (5, 13), (11, 6)]:
            cv.px(x, y, 'conc0'); cv.px(x, y + 1, 'conc4')

        def tie(x, y):
            cv.px(x, y, 'conc0'); cv.px(x + 1, y, 'conc1'); cv.px(x, y + 1, 'conc1'); cv.px(x + 1, y + 1, 'conc3')
        if v == 0:
            tie(4, 5); tie(11, 5)
        if v == 1:
            tie(7, 3)
            for k, c in enumerate(['rust2', 'rust1', 'rust1', 'rust0', 'rust1', 'rust0', 'rust0']):
                if k < 4 or (k + 5) % 2:
                    cv.px(7, 5 + k, c)
                if k % 3 == 0:
                    cv.px(8, 6 + k, 'rust0')
        if v == 2:
            for (x, y) in [(3, 12), (4, 12), (4, 13), (5, 13), (6, 13), (10, 13), (11, 12), (11, 13)]:
                cv.px(x, y, 'moss0' if (x + y) % 2 else 'moss1')
            tie(10, 4)
        if v == 3:
            for y in range(1, 15):
                if (y % 2 == 0) or y < 6:
                    cv.px(6, y, 'conc1')
                if y < 9 and y % 2:
                    cv.px(7, y, 'conc1')
        tiles.append(cv)
    return tiles


def cliff_tiles(rng):
    n = fbm(T, T, 8, 2, rng, 2)
    colv = vnoise(T, 1, 8, 1, rng)[0]
    tiles = []
    for v in range(4):
        t = 0.32 + (n - .5) * 0.25 + (colv[None, :] - .5) * 0.5
        cv = Canvas(T, T)
        cv.a[:] = dramp(t, ['cliff0', 'cliff1', 'cliff2', 'cliff3'])
        for x in (2, 7, 12):
            for y in range(T):
                if (y + x) % 5 != 0:
                    cv.px(x, y, 'cliff0')
        streaks = [[(4, 2, 9), (10, 5, 8)], [(5, 1, 12), (14, 6, 6)], [(9, 3, 10)],
                   [(3, 6, 7), (11, 1, 11), (14, 4, 5)]][v]
        for (x, y0, ln) in streaks:
            for k in range(ln):
                y = y0 + k
                if y > 14:
                    break
                c = 'cliff_wet' if k < ln * .6 else 'cliff3'
                if k % 4 == 3:
                    c = 'cliff2'
                cv.px(x, y, c)
            cv.px(x, y0, 'cliff_glint')
        if v == 2:
            cv.px(6, 10, 'cliff_glint'); cv.px(6, 11, 'cliff_wet')
        tiles.append(cv)
    return tiles


def board_tiles(rng):
    gn = fbm(T, T, 2, 8, rng, 2)
    tiles = []
    for v in range(4):
        cv = Canvas(T, T)
        for y in range(T):
            ry = y % 4
            for x in range(T):
                if ry == 3:
                    cv.px(x, y, 'board0')
                    continue
                t = [0.75, 0.5, 0.3][ry] + (gn[y, x] - .5) * 0.5
                cv.px(x, y, dpick(['board1', 'board2', 'board3', 'board4'], t, x, y))
        joints = [[5, 11, 3, 9], [12, 4, 8, 13], [3, 9, 12, 6], [10, 6, 2, 11]][v]
        for p, jx in enumerate(joints):
            y0 = p * 4
            for k in range(3):
                cv.px(jx, y0 + k, 'board0')
            cv.px(jx - 1, y0 + 1, 'nail'); cv.px(jx - 1, y0 + 2, 'nail_dk')
            cv.px(jx + 1, y0 + 1, 'nail'); cv.px(jx + 1, y0 + 2, 'nail_dk')
            cv.px(jx + 2, y0, 'board4')
        if v in (1, 3):
            for (x, y) in [(7, 5), (8, 5), (7, 6), (8, 6), (9, 6), (6, 6), (9, 4)]:
                cv.px(x, y, 'rot1' if (x + y) % 2 else 'rot0')
        if v == 3:
            for (x, y) in [(4, 8), (5, 8), (6, 8), (5, 9), (6, 9), (4, 9), (7, 9), (5, 10), (6, 10)]:
                cv.px(x, y, 'cave0')
            cv.px(3, 8, 'board4'); cv.px(7, 8, 'board4'); cv.px(8, 9, 'board4'); cv.px(4, 10, 'board4')
        if v == 2:
            for x in range(4, 10):
                cv.px(x, 13, 'board1')
        tiles.append(cv)
    return tiles


def grass_tiles(rng):
    mat_n = vnoise(T, 1, 4, 1, rng)[0]
    tiles = []
    for v in range(4):
        r = np.random.default_rng(800 + v)
        cv = Canvas(T, T)
        depth = [14, 13, 15, 15, 12, 14, 13, 15, 14, 12, 13, 15, 14, 14, 12, 13]
        for x in range(T):
            m = mat_n[x]
            cv.px(x, 8, 'grass4' if m > .6 else 'grass3')
            cv.px(x, 9, 'grass3' if (x % 3 == 0) else 'grass2')
            cv.px(x, 10, 'grass2' if (x * 5) % 7 > 2 else 'grass1')
            cv.px(x, 11, 'grass1' if (x * 3) % 5 > 1 else 'moss1')
            cv.px(x, 12, 'dirt2' if (x * 7) % 4 else 'grass1')
            for y in range(13, depth[x] + 1):
                cv.px(x, y, 'dirt2' if (x * 7 + y * 13) % 5 == 0 else 'dirt1')
            if depth[x] < 15:
                cv.px(x, depth[x] + 1, 'dirt0')
        for x in (3, 9, 13):
            cv.px(x, 15, 'root1')
        for x in range(1, 15):
            if r.random() < .25:
                continue
            h = int(r.integers(2, 7))
            lean = int(r.integers(-1, 2)) if h > 3 else 0
            back = r.random() < .35
            for k in range(h):
                yy = 7 - k
                xx = min(max(x + (lean if k >= h // 2 else 0), 0), 15)
                if back:
                    c = 'grass1' if k < h - 1 else 'grass2'
                else:
                    c = 'grass2' if k < h // 2 else ('grass3' if k < h - 1 else 'grass4')
                cv.px(xx, yy, c)
        if v == 1:  # fern frond
            pts = [(5, 7), (5, 6), (6, 5), (7, 4), (8, 3), (9, 3), (10, 4)]
            for i, (x, y) in enumerate(pts):
                cv.px(x, y, 'grass3')
                if 1 <= i <= 5:
                    cv.px(x, y - 1, 'grass4'); cv.px(x + 1, y + 1, 'grass2')
            cv.px(10, 5, 'grass3')
        if v == 2:  # aster + goldenrod
            for y in range(3, 8):
                cv.px(6, y, 'grass2')
            for (dx, dy) in [(0, -1), (-1, 0), (1, 0), (0, 1)]:
                cv.px(6 + dx, 2 + dy, 'flower_v')
            cv.px(6, 2, 'flower_y'); cv.px(5, 1, 'flower_vd')
            for y in range(2, 8):
                cv.px(11, y, 'grass2')
            for (x, y) in [(11, 1), (12, 1), (12, 2), (10, 2), (12, 3), (11, 0)]:
                cv.px(x, y, 'flower_y' if (x + y) % 2 else 'gold1')
        if v in (0, 3):
            for (x, y, c) in ([(4, 8, 'leaf_red'), (5, 8, 'leaf_red'), (11, 9, 'leaf_gold')] if v == 0
                              else [(8, 8, 'leaf_org'), (9, 8, 'leaf_org'), (9, 9, 'mo2'), (2, 9, 'leaf_gold')]):
                cv.px(x, y, c)
            if v == 3:
                cv.px(12, 4, 'leaf_red'); cv.px(12, 5, 'leaf_red'); cv.px(13, 4, 'mr2')
        tiles.append(cv)
    return tiles


def ceiling_tiles(rng):
    tiles = []
    for v in range(4):
        r = np.random.default_rng(900 + v)
        cv = Canvas(T, T)
        prob = [0.12, 0.3, 0.55, 0.8, 1, 1, 1, 1]
        for y in range(8):
            for x in range(T):
                if prob[y] > B4[y % 4, x % 4]:
                    c = 'dirt1' if y < 5 else ('dirt0' if y == 5 else ('moss0' if y == 6 else 'moss1'))
                    if y == 7 and x % 3 == 1:
                        c = 'moss2'
                    if y == 4 and x % 4 == 2:
                        c = 'root0'
                    cv.px(x, y, c)
        roots = [[(2, 5), (9, 3)], [(5, 7), (12, 4)], [(3, 3), (10, 6), (14, 2)], [(7, 6)]][v]
        for (x, ln) in roots:
            xx = x
            for k in range(ln):
                cv.px(xx, 8 + k, 'root1' if k % 3 else 'root2')
                if k % 3 == 2:
                    xx = min(max(xx + int(r.integers(-1, 2)), 0), 15)
            cv.px(xx, 8 + ln, 'root0')
        moss = [[(6, 4), (13, 2)], [(1, 3), (9, 5)], [(7, 3)], [(2, 4), (11, 5), (13, 2)]][v]
        for (x, ln) in moss:
            for k in range(ln):
                cv.px(x, 8 + k, 'moss2' if k % 2 else 'moss1')
            cv.px(x + 1, 8, 'moss1')
        dx, dy = [(6, 13), (9, 14), (7, 12), (11, 14)][v]
        for k in range(8, dy):
            if cv.get(dx, k)[3] == 0:
                cv.px(dx, k, C('glow0', 200))
        for (ox, oy) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if cv.get(dx + ox, dy + oy)[3] == 0:
                cv.px(dx + ox, dy + oy, C('glow1', 90))
        cv.px(dx, dy, 'glow2')
        cv.px(dx, dy - 1, 'glow1')
        tiles.append(cv)
    return tiles


def special_tiles(rng):
    out = []
    cv = Canvas(T, T)   # OPEN
    for i in range(T):
        for (x, y) in [(i, 0), (i, 15), (0, i), (15, i)]:
            if i % 2 == 0:
                cv.px(x, y, C('gold1', 150))
    for (x, y) in [(0, 0), (15, 0), (0, 15), (15, 15)]:
        cv.a[y, x] = C('gold2', 190)
    out.append(cv)
    for f in range(3):  # WATER SURFACE
        cv = Canvas(T, T)
        for x in range(T):
            ph = 2 * math.pi * (x / 16.0) + f * 2 * math.pi / 3
            wy = int(round(1.4 + 1.1 * math.sin(ph) + 0.4 * math.sin(2 * ph + 1)))
            for y in range(wy, T):
                if y == wy:
                    c = C('foam', 235)
                elif y == wy + 1:
                    c = C('water_hi', 210)
                elif y < 4:
                    c = C('water_hi', 175) if (x + y + f) % 3 == 0 else C('water1', 160)
                else:
                    c = mix('water1', 'water0', (y - 4) / 11.0, 150)
                    if (x * 3 + y * 5 + f * 4) % 17 == 0 and y < 10:
                        c = C('water_hi', 150)
                cv.a[y, x] = c
        out.append(cv)
    cv = Canvas(T, T)  # WATER BODY
    for y in range(T):
        for x in range(T):
            s = math.sin(2 * math.pi * x / 16 + math.sin(2 * math.pi * y / 16) * 1.6) + \
                math.sin(2 * math.pi * y / 8 + math.sin(2 * math.pi * x / 16) * 1.3)
            c = C('water0', 140)
            if s > 1.35:
                c = C('water1', 150)
            elif s < -1.2:
                c = C('water_deep', 140)
            cv.a[y, x] = c
    out.append(cv)
    cv = Canvas(T, T)  # SPRING
    for y in range(T):
        for x in range(T):
            d = math.hypot(x - 7.5, y - 7.5)
            s = math.sin(d * 1.3) + 0.5 * math.sin(2 * math.pi * (x + y) / 16)
            cv.px(x, y, dpick(['spring0', 'spring1', 'spring2'], 0.45 + 0.25 * s, x, y))
    for (x, y) in [(3, 4), (12, 11)]:
        cv.px(x, y, 'spring3'); cv.px(x + 1, y, 'spring2'); cv.px(x, y + 1, 'spring2')
    out.append(cv)
    return out


def cave_tiles(rng):
    b = rock_base(rng, 6, 5.0)
    tiles = []
    for v in range(4):
        arr, crack = render_chunks(b, b['tone'] * .6, ['cave1', 'cave2', 'cave3'], 'cave0',
                                   base=0.42, hl=0.28, noise=0.12)
        cv = Canvas(T, T)
        cv.a[:] = arr
        if v == 1:
            x = 4
            for y in range(1, 15):
                cv.px(x, y, 'cave0')
                if y % 4 == 0:
                    x += 1
                if y == 6:
                    cv.px(x + 1, y + 1, 'cave0'); cv.px(x + 2, y + 2, 'cave0'); cv.px(x + 3, y + 2, 'cave0')
        if v == 2:  # three-toed dinosaur track (Connecticut Valley ichnite)
            for (x, y) in [(8, 10), (8, 9), (8, 8), (8, 7), (8, 6), (7, 9), (6, 8), (5, 7), (5, 6),
                           (9, 9), (10, 8), (11, 7), (11, 6), (7, 11), (8, 11), (9, 11)]:
                cv.px(x, y, 'cave4')
            cv.px(8, 12, 'cave0'); cv.px(9, 12, 'cave0')
        if v == 3:
            for (x, y) in [(7, 6), (8, 6), (9, 6), (10, 7), (10, 8), (9, 9), (8, 9), (7, 8), (7, 7), (8, 7), (9, 8)]:
                cv.px(x, y, 'cave4' if (x + y) % 2 else 'cave3')
        tiles.append(cv)
    return tiles


def build_tiles():
    rng = np.random.default_rng(SEED)
    sheet = Canvas(128, 224)
    rb = rock_base(rng)
    rows = [rock_tiles(rng, base=rb), dirt_tiles(rng), timber_tiles(rng), granite_tiles(rng),
            rock_tiles(rng, false_tell=True, base=rb), concrete_tiles(rng), cliff_tiles(rng),
            board_tiles(rng), grass_tiles(rng), ceiling_tiles(rng), special_tiles(rng), cave_tiles(rng)]
    rows += [trestle_deck_tiles(), living_root_tiles()]       # expansion 2 (own seeds)
    for ri, row in enumerate(rows):
        for ci, t in enumerate(row):
            sheet.a[ri * T:(ri + 1) * T, ci * T:(ci + 1) * T] = t.a
    sheet.save('tiles.png')
    build_tiles.last = sheet
    return sheet


# ============================================================================
# PEOPLE  (128x240: 8 cols x 10 rows of 16x24, facing right)
# ============================================================================
ROLES = {
    'woodcutter': dict(torso='plaid', sleeve=('plaid_k', 'plaid_r', 'plaid_rl'), pants=('jean0', 'jean1', 'jean2'),
                       hair='hairR', hat='knit', hatc=('knit0', 'knit1', 'knit2'), tool='axe', beard=True),
    'digger': dict(torso='overalls', sleeve=('shirtw0', 'shirtw1', 'shirtw2'), pants=('over0', 'over1', 'over2'),
                   hair='hair0', hat='flat', hatc=('cap0', 'cap1', 'cap2'), tool='shovel', beard=False, stubble=True),
    'surveyor': dict(torso='solid', shirt=('khaki0', 'khaki1', 'khaki2'), sleeve=('khaki0', 'khaki1', 'khaki2'),
                     pants=('khaki0', 'khaki1', 'khaki1'), hair='hair1', hat='brim', hatc=('khaki0', 'khaki1', 'khaki2'),
                     tool='rod', belt=True),
    'engineer': dict(torso='tie', shirt=('blue0', 'blue1', 'blue2'), sleeve=('blue0', 'blue1', 'blue2'),
                     pants=('grey0', 'grey1', 'grey2'), hair='hair0', hat='fedora', hatc=('fed0', 'fed1', 'fed2'),
                     tool='plans', belt=True),
    'warden': dict(torso='badge', shirt=('green0', 'green1', 'green2'), sleeve=('green0', 'green1', 'green2'),
                   pants=('green0', 'green0', 'green1'), hair='hair1', hat='campaign', hatc=('camp0', 'camp1', 'camp2'),
                   tool='rifle', belt=True),
    'resident': dict(torso='dress', shirt=('dress0', 'dress1', 'dress2'), sleeve=('dress0', 'dress1', 'dress2'),
                     pants=('stock0', 'stock1', 'stock1'), hair='hairR', hat='bonnet',
                     hatc=('camp0', 'camp1', 'camp2'), tool=None, dress=True),
}
ROLE_ORDER = ['woodcutter', 'digger', 'surveyor', 'engineer', 'warden', 'resident']

# legs: ((knee),(ankle)) back, front ; arms: ((elbow),(hand)) back, front  (arm coords at bob=0)
WALK = [
    dict(bob=0, legs=[((5, 18), (4, 21)), ((10, 18), (11, 21))], arms=[((9, 12), (11, 14)), ((7, 12), (5, 14))]),
    dict(bob=-1, legs=[((8, 17), (7, 20)), ((8, 18), (8, 21))], arms=[((8, 13), (8, 15)), ((8, 13), (9, 15))]),
    dict(bob=0, legs=[((9, 18), (10, 21)), ((6, 18), (5, 21))], arms=[((7, 12), (5, 14)), ((9, 12), (11, 14))]),
    dict(bob=-1, legs=[((7, 18), (6, 21)), ((10, 17), (9, 20))], arms=[((8, 13), (8, 15)), ((8, 13), (9, 15))]),
]
IDLE = dict(bob=0, legs=[((6, 18), (6, 21)), ((8, 18), (8, 21))], arms=[((7, 12), (7, 14)), ((8, 12), (9, 14))])
STARTLED = dict(bob=-1, legs=[((6, 18), (5, 21)), ((9, 18), (10, 21))], arms=[((5, 8), (4, 5)), ((11, 8), (12, 5))],
                eyes='wide', mouth='open', notool=True, hdx=-1)
GRABBED = dict(bob=-2, legs=[((5, 18), (3, 20)), ((10, 18), (12, 20))], arms=[((4, 10), (2, 7)), ((12, 9), (14, 6))],
               eyes='wide', mouth='open', notool=True, rot=22)
COWER = dict(bob=3, legs=[((9, 19), (6, 21)), ((11, 19), (9, 21))], arms=[((10, 9), (10, 6)), ((11, 9), (12, 6))],
             eyes='shut', mouth='open', notool=True, hdx=1, hdy=1)

CARRY = {
    'woodcutter': dict(fa=((9, 12), (10, 14)), tool=('axe', (10, 14), (12, 20))),
    'digger': dict(fa=((10, 12), (12, 13)), tool=('shovel', (13, 5), (13, 19))),
    'surveyor': dict(fa=((10, 12), (12, 12)), tool=('rod', 12, 0, 22)),
    'engineer': dict(fa=((8, 12), (9, 14)), tool=('plans', 3, 12)),
    'warden': dict(fa=((9, 12), (10, 13)), tool=('rifle', (6, 18), (13, 5))),
    'resident': None,
}
WIDE = [((5, 18), (4, 21)), ((10, 18), (11, 21))]
ATTACK = {
    'woodcutter': dict(bob=0, legs=WIDE, arms=[((6, 8), (6, 5)), ((7, 8), (7, 5))], tool=('axe', (7, 5), (12, 1)),
                       mouth='open'),
    'digger': dict(bob=0, legs=WIDE, arms=[((6, 8), (5, 5)), ((7, 8), (6, 4))], tool=('shovel_up', (3, 8), (11, 1)),
                   mouth='open'),
    'surveyor': COWER,
    'engineer': dict(bob=0, legs=WIDE, arms=[((10, 12), (12, 11)), ((6, 8), (5, 5))], tool=('dynamite', 5, 5)),
    'warden': dict(bob=0, legs=WIDE, arms=[((7, 12), (9, 11)), ((10, 12), (12, 11))], tool=('rifle_aim', 5, 11),
                   hdx=1),
    'resident': COWER,
}


def p_leg(cv, hip, knee, ankle, R, back):
    d, m, l = R['pants']
    c1, c2 = (d, d) if back else (l, m)
    for a, b in ((hip, knee), (knee, ankle)):
        for (x, y) in bres(*a, *b):
            cv.px(x, y, c1)
            cv.px(x + 1, y, c2)
    ax, ay = ankle
    bc = ('boot0', 'boot0', 'boot1') if back else ('boot1', 'boot2', 'boot1')
    if R.get('dress'):
        bc = ('boot0', 'boot0', 'boot0') if back else ('boot0', 'boot1', 'boot0')
    cv.px(ax, ay + 1, bc[1]); cv.px(ax + 1, ay + 1, bc[0])
    cv.px(ax, ay + 2, bc[2]); cv.px(ax + 1, ay + 2, bc[0]); cv.px(ax + 2, ay + 2, bc[2])


def p_arm(cv, sh, el, hd, R, back):
    d, m, l = R['sleeve']
    pts = bres(*sh, *el) + bres(*el, *hd)[1:]
    vert_last = abs(hd[1] - el[1]) >= abs(hd[0] - el[0])
    for i, (x, y) in enumerate(pts[:-1]):
        if R['torso'] == 'plaid':
            c1 = 'plaid_k' if (i // 2) % 2 else ('plaid_kr' if back else 'plaid_r')
            c2 = 'plaid_k' if (i // 2) % 2 else ('plaid_kr' if back else 'plaid_rl')
        else:
            c1, c2 = (d, d) if back else (d, l)
        seg_vert = vert_last if i >= len(bres(*sh, *el)) - 1 else abs(el[1] - sh[1]) >= abs(el[0] - sh[0])
        if seg_vert:
            cv.px(x, y, c1); cv.px(x + 1, y, c2)
        else:
            cv.px(x, y, c2); cv.px(x, y + 1, c1)
    hx, hy = hd
    cv.px(hx, hy, 'skin1' if not back else 'skin0')
    cv.px(hx + 1, hy, 'skin1' if not back else 'skin0')


def p_torso(cv, x0, y0, R):
    kind = R['torso']
    sd, sm, sl = R.get('shirt', R['sleeve'])
    for yr in range(7):
        for xr in range(5):
            x, y = x0 + xr, y0 + yr
            if kind == 'plaid':
                blk = ((xr + 1) // 2 + yr // 2) % 2
                c = 'plaid_k' if blk else 'plaid_r'
                if blk and (yr // 2) % 2 == 0:
                    c = 'plaid_kr'
                if xr == 0:
                    c = 'plaid_k' if blk else 'plaid_kr'
                if xr == 3 and yr == 1 and not blk:
                    c = 'plaid_rl'
            elif kind == 'overalls':
                c = 'over1'
                if yr <= 1:
                    c = 'shirtw1' if xr not in (1, 3) else 'over0'
                    if xr == 0:
                        c = 'shirtw0'
                    if xr == 4 and yr == 0:
                        c = 'skin1'
                elif xr == 0:
                    c = 'shirtw0' if yr < 4 else 'over0'
                elif xr == 2 and yr == 2:
                    c = 'over2'
                elif yr == 6:
                    c = 'over0'
            else:
                c = sm
                if xr == 0:
                    c = sd
                if xr in (1, 2) and yr in (1, 2):
                    c = sl
                if yr == 0 and xr >= 3:
                    c = sl
                if kind == 'tie' and xr == 4 and 1 <= yr <= 5:
                    c = 'tie' if yr > 1 else 'tie_dk'
                if kind == 'badge' and xr == 3 and yr == 2:
                    c = 'gold2'
                if kind == 'badge' and xr == 2 and yr == 2:
                    c = sd
                if kind == 'dress':
                    if yr == 0 and xr >= 1:
                        c = 'bonnet2'
                    elif (xr + yr) % 3 == 0 and yr % 2 == 0 and xr > 0:
                        c = 'dress2'
                if R.get('belt') and yr == 6:
                    c = 'boot1' if xr != 3 else 'gold1'
            cv.px(x, y, c)


def p_skirt(cv, x0, hipy, R, sway=0):
    rows = [(0, 4), (-1, 4), (-1, 5), (-1, 5), (-2, 5)]
    for k, (a, b) in enumerate(rows):
        y = hipy + k
        s = sway if k >= 3 else 0
        for xr in range(a + s, b + 1 + s):
            c = 'dress1'
            if xr <= a + s:
                c = 'dress0'
            if k == 4:
                c = 'dress0' if (xr % 2) else 'dress1'
            if (xr + k) % 3 == 0 and k in (1, 3) and xr > a + s:
                c = 'dress2'
            cv.px(x0 + xr, y, c)


def p_head(cv, x0, y0, R, P):
    for y in range(5):
        for x in range(5):
            cv.px(x0 + x, y0 + y, 'skin1')
    cv.px(x0 + 1, y0 + 1, 'skin2'); cv.px(x0 + 2, y0 + 1, 'skin2'); cv.px(x0 + 3, y0 + 1, 'skin2')
    hair = R['hair']
    for x in range(5):
        cv.px(x0 + x, y0, hair)
    for y in range(4):
        cv.px(x0, y0 + y, hair)
    cv.px(x0 + 1, y0 + 2, 'skin0')            # ear
    cv.px(x0 + 1, y0 + 4, 'skin0'); cv.px(x0 + 2, y0 + 4, 'skin0')
    cv.px(x0 + 5, y0 + 2, 'skin1')            # nose
    cv.px(x0 + 5, y0 + 3, 'skin0')
    eyes = P.get('eyes', 'normal')
    if eyes == 'wide':
        cv.px(x0 + 3, y0 + 2, 'eye_w'); cv.px(x0 + 4, y0 + 2, 'ink'); cv.px(x0 + 3, y0 + 1, hair)
    elif eyes == 'shut':
        cv.px(x0 + 3, y0 + 2, 'skin0'); cv.px(x0 + 4, y0 + 2, 'skin0')
    else:
        cv.px(x0 + 3, y0 + 2, 'ink')
    if R.get('beard'):
        for x in range(1, 5):
            cv.px(x0 + x, y0 + 4, hair)
        cv.px(x0 + 3, y0 + 3, hair); cv.px(x0 + 2, y0 + 3, hair)
        cv.px(x0 + 5, y0 + 4, hair)
    if R.get('stubble'):
        cv.px(x0 + 3, y0 + 4, 'skin0'); cv.px(x0 + 4, y0 + 4, 'skin0')
    if P.get('mouth') == 'open':
        cv.px(x0 + 4, y0 + 3, 'mouth'); cv.px(x0 + 4, y0 + 4, 'mouth')
    else:
        cv.px(x0 + 4, y0 + 3, 'skin0')
    # hats
    d, m, l = R['hatc']
    h = R['hat']
    if h == 'knit':
        for x in range(5):
            cv.px(x0 + x, y0, d)
            cv.px(x0 + x, y0 - 1, m)
        for x in range(1, 4):
            cv.px(x0 + x, y0 - 2, m)
        cv.px(x0 + 1, y0 - 1, 'plaid_r'); cv.px(x0 + 2, y0 - 1, 'plaid_r')
        cv.px(x0 + 1, y0 - 3, l); cv.px(x0 + 2, y0 - 3, l)
    elif h == 'flat':
        for x in range(5):
            cv.px(x0 + x, y0 - 1, m)
            cv.px(x0 + x, y0, d if x == 0 else m)
        cv.px(x0 + 1, y0 - 1, l); cv.px(x0 + 2, y0 - 1, l)
        cv.px(x0 + 5, y0, d); cv.px(x0 + 6, y0, d)
    elif h == 'brim':
        for x in range(1, 5):
            cv.px(x0 + x, y0 - 2, m)
            cv.px(x0 + x, y0 - 1, d if x > 1 else m)
        cv.px(x0 + 2, y0 - 2, l)
        for x in range(-1, 7):
            cv.px(x0 + x, y0, m if 0 < x < 6 else d)
    elif h == 'fedora':
        cv.px(x0 + 1, y0 - 2, m); cv.px(x0 + 3, y0 - 2, m); cv.px(x0 + 4, y0 - 2, d)
        cv.px(x0 + 2, y0 - 2, d)
        for x in range(1, 5):
            cv.px(x0 + x, y0 - 1, 'ink2' if x > 1 else d)
        for x in range(-1, 7):
            cv.px(x0 + x, y0, m)
        cv.px(x0 + 1, y0 - 2, l)
        cv.px(x0 + 6, y0 + 1, d)
    elif h == 'campaign':
        cv.px(x0 + 2, y0 - 3, m)
        cv.px(x0 + 1, y0 - 2, l); cv.px(x0 + 2, y0 - 2, m); cv.px(x0 + 3, y0 - 2, d)
        for x in range(1, 4):
            cv.px(x0 + x, y0 - 1, 'boot1')
        for x in range(-2, 7):
            cv.px(x0 + x, y0, l if x < 2 else m)
    elif h == 'bonnet':
        for x in range(0, 5):
            cv.px(x0 + x, y0 - 1, m)
        for x in range(-1, 6):
            cv.px(x0 + x, y0, l if x < 4 else m)
        for y in range(0, 4):
            cv.px(x0 - 1, y0 + y, d)
            cv.px(x0, y0 + y, m)
        cv.px(x0 + 5, y0 + 1, d)
        cv.px(x0 + 2, y0 + 5, 'ribbon'); cv.px(x0 + 1, y0 + 5, 'ribbon')
        for x in range(0, 4):
            cv.px(x0 + x, y0 - 1, 'ribbon')
        cv.px(x0 + 1, y0 - 2, l); cv.px(x0 + 2, y0 - 2, m); cv.px(x0 + 3, y0 - 2, m)
        cv.px(x0 + 6, y0, d)
        cv.px(x0 + 6, y0 + 1, d)


def axe_head(cv, x, y):
    for (dx, dy, c) in [(-1, 0, 'steel0'), (0, -1, 'steel1'), (0, 0, 'steel1'), (0, 1, 'steel0'),
                        (1, -1, 'steel1'), (1, 0, 'steel1'), (1, 1, 'steel1'), (2, -2, 'steel2'), (2, -1, 'steel3'),
                        (2, 0, 'steel3'), (2, 1, 'steel2'), (2, 2, 'steel2')]:
        cv.px(x + dx, y + dy, c)


def p_tool(cv, tool, R, bob, stage):
    kind = tool[0]
    if kind == 'axe' and stage == 'front':
        _, a, b = tool
        a, b = (a[0], a[1] + bob), (b[0], b[1] + bob)
        for i, (x, y) in enumerate(bres(*a, *b)):
            cv.px(x, y, 'wood4' if i % 3 else 'wood3')
        axe_head(cv, *b)
    elif kind == 'shovel' and stage == 'back':
        _, a, b = tool
        for (x, y) in bres(a[0], a[1] + bob, b[0], b[1]):
            cv.px(x, y, 'wood4')
        cv.px(a[0] - 1, a[1] + bob - 1, 'wood3'); cv.px(a[0], a[1] + bob - 1, 'wood3'); cv.px(a[0] + 1, a[1] + bob - 1, 'wood3')
        bx, by = b
        for yy in range(by + 1, 24):
            cv.px(bx - 1, yy, 'steel1'); cv.px(bx, yy, 'steel2'); cv.px(bx + 1, yy, 'steel0')
        cv.px(bx, 23, 'steel1')
    elif kind == 'shovel_up' and stage == 'front':
        _, a, b = tool
        for (x, y) in bres(a[0], a[1] + bob, b[0], b[1] + bob):
            cv.px(x, y, 'wood4')
        bx, by = b[0], b[1] + bob
        for (dx, dy) in [(0, 0), (1, 0), (2, 0), (1, -1), (2, -1), (3, -1), (2, -2), (3, -2), (1, 1), (2, 1)]:
            cv.px(bx + dx, by + dy, 'steel2' if dy < 0 else 'steel1')
        cv.px(bx + 3, by - 2, 'steel3')
    elif kind == 'rod' and stage == 'back':
        _, x, y0, y1 = tool
        for y in range(y0, y1 + 1):
            cv.px(x, y, 'rod_r' if (y // 2) % 2 else 'rod_w')
        cv.px(x, y1 + 1, 'steel1')
    elif kind == 'plans' and stage == 'mid':
        _, x0, y = tool
        y += bob
        for x in range(x0, x0 + 7):
            cv.px(x, y, 'bonnet2'); cv.px(x, y + 1, 'bonnet1')
        cv.px(x0, y, 'plan1'); cv.px(x0, y + 1, 'plan0')
        cv.px(x0 + 1, y, 'plan2')
        cv.px(x0 + 4, y + 1, 'plan1')
    elif kind == 'rifle' and stage == 'front':
        _, a, b = tool
        a, b = (a[0], a[1] + bob), (b[0], b[1] + bob)
        pts = bres(*a, *b)
        for i, (x, y) in enumerate(pts):
            if i < len(pts) * 0.4:
                cv.px(x, y, 'wood3'); cv.px(x - 1, y, 'wood2')
            else:
                cv.px(x, y, 'steel0' if i % 2 else 'steel1')
    elif kind == 'rifle_aim' and stage == 'front':
        _, x0, y = tool
        y += bob
        for x in range(x0, x0 + 4):
            cv.px(x, y, 'wood3'); cv.px(x, y + 1, 'wood2' if x < x0 + 2 else None) if x < x0 + 2 else None
        for x in range(x0 + 4, 16):
            cv.px(x, y, 'steel1' if x % 2 else 'steel0')
        cv.px(x0 + 6, y + 1, 'wood3'); cv.px(x0 + 7, y + 1, 'wood3'); cv.px(x0 + 8, y + 1, 'wood2')
        cv.px(15, y - 1, 'steel1')
        cv.px(x0 + 5, y + 1, 'steel0')
    elif kind == 'dynamite' and stage == 'front':
        _, hx, hy = tool
        hy += bob
        for k in range(3):
            cv.px(hx, hy - 1 - k, 'dyn' if k != 1 else 'dyn_dk')
            cv.px(hx + 1, hy - 1 - k, 'dyn')
        cv.px(hx + 1, hy - 4, 'ink2')
        cv.px(hx + 2, hy - 5, 'spark1')
        for (dx, dy) in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
            cv.px(hx + 2 + dx, hy - 5 + dy, 'spark0')


def draw_person(role, P):
    R = ROLES[role]
    cv = Canvas(16, 24)
    b = P.get('bob', 0)
    top = 9 + b
    hipy = 16 + b
    (bk, ba), (fk, fa) = P['legs']
    (be, bh), (fe, fh) = P['arms']
    tool = None
    if not P.get('notool'):
        if 'tool' in P:
            tool = P['tool']
        elif CARRY.get(role):
            tool = CARRY[role]['tool']
            fe, fh = CARRY[role]['fa']

    def up(p):
        return (p[0], p[1] + b)
    hdx, hdy = P.get('hdx', 0), P.get('hdy', 0)
    if tool:
        p_tool(cv, tool, R, b, 'back')
    p_arm(cv, up((7, 10)), up(be), up(bh), R, back=True)
    p_leg(cv, (6, hipy), bk, ba, R, back=True)
    p_torso(cv, 6, top, R)
    p_leg(cv, (8, hipy), fk, fa, R, back=False)
    if R.get('dress'):
        sway = 1 if fa[0] > 9 else (-1 if fa[0] < 7 else 0)
        p_skirt(cv, 6, hipy, R, sway)
    p_head(cv, 6 + hdx, 4 + b + hdy, R, P)
    if tool:
        p_tool(cv, tool, R, b, 'mid')
    p_arm(cv, up((8, 10)), up(fe), up(fh), R, back=False)
    if tool:
        p_tool(cv, tool, R, b, 'front')
        if tool[0] in ('axe', 'rifle', 'shovel', 'rod'):
            hx, hy = up(fh)
            cv.px(hx, hy, 'skin1')
    if P.get('rot'):
        im = cv.image().rotate(P['rot'], resample=Image.NEAREST, center=(8, 14))
        cv.a[:] = np.array(im)
    outline(cv, 'ink')
    return cv


def build_people():
    sheet = Canvas(128, 240)
    for ri, role in enumerate(ROLE_ORDER):
        poses = WALK + [IDLE, STARTLED, GRABBED, ATTACK[role]]
        for ci, P in enumerate(poses):
            sheet.blit(draw_person(role, P), ci * 16, ri * 24)
    for ri, boss in ((6, False), (7, True)):      # burner, foreman
        for ci in range(8):
            sheet.blit(draw_burner(ci, boss), ci * 16, ri * 24)
    for ci in range(8):                            # diver, houndmaster
        sheet.blit(draw_diver(ci), ci * 16, 8 * 24)
        sheet.blit(draw_houndmaster(ci), ci * 16, 9 * 24)
    sheet.save('people.png')
    return sheet


# ============================================================================
# ANIMALS  (72x48: 3 cols x 3 rows of 24x16)
# ============================================================================
def shaded_ellipse(cv, cx, cy, rx, ry, ramp, light=(-0.5, -0.85), base=0.55, k=0.45):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            nx, ny = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            d = nx * nx + ny * ny
            if d <= 1:
                t = base + k * -(nx * light[0] + ny * light[1])
                cv.px(x, y, dpick(ramp, t, x, y))


def deer(frame):
    cv = Canvas(24, 16)
    ramp = ['deer0', 'deer1', 'deer2', 'deer3']
    alert = frame == 2
    # long thin legs: (hip, knee/hock, hoof); far legs darker
    if frame == 0:
        legs = [((7, 9), (6, 12), (5, 15), 'deer0'), ((15, 9), (16, 12), (17, 15), 'deer0'),
                ((8, 9), (9, 12), (8, 15), 'deer1'), ((16, 9), (15, 12), (14, 15), 'deer1')]
    elif frame == 1:
        legs = [((7, 9), (8, 12), (8, 15), 'deer0'), ((15, 9), (15, 12), (14, 15), 'deer0'),
                ((8, 9), (6, 12), (6, 15), 'deer1'), ((16, 9), (17, 12), (17, 15), 'deer1')]
    else:
        legs = [((7, 9), (6, 12), (6, 15), 'deer0'), ((15, 9), (15, 12), (15, 15), 'deer0'),
                ((8, 9), (8, 12), (8, 15), 'deer1'), ((16, 9), (16, 12), (17, 15), 'deer1')]
    for (a, k, b, c) in legs:
        cv.line(*a, *k, c)
        cv.line(*k, *b, c)
        cv.px(b[0], b[1], 'ink2')
    shaded_ellipse(cv, 11.5, 6.8, 6.5, 2.9, ramp)
    for x in range(7, 16):  # pale belly
        cv.px(x, 9, 'deer_w' if x % 3 else 'deer3')
    cv.px(6, 5, 'deer1'); cv.px(7, 4, 'deer2')  # rump
    # neck + head
    if alert:
        neck = [(16, 5), (17, 4), (17, 3), (18, 2), (18, 1)]
        hx, hy = 18, 0
    else:
        neck = [(16, 5), (17, 4), (18, 3), (19, 3)]
        hx, hy = 19, 2
    for (x, y) in neck:
        cv.px(x, y, 'deer2'); cv.px(x, y + 1, 'deer2'); cv.px(x - 1, y + 1, 'deer1')
    cv.px(neck[-1][0], neck[-1][1] + 2, 'deer_w')  # throat patch
    for (dx, dy, c) in [(0, 0, 'deer2'), (1, 0, 'deer3'), (2, 0, 'deer2'), (0, 1, 'deer2'), (1, 1, 'deer2'),
                        (2, 1, 'deer2'), (3, 1, 'deer2'), (4, 1, 'ink2'), (3, 2, 'deer_w'), (2, 2, 'deer1'),
                        (1, 2, 'deer1')]:
        cv.px(hx + dx, hy + dy, c)
    cv.px(hx + 2, hy, 'ink')  # eye
    if alert:   # ears pricked up tall
        cv.px(hx - 1, hy - 1, 'deer2'); cv.px(hx - 2, hy - 2 + 2, 'deer1'); cv.px(hx, hy - 1, 'deer3')
    else:
        cv.px(hx - 1, hy - 1, 'deer2'); cv.px(hx - 2, hy - 1, 'deer1'); cv.px(hx, hy - 1, 'deer1')
    # tail
    if alert:   # white flag raised
        for (x, y) in [(5, 4), (4, 3), (4, 2), (3, 1), (4, 1), (3, 2), (5, 3)]:
            cv.px(x, y, 'deer_w')
        cv.px(5, 5, 'deer2')
    else:
        cv.px(5, 5, 'deer1'); cv.px(4, 6, 'deer1'); cv.px(4, 7, 'deer_w')
    outline(cv, None)
    return cv


def sheep(frame):
    cv = Canvas(24, 16)
    jump = -1 if frame == 2 else 0
    if frame == 0:
        legs = [(6, 5), (9, 10), (14, 13), (17, 18)]
    elif frame == 1:
        legs = [(6, 7), (9, 8), (14, 15), (17, 16)]
    else:
        legs = [(6, 4), (9, 8), (14, 15), (17, 19)]
    for i, (x0, x1) in enumerate(legs):
        cv.line(x0, 12 + jump, x1, 15 + jump if frame == 2 else 15, 'sheep_face' if i % 2 else 'ink2')
    ramp = ['wool0', 'wool1', 'wool2', 'wool3']
    for (cx, cy, r) in [(7, 8, 3.6), (11, 6.5, 3.8), (15, 7, 3.6), (10, 10, 3.4), (15, 10, 3.2), (5.5, 10, 2.8)]:
        shaded_ellipse(cv, cx, cy + jump, r, r * .9, ramp, base=.6, k=.35)
    for (x, y) in [(8, 5), (12, 4), (16, 5), (10, 8), (14, 8), (6, 8)]:  # curl highlights
        cv.px(x, y + jump, 'wool3')
        cv.px(x + 1, y + 1 + jump, 'wool1')
    hy = 4 if frame == 2 else 6
    hy += jump
    for (dx, dy, c) in [(0, 0, 'sheep_face'), (1, 0, 'sheep_face'), (2, 0, 'sheep_face'), (0, 1, 'sheep_face'),
                        (1, 1, 'sheep_face'), (2, 1, 'sheep_face'), (3, 1, 'sheep_face'), (1, 2, 'sheep_face'),
                        (2, 2, 'sheep_face'), (3, 2, 'ink2'), (-1, 0, 'ink2'), (-1, 1, 'wool1')]:
        cv.px(18 + dx, hy + dy, c)
    cv.px(19, hy, 'eye_w' if frame == 2 else 'wool0')
    cv.px(18, hy - 1, 'wool2'); cv.px(19, hy - 1, 'wool3')
    cv.px(17, hy + 1, 'sheep_face')  # ear
    cv.px(16, hy + 1 + (-(1) if frame == 2 else 1), 'sheep_face')
    outline(cv, None)
    return cv


def build_animals():
    sheet = Canvas(72, 48)
    for f in range(3):
        sheet.blit(deer(f), f * 24, 0)
        sheet.blit(sheep(f), f * 24, 16)
        sheet.blit(hound(f), f * 24, 32)
    sheet.save('animals.png')
    return sheet


# ============================================================================
# PROPS  (256x128: 8x4 cells of 32x32, bottom-aligned, centred)
# ============================================================================
SLATE = ['slate0', 'slate1', 'slate2', 'slate3', 'slate4']


def headstone(w=14, h=20, moss=True, seed=0):
    cv = Canvas(w, h)
    cx = w / 2
    top = 0
    for y in range(h):
        for x in range(w):
            X, Y = x + .5, y + .5
            ins = Y >= 6 and 0 <= X <= w
            ins = ins or math.hypot(X - cx, Y - 6) <= 5.6
            ins = ins or math.hypot(X - 2.2, Y - 6.2) <= 2.2 or math.hypot(X - (w - 2.2), Y - 6.2) <= 2.2
            if ins:
                t = 0.55 - 0.3 * (x / (w - 1) - .5) + (0.12 if y < 3 else 0)
                cv.px(x, y, dpick(SLATE[1:], t, x, y))
    # bevel edge
    for y in range(h):
        for x in range(w):
            if cv.solid(x, y):
                if not cv.solid(x - 1, y) or not cv.solid(x, y - 1):
                    cv.px(x, y, 'slate4')
                elif not cv.solid(x + 1, y):
                    cv.px(x, y, 'slate1')
    # urn
    ux = int(cx) - 1
    for (dx, dy, c) in [(0, 4, 'slate1'), (1, 4, 'slate1'), (-1, 5, 'slate1'), (0, 5, 'slate4'), (1, 5, 'slate3'),
                        (2, 5, 'slate1'), (-1, 6, 'slate1'), (0, 6, 'slate3'), (1, 6, 'slate3'), (2, 6, 'slate1'),
                        (0, 7, 'slate1'), (1, 7, 'slate1'), (-1, 8, 'slate1'), (0, 8, 'slate1'), (1, 8, 'slate1'), (2, 8, 'slate1'),
                        (0, 3, 'slate1'), (1, 3, 'slate1')]:
        cv.px(ux + dx, top + dy, c)
    # willow: trunk on left of urn, drooping fronds both sides
    cv.px(ux - 3, top + 8, 'slate1'); cv.px(ux - 3, top + 7, 'slate1'); cv.px(ux - 3, top + 6, 'slate1')
    for (x, y) in [(-3, 3), (-2, 2), (-1, 2), (0, 1), (1, 1), (2, 2), (3, 3), (4, 4), (-4, 4), (-5, 5), (4, 6), (-5, 7), (5, 5)]:
        cv.px(ux + x, top + y, 'slate1' if (x + y) % 2 else 'slate0')
    # inscription
    for (y, x0, x1) in [(11, 3, 10), (13, 2, 11), (15, 4, 9), (17, 3, 10)]:
        for x in range(x0, x1 + 1):
            if (x * 7 + y) % 5 != 0:
                cv.px(x, y, 'slate1' if (x + y) % 2 else 'slate0')
    if moss:
        for (x, y, c) in [(0, h - 1, 'moss1'), (1, h - 1, 'moss2'), (0, h - 2, 'moss1'), (w - 1, h - 1, 'moss1'),
                          (w - 2, h - 1, 'moss0'), (2, h - 1, 'moss1'), (w - 1, h - 2, 'moss2'),
                          (4, 1, 'lichen'), (5, 1, 'lichen'), (5, 0, 'lichen'), (1, 5, 'moss2')]:
            cv.px(x, y, c)
    outline(cv, None)
    return cv


def prop_cell():
    return Canvas(32, 32)


def ground_tuft(cv, x, y, n=3):
    for i in range(n):
        cv.px(x + i, y, 'grass2' if i % 2 else 'grass3')
        if i % 2 == 0:
            cv.px(x + i, y - 1, 'grass3')


def p_headstone():
    cv = prop_cell()
    hs = headstone()
    cv.blit(hs, 9, 32 - hs.h)
    ground_tuft(cv, 7, 31, 3); ground_tuft(cv, 22, 31, 3)
    return cv


def p_open_grave():
    cv = prop_cell()
    # ground strip with pit
    for x in range(1, 31):
        for y in range(26, 32):
            cv.px(x, y, 'dirt1' if (x + y) % 3 else 'dirt2')
        cv.px(x, 26, 'grass2' if x % 2 else 'grass3')
    for x in range(8, 22):
        for y in range(27, 32):
            cv.px(x, y, 'cave0' if y > 27 else 'dirt0')
    cv.px(8, 27, 'dirt2'); cv.px(21, 27, 'dirt2')
    # dirt pile
    for x in range(18, 32):
        hgt = int(9 * math.sin(math.pi * (x - 17.5) / 14.5))
        for y in range(27 - hgt, 31):
            t = 0.65 - (y - (27 - hgt)) * 0.06 - (x - 18) * 0.015
            cv.px(x, y, dpick(['dirt1', 'dirt2', 'dirt3', 'dirt4'], t, x, y))
    pebble(cv, 24, 22, False, 'dirt1'); pebble(cv, 27, 25, True, 'dirt1')
    cv.px(22, 21, 'bone'); cv.px(23, 21, 'bone_dk')
    # tipped headstone
    hs = headstone(12, 17, moss=True)
    im = hs.image().rotate(68, resample=Image.NEAREST, expand=True)
    hc = Canvas(im.width, im.height)
    hc.a[:] = np.array(im)
    ys, xs = np.nonzero(hc.a[..., 3])
    cv.blit(hc, 0 - xs.min(), 30 - ys.max())
    return cv


def p_spring(frame):
    cv = prop_cell()
    cx, cy = 16, 27.5
    for y in range(22, 32):
        for x in range(0, 32):
            nx, ny = (x + .5 - cx) / 15, (y + .5 - cy) / 4.2
            d = nx * nx + ny * ny
            if d <= 1:
                t = 0.35 + 0.35 * (1 - d) + 0.12 * math.sin(x * 0.9 + frame * 2)
                cv.px(x, y, dpick(['spring0', 'spring1', 'spring2'], t, x, y))
    for x in range(4, 28):  # far rim shading
        if cv.solid(x, 24):
            cv.px(x, 24, 'spring0')
    # rim stones
    stones = [(1, 27, 3), (4, 30, 3), (9, 31, 4), (15, 31, 3), (21, 31, 4), (26, 30, 3), (29, 27, 3), (5, 24, 3), (12, 23, 3), (20, 23, 3), (26, 24, 3)]
    for (x, y, w) in stones:
        for i in range(w):
            cv.px(x + i, y, 'peb1')
            cv.px(x + i, y - 1, 'peb2' if i < w - 1 else 'peb1')
        cv.px(x + w - 1, y, 'peb0')
        if (x + y) % 2:
            cv.px(x, y - 1, 'moss2')
    sp = [(10, 27), (21, 28)] if frame == 0 else [(14, 26), (18, 29)]
    for (x, y) in sp:
        cv.px(x, y, 'spring3')
        for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            cv.px(x + dx, y + dy, 'spring2')
    cv.px(sp[0][0], sp[0][1] - 2, C('spring3', 160))
    cv.px(6 if frame == 0 else 24, 27, 'spring3')
    return cv


def fieldstones(cv, x0, y0, x1, y1, rng, wrap=False, ramp=None):
    ramp = ramp or ['fstone1', 'fstone2', 'fstone3', 'fstone4']
    W = cv.w
    y = y1
    while y > y0:
        h = int(rng.integers(3, 5))
        x = x0 + int(rng.integers(-3, 1))
        while x < x1:
            w = int(rng.integers(4, 8))
            cxs, cys = x + w / 2, y - h / 2
            tone = rng.uniform(-.1, .1)
            for yy in range(y - h, y + 1):
                for xx in range(x, x + w + 1):
                    nx, ny = (xx + .5 - cxs) / (w / 2 + .3), (yy + .5 - cys) / (h / 2 + .4)
                    if nx * nx + ny * ny <= 1 and yy >= y0:
                        t = .5 + tone - .35 * (nx * .5 + ny * .85)
                        X = xx % W if wrap else xx
                        if wrap or x0 <= xx <= x1:
                            cv.px(X, yy, dpick(ramp, t, xx, yy))
            x += w + 1
        y -= h + 1


def p_cellar(active):
    cv = prop_cell()
    rng = np.random.default_rng(55)
    # dark interior
    for y in range(19, 32):
        for x in range(4, 28):
            cv.px(x, y, 'cave0' if y > 21 else 'cave1')
    # back wall stones faint
    fieldstones(cv, 6, 19, 25, 24, rng, ramp=['cave1', 'cave2', 'cave3', 'cave4'])
    # side walls
    fieldstones(cv, 1, 17, 6, 31, rng)
    fieldstones(cv, 25, 17, 30, 31, rng)
    # rim of grass at ground
    for x in range(1, 31):
        if x < 6 or x > 25:
            cv.px(x, 17, 'grass3' if x % 2 else 'grass2')
    ground_tuft(cv, 0, 18, 2); ground_tuft(cv, 29, 18, 3)
    # front lip (bottom) stones
    for x in range(4, 28, 4):
        cv.px(x, 31, 'fstone2'); cv.px(x + 1, 31, 'fstone3'); cv.px(x + 2, 31, 'fstone1')
    if active:
        r = np.random.default_rng(7)
        for (sx, sy, dx) in [(15, 31, -1), (16, 30, 1), (14, 29, -1), (17, 31, 1), (12, 31, -1), (20, 30, 1)]:
            x, y = sx, sy
            for k in range(int(r.integers(8, 15))):
                cv.px(x, y, 'flesh2' if k % 3 else 'flesh1')
                cv.px(x, y + 1, 'flesh0')
                if k % 4 == 1:
                    cv.px(x, y - 1, 'flesh3')
                x += dx if r.random() < .7 else 0
                y -= 1 if r.random() < .55 else 0
                if y < 14:
                    break
            cv.px(x, y, 'flesh3')
        for (x, y) in [(15, 26), (16, 26), (15, 27), (16, 27), (14, 27), (17, 27)]:
            cv.px(x, y, 'flesh1')
        cv.px(15, 26, 'flesh3')
        for x in range(3, 29, 5):  # roots creeping over rim
            cv.px(x, 18, 'root1'); cv.px(x + 1, 19, 'root1'); cv.px(x + 1, 20, 'root0')
    return cv


def p_stake():
    cv = prop_cell()
    for y in range(14, 32):
        cv.px(15, y, 'wood4'); cv.px(16, y, 'wood2')
    cv.px(15, 14, 'wood5')
    for (x, y, c) in [(17, 14, 'rod_r'), (18, 14, 'rod_r'), (19, 14, 'rod_r'), (20, 15, 'rod_r'), (17, 15, 'dyn_dk'),
                      (18, 15, 'rod_r'), (19, 15, 'dyn_dk'), (21, 16, 'dyn_dk'), (17, 16, 'rod_r'), (18, 16, 'dyn_dk'),
                      (20, 16, 'rod_r'), (21, 15, 'rod_r'), (22, 16, 'rod_r')]:
        cv.px(x, y, c)
    for x in range(12, 20):
        cv.px(x, 31, 'dirt2' if x % 2 else 'dirt3')
    cv.px(13, 30, 'dirt3'); cv.px(14, 30, 'dirt2'); cv.px(17, 30, 'dirt3')
    outline(cv, None)
    return cv


def p_logpile():
    cv = prop_cell()
    rng = np.random.default_rng(3)
    for (cx, cy) in [(6, 26.5), (16, 26.5), (26, 26.5), (11, 18), (21, 18), (16, 9.5)]:
        log_end(cv, cx, cy, 5.2, rng, weathered=(cx == 21), ox=rng.uniform(-1, 1), oy=rng.uniform(-1, 1),
                check=(cx == 11))
    outline(cv, None)
    return cv


def p_stump():
    cv = prop_cell()
    for y in range(23, 32):
        flare = max(0, y - 27)
        for x in range(8 - flare, 24 + flare):
            t = .6 - (x - 8) / 20 + ((x * 3 + y) % 4 == 0) * .15
            cv.px(x, y, dpick(['bark0', 'bark1', 'bark2', 'bark3'], t, x, y))
    for y in range(20, 26):
        for x in range(8, 24):
            nx, ny = (x + .5 - 16) / 8, (y + .5 - 23) / 3
            d = nx * nx + ny * ny
            if d <= 1:
                k = int(math.sqrt(nx * nx * 64 + ny * ny * 9) * 0.9)
                c = 'wood5' if k % 2 == 0 else 'wood4'
                if d > .78:
                    c = 'bark2'
                cv.px(x, y, c)
    cv.px(16, 23, 'wood3')
    for (x, y) in [(4, 31), (5, 30), (26, 31), (28, 30), (27, 31)]:  # chips
        cv.px(x, y, 'wood5')
    outline(cv, None)
    return cv


def p_wall():
    cv = prop_cell()
    rng = np.random.default_rng(91)
    for y in range(22, 32):
        for x in range(32):
            cv.px(x, y, 'fstone0')
    fieldstones(cv, 0, 20, 31, 31, rng, wrap=True)
    for x in range(32):
        if cv.solid(x, 20) and x % 3 == 0:
            cv.px(x, 20, 'moss2')
        if x % 5 == 2:
            cv.px(x, 31, 'grass3'); cv.px(x, 30, 'grass2')
    outline(cv, None, wrap_x=True)
    return cv


def p_fern():
    cv = prop_cell()
    # herringbone fronds: stem curve, pinnae angled toward the tip, shorter near the tip
    fronds = [(-14, 21, -5, 12), (-7, 13, -4, 6), (2, 11, 1, 4), (9, 14, 7, 6), (14, 22, 9, 13),
              (-11, 27, -9, 20)]
    for i, (tx, ty, qx, qy) in enumerate(fronds):
        gold = i == 5
        lo, mid_, hi = (('mg2', 'mg3', 'mg4') if gold else ('grass2', 'grass3', 'grass4'))
        x0, y0 = 16, 31
        steps = 18
        pts = []
        for s_ in range(steps + 1):
            t = s_ / steps
            x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * (16 + qx) + t * t * (16 + tx)
            y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * qy + t * t * ty
            pts.append((x, y, t))
        for k in range(1, len(pts)):
            x, y, t = pts[k]
            px_, py_, _ = pts[k - 1]
            if k >= 3 and k % 2 == 1 and t < .95:
                dx, dy = x - px_, y - py_
                L = math.hypot(dx, dy) or 1
                ux, uy = dx / L, dy / L
                nx, ny = -uy, ux
                ln = int(round(3.5 * (1 - t) + 1))
                for j in range(1, ln + 1):
                    cv.px(x + (nx * .8 + ux * .6) * j, y + (ny * .8 + uy * .6) * j, hi if j < ln else mid_)
                    cv.px(x + (-nx * .8 + ux * .6) * j, y + (-ny * .8 + uy * .6) * j, lo if j < ln else 'grass1')
        for (x, y, t) in pts:
            cv.px(x, y, 'grass1' if not gold else 'mg1')
    for (x, y) in [(15, 31), (16, 31), (17, 31), (16, 30)]:
        cv.px(x, y, 'grass0')
    outline(cv, 'grass0')
    return cv


def p_flowers():
    cv = prop_cell()
    rng = np.random.default_rng(12)
    heads = []
    for i in range(10):
        x = int(5 + i * 2.4 + rng.uniform(-1, 1))
        h = int(rng.integers(8, 18))
        top = 31 - h
        lean = int(rng.integers(-1, 2))
        for y in range(top, 32):
            xx = x + (lean if y < top + h // 3 else 0)
            cv.px(xx, y, 'grass2' if y % 4 else 'grass1')
        cv.px(x + 1, 31 - h // 2, 'grass3'); cv.px(x - 1, 31 - h // 3, 'grass3')
        heads.append((x + lean, top, i % 3 == 1))
    for (x, top, golden) in heads:
        if golden:   # goldenrod: arching plume of tiny yellow florets
            for k in range(6):
                cv.px(x + k // 2, top - 4 + k, 'flower_y' if k % 2 else 'gold1')
                cv.px(x + k // 2 + 1, top - 4 + k, 'gold1' if k % 2 else 'flower_y')
            cv.px(x - 1, top - 3, 'flower_y')
        else:        # New England aster: violet ray florets, gold eye
            for (dx, dy) in [(0, -1), (-1, 0), (1, 0), (0, 1)]:
                cv.px(x + dx, top + dy, 'flower_v')
            for (dx, dy) in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                cv.px(x + dx, top + dy, 'flower_vd')
            cv.px(x, top, 'flower_y')
    ground_tuft(cv, 3, 31, 6); ground_tuft(cv, 18, 31, 8)
    return cv


def p_mushrooms():
    cv = prop_cell()
    shrooms = [(10, 31, 6, 4, 'glow'), (17, 31, 9, 5, 'vglow'), (23, 31, 5, 3, 'glow'), (6, 31, 3, 2, 'vglow'), (27, 31, 3, 2, 'glow')]
    for (x, base, h, r, g) in shrooms:  # halos first
        for y in range(base - h - r - 3, base + 1):
            for xx in range(x - r - 4, x + r + 5):
                d = math.hypot(xx - x, (y - (base - h)) * 1.2)
                if d < r + 4 and not cv.solid(xx, y):
                    a = int(70 * (1 - d / (r + 4)))
                    if a > 8 and (xx + y) % 2 == 0:
                        cv.px(xx, y, C(g + '1', a))
    for (x, base, h, r, g) in shrooms:
        for y in range(base - h, base + 1):
            cv.px(x, y, 'bone'); cv.px(x + 1, y, 'bone_dk')
        for y in range(base - h - r // 2 - 1, base - h + 1):
            for xx in range(x - r, x + r + 2):
                nx, ny = (xx + .5 - x - .5) / (r + .5), (y + .5 - (base - h + .5)) / (r / 2 + 1)
                if nx * nx + ny * ny <= 1 and y <= base - h:
                    t = .55 - .4 * nx * .5 - .5 * ny
                    cv.px(xx, y, dpick([g + '0', g + '1', g + '2'], t, xx, y))
        cv.px(x - r // 2, base - h - 1, 'eye_w')
    outline(cv, None)
    return cv


def p_lantern():
    cv = prop_cell()
    for y in range(8, 32):  # halo
        for x in range(0, 32):
            d = math.hypot(x - 15.5, (y - 22) * 1.1)
            if 5 < d < 14 and (x + y) % 2 == 0:
                a = int(90 * (1 - d / 14))
                if a > 10:
                    cv.px(x, y, C('lit_win', a))
    # bail handle
    for (x, y) in [(12, 16), (12, 15), (13, 14), (14, 13), (15, 13), (16, 13), (17, 14), (18, 15), (18, 16)]:
        cv.px(x, y, 'steel0')
    cv.rect(13, 16, 18, 17, 'steel1'); cv.px(13, 16, 'steel2')
    for y in range(18, 27):  # globe
        for x in range(12, 20):
            nx = (x + .5 - 16) / 4
            if abs(nx) <= (1 - ((y - 22.5) / 5.5) ** 2) ** .5:
                cv.px(x, y, mix('lit_win', 'gold1', abs(nx) * .8 + (y - 18) * .03))
    for y in range(19, 26):
        cv.px(16, y, 'steel0')  # guard wire
    cv.px(15, 21, 'spark1'); cv.px(15, 22, 'eye_w'); cv.px(15, 23, 'spark0'); cv.px(14, 22, 'spark1')
    cv.px(13, 20, 'eye_w')
    cv.rect(11, 27, 20, 28, 'steel1'); cv.rect(11, 29, 20, 31, 'rust1')
    cv.rect(12, 29, 19, 29, 'rust2'); cv.px(11, 31, 'rust0'); cv.px(20, 31, 'rust0')
    for x in range(11, 21):
        cv.px(x, 27, 'steel2' if x < 15 else 'steel1')
    return cv


def p_fence():
    cv = prop_cell()
    rng = np.random.default_rng(5)
    for y in range(12, 32):
        cv.px(14, y, 'board3'); cv.px(15, y, 'board2'); cv.px(16, y, 'board2'); cv.px(17, y, 'board1')
    cv.px(14, 12, 'board4'); cv.px(15, 12, 'board4')
    for (ry, sag) in [(16, 0), (23, 0)]:
        for x in range(32):
            cv.px(x, ry, 'board4' if (x * 3) % 7 else 'board3')
            cv.px(x, ry + 1, 'board2' if x % 5 else 'board3')
            cv.px(x, ry + 2, 'board1')
            if x % 9 == 4:
                cv.px(x, ry + 1, 'board1')
    for x in (3, 9, 22, 28):
        cv.px(x, 31, 'grass3'); cv.px(x, 30, 'grass2'); cv.px(x + 1, 31, 'grass2')
    outline(cv, None, wrap_x=True)
    return cv


def p_boulder():
    cv = prop_cell()
    rng = np.random.default_rng(15)
    blob_field(cv, 16, 23.5, 13, 8.5, ['fstone0', 'fstone1', 'fstone2', 'fstone3', 'fstone4'], rng,
               rough=1.0, contrast=.5, bias=.02)
    for y in range(14, 22):  # moss cap
        for x in range(4, 28):
            if cv.solid(x, y) and (not cv.solid(x, y - 2) or y < 17):
                if (x * 7 + y * 3) % 5 != 0:
                    cv.px(x, y, dpick(['moss0', 'moss1', 'moss2', 'moss3'], .75 - (y - 14) * .08 - (x - 4) * .01, x, y))
    for (x, y) in [(10, 26), (11, 27), (19, 22), (20, 23)]:
        cv.px(x, y, 'fstone0')
    for (x, y) in [(6, 22), (8, 20)]:
        cv.px(x, y, 'lichen')
    outline(cv, None)
    return cv


def build_props():
    sheet = Canvas(256, 128)
    items = [p_headstone(), p_open_grave(), p_spring(0), p_spring(1), p_cellar(False), p_cellar(True),
             p_stake(), p_logpile(), p_stump(), p_wall(), p_fern(), p_flowers(), p_mushrooms(), p_lantern(),
             p_fence(), p_boulder()]
    items += [p_root_heart(False), p_root_heart(True), p_charred_timber(), p_kerosene_drum(), p_kennel(),
              p_memory_stone(), p_cable_drum(), p_scorch()]
    items += [p_water_tower(), p_signal(), p_kennel_pen(), p_root_cluster(), p_egg_sac(), p_bumper(),
              p_diving_helmet(), p_dynamite_crate()]
    for i, it in enumerate(items):
        sheet.a[(i // 8) * 32:(i // 8) * 32 + 32, (i % 8) * 32:(i % 8) * 32 + 32] = it.a
    sheet.save('props.png')
    return sheet


# ============================================================================
# DECOR  (large sprites packed into decor.png + decor.json)
# ============================================================================
WHT = ['wht0', 'wht1', 'wht2', 'wht3', 'wht4', 'wht5']
ROOF = ['roof0', 'roof1', 'roof2', 'roof3']
BARK = ['bark0', 'bark1', 'bark2', 'bark3']


def trunk(cv, x, y0, y1, w0, w1, ramp=BARK, lean=0.0):
    for y in range(int(y1), int(y0) + 1):
        t = (y0 - y) / max(1, (y0 - y1))
        w = w0 + (w1 - w0) * t
        cx = x + lean * t * (y0 - y1)
        for xx in range(int(cx - w / 2), int(cx + w / 2) + 1):
            u = (xx + .5 - (cx - w / 2)) / max(w, 1)
            tt = .75 - .7 * u + (.15 if (xx * 5 + y * 3) % 7 == 0 else 0)
            cv.px(xx, y, dpick(ramp, tt, xx, y))


def branch(cv, x0, y0, x1, y1, col='bark1', w=2):
    if w >= 2:
        cv.thick(x0, y0, x1, y1, col, 'bark0')
    else:
        cv.line(x0, y0, x1, y1, col)


def crown(cv, rng, cx, cy, rx, ry, n, rmin, rmax, ramp, light=(-0.6, -0.8), flat=1.0, contrast=0.42):
    cl = []
    for _ in range(n * 4):
        a, r = rng.uniform(0, 2 * math.pi), math.sqrt(rng.random())
        x, y = cx + math.cos(a) * r * rx * .85, cy + math.sin(a) * r * ry * .85
        cl.append((x, y, rng.uniform(rmin, rmax)))
        if len(cl) >= n:
            break
    cl.sort(key=lambda c: -(c[0] * light[0] * -1 * -1 + 0) - (c[0] * -light[0] + c[1] * -light[1]))
    cl.sort(key=lambda c: (c[0] * light[0] + c[1] * light[1]))
    idmap = np.full((cv.h, cv.w), -1, int)
    for k, (x, y, r) in enumerate(reversed(cl)):
        blob_field(cv, x, y, r, r * flat, ramp, rng, light=light, rough=1.6, contrast=contrast,
                   gl=(cx, cy, max(rx, ry)), noise_amp=.18, idmap=idmap, ident=k)
    # cast shadows: a cluster in front darkens the cluster behind along its lower-right rim
    sh = C(ramp[1])
    for y in range(1, cv.h):
        for x in range(1, cv.w):
            b = idmap[y, x]
            if b < 0:
                continue
            f = max(idmap[y - 1, x], idmap[y - 1, x - 1], idmap[y, x - 1])
            if f > b and (idmap[y - 1, x] == f or idmap[y - 1, x - 1] == f):
                cv.a[y, x] = sh if (x + y) % 3 else C(ramp[0])
    return cl


def leaf_sparkle(cv, rng, ramp_hi, n, box):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = int(rng.integers(x0, x1)), int(rng.integers(y0, y1))
        if cv.solid(x, y) and not cv.solid(x - 1, y - 1):
            cv.px(x, y, ramp_hi)


def maple(rng, ramp, w=64, h=96):
    cv = Canvas(w, h)
    cx = w // 2
    trunk(cv, cx, h - 1, 48, 8, 4)
    for x in range(cx - 7, cx + 8):  # root flare
        if abs(x - cx) > 3:
            cv.px(x, h - 1, 'bark1'); cv.px(x, h - 2, 'bark0') if abs(x - cx) < 6 else None
    for (a, b, c, d) in [(cx, 60, cx - 16, 40), (cx, 56, cx + 15, 36), (cx, 50, cx - 4, 22), (cx - 8, 50, cx - 20, 52),
                         (cx + 2, 54, cx + 20, 50)]:
        branch(cv, a, b, c, d)
    crown(cv, rng, cx, 38, 27, 31, 30, 7.5, 11.5, ramp, contrast=.62)
    # second pass: a few lower clusters + gaps where branches peek
    for (bx, by) in [(cx - 9, 62), (cx + 10, 60), (cx - 1, 66)]:
        for k in range(4):
            cv.px(bx + k, by + k // 2, 'bark1')
    # falling leaves
    for _ in range(9):
        x, y = int(rng.integers(4, w - 4)), int(rng.integers(68, h - 4))
        if not cv.solid(x, y):
            cv.px(x, y, ramp[3 + int(rng.integers(0, 3))])
    leaf_sparkle(cv, rng, ramp[-1], 60, (2, 2, w - 2, 70))
    outline(cv, None)
    return cv


def white_pine(rng, w=48, h=112):
    cv = Canvas(w, h)
    cx = w // 2
    trunk(cv, cx, h - 1, 4, 5, 2, lean=0.02)
    ramp = ['pine0', 'pine1', 'pine2', 'pine3', 'pine4', 'pine5']
    # white pine: irregular, flat, windswept tiers with sky showing between them
    tiers = []
    y = h - 26
    i = 0
    while y > 10:
        span = 5 + (y - 6) / (h - 30) * 15
        left = span * rng.uniform(.5, 1.0) * (0.4 if i % 3 == 1 else 1)
        right = span * rng.uniform(.9, 1.5) * (0.5 if i % 4 == 2 else 1)
        tiers.append((y, left, right))
        y -= rng.uniform(8, 11)
        i += 1
    for (ty, L, Rr) in tiers:
        branch(cv, cx, ty + 3, cx - L * .85, ty + 1, 'bark1', 1)
        branch(cv, cx, ty + 3, cx + Rr * .85, ty, 'bark1', 1)
    for (ty, L, Rr) in tiers:
        for (x0, x1, dirn) in [(cx - L, cx + 1, -1), (cx - 1, cx + Rr, 1)]:
            n = max(1, int((x1 - x0) / 6))
            for k in range(n):
                px_ = x0 + (x1 - x0) * (k + .5) / n
                droop = abs(px_ - cx) * .12
                blob_field(cv, px_, ty + droop + rng.uniform(-1, 1), rng.uniform(5, 7.5), rng.uniform(2.8, 3.8),
                           ramp, rng, rough=1.8, contrast=.55, bias=.0, noise_amp=.22)
    blob_field(cv, cx + 1, 8, 3, 3.5, ramp, rng, rough=.8)
    for y in range(2, 6):
        cv.px(cx, y, 'pine3')
    # needle texture: short horizontal light streaks
    for _ in range(140):
        x, y = int(rng.integers(1, w - 2)), int(rng.integers(1, h - 18))
        if cv.solid(x, y) and cv.solid(x + 1, y) and not cv.solid(x, y - 2):
            cv.px(x, y, 'pine5'); cv.px(x + 1, y, 'pine4')
    outline(cv, None)
    return cv


def birch(rng, w=32, h=96):
    cv = Canvas(w, h)
    cx = w // 2
    for y in range(18, h):  # white trunk, slight curve
        off = int(round(math.sin(y / 18.0) * 1.5))
        for k, c in enumerate(['birch1', 'birch3', 'birch2', 'birch1']):
            cv.px(cx - 2 + k + off, y, c)
        if (y * 7) % 11 == 0:
            for k in range(int(rng.integers(1, 4))):
                cv.px(cx - 2 + k + off, y, 'birch0')
        if (y * 5) % 17 == 0:
            cv.px(cx + 1 + off, y, 'ink2')
    for (a, b, c, d) in [(cx, 40, cx - 10, 26), (cx, 34, cx + 11, 20), (cx, 28, cx - 6, 12), (cx + 1, 50, cx + 12, 40),
                         (cx - 1, 56, cx - 11, 48)]:
        cv.line(a, b, c, d, 'birch0')
    ramp = ['mg0', 'mg1', 'mg2', 'mg3', 'mg4', 'mg5']
    pts = [(cx - 10, 24), (cx + 10, 18), (cx - 5, 11), (cx + 3, 7), (cx + 11, 38), (cx - 11, 46), (cx, 18), (cx + 6, 28),
           (cx - 7, 34), (cx + 2, 44)]
    for (x, y) in pts:
        blob_field(cv, x, y, rng.uniform(4, 6), rng.uniform(3.5, 5), ramp, rng, rough=1.8, contrast=.5, noise_amp=.2)
    for _ in range(6):
        x, y = int(rng.integers(2, w - 2)), int(rng.integers(55, h - 4))
        if not cv.solid(x, y):
            cv.px(x, y, ramp[4])
    outline(cv, None)
    return cv


def apple_tree(rng, w=56, h=64):
    cv = Canvas(w, h)
    cx = w // 2
    trunk(cv, cx, h - 1, 42, 7, 4, lean=-0.04)
    for (a, b, c, d) in [(cx, 46, cx - 16, 32), (cx, 44, cx + 17, 34), (cx - 1, 44, cx + 2, 24)]:
        branch(cv, a, b, c, d)
    ramp = ['sg0', 'sg1', 'sg2', 'sg3', 'sg4']
    crown(cv, rng, cx, 27, 26, 20, 28, 6.5, 9.5, ramp, flat=.85, contrast=.55)
    # blossom clumps: pink-white, brightest on the lit (upper-left) faces
    for _ in range(260):
        x, y = int(rng.integers(1, w - 1)), int(rng.integers(3, 50))
        if cv.solid(x, y):
            lit = not cv.solid(x - 1, y - 2) or rng.random() < .5
            cv.px(x, y, str(rng.choice(['bloom2', 'bloom3', 'bloom1'])) if lit else 'bloom0')
            if rng.random() < .5:
                cv.px(x + 1, y, 'bloom1' if lit else 'bloom0')
            if rng.random() < .3:
                cv.px(x, y + 1, 'bloom0')
    for _ in range(10):  # falling petals
        x, y = int(rng.integers(2, w - 2)), int(rng.integers(46, h - 2))
        if not cv.solid(x, y):
            cv.px(x, y, 'bloom2')
    outline(cv, None)
    return cv


# ---------------- building helpers ----------------
def clap(cv, x0, y0, x1, y1, ramp=WHT, base=3, eave=3):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            k = base
            if (y - y0) % 3 == 2:
                k = base - 1
            if (y - y0) % 3 == 0:
                k = base + 1
            if x <= x0 + 1:
                k = min(k + 1, len(ramp) - 1)
            if x >= x1 - 1:
                k = max(k - 1, 0)
            if y - y0 < eave and B4[y % 4, x % 4] < (eave - (y - y0)) / eave:
                k = max(k - 2, 0)
            cv.px(x, y, ramp[k])


def boards_v(cv, x0, y0, x1, y1, ramp):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            k = 2
            if (x - x0) % 4 == 3:
                k = 0
            elif (x - x0) % 4 == 0:
                k = 3
            if ((x * 13 + y * 7) % 23) == 0:
                k = 1
            cv.px(x, y, ramp[min(k, len(ramp) - 1)])


def window(cv, x, y, w, h, boarded=False, lit=False, trim=('wht1', 'wht5'), arch=False):
    cv.rect(x - 1, y - 1, x + w, y + h, trim[1])
    cv.rect(x - 1, y + h, x + w, y + h, trim[0])
    cv.px(x + w, y - 1, trim[0])
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            c = 'glass0' if (yy - y) > (xx - x) * .7 + 1 else 'glass1'
            if lit:
                c = 'lit_win' if (xx + yy) % 5 else 'gold1'
            cv.px(xx, yy, c)
    cv.px(x, y, 'glass2')
    if arch:
        for xx in range(x, x + w):
            cv.px(xx, y - 1, trim[1])
        cv.px(x - 1, y - 1, (0, 0, 0, 0)); cv.px(x + w, y - 1, (0, 0, 0, 0))
        for xx in range(x, x + w):
            cv.px(xx, y - 2, trim[1])
    mx, my = x + w // 2, y + h // 2
    for xx in range(x, x + w):
        cv.px(xx, my, trim[1])
    if w >= 4:
        for yy in range(y, y + h):
            cv.px(mx, yy, trim[1])
    if boarded:
        for k, yy in enumerate([y + 1, y + h - 2]):
            for xx in range(x - 1, x + w + 1):
                cv.px(xx, yy + (xx - x) // 4 * (1 if k else 0) * 0, 'wood3' if xx % 3 else 'wood4')
                cv.px(xx, yy + 1, 'wood2')
            cv.px(x, yy, 'nail')
        for yy in range(y, y + h):
            cv.px(x + (yy - y) * w // h, yy, 'wood3')


def gable_roof(cv, xl, xr, ye, apex_y, thick=3, ramp=ROOF):
    ax = (xl + xr) / 2
    for k in range(thick):
        cv.line(xl, ye - k, ax, apex_y - k, ramp[3 if k == thick - 1 else 1])
        cv.line(ax, apex_y - k, xr, ye - k, ramp[2 if k == thick - 1 else 0])


def roof_plane(cv, pts, ramp=ROOF, rows=2):
    m = cv.poly(pts, ramp[1])
    ys, xs = np.nonzero(m)
    y0 = ys.min()
    for y, x in zip(ys, xs):
        k = 1
        if (y - y0) % rows == 0:
            k = 0
        elif ((x + ((y - y0) // rows) * 3) % 6) == 0:
            k = 0
        elif (y - y0) % rows == 1 and (x + y) % 4 == 0:
            k = 2
        cv.a[y, x] = C(ramp[k])
    return m


def chimney(cv, x, y0, y1, w=5):
    for y in range(y0, y1 + 1):
        for xx in range(x, x + w):
            c = 'brick1' if ((xx + (y // 2) * 2) % 4) else 'brick0'
            if (y % 2) == 0:
                c = 'brick0'
            if xx == x:
                c = 'brick2'
            cv.px(xx, y, c)
    cv.rect(x - 1, y0, x + w, y0, 'fstone3')


def foundation(cv, x0, x1, y0, y1, rng):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cv.px(x, y, 'gran2' if (x // 6 + y // 2) % 2 else 'gran3')
            if x % 6 == 0 or y == y0:
                cv.px(x, y, 'gran1' if y != y0 else 'gran4')


def farmhouse(rng):
    cv = Canvas(96, 80)
    # ell (lower wing) to the right
    roof_plane(cv, [(46, 50), (94, 50), (88, 36), (52, 36)])
    clap(cv, 50, 50, 92, 76)
    chimney(cv, 74, 28, 38)
    window(cv, 56, 56, 6, 8)
    window(cv, 80, 56, 6, 8, boarded=True)
    cv.rect(67, 58, 73, 75, 'wood2'); cv.rect(67, 58, 73, 58, 'wht5'); cv.rect(66, 58, 66, 75, 'wht4')
    cv.rect(74, 58, 74, 75, 'wht1'); cv.px(72, 67, 'gold1'); cv.rect(68, 60, 72, 63, 'glass1')
    # main block, gable end to viewer
    clap(cv, 6, 40, 50, 76)
    pts = [(6, 40), (28, 16), (50, 40)]
    m = cv.poly(pts, 'wht4')
    for y, x in zip(*np.nonzero(m)):
        k = 4 if (y % 3) else 3
        if x > 40:
            k -= 1
        cv.a[y, x] = C(WHT[k])
    gable_roof(cv, 3, 53, 42, 14, 3)
    chimney(cv, 25, 8, 15, 6)
    for (x, y, b) in [(11, 46, False), (37, 46, True), (11, 60, False), (37, 60, False)]:
        window(cv, x, y, 7, 9, boarded=b)
    window(cv, 26, 27, 4, 6, boarded=False)
    cv.rect(6, 40, 6, 76, 'wht5'); cv.rect(50, 40, 50, 76, 'wht2')   # corner boards
    cv.rect(24, 64, 31, 76, 'red1'); cv.rect(24, 64, 31, 64, 'wht5'); cv.rect(25, 66, 30, 69, 'red2')
    cv.px(30, 71, 'gold1')
    foundation(cv, 4, 93, 77, 79, rng)
    # weathering: grey patches, missing clapboard
    for (x, y) in [(18, 70), (19, 70), (20, 70), (44, 52), (45, 52), (86, 70), (87, 70), (60, 72)]:
        cv.px(x, y, 'board2')
    outline(cv, None)
    return cv


def barn(rng):
    cv = Canvas(96, 80)
    RED = ['red0', 'red1', 'red2', 'red3', 'red4']
    prof = [(8, 42), (18, 22), (48, 9), (78, 22), (88, 42)]
    body = [(10, 42), (19, 23), (48, 11), (77, 23), (86, 42), (86, 76), (10, 76)]
    m = cv.poly(body, 'red2')
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        k = 2
        if x % 4 == 3:
            k = 1
        elif x % 4 == 0:
            k = 3
        if x > 76:
            k = max(k - 1, 0)
        if (x * 13 + y * 7) % 31 == 0:
            k = 1
        cv.a[y, x] = C(RED[k])
    for i in range(len(prof) - 1):
        for k in range(3):
            cv.line(prof[i][0], prof[i][1] - k, prof[i + 1][0], prof[i + 1][1] - k, ROOF[3 if k == 2 else 1])
    # cupola
    cv.rect(44, 1, 52, 8, 'red2'); cv.rect(44, 1, 44, 8, 'red3')
    for y in range(2, 8):
        if y % 2:
            cv.rect(46, y, 50, y, 'wht4')
        else:
            cv.rect(46, y, 50, y, 'glass0')
    cv.line(43, 1, 48, -3, 'roof2'); cv.line(48, -3, 53, 1, 'roof1')
    cv.rect(43, 0, 53, 0, 'roof2')
    # loft door
    cv.rect(41, 26, 55, 38, 'red1')
    cv.rect(41, 26, 55, 26, 'wht5'); cv.rect(41, 38, 55, 38, 'wht3'); cv.rect(41, 26, 41, 38, 'wht5'); cv.rect(55, 26, 55, 38, 'wht2')
    cv.line(41, 26, 55, 38, 'wht4'); cv.line(55, 26, 41, 38, 'wht4')
    cv.rect(47, 22, 49, 22, 'steel1')  # hay hook
    cv.px(48, 23, 'steel0'); cv.px(48, 24, 'steel0')
    # big doors
    cv.rect(30, 48, 66, 76, 'red1')
    for (a, b) in [(30, 48), (48, 48)]:
        cv.rect(a, b, a + 18, b, 'wht5'); cv.rect(a, 76, a + 18, 76, 'wht3')
        cv.rect(a, b, a, 76, 'wht5'); cv.rect(a + 18, b, a + 18, 76, 'wht2')
        cv.line(a, b, a + 18, 76, 'wht4'); cv.line(a + 18, b, a, 76, 'wht4')
    cv.rect(28, 46, 68, 46, 'steel0')
    for (x, y) in [(16, 52), (74, 52)]:
        window(cv, x, y, 6, 6, trim=('wht2', 'wht5'))
    for x in range(10, 87):
        cv.px(x, 42, 'red0') if (x % 2) else None
    foundation(cv, 8, 88, 77, 79, rng)
    for (x, y) in [(12, 75), (13, 74), (84, 75), (20, 76)]:  # weeds
        cv.px(x, y, 'grass3')
    outline(cv, None)
    return cv


def draw_steeple(cv, cx, base_y, door=True, vane=True):
    # tower body
    clap(cv, cx - 12, 84, cx + 11, base_y)
    cv.rect(cx - 12, 84, cx - 12, base_y, 'wht5'); cv.rect(cx + 11, 84, cx + 11, base_y, 'wht1')
    if door:
        cv.rect(cx - 5, base_y - 18, cx + 4, base_y, 'wht5')
        cv.rect(cx - 4, base_y - 15, cx + 3, base_y, 'wood2')
        cv.rect(cx - 4, base_y - 15, cx + 3, base_y - 15, 'wood1')
        cv.line(cx - 4, base_y - 16, cx + 3, base_y - 16, 'glass1')
        for xx in range(cx - 3, cx + 3):
            cv.px(xx, base_y - 17, 'glass2' if xx % 2 else 'glass1')
        cv.rect(cx - 1, base_y - 14, cx - 1, base_y, 'wood1')
        cv.px(cx - 2, base_y - 7, 'gold1'); cv.px(cx, base_y - 7, 'gold1')
        window(cv, cx - 3, base_y - 38, 6, 12, arch=True)
    else:
        window(cv, cx - 3, base_y - 50, 6, 12, arch=True)
        window(cv, cx - 3, base_y - 26, 6, 12, arch=True)
    # cornice
    cv.rect(cx - 14, 82, cx + 13, 83, 'wht5'); cv.rect(cx - 14, 84, cx + 13, 84, 'wht1')
    # clock stage
    clap(cv, cx - 10, 64, cx + 9, 81, eave=2)
    cv.ellipse(cx, 73, 6.5, 6.5, 'wht1')
    cv.ellipse(cx, 73, 5.5, 5.5, 'wht5')
    for (dx, dy) in [(0, -4), (4, 0), (0, 4), (-4, 0)]:
        cv.px(cx + dx - 1 + (1 if dx <= 0 else 0), 72 + dy + (1 if dy <= 0 else 0), 'ink2')
    cv.line(cx, 73, cx, 69, 'ink'); cv.line(cx, 73, cx + 3, 74, 'ink')
    cv.rect(cx - 12, 62, cx + 11, 63, 'wht5'); cv.rect(cx - 12, 64, cx + 11, 64, 'wht1')
    # balustrade + corner urns
    for x in range(cx - 11, cx + 11):
        cv.px(x, 58, 'wht4')
        if x % 2 == 0:
            cv.px(x, 59, 'wht4'); cv.px(x, 60, 'wht3'); cv.px(x, 61, 'wht3')
    for ux in (cx - 12, cx + 10):
        cv.rect(ux, 55, ux + 1, 61, 'wht4'); cv.px(ux, 54, 'wht5'); cv.px(ux + 1, 54, 'wht3')
    # belfry
    clap(cv, cx - 8, 44, cx + 7, 57, eave=2)
    cv.rect(cx - 5, 47, cx + 4, 57, 'glass0')
    for xx in range(cx - 4, cx + 4):
        cv.px(xx, 46, 'glass0')
    for y in range(49, 57, 2):
        cv.rect(cx - 5, y, cx + 4, y, 'wht2')
    cv.rect(cx - 8, 44, cx - 7, 57, 'wht5'); cv.rect(cx + 6, 44, cx + 7, 57, 'wht2')
    cv.rect(cx - 9, 42, cx + 8, 43, 'wht5')
    # lantern stage
    clap(cv, cx - 6, 34, cx + 5, 41, eave=1)
    for xx in (cx - 3, cx + 1):
        cv.rect(xx, 36, xx + 1, 40, 'glass0')
    cv.rect(cx - 7, 33, cx + 6, 33, 'wht5')
    # spire
    for y in range(6, 33):
        half = (y - 6) / 27 * 6.5
        for xx in range(int(cx - half), int(cx + half) + 1):
            u = (xx - (cx - half)) / max(2 * half, 1)
            k = 5 if u < .3 else (4 if u < .55 else (3 if u < .8 else 1))
            if (y % 4 == 0) and k > 1:
                k -= 1
            cv.px(xx, y, WHT[k])
    if vane:
        cv.line(cx, 0, cx, 6, 'ink2')
        for (dx, dy) in [(-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (3, 1), (1, 1), (-2, 1)]:
            cv.px(cx + dx, dy, 'gold1')
        cv.px(cx + 3, 2, 'gold2')


def church(rng):
    cv = Canvas(96, 160)
    cx = 48
    # main meetinghouse body behind the tower
    clap(cv, 8, 100, 87, 156)
    m = cv.poly([(8, 100), (48, 74), (87, 100)], 'wht4')
    for y, x in zip(*np.nonzero(m)):
        cv.a[y, x] = C(WHT[4 if y % 3 else 3] if x < 70 else WHT[3 if y % 3 else 2])
    gable_roof(cv, 4, 91, 102, 72, 3)
    for x in (16, 68):
        window(cv, x, 108, 8, 16, arch=True)
        window(cv, x, 132, 8, 14)
    cv.rect(8, 100, 8, 156, 'wht5'); cv.rect(87, 100, 87, 156, 'wht1')
    draw_steeple(cv, cx, 156, door=True)
    foundation(cv, 4, 91, 157, 159, rng)
    cv.rect(cx - 7, 157, cx + 6, 159, 'gran3'); cv.rect(cx - 7, 157, cx + 6, 157, 'gran4')
    outline(cv, None)
    return cv


def drowned_steeple(rng):
    cv = Canvas(48, 160)
    draw_steeple(cv, 24, 159, door=False, vane=False)
    # bent vane stub
    cv.line(24, 2, 24, 6, 'rust1'); cv.px(25, 2, 'rust0'); cv.px(26, 3, 'rust1')
    a = cv.a.astype(float)
    m = a[..., 3] > 0
    alg = np.array(C('algae1')[:3], float)
    yy = np.arange(cv.h)[:, None] * np.ones((1, cv.w))
    f = 0.45 + 0.25 * (yy / cv.h)
    rgb = a[..., :3] * (1 - f[..., None]) * 0.75 + alg * f[..., None]
    rgb[..., 2] += 10
    a[..., :3] = np.where(m[..., None], rgb, a[..., :3])
    cv.a[:] = np.clip(a, 0, 255).astype(np.uint8)
    # algae drips & blotches
    for _ in range(70):
        x, y = int(rng.integers(0, cv.w)), int(rng.integers(5, cv.h))
        if cv.solid(x, y):
            ln = int(rng.integers(2, 9))
            for k in range(ln):
                if cv.solid(x, y + k):
                    cv.px(x, y + k, 'algae2' if k < ln // 2 else 'algae0')
    for _ in range(40):
        x, y = int(rng.integers(0, cv.w)), int(rng.integers(30, cv.h))
        if cv.solid(x, y):
            blob_field(cv, x, y, rng.uniform(1.5, 3), rng.uniform(1, 2), ['algae0', 'algae1', 'algae2', 'algae3'], rng,
                       rough=1.5)
    # weed streamers off ledges
    for (x, y) in [(10, 85), (36, 85), (13, 63), (34, 63), (17, 43), (31, 43), (20, 34)]:
        ln = int(rng.integers(5, 12))
        for k in range(ln):
            cv.px(x + int(math.sin(k * .7) * 1.2), y + k, 'algae3' if k % 3 else 'algae2')
    # missing louvers
    for (x, y) in [(22, 49), (23, 49), (25, 53), (26, 53)]:
        cv.px(x, y, 'cave0')
    outline(cv, None)
    return cv


def town_hall(rng):
    cv = Canvas(112, 80)
    # cupola behind the pediment
    cv.rect(50, 4, 61, 16, 'wht4'); cv.rect(50, 4, 50, 16, 'wht5'); cv.rect(61, 4, 61, 16, 'wht2')
    for x in (53, 57):
        cv.rect(x, 7, x + 1, 12, 'glass0')
    cv.poly([(49, 4), (55.5, -1), (62, 4)], 'roof2')
    cv.line(55, -1, 55, 0, 'ink2')
    cv.px(55, 0, 'gold1')
    # wall behind portico
    clap(cv, 10, 30, 101, 76, base=2)
    for x in (24, 54, 84):
        window(cv, x - 3, 44, 6, 12)
    cv.rect(50, 58, 61, 76, 'wht5'); cv.rect(52, 60, 59, 76, 'wood2'); cv.rect(55, 60, 56, 76, 'wood1')
    cv.ellipse(55.5, 58, 4, 3, 'glass1')
    # pediment
    m = cv.poly([(4, 30), (56, 9), (107, 30)], 'wht4')
    for y, x in zip(*np.nonzero(m)):
        cv.a[y, x] = C('wht4' if x < 80 else 'wht3')
    cv.poly([(14, 28), (56, 13), (97, 28)], 'wht3')
    cv.ellipse(56, 22, 3.5, 3.5, 'glass1')
    cv.ellipse(56, 22, 2.5, 2.5, 'glass2')
    gable_roof(cv, 2, 109, 31, 8, 3)
    cv.rect(4, 30, 107, 34, 'wht5'); cv.rect(4, 33, 107, 33, 'wht3'); cv.rect(4, 35, 107, 35, 'wht1')
    # columns
    for x in (12, 32, 75, 95):
        for y in range(36, 74):
            for k in range(6):
                cv.px(x + k, y, ['wht3', 'wht5', 'wht5', 'wht4', 'wht3', 'wht1'][k])
            if y % 6 == 0:
                cv.px(x + 2, y, 'wht4')
        cv.rect(x - 1, 36, x + 6, 37, 'wht5'); cv.rect(x - 1, 73, x + 6, 74, 'wht4')
        for y in range(38, 72):  # column shadow on wall
            cv.px(x + 6, y, 'wht0')
            cv.px(x + 7, y, 'wht1')
    # steps
    for k, y in enumerate((75, 77, 79)):
        cv.rect(2 + k * 0, y - 1 + (1 if k else 0), 109, y, 'gran3' if k % 2 == 0 else 'gran2')
        cv.rect(2, y - 1 + (1 if k else 0), 109, y - 1 + (1 if k else 0), 'gran4')
    outline(cv, None)
    return cv


def mill(rng):
    cv = Canvas(96, 96)
    # stone lower storey
    for y in range(60, 92):
        for x in range(34, 93):
            cv.px(x, y, 'fstone0')
    fieldstones(cv, 34, 60, 92, 92, rng)
    # wooden upper storey
    boards_v(cv, 34, 30, 92, 59, ['bark0', 'board1', 'board2', 'board3'])
    m = cv.poly([(34, 30), (63, 8), (92, 30)], 'board2')
    for y, x in zip(*np.nonzero(m)):
        cv.a[y, x] = C(['board1', 'board2', 'board3', 'board2'][x % 4])
    gable_roof(cv, 31, 95, 32, 6, 3)
    for (x, y) in [(42, 38), (78, 38), (60, 18)]:
        window(cv, x, y, 6, 8, trim=('bark1', 'board4'))
    window(cv, 60, 66, 6, 8, trim=('fstone1', 'fstone4'))
    cv.rect(44, 74, 52, 91, 'wood1'); cv.rect(44, 74, 52, 74, 'gran4'); cv.rect(45, 76, 51, 91, 'wood2')
    cv.rect(48, 76, 48, 91, 'wood1')
    cv.rect(80, 72, 86, 76, 'wood3')  # a sack hoist beam
    # flume
    for x in range(0, 30):
        cv.px(x, 40, 'wood4'); cv.px(x, 41, 'wood2'); cv.px(x, 42, 'wood1')
        cv.px(x, 39, 'water_hi' if x % 3 else 'foam')
    for x in (4, 14, 24):
        cv.rect(x, 43, x + 1, 92, 'wood2')
    # waterwheel
    wx, wy, R = 30, 66, 22
    for y in range(wy - R - 1, wy + R + 2):
        for x in range(wx - R - 1, wx + R + 2):
            d = math.hypot(x + .5 - wx, y + .5 - wy)
            if R - 2.5 <= d <= R:
                cv.px(x, y, 'wood3' if (x + y) % 3 else 'wood2')
            elif R - 7 <= d <= R - 6:
                cv.px(x, y, 'wood2')
    for k in range(16):
        a = k * 2 * math.pi / 16
        x0, y0 = wx + math.cos(a) * (R - 6), wy + math.sin(a) * (R - 6)
        x1, y1 = wx + math.cos(a) * (R + 1.5), wy + math.sin(a) * (R + 1.5)
        cv.line(x0, y0, x1, y1, 'wood4')
    for k in range(8):
        a = k * 2 * math.pi / 8 + .2
        cv.line(wx, wy, wx + math.cos(a) * (R - 6), wy + math.sin(a) * (R - 6), 'wood2')
    cv.ellipse(wx, wy, 2.5, 2.5, 'steel0')
    for (x, y) in [(10, 50), (9, 52), (11, 55), (8, 58)]:  # spill
        cv.px(x, y, 'water_hi')
    outline(cv, None)
    return cv


def trestle(rng):
    cv = Canvas(64, 64)
    W = 64
    ramp = ['bark0', 'board1', 'board2', 'board3']

    def beam(x0, y0, x1, y1, c='board2', c2='board1'):
        for off in (-W, 0, W):
            cv.thick(x0 + off, y0, x1 + off, y1, c, c2)
    for bx in (12, 44):  # bents: battered posts
        for (a, b) in [(bx - 2, bx - 6), (bx + 2, bx + 6)]:
            for y in range(8, 64):
                x = a + (b - a) * (y - 8) / 56
                cv.px(x, y, 'board3'); cv.px(x + 1, y, 'board2'); cv.px(x + 2, y, 'board1')
    for y in (28, 48):
        for x in range(W):
            cv.px(x, y, 'board3'); cv.px(x, y + 1, 'board2'); cv.px(x, y + 2, 'board1')
    for bx in (12, 44):  # cross bracing between bents (wraps)
        beam(bx, 12, bx + 32, 28)
        beam(bx, 28, bx + 32, 12)
        beam(bx, 31, bx + 32, 48)
        beam(bx, 48, bx + 32, 31)
    for x in range(W):  # deck: stringer + ties + rail
        cv.px(x, 8, 'board3'); cv.px(x, 9, 'board2'); cv.px(x, 10, 'board1'); cv.px(x, 11, 'bark0')
        if x % 4 in (0, 1):
            cv.px(x, 6, 'board3'); cv.px(x, 7, 'board2')
        cv.px(x, 5, 'steel1'); cv.px(x, 4, 'steel2')
    for bx in (12, 44):
        for (x, y) in [(bx, 9), (bx, 29), (bx, 49)]:
            cv.px(x, y, 'nail')
    outline(cv, None, wrap_x=True)
    return cv


def lattice(cv, p0, p1, w, col='steel0', col2='rust1', step=5):
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    a0 = (x0 + nx * w / 2, y0 + ny * w / 2)
    b0 = (x0 - nx * w / 2, y0 - ny * w / 2)
    cv.line(a0[0], a0[1], a0[0] + ux * L, a0[1] + uy * L, col)
    cv.line(b0[0], b0[1], b0[0] + ux * L, b0[1] + uy * L, col2)
    n = int(L / step)
    for i in range(n):
        s0, s1 = i * step, (i + 1) * step
        pa = (a0[0] + ux * s0, a0[1] + uy * s0) if i % 2 == 0 else (b0[0] + ux * s0, b0[1] + uy * s0)
        pb = (b0[0] + ux * s1, b0[1] + uy * s1) if i % 2 == 0 else (a0[0] + ux * s1, a0[1] + uy * s1)
        cv.line(pa[0], pa[1], pb[0], pb[1], col)


def crane(rng):
    cv = Canvas(96, 128)
    mx = 20
    # guy cables
    cv.line(mx, 6, 0, 110, 'ink2')
    cv.line(mx, 6, 95, 70, 'ink2')
    lattice(cv, (mx, 127), (mx, 4), 6, 'steel0', 'rust0', 5)
    cv.rect(mx - 4, 2, mx + 4, 5, 'steel1'); cv.px(mx, 1, 'steel2')
    # boom
    tip = (86, 26)
    lattice(cv, (mx + 3, 112), tip, 5, 'steel1', 'rust1', 6)
    cv.line(mx, 6, tip[0], tip[1], 'ink2')
    cv.line(mx + 1, 8, tip[0], tip[1] + 1, 'ink2')
    cv.ellipse(tip[0], tip[1], 2, 2, 'steel1')
    # hook
    cv.line(tip[0], tip[1], tip[0], 70, 'ink2')
    cv.rect(tip[0] - 2, 70, tip[0] + 2, 74, 'steel0'); cv.rect(tip[0] - 1, 71, tip[0] + 1, 72, 'rust2')
    for (dx, dy) in [(0, 75), (0, 76), (1, 77), (2, 77), (3, 76)]:
        cv.px(tip[0] + dx, dy, 'steel1')
    # engine house
    cv.rect(30, 104, 62, 127, 'board2')
    boards_v(cv, 30, 104, 62, 127, ['bark0', 'board1', 'board2', 'board3'])
    roof_plane(cv, [(27, 104), (65, 104), (60, 96), (32, 96)])
    window(cv, 36, 110, 5, 5, lit=True, trim=('bark0', 'board4'))
    cv.rect(48, 112, 56, 127, 'cave1')
    chimney(cv, 52, 86, 96, 3)
    for (x, y) in [(53, 82), (52, 79), (54, 76), (51, 74)]:
        cv.px(x, y, 'grey1'); cv.px(x + 1, y - 1, 'grey2')
    cv.rect(mx - 6, 124, mx + 6, 127, 'conc2'); cv.rect(mx - 6, 124, mx + 6, 124, 'conc3')
    outline(cv, None)
    return cv


def intake_tower(rng):
    cv = Canvas(64, 112)
    CONC = ['conc0', 'conc1', 'conc2', 'conc3', 'conc4']
    # main shaft (cylindrical shading)
    for y in range(30, 112):
        flare = max(0, (y - 96) / 16) * 4
        x0, x1 = 12 - flare, 51 + flare
        for x in range(int(x0), int(x1) + 1):
            u = (x - x0) / (x1 - x0)
            t = .78 - u * .7 + .12 * math.sin(u * math.pi)
            if (y % 10) == 0:
                t -= .1
            cv.px(x, y, dpick(CONC, t, x, y))
    # deco pilasters
    for px_ in (18, 31, 44):
        for y in range(34, 100):
            cv.px(px_, y, 'conc4' if px_ < 40 else 'conc2'); cv.px(px_ + 1, y, 'conc1')
    # upper shaft house
    for y in range(10, 27):
        for x in range(8, 56):
            u = (x - 8) / 48
            cv.px(x, y, dpick(CONC, .82 - u * .7, x, y))
    for x in (13, 23, 34, 44):
        window(cv, x, 13, 6, 10, trim=('conc1', 'conc4'), arch=True)
    cv.rect(6, 26, 57, 29, 'conc3'); cv.rect(6, 26, 57, 26, 'conc4'); cv.rect(6, 29, 57, 29, 'conc1')
    cv.rect(6, 8, 57, 10, 'conc3'); cv.rect(6, 8, 57, 8, 'conc4')
    # stepped deco parapet
    for (x0, x1, y) in [(10, 53, 6), (16, 47, 4), (24, 39, 2), (29, 34, 0)]:
        cv.rect(x0, y, x1, y + 1, 'conc3'); cv.rect(x0, y, x1, y, 'conc4'); cv.rect(x1, y, x1, y + 1, 'conc1')
    # arched door
    for y in range(84, 112):
        for x in range(25, 39):
            dx = x + .5 - 32
            if y >= 91 or dx * dx + ((y - 91) * 1.0) ** 2 <= 49:
                cv.px(x, y, 'cave0' if (x > 26 and x < 37 and (y > 87)) else 'conc1')
    for y in range(88, 112):
        cv.px(27, y, 'steel0'); cv.px(36, y, 'steel0')
    for x in range(27, 37, 3):
        for y in range(90, 112):
            cv.px(x, y, 'steel0')
    cv.px(32, 83, 'conc4'); cv.px(31, 83, 'conc4'); cv.px(32, 84, 'conc3')  # keystone
    # stains
    for x in (15, 29, 47):
        for y in range(30, 30 + int(rng.integers(12, 30))):
            if y % 2:
                cv.px(x, y, 'conc1')
    for y in range(102, 112):  # waterline algae
        for x in range(8, 56):
            if cv.solid(x, y) and (x + y) % 2 == 0 and y > 104:
                cv.px(x, y, 'algae1')
    outline(cv, None)
    return cv


def stone_bridge(rng):
    cv = Canvas(96, 48)
    cx, cy, R = 48, 47, 29
    for y in range(8, 48):
        for x in range(96):
            cv.px(x, y, 'fstone1')
    fieldstones(cv, 0, 8, 95, 47, rng, ramp=['fstone1', 'fstone2', 'fstone3', 'fstone4'])
    # arch opening (transparent)
    for y in range(0, 48):
        for x in range(96):
            if math.hypot(x + .5 - cx, y + .5 - cy) < R:
                cv.a[y, x] = 0
    # voussoirs
    nv = 15
    for k in range(nv):
        a0 = math.pi + k * math.pi / nv
        a1 = math.pi + (k + 1) * math.pi / nv
        key = k == nv // 2
        r1 = R + (8 if key else 6)
        for y in range(0, 48):
            for x in range(96):
                dx, dy = x + .5 - cx, y + .5 - cy
                d = math.hypot(dx, dy)
                ang = math.atan2(dy, dx) % (2 * math.pi)
                if R <= d < r1 and a0 <= ang < a1:
                    edge = (ang - a0) < 0.03 or d > r1 - 1
                    t = .55 + (.25 if key else 0) - .3 * (d - R) / (r1 - R) * 0 - .2 * ((ang - a0) / (a1 - a0))
                    c = dpick(['gran1', 'gran2', 'gran3', 'gran4'], t, x, y)
                    cv.px(x, y, 'gran0' if edge else c)
    # parapet & coping
    for x in range(96):
        cv.px(x, 2, 'gran4'); cv.px(x, 3, 'gran3'); cv.px(x, 4, 'gran2')
        cv.px(x, 5, 'gran1' if x % 8 else 'gran0')
        for y in range(6, 9):
            cv.px(x, y, 'fstone2' if (x // 5 + y) % 2 else 'fstone3')
    for x in range(0, 96, 12):
        cv.px(x, 2, 'gran0'); cv.px(x, 3, 'gran0'); cv.px(x, 4, 'gran0')
    # ivy / moss
    for _ in range(40):
        x, y = int(rng.integers(0, 96)), int(rng.integers(8, 47))
        if cv.solid(x, y):
            cv.px(x, y, 'moss1' if rng.random() < .6 else 'moss2')
    outline(cv, None)
    return cv


def build_decor():
    rng = np.random.default_rng(SEED + 5)
    items = [
        ('maple_red', maple(np.random.default_rng(11), ['mr0', 'mr1', 'mr2', 'mr3', 'mr4', 'mr5'])),
        ('maple_orange', maple(np.random.default_rng(12), ['mo0', 'mo1', 'mo2', 'mo3', 'mo4', 'mo5'])),
        ('maple_gold', maple(np.random.default_rng(13), ['mg0', 'mg1', 'mg2', 'mg3', 'mg4', 'mg5'])),
        ('white_pine', white_pine(np.random.default_rng(14))),
        ('birch', birch(np.random.default_rng(15))),
        ('apple_tree', apple_tree(np.random.default_rng(16))),
        ('farmhouse', farmhouse(np.random.default_rng(17))),
        ('barn', barn(np.random.default_rng(18))),
        ('church', church(np.random.default_rng(19))),
        ('town_hall', town_hall(np.random.default_rng(20))),
        ('mill', mill(np.random.default_rng(21))),
        ('trestle', trestle(np.random.default_rng(22))),
        ('crane', crane(np.random.default_rng(23))),
        ('intake_tower', intake_tower(np.random.default_rng(24))),
        ('drowned_steeple', drowned_steeple(np.random.default_rng(25))),
        ('stone_bridge', stone_bridge(np.random.default_rng(26))),
    ]
    # shelf packing, width 1024
    W = 1024
    x = y = shelf = 0
    pos = {}
    for name, cv in items:
        if x + cv.w > W:
            x = 0
            y += shelf + 2
            shelf = 0
        pos[name] = [x, y, cv.w, cv.h]
        x += cv.w + 2
        shelf = max(shelf, cv.h)
    H = y + shelf
    sheet = Canvas(W, H)
    for name, cv in items:
        px_, py_, w, h = pos[name]
        sheet.a[py_:py_ + h, px_:px_ + w] = cv.a
    sheet.save('decor.png')
    with open(os.path.join(OUT, 'decor.json'), 'w') as f:
        json.dump(pos, f, indent=1)
    return sheet


# ============================================================================
# PARALLAX BACKGROUNDS  (480x270, horizontally tileable)
# ============================================================================
BW, BH = 480, 270

AREAS = {
    'enfield': dict(
        sky=['#2c2160', '#4a2a74', '#723680', '#a44a82', '#d4687a', '#f08e6a', '#f8b462', '#ffd884'],
        sun=(352, 168, 16, ['#ffd884', '#ffe9a8', '#fff6d8'], ['#f8b462', '#ffd884']),
        cloud=['#5a3a78', '#8a4a80', '#d07a7a', '#ffc08a'], cloud_y=(60, 130), cloud_amt=.56,
        far_back=['#8a5a8e', '#7a4e86', '#a8688e'], far_front=['#4e3070', '#5e3878', '#7a4880', '#9a5a7e'],
        far_fleck=['#8a2a4a', '#b04a3a'],
        mid='autumn', mid_ramps=[['mr0', 'mr1', 'mr2', 'mr3', 'mr4'], ['mo0', 'mo1', 'mo2', 'mo3', 'mo4'],
                                 ['mg0', 'mg1', 'mg2', 'mg3', 'mg4'], ['pine0', 'pine1', 'pine2', 'pine3']],
        mid_fill=['#1e0c1c', '#2e1224', '#4a1a26'], mid_light=(.55, -.83), pine_w=.05),
    'greenwich': dict(
        sky=['#0a1238', '#14205a', '#22307a', '#3e3c8a', '#6a4a92', '#a45a96', '#d87a98', '#f6a4a0'],
        sun=None, moon=(96, 52, 7, 'crescent'), stars=40,
        cloud=['#2a2a64', '#4a3a7a', '#8a5a8e', '#e08a9a'], cloud_y=(70, 150), cloud_amt=.6,
        far_back=['#3a3a7a', '#44427e', '#54508a'], far_front=['#1e1e4e', '#262658', '#302e62', '#3e3a6e'],
        far_fleck=['#5a3a6a', '#6a4a5a'], steeple=True,
        mid='birch', mid_ramps=[['mg0', 'mg1', 'mg2', 'mg3', 'mg4'], ['mo0', 'mo1', 'mo2', 'mo3'],
                                ['pine0', 'pine1', 'pine2']],
        mid_fill=['#0c0c22', '#16142e', '#24203e'], mid_light=(-.8, -.6), pine_w=.3),
    'dana': dict(
        sky=['#2e6ad0', '#3e7cdc', '#5090e4', '#68a6ea', '#84bcee', '#a2d2ee', '#bce4e8', '#d0f2e0'],
        sun=(110, 46, 9, ['#fff8d8', '#ffffff', '#ffffff'], ['#bce4e8', '#e8f8f0']),
        cloud=['#9ab8e0', '#c4d8f0', '#e8f2fa', '#ffffff'], cloud_y=(30, 110), cloud_amt=.58,
        far_back=['#7ab2b0', '#86bcb4', '#9ac8bc'], far_front=['#4e8a6e', '#5a9a72', '#6aa878', '#86ba82'],
        far_fleck=['#9ac888', '#e4b8c8'],
        mid='spring', mid_ramps=[['sg0', 'sg1', 'sg2', 'sg3', 'sg4'], ['bloom0', 'bloom1', 'bloom2', 'bloom3'],
                                 ['sg0', 'sg1', 'sg2', 'sg3'], ['pine0', 'pine1', 'pine2', 'pine3', 'pine4']],
        mid_fill=['#14281c', '#1e3a24', '#2e5230'], mid_light=(-.6, -.8), pine_w=.25),
    'works': dict(
        sky=['#2a1a1e', '#46221e', '#6a2e1e', '#94401e', '#bc5a22', '#da7a2a', '#ee9e3a', '#f8c264'],
        sun=(300, 176, 22, ['#f8c264', '#ffd88a', '#ffe8b0'], ['#ee9e3a', '#f8c264']),
        cloud=['#2e2224', '#4a3230', '#6e4434', '#a0603a'], cloud_y=(20, 120), cloud_amt=.5, smoke=True,
        far_back=['#7a4a3a', '#86523c', '#965e40'], far_front=['#3e2420', '#4a2c24', '#5a3428', '#6e402c'],
        far_fleck=['#2e1c1c', '#7a5030'], dam=True,
        mid='works', mid_ramps=[['#140c0e', '#24161a', '#3a2620', '#5a3a28']],
        mid_fill=['#140c0e', '#1e1214'], mid_light=(.6, -.8)),
    'basin': dict(
        sky=['#05061a', '#0a0e2a', '#10183c', '#16244c', '#1a3458', '#1e4862', '#245a6a', '#2e6c72'],
        sun=None, moon=(150, 70, 24, 'full'), stars=180,
        cloud=['#0e1430', '#18244a', '#2a3c66', '#5a7a9a'], cloud_y=(110, 170), cloud_amt=.64,
        far_back=['#16224a', '#1a2a52', '#22345e'], far_front=['#0a1028', '#0e1630', '#121c3a', '#182446'],
        far_fleck=['#0a0e22', '#1e2e52'],
        mid='night', mid_ramps=[['#04060e', '#080c1a', '#0e1426', '#182238', '#2a3c5a']],
        mid_fill=['#04060e', '#060a14'], mid_light=(.0, -1.0)),
}


def wrapd(x, x0, W=BW):
    return (x - x0 + W / 2) % W - W / 2


def sky_layer(A, rng):
    cv = Canvas(BW, BH)
    yy, xx = np.mgrid[0:BH, 0:BW].astype(float)
    t = (yy / (BH * 0.78)) ** 1.05
    cv.a[:] = dramp(t, A['sky'], B=B8)
    if A.get('sun'):
        sx, sy, sr, disc, glow = A['sun']
        d = np.hypot(wrapd(xx, sx), yy - sy)
        g = np.clip(1 - (d - sr) / (sr * 4.5), 0, 1) ** 1.6
        idx = dramp(g, ['#000000'] + glow, B=B8)
        m = (g > 0) & (idx[..., 0:3].sum(-1) > 0)
        cv.a[m] = idx[m]
        ring = np.clip(1 - d / sr, 0, 1)
        dd = dramp(ring * 1.8, disc, B=B8)
        cv.a[d <= sr] = dd[d <= sr]
    if A.get('stars'):
        for _ in range(A['stars']):
            x, y = int(rng.integers(0, BW)), int(rng.integers(0, int(BH * .6)))
            b = rng.random()
            c = '#ffffff' if b > .8 else ('#c8d8ff' if b > .4 else '#7a8ab8')
            cv.px(x, y, c)
            if b > .93:
                for (dx, dy) in N4:
                    cv.pxw(x + dx, y + dy, '#7a8ab8')
    if A.get('moon'):
        mx, my, mr, kind = A['moon']
        d = np.hypot(wrapd(xx, mx), yy - my)
        if kind == 'full':
            g = np.clip(1 - (d - mr) / (mr * 2.5), 0, 1) ** 2
            idx = dramp(g * .9, ['#000000', '#1e3c5c', '#3a6280', '#6a90a8'], B=B8)
            m = (g > 0) & (idx[..., 0:3].sum(-1) > 0)
            cv.a[m] = idx[m]
            n = fbm(BW, BH, 60, 34, rng, 2)
            lit = np.clip(.75 - (wrapd(xx, mx) * .4 + (yy - my) * .5) / mr * .5 + (n - .5) * .5, 0, 1)
            md = dramp(lit, ['#8a9ab0', '#b8c4d0', '#dfe6ea', '#fbfaf0'], B=B4)
            cv.a[d <= mr] = md[d <= mr]
            for (cx_, cy_, r) in [(-8, -6, 4), (6, 4, 5), (-2, 10, 3), (10, -10, 3)]:
                dc = np.hypot(wrapd(xx, mx + cx_), yy - (my + cy_))
                mm = (dc <= r) & (d <= mr)
                cv.a[mm] = np.array(C('#9aa6b8'), np.uint8)
        else:
            d2 = np.hypot(wrapd(xx, mx + 3), yy - (my - 1))
            m = (d <= mr) & (d2 > mr - .5)
            cv.a[m] = np.array(C('#fff4d0'), np.uint8)
    # clouds
    y0, y1 = A['cloud_y']
    n = fbm(BW, BH, 8, 12, rng, 4)
    band = np.exp(-((yy - (y0 + y1) / 2) / ((y1 - y0) / 2)) ** 2)
    dens = n * (0.45 + 0.55 * band)
    thr = A['cloud_amt']
    above = np.roll(dens, 3, axis=0)
    shade_ = np.clip(.45 + (dens - above) * 6 + (dens - thr) * 2.5, 0, 1)
    cc = dramp(shade_, A['cloud'], B=B4)
    m = dens > thr
    cv.a[m] = cc[m]
    if A.get('smoke'):
        for (sx, w) in [(80, 14), (210, 10), (395, 18)]:
            for y in range(0, 200):
                drift = (200 - y) * .55
                cx_ = sx + drift + math.sin(y / 9.0) * 4
                ww = w * (0.4 + (200 - y) / 200 * 1.6)
                for x in range(int(cx_ - ww), int(cx_ + ww) + 1):
                    u = (x - cx_) / ww
                    dn = 1 - u * u + (rng.random() - .5) * .5
                    if dn > .3:
                        c = dpick(['#2a1c1e', '#3e2a28', '#5a3a30'], .3 + (1 - abs(u)) * .2 + (y / 200) * .2 - (u * .3), x, y)
                        cv.pxw(x, y, c)
    return cv


def ridge(rng, base, amps, ks):
    x = np.arange(BW)
    h = np.full(BW, float(base))
    for A_, k in zip(amps, ks):
        h += A_ * np.sin(2 * np.pi * k * x / BW + rng.uniform(0, 2 * np.pi))
    return h


def bump(x0, width, height):
    d = wrapd(np.arange(BW), x0)
    return height * np.exp(-(d / width) ** 2)


def fill_ridge(cv, h, ramp, rng, rim=None, flecks=None, tex=0.25, haze_top=0.0, depth=80):
    n = fbm(BW, BH, 48, 24, rng, 3)
    for x in range(BW):
        top = int(round(h[x]))
        for y in range(max(0, top), BH):
            t = 1 - min(1, (y - top) / depth) * .8 + (n[y, x] - .5) * tex * 2
            t = t * .85 + haze_top
            c = dpick(ramp, t, x, y)
            if flecks and n[y, x] > .78 and (x + y) % 2 == 0 and y > top + 2:
                c = C(flecks[(x // 3 + y) % len(flecks)])
            cv.a[y, x] = c
        if rim and 0 <= top < BH:
            if h[(x - 1) % BW] > h[x] or h[(x + 1) % BW] >= h[x]:
                cv.a[top, x] = C(rim)


def far_layer(A, rng, area):
    cv = Canvas(BW, BH)
    hb = ridge(rng, 132, [9, 6, 3], [1, 3, 7]) - bump(140, 40, 16)
    fill_ridge(cv, hb, A['far_back'], rng, rim=A['far_back'][-1], tex=.18, depth=120)
    hf = ridge(rng, 160, [10, 5, 2.5, 1.2], [2, 3, 6, 13]) - bump(330, 28, 26)   # Mount Pomeroy-ish
    if A.get('dam'):
        d = np.abs(wrapd(np.arange(BW), 200))
        dam_h = np.where(d < 90, 142, np.where(d < 125, 142 + (d - 90) * 0.8, 999))
        hf = np.minimum(hf, dam_h)
    fill_ridge(cv, hf, A['far_front'], rng, rim=A['far_front'][-1], flecks=A.get('far_fleck'), tex=.22, depth=90)
    if A.get('dam'):
        for x in range(110, 291):   # earthen dam: flat crest road, grassy stepped face
            cv.px(x, 142, '#c08a58'); cv.px(x, 143, '#8a5a3c')
            if x % 9 == 0:
                cv.px(x, 141, '#4a2c24')
            for y in range(144, 176):
                if (y - 144) % 6 == 0:
                    cv.px(x, y, '#7a4c34')
                elif (y - 144) % 6 == 1 and (x + y) % 2:
                    cv.px(x, y, '#5e3a2a')
        for x in range(150, 250, 3):
            cv.px(x, 141, '#2e1c1c')
    if A.get('steeple'):
        sx, sy = 382, int(hf[382])
        for y in range(sy - 30, sy + 2):
            ww = 3 if y > sy - 16 else (2 if y > sy - 22 else (1 if y > sy - 28 else 0))
            for x in range(sx - ww, sx + ww + 1):
                cv.px(x, y, '#141436')
        cv.rect(sx - 8, sy - 10, sx + 8, sy + 2, '#141436')
        cv.poly([(sx - 10, sy - 10), (sx, sy - 18), (sx + 10, sy - 10)], '#141436')
        cv.px(sx, sy - 13, '#ffd27a')
        cv.px(sx - 4, sy - 5, '#ffd27a'); cv.px(sx + 4, sy - 5, '#e0a830')
    return cv


def tree_line(cv, A, rng, base, rough_top=True):
    W = BW
    x = 0.0
    ramps = A['mid_ramps']
    lx, ly = A['mid_light']
    kind = A['mid']
    while x < W:
        r = rng.uniform(5, 11)
        pines = [q for q in ramps if q[0] == 'pine0']
        leafy = [q for q in ramps if q[0] != 'pine0'] or pines
        if pines and rng.random() < A.get('pine_w', .3):
            ramp = pines[int(rng.integers(0, len(pines)))]
        else:
            ramp = leafy[int(rng.integers(0, len(leafy)))]
        is_pine = ramp[0] == 'pine0'
        cy = base[int(x) % W] - r * rng.uniform(.3, .9)
        if is_pine:
            hgt = rng.uniform(22, 34)
            bx = int(x)
            topy = base[bx % W] - hgt
            for y in range(int(topy), BH):
                half = max(0, (y - topy) / hgt * 7 + (1 if (y % 4 == 0) else 0))
                for xx in range(int(bx - half), int(bx + half) + 1):
                    u = (xx - bx) / max(half, 1)
                    t = .45 - .35 * u * (-lx) + (.15 if (y % 4) == 1 else 0)
                    cv.pxw(xx, y, dpick(ramp, t, xx, y))
        else:
            blob_field(cv, x, cy, r, r * .9, ramp, rng, light=(lx, ly), rough=1.4, contrast=.5, wrap=True,
                       noise_amp=.2)
            if kind == 'birch' and rng.random() < .5:
                tx = int(x + rng.uniform(-3, 3))
                for y in range(int(cy + r * .6), int(base[tx % W]) + 14):
                    cv.pxw(tx, y, '#d8d4e4' if y % 5 else '#2a2a3e')
                    cv.pxw(tx + 1, y, '#8a88a8')
        x += rng.uniform(4, 9)


def mid_layer(A, rng, area):
    cv = Canvas(BW, BH)
    base = ridge(rng, 178, [5, 3, 1.5], [2, 5, 11])
    if A['mid'] == 'night':
        base = ridge(rng, 186, [8, 4, 2], [1, 4, 9])
    tree_line(cv, A, rng, base)
    tex = fbm(BW, BH, 60, 30, rng, 3)
    # textured forest floor beneath the crowns (darkens with depth)
    for x in range(BW):
        top = int(base[x]) + 6
        for y in range(top, BH):
            cv.a[y, x] = dpick(A['mid_fill'][::-1], .25 + (y - top) / 70 + (tex[y, x] - .5) * .6, x, y)
    # extra front row of crowns for depth
    base2 = base + 18
    if A['mid'] in ('autumn', 'spring', 'birch'):
        A2 = dict(A)
        tree_line(cv, A2, rng, base2)
        for x in range(BW):
            top = int(base2[x]) + 6
            for y in range(top, BH):
                cv.a[y, x] = dpick(A['mid_fill'][::-1], .3 + (y - top) / 50 + (tex[y, x] - .5) * .5, x, y)
    if A['mid'] == 'birch':
        for bx in range(11, BW, 41):
            bx += int(rng.integers(-8, 9))
            by = int(base2[bx % BW]) - int(rng.integers(18, 30))
            for y in range(by, int(base2[bx % BW]) + 10):
                cv.pxw(bx, y, '#2a2a40' if (y * 7) % 9 == 0 else '#e8e4f0')
                cv.pxw(bx + 1, y, '#9894b4')
            for (ox, oy) in [(0, 0), (-4, 4), (4, 3), (1, -3)]:
                blob_field(cv, bx + ox, by + oy, rng.uniform(3.5, 5.5), rng.uniform(3, 4.5),
                           ['mg0', 'mg1', 'mg2', 'mg3', 'mg4', 'mg5'], rng, light=A['mid_light'], rough=1.6,
                           contrast=.55, wrap=True, noise_amp=.2)
    if A['mid'] == 'spring':
        for hx in (60, 230, 400):   # white farmhouses + survey flags
            hy = int(base2[hx]) + 2
            cv.rect(hx, hy - 10, hx + 16, hy + 4, 'wht4'); cv.rect(hx + 12, hy - 10, hx + 16, hy + 4, 'wht2')
            cv.poly([(hx - 2, hy - 10), (hx + 8, hy - 18), (hx + 18, hy - 10)], 'roof2')
            cv.rect(hx + 3, hy - 6, hx + 5, hy - 3, 'glass1'); cv.rect(hx + 10, hy - 6, hx + 12, hy - 3, 'glass1')
            cv.rect(hx + 11, hy - 20, hx + 12, hy - 15, 'brick1')
        for fx in range(20, BW, 37):
            fy = int(base2[fx]) + 4
            cv.line(fx, fy - 9, fx, fy + 2, 'wood4')
            cv.px(fx + 1, fy - 9, 'rod_r'); cv.px(fx + 2, fy - 9, 'rod_r'); cv.px(fx + 1, fy - 8, 'dyn_dk')
    if A['mid'] == 'works':
        for x in range(BW):
            top = int(base[x]) + 6
            for y in range(top - 6, top):
                cv.px(x, y, A['mid_fill'][1])
        for (cx_, h) in [(50, 70), (180, 56), (330, 80), (430, 50)]:   # derricks
            by = int(base[cx_]) + 4
            lattice(cv, (cx_, by), (cx_, by - h), 4, '#140c0e', '#24161a', 4)
            lattice(cv, (cx_ + 2, by - 8), (cx_ + h * .7, by - h * .8), 3, '#140c0e', '#24161a', 5)
            cv.line(cx_, by - h, cx_ + h * .7, by - h * .8, '#140c0e')
            cv.line(int(cx_ + h * .7), int(by - h * .8), int(cx_ + h * .7), int(by - h * .4), '#140c0e')
        for (sx, w, h) in [(100, 30, 14), (250, 40, 18), (380, 24, 12)]:  # sheds w/ lit windows
            by = int(base[sx]) + 6
            cv.rect(sx, by - h, sx + w, by, '#1e1214')
            cv.poly([(sx - 2, by - h), (sx + w / 2, by - h - 7), (sx + w + 2, by - h)], '#1e1214')
            for wx in range(sx + 4, sx + w - 3, 7):
                cv.rect(wx, by - h + 5, wx + 2, by - h + 7, '#f8b062')
            cv.rect(sx + w - 6, by - h - 14, sx + w - 3, by - h, '#24161a')
        for x in range(0, BW, 2):   # trestle bents across
            pass
        for x in range(BW):
            ty = 214
            cv.px(x, ty, '#3a2620'); cv.px(x, ty + 1, '#24161a')
            if x % 16 in (0, 1):
                for y in range(ty + 2, BH):
                    cv.px(x, y, '#24161a')
            if x % 16 < 8:
                cv.px(x, ty + 2 + (x % 16), '#24161a')
                cv.px(x, ty + 9 - (x % 16), '#24161a')
    if A['mid'] == 'night':
        # the emptied village, dark against the hills
        sil = '#03050c'
        for (hx, w, h) in [(60, 14, 9), (82, 11, 8), (300, 16, 10), (322, 10, 7), (420, 13, 9)]:
            hy = int(base[hx]) + 2
            cv.rect(hx, hy - h, hx + w, hy + 4, sil)
            cv.poly([(hx - 1, hy - h), (hx + w / 2, hy - h - 6), (hx + w + 1, hy - h)], sil)
        sx = 250
        sy = int(base[sx]) + 2
        cv.rect(sx - 3, sy - 26, sx + 3, sy + 4, sil)
        cv.poly([(sx - 3, sy - 26), (sx, sy - 42), (sx + 3, sy - 26)], sil)
        cv.rect(sx - 10, sy - 10, sx + 10, sy + 4, sil)
        cv.poly([(sx - 12, sy - 10), (sx, sy - 18), (sx + 12, sy - 10)], sil)
        wy = 238
        for y in range(wy, BH):   # flooded basin water with reflections
            for x in range(BW):
                c = dpick(['#04060e', '#08101e', '#0c1a2c'], .3 + (y - wy) / 60, x, y)
                cv.a[y, x] = c
                src = wy - (y - wy) - 4
                if 0 <= src < BH and cv.a[src, x, 3] > 0 and (y % 2 == 0):
                    cv.a[y, x] = C('#0e1830')
        for y in range(wy + 1, BH, 2):   # moon glitter
            for x in range(BW):
                if abs(wrapd(x, 150)) < 4 + (y - wy) * .25 + 3 * math.sin(y * 1.7) and (x * 7 + y * 3) % 4 == 0:
                    cv.a[y, x] = C('#8ab0c8' if (x + y) % 3 else '#e0eef0')
        for x in range(BW):
            cv.a[wy, x] = C('#2a4a66') if x % 3 else C('#1a3048')
    return cv


def cave_bg(rng):
    cv = Canvas(BW, BH)
    yy, xx = np.mgrid[0:BH, 0:BW].astype(float)
    n = fbm(BW, BH, 24, 14, rng, 4)
    t = .25 + .25 * (yy / BH) + (n - .5) * .5
    cv.a[:] = dramp(t, ['#06050c', '#0c0a18', '#141226', '#1c1a34', '#262446'], B=B8)
    # rock strata cracks
    pts = poisson_pts(rng, BW, BH, 70, 34)
    i1, d1, d2, vx, vy = vor(BW, BH, pts)
    patchy = fbm(BW, BH, 12, 8, rng, 2) > .45
    m = ((d2 - d1) < 1.0) & patchy
    cv.a[m] = C('#0a0914')
    hl = ((d2 - d1) < 2.0) & ~((d2 - d1) < 1.0) & ((vx * .6 + vy * .8) > .5) & patchy & (B8[yy.astype(int) % 8, xx.astype(int) % 8] < .5)
    cv.a[hl] = C('#22203c')
    # roots hanging from the top
    for k in range(14):
        x = rng.uniform(0, BW)
        y = 0.0
        ln = rng.uniform(40, 140)
        w = 2
        while y < ln:
            cv.pxw(x, y, '#04030a')
            if w > 1:
                cv.pxw(x + 1, y, '#0a0814')
            x += rng.uniform(-1, 1)
            y += 1
            if rng.random() < .05:
                bx, by = x, y
                for j in range(int(rng.uniform(6, 20))):
                    bx += rng.choice([-1, 1]) * .8
                    by += 1
                    cv.pxw(bx, by, '#04030a')
            if y > ln * .6:
                w = 1
    # bioluminescent specks
    for k in range(26):
        x, y = int(rng.integers(0, BW)), int(rng.integers(20, BH - 10))
        g = 'glow' if rng.random() < .6 else 'vglow'
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                d = math.hypot(dx, dy)
                if 1 < d < 4.5 and (dx + dy) % 2 == 0:
                    cv.pxw(x + dx, y + dy, mix(cv.get((x + dx) % BW, y + dy), g + '0', .5 * (1 - d / 4.5)))
        cv.pxw(x, y, g + '2')
        for (dx, dy) in N4:
            cv.pxw(x + dx, y + dy, g + '1')
    return cv


def build_backgrounds():
    out = {}
    for i, (area, A) in enumerate(AREAS.items()):
        rng = np.random.default_rng(SEED + 100 + i * 7)
        sky = sky_layer(A, rng)
        far = far_layer(A, rng, area)
        mid = mid_layer(A, rng, area)
        sky.save('bg_%s_sky.png' % area)
        far.save('bg_%s_far.png' % area)
        mid.save('bg_%s_mid.png' % area)
        out[area] = (sky, far, mid)
    cave = cave_bg(np.random.default_rng(SEED + 999))
    cave.save('bg_cave.png')
    out['cave'] = cave
    return out


# ============================================================================
# EXPANSION ART: burners + foreman (people rows 6-7), tracker dog (animals
# row 2), props row 2, and the steam-shovel boss (boss_shovel.png/.json).
# Every new drawing makes its own seeded RNG, so nothing above is perturbed.
# ============================================================================
RUB = ('rub0', 'rub1', 'rub2')
FOREMAN_COAT = ('iron1', 'iron2', 'iron3')
STEEL = ['steel0', 'steel1', 'steel2', 'steel3']
BRASS = ['brass0', 'brass1', 'brass2', 'brass3']
CHAR = ['char0', 'char1', 'char2', 'char3']
OX = ['ox0', 'ox1', 'ox2', 'ox3', 'ox4']
IRON = ['iron0', 'iron1', 'iron2', 'iron3', 'iron4']


def amap(cv, x0, y0, rows, key):
    """Stamp an ASCII pixel map; '.' is skipped."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.':
                cv.px(x0 + i, y0 + j, key[ch])


def tube(cv, p0, pc, p1, r0, r1, ramp, n=40, light=(-0.6, -0.8), base=.45, k=.5):
    """Shaded tapering tube along a quadratic bezier (roots, hoses, logs)."""
    for s in range(n + 1):
        t = s / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * pc[0] + t * t * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * pc[1] + t * t * p1[1]
        r = r0 + (r1 - r0) * t
        for yy in range(int(y - r - 1), int(y + r + 2)):
            for xx in range(int(x - r - 1), int(x + r + 2)):
                dx, dy = xx + .5 - x, yy + .5 - y
                if dx * dx + dy * dy <= r * r:
                    lit = -(dx * light[0] + dy * light[1]) / max(r, .5)
                    cv.px(xx, yy, dpick(ramp, base + k * lit, xx, yy))


# ---------------------------------------------------------------- burners
def bn_arm(cv, sh, el, hd, sleeve, back, band=False):
    d, m, l = sleeve
    seg1 = bres(*sh, *el)
    pts = seg1 + bres(*el, *hd)[1:]
    v1 = abs(el[1] - sh[1]) >= abs(el[0] - sh[0])
    v2 = abs(hd[1] - el[1]) >= abs(hd[0] - el[0])
    for i, (x, y) in enumerate(pts[:-1]):
        c1, c2 = (d, d) if back else (d, l)
        if band and not back and i == 1:
            c1, c2 = 'tie_dk', 'tie'
        if v2 if i >= len(seg1) - 1 else v1:
            cv.px(x, y, c1); cv.px(x + 1, y, c2)
        else:
            cv.px(x, y, c2); cv.px(x, y + 1, c1)
    hx, hy = hd
    g = 'lea0' if back else 'lea2'
    cv.px(hx, hy, g); cv.px(hx + 1, hy, 'lea1' if not back else g)


def bn_leg(cv, hip, knee, ankle, back, wide=False, co=RUB):
    c = (co[0], co[0], co[0]) if back else (co[2], co[1], co[0])
    for a, b in ((hip, knee), (knee, ankle)):
        for (x, y) in bres(*a, *b):
            cv.px(x, y, c[0]); cv.px(x + 1, y, c[1])
            if wide:
                cv.px(x + 2, y, c[2])
    ax, ay = ankle
    bc = ('boot0', 'boot0', 'boot1') if back else ('boot1', 'boot2', 'boot1')
    cv.px(ax, ay + 1, bc[1]); cv.px(ax + 1, ay + 1, bc[0])
    cv.px(ax, ay + 2, bc[2]); cv.px(ax + 1, ay + 2, bc[0]); cv.px(ax + 2, ay + 2, bc[2])
    if wide:
        cv.px(ax + 2, ay + 1, bc[0]); cv.px(ax + 3, ay + 2, bc[0])


def bn_tank(cv, x0, y0, w, h, dark=False, gauge=False):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if y in (y0, y0 + h - 1) and x in (x0, x0 + w - 1):
                continue
            u = (x - x0 + .5) / w
            t = .74 - abs(u - .3) * 1.5 - (.22 if dark else 0)
            hoop = y in (y0 + 2, y0 + h - 3)
            body = (IRON[1:] if gauge else BRASS)
            hoopr = (BRASS if gauge else STEEL)
            cv.px(x, y, dpick(hoopr if hoop else body, t + (.12 if hoop else 0), x, y))
    for x in range(x0 + 1, x0 + w - 1, 2):            # rivets on the hoops
        cv.px(x, y0 + 2, 'steel3' if not gauge else 'brass3')
        cv.px(x, y0 + h - 3, 'steel2' if not gauge else 'brass2')
    for y in range(y0 + 4, y0 + h - 4, 2):            # seam rivets
        cv.px(x0 + 1, y, 'brass3' if not gauge else 'iron4')
    cx = x0 + w // 2
    if gauge:                                           # glowing pressure dial
        for (dx, dy, c) in [(-1, -2, 'brass1'), (0, -2, 'amber1'), (1, -2, 'brass1'),
                            (-1, -3, 'amber1'), (0, -3, 'amber2'), (1, -3, 'amber1'),
                            (0, -4, 'brass2'), (0, -1, 'brass0')]:
            cv.px(cx + dx, y0 + dy + 1, c)
    else:                                               # valve + handwheel
        cv.px(cx, y0 - 1, 'brass1')
        cv.px(cx - 1, y0 - 2, 'brass2'); cv.px(cx, y0 - 2, 'brass3'); cv.px(cx + 1, y0 - 2, 'brass1')


def bn_hose(cv, p0, p1, sag):
    mx, my = (p0[0] + p1[0]) / 2, max(p0[1], p1[1]) + sag
    prev = None
    for k in range(17):
        t = k / 16
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * mx + t * t * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * my + t * t * p1[1]
        p = (int(round(x)), int(round(y)))
        if prev:
            cv.line(*prev, *p, 'iron1')
        prev = p
    cv.px(p0[0], p0[1], 'brass2')


def bn_torso(cv, x0, y0, w, boss, co=RUB):
    for yr in range(7):
        for xr in range(w):
            c = co[1]
            if xr == 0:
                c = co[0]
            elif xr in (1, 2) and yr in (1, 2):
                c = co[2]
            elif yr == 0 and xr >= w - 3:
                c = co[2]
            if xr == w - 2 and 1 <= yr <= 5:          # harness strap
                c = 'lea1' if yr != 3 else 'brass2'
            if xr == w - 1 and yr in (2, 4):          # coat clasps
                c = 'steel2'
            if yr == 6:
                c = 'lea0' if xr != w - 2 else 'brass2'
            cv.px(x0 + xr, y0 + yr, c)
    if boss:                                          # leather shoulder cape
        for xr in range(-1, w + 1):
            cv.px(x0 + xr, y0, 'lea2' if 0 < xr < w - 1 else 'lea1')
            cv.px(x0 + xr, y0 + 1, 'lea1' if xr > -1 else 'lea0')
        cv.px(x0 + 2, y0, 'lea3'); cv.px(x0 + 3, y0, 'lea3')
        cv.px(x0 + w - 1, y0 + 4, 'gold2')            # foreman's badge


def bn_coat(cv, x0, hipy, w, sway, co=RUB):
    for k in range(3):
        s = sway if k == 2 else 0
        for xr in range(-1 + s, w + 1 + s):
            c = co[1]
            if xr <= -1 + s or xr == 0:
                c = co[0]
            if k == 2:
                c = co[0] if xr % 2 else co[1]
            if k == 0 and xr == 2:
                c = co[2]
            cv.px(x0 + xr, hipy + k, c)


def bn_head(cv, x0, y0, boss):
    for y in range(-1, 5):
        for x in range(5):
            if y == -1 and x in (0, 4):
                continue
            c = 'lea1'
            if x == 0 or y == 4:
                c = 'lea0'
            elif y <= 0 and x >= 2:
                c = 'lea2'
            cv.px(x0 + x, y0 + y, c)
    cv.px(x0 + 2, y0 - 1, 'lea3')
    for y in range(1, 4):                              # seam
        cv.px(x0 + 1, y0 + y, 'lea0')
    for y in range(2, 6):                              # hood drape at the neck
        cv.px(x0 - 1, y0 + y, 'lea0')
    g = ('amber0', 'amber1', 'amber2') if boss else ('gog0', 'gog1', 'gog2')
    cv.px(x0 + 3, y0 + 1, g[1]); cv.px(x0 + 4, y0 + 1, g[2])
    cv.px(x0 + 3, y0 + 2, g[0]); cv.px(x0 + 4, y0 + 2, g[1])
    cv.px(x0 + 5, y0 + 1, 'brass2'); cv.px(x0 + 5, y0 + 2, 'brass1')
    cv.px(x0 + 2, y0 + 1, 'brass1'); cv.px(x0 + 2, y0 + 2, 'brass0')
    cv.px(x0 + 4, y0 + 3, 'steel0'); cv.px(x0 + 5, y0 + 3, 'steel1')   # respirator
    cv.px(x0 + 4, y0 + 4, 'steel0'); cv.px(x0 + 5, y0 + 4, 'steel2'); cv.px(x0 + 6, y0 + 4, 'steel1')
    if boss:                                           # brass-ridged helmet hood
        for x in range(1, 4):
            cv.px(x0 + x, y0 - 2, 'brass2' if x != 1 else 'brass1')
        cv.px(x0 + 2, y0 - 2, 'brass3')


def bn_wand(cv, a, b, heavy=False):
    pts = bres(*a, *b)
    for i, (x, y) in enumerate(pts):
        if i < 2:
            c, c2 = 'lea1', 'lea0'
        elif i == 3:
            c, c2 = 'brass2', 'brass0'
        else:
            c, c2 = ('steel2' if i % 3 else 'steel1'), 'steel0'
        cv.px(x, y, c)
        cv.px(x, y + 1, c2)
        if heavy and i >= 2:
            cv.px(x, y - 1, 'steel1' if i % 2 else 'steel2')
    vx, vy = pts[3]
    cv.px(vx, vy - (2 if heavy else 1), 'brass2')       # valve wheel
    bx, by = b
    cv.px(bx, by - (2 if heavy else 1), 'steel1'); cv.px(bx, by + 2, 'steel0')
    cv.px(bx, by, 'steel3'); cv.px(bx, by + 1, 'steel1')
    if heavy:                                           # fuel canister under the barrel
        for x in range(a[0] + 2, a[0] + 5):
            cv.px(x, a[1] + 2 + (b[1] - a[1]) * (x - a[0]) // max(1, b[0] - a[0]), 'brass1' if x % 2 else 'brass2')


def draw_burner(ci, boss=False):
    """Row 6 burner / row 7 foreman. Columns as other rows; facing right."""
    if ci < 4:
        P = WALK[ci]
    else:
        P = [IDLE, STARTLED, GRABBED, None][ci - 4]
    attack = ci == 7
    if attack:
        P = dict(bob=0, legs=WIDE, arms=[((8, 12), (8, 12)), ((10, 12), (10, 12))])
    hold = ci not in (5, 6)
    cv = Canvas(16, 24)
    b = P.get('bob', 0)
    top, hipy = 9 + b, 16 + b
    (bk, ba), (fk, fa) = P['legs']
    (be, bh), (fe, fh) = P['arms']

    def up(p):
        return (p[0], p[1] + b)
    tx = 0 if boss else 2
    tw = 4
    if hold:
        if attack:
            wa, wb = (5, 12), (13, 12)
            fe, fh = (9, 13), (10, 12)
        else:
            wa, wb = (5, 17), (15, 14)
            fe, fh = (9, 13), (10, 15)
            wa, wb = up(wa), up(wb)
            fe, fh = (fe[0], fe[1]), (fh[0], fh[1])
    # tanks (behind everything)
    if boss:
        bn_tank(cv, 1, top - 3, tw, 11, dark=True, gauge=True)
        bn_tank(cv, 3, top - 1, tw + 1, 11, gauge=True)
        tank_out = (5, top + 9)
    else:
        bn_tank(cv, tx, top, tw, 10)
        tank_out = (tx + 2, top + 10)
    if hold:
        bn_hose(cv, tank_out, (wa[0] + 1, wa[1] + 1), 3)
    else:
        bn_hose(cv, tank_out, (tank_out[0] + 5, 22), 0)
    sx = 1 if boss else 0
    co = FOREMAN_COAT if boss else RUB
    bn_arm(cv, up((7, 10)), up(be), up(bh), co, back=True)
    bn_leg(cv, (6, hipy), bk, ba, back=True, wide=boss, co=co)
    if boss:
        bn_torso(cv, 5, top, 7, True, co)
    else:
        bn_torso(cv, 6, top, 5, False, co)
    bn_leg(cv, (8, hipy), fk, fa, back=False, wide=boss, co=co)
    sway = 1 if fa[0] > 9 else (-1 if fa[0] < 7 else 0)
    if boss:
        bn_coat(cv, 5, hipy, 7, sway, co)
    else:
        bn_coat(cv, 6, hipy, 5, sway, co)
    hdx, hdy = P.get('hdx', 0), P.get('hdy', 0)
    bn_head(cv, 6 + sx + hdx, 4 + b + hdy, boss)
    if hold:
        bn_wand(cv, wa, wb, heavy=boss)
        bn_arm(cv, (8 + sx, 10 + b), fe if attack else up(fe), fh if attack else up(fh), co, back=False, band=boss)
    else:
        bn_arm(cv, up((8 + sx, 10)), up(fe), up(fh), co, back=False, band=boss)
    if P.get('rot'):
        im = cv.image().rotate(P['rot'], resample=Image.NEAREST, center=(8, 14))
        cv.a[:] = np.array(im)
    outline(cv, 'ink')
    if attack and not boss:                             # blue-white pilot flame
        bx, by = wb
        for (x, y, c) in [(14, by, 'pilot2'), (15, by, 'pilot1'), (14, by - 1, 'pilot1'), (15, by - 1, 'pilot0'),
                          (14, by + 1, 'pilot0')]:
            cv.px(x, y, c)
    if attack and boss:                                 # spraying: flame bloom at the nozzle
        by = wb[1]
        for (x, y, c) in [(14, by, 'fire3'), (15, by, 'fire3'), (14, by + 1, 'fire2'), (15, by + 1, 'fire3'),
                          (14, by - 1, 'fire2'), (15, by - 1, 'fire2'), (15, by - 2, 'fire1'), (15, by + 2, 'fire1'),
                          (14, by + 2, 'fire1'), (13, by - 2, 'fire0')]:
            cv.px(x, y, c)
    return cv


# ---------------------------------------------------------------- tracker dog
HOUND_KEY = {'0': 'dog0', '1': 'dog1', '2': 'dog2', '3': 'dog3', 'k': 'ink', 'K': 'dogk0', 'b': 'dog0', 'B': 'dogk1',
             'm': 'mouth', 'r': 'tie', 'g': 'brass2', 'n': 'worm'}
HOUND_HEAD = [
    "..2332...",
    ".222322..",
    ".bb2k2233",
    "bbb22222k",
    "bbb122221",
    "Bbb.11111",
    ".bb.1.11.",
    "..B......",
]
HOUND_BAY = [
    ".......3k",
    ".....2322",
    "...232mmm",
    "..2k2mmn.",
    ".bb22111.",
    "bbb1111..",
    "Bbb.1....",
    ".bB......",
]


def hound(frame):
    cv = Canvas(24, 16)
    ramp = ['dog0', 'dog1', 'dog2', 'dog3']
    bay = frame == 2
    if frame == 0:     # stretched: forelegs reaching, hind legs driving
        legs = [((6, 9), (4, 12), (2, 15), 'dog0'), ((16, 9), (18, 12), (20, 14), 'dog0'),
                ((7, 9), (6, 12), (4, 14), 'dog1'), ((17, 9), (19, 11), (21, 15), 'dog1')]
        bcy = 7.5
    elif frame == 1:   # gathered under the body
        legs = [((6, 9), (8, 12), (10, 15), 'dog0'), ((16, 9), (14, 12), (12, 14), 'dog0'),
                ((7, 9), (9, 12), (8, 15), 'dog1'), ((17, 9), (16, 12), (14, 15), 'dog1')]
        bcy = 6.5
    else:              # planted, baying
        legs = [((6, 9), (5, 12), (5, 15), 'dog0'), ((16, 9), (16, 12), (16, 15), 'dog0'),
                ((7, 9), (7, 12), (7, 15), 'dog1'), ((17, 9), (17, 12), (18, 15), 'dog1')]
        bcy = 7.5
    for (a, k, f, c) in legs:
        cv.line(*a, *k, c); cv.line(*k, *f, c)
        cv.line(a[0] + 1, a[1], k[0] + 1, k[1], 'dog0')
        cv.px(f[0], f[1], 'dogk1'); cv.px(f[0] + 1, f[1], 'dogk1')
    shaded_ellipse(cv, 11.5, bcy, 7.4, 3.3, ramp, base=.6, k=.4)
    for y in range(int(bcy - 4), int(bcy + 1)):           # black saddle
        for x in range(5, 17):
            if cv.solid(x, y) and y < bcy - .2 + (x - 11) * 0 and (y < bcy - 1 or 7 < x < 15):
                cv.px(x, y, dpick(['dogk0', 'dogk1', 'dogk2'], .75 - (y - (bcy - 4)) * .2, x, y))
    for x in range(7, 16):                                 # pale chest/belly
        cv.px(x, int(bcy + 3), 'dog3' if x % 3 else 'dog2')
    # neck
    by = int(bcy)
    if bay:
        hx, hy = 14, 0
        for (x, y) in [(16, by - 1), (16, by - 2), (17, by - 3), (16, by - 3), (17, by - 4)]:
            cv.px(x, y, 'dog2'); cv.px(x - 1, y + 1, 'dog1')
        cv.px(15, by - 2, 'tie'); cv.px(16, by - 2, 'tie'); cv.px(17, by - 2, 'tie'); cv.px(17, by - 1, 'brass2')
        amap(cv, hx, hy, HOUND_BAY, HOUND_KEY)
        tail = [(5, 5), (4, 4), (4, 3), (3, 2), (3, 1)]
    else:
        hx, hy = 15, by - 5
        for (x, y) in [(16, by - 1), (17, by - 1), (17, by - 2), (18, by - 2)]:
            cv.px(x, y, 'dog2'); cv.px(x, y + 1, 'dog1')
        cv.px(17, by - 1, 'tie'); cv.px(18, by - 1, 'tie'); cv.px(18, by, 'tie'); cv.px(19, by, 'brass2')
        amap(cv, hx, hy, HOUND_HEAD, HOUND_KEY)
        tail = [(5, by - 2), (4, by - 3), (3, by - 4), (3, by - 5)] if frame == 0 else \
               [(5, by - 2), (4, by - 3), (4, by - 4), (3, by - 5)]
    for i, (x, y) in enumerate(tail):
        cv.px(x, y, 'dog3' if i == len(tail) - 1 else 'dog2')
    outline(cv, None)
    return cv


# ---------------------------------------------------------------- props row 2
def _heart_in(x, y, cx, cy, s):
    u = (x + .5 - cx) / s
    v = -(y + .5 - cy) / s
    return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0, u, v


def p_root_heart(taken):
    cv = prop_cell()
    rng = np.random.default_rng(1600)
    back = ['bark0', 'root0', 'root1'] if not taken else ['bark0', 'bark0', 'root0']
    front = ['bark0', 'root0', 'root1', 'root2'] if not taken else ['bark0', 'root0', 'root0', 'root1']
    # thin rootlets fanning out behind (the knot's crown and feeders)
    for (p0, pc, p1, r0, r1) in [((13, 13), (10, 8), (7, 5), .9, .4), ((19, 13), (22, 7), (26, 6), .9, .4),
                                 ((9, 20), (5, 19), (3, 15), .8, .4), ((23, 20), (28, 21), (30, 17), .8, .4)]:
        tube(cv, p0, pc, p1, r0, r1, back, n=24, base=.4)
    cx, cy, s = 16, 18.6, 7.4
    for y in range(6, 30):
        for x in range(4, 29):
            ins, u, v = _heart_in(x, y, cx, cy, s)
            if not ins:
                continue
            if taken:
                t = .15 + .3 * (1 - (v + 1) / 2.2) + rng.uniform(-.1, .1)
                c = dpick(['cave0', 'cave1', 'cave2'], t, x, y)
                if (x * 3 + y * 5) % 13 == 0:
                    c = 'root0'
            else:
                lc = .55 if u > 0 else -.55                     # each lobe lit at its upper left
                t = .5 + .27 * (-.6 * (u - lc) + .8 * v) + .12 * v + rng.uniform(-.06, .06)
                if abs(u) < .16 and v > .45:                     # cleft between the lobes
                    t -= .35
                c = dpick(['flesh0', 'flesh1', 'flesh2', 'flesh3'], t, x, y)
            cv.px(x, y, c)
    if not taken:
        for (p0, p1) in [((16, 12), (14, 19)), ((14, 19), (11, 18)), ((14, 19), (15, 24)), ((16, 12), (19, 18)),
                         ((19, 18), (22, 15))]:
            for i, (x, y) in enumerate(bres(*p0, *p1)):
                cv.px(x, y, 'flesh0' if i % 4 else 'flesh3')
        for (x, y) in [(10, 11), (11, 11), (10, 12), (20, 11), (21, 11)]:   # lobe gloss
            cv.px(x, y, 'worm_hl')
    else:
        for (x, y) in [(14, 23), (15, 24), (19, 15), (12, 16)]:
            cv.px(x, y, 'flesh0')
    # gnarled roots gripping the knot from below and wrapping over its face
    for (p0, pc, p1, r0, r1) in [((16, 31), (16, 29), (16, 25), 2.4, 1.4),            # taproot under the point
                                 ((5, 31), (3, 22), (10, 12), 2.0, .8),               # up the left flank
                                 ((27, 31), (30, 22), (22, 11), 2.0, .8),             # up the right flank
                                 ((26, 30), (16, 23), (6, 17), 1.4, .7),              # across the front
                                 ((9, 31), (13, 27), (21, 22), 1.2, .6),
                                 ((16, 31), (8, 31), (1, 30), 1.3, .5), ((16, 31), (24, 31), (31, 30), 1.3, .5)]:
        tube(cv, p0, pc, p1, r0, r1, front, base=.5)
    for (x, y) in [(4, 23), (28, 21), (15, 22), (12, 28)]:   # knots
        cv.px(x, y, front[0])
    outline(cv, None)
    if not taken:
        for (x, y) in [(6, 8), (27, 9), (29, 24), (2, 19), (21, 3)]:   # gold motes
            cv.px(x, y, 'gold2')
            for (dx, dy) in N4:
                if not cv.solid(x + dx, y + dy):
                    cv.px(x + dx, y + dy, C('gold1', 120))
    return cv


def char_log(cv, p0, p1, r, rng, end=True):
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    if ny < 0:
        nx, ny = -nx, -ny
    xs = range(int(min(x0, x1) - r - 1), int(max(x0, x1) + r + 2))
    ys = range(int(min(y0, y1) - r - 1), int(max(y0, y1) + r + 2))
    for y in ys:
        for x in xs:
            dx, dy = x + .5 - x0, y + .5 - y0
            s = dx * ux + dy * uy
            d = dx * nx + dy * ny
            if 0 <= s <= L and abs(d) <= r:
                t = .7 - .6 * d / r
                row = int((d + r) / 2.0)
                crack = (int(s) + row * 2) % 5 == 0 and abs(d) < r - .6
                if crack:
                    hot = ((int(s) * 7 + row * 3) % 4 == 0) and d < r * .5
                    c = ('fire1' if (int(s) + row) % 2 else 'spark0') if hot else 'char0'
                else:
                    c = dpick(CHAR, t, x, y)
                cv.px(x, y, c)
    if end:                                            # charred end grain with a live core
        for y in range(int(y1 - r - 1), int(y1 + r + 2)):
            for x in range(int(x1 - r), int(x1 + r + 2)):
                ddx, ddy = (x + .5 - x1) * 1.6, y + .5 - y1
                dd = math.hypot(ddx, ddy)
                if dd <= r:
                    k = int(dd * 1.2)
                    c = 'char2' if k % 2 else 'char1'
                    if dd < r * .45:
                        c = 'fire1' if dd > r * .25 else 'fire2'
                    if dd > r - .8:
                        c = 'char3' if ddy < 0 else 'char0'
                    cv.px(x, y, c)


def smoke_wisp(cv, x0, y0, h, rng, phase=0.0):
    for k in range(h):
        y = y0 - k
        x = x0 + math.sin(k * .45 + phase) * 1.6 + k * .12
        a = int(170 * (1 - k / h))
        if a < 30 or (k % 2 and k > h * .5):
            continue
        c = 'smoke2' if k < h * .35 else 'smoke1'
        cv.px(x, y, C(c, a))
        if k < h * .6:
            cv.px(x + 1, y, C('smoke1', a // 2))


def p_charred_timber():
    cv = prop_cell()
    rng = np.random.default_rng(1610)
    char_log(cv, (2, 27.5), (26, 28), 3.3, rng)
    char_log(cv, (7, 21.5), (28, 22.5), 2.9, rng)
    char_log(cv, (3, 14), (22, 23), 2.4, rng, end=False)
    for (x, y) in [(5, 13), (4, 14), (6, 14)]:          # snapped, glowing tip
        cv.px(x, y, 'fire2' if x == 5 else 'fire1')
    for (x, y) in [(11, 16), (18, 19), (24, 19), (9, 24)]:   # live embers on top
        cv.px(x, y, 'spark1')
    outline(cv, None)
    for (x, y) in [(1, 31), (29, 31), (30, 30), (0, 30)]:
        cv.px(x, y, 'ash')
    smoke_wisp(cv, 11, 16, 14, rng, 0.0)
    smoke_wisp(cv, 19, 19, 16, rng, 2.0)
    smoke_wisp(cv, 6, 14, 9, rng, 4.0)
    return cv


def p_kerosene_drum():
    cv = prop_cell()
    x0, x1, yt, yb = 9, 22, 12, 31
    w = x1 - x0 + 1
    RED = ['red0', 'red1', 'red2', 'red3', 'red4']
    for y in range(yt, yb + 1):
        for x in range(x0, x1 + 1):
            u = (x - x0 + .5) / w
            t = .74 - abs(u - .3) * 1.35
            dd = math.hypot((x + .5 - 18.5) / 2.6, (y + .5 - 22) / 3.2)
            if dd < 1:                                  # dent: shadowed bowl, lit lower lip
                t += -.32 * (1 - dd) if (y + .5) < 22.5 else .18 * (1 - dd)
            ramp = RED
            if yt + 1 <= y <= yt + 5 or yb - 2 <= y <= yb:
                ramp = CHAR
            if y in (yt + 9, yb - 6):                   # rolling hoops
                t += .25
            if y in (yt + 10, yb - 5):
                t -= .2
            cv.px(x, y, dpick(ramp, t, x, y))
    # 'KEROSENE' in tiny cream marks across the black band
    lx = x0 + 1
    for i, ch in enumerate("101101110110"):
        if ch == '1':
            cv.px(lx + i, yt + 3, 'bonnet1' if i % 3 else 'bonnet2')
    for i, ch in enumerate("110101011011"):
        if ch == '1':
            cv.px(lx + i, yt + 4, 'bonnet0')
    # lid seen slightly from above, bung cap
    for x in range(x0 + 1, x1):
        cv.px(x, yt - 1, 'char3' if x in (x0 + 1, x1 - 1) else 'char1')
    for x in range(x0 + 2, x1 - 1):
        cv.px(x, yt - 2, 'char3' if x < x0 + 6 else 'char2')
    cv.px(x0 + 4, yt - 2, 'steel2'); cv.px(x0 + 5, yt - 2, 'steel1'); cv.px(x0 + 4, yt - 3, 'steel3')
    cv.px(x1 - 3, yt - 1, 'steel1')
    for (x, y) in [(18, 25), (17, 25), (16, 24)]:       # paint chips at the dent
        cv.px(x, y, 'steel1')
    outline(cv, None)
    for x in range(x1 + 1, x1 + 5):                     # kerosene stain
        cv.px(x, 31, C('char1', 150))
    return cv


def p_kennel():
    cv = prop_cell()
    boards_v(cv, 6, 18, 24, 31, ['bark0', 'board1', 'board2', 'board3'])
    for x in range(6, 25):                              # weathered sill line
        cv.px(x, 31, 'board1')
    roof_plane(cv, [(3, 19), (15.5, 7), (28, 19), (25, 19), (15.5, 10), (6, 19)], ROOF)
    for k, (x, y) in enumerate(bres(3, 19, 15, 7)):
        cv.px(x, y, 'board4' if k % 2 else 'board3')
    for (x, y) in bres(16, 7, 28, 19):
        cv.px(x, y, 'board2')
    for y in range(11, 19):                             # gable boards
        for x in range(6, 25):
            if not cv.solid(x, y) and abs(x + .5 - 15.5) < (y - 9.5):
                cv.px(x, y, 'board2' if (x - 6) % 4 else 'board1')
    for y in range(21, 32):                             # arched door
        for x in range(12, 20):
            dx = x + .5 - 16
            if y >= 24 or dx * dx + (y - 24) ** 2 * 1.4 <= 16:
                cv.px(x, y, 'cave0' if y < 30 else 'khaki0')
    cv.px(13, 31, 'khaki1'); cv.px(17, 30, 'khaki1'); cv.px(18, 31, 'khaki0')
    for x in range(13, 19):                             # name board
        cv.px(x, 15, 'wood4'); cv.px(x, 16, 'wood3')
    cv.px(14, 15, 'wood1'); cv.px(16, 15, 'wood1'); cv.px(17, 15, 'wood1')
    # dented tin bowl
    for (x, y, c) in [(2, 30, 'steel2'), (3, 30, 'steel3'), (4, 30, 'steel2'), (5, 30, 'steel1'),
                      (2, 31, 'steel1'), (3, 31, 'steel1'), (4, 31, 'steel0'), (5, 31, 'steel0')]:
        cv.px(x, y, c)
    # iron stake
    for y in range(27, 32):
        cv.px(29, y, 'steel1'); cv.px(30, y, 'steel0')
    cv.px(28, 27, 'steel2'); cv.px(31, 27, 'steel1'); cv.px(29, 26, 'steel2'); cv.px(30, 26, 'steel1')
    outline(cv, None)
    # chain sagging from the doorway to the stake (drawn over, not outlined)
    pts = []
    for k in range(17):
        t = k / 16
        x = 17 + (29 - 17) * t
        y = 29 + (27 - 29) * t + math.sin(t * math.pi) * 2.4
        pts.append((int(round(x)), int(round(y))))
    for i, (x, y) in enumerate(pts):
        cv.px(x, y, 'steel2' if i % 2 else 'steel0')
        if i % 2:
            cv.px(x, y - 1, 'steel3' if i % 4 == 1 else 'steel1')
    return cv


def p_memory_stone():
    cv = prop_cell()
    rng = np.random.default_rng(1620)
    cx, cy = 16, 22
    FS = ['fstone0', 'fstone1', 'fstone2', 'fstone3', 'fstone4']
    for y in range(12, 32):
        for x in range(6, 26):
            nx = (x + .5 - cx) / 6.6
            ny = (y + .5 - 21) / 10.2
            if y >= 21:
                inside = abs(nx) <= 1.0 + (y - 28) * .05 * (y > 28)
            else:
                inside = abs(nx) ** 2.3 + abs(ny) ** 2.3 <= 1
            if inside:
                t = .58 - .38 * nx - .22 * ny + rng.uniform(-.08, .08)
                cv.px(x, y, dpick(FS, t, x, y))
    # carved spiral, softly glowing
    for y in range(14, 30):
        for x in range(8, 25):
            if cv.solid(x, y):
                d = math.hypot(x + .5 - cx, (y + .5 - cy) * 1.05)
                if d < 6.5:
                    cv.px(x, y, C(mix(cv.get(x, y), 'gold1', .35 * (1 - d / 6.5))))
    prev = None
    for k in range(70):
        th = k * .2
        r = .62 * th
        if r > 4.6:
            break
        p = (int(round(cx - .5 + r * math.cos(th))), int(round(cy - .5 + r * math.sin(th) * 1.05)))
        if p != prev:
            cv.px(p[0], p[1], 'gold2' if r < 2.2 else 'gold1')
            cv.px(p[0] + 1, p[1] + 1, 'gold0') if not cv.get(p[0] + 1, p[1] + 1)[:3] == C('gold1')[:3] else None
        prev = p
    cv.px(cx - 1, cy - 1, 'gold2'); cv.px(cx, cy - 1, 'bloom3')
    for (x, y, c) in [(9, 30, 'moss1'), (10, 31, 'moss2'), (22, 31, 'moss1'), (23, 30, 'moss2'), (11, 14, 'lichen'),
                      (12, 13, 'lichen'), (21, 17, 'moss2')]:
        cv.px(x, y, c)
    outline(cv, None)
    ground_tuft(cv, 6, 31, 3); ground_tuft(cv, 24, 31, 3)
    for y in range(4, 32):                              # soft halo
        for x in range(0, 32):
            d = math.hypot(x + .5 - cx, (y + .5 - cy) * 1.1)
            if 7 < d < 15 and (x + y) % 2 == 0 and not cv.solid(x, y):
                a = int(80 * (1 - (d - 7) / 8))
                if a > 10:
                    cv.px(x, y, C('gold1', a))
    return cv


def p_cable_drum():
    cv = prop_cell()
    cx, cy, R = 15, 20.5, 11
    WOOD = ['wood1', 'wood2', 'wood3', 'wood4']
    rng = np.random.default_rng(1630)
    jag = rng.uniform(-1, 1, 64)

    def broken(x, y, d):
        ang = math.degrees(math.atan2(y + .5 - cy, x + .5 - cx))
        k = int((ang + 180) / 360 * 63)
        return -78 < ang < -18 and d > 5.5 + jag[k] * 1.2
    # back flange (offset, dark) and cable barrel showing through the break
    for y in range(8, 32):
        for x in range(2, 30):
            d = math.hypot(x + .5 - cx, y + .5 - cy)
            db = math.hypot(x + .5 - cx - 3, y + .5 - cy + 1)
            if d <= R and broken(x, y, d):
                if d < R - 2.6:
                    cv.px(x, y, 'steel2' if int(d * 1.3) % 2 else 'steel0')
                elif db <= R:
                    cv.px(x, y, 'wood0' if (x + y) % 3 else 'wood1')
            elif db <= R and d > R:
                cv.px(x, y, 'wood1' if db < R - 1 else 'wood0')
    for y in range(8, 32):
        for x in range(2, 30):
            d = math.hypot(x + .5 - cx, y + .5 - cy)
            if d > R or broken(x, y, d):
                continue
            lit = -((x + .5 - cx) * -.6 + (y + .5 - cy) * -.8) / R
            t = .5 + .35 * lit
            c = dpick(WOOD, t, x, y)
            if (x - cx + 40) % 5 == 0:
                c = 'wood1'
            if d > R - 1.1:
                c = 'wood2' if lit < .2 else 'wood4'
            if d < 2.6:
                c = 'steel1' if d > 1.3 else 'cave0'
            cv.px(x, y, c)
    for a in (45, 135, 225, 315):                        # hub bolts
        cv.px(cx + 4.2 * math.cos(math.radians(a)) - .5, cy + 4.2 * math.sin(math.radians(a)) - .5, 'steel2')
    for y in range(8, 32):                               # splintered edge
        for x in range(2, 30):
            d = math.hypot(x + .5 - cx, y + .5 - cy)
            if d <= R and not broken(x, y, d) and any(broken(x + dx, y + dy, math.hypot(x + dx + .5 - cx, y + dy + .5 - cy))
                                                       for dx, dy in N4):
                cv.px(x, y, 'wood5' if (x + y) % 2 else 'wood3')
    # loose cable snaking to the ground, frayed end
    prev = None
    for k in range(21):
        t = k / 20
        x = (1 - t) ** 2 * 22 + 2 * (1 - t) * t * 31 + t * t * 27
        y = (1 - t) ** 2 * 14 + 2 * (1 - t) * t * 22 + t * t * 31
        p = (int(round(x)), int(round(y)))
        if prev:
            for (xx, yy) in bres(*prev, *p):
                cv.px(xx, yy, 'steel1' if (xx + yy) % 3 else 'steel3')
        prev = p
    outline(cv, None)
    for (x, y) in [(25, 31), (25, 30), (26, 29)]:
        cv.px(x, y, 'steel2')
    return cv


def p_scorch():
    cv = prop_cell()
    rng = np.random.default_rng(1640)
    cx, cy, rx, ry = 16, 28.6, 15, 3.1
    for y in range(25, 32):
        for x in range(0, 32):
            d = ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 + rng.uniform(-.12, .12)
            if d > 1:
                continue
            t = 1 - d
            if t < .3 and t / .3 < B4[y % 4, x % 4]:
                continue
            c = dpick(['char2', 'char1', 'char0'], t * 1.3, x, y)
            cv.px(x, y, c)
    for (x, y, c) in [(12, 29, 'spark0'), (13, 29, 'fire1'), (19, 28, 'spark1'), (20, 29, 'fire1'), (8, 30, 'fire0'),
                      (24, 30, 'spark0'), (16, 30, 'fire0')]:
        cv.px(x, y, c)
    for (x, y) in [(5, 28), (27, 28), (10, 27), (22, 27)]:
        cv.px(x, y, 'ash')
    return cv


# ---------------------------------------------------------------- steam shovel boss
GLYPH = {
    'M': ["1...1", "11.11", "1.1.1", "1...1", "1...1"],
    'D': ["111.", "1..1", "1..1", "1..1", "111."],
    'C': [".111", "1...", "1...", "1...", ".111"],
}


def paint_text(cv, x, y, text, col, shadow, k=2, rng=None, chip=0.0):
    for ch in text:
        g = GLYPH[ch]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v != '1':
                    continue
                for a in range(k):
                    for b in range(k):
                        X, Y = x + i * k + a, y + j * k + b
                        if rng is not None and rng.random() < chip:
                            continue
                        cv.px(X + 1, Y + 1, shadow)
                        cv.px(X, Y, col)
        x += (len(g[0]) + 1) * k


def roof_y(x):
    return 12 + int(round(((x - 48) / 44) ** 2 * 5))


def disc(cv, cx, cy, r, ramp, light=(-0.6, -0.8), base=.5, k=.45):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x + .5 - cx, y + .5 - cy
            d = math.hypot(dx, dy)
            if d <= r:
                lit = -(dx * light[0] + dy * light[1]) / max(r, .5)
                cv.px(x, y, dpick(ramp, base + k * lit, x, y))


def shovel_body(wreck=False):
    cv = Canvas(112, 80)
    rng = np.random.default_rng(SEED + 3001)
    HX0, HX1, HY0, HY1 = 10, 88, 19, 55
    # counterweight
    for y in range(40, 58):
        for x in range(3, 11):
            cv.px(x, y, dpick(IRON[1:], .6 - (y - 40) * .02 - (x - 3) * .01, x, y))
    for x in range(3, 11):
        cv.px(x, 40, 'iron4')
    # crawler track
    for y in range(62, 80):
        for x in range(4, 108):
            inl = 14 <= x + .5 <= 98 or math.hypot(x + .5 - 14, y + .5 - 71) <= 8.6 or math.hypot(x + .5 - 98, y + .5 - 71) <= 8.6
            if not inl:
                continue
            edge = (y <= 63 or y >= 78 or math.hypot(x + .5 - 14, y + .5 - 71) > 6.6 and x < 14 or
                    math.hypot(x + .5 - 98, y + .5 - 71) > 6.6 and x > 98)
            if edge:
                shoe = (x // 4) % 2
                if y >= 78:
                    c = 'iron2' if shoe else 'iron1'
                    if y == 79 and x % 4 == 0:
                        c = 'iron0'
                elif y <= 63:
                    c = 'iron3' if y == 62 and shoe else ('iron2' if shoe else 'iron1')
                else:
                    c = 'iron2' if (y // 3) % 2 else 'iron1'
            else:
                c = 'iron1' if (y - 64) % 13 > 1 else 'iron0'
            cv.px(x, y, c)
    for rx in range(26, 90, 12):                         # road rollers
        disc(cv, rx, 72.5, 3.2, IRON[1:])
        cv.px(rx - 1, 72, 'iron0')
    for (wx, sp) in ((14, 0), (98, 1)):                  # idler & drive sprocket
        disc(cv, wx, 71, 5.4, IRON[1:], base=.55)
        for a in range(0, 360, 45 if sp else 90):
            cv.px(wx + 3 * math.cos(math.radians(a)) - .5, 71 + 3 * math.sin(math.radians(a)) - .5, 'iron1')
        disc(cv, wx, 71, 1.6, ['brass0', 'brass1', 'brass2'])
    for _ in range(26):                                  # caked mud
        x, y = int(rng.integers(6, 106)), int(rng.integers(74, 80))
        if cv.solid(x, y):
            cv.px(x, y, 'dirt1' if rng.random() < .6 else 'dirt2')
    # deck / turntable
    for y in range(56, 62):
        for x in range(6, 104):
            c = 'iron2'
            if y == 56:
                c = 'iron4' if x % 7 else 'iron3'
            elif y == 57:
                c = 'iron3'
            elif y == 61:
                c = 'iron0'
            elif x % 6 == 0 and y == 59:
                c = 'iron4'
            cv.px(x, y, c)
    # house body: riveted oxide-red panels
    for y in range(HY0, HY1 + 1):
        for x in range(HX0, HX1 + 1):
            t = .66 - (y - HY0) / (HY1 - HY0) * .24 - (x - HX0) / (HX1 - HX0) * .1
            q = (x - HX0) % 13
            if q == 0:
                c = 'ox1'
            elif q == 1:
                c = 'ox3'
            else:
                c = dpick(OX[1:], t, x, y)
            if y in (HY0, HY0 + 1):
                c = 'ox3' if y == HY0 else 'ox2'
            if y >= HY1 - 2:
                c = 'ox1' if y < HY1 else 'ox0'
            if x >= HX1 - 1:
                c = 'ox1' if x == HX1 - 1 else 'ox0'
            cv.px(x, y, c)
    for sx in range(HX0, HX1 - 2, 13):
        for y in range(HY0 + 3, HY1 - 3, 3):
            cv.px(sx + 2, y, 'ox4'); cv.px(sx - 1, y, 'ox0') if sx > HX0 else None
    for x in range(HX0 + 2, HX1 - 1, 3):
        cv.px(x, HY1 - 1, 'ox3')
    # rear bay: vertical boiler with firebox
    for y in range(24, HY1 - 2):
        for x in range(12, 27):
            cv.px(x, y, 'cave1' if x < 26 else 'ox0')
    for y in range(23, HY1 - 2):
        for x in range(14, 25):
            u = (x - 14 + .5) / 11
            t = .78 - abs(u - .32) * 1.3
            if y in (28, 38, 48):
                t += .18
            cv.px(x, y, dpick(IRON[1:], t, x, y))
    for y in (28, 38, 48):
        for x in range(15, 24, 2):
            cv.px(x, y, 'iron4')
    for y in range(43, 51):                              # firebox door
        for x in range(16, 23):
            if y in (43, 50) or x in (16, 22):
                c = 'iron0'
            else:
                c = dpick(['fire0', 'fire1', 'fire2', 'fire3'], .3 + (50 - y) * .1 * (1 if x % 2 else .6), x, y)
                if x in (18, 20):
                    c = 'iron0'
            cv.px(x, y, c)
    cv.px(23, 32, 'brass2'); cv.px(23, 33, 'amber1'); cv.px(22, 33, 'brass1')  # water gauge
    # roof
    for x in range(HX0 - 3, HX1 + 4):
        yt = roof_y(x)
        for y in range(yt, HY0):
            k = y - yt
            c = 'roof3' if k == 0 else ('roof2' if k == 1 else 'roof1')
            if y == HY0 - 1:
                c = 'roof0'
            if k == 1 and x % 9 == 0:
                c = 'roof1'
            cv.px(x, y, c)
    # smokestack on the boiler
    if not wreck:
        for y in range(3, roof_y(19) + 1):
            for x in range(17, 22):
                cv.px(x, y, dpick(IRON[1:], .75 - abs(x - 18) * .25, x, y))
        for x in range(15, 24):
            cv.px(x, 1, 'iron3' if x < 19 else 'iron2'); cv.px(x, 2, 'iron1')
        for x in range(16, 23):
            cv.px(x, 0, 'iron2')
        for x in range(17, 22):
            cv.px(x, 7, 'iron4' if x < 19 else 'iron3')
    else:                                               # bent and snapped stack
        for y in range(5, roof_y(19) + 1):
            sh = 0 if y > 8 else (8 - y)
            for x in range(17, 22):
                cv.px(x - sh, y, dpick(IRON[1:], .5 - abs(x - 18) * .25, x, y))
        for (x, y) in [(10, 4), (11, 5), (13, 4), (12, 3)]:
            cv.px(x, y, 'iron0')
    # A-frame gantry and hoist sheave at the front
    for (a, b) in (((70, roof_y(70)), (82, 3)), ((88, roof_y(88)), (82, 3))):
        cv.line(a[0], a[1], b[0], b[1], 'iron2')
        cv.line(a[0] + 1, a[1], b[0] + 1, b[1], 'iron1')
    disc(cv, 82.5, 4, 2.4, IRON[2:])
    cv.px(82, 4, 'brass2')
    # side windows
    for wx in (31, 45):
        window(cv, wx, 25, 10, 9, trim=('ox0', 'ox4'))
    # cab door
    for y in range(27, HY1 - 2):
        for x in range(59, 68):
            c = 'ox2'
            if x == 59 or y == 27:
                c = 'ox4'
            elif x == 67:
                c = 'ox0'
            elif x in (61, 65) and 39 < y < 52 or y in (40, 51) and 61 <= x <= 65:
                c = 'ox1'
            cv.px(x, y, c)
    for y in range(29, 36):
        for x in range(61, 66):
            cv.px(x, y, 'glass1' if (y - 29) > (x - 61) else 'glass2')
    cv.px(66, 44, 'brass3'); cv.px(65, 44, 'brass1')
    cv.px(60, 30, 'iron3'); cv.px(60, 50, 'iron3')            # hinges
    # operator window (dark: the operator sprite is drawn into it)
    for y in range(24, 38):
        for x in range(71, 85):
            if x in (71, 84) or y in (24, 37):
                c = 'ox0' if y == 37 or x == 84 else 'ox4'
            else:
                c = 'glass0' if (x + y) % 5 else 'cave1'
            cv.px(x, y, c)
    for (x, y) in [(73, 26), (74, 26), (73, 27)]:
        cv.px(x, y, 'glass2')
    # lettering
    paint_text(cv, 29, 39, 'MDC', 'wht4', 'ox0', 2, rng if wreck else None, .3 if wreck else 0)
    # front hoist drum housing + boom-foot clevis (pivot sits on its pin)
    for y in range(44, 60):
        for x in range(89, 104):
            if x < 92 and y < 50:
                continue
            c = dpick(IRON[1:], .62 - (x - 89) * .02 - (y - 44) * .015, x, y)
            if y == 44 or x == 89:
                c = 'iron4'
            cv.px(x, y, c)
    disc(cv, 98, 53, 3.6, ['iron1', 'iron3', 'iron4'], base=.55)
    disc(cv, 98, 53, 1.4, ['iron0', 'iron1'])
    for y in range(46, 58, 3):
        cv.px(91, y, 'iron4'); cv.px(103, y, 'iron3')
    # handrail and steps
    for x in range(14, 30):
        cv.px(x, roof_y(x) - 2, 'iron3' if x % 4 else 'iron2')
    for x in (14, 21, 29):
        cv.px(x, roof_y(x) - 1, 'iron2')
    for (y, x0) in ((58, 30), (60, 28)):
        for x in range(x0, x0 + 4):
            cv.px(x, y, 'iron4' if y == 58 else 'iron3')
    if wreck:
        _wreck(cv, rng, HX0, HX1, HY0, HY1)
    outline(cv, None)
    if wreck:
        for (sx, sy, h, ph) in ((46, 12, 16, 0.0), (53, 13, 14, 1.7), (11, 4, 5, 3.0)):
            for k in range(h):
                y = sy - k
                x = sx + math.sin(k * .5 + ph) * 2 - k * .3
                rad = 1.7 + k * .3
                a = int(215 * (1 - k / (h + 3)))
                for yy in range(int(y - rad), int(y + rad + 1)):
                    for xx in range(int(x - rad), int(x + rad + 1)):
                        dd = math.hypot(xx - x, yy - y)
                        if dd > rad or not cv.inb(xx, yy) or cv.a[yy, xx, 3]:
                            continue
                        if dd < rad * .6 or (xx + yy + k) % 2 == 0:
                            c = 'smoke0' if dd < rad * .45 else ('smoke1' if xx < x else 'smoke2')
                            cv.a[yy, xx] = C(c, a)
    return cv


def _wreck(cv, rng, HX0, HX1, HY0, HY1):
    """Scorch, buckle and smash the house in place (before outlining)."""
    a = cv.a
    noise = fbm(112, 80, 6, 5, rng, 3)
    tomap = {C(c)[:3]: i for i, c in enumerate(OX)}
    for y in range(8, HY1 + 1):
        for x in range(HX0 - 3, HX1 + 4):
            px = tuple(int(v) for v in a[y, x])
            if px[3] == 0:
                continue
            if noise[y, x] > .5:
                i = tomap.get(px[:3])
                if i is not None:
                    cv.px(x, y, CHAR[max(0, min(3, i - 1))] if noise[y, x] > .62 else OX[max(0, i - 1)])
    # roof buckles in the middle and tears open
    old = a.copy()
    for x in range(36, 68):
        sag = int(round(4.5 * math.sin(math.pi * (x - 36) / 32)))
        if sag <= 0:
            continue
        for y in range(HY0 + 3, 7, -1):
            a[y, x] = old[y - sag, x] if y - sag >= 0 else 0
        for y in range(8, 8 + sag):
            if y < roof_y(x) + sag:
                a[y, x] = 0
    for (x, y) in [(51, 16), (52, 17), (52, 18), (53, 19), (53, 20), (54, 21), (50, 17), (51, 18)]:
        cv.px(x, y, 'cave0')
    for (x, y, c) in [(51, 14, 'fire2'), (52, 13, 'fire3'), (53, 14, 'fire1'), (52, 15, 'fire2'), (50, 15, 'fire1')]:
        cv.px(x, y, c)
    # smashed windows
    for wx in (31, 45):
        for y in range(25, 34):
            for x in range(wx, wx + 10):
                cv.px(x, y, 'cave0')
        for (dx, dy) in [(0, 0), (1, 0), (0, 1), (9, 0), (8, 0), (9, 8), (0, 8), (1, 8), (0, 7), (4, 0)]:
            cv.px(wx + dx, 25 + dy, 'glass2' if (dx + dy) % 2 else 'glass1')
    for y in range(25, 37):
        for x in range(72, 84):
            if (x * 7 + y * 3) % 9 == 0:
                cv.px(x, y, 'glass2')
    # door torn open: dark doorway, panel hanging from the bottom hinge
    for y in range(27, HY1 - 2):
        for x in range(59, 68):
            cv.px(x, y, 'cave0' if x > 59 else 'ox0')
    door = Canvas(9, 26)
    for y in range(26):
        for x in range(9):
            c = 'ox2' if (x * 3 + y) % 7 else 'char2'
            if x == 0 or y == 0:
                c = 'ox3'
            if x == 8 or y == 25:
                c = 'ox0'
            door.px(x, y, c)
    for y in range(2, 8):
        for x in range(2, 7):
            door.px(x, y, 'cave0' if (x + y) % 3 else 'glass2')
    im = door.image().rotate(-28, resample=Image.NEAREST, expand=True)
    dc = Canvas(im.width, im.height)
    dc.a[:] = np.array(im)
    ys, xs = np.nonzero(dc.a[..., 3])
    cv.blit(dc, 66 - xs.min(), 55 - ys.max())
    # boiler fire spilling, scattered debris on the deck
    for (x, y, c) in [(16, 51, 'fire2'), (17, 52, 'fire3'), (19, 52, 'fire2'), (21, 51, 'fire1'), (15, 52, 'fire1')]:
        cv.px(x, y, c)
    for (x, y) in [(40, 55), (41, 55), (72, 55), (80, 54), (81, 55)]:
        cv.px(x, y, 'char1')
    for x in range(100, 106):                            # thrown track shoes
        cv.px(x, 78 + (x % 2), 'iron2')
    for x in range(30, 40):
        cv.px(x, 79, (0, 0, 0, 0)) if x % 3 else None


def shovel_boom():
    cv = Canvas(16, 104)
    y0, y1 = 9, 100

    def xl(y):
        return int(round(4 - 3 * (y - y0) / (y1 - y0)))

    def xr(y):
        return 15 - xl(y)
    for y in range(y0, y1 + 1):
        cv.px(xl(y), y, 'ox3'); cv.px(xl(y) + 1, y, 'ox2')
        cv.px(xr(y) - 1, y, 'ox1'); cv.px(xr(y), y, 'ox0')
    k = 0
    for y in range(y0 + 3, y1 - 6, 7):
        ya, yb = y, y + 7
        if k % 2 == 0:
            cv.line(xl(ya) + 2, ya, xr(yb) - 2, yb, 'ox2')
        else:
            cv.line(xr(ya) - 2, ya, xl(yb) + 2, yb, 'ox1')
        if k % 2 == 0:
            for x in range(xl(ya) + 2, xr(ya) - 1):
                cv.px(x, ya, 'ox1')
        k += 1
    for y in range(y0 + 2, y1, 5):                       # rivets on the chords
        cv.px(xl(y), y, 'ox4')
    # mid saddle block (shipper shaft)
    for y in range(50, 59):
        for x in range(xl(y), xr(y) + 1):
            cv.px(x, y, 'iron2' if y not in (50, 58) else ('iron4' if y == 50 else 'iron0'))
    disc(cv, 8, 54.5, 2.2, ['iron1', 'iron3', 'iron4'])
    cv.px(7, 54, 'iron0')
    # head: cheek plates + big sheave
    for y in range(1, 13):
        for x in range(3, 13):
            if math.hypot(x + .5 - 8, y + .5 - 6) <= 6:
                cv.px(x, y, 'ox2' if x < 8 else 'ox1')
    disc(cv, 8, 6, 4.6, IRON[1:], base=.55)
    for y in range(1, 12):
        for x in range(3, 13):
            d = math.hypot(x + .5 - 8, y + .5 - 6)
            if 3.0 < d <= 3.8:
                cv.px(x, y, 'iron0')
    for a in range(0, 360, 60):
        cv.px(8 + 2 * math.cos(math.radians(a)) - .5, 6 + 2 * math.sin(math.radians(a)) - .5, 'iron2')
    disc(cv, 8, 6, 1.2, ['brass1', 'brass3'])
    # foot: flared plates and hinge pin (pivot)
    for y in range(93, 104):
        for x in range(0, 16):
            if abs(x + .5 - 8) <= 7.5 - max(0, y - 100) * 1.5:
                cv.px(x, y, dpick(OX[1:], .62 - (x / 16) * .4 - (y - 93) * .015, x, y))
    for x in range(1, 15):
        cv.px(x, 93, 'ox4')
    disc(cv, 8, 99, 3.3, ['iron1', 'iron3', 'iron4'], base=.55)
    disc(cv, 8, 99, 1.3, ['iron0', 'iron1'])
    outline(cv, None)
    return cv


def shovel_stick():
    cv = Canvas(10, 56)
    for y in range(3, 53):
        for x in range(1, 9):
            c = {1: 'ox3', 2: 'ox2', 3: 'ox2', 4: 'ox1', 5: 'ox1', 6: 'ox2', 7: 'ox1', 8: 'ox0'}[x]
            cv.px(x, y, c)
        if y % 6 == 0:
            cv.px(2, y, 'ox4'); cv.px(7, y, 'ox4')
            for x in (4, 5):
                cv.px(x, y, 'ox2')
    for y in range(10, 47, 2):                           # crowd rack teeth
        cv.px(9, y, 'iron3')
    for y in range(0, 7):
        for x in range(0, 10):
            if math.hypot(x + .5 - 5, y + .5 - 4) <= 4.2:
                cv.px(x, y, 'ox2' if x < 5 else 'ox1')
    disc(cv, 5, 3.5, 2.4, ['iron1', 'iron3', 'iron4'])
    cv.px(4, 3, 'iron0'); cv.px(5, 3, 'iron0')
    for y in range(49, 56):
        for x in range(1, 9):
            if y < 53 or abs(x + .5 - 5) < 4 - (y - 53):
                cv.px(x, y, 'iron2' if x < 5 else 'iron1')
    disc(cv, 5, 52, 1.6, ['iron0', 'iron3'])
    outline(cv, None)
    return cv


def shovel_bucket():
    cv = Canvas(34, 30)
    rng = np.random.default_rng(SEED + 3003)
    # bail lugs
    for y in range(0, 8):
        for x in range(12, 22):
            if math.hypot(x + .5 - 17, y + .5 - 3.5) <= 4.6 or y >= 4:
                cv.px(x, y, 'iron2' if x < 17 else 'iron1')
    disc(cv, 17, 3.5, 2.0, ['iron1', 'iron3', 'iron4'])
    cv.px(16, 3, 'iron0')
    for y in range(5, 25):
        f = (y - 5) / 19
        xa, xb = int(round(4 - 2 * f)), int(round(29 + 2 * f))
        for x in range(xa, xb + 1):
            u = (x - xa) / (xb - xa)
            t = .66 - u * .32 - f * .14 + rng.uniform(-.05, .05)
            c = dpick(IRON[1:], t, x, y)
            if y in (6, 7):
                c = 'iron4' if y == 6 else 'iron3'
            if y in (21, 22, 23):
                c = 'steel2' if y == 21 else ('steel1' if y == 22 else 'steel0')
            if x in (xa, xa + 1) and 8 <= y <= 20:
                c = 'iron3' if x == xa else 'iron2'
            cv.px(x, y, c)
        if y % 3 == 0 and 8 < y < 21:
            for rx in (10, 17, 24):
                cv.px(rx, y, 'iron4')
    for rx in (10, 17, 24):                              # rust weeping from the rivet lines
        for y in range(10, 20):
            if (y + rx) % 3 == 0:
                cv.px(rx, y + 1, 'rust0')
    for (x, y, n) in ((7, 9, 4), (21, 12, 3), (27, 10, 5), (13, 15, 3)):
        for k in range(n):
            cv.px(x, y + k, 'rust1' if k else 'rust2')
    for i, tx in enumerate((4, 10, 16, 22, 28)):         # teeth
        for (dy, w) in ((0, 3), (1, 3), (2, 2), (3, 2), (4, 1)):
            for dx in range(w):
                c = 'steel1' if dx == 0 else ('steel2' if dx == 1 else 'steel0')
                if dy == 4:
                    c = 'steel3'
                cv.px(tx + dx + (1 if dy >= 2 else 0) * 0, 24 + dy, c)
        cv.px(tx, 24, 'dirt2'); cv.px(tx + 2, 23, 'dirt3')
    for x in range(3, 7):                                # door latch on the back
        cv.px(x, 14, 'iron0')
    outline(cv, None)
    return cv


def sheave(cut=False):
    cv = Canvas(14, 14)
    for y in range(0, 4):                                # twin falls of cable
        cv.px(4, y, 'steel2'); cv.px(5, y, 'steel0')
        cv.px(9, y, 'steel2'); cv.px(10, y, 'steel0')
    cx, cy = 7, 6.5
    for y in range(1, 12):
        for x in range(1, 13):
            d = math.hypot(x + .5 - cx, y + .5 - cy)
            if d > 4.9:
                continue
            ang = math.degrees(math.atan2(y + .5 - cy, x + .5 - cx)) % 90
            lit = -((x + .5 - cx) * -.6 + (y + .5 - cy) * -.8) / 4.9
            if d > 3.9:
                c = 'steel3' if lit > .35 else ('steel2' if lit > -.3 else 'steel1')
            elif d > 3.0:
                c = 'steel0'
            elif d > 1.3:
                c = 'steel2' if (ang < 20 or ang > 70) else 'iron1'
            else:
                c = 'brass2' if lit > 0 else 'brass1'
            cv.px(x, y, c)
    cv.px(6, 6, 'brass3')
    for x in range(4, 11):                               # yoke
        cv.px(x, 11, 'iron3' if x < 7 else 'iron2')
    for (x, y, c) in [(7, 12, 'steel2'), (6, 12, 'steel1'), (8, 13, 'steel2'), (7, 13, 'steel3'), (9, 12, 'steel1'),
                      (9, 11, 'steel2')]:
        cv.px(x, y, c)
    if cut:
        im = cv.image().rotate(-35, resample=Image.NEAREST, center=(7, 7))
        cv.a[:] = np.array(im)
        for y in range(0, 4):                            # cable snapped: frayed stub
            for x in range(0, 14):
                if y < 2 or x < 6:
                    cv.a[y, x] = 0
        for (x, y, c) in [(10, 1, 'steel2'), (11, 0, 'steel1'), (9, 0, 'steel2'), (12, 1, 'steel1'), (8, 1, 'steel1')]:
            cv.px(x, y, c)
    outline(cv, None)
    if cut:
        for (x, y, c) in [(3, 2, 'spark1'), (2, 1, 'spark0'), (4, 1, 'spark0'), (3, 3, 'spark0'), (13, 3, 'spark1'),
                          (13, 5, 'spark0'), (1, 6, 'spark1'), (12, 0, 'spark0'), (2, 4, 'spark1'), (0, 2, 'spark0')]:
            cv.px(x, y, c)
    return cv


OPERATOR = [
    "..cCCC....",
    ".cCCCCCCC.",
    "..hSsSs...",
    "..hSSkS...",
    "..hSSSSs..",
    "...sSS....",
    ".wWOWWOw..",
    ".wOOOOOWWl",
    "..OoOOO.Rl",
    "..OOOOO..l",
    "..OOoOO..l",
    "..OOOOO..l",
]
OP_KEY = {'c': 'cap0', 'C': 'cap1', 'h': 'hair0', 'S': 'skin1', 's': 'skin0', 'k': 'ink', 'w': 'shirtw0',
          'W': 'shirtw1', 'O': 'over1', 'o': 'over2', 'R': 'skin1', 'l': 'steel1'}


def shovel_operator():
    cv = Canvas(10, 12)
    amap(cv, 0, 0, OPERATOR, OP_KEY)
    cv.px(9, 6, 'rod_r')
    cv.px(3, 0, 'cap2'); cv.px(4, 0, 'cap2')
    outline(cv, None)
    return cv


def build_boss_shovel():
    pieces = [
        ('body', shovel_body(False), (98, 53)),
        ('body_wreck', shovel_body(True), (98, 53)),
        ('boom', shovel_boom(), (8, 99)),
        ('stick', shovel_stick(), (5, 3)),
        ('bucket', shovel_bucket(), (17, 3)),
        ('cable_ok', sheave(False), (7, 7)),
        ('cable_cut', sheave(True), (7, 7)),
        ('operator', shovel_operator(), (5, 6)),
    ]
    x, meta = 0, {}
    for name, cv, pv in pieces:
        meta[name] = {'rect': [x, 0, cv.w, cv.h], 'pivot': [pv[0], pv[1]]}
        x += cv.w + 2
    W, H = x - 2, max(cv.h for _, cv, _ in pieces)
    sheet = Canvas(W, H)
    for name, cv, pv in pieces:
        rx, ry, w, h = meta[name]['rect']
        sheet.a[ry:ry + h, rx:rx + w] = cv.a
    sheet.save('boss_shovel.png')
    with open(os.path.join(OUT, 'boss_shovel.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    # assembled demo for the preview sheet: boom raised, dipper hanging
    P = {n: (cv, pv) for n, cv, pv in pieces}
    demo = Image.new('RGBA', (372, 200), (0, 0, 0, 0))

    def place(name, tx, ty, ang=0.0):
        cv, (px_, py_) = P[name]
        layer = Image.new('RGBA', demo.size, (0, 0, 0, 0))
        layer.paste(cv.image(), (int(tx - px_), int(ty - py_)))
        if ang:
            layer = layer.rotate(ang, resample=Image.NEAREST, center=(tx, ty))
        demo.alpha_composite(layer)
    bx, by = 6, 116
    fx, fy = bx + 98, by + 53
    ang = -40
    tip = (fx + 93 * math.sin(math.radians(-ang)), fy - 93 * math.cos(math.radians(-ang)))
    mid = (fx + 45 * math.sin(math.radians(-ang)), fy - 45 * math.cos(math.radians(-ang)))
    place('body', bx + 98, by + 53)
    place('operator', bx + 78, by + 31)
    place('boom', fx, fy, ang)
    sx, sy = mid
    place('stick', sx, sy, 50)
    bxx = sx + 49 * math.sin(math.radians(50))
    byy = sy + 49 * math.cos(math.radians(50))
    place('bucket', bxx, byy, 0)
    d = ImageDraw.Draw(demo)
    d.line([tip, (bxx, byy - 2)], fill=C('steel1'))
    d.line([(bx + 82, by + 4), tip], fill=C('steel0'))
    place('cable_ok', bxx + 1, byy - 9)
    place('body_wreck', 258 + 98, by + 53)
    sheet_demo = Canvas(372, 200)
    sheet_demo.a[:] = np.array(demo)
    return sheet, sheet_demo


# ============================================================================
# EXPANSION ART 2: trestle deck + living-root tiles (tiles rows 12-13), diver +
# houndmaster (people rows 8-9), props row 3, and the locomotive boss
# (boss_train.png/.json). Every drawing makes its own seeded RNG and is only
# appended after the existing rows, so nothing above changes.
# ============================================================================
CRE = ['cre0', 'cre1', 'cre2', 'cre3', 'cre4']
LR = ['lr0', 'lr1', 'lr2', 'lr3', 'lr4', 'lr5']
COP = ['cop0', 'cop1', 'cop2', 'cop3', 'cop4']
CNV = ('cnv0', 'cnv1', 'cnv2')
WAX = ('wax0', 'wax1', 'wax2')
SMK = ['smk0', 'smk1', 'smk2', 'smk3']
RED = ['red0', 'red1', 'red2', 'red3', 'red4']

GLYPH3 = {
    'B': ["11.", "1.1", "11.", "1.1", "11."],
    '&': [".1...", "1.1..", ".1...", "1.1.1", ".1.1."],
    'A': [".1.", "1.1", "111", "1.1", "1.1"],
    'D': ["11.", "1.1", "1.1", "1.1", "11."],
    'N': ["1..1", "11.1", "1.11", "1..1", "1..1"],
    'G': [".11", "1..", "1.1", "1.1", ".11"],
    'E': ["111", "1..", "11.", "1..", "111"],
    'R': ["11.", "1.1", "11.", "1.1", "1.1"],
}


def text_w(text):
    return sum(len(GLYPH3[ch][0]) + 1 for ch in text) - 1


def stencil(cv, x, y, text, col, shadow=None, rng=None, chip=0.0, col2=None):
    """Tiny 5px-high lettering; col2 (if given) lights the top row of every glyph."""
    for ch in text:
        g = GLYPH3[ch]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v != '1':
                    continue
                if rng is not None and rng.random() < chip:
                    continue
                if shadow:
                    cv.px(x + i + 1, y + j + 1, shadow)
                cv.px(x + i, y + j, col2 if (col2 and j == 0) else col)
        x += len(g[0]) + 1


def wrapd16(v):
    return (v + 8.0) % 16.0 - 8.0


def qpick(ramp, t, x, y):
    """Like dpick but only dithers near the middle of each band: cleaner, flatter shading."""
    t = min(max(t, 0.0), 1.0) * (len(ramp) - 1)
    i = int(t)
    if i >= len(ramp) - 1:
        return C(ramp[-1])
    f = t - i
    if f < .3:
        return C(ramp[i])
    if f > .7:
        return C(ramp[i + 1])
    return C(ramp[i + 1]) if (f - .3) / .4 > B4[y % 4, x % 4] else C(ramp[i])


# ---------------------------------------------------------------- tiles row 12: trestle deck
def trestle_deck_tiles():
    gr = fbm(T, T, 2, 8, np.random.default_rng(1700), 2)      # periodic grain field
    tiles = []
    for v in range(4):
        r = np.random.default_rng(1710 + v)
        cv = Canvas(T, T)
        # stringer: a thick creosoted timber, lit from above, grain running along it
        for y in range(4, T):
            for x in range(T):
                if y == 4:
                    c = 'cre5' if (x * 5 + 3) % 7 == 0 else 'cre4'
                elif y == 5:
                    c = 'cre3'
                elif y == 14:
                    c = 'cre1'
                elif y == 15:
                    c = 'cre0'
                else:
                    t = .5 - (y - 6) * .035 + (gr[y, x] - .5) * .3
                    if (y * 5 + int(gr[y, x] * 7)) % 4 == 0:
                        t -= .16
                    c = qpick(CRE, t, x, y)
                cv.px(x, y, c)
        # rail head + tie ends along the top 4px (period 8 -> seamless)
        for x in range(T):
            m = x % 8
            cv.px(x, 0, 'steel3' if m in (2, 3) else 'steel2')
            cv.px(x, 1, 'steel1')
            if m <= 4:
                cv.px(x, 2, 'cre5' if m == 0 else ('cre4' if m < 4 else 'cre3'))
                cv.px(x, 3, 'cre3' if m == 0 else ('cre2' if m < 4 else 'cre1'))
            else:
                cv.px(x, 2, 'iron1')
                cv.px(x, 3, 'cre0')
        for x in (2, 10):
            cv.px(x, 2, 'steel1')                                # spike heads on the tie plates

        def plate(x0, y0, w, h, bolts):
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    c = 'iron2'
                    if x == x0 or y == y0:
                        c = 'iron3'
                    if x == x0 + w - 1 or y == y0 + h - 1:
                        c = 'iron1'
                    cv.px(x, y, c)
            for (bx, by) in bolts:
                cv.px(bx, by, 'steel2'); cv.px(bx + 1, by, 'iron0'); cv.px(bx, by + 1, 'iron1')
            for x in range(x0 + 1, x0 + w + 1):                 # cast shadow on the timber
                cv.px(x, y0 + h, 'cre0')
            for y in range(y0 + 1, y0 + h):
                cv.px(x0 + w, y, 'cre1')
        if v == 0:
            plate(9, 7, 4, 5, [(10, 8), (10, 10)])
            cv.px(4, 9, 'cre1'); cv.px(5, 9, 'cre1'); cv.px(4, 10, 'cre4')   # knot
        if v == 1:
            plate(3, 7, 4, 5, [(4, 8), (4, 10)])
            for x in range(8, 15):                               # long seasoning check
                cv.px(x, 11 + (x > 11), 'cre0')
                cv.px(x, 12 + (x > 11), 'cre4' if x % 2 else 'cre3')
        if v == 2:                                              # splice with a fishplate
            plate(4, 6, 9, 7, [(5, 7), (5, 10), (10, 7), (10, 10)])
            for y in range(4, 6):
                cv.px(8, y, 'cre0')
            for y in range(13, 15):
                cv.px(8, y, 'cre0'); cv.px(9, y, 'cre3')
        if v == 3:
            plate(9, 7, 4, 5, [(10, 8), (10, 10)])
            for k, y in enumerate(range(12, 15)):              # rust bleeding from the bolts
                cv.px(10, y, 'rust1' if k == 0 else 'rust0')
                if k < 2:
                    cv.px(11, y + 1, 'rust0')
            for (x, y) in [(3, 6), (3, 7), (3, 8), (2, 8), (3, 9)]:   # creosote run, wet glint
                cv.px(x, y, 'cre0' if y > 6 else 'cre1')
            cv.px(4, 7, 'cre5')
            kx = 13 + int(r.integers(0, 2))                          # knot
            cv.px(kx, 10, 'cre1'); cv.px(kx - 1, 10, 'cre1'); cv.px(kx, 11, 'cre4')
        tiles.append(cv)
    return tiles


# ---------------------------------------------------------------- tiles row 13: living root
ROOT_STRANDS = [  # (axis, centre, amplitude, phase, radius)  -- period 16 both ways
    ('h', 4.0, 1.5, 0.0, 1.9),
    ('h', 11.5, 1.2, 2.6, 1.3),
    ('v', 3.5, 1.4, 1.0, 1.6),
    ('v', 11.0, 1.5, 4.0, 1.15),
]


def _strand_d(s, x, y):
    """Signed perpendicular distance (px) from pixel centre to strand s, and along-axis coord."""
    ax, c0, A, ph, rad = s
    if ax == 'h':
        u, w = x + .5, y + .5
    else:
        u, w = y + .5, x + .5
    ang = 2 * math.pi * u / 16 + ph
    c = c0 + A * math.sin(ang)
    slope = A * 2 * math.pi / 16 * math.cos(ang)
    return wrapd16(w - c) / math.sqrt(1 + slope * slope), u


def living_root_tiles():
    b = rock_base(np.random.default_rng(1720), 6, 5.0)
    stone, crack = render_chunks(b, b['tone'] * .5, ['cave0', 'cave1', 'cave2', 'cave3'], 'cave0',
                                 base=0.42, hl=0.34, noise=0.10)
    D = np.zeros((len(ROOT_STRANDS), T, T))
    U = np.zeros((len(ROOT_STRANDS), T, T))
    for k, s in enumerate(ROOT_STRANDS):
        for y in range(T):
            for x in range(T):
                D[k, y, x], U[k, y, x] = _strand_d(s, x, y)
    R_ = np.array([s[4] for s in ROOT_STRANDS])
    H_ = [0, 1]
    V_ = [2, 3]

    def on_top(i, j):          # weave: alternate over/under at each crossing
        hi, vj = (i, j) if i in H_ else (j, i)
        h_over = (H_.index(hi) + V_.index(vj)) % 2 == 0
        return hi if h_over else vj
    base = Canvas(T, T)
    base.a[:] = stone
    owner = -np.ones((T, T), int)
    for y in range(T):
        for x in range(T):
            ins = [k for k in range(len(R_)) if abs(D[k, y, x]) <= R_[k]]
            if not ins:
                near = [k for k in range(len(R_)) if abs(D[k, y, x]) <= R_[k] + .9]
                if near:
                    base.px(x, y, 'lr0')                     # sinew rim / contact shadow
                continue
            top = ins[0]
            for k in ins[1:]:
                top = on_top(top, k) if (top in H_) != (k in H_) else top
            owner[y, x] = top
            dn = D[top, y, x] / R_[top]
            t = .6 - .48 * dn
            if abs(dn) < .7 and ((U[top, y, x] + 2.2 * D[top, y, x]) % 5.0) < .9:   # twisted fibres
                t -= .16
            for k in range(len(R_)):                         # shadowed where it dives under
                if k == top or (top in H_) == (k in H_):
                    continue
                if on_top(top, k) == k and abs(D[k, y, x]) <= R_[k] + 1.3:
                    t -= .32
            base.px(x, y, qpick(LR, t, x, y))
    tiles = []
    for v in range(4):
        cv = Canvas(T, T)
        cv.a[:] = base.a
        # gold veins: interior segments along the centre lines (same in every variant so
        # edges stay seamless), plus a faint glow bleeding into the nearby stone
        veins = []
        for k, segs in ((0, [(2, 6), (10, 13)]), (3, [(5, 9)])):
            for (a0, a1) in segs:
                for a in range(a0, a1 + 1):
                    for w in range(T):
                        if ROOT_STRANDS[k][0] == 'h':
                            x, y = a, w
                        else:
                            x, y = w, a
                        if owner[y, x] == k and abs(D[k, y, x]) < .5:
                            veins.append((x, y))
        for (x, y) in veins:
            for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                X, Y = x + dx, y + dy
                if 0 <= X < T and 0 <= Y < T and owner[Y, X] < 0:
                    cv.a[Y, X] = mix(tuple(int(c) for c in cv.a[Y, X]), 'gold0', .35)
        for i, (x, y) in enumerate(veins):
            cv.px(x, y, 'gold2' if (x * 3 + y * 5 + v) % 5 == 0 else 'gold1')

        def knuckle(x0, y0, rr=1.8):
            for y in range(int(y0 - rr - 1), int(y0 + rr + 2)):
                for x in range(int(x0 - rr - 1), int(x0 + rr + 2)):
                    dx, dy = x + .5 - x0, y + .5 - y0
                    d = math.hypot(dx, dy)
                    if d <= rr:
                        lit = -(dx * .6 + dy * .8) / rr
                        cv.px(x, y, qpick(['lr1', 'lr3', 'bone_dk', 'bone'], .42 + .55 * lit, x, y))
                    elif d <= rr + .9 and 0 <= x < T and 0 <= y < T and owner[y, x] < 0:
                        cv.px(x, y, 'lr0')

        def fangs(x0, y0, n):
            """A slit of gum in the stone with thin fangs standing out of it."""
            for i in range(2 * n + 1):
                cv.px(x0 - 1 + i, y0 + 1, 'lr0')
                cv.px(x0 - 1 + i, y0 + 2, 'flesh1' if 0 < i < 2 * n else 'lr1')
            for i in range(n):
                x = x0 + 2 * i
                cv.px(x, y0, 'bone')
                cv.px(x, y0 + 1, 'bone_dk')
                if i % 2 == 0:
                    cv.px(x, y0 - 1, 'bone')

        def pore(x0, y0):
            for (dx, dy) in N4:
                cv.px(x0 + dx, y0 + dy, 'gold1')
            cv.px(x0, y0, 'gold2')
            for (dx, dy) in [(-1, -1), (1, 1), (1, -1), (-1, 1)]:
                cv.px(x0 + dx, y0 + dy, 'lr1')
        if v == 0:
            knuckle(8.0, 4.0 + 1.5 * math.sin(2 * math.pi * 8.0 / 16) - .3)
            fangs(6, 8, 3)
        if v == 1:
            pore(7, 8)
            knuckle(11.2, 12.4, 1.4)
        if v == 2:
            knuckle(7.0, 3.6, 1.6)
            knuckle(10.4, 9.0, 1.5)
            for (x, y, c) in [(6, 13, 'flesh2'), (6, 14, 'flesh3'), (6, 15, 'flesh1')]:   # weeping drip
                cv.px(x, y, c)
        if v == 3:
            fangs(6, 8, 2)
            pore(12, 14)
        tiles.append(cv)
    return tiles


# ---------------------------------------------------------------- people row 8: hard-hat diver
def dv_leg(cv, hip, knee, ankle, back):
    c = ('cnv0', 'cnv0') if back else ('cnv2', 'cnv1')
    for a, b in ((hip, knee), (knee, ankle)):
        for (x, y) in bres(*a, *b):
            cv.px(x, y, c[0]); cv.px(x + 1, y, c[1])
    ax, ay = ankle
    # lead-soled boots with brass toe caps (one size bigger than a work boot)
    lo = ('iron1', 'iron0', 'iron1', 'brass1') if back else ('iron3', 'iron2', 'iron1', 'brass2')
    cv.px(ax - 1, ay, lo[1]); cv.px(ax, ay, lo[0]); cv.px(ax + 1, ay, lo[1])
    cv.px(ax - 1, ay + 1, lo[1]); cv.px(ax, ay + 1, lo[0]); cv.px(ax + 1, ay + 1, lo[1]); cv.px(ax + 2, ay + 1, lo[3])
    cv.px(ax - 1, ay + 2, lo[2]); cv.px(ax, ay + 2, lo[2]); cv.px(ax + 1, ay + 2, lo[2]); cv.px(ax + 2, ay + 2, lo[3])


def dv_torso(cv, x0, y0):
    for yr in range(7):
        for xr in range(6):
            c = 'cnv1'
            if xr == 0:
                c = 'cnv0'
            elif xr in (1, 2) and yr in (2, 3):
                c = 'cnv2'
            cv.px(x0 + xr, y0 + yr, c)
    # corselet (copper breastplate) over the shoulders, studded with brass wing nuts
    for xr in range(-1, 7):
        cv.px(x0 + xr, y0, 'cop2' if 0 < xr < 4 else 'cop1')
        cv.px(x0 + xr, y0 + 1, 'cop0' if xr in (-1, 6) else 'cop1')
    for xr in (0, 2, 4):
        cv.px(x0 + xr, y0 + 1, 'brass2')
    # lead chest weight + weight belt
    for yr in range(2, 5):
        cv.px(x0 + 4, y0 + yr, 'iron3' if yr == 2 else 'iron2')
        cv.px(x0 + 5, y0 + yr, 'iron2' if yr == 2 else 'iron1')
    for xr in range(-1, 7):
        cv.px(x0 + xr, y0 + 6, 'lea1' if xr % 3 else 'iron2')
    cv.px(x0 + 4, y0 + 6, 'brass2')


def dv_helmet(cv, cx, cy):
    """Round Mark V-style helmet; faceplate on the right (facing right)."""
    for y in range(int(cy - 5), int(cy + 5)):
        for x in range(int(cx - 5), int(cx + 6)):
            dx, dy = x + .5 - cx, (y + .5 - cy) * 1.05
            d = math.hypot(dx, dy)
            if d <= 4.6:
                lit = -(dx * .6 + dy * .8) / 4.6
                cv.px(x, y, qpick(COP, .5 + .55 * lit, x, y))
    # neck ring: dark gasket with bolt heads
    for x in range(int(cx - 4), int(cx + 4)):
        cv.px(x, cy + 4, 'brass2' if x % 2 else 'iron1')
    # front faceplate: brass ring round a faintly glowing pane
    fx, fy = int(cx + 2), int(cy)
    for (dx, dy, c) in [(0, -1, 'brass2'), (1, -1, 'brass3'), (2, 0, 'brass1'), (2, 1, 'brass1'),
                        (-1, 0, 'brass2'), (-1, 1, 'brass1'), (0, 2, 'brass0'), (1, 2, 'brass0'),
                        (0, 0, 'glow2'), (1, 0, 'glow1'), (0, 1, 'glow1'), (1, 1, 'glow0')]:
        cv.px(fx + dx, fy + dy, c)
    cv.px(int(cx - 1), int(cy - 4), 'cop4')                    # top glint
    cv.px(int(cx - 3), int(cy + 1), 'brass2')                  # side port rim
    cv.px(int(cx - 3), int(cy + 2), 'glass1')


def dv_gun(cv, a, b, fired=False):
    """Harpoon gun from stock a to muzzle b (roughly horizontal)."""
    pts = bres(*a, *b)
    for i, (x, y) in enumerate(pts):
        if i < 3:
            cv.px(x, y, 'wood3'); cv.px(x, y + 1, 'wood2' if i else 'wood1')
        else:
            cv.px(x, y, 'steel1' if i % 2 else 'steel2')
            cv.px(x, y + 1, 'steel0')
    gx, gy = pts[2]
    cv.px(gx, gy + 2, 'wood1')                                 # pistol grip
    bx, by = b
    if not fired:                                              # spear head + barb
        cv.px(bx + 1, by, 'steel3'); cv.px(bx, by - 1, 'steel2'); cv.px(bx - 1, by - 1, 'steel1')


def draw_diver(ci):
    P = WALK[ci] if ci < 4 else [IDLE, STARTLED, GRABBED, None][ci - 4]
    attack = ci == 7
    if attack:
        P = dict(bob=0, legs=WIDE, arms=[((6, 11), (8, 11)), ((9, 11), (10, 11))])
    hold = ci not in (5, 6)
    cv = Canvas(16, 24)
    b = P.get('bob', 0)
    top, hipy = 10 + b, 16 + b
    (bk, ba), (fk, fa) = P['legs']
    (be, bh), (fe, fh) = P['arms']

    def up(p):
        return (p[0], p[1] + b)
    hdx, hdy = P.get('hdx', 0), P.get('hdy', 0)
    hcx, hcy = 8.0 + hdx, 5.0 + b + hdy
    # air hose stub leaving the back of the helmet (the game draws the long hose from its end)
    hx0, hy0 = int(hcx - 4), int(hcy + 1)
    for (dx, dy, c) in [(0, 0, 'brass2'), (-1, 0, 'brass1'), (-2, 1, 'char2'), (-2, 2, 'char1'), (-3, 2, 'char2'),
                        (-3, 3, 'char1'), (-3, 4, 'char2'), (-2, 3, 'char0')]:
        cv.px(hx0 + dx, hy0 + dy, c)
    bn_arm(cv, up((7, 11)), up(be), up(bh), CNV, back=True)
    dv_leg(cv, (6, hipy), bk, ba, back=True)
    dv_torso(cv, 5, top)
    dv_leg(cv, (8, hipy), fk, fa, back=False)
    dv_helmet(cv, hcx, hcy)
    if hold:
        if attack:
            a, m = (4, 10), (13, 10)
            fe2, fh2 = (9, 12), (10, 11)
        else:
            a, m = up((4, 15)), up((13, 14))
            fe2, fh2 = up((9, 13)), up((10, 15))
        dv_gun(cv, a, m, fired=attack)
        bn_arm(cv, up((9, 11)) if not attack else (9, 11), fe2, fh2, CNV, back=False)
    else:
        bn_arm(cv, up((9, 11)), up(fe), up(fh), CNV, back=False)
    if P.get('rot'):
        im = cv.image().rotate(P['rot'], resample=Image.NEAREST, center=(8, 14))
        cv.a[:] = np.array(im)
    outline(cv, 'ink')
    if not P.get('rot'):                                       # faint faceplate glow
        fx, fy = int(hcx + 2), int(hcy)
        for (x, y) in [(fx + 3, fy), (fx + 3, fy + 1)]:
            if cv.get(x, y)[3] == 0:
                cv.px(x, y, C('glow1', 80))
    if attack:                                                 # muzzle puff (bubbles + powder smoke)
        for (x, y, c) in [(14, 10, 'foam'), (15, 10, C('smk3', 220)), (14, 9, C('smk2', 200)),
                          (15, 9, C('foam', 170)), (15, 11, C('smk2', 180)), (14, 11, C('smk3', 140)),
                          (15, 8, C('water_hi', 150)), (13, 8, C('foam', 120))]:
            cv.px(x, y, c)
    return cv


# ---------------------------------------------------------------- people row 9: houndmaster
HM = dict(hair='hair1', hat='flat', hatc=('fed0', 'fed1', 'fed2'))


def hm_leg(cv, hip, knee, ankle, back):
    th = ('fed0', 'fed0') if back else ('fed2', 'fed1')
    bt = ('lea0', 'lea0') if back else ('lea2', 'lea1')
    for (x, y) in bres(*hip, *knee):
        cv.px(x, y, th[0]); cv.px(x + 1, y, th[1])
    for i, (x, y) in enumerate(bres(*knee, *ankle)):       # tall laced field boots
        cv.px(x, y, bt[0]); cv.px(x + 1, y, bt[1])
        if i == 0 and not back:
            cv.px(x, y, 'lea3')
    ax, ay = ankle
    bc = ('boot0', 'boot0', 'boot1') if back else ('boot1', 'boot2', 'boot1')
    cv.px(ax, ay + 1, bc[1]); cv.px(ax + 1, ay + 1, bc[0])
    cv.px(ax, ay + 2, bc[2]); cv.px(ax + 1, ay + 2, bc[0]); cv.px(ax + 2, ay + 2, bc[2])


def hm_torso(cv, x0, y0, whistle=True):
    for yr in range(7):
        for xr in range(4):
            c = 'wax1'
            if xr == 0:
                c = 'wax0'
            elif xr == 1 and yr in (1, 2, 3):
                c = 'wax2'
            elif yr == 0 and xr >= 2:
                c = 'wax3'
            if xr == 3 and 1 <= yr <= 5:
                c = 'wax0' if yr % 2 else 'wax1'                 # coat front / buttons
            cv.px(x0 + xr, y0 + yr, c)
    cv.px(x0 + 2, y0, 'fed2'); cv.px(x0 + 3, y0, 'fed1')          # corduroy collar
    for xr in range(4):
        cv.px(x0 + xr, y0 + 6, 'lea0' if xr != 2 else 'brass2')   # belt
    if whistle:                                                   # whistle on a lanyard
        cv.px(x0 + 3, y0 + 1, 'bonnet1'); cv.px(x0 + 3, y0 + 2, 'bonnet1')
        cv.px(x0 + 4, y0 + 3, 'brass3'); cv.px(x0 + 3, y0 + 3, 'brass1')


def hm_coat(cv, x0, hipy, sway):
    for k in range(4):
        s = sway if k >= 2 else 0
        for xr in range(-1 + s, 5 + s):
            c = 'wax1'
            if xr <= s:
                c = 'wax0'
            if k == 0 and xr == 1:
                c = 'wax2'
            if k == 3:
                c = 'wax0' if xr % 2 else 'wax1'
            if xr == 3 + s and k >= 1:
                c = 'wax0'                                         # front vent
            cv.px(x0 + xr, hipy + k, c)


def hm_whip_coil(cv, x, y):
    for (dx, dy, c) in [(0, 0, 'lea2'), (1, 0, 'lea1'), (-1, 1, 'lea2'), (2, 1, 'lea0'), (-1, 2, 'lea1'),
                        (2, 2, 'lea0'), (0, 3, 'lea1'), (1, 3, 'lea0'), (0, 1, 'lea3')]:
        cv.px(x + dx, y + dy, c)


def draw_houndmaster(ci):
    P = WALK[ci] if ci < 4 else [IDLE, STARTLED, GRABBED, None][ci - 4]
    attack = ci == 7
    whistle_up = ci == 5
    if attack:
        P = dict(bob=0, legs=WIDE, arms=[((6, 12), (4, 13)), ((10, 10), (11, 10))], mouth='open')
    if whistle_up:
        P = dict(bob=-1, legs=[((6, 18), (5, 21)), ((9, 18), (10, 21))], arms=[((5, 8), (4, 5)), ((11, 12), (10, 9))],
                 eyes='wide')
    cv = Canvas(16, 24)
    b = P.get('bob', 0)
    top, hipy = 9 + b, 16 + b
    (bk, ba), (fk, fa) = P['legs']
    (be, bh), (fe, fh) = P['arms']

    def up(p):
        return (p[0], p[1] + b)
    hm_whip_coil(cv, 5, hipy - 1)
    bn_arm(cv, up((7, 10)), up(be), up(bh), WAX, back=True)
    hm_leg(cv, (6, hipy), bk, ba, back=True)
    hm_torso(cv, 6, top, whistle=not whistle_up)
    hm_leg(cv, (8, hipy), fk, fa, back=False)
    sway = 1 if fa[0] > 9 else (-1 if fa[0] < 7 else 0)
    hm_coat(cv, 6, hipy, sway)
    hdx, hdy = P.get('hdx', 0), P.get('hdy', 0)
    x0, y0 = 6 + hdx, 4 + b + hdy
    p_head(cv, x0, y0, HM, P)
    cv.px(x0 + 4, y0 + 3, 'hair0'); cv.px(x0 + 3, y0 + 3, 'hair1')   # moustache
    cv.px(x0 + 1, y0 + 3, 'hair1')                                   # sideburn
    bn_arm(cv, up((8, 10)), up(fe), up(fh), WAX, back=False)
    if whistle_up:                                                   # whistle to mouth
        cv.px(x0 + 5, y0 + 3, 'brass3'); cv.px(x0 + 6, y0 + 3, 'brass1')
        cv.px(x0 + 4, y0 + 3, 'brass2')
        cv.px(x0 + 4, y0 + 4, 'bonnet1')
    if attack:                                                       # whip stock in the fist
        hx, hy = up(fh)
        cv.px(hx + 2, hy - 1, 'lea3'); cv.px(hx + 3, hy - 1, 'lea2')
    if P.get('rot'):
        im = cv.image().rotate(P['rot'], resample=Image.NEAREST, center=(8, 14))
        cv.a[:] = np.array(im)
    outline(cv, 'ink')
    if attack:                                                       # lash snapping out ahead, crack at the tip
        hx, hy = up(fh)
        for (x, y, c) in [(14, hy - 2, 'lea1'), (15, hy - 2, 'lea0'), (15, hy - 3, C('spark1', 230)),
                          (14, hy - 4, C('foam', 170)), (15, hy - 1, C('spark0', 170)), (13, hy - 4, C('foam', 90))]:
            cv.px(x, y, c)
    if whistle_up:                                                   # shrill notes
        for (x, y, a) in [(14, y0 + 1, 200), (15, y0, 160), (14, y0 + 5, 160), (15, y0 + 6, 120)]:
            cv.px(x, y, C('wht5', a))
    return cv


# ---------------------------------------------------------------- props row 3
def p_water_tower():
    cv = prop_cell()
    # legs (back pair darker), sway rods
    for (a, bb, back) in [((12, 17), (11, 29), True), ((19, 17), (20, 29), True),
                          ((9, 17), (6, 29), False), ((22, 17), (25, 29), False)]:
        for (x, y) in bres(*a, *bb):
            if back:
                cv.px(x, y, 'cre1'); cv.px(x + 1, y, 'cre0')
            else:
                cv.px(x, y, 'cre4'); cv.px(x + 1, y, 'cre2')
    for (p0, p1) in [((8, 19), (23, 28)), ((23, 19), (8, 28))]:
        for (x, y) in bres(*p0, *p1):
            cv.px(x, y, 'steel0')
    for x in range(8, 24):
        cv.px(x, 23, 'cre3' if x % 3 else 'cre2'); cv.px(x, 24, 'cre1')
    for (x0, x1) in [(5, 9), (23, 27)]:                                 # stone footings
        for x in range(x0, x1):
            cv.px(x, 30, 'fstone3' if x == x0 else 'fstone2'); cv.px(x, 31, 'fstone1')
    # tank: vertical staves on a barrel, iron hoops
    for y in range(7, 18):
        for x in range(6, 26):
            u = (x - 6 + .5) / 20
            t = .78 - abs(u - .3) * 1.4
            if (x - 6) % 3 == 2:
                t -= .18
            ramp = ['wood1', 'wood2', 'wood3', 'wood4', 'wood5']
            if y in (9, 13, 16):
                ramp = ['iron1', 'iron2', 'iron3', 'iron4']
            cv.px(x, y, dpick(ramp, t, x, y))
    for x in range(6, 26):
        cv.px(x, 17, 'wood1')
    # conical roof with a finial
    m = cv.poly([(15.5, 1.5), (16.5, 1.5), (27, 7.5), (5, 7.5)], 'roof2')
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        t = .75 - (x - 5) / 22 * .7 + (.1 if (x + y) % 3 == 0 else 0)
        cv.a[y, x] = C(dpick(ROOF, t, x, y))
    for x in range(5, 27):
        cv.px(x, 7, 'roof0' if x % 2 else 'roof1')
    cv.px(15, 0, 'iron3'); cv.px(16, 0, 'iron2'); cv.px(15, 1, 'iron3')
    # spout: hinged canvas pipe with a counterweight chain
    for i, (x, y) in enumerate(bres(25, 13, 30, 18)):
        cv.px(x, y, 'iron3'); cv.px(x, y + 1, 'iron1')
    cv.px(30, 20, 'iron2'); cv.px(31, 20, 'iron1')
    for y in range(8, 13):
        cv.px(28, y, 'steel1' if y % 2 else 'steel0')
    # ladder on the right leg
    for y in range(18, 29, 2):
        cv.px(23 + (y - 17) * 3 // 12 - 1, y, 'cre4')
    outline(cv, None)
    for (x, y, a) in [(30, 22, 200), (30, 25, 150), (30, 28, 110)]:      # drip
        cv.px(x, y, C('water_hi', a))
    return cv


def p_signal():
    cv = prop_cell()
    for x in range(11, 21):                                             # concrete base
        cv.px(x, 29, 'conc3' if x < 14 else 'conc2'); cv.px(x, 30, 'conc2' if x < 18 else 'conc1')
        cv.px(x, 31, 'conc1')
    for y in range(4, 29):                                              # mast
        cv.px(15, y, 'iron3'); cv.px(16, y, 'iron2'); cv.px(17, y, 'iron1')
    for y in range(9, 28, 3):                                           # ladder
        cv.px(19, y, 'iron2'); cv.px(18, y, 'iron2')
    for y in range(9, 29):
        cv.px(20, y, 'iron1')
    cv.px(15, 2, 'iron3'); cv.px(16, 2, 'iron2'); cv.px(15, 3, 'iron4'); cv.px(16, 3, 'iron3')   # finial
    cv.px(16, 1, 'iron3')
    # spectacle casting with red + green lenses, left of the mast
    for y in range(6, 15):
        for x in range(9, 15):
            cv.px(x, y, 'iron2' if (x == 9 or y in (6, 14)) else 'iron1')
    for (cx, cy, c0, c1, c2) in [(11.5, 8.5, 'red1', 'red3', 'flesh3'), (11.5, 12, 'sig_g0', 'sig_g1', 'sig_g2')]:
        for y in range(int(cy - 2), int(cy + 2)):
            for x in range(int(cx - 2), int(cx + 2)):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if d <= 1.6:
                    cv.px(x, y, c2 if d < .8 else c1)
                elif d <= 2.2:
                    cv.px(x, y, c0)
    # semaphore arm (horizontal: STOP), square end with a white band
    for x in range(18, 30):
        for y in range(7, 10):
            c = 'red3' if y == 7 else ('red2' if y == 8 else 'red1')
            if 24 <= x <= 25:
                c = 'wht5' if y == 7 else ('wht3' if y == 8 else 'wht2')
            cv.px(x, y, c)
    for x in range(14, 18):
        cv.px(x, 8, 'iron3' if x < 16 else 'iron2')
    cv.px(16, 7, 'brass2'); cv.px(16, 8, 'brass3'); cv.px(17, 8, 'brass1'); cv.px(16, 9, 'brass1')   # pivot
    # lamp box behind the spectacle
    for y in range(9, 13):
        for x in range(4, 9):
            cv.px(x, y, 'iron2' if x == 4 else 'iron1')
    cv.px(5, 8, 'iron2'); cv.px(6, 8, 'iron3'); cv.px(6, 7, 'iron2')
    cv.px(8, 10, 'lit_win'); cv.px(8, 11, 'amber1')
    outline(cv, None)
    for (x, y, a) in [(10, 5, 80), (13, 5, 80), (8, 8, 90), (12, 5, 60)]:
        if cv.get(x, y)[3] == 0:
            cv.px(x, y, C('flesh3', a))
    return cv


def p_kennel_pen():
    cv = prop_cell()
    for x in range(2, 30):                                              # rails
        cv.px(x, 10, 'board4' if x % 4 else 'board3'); cv.px(x, 11, 'board2'); cv.px(x, 12, 'board1')
        cv.px(x, 25, 'board3'); cv.px(x, 26, 'board2'); cv.px(x, 27, 'board1')
    for x0 in (2, 27):                                                  # posts
        for y in range(8, 32):
            cv.px(x0, y, 'board3' if y > 8 else 'board4'); cv.px(x0 + 1, y, 'board2'); cv.px(x0 + 2, y, 'board1')
        cv.px(x0 + 1, 7, 'board3')
        cv.px(x0 + 1, 11, 'nail'); cv.px(x0 + 1, 26, 'nail')
    # tin bowl with water, and a gnawed bone, in front of the pen
    for (x, y, c) in [(9, 28, 'steel2'), (10, 28, 'steel3'), (11, 28, 'water_hi'), (12, 28, 'water1'),
                      (13, 28, 'water1'), (14, 28, 'water_hi'), (15, 28, 'steel2'), (16, 28, 'steel1'),
                      (9, 29, 'steel1'), (10, 29, 'steel2'), (11, 29, 'steel2'), (12, 29, 'steel1'),
                      (13, 29, 'steel1'), (14, 29, 'steel1'), (15, 29, 'steel0'), (16, 29, 'steel0'),
                      (10, 30, 'steel1'), (11, 30, 'steel1'), (12, 30, 'steel0'), (13, 30, 'steel0'),
                      (14, 30, 'steel0'), (15, 30, 'steel0'), (11, 31, 'steel0'), (14, 31, 'steel0')]:
        cv.px(x, y, c)
    for (x, y, c) in [(19, 30, 'bone'), (20, 31, 'bone_dk'), (20, 30, 'bone'), (21, 30, 'bone'), (22, 30, 'bone'),
                      (23, 30, 'bone'), (24, 29, 'bone'), (24, 31, 'bone_dk'), (19, 29, 'bone'), (21, 31, 'bone_dk'),
                      (22, 31, 'bone_dk')]:
        cv.px(x, y, c)
    ground_tuft(cv, 4, 31); ground_tuft(cv, 25, 31, 2)
    outline(cv, None)
    # chain-link mesh stretched between the rails (drawn after outlining so it stays see-through)
    for y in range(13, 25):
        for x in range(5, 27):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                if (9 <= x <= 12 and 17 <= y <= 21) and (x + y) % 3:      # a torn, curled-back hole
                    continue
                hi = (x + y) % 4 == 0 and (x - y) % 4 == 0
                cv.px(x, y, 'steel2' if hi and y < 19 else ('steel1' if hi else C('steel1', 200)))
    for (x, y) in [(9, 17), (8, 18), (12, 21), (13, 22)]:
        cv.px(x, y, 'steel3')
    return cv


def p_root_cluster():
    cv = prop_cell()
    rng = np.random.default_rng(1800)
    for y in range(26, 32):                                             # heaved earth
        for x in range(3, 30):
            if y - 26 >= abs(x - 16) * .32 - 1.2 + rng.uniform(-.6, .6):
                t = .3 + (31 - y) * .1 - (x - 16) * .015 + rng.uniform(-.1, .1)
                cv.px(x, y, dpick(['dirt0', 'dirt1', 'dirt2', 'dirt3'], t, x, y))
    curves = [((9, 31), (5, 21), (11, 12), 2.4, .8), ((16, 31), (14, 17), (19, 4), 3.0, 1.0),
              ((23, 31), (28, 22), (24, 12), 2.3, .7), ((13, 30), (19, 26), (27, 25), 1.6, .6),
              ((20, 30), (12, 28), (4, 23), 1.5, .5)]
    for (p0, pc, p1, r0, r1) in curves:
        tube(cv, p0, pc, p1, r0, r1, LR, light=(.6, .8), base=.45, k=.5)
    for (p0, pc, p1, r0, r1) in curves[:3]:                            # gold veins up the stems
        for s in range(4, 22, 2):
            t = s / 24
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * pc[0] + t * t * p1[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * pc[1] + t * t * p1[1]
            cv.px(x, y, 'gold2' if s % 6 == 0 else 'gold1')
    for (x, y) in [(11, 12), (19, 4), (24, 12)]:                       # knuckled tips
        cv.px(x, y, 'bone'); cv.px(x, y + 1, 'bone_dk')
    for (x, y) in [(6, 29), (25, 28), (10, 27), (21, 27)]:             # clods
        cv.px(x, y, 'dirt4'); cv.px(x + 1, y, 'dirt3')
    outline(cv, None)
    for (x, y) in [(5, 9), (26, 6), (29, 17), (13, 3), (2, 19), (22, 1)]:
        cv.px(x, y, 'gold2')
        for (dx, dy) in N4:
            if not cv.solid(x + dx, y + dy):
                cv.px(x + dx, y + dy, C('gold1', 110))
    return cv


def p_egg_sac():
    cv = prop_cell()
    rng = np.random.default_rng(1810)
    for (p0, pc, p1, r0, r1) in [((9, 31), (8, 27), (11, 24), 1.4, .7), ((24, 31), (25, 27), (21, 24), 1.4, .7),
                                 ((16, 31), (16, 30), (16, 27), 1.8, 1.2)]:
        tube(cv, p0, pc, p1, r0, r1, LR, light=(.6, .8), base=.4)
    cx, cy, rx, ry = 16, 17.5, 7.6, 10.5
    for y in range(6, 30):
        for x in range(7, 26):
            nx, ny = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            d = math.hypot(nx, ny * (1 + .08 * ny))
            if d > 1:
                continue
            lit = -(nx * .6 + ny * .8)
            t = .36 + .26 * lit * d + .5 * (1 - d) ** 1.5 + rng.uniform(-.04, .04)
            c = qpick(['flesh0', 'flesh1', 'flesh2', 'flesh3'], t, x, y)
            if d > .86 and lit < -.25:
                c = C('flesh2')                                         # back-lit translucent rim
            # the curled thing inside, a shadow through the membrane
            ex, ey = (x + .5 - 16.5) / 4.0, (y + .5 - 19.0) / 5.0
            ed = math.hypot(ex, ey)
            if .42 < ed < 1.0 and not (ex > .15 and ey < -.25):
                c = C('lr1') if ed > .82 or ed < .55 else C('flesh0')
            if math.hypot(x + .5 - 18.6, y + .5 - 15.6) < 1.2:          # its head
                c = C('flesh0')
            cv.px(x, y, c)
    for (p0, p1) in [((14, 7), (12, 12)), ((12, 12), (10, 15)), ((12, 12), (13, 17)), ((20, 9), (22, 15)),
                     ((22, 15), (21, 21)), ((22, 15), (24, 18)), ((11, 22), (14, 27))]:
        for i, (x, y) in enumerate(bres(*p0, *p1)):
            if cv.solid(x, y):
                cv.px(x, y, 'flesh0' if i % 3 else 'lr1')
    for (x, y, c) in [(11, 10, 'eye_w'), (12, 9, 'worm_hl'), (11, 11, 'worm_hl'), (13, 8, 'flesh3'),
                      (10, 13, 'worm_hl'), (21, 25, 'flesh3'), (18, 19, 'gold2'), (17, 19, 'gold1')]:
        cv.px(x, y, c)
    outline(cv, None)
    for x in range(5, 28):                                             # glistening slime pool
        if abs(x - 16) < 11:
            cv.px(x, 31, C('flesh1', 150 if abs(x - 16) < 8 else 90))
    for (x, y, a) in [(6, 14, 70), (26, 12, 70), (5, 20, 50), (27, 21, 50)]:
        cv.px(x, y, C('flesh3', a))
    return cv


def p_bumper():
    cv = prop_cell()
    for x in range(0, 32):                                              # ties + rail
        if x % 6 < 4:
            cv.px(x, 30, 'cre3' if x % 6 == 0 else 'cre2'); cv.px(x, 31, 'cre1')
        else:
            cv.px(x, 31, 'cre0')
    for x in range(0, 27):
        cv.px(x, 28, 'steel2' if x % 5 else 'steel3'); cv.px(x, 29, 'steel0')
    # rails bent up into a braced triangle
    for (p0, p1) in [((26, 29), (24, 13)), ((12, 29), (22, 14))]:
        for (x, y) in bres(*p0, *p1):
            cv.px(x, y, 'steel1'); cv.px(x + 1, y, 'steel0')
    for (x, y) in bres(17, 21, 25, 21):
        cv.px(x, y, 'steel1')
    # heavy timber header painted with warning stripes
    for y in range(12, 18):
        for x in range(14, 30):
            stripe = ((x - y) // 3) % 2 == 0
            c = ('red3' if y == 12 else 'red2') if stripe else ('wht5' if y == 12 else 'wht3')
            if y == 17:
                c = 'red0' if stripe else 'wht1'
            cv.px(x, y, c)
    # buffer head facing the oncoming train (left)
    for y in range(12, 18):
        cv.px(13, y, 'iron2')
    for (x, y, c) in [(10, 13, 'iron3'), (11, 13, 'iron3'), (12, 13, 'iron2'), (10, 14, 'iron4'), (11, 14, 'iron3'),
                      (12, 14, 'iron2'), (10, 15, 'iron3'), (11, 15, 'iron2'), (12, 15, 'iron1'), (10, 16, 'iron2'),
                      (11, 16, 'iron1'), (12, 16, 'iron1'), (9, 14, 'iron2'), (9, 15, 'iron1')]:
        cv.px(x, y, c)
    for (x, y) in [(15, 14), (28, 14), (15, 16), (28, 16)]:
        cv.px(x, y, 'nail')
    for x in range(20, 31):                                             # gravel
        if (x * 7) % 3:
            cv.px(x, 29, 'peb1' if x % 2 else 'peb0')
    outline(cv, None)
    return cv


def p_diving_helmet():
    cv = prop_cell()
    rng = np.random.default_rng(1820)
    rust = fbm(32, 32, 4, 4, rng, 3)
    # corselet lying flat beneath
    for y in range(26, 31):
        for x in range(4, 28):
            if abs(x - 16) <= 12 - (30 - y) * .6:
                t = .62 - (x - 4) / 24 * .4 + (.15 if y == 26 else 0)
                c = dpick(COP, t, x, y)
                if rust[y, x] > .72:
                    c = qpick(['verd0', 'verd1', 'verd2'], (rust[y, x] - .72) * 3, x, y)
                cv.px(x, y, c)
    for x in range(6, 27, 3):
        cv.px(x, 28, 'brass3' if x < 16 else 'brass1')
    # the dome, tipped over onto its side
    cx, cy, rr = 16.5, 18.5, 8.3
    for y in range(9, 29):
        for x in range(7, 27):
            dx, dy = x + .5 - cx, y + .5 - cy
            d = math.hypot(dx, dy)
            if d > rr:
                continue
            lit = -(dx * .6 + dy * .8) / rr
            c = qpick(COP, .48 + .55 * lit, x, y)
            if rust[y, x] > .7:
                c = qpick(['verd0', 'verd1', 'verd2'], (rust[y, x] - .7) * 3 + .3 * lit + .3, x, y)
            elif rust[y, x] < .22:
                c = 'rust1' if lit > 0 else 'rust0'
            cv.px(x, y, c)
    # front faceplate (now facing up-right), glass cracked and dark
    fx, fy = 20.5, 15.5
    for y in range(11, 21):
        for x in range(16, 26):
            d = math.hypot(x + .5 - fx, y + .5 - fy)
            if d <= 3.2:
                cv.px(x, y, 'glass0' if d < 2.2 else ('brass2' if (x + .5 - fx) + (y + .5 - fy) < 0 else 'brass0'))
    for (x, y) in [(19, 14), (20, 15), (21, 15), (21, 16), (22, 17)]:
        cv.px(x, y, 'glass2')
    cv.px(19, 13, 'glass1')
    for (x, y) in [(10, 17), (11, 16), (10, 18)]:                     # side port
        cv.px(x, y, 'brass1')
    cv.px(11, 17, 'glass0')
    for (x, y, c) in [(8, 25, 'char2'), (7, 26, 'char1'), (6, 27, 'char2'), (5, 28, 'char1'), (5, 29, 'char2'),
                      (9, 24, 'brass2')]:
        cv.px(x, y, c)                                                # torn hose stub
    cv.px(13, 12, 'cop4'); cv.px(14, 11, 'cop3')
    for (x, y) in [(3, 31), (4, 30), (26, 31), (27, 30), (28, 31), (12, 31)]:
        cv.px(x, y, 'algae2' if (x + y) % 2 else 'algae3')
    for x in range(3, 30):                                             # silt line
        if not cv.solid(x, 31):
            cv.px(x, 31, 'dirt1')
    outline(cv, None)
    return cv


def p_dynamite_crate():
    cv = prop_cell()
    rng = np.random.default_rng(1830)
    # sticks poking out of the pried-open lid
    for (x0, h) in [(9, 6), (12, 8), (15, 5), (19, 7)]:
        for y in range(15 - h, 15):
            cv.px(x0, y, 'dyn' if y > 15 - h else 'flesh3'); cv.px(x0 + 1, y, 'dyn_dk')
        cv.px(x0, 14 - h, 'ink2'); cv.px(x0 + 1, 13 - h, 'ink2')        # fuse
    for x in range(4, 27):                                              # lid, propped askew
        y = 13 - (x - 4) * 4 // 22
        cv.px(x, y, 'wood4' if x % 5 else 'wood3'); cv.px(x, y + 1, 'wood2')
    for y in range(15, 32):
        for x in range(2, 30):
            k = (y - 15) % 6
            t = [.82, .62, .55, .5, .42, .1][k] + (rng.random() - .5) * .12
            c = dpick(['wood1', 'wood2', 'wood3', 'wood4'], t, x, y)
            if x in (2, 3, 28, 29):
                c = 'wood3' if x in (2, 28) else 'wood1'
            cv.px(x, y, c)
    for (x, y) in [(2, 16), (28, 16), (2, 30), (28, 30), (2, 22), (28, 22)]:
        cv.px(x, y, 'nail')
    tw = text_w('DANGER')
    for x in range(4, 28):                                              # pale label band
        for y in range(21, 28):
            if y in (21, 27):
                cv.px(x, y, 'wood2')
            else:
                cv.px(x, y, 'camp2' if (x + y) % 5 else 'camp1')
    stencil(cv, 16 - tw // 2, 22, 'DANGER', 'dyn', shadow=None, rng=rng, chip=.04)
    for (x, y) in [(5, 18), (6, 18), (7, 18), (24, 18), (25, 18), (26, 18)]:   # stencil bars
        cv.px(x, y, 'dyn_dk')
    outline(cv, None)
    return cv


# ---------------------------------------------------------------- locomotive boss
LOCO_DRIVERS = [(36, 47), (56, 47)]       # drive-wheel centres on the loco piece (wheel radius 9)
LOCO_WINDOW = (9, 13, 12, 12)             # cab window x, y, w, h (engineer inside)


def spoked_wheel(cv, cx, cy, r, nsp=12, counterweight=True, crank=0.0):
    rim_in = r - 2.2
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x + .5 - cx, y + .5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            lit = -(dx * .6 + dy * .8) / r
            ang = math.atan2(dy, dx)
            if d > r - 1.2:
                c = 'steel2' if lit > .35 else ('steel1' if lit > -.35 else 'steel0')
            elif d > rim_in:
                c = 'red1' if lit < .2 else 'red2'
            elif d < 1.3:
                c = 'iron3' if lit > 0 else 'iron2'
            elif d < 2.3:
                c = 'red3' if lit > 0 else 'red2'
            else:
                da = (ang - crank) % (2 * math.pi / nsp)
                da = min(da, 2 * math.pi / nsp - da) * d
                cwa = abs(((ang - crank - math.pi) + math.pi) % (2 * math.pi) - math.pi)
                if counterweight and cwa < .8 and d > 3.2:
                    c = 'red2' if lit > 0 else 'red1'
                elif da < .72:
                    c = 'red4' if lit > .3 else ('red3' if lit > -.3 else 'red2')
                else:
                    continue
            cv.px(x, y, c)
    if counterweight:                                            # crank pin
        px_, py_ = cx + math.cos(crank) * r * .5, cy + math.sin(crank) * r * .5
        cv.px(px_ - .5, py_ - .5, 'steel3'); cv.px(px_ + .5, py_ - .5, 'steel1')
        cv.px(px_ - .5, py_ + .5, 'steel1'); cv.px(px_ + .5, py_ + .5, 'steel0')


def train_wheel():
    cv = Canvas(18, 18)
    spoked_wheel(cv, 9, 9, 9, 10, True, crank=0.0)
    return cv


def h_cyl(cv, x0, x1, y0, y1, ramp, hl=.0, k=.55):
    """Horizontal cylinder seen side-on: shade by row, highlight band high."""
    h = y1 - y0
    for y in range(y0, y1 + 1):
        v = (y + .5 - y0) / (h + 1)
        t = (.85 + hl - (.25 - v) * 1.6) if v < .25 else (.85 + hl - (v - .25) * k * 2.3)
        for x in range(x0, x1 + 1):
            cv.px(x, y, qpick(ramp, t, x, y))


def loco():
    cv = Canvas(96, 56)
    rng = np.random.default_rng(SEED + 4001)
    # frame + pilot truck
    for x in range(20, 88):
        cv.px(x, 41, 'iron2'); cv.px(x, 42, 'iron1')
    for (cx, cy) in [(73, 50.5), (83, 50.5)]:
        spoked_wheel(cv, cx, cy, 5.2, 8, False)
        cv.px(cx - .5, cy - .5, 'brass2')
    for x in range(69, 88):                                        # truck side frame
        cv.px(x, 47, 'iron2' if x % 4 else 'iron3')
    # cylinder + valve chest
    h_cyl(cv, 70, 85, 39, 46, IRON)
    for y in range(39, 47):
        cv.px(70, y, 'brass1'); cv.px(85, y, 'brass1'); cv.px(71, y, 'brass2')
    for y in range(35, 39):
        for x in range(72, 84):
            cv.px(x, y, 'iron3' if y == 35 else ('iron2' if x > 73 else 'iron3'))
    # boiler
    h_cyl(cv, 28, 76, 22, 38, IRON, hl=.02)
    for bx in (45, 63):                                            # brass bands
        for y in range(22, 39):
            v = (y - 22) / 16
            cv.px(bx, y, 'brass3' if v < .2 else ('brass2' if v < .55 else 'brass1'))
            cv.px(bx + 1, y, 'brass1' if v < .55 else 'brass0')
    # smokebox (sooty, slightly larger) + front ring
    h_cyl(cv, 76, 88, 21, 39, CHAR, hl=.0)
    for y in range(22, 39):
        cv.px(76, y, 'iron3'); cv.px(77, y, 'iron1')
        cv.px(88, y, 'iron3' if y < 30 else 'iron2')
    # handrail with stanchions
    for x in range(30, 87):
        cv.px(x, 27, 'steel2' if x < 76 else 'steel1')
    for x in range(34, 86, 9):
        cv.px(x, 28, 'steel0')
    # running board
    for x in range(26, 90):
        cv.px(x, 38, 'iron3'); cv.px(x, 39, 'iron1')
    # splashers over the drivers (brass beading)
    for (cx, cy) in LOCO_DRIVERS:
        for y in range(34, 40):
            for x in range(cx - 12, cx + 13):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if 9.6 < d <= 11.6 and y < 41:
                    cv.px(x, y, 'brass2' if d > 10.8 else 'iron2')
    # diamond stack
    sx = 79.5
    for y in range(1, 22):
        if y >= 14:
            hw = 2.5
        elif y >= 7:
            hw = 2.5 + (14 - y) / 7 * 5.0
        else:
            hw = 7.5 - (7 - y) / 6 * 3.0
        x0, x1 = int(round(sx - hw)), int(round(sx + hw))
        for x in range(x0, x1):
            u = (x + .5 - sx) / hw
            t = .6 - .5 * u + (.12 if y < 7 else 0)
            cv.px(x, y, qpick(IRON, t, x, y))
    for x in range(75, 85):
        cv.px(x, 1, 'iron4' if x < 79 else 'iron3')
    for x in range(72, 88):                                         # band at the widest point
        cv.px(x, 7, 'brass3' if x < 76 else ('brass2' if x < 82 else 'brass1'))
    for x in range(77, 82):
        cv.px(x, 20, 'brass2' if x < 79 else 'brass1')
    # steam dome (brass), sand dome, bell, whistle + pops
    for y in range(13, 23):
        for x in range(51, 66):
            dx = (x + .5 - 58) / (4.6 + max(0, y - 19) * 1.0)
            dy = (y + .5 - 18.5) / 5.0
            if (y >= 18 and abs(dx) <= 1) or (y < 18 and dx * dx + dy * dy <= 1):
                lit = -dx * .8 + (.3 if y < 16 else 0)
                cv.px(x, y, dpick(BRASS, .5 + .45 * lit, x, y))
    cv.px(57, 13, 'brass3'); cv.px(58, 12, 'brass2')
    for y in range(16, 23):
        for x in range(38, 46):
            dx = (x + .5 - 42) / (3.0 + max(0, y - 20))
            if abs(dx) <= 1 and not (y == 16 and abs(dx) > .6):
                cv.px(x, y, dpick(IRON, .55 - dx * .4, x, y))
    for x in range(40, 45):
        cv.px(x, 16, 'brass2' if x < 43 else 'brass1')
    for (x, y, c) in [(68, 15, 'iron2'), (69, 15, 'iron2'), (68, 16, 'brass2'), (69, 16, 'brass1'),
                      (67, 17, 'brass3'), (68, 17, 'brass2'), (69, 17, 'brass1'), (70, 17, 'brass1'),
                      (67, 18, 'brass2'), (68, 18, 'brass2'), (69, 18, 'brass1'), (70, 18, 'brass0'),
                      (66, 19, 'brass2'), (67, 19, 'brass2'), (68, 19, 'brass1'), (69, 19, 'brass1'), (70, 19, 'brass0'),
                      (71, 19, 'brass0'), (68, 20, 'iron2'), (68, 21, 'iron2')]:
        cv.px(x, y, c)                                              # bell
    for (x, y, c) in [(32, 15, 'brass3'), (32, 16, 'brass2'), (33, 16, 'brass1'), (32, 17, 'brass2'), (33, 17, 'brass1'),
                      (32, 18, 'brass1'), (32, 19, 'iron2'), (32, 20, 'iron2'), (32, 21, 'iron1'),
                      (36, 19, 'brass2'), (37, 19, 'brass1'), (36, 20, 'brass1'), (37, 20, 'brass0'), (36, 21, 'iron2')]:
        cv.px(x, y, c)                                              # whistle + safety valve
    # headlamp: big box lamp on the smokebox, lens blazing forward
    for y in range(11, 21):
        for x in range(84, 94):
            c = 'iron2' if x < 86 else 'iron1'
            if y == 11:
                c = 'iron3'
            if x == 84:
                c = 'iron3'
            cv.px(x, y, c)
    for x in range(85, 93):
        cv.px(x, 13, 'brass2' if x < 89 else 'brass1')              # number board trim
    for x in range(86, 91):
        cv.px(x, 15, 'gold1' if x % 2 else 'gold0')
    for y in range(12, 20):
        cv.px(94, y, 'brass2')
    for (x, y, c) in [(95, 13, 'lit_win'), (95, 14, 'amber2'), (95, 15, 'amber2'), (95, 16, 'amber2'),
                      (95, 17, 'lit_win'), (95, 18, 'amber1'), (95, 12, 'amber1')]:
        cv.px(x, y, c)
    for (x, y, c) in [(87, 9, 'iron2'), (88, 9, 'iron2'), (87, 10, 'iron3'), (88, 10, 'iron2'), (86, 8, 'iron3'),
                      (87, 8, 'iron3'), (88, 8, 'iron2'), (89, 8, 'iron1')]:
        cv.px(x, y, c)                                              # lamp chimney
    for x in range(86, 92):
        cv.px(x, 21, 'iron2')                                       # bracket
    # buffer beam, coupler, cowcatcher
    for y in range(40, 45):
        for x in range(86, 93):
            cv.px(x, y, 'red3' if y == 40 else ('red2' if y < 43 else 'red1'))
    cv.px(93, 42, 'iron3'); cv.px(94, 42, 'iron2'); cv.px(94, 43, 'iron1'); cv.px(95, 42, 'iron2')
    m = Image.new('L', (96, 56), 0)
    ImageDraw.Draw(m).polygon([(84, 45), (90, 45), (95.5, 53.5), (95.5, 55.5), (84, 55.5)], fill=255)
    m = np.array(m) > 0
    for y, x in zip(*np.nonzero(m)):
        s = int(x - .62 * y) % 3
        c = ['red0', 'red3', 'red2'][s] if y > 45 else 'red4'          # sloped slats
        if y >= 53 and s:
            c = 'red1'
        cv.px(x, y, c)
    for x in range(84, 96):
        cv.px(x, 55, 'iron2' if x < 95 else 'iron1')
    # cab: varnished wood, arched roof, gold-lined panel and B&A lettering
    for y in range(11, 45):
        for x in range(4, 30):
            c = 'ox3' if x <= 6 else ('ox1' if x >= 26 else 'ox2')
            if (y - 11) % 4 == 3 and y < 26 and 4 < x < 29:
                c = 'ox1'                                           # tongue-and-groove siding
            if x == 4:
                c = 'ox4'
            if x == 29:
                c = 'ox1'
            cv.px(x, y, c)
    for x in range(6, 28):                                          # lined panel
        cv.px(x, 26, 'gold0'); cv.px(x, 41, 'gold0')
    for y in range(26, 42):
        cv.px(6, y, 'gold0'); cv.px(27, y, 'gold0')
    for x in range(7, 27):
        for y in range(27, 41):
            if (x + y) % 7 == 0 and y < 34:
                cv.px(x, y, 'ox3')
    for x in range(2, 31):                                          # sill + roof
        cv.px(x, 44, 'iron2'); cv.px(x, 45, 'iron1')
    for (y, x0, x1, c) in [(6, 5, 28, 'iron3'), (7, 3, 30, 'iron2'), (8, 1, 31, 'iron2'), (9, 1, 31, 'iron1'),
                           (10, 2, 30, 'ox0')]:
        for x in range(x0, x1 + 1):
            cv.px(x, y, c)
    for x in range(6, 26, 4):
        cv.px(x, 7, 'iron4')
    wx, wy, ww, wh = LOCO_WINDOW
    for y in range(wy - 1, wy + wh + 1):                           # window frame
        for x in range(wx - 1, wx + ww + 1):
            cv.px(x, y, 'wood4' if (x == wx - 1 or y == wy - 1) else 'wood2')
    for y in range(wy, wy + wh):
        for x in range(wx, wx + ww):
            t = (y - wy) / wh
            cv.px(x, y, 'cave1' if t < .55 else ('amber0' if (x + y) % 2 else 'red0'))   # firebox glow
    eng = [  # engineer: striped cap, red bandana, looking ahead
        "..bwbw..",
        ".bwbwbwb",
        "..hSSSS.",
        "..hSSkSs",
        "..hSSSS.",
        "...sSSs.",
        "..rrRrr.",
        ".jjjjjjj",
        ".jJJjjSS",
    ]
    amap(cv, wx + 3, wy + 1, eng, {'b': 'blue1', 'w': 'wht4', 'h': 'hair0', 'S': 'skin1', 's': 'skin0', 'k': 'ink',
                                   'r': 'tie', 'R': 'tie_dk', 'j': 'blue0', 'J': 'blue1'})
    cv.px(wx + ww - 1, wy + 5, 'skin2')
    tw = text_w('B&A')
    stencil(cv, 17 - tw // 2, 30, 'B&A', 'gold1', shadow='ox0', col2='gold2')
    # front cab window + cab steps + firebox below
    for y in range(14, 20):
        cv.px(28, y, 'glass2' if y < 16 else 'glass1')
    for y in range(46, 53):
        cv.px(5, y, 'iron2'); cv.px(9, y, 'iron1')
    for x in range(5, 10):
        cv.px(x, 49, 'iron3'); cv.px(x, 52, 'iron3')
    for y in range(39, 46):                                          # firebox between cab and drivers
        for x in range(20, 27):
            cv.px(x, y, 'char2' if x < 22 else 'char1')
    for (x, y) in [(22, 44), (23, 44), (24, 45)]:
        cv.px(x, y, 'fire2')
    # sand pipe + steam pipe
    for (x, y) in bres(44, 23, 46, 37):
        cv.px(x, y, 'iron2')
    for y in range(39, 41):
        cv.px(79, y, 'iron3'); cv.px(80, y, 'iron2')
    for (x, y) in [(31, 31), (40, 33), (52, 31), (68, 33)]:          # boiler rivet glints
        cv.px(x, y, 'iron4')
    outline(cv, None)
    # empty space for the code-drawn drive wheels
    for (cx, cy) in LOCO_DRIVERS:
        for y in range(cy - 10, cy + 10):
            for x in range(cx - 10, cx + 10):
                if 0 <= y < 56 and math.hypot(x + .5 - cx, y + .5 - cy) <= 9.6:
                    cv.a[y, x] = 0
    for (x, y, a) in [(95, 10, 90), (95, 20, 90)]:
        if cv.get(x, y)[3] == 0:
            cv.px(x, y, C('lit_win', a))
    return cv


def tender():
    cv = Canvas(44, 40)
    rng = np.random.default_rng(SEED + 4002)
    for (cx, cy) in [(8, 35.5), (16, 35.5), (28, 35.5), (36, 35.5)]:
        spoked_wheel(cv, cx, cy, 4.4, 8, False)
        cv.px(cx - .5, cy - .5, 'brass2')
    for (x0, x1) in [(3, 21), (23, 41)]:                            # arch-bar trucks
        for x in range(x0, x1 + 1):
            cv.px(x, 33, 'iron3'); cv.px(x, 34, 'iron1') if (x - x0) % 8 in (3, 4) else None
        for x in range(x0 + 6, x0 + 13):
            cv.px(x, 36, 'iron2')
        cv.px(x0 + 9, 35, 'iron3'); cv.px(x0 + 9, 37, 'iron1')
    for x in range(1, 44):
        cv.px(x, 31, 'iron2'); cv.px(x, 32, 'iron1')
    cv.px(42, 30, 'iron3'); cv.px(43, 30, 'iron2')                 # drawbar
    # tank
    for y in range(13, 31):
        for x in range(1, 43):
            t = .5 - (y - 13) / 17 * .3 - (x - 1) / 42 * .1
            if y == 13:
                t = .9
            cv.px(x, y, qpick(IRON, t, x, y))
    for x in range(3, 41):
        cv.px(x, 15, 'gold0'); cv.px(x, 28, 'gold0')
    for y in range(15, 29):
        cv.px(3, y, 'gold0'); cv.px(40, y, 'gold0')
    for y in range(13, 31):
        cv.px(1, y, 'iron3')
    for x in range(1, 43, 4):
        cv.px(x, 30, 'iron4')
    # flared coal boards + heaped coal
    for x in range(2, 42):
        cv.px(x, 12, 'iron3'); cv.px(x, 11, 'iron2' if x < 9 or x > 34 else 'iron1')
    heap = fbm(44, 16, 6, 3, rng, 3)
    for x in range(4, 41):
        top = 11 - int(round(8.5 * max(0, 1 - ((x - 27) / 16.5) ** 2))) + int(rng.integers(0, 2))
        for y in range(max(1, top), 13):
            if y >= 11 and (x < 6 or x > 38):
                continue
            n = heap[y, x]
            t = .55 - (y - top) * .06 + (n - .5) * .7
            c = dpick(CHAR, t, x, y)
            if n > .78 and (x + y) % 3 == 0:
                c = 'rock3'
            if n > .86 and (x * 3 + y) % 5 == 0:
                c = 'iron4'
            cv.px(x, y, c)
    # water hatch + rear marker lamp
    for x in range(6, 12):
        cv.px(x, 10, 'iron3' if x < 9 else 'iron2')
    cv.px(8, 9, 'brass2')
    for (x, y, c) in [(0, 17, 'iron2'), (0, 18, 'tie'), (0, 19, 'red3'), (0, 20, 'iron2')]:
        cv.px(x, y, c)
    outline(cv, None)
    return cv


def _post_pattern(cv, oy, grain):
    """One 48px repeat of the trestle bent post + sway bracing, drawn at y offset oy.
    Braces zig-zag edge to edge every 24px, so the strip repeats seamlessly."""
    for (y0, x0, x1) in [(0, 0, 15), (24, 15, 0)]:                  # braces behind the post
        for (x, y) in bres(x0, y0, x1, y0 + 23):
            cv.px(x, y + oy, 'cre4'); cv.px(x + 1, y + oy, 'cre3'); cv.px(x + 2, y + oy, 'cre1')
    for (y0, x0, x1) in [(0, 15, 0), (24, 0, 15)]:                  # and the opposite diagonals, in front
        for (x, y) in bres(x0, y0, x1, y0 + 23):
            cv.px(x - 1, y + oy, 'cre5'); cv.px(x, y + oy, 'cre3'); cv.px(x + 1, y + oy, 'cre2')
    for y in range(48):
        for x in range(5, 11):
            t = .82 - (x - 5) / 5 * .72 + (grain[y, x] - .5) * .25
            if x in (7, 9) and (y + int(grain[y, x] * 6)) % 9 < 3:
                t -= .2
            cv.px(x, y + oy, qpick(CRE, t, x, y))
    for (y0, x0, x1) in [(0, 15, 0), (24, 0, 15)]:                  # front braces cross over the post
        for (x, y) in bres(x0, y0, x1, y0 + 23):
            if 4 <= x <= 11 and 6 <= y - y0 <= 17:
                cv.px(x - 1, y + oy, 'cre5'); cv.px(x, y + oy, 'cre3'); cv.px(x + 1, y + oy, 'cre2')
    for yy in (0, 24):                                              # girts where the braces meet
        for x in range(16):
            cv.px(x, yy + oy, 'cre5' if x % 5 else 'cre4')
            cv.px(x, yy + 1 + oy, 'cre3')
            cv.px(x, yy + 2 + oy, 'cre1')
        for x in (2, 8, 13):
            cv.px(x, yy + 1 + oy, 'steel2')
    for (x, y) in [(7, 12), (8, 36)]:                               # through-bolts at the crossings
        cv.px(x, y + oy, 'steel3'); cv.px(x + 1, y + oy, 'iron1'); cv.px(x, y + 1 + oy, 'iron1')


def trestle_post(torn=False):
    grain = vnoise(16, 48, 3, 8, np.random.default_rng(SEED + 4003))
    big = Canvas(16, 48 * 3)
    for oy in (0, 48, 96):
        _post_pattern(big, oy, grain)
    if torn:
        rng = np.random.default_rng(SEED + 4004)
        # snap the post (and the braces) through the middle, leaving splintered ends
        for x in range(0, 16):
            top = 48 + 16 + int(rng.integers(0, 3)) + (2 if 6 <= x <= 9 and x % 2 else 0)
            bot = 48 + 30 - int(rng.integers(0, 3)) - (2 if 5 <= x <= 10 and x % 2 == 0 else 0)
            for y in range(top, bot):
                big.a[y, x] = 0
            if 5 <= x <= 10:
                big.px(x, top - 1, 'wood5' if x % 2 else 'wood4')
                big.px(x, top - 2, 'wood3' if x % 2 else 'wood4')
                big.px(x, bot, 'wood4' if x % 2 == 0 else 'wood5')
                big.px(x, bot + 1, 'wood3')
        for (x, y, c) in [(7, 48 + 16, 'wood4'), (7, 48 + 17, 'wood5'), (9, 48 + 17, 'wood4'), (9, 48 + 18, 'wood5'),
                          (6, 48 + 28, 'wood5'), (6, 48 + 27, 'wood4'), (10, 48 + 27, 'wood5'),
                          (2, 48 + 21, 'cre3'), (3, 48 + 22, 'cre2'), (13, 48 + 25, 'cre3'), (12, 48 + 24, 'cre2')]:
            big.px(x, y, c)
    outline(big, None)
    cv = Canvas(16, 48)
    cv.a[:] = big.a[48:96]
    return cv


def rowboat():
    cv = Canvas(56, 20)
    rng = np.random.default_rng(SEED + 4005)
    # air pump: a wooden box amidships with a big brass flywheel on its side
    for y in range(4, 12):
        for x in range(25, 38):
            cv.px(x, y, 'wood4' if y == 4 else ('wood3' if x < 28 else 'wood2'))
    cv.px(26, 4, 'wood5')
    for y in range(0, 10):
        for x in range(26, 37):
            dx, dy = x + .5 - 31.5, y + .5 - 4.5
            d = math.hypot(dx, dy)
            if 3.4 < d <= 4.5:
                cv.px(x, y, 'brass3' if (dx + dy) < -2 else ('brass2' if (dx + dy) < 2 else 'brass1'))
            elif d <= 3.4 and (abs(dx) < .6 or abs(dy) < .6):
                cv.px(x, y, 'iron2')
            elif d <= 1.2:
                cv.px(x, y, 'iron3')
    cv.px(31, 4, 'brass3')
    for (x, y, c) in [(35, 1, 'wood4'), (36, 0, 'wood4'), (35, 2, 'iron2')]:   # crank handle
        cv.px(x, y, c)
    # coil of air hose heaped in the stern: stacked loops, each lit along its top
    for k, (cy, rx) in enumerate([(8.2, 6.6), (6.9, 6.0), (5.6, 5.2), (4.4, 4.2)]):
        for x in range(int(14 - rx - 1), int(14 + rx + 2)):
            for y in range(int(cy - 2), int(cy + 3)):
                d = ((x + .5 - 14) / rx) ** 2 + ((y + .5 - cy) / 1.5) ** 2
                if .45 < d <= 1.05:
                    top = y + .5 < cy
                    cv.px(x, y, ('cnv2' if (x + k) % 3 else 'cnv3') if top else ('cnv1' if d < .8 else 'cnv0'))
    for (x, y, c) in [(20, 5, 'brass2'), (21, 5, 'brass3'), (22, 5, 'cnv1'), (23, 6, 'cnv1'), (24, 7, 'cnv0')]:
        cv.px(x, y, c)                                               # hose run to the pump
    # hose over the gunwale and down into the water (the long hose continues in code)
    for (x, y) in bres(38, 8, 44, 6) + bres(44, 6, 46, 9) + bres(46, 9, 46, 19):
        cv.px(x, y, 'cnv2'); cv.px(x + 1, y, 'cnv0')
    # lapstrake hull
    poly = [(1, 6), (10, 8.5), (22, 9.6), (34, 9.6), (44, 8), (51, 5), (55, 2), (55.6, 4), (53, 10), (49, 16),
            (45, 20), (6, 20), (2, 15)]
    m = Image.new('L', (56, 20), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    m = np.array(m) > 0
    sheer = [int(np.nonzero(m[:, x])[0].min()) if m[:, x].any() else 99 for x in range(56)]
    paint = fbm(56, 20, 7, 3, rng, 3)
    for y, x in zip(*np.nonzero(m)):
        k = (y - sheer[x])
        if k <= 0:
            c = 'wood5' if x % 6 == 2 else 'wood4'                   # gunwale cap
        elif k == 1:
            c = 'wood2'
        else:
            s = (k - 2) % 3
            t = [.8, .55, .18][s] - (y / 20) * .12
            c = qpick(['board0', 'board1', 'board2', 'board3', 'board4'], t, x, y)
            if paint[y, x] > .64 and s == 1:                         # last flakes of white paint
                c = 'wht2'
            if y >= 17:
                c = qpick(['algae0', 'algae1', 'algae2'], .65 - (y - 17) * .25 + (paint[y, x] - .5) * .5, x, y)
        cv.px(x, y, c)
    for x in (12, 40):                                               # oarlocks
        cv.px(x, sheer[x] - 1, 'steel1'); cv.px(x + 1, sheer[x] - 1, 'steel0')
    for (x, y) in [(5, 12), (5, 13), (26, 14), (27, 14), (38, 12)]:  # rust weeping from nails
        cv.px(x, y, 'rust1')
    for x in range(50, 54):                                          # stem band
        cv.px(x, sheer[x] + 1, 'steel1')
    outline(cv, None)
    for x in range(56):                                              # clean waterline: nothing below row 19
        if cv.a[19, x, 3] and not m[19, x]:
            cv.a[19, x] = 0
    return cv


def hose_piece(cut=False):
    cv = Canvas(12, 12)
    for x in range(0, 12):                                           # hose
        if cut and 3 <= x <= 9:
            continue
        cv.px(x, 5, 'smoke1' if x % 3 else 'char3'); cv.px(x, 6, 'char2'); cv.px(x, 7, 'char1')
    body = [(3, 'brass1', 3, 9), (4, 'brass3', 3, 9), (5, 'brass2', 4, 8), (6, 'brass2', 4, 8), (7, 'brass1', 3, 9),
            (8, 'brass0', 3, 9)]
    for (x, c, y0, y1) in body:
        if cut and x >= 7:
            continue
        for y in range(y0, y1 + 1):
            cv.px(x, y, c if y > y0 else 'brass3' if x < 6 else 'brass2')
    if not cut:
        for (x, y, c) in [(5, 3, 'brass1'), (6, 3, 'brass1'), (5, 2, 'brass2'), (6, 2, 'brass1'),
                          (3, 1, 'red3'), (4, 1, 'red3'), (5, 1, 'red2'), (6, 1, 'red2'), (7, 1, 'red1'), (8, 1, 'red1')]:
            cv.px(x, y, c)
        cv.px(4, 4, 'steel3')
    else:
        for (x, y, c) in [(7, 4, 'brass1'), (7, 8, 'brass0'), (8, 5, 'char2'), (8, 7, 'char1'), (9, 8, 'cnv2'),
                          (10, 7, 'char2'), (10, 6, 'char1'), (9, 9, 'cnv2'), (11, 6, 'char2')]:
            cv.px(x, y, c)                                           # torn, frayed ends
        cv.px(4, 4, 'steel3')
    outline(cv, None)
    if cut:                                                          # air spraying out as bubbles
        for (x, y, r_) in [(8, 2.5, 1.4), (10.5, 1.5, 1.0), (9.5, 4.5, .9), (7, 0.5, .8), (11, 3.5, .7)]:
            for yy in range(int(y - 2), int(y + 2)):
                for xx in range(int(x - 2), int(x + 2)):
                    d = math.hypot(xx + .5 - x, yy + .5 - y)
                    if d <= r_ + .3:
                        rim = d > r_ - .6
                        cv.px(xx, yy, C('foam', 230) if rim and yy + .5 < y else
                              (C('water_hi', 200) if rim else C('water1', 90)))
        cv.px(8, 2, 'eye_w')
    return cv


def smoke_puff():
    cv = Canvas(16, 16)
    blobs = [(7.5, 9.8, 5.0), (10.6, 6.6, 3.9), (5.2, 6.4, 3.5), (11.4, 10.6, 3.3), (8.2, 4.4, 3.0)]
    for y in range(16):
        for x in range(16):
            best, lit = -9.0, 0.0
            for (bx, by, br) in blobs:
                dx, dy = (x + .5 - bx) / br, (y + .5 - by) / br
                d = math.hypot(dx, dy)
                if d <= 1 and 1 - d > best:
                    best, lit = 1 - d, -(dx * .6 + dy * .8)
            if best < 0:
                continue
            t = .45 + .4 * lit + (.1 if y < 8 else -.05)
            col = qpick(SMK, t, x, y)
            a = 235
            if best < .14:                                           # soft, broken edge
                a = 150 if B4[y % 4, x % 4] < .5 else 90
            cv.px(x, y, C(col, a))
    return cv


def build_boss_train():
    pieces = [
        ('loco', loco(), (48, 56)),
        ('tender', tender(), (22, 40)),
        ('wheel', train_wheel(), (9, 9)),
        ('post', trestle_post(False), (8, 0)),
        ('post_torn', trestle_post(True), (8, 0)),
        ('rowboat', rowboat(), (28, 20)),
        ('hose_valve', hose_piece(False), (6, 6)),
        ('hose_cut', hose_piece(True), (6, 6)),
        ('smoke', smoke_puff(), (8, 8)),
    ]
    x, meta = 0, {}
    for name, cv, pv in pieces:
        meta[name] = {'rect': [x, 0, cv.w, cv.h], 'pivot': [pv[0], pv[1]]}
        x += cv.w + 2
    W, H = x - 2, max(cv.h for _, cv, _ in pieces)
    sheet = Canvas(W, H)
    for name, cv, pv in pieces:
        rx, ry, w, h = meta[name]['rect']
        sheet.a[ry:ry + h, rx:rx + w] = cv.a
    sheet.save('boss_train.png')
    with open(os.path.join(OUT, 'boss_train.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    # assembled demo: train crossing the trestle, one bent torn, the diver's boat below
    P = {n: cv for n, cv, _ in pieces}
    PV = {n: pv for n, _, pv in pieces}
    demo = Canvas(240, 150)
    tl = build_tiles.last if hasattr(build_tiles, 'last') else None
    deck_y = 64
    if tl is not None:
        for i in range(15):
            demo.blit(tl.a[12 * 16:13 * 16, (i % 4) * 16:(i % 4) * 16 + 16], i * 16, deck_y)
    for i, bx in enumerate(range(8, 240, 48)):
        nm = 'post_torn' if i == 2 else 'post'
        for k in range(2):
            demo.blit(P[nm if k == 0 else 'post'].a, bx, deck_y + 16 + k * 48)

    def place(nm, x, y):
        demo.blit(P[nm].a, x - PV[nm][0], y - PV[nm][1])
    place('tender', 60, deck_y)
    place('loco', 132, deck_y)
    for (cx, cy) in LOCO_DRIVERS:
        place('wheel', 132 - 48 + cx, deck_y - 56 + cy)
    place('smoke', 166, 4); place('smoke', 152, 10)
    place('rowboat', 190, 146)
    place('hose_valve', 208, 120)
    place('hose_cut', 226, 120)
    return sheet, demo


# ============================================================================
# PREVIEW SHEET
# ============================================================================
def build_preview(built):
    from PIL import ImageFont
    K = 3
    font = ImageFont.load_default()
    blocks = []

    def on_checker(img):
        bg = Image.new('RGBA', img.size, (58, 62, 74, 255))
        ch = Image.new('RGBA', img.size, (70, 74, 88, 255))
        mask = Image.fromarray(((np.indices((img.height, img.width)).sum(0) // 8) % 2 * 255).astype(np.uint8))
        bg.paste(ch, (0, 0), mask)
        bg.alpha_composite(img)
        return bg
    for k in ('tiles', 'people', 'animals', 'props', 'decor'):
        blocks.append((k + '.png', scaled(on_checker(built[k].image()), K)))
    blocks.append(('boss_shovel.png', scaled(on_checker(built['shovel'].image()), K)))
    blocks.append(('boss_shovel (assembled)', scaled(on_checker(built['shovel_demo'].image()), K)))
    blocks.append(('boss_train.png', scaled(on_checker(built['train'].image()), K)))
    blocks.append(('boss_train (assembled)', scaled(on_checker(built['train_demo'].image()), K)))
    for area in AREAS:
        sky, far, mid = built['bgs'][area]
        im = sky.image().copy()
        im.alpha_composite(far.image())
        im.alpha_composite(mid.image())
        blocks.append(('bg_%s (sky+far+mid)' % area, scaled(im, K)))
    blocks.append(('bg_cave.png', scaled(built['bgs']['cave'].image(), K)))
    # layout: shelf-pack the blocks, labelled
    pad, lab = 14, 16
    W = max(b.width for _, b in blocks) + 2 * pad
    placed, x, y, shelf = [], pad, pad, 0
    for name, b in blocks:
        if x + b.width + pad > W:
            x, y, shelf = pad, y + shelf + pad + lab, 0
        placed.append((name, b, x, y))
        x += b.width + pad
        shelf = max(shelf, b.height)
    H = y + shelf + lab + pad
    sheet = Image.new('RGBA', (W, H), (24, 22, 30, 255))
    d = ImageDraw.Draw(sheet)
    for name, b, x, y in placed:
        d.text((x, y), name, fill=(230, 220, 200, 255), font=font)
        sheet.alpha_composite(b, (x, y + lab))
    sheet.save(os.path.join(OUT, '_preview_sheet.png'))


# ============================================================================
# main
# ============================================================================
def scaled(img, k=3):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def main():
    os.makedirs(OUT, exist_ok=True)
    built = {}
    built['tiles'] = build_tiles()
    built['people'] = build_people()
    built['animals'] = build_animals()
    built['props'] = build_props()
    built['decor'] = build_decor()
    built['shovel'], built['shovel_demo'] = build_boss_shovel()
    built['train'], built['train_demo'] = build_boss_train()
    built['bgs'] = build_backgrounds()
    build_preview(built)
    print('done')


if __name__ == '__main__':
    main()
