"""mix — 试片音轨：系列 BGM 从第 96 拍截一段 + 代码合成的打斗音效（拖尺、叮当、尺剑相撞、风爆、残影、踏地、最后一击）。 → out/mix.wav
音乐在最后一击（108 拍）带余响停住，109 拍字卡只留一声鼓。"""
import _env, subprocess, numpy as np
from scipy import signal
from scipy.io import wavfile
import fight as F
SR = 44100; DUR = F.DUR; START = 0.50 + F.B0 * F.BEAT - F.LEAD; n = int(DUR * SR); t = np.arange(n) / SR; r = np.random.default_rng(5)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{START:.4f}', '-i', _env.BGM, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-t', f'{DUR:.3f}', '-'], capture_output=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy(); x = np.vstack([x, np.zeros((max(0, n - len(x)), 2), np.float32)])[:n]
bp = lambda lo, hi, s, o=2: signal.sosfilt(signal.butter(o, [lo, hi], 'bp', fs=SR, output='sos'), s); lp = lambda f, s, o=2: signal.sosfilt(signal.butter(o, f, 'lp', fs=SR, output='sos'), s); hp = lambda f, s, o=2: signal.sosfilt(signal.butter(o, f, 'hp', fs=SR, output='sos'), s)
def verb(sig, sec=1.8, wet=0.4, seed=1):
    rr = np.random.default_rng(seed); m = int(sec * SR); ir = rr.normal(0, 1, (m, 2)) * np.exp(-np.arange(m) / (sec * SR / 6.9))[:, None]; ir = signal.sosfilt(signal.butter(2, [200, 6000], 'bp', fs=SR, output='sos'), ir, axis=0); ir /= np.sqrt((ir ** 2).sum(0)).max()
    s2 = sig if sig.ndim == 2 else np.stack([sig, sig], 1); return np.stack([signal.fftconvolve(s2[:, c], ir[:, c])[:len(s2) + m] for c in range(2)], 1) * wet
sfx = np.zeros((n + SR * 4, 2), np.float32)
def add(sig, at, pan=0.0, gain=1.0):
    i = max(0, int(at * SR)); s2 = np.stack([sig * (1 - max(0, pan)), sig * (1 + min(0, pan))], 1) if sig.ndim == 1 else sig; e = min(len(sfx), i + len(s2)); sfx[i:e] += s2[:e - i] * gain
def tt(sec): return np.arange(int(sec * SR)) / SR
def S(*a):
    m = max(len(q) for q in a); return sum(np.pad(q, (0, m - len(q))) for q in a)
def whoosh(sec, f0, f1, shape=1.6):
    q = tt(sec); u = q / sec; f = f0 + (f1 - f0) * u ** 2; return bp(250, 8000, r.normal(0, 1, len(q))) * (0.4 + 0.6 * np.sin(np.cumsum(2 * np.pi * f / SR))) * np.sin(np.pi * u ** shape) ** 2
def boom(sec=1.4, f0=70, f1=30, k=3.0):
    q = tt(sec); f = f1 + (f0 - f1) * np.exp(-q * 8); return np.tanh((np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-q * k) + 0.6 * lp(220, r.normal(0, 1, len(q))) * np.exp(-q * 12)) * 1.8)
def crack(sec=0.5, f=1800): q = tt(sec); return hp(f, r.normal(0, 1, len(q)), 3) * (np.exp(-q * 40) + 0.2 * np.exp(-q * 8))
def ping(fq, sec=0.7, dec=6, parts=((1, 1.0), (2.76, 0.5), (5.4, 0.25))): q = tt(sec); return sum(np.sin(2 * np.pi * fq * m * q + i) * np.exp(-q * dec * (1 + 0.6 * i)) * a for i, (m, a) in enumerate(parts))
def clang(fq=520):
    q = tt(1.6); v = sum(np.sin(2 * np.pi * fq * m * q + i * 1.3) * np.exp(-q * (2.4 + 1.1 * i)) * a for i, (m, a) in enumerate(((1, 1.0), (1.47, 0.8), (2.09, 0.7), (2.56, 0.6), (3.9, 0.45), (5.3, 0.3), (7.1, 0.2)))); return S(v, crack(0.3, 2500) * 1.5)
# 开场：睁眼时火「呼」地起来；斗气的低鸣
q = tt(0.9); u = q / 0.9; add(lp(900, r.normal(0, 1, len(q))) * np.exp(-q * 4) * np.minimum(1, q * 30), 0.36, -0.3, 0.55); add(whoosh(0.45, 400, 2400), 0.30, -0.3, 0.5)
q = tt(1.0); add(lp(300, r.normal(0, 1, len(q))) * np.minimum(1, q * 3) * np.minimum(1, (1.0 - q) * 12) * (1 + 0.4 * np.sin(q * 60)), 0.35, -0.2, 0.5)
# 冲锋：蹬地 + 破风；重尺擦着青石一路过去（发闷的沙沙声 + 金属的尖声），镜头里从左到右
add(boom(0.9, 90, 40, 5), F.T_GO, -0.4, 0.8); add(crack(0.25, 900), F.T_GO, -0.4, 0.35); add(whoosh(0.9, 500, 3200, 1.0), F.T_GO, 0.0, 0.6)
q = tt(2.24 - F.T_GO); u = q / q[-1]; sc = (bp(1800, 7500, r.normal(0, 1, len(q))) * 0.6 + bp(300, 900, r.normal(0, 1, len(q))) * 1.4) * (0.6 + 0.4 * np.sign(np.sin(q * 300))) * np.minimum(1, q * 20) * np.minimum(1, (q[-1] - q) * 14) + 0.25 * np.sin(2 * np.pi * 3100 * q + 3 * np.sin(q * 70)) * np.minimum(1, (q[-1] - q) * 14)
add(np.stack([sc * (1 - u * 0.7), sc * (0.3 + u * 0.7)], 1), F.T_GO + 0.04, 0, 0.30); add(whoosh(0.3, 2500, 600), 2.20, 0.2, 0.4)
# 她脚尖一点飘起来；三道风刃叮叮叮打在尺上
add(whoosh(0.6, 900, 5000, 1.2), 2.24, 0.4, 0.4)
for i, (ta, tb, sv) in enumerate(F.BLADES): add(whoosh(0.1, 4000, 7000), ta, 0.3, 0.3); add(S(ping(2300 + 420 * i, 0.5, 9), crack(0.1, 4000) * 0.6), tb, 0.15, 0.22)
add(whoosh(0.7, 700, 3500, 1.3), 2.45, -0.1, 0.3)
# 转身抡尺：很沉的破风；尺砸在剑尖上
add(whoosh(0.34, 180, 1500, 2.2), F.T_HIT - 0.33, 0.1, 0.9); add(whoosh(0.2, 3000, 8000, 2.0), F.T_HIT - 0.2, -0.3, 0.3)
add(clang(540), F.T_HIT, 0.0, 0.30); add(boom(1.2, 80, 34, 4), F.T_HIT, 0.0, 0.85); add(verb(clang(540)[:int(0.3 * SR)], 1.6, 0.12, 2), F.T_HIT, 0, 1.0)
q = tt(F.T_POP - F.T_HIT); u = q / q[-1]; f = 900 + 1500 * u ** 2; add((np.sin(np.cumsum(2 * np.pi * f / SR)) * 0.5 + np.sin(np.cumsum(2 * np.pi * f * 1.51 / SR)) * 0.3) * u ** 1.5 * (0.7 + 0.3 * np.sin(q * 180)) + bp(2000, 9000, r.normal(0, 1, len(q))) * 0.25 * u, F.T_HIT, 0.0, 0.16)   # 剑被压弯：越绷越尖
# 青芒暴涨，把尺弹开
add(whoosh(0.8, 1500, 300, 0.5), F.T_POP, 0.0, 0.9); add(boom(1.0, 100, 40, 5), F.T_POP, 0.0, 0.7); add(ping(1250, 1.2, 3), F.T_POP, -0.2, 0.2); add(whoosh(0.5, 800, 300), F.T_POP + 0.1, 0.4, 0.3)
# 五道残影：一声比一声高
for i, tp in enumerate(F.T_PH): add(S(ping(1320 * 2 ** (i * 2 / 12), 1.0, 4.5, ((1, 1.0), (2.0, 0.4), (3.01, 0.25))), whoosh(0.12, 3000, 9000) * 0.5), tp, -0.35, 0.16); add(verb(ping(1320 * 2 ** (i * 2 / 12), 0.3, 8), 1.2, 0.05, 10 + i), tp, 0, 1.0)
# 蓄势：火越烧越响；踏地炸开
q = tt(F.T_STOMP - 5.15); u = q / q[-1]; add((lp(700, r.normal(0, 1, len(q))) * (1 + 0.5 * np.sin(q * 45)) + 0.5 * bp(900, 3000, r.normal(0, 1, len(q))) + 0.6 * np.sin(np.cumsum(2 * np.pi * (60 + 90 * u ** 2) / SR))) * u ** 1.6, 5.15, 0.35, 0.55)
add(boom(1.8, 110, 30, 2.6), F.T_STOMP, 0.3, 1.0); add(crack(0.7, 700), F.T_STOMP, 0.3, 0.6); add(whoosh(1.0, 400, 2600, 0.8), F.T_STOMP, 0.0, 0.7); add(verb(crack(0.3, 500), 1.5, 0.12, 4), F.T_STOMP, 0, 1.0)
for i in range(40): dt = 0.25 + r.exponential(0.3); add(bp(600, 3000, r.normal(0, 1, int(0.05 * SR))) * np.exp(-tt(0.05) * 60), F.T_STOMP + dt, r.uniform(-0.3, 0.8), 0.12 * np.exp(-dt))      # 碎石落地
# 「风灵分形剑」：剑鸣 + 五剑破空
add(ping(1760, 1.0, 4, ((1, 1.0), (1.5, 0.5), (2.02, 0.4))), F.T_NAME - 0.04, -0.4, 0.2); add(whoosh(F.T_END - F.T_NAME, 2500, 500, 0.9), F.T_NAME, -0.2, 0.75); add(boom(0.6, 60, 40, 6), F.T_NAME, 0, 0.5)
add(whoosh(0.3, 200, 1800, 2.2), F.T_END - 0.29, 0.2, 1.0)
# 最后一击：闷响 + 金铁 + 一片白噪的光，拖长余响
q = tt(1.6); blast = np.tanh((lp(2500, r.normal(0, 1, len(q))) * np.exp(-q * 3.5) + hp(3000, r.normal(0, 1, len(q))) * np.exp(-q * 9) * 0.6) * 1.5); add(boom(2.4, 120, 28, 1.8), F.T_END, 0, 1.0); add(blast, F.T_END, 0, 0.55); add(clang(410), F.T_END, 0, 0.22); add(verb(blast[:int(0.6 * SR)], 2.6, 0.10, 6), F.T_END, 0, 1.0)
add(boom(1.6, 75, 36, 2.4), F.T_CARD, 0, 0.9); add(ping(196, 1.6, 2.2, ((1, 1.0), (2, 0.5), (3, 0.3))), F.T_CARD, 0, 0.12)
# 音乐：最后一击前 0.08 秒开始收，余响拖过去；开头 0.05 秒渐入
g = np.ones(n, np.float32); k = t < 0.05; g[k] = t[k] / 0.05; k = t >= F.T_END - 0.08; g[k] = np.clip(1 - (t[k] - (F.T_END - 0.08)) / 0.08, 0, 1); music = x * g[:, None] * 0.95
i0 = int((F.T_END - 0.6) * SR); i1 = int(F.T_END * SR); seg = x[i0:i1] * np.hanning(2 * (i1 - i0))[:i1 - i0, None] ** 0.5; tail = verb(seg, 2.2, 0.30, 3); e = min(n, i0 + len(tail)); music[i0:e] += tail[:e - i0] * np.clip((np.arange(e - i0) / SR - 0.5) / 0.1, 0, 1)[:, None]
duck = np.ones(n, np.float32)
for t0 in (F.T_HIT, F.T_POP, F.T_STOMP): k = (t >= t0) & (t < t0 + 0.35); duck[k] = np.minimum(duck[k], 0.55 + 0.45 * (t[k] - t0) / 0.35)
out = music * duck[:, None] + sfx[:n] * 0.42; print('rms music', float(np.sqrt((music ** 2).mean())), 'sfx', float(np.sqrt((sfx[:n] ** 2).mean())) * 0.55); k = t > DUR - 0.6; out[k] *= np.clip((DUR - t[k]) / 0.6, 0, 1)[:, None]; pk = np.abs(out).max(); out = np.tanh(out * (1.25 / max(pk, 1e-6)) * 1.0) / np.tanh(1.25) * 0.97
wavfile.write('out/mix.wav', SR, (out * 32767).astype(np.int16)); print('out/mix.wav', round(DUR, 2), 'peak', round(float(pk), 2))
