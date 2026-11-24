"""mix — 奈德片音轨：系列 BGM + 开场彩窗碎裂/倒带音效 + 结尾剑落处的合成音效（破风、闷响、玻璃碎裂），结尾音乐带余响停住，下一段渐入，片尾淡出 4 秒。 → out/mix.wav"""
import _env
import subprocess, numpy as np
from scipy import signal
from scipy.io import wavfile
SR = 44100; T0 = 0.50; BEAT = 0.59413; nt = lambda n: T0 + n * BEAT                       # 系列 BGM 的第 n 拍；下面的拍号和 film.py 的 RETIME 表对应
DUR = nt(206); A0 = nt(4); R0 = nt(5.5); R1 = nt(7); A = nt(166); BM = nt(170); B = 2 * BEAT; DUCK = 0.55   # A0 开场剑落，R0–R1 碎片倒飞，A 结尾剑落，BM 音乐回来（用 B 这么长渐入）
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', _env.BGM, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-t', f'{DUR:.3f}', '-'], capture_output=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy(); n = len(x); t = np.arange(n) / SR; r = np.random.default_rng(7)
def verb(sig, sec=2.2, wet=0.5, seed=1):
    rr = np.random.default_rng(seed); m = int(sec * SR); ir = rr.normal(0, 1, (m, 2)) * np.exp(-np.arange(m) / (sec * SR / 6.9))[:, None]; ir = signal.sosfilt(signal.butter(2, [200, 6000], 'bp', fs=SR, output='sos'), ir, axis=0); ir /= np.sqrt((ir ** 2).sum(0)).max()
    return np.stack([signal.fftconvolve(sig[:, c], ir[:, c])[:len(sig) + m] for c in range(2)], 1) * wet
# 音乐：A 前 0.1 秒开始变闷并滑落，余响拖 2 秒；BM 起两拍渐入；片尾 4 秒淡出
g = np.ones(n, np.float32); g[(t >= A - 0.02)] = 0; k = (t >= A - 0.10) & (t < A - 0.02); g[k] = 1 - (t[k] - (A - 0.10)) / 0.08; k = (t >= BM) & (t < BM + B); g[k] = ((t[k] - BM) / B) ** 1.5; g[t >= BM + B] = 1
i0 = int((A - 0.7) * SR); i1 = int(A * SR); seg = x[i0:i1] * np.hanning(2 * (i1 - i0))[:i1 - i0, None] ** 0.5; tail = verb(seg, 2.4, 0.42, 3); music = x * g[:, None]; e = min(n, i0 + len(tail)); music[i0:e] += tail[:e - i0] * np.clip((np.arange(e - i0) / SR - 0.55) / 0.15, 0, 1)[:, None]
k = t > DUR - 4.0; music[k] *= (np.clip((DUR - t[k]) / 4.0, 0, 1) ** 1.6)[:, None]
sfx = np.zeros((n + SR * 4, 2), np.float32)
def add(sig, at, pan=0.0, gain=1.0):
    i = int(at * SR); s2 = np.stack([sig * (1 - max(0, pan)), sig * (1 + min(0, pan))], 1) if sig.ndim == 1 else sig; sfx[i:i + len(s2)] += s2[:len(sfx) - i] * gain
# 破风：带通噪声，中心频率上扫，0.32 秒，落在 A
m = int(0.34 * SR); u = np.arange(m) / m; nz = r.normal(0, 1, m); f = 500 + 3800 * u ** 2; ph = np.cumsum(2 * np.pi * f / SR); wh = signal.sosfilt(signal.butter(2, [300, 7000], 'bp', fs=SR, output='sos'), nz) * (0.45 + 0.55 * np.sin(ph)) * np.sin(np.pi * u ** 1.6) ** 2
add(wh, A - 0.33, 0.0, 0.50)
# 闷响：55→32 Hz 正弦下滑 + 低通噪声的一击
m = int(1.8 * SR); tt = np.arange(m) / SR; f = 32 + 30 * np.exp(-tt * 7); boom = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-tt * 2.6) + 0.5 * signal.sosfilt(signal.butter(2, 180, 'lp', fs=SR, output='sos'), r.normal(0, 1, m)) * np.exp(-tt * 14)
add(np.tanh(boom * 1.6), A, 0.0, 0.62)
# 剑刃余音：几个高频泛音，慢衰减
ring = sum(np.sin(2 * np.pi * fq * tt[:int(1.4 * SR)] + i) * np.exp(-tt[:int(1.4 * SR)] * (3.0 + i)) * a for i, (fq, a) in enumerate(((2310, 1.0), (3470, 0.6), (5120, 0.35)))); add(ring, A, 0.0, 0.045)
# 玻璃碎裂：A+0.02 一声裂（高通噪声短脉冲），A+0.16 起碎片叮当（随机高频衰减正弦，密度逐渐变稀）
m = int(0.5 * SR); tt = np.arange(m) / SR; crack = signal.sosfilt(signal.butter(3, 2500, 'hp', fs=SR, output='sos'), r.normal(0, 1, m)) * (np.exp(-tt * 38) + 0.25 * np.exp(-tt * 7)); add(crack, A + 0.02, 0.0, 0.30); add(crack[::-1].copy() * 0.0 + crack, A + 0.16, 0.0, 0.34)
for i in range(190):
    dt = 0.16 + r.exponential(0.42); fq = r.uniform(2200, 9500); dur = r.uniform(0.05, 0.28); mm = int(dur * SR); q = np.arange(mm) / SR; tk = np.sin(2 * np.pi * fq * q) * np.exp(-q * r.uniform(18, 60)) + 0.4 * np.sin(2 * np.pi * fq * r.uniform(1.4, 2.3) * q) * np.exp(-q * 70)
    if dt < 2.4: add(tk, A + dt, r.uniform(-0.8, 0.8), 0.085 * np.exp(-dt * 0.9) * r.uniform(0.4, 1.0))
# ---- 开场：A0 彩窗炸碎（音乐不停，只压一下），R0–R1 碎片倒飞（碎裂声倒放 + 上扫噪声），R1 一记短促的合拢声
add(wh, A0 - 0.33, 0.0, 0.42); add(np.tanh(boom * 1.6)[:int(0.9 * SR)] * np.linspace(1, 0, int(0.9 * SR)), A0, 0.0, 0.50); add(crack, A0 + 0.01, 0.0, 0.34)
for i in range(120):
    dt = 0.05 + r.exponential(0.30); fq = r.uniform(2200, 9500); mm = int(r.uniform(0.05, 0.22) * SR); q = np.arange(mm) / SR; tk = np.sin(2 * np.pi * fq * q) * np.exp(-q * r.uniform(18, 60)) + 0.4 * np.sin(2 * np.pi * fq * r.uniform(1.4, 2.3) * q) * np.exp(-q * 70)
    if dt < 0.9: add(tk, A0 + dt, r.uniform(-0.8, 0.8), 0.10 * np.exp(-dt * 1.2) * r.uniform(0.4, 1.0))
m = int((R1 - R0) * SR); u = np.arange(m) / m; rv = np.zeros(m)
for i in range(150):
    at = r.uniform(0, 1) ** 0.6; fq = r.uniform(2000, 9000) * (0.7 + 0.6 * at); mm = int(r.uniform(0.04, 0.12) * SR); q = np.arange(mm) / SR; tk = (np.sin(2 * np.pi * fq * q) * np.exp(-q * r.uniform(25, 60)))[::-1]; i0 = int(at * (m - mm)); rv[i0:i0 + mm] += tk * (0.3 + 0.7 * at)
f = 400 + 5200 * u ** 2.2; sw = signal.sosfilt(signal.butter(2, [300, 9000], 'bp', fs=SR, output='sos'), r.normal(0, 1, m)) * (0.4 + 0.6 * np.sin(np.cumsum(2 * np.pi * f / SR))) * u ** 2.5
add(rv * u ** 1.2, R0, 0.0, 0.15); add(sw, R0, 0.0, 0.48); mm = int(0.25 * SR); q = np.arange(mm) / SR; add(np.sin(2 * np.pi * (70 + 60 * np.exp(-q * 30)) * q) * np.exp(-q * 16), R1, 0.0, 0.5); add(crack[:int(0.12 * SR)] * np.linspace(1, 0, int(0.12 * SR)), R1, 0.0, 0.2)
k = (t >= A0 - 0.03) & (t < R1 + 0.05); music[k] *= (DUCK + (1 - DUCK) * np.clip(np.abs(t[k] - (A0 + R1) / 2) / ((R1 - A0) / 2 + 0.04), 0, 1) ** 6)[:, None]     # 开场音效期间音乐压到 45%
sfx[:] += verb(sfx, 1.8, 0.22, 5)[:len(sfx)]; out = music + sfx[:n] * 0.62; pk = np.abs(out).max(); ab = np.abs(out); out = np.where(ab > 0.8, np.sign(out) * (0.8 + 0.17 * np.tanh((ab - 0.8) / 0.17)), out)
wavfile.write('out/mix.wav', SR, (out * 32767).astype(np.int16)); print('peak', pk, 'A', A, 'BM', BM, 'dur', n / SR)
seg = out[int((A - 0.5) * SR):int((A + 3.2) * SR)]; print('rms 0.1s:', ' '.join(f'{20 * np.log10(np.sqrt((seg[i:i + 4410] ** 2).mean()) + 1e-6):.0f}' for i in range(0, len(seg) - 4410, 4410)))

seg = out[int((A0 - 0.5) * SR):int((R1 + 0.6) * SR)]; print('open rms 0.1s:', ' '.join(f'{20 * np.log10(np.sqrt((seg[i:i + 4410] ** 2).mean()) + 1e-6):.0f}' for i in range(0, len(seg) - 4410, 4410)))
print('bgm first 4 bars rms per half bar:', ' '.join(f'{20 * np.log10(np.sqrt((x[int((T0 + i * B / 2) * SR):int((T0 + (i + 1) * B / 2) * SR)] ** 2).mean()) + 1e-6):.0f}' for i in range(8)))
