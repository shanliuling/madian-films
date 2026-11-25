"""双 BGM 衔接小样：bgm1「不小心惹了上帝」→ bgm2。只做音频。"""
import numpy as np, soundfile as sf, subprocess
from scipy.signal import butter, sosfiltfilt, fftconvolve

SR = 44100
b1, _ = sf.read('b1_16.wav')                       # bgm1 前 16s，立体声
voc, _ = sf.read('sep/htdemucs/b1_16/vocals.wav')  # bgm1 人声干声
b2, _ = sf.read('b2_full.wav')

S = lambda t: int(round(t * SR))
T_VOC_END = 3.045      # 「帝」唱完（人声 2.82–3.03，伴奏此处留白）
T_HIT = 3.065          # bgm1 自己的重拍落点 → 用 bgm2 顶替
DROP2 = 29.995         # bgm2 高能段起点
G1, G2 = 10 ** (1.5 / 20), 10 ** (-2.0 / 20)       # 响度靠拢：bgm1 +1.5dB，bgm2 -2dB
TAIL = 12.5            # 接入后保留多少秒 bgm2


def fade(x, n_in=0, n_out=0):
    x = x.copy()
    if n_in: x[:n_in] *= np.linspace(0, 1, n_in)[:, None] ** 2
    if n_out: x[-n_out:] *= np.linspace(1, 0, n_out)[:, None] ** 2
    return x


def put(buf, x, t, g=1.0):
    i = S(t); n = min(len(x), len(buf) - i)
    if n > 0: buf[i:i + n] += x[:n] * g


def head(t_end=T_VOC_END):
    return fade(b1[:S(t_end)], n_out=S(0.012)) * G1


def body(t_from, dur=TAIL):
    return fade(b2[S(t_from):S(t_from + dur)], n_in=S(0.002), n_out=S(1.2)) * G2


def reverb(x, secs=1.6, decay=3.2, seed=7):
    rng = np.random.default_rng(seed); n = S(secs)
    ir = rng.standard_normal((n, 2)) * np.exp(-decay * np.arange(n) / SR * 3)[:, None]
    ir = sosfiltfilt(butter(2, [300, 7000], 'bp', fs=SR, output='sos'), ir, axis=0)
    out = np.stack([fftconvolve(x[:, c], ir[:, c]) for c in range(2)], 1)
    return out / (np.abs(out).max() + 1e-9)


def di_tail(buf, g=0.26, secs=0.75):
    """「帝」的混响尾音，避免人声像被剪断。"""
    di = fade(voc[S(2.80):S(3.05)], n_in=S(0.01), n_out=S(0.03))
    put(buf, fade(reverb(di)[:S(secs)], n_out=S(0.45)), 2.86, g)


def finish(buf, name):
    buf = np.tanh(buf * 1.05) / 1.05                # 软限幅
    buf *= 0.89 / np.abs(buf).max()
    sf.write(name + '.wav', buf, SR)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', name + '.wav', '-b:a', '320k', name + '.mp3'], check=True)
    print(name, '%.2fs' % (len(buf) / SR))


def variant_a():
    """A 卡点直切：「帝」唱完，bgm2 的 drop 顶替 bgm1 原本的重拍。"""
    buf = np.zeros((S(T_HIT + TAIL), 2))
    put(buf, head(), 0); di_tail(buf); put(buf, body(DROP2), T_HIT)
    finish(buf, 'A_卡点直切')


def variant_b(gap=0.60):
    """B 回声悬停：「帝」拖出回声和混响悬空一拍，再炸 drop。"""
    t_drop = T_HIT + gap
    buf = np.zeros((S(t_drop + TAIL), 2))
    put(buf, head(), 0)
    di = voc[S(2.80):S(3.05)]; di = fade(di, n_in=S(0.01), n_out=S(0.03))
    for k, g in enumerate([0.62, 0.40, 0.25], 1):   # 三次回声，间隔 0.2s
        put(buf, di, 2.80 + 0.20 * k, g * G1)
    rv = reverb(di)[:S(gap + 0.30)]
    put(buf, fade(rv, n_out=S(0.10)), 2.86, 0.42)
    hit = b2[S(DROP2):S(DROP2 + 0.50)]              # drop 第一下倒放成吸入音
    sw = fade(reverb(hit, 1.0, 4.0)[:S(0.50)][::-1], n_in=S(0.42), n_out=S(0.01))
    put(buf, sw, t_drop - 0.50, 0.30)
    cut = S(t_drop) - S(0.02); buf[cut:S(t_drop)] *= np.linspace(1, 0, S(t_drop) - cut)[:, None]
    put(buf, body(DROP2), t_drop)
    finish(buf, 'B_回声悬停')


def variant_c(gap=0.60):
    """C 自带铺垫：歌词底下垫 bgm2 自己的上升音效，「帝」唱完留白半秒，drop。"""
    t_drop = T_HIT + gap
    buf = np.zeros((S(t_drop + TAIL), 2))
    put(buf, head(), 0); di_tail(buf, 0.36, 0.80)
    off = DROP2 - t_drop                             # bgm2 时间 = 成片时间 + off
    r = b2[S(off + 0.55):S(DROP2)]                  # bgm2 上升段（末尾 0.5s 本身是静音）
    r = sosfiltfilt(butter(4, 1800, 'hp', fs=SR, output='sos'), r, axis=0)   # 只留高频气流，避开调性打架
    r *= np.linspace(0.15, 1.0, len(r))[:, None]
    put(buf, r, 0.55, 0.55 * G2)
    put(buf, body(DROP2), t_drop)
    finish(buf, 'C_自带铺垫')


def variant_d(gap=0.60):
    """D 从头进：「帝」唱完留白，接 bgm2 开头的管弦铺底，慢热史诗感。"""
    t_in = T_HIT + gap
    buf = np.zeros((S(t_in + 17.0), 2))
    put(buf, head(), 0); di_tail(buf, 0.30, 0.62)
    put(buf, body(0.0, 17.0), t_in, 10 ** (3.0 / 20))
    finish(buf, 'D_从头进')


if __name__ == '__main__':
    variant_a(); variant_b(); variant_c(); variant_d()
