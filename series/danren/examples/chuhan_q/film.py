"""楚汉争霸 · 精致 Q 版（演义扮相）成片：开头提问 → 原因一/二/三 → 结尾作答。
地图和俯视阵战的数据沿用 ../chuhan/scenario.py（R() 把旧时刻映射到新时间线）；人物戏全部用 mapwar.qchar 的 Q 版角色；
彭城是斜视角蛋蛋兵撞阵 + 一段打斗特写（fight.py）；夜间突围是蛋蛋兵凿穿（breakout.py）；别姬、乌江是侧面全身戏。
  python film.py times | still 输出目录 t... | part i n out.mp4 0.5 | render out.mp4
音频自备：MAPWAR_AUDIO=从 BGM 的 OFF 秒起截出 T_END 秒的一段（连续播放，不剪接）。成片再过一遍 mapwar.brand 加印章和片尾页。
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(HERE, '..', '..'), os.path.join(HERE, '..', 'chuhan'), HERE):
    sys.path.insert(0, p)
import numpy as np, cairo
from PIL import Image
import scenario as O
from mapwar.util import SW, SH, ease, eout, Txt, to_img, VR, grain, font
from mapwar.mapshot import MapShot
from mapwar import field as F, eggfield, qhorse, qrig as RG
from mapwar.qchar import Q, rider, PI, TAU
from mapwar.scenery import landscape, burn, grass, tent, fire, snow, boat, reeds, dust
from cast.chuhan import XY, FK, HAN, LB, HX, ZL, XH, FZ, YJ, TZ
import fight
from breakout import breakout_frame

W, H = SW, SH
H_, C_, Q_, N_ = O.H_, O.C_, O.Q_, O.N_
BAR = O.BAR; BEAT = BAR / 4
RED_T, BLUE_T = (168, 26, 16), (22, 46, 100)


class Txt2(Txt):                                        # 去掉「号称」之类的修饰
    def T(self, s, *a, **k): return super().T(s.replace('号称', '').replace('  ', ' '), *a, **k)


O.Txt = Txt2


def card_titles(X, lt, big, place, date, x0=1775):     # 大战役：横排砸到正中，随后缩到左上
    if lt < 1.2:
        sz = 250 * (1 + 0.5 * (1 - eout(lt / 0.16))); a = ease(lt / 0.06) * (1 - ease((lt - 0.95) / 0.25))
        X.T(big, SW / 2 + 8, 508, sz, fill=(20, 14, 12), stroke=0, a=a * 0.8); X.T(big, SW / 2, 500, sz, fill=RED_T, stroke=14, halo=(250, 238, 215), a=a)
    X.T(big, 300, 100, 92, fill=RED_T, stroke=8, a=ease((lt - 1.0) / 0.2))


O.card_titles = card_titles

# ================================================================ 时间线：BGM 从 OFF 秒起连续播放，不剪接（开头钩子压在间奏上，鼓点落在彭城撞击）
T_A = 8.6; OFF = 63.543 - T_A        # OFF = 54.943
D1 = 73.88 - OFF; PB0 = D1 - 3 * BAR
R1 = D1 + 3.5 * BAR; HP = R1 + 3 * BAR; HQ = HP + BAR
J0 = HQ + 1.5 * BAR; J1 = J0 + 2.5 * BAR; WS0 = J1 + 1.5 * BAR; WS1 = WS0 + 2.5 * BAR
HG0 = WS1 + 2 * BAR; BY = HG0 + 2 * BAR; E1 = BY + 2.5 * BAR
CS1 = E1 + 2.5 * BAR; G0 = CS1 + 2 * BAR; G1 = G0 + 2 * BAR
S0 = 129.25 - OFF; D2 = 131.50 - OFF; BJ0 = S0 - 2 * BAR
M5 = D2 + 1.5 * BAR; W0 = M5 + 2.5 * BAR; F0 = W0 + 3 * BAR; T_END = F0 + 3 * BAR + 1.0
BURN0, BURN1 = T_A - 0.3, T_A + 0.6

OLD = [O.T_A, O.D1, O.D1 + O.BAR / 2, O.R1, O.R1 + 3.4, O.HP, O.HP + O.BAR / 2, O.J0, O.J1, O.WS0, O.WS1, O.HG0, O.E1 - .88, 36.45, 36.46, 38.25, O.G0, O.G1, O.S0, O.D2, O.M5, O.W0, O.F0, O.F0 + 2 * O.BAR, O.T_END, 199]
NEW = [T_A, PB0, PB0 + 0.5, R1, R1 + 3.4, HP, HQ, J0, J1, WS0, WS1, HG0, BY, E1, CS1, CS1 + 1.4, G0, G1, BJ0, D2, M5, W0, F0, F0 + 3 * BAR, T_END, 199 + T_END - O.T_END]
R = lambda t: float(np.interp(t, OLD, NEW))

O.W.flips = {k: [(R(t), o) for t, o in v] for k, v in O.FLIPS.items()}
ARMIES = []
for A in O.ARMIES:
    A2 = dict(A); A2['path'] = [(R(p[0]),) + tuple(p[1:]) for p in A['path']]
    A2['rout'] = [(R(a), R(b)) for a, b in A.get('rout', [])]
    A2['tags'] = [(R(a), R(b), x.replace('号称', '').replace('约', '')) for a, b, x in A.get('tags', [])]
    if 'die' in A: A2['die'] = R(A['die'])
    ARMIES.append(A2)
ARROWS = [(R(x[0]), R(x[1]), R(x[2])) + tuple(x[3:]) for x in O.ARROWS]
CAMSEG = [[(R(k[0]),) + tuple(k[1:]) for k in seg] for seg in O.CAMSEG]
DATES = [(R(d[0]), d[2]) for d in O.DATES]
CARDS = [(T_A + 0.5, PB0 - 0.05, '直取彭城', '56万联军 攻入楚都'),
         (J1 + 0.05, WS0 - 0.05, '赵燕归汉', ''),
         (WS1 + 0.3, HG0 - 0.05, '北线尽取', '北方全归刘邦'),
         (HG0 + 0.05, BY - 0.05, '楚河汉界', '以鸿沟为界 中分天下'),
         (BY + 0.05, E1 - 0.05, '追击', '刘邦毁约 追击项羽'),
         (CS1 + 0.05, G0 - 0.05, '三路会师', '韩信 彭越 英布 合围'),
         (G1 + 0.05, BJ0 - 0.05, '四面楚歌', '汉军唱楚歌 楚军心散'),
         (M5 + 0.05, W0 - 0.05, '突围', ''),
         (F0 + 0.3, 99, '汉', '', 'huge')]
FIRES = [(a, b, R(c), R(d)) for a, b, c, d in [(117.1, 34.32, O.R1, O.R1 + 2.4), (113.6, 34.86, O.R1 + 2.7, O.R1 + 3.4), (114.9, 33.92, 36.4, 37.4), (117.55, 33.32, 39.6, O.S0)]]


def style_at(t): return 'night' if G0 <= t < W0 else 'ink'


def ground_fx(ms, c, t, Sp, st):
    if HG0 <= t < BY + 0.4:
        a = ease((t - HG0) / 0.3) * (1 - ease((t - BY) / 0.4)); pts = [Sp(*p)[:2] for p in O.HONGGOU]
        for wd, al in ((30, 0.18), (15, 0.45), (7, 1.0)):
            c.set_source_rgba(0.08, 0.06, 0.06, al * a); c.set_line_width(wd); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(*pts[0])
            for p in pts[1:]: c.line_to(*p)
            c.stroke()


def post(frame, t, st):
    if G1 <= t < BJ0: dk = ease((t - G1) / 0.6); frame = frame * (1 - 0.3 * dk) * np.float32([0.88, 0.95, 1.12])
    return frame


def overlay(ms, X, t, Sp, st, tilt):
    T = X.T; tint = ms.tint
    m1, m2 = M5 + 1.0, M5 + 2.6
    if m1 <= t < W0:
        big = '28 骑' if t >= m2 else '百余骑'; l2 = t - (m2 if big == '28 骑' else m1)
        T(big, 360, 540, 190 * (1 + 0.4 * (1 - eout(l2 / 0.15))), fill=tint(C_, 0.85, 1.4), stroke=9, a=ease(l2 / 0.1))


MS = MapShot(O.W, dict(style=style_at, camseg=CAMSEG, armies=ARMIES, arrows=ARROWS, dates=DATES, cards=CARDS,
                       shakes=[(R1, 16), (J1, 12), (WS1, 12), (M5, 12), (G1, 10), (F0 + .25, 10)], flashes=[R1, J1, WS1, G1, M5, F0], fires=FIRES,
                       regions=O.MS.sc['regions'], keycity=O.MS.sc['keycity'], hud=dict(share=False),
                       ground_fx=ground_fx, post=post, overlay=overlay))
from mapwar.eggfield import CHU_B, HAN_B, GOLD
MS.sc['egg'] = {0: dict(body=HAN_B, hat='ancient', hatcol=(0.62, 0.63, 0.66), plume=(0.92, 0.12, 0.08), band=(0.75, 0.12, 0.08), weapon='spear'),     # 地图上的军队画成古代蛋蛋兵（势力下标 → 长相）
                1: dict(body=CHU_B, hat='ancient', hatcol=(0.14, 0.14, 0.17), plume=(0.96, 0.95, 0.9), band=GOLD, weapon='ji', shaft=GOLD),
                2: dict(body=(0.52, 0.5, 0.24), hat='ancient', hatcol=(0.45, 0.42, 0.3), weapon='spear'),
                3: dict(body=(0.52, 0.48, 0.42), hat='ancient', hatcol=(0.42, 0.4, 0.36), weapon='spear')}
MS.sc['fig_scale'] = 0.45


# ================================================================ 公用
def layer(draw):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); draw(c)
    return np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32) / 255


def over(fr, a, k=1.0): return fr * (1 - a[..., 3:4] * k) + a[..., [2, 1, 0]] * k


def reason(X, n, title, l, a=1.0):
    """顶部「原因X」标签：红底白字印章 + 大标题。"""
    pop = 1 + 0.35 * (1 - eout(min(1, l / 0.16))); a = a * ease(l / 0.08)
    if a <= 0.01: return
    fs = int(100 * pop); tw = X.d.textbbox((0, 0), title, font=font(fs), anchor='lt')[2]
    sw, sh_ = int(200 * pop), int(96 * pop); gap = 26; x0 = W / 2 - (sw + gap + tw) / 2; y = 128
    X.d.rounded_rectangle([x0, y - sh_ / 2, x0 + sw, y + sh_ / 2], radius=10, fill=(176, 30, 20, int(255 * a)), outline=(250, 236, 210, int(220 * a)), width=4)
    X.T('原因' + n, x0 + sw / 2, y, int(62 * pop), fill=(255, 244, 225), stroke=0, a=a)
    X.T(title, x0 + sw + gap + tw / 2, y, fs, fill=(30, 22, 18), stroke=9, halo=(250, 238, 215), a=a)


def sub(X, s, l, a=1.0, dark=False, x=W / 2):
    X.T(s, x, 968, 70, fill=(255, 238, 210) if dark else (25, 20, 18), halo=(20, 14, 10) if dark else (245, 232, 205), stroke=8, a=a * ease(l / 0.18))


def camp(c, t):
    for k in range(16):
        x = 40 + k * 125; c.set_source_rgba(1.0, 0.7, 0.3, 0.6 + 0.3 * math.sin(t * 7 + k)); c.arc(x, 640 + 22 * math.sin(k * 1.7), 5, 0, 2 * math.pi); c.fill()
    tent(c, 1680, 830, 420, (0.62, 0.58, 0.52)); tent(c, 240, 810, 300, (0.56, 0.52, 0.47)); fire(c, 960, 880, 80, t)


QUESTION = '3万打赢56万，项羽为什么还是输了？'
S_TW = {}


def sim():
    if 'S' not in S_TW: S_TW['S'] = eggfield.simulate()          # 约 5 秒；每个渲染进程各算一次，结果相同
    return S_TW['S']


def qline(img, a=1.0):
    X = Txt(False); X.T(QUESTION, W / 2, 96, 86, fill=(255, 238, 200), stroke=9, halo=(28, 18, 14), a=a); return X.over(img)


def push(img, k):
    s = 1 + 0.045 * k; w, h = W / s, H / s; x0, y0 = (W - w) / 2, (H - h) / 2
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)


def ring(lt, dur, t):
    """入夜：火圈从四周收拢吞掉白天地图 → 夜里十面埋伏。"""
    if 'ring' not in O._B: O._B['ring'] = F.Ring()
    k = lt / dur; surf, c = F.canvas(); NF = 0.9; e = math.exp(-max(0, lt - NF) / 0.13) if lt >= NF else 0
    z = 0.78 + 0.34 * ease(k)
    c.translate(SW / 2 + 22 * e * math.sin(lt * 85), SH / 2 + 22 * e * math.sin(lt * 67 + 1)); c.rotate(0.05 - 0.1 * k); c.scale(z, z); c.translate(-960, -560); c.set_line_cap(cairo.LINE_CAP_ROUND)
    O._B['ring'].draw(c, k, lt, O.SDN['C'], O.SDN['H']); c.set_source_rgba(1.0, 0.95, 0.8, 1); c.arc(960, 560, 9, 0, 2 * math.pi); c.fill()
    X = Txt(True); l = lt - NF
    if l >= 0:
        sz = 250 * (1 + 0.5 * (1 - eout(l / 0.16))); a = ease(l / 0.06) * (1 - ease((l - 1.0) / 0.25))
        X.T('垓下之战', SW / 2, 500, sz, fill=(255, 226, 150), stroke=14, halo=(30, 10, 6), a=a); X.T('垓下之战', 300, 100, 92, fill=(255, 210, 120), stroke=8, a=ease((l - 1.0) / 0.2))
        if l > 1.1: X.T('汉军 30万', 300, 470, 84, fill=(255, 130, 95), stroke=8, a=ease((l - 1.1) / 0.1)); X.T('楚军 10万', 300, 580, 84, fill=(130, 195, 255), stroke=8, a=ease((l - 1.35) / 0.1))
        X.T('十面埋伏 层层合围', SW / 2, 968, 66, stroke=7, a=ease((l - 0.3) / 0.2))
    img = F.finish(surf, lt, X, 'night', [NF])
    if lt < NF:                                                               # 火圈收拢：外圈是夜，内圈的白天越来越小
        day = _dayframe(); u = ease(lt / NF)
        img = to_img(burn(np.asarray(img).astype(np.float32) / 255, day, 1 - u, edge=0.06))
    return img


_DF = {}


def _dayframe():
    if 'd' not in _DF: _DF['d'] = np.asarray(push(MS.frame(G0 - 0.02), 1.0)).astype(np.float32) / 255
    return _DF['d']


XYs = dict(XY); XYn = dict(XY, weapon=None)
INS0 = D1 - (4.056 - 2.5); INS1 = D1 + 2.2                                   # 项羽空翻下劈插入段


def sm(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def layer(draw):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); draw(c)
    return np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32) / 255


def compose(draw, bg='day', Xu=None, Xo=None, lt=0.0, flashes=(), fade_in=0.0, zoom=1.0, cx=W / 2, cy=H / 2, gray=0.0, mul=None, glow=None, shake=0.0, sil=None, base=None, under=None, top=None):
    """背景 → 字（Xu，在人下面）→ 人 → 调色。sil=(颜色, 程度) 把人压成剪影。"""
    def cam(fn):
        def d(c):
            if shake: c.translate(shake * math.sin(lt * 83), shake * math.sin(lt * 67 + 1))
            if zoom != 1.0: c.translate(cx, cy); c.scale(zoom, zoom); c.translate(-cx, -cy)
            fn(c)
        return d
    d = cam(draw)
    Bg = landscape(bg) if base is None else base
    if glow is not None:
        gx, gy, gr, gc, ga = glow; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); Bg = Bg + np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * gr * gr))[..., None] * np.float32(gc) * ga
    if under is not None: U = layer(cam(under)); Bg = U[..., [2, 1, 0]] + Bg * (1 - U[..., 3:4])
    if Xu is not None: Bg = np.asarray(Xu.over(to_img(Bg))).astype(np.float32) / 255
    A = layer(d)
    if sil is not None:
        col, k = sil; A[..., :3] = A[..., :3] * (1 - k) + A[..., 3:4] * np.float32(col[::-1]) * k
    fr = A[..., [2, 1, 0]] + Bg * (1 - A[..., 3:4])
    if top is not None: Tp = layer(cam(top)); fr = Tp[..., [2, 1, 0]] + fr * (1 - Tp[..., 3:4])
    if mul is not None: fr = fr * np.float32(mul)
    if gray: g = fr.mean(-1, keepdims=True); fr = fr * (1 - gray) + g * gray * 0.85
    fr = fr * (1 - 0.32 * VR)
    for h_ in flashes: fr = fr + np.float32([1, 0.95, 0.85]) * 0.4 * math.exp(-max(0, lt - h_) / 0.07) * (lt >= h_)
    if fade_in: fr = fr * ease(lt / fade_in)
    img = to_img(fr + grain(0.02))
    return Xo.over(img) if Xo is not None else img


# ================================================================ 开头钩子
def qcard(l):
    X = Txt(True); sz = 330 * (1 + 0.5 * (1 - eout(l / 0.16)))
    X.T('为什么？', W / 2 + 8, 568, sz, fill=(20, 12, 10), stroke=0, a=0.9); X.T('为什么？', W / 2, 560, sz, fill=(200, 34, 22), stroke=14, halo=(255, 240, 215))
    def d(c):
        Q(c, 240, 1200, 660, XY, 1, 'stand', l, eye='dot2', brow='angry', mouth='flat', flags=False)
        Q(c, 1690, 1200, 640, LB, -1, 'idle', l, eye='dot', brow='raised', mouth='smirk')
    return compose(d, 'day', Xu=X, lt=l, flashes=(0,), gray=0.25, mul=(0.85, 0.82, 0.8))


def egg_impact(l):
    S = sim(); T = S['imp'][0]; img, cam, ts = eggfield.render(T + 0.04 + l * 0.42, S)
    fr = np.asarray(img).astype(np.float32) / 255; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    fr = fr * (1 - 0.55 * np.exp(-((xx - W / 2) / 760) ** 2 - ((yy - 560) / 200) ** 2))[..., None]
    X = Txt(True); sz = 210 * (1 + 0.5 * (1 - eout(l / 0.14)))
    X.T('3万', 600, 560, sz, fill=(140, 190, 255), stroke=12, a=ease(l / 0.06)); X.T('VS', W / 2, 560, 90, stroke=8, a=ease((l - 0.25) / 0.1))
    X.T('56万', 1340, 560, sz * ease((l - 0.35) / 0.12) + 1, fill=(255, 110, 80), stroke=12, a=ease((l - 0.35) / 0.06))
    return X.over(to_img(fr))


def hook(lt, dur, t):
    b = [0, BAR, 2 * BAR, 3 * BAR, 4 * BAR]
    if lt >= b[4]: img = qcard(lt - b[4])
    elif lt >= b[3]:                                                           # 刘邦特写
        l = lt - b[3]; X = Txt(False)
        X.V('刘邦', 1400, 300, 230 * (1 + 0.4 * (1 - eout(l / 0.15))), fill=RED_T, stroke=10, a=ease(l / 0.08))
        X.T('赢家却是他', 1330, 830, 74, stroke=8, a=ease((l - 0.1) / 0.15)); X.T('屡战屡败', 1330, 935, 80, fill=RED_T, stroke=8, a=ease((l - 0.3) / 0.15))
        img = compose(lambda c: Q(c, 700, 1800, 1650, LB, 1, 'idle', l, eye='dot', brow='raised', mouth='smirk'), 'day', Xu=X, lt=l, flashes=(0,), zoom=1 + 0.03 * l)
    elif lt >= b[2]:                                                           # 乌江跪地
        l = lt - b[2]; X = Txt(True); sub(X, '却在31岁 自刎乌江', l - 0.1, dark=True)
        def d(c):
            qhorse.horse(c, 1680, 900, 330, (0.16, 0.17, 0.22), -1, lt, 'stand', head_a=0.5)
            Q(c, 1150, 905, 470, XYn, -1, 'kneel', lt, eye='closed', brow='worried', mouth='flat', flags=False)
            reeds(c, 0, 900, 1080, 260, 3, lt)
        img = compose(d, 'dusk', Xo=X, lt=l, flashes=(0,), gray=0.5, zoom=1 + 0.05 * l, cx=1200, cy=700)
    elif lt >= b[1]:                                                           # 项羽 + 乌骓扬蹄
        l = lt - b[1]; X = Txt(False)
        X.V('项羽', 300, 330, 230 * (1 + 0.4 * (1 - eout(l / 0.15))), fill=BLUE_T, stroke=10, a=ease(l / 0.08)); sub(X, '七十余战  未尝一败', l - 0.1, x=560)
        rr = ease(l / 0.35)
        def d(c):
            grass(c, 0, W, 800, 1080, 80, 2, t=lt)
            rider(c, 1330, 1000, 400, XY, 1, lt, 'stand', rear=rr, hk=1.12, sf=1.8, ef=2.2, w=1.85, lean=-0.2, eye='fierce', brow='angry', mouth='shout')
            dust(c, 1200, 910, lt, 7, 7, 1.4)
        img = compose(d, 'day', Xo=X, lt=l, flashes=(0,), shake=10 * math.exp(-l / 0.2))
    else: img = egg_impact(lt)
    img = qline(img, ease(lt / 0.12))
    if t >= BURN0: img = to_img(burn(np.asarray(img).astype(np.float32) / 255, np.asarray(MS.frame(T_A)).astype(np.float32) / 255, (t - BURN0) / (BURN1 - BURN0)))
    return img


_QL = {}


def _qlast():
    if 'q' not in _QL: _QL['q'] = qline(qcard(T_A - 4 * BAR))
    return _QL['q']


# ================================================================ 地图：刘邦跑 / 终章刘邦
def map_shot(lt, dur, t):
    img = push(MS.frame(t), lt / max(dur, 1e-3))
    if t < BURN1: img = to_img(burn(np.asarray(_qlast()).astype(np.float32) / 255, np.asarray(img).astype(np.float32) / 255, (t - BURN0) / (BURN1 - BURN0)))
    X = Txt(False); people = None
    if R1 <= t < HP:
        l = t - R1; reason(X, '一', '刘邦输得起', l - 0.3); sub(X, '彭城惨败 照样卷土重来', l - 0.6, x=W / 2 + 120)
        k = ease((l - 0.3) / 0.4)
        people = lambda c: Q(c, 300 - (1 - k) * 500, 1080, 560, LB, 1, 'run', l * 1.4, eye='dot', brow='worried', mouth='o', fx=('sweat',))
    if HQ <= t < J0: reason(X, '二', '韩信', 1.0); sub(X, '韩信北伐 灭魏破代', t - HQ)
    if t >= F0 + 0.4:
        l = t - F0; s1 = '前202年  刘邦称帝'; s2 = '项羽只靠自己，刘邦靠所有人'
        if l < 2.9: sub(X, s1, l - 0.5, a=1 - ease((l - 2.7) / 0.2), x=W / 2 - 150)
        else: sub(X, s2, l - 2.9, x=W / 2 - 150)
        k = eout((l - 0.4) / 0.5)
        people = lambda c: Q(c, 1660 + (1 - k) * 420, 1150, 860, LB, -1, 'cheer', l, eye='dot', brow='raised', mouth='smile')
    img = X.over(img)
    if people is not None: img = to_img(over(np.asarray(img).astype(np.float32) / 255, layer(people)))
    return img


# ================================================================ 彭城：俯视 → 斜视角蛋蛋骑兵 → 项羽空翻下劈 → 溃逃
def pengcheng(lt, dur, t):
    if INS0 <= t < INS1: return fight.frame(2.5 + (t - INS0)).convert('RGB')
    S = sim(); T = S['imp'][0]; ft = t - D1 + T
    img, cam, ts = eggfield.render(ft, S); X = Txt(False)
    if lt < 1.3: card_titles(X, lt, '彭城之战', '', '')
    else: X.T('彭城之战', 300, 100, 92, fill=RED_T, stroke=8)
    if lt > 1.25 and ts < 2.7:
        F_ = S['frames'][min(len(S['frames']) - 1, int(round(ts * 30)))]; a = (1 - ease((ts - 2.3) / 0.35)) * ease((lt - 1.25) / 0.2)
        for m, s, col in (((S['kind'] != 3), '汉军 56万', RED_T), ((S['kind'] == 3), '楚 3万骑', BLUE_T)):
            p, _ = cam.proj(np.c_[F_['pos'][m].mean(0)[None], [[0]]]); X.T(s, float(np.clip(p[0, 0] * 2, 240, 1680)), float(np.clip(p[0, 1] * 2, 240, 900)), 100, fill=col, stroke=9, a=a)
    if t >= INS1: sub(X, '汉军全线溃逃', t - INS1 - 0.3)
    if t >= INS1: img = Image.fromarray((np.asarray(img).astype(np.float32) + 255 * 0.5 * max(0, 1 - (t - INS1) / 0.12)).clip(0, 255).astype(np.uint8))
    return X.over(img)


# ================================================================ 人物
def hanxin(lt, dur, t):
    X = Txt(False); reason(X, '二', '韩信', lt); sub(X, '汉大将军 · 兵仙', lt - 0.25)
    def d(c):
        grass(c, 0, W, 800, 1080, 70, 4, t=lt)
        for k in range(6): Q(c, 1100 + k * 125, 905 - (k % 2) * 30, 300, HAN, -1, 'stand', lt + k, w=2.8, sf=0.9, ef=1.6, eye='dot', brow='flat', mouth='flat')
        Q(c, 640, 930, 600, HX, 1, 'point', lt, eye='glint', brow='angry', mouth='smirk', w=2.2, sf=1.9, ef=2.2)
    return compose(d, 'day', Xu=X, lt=lt, flashes=(0,), shake=10 * math.exp(-lt / 0.2))


def renyong(lt, dur, t):
    X = Txt(False); reason(X, '三', '刘邦会用人', lt)
    half = dur * 0.5
    if lt < half: sub(X, '张良出谋  萧何管粮  韩信打仗', lt - 0.3, a=1 - ease((lt - half + 0.2) / 0.2))
    else: sub(X, '项羽连一个范增都留不住', lt - half)
    fz = ease((lt - half) / (dur - half)); later = lt > half
    cast = [(180, ZL, 1, 340, '张良', dict(eye='dot', brow='raised', mouth='smile', sf=1.2, ef=2.3, w=2.6)),
            (390, XH, 1, 340, '萧何', dict(eye='dot', brow='flat', mouth='flat', sf=0.6, ef=1.5)),
            (860, HX, -1, 360, '韩信', dict(eye='glint', brow='angry', mouth='smirk'))]
    def d(c):
        grass(c, 0, W, 800, 1080, 70, 6, t=lt)
        for x, sp, f, h, n, ex in cast: Q(c, x, 890, h, sp, f, 'idle' if sp is not HX else 'stand', lt, **ex)
        Q(c, 630, 900, 420, LB, 1, 'cheer' if later else 'idle', lt, eye='dot', brow='raised', mouth='smile')
        Q(c, 1330, 900, 430, XY, 1 if later else -1, 'stand', lt, eye='dot2', brow='worried' if later else 'angry', mouth='flat' if later else 'smirk', flags=False)
        Q(c, 1640 + fz * 420, 890, 340, FZ, 1, 'walk' if later else 'idle', lt * 1.3, eye='dot', brow='worried', mouth='flat')
    X2 = Txt(False)
    for x, n, h in [(c_[0], c_[4], c_[3]) for c_ in cast] + [(1640 + fz * 420, '范增', 340)]:
        X2.T(n, x, 890 - h - 110, 48, fill=(60, 48, 40), stroke=5, a=ease((lt - 0.4) / 0.2))
    return compose(d, 'day', Xu=X, Xo=X2, lt=lt, flashes=(0,))


# ================================================================ 霸王别姬：剑舞 → 相拥 → 自刎倒入怀中（无血：剑落、花钿落）
def blade(c, x, y, dx, dy, L, glow=0.0, w=9):
    ex, ey = x + dx * L, y + dy * L
    if glow:
        for k in range(4): c.move_to(x, y); c.line_to(ex, ey); c.set_source_rgba(1, 0.92, 0.7, 0.12 * glow); c.set_line_width(w * (3 + 3 * k)); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    c.move_to(x, y); c.line_to(ex, ey); c.set_source_rgb(0.1, 0.08, 0.08); c.set_line_width(w + 5); c.stroke()
    c.move_to(x, y); c.line_to(ex, ey); c.set_source_rgb(0.93, 0.95, 1.0); c.set_line_width(w); c.stroke()


def hand_w(J, P, S):
    hx, hy = RG.to_world(P, S, J['hdf']); w = P['w']; return hx, hy, P['f'] * math.sin(w), math.cos(w)


def flower(c, x, y, r, rot):
    c.save(); c.translate(x, y); c.rotate(rot)
    for kk in range(5): a = kk / 5 * TAU; c.arc(math.cos(a) * r, math.sin(a) * r, r * 0.9, 0, TAU); c.set_source_rgb(0.95, 0.45, 0.55); c.fill()
    c.arc(0, 0, r * 0.55, 0, TAU); c.set_source_rgb(1.0, 0.82, 0.3); c.fill(); c.restore()


def bieji(lt, dur, t):
    X = Txt(True); X.T('霸王别姬', 290, 100, 110, fill=(255, 220, 160), stroke=8, a=ease(lt / 0.3))
    t1, t2, t3 = 1.9, 3.1, 3.55
    if lt < t1: sub(X, '力拔山兮气盖世', lt - 0.15, dark=True, a=1 - ease((lt - t1 + 0.2) / 0.2))
    elif lt < t3: sub(X, '虞兮虞兮奈若何', lt - t1, dark=True, a=1 - ease((lt - t3 + 0.15) / 0.15))
    else: sub(X, '虞姬自刎', lt - t3, dark=True)
    HX_, HY_ = 560, 500
    def d(c):
        if lt < t1:                                                            # 剑舞：转身、甩剑，剑始终向外
            sp = lt * 4.2; fl = 1 if math.sin(lt * 3.3) > 0 else -1
            Q(c, 700, 905, HX_, XYn, 1, 'idle', lt, eye='dot2', brow='worried', mouth='flat', flags=False)
            Q(c, 1250, 905 - 25 * abs(math.sin(sp)), HY_, YJ, fl, 'stand', lt, eye='lady', mouth='lips', sf=2.1 + 0.5 * math.sin(sp), ef=2.3 + 0.5 * math.sin(sp), w=2.4 + 0.5 * math.sin(sp),
              sb=-1.9 - 0.4 * math.cos(sp), eb=-2.3, lean=-0.1 * math.sin(sp), hf=0.15 + 0.35 * max(0, math.sin(sp)), kf=-0.15)
        elif lt < t2:                                                          # 走近 → 相拥
            k = sm((lt - t1) / 0.5)
            Q(c, 700 + 90 * k, 905, HX_, XYn, 1, 'stand', lt, eye='closed' if k > 0.9 else 'dot2', brow='worried', mouth='flat', flags=False, sf=0.25 + 1.3 * k, ef=0.5 + 0.2 * k, sb=-0.2, eb=0.3, lean=0.08)
            Q(c, 1250 - 280 * k, 905, HY_, YJ, -1, 'stand' if k > 0.99 else 'walk', lt, eye='closed' if k > 0.9 else 'lady', mouth='lips', sf=1.4 * k, ef=0.4 * k + 1.2 * (1 - k), sb=1.2 * k, eb=0.6 * k, lean=0.08, w=0.4)
        elif lt < t3:                                                          # 退开一步，举剑
            k = sm((lt - t2) / 0.25)
            Q(c, 790, 905, HX_, XYn, 1, 'stand', lt, sf=1.3, ef=1.1, sb=-0.2, eb=0.3, eye='shock', brow='worried', mouth='o', flags=False, fx=('shocklines',))
            Q(c, 1000 + 70 * k, 905, HY_, dict(YJ, weapon=None), 1, 'stand', lt, eye='closed', mouth='lips', sf=2.2 * k + 0.4 * (1 - k), ef=-0.9 * k + 0.8 * (1 - k), w=-2.84, hd=0.15 * k)
        else:                                                                  # 倒入怀中：跪地抱住，闭眼落泪
            f2 = sm((lt - t3) / 0.5)
            Q(c, 700, 905, HX_, XYn, 1, 'kneel', lt, sf=1.5, ef=1.2, sb=1.0, eb=0.5, lean=0.22, hd=0.45, eye='closed', brow='worried', mouth='wavy', flags=False, fx=('tear',), arm_back=True)
            fx_ = 1070 + 130 * f2; th = -1.15 * f2
            c.save(); c.translate(fx_, 905); c.rotate(th); c.translate(-fx_, -905)
            Q(c, fx_, 905, HY_, dict(YJ, weapon=None), 1, 'stand', lt, eye='closed', mouth='lips', sf=0.4 * (1 - f2) + th, ef=0.6 * (1 - f2) + th, sb=-0.3 + th * 0.5, eb=th * 0.5, hd=-0.25 * f2, lean=0.0)
            c.restore()
    def tp(c):
        if t2 <= lt < t3:                                                      # 剑光横在颈前
            k = sm((lt - t2) / 0.25)
            J, P, S = Q(layer_dummy(), 1000 + 70 * k, 905, HY_, dict(YJ, weapon=None), 1, 'stand', lt, sf=2.2 * k + 0.4 * (1 - k), ef=-0.9 * k + 0.8 * (1 - k), w=-2.84)
            hx, hy, dx, dy = hand_w(J, P, S); blade(c, hx, hy, dx, dy, 0.4 * S * k, glow=k, w=7)
        if lt >= t3:                                                           # 剑落地，花钿飘落
            c.save(); c.translate(1330, 905); c.rotate(-0.06); B_sword(c, 0, 0, 150); c.restore()
            fy = min(898, 600 + (lt - t3) * 190); flower(c, 1210 + 35 * math.sin((lt - t3) * 4), fy, 9, (lt - t3) * 2)
        snow(c, lt)
    fl = (t2, t3) if lt >= t3 else (t2,) if lt >= t2 else ()
    return compose(d, 'night', under=lambda c: camp(c, lt), top=tp, glow=(960, 850, 320, (1.0, 0.55, 0.2), 0.42), Xo=X, lt=lt, fade_in=0.4, flashes=(0,) + fl, zoom=1 + 0.06 * lt / dur, cy=820,
                   gray=0.35 * sm((lt - t3) / 0.6), mul=(1 - 0.25 * ease((lt - dur + 0.6) / 0.6),) * 3)


_DUM = {}


def layer_dummy():
    if 'c' not in _DUM: s_ = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4); _DUM['c'] = cairo.Context(s_)
    return _DUM['c']


def B_sword(c, x, y, L):
    c.save(); c.translate(x, y)
    c.move_to(0, -4); c.line_to(L, -5); c.line_to(L + 14, 0); c.line_to(L, 5); c.line_to(0, 4); c.close_path(); c.set_source_rgb(0.85, 0.88, 0.95); c.fill_preserve(); c.set_source_rgb(0.1, 0.08, 0.08); c.set_line_width(2.5); c.stroke()
    c.rectangle(-6, -14, 8, 28); c.set_source_rgb(0.85, 0.66, 0.22); c.fill(); c.rectangle(-36, -4, 30, 8); c.set_source_rgb(0.3, 0.15, 0.08); c.fill(); c.restore()


# ================================================================ 乌江：交出乌骓 → 回身迎敌 → 剪影自刎 → 跪地、去色
def wujiang(lt, dur, t):
    seg = min(2, int(lt // BAR)); l_ = lt - seg * BAR; X = Txt(True)
    if seg == 0: X.V('乌江', 170, 330, 230 * (1 + 0.4 * (1 - eout(l_ / 0.16))), fill=(255, 200, 140), stroke=10, a=ease(l_ / 0.08)); sub(X, '只剩二十八骑，退到江边', l_ - 0.15, dark=True)
    elif seg == 1: X.T('“天之亡我，我何渡为！”', W / 2, 120, 80, fill=(255, 210, 150), stroke=9, a=ease(l_ / 0.12)); sub(X, '把乌骓交给亭长，回身迎敌', l_ - 0.15, dark=True)
    else: X.V('自刎', 190, 330, 260 * (1 + 0.4 * (1 - eout(l_ / 0.16))), fill=(240, 228, 220), stroke=11, a=ease(l_ / 0.08)); sub(X, '项羽，时年三十一', l_ - 0.2, dark=True)
    XH_ = 430
    def under(c):
        c.set_source_rgb(0.66, 0.58, 0.44); c.move_to(640, 770); c.curve_to(1100, 720, 1600, 730, W, 700); c.line_to(W, H); c.line_to(700, H); c.close_path(); c.fill_preserve()
        c.set_source_rgb(0.1, 0.08, 0.08); c.set_line_width(4); c.stroke()
        reeds(c, 1550, 1920, 780, 200, 5, lt, a=0.6)
        if seg < 2: boat(c, 470, 805, 470)
    def soldiers(c, x0):
        for j in range(5): Q(c, x0 + j * 105, 905 - (j % 2) * 26, 270, HAN, -1, 'stand', lt + j, eye='shock', brow='worried', mouth='o', w=2.3, sf=1.4, ef=1.5)
    st = {}
    def d(c):
        if seg == 0:
            Q(c, 460, 805, 300, TZ, 1, 'idle', lt, eye='dot', brow='worried', mouth='flat')
            qhorse.horse(c, 1520, 905, 320, (0.16, 0.17, 0.22), -1, lt, 'stand', head_a=0.2)
            Q(c, 1180, 905, XH_, XY, -1, 'stand', lt, eye='dot2', brow='angry', mouth='grit', flags=False)
        elif seg == 1:
            k = sm(l_ / 1.0); turn = l_ > 1.15
            hx = 1260 - 300 * k
            qhorse.horse(c, hx, 885, 320, (0.16, 0.17, 0.22), -1, lt, 'walk' if 0.02 < k < 0.98 else 'stand', head_a=0.15)
            J, P, S = Q(c, 760, 860, 320, TZ, 1, 'point', lt, eye='dot', brow='worried', mouth='o', sf=1.25, ef=1.2)
            st['rein'] = (RG.to_world(P, S, J['hdf']), (hx - 0.86 * 320, 885 - 1.2 * 320))
            if not turn: Q(c, 1430 - 200 * k, 905, XH_, XYn, -1, 'stand', lt, eye='dot2', brow='worried', mouth='flat', flags=False, sf=1.5, ef=1.4, w=1.4)
            else:
                Q(c, 1230, 905, XH_, XY, 1, 'stand', lt, eye='fierce', brow='angry', mouth='grit', flags=False, sf=1.0, ef=1.6, w=1.9, lean=0.1)
                soldiers(c, 2000 - 260 * sm((l_ - 1.15) / 0.4))
        else:
            soldiers(c, 1740)
            if l_ < 0.75:
                J, P, S = Q(c, 1150, 905, XH_, XYn, 1, 'stand', lt, sf=2.2, ef=-0.9, w=-1.75, hd=0.2, lean=-0.05, eye='closed', brow='flat', mouth='flat', flags=False)
                st['bl'] = hand_w(J, P, S) + (S,)
            else: Q(c, 1150, 905, XH_, XYn, 1, 'kneel', lt, eye='closed', brow='flat', mouth='flat', flags=False, hd=0.5, lean=0.2, sf=1.25, ef=1.45, sb=0.3, eb=0.2)
    def tp(c):
        if 'rein' in st and l_ < 1.15:
            (a1, a2) = st['rein']; c.move_to(*a1); c.curve_to(a1[0] + 80, a1[1] + 60, a2[0] - 60, a2[1] + 60, *a2); c.set_source_rgb(0.75, 0.15, 0.1); c.set_line_width(5); c.stroke()
        if 'bl' in st: hx, hy, dx, dy, S = st['bl']; blade(c, hx, hy, dx, dy, 0.44 * S, glow=1.0, w=8)
        if seg == 2 and l_ >= 0.75: c.save(); c.translate(1262, 912); c.rotate(-PI / 2 - 0.06); B_sword(c, 0, 0, 170); c.restore()
        reeds(c, 900, 1700, 1090, 240, 7, lt)
    if seg < 2:
        d(layer_dummy()) if False else None
        return compose(d, 'dusk', under=under, top=tp, Xo=X, lt=lt, flashes=(0, BAR), zoom=1 + 0.03 * l_, cx=1100, cy=760)
    k = ease(l_ / 0.25); gk = ease((l_ - 0.75) / 0.8)
    return compose(d, 'dusk', under=under, top=tp, Xo=X, lt=l_, flashes=(0, 0.75), glow=(1150, 600, 360, (1.0, 0.6, 0.25), 0.7 * k), sil=((0.06, 0.04, 0.04), k * (1 - 0.14 * gk)), gray=0.65 * gk, mul=(1 - 0.3 * gk,) * 3, zoom=1.04 + 0.04 * l_, cx=1180, cy=700)


def breakout(lt, dur, t):
    fr = breakout_frame(lt); fr = fr + np.float32([1, 0.9, 0.75]) * 0.5 * math.exp(-lt / 0.08)
    X = Txt(True); sz = 200 * (1 + 0.5 * (1 - eout(lt / 0.16)))
    X.T('八百骑', 1580, 150, sz, fill=(150, 200, 255), stroke=11, a=ease(lt / 0.06)); sub(X, '项羽 夜里杀出重围', lt - 0.25, dark=True)
    return X.over(to_img(fr + grain(0.02)))


SHOTS = [(0, T_A, hook), (T_A, PB0, map_shot), (PB0, R1, pengcheng), (R1, HP, map_shot), (HP, HQ, hanxin), (HQ, J0, map_shot),
         (J0, J1, lambda lt, dur, t: O.jingxing(lt, dur, t, tF=1.25 * BAR)), (J1, WS0, map_shot), (WS0, WS1, lambda lt, dur, t: O.weishui(lt, dur, t, tF=BAR)),
         (WS1, E1, map_shot), (E1, CS1, renyong), (CS1, G0, map_shot), (G0, G1, ring), (G1, BJ0, map_shot), (BJ0, D2, bieji), (D2, M5, breakout),
         (M5, W0, map_shot), (W0, F0, wujiang), (F0, T_END, map_shot)]

if __name__ == '__main__':
    from mapwar.film import Film
    if sys.argv[1:2] == ['times']:
        for k in ('T_A', 'PB0', 'INS0', 'D1', 'INS1', 'R1', 'HP', 'BJ0', 'D2', 'W0', 'F0', 'T_END'): print(k, round(globals()[k], 3))
    else: Film(SHOTS, T_END, audio=os.environ.get('MAPWAR_AUDIO'), fade_out=1.5).cli()
