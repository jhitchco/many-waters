"""Synthesizes the score, ambient beds and extra sound effects (22.05 kHz, 16-bit mono).

Every piece is original, written for period instruments a 1930s Swift River town would
know: reed organ, fiddle, plucked strings, church bell and a choir. Music and ambient
beds loop seamlessly: each is rendered with its reverb tail wrapped back onto its start.

Writes assets/music/*.wav, assets/ambient/*.wav and more assets/sfx/*.wav.
"""
import os, wave
import numpy as np

SR = 22050
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rng = np.random.default_rng(1938)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def nm(s):
    """'A4', 'C#5', 'Bb3' -> midi number."""
    base = NOTE[s[0]]
    i = 1
    if s[i] == '#': base += 1; i += 1
    elif s[i] == 'b': base -= 1; i += 1
    return base + 12 * (int(s[i:]) + 1)


def save(path, x, gain=0.85):
    x = np.asarray(x, dtype=np.float64)
    peak = np.max(np.abs(x)) or 1.0
    x = np.clip(x / peak * gain, -1, 1)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def lowpass(x, k):
    k = max(1, int(k))
    return np.convolve(x, np.ones(k) / k, mode='same')


def adsr(n, a=0.02, r=0.2, sustain=1.0):
    e = np.full(n, sustain)
    na, nr = min(n, int(SR * a)), min(n, int(SR * r))
    if na: e[:na] = np.linspace(0, sustain, na)
    if nr: e[n - nr:] *= np.linspace(1, 0, nr)
    return e


# ---------------------------------------------------------------- instruments
def organ(f, d):
    t = np.arange(int(SR * d)) / SR
    w = sum(a * np.sin(2 * np.pi * f * h * t) for h, a in ((1, 1.0), (2, 0.55), (3, 0.3), (4, 0.18), (6, 0.08)))
    w += 0.12 * np.sign(np.sin(2 * np.pi * f * t))            # reed buzz
    return lowpass(w, 3) * adsr(t.size, 0.08, 0.35) * (1 + 0.05 * np.sin(2 * np.pi * 5.2 * t))


def fiddle(f, d):
    t = np.arange(int(SR * d)) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.18) * 4, 0, 1)
    ph = np.cumsum(f * vib) / SR
    saw = 2 * (ph % 1.0) - 1
    w = lowpass(saw, 6) + 0.25 * np.sin(2 * np.pi * ph * 2)
    bow = 1 + 0.15 * lowpass(rng.uniform(-1, 1, t.size), 200)
    return w * bow * adsr(t.size, 0.09, 0.25)


def pluck(f, d, bright=0.5):
    n = int(SR * d)
    p = max(2, int(round(SR / f)))
    out = np.zeros(n + p)
    out[:p] = rng.uniform(-1, 1, p) * (0.6 + bright * 0.4)
    k = p
    while k < n + p - 1:
        end = min(k + p, n + p)
        src = out[k - p:end - p + 1]
        seg = 0.498 * (src[:-1] + src[1:]) if src.size > 1 else src
        out[k:k + seg.size] = seg[:end - k]
        k = end
    return out[p:p + n] * adsr(n, 0.002, 0.05)


def bell(f, d):
    t = np.arange(int(SR * d)) / SR
    w = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * dc) for m, a, dc in
            ((1, 1.0, 0.9), (2.0, 0.6, 1.3), (2.4, 0.4, 1.8), (3.0, 0.3, 2.2), (4.2, 0.2, 3.0), (5.4, 0.12, 4.0)))
    return w * adsr(t.size, 0.002, 0.3)


FORMANTS = ((700, 130, 1.0), (1150, 160, 0.55), (2600, 250, 0.25))     # an open "ah"


def choir(f, d, voices=4):
    t = np.arange(int(SR * d)) / SR
    w = np.zeros(t.size)
    for v in range(voices):
        det = f * (1 + (v - voices / 2) * 0.004)
        vib = 1 + 0.004 * np.sin(2 * np.pi * (4.6 + v * 0.3) * t + v)
        ph = np.cumsum(det * vib) / SR
        for h in range(1, 28):
            fh = det * h
            if fh > 5000: break
            amp = sum(a * np.exp(-((fh - c) / bw) ** 2) for c, bw, a in FORMANTS) + 0.02 / h
            w += amp * np.sin(2 * np.pi * ph * h)
    return w * adsr(t.size, 0.6, 0.9)


def bass(f, d):
    t = np.arange(int(SR * d)) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * adsr(t.size, 0.05, 0.3)


def thud(d=0.5):
    t = np.arange(int(SR * d)) / SR
    return np.sin(2 * np.pi * (70 - 40 * t) * t) * np.exp(-t * 9) + lowpass(rng.uniform(-1, 1, t.size), 30) * np.exp(-t * 20) * 0.5


def clank(f=430, d=0.9):
    t = np.arange(int(SR * d)) / SR
    return sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * dc) for m, a, dc in
               ((1, 1, 5), (1.48, 0.7, 6), (2.21, 0.5, 8), (3.57, 0.3, 10))) + rng.uniform(-1, 1, t.size) * np.exp(-t * 60) * 0.4


# ---------------------------------------------------------------- arranging
class Track:
    def __init__(self, beats, bpm, tail=3.0):
        self.spb = 60.0 / bpm
        self.n = int(round(beats * self.spb * SR))
        self.buf = np.zeros(self.n + int(SR * (tail + 6)))

    def add(self, beat, sig, vol=1.0):
        i = int(round(beat * self.spb * SR))
        j = min(self.buf.size, i + sig.size)
        self.buf[i:j] += sig[:j - i] * vol

    def seq(self, inst, notes, start=0.0, vol=1.0, legato=1.0, octave=0):
        """notes: list of (name or None, beats)."""
        b = start
        for name, dur in notes:
            if name:
                for nmn in name.split('+'):
                    self.add(b, inst(midi(nm(nmn) + octave), dur * self.spb * legato), vol)
            b += dur
        return b

    def render(self, wet=0.35, decay=2.6):
        ir_n = int(SR * decay)
        t = np.arange(ir_n) / SR
        ir = rng.uniform(-1, 1, ir_n) * np.exp(-t * 6.9 / decay)
        ir = lowpass(ir, 4)
        ir /= np.sqrt(np.sum(ir ** 2))
        size = 1 << int(np.ceil(np.log2(self.buf.size + ir_n)))
        rev = np.fft.irfft(np.fft.rfft(self.buf, size) * np.fft.rfft(ir, size), size)[:self.buf.size]
        y = self.buf * (1 - wet) + rev * wet * 0.6
        out = y[:self.n].copy()
        tail = y[self.n:]
        out[:tail.size] += tail[:self.n] if tail.size > self.n else tail      # wrap the tail into the loop start
        return out


def chords(tr, inst, prog, beats_each, vol=0.5, start=0.0):
    b = start
    for c in prog:
        for nmn in c.split('+'):
            tr.add(b, inst(midi(nm(nmn)), beats_each * tr.spb * 1.02), vol)
        b += beats_each


# ---------------------------------------------------------------- pieces
def enfield():
    tr = Track(64, 66)
    prog = ['D3+A3+F4', 'D3+A3+F4', 'F3+C4+A4', 'A2+E3+C4', 'D3+A3+F4', 'C3+G3+E4', 'F3+C4+A4', 'C3+G3+E4',
            'D3+A3+F4', 'G2+D3+Bb3', 'C3+G3+E4', 'A2+E3+C4', 'F3+C4+A4', 'A2+E3+C4', 'C3+G3+E4', 'D3+A3+F4']
    chords(tr, organ, prog, 4, 0.35)
    for b in range(0, 64, 4):
        tr.add(b, bass(midi(nm('D2')), 4 * tr.spb), 0.35)
    mel = [('A4', 2), ('G4', 1), ('F4', 1), ('E4', 2), ('D4', 2), ('F4', 1), ('G4', 1), ('A4', 1), ('C5', 1), ('B4', 2), ('A4', 2),
           ('A4', 1), ('C5', 1), ('D5', 2), ('C5', 1), ('A4', 1), ('G4', 2), ('F4', 1), ('G4', 1), ('A4', 1), ('F4', 1), ('E4', 4),
           ('D5', 2), ('C5', 1), ('A4', 1), ('G4', 1), ('A4', 1), ('F4', 2), ('E4', 1), ('F4', 1), ('G4', 1), ('E4', 1), ('D4', 3), (None, 1),
           ('F4', 1), ('A4', 1), ('C5', 1), ('B4', 1), ('A4', 2), ('G4', 1), ('F4', 1), ('E4', 1), ('C4', 1), ('D4', 1), ('E4', 1), ('D4', 4)]
    tr.seq(fiddle, mel, 0, 0.55, 1.05)
    for b in (0, 32):
        tr.add(b, bell(midi(nm('D5')), 5.0), 0.15)
    return tr.render(0.3)


def greenwich():
    tr = Track(64, 54)
    prog = ['A2+E3+C4+A4', 'F2+C3+A3+C5', 'C3+G3+E4+G4', 'G2+D3+B3+D4', 'A2+E3+C4+E4', 'D3+A3+F4+D4', 'E2+B2+G#3+B3', 'A2+E3+C4+A4',
            'F2+C3+A3+F4', 'C3+G3+E4+C5', 'D3+A3+F4+A4', 'E2+B2+G#3+E4', 'A2+E3+C4+C5', 'F2+C3+A3+A4', 'E2+B2+G#3+G#4', 'A2+E3+C4+A4']
    chords(tr, organ, prog, 4, 0.45)
    for i, c in enumerate(prog):
        if i % 2 == 0:
            top = c.split('+')[-1]
            tr.add(i * 4, choir(midi(nm(top) - 12), 8 * tr.spb), 0.22)
    for b in (0, 32):
        tr.add(b, bell(midi(nm('A3')), 7.0), 0.3)
    return tr.render(0.45, 3.4)


def dana():
    tr = Track(64, 84)
    prog = [('G2', 'G3+B3+D4'), ('F2', 'F3+A3+C4'), ('C3', 'C4+E4+G4'), ('G2', 'G3+B3+D4')] * 4
    b = 0.0
    for root, tri in prog:
        tr.add(b, bass(midi(nm(root)), 4 * tr.spb), 0.3)
        notes = tri.split('+')
        pat = [notes[0], notes[1], notes[2], notes[1], notes[0], notes[2], notes[1], notes[2]]
        for k, n in enumerate(pat):
            tr.add(b + k * 0.5, pluck(midi(nm(n)), 1.4), 0.4)
        b += 4
    mel = [(None, 16), ('D5', 1.5), ('B4', 0.5), ('A4', 1), ('G4', 1), ('F5', 2), ('E5', 1), ('C5', 1), ('D5', 3), (None, 1), ('B4', 1), ('C5', 1), ('D5', 2),
           ('E5', 1.5), ('D5', 0.5), ('C5', 1), ('A4', 1), ('F4', 2), ('A4', 1), ('C5', 1), ('B4', 1), ('A4', 1), ('G4', 2), (None, 4),
           ('G5', 2), ('F5', 1), ('D5', 1), ('C5', 2), ('A4', 2), ('B4', 1), ('D5', 1), ('C5', 1), ('B4', 1), ('G4', 4)]
    tr.seq(fiddle, mel, 0, 0.35, 1.0)
    return tr.render(0.28)


def works():
    tr = Track(64, 90)
    for b in range(64):
        if b % 2 == 0:
            tr.add(b, thud(), 0.7)
        if b % 8 == 3 or b % 8 == 6:
            tr.add(b + 0.5, clank(380 + 40 * (b % 3)), 0.25)
    ost = [('E2', 1), ('E2', 0.5), ('F2', 0.5), ('E2', 1), ('G2', 0.5), ('F2', 0.5)] * 16
    tr.seq(bass, ost, 0, 0.45, 0.9)
    for b, c in ((0, 'E3+F3+B3'), (16, 'E3+G3+Bb3'), (32, 'D3+E3+F3+B3'), (48, 'E3+F3+B3')):
        for nmn in c.split('+'):
            tr.add(b, organ(midi(nm(nmn)), 14 * tr.spb), 0.22)
    return tr.render(0.25, 1.8)


def basin():
    tr = Track(48, 48)
    prog = ['C#3+G#3+E4', 'A2+E3+C#4', 'E3+B3+G#4', 'B2+F#3+D#4'] * 3
    for i, c in enumerate(prog):
        for nmn in c.split('+'):
            tr.add(i * 4, choir(midi(nm(nmn)), 5 * tr.spb, 3), 0.18)
    arp = ['C#5', 'G#4', 'E5', 'B4', 'A4', 'E5', 'C#5', 'G#5', 'F#4', 'B4', 'D#5', 'F#5']
    for k in range(24):
        tr.add(k * 2 + (0.5 if k % 3 == 1 else 0), bell(midi(nm(arp[k % len(arp)])), 4.0), 0.22)
    return tr.render(0.6, 4.5)


def cave():
    tr = Track(48, 40)
    for b, c in ((0, 'D2+A2'), (12, 'D2+Bb2'), (24, 'C2+G2'), (36, 'D2+A2')):
        for nmn in c.split('+'):
            tr.add(b, choir(midi(nm(nmn) + 12), 13 * tr.spb, 3), 0.25)
            tr.add(b, bass(midi(nm(nmn)), 12 * tr.spb), 0.2)
    for b in (6, 22, 39):
        tr.add(b, bell(midi(nm('A2')), 6.0), 0.12)
    return tr.render(0.55, 4.0)


def title():
    tr = Track(48, 52)
    prog = ['D3+A3+F#4+D5', 'G2+D3+B3+D5', 'D3+A3+F#4+A4', 'A2+E3+C#4+E4', 'B2+F#3+D4+F#4', 'G2+D3+B3+G4',
            'E3+B3+G4+E4', 'A2+E3+C#4+A4', 'D3+A3+F#4+F#4', 'B2+F#3+D4+B4', 'G2+D3+A3+E4', 'D3+A3+D4+D4']
    chords(tr, organ, prog, 4, 0.4)
    for i, c in enumerate(prog):
        tr.add(i * 4, choir(midi(nm(c.split('+')[-1]) - 12), 4.2 * tr.spb, 3), 0.18)
    tr.add(0, bell(midi(nm('D4')), 7.0), 0.25)
    return tr.render(0.45, 3.4)


def boss():
    """Driving and dissonant: a kick on every beat, a galloping bass, fiddle stabs, an organ that won't resolve."""
    tr = Track(64, 132)
    for b in range(64):
        tr.add(b, thud(0.4), 0.9)
        if b % 4 == 3:
            tr.add(b + 0.5, thud(0.3), 0.5)
        if b % 2 == 1:
            tr.add(b, clank(520 + 30 * (b % 5), 0.4), 0.18)
    gallop = [('E2', 0.5), ('E2', 0.25), ('E2', 0.25), ('G2', 0.5), ('F2', 0.5)] * 32
    tr.seq(bass, gallop, 0, 0.55, 0.9)
    stabs = [('E5+B5', 1), (None, 1), ('F5+C6', 0.5), (None, 1.5), ('E5+B5', 1), (None, 1), ('G5+D6', 0.5), ('F5+C6', 0.5), (None, 1)]
    b = 16.0
    while b < 64:
        b = tr.seq(fiddle, stabs, b, 0.32, 0.8)
    for b0, c in ((0, 'E3+F3+B3'), (16, 'E3+G3+Bb3'), (32, 'D3+E3+F3+B3'), (48, 'C3+E3+F3+B3')):
        for nmn in c.split('+'):
            tr.add(b0, organ(midi(nm(nmn)), 15 * tr.spb), 0.2)
    return tr.render(0.2, 1.6)


def memory():
    """A music box in a slow waltz, a little out of tune, as if wound long ago."""
    tr = Track(72, 66)
    def box(f, d):
        a = bell(f * 2, min(d, 2.5)) * 0.7
        p = pluck(f * 2, min(d, 1.5), 0.2) * 0.4
        a[:p.size] += p[:a.size]
        return a
    mel = [('A4', 1), ('C5', 1), ('E5', 1), ('D5', 2), ('C5', 1), ('B4', 2), ('G4', 1), ('A4', 3),
           ('E4', 1), ('A4', 1), ('C5', 1), ('B4', 2), ('A4', 1), ('G#4', 2), ('E4', 1), ('A4', 3),
           ('C5', 1), ('E5', 1), ('A5', 1), ('G5', 2), ('E5', 1), ('F5', 2), ('D5', 1), ('E5', 3),
           ('A4', 1), ('B4', 1), ('C5', 1), ('D5', 2), ('B4', 1), ('C5', 1), ('B4', 1), ('G#4', 1), ('A4', 6)]
    tr.seq(box, mel, 0, 0.5, 1.0)
    for i, c in enumerate(['A2', 'E2', 'A2', 'E2', 'A2', 'D2', 'E2', 'A2'] * 3):
        if i * 3 < 72:
            tr.add(i * 3, bass(midi(nm(c)), 3 * tr.spb), 0.25)
    return tr.render(0.5, 3.5)


def sting():
    tr = Track(8, 70)
    for nmn in ('D3', 'A3', 'D4', 'F#4', 'A4'):
        tr.add(0, organ(midi(nm(nmn)), 6 * tr.spb), 0.4)
        tr.add(0, choir(midi(nm(nmn)), 6 * tr.spb, 2), 0.12)
    tr.add(0, bell(midi(nm('D4')), 5.0), 0.35)
    tr.add(0, thud(0.6), 0.8)
    x = tr.render(0.4, 2.5)
    return x * np.minimum(1, np.linspace(6, 0, x.size))


# ---------------------------------------------------------------- ambient beds (30 s loops)
def loop_noise(d):
    return rng.uniform(-1, 1, int(SR * d))


def wrap(x, fade=1.0):
    """Crossfade the end into the start so a bed loops without a seam."""
    n = int(SR * fade)
    y = x[:-n].copy()
    y[:n] = y[:n] * np.linspace(0, 1, n) + x[-n:] * np.linspace(1, 0, n)
    return y


def amb_birds(density=0.6):
    d = 31.0
    t = np.arange(int(SR * d)) / SR
    x = lowpass(loop_noise(d), 120) * (0.4 + 0.3 * np.sin(2 * np.pi * t / 10.3))      # wind in leaves
    for _ in range(int(40 * density)):
        s = rng.uniform(0, d - 1.5)
        f0 = rng.uniform(2200, 4200)
        for k in range(rng.integers(2, 6)):
            nn = int(SR * rng.uniform(0.05, 0.12))
            tt = np.arange(nn) / SR
            sweep = f0 * (1 + rng.uniform(-0.3, 0.3) * tt / tt[-1])
            chirp = np.sin(2 * np.pi * np.cumsum(sweep) / SR) * np.sin(np.pi * tt / tt[-1]) ** 2
            i = int(SR * (s + k * rng.uniform(0.09, 0.16)))
            x[i:i + nn] += chirp * rng.uniform(0.15, 0.35)
    return wrap(x)


def amb_night():
    d = 31.0
    t = np.arange(int(SR * d)) / SR
    x = lowpass(loop_noise(d), 200) * 0.35
    for f, rate, ph in ((4400, 3.1, 0), (4700, 2.7, 1.3), (4100, 3.6, 2.1)):
        gate = (np.sin(2 * np.pi * rate * t + ph) > 0.6) * (np.sin(2 * np.pi * 40 * t) > 0)
        x += np.sin(2 * np.pi * f * t) * lowpass(gate.astype(float), 20) * 0.08
    return wrap(x)


def amb_machines():
    d = 31.0
    t = np.arange(int(SR * d)) / SR
    x = lowpass(loop_noise(d), 300) * 1.2 + np.sin(2 * np.pi * 48 * t) * 0.3 * (1 + 0.3 * np.sin(2 * np.pi * 0.5 * t))
    for s in np.arange(0.7, d - 1, 2.9):
        c = clank(rng.uniform(250, 600), 0.9) * 0.18
        i = int(SR * s)
        x[i:i + c.size] += c
    return wrap(x)


def amb_cave():
    d = 31.0
    x = lowpass(loop_noise(d), 400) * 0.8
    for _ in range(26):
        s = rng.uniform(0, d - 1)
        nn = int(SR * 0.6)
        tt = np.arange(nn) / SR
        f = rng.uniform(900, 1700)
        drip = np.sin(2 * np.pi * f * (1 + 0.6 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14)
        i = int(SR * s)
        x[i:i + nn] += drip * rng.uniform(0.1, 0.3)
    return wrap(x)


def amb_water():
    d = 31.0
    t = np.arange(int(SR * d)) / SR
    n = loop_noise(d)
    x = (lowpass(n, 8) - lowpass(n, 40)) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 3.1) ** 2) + lowpass(n, 200) * 0.6
    return wrap(x)


# ---------------------------------------------------------------- more effects
def scream(f0=420, d=0.9):
    t = np.arange(int(SR * d)) / SR
    f = f0 * (1 + 0.35 * np.exp(-t * 4)) * (1 + 0.02 * np.sin(2 * np.pi * 7 * t))
    ph = np.cumsum(f) / SR
    w = np.zeros(t.size)
    for h in range(1, 20):
        fh = f0 * h
        amp = sum(a * np.exp(-((fh - c) / bw) ** 2) for c, bw, a in ((800, 200, 1.0), (1250, 250, 0.6), (2800, 400, 0.3)))
        w += amp * np.sin(2 * np.pi * ph * h)
    w += lowpass(rng.uniform(-1, 1, t.size), 3) * 0.15
    return w * adsr(t.size, 0.02, 0.35)


def bleat(f0=480, d=0.6):
    t = np.arange(int(SR * d)) / SR
    am = 0.6 + 0.4 * np.sin(2 * np.pi * 18 * t)
    ph = np.cumsum(f0 * (1 - 0.15 * t)) / SR
    w = sum(np.sin(2 * np.pi * ph * h) / h for h in range(1, 8))
    return w * am * adsr(t.size, 0.03, 0.2)


def slither(d=2.0):
    n = loop_noise(d)
    t = np.arange(n.size) / SR
    x = (lowpass(n, 6) - lowpass(n, 30)) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 3.3 * t))) + lowpass(n, 60) * 0.5
    return wrap(x, 0.3)


def dig(d=2.0):
    x = np.zeros(int(SR * d))
    for s in np.arange(0.05, d - 0.2, 0.23):
        c = lowpass(rng.uniform(-1, 1, int(SR * 0.12)), 5) * np.exp(-np.arange(int(SR * 0.12)) / SR * 30)
        i = int(SR * s)
        x[i:i + c.size] += c
    return wrap(x + lowpass(rng.uniform(-1, 1, x.size), 80) * 0.3, 0.2)


def heartbeat():
    x = np.zeros(int(SR * 1.0))
    for s, v in ((0.0, 1.0), (0.22, 0.7)):
        tb = thud(0.35) * v
        i = int(SR * s)
        x[i:i + tb.size] += tb
    return x


def whisper(d=2.2):
    t = np.arange(int(SR * d)) / SR
    n = rng.uniform(-1, 1, t.size)
    band = lowpass(n, 3) - lowpass(n, 9)
    syll = np.clip(np.sin(2 * np.pi * 3.7 * t + 2 * np.sin(2 * np.pi * 0.9 * t)), 0, 1) ** 2
    return band * syll * adsr(t.size, 0.3, 0.6)


def splash_big():
    n = rng.uniform(-1, 1, int(SR * 1.0))
    t = np.arange(n.size) / SR
    return (lowpass(n, 4) * np.exp(-t * 4) + lowpass(n, 30) * np.exp(-t * 2) * 0.6) + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 10) * 0.5


def bark():
    x = np.zeros(int(SR * 0.5))
    for s0 in (0.0, 0.2):
        t = np.arange(int(SR * 0.16)) / SR
        f = 300 * (1 + 0.6 * np.exp(-t * 25))
        w = sum(np.sin(2 * np.pi * np.cumsum(f * h) / SR) / h for h in range(1, 9))
        w = w * np.exp(-t * 14) + lowpass(rng.uniform(-1, 1, t.size), 3) * np.exp(-t * 30) * 0.4
        i = int(SR * s0)
        x[i:i + t.size] += w
    return x


def flame():
    n = rng.uniform(-1, 1, int(SR * 0.9))
    t = np.arange(n.size) / SR
    return (lowpass(n, 3) - lowpass(n, 40)) * np.minimum(1, t / 0.05) * np.exp(-t * 2.5) + lowpass(n, 60) * np.exp(-t * 3)


def snap():
    t = np.arange(int(SR * 0.7)) / SR
    twang = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((180, 6), (412, 9), (931, 14)))
    crack = (rng.uniform(-1, 1, t.size) - lowpass(rng.uniform(-1, 1, t.size), 4)) * np.exp(-t * 40)
    return twang * 0.6 + crack


def roar():
    t = np.arange(int(SR * 1.4)) / SR
    f0 = 70 * (1 + 0.25 * np.sin(np.pi * t / 1.4)) * (1 + 0.05 * np.sin(2 * np.pi * 23 * t))
    ph = np.cumsum(f0) / SR
    w = sum(np.sin(2 * np.pi * ph * h) * (1.0 / h) * (1.6 if 5 < h < 12 else 1.0) for h in range(1, 30))
    w += lowpass(rng.uniform(-1, 1, t.size), 6) * 0.5
    return w * adsr(t.size, 0.15, 0.5)


def engine():
    d = 2.0
    t = np.arange(int(SR * d)) / SR
    chug = np.zeros(t.size)
    for s0 in np.arange(0, d, 0.25):
        i = int(SR * s0)
        n = int(SR * 0.18)
        chug[i:i + n] += lowpass(rng.uniform(-1, 1, n), 12) * np.exp(-np.arange(n) / SR * 18)
    return wrap(chug + np.sin(2 * np.pi * 42 * t) * 0.3 + lowpass(rng.uniform(-1, 1, t.size), 90) * 0.4, 0.2)


def crackle():
    d = 3.0
    x = lowpass(rng.uniform(-1, 1, int(SR * d)), 50) * 0.5
    for _ in range(90):
        i = rng.integers(0, x.size - 300)
        x[i:i + 200] += (rng.uniform(-1, 1, 200)) * np.exp(-np.arange(200) / 40) * rng.uniform(0.3, 1.0)
    return wrap(x, 0.2)


def howl():
    t = np.arange(int(SR * 1.8)) / SR
    f = 420 + 160 * np.sin(np.pi * np.minimum(1, t / 1.2)) - 120 * np.maximum(0, t - 1.2)
    ph = np.cumsum(f) / SR
    return sum(np.sin(2 * np.pi * ph * h) / h ** 1.5 for h in range(1, 6)) * adsr(t.size, 0.2, 0.5)


def gurgle():
    t = np.arange(int(SR * 0.8)) / SR
    x = np.zeros(t.size)
    for s0 in (0.0, 0.18, 0.31, 0.5):
        n = int(SR * 0.12)
        tt = np.arange(n) / SR
        b = np.sin(2 * np.pi * (180 + 300 * tt / 0.12 + rng.uniform(-40, 40)) * tt) * np.sin(np.pi * tt / 0.12)
        i = int(SR * s0)
        x[i:i + n] += b * rng.uniform(0.5, 1.0)
    return x + lowpass(rng.uniform(-1, 1, t.size), 20) * 0.2 * adsr(t.size, 0.05, 0.3)


def paper():
    n = rng.uniform(-1, 1, int(SR * 0.45))
    t = np.arange(n.size) / SR
    return (n - lowpass(n, 3)) * (0.3 + 0.7 * np.abs(np.sin(2 * np.pi * 7 * t))) * adsr(n.size, 0.02, 0.15)


def whistle():
    t = np.arange(int(SR * 1.6)) / SR
    chord = sum(np.sin(2 * np.pi * f * t + 2 * np.sin(2 * np.pi * 5 * t)) for f in (415, 523, 622))
    breath = (rng.uniform(-1, 1, t.size) - lowpass(rng.uniform(-1, 1, t.size), 3)) * 0.4
    return (chord * 0.5 + breath) * adsr(t.size, 0.08, 0.4)


def whip():
    n = rng.uniform(-1, 1, int(SR * 0.25))
    t = np.arange(n.size) / SR
    swish = (lowpass(n, 3) - lowpass(n, 18)) * np.sin(np.pi * np.minimum(1, t / 0.15)) ** 2 * (t < 0.15)
    crack = (n - lowpass(n, 2)) * np.exp(-np.maximum(0, t - 0.15) * 80) * (t >= 0.15)
    return swish * 0.5 + crack * 1.4


def harpoon():
    t = np.arange(int(SR * 0.5)) / SR
    thunk = np.sin(2 * np.pi * (180 - 120 * t) * t) * np.exp(-t * 18)
    return thunk + lowpass(rng.uniform(-1, 1, t.size), 6) * np.exp(-t * 10) * 0.6


def bubbles():
    x = np.zeros(int(SR * 1.2))
    for _ in range(26):
        n = int(SR * rng.uniform(0.03, 0.08))
        tt = np.arange(n) / SR
        f = rng.uniform(400, 1400)
        b = np.sin(2 * np.pi * f * (1 + 2.0 * tt / tt[-1]) * tt) * np.sin(np.pi * tt / tt[-1])
        i = rng.integers(0, x.size - n)
        x[i:i + n] += b * rng.uniform(0.3, 1.0)
    return x


def crash():
    n = rng.uniform(-1, 1, int(SR * 2.2))
    t = np.arange(n.size) / SR
    metal = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((143, 2.5), (271, 3), (433, 4), (781, 6))) * 0.4
    return lowpass(n, 40) * np.exp(-t * 1.6) + metal + (n - lowpass(n, 5)) * np.exp(-t * 8) * 0.5


def main():
    m = os.path.join(ROOT, 'assets', 'music')
    for name, fn in (('enfield', enfield), ('greenwich', greenwich), ('dana', dana), ('works', works),
                     ('basin', basin), ('cave', cave), ('title', title), ('boss', boss), ('memory', memory)):
        save(os.path.join(m, name + '.wav'), fn(), 0.8)
        print('music', name)
    a = os.path.join(ROOT, 'assets', 'ambient')
    save(os.path.join(a, 'birds.wav'), amb_birds(0.7), 0.6)
    save(os.path.join(a, 'birds_dusk.wav'), amb_birds(0.3), 0.6)
    save(os.path.join(a, 'night.wav'), amb_night(), 0.5)
    save(os.path.join(a, 'machines.wav'), amb_machines(), 0.6)
    save(os.path.join(a, 'cave.wav'), amb_cave(), 0.55)
    save(os.path.join(a, 'water.wav'), amb_water(), 0.55)
    s = os.path.join(ROOT, 'assets', 'sfx')
    save(os.path.join(s, 'scream.wav'), scream(), 0.6)
    save(os.path.join(s, 'scream2.wav'), scream(560, 0.7), 0.6)
    save(os.path.join(s, 'bleat.wav'), bleat(), 0.5)
    save(os.path.join(s, 'slither.wav'), slither(), 0.6)
    save(os.path.join(s, 'dig.wav'), dig(), 0.6)
    save(os.path.join(s, 'heartbeat.wav'), heartbeat(), 0.8)
    save(os.path.join(s, 'whisper.wav'), whisper(), 0.4)
    save(os.path.join(s, 'splash_big.wav'), splash_big(), 0.6)
    save(os.path.join(s, 'bark.wav'), bark(), 0.6)
    for name, fn, g in (('snap', snap, 0.7), ('roar', roar, 0.7), ('engine', engine, 0.6), ('crackle', crackle, 0.5),
                        ('howl', howl, 0.5), ('gurgle', gurgle, 0.5), ('paper', paper, 0.5), ('sting', sting, 0.8),
                        ('whistle', whistle, 0.6), ('whip', whip, 0.7), ('harpoon', harpoon, 0.6), ('bubbles', bubbles, 0.5),
                        ('crash', crash, 0.9)):
        save(os.path.join(s, name + '.wav'), fn(), g)
    save(os.path.join(s, 'flame.wav'), flame(), 0.6)
    print('ambient and effects done')


if __name__ == '__main__':
    main()
