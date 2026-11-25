"""纯音频版：B 接法双 BGM + 旁白 + 蛋蛋人萌音 + 重击音效 → out/audio_draft.mp3"""
import os, sys, json, subprocess
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir('/home/ubuntu/mongol/bgm'); sys.path.insert(0, '/home/ubuntu/mongol/bgm'); sys.path.insert(0, '/home/ubuntu/kunyang/zhanju-kit')
import splice as P
from mapwar import audio as A
sys.path.insert(0, HERE)
import common as CM
from script import T0, B, BAR, TOTAL, T_CANNON, T_DROP2, T_NIGHT, T_BAG

SR = P.SR; S = P.S
tl = json.load(open(os.path.join(HERE, 'vo', 'timeline.json'), encoding='utf-8'))


def onset_near(t, win=0.08):
    m = np.abs(P.b2[S(t - win):S(t + win)]).mean(1); thr = 0.25 * m.max()
    return t - win + int(np.argmax(m > thr)) / SR


def build_bgm():
    buf = np.zeros((S(TOTAL), 2))
    gap = T0 - P.T_HIT
    # —— B 接法开头：歌词 → 「帝」回声 + 吸入音 → drop ——
    P.put(buf, P.head(), 0)
    di = P.fade(P.voc[S(2.80):S(3.05)], n_in=S(0.01), n_out=S(0.03))
    for k, g in enumerate([0.62, 0.40, 0.25], 1): P.put(buf, di, 2.80 + 0.20 * k, g * P.G1)
    P.put(buf, P.fade(P.reverb(di)[:S(gap + 0.30)], n_out=S(0.10)), 2.86, 0.42)
    hit = P.b2[S(P.DROP2):S(P.DROP2 + 0.50)]
    P.put(buf, P.fade(P.reverb(hit, 1.0, 4.0)[:S(0.50)][::-1], n_in=S(0.42), n_out=S(0.01)), T0 - 0.50, 0.30)
    c = S(T0) - S(0.02); buf[c:S(T0)] *= np.linspace(1, 0, S(T0) - c)[:, None]
    # —— bgm2 第一段：drop → 炮击前半秒收声 ——
    t_stop = T_CANNON - 0.50
    # 金国段多一小节：把 bgm2 的第 3 小节重复一次（前 6 小节是同一乐句的反复，接缝处 12ms 交叉淡化）
    xf = 0.012; D = P.DROP2
    seg_a = P.fade(P.b2[S(D):S(D + 3 * BAR + xf)].copy(), n_in=S(0.002), n_out=S(xf))
    seg_b = P.fade(P.b2[S(D + 2 * BAR):S(D + 2 * BAR + (t_stop - T0 - 3 * BAR))].copy(), n_in=S(xf), n_out=S(0.06))
    P.put(buf, seg_a, T0, P.G2); P.put(buf, seg_b, T0 + 3 * BAR, P.G2)
    # —— 炮击 = 第二次 drop（bgm2 自己的第二个高能段）——
    d2 = onset_near(45.0)
    seg2 = P.fade(P.b2[S(d2):S(d2 + TOTAL - T_CANNON)].copy(), n_in=S(0.002), n_out=S(1.6))
    P.put(buf, seg2, T_CANNON, P.G2)
    print('drop2 onset in bgm2: %.3f' % d2)
    return buf


def main():
    bgm = build_bgm(); n = len(bgm)
    # 侧链：有人说话时压低 BGM
    env = np.ones(n)
    for L in tl:
        a, b = S(max(0, L['t'] - 0.10)), S(min(TOTAL, L['t'] + L['d'] + 0.15))
        env[a:b] = np.minimum(env[a:b], 0.45 if L['who'] == 'N' else 0.42)
    k = S(0.10); env = np.convolve(env, np.ones(k) / k, 'same')
    env[:S(T0)] = 1.0
    mix = bgm * env[:, None]
    # 人声
    for L in tl:
        w, _ = sf.read(os.path.join(HERE, 'vo', L['id'] + '.wav'))
        w = w / (np.abs(w).max() + 1e-9) * (0.80 if L['who'] == 'N' else 0.82)
        P.put(mix, np.stack([w, w], 1), L['t'])
    # ---- 音效
    def sfx(x, t, g): P.put(mix, np.stack([x, x], 1), t, g)
    T = {L['id']: L['t'] for L in tl}; end = {L['id']: L['t'] + L['d'] for L in tl}
    hit = lambda t, g=0.26, d=0.3: sfx(A.hit(d, sr=SR), t, g)
    boom = lambda t, g=0.4, d=0.9: sfx(A.boom(d, sr=SR), t, g)
    def whoosh(t, g=0.30, d=0.7, seed=1):
        from scipy.signal import butter, lfilter
        r = np.random.default_rng(seed); n = int(d * SR); x = r.standard_normal(n); bb, aa = butter(2, [500 / (SR / 2), 3500 / (SR / 2)], 'band'); x = lfilter(bb, aa, x)
        e = np.sin(np.linspace(0, np.pi, n)) ** 2; sfx((x / np.abs(x).max() * e).astype(np.float32), t - 0.05, g)
    for i in range(4): hit(T0 + 0.6 + i * 0.4, 0.20, 0.22)                    # 点名
    hit(T['a3'] + 0.32, 0.14)                                                 # 呸
    # ① 金：三路出发 → 扎进野狐岭 → 围圈骑射 → 盖章
    for k in range(3): hit(CM.C_JIN1 + 0.10 + 0.42 * k, 0.22)
    whoosh(CM.C_YH0 - 0.40, 0.30, 0.6, 11)
    sfx(A.hooves(CM.C_YH1 - CM.C_YH0 - 0.1, rate=13, sr=SR), CM.C_YH0, 0.22)                 # 围圈骑射：马蹄不停，箭一轮轮落
    sfx(A.arrows(0.6, sr=SR, seed=4), CM.T_YH - 0.47, 0.40); boom(CM.T_YH, 0.36, 0.8); hit(CM.T_YH, 0.30)
    sfx(A.arrows(1.4, sr=SR, seed=5), CM.T_YH + 0.30, 0.28)
    whoosh(CM.C_YH1 - 0.25, 0.22, 0.5, 12); hit(CM.T_END1, 0.30, 0.35)
    # ② 花剌子模
    whoosh(B(9), seed=2); hit(T['b1'] + 3.25, 0.30); hit(T['b6'] + 0.8, 0.30); hit(T['b6'] + 2.0, 0.16)
    boom(T_DROP2, 0.30)
    for k in range(4): hit(T_DROP2 + 1.0 + 0.47 * k, 0.24)
    sfx(A.hooves(2.6, rate=13, sr=SR), T_DROP2 + 0.3, 0.16)
    hit(CM.T_END2, 0.32, 0.35)
    # ③ 罗斯
    whoosh(T_NIGHT, seed=3); hit(end['c2'] + 0.12, 0.34, 0.35)
    whoosh(CM.T_TURN - 0.3, 0.26, 0.5, 13); boom(CM.T_TURN + 0.45, 0.36, 0.8); hit(CM.T_END3, 0.34, 0.35)
    boom(CM.C_BQ0 + 0.28, 0.34, 0.7)
    # ④ 巴格达：三路合围 → 攻城 → 城墙塌
    whoosh(T_BAG, seed=4)
    for k in range(3): hit(CM.C_CA2 + 0.10 + 0.42 * k, 0.22)
    whoosh(CM.C_BG0 - 0.40, 0.30, 0.6, 14)
    boom(CM.T_BG, 0.44, 1.1); hit(CM.T_BG, 0.30); hit(CM.T_END4, 0.34, 0.35); boom(CM.T_BG + 1.35, 0.26, 0.7)
    # 钓鱼城
    whoosh(T['e1'] + 2.0, seed=5); boom(T_CANNON, 0.50, 1.0)
    whoosh(T['f1'] + 3.0, seed=6); boom(T['f1'] + 3.75, 0.45, 1.1)
    mix = np.tanh(mix * 1.1) / 1.1; mix *= 0.92 / np.abs(mix).max()
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    sf.write(os.path.join(out, 'mix.wav'), mix, SR)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(out, 'mix.wav'), '-b:a', '256k', os.path.join(out, '谁惹了蒙古_纯音频版.mp3')], check=True)
    print('saved %.2fs' % (n / SR))


main()
