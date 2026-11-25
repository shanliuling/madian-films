"""共用：时间线、合成、气泡、字幕、名单 HUD。"""
import os, sys, json, math
KIT = '/home/ubuntu/kunyang/zhanju-kit'
if KIT not in sys.path: sys.path.insert(0, KIT)
import numpy as np, cairo, cv2
from PIL import Image
from mapwar.util import SW, SH, cl, ease, eout, hsh, to_img, Txt, VR, grain, font
from mapwar.scenery import landscape
from mapwar import qrig as RG
import mcast as C
from script import T0, B, BAR, TOTAL, T_DROP2, T_NIGHT, T_BAG, T_DY, T_CANNON

HERE = os.path.dirname(os.path.abspath(__file__))
TLL = json.load(open(os.path.join(HERE, 'vo', 'timeline.json'), encoding='utf-8'))
TL = {L['id']: L for L in TLL}
st = lambda i: TL[i]['t']
en = lambda i: TL[i]['t'] + TL[i]['d']
OL = (0.09, 0.08, 0.08); TAU = 2 * math.pi
W, H = SW, SH
CAM = [1.0, W / 2, H / 2]


def cam_pt(p): z, cx, cy = CAM; return ((p[0] - cx) * z + cx, (p[1] - cy) * z + cy)

# ---- 关键时刻
T_YH = en('a4') - 0.45                    # 野狐岭：骑兵撞阵（「全崩」）
C_YH0, C_YH1 = T_YH - 0.85, T_YH + 1.95   # 野狐岭战场镜头
T_BG = st('d5') + 2.45                    # 巴格达：城墙被砸塌（「陷落」）
C_BG0, C_BG1 = T_BG - 0.70, T_BG + 2.20   # 巴格达攻城镜头
T_FEINT = st('c6') - 0.35                 # 罗斯：佯退开始
T_TURN = st('c3') - 0.05                  # 回头反杀
C_BQ0 = st('c3') + 2.10                   # 木板宴
C_JIN1 = st('a4') + 0.12                  # 金使小剧场结束
C_CA2 = st('d5') - 0.16                   # 哈里发小剧场结束
# 四个「惹了蒙古」的 + 钓鱼城：(名, 开始点名, 下场时刻)
T_END1, T_END2, T_END3, T_END4 = C_YH1 + 1.0, en('b5') + 0.12, st('c3') + 0.85, T_BG + 0.55
CHIPS = [('金国', B(2) - 0.4, T_END1), ('花剌子模', B(9), T_END2), ('罗斯', T_NIGHT, T_END3), ('巴格达', T_BAG, T_END4)]


def layer(draw):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); draw(c)
    return np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32) / 255


def over(fr, A): return A[..., [2, 1, 0]] + fr * (1 - A[..., 3:4])


def fs(c, col, lw=4.0, a=1.0):
    if len(col) == 4: c.set_source_rgba(*col)
    else: c.set_source_rgba(*col, a)
    c.fill_preserve(); c.set_source_rgba(*OL, a); c.set_line_width(lw); c.stroke()


def rr(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2); c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()


def scene(bg, draw, lt, t, under=None, mul=None, zoom=1.0, cx=W / 2, cy=H / 2, shake=0.0, flash=0.0, punch=True, tint=None, dark=0.0):
    """背景 → under → 人物 → 调色。返回 float 帧。"""
    CAM[:] = [zoom, cx, cy]
    if punch: zoom = zoom * (1 + 0.07 * (1 - eout(lt / 0.28)))
    def cam(fn):
        def d(c):
            if shake: c.translate(shake * math.sin(t * 83), shake * math.sin(t * 67 + 1))
            if zoom != 1.0: c.translate(cx, cy); c.scale(zoom, zoom); c.translate(-cx, -cy)
            fn(c)
        return d
    Bg = landscape(bg) if isinstance(bg, str) else bg
    if zoom != 1.0:
        M = np.float32([[zoom, 0, cx * (1 - zoom)], [0, zoom, cy * (1 - zoom)]]); Bg = cv2.warpAffine(Bg, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if tint is not None: Bg = Bg * np.float32(tint)
    if under is not None: Bg = over(Bg, layer(cam(under)))
    fr = over(Bg, layer(cam(draw)))
    if mul is not None: fr = fr * np.float32(mul)
    if dark: fr = fr * (1 - dark)
    fr = fr * (1 - 0.30 * VR)
    if flash: fr = fr + np.float32([1, 0.96, 0.88]) * flash
    if punch and lt < 0.2: fr = fr + np.float32([1, 0.96, 0.88]) * 0.35 * (1 - lt / 0.2)
    return fr + grain(0.02)


def finish(fr, X): return X.over(to_img(fr))


# ---------------------------------------------------------------- 文字零件
def bubble(X, s, cx, cy, tail=None, lt=1.0, size=62, fill=(255, 255, 255), ink=(24, 20, 18), a=1.0):
    k = 0.55 + 0.45 * eout(lt / 0.12, 3) + 0.06 * math.sin(min(1, lt / 0.25) * math.pi); sz = int(size * k)
    f = font(sz); l, tp, r, b = X.d.textbbox((cx, cy), s, font=f, anchor='mm'); px, py = sz * 0.55, sz * 0.42; al = int(255 * cl(a) * ease(lt / 0.06))
    box = [l - px, tp - py, r + px, b + py]
    if tail:
        tx, ty = tail; bx = min(max(tx, box[0] + 50), box[2] - 50); by = box[3] if ty > cy else box[1]; w_ = 26 * k
        X.d.polygon([(bx - w_, by + (-6 if ty > cy else 6)), (bx + w_, by + (-6 if ty > cy else 6)), (bx + (tx - bx) * 0.55, by + (ty - by) * 0.55)], fill=tuple(fill) + (al,), outline=tuple(ink) + (al,), width=5)
    X.d.rounded_rectangle(box, radius=sz * 0.6, fill=tuple(fill) + (al,), outline=tuple(ink) + (al,), width=6)
    if tail: X.d.polygon([(bx - w_ + 6, by + (-9 if ty > cy else 9)), (bx + w_ - 6, by + (-9 if ty > cy else 9)), (bx + (tx - bx) * 0.42, by + (ty - by) * 0.42)], fill=tuple(fill) + (al,))
    X.d.text((cx, cy), s, font=f, fill=tuple(ink) + (al,), anchor='mm')


def say(X, t, lid, cx, cy, tail=None, size=62, hold=0.25, text=None, **kw):
    L = TL[lid]
    if L['t'] - 0.03 <= t <= L['t'] + L['d'] + hold: bubble(X, text or L['sub'], cx, cy, tail, t - L['t'] + 0.03, size, **kw); return True
    return False


def talking(t, lid, pad=0.0): return TL[lid]['t'] <= t <= TL[lid]['t'] + TL[lid]['d'] + pad


def mouth_of(t, lid, a='shout', b='smile', rest='flat'): return (a if int(t * 10) % 2 else b) if talking(t, lid) else rest


def subtitle(X, t):
    for L in TLL:
        if L['who'] != 'N': continue
        if L['t'] - 0.05 <= t <= L['t'] + L['d'] + 0.15:
            al = ease((t - (L['t'] - 0.05)) / 0.1) * (1 - ease((t - (L['t'] + L['d'])) / 0.15)); s = L['sub']
            l, tp, r, b = X.d.textbbox((W / 2, 972), s, font=font(56), anchor='mm')
            X.d.rounded_rectangle([l - 44, 926, r + 44, 1018], radius=16, fill=(12, 14, 20, int(205 * al)))
            X.T(s, W / 2, 972, 56, fill=(255, 250, 236), stroke=0, a=al); return


def chips(X, t, dark=False):
    """左上角「惹蒙古名单」：点到名的亮起，下场后盖『亡』。"""
    if t < T0: return
    x0, y0, cw, ch, gap = 56, 92, 214, 74, 14
    X.T('惹 了 蒙 古 的', x0 + 4, 52, 44, fill=(255, 226, 150) if dark else (150, 28, 18), anchor='lm', stroke=5)
    items = list(CHIPS) + ([('钓鱼城', T_DY, 1e9)] if t >= T_DY else [])
    for i, (nm, ta, td) in enumerate(items):
        ap = T0 + 0.6 + i * 0.4 if i < 4 else T_DY + 0.3
        if t < ap: continue
        k = eout((t - ap) / 0.18, 3); x = x0 + i * (cw + gap); y = y0 + (1 - k) * -30
        done = t >= td; act = ta <= t < td; special = i == 4
        if special: fill, outl, txt = (30, 80, 130, 235), (140, 210, 255, 255), (235, 248, 255)
        elif done: fill, outl, txt = (60, 56, 54, 215), (120, 112, 104, 255), (170, 162, 150)
        elif act: fill, outl, txt = (168, 26, 18, 240), (255, 214, 120, 255), (255, 244, 220)
        else: fill, outl, txt = ((40, 40, 48, 190), (150, 150, 160, 220), (215, 210, 200)) if dark else ((240, 230, 208, 215), (110, 96, 80, 230), (60, 48, 40))
        pulse = 4 * math.sin(t * 9) if act else 0
        X.d.rounded_rectangle([x - pulse / 2, y - pulse / 2, x + cw + pulse / 2, y + ch + pulse / 2], radius=14, fill=fill, outline=outl, width=4)
        X.T(('①②③④'[i] if i < 4 else '★') + ' ' + nm, x + cw / 2, y + ch / 2 + 1, 40 if len(nm) < 4 else 34, fill=txt, stroke=0, a=k)
        if done and not special:
            u = t - td; sz = 58 * (1 + 0.9 * (1 - eout(u / 0.16)))
            X.d.line([x + 10, y + ch - 12, x + cw - 10, y + 12], fill=(220, 30, 22, 255), width=7)
            X.T('亡', x + cw - 34, y + ch / 2, sz, fill=(232, 36, 26), stroke=5, halo=(255, 240, 220))
        if special and t >= T_CANNON:
            X.T('守住', x + cw / 2, y + ch + 30, 40, fill=(255, 226, 120), stroke=5, halo=(20, 30, 50))


def stamp(X, s, t, t0, x=W / 2, y=500, size=190, hold=1.6, sub=None):
    """红色大印章字砸下。"""
    u = t - t0
    if u < 0 or u > hold: return
    k = 1 + 0.9 * (1 - eout(u / 0.14)); a = ease(u / 0.05) * (1 - ease((u - hold + 0.18) / 0.18)); sz = int(size * k)
    f = font(sz); l, tp, r, b = X.d.textbbox((x, y), s, font=f, anchor='mm'); al = int(255 * a)
    X.d.rounded_rectangle([l - 46, tp - 34, r + 46, b + 34], radius=22, fill=(250, 240, 222, int(215 * a)), outline=(200, 26, 18, al), width=14)
    X.T(s, x, y, sz, fill=(200, 26, 18), stroke=0, a=a)
    if sub: X.T(sub, x, b + 84, 54, fill=(255, 244, 220), stroke=7, halo=(40, 10, 8), a=a * ease((u - 0.15) / 0.15))


def poof(c, x, y, u, s=1.0, col=(0.93, 0.91, 0.86)):
    """一团烟：u 0..1。"""
    if u <= 0 or u >= 1: return
    for k in range(7):
        a = k / 7 * TAU + 0.4; r = (38 + 70 * eout(u)) * s; rad = (46 * (1 - u) + 14) * s * (0.8 + 0.4 * hsh(k, 3))
        c.arc(x + math.cos(a) * r, y + math.sin(a) * r * 0.7, rad, 0, TAU); fs(c, col, 3.5, a=1 - u ** 2)
    c.arc(x, y, 60 * s * (1 - u), 0, TAU); fs(c, col, 3.5, a=1 - u)


def impact_lines(c, x, y, u, n=18, r0=120, r1=420, col=(1, 0.95, 0.75)):
    if u <= 0 or u >= 1: return
    c.set_source_rgba(*col, 1 - u); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(n):
        a = k / n * TAU + hsh(k) * 0.3; a0 = r0 + (r1 - r0) * eout(u) * 0.6; a1 = a0 + (90 + 110 * hsh(k, 2)) * (1 - u * 0.5)
        c.set_line_width(10 * (1 - u) + 3); c.move_to(x + math.cos(a) * a0, y + math.sin(a) * a0); c.line_to(x + math.cos(a) * a1, y + math.sin(a) * a1); c.stroke()


def zoomblur(fr, k, n=7, cx=W / 2, cy=H / 2):
    """径向推镜模糊：k 0..0.4。"""
    if k <= 0.003: return fr
    acc = fr.copy()
    for i in range(1, n):
        z = 1 + k * i / (n - 1); M = np.float32([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]])
        acc += cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return acc / n


def tag(X, s, dark=False): X.T(s, 62, 226, 46, fill=(255, 236, 200) if dark else (60, 44, 34), anchor='lm', stroke=5)
