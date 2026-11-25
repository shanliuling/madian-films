"""mapwar.audio — BGM 找拍、剪接，加少量程序合成音效。全部 numpy，读写靠 ffmpeg。

    y = load('bgm.mp3')                                  # float32 (n,2) @ 48k
    print(onsets(y)[:20]); print(loud_sections(y))       # 先看重拍和段落在哪，再定时间线
    bgm = splice(y, [(50.80, 55.35), (63.53, 92.76), (116.84, None)])     # 取几段，接缝交叉淡化
    mix = Mix(bgm, total); mix.add(boom(), 14.87); mix.add(hooves(1.5), 15.0, 0.5); mix.save('mix.wav')
习惯：没有配音时 BGM 音量全程不变（不做闪避）；有配音时用 voice.lay() 只在说话处压低；音效少而准，只给真正的重拍和有画面依据的声音（蹄声、箭、撞击）。
"""
import subprocess, math
import numpy as np

SR = 48000


def load(path, sr=SR):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(sr), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def save(path, y, sr=SR):
    y = np.clip(y, -1, 1).astype(np.float32)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ac', '2', '-ar', str(sr), '-i', '-', path], input=y.tobytes(), check=True)


def envelope(y, hop=512, sr=SR):
    m = np.abs(y).mean(1); n = len(m) // hop; return m[:n * hop].reshape(n, hop).mean(1), hop / sr


def onsets(y, k=40, sr=SR):
    """能量突增最强的 k 个时间点（秒）——候选重拍。别只信自动节拍检测，自己对着这些点量小节长度。"""
    e, dt = envelope(y, 512, sr); d = np.maximum(0, np.diff(np.log(e + 1e-5))); idx = []
    for i in np.argsort(-d):
        if all(abs(i - j) > 0.25 / dt for j in idx): idx.append(i)
        if len(idx) >= k: break
    return sorted(round((i + 1) * dt, 3) for i in idx)


def loud_sections(y, win=1.0, sr=SR):
    """每秒响度（相对值）——看哪里是铺垫、哪里是高潮、哪里有静默。"""
    e, dt = envelope(y, int(sr * win), sr); return [(round(i * win, 1), round(float(v / (e.max() + 1e-9)), 2)) for i, v in enumerate(e)]


def splice(y, segs, xf=0.08, fade_out=1.0, sr=SR):
    """按 [(开始秒, 结束秒|None), ...] 取段拼接，接缝做 xf 秒交叉淡化（切点尽量落在同相位的拍点上）。"""
    out = None; n = int(xf * sr)
    for a, b in segs:
        s = y[int(a * sr):(int(b * sr) if b else len(y))].copy()
        if out is None: out = s
        else:
            r = np.linspace(0, 1, n, dtype=np.float32)[:, None]; out[-n:] = out[-n:] * (1 - r) + s[:n] * r; out = np.concatenate([out, s[n:]])
    if fade_out: m = int(fade_out * sr); out[-m:] *= np.linspace(1, 0, m, dtype=np.float32)[:, None]
    return out


# ---- 合成音效（单声道 float32）
def _env(n, a=0.005, d=0.3, sr=SR): t = np.arange(n) / sr; return np.minimum(1, t / a) * np.exp(-t / d)


def boom(dur=1.4, f0=58, sr=SR):
    """低频重击：重拍、城破、大字砸下。"""
    n = int(dur * sr); t = np.arange(n) / sr; f = f0 * (1 + 1.6 * np.exp(-t * 18)); ph = 2 * np.pi * np.cumsum(f) / sr
    r = np.random.default_rng(1); return (np.sin(ph) * _env(n, 0.003, 0.33) + r.normal(0, 0.25, n) * _env(n, 0.001, 0.035)).astype(np.float32) * 0.9


def hit(dur=0.35, sr=SR):
    """短促撞击：兵器、盾。"""
    n = int(dur * sr); r = np.random.default_rng(2); x = r.normal(0, 1, n) * _env(n, 0.001, 0.05); x = np.convolve(x, np.ones(6) / 6, 'same'); return (x * 0.6).astype(np.float32)


def hooves(dur=2.0, rate=11.0, sr=SR, seed=3):
    """马蹄群：只有蹄声，没有马嘶。"""
    n = int(dur * sr); out = np.zeros(n, np.float32); r = np.random.default_rng(seed); k = int(0.06 * sr); t = np.arange(k) / sr
    for i in range(int(dur * rate * 4)):
        p = int(r.uniform(0, max(1, n - k))); f = r.uniform(70, 130); out[p:p + k] += (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.012) * r.uniform(0.2, 0.6)).astype(np.float32)
    e = np.minimum(1, np.arange(n) / (0.25 * sr)) * np.minimum(1, (n - np.arange(n)) / (0.4 * sr)); return out * e.astype(np.float32) * 0.5


def arrows(dur=0.9, sr=SR, seed=4):
    """箭雨：一片嘶嘶声。"""
    n = int(dur * sr); r = np.random.default_rng(seed); x = np.diff(r.normal(0, 1, n + 1)); t = np.arange(n) / sr
    return (x * np.sin(np.pi * t / dur) ** 2 * 0.12).astype(np.float32)


class Mix:
    def __init__(self, bgm, total=None, bgm_gain=1.0, sr=SR):
        n = int(total * sr) if total else len(bgm); self.y = np.zeros((n, 2), np.float32); m = min(n, len(bgm)); self.y[:m] = bgm[:m] * bgm_gain; self.sr = sr

    def add(self, x, t, gain=1.0, pan=0.0):
        p = int(t * self.sr)
        if p >= len(self.y) or p < 0: return
        x = x[:len(self.y) - p] * gain; self.y[p:p + len(x), 0] += x * (1 - max(0, pan)); self.y[p:p + len(x), 1] += x * (1 + min(0, pan))

    def save(self, path):
        pk = float(np.abs(self.y).max()); save(path, self.y * (0.97 / pk if pk > 0.97 else 1.0), self.sr)
