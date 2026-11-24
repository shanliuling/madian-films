"""mixfilm — 萧炎（上）的音轨：系列 BGM 从头放到尾 + 合成音效（按拍子摆）。→ out/mixfilm.wav"""
import _env, subprocess, numpy as np, wave
SR = 44100; BEAT = 0.59413; DUR = 175.4; rng = np.random.default_rng(7)
def bt(b): return 0.50 + b * BEAT
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', _env.BGM, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
mus = np.frombuffer(raw, np.float32).reshape(-1, 2); n = int(DUR * SR); mus = np.vstack([mus, np.zeros((max(0, n - len(mus)), 2), np.float32)])[:n]; sfx = np.zeros(n, np.float32)
def lp(x, k):
    y = np.cumsum(x); y[k:] = y[k:] - y[:-k]; return y / k
def boom(d=0.7): t = np.arange(int(d * SR)) / SR; f = 34 + 70 * np.exp(-t * 9); return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) + lp(rng.standard_normal(len(t)), 60) * np.exp(-t * 9) * 2.0).astype(np.float32)
def whoosh(d=0.4): t = np.arange(int(d * SR)) / SR; return (lp(rng.standard_normal(len(t)), 14) * np.sin(np.pi * t / d) ** 2 * 2.2).astype(np.float32)
def clang(d=0.5): t = np.arange(int(d * SR)) / SR; return (sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (9 + i * 3)) for i, f in enumerate((1210, 1873, 2637, 3411, 4520))) * 0.3 + rng.standard_normal(len(t)) * np.exp(-t * 90) * 0.6).astype(np.float32)
def ping(d=0.2): t = np.arange(int(d * SR)) / SR; return (sum(np.sin(2 * np.pi * f * t) for f in (2900, 4300)) * np.exp(-t * 28) * 0.3).astype(np.float32)
def rumble(d): t = np.arange(int(d * SR)) / SR; return (lp(rng.standard_normal(len(t)), 90) * np.clip(np.minimum(t / 0.4, (d - t) / 0.6), 0, 1) * (0.8 + 0.2 * np.sin(t * 23)) * 5).astype(np.float32)
def put(b, x, g):
    i = int(bt(b) * SR); x = x[:max(0, n - i)]
    if i < n: sfx[i:i + len(x)] += x * g
for b, g in ((3, 0.8), (4, 1.0), (24, 0.7), (48, 1.0), (56, 0.9), (70, 0.4), (80, 1.0), (85, 0.5), (87, 0.5), (92, 1.0), (98, 1.0), (112, 0.8), (126, 0.8), (128, 1.0), (129.6, 0.6), (132, 1.0), (133.5, 0.9), (136.6, 0.5), (145, 0.7), (148, 1.0), (149.6, 0.5), (174, 0.8), (190.1, 0.6), (198, 1.0), (212, 1.0), (214, 0.6),
             (216, 0.45), (218, 0.45), (220, 0.45), (222, 0.45), (224, 0.45), (228, 0.9), (232, 0.9), (234, 0.9), (236, 1.0), (240, 0.9), (244, 1.0), (282, 0.9), (288, 0.7)): put(b, boom(), g)
for b, g in ((122, 1.0), (131, 0.9), (160, 1.0), (84, 0.3)): put(b, clang(), g)
for b in (120, 120.14, 120.28, 124, 124.5, 125, 125.5, 126): put(b, ping(), 0.5)
for b in (2.6, 38.5, 65, 84, 86, 91.7, 118, 130.6, 131.1, 145.2, 147, 193.5, 196, 211, 231.7, 233.5, 235.5, 244.6): put(b - 0.2, whoosh(), 0.7)
for b, d, g in ((98, 14, 0.35), (138, 7, 0.3), (240, 4, 0.6), (216, 10, 0.3), (212, 2, 0.5)): put(b, rumble(d * BEAT), g)
out = mus * 0.9 + (sfx * 0.36)[:, None]; t = np.arange(n) / SR; out = np.tanh(out * 1.05) * np.clip((DUR - t) / 1.5, 0, 1)[:, None]
w = wave.open('out/mixfilm.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close(); print('out/mixfilm.wav')
