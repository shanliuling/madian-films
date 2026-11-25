"""四渡赤水：现代题材示例（精致 Q 版 + 地图上的现代蛋蛋兵 + 战壕/沙包/枪炮的斜视角战场 + 正面大头特写）。
镜头时间按 BGM 时间写（SONG），再统一减去 OFF（BGM 从第 2 小节附近起播）。环境变量 LOGO=1：战役小标题右移，给左上角商单 logo 让位。
需要自备 bgm.wav，先跑 mix.py 生成 mix.wav。
  python film.py still 目录 t... | part i n out.mp4 0.5
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.join(HERE, '..', '..')
for p in (KIT, HERE): sys.path.insert(0, p)
import numpy as np, cairo
from PIL import Image
from mapwar.util import SW, SH, ease, eout, Txt, to_img, VR, grain, font
from mapwar.mapshot import MapShot
from mapwar import qhorse, qrig as RG
from mapwar.qchar import Q, PI, TAU
from mapwar.scenery import landscape, burn, grass, dust
from cast.sidu import HJ, MZ, ZE, ZD, JJ, ZY, CJ, QJ
import geo, battles
from geo import R_, K_

W, H = SW, SH; BAR = 2.3424; B0 = 0.275
T = lambda n: B0 + n * BAR
T_END = T(42) + 0.6
OFF = T(2) - 0.15                                   # BGM 从第 2 小节前起播：前奏只留一小节钩子
RED_T = (200, 34, 22); INK_T = (38, 34, 40); CREAM = (255, 238, 210)

# ================================================================ 地图数据
RED_PATH = [(0, 106.93, 27.70, 3), (T(5), 106.93, 27.70, 3), (T(6.9), 105.98, 28.25, 3), (T(7.7), 105.75, 28.05, 3), (T(8.5), 105.05, 27.85, 3), (T(9.5), 105.05, 27.85, 3),
            (T(10.1), 106.12, 28.12, 3), (T(10.5), 106.80, 28.13, 3), (T(12.0), 106.83, 27.95, 3), (T(12.4), 106.93, 27.70, 3), (T(17), 106.85, 27.65, 3), (T(20), 106.38, 27.86, 3),
            (T(21.3), 105.95, 27.98, 3), (T(24), 105.95, 27.98, 3), (T(26), 106.20, 28.02, 3), (T(27.2), 106.45, 27.55, 3), (T(28.5), 106.60, 27.18, 3), (T(29.2), 106.74, 27.05, 3),
            (T(30.4), 106.88, 26.78, 3), (T(33.6), 106.88, 26.78, 3), (T(34.1), 106.75, 26.40, 3), (T(34.7), 106.0, 25.75, 3), (T(35.3), 104.90, 25.25, 3), (T(35.7), 103.75, 25.55, 3),
            (T(36.1), 102.55, 26.18, 3), (T(38), 102.45, 26.22, 3), (T(39), 102.25, 26.68, 3), (T_END, 102.25, 26.68, 3)]
ARMIES = [
    dict(n='红军', o=R_, path=RED_PATH, tags=[(0, T(22), '3万'), (T(22), T(24), '主力 隐蔽待机'), (T(24), T_END, '3万')]),
    dict(n='一个团', o=R_, path=[(T(21.9), 105.95, 27.98, 0.15), (T(22.3), 105.90, 28.05, 0.15), (T(24), 105.50, 28.28, 0.15), (T(24.6), 105.45, 28.30, 0.15)], die=T(24.6), tags=[(T(21.9), T(24.6), '佯装主力')]),
    dict(n='川军', o=K_, face=-1, path=[(0, 105.95, 29.0, 12), (T(5), 105.97, 28.6, 12), (T(7), 105.92, 28.42, 12), (T(8.5), 105.30, 28.45, 12), (T(13), 105.55, 28.5, 12), (T(17), 106.2, 28.3, 12), (T(22), 106.2, 28.3, 12),
                                            (T(24), 105.55, 28.42, 12), (T(36), 105.6, 28.2, 12), (T(40), 105.0, 27.7, 12), (T_END, 105.0, 27.7, 12)]),
    dict(n='中央军', o=K_, face=-1, path=[(0, 107.75, 26.85, 10), (T(4), 107.3, 27.1, 10), (T(7), 106.95, 27.55, 10), (T(8.5), 106.1, 27.85, 10), (T(9.5), 105.65, 27.72, 10), (T(11), 105.75, 27.7, 10),
                                              (T(12.2), 106.62, 27.42, 10), (T(13), 106.9, 27.2, 8), (T(15), 107.05, 27.3, 9), (T(17), 106.95, 27.45, 9), (T(22), 106.95, 27.45, 9), (T(24), 105.95, 27.72, 9),
                                              (T(29), 106.0, 27.55, 9), (T(31), 106.3, 27.25, 9), (T(33), 107.3, 26.75, 9), (T(36), 106.6, 26.2, 9), (T(40), 104.6, 25.6, 9), (T_END, 104.6, 25.6, 9)], rout=[(T(12.2), T(13.2))]),
    dict(n='黔军', o=K_, face=-1, path=[(0, 106.95, 28.4, 4), (T(6), 106.93, 27.75, 4), (T(10.5), 106.83, 27.97, 4), (T(12.3), 107.25, 27.85, 1.2), (T_END, 107.3, 27.85, 1.2)], rout=[(T(10.8), T(12.5))]),
    dict(n='滇军', o=K_, path=[(0, 104.2, 26.55, 6), (T(7), 104.7, 27.2, 6), (T(8.5), 104.72, 27.55, 6), (T(13), 105.25, 27.3, 6), (T(22), 105.5, 27.45, 6), (T(24), 105.55, 27.72, 6), (T(30.5), 105.6, 27.3, 6),
                                   (T(32.2), 106.5, 26.62, 6), (T(36), 106.5, 26.62, 6), (T(40), 105.6, 26.1, 6), (T_END, 105.6, 26.1, 6)]),
    dict(n='湘军', o=K_, face=-1, path=[(0, 109.0, 27.6, 7), (T(4), 108.3, 27.6, 7), (T_END, 108.3, 27.6, 7)]),
]
A = lambda n0, n1, n2, o, w, pts: (T(n0), T(n1), T(n2), o, w, pts)
ARROWS = [A(1.05, 1.7, 2.0, K_, 11, [(105.95, 28.9), (106.3, 28.4), (106.8, 27.95)]), A(1.15, 1.8, 2.0, K_, 11, [(107.7, 26.85), (107.3, 27.2), (107.0, 27.55)]),
          A(1.25, 1.9, 2.0, K_, 11, [(104.3, 26.6), (105.3, 27.1), (106.4, 27.5)]), A(1.35, 1.95, 2.0, K_, 11, [(108.9, 27.6), (108.0, 27.65), (107.3, 27.7)]),
          A(7.0, 7.8, 9.4, R_, 15, [(106.0, 28.25), (105.75, 28.05), (105.4, 27.9), (105.05, 27.85)]),
          A(9.5, 10.3, 12.9, R_, 15, [(105.05, 27.85), (105.6, 27.98), (106.12, 28.12), (106.6, 28.18), (106.83, 27.95), (106.93, 27.72)]),
          A(20.0, 21.0, 23.9, R_, 15, [(106.9, 27.7), (106.38, 27.86), (105.95, 27.98)]),
          A(22.0, 23.2, 24.0, R_, 7, [(105.95, 27.98), (105.75, 28.15), (105.5, 28.28), (105.3, 28.5)]),
          A(22.4, 23.4, 24.0, K_, 10, [(106.9, 27.45), (106.4, 27.6), (105.98, 27.72)]), A(22.5, 23.5, 24.0, K_, 10, [(106.2, 28.3), (105.9, 28.4), (105.6, 28.42)]),
          A(26.0, 28.3, 31.0, R_, 15, [(106.2, 28.02), (106.4, 27.65), (106.52, 27.3), (106.74, 27.05)]), A(29.2, 30.3, 31.0, R_, 15, [(106.74, 27.05), (106.85, 26.9), (106.8, 26.7)]),
          A(30.6, 31.8, 33.5, K_, 12, [(105.6, 27.3), (106.0, 26.95), (106.5, 26.65)]),
          A(33.6, 35.4, 36.0, R_, 16, [(106.88, 26.78), (106.55, 26.15), (105.8, 25.6), (104.9, 25.25), (103.75, 25.55), (103.0, 25.6), (102.55, 26.18)]),
          A(38.0, 38.8, 44.6, R_, 16, [(106.55, 26.15), (104.9, 25.25), (103.75, 25.55), (102.55, 26.18), (102.25, 26.68)]),
          A(38.3, 39.1, 44.6, K_, 10, [(106.5, 26.6), (105.9, 26.2), (105.6, 26.1)]), A(38.4, 39.2, 44.6, K_, 10, [(106.6, 26.2), (105.5, 25.7), (104.6, 25.6)]),
          A(38.5, 39.3, 44.6, K_, 10, [(105.6, 28.2), (105.2, 27.9), (105.0, 27.7)])]
C = lambda n0, n1, lo0, la0, z0, lo1, la1, z1, tl: [(T(n0), lo0, la0, z0, tl), (T(n1), lo1, la1, z1, tl)]
CAMSEG = [C(0, 2, 106.3, 27.6, 0.86, 106.4, 27.65, 1.0, 0), C(4, 5, 106.3, 28.0, 1.5, 106.25, 28.05, 1.75, 1), C(7, 9.5, 105.9, 28.05, 1.9, 105.55, 27.95, 1.7, 0.7) + [(T(10.5), 106.3, 28.0, 1.9, 0.7)],
          C(12, 13, 106.85, 27.75, 2.3, 106.9, 27.7, 2.7, 0.8), C(14, 15.5, 106.6, 27.75, 1.6, 106.8, 27.7, 1.95, 0.3), C(20, 24, 106.3, 27.95, 2.0, 105.85, 28.05, 1.75, 0.7),
          C(25.5, 28, 106.2, 27.85, 1.9, 106.6, 27.15, 1.95, 0.6) + [(T(29), 106.78, 26.8, 2.2, 0.6)], C(30.5, 32.5, 106.2, 26.8, 1.55, 106.5, 26.6, 1.7, 0.3) + [(T(33.5), 106.3, 26.3, 1.45, 0.3), (T(36), 103.6, 25.9, 1.25, 0.3)],
          C(38, 44.8, 105.3, 26.9, 0.80, 105.1, 26.85, 0.86, 0)]
FLIPS = {'遵义': [(T(6.0), K_), (T(12.4), R_), (T(20.6), K_)], '娄山关': [(T(11.8), R_), (T(20.6), K_)], '桐梓': [(T(10.6), R_), (T(20.6), K_)]}
CIT = [(n, lo, la, R_ if n == '遵义' else o, lv) for (n, lo, la, o, lv) in geo.CITIES]
EGG = {'红军': dict(body=(0.46, 0.50, 0.52), hat='bajiao', hatcol=(0.40, 0.44, 0.47)), '一个团': dict(body=(0.46, 0.50, 0.52), hat='bajiao', hatcol=(0.40, 0.44, 0.47)),
       '中央军': dict(body=(0.50, 0.50, 0.40), hat='helmet', hatcol=(0.36, 0.42, 0.36)), '湘军': dict(body=(0.50, 0.50, 0.40), hat='helmet', hatcol=(0.36, 0.42, 0.36)),
       '川军': dict(body=(0.42, 0.44, 0.50), hat='junmao', hatcol=(0.33, 0.35, 0.42)), '滇军': dict(body=(0.36, 0.42, 0.40), hat='junmao', hatcol=(0.28, 0.34, 0.32)),
       '黔军': dict(body=(0.56, 0.49, 0.34), hat='strawhat', hatcol=(0.86, 0.74, 0.48))}
_MS = {}


def MS():
    if 'm' not in _MS:
        from mapwar.world import World
        Wd = World(dict(bbox=(101.0, 110.0, 24.3, 30.4), px_per_deg=230, sides=geo.SIDES, cities=CIT, flips=FLIPS, reach=(0.22, 0.4), ranges=geo.RANGES, relief=0.15,
                        main_rivers=('Chang Jiang', 'Yangtze', 'Jinsha'), major_rivers=('Wu',), extra_rivers=[dict(pts=geo.CHISHUI, width=7.5)]), os.path.join(KIT, 'data'))
        _MS['m'] = MapShot(Wd, dict(style=lambda t: 'ink', camseg=CAMSEG, armies=ARMIES, arrows=ARROWS, hud=dict(share=False), egg=EGG, fig_scale=0.5,
                                    keycity={'遵义', '贵阳', '重庆', '昆明', '土城', '茅台', '娄山关', '扎西', '皎平渡'}))
    return _MS['m']


# ================================================================ 公用
def sub(X, s, l, a=1.0, dark=False, y=968):
    X.T(s, W / 2, y, 72, fill=CREAM if dark else (25, 20, 18), halo=(20, 14, 10) if dark else (245, 232, 205), stroke=8, a=a * ease(l / 0.18))


CORNER = (470, 100)                                  # 左上角让给 logo（商单版），两版共用一次渲染


def slam(X, s, l, col=RED_T, size=250, keep=True, hold=1.15, corner=None):
    """大字横排砸到正中，hold 秒后缩到左上角。"""
    if l < 0: return
    if l < hold + 0.2:
        sz = size * (1 + 0.5 * (1 - eout(l / 0.16))); a = ease(l / 0.06) * (1 - ease((l - hold + 0.05) / 0.25))
        X.T(s, W / 2 + 8, 508, sz, fill=(20, 14, 12), stroke=0, a=a * 0.8); X.T(s, W / 2, 500, sz, fill=col, stroke=14, halo=(250, 238, 215), a=a)
    corner = corner or CORNER
    if keep: X.T(s, corner[0], corner[1], 96, fill=col, stroke=8, halo=(250, 238, 215), a=ease((l - hold) / 0.2))


def date(X, s, a=1.0, dark=False): X.T(s, 1640, 96, 60, fill=CREAM if dark else (40, 30, 24), halo=(20, 14, 10) if dark else (245, 232, 205), stroke=6, a=a)


def push(img, k, amt=0.05):
    s = 1 + amt * k; w, h = W / s, H / s; x0, y0 = (W - w) / 2, (H - h) / 2
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)


def flash(img, l, k=0.45, tau=0.07):
    if l > 0.4: return img
    return Image.fromarray((np.asarray(img).astype(np.float32) + 255 * k * math.exp(-max(0, l) / tau)).clip(0, 255).astype(np.uint8))


def layer(draw):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); draw(c)
    return np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32) / 255


def compose(draw, bg='day', X=None, lt=0.0, zoom=1.0, cx=W / 2, cy=H / 2, mul=None, glow=None, shake=0.0, fl=0.4):
    def d(c):
        if shake: c.translate(shake * math.sin(lt * 83), shake * math.sin(lt * 67 + 1))
        if zoom != 1.0: c.translate(cx, cy); c.scale(zoom, zoom); c.translate(-cx, -cy)
        draw(c)
    Bg = landscape(bg)
    if glow is not None:
        gx, gy, gr, gc, ga = glow; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); Bg = Bg + np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * gr * gr))[..., None] * np.float32(gc) * ga
    A_ = layer(d); fr = A_[..., [2, 1, 0]] + Bg * (1 - A_[..., 3:4])
    if mul is not None: fr = fr * np.float32(mul)
    fr = fr * (1 - 0.32 * VR) + np.float32([1, 0.95, 0.85]) * fl * math.exp(-lt / 0.07)
    img = to_img(fr + grain(0.02))
    return X.over(img) if X is not None else img


def battle(fr, X, lt): return X.over(to_img(fr + np.float32([1, 0.95, 0.85]) * 0.45 * math.exp(-lt / 0.07) + grain(0.02)))


def table(c, x, y, w=420, h=150, mapon=True):
    c.rectangle(x - w / 2, y - h, w, 26); c.set_source_rgb(0.5, 0.32, 0.17); c.fill_preserve(); c.set_source_rgb(0.1, 0.08, 0.08); c.set_line_width(5); c.stroke()
    for k in (-1, 1): c.rectangle(x + k * (w / 2 - 34) - 12, y - h + 26, 24, h - 26); c.set_source_rgb(0.4, 0.25, 0.13); c.fill_preserve(); c.set_source_rgb(0.1, 0.08, 0.08); c.stroke()
    if mapon:
        c.move_to(x - w * 0.36, y - h - 4); c.line_to(x + w * 0.36, y - h - 4); c.line_to(x + w * 0.42, y - h - 30); c.line_to(x - w * 0.3, y - h - 30); c.close_path(); c.set_source_rgb(0.93, 0.87, 0.72); c.fill_preserve(); c.set_source_rgb(0.1, 0.08, 0.08); c.set_line_width(4); c.stroke()
        c.move_to(x - w * 0.2, y - h - 12); c.curve_to(x - w * 0.05, y - h - 26, x + w * 0.1, y - h - 8, x + w * 0.3, y - h - 22); c.set_source_rgb(0.8, 0.15, 0.1); c.set_line_width(5); c.stroke()


def lantern(c, x, y, t, s=1.0):
    fl = 1 + 0.06 * math.sin(t * 13) + 0.04 * math.sin(t * 7.3)
    for r, a in ((150, 0.10), (90, 0.18), (50, 0.3)): c.arc(x, y - 50 * s, r * s * fl, 0, TAU); c.set_source_rgba(1.0, 0.72, 0.3, a); c.fill()
    c.rectangle(x - 26 * s, y - 14 * s, 52 * s, 14 * s); c.set_source_rgb(0.25, 0.22, 0.2); c.fill()
    c.rectangle(x - 20 * s, y - 80 * s, 40 * s, 66 * s); c.set_source_rgba(1.0, 0.9, 0.6, 0.85); c.fill_preserve(); c.set_source_rgb(0.1, 0.08, 0.08); c.set_line_width(4); c.stroke()
    c.arc(x, y - 40 * s, 9 * s * fl, 0, TAU); c.set_source_rgb(1, 0.6, 0.15); c.fill()
    c.rectangle(x - 24 * s, y - 92 * s, 48 * s, 12 * s); c.set_source_rgb(0.25, 0.22, 0.2); c.fill(); c.arc(x, y - 96 * s, 22 * s, PI, TAU); c.set_source_rgb(0.25, 0.22, 0.2); c.set_line_width(5 * s); c.stroke()


# ================================================================ 大头特写（正面）
def bust(c, x, y, R, spec, P, t, arm=None):
    """正面胸像：(x, y) 头中心，R 头半径。arm=(肩→手的方向角, 长度系数, 手里拿的东西) 抬起一只手。"""
    col = spec.get('uniform', (0.46, 0.5, 0.52)); dk = tuple(v * 0.72 for v in col); OLc = (0.1, 0.08, 0.08); lw = max(3, 0.05 * R)
    top = y + 0.85 * R; sw = 1.55 * R
    if spec.get('cloak'):
        c.move_to(x - sw - 0.2 * R, H + 50); c.curve_to(x - sw - 0.3 * R, top + 0.4 * R, x - 0.9 * R, top, x, top); c.curve_to(x + 0.9 * R, top, x + sw + 0.3 * R, top + 0.4 * R, x + sw + 0.2 * R, H + 50); c.close_path()
        c.set_source_rgb(*spec['cloak']); c.fill_preserve(); c.set_source_rgb(*OLc); c.set_line_width(lw); c.stroke()
    c.move_to(x - sw, H + 50); c.curve_to(x - sw, top + 0.3 * R, x - 0.8 * R, top, x, top); c.curve_to(x + 0.8 * R, top, x + sw, top + 0.3 * R, x + sw, H + 50); c.close_path()
    g = cairo.LinearGradient(x - sw, 0, x + sw, 0); g.add_color_stop_rgb(0, *dk); g.add_color_stop_rgb(0.5, *col); g.add_color_stop_rgb(1, *dk)
    c.set_source(g); c.fill_preserve(); c.set_source_rgb(*OLc); c.set_line_width(lw); c.stroke()
    c.move_to(x - 0.42 * R, top - 0.05 * R); c.line_to(x, top + 0.45 * R); c.line_to(x + 0.42 * R, top - 0.05 * R); c.set_source_rgb(*spec.get('collar', dk)); c.set_line_width(0.16 * R); c.stroke()
    if spec.get('collar_tab'):
        for k in (-1, 1): c.rectangle(x + k * 0.32 * R - 0.09 * R, top + 0.12 * R, 0.18 * R, 0.14 * R); c.set_source_rgb(*spec['collar_tab']); c.fill()
    for k in range(3): c.arc(x, top + 0.6 * R + k * 0.42 * R, 0.06 * R, 0, TAU); c.set_source_rgb(0.25, 0.22, 0.18); c.fill()
    for k in (-1, 1): c.rectangle(x + k * 0.75 * R - 0.28 * R, top + 0.75 * R, 0.56 * R, 0.4 * R); c.set_source_rgba(0, 0, 0, 0.12); c.fill()
    def draw_arm():
        a, L, thing = arm; sx_ = x + 1.25 * R; sy_ = top + 0.45 * R; hx, hy = sx_ + math.sin(a) * L * R, sy_ - math.cos(a) * L * R
        for w_, cc in ((0.55 * R + 2 * lw, OLc), (0.55 * R, col)): c.move_to(sx_, sy_); c.line_to(hx, hy); c.set_source_rgb(*cc); c.set_line_width(w_); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        if thing == 'phone':
            c.save(); c.translate(hx - 0.1 * R, hy - 0.2 * R); c.rotate(-0.35); c.rectangle(-0.09 * R, -0.5 * R, 0.18 * R, 1.0 * R); c.set_source_rgb(0.08, 0.08, 0.09); c.fill()
            for yy in (-0.5, 0.5): c.save(); c.translate(0, yy * R); c.scale(1.4, 1); c.arc(0, 0, 0.14 * R, 0, TAU); c.restore(); c.fill()
            c.restore()
        c.arc(hx, hy, 0.26 * R, 0, TAU); c.set_source_rgb(*spec.get('skin', (0.95, 0.82, 0.7))); c.fill_preserve(); c.set_source_rgb(*OLc); c.set_line_width(lw); c.stroke()
    if arm and arm[2] != 'phone': draw_arm()
    P = dict(P, front=True); RG.head(c, x, y, R, spec, P, t)
    if arm and arm[2] == 'phone': draw_arm()


def name_tag(X, s, x, y, dark=False): X.T(s, x, y, 64, fill=CREAM if dark else INK_T, halo=(20, 14, 10) if dark else (250, 238, 215), stroke=7)


# ================================================================ 镜头（t 都是 BGM 时间）
QUESTION = '被40万人围住，3万红军怎么走出去？'


def hook(lt, dur, t):
    X = Txt(True); l = lt - 0.15
    if l >= 0:
        sz = 240 * (1 + 0.5 * (1 - eout(l / 0.14)))
        X.T('40万', 560, 830, sz, fill=(52, 70, 120), stroke=13, halo=(250, 238, 215), a=ease(l / 0.06)); X.T('围', W / 2, 830, 130, fill=INK_T, stroke=9, halo=(250, 238, 215), a=ease((l - 0.3) / 0.1))
        X.T('3万', 1380, 830, sz * ease((l - 0.55) / 0.12) + 1, fill=RED_T, stroke=13, halo=(250, 238, 215), a=ease((l - 0.55) / 0.06))
    fr = battles.hook(lt * 1.1); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    fr = fr * (1 - 0.5 * np.exp(-((xx - W / 2) / 800) ** 2 - ((yy - 830) / 210) ** 2))[..., None]
    return X.over(to_img(fr + np.float32([1, 0.95, 0.85]) * 0.5 * math.exp(-max(0, l) / 0.08) * (l >= 0)))


def mao_plan(lt, dur, t):
    X = Txt(False); X.T(QUESTION, W / 2, 110, 84, fill=(255, 238, 200), stroke=9, halo=(28, 18, 14), a=ease(lt / 0.12))
    def d(c):
        grass(c, 0, W, 820, 1080, 60, 3, t=lt); table(c, 1010, 905, 460, 170)
        Q(c, 420, 905, 440, ZD, 1, 'fold', lt, eye='dot', brow='flat', mouth='flat'); Q(c, 1560, 905, 450, ZE, -1, 'fold', lt, eye='dot', brow='angry', mouth='flat')
        Q(c, 720, 905, 500, MZ, 1, 'point', lt, eye='glint', brow='angry', mouth='flat', sf=1.15, ef=1.25, w=1.2)
    X2 = Txt(False)
    for nm, x, h in (('朱德', 420, 440), ('毛泽东', 720, 500), ('周恩来', 1560, 450)): X2.T(nm, x, 905 - h - 100, 46, fill=(60, 48, 40), stroke=5, a=ease((lt - 0.2) / 0.15))
    return X2.over(compose(d, 'day', X=X, lt=lt, zoom=1.04 + 0.05 * lt / dur, cy=800))


def map_shot(lt, dur, t):
    n = (t - B0) / BAR; pk = math.exp(-(((t - B0) % BAR)) / 0.13)                 # 每小节一次推镜冲击
    img = push(MS().frame(t), lt / max(dur, 1e-3), 0.07); img = push(img, pk, 0.025)
    X = Txt(False); fl = 9.0
    def at(n0): return t - T(n0)
    if n < 5: date(X, '1935年1月  遵义'); slam(X, '四渡赤水', at(4), size=300, keep=False, hold=2.0); fl = at(4)
    elif n < 8.5: date(X, '1月29日'); slam(X, '一渡', at(7)); sub(X, '向西渡过赤水河  甩开追兵', at(7) - 0.35); fl = at(7)
    elif n < 10.5: date(X, '2月18日'); slam(X, '二渡', at(9.5), hold=0.9); sub(X, '敌人扑向川南  红军掉头杀回贵州', at(9.5) - 0.3); fl = at(9.5)
    elif n < 13: date(X, '2月28日'); slam(X, '再占遵义', at(12), hold=0.9); sub(X, '5天  歼敌2个师又8个团', at(12) - 0.3); fl = at(12)
    elif n < 15.5: date(X, '3月'); slam(X, '碉堡合围', at(14), col=INK_T, hold=0.9); sub(X, '几十万大军  一圈一圈往里压', at(14) - 0.3); fl = at(14)
    elif n < 21: date(X, '3月16日'); slam(X, '三渡', at(20), hold=0.9); sub(X, '再向西渡河  故意让敌人看见', at(20) - 0.3); fl = at(20)
    elif n < 23: date(X, '3月20日'); sub(X, '一个团假装主力北上  敌人全线西扑', at(22)); fl = at(22)
    elif n < 27: date(X, '3月21日'); sub(X, '40万人  全被甩在河西', at(25.5)); fl = at(25.5)
    elif n < 30: date(X, '4月初'); slam(X, '直逼贵阳', at(27.5), hold=0.9); sub(X, '蒋介石  就在贵阳城里', at(27.5) - 0.3); fl = at(27.5)
    elif n < 32.5: date(X, '4月'); sub(X, '滇军火速赶来救驾  云南空了', at(30.5)); fl = at(30.5)
    elif n < 36: date(X, '4月'); slam(X, '向西', at(33.5), hold=0.8); sub(X, '掉头直奔云南  抢渡金沙江', at(33.5) - 0.25); fl = at(33.5)
    else: date(X, '1935年5月'); slam(X, '跳出包围', at(38), hold=1.0); sub(X, '40万大军  扑了个空', at(38) - 0.35); fl = at(38)
    return flash(X.over(img), fl)


def battle_shot(fn, title, day, line, dark=False, rate=0.82):
    def f(lt, dur, t):
        X = Txt(dark); slam(X, title, lt, hold=0.85); date(X, day, dark=dark); sub(X, line, lt - 0.3, dark=dark)
        return battle(fn(lt * rate), X, lt)
    return f


tucheng = battle_shot(battles.tucheng, '土城', '1月28日', '想北渡长江  第一仗就打输了', rate=0.8)
loushan = battle_shot(battles.loushan, '娄山关', '2月25日', '回马枪  一举冲垮守军')
lubanchang = battle_shot(lambda l: battles.tucheng(l, battles.ZY), '鲁班场', '3月15日', '强攻碉堡  打不下来', rate=0.8)
ford1 = battle_shot(lambda l: battles.crossing(l, night=False), '一渡', '1月29日', '甩开追兵  敌人全扑向川南', rate=1.0)
ford3 = battle_shot(lambda l: battles.crossing(l, night=False), '三渡', '3月16日', '大张旗鼓  故意让敌人看见', rate=1.0)
ford4 = battle_shot(lambda l: battles.crossing(l, night=True), '四渡', '3月21日 夜', '主力连夜  悄悄渡回东岸', dark=True, rate=1.0)
wujiang = battle_shot(lambda l: battles.crossing(l, night=False), '南渡乌江', '3月31日', '一路向南  甩开所有追兵', rate=1.0)
jinsha = battle_shot(battles.jinsha, '金沙江', '5月3日—9日', '靠几条木船  全军渡过金沙江', rate=1.0)


def jiang_angry(lt, dur, t):
    X = Txt(False); sub(X, '亲自飞到重庆、贵阳督战', lt - 0.3)
    hit = (lt * 3.4) % 1.0; down = math.exp(-hit / 0.08)
    def d(c):
        bust(c, 900, 430 + 14 * down, 300, JJ, dict(eye='fierce', brow='angry', mouth='grit', fx=('anger',)), lt, arm=(0.25 + 0.9 * down, 1.9, None))
    return compose(d, 'hall', X=X, lt=lt, shake=14 * down, zoom=1.02 + 0.04 * lt / dur)


def jiang_proud(lt, dur, t):
    X = Txt(False); 
    X.T('“剿匪成功  在此一举”', W / 2, 960, 86 * (1 + 0.25 * (1 - eout(lt / 0.15))), fill=RED_T, stroke=9, halo=(250, 238, 215), a=ease(lt / 0.08))
    def d(c): bust(c, 960, 470, 340, JJ, dict(eye='happy', brow='raised', mouth='smile', tilt=0.06 * math.sin(lt * 6)), lt, arm=(0.15, 1.9, None))
    return compose(d, 'hall', X=X, lt=lt, zoom=1.0 + 0.06 * lt / dur, glow=(960, 450, 420, (1.0, 0.8, 0.4), 0.25))


def jiang_shock(lt, dur, t):
    X = Txt(False); sub(X, '急调云南的滇军  火速救驾', lt - 0.3)
    X.T('“快！快！”', 1470, 330, 140 * (1 + 0.3 * (1 - eout(lt / 0.15))), fill=RED_T, stroke=10, halo=(250, 238, 215), a=ease(lt / 0.08))
    def d(c): bust(c, 860, 480 + 8 * math.sin(lt * 40), 350, JJ, dict(eye='shock', brow='worried', mouth='gasp', fx=('sweat', 'shocklines')), lt, arm=(-0.2, 1.25, 'phone'))
    return compose(d, 'hall', X=X, lt=lt, shake=6 + 6 * math.exp(-lt / 0.3), zoom=1.06 + 0.06 * lt / dur, cx=860, cy=480)


def mao_night(lt, dur, t):
    X = Txt(True); k2 = lt > dur * 0.5
    slam(X, '换个打法', lt, size=230, keep=False, hold=1.5)
    if not k2: sub(X, '打不赢  就不打', lt - 0.4, dark=True, a=1 - ease((lt - dur * 0.5 + 0.15) / 0.15))
    else: sub(X, '让敌人  跟着自己走', lt - dur * 0.5, dark=True)
    def d(c):
        table(c, 1090, 930, 480, 180); lantern(c, 1250, 750, lt, 1.3)
        Q(c, 740, 930, 560, MZ, 1, 'fold' if not k2 else 'point', lt, eye='glint' if k2 else 'dot', brow='angry', mouth='smirk' if k2 else 'flat', sf=1.2 if k2 else 0.25, ef=1.3 if k2 else 1.25, w=1.3)
    return compose(d, 'night', X=X, lt=lt, glow=(1250, 680, 330, (1.0, 0.6, 0.25), 0.5), zoom=1.03 + 0.06 * lt / dur, cx=900, cy=760)


def mao_smile(lt, dur, t):
    X = Txt(False); sub(X, '这才是真正的目标', lt - 0.2)
    def d(c): bust(c, 960, 450, 320, MZ, dict(eye='glint', brow='angry', mouth='smirk'), lt, arm=(0.9, 1.6, None))
    return compose(d, 'day', X=X, lt=lt, zoom=1.04 + 0.08 * lt / dur, cy=450)


def answer(lt, dur, t):
    X = Txt(False); l2 = lt - BAR
    if l2 < 0: slam(X, '不硬拼', lt, size=260, keep=False, hold=BAR - 0.1)
    else: slam(X, '调动敌人', l2, size=260, keep=False, hold=9)
    sub(X, '四渡赤水：3万人  牵着40万人走', lt - 0.5)
    def d(c):
        for k in range(5): Q(c, 1440 + k * 105, 890 - (k % 2) * 22, 250, HJ, 1, 'walk', lt * 1.2 + k * 0.7, eye='dot', brow='angry', mouth='flat', w=PI - 0.3)
        Q(c, 250, 900, 400, MZ, 1, 'point', lt, eye='glint', brow='angry', mouth='smirk', sf=1.7, ef=1.8, w=1.7)
    img = push(MS().frame(t), lt / max(dur, 1e-3)); Bg = np.asarray(img).astype(np.float32) / 255
    A_ = layer(d); fr = A_[..., [2, 1, 0]] + Bg * (1 - A_[..., 3:4])
    return flash(X.over(to_img(fr)), min(lt, l2 if l2 >= 0 else 9))


SONG = [(T(2), T(3), hook), (T(3), T(4), mao_plan), (T(4), T(5), map_shot), (T(5), T(7), tucheng), (T(7), T(8), map_shot), (T(8), T(9.5), ford1),
        (T(9.5), T(10.5), map_shot), (T(10.5), T(12), loushan), (T(12), T(13), map_shot), (T(13), T(14), jiang_angry), (T(14), T(15.5), map_shot),
        (T(15.5), T(17), lubanchang), (T(17), T(20), mao_night), (T(20), T(21), map_shot), (T(21), T(22), ford3), (T(22), T(23), map_shot), (T(23), T(24), jiang_proud),
        (T(24), T(25.5), ford4), (T(25.5), T(26.5), map_shot), (T(26.5), T(27.5), wujiang), (T(27.5), T(29), map_shot), (T(29), T(30.5), jiang_shock),
        (T(30.5), T(32.5), map_shot), (T(32.5), T(33.5), mao_smile), (T(33.5), T(36), map_shot), (T(36), T(38), jinsha), (T(38), T(39.5), map_shot), (T(39.5), T_END, answer)]
SHOTS = [(max(0.0, a - OFF), b - OFF, (lambda f: (lambda lt, dur, t: f(lt, dur, t + OFF)))(f)) for a, b, f in SONG]

if __name__ == '__main__':
    from mapwar.film import Film
    Film(SHOTS, T_END - OFF, audio=os.path.join(HERE, 'mix.wav'), fade_out=1.4).cli()
