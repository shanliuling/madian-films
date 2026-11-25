"""BGM 连续播放 + 少量音效（炮声、枪声、手榴弹、过河水声）。BGM 增益不变。"""
import sys, os; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..')); sys.path.insert(0, HERE)
import numpy as np
from scipy.signal import butter, lfilter
from mapwar import audio as A
import battles
BAR, B0 = 2.3424, 0.275; T = lambda n: B0 + n * BAR; T_END = T(42) + 0.6; SR = A.SR
r = np.random.default_rng(5)


def env(n, a, d): t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / d)


def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)


def blast(size=1.0):
    n = int(1.3 * SR); t = np.arange(n) / SR; f = 70 * (1 + 1.2 * np.exp(-t * 14)); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.3) + lp(r.normal(0, 1, n), 900) * env(n, 0.002, 0.22) * 1.6
    return (x * 0.5 * size).astype(np.float32)


def shot():
    n = int(0.22 * SR); x = lp(r.normal(0, 1, n), 3500) * env(n, 0.0008, 0.035) + np.sin(2 * np.pi * 160 * np.arange(n) / SR) * env(n, 0.001, 0.03) * 0.5
    return (x * 0.5).astype(np.float32)


def volley(dur, rate):
    n = int(dur * SR); out = np.zeros(n + int(0.3 * SR), np.float32)
    for k in range(int(dur * rate)):
        p = int(r.uniform(0, n)); s = shot() * r.uniform(0.35, 1.0); out[p:p + len(s)] += s
    return out


def water(dur):
    n = int(dur * SR); x = lp(r.normal(0, 1, n), 1400) - lp(r.normal(0, 1, n), 300); t = np.arange(n) / SR
    return (x * (0.6 + 0.4 * np.sin(t * 5.1) * np.sin(t * 1.7)) * np.minimum(1, t / 0.5) * np.minimum(1, (dur - t) / 0.7) * 0.22).astype(np.float32)


y = A.load(os.path.join(HERE, 'bgm.wav')); M = A.Mix(y, T_END)
battles.tucheng(0.0); battles.loushan(0.0)
M.add(volley(2 * BAR, 9), T(5), 0.30)
for (bt, bx, by, sz) in battles._T['bl']: M.add(blast(sz / 1.4), T(5) + bt / 0.8, 0.5, pan=float(np.clip(by / 14, -0.6, 0.6)))
M.add(volley(1.3, 10), T(10.5), 0.28)
for (gt, gy, gy2) in battles._L['gr']: M.add(blast(0.7), T(10.5) + (gt + 0.55) / 0.82, 0.42, pan=float(np.clip(gy2 / 12, -0.6, 0.6)))
for (bt, bx, by, sz) in battles._T['bl'][::2]: M.add(blast(sz / 1.6), T(15.5) + bt / 0.8, 0.38, pan=float(np.clip(by / 14, -0.6, 0.6)))
M.add(volley(1.5 * BAR, 8), T(15.5), 0.24)
for a, b, g in ((8, 9.5, 0.7), (21, 22, 0.7), (24, 25.5, 0.8), (26.5, 27.5, 0.7), (36, 38, 0.9)): M.add(water((b - a) * BAR), T(a), g)
n = len(M.y); f = np.ones(n, np.float32); k = int(1.6 * SR); f[-k:] = np.linspace(1, 0, k) ** 1.5; M.y *= f[:, None]
OFF = T(2) - 0.15; i0 = int(OFF * SR); M.y = M.y[i0:]; k = int(0.03 * SR); M.y[:k] *= np.linspace(0, 1, k)[:, None]
M.save(os.path.join(HERE, 'mix.wav')); print(len(M.y) / SR)
