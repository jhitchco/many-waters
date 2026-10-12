"""Synthesizes the game's sound effects into assets/sfx/*.wav (22.05 kHz, 16-bit mono)."""
import os, wave
import numpy as np

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'sfx')
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, attack=0.005, power=2.0):
    x = np.linspace(0, 1, n)
    e = (1 - x) ** power
    a = int(SR * attack)
    if a > 0:
        e[:a] *= np.linspace(0, 1, a)
    return e


def lowpass(x, k):
    k = max(1, int(k))
    return np.convolve(x, np.ones(k) / k, mode='same')


def noise(d):
    return rng.uniform(-1, 1, int(SR * d))


def save(name, x, gain=0.8):
    x = np.asarray(x, dtype=np.float64)
    peak = np.max(np.abs(x)) or 1.0
    x = np.clip(x / peak * gain, -1, 1)
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def main():
    os.makedirs(OUT, exist_ok=True)
    # 8-second seamless drone: every frequency completes whole cycles in 8 s
    tt = t(8.0)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.125 * tt)
    saw = lambda f: 2 * ((tt * f) % 1.0) - 1
    d = (saw(55.0) + saw(55.125) * 0.8 + saw(82.5) * 0.5) * lfo + np.sin(2 * np.pi * 110 * tt) * 0.3
    save('drone', lowpass(lowpass(d, 40), 40), 0.5)

    n = noise(0.45)
    save('squelch', lowpass(n, 18) * env(n.size, 0.01, 1.5) + np.sin(2 * np.pi * 70 * t(0.45) * (1 - t(0.45))) * env(n.size, 0.01, 3) * 0.8)
    n = noise(0.25)
    save('hurt', lowpass(n, 30) * env(n.size, 0.005, 2) + np.sin(2 * np.pi * 55 * t(0.25)) * env(n.size, 0.0, 2), 0.7)

    tb = t(3.2)
    bell = sum(a * np.sin(2 * np.pi * f * tb) * np.exp(-tb * dcy) for f, a, dcy in
               ((196.0, 1.0, 1.1), (293.7, 0.5, 1.4), (392.0, 0.35, 1.8), (527.0, 0.2, 2.5), (731.0, 0.12, 3.2)))
    bell[: int(SR * 0.004)] *= np.linspace(0, 1, int(SR * 0.004))
    save('bell', bell, 0.6)

    n = noise(0.18)
    save('crack', (n - lowpass(n, 6)) * env(n.size, 0.001, 3) + lowpass(n, 10) * env(n.size, 0.001, 5) * 0.6, 0.7)
    n = noise(0.9)
    tt = t(0.9)
    save('boom', lowpass(n, 60) * env(n.size, 0.003, 1.6) + np.sin(2 * np.pi * (60 - 30 * tt) * tt) * env(n.size, 0.0, 2), 0.9)
    n = noise(0.14)
    save('shot', (n - lowpass(n, 4)) * env(n.size, 0.0, 6) + lowpass(n, 20) * env(n.size, 0.0, 3) * 0.5, 0.7)
    n = noise(0.5)
    tt = t(0.5)
    save('splash', lowpass(n, 5) * env(n.size, 0.02, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt)), 0.5)
    tt = t(1.4)
    f = 880 * (1 - 0.25 * tt / 1.4)
    save('chime', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2) + 0.4 * np.sin(2 * np.pi * 1320 * tt) * np.exp(-tt * 3), 0.45)
    tt = t(0.06)
    save('tick', np.sign(np.sin(2 * np.pi * 880 * tt)) * env(tt.size, 0.0, 2), 0.35)
    n = noise(0.3)
    tt = t(0.3)
    g = lowpass(n, 3) - lowpass(n, 14)
    save('gasp', g * np.sin(np.pi * tt / 0.3) ** 2, 0.35)
    n = noise(0.22)
    save('swing', (lowpass(n, 4) - lowpass(n, 20)) * np.sin(np.pi * t(0.22) / 0.22) ** 3, 0.45)
    tt = t(4.0)
    save('flood', (np.sin(2 * np.pi * 49 * tt) + 0.5 * np.sin(2 * np.pi * 73.5 * tt)) * np.sin(np.pi * tt / 4.0) ** 2 + lowpass(noise(4.0), 80) * 0.6 * np.sin(np.pi * tt / 4.0), 0.8)
    tt = t(2.6)
    save('unlock', sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 1.2) for f in (220, 277.2, 330, 440)) * np.minimum(1, tt / 0.05), 0.5)


if __name__ == '__main__':
    main()
