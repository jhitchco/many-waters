"""Builds the Many Waters world map.

Writes data/world.txt (one character per 16px tile), data/entities.json, data/decor.json,
data/regions.json and data/meta.json, renders data/_world_preview.png, and checks the
design three ways:

  1. Progression. Starting with no abilities, it repeatedly finds everything the creature
     can reach (crawling, falling, and flinging a tentacle at any rough surface in reach),
     unlocks a memory once three of that kind of person are reachable, and reports which
     graves each new memory opens.
  2. Order. It confirms the first three towns' memories can be earned in any order, and
     that the Works can be entered two different ways.
  3. Traps. At every stage, every place the creature can reach must have a way back to
     where it woke (the basin is the one deliberate one-way drop).

Tile legend
  .  open          #  rock (climbable)      d  soft earth (Shovel)
  w  timber jam (Axe)                        g  granite (Charge)
  f  false stone (Level)                     c  concrete (not climbable)
  X  sheer cliff (not climbable)             b  rotten boards (break under a heavy body)
  t  trestle deck (climbable)                h  living root (climbable)
"""
import itertools, json, math, os, sys
from collections import deque

W, H = 420, 136
SURF = 60                   # town ground row
FLOOD_ROW = 50.6            # full pool (just under the intake platform top)
BASIN_X0 = 351              # basin floor starts here
BASIN_FLOOR = 100
FLING = 6                   # tiles a flung tentacle is guaranteed to reach
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

g = [['.'] * W for _ in range(H)]
G = [SURF] * W
ents, decor, regions = [], [], []


def fill(x0, y0, x1, y1, ch):
    for y in range(max(0, y0), min(H - 1, y1) + 1):
        for x in range(max(0, x0), min(W - 1, x1) + 1):
            g[y][x] = ch


def carve(x0, y0, x1, y1):
    fill(x0, y0, x1, y1, '.')


def ground(x, frm=1, deck=False):
    """First row whose top a walker could stand on. Skips the trestle deck unless asked."""
    for y in range(max(1, frm), H):
        if g[y][x] != '.' and (deck or g[y][x] != 't') and g[y - 1][x] == '.':
            return y
    raise ValueError(f'no ground at x={x} from row {frm}')


def ent(t, x, frm=1, deck=False, **kw):
    ents.append(dict(t=t, x=x, y=ground(x, frm, deck), **kw))


def dec(k, x, frm=1, layer='back', deck=False, **kw):
    decor.append(dict(k=k, x=x, y=ground(x, frm, deck), layer=layer, **kw))


def region(name, x0, y0, x1, y1):
    regions.append(dict(name=name, x0=x0, y0=y0, x1=x1, y1=y1))


# ---------------------------------------------------------------- shapes
def terrain():
    for x in range(W):
        fill(x, G[x], x, H - 1, '#')
        g[G[x]][x] = 'd'
    fill(0, 0, 1, SURF - 1, 'X')
    fill(0, SURF, 1, H - 1, '#')
    fill(0, H - 1, W - 1, H - 1, '#')


def island(x0, x1, top=49):
    """A sheer-sided hilltop. Too tall to fling to from the valley floor; once the
    valley floods, its top sits just above the water."""
    fill(x0, top + 1, x1, SURF - 1, 'X')
    fill(x0, top, x1, top, '#')


def mound(x0, x1, top, step=2):
    """A climbable rocky hill with stepped sides."""
    for i, x in enumerate(range(x0, x1 + 1)):
        edge = min(i, x1 - x)
        t = max(top, SURF - 1 - edge * step)
        fill(x, t, x, SURF - 1, '#')
        g[t][x] = 'd'


def ridge(x0, gate):
    """The hills between towns: sheer above, a 3-tile pass at ground level."""
    fill(x0, 0, x0 + 3, SURF - 7, 'X')
    fill(x0, SURF - 6, x0 + 3, SURF - 4, '#')
    if gate:
        fill(x0, SURF - 3, x0 + 3, SURF - 1, gate)
    else:
        fill(x0, SURF - 3, x0 + 3, SURF - 1, 'X')
    fill(x0, SURF, x0 + 3, H - 1, '#')


def pillar(x, y0, y1, w=2):
    fill(x, y0, x + w - 1, y1, '#')


def build():
    for x in range(BASIN_X0, 411):
        G[x] = BASIN_FLOOR
    terrain()

    # ================================================================ I. ENFIELD (x 2-89)
    # the lair, deep under the Rich farm
    carve(6, 112, 28, 122)
    pillar(15, 112, 115); pillar(21, 112, 116, 1)
    carve(22, 100, 25, 112)                            # shaft up into the Under-Valley
    # the Under-Valley: a wide cavern of hanging rock, crossed by flinging
    carve(10, 92, 84, 108)
    for x, a, b in ((18, 92, 97), (30, 92, 99), (44, 92, 96), (58, 92, 100), (72, 92, 97)):
        pillar(x, a, b, 3)                             # hanging rock
    for x, a, b in ((36, 103, 108), (64, 101, 108)):
        pillar(x, a, b, 2)                             # stalagmites
    carve(46, 108, 60, 124)                            # the Drop: falls to the deep road
    fill(44, 107, 45, 108, 'X'); fill(61, 107, 62, 108, 'X')
    # root cellar, between the Under-Valley and the town
    carve(30, 74, 62, 84)
    carve(40, 85, 43, 91)                              # up from the Under-Valley
    carve(62, 60, 64, 73)                              # up to Enfield village
    pillar(46, 74, 77, 2)
    # Shaw family crypt under the Rich farm (Shovel)
    carve(4, 64, 15, 69); fill(9, 61, 11, 63, 'd')
    # Quabbin Hill: climbable, with the future island on top
    mound(20, 40, 46, 2)
    island(28, 32, 40)                                 # summit stays out of reach until the flood
    carve(24, 52, 36, 57); carve(20, 58, 24, 59)       # hill cave, entered from the west foot
    fill(25, 58, 36, 58, '#')
    # town hall cellar (heavy)
    carve(50, 63, 60, 67); fill(52, 60, 57, 62, 'b')
    # the sawmill: timber walls (Axe)
    fill(66, 48, 84, 59, 'w'); carve(68, 50, 82, 59)    # the Foreman's arena
    fill(66, 47, 84, 47, '#')
    # a niche above the Under-Valley's ceiling, reached by flinging (Root Heart)
    carve(66, 86, 67, 91); carve(68, 86, 71, 88)
    # Swift River caves, west half sealed by granite at both ends (Charge)
    carve(64, 76, 84, 84)
    fill(62, 77, 63, 83, 'g')
    carve(60, 78, 61, 82)
    ridge(86, 'w')

    # ================================================================ II. GREENWICH (x 90-179)
    carve(88, 76, 128, 84)                             # Swift River caves, east
    fill(85, 77, 87, 83, 'g')                          # granite between the halves
    carve(85, 100, 140, 104)                           # Under-Valley branch east
    carve(112, 85, 114, 99)                            # up into the crypt
    carve(104, 62, 122, 75)                            # church crypt
    fill(107, 60, 113, 61, 'b')                        # church floor (heavy)
    fill(118, 61, 120, 61, 'd')                        # soft earth into the crypt (Shovel)
    carve(104, 60, 105, 61)                            # the crypt stair, open to the yard
    # cemetery ledges: a rocky rise to climb, graves on top
    mound(138, 150, 50, 2)
    carve(141, 55, 147, 58)                            # cave under the rise
    carve(138, 58, 140, 59)
    # bone room behind a crawlway (small)
    carve(152, 60, 153, 62)
    carve(154, 62, 158, 62)
    carve(159, 61, 164, 65)
    island(160, 165)                                   # Mount Pomeroy (flood)
    carve(160, 56, 165, 59)                            # an arch through its foot
    ridge(176, None)
    fill(172, 60, 186, 66, 'd')                        # deep soft earth under the ridge (Shovel)

    # ================================================================ III. DANA (x 180-269)
    carve(186, 96, 252, 110)                           # the mill race
    carve(190, 111, 196, 117)                          # down to the deep road
    for x in (204, 222, 238):
        pillar(x, 96, 100, 2)
    carve(240, 60, 242, 95)                            # up to Dana common
    fill(212, 111, 214, 111, 'f'); carve(208, 112, 220, 116)   # sealed room (Level)
    island(206, 212)                                   # Dana hill (flood)
    carve(206, 56, 212, 59)                            # an arch through its foot
    mound(222, 232, 52, 2)                             # orchard knoll
    carve(253, 100, 255, 104)                          # the mill race runs on into the diversion tunnel
    ridge(266, 'f')

    # ================================================================ IV. THE WORKS (x 270-349)
    # the diversion tunnel: a second way in (Axe + Shovel)
    carve(252, 100, 252, 104)
    carve(256, 100, 300, 104)
    fill(258, 100, 259, 104, 'w')                      # timber cofferdam (Axe)
    fill(266, 100, 269, 104, 'd')                      # soft earth under the ridge (Shovel)
    fill(272, 99, 300, 99, 'c'); fill(272, 105, 300, 105, 'c')
    carve(298, 66, 300, 99)                            # shaft up into the spillway cut
    # the spillway cut: a chasm across the works, crossed by flinging
    carve(284, 60, 312, 76)
    pillar(304, 66, 76, 2)                             # the steam shovel works from the west end
    fill(260, 60, 266, 61, 'b'); carve(259, 62, 267, 67)       # trestle pit (heavy)
    mound(316, 330, 44, 1)                             # the earthen dam rising
    fill(322, 44, 323, 59, 'c')                        # its concrete core
    ridge(346, 'g')

    # ================================================================ V. THE BASIN (x 350-419)
    fill(349, SURF, 350, BASIN_FLOOR - 1, 'c')
    fill(411, 0, 419, BASIN_FLOOR - 1, 'c')
    fill(398, 50, 410, 50, '#')                        # intake platform
    for x in (360, 378):
        pillar(x, 84, 99, 2)                           # drowned chimneys
    # the deep road east to Dana, carved last so the ridges above don't seal it
    carve(46, 118, 196, 122)
    pillar(90, 118, 119, 2); pillar(120, 121, 122, 3)
    fill(168, 118, 175, 121, '#')                                         # a crawlway along the floor, row 122
    fill(124, 123, 125, 123, 'f'); carve(121, 124, 128, 128)              # a sealed room under the road (Root Heart)

    # ---------------- the Hollow: living roots at the bottom of the valley, where it began
    fill(58, 124, 116, 134, 'h')
    carve(61, 125, 113, 133)
    for x, a, b in ((72, 125, 128), (84, 130, 133), (96, 125, 127), (106, 130, 133)):
        fill(x, a, x + 1, b, 'h')
    fill(70, 123, 71, 124, 'f')                        # a false floor in the deep road (Level)
    fill(104, 123, 105, 124, 'd')                      # or dig down (Shovel)

    # ---------------- the Rabbit Run: the old railroad on a trestle high over Dana
    fill(233, 44, 265, 44, 't')
    carve(266, 41, 269, 43); fill(266, 41, 267, 43, 'w')   # rail tunnel through the ridge, jammed with timber (Axe)
    fill(270, 44, 278, 44, 't')                        # the works siding

    # ---------------- regions (named places)
    for args in (("The Hollow", 58, 123, 116, 135), ("The Rabbit Run", 231, 34, 279, 46), ("The kennels", 184, 46, 198, 59),
                 ("The lair", 4, 110, 30, 124), ("The Under-Valley", 8, 90, 86, 109), ("The deep road", 44, 110, 198, 124),
                 ("The root cellar", 28, 72, 64, 86), ("The Rich farm", 2, 40, 18, 61), ("The Shaw family plot", 3, 62, 16, 70),
                 ("Quabbin Hill", 19, 30, 41, 59), ("Enfield village", 42, 40, 68, 59), ("Enfield town hall cellar", 49, 62, 61, 68),
                 ("The sawmill", 68, 40, 85, 59), ("The Swift River caves", 58, 74, 130, 86),
                 ("Greenwich", 90, 30, 136, 59), ("The church crypt", 103, 60, 123, 76), ("The cemetery rise", 137, 40, 151, 59),
                 ("The bone room", 151, 60, 165, 66), ("Mount Pomeroy", 165, 30, 172, 59),
                 ("Dana common", 180, 30, 265, 59), ("The mill race", 185, 94, 254, 118), ("Dana hill", 205, 30, 213, 59),
                 ("The works", 270, 30, 345, 59), ("The spillway cut", 283, 60, 313, 77), ("The diversion tunnel", 252, 98, 301, 106),
                 ("The earthen dam", 315, 40, 331, 59), ("Prescott, drowned", 351, 60, 410, 100), ("The intake", 396, 30, 411, 50)):
        region(*args)

    # ---------------- people and animals
    for x in (8, 16, 38, 44, 59): ent('R', x)
    ent('R', 48, id='amos')
    ent('P', 54, id='marion'); ent('P', 50)
    for x in (4, 34, 132): ent('D', x)
    for x in (20, 96, 150, 272, 340): ent('U', x)                     # burners
    for x in (100, 200, 330): ent('H', x)                             # tracker dogs
    ent('M', 75, 50)                                                  # the Foreman
    ent('Z', 289, 61)                                                 # the steam shovel
    ent('Y', 236, 30, deck=True)                                                 # the last train (on the trestle)
    ent('V', 191)                                                     # the houndmaster
    ent('X', 392, 80)                                                 # the diver (after the flood)
    for x in (96, 124, 134, 146, 158): ent('B', x)
    ent('P', 100)
    for x in (192, 200, 218, 236, 250): ent('K', x, id='ballou' if x == 236 else None)
    ent('P', 196); ent('P', 246)
    for x in (226, 258): ent('S', x)
    for x in (276, 316, 326, 336): ent('E', x)
    ent('E', 282, id='pike_e')
    for x in (278, 314, 334): ent('G', x)
    ent('G', 401, 40); ent('G', 407, 40)
    for e in ents:
        e.pop('id', None) if e.get('id') is None else None

    # ---------------- graves: (id, x, scan-from row)
    for gid, x, frm in (
        ('thankful', 12, 113), ('hale', 26, 113),                     # the lair (Thankful starts the first memory)
        ('doane', 70, 101), ('fay_e', 50, 119),                       # Under-Valley, the Drop
        ('cutler_j', 68, 77), ('cutler_m', 80, 77),                    # Swift west (Charge)
        ('ward_l', 52, 64), ('ward_o', 59, 64),                        # town hall cellar (heavy)
        ('stone', 6, 65), ('shaw', 14, 65),                            # Shaw crypt (Shovel)
        ('gould', 31, 30),                                             # Quabbin Hill summit (flood)
        ('woods', 30, 53),                                             # hill cave
        ('sawyer', 78, 50),                                            # inside the sawmill (Axe)
        ('clough', 100, 77),                                           # Swift east
        ('rand', 106, 63), ('pierce', 120, 63),                        # church crypt
        ('pease', 126, 1), ('lyon_b', 129, 1), ('lyon_l', 131, 1),     # cemetery
        ('tyler', 144, 40), ('eli', 140, 40),                          # cemetery rise top (Eli's memory)
        ('child', 162, 62),                                            # bone room (small)
        ('bartlett', 164, 40),                                         # Mount Pomeroy (flood)
        ('barlow_i', 184, 1), ('barlow_m', 262, 1),                    # Dana roadside
        ('ellis_n', 209, 40),                                          # Dana hill (flood)
        ('vaughn', 200, 97), ('alden', 230, 97),                       # mill race
        ('clara', 216, 112),                                           # sealed room (Level)
        ('lucy', 246, 97),
        ('pike', 263, 62),                                             # trestle pit (heavy)
        ('kittredge', 280, 100),                                       # diversion tunnel
        ('works_plot', 272, 1),
        ('phebe', 356, 80), ('fay_z', 370, 80), ('fay_es', 390, 80),   # drowned Prescott
        ('first', 64, 126), ('cooley', 110, 126),                      # the Hollow
    ):
        ent('T', x, frm, id=gid)

    for x, frm in ((9, 113), (35, 1), (114, 101), (150, 1), (160, 119), (224, 97), (310, 1)):
        ent('W', x, frm)                                               # springs
    for x, frm in ((18, 113), (34, 99), (46, 75), (44, 1), (92, 1), (116, 63), (128, 1), (188, 1),
                   (214, 97), (244, 1), (274, 1), (296, 101), (340, 1), (365, 80)):
        ent('C', x, frm)                                               # cellar holes
    for x, frm, after in ((13, 1, 'axe'), (40, 1, 'axe'), (86, 1, 'axe'), (286, 1, ''), (334, 1, ''), (326, 1, '')):
        ent('F', x, frm, after=after)                                  # brush fires
    for hid, x, frm in (('long_reach', 29, 30), ('quick_tendons', 70, 86), ('regrowth', 126, 124), ('old_blood', 161, 40),
                        ('thick_hide', 90, 126)):
        ent('Q', x, frm, id=hid)                                       # Root Hearts
    for lid, x, frm in (('notice', 7, 1), ('diary', 56, 64), ('sermon', 110, 63), ('ledger', 145, 55), ('survey', 208, 97),
                        ('telegram', 333, 1), ('child', 161, 62), ('last', 372, 80)):
        ent('L', x, frm, id=lid)                                       # papers left behind
    ent('I', 404, 40)
    ents.append(dict(t='@', x=20, y=121))

    # ---------------- decor
    for x, k in ((5, 'white_pine'), (14, 'maple_red'), (42, 'maple_gold'), (48, 'maple_orange'), (62, 'maple_red'),
                 (66, 'white_pine'), (84, 'maple_gold')):
        dec(k, x, clear='axe')
    for x in (22, 25, 36, 39):
        dec('maple_orange', x, 40, clear='axe')
    dec('maple_red', 30, 30); dec('farmhouse', 9); dec('town_hall', 55)
    for x, k in ((94, 'birch'), (100, 'farmhouse'), (110, 'church'), (133, 'birch'), (152, 'maple_gold'), (168, 'birch'), (174, 'maple_red')):
        dec(k, x)
    dec('white_pine', 163, 40); dec('maple_gold', 146, 40)
    for x, k in ((183, 'apple_tree'), (190, 'barn'), (198, 'apple_tree'), (216, 'farmhouse'), (226, 'apple_tree'),
                 (230, 'apple_tree'), (248, 'mill'), (258, 'apple_tree')):
        dec(k, x)
    dec('apple_tree', 209, 40)
    for x in range(276, 284, 4): dec('trestle', x)
    dec('crane', 314); dec('town_hall', 338)
    dec('drowned_steeple', 384, 80); dec('stone_bridge', 370, 80); dec('intake_tower', 404, 40)
    for x, frm in ((10, 113), (16, 113), (26, 113), (24, 101), (52, 101), (70, 101), (48, 119), (100, 119), (150, 119),
                   (36, 75), (56, 75), (70, 77), (98, 77), (196, 97), (240, 97), (212, 112)):
        dec('p:12', x, frm, 'front')
    dec('p:13', 112, 63); dec('p:13', 216, 112); dec('p:13', 72, 50)
    for x, frm in ((14, 113), (142, 40), (218, 112), (358, 80)):
        dec('p:21', x, frm)                                            # memory stones
    dec('p:24', 222, 52); dec('p:25', 262); dec('p:29', 277, 30, deck=True)       # water tower, signal, buffer stop
    for x in (186, 196): dec('p:26', x)                                # kennel pens
    dec('p:20', 189)
    for x, frm in ((66, 126), (78, 126), (92, 126), (102, 126), (112, 126)): dec('p:27', x, frm, 'front')
    for x, frm in ((74, 129), (98, 128)): dec('p:28', x, frm)          # egg sacs
    dec('p:30', 366, 80); dec('p:31', 300, 1)
    for x in (4, 66, 98, 124): dec('p:9', x)
    for x in (182, 220, 252): dec('p:14', x)
    for x in (44, 60, 80): dec('p:8', x)
    dec('p:7', 50); dec('p:7', 72)
    for x in (194, 206, 228, 244): dec('p:6', x)
    for x in (3, 38, 90, 118, 156, 180, 262): dec('p:10', x, 1, 'front')
    for x in (20, 68, 104, 136, 186, 214, 252): dec('p:11', x, 1, 'front')
    dec('p:15', 33); dec('p:15', 154); dec('p:15', 270)


# ---------------------------------------------------------------- checking
CLING = set('#dwgfbth')
DIRS = [(math.cos(a), math.sin(a)) for a in (i * math.pi / 8 for i in range(16))]


def blocked(ch, ab):
    if ch == '.': return False
    if ch == 'd': return 'shovel' not in ab
    if ch == 'w': return 'axe' not in ab
    if ch == 'g': return 'charge' not in ab
    if ch == 'f': return 'level' not in ab
    if ch == 'b': return 'heavy' not in ab
    return True


def explore(ab, flood):
    def open_(x, y):
        return 0 <= x < W and 0 <= y < H and not blocked(g[y][x], ab)

    def supported(x, y):
        if flood and y >= FLOOD_ROW - 0.5: return True
        if g[y][x] == 'd': return True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and g[yy][xx] in CLING and (blocked(g[yy][xx], ab) or g[yy][xx] == 'd'):
                    return True
        return False

    def fling(x, y):
        out = []
        for dx, dy in DIRS:
            last = None
            for s in range(1, FLING + 1):
                xx, yy = int(round(x + dx * s)), int(round(y + dy * s))
                if not (0 <= xx < W and 0 <= yy < H):
                    break
                if blocked(g[yy][xx], ab):
                    if g[yy][xx] in CLING and last:
                        out.append(last)
                    break
                last = (xx, yy)
        return out

    start = next((e['x'], e['y'] - 1) for e in ents if e['t'] == '@')
    seen = {start}
    edges = {}
    q = deque([start])
    while q:
        x, y = q.popleft()
        if supported(x, y):
            nbrs = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        elif not open_(x, y + 1):
            nbrs = [(x + 1, y), (x - 1, y)]                 # resting on a smooth floor: it can still slide
        else:
            nbrs = [(x, y + 1), (x + 1, y + 1), (x - 1, y + 1)]
        nbrs += fling(x, y)
        nb = [n for n in nbrs if open_(*n)]
        edges[(x, y)] = nb
        for n in nb:
            if n not in seen:
                seen.add(n); q.append(n)
    return seen, edges, start


def returnable(seen, edges, start):
    rev = {}
    for a, bs in edges.items():
        for b in bs:
            rev.setdefault(b, []).append(a)
    back = {start}
    q = deque([start])
    while q:
        c = q.popleft()
        for p in rev.get(c, []):
            if p not in back:
                back.add(p); q.append(p)
    return back


def near(e, cells):
    return any((e['x'] + dx, e['y'] - 1 - dy) in cells for dx in (-1, 0, 1) for dy in (0, 1))


UNL = {'R': 'axe', 'B': 'shovel', 'K': 'level', 'E': 'charge'}


def progression(order=None, verbose=True):
    """Simulates a run. With `order`, only unlocks the first three memories in that order."""
    ab, flood = set(), False
    log, got = [], set()
    traps = set()
    for _ in range(16):
        cells, edges, start = explore(ab, flood)
        back = returnable(cells, edges, start)
        traps |= {c for c in cells - back if c[0] < BASIN_X0 - 2 and not flood}
        people = {}
        for e in ents:
            if e['t'] in 'RBKEG' and near(e, cells):
                people[e['t']] = people.get(e['t'], 0) + 1
        new = set(ab)
        if sum(1 for e in ents if e['t'] in 'RBKEGPDS' and near(e, cells)) >= 6:
            new.add('heavy')
        cand = [UNL[t] for t, n in people.items() if n >= 3 and t in UNL]
        if order:
            for a in order:
                if a in cand and a not in new:
                    new.add(a)
                    break
            if 'charge' in cand: new.add('charge')
        else:
            new |= set(cand)
        gr = {e['id'] for e in ents if e['t'] in 'TQL' and near(e, cells)}
        log.append((sorted(ab), flood, sorted(gr - got)))
        got |= gr
        basin = any((x, y) in cells for x in range(BASIN_X0 + 1, 410) for y in range(90, BASIN_FLOOR))
        if new == ab:
            if basin and not flood:
                flood = True
                continue
            break
        ab = new
    cells, _, _ = explore(ab, True)
    intake = next(e for e in ents if e['t'] == 'I')
    ok_intake = any((intake['x'] + dx, intake['y'] - 1) in cells for dx in range(-4, 4))
    missing = {e['id'] for e in ents if e['t'] in 'TQL'} - got
    return log, ok_intake, missing, traps, ab


def works_routes():
    """The Works must open by the Level alone, and separately by the Axe with the Shovel."""
    res = {}
    for name, ab in (('level only', {'level', 'heavy'}), ('axe + shovel', {'axe', 'shovel', 'heavy'})):
        cells, _, _ = explore(ab, False)
        res[name] = any((x, y) in cells for x in range(272, 283) for y in range(50, 60))
    return res


def preview():
    try:
        from PIL import Image
    except ImportError:
        return
    col = {'t': (110, 70, 40), 'h': (150, 40, 60), '.': (20, 26, 40), '#': (70, 80, 96), 'd': (120, 84, 52), 'w': (150, 96, 40), 'g': (190, 170, 170),
           'f': (90, 100, 120), 'c': (120, 130, 125), 'X': (40, 44, 58), 'b': (170, 130, 70)}
    im = Image.new('RGB', (W, H))
    for y in range(H):
        for x in range(W):
            c = col[g[y][x]]
            if g[y][x] == '.' and y >= FLOOD_ROW: c = (24, 50, 70)
            im.putpixel((x, y), c)
    mark = {'Y': (255, 255, 255), 'V': (255, 255, 255), 'X': (255, 255, 255), 'U': (255, 160, 40), 'H': (160, 110, 60), 'M': (255, 0, 0), 'Z': (255, 255, 255), 'Q': (255, 0, 120), 'L': (255, 255, 255), 'R': (220, 40, 40), 'B': (140, 90, 40), 'K': (210, 190, 120), 'E': (60, 100, 220), 'G': (60, 160, 60),
            'P': (250, 250, 250), 'T': (255, 220, 80), 'W': (60, 220, 230), 'C': (255, 60, 160), 'I': (255, 255, 0),
            '@': (255, 0, 255), 'D': (200, 140, 90), 'S': (230, 230, 230), 'F': (255, 120, 0)}
    for e in ents:
        im.putpixel((e['x'], max(0, e['y'] - 1)), mark[e['t']])
    im = im.resize((W * 4, H * 4), Image.NEAREST)
    im.save(os.path.join(ROOT, 'data', '_world_preview.png'))


def main():
    build()
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    with open(os.path.join(ROOT, 'data', 'world.txt'), 'w', newline='\n') as f:
        f.write('\n'.join(''.join(r) for r in g) + '\n')
    for name, obj in (('entities', ents), ('decor', decor), ('regions', regions)):
        with open(os.path.join(ROOT, 'data', name + '.json'), 'w', newline='\n') as f:
            json.dump(obj, f, indent=0)
    intake = next(e for e in ents if e['t'] == 'I')
    meta = dict(w=W, h=H, surf=SURF, flood_row=FLOOD_ROW, flood_start_row=BASIN_FLOOR - 0.4, basin_x0=BASIN_X0,
                flood_trigger=[BASIN_X0, BASIN_FLOOR - 14], intake=[intake['x'], intake['y']],
                zones=[[0, 90], [90, 180], [180, 270], [270, 349], [349, 420]])
    with open(os.path.join(ROOT, 'data', 'meta.json'), 'w', newline='\n') as f:
        json.dump(meta, f, indent=1)
    preview()

    log, ok_intake, missing, traps, ab = progression()
    for a, flood, fresh in log:
        print(f"abilities={a or ['none']} flood={flood}: new graves {fresh}")
    print('intake reachable:', ok_intake)
    print('unreachable graves or hearts:', sorted(missing) or 'none')
    print('trap cells (reachable, no way back):', len(traps), sorted(traps)[:12])
    bad = not ok_intake or bool(missing) or bool(traps)
    cells, _, _ = explore(set(), False)
    for t, a in (('R', 'axe'), ('B', 'shovel'), ('K', 'level')):
        n = sum(1 for e in ents if e['t'] == t and near(e, cells))
        print(f"from the start, {a:7s} can be earned first: {'yes' if n >= 3 else 'NO'} ({n} reachable)")
        bad |= n < 3
    flood_only = {'bartlett', 'ellis_n', 'old_blood'}
    early = set().union(*[set(fr) for _, fl, fr in log if not fl])
    leak = flood_only & early
    print('island graves reachable before the flood:', sorted(leak) or 'none')
    bad |= bool(leak)
    routes = works_routes()
    for k, v in routes.items():
        print(f"works entrance by {k}: {'yes' if v else 'NO'}")
        bad |= not v
    print(f"totals: graves={sum(e['t']=='T' for e in ents)} people={sum(e['t'] in 'RBKEGP' for e in ents)} "
          f"regions={len(regions)}")
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
