"""baelor — 贝勒大圣堂一场：真人动作戏 → 举剑 → 画面凝成三联彩窗 → 行刑人挥剑，劈到时彩窗碎裂。也是「一场戏怎么写」的完整例子（场景、人物时间函数、镜头表）。
python baelor.py strip [小节...] → out/_baelor_strip.jpg"""
import _env
import sys, math, subprocess
from looks import *
import tallfig as F, scene as SC, bighead, glass, shots as S
from stage import *
from txt import Titles
B = 1.6056; R = Out(1920, 1080) if __import__('os').environ.get('RES') == '1080' else Out(960, 540); GY = 772; INK = (0.030, 0.012, 0.014); RIM = (1.0, 0.70, 0.36); LIGHT = (1, -0.6); HN = 384
C = F.CAST; r = np.random.default_rng(4); ST = dict(tau=0.0)
NEDP = dict(C['ned_prison'], body=(0.44, 0.39, 0.34), legs=(0.24, 0.21, 0.20))
BOUND = dict(af=(-24, -50), ab=(-28, -54))

def sky_plate():
    img = S.sky((0.07, 0.02, 0.04), (0.98, 0.55, 0.20), GY, 1.8); img = S.blob(img, 1420, 580, 460, 320, (1.0, 0.8, 0.5), 0.45)
    img = S.glowl(img, lambda c: (c.set_source_rgb(1.0, 0.93, 0.78), c.arc(1420, 610, 118, 0, math.tau), c.fill()), blur=44, k=0.7, sblur=1.5)
    s, c = layer(); SC.sept(c, 1290, GY, 1.0, (0.17, 0.05, 0.05)); img = over(img, s, blur=2.0, opacity=0.95)
    s, c = layer(); SC.skyline(c, GY, np.random.default_rng(4), (0.10, 0.03, 0.04), gap=(520, 1000)); img = over(img, s, blur=1.5, opacity=0.95)
    hz = np.clip((S.yy - 430) / (GY - 430), 0, 1)[..., None] ** 1.8 * (S.yy < GY)[..., None]; img = img * (1 - 0.30 * hz) + np.float32((0.95, 0.45, 0.18)) * 0.30 * hz
    img = np.where((S.yy >= GY)[..., None], np.float32((0.05, 0.02, 0.02)), img)
    img = beam(img, (2250, -260), 128, 141, 2600, col=(1.0, 0.72, 0.38), a=0.26, blur=16); return np.clip(img, 0, 1).astype(np.float32)
def crowd_layer(y0, R0, n, col, rim_a, seed, fists=0.3):
    s, c = layer(); SC.crowd(c, y0, R0, n, np.random.default_rng(seed), col, fists=fists); c.rectangle(0, y0 + R0 * 2.4, W, H); c.fill()
    rgb = lit(np.zeros((H, W, 3), np.float32), s, light=(0.5, -1), rim=RIM, rim_w=2.5, rim_a=rim_a, half_a=0, shade_a=0); return rgb.astype(np.float32), rgba(s)[1][..., 0].copy()
def bob(amp, per, ph, exc_at=6.5):
    def f(t): e = ease((ST['tau'] - exc_at * B) / (0.3 * B)); return (amp * (1 + 2.2 * e)) * math.sin(math.tau * ST['tau'] / (per * B * (1 - 0.5 * e)) + ph)
    return f
def motes(col, n=60, seed=7):
    P = np.random.default_rng(seed).random((n, 5))
    def f(fr, t, M, R):
        ov = np.zeros((R.h, R.w, 3), np.uint8)
        for (a, b, c, d, e) in P:
            x = ((a + 0.02 * math.sin(t * 1.3 + d * 9) - t * 0.012 * c) % 1.0) * R.w; y = ((b - t * (0.02 + 0.04 * c)) % 1.0) * R.h; cv2.circle(ov, (int(x), int(y)), int((1 + e * 1.6) * R.k * 2 + 0.5), tuple(int(v * (0.2 + 0.6 * d)) for v in col), -1, cv2.LINE_AA)
        o = ov.astype(np.float32) / 255; return fr + o + cv2.GaussianBlur(o, (0, 0), 6 * R.k) * 0.8
    return f
PLT = {}
def P0():
    if 'sky' not in PLT: PLT['sky'] = sky_plate()
    return PLT['sky']

# ---------------- 台上（主场景）：时间 t = 这场戏的秒数
def ned_state(t):
    x = kf([(2.0 * B, 1160), (2.8 * B, 800)], t)
    if t < 2.8 * B: p = walk(step_phase(1160 - x, HN), bound=True, lean=7, head=12)
    else: p = kf([(2.9 * B, pose('stand', head=10, **BOUND)), (3.3 * B, pose('kneel')), (8.0 * B, pose('kneel')), (8.8 * B, pose('kneel', head=44, lean=20))], t)
    return x, p
def set_platform():
    sc = Scene(); sc.bg.append((P0(), 0.25)); s, c = layer()
    g = cairo.LinearGradient(0, GY, 0, GY + 90); g.add_color_stop_rgb(0, 0.20, 0.09, 0.06); g.add_color_stop_rgb(1, 0.07, 0.03, 0.03); c.set_source(g); c.rectangle(-200, GY, W + 400, 90); c.fill()
    for i in range(7): q = max(0.012, 0.06 - i * 0.009); c.set_source_rgb(q * 1.5, q * 0.7, q * 0.6); c.rectangle(0, GY + 90 + i * 34, W, 36); c.fill(); c.set_source_rgba(1.0, 0.6, 0.3, max(0, 0.20 - i * 0.04)); c.rectangle(0, GY + 90 + i * 34, W, 2.5); c.fill()
    c.set_source_rgba(1.0, 0.72, 0.40, 0.6); c.rectangle(0, GY, W, 3); c.fill(); rgb, al = rgba(s); sc.bg.append(((rgb.copy(), al[..., 0].copy()), 1.0)); o = {}
    def sil(c, t):
        sw = 0.6 * math.sin(t * 1.7)
        fig(c, 'goldcloak', 250, GY, 372, pose('guard', lean=sw), 1, mono=INK, held=('spear', 180, 130)); fig(c, 'goldcloak', 470, GY, 372, pose('guard', lean=-sw), 1, mono=INK, held=('spear', 180, 130))
        nx, _ = ned_state(t); ix = max(962, nx + 162) if t < 2.8 * B else 962; carry = dict(af=(24, 96), ab=(18, 88))
        if t < 2.8 * B: ip = walk(step_phase(1160 - nx, 384), lean=3, carry=((24, 96), (18, 88)))
        else: ip = kf([(9.0 * B, pose('guard', **carry)), (9.75 * B, pose('strike', af=(150, 186), ab=(144, 182)))], t)
        o['il'] = fig(c, 'ilyn', ix, GY, 384, ip, -1, mono=INK); o['sa'] = kf([(9.0 * B, 180), (9.75 * B, 176)], t)
        fig(c, 'lannguard', 1700, GY, 372, pose('guard', lean=sw), -1, mono=INK, held=('spear', 180, 130)); fig(c, 'little', 1800, GY, 350, pose('stand'), -1, mono=INK)
        fig(c, 'cersei', 1400, GY, 356, kf([(7.1 * B, pose('stand')), (7.5 * B, pose('stand', af=(70, 84), lean=8))], t), -1, mono=INK)
        jx = kf([(5.6 * B, 1262), (6.1 * B, 1190)], t); jp = walk(step_phase(1262 - jx, 330), lean=3) if 5.6 * B < t < 6.1 * B else kf([(6.2 * B, pose('stand')), (6.45 * B, pose('point', af=(96, 100), lean=-2))], t)
        o['jo'] = fig(c, 'joffrey', jx, GY, 330, jp, -1, mono=INK, hat=None)
        gx = kf([(7.0 * B, 1608), (7.4 * B, 1545)], t); fig(c, 'lannguard', gx, GY, 372, kf([(7.0 * B, pose('guard')), (7.4 * B, pose('hold', lean=12))], t), -1, mono=INK)
    sc.add('sil', sil, rim=RIM, light=LIGHT, rim_a=0.85)
    sc.add('glow', lambda c, t: F.sword(c, o['il']['hand'], o['sa'], 64 * 3.84, -1, col=(1.0, 0.94, 0.84)), blur=16, k=0.5)
    sc.add('glow', lambda c, t: S.crown(c, o['jo'], -1), blur=8, k=0.5)
    def sansa(c, t):
        x = kf([(7.0 * B, 1520), (7.4 * B, 1462)], t); p = kf([(4.6 * B, pose('stand')), (5.0 * B, pose('stand', af=(46, 112), ab=(40, 106), head=-4)), (7.0 * B, pose('stand', af=(46, 112), ab=(40, 106), head=-4)), (7.4 * B, pose('reach'))], t)
        fig(c, 'sansa', x, GY, 332, p, -1, mono=(0.96, 0.93, 0.90))
    sc.add('white', sansa)
    sc.add('plain', lambda c, t: (c.save(), c.translate(ned_state(t)[0], GY + 4), c.scale(110, 8), c.set_source_rgba(0, 0, 0, 0.5), c.arc(0, 0, 1, 0, math.tau), c.fill(), c.restore()), blur=4)
    sc.add('col', lambda c, t: fig(c, NEDP, ned_state(t)[0], GY, HN, ned_state(t)[1], -1), light=LIGHT, rim=(1.0, 0.80, 0.52), rim_a=0.85, shade_a=0.35)
    sc.add('np', motes((255, 200, 140), 50))
    for (y0, R0, n, col, ra, d, amp, ph, seed) in ((962, 31, 40, (0.060, 0.022, 0.022), 0.45, 1.25, 5, 0, 5), (1050, 46, 26, (0.018, 0.008, 0.010), 0.0, 1.6, 8, 1.7, 6)):
        rgb, al = crowd_layer(y0, R0, n, col, ra, seed); sc.fg.append((rgb, al, d, bob(amp, 0.5, ph)))
    wr, wa, wadd, _ = S.witness(); sc.fg.append(((wr + wadd).astype(np.float32), wa[..., 0].copy(), 1.6, None)); return sc
# ---------------- 押解：跟拍
def nx_street(t): return 1500 - 300 * t / B
def set_street():
    sc = Scene(); sc.bg.append((P0(), 0.12)); gy = 830; rr = np.random.default_rng(9)
    s, c = layer(); x = -100
    while x < W + 100: w = rr.uniform(90, 200); h = rr.uniform(240, 430); S.poly(c, [(x, gy), (x, gy - h), (x + w * 0.5, gy - h - rr.uniform(20, 70)), (x + w, gy - h), (x + w, gy)], (0.10, 0.035, 0.035)); x += w * 0.92
    rgb, al = rgba(s); rgb = cv2.GaussianBlur(rgb, (0, 0), 2.5); a2 = cv2.GaussianBlur(al[..., 0], (0, 0), 2.5); sc.bg.append(((rgb, a2), 0.5))
    rgb, al = crowd_layer(gy - 150, 30, 46, (0.07, 0.025, 0.025), 0.5, 11, fists=0.35); sc.bg.append(((rgb, al), 0.8))
    s, c = layer(); g = cairo.LinearGradient(0, gy, 0, H); g.add_color_stop_rgb(0, 0.22, 0.10, 0.07); g.add_color_stop_rgb(1, 0.04, 0.015, 0.015); c.set_source(g); c.rectangle(-300, gy, W + 600, H); c.fill(); c.set_source_rgba(1.0, 0.7, 0.4, 0.5); c.rectangle(-300, gy, W + 600, 3); c.fill()
    rgb, al = rgba(s); sc.bg.append(((rgb.copy(), al[..., 0].copy()), 1.0))
    def guards(c, t):
        x = nx_street(t); ph = step_phase(1500 - x, 440)
        fig(c, 'goldcloak', x - 170, gy, 440, walk(ph + 1.2, lean=3, carry=((28, 92), (-6, 0))), -1, mono=INK, held=('spear', 180, 130)); fig(c, 'goldcloak', x + 170, gy, 440, walk(ph + 2.6, lean=3, carry=((28, 92), (-6, 0))), -1, mono=INK, held=('spear', 180, 130))
    sc.add('sil', guards, rim=RIM, light=LIGHT, rim_a=0.85)
    sc.add('col', lambda c, t: fig(c, NEDP, nx_street(t), gy, 440, walk(step_phase(1500 - nx_street(t), 440), bound=True, lean=8, head=14), -1), light=LIGHT, rim=(1.0, 0.80, 0.52), rim_a=0.85, shade_a=0.35)
    sc.add('np', motes((255, 200, 140), 50)); rgb, al = crowd_layer(1000, 50, 20, (0.018, 0.008, 0.010), 0.0, 12, fists=0.5); sc.fg.append((rgb, al, 1.5, bob(9, 0.5, 0.4, exc_at=99))); return sc
# ---------------- 特写：反绑的手
def set_hands():
    sc = Scene(); sc.bg.append((np.clip(cv2.GaussianBlur(P0(), (0, 0), 22) * 0.55, 0, 1), 0.3))
    def hands(c, t):
        cl = 1 - 0.10 * ease((t - 0.5) / 0.5); tr = 3 * math.sin(t * 23) * ease((t - 0.5) / 0.5); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for sg in (-1, 1):
            c.set_line_width(170); c.set_source_rgb(0.44, 0.39, 0.34); c.move_to(960 + sg * 560, 120); c.line_to(960 + sg * 190, 500); c.stroke()
            c.set_line_width(118); c.set_source_rgb(0.80, 0.64, 0.52); c.move_to(960 + sg * 190, 500); c.line_to(960 + sg * 60, 640 + tr); c.stroke()
        for sg in (-1, 1):
            c.set_source_rgb(0.76, 0.60, 0.49); c.save(); c.translate(960 + sg * 78, 742 + tr); c.scale(100, 86 * cl); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore(); c.set_source_rgba(0.35, 0.22, 0.18, 0.7); c.set_line_width(5)
            for i in range(3): c.move_to(960 + sg * (40 + i * 34), 742 + tr - 50 * cl); c.line_to(960 + sg * (36 + i * 34), 742 + tr + 60 * cl); c.stroke()
        c.set_source_rgb(0.62, 0.50, 0.32)
        for i in range(5): c.set_line_width(17); c.move_to(770, 560 + i * 21 + tr); c.curve_to(880, 600 + i * 21 + tr, 1040, 600 + i * 21 + tr, 1150, 560 + i * 21 + tr); c.stroke()
    sc.add('col', hands, light=LIGHT, rim=(1.0, 0.80, 0.52), rim_a=0.8, shade_a=0.5); sc.add('np', motes((255, 200, 140), 40, 3)); return sc
# ---------------- 特写：奈德低头
def set_face():
    sc = Scene(); sc.bg.append((np.clip(cv2.GaussianBlur(P0(), (0, 0), 18) * 0.7, 0, 1), 0.3))
    def hd(c, t): a = 0.13 * ease(t / (0.9 * B)); c.save(); c.translate(1080, 1000); c.rotate(-a); c.translate(-1080, -1000); bighead.ned(c, 1040, 500, 640, -1); c.restore()
    sc.add('col', hd, light=(1, -0.25), rim=(1.0, 0.74, 0.40), rim_a=0.9, shade_a=0.25); sc.add('np', motes((255, 200, 140), 60, 5)); return sc
# ---------------- 仰拍：举剑
def set_sword():
    img = S.sky((0.10, 0.03, 0.04), (0.95, 0.50, 0.18), H, 1.3); img = S.blob(img, 960, 230, 520, 400, (1.0, 0.85, 0.6), 0.55); img = beam(img, (960, -500), 76, 104, 2000, col=(1.0, 0.8, 0.5), a=0.28, blur=22)
    sc = Scene(); sc.bg.append((np.clip(img, 0, 1).astype(np.float32), 0.3)); o = {}
    def il(c, t): o['il'] = fig(c, 'ilyn', 1040, 1760, 1150, kf([(0.05 * B, pose('guard', af=(24, 96), ab=(18, 88))), (0.8 * B, pose('strike', af=(150, 186), ab=(144, 182)))], t), -1, mono=INK); o['a'] = kf([(0.05 * B, 180), (0.8 * B, 177)], t)
    sc.add('sil', il, rim=RIM, light=(0, -1), rim_a=0.9, rim_w=5); sc.add('glow', lambda c, t: F.sword(c, o['il']['hand'], o['a'], 470, -1, col=(1.0, 0.95, 0.86), w=34), blur=26, k=0.8); return sc
# ---------------- 三联彩窗
def tri_glass(k=0.0):
    """k：行刑人挥剑进度，-0.25 蓄力后仰，0 举到最高，1 劈到底。"""
    from windows import NEDP as GN, ILYN as GI, CER as GC, ICE, SK
    G = dict(gold=dict(C['goldcloak'], body=(0.24, 0.26, 0.36), legs=(0.16, 0.17, 0.26), cloak=(0.97, 0.76, 0.16), helm=(0.62, 0.66, 0.74), skin=SK), lann=dict(C['lannguard'], body=(0.74, 0.10, 0.10), legs=(0.40, 0.06, 0.08), cloak=(0.56, 0.05, 0.08), helm=(0.96, 0.76, 0.22), skin=SK),
             jo=dict(C['joffrey'], body=(0.82, 0.10, 0.10), legs=(0.36, 0.06, 0.10), cloak=(0.96, 0.74, 0.18), hair=(0.99, 0.86, 0.36), skin=SK), sa=dict(C['sansa'], body=(0.40, 0.70, 0.92), gown=(0.30, 0.58, 0.86), sleeve=(0.52, 0.78, 0.95), hair=(0.90, 0.38, 0.10), skin=SK))
    def draw(c, gy):
        F.fig(c, 250, gy, 440, dict(G['gold'], held=('spear', 180, 128)), 'guard', 1); F.fig(c, 470, gy, 440, dict(G['gold'], held=('spear', 180, 128)), 'guard', 1)
        F.fig(c, 880, gy, 450, GN, 'kneel', -1); il = F.fig(c, 1085, gy, 452, GI, 'strike', -1, P=dict(lean=-5 + 19 * max(k, 0) + 16 * min(k, 0), head=8 + 14 * max(k, 0), af=(150 - 88 * k, 186 - 108 * k), ab=(144 - 88 * k, 182 - 108 * k))); F.sword(c, il['hand'], 176 - 104 * k, 0.62 * 452, -1, w=26, **ICE)
        F.fig(c, 1745, gy, 440, G['lann'], 'hold', -1); F.fig(c, 1500, gy, 424, GC, 'stand', -1); F.fig(c, 1640, gy, 396, G['sa'], 'reach', -1); F.fig(c, 1360, gy, 396, G['jo'], 'point', -1)
    g, m = glass.window(draw, w=1920, h=1080, seed=12, sun=(0.5, 560 / 1080), R=215 / 1920, gy=880 / 1080, cell=92, mask=glass.triptych_mask(), warm_r=3.0); img, M = glass.wall([(g, m, 0, 0)]); return img.astype(np.float32), M[..., 0]

GLK = {}; KHIT = 0.8                                                                     # KHIT：剑刃碰到脖子时的挥剑进度，彩窗在这一帧碎
def glk(k):
    """挥剑进度 k 的彩窗帧（按 1/20 量化缓存）→ (img, mask)，已缩到输出分辨率。"""
    q = round(max(-0.25, min(KHIT, k)) * 20)
    if q not in GLK: g, m = tri_glass(q / 20); GLK[q] = (cv2.resize(g, (R.w, R.h), interpolation=cv2.INTER_AREA), cv2.resize(m, (R.w, R.h), interpolation=cv2.INTER_AREA))
    return GLK[q]
def glass_init():
    if 'sh' not in PLT:
        g, mm = glk(KHIT); PLT['sh'] = Shatter(g, mm, (880 * R.k, 560 * R.k), n=300); rr = np.random.default_rng(2)
        PLT['cr'] = [[(880 + math.cos(a + rr.normal(0, 0.25) * i * 0.3) * i * 70 + rr.normal(0, 14), 560 + math.sin(a) * i * 70 + rr.normal(0, 14)) for i in range(12)] for a in np.linspace(0, math.tau, 13)[:-1] + rr.normal(0, 0.15, 12)]
def swing(b, hit):
    """hit 小节时劈到；之前 0.2 小节劈下，再之前 0.25 小节蓄力后仰。"""
    return 0.0 if b < hit - 0.45 else (-0.25 * ease((b - (hit - 0.45)) / 0.25) if b < hit - 0.2 else -0.25 + (KHIT + 0.25) * min(1.0, (b - (hit - 0.2)) / 0.2) ** 1.8)
# ---------------- 这场戏的镜头表（小节）：(b0, b1, 场景, 镜头关键帧[(小节, (cx, cy, z))], 时钟：'g' 全场连续 / 'l' 本镜头从 0 起)
SHOTS = [(0, 2, 'street', None, 'l'), (2, 3.5, 'plat', [(2, (960, 560, 1.0)), (3.5, (900, 590, 1.22))], 'g'), (3.5, 4.5, 'plat', [(3.5, (850, 640, 3.3)), (4.5, (835, 655, 3.9))], 'g'),
         (4.5, 5.5, 'plat', [(4.5, (1480, 610, 2.2)), (5.5, (1450, 610, 2.5))], 'g'), (5.5, 7, 'plat', [(5.5, (1250, 600, 2.3)), (6.2, (1200, 590, 2.6)), (7, (1150, 580, 3.0))], 'g'), (7, 8, 'plat', [(7, (1000, 570, 1.12)), (8, (960, 560, 1.02))], 'g'),
         (8, 9, 'face', [(8, (960, 540, 1.0)), (9, (1000, 560, 1.12))], 'l'), (9, 10, 'sword', [(9, (960, 640, 1.0)), (10, (960, 520, 1.12))], 'l'), (10, 10.75, 'plat', [(10, (868, 481, 1.17)), (10.75, (868, 481, 1.17))], 'g')]
TT = Titles(); TT.add(0, 2 * B, 'sub', '认罪那天，全城的人都来了。'); TT.add(2 * B, 3.5 * B, 'tag', '— 君临 · 贝勒大圣堂', 960, 76, 36, 'm'); TT.add(3.5 * B, 4.5 * B, 'sub', '他当众认下叛国。'); TT.add(4.5 * B, 5.5 * B, 'sub', '他们答应过：认了罪，就让他去长城。')
TT.add(6.45 * B, 8 * B, 'gold', '「把他的头拿来。」', 960, 240, 100); TT.add(9.25 * B, 11.5 * B, 'gold', '落下的，是他自己的剑。', 960, 985, 80)
SHAKE = [(6.45 * B, 26, 0.5), (7.0 * B, 10, 1.4), (11.5 * B, 30, 0.3)]; FLASH = [(6.45 * B, 0.5), (9.8 * B, 0.35), (10.25 * B, 0.6), (11.5 * B, 1.0)]
SC_ = {}; DUR = 12.6 * B
def scene(k):
    if k not in SC_: SC_[k] = dict(plat=set_platform, street=set_street, hands=set_hands, face=set_face, sword=set_sword)[k]()
    return SC_[k]
VG = None
def frame(t):
    global VG
    ST['tau'] = t; b = t / B; fr = None
    for (b0, b1, k, cam, clk) in SHOTS:
        if b0 <= b < b1:
            tl = t if clk == 'g' else t - b0 * B; cm = kf(cam, b) if cam else (nx_street(tl) - 70, 620, 1.32 + 0.06 * tl / B); cx, cy, z = cm
            for (ts, amp, d) in SHAKE:
                if ts <= t < ts + d: q = (1 - (t - ts) / d) * amp; cx += q * math.sin(t * 91); cy += q * math.cos(t * 77)
            fr = scene(k).render(tl, (cx, cy, z), R).astype(np.float32); break
    if b >= 10.25:                                                                       # 凝成彩窗 → 裂 → 碎
        glass_init()
        if b < 11.6:
            g = glk(swing(b, 11.5))[0]; u = ease((b - 10.25) / 0.5); z = 1 + 0.05 * ease((b - 10.25) / 1.3); M = np.float32([[z, 0, R.w / 2 * (1 - z)], [0, z, R.h / 2 * (1 - z)]]); gl = cv2.warpAffine(g, M, (R.w, R.h)) * (1.0 + 0.10 * math.sin((b - 10.25) * 6))
            if b >= 11.5:                                                                # 裂纹
                p = (b - 11.5) / 0.1; ov = np.zeros((R.h, R.w, 3), np.uint8)
                for ln in PLT['cr']: n = max(2, int(len(ln) * p)); cv2.polylines(ov, [np.int32(np.float32(ln[:n]) * R.k * z + np.float32([R.w / 2 * (1 - z), R.h / 2 * (1 - z)]))], False, (255, 250, 240), max(1, int(3 * R.k * 2)), cv2.LINE_AA)
                gl = gl + ov.astype(np.float32) / 255
            fr = gl if fr is None else fr * (1 - u) + gl * u
        else: fr = PLT['sh'].frame((b - 11.6) * B, dim=max(0.0, 1 - (b - 11.6) / 0.5))
    if fr is None: fr = np.zeros((R.h, R.w, 3), np.float32)
    for (tf, s) in FLASH:
        if tf <= t < tf + 0.22: fr = fr + s * (1 - (t - tf) / 0.22) ** 2
    if VG is None: yy, xx = np.mgrid[0:R.h, 0:R.w].astype(np.float32); d = np.sqrt(((xx - R.w / 2) / (R.w / 2)) ** 2 + ((yy - R.h / 2) / (R.h / 2)) ** 2) / 1.414; VG = (1 - 0.55 * np.clip(d, 0, 1) ** 2.0)[..., None]; rr = np.random.default_rng(1); PLT['gr'] = [(rr.random((R.h, R.w, 1)).astype(np.float32) - 0.5) * 0.022 for _ in range(6)]
    fr = fr * VG if b < 10.25 else fr; TT.draw(fr, t, R); fr = fr + PLT['gr'][int(t * 30) % 6]
    return (np.clip(fr, 0, 1) * 255).astype(np.uint8)
if __name__ == '__main__':
    from PIL import Image
    if sys.argv[1] == 'strip':
        bs = [float(x) for x in sys.argv[2:]] or [0.3, 1.0, 1.7, 2.2, 2.6, 3.0, 3.4, 3.8, 4.3, 4.8, 5.3, 5.8, 6.3, 6.6, 7.2, 7.6, 8.2, 8.9, 9.2, 9.8, 10.1, 10.5, 11.0, 11.55, 11.75, 11.95, 12.3]
        ims = [cv2.resize(frame(b * B), (480, 270), interpolation=cv2.INTER_AREA) for b in bs]
        while len(ims) % 5: ims.append(np.zeros_like(ims[0]))
        Image.fromarray(np.vstack([np.hstack(ims[i:i + 5]) for i in range(0, len(ims), 5)])).save('out/_baelor_strip.jpg', quality=85)
