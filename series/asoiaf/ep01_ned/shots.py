"""shots — A 风格（暗调电影感）各镜头的 1920×1080 底板，不带字。每个函数返回 float32 RGB。"""
import math
from looks import *
import tallfig as F, scene as SC, bighead
C = F.CAST; INK = (0.012, 0.016, 0.028); COLD = (0.50, 0.68, 0.95); WARMR = (1.0, 0.62, 0.28); ICEC = (0.86, 0.92, 1.0)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
NEDL = dict(C['ned'], body=(0.30, 0.31, 0.35), legs=(0.17, 0.17, 0.20), cloak=(0.40, 0.44, 0.50), fur=(0.66, 0.65, 0.62), hair=(0.30, 0.21, 0.15), beard=(0.32, 0.25, 0.19))
NEDP = dict(C['ned_prison'], body=(0.40, 0.37, 0.34), legs=(0.22, 0.21, 0.21))
ROB = dict(body=(0.1, 0.1, 0.1), skirt='tunic', cloak=(0.1, 0.1, 0.1), hat='helm', hairstyle='bald', bulk=1.32, tbulk=1.25, beard=(0.1, 0.1, 0.1), beardlen=0.12)
KID = dict(body=(0.1, 0.1, 0.1), skirt='tunic', hairstyle='short', bulk=0.84)

def sky(top, bot, gy, p=2.2): t = np.clip(yy / gy, 0, 1)[..., None]; return np.float32(top) * (1 - t) + np.float32(bot) * t ** p
def blob(img, x, y, rx, ry, col, a): return img + a * np.exp(-(((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2))[..., None] * np.float32(col)
def floor(img, gy, c0=(0.085, 0.115, 0.160), c1=(0.012, 0.016, 0.028), line=(0.55, 0.72, 0.95), la=0.5):
    s, c = layer(); g = cairo.LinearGradient(0, gy, 0, H); g.add_color_stop_rgb(0, *c0); g.add_color_stop_rgb(1, *c1); c.set_source(g); c.rectangle(0, gy, W, H - gy); c.fill()
    c.set_source_rgba(*line, la); c.rectangle(0, gy, W, 3); c.fill(); return over(img, s)
def sil(img, draw, rim=COLD, light=(-1, -0.75), rim_a=0.75, rim_w=3):
    s, c = layer(); draw(c); return lit(img, s, light=light, rim=rim, rim_w=rim_w, rim_a=rim_a, half_w=9, half_a=0.10, shade_a=0)
def colr(img, draw, light=(-1, -0.9), rim=(0.80, 0.90, 1.0), shade_a=0.45, rim_a=0.70):
    s, c = layer(); draw(c); return lit(img, s, light=light, rim=rim, rim_w=3.5, rim_a=rim_a, half_w=12, half_a=0.13, shade_w=20, shade_a=shade_a)
def white(img, draw, k=0.28, blur=22):
    s, c = layer(); draw(c); img = glow_add(img, s, blur=blur, k=k); return over(img, s, opacity=0.96)
def glowl(img, draw, blur=12, k=0.6, solid=True, sblur=0):
    s, c = layer(); draw(c); img = glow_add(img, s, blur=blur, k=k); return over(img, s, blur=sblur) if solid else img
def plain(img, draw, blur=0, opacity=1.0): s, c = layer(); draw(c); return over(img, s, blur=blur, opacity=opacity)
def fin(img, v=0.62, g=0.03, seed=1): return grain(vignette(np.clip(img, 0, 1), v, 2.0), g, seed).astype(np.float32)
NOFIG = False
_D = layer(4, 4)[1]
def P(c, k, x, gy, Hh, pose, face=-1, mono=None, keep=(), **ex):
    S = dict(C[k]) if isinstance(k, str) else dict(k); Pp = ex.pop('P', None); S.update(ex); return F.fig(_D if NOFIG else c, x, gy, Hh, S, pose, face, P=Pp, mono=mono, keep=keep)
def poly(c, pts, col, a=1.0): c.set_source_rgba(*col, a); c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]; c.close_path(); c.fill()
def dirv(ang, face): r = math.radians(ang); return (math.sin(r) * face, math.cos(r))
def hammer(c, hand, ang, L, face, col):
    if NOFIG: return hand
    d = dirv(ang, face); n = (-d[1], d[0]); c.set_source_rgb(*col); c.set_line_width(L * 0.05); c.set_line_cap(cairo.LINE_CAP_ROUND)
    tip = (hand[0] + d[0] * L * 0.78, hand[1] + d[1] * L * 0.78); c.move_to(hand[0] - d[0] * L * 0.22, hand[1] - d[1] * L * 0.22); c.line_to(*tip); c.stroke()
    hw, hl = L * 0.10, L * 0.20; poly(c, [(tip[0] + n[0] * hl * a + d[0] * hw * b, tip[1] + n[1] * hl * a + d[1] * hw * b) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))], col)
    poly(c, [(tip[0] - n[0] * hl - d[0] * hw * 0.6, tip[1] - n[1] * hl - d[1] * hw * 0.6), (tip[0] - n[0] * hl * 1.7, tip[1] - n[1] * hl * 1.7), (tip[0] - n[0] * hl + d[0] * hw * 0.6, tip[1] - n[1] * hl + d[1] * hw * 0.6)], col); return tip
def antlers(c, o, face, col, k=1.0):
    if NOFIG: return
    hx, hy = o['head']; hh = o['HH'] * k; c.set_source_rgb(*col); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for s in (-1, 1):
        bx, by = hx + s * 0.16 * hh - face * 0.05 * hh, hy - 0.52 * hh; c.set_line_width(0.10 * hh)
        c.move_to(bx, by); c.curve_to(bx + s * 0.30 * hh, by - 0.35 * hh, bx + s * 0.75 * hh, by - 0.55 * hh, bx + s * 0.70 * hh, by - 1.15 * hh); c.stroke(); c.set_line_width(0.075 * hh)
        for (u, v, du, dv) in ((0.30, -0.36, 0.34, -0.26), (0.58, -0.60, 0.36, -0.14), (0.70, -0.86, -0.26, -0.24)): c.move_to(bx + s * u * hh, by + v * hh); c.line_to(bx + s * (u + du) * hh, by + (v + dv) * hh); c.stroke()
def goldhair(c, o, face, long=0):
    if NOFIG: return
    hx, hy = o['head']; hh = o['HH']; c.set_source_rgb(0.98, 0.80, 0.34); a0, a1 = (math.radians(-165), math.radians(55)) if face < 0 else (math.radians(125), math.radians(345))
    c.move_to(hx, hy); c.arc(hx, hy - 0.02 * hh, 0.56 * hh, a0, a1); c.close_path(); c.fill()
    if long: c.rectangle(hx + (0.10 if face < 0 else -0.52) * hh, hy, 0.42 * hh, long * hh); c.fill()
def crown(c, o, face, col=(0.95, 0.72, 0.25)):
    if NOFIG: return
    hx, hy = o['head']; hh = o['HH']; f = -face; c.set_source_rgb(*col)
    c.move_to(hx - f * 0.36 * hh, hy - 0.30 * hh); c.line_to(hx + f * 0.44 * hh, hy - 0.30 * hh); c.line_to(hx + f * 0.44 * hh, hy - 0.58 * hh)
    for i in range(1, 9): c.line_to(hx + f * (0.44 - (i * 0.1 - 0.05)) * hh, hy - 0.42 * hh); c.line_to(hx + f * (0.44 - i * 0.1) * hh, hy - 0.58 * hh)
    c.close_path(); c.fill()
def torch(img, TX, TY, k=1.0, r=None):
    def d(c):
        c.set_source_rgb(0.05, 0.04, 0.04); c.set_line_width(20 * k); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(TX - 34 * k, TY + 210 * k); c.line_to(TX, TY + 40 * k); c.stroke()
    img = plain(img, d)
    def fl(c):
        for cl, q in (((1.0, 0.42, 0.10), 1.0), ((1.0, 0.72, 0.25), 0.66), ((1.0, 0.95, 0.70), 0.36)):
            q *= k; c.set_source_rgb(*cl); c.move_to(TX - 30 * q, TY + 14 * k); c.curve_to(TX - 46 * q, TY - 40 * q, TX - 10 * q, TY - 70 * q, TX - 14 * q, TY - 128 * q); c.curve_to(TX + 20 * q, TY - 90 * q, TX + 14 * q, TY - 70 * q, TX + 30 * q, TY - 96 * q)
            c.curve_to(TX + 46 * q, TY - 50 * q, TX + 40 * q, TY - 10 * q, TX + 30 * q, TY + 14 * k); c.close_path(); c.fill()
    s, c = layer(); fl(c); img = glow_add(img, s, blur=40, k=0.9); img = glow_add(img, s, blur=9, k=0.5); return over(img, s, blur=1.0)
def firelight(TX, TY, base=(0.016, 0.018, 0.028), a=0.40, b=0.10, col=(1.0, 0.50, 0.18)):
    d = np.sqrt((xx - TX) ** 2 + ((yy - TY) * 1.15) ** 2); return np.float32(base)[None, None] + np.float32(col) * (a * np.exp(-d / 330) + b * np.exp(-d / 900))[..., None]
def bricks(img, r, a=0.55):
    def d(c):
        c.set_source_rgba(0, 0, 0, a); c.set_line_width(5)
        for j in range(12):
            y = j * 98 + 20; c.move_to(0, y); c.line_to(W, y); c.stroke()
            for i in range(12): x = i * 190 + (95 if j % 2 else 0) + r.uniform(-8, 8); c.move_to(x, y); c.line_to(x, y + 98); c.stroke()
    img = plain(img, d, blur=1.2); return img * (0.86 + 0.14 * cv2.GaussianBlur(r.random((H, W)).astype(np.float32), (0, 0), 5)[..., None] * 2)

# ---------- 1 侧脸（火光） / 黑牢
def face(cell=False):
    r = np.random.default_rng(8); TX, TY = 1560, 400; img = bricks(firelight(TX, TY), r); img = torch(img, TX, TY)
    s, c = layer()
    for i in range(40): c.set_source_rgba(1.0, 0.6, 0.2, r.uniform(0.3, 0.9)); c.arc(TX + r.normal(0, 60), TY - r.uniform(100, 420), r.uniform(1, 2.6), 0, math.tau); c.fill()
    img = glow_add(img, s, blur=1.5, k=1.0)
    if cell:                                                                             # 黑牢：铁栏的影子
        def bars(c):
            c.set_source_rgba(0, 0, 0, 0.55)
            for i in range(7): c.move_to(1020 + i * 120, 0); c.line_to(700 + i * 150, H); c.line_to(740 + i * 150, H); c.line_to(1050 + i * 120, 0); c.close_path(); c.fill()
        img = plain(img, bars, blur=14)
    s, c = layer(); bighead.ned(c, 640, 470, 640, 1)
    img = lit(img, s, light=(1, -0.15), rim=WARMR, rim_w=5, rim_a=0.75, half_w=22, half_a=0.16, shade_w=70, shade_a=0.50)
    m = np.clip((760 - xx) / 700, 0, 1)[..., None] ** 1.3; img = img * (1 - 0.55 * m); return fin(img, 0.55, 0.03, 3)

# ---------- 2 举剑
def sword_up():
    img = sky((0.010, 0.016, 0.032), (0.11, 0.16, 0.25), H, 1.5); img = blob(img, 960, 210, 560, 420, (0.6, 0.8, 1.0), 0.60)
    img = beam(img, (960, -500), 76, 104, 2000, a=0.30, blur=22); o = {}
    def d(c): o.update(P(c, 'ilyn', 1040, 1760, 1150, 'strike', -1, mono=INK, P=dict(af=(150, 186), ab=(144, 182))))
    img = sil(img, d, rim_w=5, rim_a=0.9, light=(0, -1))
    img = glowl(img, lambda c: F.sword(c, o['hand'], 177, 470, -1, col=ICEC, w=34), blur=26, k=0.8)
    s, c = layer(); r = np.random.default_rng(3); SC.birds(c, r, 22, 200, 80, 1500, 420, (0.75, 0.85, 1.0), 0.6); img = over(img, s, blur=0.8)
    return fin(img, 0.70)

# ---------- 3 三叉戟河
def trident(v=0):
    GY = 770; r = np.random.default_rng(6); img = sky((0.015, 0.024, 0.048), (0.20, 0.27, 0.36), GY, 2.0); img = blob(img, 980, 640, 620, 300, (0.60, 0.75, 0.95), 0.30)
    def far(c):                                                                          # 两岸的矛林和旗
        for side, x0, x1 in ((0, 0, 700), (1, 1220, W)):
            for i in range(90):
                x = r.uniform(x0, x1); h = r.uniform(60, 130); c.set_source_rgba(0.05, 0.07, 0.11, 0.95); c.set_line_width(3); c.move_to(x, GY + 4); c.line_to(x + r.uniform(-6, 6), GY - h); c.stroke(); c.arc(x, GY - 10, 9, 0, math.tau); c.fill()
            for i in range(5): x = r.uniform(x0 + 40, x1 - 40); poly(c, [(x, GY - 190), (x + 70, GY - 176), (x + 60, GY - 140), (x, GY - 130)], (0.06, 0.08, 0.12)); c.set_line_width(4); c.move_to(x, GY); c.line_to(x, GY - 195); c.stroke()
    img = plain(img, far, blur=1.6, opacity=0.9)
    hz = np.clip((yy - 520) / (GY - 520), 0, 1)[..., None] ** 1.6 * (yy < GY)[..., None]; img = img * (1 - 0.35 * hz) + np.float32((0.22, 0.30, 0.42)) * 0.35 * hz
    img = floor(img, GY, (0.10, 0.15, 0.22), (0.010, 0.016, 0.030), la=0.35)
    def water(c):
        for i in range(130):
            y = GY + 6 + r.uniform(0, 1) ** 1.6 * 300; x = r.uniform(0, W); L = r.uniform(40, 260) * (0.4 + (y - GY) / 300); c.set_source_rgba(0.55, 0.72, 0.95, r.uniform(0.05, 0.22)); c.rectangle(x, y, L, 2 + (y - GY) / 90); c.fill()
    img = plain(img, water, blur=0.8); img = blob(img, 980, GY + 60, 380, 60, (0.6, 0.78, 1.0), 0.22 * 1.0)
    ro, rh = {}, {}
    def d(c):
        if v == 0:
            ro.update(P(c, ROB, 780, GY + 150, 540, 'strike', 1, mono=INK, P=dict(af=(140, 168), ab=(132, 160), lean=-8))); hammer(c, ro['hand'], 188, 290, 1, INK)
            rh.update(P(c, dict(C['goldcloak'], cloak=(0, 0, 0)), 1200, GY + 150, 510, 'strike', -1, skirt=None, mono=INK, held=('sword', 150, 50), P=dict(af=(120, 150), ab=(110, 140))))
        else:
            ro.update(P(c, ROB, 820, GY + 150, 540, 'reach', 1, mono=INK, P=dict(af=(66, 80), ab=(58, 74), lean=24, lf=(34, 10), lb=(-26, -40)))); hammer(c, ro['hand'], 96, 290, 1, INK)
            rh.update(P(c, dict(C['goldcloak'], cloak=(0, 0, 0)), 1340, GY + 150, 510, 'stand', -1, skirt=None, mono=INK, P=dict(lean=-38, head=-20, af=(150, 170), ab=(-60, -90), lf=(40, 10), lb=(10, -20))))
        antlers(c, ro, 1, INK)
    img = sil(img, d, rim_a=0.85, light=(0.3, -1))
    def rub(c):                                                                          # 红宝石
        cx, cy = rh['sh'][0] - 20, rh['sh'][1] + 50
        for i in range(7 if v == 0 else 46):
            if v == 0: x, y, rr = cx + r.uniform(-26, 26), cy + r.uniform(-30, 40), r.uniform(4, 6)
            else: a = r.uniform(-2.6, 0.6); dd = r.uniform(30, 520); x, y, rr = cx + math.cos(a) * dd + 40, cy + math.sin(a) * dd * 0.8, r.uniform(4, 12)
            c.set_source_rgb(1.0, 0.16, 0.14); c.move_to(x, y - rr); c.line_to(x + rr * 0.8, y); c.line_to(x, y + rr); c.line_to(x - rr * 0.8, y); c.close_path(); c.fill()
    img = glowl(img, rub, blur=10, k=1.0 if v else 0.5) if not NOFIG else img
    if v: img = blob(img, 1240, 600, 170, 170, (1.0, 0.85, 0.75), 0.55)                 # 击中的闪光
    return fin(img, 0.60, 0.03, 4)

# ---------- 4 极乐塔（外）
def tower():
    GY = 830; r = np.random.default_rng(9); img = sky((0.07, 0.04, 0.10), (0.92, 0.42, 0.16), GY, 1.7)
    img = blob(img, 1330, 650, 300, 220, (1.0, 0.75, 0.45), 0.55)
    def sun(c): c.set_source_rgb(1.0, 0.90, 0.72); c.arc(1330, 660, 96, 0, math.tau); c.fill()
    img = glowl(img, sun, blur=40, k=0.7, sblur=1.5)
    def ridge(y0, amp, col, seed, step=90):
        rr = np.random.default_rng(seed); pts = [(0, H)]; x = -40
        while x < W + 80: pts.append((x, y0 - rr.uniform(0, amp))); x += rr.uniform(step * 0.5, step * 1.4)
        pts.append((W, H)); return lambda c: poly(c, pts, col)
    img = plain(img, ridge(700, 190, (0.50, 0.17, 0.12), 1, 120), blur=2.0); img = plain(img, ridge(770, 150, (0.30, 0.09, 0.09), 2, 100), blur=1.2)
    def near(c):
        poly(c, [(0, H), (0, 860), (300, 850), (700, 800), (1000, 740), (1180, 700), (1330, 690), (1480, 720), (1700, 800), (W, 840), (W, H)], (0.045, 0.020, 0.030))
        poly(c, [(1215, 705), (1228, 330), (1312, 330), (1325, 705)], (0.045, 0.020, 0.030))                               # 塔
        for i in range(4): c.rectangle(1222 + i * 26, 304, 16, 30); c.fill()
        c.rectangle(1216, 326, 108, 12); c.fill()
        for (x, y, a) in ((860, 772, -0.25), (930, 752, 0.18), (1010, 738, -0.08)):                                      # 插在地上的剑
            c.save(); c.translate(x, y); c.rotate(a); c.rectangle(-3, -70, 6, 74); c.fill(); c.rectangle(-16, -52, 32, 5); c.fill(); c.restore()
    img = plain(img, near)
    img = glowl(img, lambda c: (c.set_source_rgb(1.0, 0.75, 0.35), c.rectangle(1258, 400, 16, 34), c.fill()), blur=10, k=0.9)
    img = colr(img, lambda c: P(c, NEDL, 520, 842, 300, 'walk', 1, held=('sword', 20, 34)), light=(1, -0.5), rim=(1.0, 0.70, 0.40), rim_a=0.85, shade_a=0.55)
    return fin(img, 0.55, 0.03, 5)

# ---------- 5 极乐塔（内）
def deathbed(v=0):
    r = np.random.default_rng(11); img = np.zeros((H, W, 3), np.float32) + np.float32((0.030, 0.018, 0.022)); img = blob(img, 1250, 560, 700, 420, (0.55, 0.22, 0.10), 0.22)
    img = bricks(img, r, 0.35)
    def win(c): c.set_source_rgb(1.0, 0.70, 0.36); c.move_to(1560, 300); c.line_to(1560, 150); c.curve_to(1560, 90, 1620, 60, 1650, 60); c.curve_to(1680, 60, 1740, 90, 1740, 150); c.line_to(1740, 300); c.close_path(); c.fill()
    img = glowl(img, win, blur=30, k=0.8); img = beam(img, (1650, 120), 128, 150, 1500, col=(1.0, 0.62, 0.30), a=0.30, blur=16)
    GY = 860; img = floor(img, GY, (0.10, 0.055, 0.045), (0.015, 0.010, 0.012), line=(0.9, 0.55, 0.3), la=0.25)
    def bed(c):
        c.set_source_rgb(0.035, 0.020, 0.020); c.rectangle(820, GY - 150, 760, 150); c.fill(); c.rectangle(1560, GY - 330, 40, 330); c.fill(); c.rectangle(800, GY - 190, 30, 190); c.fill()
    img = sil(img, bed, rim=(1.0, 0.6, 0.3), light=(1, -1), rim_a=0.5)
    def ly(c):                                                                           # 莱安娜：白色剪影
        c.set_source_rgb(0.93, 0.92, 0.95); c.move_to(840, GY - 150); c.curve_to(960, GY - 215, 1180, GY - 240, 1330, GY - 232); c.curve_to(1400, GY - 236, 1440, GY - 215, 1560, GY - 190); c.line_to(1560, GY - 150); c.close_path(); c.fill()
        c.arc(1470, GY - 262, 44, 0, math.tau); c.fill(); c.move_to(1440, GY - 290); c.curve_to(1500, GY - 330, 1570, GY - 280, 1560, GY - 200); c.line_to(1500, GY - 222); c.close_path(); c.fill()
        c.set_line_width(26); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(1300, GY - 222); c.line_to(1120, GY - 196); c.stroke()
    img = white(img, ly, k=0.34)
    img = plain(img, lambda c: (c.set_source_rgba(0.55, 0.02, 0.04, 0.85), c.save(), c.translate(1150, GY - 150), c.scale(190, 34), c.arc(0, 0, 1, math.pi, math.tau), c.fill(), c.restore()), blur=6)   # 血
    def roses(c):
        for i in range(70):
            x = r.uniform(700, 1700); y = GY + r.uniform(8, 150); k = 0.6 + (y - GY) / 150; c.set_source_rgba(0.35, 0.60, 1.0, r.uniform(0.5, 1.0)); c.save(); c.translate(x, y); c.rotate(r.uniform(0, 3)); c.scale(9 * k, 5 * k); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
    img = glowl(img, roses, blur=7, k=0.7)
    img = colr(img, lambda c: P(c, NEDL, 760, GY + 26, 640, 'kneel1', 1, P=dict(af=(52, 84), head=10)), light=(1, -0.6), rim=(1.0, 0.68, 0.38), rim_a=0.8, shade_a=0.5)
    if v:                                                                                # 襁褓
        def baby(c): c.set_source_rgb(1.0, 0.97, 0.90); c.save(); c.translate(1280, GY - 262); c.rotate(-0.15); c.scale(84, 42); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore(); c.set_source_rgb(0.96, 0.80, 0.66); c.arc(1340, GY - 280, 22, 0, math.tau); c.fill()
        img = glowl(img, baby, blur=34, k=1.0); img = blob(img, 1290, GY - 270, 240, 170, (1.0, 0.30, 0.20), 0.16)
    return fin(img, 0.62, 0.03, 6)

# ---------- 6 风雪北归
def snow_walk():
    GY = 800; r = np.random.default_rng(13); img = sky((0.03, 0.045, 0.075), (0.36, 0.43, 0.52), GY, 1.6); img = blob(img, 420, 620, 520, 260, (0.75, 0.85, 1.0), 0.22)
    def wf(c):                                                                           # 临冬城
        col = (0.13, 0.17, 0.23); poly(c, [(90, GY), (90, GY - 120), (760, GY - 120), (760, GY)], col)
        for (x, w, h) in ((120, 70, 230), (300, 96, 300), (470, 60, 210), (620, 84, 260)):
            c.rectangle(x, GY - h, w, h); c.fill()
            for i in range(int(w // 22)): c.rectangle(x + i * 22, GY - h - 16, 12, 16); c.fill()
    img = plain(img, wf, blur=2.2, opacity=0.85)
    hz = np.clip((yy - 450) / (GY - 450), 0, 1)[..., None] ** 1.5 * (yy < GY)[..., None]; img = img * (1 - 0.5 * hz) + np.float32((0.40, 0.47, 0.56)) * 0.5 * hz
    img = floor(img, GY, (0.46, 0.53, 0.62), (0.07, 0.09, 0.13), line=(0.9, 0.95, 1.0), la=0.35)
    def tracks(c):
        for i in range(16): x = 1180 + i * 46; c.set_source_rgba(0.10, 0.13, 0.20, 0.55); c.save(); c.translate(x, GY + 34 + (i % 2) * 14 + i * 2.2); c.scale(15 + i * 0.5, 5 + i * 0.2); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
    img = plain(img, tracks, blur=1.0); o = {}
    img = colr(img, lambda c: o.update(P(c, NEDL, 1080, GY + 46, 440, 'walk', -1, P=dict(af=(30, 100), ab=(22, 92), lean=8, head=12))), light=(-1, -0.7), rim=(0.85, 0.92, 1.0), rim_a=0.8, shade_a=0.4)
    def baby(c):
        hx, hy = o['hand']; sx, sy = o['sh']; c.set_source_rgb(0.60, 0.58, 0.56); c.save(); c.translate((hx + sx) / 2 - 10, (hy + sy) / 2 + 30); c.rotate(0.30); c.scale(25, 44); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
        c.set_source_rgb(0.80, 0.66, 0.56); c.arc((hx + sx) / 2 - 20, (hy + sy) / 2 - 8, 11, 0, math.tau); c.fill()
    img = colr(img, baby, light=(-1, -0.7), rim=(0.85, 0.92, 1.0), rim_a=0.6, shade_a=0.3) if not NOFIG else img
    def snow(c):
        for i in range(500): c.set_source_rgba(0.92, 0.96, 1.0, r.uniform(0.15, 0.8)); c.arc(r.uniform(0, W), r.uniform(0, H), r.uniform(1, 3.4), 0, math.tau); c.fill()
    img = glowl(img, snow, blur=2, k=0.5, sblur=0.6)
    return fin(img, 0.55, 0.03, 7)

# ---------- 7 三个金发的孩子
def kids():
    GY = 930; r = np.random.default_rng(15); img = bricks(firelight(300, 380, (0.020, 0.014, 0.020), 0.30, 0.10), r, 0.4); img = torch(img, 300, 380, 0.8)
    img = floor(img, GY, (0.11, 0.06, 0.045), (0.012, 0.010, 0.012), line=(1.0, 0.6, 0.3), la=0.25); os = []
    def d(c):
        for (x, h, pose) in ((1060, 500, 'stand'), (1310, 440, 'stand'), (1530, 360, 'stand')): os.append(P(c, KID, x, GY, h, pose, -1, mono=INK))
    img = sil(img, d, rim=WARMR, light=(-1, -0.4), rim_a=0.8)
    img = glowl(img, lambda c: [goldhair(c, o, -1, long=(1.5 if i == 1 else 0)) for i, o in enumerate(os)], blur=16, k=0.9)
    img = colr(img, lambda c: P(c, NEDL, 560, GY, 640, 'stand', 1, P=dict(head=8)), light=(-1, -0.4), rim=WARMR, rim_a=0.8, shade_a=0.5)
    return fin(img, 0.62, 0.03, 8)

# ---------- 8 神木林
def godswood(v=0):
    GY = 850; r = np.random.default_rng(17); img = sky((0.010, 0.022, 0.035), (0.09, 0.17, 0.20), GY, 1.8); img = blob(img, 960, 420, 560, 420, (0.55, 0.80, 0.85), 0.20)
    def back(c):
        for i in range(14): x = r.uniform(0, W); w = r.uniform(30, 80); poly(c, [(x - w, GY), (x - w * 0.5, 0), (x + w * 0.5, 0), (x + w, GY)], (0.02, 0.045, 0.055), 0.9)
    img = plain(img, back, blur=5); img = floor(img, GY, (0.06, 0.11, 0.12), (0.008, 0.014, 0.020), line=(0.5, 0.8, 0.85), la=0.3)
    def trunk(c):
        c.set_source_rgb(0.86, 0.87, 0.86); c.move_to(860, GY + 20); c.curve_to(905, GY - 240, 900, 380, 880, 180); c.line_to(1010, 150); c.curve_to(1000, 380, 1010, GY - 240, 1075, GY + 20); c.close_path(); c.fill()
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for (x0, y0, x1, y1, w) in ((900, 330, 640, 150, 34), (990, 300, 1290, 130, 34), (940, 240, 900, 20, 30), (760, 240, 560, 210, 18), (1160, 205, 1400, 220, 18)): c.set_line_width(w); c.move_to(x0, y0); c.line_to(x1, y1); c.stroke()
    img = plain(img, trunk)
    def facec(c):                                                                        # 树脸（流红泪）
        c.set_source_rgb(0.50, 0.04, 0.05)
        for x in (925, 990): c.save(); c.translate(x, 520); c.scale(17, 11); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore(); c.rectangle(x - 3, 524, 6, 60); c.fill()
        c.rectangle(930, 640, 56, 9); c.fill()
    img = plain(img, facec, blur=0.8)
    def leaves(c):
        for i in range(520):
            x = r.normal(960, 420); y = r.normal(150, 120)
            if y > 400: continue
            c.set_source_rgba(r.uniform(0.62, 0.92), r.uniform(0.04, 0.12), 0.07, r.uniform(0.6, 1.0)); c.save(); c.translate(x, y); c.rotate(r.uniform(0, 3)); c.scale(r.uniform(14, 30), r.uniform(7, 13)); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
        for i in range(34): c.set_source_rgba(0.85, 0.08, 0.07, r.uniform(0.5, 0.9)); c.save(); c.translate(r.uniform(300, 1650), r.uniform(380, GY + 120)); c.rotate(r.uniform(0, 3)); c.scale(11, 5); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
    img = glowl(img, leaves, blur=14, k=0.35); co = {}
    def cer(c): co.update(P(c, 'cersei', 1330 if v == 0 else 1520, GY + 40, 520, 'stand' if v == 0 else 'walk', -1 if v == 0 else 1, mono=INK))
    img = sil(img, cer, rim=(0.95, 0.35, 0.25), light=(-1 if v == 0 else 1, -0.6), rim_a=0.85)
    img = glowl(img, lambda c: goldhair(c, co, -1 if v == 0 else 1, long=1.9), blur=14, k=0.7)
    img = colr(img, lambda c: P(c, NEDL, 560, GY + 40, 560, 'stand', 1, P=dict(af=(30, 70)) if v == 0 else dict(head=16, lean=5)), light=(1, -0.7), rim=(0.75, 0.95, 0.95), rim_a=0.7, shade_a=0.45)
    return fin(img, 0.62, 0.03, 9)

# ---------- 9 劳勃临终
def kingbed():
    GY = 880; r = np.random.default_rng(19); img = bricks(firelight(1640, 420, (0.020, 0.014, 0.018), 0.34, 0.12), r, 0.35)
    img = floor(img, GY, (0.11, 0.06, 0.045), (0.012, 0.010, 0.012), line=(1.0, 0.6, 0.3), la=0.25)
    def bed(c):
        c.set_source_rgb(*INK); c.rectangle(700, GY - 170, 800, 170); c.fill(); c.rectangle(1480, GY - 420, 44, 420); c.fill(); c.rectangle(680, GY - 230, 34, 230); c.fill()
        c.move_to(730, GY - 170); c.curve_to(820, GY - 230, 900, GY - 250, 1000, GY - 260); c.curve_to(1080, GY - 400, 1260, GY - 400, 1320, GY - 270); c.line_to(1480, GY - 250); c.line_to(1480, GY - 170); c.close_path(); c.fill()   # 被子下的大肚子
        c.arc(1400, GY - 290, 50, 0, math.tau); c.fill(); poly(c, [(1360, GY - 270), (1330, GY - 215), (1410, GY - 240)], INK)                                                                                                  # 头和胡子
        c.rectangle(1600, GY - 190, 150, 190); c.fill()                                                                                                                                                                           # 床头柜
    img = sil(img, bed, rim=WARMR, light=(1, -1), rim_a=0.6)
    def cr(c):                                                                           # 鹿角王冠
        c.set_source_rgb(0.95, 0.72, 0.25); c.rectangle(1630, GY - 222, 90, 30); c.fill(); c.set_line_width(7); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(4):
            x = 1640 + i * 23; c.move_to(x, GY - 222); c.line_to(x + (i - 1.5) * 9, GY - 290); c.stroke(); c.move_to(x + (i - 1.5) * 4, GY - 255); c.line_to(x + (i - 1.5) * 4 + 16, GY - 275); c.stroke()
    img = glowl(img, cr, blur=14, k=0.7)
    def candle(c): c.set_source_rgb(0.9, 0.85, 0.75); c.rectangle(1772, GY - 110, 16, 110); c.fill(); c.set_source_rgb(1.0, 0.85, 0.45); c.save(); c.translate(1780, GY - 132); c.scale(9, 22); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
    img = glowl(img, candle, blur=30, k=1.0); o = {}
    img = colr(img, lambda c: o.update(P(c, NEDL, 440, GY + 30, 620, 'stand', 1, P=dict(head=14, af=(30, 86)))), light=(1, -0.5), rim=WARMR, rim_a=0.8, shade_a=0.5)
    img = glowl(img, lambda c: (c.set_source_rgb(0.96, 0.92, 0.82), c.save(), c.translate(o['hand'][0] + 30, o['hand'][1]), c.rotate(-0.2), c.rectangle(-36, -52, 72, 96), c.fill(), c.restore()), blur=12, k=0.35) if not NOFIG else img   # 遗诏
    return fin(img, 0.62, 0.03, 10)

# ---------- 10 那一夜
def night():
    GY = 880; r = np.random.default_rng(21); img = bricks(np.zeros((H, W, 3), np.float32) + np.float32((0.016, 0.020, 0.034)), r, 0.4); img = blob(img, 300, 500, 500, 500, (0.45, 0.60, 0.90), 0.14)
    img = beam(img, (-200, -100), 20, 38, 1900, a=0.16, blur=18)
    def door(c): c.set_source_rgb(1.0, 0.66, 0.30); c.move_to(1330, GY); c.line_to(1330, 330); c.curve_to(1330, 230, 1440, 170, 1520, 170); c.curve_to(1600, 170, 1710, 230, 1710, 330); c.line_to(1710, GY); c.close_path(); c.fill()
    img = glowl(img, door, blur=50, k=0.55, solid=False); img = plain(img, door, opacity=0.50)
    img = floor(img, GY, (0.07, 0.08, 0.11), (0.010, 0.012, 0.020), line=(0.6, 0.7, 0.9), la=0.25); img = blob(img, 1520, GY + 60, 330, 70, (1.0, 0.6, 0.3), 0.25)
    def bedf(c): c.set_source_rgb(0.05, 0.03, 0.03); c.rectangle(1390, GY - 120, 300, 120); c.fill(); c.rectangle(1672, GY - 250, 24, 250); c.fill()
    img = plain(img, bedf)
    def child(c):
        c.set_source_rgb(0.95, 0.94, 0.97); c.move_to(1400, GY - 120); c.curve_to(1470, GY - 175, 1560, GY - 170, 1672, GY - 132); c.line_to(1672, GY - 120); c.close_path(); c.fill(); c.arc(1630, GY - 162, 27, 0, math.tau); c.fill()
    img = white(img, child, k=0.5)
    img = sil(img, lambda c: P(c, dict(C['joffrey'], hat=None), 1010, GY + 30, 560, 'point', 1, mono=INK), rim=WARMR, light=(1, -0.5), rim_a=0.8)
    img = colr(img, lambda c: P(c, NEDL, 500, GY + 30, 600, 'stand', -1, P=dict(head=20, lean=6)), light=(-1, -0.7), rim=(0.70, 0.82, 1.0), rim_a=0.75, shade_a=0.45)
    return fin(img, 0.62, 0.03, 11)

# ---------- 11 王座厅
def throne(v=0):
    GY = 850; r = np.random.default_rng(23); img = sky((0.012, 0.018, 0.034), (0.10, 0.14, 0.20), GY, 2.0); img = blob(img, 800, 560, 620, 360, (0.55, 0.72, 1.0), 0.16)
    def cols(c):
        for x in (120, 520, 920, 1320): c.set_source_rgba(0.03, 0.045, 0.07, 0.95); c.rectangle(x, 0, 96, GY); c.fill(); c.rectangle(x - 22, GY - 46, 140, 46); c.fill()
    img = plain(img, cols, blur=2.5)
    for ap in ((330, -260), (730, -260), (1130, -260)): img = beam(img, ap, 62, 74, 1500, a=0.20, blur=14)
    img = floor(img, GY, (0.085, 0.115, 0.160), (0.012, 0.016, 0.028)); img = blob(img, 830, GY + 40, 400, 46, (0.6, 0.78, 1.0), 0.20)
    def th(c):                                                                           # 铁王座：一堆剑
        c.set_source_rgb(*INK); poly(c, [(1400, GY), (1440, GY - 70), (1500, GY - 70), (1520, GY - 140), (1920, GY - 140), (1920, GY)], INK); poly(c, [(1660, GY - 140), (1640, GY - 520), (1900, GY - 560), (1920, GY - 140)], INK)
        rr = np.random.default_rng(5)
        for i in range(46):
            x = rr.uniform(1620, 1920); y = GY - rr.uniform(300, 560); a = rr.normal(-0.15, 0.5); L = rr.uniform(120, 300); c.save(); c.translate(x, y); c.rotate(a); poly(c, [(-7, 0), (7, 0), (4, -L * 0.9), (0, -L), (-4, -L * 0.9)], INK); c.rectangle(-20, -18, 40, 6); c.fill(); c.restore()
    img = sil(img, th, rim_a=0.55, light=(-1, -0.6)); jo, ce = {}, {}
    def court(c):
        jo.update(P(c, 'joffrey', 1690, GY - 140, 380, 'stand', -1, mono=INK, P=dict(lf=(86, 2), lb=(82, -2), lean=-4, af=(60, 88))))
        ce.update(P(c, 'cersei', 1300, GY + 20, 520, 'hold', -1, mono=INK, P=dict(af=(60, 96), ab=(50, 88)) if v == 0 else dict(af=(96, 120), ab=(20, 50))))
        for i, x in enumerate((1060, 1180)): P(c, 'lannguard', x + 380 * 0 - 0, GY + 20, 540, 'guard' if v < 3 else 'hold', -1, mono=INK, held=('spear', 180, 128) if v < 3 else ('spear', 96, 128)) if False else None
    img = sil(img, court, rim_a=0.8, light=(-1, -0.75))
    img = glowl(img, lambda c: (crown(c, jo, -1), goldhair(c, ce, -1, long=1.9)), blur=10, k=0.6)
    def paper(c):
        hx, hy = ce['hand']; c.set_source_rgb(0.96, 0.94, 0.88)
        if v == 0: c.save(); c.translate(hx - 30, hy - 10); c.rotate(0.15); c.rectangle(-40, -56, 80, 104); c.fill(); c.restore()
        else:
            rr = np.random.default_rng(31)
            for i in range(26): c.save(); c.translate(hx - 40 + rr.normal(0, 130), hy + rr.uniform(-160, 330)); c.rotate(rr.uniform(0, 3)); c.rectangle(-rr.uniform(8, 20), -rr.uniform(6, 16), rr.uniform(16, 40), rr.uniform(12, 30)); c.fill(); c.restore()
    img = glowl(img, paper, blur=12, k=0.4) if not NOFIG else img
    def guards(c):                                                                       # 奈德身后的金袍子
        for i, x in enumerate((130, 290, 450)):
            turned = (v == 2 and i == 2) or v >= 3
            P(c, 'goldcloak', x, GY + 30, 560, 'hold' if turned else 'guard', 1, mono=INK, held=('spear', 92, 130) if turned else ('spear', 180, 130), P=dict(lean=10, lf=(24, 6), lb=(-16, -30)) if turned else None)
    img = sil(img, guards, rim_a=0.8, light=(1, -0.75), rim=COLD if v < 2 else (0.95, 0.75, 0.35))
    img = colr(img, lambda c: P(c, NEDL, 830, GY + 30, 580, 'stand', 1, P=dict(af=(50, 90)) if v < 2 else dict(head=-6, lean=-3, af=(-10, 30))), light=(-1, -0.9), rim=(0.80, 0.90, 1.0))
    if v >= 3: img = img * np.float32((1.0, 0.82, 0.82)) + blob(np.zeros_like(img), 300, 600, 500, 400, (0.9, 0.2, 0.1), 0.10)
    return fin(img, 0.62, 0.03, 12)

# ---------- 12 匕首
def dagger():
    r = np.random.default_rng(25); TX, TY = 1620, 330; img = bricks(firelight(TX, TY, a=0.34), r); img = torch(img, TX, TY)
    img = sil(img, lambda c: P(c, 'little', 330, 4060, 3900, 'stand', 1, mono=(0.02, 0.018, 0.022)), rim=WARMR, light=(1, -0.2), rim_a=0.75, rim_w=5)
    s, c = layer(); bighead.ned(c, 900, 400, 640, 1)
    img = lit(img, s, light=(1, -0.15), rim=WARMR, rim_w=5, rim_a=0.75, half_w=22, half_a=0.16, shade_w=70, shade_a=0.50)
    def arm(c): c.set_source_rgb(0.02, 0.018, 0.022); c.set_line_width(120); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(380, 1150); c.line_to(700, 930); c.stroke(); c.arc(730, 915, 62, 0, math.tau); c.fill()
    img = sil(img, arm, rim=WARMR, light=(0.3, -1), rim_a=0.6, rim_w=4)
    img = glowl(img, lambda c: poly(c, [(760, 885), (1120, 838), (1170, 850), (770, 935)], (0.90, 0.94, 1.0)), blur=18, k=0.6)
    m = np.clip((560 - xx) / 600, 0, 1)[..., None] ** 1.3; img = img * (1 - 0.5 * m); return fin(img, 0.55, 0.03, 13)

# ---------- 13 贝勒大圣堂
def baelor(jo='stand', sansa='stand', ilyn='rest'):
    GY = 772; r = np.random.default_rng(4); t = np.clip(yy / GY, 0, 1)[..., None]
    img = np.float32((0.020, 0.032, 0.060)) * (1 - t) + np.float32((0.150, 0.215, 0.300)) * t ** 2.2; img = blob(img, 560, 620, 700, 300, (0.55, 0.75, 1.0), 0.10)
    s, c = layer(); SC.sept(c, 1290, GY, 1.0, (0.085, 0.125, 0.190)); img = over(img, s, blur=2.0, opacity=0.92)
    s, c = layer(); SC.skyline(c, GY, r, (0.05, 0.075, 0.115), gap=(520, 1000)); img = over(img, s, blur=1.5, opacity=0.9)
    haze = np.clip((yy - 430) / (GY - 430), 0, 1)[..., None] ** 1.8 * (yy < GY)[..., None]; img = img * (1 - 0.42 * haze) + np.float32((0.20, 0.29, 0.40)) * 0.42 * haze
    s, c = layer(); c.set_source_rgba(0.55, 0.75, 1.0, 0.55)
    for i in range(11): c.rectangle(1290 - 285 + i * 57 - 9, GY - 120, 18, 100); c.fill()
    img = glow_add(img, s, blur=10, k=0.5)
    s, c = layer(); g = cairo.LinearGradient(0, GY, 0, GY + 90); g.add_color_stop_rgb(0, 0.085, 0.115, 0.160); g.add_color_stop_rgb(1, 0.030, 0.042, 0.065); c.set_source(g); c.rectangle(0, GY, W, 90); c.fill()
    for i in range(4): q = 0.05 - i * 0.010; c.set_source_rgb(q * 0.7, q * 0.95, q * 1.35); c.rectangle(0, GY + 90 + i * 34, W, 34); c.fill(); c.set_source_rgba(0.45, 0.60, 0.80, 0.22 - i * 0.04); c.rectangle(0, GY + 90 + i * 34, W, 2.5); c.fill()
    c.set_source_rgba(0.55, 0.72, 0.95, 0.55); c.rectangle(0, GY, W, 3); c.fill(); img = over(img, s)
    img = blob(img, 800, GY + 26, 330, 34, (0.60, 0.78, 1.0), 0.30) if True else img
    img = beam(img, (-260, -420), 42.5, 52.5, 2100, a=0.30, blur=14); img = beam(img, (-260, -420), 45.5, 49.5, 2100, a=0.22, blur=6); il, jf = {}, {}
    def grp(c):
        P(c, 'goldcloak', 250, GY, 372, 'guard', 1, mono=INK, held=('spear', 180, 130)); P(c, 'goldcloak', 470, GY, 372, 'guard', 1, mono=INK, held=('spear', 180, 130))
        il.update(P(c, 'ilyn', 962, GY, 384, 'strike', -1, mono=INK, P=dict(af=(150, 186), ab=(144, 182))) if ilyn == 'up' else P(c, 'ilyn', 962, GY, 384, 'guard', -1, mono=INK, P=dict(af=(24, 96), ab=(18, 88))))
        P(c, 'lannguard', 1700, GY, 372, 'guard', -1, mono=INK, held=('spear', 180, 130)); P(c, 'little', 1800, GY, 350, 'stand', -1, mono=INK); P(c, 'cersei', 1400, GY, 356, 'stand', -1, mono=INK)
        jf.update(P(c, 'joffrey', 1262, GY, 330, jo, -1, mono=INK, hat=None)); P(c, 'lannguard', 1608, GY, 372, 'hold' if sansa == 'reach' else 'guard', -1, mono=INK)
    img = sil(img, grp)
    img = glowl(img, lambda c: F.sword(c, il['hand'], 176 if ilyn == 'up' else 180, 64 * 3.84, -1, col=ICEC), blur=16, k=0.55 if ilyn == 'up' else 0.35)
    img = glowl(img, lambda c: crown(c, jf, -1), blur=8, k=0.5)
    img = white(img, lambda c: P(c, 'sansa', 1520, GY, 332, sansa, -1, mono=(0.90, 0.93, 0.98)))
    img = plain(img, lambda c: (c.save(), c.translate(800, GY + 4), c.scale(120, 9), c.set_source_rgba(0, 0, 0, 0.5), c.arc(0, 0, 1, 0, math.tau), c.fill(), c.restore()), blur=4)
    img = colr(img, lambda c: P(c, NEDP, 800, GY, 384, 'kneel', -1), rim_a=0.70)
    s, c = layer()
    for i in range(240):
        u = r.uniform(0.25, 1.0); a = math.radians(r.uniform(43, 52)); x = -260 + math.cos(a) * 2100 * u; y = -420 + math.sin(a) * 2100 * u
        if y < GY - 10: c.set_source_rgba(0.8, 0.9, 1.0, r.uniform(0.15, 0.6)); c.arc(x, y, r.uniform(0.8, 2.4), 0, math.tau); c.fill()
    img = glow_add(img, s, blur=1.2, k=1.0)
    for y0, R0, cl, bl, n in ((962, 31, (0.022, 0.030, 0.048), 1.0, 40), (1050, 46, (0.006, 0.008, 0.014), 2.5, 26)):
        s, c = layer(); SC.crowd(c, y0, R0, n, r, cl); c.rectangle(0, y0 + R0 * 2.4, W, H); c.fill()
        img = lit(img, s, light=(-0.4, -1), rim=(0.40, 0.56, 0.80), rim_w=2.5, rim_a=0.35, half_a=0, shade_a=0) if bl < 2 else over(img, s, blur=bl)
    return fin(img, 0.62, 0.03)

# ---------- 提灯的码点小人（前景图层）：返回 (rgb 预乘, alpha, 加色光)
WIT = dict(body=(0.03, 0.03, 0.04), skirt='coat', cloak=(0.03, 0.03, 0.04), hat='hood', hoodc=(0.03, 0.03, 0.04), hairstyle='bald', bulk=1.0)
def witness(x=210, y=1330, Hh=640, face=1, lamp=True):
    s, c = layer(); o = P(c, WIT, x, y, Hh, 'guard', face, mono=(0.014, 0.014, 0.020), P=dict(af=(30, 70)))
    hx, hy = o['hand']; lx, ly = hx + face * 6, hy + 0.10 * Hh
    c.set_source_rgb(0.014, 0.014, 0.020); c.set_line_width(4); c.move_to(hx, hy); c.line_to(lx, ly - 0.035 * Hh); c.stroke(); c.rectangle(lx - 0.022 * Hh, ly - 0.035 * Hh, 0.044 * Hh, 0.075 * Hh); c.fill()
    z = np.zeros((H, W, 3), np.float32); rgb = lit(z, s, light=(face, -0.2), rim=(1.0, 0.66, 0.30), rim_w=4, rim_a=0.9 if lamp else 0.0, half_w=14, half_a=0.10 if lamp else 0, shade_a=0); al = rgba(s)[1]
    s2, c2 = layer(); c2.set_source_rgb(1.0, 0.80, 0.42); c2.rectangle(lx - 0.014 * Hh, ly - 0.026 * Hh, 0.028 * Hh, 0.055 * Hh); c2.fill()
    add = glow_add(z, s2, blur=60, k=1.3) + glow_add(z, s2, blur=14, k=0.9) + over(z, s2) if lamp else z
    return rgb.astype(np.float32), al.astype(np.float32), add.astype(np.float32), (lx, ly)
