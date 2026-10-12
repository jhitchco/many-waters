"""Builds the Many Waters world map.

Writes data/world.txt (one character per 16px tile), data/entities.json and
data/decor.json, renders data/_world_preview.png, and runs a progression check:
starting with no abilities, it repeatedly finds everything the creature can
reach, unlocks abilities from the people it can take, and reports which graves
open up at each stage. The check fails loudly if the intake or any grave is
unreachable.

Tile legend
  .  open          #  rock (climbable)      d  soft earth (Shovel)
  w  timber jam (Axe)                        g  granite (Charge)
  f  false stone (Level)                     c  concrete (not climbable)
  X  sheer cliff (not climbable)             b  rotten boards (break under a heavy body)
"""
import json, os, sys
from collections import deque

W, H = 380, 110
SURF = 44                 # default ground row
FLOOD_ROW = 36.6          # full pool, in rows (just under the intake platform top)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

g = [['.'] * W for _ in range(H)]
G = [SURF] * W
ents, decor = [], []


def fill(x0, y0, x1, y1, ch):
    for y in range(max(0, y0), min(H - 1, y1) + 1):
        for x in range(max(0, x0), min(W - 1, x1) + 1):
            g[y][x] = ch


def carve(x0, y0, x1, y1):
    fill(x0, y0, x1, y1, '.')


def ground(x, frm=1):
    """Row whose top a walker stands on, scanning down from row `frm`."""
    for y in range(max(1, frm), H):
        if g[y][x] != '.' and g[y - 1][x] == '.':
            return y
    raise ValueError(f'no ground at x={x} from row {frm}')


def ent(t, x, frm=1, **kw):
    ents.append(dict(t=t, x=x, y=ground(x, frm), **kw))


def dec(k, x, frm=1, layer='back'):
    decor.append(dict(k=k, x=x, y=ground(x, frm), layer=layer))


# ---------------------------------------------------------------- terrain
def terrain():
    for x in range(W):
        fill(x, G[x], x, H - 1, '#')
        g[G[x]][x] = 'd'                     # one row of topsoil
    fill(0, 0, 1, SURF - 1, 'X')
    fill(0, SURF, 1, H - 1, '#')
    fill(0, H - 1, W - 1, H - 1, '#')


def hill(x0, x1, top):
    """A sheer-sided hill. Only its top row is climbable, so it can only be
    reached by swimming up to it once the valley floods."""
    fill(x0, top + 1, x1, SURF - 1, 'X')
    fill(x0, top, x1, top, '#')


def mound(x0, x1, top):
    """A climbable rocky rise with stepped sides."""
    for i, x in enumerate(range(x0, x1 + 1)):
        edge = min(i, x1 - x)
        t = max(top, SURF - 1 - edge * 2)
        fill(x, t, x, SURF - 1, '#')
        g[t][x] = 'd'


def ridge(x0, gate):
    """The hills between towns: sheer above, a 3-tile pass at ground level."""
    fill(x0, 0, x0 + 3, 37, 'X')
    fill(x0, 38, x0 + 3, 40, '#')
    fill(x0, 41, x0 + 3, 43, gate)
    fill(x0, SURF, x0 + 3, H - 1, '#')


def build():
    # basin floor sits much lower
    for x in range(315, 372):
        G[x] = 75
    terrain()

    # ---------------- I. Enfield (x 2-77)
    carve(6, 86, 26, 96)                       # the lair where it wakes
    carve(8, 100, 22, 105); fill(12, 97, 14, 99, 'f')      # hidden spring room (Level)
    carve(22, 62, 25, 86)                      # shaft up
    carve(16, 52, 40, 61)                      # root cave
    carve(38, 44, 40, 51)                      # opening to the surface
    hill(22, 32, 35)                           # Quabbin Hill (flood)
    carve(44, 52, 69, 60)                      # Swift River cave, west (Charge both ends)
    carve(41, 54, 43, 59); fill(41, 54, 43, 59, 'g')
    carve(46, 46, 55, 50); fill(48, 44, 53, 45, 'b')       # town hall cellar (heavy)
    carve(4, 47, 14, 51); fill(9, 45, 11, 46, 'd')        # Shaw family crypt (Shovel)
    ridge(74, 'w')

    # ---------------- II. Greenwich (x 78-157)
    carve(73, 52, 96, 60)                      # Swift River cave, east
    fill(70, 54, 72, 59, 'g')                  # plug between the two halves
    carve(94, 46, 110, 58)                     # church crypt
    fill(97, 44, 103, 45, 'b')                 # church floor (heavy)
    fill(108, 45, 110, 45, 'd')                # soft earth into the crypt (Shovel)
    carve(132, 44, 133, 46)                    # pit
    carve(134, 46, 139, 46)                    # crawlway (small)
    carve(140, 46, 145, 49)                    # bone room
    hill(135, 143, 35)                         # Mount Pomeroy (flood)
    ridge(154, '#'); fill(154, 0, 157, 43, 'X')
    fill(148, 44, 163, 50, 'd')                # deep soft earth under the ridge (Shovel)

    # ---------------- III. Dana (x 158-235)
    fill(184, 0, 187, 42, 'X'); carve(184, 43, 187, 43); fill(184, 44, 187, 47, '#')  # crawlway (small)
    hill(198, 205, 35)                         # Dana hill (flood)
    fill(192, 45, 194, 59, 'd')                # soft earth down to the mill race
    carve(166, 60, 232, 68)                    # mill race cave
    fill(223, 69, 225, 69, 'f'); carve(220, 70, 228, 74)   # false floor, sealed room (Level)
    carve(233, 61, 235, 67); fill(233, 61, 235, 67, 'g')   # plug to the diversion tunnel
    ridge(236, 'f')

    # ---------------- IV. The Works (x 240-309)
    carve(236, 61, 306, 65)                    # diversion tunnel
    fill(240, 60, 306, 60, 'c'); fill(240, 66, 306, 66, 'c')
    carve(300, 44, 302, 60)                    # shaft from the works into the tunnel
    fill(260, 44, 266, 45, 'b'); carve(259, 46, 267, 52)   # trestle pit (heavy)
    mound(274, 282, 40)
    ridge(306, 'g')

    # ---------------- V. The basin (x 310-379)
    fill(313, 44, 314, 74, 'c')
    fill(372, 0, 379, 74, 'c')
    fill(362, 36, 371, 36, '#')                # intake platform

    # ---------------- people, animals, graves, springs, cellar holes
    for x in (8, 16, 44, 58, 68): ent('R', x)
    ent('P', 56); ent('D', 20); ent('D', 62)
    for x in (84, 104, 116, 124, 146): ent('B', x)
    ent('P', 94); ent('S', 128)
    for x in (168, 196, 206, 216, 226): ent('K', x)
    ent('P', 172); ent('P', 212); ent('S', 178)
    for x in (248, 258, 270, 284, 296): ent('E', x)
    for x in (264, 280, 292): ent('G', x)
    ent('G', 364, 30); ent('G', 369, 30)

    graves = [  # (x, scan-from row)
        (10, 98), (19, 98),                    # hidden spring room
        (70, 1),                               # Enfield roadside
        (50, 53), (62, 53),                    # Swift west
        (47, 46), (54, 46),                    # town hall cellar
        (6, 47), (13, 47),                     # Shaw crypt
        (27, 30),                              # Quabbin Hill
        (85, 53),                              # Swift east
        (99, 47), (106, 47),                   # church crypt
        (112, 1), (115, 1), (118, 1), (121, 1), (124, 1),  # Greenwich cemetery
        (143, 47),                             # bone room
        (139, 30),                             # Mount Pomeroy
        (180, 1), (222, 1),                    # Dana roadside
        (201, 30),                             # Dana hill
        (172, 61), (214, 61),                  # mill race
        (226, 70),                             # sealed room
        (252, 1), (263, 47), (270, 62),        # works
        (322, 60), (340, 60), (356, 60),       # drowned Prescott
    ]
    for x, frm in graves: ent('T', x, frm)

    for x, frm in ((9, 90), (66, 1), (130, 1), (176, 1), (290, 1)): ent('W', x, frm)     # springs
    for x, frm in ((16, 90), (30, 53), (35, 1), (82, 1), (102, 47), (126, 1), (166, 1),
                   (190, 1), (200, 61), (244, 1), (288, 1), (311, 1), (330, 60)):
        ent('C', x, frm)                                                               # cellar holes
    ent('I', 368, 30)                                                                  # intake
    ents.append(dict(t='@', x=20, y=92))

    # ---------------- decor (bottom-centre anchored on the ground row)
    for x, k in ((5, 'white_pine'), (13, 'maple_red'), (19, 'maple_gold'), (35, 'maple_orange'),
                 (46, 'maple_red'), (60, 'white_pine'), (64, 'maple_gold'), (71, 'maple_orange')):
        dec(k, x)
    dec('maple_red', 27, 30); dec('town_hall', 51); dec('farmhouse', 9)
    for x, k in ((81, 'birch'), (88, 'farmhouse'), (100, 'church'), (127, 'maple_gold'), (131, 'birch'),
                 (147, 'birch'), (151, 'maple_red')):
        dec(k, x)
    dec('white_pine', 139, 30)
    for x, k in ((162, 'apple_tree'), (170, 'barn'), (178, 'apple_tree'), (192, 'mill'),
                 (210, 'farmhouse'), (219, 'apple_tree'), (229, 'apple_tree')):
        dec(k, x)
    dec('apple_tree', 202, 30)
    for x in range(242, 258, 4): dec('trestle', x)
    dec('crane', 286); dec('town_hall', 296)
    dec('drowned_steeple', 345, 60); dec('stone_bridge', 332, 60); dec('intake_tower', 368, 30)
    for x in (24, 30, 36): dec('p:12', x, 53, 'front')                      # glowing mushrooms
    for x in (10, 15, 20): dec('p:12', x, 90, 'front')
    for x in (180, 205, 228): dec('p:12', x, 61, 'front')
    dec('p:13', 102, 47); dec('p:13', 226, 70)
    for x in (54, 87, 120): dec('p:9', x)                                       # stone walls
    for x in (164, 220): dec('p:14', x)                                         # fences
    for x in (12, 42, 57): dec('p:8', x)                                        # stumps
    dec('p:7', 40); dec('p:7', 63)
    for x in (174, 196, 208, 224): dec('p:6', x)                                 # survey stakes
    for x in (3, 37, 77, 92, 134, 160, 232): dec('p:10', x, 1, 'front')          # ferns
    for x in (21, 66, 110, 150, 182, 214): dec('p:11', x, 1, 'front')           # wildflowers
    dec('p:15', 33); dec('p:15', 152); dec('p:15', 250)


# ---------------------------------------------------------------- progression check
CLING = set('#dwgfb')


def blocked(ch, ab):
    if ch == '.': return False
    if ch == 'd': return 'shovel' not in ab
    if ch == 'w': return 'axe' not in ab
    if ch == 'g': return 'charge' not in ab
    if ch == 'f': return 'level' not in ab
    if ch == 'b': return 'heavy' not in ab
    return True


def reach(ab, flood):
    def open_(x, y):
        return 0 <= x < W and 0 <= y < H and not blocked(g[y][x], ab)

    # local clearance: the creature can be made small (1 tile), so any open cell is passable,
    # but record whether a cell needs the small body
    def supported(x, y):
        if flood and y >= FLOOD_ROW - 0.5: return True
        if g[y][x] == 'd': return True             # burrowing
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H:
                    ch = g[yy][xx]
                    if ch in CLING and (blocked(ch, ab) or ch == 'd'):
                        return True
        return False

    start = next((e['x'], e['y'] - 1) for e in ents if e['t'] == '@')
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        if supported(x, y):
            nbrs = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        else:
            nbrs = [(x, y + 1), (x + 1, y + 1), (x - 1, y + 1)]
        for n in nbrs:
            if n not in seen and open_(*n):
                seen.add(n); q.append(n)
    return seen


def progression():
    ab, flood = set(), False
    order = []
    taken = {}
    reachable_graves = set()
    for _ in range(12):
        cells = reach(ab, flood)
        def near(e):
            return any((e['x'] + dx, e['y'] - 1 - dy) in cells for dx in (-1, 0, 1) for dy in (0, 1))
        people = {}
        for e in ents:
            if e['t'] in 'RBKEG' and near(e): people[e['t']] = people.get(e['t'], 0) + 1
        new = set(ab)
        if people.get('R', 0) >= 3: new.add('axe')
        if people.get('B', 0) >= 3: new.add('shovel')
        if people.get('K', 0) >= 3: new.add('level')
        if people.get('E', 0) >= 3: new.add('charge')
        if len([e for e in ents if e['t'] in 'RBKEGPD' and near(e)]) >= 6: new.add('heavy')
        basin = any((x, y) in cells for x in range(316, 371) for y in range(68, 75))
        gr = {(e['x'], e['y']) for e in ents if e['t'] == 'T' and near(e)}
        fresh = gr - reachable_graves
        reachable_graves |= gr
        order.append((sorted(ab), flood, len(gr), sorted(fresh)))
        if new == ab and (flood or not basin):
            break
        if new == ab and basin: flood = True
        ab = new
    intake = next(e for e in ents if e['t'] == 'I')
    cells = reach(ab, True)
    ok_intake = any((intake['x'] + dx, intake['y'] - 1) in cells for dx in range(-4, 4))
    allg = {(e['x'], e['y']) for e in ents if e['t'] == 'T'}
    return order, ok_intake, allg - reachable_graves


def preview():
    try:
        from PIL import Image
    except ImportError:
        return
    col = {'.': (20, 26, 40), '#': (70, 80, 96), 'd': (120, 84, 52), 'w': (150, 96, 40), 'g': (190, 170, 170),
           'f': (90, 100, 120), 'c': (120, 130, 125), 'X': (40, 44, 58), 'b': (170, 130, 70)}
    im = Image.new('RGB', (W, H))
    for y in range(H):
        for x in range(W):
            c = col[g[y][x]]
            if g[y][x] == '.' and y >= FLOOD_ROW: c = (24, 50, 70)
            im.putpixel((x, y), c)
    mark = {'R': (220, 40, 40), 'B': (140, 90, 40), 'K': (210, 190, 120), 'E': (60, 100, 220), 'G': (60, 160, 60),
            'P': (250, 250, 250), 'T': (255, 220, 80), 'W': (60, 220, 230), 'C': (255, 60, 160), 'I': (255, 255, 0),
            '@': (255, 0, 255), 'D': (200, 140, 90), 'S': (230, 230, 230)}
    for e in ents:
        im.putpixel((e['x'], max(0, e['y'] - 1)), mark[e['t']])
    im = im.resize((W * 4, H * 4), Image.NEAREST)
    im.save(os.path.join(ROOT, 'data', '_world_preview.png'))


def main():
    build()
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    with open(os.path.join(ROOT, 'data', 'world.txt'), 'w', newline='\n') as f:
        f.write('\n'.join(''.join(r) for r in g) + '\n')
    with open(os.path.join(ROOT, 'data', 'entities.json'), 'w') as f:
        json.dump(ents, f, indent=0)
    with open(os.path.join(ROOT, 'data', 'decor.json'), 'w') as f:
        json.dump(decor, f, indent=0)
    preview()
    order, ok_intake, missing = progression()
    for ab, flood, n, fresh in order:
        print(f"abilities={ab or ['none']} flood={flood}: {n} graves reachable, new: {fresh}")
    print('intake reachable:', ok_intake)
    print('unreachable graves:', sorted(missing) or 'none')
    print(f"totals: graves={sum(e['t']=='T' for e in ents)} people={sum(e['t'] in 'RBKEGP' for e in ents)}")
    if not ok_intake or missing:
        sys.exit(1)


if __name__ == '__main__':
    main()
