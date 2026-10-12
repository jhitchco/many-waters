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
# TILES  (128x192, 16x16 cells)
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
    sheet = Canvas(128, 192)
    rb = rock_base(rng)
    rows = [rock_tiles(rng, base=rb), dirt_tiles(rng), timber_tiles(rng), granite_tiles(rng),
            rock_tiles(rng, false_tell=True, base=rb), concrete_tiles(rng), cliff_tiles(rng),
            board_tiles(rng), grass_tiles(rng), ceiling_tiles(rng), special_tiles(rng), cave_tiles(rng)]
    for ri, row in enumerate(rows):
        for ci, t in enumerate(row):
            sheet.a[ri * T:(ri + 1) * T, ci * T:(ci + 1) * T] = t.a
    sheet.save('tiles.png')
    return sheet


# ============================================================================
# PEOPLE  (128x144: 8 cols x 6 rows of 16x24, facing right)
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
    sheet = Canvas(128, 144)
    for ri, role in enumerate(ROLE_ORDER):
        poses = WALK + [IDLE, STARTLED, GRABBED, ATTACK[role]]
        for ci, P in enumerate(poses):
            sheet.blit(draw_person(role, P), ci * 16, ri * 24)
    sheet.save('people.png')
    return sheet


# ============================================================================
# ANIMALS  (72x32: 3 cols x 2 rows of 24x16)
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
    sheet = Canvas(72, 32)
    for f in range(3):
        sheet.blit(deer(f), f * 24, 0)
        sheet.blit(sheep(f), f * 24, 16)
    sheet.save('animals.png')
    return sheet


# ============================================================================
# PROPS  (256x64: 8x2 cells of 32x32, bottom-aligned, centred)
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
    sheet = Canvas(256, 64)
    items = [p_headstone(), p_open_grave(), p_spring(0), p_spring(1), p_cellar(False), p_cellar(True),
             p_stake(), p_logpile(), p_stump(), p_wall(), p_fern(), p_flowers(), p_mushrooms(), p_lantern(),
             p_fence(), p_boulder()]
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
    built['bgs'] = build_backgrounds()
    build_preview(built)
    print('done')


if __name__ == '__main__':
    main()
