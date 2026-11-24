"""film — 冰火人物志 01《奈德·史塔克：最重荣誉的人，为什么第一个死》总时间线（逐帧动画，30fps）。
python film.py strip 小节...        抽这些小节处的画面拼成 out/_strip.jpg（小节是 RETIME 表左边那一列的旧小节）
python film.py clip 秒0 秒1         渲染成片的第 秒0–秒1 秒，配 out/mix.wav → out/clip_{高}p.mp4
python film.py full [并行数]        整片：先跑 mix.py，分段并行渲染，拼接配音 → out/ned_{高}p.mp4
python film.py seg i n              只渲染第 i/n 段（无声）→ out/_seg{高}_{i}.mp4
分辨率：默认 960×540；环境变量 RES=1080 出 1920×1080。
导演构思：彩窗 = 后人记住的版本，开场碎了能倒回去，结尾碎了回不来；越往南越红；人小厅堂大；剑落处音乐留白。"""
import _env, os
import sys, math, subprocess
from looks import *
import tallfig as F, scene as SC, bighead, glass, windows, shots as S
from stage import *
from txt import Titles, tlayer, put
import baelor as BA
B = BA.B; R = BA.R; T0 = 0.05; NB = 76; DUR = T0 + NB * B
C = F.CAST; INK = (0.012, 0.016, 0.028); WINK = (0.030, 0.012, 0.014); COLD = (0.50, 0.68, 0.95); WARM = (1.0, 0.62, 0.28); ICEC = (0.86, 0.92, 1.0)
NEDL = S.NEDL; motes = BA.motes; ST = BA.ST
def nofig(fn, *a):
    S.NOFIG = True
    try: return np.clip(fn(*a), 0, 1).astype(np.float32)
    finally: S.NOFIG = False
def snowfall(n=110, seed=3):
    P = np.random.default_rng(seed).random((n, 5))
    def f(fr, t, M, R):
        ov = np.zeros((R.h, R.w, 3), np.uint8)
        for (a, b, c, d, e) in P: cv2.circle(ov, (int(((a - t * (0.03 + 0.05 * c)) % 1.0) * R.w), int(((b + t * (0.10 + 0.14 * c)) % 1.0) * R.h)), int((1 + e * 2.2) * R.k * 2 + 0.5), tuple(int(v * (0.3 + 0.6 * d)) for v in (235, 242, 255)), -1, cv2.LINE_AA)
        o = ov.astype(np.float32) / 255; return fr + o + cv2.GaussianBlur(o, (0, 0), 4 * R.k) * 0.6
    return f
def leaves(n=50, seed=4):
    P = np.random.default_rng(seed).random((n, 5))
    def f(fr, t, M, R):
        ov = np.zeros((R.h, R.w, 3), np.uint8)
        for (a, b, c, d, e) in P: cv2.ellipse(ov, (int(((a + 0.04 * math.sin(t * 1.5 + d * 9)) % 1.0) * R.w), int(((b + t * (0.05 + 0.07 * c)) % 1.0) * R.h)), (int((5 + e * 6) * R.k * 2), int((2 + e * 3) * R.k * 2)), d * 180 + t * 60 * (c - 0.5), 0, 360, (215, 26, 20), -1, cv2.LINE_AA)
        return np.clip(fr * (1 - (ov.sum(2, keepdims=True) > 0) * 0.85) + ov.astype(np.float32) / 255 * 0.85, 0, 2)
    return f
def bundle(c, o, face):
    hx, hy = o['hand']; sx, sy = o['sh']; c.set_source_rgb(0.62, 0.60, 0.58); c.save(); c.translate((hx + sx) / 2 + face * 10, (hy + sy) / 2 + 30); c.rotate(-face * 0.30); c.scale(25, 44); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore(); c.set_source_rgb(0.80, 0.66, 0.56); c.arc((hx + sx) / 2 + face * 20, (hy + sy) / 2 - 8, 11, 0, math.tau); c.fill()
CARRY = dict(af=(24, 96), ab=(18, 88)); UP = dict(af=(150, 186), ab=(144, 182))

# ============ 1 开场：北境，处决逃兵（冷色）
def set_north():
    sc = Scene(); sc.bg.append((nofig(S.snow_walk), 1.0)); GY = 846; o = {}
    def nx(t): return kf([(0, 1560), (1.3 * B, 1270)], t)
    def sil(c, t):
        c.set_source_rgb(*INK); c.rectangle(1010, GY - 46, 110, 46); c.fill()                                                # 木墩
        fig(c, 'little', 1150, GY, 400, pose('kneel', lean=42, head=30), -1, mono=INK, beard=None)
        for i, (x, h) in enumerate(((1640, 430), (1740, 440), (1850, 420))): fig(c, 'goldcloak', x, GY, h, pose('stand', lean=0.5 * math.sin(t + i)), -1, mono=INK, cloak=(0, 0, 0))
        fig(c, S.KID, 1560, GY, 250, pose('stand', head=-6), -1, mono=INK)
    sc.add('sil', sil, rim=COLD, light=(-1, -0.7), rim_a=0.7)
    def ned(c, t):
        x = nx(t)
        if t < 1.3 * B: p = walk(step_phase(1560 - x, 440), lean=3, carry=((24, 96), (18, 88)))
        else: p = kf([(1.4 * B, pose('guard', **CARRY)), (2.6 * B, pose('strike', **UP)), (3.62 * B, pose('strike', lean=-8, **UP)), (3.86 * B, pose('reach', af=(62, 58), ab=(56, 52), lean=26))], t)
        o['n'] = fig(c, NEDL, x, GY, 440, p, -1); o['a'] = kf([(1.4 * B, 180), (2.6 * B, 176), (3.62 * B, 184), (3.86 * B, 72)], t)
    sc.add('col', ned, light=(-1, -0.7), rim=(0.85, 0.92, 1.0), rim_a=0.8, shade_a=0.4)
    sc.add('glow', lambda c, t: F.sword(c, o['n']['hand'], o['a'], 0.62 * 440, -1, col=ICEC), blur=16, k=0.5); sc.add('np', snowfall()); return sc
def set_sword_cold():
    img = S.sky((0.010, 0.016, 0.032), (0.20, 0.27, 0.38), H, 1.4); img = S.blob(img, 960, 210, 560, 420, (0.7, 0.85, 1.0), 0.55); img = beam(img, (960, -500), 76, 104, 2000, a=0.30, blur=22); sc = Scene(); sc.bg.append((np.clip(img, 0, 1).astype(np.float32), 0.3)); o = {}
    def n(c, t): o['n'] = fig(c, NEDL, 1040, 1760, 1150, kf([(0.05 * B, pose('guard', **CARRY)), (1.1 * B, pose('strike', **UP))], t), -1, mono=INK); o['a'] = kf([(0.05 * B, 180), (1.1 * B, 177)], t)
    sc.add('sil', n, rim=COLD, light=(0, -1), rim_a=0.9, rim_w=5); sc.add('glow', lambda c, t: F.sword(c, o['n']['hand'], o['a'], 470, -1, col=ICEC, w=34), blur=26, k=0.8); sc.add('np', snowfall(70, 9)); return sc
# ============ 2 三叉戟河
def set_trident():
    sc = Scene(); sc.bg.append((nofig(S.trident, 0), 1.0)); GY = 920; o = {}; HIT = 0.5 * B; rr = np.random.default_rng(3)
    rub = [(rr.uniform(-2.9, 0.3), rr.uniform(200, 900), rr.uniform(4, 11)) for _ in range(54)]
    def sil(c, t):
        rp = kf([(0, pose('strike', af=(120, 150), ab=(112, 142), lean=-4)), (0.3 * B, pose('strike', af=(146, 172), ab=(138, 164), lean=-12)), (HIT, pose('reach', af=(66, 80), ab=(58, 74), lean=24, lf=(34, 10), lb=(-26, -40))), (1.3 * B, pose('reach', af=(60, 76), ab=(52, 70), lean=20, lf=(30, 8), lb=(-22, -34))), (2.2 * B, pose('stand', af=(20, 40), ab=(10, 30)))], t)
        rx = kf([(0.3 * B, 760), (HIT, 830)], t); o['r'] = fig(c, S.ROB, rx, GY, 540, rp, 1, mono=INK); S.hammer(c, o['r']['hand'], kf([(0, 170), (0.3 * B, 192), (HIT, 96), (1.3 * B, 92), (2.2 * B, 20)], t), 290, 1, INK); S.antlers(c, o['r'], 1, INK)
        hp = kf([(0, pose('strike', af=(120, 150), ab=(110, 140))), (HIT, pose('strike', af=(124, 154), ab=(114, 144))), (HIT + 0.25 * B, pose('stand', lean=-40, head=-20, af=(150, 170), ab=(-60, -90), lf=(40, 10), lb=(10, -20))), (HIT + 0.9 * B, pose('stand', lean=-82, head=-30, af=(160, 176), ab=(-70, -96), lf=(60, 30), lb=(30, 0)))], t)
        hx = kf([(HIT, 1200), (HIT + 0.9 * B, 1420)], t); o['h'] = fig(c, dict(C['goldcloak'], cloak=(0, 0, 0), skirt=None), hx, GY + kf([(HIT + 0.25 * B, 0), (HIT + 0.9 * B, 60)], t), 510, hp, -1, mono=INK, held=('sword', 150, 50) if t < HIT + 0.3 * B else None)
    sc.add('sil', sil, rim=COLD, light=(0.3, -1), rim_a=0.85)
    def rubies(c, t):
        u = t - HIT; cx, cy = 1180, 560; c.set_source_rgb(1.0, 0.16, 0.14)
        for (a, v, q) in rub:
            if u < 0: x, y = cx + math.cos(a) * 18, cy + math.sin(a) * 22; q = q * 0.6
            else: x = cx + math.cos(a) * v * u; y = cy + math.sin(a) * v * u + 520 * u * u
            c.move_to(x, y - q); c.line_to(x + q * 0.8, y); c.line_to(x, y + q); c.line_to(x - q * 0.8, y); c.close_path(); c.fill()
    sc.add('glow', rubies, blur=10, k=0.9); sc.add('np', motes((200, 220, 255), 40, 2)); return sc
# ============ 3 极乐塔
def gy_ridge(x): return float(np.interp(x, [0, 300, 700, 1000, 1180, 1330], [862, 852, 802, 742, 702, 692]))
def set_tower():
    sc = Scene(); sc.bg.append((nofig(S.tower), 1.0))
    def ned(c, t): x = kf([(0, 380), (1.5 * B, 760)], t, smooth=False); fig(c, NEDL, x, gy_ridge(x) + 4, 300, walk(step_phase(x - 380, 300), lean=6), 1, held=('sword', 20, 34))
    sc.add('col', ned, light=(1, -0.5), rim=(1.0, 0.70, 0.40), rim_a=0.85, shade_a=0.55); sc.add('np', motes((255, 190, 120), 40, 6))
    wr, wa, wadd, _ = S.witness(); sc.fg.append(((wr + wadd).astype(np.float32), wa[..., 0].copy(), 1.5, None)); return sc
def set_bed():
    sc = Scene(); sc.bg.append((nofig(S.deathbed, 0), 1.0)); GY = 886
    def ned(c, t):
        x = kf([(0, 330), (0.8 * B, 700), (1.4 * B, 760)], t); p = walk(step_phase(x - 330, 640), lean=5) if t < 0.8 * B else kf([(0.8 * B, pose('stand')), (1.4 * B, pose('kneel1', af=(52, 84), head=10)), (2.0 * B, pose('kneel1', af=(58, 80), head=16, lean=14))], t)
        fig(c, NEDL, x, GY, 640, p, 1)
    sc.add('col', ned, light=(1, -0.6), rim=(1.0, 0.68, 0.38), rim_a=0.8, shade_a=0.5)
    def petals(fr, t, M, R):
        zz, tx, ty = M; ov = np.zeros((R.h, R.w, 3), np.uint8); rr = np.random.default_rng(5)
        for i in range(26): x = 760 + rr.random() * 900; y = ((rr.random() * 900 + t * (60 + 80 * rr.random())) % 900); cv2.ellipse(ov, (int(x * zz + tx + 20 * math.sin(t * 2 + i)), int(y * zz + ty)), (max(1, int(8 * zz)), max(1, int(4 * zz))), i * 40 + t * 50, 0, 360, (90, 150, 255), -1, cv2.LINE_AA)
        o = ov.astype(np.float32) / 255; return fr + o * 0.8 + cv2.GaussianBlur(o, (0, 0), 5 * R.k) * 0.6
    sc.add('np', petals); return sc
def set_babyhand():
    """中景：奈德跪着把襁褓接进怀里，襁褓里伸出一只很小的手够向他的脸（代替手的大特写）。"""
    r = np.random.default_rng(31); bgp = S.bricks(S.firelight(1500, 300, (0.030, 0.018, 0.022), 0.34, 0.14), r, 0.25); bgp = S.floor(bgp, 930, (0.10, 0.06, 0.04), (0.012, 0.008, 0.008), line=(1.0, 0.6, 0.3), la=0.25)
    sc = Scene(); sc.bg.append((np.clip(cv2.GaussianBlur(bgp, (0, 0), 5), 0, 1).astype(np.float32), 0.5)); o = {}; HH = 760; GY = 930
    def ned(c, t): o['n'] = fig(c, NEDL, 860, GY, HH, kf([(0, pose('kneel1', af=(40, 100), ab=(30, 92), head=4, lean=4)), (0.6 * B, pose('kneel1', af=(26, 98), ab=(18, 90), head=30, lean=12))], t), 1)
    sc.add('col', ned, light=(1, -0.5), rim=(1.0, 0.70, 0.40), rim_a=0.85, shade_a=0.55)
    def bun(c, t):
        hx, hy = o['n']['hand']; bx, by = hx - 62, hy - 34; o['b'] = (bx, by); c.save(); c.translate(bx, by); c.rotate(0.50); cl = (0.60, 0.58, 0.55)
        c.set_source_rgb(*cl); c.move_to(-100, -8); c.curve_to(-96, -52, 10, -50, 104, -16); c.curve_to(118, -4, 118, 10, 104, 18); c.curve_to(10, 52, -96, 46, -100, -8); c.close_path(); c.fill()
        c.set_source_rgb(0.74, 0.72, 0.68); c.arc(-84, -6, 38, 0, math.tau); c.fill(); c.set_source_rgb(0.90, 0.76, 0.66); c.arc(-80, -10, 25, 0, math.tau); c.fill(); c.set_source_rgb(0.16, 0.11, 0.09); c.arc(-86, -14, 25, math.radians(150), math.radians(290)); c.close_path(); c.fill()
        c.set_source_rgba(0.30, 0.28, 0.27, 0.55); c.set_line_width(5); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in (-30, 10, 50): c.move_to(k, -38 + abs(k) * 0.2); c.curve_to(k + 18, -10, k + 18, 14, k + 4, 36 - abs(k) * 0.2); c.stroke()
        c.set_source_rgb(0.80, 0.64, 0.52); c.save(); c.translate(52, 34); c.scale(30, 15); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore(); c.restore()
    sc.add('col', bun, light=(1, -0.5), rim=(1.0, 0.78, 0.50), rim_a=0.8, shade_a=0.4)
    def tiny(c, t):
        bx, by = o['b']; g = ease((t - 0.15 * B) / (0.45 * B)); c.set_source_rgb(0.93, 0.79, 0.69); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_width(13); x0, y0 = bx - 38, by - 52; x1, y1 = x0 - 10 * g, y0 - 44 * g; c.move_to(x0, y0 + 14); c.line_to(x1, y1); c.stroke(); c.arc(x1 - 1, y1 - 4, 10, 0, math.tau); c.fill()
    sc.add('col', tiny, light=(1, -0.5), rim=(1.0, 0.85, 0.60), rim_a=0.9, shade_a=0.2); sc.add('np', motes((255, 190, 120), 40, 8)); return sc
def set_snow():
    sc = Scene(); sc.bg.append((nofig(S.snow_walk), 1.0)); GY = 846; o = {}
    def nx(t): return 1560 - 190 * t / B
    sc.nx = nx
    def ned(c, t): x = nx(t); o['n'] = fig(c, NEDL, x, GY, 440, walk(step_phase(1560 - x, 440), lean=9, head=12, carry=((30, 100), (22, 92))), -1); bundle(c, o['n'], -1)
    sc.add('col', ned, light=(-1, -0.7), rim=(0.85, 0.92, 1.0), rim_a=0.8, shade_a=0.4); sc.add('np', snowfall())
    wr, wa, wadd, _ = S.witness(); sc.fg.append(((wr + wadd)[:, ::-1].copy().astype(np.float32), wa[:, ::-1, 0].copy(), 1.5, None)); return sc
# ============ 彩窗墙
def winwall(k, sigil=None):
    g, m = windows.get(k); fr = glass.wall([(g, m, 230, 70)])[0].astype(np.float32)
    if sigil:                                                                            # 片名页：字后面垫一枚压暗的大家徽，和封面一个样子
        import heraldry; n = 860; sr, sa = heraldry.sigil(sigil, n); x0, y0 = 1360 - n // 2, 550 - n // 2; reg = fr[y0:y0 + n, x0:x0 + n]; reg[:] = reg * (1 - 0.9 * sa) + sr * sa * 0.20
    return fr
def four(n, broken=True):
    wins = []
    for i, k in enumerate(['baby', 'wood', 'night', 'sword']):
        g, m = windows.get(k); g = cv2.resize(g, (420, 658), interpolation=cv2.INTER_AREA); m = cv2.resize(m, (420, 658), interpolation=cv2.INTER_AREA)[..., None]; wins.append((g * (0.05 if (i == 3 and broken) else (1.0 if i < n else 0.07)), m, 96 + i * 436, 90))
    return glass.wall(wins)[0].astype(np.float32)
def plate_scene(img, part=None):
    sc = Scene(); sc.bg.append((img, 1.0))
    if part: sc.add('np', part)
    return sc
BLACK = np.zeros((1080, 1920, 3), np.float32) + np.float32((0.006, 0.008, 0.012))
SETS = dict(north=set_north, swordc=set_sword_cold, trident=set_trident, tower=set_tower, bed=set_bed, baby=set_babyhand, snow=set_snow, black=lambda: plate_scene(BLACK),
            wtitle=lambda: plate_scene(winwall('title', 'stark')), w1=lambda: plate_scene(winwall('baby')), w2=lambda: plate_scene(winwall('wood')), w3=lambda: plate_scene(winwall('night')))
# ============ 地图（series/asoiaf/westeros.py：羊皮纸沙盘，被提灯照亮）
import westeros as wmap3, heraldry as HR
TEXC = {}
def tex():
    if 't' not in TEXC: TEXC['t'] = wmap3.texture()
    return TEXC['t']
def glowov(fr, ov, k=1.0): o = ov.astype(np.float32) / 255; return fr + o + cv2.GaussianBlur(o, (0, 0), 5 * R.k * 2) * k
class Ov:
    """不透明叠加层：颜色 + 遮罩（亮底地图上用，不能靠加色发光）。"""
    def __init__(s): s.c = np.zeros((R.h, R.w, 3), np.uint8); s.m = np.zeros((R.h, R.w), np.uint8)
    def line(s, pts, col, th, out=(40, 28, 20)):
        p = [np.int32(pts)]; w = max(1, int(th * R.k * 2))
        for cc, ww in ((out, w + max(2, int(3 * R.k * 2))), (col, w)): cv2.polylines(s.c, p, False, cc, ww, cv2.LINE_AA); cv2.polylines(s.m, p, False, 255, ww, cv2.LINE_AA)
    def poly(s, pts, col, out=(40, 28, 20)): p = [np.int32(pts)]; cv2.fillPoly(s.c, p, col, cv2.LINE_AA); cv2.fillPoly(s.m, p, 255, cv2.LINE_AA); cv2.polylines(s.c, p, True, out, max(1, int(2 * R.k * 2)), cv2.LINE_AA); cv2.polylines(s.m, p, True, 255, max(1, int(2 * R.k * 2)), cv2.LINE_AA)
    def dot(s, xy, rad, col, out=(40, 28, 20)): q = (int(xy[0]), int(xy[1])); rr = max(1, int(rad * R.k * 2)); cv2.circle(s.c, q, rr + max(1, int(2 * R.k * 2)), out, -1, cv2.LINE_AA); cv2.circle(s.m, q, rr + max(1, int(2 * R.k * 2)), 255, -1, cv2.LINE_AA); cv2.circle(s.c, q, rr, col, -1, cv2.LINE_AA)
    def ring(s, xy, rad, col, th, a=1.0): q = (int(xy[0]), int(xy[1])); cv2.circle(s.c, q, max(1, int(rad * R.k * 2)), col, max(1, int(th * R.k * 2)), cv2.LINE_AA); cv2.circle(s.m, q, max(1, int(rad * R.k * 2)), int(255 * a), max(1, int(th * R.k * 2)), cv2.LINE_AA)
    def apply(s, fr, glow=0.0):
        a = (s.m.astype(np.float32) / 255)[..., None]; o = s.c.astype(np.float32) / 255; fr = fr * (1 - a) + o * a
        return fr + cv2.GaussianBlur(o * a, (0, 0), 6 * R.k * 2) * glow if glow else fr
def P3(pts): return [wmap3.XY(p) for p in pts]
def marrow(ov, proj, path, p, col, th=6):
    q = wmap3.smoothline(P3(path), 14); hd, i = along(q, p); pts = [proj(v) for v in q[:i + 1]] + [proj(hd)]; ov.line(pts, col, th)
    (x1, y1) = pts[-1]; (x0, y0) = proj(q[max(0, i - 2)]); d = math.hypot(x1 - x0, y1 - y0) or 1; ux, uy = (x1 - x0) / d, (y1 - y0) / d; L = 34 * R.k; ov.poly([(x1 + ux * L, y1 + uy * L), (x1 - uy * L * 0.6, y1 + ux * L * 0.6), (x1 + uy * L * 0.6, y1 - ux * L * 0.6)], col)
HOUSES = [('stark', [(362, 470), (352, 600), (345, 720), (372, 820), (396, 862)], (235, 238, 245)), ('arryn', [(527, 876), (495, 884), (468, 891)], (120, 170, 235)), ('tully', [(313, 940), (345, 932), (372, 924)], (215, 70, 55)), ('baratheon', [(580, 1213), (500, 1120), (440, 1000), (430, 952)], (240, 190, 50))]   # 各自停在三叉戟河外一圈，旗不叠在一起
def flags(fr, items, t):
    """items: (家族, 屏幕 x, y, 旗高, 升旗进度[, 王冠])，按远近排好再画。"""
    for it in sorted(items, key=lambda it: it[2]): HR.flag(fr, it[0], it[1], it[2], it[3] * R.k, t, it[4], *it[5:])
    return fr
def map1(tl, d, t):
    """四家起兵：四面旗各自升起，沿路压向三叉戟河，身后拖一条家族色的线。"""
    lb = tl / B; c = wmap3.XY((440, 812)); tr = wmap3.XY('trident'); fr, proj = wmap3.pview(tex(), c[0], c[1] - 20 * lb, 3900 - 160 * lb, 0.35, R, lamp=(tr[0], tr[1], 1800), dark=0.35); ov = Ov(); fl = []
    kl = proj(wmap3.XY('kl')); q = (tl * 1.6) % 1.0; ov.ring(kl, 12 + 50 * q, (215, 40, 30), 4, 1 - q); ov.dot(kl, 8, (215, 40, 30))
    for i, (h, path, col) in enumerate(HOUSES):
        p = ease((lb - 0.6 - i * 0.25) / 1.1); ln = wmap3.smoothline(P3(path), 14); hd, k = along(ln, p)
        if p > 0: ov.line([proj(v) for v in ln[:k + 1]] + [proj(hd)], col, 4)
        x, y = proj(hd); fl.append((h, x, y - (4 * R.k * abs(math.sin(t * 9 + i)) if 0 < p < 1 else 0), 128, (lb - 0.1 - i * 0.12) / 0.3))
    return flags(ov.apply(fr, 0.25), fl, t)
def along(q, p):
    x = min(len(q) - 1.0001, max(0.0, p * (len(q) - 1))); i = int(x); return q[i] + (q[i + 1] - q[i]) * (x - i), i
def trail(fr, proj, path, p, t):
    q = wmap3.smoothline(P3(path), 16); hd, i = along(q, p); ov = Ov(); ov.line([proj(v) for v in q[:i + 1]] + [proj(hd)], (150, 30, 20), 5); fr = ov.apply(fr); g = np.zeros((R.h, R.w, 3), np.uint8)
    fl = 0.85 + 0.15 * math.sin(t * 17); x, y = proj(hd); cv2.circle(g, (int(x), int(y)), int(10 * R.k * 2), tuple(int(v * fl) for v in (255, 215, 130)), -1, cv2.LINE_AA); return glowov(fr, g, 2.2), hd
def follow(path, span, tilt, house=None):
    def f(tl, d, t):
        p = ease(tl / (d - 0.5)); q = wmap3.smoothline(P3(path), 16); c, _ = along(q, p); fr, proj = wmap3.pview(tex(), c[0], c[1] - span * 0.06, span, tilt, R, lamp=(c[0], c[1], span * 0.40), dark=0.22); fr, hd = trail(fr, proj, path, p, t)
        if house: x, y = proj(hd); flags(fr, [(house, x, y - 3 * R.k * abs(math.sin(t * 9)), 150, tl / 0.3)], t)
        return fr
    return f
def map3(tl, d, t):
    """国王北上：宝冠雄鹿旗从君临一路走到临冬城；然后狼旗升起，跟着它南下。"""
    lb = tl / B; road = wmap3.KINGSROAD[2:]; q = wmap3.smoothline(P3(road), 16); ua = ease(lb / 1.2); ub = ease((lb - 1.45) / (d / B - 1.45 - 0.3))
    c, _ = along(q, 0.42 * (1 - ua) + ub); span = 3300 - 1150 * ua - 250 * ub; fr, proj = wmap3.pview(tex(), c[0], c[1] - span * 0.06, span, 0.5, R, lamp=(c[0], c[1], span * 0.42), dark=0.22)
    ov = Ov(); gq = q[::-1]; hd, k = along(gq, ua); ov.line([proj(v) for v in gq[:k + 1]] + [proj(hd)], (200, 160, 60), 3); fr = ov.apply(fr); bob = 3 * R.k * abs(math.sin(t * 9))
    lead = 0.15 * ease((lb - 1.2) / 0.5)     # 鹿旗先掉头往南走出一段，狼旗升起后跟上
    if ub > 0: fr, _ = trail(fr, proj, road, ub, t)
    x, y = proj(along(q, min(1.0, ub + lead))[0]) if ua >= 1 else proj(hd); fl = [('baratheon', x, y - (bob if ua < 1 or lead > 0 else 0), 150, 1.0, True)]
    if lb > 1.2: x, y = proj(along(q, ub)[0]); fl.append(('stark', x, y - (bob if ub > 0 else 0), 150, (lb - 1.2) / 0.25))
    return flags(fr, fl, t)
def gopen(tl, d, t):
    """冷开场：三联彩窗中间一扇。0–1 小节推近；1 小节剑落、裂、碎；1.6–2 小节碎片倒飞拼回。"""
    P = BA.PLT; b = tl / B
    BA.glass_init()
    cx, cy, z = kf([(0, (960, 560, 1.22)), (1.0, (965, 600, 1.72)), (1.5, (960, 560, 1.22)), (1.6, (960, 560, 1.20)), (2.0, (962, 580, 1.5))], b)
    if 1.0 <= b < 1.22: q = (1 - (b - 1.0) / 0.22) * 26; cx += q * math.sin(t * 91); cy += q * math.cos(t * 77)
    if b < 1.05:
        fr = BA.glk(BA.swing(b, 1.0))[0] * (1.0 + 0.10 * math.sin(b * 6))
        if b >= 1.0:
            p = (b - 1.0) / 0.05; ov = np.zeros((R.h, R.w, 3), np.uint8)
            for ln in P['cr']: n = max(2, int(len(ln) * p)); cv2.polylines(ov, [np.int32(np.float32(ln[:n]) * R.k)], False, (255, 250, 240), max(1, int(3 * R.k * 2)), cv2.LINE_AA)
            fr = fr + ov.astype(np.float32) / 255
    else:
        ts = (b - 1.05) * B if b < 1.5 else (0.45 * B + (b - 1.5) * B * 0.25 if b < 1.6 else (0.45 * B + 0.025 * B) * (1 - ((b - 1.6) / 0.4) ** 2.2))
        fr = P['sh'].frame(max(0.0, ts), g=1500.0, fade=3.5) if ts > 0.004 else BA.glk(BA.KHIT)[0].copy()
    M = np.float32([[z, 0, R.w / 2 - cx * R.k * z], [0, z, R.h / 2 - cy * R.k * z]]); fr = cv2.warpAffine(fr, M, (R.w, R.h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if 'og' not in P: P['og'] = (1 - 0.78 * np.clip((np.arange(R.h, dtype=np.float32) / R.h - 0.70) / 0.2, 0, 1) ** 1.3)[:, None, None]
    fr = fr * P['og']                                                                     # 底部压暗，托住金字
    if 1.6 <= b < 2.0: v = ((b - 1.6) / 0.4) ** 2; ks = int(60 * v * R.k * 2) | 1; fr = cv2.blur(fr, (1, ks)) if ks > 1 else fr                  # 倒带越来越快：竖向拖影
    return fr
MAPS = dict(gopen=gopen, map1=map1, map2=follow([(462, 1108), (430, 1180), (380, 1260), (340, 1325)], 1500, 0.5, 'stark'), map3=map3)
def kidcam(i, h): return lambda tl: (1560 + i * 250 - 700 * tl / B - 20, 930 - h * 0.86, 2.7)
# ============ 时间线
SHOTS = [(0, 2.0, 'gopen', None, 0),                                                    # 冷开场：彩窗中间一扇推近 → 剑落炸碎 → 碎片倒飞拼回
         (2.0, 2.25, 'dagger', [(2.0, (900, 560, 1.1))], ('rev', 2.7)), (2.25, 2.5, 'paper', [(2.25, (960, 550, 1.05))], ('rev', 2.8)), (2.5, 2.75, 'ring', [(2.5, (960, 560, 1.6))], ('rev', 3.75)), (2.75, 3.0, 'kids', kidcam(0, 500), ('rev', 3.2)),   # 倒放快剪
         (3.0, 3.5, 'baby', [(3.0, (900, 520, 1.5)), (3.5, (910, 470, 1.75))], 2.9), (3.5, 4.0, 'black', [(3.5, (960, 540, 1.0))], 3.5),
         (4, 6, 'wtitle', [(4, (960, 540, 1.0)), (6, (900, 540, 1.06))], 4), (6, 8.5, 'map1', None, 6), (8.5, 11, 'trident', [(8.5, (1000, 600, 1.25)), (9.0, (1020, 600, 1.38)), (11, (1000, 580, 1.15))], 8.5), (11, 12.5, 'map2', None, 11),
         (12.5, 14, 'tower', [(12.5, (700, 620, 1.5)), (14, (900, 560, 1.15))], 12.5), (14, 16, 'bed', [(14, (900, 600, 1.0)), (16, (1100, 620, 1.25))], 14), (16, 17, 'baby', [(16, (900, 560, 1.25)), (17, (910, 470, 1.8))], 16),
         (17, 20, 'snow', lambda tl: (min(1150, 1560 - 190 * tl / B - 120), 600, 1.35), 17), (20, 21, 'black', [(20, (960, 540, 1.0))], 20), (21, 23, 'w1', [(21, (960, 540, 1.0)), (23, (900, 540, 1.06))], 21)]
TT = Titles(); G = 'gold'
def bt(b): return T0 + b * B
def T(b0, b1, sty, s, x=960, y=None, px=None, anchor='m'): TT.add(bt(b0), bt(b1), sty, s, x, y, px, anchor)
def choice(b, e, n, a, c): T(b, e, G, n, 1020, 330, 84, 'l'); T(b + 0.25, e, 'keep', a, 1020, 500, 66, 'l'); T(b + 0.5, e, 'cost', c, 1020, 610, 66, 'l')
T(0, 1.0, G, '七国上下，没人怀疑过他的荣誉。', 960, 930, 76); T(1.0, 2.0, G, '可第一个掉脑袋的，就是他。', 960, 930, 84); T(2.0, 3.0, G, '他不是不懂权力的游戏。', 960, 930, 76); T(3.0, 4.0, G, '他只是有一样东西，不肯拿去赌。', 960, 930, 76)
T(4, 6, 'brand', '奈德·史塔克', 1360, 450, 112); T(4.5, 6, 'keep', '最重荣誉的人', 1360, 610, 54); T(4.75, 6, 'keep', '为什么第一个死？', 1360, 690, 54)
T(6, 8.4, 'sub', '疯王处死了他的父亲和兄长，还要他的人头。'); T(7, 8.4, G, '四家起兵', 330, 300, 96); T(9.1, 11, 'sub', '三叉戟河一战，铁王座换了主人：他最好的兄弟，劳勃。', px=52)
T(11, 12.5, 'sub', '仗打赢了。他却一路向南。'); T(12.5, 14, 'tag', '— 多恩 · 极乐塔', 960, 76, 36, 'm'); T(12.5, 14, 'sub', '在一座塔里，他找到了垂死的妹妹。'); T(14.6, 16, 'sub', '她只来得及说一句：答应我，奈德。')
T(16, 17, 'sub', '她留下一个婴儿，流着龙家的血。'); T(17, 18.5, 'sub', '劳勃知道，这孩子就活不成。'); T(18.5, 20, 'sub', '他把孩子抱回北境，只说——'); T(20, 21, G, '「这是我的私生子。」', 960, 540, 92); choice(21, 23, '第一次选择', '保住：妹妹的孩子', '代价：一生的名誉')
FLASH = [(bt(1.0), 0.9), (bt(2.0), 0.8), (bt(2.25), 0.4), (bt(2.5), 0.4), (bt(2.75), 0.4), (bt(3.0), 0.5), (bt(4), 0.4), (bt(9.0), 0.8), (bt(21), 0.7)]; SHAKE = [(bt(9.0), 30, 0.5)]
# ============ 5 族谱书
def set_book():
    r = np.random.default_rng(41); bgp = S.bricks(S.firelight(300, 200, (0.030, 0.020, 0.020), 0.30, 0.12), r, 0.25); sc = Scene(); sc.bg.append((np.clip(cv2.GaussianBlur(bgp, (0, 0), 8), 0, 1).astype(np.float32), 0.3))
    def head(c, x, y, hair, k=1.0):
        c.set_source_rgb(0.30, 0.22, 0.16); c.save(); c.translate(x, y + 62 * k); c.scale(52 * k, 30 * k); c.arc(0, 0, 1, math.pi, math.tau); c.fill(); c.restore(); c.set_source_rgb(0.86, 0.70, 0.58); c.arc(x, y, 34 * k, 0, math.tau); c.fill()
        c.set_source_rgb(*hair); c.arc(x, y - 3 * k, 37 * k, math.radians(196), math.radians(344)); c.close_path(); c.fill()
    def page(c, t):
        c.set_source_rgb(0.16, 0.09, 0.06); c.rectangle(240, 130, 1440, 840); c.fill()
        for x0 in (270, 975): c.set_source_rgb(0.80, 0.72, 0.56); c.rectangle(x0, 160, 675, 780); c.fill()
        g = cairo.LinearGradient(900, 0, 1020, 0); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(0.5, 0.2, 0.1, 0.05, 0.55); g.add_color_stop_rgba(1, 0, 0, 0, 0); c.set_source(g); c.rectangle(900, 160, 120, 780); c.fill()
        c.set_source_rgba(0.25, 0.18, 0.12, 0.55)
        for i in range(15): c.rectangle(330, 220 + i * 46, 540 - (i % 3) * 80, 8); c.fill()
        for i in range(5):
            u = t - (i * 0.4 * B if i < 4 else 1.5 * B)
            if u < 0: continue
            y = 250 + i * 138; k = 1 + 0.25 * max(0, 1 - u / 0.15); blk = (0.07, 0.06, 0.06); head(c, 1110, y, blk, k); c.set_source_rgba(0.25, 0.18, 0.12, 0.8); c.set_line_width(6); c.move_to(1180, y + 10); c.line_to(1330, y + 10); c.stroke()
            c.move_to(1330, y + 10); c.line_to(1306, y - 4); c.line_to(1306, y + 24); c.close_path(); c.fill(); head(c, 1420, y, blk if i < 4 else (0.80, 0.62, 0.20), k)
    sc.add('plain', page)
    def goldh(c, t):
        if t >= 1.5 * B: c.set_source_rgb(1.0, 0.82, 0.32); c.arc(1420, 250 + 4 * 138 - 3, 37, math.radians(196), math.radians(344)); c.close_path(); c.fill()
    sc.add('glow', goldh, blur=20, k=1.2); sc.add('np', motes((255, 190, 120), 40, 4)); return sc
def set_kids():
    sc = Scene(); sc.bg.append((nofig(S.kids), 1.0)); GY = 930; os_ = []
    def kd(c, t):
        os_.clear()
        for i, h in enumerate((500, 440, 360)): x = 1560 + i * 250 - 700 * t / B; os_.append(fig(c, S.KID, x, GY, h, walk(step_phase(2050 - x + i * 90, h) , amp=32, arm=30, lean=10), -1, mono=INK))
    sc.add('sil', kd, rim=WARM, light=(-1, -0.4), rim_a=0.8); sc.add('glow', lambda c, t: [S.goldhair(c, o, -1, long=(1.5 if i == 1 else 0)) for i, o in enumerate(os_)], blur=16, k=0.9)
    sc.add('col', lambda c, t: fig(c, NEDL, 520, GY, 640, pose('stand', head=6), 1), light=(-1, -0.4), rim=WARM, rim_a=0.8, shade_a=0.5); sc.add('np', motes((255, 190, 120), 40, 5)); return sc
# ============ 6 神木林 + 分屏
def set_wood():
    sc = Scene(); sc.bg.append((nofig(S.godswood, 0), 1.0)); GY = 890; o = {}
    def cer(c, t): x = kf([(0, 1780), (0.85 * B, 1330)], t); o['c'] = fig(c, 'cersei', x, GY, 520, walk(step_phase(1780 - x, 520), amp=14, arm=6, lean=2) if t < 0.85 * B else pose('stand'), -1, mono=INK)
    sc.add('sil', cer, rim=(0.95, 0.35, 0.25), light=(-1, -0.6), rim_a=0.85); sc.add('glow', lambda c, t: S.goldhair(c, o['c'], -1, long=1.9), blur=14, k=0.7)
    sc.add('col', lambda c, t: fig(c, NEDL, 560, GY, 560, pose('stand', af=(30, 70)), 1), light=(1, -0.7), rim=(0.75, 0.95, 0.95), rim_a=0.7, shade_a=0.45); sc.add('np', leaves()); return sc
def set_nedhead():
    img = S.sky((0.010, 0.030, 0.035), (0.07, 0.16, 0.16), H, 1.5); img = S.blob(img, 1300, 400, 600, 500, (0.5, 0.8, 0.8), 0.18); sc = Scene(); sc.bg.append((np.clip(img, 0, 1).astype(np.float32), 0.3))
    sc.add('col', lambda c, t: bighead.ned(c, 520, 500, 640, 1), light=(1, -0.2), rim=(0.70, 0.95, 0.90), rim_a=0.8, shade_a=0.45); sc.add('np', leaves(20, 6)); return sc
def set_cerhead():
    img = S.sky((0.05, 0.012, 0.016), (0.30, 0.07, 0.05), H, 1.5); img = S.blob(img, 700, 420, 600, 500, (1.0, 0.5, 0.3), 0.20); sc = Scene(); sc.bg.append((np.clip(img, 0, 1).astype(np.float32), 0.3)); o = {}
    sc.add('col', lambda c, t: fig(c, 'cersei', 1470, 3560, 3400, pose('stand', head=3), -1), light=(-1, -0.25), rim=(1.0, 0.72, 0.45), rim_a=0.8, shade_a=0.6); sc.add('np', leaves(20, 7)); return sc
SPM = {}
def split(tl, d, t):
    if 'm' not in SPM:
        yy, xx = np.mgrid[0:R.h, 0:R.w].astype(np.float32); bx = (1060 - 200 * yy / R.h) * R.k; SPM['m'] = np.clip((xx - bx) / 2 + 0.5, 0, 1)[..., None]; SPM['l'] = np.clip(1 - np.abs(xx - bx) / (3 * R.k * 2), 0, 1)[..., None]
    u = ease(tl / (0.25 * B)); a = scene('nedhead').render(tl, (960 + 500 * (1 - u), 540, 1.0 + 0.05 * tl / d), R); b = scene('cerhead').render(tl, (960 - 500 * (1 - u), 540, 1.0 + 0.05 * tl / d), R); k = ease((tl - 0.9 * B) / (0.3 * B))
    return (a * (1 - 0.45 * k)) * (1 - SPM['m']) + (b * (0.45 + 0.55 * k)) * SPM['m'] + SPM['l'] * np.float32((0.95, 0.90, 0.80))
# ============ 7 国王临终 / 那一夜
def set_king():
    sc = Scene(); sc.bg.append((nofig(S.kingbed), 1.0)); GY = 910; o = {}
    def arm(c, t): a = kf([(0.2 * B, 0.0), (0.7 * B, 1.0), (1.25 * B, 1.0), (1.45 * B, 0.0)], t); c.set_source_rgb(*INK); c.set_line_width(46); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(1230, GY - 290); c.line_to(1130 - 40 * a, GY - 300 - 150 * a); c.stroke()
    sc.add('sil', arm, rim=WARM, light=(1, -1), rim_a=0.6); sc.add('col', lambda c, t: o.update(n=fig(c, NEDL, 440, GY, 620, kf([(0, pose('stand', head=8, af=(30, 86))), (1.5 * B, pose('stand', head=22, af=(30, 86), lean=5))], t), 1)), light=(1, -0.5), rim=WARM, rim_a=0.8, shade_a=0.5)
    sc.add('glow', lambda c, t: (c.set_source_rgb(0.96, 0.92, 0.82), c.save(), c.translate(o['n']['hand'][0] + 30, o['n']['hand'][1]), c.rotate(-0.2), c.rectangle(-36, -52, 72, 96), c.fill(), c.restore()), blur=12, k=0.35)
    sc.add('np', lambda fr, t, M, R: fr * (1 + 0.03 * math.sin(t * 19)) * (1 - 0.5 * ease((t - 1.45 * B) / (0.15 * B)))); sc.add('np', motes((255, 190, 120), 40, 5))
    wr, wa, wadd, _ = S.witness(); sc.fg.append(((wr + wadd).astype(np.float32), wa[..., 0].copy(), 1.5, None)); return sc
def ned_night(t): return 620 if t < 1.5 * B else 620 - 330 * (t - 1.5 * B) / B
def set_night():
    sc = Scene(); sc.bg.append((nofig(S.night), 1.0)); GY = 910
    sc.add('sil', lambda c, t: fig(c, dict(C['joffrey'], hat=None), 1010, GY, 560, kf([(0.25 * B, pose('stand')), (0.6 * B, pose('point')), (1.5 * B, pose('point')), (1.8 * B, pose('stand', af=(30, 50)))], t), 1, mono=INK), rim=WARM, light=(1, -0.5), rim_a=0.8)
    def ned(c, t):
        x = ned_night(t)
        if t < 1.5 * B: fig(c, NEDL, x, GY, 600, kf([(0.7 * B, pose('stand')), (1.2 * B, pose('stand', lean=-4, head=14, af=(-6, 4)))], t), 1)
        else: fig(c, NEDL, x, GY, 600, walk(step_phase(620 - x, 600), lean=5, head=16, arm=10), -1)
    sc.add('col', ned, light=(-1, -0.7), rim=(0.70, 0.82, 1.0), rim_a=0.75, shade_a=0.45); sc.add('np', motes((200, 220, 255), 40, 6)); return sc
# ============ 8 王座厅 / 撕遗诏 / 匕首
def set_throne():
    sc = Scene(); sc.bg.append((nofig(S.throne, 0), 1.0)); GY = 880; o = {}; TB = (3.0 * B, 3.25 * B, 3.5 * B); rr = np.random.default_rng(31); bits = [(rr.normal(0, 150), rr.uniform(-320, 60), rr.uniform(0, 3), rr.uniform(14, 34), rr.uniform(10, 26), rr.uniform(-3, 3)) for _ in range(30)]
    def nx(t): return kf([(0, 230), (1.4 * B, 830)], t)
    def court(c, t):
        o['j'] = fig(c, 'joffrey', 1690, GY - 170, 380, pose('stand', lf=(86, 2), lb=(82, -2), lean=-4, af=(60, 88)), -1, mono=INK)
        o['c'] = fig(c, 'cersei', 1300, GY - 10, 520, kf([(1.5 * B, pose('stand')), (2.0 * B, pose('hold', af=(60, 96), ab=(50, 88))), (2.2 * B, pose('hold', af=(60, 96), ab=(50, 88))), (2.35 * B, pose('hold', af=(100, 124), ab=(18, 48)))], t), -1, mono=INK)
    sc.add('sil', court, rim_a=0.8, light=(-1, -0.75)); sc.add('glow', lambda c, t: (S.crown(c, o['j'], -1), S.goldhair(c, o['c'], -1, long=1.9)), blur=10, k=0.6)
    for i in range(3):
        def gd(c, t, i=i):
            x = nx(t) - 380 - 160 * i; tb = TB[i]
            if t < 1.4 * B: p = walk(step_phase(x + 150 + 160 * i, 560) + i, lean=3, carry=((28, 92), (-6, 0))); a = 180
            else: p = kf([(tb, pose('guard')), (tb + 0.12 * B, pose('hold', lean=10, lf=(24, 6), lb=(-16, -30)))], t); a = kf([(tb, 180), (tb + 0.12 * B, 92)], t)
            fig(c, 'goldcloak', x, GY, 560, p, 1, mono=INK, held=('spear', a, 130))
        sc.add('sil', gd, rim_a=0.8, light=(1, -0.75), rim=COLD)
    def ned(c, t):
        x = nx(t)
        if t < 1.4 * B: p = walk(step_phase(x - 230, 580), lean=3, carry=((50, 90), (-6, 4)))
        else: p = kf([(1.4 * B, pose('stand', af=(50, 90))), (2.2 * B, pose('stand', af=(50, 90))), (2.6 * B, pose('stand', af=(6, 14))), (3.0 * B, pose('stand', af=(6, 14))), (3.3 * B, pose('stand', lean=-4, head=-8, af=(-14, 26), ab=(-20, -10)))], t)
        o['n'] = fig(c, NEDL, x, GY, 580, p, 1)
    sc.add('col', ned, light=(-1, -0.9), rim=(0.80, 0.90, 1.0))
    def will(c, t):
        c.set_source_rgb(0.96, 0.94, 0.88)
        if t < 2.2 * B: h0 = o['n']['hand']; h1 = o['c']['hand']; k = ease((t - 2.0 * B) / (0.2 * B)); c.save(); c.translate(h0[0] + 30 + (h1[0] - 30 - h0[0] - 30) * k, h0[1] + (h1[1] - h0[1]) * k - 10); c.rotate(0.15); c.rectangle(-36, -50, 72, 96); c.fill(); c.restore()
        else:
            u = t - 2.2 * B; hx, hy = o['c']['hand']
            for (dx, dy, a, w, h, vr) in bits: c.save(); c.translate(hx - 40 + dx * min(1, u * 3), hy + dy * min(1, u * 3) + 140 * u * u + 60 * u); c.rotate(a + vr * u); c.rectangle(-w / 2, -h / 2, w, h); c.fill(); c.restore()
    sc.add('glow', will, blur=12, k=0.4); sc.add('np', lambda fr, t, M, R: fr * (1 - (1 - np.float32((1.0, 0.80, 0.80))) * ease((t - 3.0 * B) / (0.6 * B)))); sc.add('np', motes((200, 220, 255), 50, 7)); return sc
def set_paper():
    sc = Scene(); sc.bg.append((np.clip(cv2.GaussianBlur(nofig(S.throne, 0), (0, 0), 16) * 0.6, 0, 1).astype(np.float32), 0.3)); rr = np.random.default_rng(8); zig = [(960 + rr.uniform(-34, 34), 150 + i * 56) for i in range(15)]
    def sheet(c, t):
        u = ease((t - 0.25 * B) / (0.45 * B))
        for sg in (-1, 1):
            c.save(); c.translate(960 + sg * 30 * u, 930); c.rotate(sg * 0.30 * u); c.translate(-960, -930); c.set_source_rgb(0.93, 0.88, 0.74); c.move_to(960 + sg * 330, 150); [c.line_to(*p) for p in zig]; c.line_to(960 + sg * 330, 934); c.close_path(); c.fill()
            c.set_source_rgba(0.25, 0.18, 0.12, 0.6)
            for i in range(11): c.rectangle(960 + sg * 60 if sg > 0 else 960 - 290, 230 + i * 54, 230, 8); c.fill()
            c.set_source_rgb(0.42, 0.03, 0.05); c.set_line_width(120); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(960 + sg * 700, 40); c.line_to(960 + sg * 360, 200); c.stroke(); c.set_source_rgb(0.95, 0.80, 0.68); c.arc(960 + sg * 320, 215, 62, 0, math.tau); c.fill(); c.restore()
        c.set_source_rgb(0.62, 0.05, 0.06); c.arc(960 - 150 - 60 * u, 830 + 20 * u, 46, 0, math.tau); c.fill()
    sc.add('col', sheet, light=(-1, -0.8), rim=(0.85, 0.92, 1.0), rim_a=0.5, shade_a=0.3); sc.add('np', motes((200, 220, 255), 30, 9)); return sc
def set_dagger():
    r = np.random.default_rng(25); TX, TY = 1620, 330; sc = Scene(); sc.bg.append((np.clip(S.torch(S.bricks(S.firelight(TX, TY, a=0.34), r), TX, TY), 0, 1).astype(np.float32), 0.6))
    sc.add('sil', lambda c, t: fig(c, 'little', 330 - 300 * (1 - ease(t / (0.3 * B))), 4060, 3900, pose('stand'), 1, mono=(0.02, 0.018, 0.022)), rim=WARM, light=(1, -0.2), rim_a=0.75, rim_w=5)
    def hd(c, t): a = 0.06 * ease((t - 0.2 * B) / (0.3 * B)); c.save(); c.translate(820, 1000); c.rotate(-a); c.translate(-820, -1000); bighead.ned(c, 900, 400, 640, 1); c.restore()
    sc.add('col', hd, light=(1, -0.15), rim=WARM, rim_a=0.75, shade_a=0.5)
    def off(t): k = 1 - ease(t / (0.3 * B)); return (-460 * k, 240 * k)
    def arm(c, t): dx, dy = off(t); c.set_source_rgb(0.02, 0.018, 0.022); c.set_line_width(120); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(380 + dx, 1150 + dy); c.line_to(700 + dx, 930 + dy); c.stroke(); c.arc(730 + dx, 915 + dy, 62, 0, math.tau); c.fill()
    sc.add('sil', arm, rim=WARM, light=(0.3, -1), rim_a=0.6, rim_w=4); sc.add('glow', lambda c, t: S.poly(c, [(760 + off(t)[0], 885 + off(t)[1]), (1120 + off(t)[0], 838 + off(t)[1]), (1170 + off(t)[0], 850 + off(t)[1]), (770 + off(t)[0], 935 + off(t)[1])], (0.90, 0.94, 1.0)), blur=18, k=0.6)
    sc.add('np', motes((255, 160, 60), 60, 10)); return sc
# ============ 9 黑牢
def set_cell():
    r = np.random.default_rng(27); img = S.bricks(np.zeros((H, W, 3), np.float32) + np.float32((0.014, 0.018, 0.030)), r, 0.45); img = beam(img, (300, -200), 62, 80, 1500, a=0.20, blur=16); GY = 900
    img = S.floor(img, GY, (0.06, 0.07, 0.10), (0.008, 0.010, 0.016), line=(0.5, 0.6, 0.8), la=0.2); img = S.blob(img, 640, GY + 30, 260, 40, (0.6, 0.75, 1.0), 0.16); sc = Scene(); sc.bg.append((np.clip(img, 0, 1).astype(np.float32), 1.0)); o = {}
    VAR = dict(body=(0.1, 0.1, 0.1), skirt='gown', gown=(0.1, 0.1, 0.1), hairstyle='bald', bulk=1.25, tbulk=1.2)
    def vx(t): return kf([(0, 2050), (1.3 * B, 1300)], t)
    sc.add('col', lambda c, t: fig(c, S.NEDP, 640, GY, 420, kf([(0.6 * B, pose('kneel', af=(10, 30), ab=(4, 24), head=36, lean=18)), (1.2 * B, pose('kneel', af=(10, 30), ab=(4, 24), head=-4, lean=8))], t), 1, bound=False), light=(-0.4, -1), rim=(0.70, 0.82, 1.0), rim_a=0.7, shade_a=0.5)
    sc.add('sil', lambda c, t: o.update(v=fig(c, VAR, vx(t), GY, 520, walk(step_phase(2050 - vx(t), 520), amp=12, lean=2, carry=((50, 120), (-4, 6))) if t < 1.3 * B else pose('stand', af=(50, 120)), -1, mono=INK)), rim=WARM, light=(0, -1), rim_a=0.8)
    def flame(c, t): hx, hy = o['v']['hand']; f = 1 + 0.12 * math.sin(t * 21); c.set_source_rgb(0.05, 0.04, 0.04); c.rectangle(hx - 5, hy - 40, 10, 70); c.fill(); c.set_source_rgb(1.0, 0.72, 0.30); c.save(); c.translate(hx, hy - 62); c.scale(16, 30 * f); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
    sc.add('glow', flame, blur=34, k=1.3)
    def light(fr, t, M, R):
        zz, tx, ty = M; hx, hy = o['v']['hand']; yy, xx = np.mgrid[0:R.h, 0:R.w].astype(np.float32); d = np.sqrt((xx - (hx * zz + tx)) ** 2 + (yy - ((hy - 60) * zz + ty)) ** 2) / (zz + 1e-6); return fr + (0.22 * np.exp(-d / 330))[..., None] * np.float32((1.0, 0.55, 0.22)) * (1 + 0.08 * math.sin(t * 21))
    sc.add('np', light); return sc
def set_cellface():
    def plate(t):                                                                       # 129–130.6 拍眼睛合上；泪先在眼角聚起，131.6 拍起往下滑
        n = beat_of(48.5 + t / B); return S.face(True, closed=ease((n - 129.0) / 1.6), tear=0.15 * float(np.clip((n - 130.4) / 1.2, 0, 1)) + 0.85 * float(np.clip((n - 131.6) / 5.2, 0, 1)) ** 1.3)
    sc = Scene(); sc.bg.append((plate, 1.0)); sc.add('np', lambda fr, t, M, R: fr * (1 + 0.04 * math.sin(t * 17) + 0.02 * math.sin(t * 41))); sc.add('np', motes((255, 160, 60), 60, 12)); return sc
# ============ 10 收尾
def four2(n):
    wins = []; r = np.random.default_rng(77)
    for i, k in enumerate(['baby', 'wood', 'night', 'sword']):
        g, m = windows.get(k); g = cv2.resize(g, (420, 658), interpolation=cv2.INTER_AREA); m = cv2.resize(m, (420, 658), interpolation=cv2.INTER_AREA)[..., None]
        if i == 3: edge = 1 - cv2.erode(m[..., 0], np.ones((150, 150), np.uint8)); nz = cv2.GaussianBlur(r.random(m.shape[:2]).astype(np.float32), (0, 0), 9); keep = (edge * (nz > nz.mean() + 0.3 * nz.std()))[..., None]; g = g * (0.03 + 0.75 * keep)
        else: g = g * (1.0 if i < n else 0.07)
        wins.append((g, m, 96 + i * 436, 90))
    return glass.wall(wins)[0].astype(np.float32)
NORTH = ['winterfell', 'whiteharbor', (250, 520), (480, 400), (300, 360), (520, 480), (330, 640), 'castleblack']
KINGS = [('riverrun', 'stark'), ('kl', 'joffrey'), ('dragonstone', 'stannis'), ('storm', 'baratheon'), ('pyke', 'greyjoy')]
def map4(tl, d, t):
    lb = tl / B; c0 = wmap3.XY('winterfell'); c1 = wmap3.XY((430, 900)); u = ease(lb / 3.2); cx, cy = c0[0] + (c1[0] - c0[0]) * u, c0[1] + (c1[1] - c0[1]) * u; fr, proj = wmap3.pview(tex(), cx, cy, 2300 + 1500 * u, 0.35, R, lamp=(cx, cy, 1100 + 900 * u), dark=0.30)
    fl = [('stark', *proj(wmap3.XY(p)), 96 if i else 130, (lb - i * 0.2) / 0.3) for i, p in enumerate(NORTH) if lb > i * 0.2]
    fl += [(h, *proj(wmap3.XY(p)), 150, (lb - 2 - i * 0.25) / 0.25, True) for i, (p, h) in enumerate(KINGS) if lb > 2 + i * 0.25]
    return flags(fr, fl, t)
EC = {}
def endcard(tl, d, t):
    import endcard as brandfig
    rgb, al, add, (lx, ly) = [cv2.resize(a, (R.w, R.h), interpolation=cv2.INTER_AREA) if isinstance(a, np.ndarray) else a for a in brandfig.greenseer(560, 900, 600, tl, hide='stark')]; al = al[..., None]
    if 'd' not in EC: EC['d'] = np.mgrid[0:R.h, 0:R.w].astype(np.float32)
    yy, xx = EC['d']; dd = np.sqrt((xx - lx * R.k) ** 2 + ((yy - ly * R.k) * 1.3) ** 2) / R.k
    fr = np.zeros((R.h, R.w, 3), np.float32) + np.float32((0.006, 0.008, 0.012)) + (0.20 * np.exp(-dd / 260))[..., None] * np.float32((1.0, 0.62, 0.30)); fr[int(900 * R.k):int(900 * R.k) + max(1, int(3 * R.k))] += np.float32((0.25, 0.15, 0.08)) * np.exp(-np.abs(np.arange(R.w) / R.k - lx) / 500)[None, :, None]
    return (fr * (1 - al) + rgb + add) * ease(tl / 0.5)
MAPS.update(split=split, map4=map4, end=endcard)
SETS.update(book=set_book, kids=set_kids, wood=set_wood, nedhead=set_nedhead, cerhead=set_cerhead, king=set_king, night=set_night, throne=set_throne, paper=set_paper, dagger=set_dagger, cell=set_cell, cellface=set_cellface,
            f0=lambda: plate_scene(four2(0)), f1=lambda: plate_scene(four2(1)), f2=lambda: plate_scene(four2(2)), f3=lambda: plate_scene(four2(3)))
# ============ v3 新增：俯拍王座厅（长矛一圈调转）
def set_ring():
    sc = Scene(); sc.bg.append((BLACK.copy(), 1.0)); CX, CY = 960, 560; N = 14; RR = 330; rr = np.random.default_rng(8); jit = rr.normal(0, 0.05, N)
    def td(c, x, y, ang, cloak, top, s=1.0, cl=1.0):
        c.save(); c.translate(x, y); c.rotate(ang); c.set_source_rgba(0, 0, 0, 0.45); c.save(); c.rotate(-ang); c.translate(46 * s, 30 * s); c.scale(70 * s, 30 * s); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
        c.set_source_rgb(*cloak); c.move_to(-6 * s, -30 * s); c.curve_to(-70 * s * cl, -40 * s, -90 * s * cl, 0, -70 * s * cl, 40 * s); c.line_to(-6 * s, 30 * s); c.close_path(); c.fill()
        c.set_source_rgb(*[v * 0.55 for v in cloak]); c.save(); c.scale(22 * s, 34 * s); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore(); c.set_source_rgb(*top); c.arc(3 * s, 0, 15 * s, 0, math.tau); c.fill(); c.restore()
    def draw(c, t):
        a = math.radians(kf([(0, -7), (1.5 * B, 6)], t)); c.translate(CX, CY); c.rotate(a); c.translate(-CX, -CY)
        c.set_source_rgb(0.050, 0.044, 0.050); c.rectangle(-600, -600, 3200, 2400); c.fill(); c.set_line_width(3)
        for i in range(-6, 30):
            for j in range(-6, 18):
                if (i + j) % 2: c.set_source_rgb(0.070, 0.060, 0.064); c.rectangle(i * 120, j * 120, 120, 120); c.fill()
        for k in range(5):                                                               # 高窗投下的光
            x0 = 200 + k * 330; g = cairo.LinearGradient(x0, 0, x0 + 520, 900); g.add_color_stop_rgba(0, 1.0, 0.62, 0.30, 0.20); g.add_color_stop_rgba(1, 1.0, 0.50, 0.25, 0.0); c.set_source(g); c.move_to(x0, -200); c.line_to(x0 + 150, -200); c.line_to(x0 + 700, 1300); c.line_to(x0 + 480, 1300); c.close_path(); c.fill()
        g = cairo.RadialGradient(CX, CY, 60, CX, CY, 560); g.add_color_stop_rgba(0, 0.9, 0.95, 1.0, 0.16); g.add_color_stop_rgba(1, 0, 0, 0, 0); c.set_source(g); c.arc(CX, CY, 560, 0, math.tau); c.fill()
        c.set_source_rgb(0.035, 0.030, 0.034)                                             # 王座台阶
        for k in range(4): c.rectangle(CX - 300 + k * 36, -330 + k * 30, 600 - k * 72, 330 - k * 26); c.fill(); c.set_source_rgb(0.035 + 0.012 * (k + 1), 0.030 + 0.010 * (k + 1), 0.034 + 0.010 * (k + 1))
        td(c, CX, 20, math.pi / 2, (0.75, 0.56, 0.16), (0.98, 0.82, 0.36), 0.9); td(c, CX - 200, 120, math.pi / 2 + 0.3, (0.55, 0.06, 0.08), (0.98, 0.82, 0.36), 1.0, 1.3)
        for i in range(N):
            th = i / N * math.tau + jit[i] + 0.2; x, y = CX + RR * math.cos(th), CY + RR * math.sin(th) * 0.92; u = ease((t - (0.25 + i * 0.075) * B) / (0.10 * B)); L = 18 + 205 * u; fa = th + math.pi
            td(c, x, y, fa, (0.66, 0.48, 0.13), (0.62, 0.64, 0.70)); hx, hy = x + 22 * math.cos(fa + 1.2), y + 22 * math.sin(fa + 1.2)
            c.set_source_rgb(0.46, 0.36, 0.26); c.set_line_width(8); c.move_to(hx - 40 * (1 - u) * math.cos(fa), hy - 40 * (1 - u) * math.sin(fa)); c.line_to(hx + L * math.cos(fa), hy + L * math.sin(fa)); c.stroke()
        td(c, CX, CY, -math.pi / 2, (0.50, 0.52, 0.56), (0.20, 0.15, 0.12), 1.15, 1.2)
    sc.add('plain', draw)
    def tips(c, t):
        a = math.radians(kf([(0, -7), (1.5 * B, 6)], t)); c.translate(CX, CY); c.rotate(a); c.translate(-CX, -CY); c.set_source_rgb(0.92, 0.96, 1.0)
        for i in range(N):
            th = i / N * math.tau + jit[i] + 0.2; x, y = CX + RR * math.cos(th), CY + RR * math.sin(th) * 0.92; u = ease((t - (0.25 + i * 0.075) * B) / (0.10 * B)); L = 18 + 205 * u; fa = th + math.pi; hx, hy = x + 22 * math.cos(fa + 1.2), y + 22 * math.sin(fa + 1.2)
            px, py = hx + L * math.cos(fa), hy + L * math.sin(fa); c.move_to(px + 26 * math.cos(fa), py + 26 * math.sin(fa)); c.line_to(px + 7 * math.cos(fa + 1.57), py + 7 * math.sin(fa + 1.57)); c.line_to(px - 7 * math.cos(fa + 1.57), py - 7 * math.sin(fa + 1.57)); c.close_path(); c.fill()
    sc.add('glow', tips, blur=10, k=0.9); sc.add('np', motes((200, 220, 255), 40, 13)); return sc
SETS.update(ring=set_ring, baface=BA.set_face, basword=BA.set_sword, baplat=BA.set_platform)
# 前景遮挡（失焦的柱子/树干，视差比主体大）、斜角构图、甩镜
FGS = {}
ROLL = [(45, 47, 3.0, 6.5), (42, 42.75, -3, -5)]
WHIP = [8.5, 12.5, 23, 26, 34, 40.5]
def fgbars(fr, cx, z, bars):
    m = np.zeros((R.h, R.w), np.float32)
    for (x0, w) in bars: xa = (x0 - cx * 2.3) * z * R.k + R.w / 2; cv2.rectangle(m, (int(xa), -10), (int(xa + w * z * R.k * 1.6), R.h + 10), 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), 16 * R.k * 2)[..., None]; return fr * (1 - 0.96 * m) + np.float32((0.004, 0.005, 0.008)) * m
def post_cam(fr, b, t):
    for (b0, b1, a0, a1) in ROLL:
        if b0 <= b < b1: a = a0 + (a1 - a0) * (b - b0) / (b1 - b0); s = math.cos(math.radians(abs(a))) + R.w / R.h * math.sin(math.radians(abs(a))); fr = cv2.warpAffine(fr, cv2.getRotationMatrix2D((R.w / 2, R.h / 2), a, s), (R.w, R.h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    for bw in WHIP:
        d = abs(t - bt(bw))
        if d < 0.12: ks = int(260 * (1 - d / 0.12) * R.k * 2) | 1; fr = cv2.blur(fr, (ks, 1))
    return fr
W2 = lambda b: [(b, (960, 540, 1.0)), (b + 2, (900, 540, 1.06))]
SHOTS += [(23, 26, 'map3', None, 23), (26, 28, 'book', [(26, (1100, 520, 1.25)), (28, (1250, 620, 1.7))], 26), (28, 28.25, 'kids', [(28, (1000, 600, 1.15)), (28.25, (990, 600, 1.18))], 28), (28.25, 28.5, 'kids', kidcam(0, 500), 28), (28.5, 28.75, 'kids', kidcam(1, 440), 28), (28.75, 29, 'kids', kidcam(2, 360), 28), (29, 30, 'wood', [(29, (1000, 560, 1.0)), (30, (940, 580, 1.12))], 29), (30, 32, 'split', None, 30),
          (32, 34, 'w2', W2(32), 32), (34, 36, 'king', [(34, (860, 600, 1.05)), (36, (1000, 600, 1.2))], 34), (36, 37.5, 'night', [(36, (960, 560, 1.0)), (37.5, (1000, 580, 1.1))], 36), (37.5, 38.5, 'night', lambda tl: (max(560, ned_night(tl) + 60), 620, 1.7), 36),
          (38.5, 40.5, 'w3', W2(38.5), 38.5), (40.5, 42, 'throne', [(40.5, (900, 560, 1.0)), (42, (1000, 570, 1.12))], 40.5), (42, 42.75, 'throne', [(42, (1180, 590, 1.9)), (42.75, (1230, 570, 2.2))], 40.5), (42.75, 43.5, 'paper', [(42.75, (960, 540, 1.0)), (43.5, (960, 560, 1.1))], 42.75),
          (43.5, 45, 'ring', [(43.5, (960, 560, 2.3)), (45, (960, 560, 1.45))], 43.5), (45, 47, 'dagger', [(45, (900, 560, 1.0)), (47, (940, 620, 1.14))], 45), (47, 48.5, 'cell', [(47, (1000, 560, 1.0)), (48.5, (900, 600, 1.2))], 47), (48.5, 49, 'cellface', [(48.5, (900, 430, 1.9)), (49, (908, 438, 2.06))], 48.5), (49, 49.25, 'baby', [(49, (910, 480, 1.75))], 48.6), (49.25, 50, 'cellface', [(49.25, (905, 452, 2.0)), (50, (896, 520, 1.9))], 48.5),
          (50, 62.6, 'BA', None, 50), (63, 63.5, 'f0', [(63, (960, 540, 1.0))], 63), (63.5, 64, 'f1', [(63.5, (960, 540, 1.0))], 63), (64, 64.5, 'f2', [(64, (960, 540, 1.0))], 63), (64.5, 70, 'f3', [(64.5, (960, 540, 1.0)), (70, (960, 520, 1.07))], 63), (70, 74, 'map4', None, 70), (74, 76, 'end', None, 74)]
T(23, 24.45, 'sub', '十几年后，国王北上：来当我的首相。'); T(24.5, 26, 'sub', '他知道南方是什么地方。他还是去了。'); T(26, 27.45, 'sub', '他翻到一本族谱：劳勃家的孩子，代代黑发。'); T(27.5, 28, 'sub', '只有这一代，是金发。'); T(28, 29, G, '王后的三个孩子，没有一个是国王的。', 960, 200, 64)
T(29, 30, 'sub', '他没先告诉国王，先去找了王后。'); T(30.15, 32, G, '「带上孩子，走。」', 470, 900, 70); T(31, 32, G, '「权力的游戏，', 1150, 760, 64, 'l'); T(31.25, 32, G, '不赢，就死。」', 1190, 860, 64, 'l'); choice(32, 34, '第二次选择', '保住：王后的孩子', '代价：先手')
T(34, 36, 'sub', '几天后，国王打猎重伤，没能撑过去。'); T(36, 37.45, 'sub', '有人劝他：今晚动手，把王子抓在手里。'); T(37.5, 38.5, 'sub', '他不肯把孩子从床上拖走。'); choice(38.5, 40.5, '第三次选择', '保住：国王的孩子', '代价：兵权')
T(40.5, 42, 'tag', '— 君临 · 王座厅', 960, 76, 36, 'm'); T(40.5, 42, 'sub', '第二天，他带着国王的遗诏，走进王座厅。'); T(42, 43.5, 'sub', '王后把它撕了。'); T(43.5, 45, G, '守卫的长矛，调转方向。', 960, 140)
T(45.25, 47, G, '「我警告过你，', 1260, 640, 62, 'l'); T(45.75, 47, G, '别相信我。」', 1300, 740, 62, 'l'); T(47, 48.5, 'sub', '黑牢里，有人开了价：认罪，女儿活。'); T(49.27, 50, G, '这一次，', 1150, 700, 70, 'l'); T(49.42, 50, G, '他连荣誉也放下了。', 1150, 810, 70, 'l')
T(63.2, 65, 'sub', '他这辈子，撒过两个大谎。', y=900); T(65, 66, 'sub', '一个，救了妹妹的孩子。', y=900); T(66, 67, 'sub', '一个，想救自己的女儿。', y=900); T(67, 70, G, '他不是不懂游戏，', 960, 850, 66); T(68, 70, G, '只是每一次，都不肯拿孩子下注。', 960, 950, 66)
T(70, 72, 'sub', '他死后，北境举旗。'); T(72, 74, G, '五个国王，', 1330, 300, 70, 'l'); T(72.5, 74, G, '开始抢一把椅子。', 1330, 410, 70, 'l'); T(74.25, 76, 'brand', '码点小人', 1260, 440, 120); T(74.75, 76, 'keep', '长夜黑暗，我替你提灯。', 1260, 610, 50)
FLASH += [(bt(27.5), 0.6), (bt(28), 0.4), (bt(32), 0.5), (bt(38.5), 0.5), (bt(42.75), 0.4), (bt(45), 0.6), (bt(28.25), 0.3), (bt(28.5), 0.3), (bt(28.75), 0.3), (bt(49), 0.8), (bt(49.25), 0.5), (bt(63), 0.3)]; SHAKE += [(bt(45), 16, 0.4)]
SCN = {}; VG = {}
def scene(k):
    if k not in SCN: SCN[k] = SETS[k]()
    return SCN[k]
def frame(t):
    b = (t - T0) / B; ST['tau'] = t; fr = None
    for (b0, b1, k, cam, org) in SHOTS:
        if b0 <= b < b1:
            if k == 'BA': return BA.frame(t - bt(b0))
            tl = (org[1] - b) * B if isinstance(org, tuple) else (b - org) * B
            if k in MAPS: fr = MAPS[k](tl, (b1 - b0) * B, t); break
            cx, cy, z = cam(tl) if callable(cam) else kf(cam, b); z *= 1 + 0.004 * math.exp(-((t - T0) % (B / 2)) / 0.10)
            for (ts, amp, d) in SHAKE:
                if ts <= t < ts + d: q = (1 - (t - ts) / d) * amp; cx += q * math.sin(t * 91); cy += q * math.cos(t * 77)
            fr = scene(k).render(tl, (cx, cy, z), R).astype(np.float32)
            if b0 in FGS: fr = fgbars(fr, cx, z, FGS[b0])
            break
    if fr is None: fr = np.zeros((R.h, R.w, 3), np.float32)
    fr = post_cam(fr, b, t)
    for (tf, s) in FLASH:
        if tf <= t < tf + 0.22: fr = fr + s * (1 - (t - tf) / 0.22) ** 2
    if 'v' not in VG: yy, xx = np.mgrid[0:R.h, 0:R.w].astype(np.float32); d = np.sqrt(((xx - R.w / 2) / (R.w / 2)) ** 2 + ((yy - R.h / 2) / (R.h / 2)) ** 2) / 1.414; VG['v'] = (1 - 0.5 * np.clip(d, 0, 1) ** 2.0)[..., None]; rr = np.random.default_rng(1); VG['g'] = [(rr.random((R.h, R.w, 1)).astype(np.float32) - 0.5) * 0.022 for _ in range(6)]
    fr = fr * VG['v']; TT.draw(fr, t, R); fr = fr + VG['g'][int(t * 30) % 6]
    if t > DUR - 0.8: fr = fr * max(0, (DUR - t) / 0.8)
    return (np.clip(fr, 0, 1) * 255).astype(np.uint8)
# ---- 卡 BGM：这一集最初是按另一首曲子（一小节 1.6056 秒）做的，上面所有的「小节」都是那首曲子的小节。换成系列 BGM 后没有重写各场景，
#      只用下面这张表把每个旧小节摆到系列 BGM 的拍子上（切点落在拍或半拍，重点落在重拍和段落起点）。新的一集直接按系列 BGM 的拍子写，不需要这张表。
BEAT, PH = 0.59413, 0.50                                                                # 系列 BGM 的拍长；第 0 拍在曲子的 0.50 秒
def nt(n): return PH + n * BEAT
RETIME = [(1.0, 4), (1.6, 5.5), (2.0, 7), (2.25, 8), (2.5, 9), (2.75, 10), (3.0, 11), (3.5, 12.5), (4, 14),                # 剑落在第 4 拍（2.88 秒），片名在第 14 拍
          (6, 20), (8.5, 27), (9.0, 28), (11, 33), (12.5, 36.5), (14, 40.5), (16, 45.5), (17, 48), (20, 55.5), (21, 58),
          (23, 64), (26, 74), (28, 80),                                                 # 64–80 拍音乐没有鼓：国王北上、族谱；80 拍重鼓进：孩子的真相
          (28.25, 81), (28.5, 82), (28.75, 83), (29, 84), (30, 86.5), (32, 92), (34, 98),   # 96–98 两拍空白留给「第二次选择」的最后一行
          (36, 102.5), (37.5, 106), (38.5, 108.5), (40.5, 113), (42, 116.5), (42.75, 118), (43.5, 119.5), (45, 122), (47, 125.5),
          (48.5, 128.5), (49, 132.5), (49.25, 133.5), (50, 137),                       # 歌词「快闭上眼睛」的「睛」落在 129 拍、拖到 131 拍：黑牢的大特写在这里闭眼（见 set_cellface）
          (52, 142), (53.5, 145.5), (54.5, 148), (55.5, 151), (56.45, 153), (57, 154.5), (58, 157), (59, 159.5), (60, 162), (61.5, 166),   # 剑落在 166 拍：音乐的鼓和高频正好退掉
          (63, 170), (63.5, 171.5), (64, 173), (64.5, 174.5), (65, 176), (66, 178.5), (67, 181), (70, 188), (72, 193), (74, 198), (76, 206)]   # 193 拍鼓回来：五个国王；198 拍片尾
_WX = [0.0] + [nt(n) for _, n in RETIME]; _WB = [0.0] + [b for b, _ in RETIME]
DUR2 = _WX[-1]
def beat_of(b): return (float(np.interp(b, _WB, _WX)) - PH) / BEAT                       # 旧小节 → 系列 BGM 的拍号
def frame2(tau): return frame(bt(float(np.interp(tau, _WX, _WB))))                    # 成片第 tau 秒的画面
def _enc(out, extra=()): return subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{R.w}x{R.h}', '-r', '30', '-i', '-', *extra, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
if __name__ == '__main__':
    from PIL import Image
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'full'
    if cmd == 'strip':
        bs = [float(x) for x in sys.argv[2:]]; ims = [cv2.resize(frame(bt(b)), (480, 270), interpolation=cv2.INTER_AREA) for b in bs]
        while len(ims) % 6: ims.append(np.zeros_like(ims[0]))
        Image.fromarray(np.vstack([np.hstack(ims[i:i + 6]) for i in range(0, len(ims), 6)])).save('out/_strip.jpg', quality=85); print('out/_strip.jpg')
    elif cmd == 'seg':
        i, k = int(sys.argv[2]), int(sys.argv[3]); n = int(DUR2 * 30); f0, f1 = n * i // k, n * (i + 1) // k; p = _enc(f'out/_seg{R.h}_{i:02d}.mp4')
        for j in range(f0, f1):
            p.stdin.write(frame2(j / 30).tobytes())
            if (j - f0) % 100 == 0: print(i, j - f0, f1 - f0, flush=True)
        p.stdin.close(); p.wait(); print('done', i)
    elif cmd == 'clip':
        t0, t1 = float(sys.argv[2]), float(sys.argv[3]); out = f'out/clip_{R.h}p.mp4'; subprocess.run([sys.executable, 'mix.py'], check=True)
        p = _enc(out, ('-ss', str(t0), '-t', str(t1 - t0), '-i', 'out/mix.wav', '-c:a', 'aac', '-b:a', '192k', '-shortest'))
        for j in range(int(t0 * 30), int(t1 * 30)): p.stdin.write(frame2(j / 30).tobytes())
        p.stdin.close(); p.wait(); print('done', out)
    elif cmd == 'full':
        k = int(sys.argv[2]) if len(sys.argv) > 2 else max(1, (os.cpu_count() or 2) - 1); out = f'out/ned_{R.h}p.mp4'
        subprocess.run([sys.executable, 'mix.py'], check=True); texture_ready = tex()          # 地图纹理先生成好，免得各段同时写缓存
        ps = [subprocess.Popen([sys.executable, 'film.py', 'seg', str(i), str(k)]) for i in range(k)]
        if any(p.wait() for p in ps): sys.exit('有分段渲染失败')
        open('out/_cat.txt', 'w').write(''.join(f"file '_seg{R.h}_{i:02d}.mp4'\n" for i in range(k)))
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'out/_cat.txt', '-i', 'out/mix.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out], check=True); print('done', out)
