"""mixfilm — 萧炎（上）v2 的音轨 → out/mixfilm.wav
音乐：系列 BGM 按 MAP 在小节线上剪接（成片的拍 fb → BGM 的拍），大招命中前收一下。
音效：全部代码合成，沿用试片 mix.py 的那套（混响、左右声像）；三年之约开打那段直接用试片的音效。时间都写成片的拍号。"""
import _env, subprocess, numpy as np
from scipy import signal
from scipy.io import wavfile
SR = 44100; BEAT = 0.59413; NB = 228.5; DUR = 0.50 + NB * BEAT; n = int(DUR * SR); t = np.arange(n) / SR
def bt(b): return 0.50 + b * BEAT
_src = open('mix.py').read(); T = {'__name__': 'mixlib'}; exec(compile(_src[:_src.index('# 音乐')], 'mix.py', 'exec'), T)      # 试片的合成工具箱和它那段音效
verb, tt, S, whoosh, boom, crack, ping, clang, lp, hp, bp, r = (T[k] for k in ('verb', 'tt', 'S', 'whoosh', 'boom', 'crack', 'ping', 'clang', 'lp', 'hp', 'bp', 'r')); FT = T['F']
MAP = [(0, 32, 0), (32, 48, 64), (48, 64, 80), (64, 80, 112), (80, 120, 96), (120, 126, 160), (126, 136, 166), (136, 142, 187), (142, 211, 193), (211, NB, 262)]
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', _env.BGM, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
bgm = np.frombuffer(raw, np.float32).reshape(-1, 2); bgm = np.vstack([bgm, np.zeros((SR * 30, 2), np.float32)]); music = np.zeros((n + SR, 2), np.float32); XF = int(0.03 * SR)
for k, (f0, f1, m0) in enumerate(MAP):
    i0 = int(bt(f0) * SR) if k else 0; i1 = min(n, int(bt(f1) * SR)); j0 = int(bt(m0) * SR) if k else 0; a = XF if k else 0; seg = bgm[j0 - a:j0 + (i1 - i0) + XF].copy(); w = np.ones(len(seg), np.float32)
    if k: w[:XF] = np.sin(np.linspace(0, np.pi / 2, XF)) ** 2
    w[-XF:] = np.cos(np.linspace(0, np.pi / 2, XF)) ** 2; music[i0 - a:i0 - a + len(seg)] += seg * w[:, None]
    if k and MAP[k - 1][2] + (MAP[k - 1][1] - MAP[k - 1][0]) != m0:                       # 接点：上一段最后半秒拖一点余响盖住剪口
        p0 = int(bt(MAP[k - 1][2] + MAP[k - 1][1] - MAP[k - 1][0]) * SR); tail = bgm[p0 - int(0.45 * SR):p0] * (np.hanning(2 * int(0.45 * SR))[:int(0.45 * SR), None] ** 0.5); tv = verb(tail, 1.6, 0.22, 3 + k); e = min(len(music), i0 - int(0.45 * SR) + len(tv)); music[i0 - int(0.45 * SR):e] += tv[:e - (i0 - int(0.45 * SR))] * np.clip((np.arange(e - (i0 - int(0.45 * SR))) / SR - 0.40) / 0.08, 0, 1)[:, None]
music = music[:n]
sfx = np.zeros((n + SR * 6, 2), np.float32)
def add(sig, b, pan=0.0, gain=1.0, sec=None):
    """在第 b 拍放一个声音（sec 给了就按秒）。pan: -1 左 … 1 右。"""
    i = max(0, int((bt(b) if sec is None else sec) * SR)); s2 = np.stack([sig * (1 - max(0, pan)), sig * (1 + min(0, pan))], 1) if sig.ndim == 1 else sig; e = min(len(sfx), i + len(s2)); sfx[i:e] += s2[:e - i] * gain
def fire(sec, f=1100, k=1.0):
    q = tt(sec); u = q / sec; fl = 1 + 0.5 * lp(14, r.normal(0, 1, len(q))) * 6; return lp(f, r.normal(0, 1, len(q))) * np.clip(fl, 0.2, 2.2) * np.sin(np.pi * u ** k) ** 1.2 * 1.6
def riser(sec): q = tt(sec); u = q / sec; return bp(300, 9000, r.normal(0, 1, len(q))) * u ** 3 * (0.6 + 0.4 * np.sin(np.cumsum(2 * np.pi * (200 + 2400 * u ** 2) / SR)))
def thump(g=1.0): return S(boom(0.4, 130, 55, 11), crack(0.08, 1400) * 0.5) * g
def slamhit(big=1.0): return S(boom(1.8, 95, 30, 2.4) * big, crack(0.6, 650) * 0.7, verb(crack(0.3, 500), 1.6, 0.14, 4)[:, 0])
def chime(k, base=660): return S(ping(base * 2 ** (k * 4 / 12), 1.4, 3.2, ((1, 1.0), (2.0, 0.5), (3.01, 0.3), (4.2, 0.15))), whoosh(0.35, 1500, 7000, 1.0) * 0.5)
def flap(): return S(whoosh(0.5, 180, 1300, 1.3) * 1.2, lp(160, r.normal(0, 1, int(0.3 * SR))) * np.exp(-tt(0.3) * 14) * 2)
def wingopen(): return S(whoosh(0.7, 300, 5200, 0.7) * 1.3, boom(0.8, 110, 45, 5) * 0.8, crack(0.2, 2500) * 0.6, verb(ping(1976, 0.8, 5), 1.4, 0.2, 9)[:, 0])
def tick(): return S(ping(1900, 0.16, 28) * 0.7, crack(0.05, 3200) * 0.4)
def heart(g): return S(boom(0.32, 62, 44, 13), np.pad(boom(0.28, 56, 40, 15) * 0.7, (int(0.17 * SR), 0))) * g
def rumble(sec): q = tt(sec); return lp(110, r.normal(0, 1, len(q))) * np.clip(np.minimum(q / 0.3, (sec - q) / 0.8), 0, 1) * (1 + 0.3 * np.sin(q * 31)) * 7
def wind(sec): q = tt(sec); return bp(300, 1400, r.normal(0, 1, len(q))) * (0.6 + 0.4 * np.sin(q * 1.1) * np.sin(q * 0.37 + 1)) * np.clip(np.minimum(q / 1.0, (sec - q) / 1.0), 0, 1)
def burnfx(b, pan=0.0): add(S(whoosh(0.55, 500, 3400, 1.1), fire(0.8, 2400)), b - 0.05, pan, 0.6)
def lotusfx(b_w, layers, b_t, b_hit, hi=0):
    """展翼（b_w 为 None 就没有）→ 三层花瓣 → 出手 → 命中。"""
    if b_w is not None: add(wingopen(), b_w, 0.2, 0.9)
    add(fire((b_t - layers[0] + 1) * BEAT, 1500), layers[0] - 0.5, 0.1, 0.45)
    for k, b in enumerate(layers): add(chime(k + hi), b, 0.15, 0.34); add(verb(chime(k + hi), 1.6, 0.25, 20 + k), b, 0, 0.5); add(thump(0.6), b, 0.1, 0.5)
    add(S(whoosh(0.5, 300, 5000, 0.8) * 1.4, boom(0.7, 120, 50, 6)), b_t, 0, 0.9); add(riser((b_hit - b_t) * BEAT), b_t, 0, 0.5)
    add(slamhit(1.2), b_hit, 0, 1.0); add(boom(2.4, 60, 24, 1.6), b_hit, 0, 0.8); add(rumble(2.6), b_hit, 0, 0.5); add(verb(clang(300)[:int(0.5 * SR)], 2.4, 0.2, 31), b_hit, 0, 0.8); add(whoosh(1.2, 4000, 500, 0.6), b_hit + 0.15, 0, 0.5)
# ---- 钩子、石碑
lotusfx(0.0, (0.8, 1.6, 2.4), 3.15, 4.0); add(S(crack(0.5, 500), verb(boom(1.2, 70, 30, 3), 1.8, 0.3, 2)[:, 0]), 4, 0, 0.6)
add(thump(1.2), 14, 0, 0.8)
for k, b in enumerate((16, 18, 20, 22)): add(chime(k, 392), b, -0.2 + 0.1 * k, 0.16)
add(S(crack(0.5, 2600) * 1.4, whoosh(1.0, 3600, 250, 0.6), *[np.pad(ping(2600 - 300 * i, 0.5, 9), (int(0.09 * i * SR), 0)) * 0.5 for i in range(5)]), 24, 0, 0.55); add(verb(ping(1175, 1.4, 3), 1.8, 0.3, 5), 29.6, 0.4, 0.5)
# ---- 退婚（静）：心跳越来越重，莫欺少年穷
add(lp(160, r.normal(0, 1, int(16 * BEAT * SR))) * np.linspace(0.3, 1.2, int(16 * BEAT * SR)) * 3, 32, 0, 0.22); add(ping(1568, 0.9, 5), 34.6, 0.4, 0.14); add(whoosh(0.3, 800, 3000), 38.5, 0.1, 0.5)
for k, b in enumerate((40, 41, 42)): add(thump(1.0), b, -0.5 + 0.5 * k, 0.9); add(crack(0.12, 1800), b, -0.5 + 0.5 * k, 0.4)
for k, b in enumerate((44, 45, 46, 47, 47.5)): add(heart(0.5 + 0.18 * k), b, 0, 0.9)
add(riser(1.1 * BEAT), 46.9, 0, 0.55); add(slamhit(1.3), 48, 0, 1.0); add(verb(clang(240)[:int(0.6 * SR)], 2.2, 0.2, 6), 48, 0, 0.9); add(thump(), 50, 0, 0.6)
add(S(crack(0.16, 700) * 1.6, boom(0.6, 105, 45, 7), lp(900, r.normal(0, 1, int(0.2 * SR))) * np.exp(-tt(0.2) * 22) * 2), 52, 0, 0.5)
# ---- 戒指、药老、焚诀；苦修四格；吞火
burnfx(57); add(whoosh(0.5, 600, 2600), 57.3, 0.3, 0.5); add(verb(S(ping(440, 2.0, 2), ping(659, 2.0, 2.4) * 0.7), 2.2, 0.35, 7), 58.6, 0.3, 0.5); add(fire(3.2 * BEAT, 2600), 58.6, 0.3, 0.3); add(slamhit(0.9), 62, 0, 0.8)
burnfx(64); add(S(slamhit(1.2), clang(190) * 0.5), 64, -0.3, 0.75)
for k, b in enumerate((65, 66, 67)): add(thump(), b, (0.4, -0.4, 0.4)[k], 0.9); add(whoosh(0.34, 200, 1500, 2.0), b + 0.35, (0.4, -0.4, 0.4)[k], 0.7)
for b in (66, 67, 78): add(tick(), b, -0.8, 0.6)
burnfx(68); add(fire(11 * BEAT, 1400) * np.linspace(0.4, 1.3, int(11 * BEAT * SR)), 68, 0, 0.5); add(S(boom(1.4, 85, 32, 3), whoosh(0.9, 300, 4200, 0.8)), 70, 0, 0.9)
for b in (72, 74): add(heart(0.8), b, 0, 0.7)
add(S(ping(2093, 1.0, 4), boom(0.9, 90, 40, 5)), 76, 0, 0.5); add(slamhit(1.1), 78, 0, 0.9); add(whoosh(1.0, 400, 5000, 0.7), 78, 0, 0.7)
# ---- 三年之约：试片那段的音效原样搬来（试片 0 秒 = 成片第 80 拍前 LEAD 秒）
tr = T['sfx']; i = int((bt(80) - FT.LEAD) * SR); e = min(len(sfx), i + len(tr)); sfx[i:e] += tr[:e - i]
# ---- 八极崩
add(thump(1.2), 93.6, -0.3, 0.8); add(whoosh(0.5, 150, 1600, 1.6) * 1.3, 94.5, 0, 0.9); add(whoosh(0.3, 1200, 6000, 1.2), 95.3, 0.3, 0.6); add(riser(0.5 * BEAT), 95.5, 0, 0.5); add(slamhit(1.4), 96, 0.2, 0.8); add(crack(0.3, 1200) * 1.5, 96, 0.2, 0.35); add(boom(2.0, 65, 26, 2), 96, 0, 0.7)
add(S(boom(1.0, 90, 36, 4), crack(0.5, 500)), 97.5, -0.4, 0.8); add(lp(140, r.normal(0, 1, int(2 * BEAT * SR))) * 3, 98, 0, 0.2)
# ---- 陨杀 对 佛怒火莲
add(verb(chime(2, 880), 1.5, 0.3, 8), 100.6, -0.4, 0.5); add(whoosh(3.6 * BEAT, 700, 6500, 2.6), 100.4, -0.4, 0.45); add(S(slamhit(0.9), clang(900) * 0.5), 104, -0.3, 0.8)
lotusfx(106, (107, 108, 109), 109.45, 112, hi=1)
add(thump(), 113.6, -0.2, 0.5)
for k in range(5): add(hp(2500, r.normal(0, 1, int(0.12 * SR))) * np.hanning(int(0.12 * SR)), 114.2 + 0.4 * k, -0.2 + 0.1 * k, 0.12)
add(verb(ping(392, 2.4, 1.6), 2.4, 0.35, 12), 116.3, 0, 0.5); add(S(clang(760) * 0.9, ping(3100, 0.5, 8) * 0.4), 122, 0.2, 0.5); add(verb(clang(760)[:int(0.3 * SR)], 1.8, 0.2, 13), 122, 0, 0.9)
# ---- 萧家变故（夜）
burnfx(126); add(wind(16 * BEAT), 126, 0, 0.16)
for k in range(3): add(whoosh(0.5, 900, 250, 0.7), 129.2 + 0.3 * k, -0.5 + 0.5 * k, 0.5)
add(boom(1.0, 60, 30, 4), 130.4, 0, 0.5); add(whoosh(0.5, 300, 2400), 132.3, 0.4, 0.5); add(verb(ping(110, 2.6, 1.3), 2.4, 0.3, 14), 135, 0, 0.6); add(boom(1.4, 55, 28, 3), 139, 0, 0.7); add(riser(1.6 * BEAT), 140.4, 0, 0.5)
# ---- 再上云岚宗
burnfx(142)
for b in (142.5, 143.7, 144.9, 146.0): add(flap(), b, -0.4 + (b - 142.5) * 0.25, 0.6)
add(slamhit(1.4), 147, 0.1, 1.0); add(boom(2.0, 60, 26, 2), 147, 0, 0.7)
for b, p in ((149, -0.5), (151.6, 0.5)): add(thump(1.1), b, p, 0.9); add(crack(0.12, 1800), b, p, 0.4)
add(whoosh(0.4, 400, 2600), 155, -0.4, 0.5); lotusfx(None, (157, 158, 159), 159.5, 161, hi=2); add(wingopen(), 157, 0.2, 0.4)
add(S(boom(2.6, 50, 22, 1.4), verb(crack(0.4, 400), 2.2, 0.25, 15)[:, 0]), 163, -0.3, 1.0); add(rumble(14 * BEAT), 163, 0, 0.32)
for k, b in enumerate((165, 167, 169, 171, 173, 175)): add(S(boom(0.9, 70, 30, 5), crack(0.3, 600) * (0.6 + 0.1 * k)), b, 0.1, 0.5 + 0.06 * k)
add(riser(0.6 * BEAT), 176.4, 0, 0.5); add(S(ping(2637, 1.6, 3), ping(3520, 1.4, 4) * 0.5, boom(1.4, 80, 30, 3)), 177, 0, 0.6); add(verb(ping(2637, 0.6, 5), 2.4, 0.3, 16), 177, 0, 0.6); add(fire(3 * BEAT, 3000), 177, 0, 0.4)
add(S(whoosh(0.9, 300, 5000, 0.7), fire(1.2, 3200)), 180, 0, 0.8)
for b, p, g in ((181, 0.2, 0.9), (183, -0.2, 0.9), (185, 0.1, 1.0), (185.3, -0.1, 0.7)): add(whoosh(0.32, 200, 2600, 2.0), b - 0.55, p, 0.8); add(S(slamhit(1.0), clang(420 + 80 * p) * 0.35), b, p, g)
add(rumble(4 * BEAT), 189, 0, 0.6); add(riser(3.9 * BEAT), 189, 0, 0.6); add(fire(4 * BEAT, 3000), 189, 0, 0.5); add(slamhit(1.5), 193, 0, 1.0); add(boom(2.6, 55, 22, 1.5), 193, 0, 0.9); add(verb(clang(260)[:int(0.5 * SR)], 2.6, 0.22, 17), 193, 0, 0.9)
add(whoosh(0.7, 300, 4500, 0.8), 193.6, 0.2, 0.7)
for b in (194.4, 195.5, 196.5): add(flap(), b, 0.3, 0.5)
# ---- 逃、魂殿、片尾
burnfx(197); add(wind(8 * BEAT), 197, 0, 0.14); add(riser(1.0 * BEAT), 204, 0, 0.5); add(slamhit(1.4), 205, 0, 0.8); add(boom(3.0, 46, 22, 1.2), 205, 0, 0.9); add(lp(120, r.normal(0, 1, int(6 * BEAT * SR))) * 4 * np.linspace(1, 0.3, int(6 * BEAT * SR)), 205, 0, 0.3)
for k in range(9): add(S(ping(180 + 37 * (k % 4), 0.3, 12, ((1, 1.0), (2.9, 0.7), (5.1, 0.5))), crack(0.06, 2400) * 0.8), 205.3 + k * 0.45, -0.6 + 0.15 * k, 0.3)
add(S(slamhit(1.0), whoosh(1.0, 300, 4000, 0.7)), 211, 0, 0.8); add(fire(4.5 * BEAT, 1800), 211, 0, 0.3)
add(fire(11 * BEAT, 1500), 216, -0.3, 0.3)
for k in range(26): add(crack(0.04, 2000 + 1500 * r.random()), 216.3 + 11 * r.random(), -0.3, 0.10 + 0.12 * r.random())
add(verb(ping(784, 2.0, 2), 2.4, 0.35, 18), 216.8, 0.3, 0.4); add(verb(ping(1175, 2.0, 2.4), 2.4, 0.35, 19), 218.2, 0.3, 0.3)
# ---- 音乐在大招前收一下；试片那段照试片的压法
duck = np.ones(n, np.float32)
for b0, b1, d in ((47.4, 48, 0.25), (95.6, 96, 0.3), (111.2, 112, 0.2), (160.4, 161, 0.25), (176.4, 177, 0.25), (192.5, 193, 0.2), (204.5, 205, 0.3)):
    k = (t >= bt(b0) - 0.06) & (t < bt(b1)); duck[k] = np.minimum(duck[k], 1 - (1 - d) * np.clip((t[k] - (bt(b0) - 0.06)) / 0.06, 0, 1))
for b in (48, 86, 87, 90, 96, 112, 147, 161, 193, 205): k = (t >= bt(b)) & (t < bt(b) + 0.35); duck[k] = np.minimum(duck[k], 0.55 + 0.45 * (t[k] - bt(b)) / 0.35)
pkb = [(round(float(np.abs(sfx[int(bt(b) * SR):int(bt(b + 1) * SR)]).max()) * 0.32, 2), b) for b in range(0, 228)]; print('sfx 最响的拍', sorted(pkb, reverse=True)[:12])
out = music * duck[:, None] * 0.92 + sfx[:n] * 0.32; k = t > DUR - 2.4; out[k] *= np.clip((DUR - 0.1 - t[k]) / 2.3, 0, 1)[:, None]; pk = np.abs(out).max(); out = np.tanh(out * 1.15) * 0.97
print('rms music', round(float(np.sqrt((music ** 2).mean())), 3), 'sfx', round(float(np.sqrt((sfx[:n] ** 2).mean())) * 0.40, 3), 'peak', round(float(pk), 2)); wavfile.write('out/mixfilm.wav', SR, (out * 32767).astype(np.int16)); print('out/mixfilm.wav', round(DUR, 2))
