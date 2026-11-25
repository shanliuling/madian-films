"""蛋蛋人小剧场：七段。每个函数 (lt, dur, t) -> PIL.Image，t 是全片时间。"""
import math
import numpy as np, cairo
from common import *
from mapwar.qchar import Q
from mapwar import scenery as SC
PI = math.pi


def wpos(J, P, S, key='head'): return cam_pt(RG.to_world(P, S, J[key]))
Z = dict(zoom=1.16, cy=760)


def tag(X, s, dark=False): X.T(s, 62, 226, 46, fill=(255, 236, 200) if dark else (60, 44, 34), anchor='lm', stroke=5)


def yurt(c, x, y, w):
    h = w * 0.55; c.move_to(x - w, y); c.line_to(x - w, y - h); c.curve_to(x - w * 0.6, y - h * 1.9, x + w * 0.6, y - h * 1.9, x + w, y - h); c.line_to(x + w, y); c.close_path(); fs(c, (0.94, 0.91, 0.84), 4)
    c.rectangle(x - w, y - h - 8, 2 * w, 16); fs(c, (0.72, 0.16, 0.12), 3); rr(c, x - w * 0.2, y - h * 0.85, w * 0.4, h * 0.85, 8); fs(c, (0.62, 0.20, 0.12), 3.5)
    c.arc(x, y - h * 1.6, w * 0.12, 0, TAU); fs(c, (0.72, 0.16, 0.12), 3)


def hat_drop(c, x, y, u, col=(0.72, 0.12, 0.10), s=1.0):
    """帽子从半空掉到地上。u: 0 开始掉。"""
    if u < 0: return
    yy = y - 260 * s * (1 - min(1, u / 0.35) ** 2) + (abs(math.sin(u * 14)) * 22 * math.exp(-u * 5) if u > 0.35 else 0)
    c.save(); c.translate(x, yy); c.rotate(0.25 * math.sin(min(u, 0.6) * 9)); c.scale(s, s)
    c.move_to(-62, 0); c.line_to(0, -84); c.line_to(62, 0); c.close_path(); fs(c, col, 4)
    rr(c, -74, -16, 148, 30, 14); fs(c, (0.42, 0.28, 0.16), 4); c.restore()


def chest(c, x, y, s=1.0, open_=False):
    rr(c, x - 60 * s, y - 70 * s, 120 * s, 70 * s, 8 * s); fs(c, (0.55, 0.34, 0.16), 4)
    c.rectangle(x - 60 * s, y - 50 * s, 120 * s, 10 * s); fs(c, (0.92, 0.74, 0.28), 3); c.arc(x, y - 40 * s, 9 * s, 0, TAU); fs(c, (0.92, 0.74, 0.28), 3)
    if open_:
        for k in range(5): c.arc(x - 40 * s + k * 20 * s, y - 76 * s - (k % 2) * 8 * s, 13 * s, 0, TAU); fs(c, (0.98, 0.82, 0.25), 3)


def coin(c, x, y, r=16, a=1.0):
    c.arc(x, y, r, 0, TAU); fs(c, (0.98, 0.82, 0.25), 3, a); c.arc(x, y, r * 0.45, 0, TAU); c.set_source_rgba(0.75, 0.55, 0.12, a); c.set_line_width(3); c.stroke()


def gold_heap(c, x, y, w, h):
    c.move_to(x - w, y); c.curve_to(x - w * 0.7, y - h * 1.2, x + w * 0.7, y - h * 1.2, x + w, y); c.close_path(); fs(c, (0.93, 0.74, 0.20), 5)
    for k in range(34):
        u, v = hsh(k, 1) * 2 - 1, hsh(k, 2); px = x + u * w * 0.85; top = y - h * 0.9 * (1 - u * u); coin(c, px, y - 10 - v * (y - 10 - top - 10), 15)


# ================================================================ ① 金使：跪下接旨 → 我呸
def jin(lt, dur, t):
    X = Txt(False); pos = {}
    ex = 1270 + 520 * (1 - eout(lt / 0.9)); spit0 = st('a3') + 0.12; u_sp = (t - spit0) / 0.20; hit = u_sp >= 1

    def under(c):
        for (x, w) in ((250, 150), (1660, 190), (960, 100)): yurt(c, x, 742, w)
        SC.grass(c, 0, W, 800, 1000, n=70, seed=3, t=t)

    def d(c):
        if t >= st('a3') - 0.05: kw = dict(lean=0.32 * (1 - cl((t - spit0 - 0.25) / 0.3)), eye='fierce', brow='angry', mouth='o' if u_sp < 1.3 else 'smirk')
        elif t >= st('a2'): kw = dict(eye='dot', brow='angry', mouth='grit', fx=('anger',))
        else: kw = dict(eye='dot', brow='flat', mouth='flat')
        J, P, S = Q(c, 640, 870, 450, C.TMZ, 1, 'fold', t, **kw); pos['t'] = wpos(J, P, S); pos['t0'] = RG.to_world(P, S, J['head'])
        if hit: kw = dict(eye='shock', brow='raised', mouth='o', fx=('shocklines', 'sweat'), lean=-0.22)
        elif talking(t, 'a2'): kw = dict(eye='fierce', brow='angry', mouth=mouth_of(t, 'a2', 'shout', 'o'), sf=1.9, ef=1.9, lean=0.12)
        else: kw = dict(eye='closed', brow='raised', mouth='smirk', lean=-0.06)
        J, P, S = Q(c, ex, 870, 440, C.JSZ, -1, 'point' if lt > 0.9 else 'walk', t, **kw); pos['e'] = wpos(J, P, S); pos['e0'] = RG.to_world(P, S, J['head'])
        if 0 <= u_sp < 1:                                                       # 唾沫
            (x0, y0), (x1, y1) = pos['t0'], pos['e0']; x0 += 95; y0 += 40; x1 -= 70; y1 += 10
            for k in range(3):
                u = cl(u_sp - k * 0.08); px = x0 + (x1 - x0) * u; py = y0 + (y1 - y0) * u - 90 * math.sin(u * PI)
                c.save(); c.translate(px, py); c.scale(1.5, 0.9); c.arc(0, 0, 13 - k * 3, 0, TAU); c.restore(); fs(c, (0.80, 0.93, 1.0), 3)
        if hit:
            x1, y1 = pos['e0']; u = t - spit0 - 0.20
            for k in range(6): a = k / 6 * TAU; r = 30 + 160 * eout(u / 0.3); c.arc(x1 - 60 + math.cos(a) * r, y1 + 10 + math.sin(a) * r * 0.8 + 300 * u * u, 9, 0, TAU); fs(c, (0.80, 0.93, 1.0), 2.5, a=1 - cl(u / 0.5))

    fr = scene('day', d, lt, t, under=under, **Z, shake=10 * math.exp(-(t - spit0 - 0.2) * 9) if hit else 0)
    chips(X, t); tag(X, '1210 年 · 蒙古草原'); subtitle(X, t)
    if lt > 1.0 and t < st('a2') - 0.1: X.T('金国使者', pos['e'][0], pos['e'][1] - 260, 44, fill=(130, 88, 12), stroke=6); X.T('铁木真', pos['t'][0], pos['t'][1] - 290, 44, fill=(165, 22, 18), stroke=6)
    say(X, t, 'a2', pos['e'][0] - 60, pos['e'][1] - 330, (pos['e'][0] - 40, pos['e'][1] - 150), size=78, hold=0.05)
    say(X, t, 'a3', pos['t'][0] + 60, pos['t'][1] - 350, (pos['t'][0] + 40, pos['t'][1] - 170), size=96, hold=0.5)
    return finish(fr, X)


# ================================================================ ② 花剌子模：杀商队 → 发财啦 → 剃胡子
def _town(c):
    c.rectangle(0, 470, W, 300); fs(c, (0.86, 0.72, 0.50), 5)
    for k in range(17): c.rectangle(k * 120 - 10, 430, 70, 44); fs(c, (0.86, 0.72, 0.50), 5)
    c.move_to(1500, 770); c.line_to(1500, 600); c.curve_to(1500, 500, 1700, 500, 1700, 600); c.line_to(1700, 770); c.close_path(); fs(c, (0.30, 0.20, 0.14), 5)
    c.arc(420, 430, 120, PI, TAU); c.close_path(); fs(c, (0.25, 0.62, 0.62), 5); c.arc(420, 300, 16, 0, TAU); fs(c, (0.92, 0.74, 0.28), 3)


def khwarazm(lt, dur, t):
    X = Txt(False); pos = {}
    tk = st('b1') + 3.25; uk = t - tk; tb = st('b3') - 0.25; k1 = st('b6') + 0.8; k2 = st('b6') + 2.0
    phaseB = t >= tb

    def d(c):
        gx = 1330
        if not phaseB:
            slide = eout(uk / 0.5) if uk > 0 else 0
            for i, x in enumerate((860, 980)): chest(c, x + (gx - 250 - 860) * slide, 870 - (i * 0), 1.1, open_=uk > 0.5)
            if uk < 0:
                for i, x in enumerate((330, 500, 670)): Q(c, x, 870, 350, (C.MGB, C.MGB2, C.MGB3)[i], 1, 'idle', t + i, eye='happy', mouth='smile')
            else:
                for i, x in enumerate((330, 500, 670)): poof(c, x, 700, (uk - i * 0.05) / 0.55, 1.3); hat_drop(c, x, 866, uk - 0.1 - i * 0.05)
                if uk < 0.25:
                    c.set_source_rgba(1, 1, 1, 1 - uk / 0.25); c.set_line_width(26); c.move_to(180, 520); c.line_to(820, 820); c.stroke()
            if talking(t, 'b2', 0.4): kw = dict(eye='happy', brow='raised', mouth=mouth_of(t, 'b2', 'shout', 'smile', 'smile'), dy=-70 - 26 * abs(math.sin(t * 9)))
            elif uk > 0: kw = dict(eye='glint', brow='raised', mouth='smile')
            else: kw = dict(eye='glint', brow='angry', mouth='smirk')
            J, P, S = Q(c, gx, 870, 430, C.SJ, -1, 'cheer' if talking(t, 'b2', 0.4) else 'fold', t, **kw); pos['g'] = wpos(J, P, S)
            if talking(t, 'b2', 0.4):
                for k in range(16):
                    u = ((t - st('b2')) * 0.9 + hsh(k, 5)) % 1; coin(c, gx - 420 + hsh(k) * 620, 380 + u * 480, 17, a=1 - u * 0.5)
        else:
            for x in (1010, 1130): chest(c, x, 870, 1.1, open_=True)
            J, P, S = Q(c, gx, 870, 430, C.SJ, -1, 'point' if k1 - 0.25 < t < k1 + 0.4 or k2 - 0.3 < t < k2 + 0.3 else 'fold', t,
                        eye='closed' if t > k2 + 0.3 else 'fierce', brow='angry', mouth='smile' if t > k2 + 0.3 else 'smirk'); pos['g'] = wpos(J, P, S)
            walk = cl((t - tb) / 0.9)
            for i, (x1, sp) in enumerate(((620, C.MGB3), (450, C.MGB2), (790, C.TMZ))):
                x = x1 - 700 * (1 - eout(walk)); nm = 'walk' if walk < 1 else 'stand'
                if i == 2:                                                      # 领头的：被砍
                    sp = dict(C.MGB, beard='goatee', head='square')
                    if t < k1: J, P, S = Q(c, x, 870, 370, sp, 1, nm if walk < 1 else 'point', t, eye='fierce', brow='angry', mouth=mouth_of(t, 'b3', 'shout', 'o')); pos['l'] = wpos(J, P, S)
                    else: poof(c, x, 690, (t - k1) / 0.55, 1.4); hat_drop(c, x, 866, t - k1 - 0.1)
                    if 0 <= t - k1 < 0.22: c.set_source_rgba(1, 1, 1, 1 - (t - k1) / 0.22); c.set_line_width(26); c.move_to(x - 200, 480); c.line_to(x + 200, 860); c.stroke()
                else:
                    shaved = t >= k2
                    if shaved: sp = dict(sp, beard='stubble'); kw = dict(eye='shock' if t < st('b7') else 'squeeze', brow='worried', mouth='o' if not talking(t, 'b7') or i else mouth_of(t, 'b7', 'shout', 'o'), fx=('tear',) if t >= st('b7') - 0.1 else ('shocklines',))
                    elif t >= k1: kw = dict(eye='shock', brow='raised', mouth='o', fx=('sweat',))
                    else: kw = dict(eye='dot', brow='angry', mouth='flat')
                    J, P, S = Q(c, x, 870, 360, sp, 1, nm, t + i, **kw); pos['e%d' % i] = wpos(J, P, S)
                    if shaved:
                        u = t - k2; hx, hy = RG.to_world(P, S, J['head'])
                        for k in range(9):                                      # 胡子渣飞出去
                            a = -0.4 + hsh(k, i) * 1.6; r = 240 * eout(u / 0.5); px = hx + 40 + math.cos(a) * r; py = hy + 70 + math.sin(a) * r * 0.5 + 500 * u * u
                            c.save(); c.translate(px, py); c.rotate(u * 9 + k); c.rectangle(-16, -4, 32, 8); c.set_source_rgba(0.08, 0.07, 0.07, 1 - cl(u / 0.9)); c.fill(); c.restore()
                        if u < 0.2: c.set_source_rgba(1, 1, 1, 1 - u / 0.2); c.set_line_width(18); c.move_to(hx - 60, hy + 150); c.line_to(hx + 150, hy + 20); c.stroke()

    sh = 12 * math.exp(-uk * 8) if (uk > 0 and not phaseB) else 12 * math.exp(-(t - k1) * 8) if t > k1 else 0
    fr = scene('dusk', d, lt, t, under=_town, **Z, shake=sh, tint=(1.12, 1.02, 0.86))
    chips(X, t); tag(X, '1218 年 · 讹答剌城'); subtitle(X, t)
    if not phaseB:
        n = 450 if uk < 0 else int(450 * (1 - eout(uk / 0.5)))
        X.T(f'蒙古商队  {n} 人', 500, 390 if uk < 0 else 520, 60, fill=(165, 22, 18), stroke=7)
        say(X, t, 'b2', pos['g'][0] - 140, pos['g'][1] - 330, (pos['g'][0] - 60, pos['g'][1] - 160), size=78, hold=0.3)
    else:
        if t < k1 and t > tb + 0.9: X.T('蒙古使者 ×3', 620, 400, 54, fill=(165, 22, 18), stroke=7)
        if 'e1' in pos: say(X, t, 'b7', pos['e1'][0] + 40, pos['e1'][1] - 300, (pos['e1'][0] + 30, pos['e1'][1] - 150), size=84, hold=0.3)
    return finish(fr, X)


# ================================================================ 成吉思汗特写：行，我亲自来
def khan(lt, dur, t):
    X = Txt(True); u = cl(lt / dur)

    def d(c):
        cx, cy, R = 960, 520, 255
        c.move_to(cx - 520, 1080); c.curve_to(cx - 480, 760, cx - 260, 700, cx, 700); c.curve_to(cx + 260, 700, cx + 480, 760, cx + 520, 1080); c.close_path(); fs(c, C.TMZ['robe'], 7)
        c.move_to(cx - 150, 705); c.line_to(cx, 900); c.line_to(cx + 150, 705); c.set_source_rgb(*C.TMZ['collar']); c.set_line_width(46); c.stroke()
        RG.head(c, cx, cy, R, dict(C.TMZ, beard='long', beardcol=(0.30, 0.28, 0.27)), dict(front=True, eye='glint' if t > en('b4') else 'fierce', brow='angry', mouth=mouth_of(t, 'b4', 'grit', 'flat', 'flat')), t)

    bg = landscape('night') * np.float32([1.5, 0.55, 0.45])
    fr = scene(bg, d, lt, t, zoom=1.0 + 0.16 * u, cy=520, mul=(1.0, 0.88, 0.82), flash=0.0)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); fr = fr + np.exp(-((xx - 960) ** 2 + (yy - 560) ** 2) / (2 * 520 ** 2))[..., None] * np.float32([0.42, 0.06, 0.03]) * (0.6 + 0.4 * math.sin(t * 5))
    chips(X, t, True); tag(X, '消息传回蒙古', True)
    if talking(t, 'b4', 0.6):
        l = t - st('b4'); X.T('行，我亲自来。', 960, 930, 110 * (1 + 0.3 * (1 - eout(l / 0.15))), fill=(255, 236, 200), stroke=10, halo=(120, 14, 8))
    X.T('成吉思汗', 300, 520, 70, fill=(255, 214, 120), stroke=7, a=ease(lt / 0.3))
    return finish(fr, X)


# ================================================================ ③ 罗斯：我们不打你 → 给我砍了
def _church(c):
    for (x, w, h) in ((1560, 150, 330), (1740, 100, 240)):
        c.rectangle(x - w / 2, 760 - h, w, h); fs(c, (0.30, 0.30, 0.38), 5)
        c.move_to(x - w * 0.62, 760 - h); c.curve_to(x - w * 0.9, 760 - h - w * 0.8, x - w * 0.1, 760 - h - w * 0.9, x, 760 - h - w * 1.3); c.curve_to(x + w * 0.1, 760 - h - w * 0.9, x + w * 0.9, 760 - h - w * 0.8, x + w * 0.62, 760 - h); c.close_path(); fs(c, (0.80, 0.62, 0.20), 5)
        c.set_source_rgb(*OL); c.set_line_width(6); c.move_to(x, 760 - h - w * 1.3); c.line_to(x, 760 - h - w * 1.7); c.move_to(x - 16, 760 - h - w * 1.55); c.line_to(x + 16, 760 - h - w * 1.55); c.stroke()


def rus(lt, dur, t):
    X = Txt(True); pos = {}; hit = en('c2') + 0.12; uh = t - hit; t_say = st('c1') + 2.35

    def d(c):
        Q(c, 1530, 860, 420, C.WG2, -1, 'stand', t + 1, eye='fierce', brow='angry', mouth='grit')
        if talking(t, 'c2', 0.5): kw = dict(eye='fierce', brow='angry', mouth=mouth_of(t, 'c2', 'shout', 'o', 'shout'), fx=('anger',), lean=0.15)
        else: kw = dict(eye='dot', brow='angry', mouth='grit')
        J, P, S = Q(c, 1300, 870, 470, C.WG, -1, 'point' if t >= st('c2') - 0.05 else 'stand', t, **kw); pos['p'] = wpos(J, P, S)
        for i, x in enumerate((560, 740)):
            if uh < 0:
                if t >= st('c2'): kw = dict(eye='shock', brow='raised', mouth='o', fx=('shocklines',))
                elif t >= t_say: kw = dict(eye='happy', brow='raised', mouth='shout' if int(t * 10) % 2 and i else 'smile')
                else: kw = dict(eye='dot', mouth='smile')
                J, P, S = Q(c, x, 870, 380, (C.MGB2, C.MGB)[i], 1, 'idle', t + i, **kw); pos['e%d' % i] = wpos(J, P, S)
            else: poof(c, x, 690, (uh - i * 0.04) / 0.5, 1.4); hat_drop(c, x, 866, uh - 0.08)
        if 0 <= uh < 0.25: c.set_source_rgba(1, 1, 1, 1 - uh / 0.25); c.set_line_width(30); c.move_to(380, 500); c.line_to(940, 830); c.stroke()
        SC.snow(c, t, 140, 4)

    fr = scene('night', d, lt, t, under=_church, **Z, shake=14 * math.exp(-uh * 8) if uh > 0 else 0, flash=0.5 * math.exp(-uh * 10) if uh > 0 else 0, mul=(1.1, 1.1, 1.2))
    chips(X, t, True); tag(X, '1223 年 · 罗斯', True); subtitle(X, t)
    if t < t_say: X.T('罗斯王公', pos['p'][0] + 40, pos['p'][1] - 330, 48, fill=(255, 226, 150), stroke=6); X.T('蒙古使者', 650 , pos['e1'][1] - 250, 48, fill=(255, 150, 130), stroke=6)
    if uh < 0 and t_say <= t < st('c2') - 0.05: bubble(X, '我们不打你～', pos['e1'][0] + 30, pos['e1'][1] - 300, (pos['e1'][0] + 20, pos['e1'][1] - 150), t - t_say, 64)
    say(X, t, 'c2', pos['p'][0] - 120, pos['p'][1] - 360, (pos['p'][0] - 50, pos['p'][1] - 180), size=100, hold=0.45)
    return finish(fr, X)


# ================================================================ ③ 木板庆功宴
def banquet(lt, dur, t):
    X = Txt(True); pos = {}; drop = eout(lt / 0.28, 2); by = 720 - 520 * (1 - drop)
    bounce = lambda k: 16 * abs(math.sin(t * 5.2 + k * 1.3)) if lt > 0.9 + k * 0.3 else 0
    press = 6 * math.sin(t * 10.4)

    def d(c):
        SC.fire(c, 150, 850, 1.6, t); SC.fire(c, 1780, 850, 1.6, t)
        for i, (x, sp, tl) in enumerate(((470, C.WG2, -0.25), (960, C.WG, 0.0), (1450, dict(C.WG, beardcol=(0.55, 0.50, 0.45)), 0.25))):   # 压在底下的王公
            sq = lt > 0.28
            RG.head(c, x, 818 + (4 if sq else 0), 84, dict(sp, gear=None), dict(front=True, tilt=tl, eye='dizzy' if sq and i != 1 else 'squeeze' if sq else 'shock', brow='worried',
                    mouth=mouth_of(t, 'c5', 'wavy', 'o', 'wavy') if i == 1 else 'wavy', fx=('tear',) if i == 1 and t >= st('c5') - 0.2 else ('stars',) if sq else ()), t)
            for k in (-1, 1): rr(c, x + k * 120 - 34, 866, 68, 30, 14); fs(c, sp['skin'], 4)
            pos['w%d' % i] = (x, 818)
        y = by + (press if lt > 1.0 else 0)
        rr(c, 330, y, 1260, 54, 10); fs(c, (0.62, 0.42, 0.22), 6)
        c.set_source_rgba(0.3, 0.18, 0.08, 0.5); c.set_line_width(3)
        for k in range(6): c.move_to(360 + k * 210, y + 16 + (k % 2) * 14); c.line_to(520 + k * 210, y + 20 + (k % 2) * 14); c.stroke()
        for (x, a) in ((1640, 0.3), (270, -0.5)):                               # 掉在地上的王冠
            c.save(); c.translate(x, 880); c.rotate(a); rr(c, -50, -50, 100, 50, 10); fs(c, (0.90, 0.70, 0.22), 4); rr(c, -58, -14, 116, 26, 12); fs(c, (0.36, 0.22, 0.12), 4); c.restore()
        cheers = talking(t, 'c4', 1.2)
        for k, (x, f, sp) in enumerate(((480, 1, C.MGB), (800, -1, C.MGB2), (1120, 1, C.MGB3), (1440, -1, C.TMZ))):
            ap = 0.75 + k * 0.3
            if lt < ap: continue
            fall = (1 - eout((lt - ap) / 0.22, 2)) * 420; dy = -bounce(k) - fall
            sp = dict(sp, beard=None) if k == 3 else sp
            kw = dict(sf=2.5, ef=2.7) if cheers else dict(sf=1.2 + 0.3 * math.sin(t * 5 + k), ef=2.2)
            J, P, S = Q(c, x, by - 2, 330, sp, f, 'kneel', t + k, lean=0.14, hd=0.0, eye='happy', brow='raised', mouth='shout' if (cheers or int(t * 6 + k) % 3 == 0) else 'smile', dy=dy, **kw); pos['m%d' % k] = wpos(J, P, S)
            hx, hy = wpos(J, P, S, 'hdf'); c.move_to(hx - 20, hy - 34); c.line_to(hx + 20, hy - 34); c.line_to(hx + 14, hy + 6); c.line_to(hx - 14, hy + 6); c.close_path(); fs(c, (0.92, 0.76, 0.30), 3.5)
        if lt > 1.3:
            for (x, kind) in ((640, 0), (960, 1), (1280, 0)):
                if kind: c.save(); c.translate(x, by - 4); c.scale(1.6, 0.6); c.arc(0, -40, 60, 0, TAU); c.restore(); fs(c, (0.72, 0.38, 0.16), 4); c.rectangle(x + 70, by - 44, 60, 14); fs(c, (0.95, 0.93, 0.88), 3)
                else: rr(c, x - 30, by - 70, 60, 70, 12); fs(c, (0.55, 0.30, 0.18), 4); c.rectangle(x - 12, by - 92, 24, 24); fs(c, (0.55, 0.30, 0.18), 4)
        SC.snow(c, t, 110, 7)

    slam = 0.28 <= lt
    fr = scene('night', d, lt, t, shake=18 * math.exp(-(lt - 0.28) * 8) if slam else 0, flash=0.45 * math.exp(-(lt - 0.28) * 10) if slam else 0, mul=(1.22, 1.08, 1.0), punch=False)
    for gx in (190, 1740):
        yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32); g = np.exp(-((xx - gx) ** 2 + (yy - 800) ** 2) / (2 * 300 ** 2)); fr = fr + cv2.resize(g, (W, H))[..., None] * np.float32([0.40, 0.20, 0.05])
    chips(X, t, True); tag(X, '1223 年 · 迦勒迦河畔（据罗斯编年史）', True); subtitle(X, t)
    if 'm1' in pos: say(X, t, 'c4', pos['m1'][0] + 140, pos['m1'][1] - 280, (pos['m1'][0] + 30, pos['m1'][1] - 150), size=84, hold=0.35)
    say(X, t, 'c5', 960, 990, (960, 905), size=60, hold=0.3, text='压……压到我了……')
    return finish(fr, X)


# ================================================================ ④ 哈里发：敢动我？→ 没有人来
def caliph(lt, dur, t):
    X = Txt(False); pos = {}

    def under(c):
        for x in (240, 620, 1300, 1680):
            c.rectangle(x - 46, 250, 92, 560); fs(c, (0.93, 0.84, 0.62), 5); rr(c, x - 66, 220, 132, 44, 10); fs(c, (0.90, 0.72, 0.30), 5)
        for x in (430, 960, 1490): c.arc(x, 330, 150, PI, TAU); c.set_source_rgba(0.90, 0.72, 0.30, 0.9); c.set_line_width(14); c.stroke()

    def d(c):
        gold_heap(c, 1040, 900, 520, 250)
        J, P, S = Q(c, 1040, 690, 440, C.HLF, -1, 'point', t, eye='fierce', brow='angry', mouth=mouth_of(t, 'd2', 'shout', 'o', 'smirk'), sf=1.9 + 0.2 * math.sin(t * 9), ef=1.9, lean=0.1, fx=('anger',) if talking(t, 'd2') else ()); pos['c'] = wpos(J, P, S)
        u = cl((t - st('d2') - 0.3) / 1.6)                                       # 回信飞出去
        if u > 0:
            x = 800 - 900 * u; y = 640 - 160 * math.sin(u * PI) - 60 * u
            c.save(); c.translate(x, y); c.rotate(-0.3 - u * 0.4); rr(c, -52, -34, 104, 68, 6); fs(c, (0.98, 0.95, 0.86), 4); c.move_to(-52, -34); c.line_to(0, 8); c.line_to(52, -34); c.set_source_rgb(*OL); c.set_line_width(4); c.stroke(); c.arc(0, 10, 11, 0, TAU); fs(c, (0.78, 0.10, 0.10), 3); c.restore()

    fr = scene('hall', d, lt, t, under=under, **Z, tint=(1.10, 1.02, 0.80))
    chips(X, t); tag(X, '1258 年 · 巴格达'); subtitle(X, t)
    X.T('哈里发', pos['c'][0] + 270, pos['c'][1] + 40, 54, fill=(140, 70, 14), stroke=6)
    say(X, t, 'd2', 560, 420, (pos['c'][0] - 110, pos['c'][1] - 20), size=70, hold=0.3)
    return finish(fr, X)


def lonely(lt, dur, t):
    X = Txt(False); pos = {}

    def d(c):
        c.rectangle(0, 800, W, 280); c.set_source_rgba(0.80, 0.62, 0.36, 0.55); c.fill()
        gold_heap(c, 960, 850, 150, 80)
        J, P, S = Q(c, 960, 790, 190, C.HLF, -1 if int(lt / 0.7) % 2 == 0 else 1, 'stand', t, eye='dot', brow='worried', mouth=mouth_of(t, 'd4', 'shout', 'o', 'wavy'), sf=2.3, ef=2.7, fx=('sweat',)); pos['c'] = wpos(J, P, S)
        x = -100 + lt * 620; y = 900 - 40 * abs(math.sin(lt * 6))                # 风滚草
        c.save(); c.translate(x, y); c.rotate(lt * 7); c.set_source_rgba(0.42, 0.30, 0.16, 0.9); c.set_line_width(4)
        for k in range(9): a = k / 9 * TAU; c.arc(math.cos(a) * 14, math.sin(a) * 14, 34, a, a + 4.2); c.stroke()
        c.restore()

    fr = scene('dusk', d, lt, t, tint=(1.10, 1.0, 0.82), punch=True)
    chips(X, t); tag(X, '1258 年 · 巴格达'); subtitle(X, t)
    if lt < st('d4') - (t - lt) - 0.1: X.T('……', pos['c'][0], pos['c'][1] - 130, 70, fill=(60, 44, 34), stroke=6, a=ease(lt / 0.3))
    if say(X, t, 'd4', pos['c'][0], pos['c'][1] - 170, (pos['c'][0], pos['c'][1] - 70), size=60, hold=0.5):
        u = t - st('d4')
        for k, (s, x, y, sz) in enumerate((('有人吗……', 1380, 430, 52), ('吗……', 1640, 330, 40))): X.T(s, x, y, sz, fill=(110, 86, 60), stroke=4, a=cl((u - 0.5 - k * 0.3) / 0.3) * 0.8)
    return finish(fr, X)


# ================================================================ 钓鱼城：就这小破城？→ 炮石
def _cliff(c, t, load):
    c.move_to(1130, 1080); c.line_to(1210, 700); c.line_to(1180, 520); c.line_to(1270, 400); c.line_to(1920, 400); c.line_to(1920, 1080); c.close_path(); fs(c, (0.52, 0.50, 0.44), 6)
    c.set_source_rgba(0.2, 0.2, 0.18, 0.35); c.set_line_width(5)
    for k in range(7): x = 1280 + k * 95; c.move_to(x, 430 + (k % 3) * 40); c.line_to(x - 40 + (k % 2) * 60, 640 + (k % 3) * 70); c.line_to(x + 10, 900); c.stroke()
    c.rectangle(1290, 300, 640, 104); fs(c, (0.70, 0.66, 0.58), 6)
    for k in range(7): c.rectangle(1290 + k * 95, 262, 58, 40); fs(c, (0.70, 0.66, 0.58), 5)


def _trebuchet(c, x, y, ang):
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in (-1, 1): c.move_to(x + k * 70, y); c.line_to(x, y - 150); c.set_source_rgb(*OL); c.set_line_width(22); c.stroke(); c.move_to(x + k * 70, y); c.line_to(x, y - 150); c.set_source_rgb(0.55, 0.36, 0.18); c.set_line_width(13); c.stroke()
    c.save(); c.translate(x, y - 150); c.rotate(ang)
    c.move_to(-210, 0); c.line_to(90, 0); c.set_source_rgb(*OL); c.set_line_width(24); c.stroke(); c.move_to(-210, 0); c.line_to(90, 0); c.set_source_rgb(0.62, 0.42, 0.22); c.set_line_width(14); c.stroke()
    rr(c, 60, -10, 66, 66, 10); fs(c, (0.36, 0.34, 0.34), 4); c.restore()
    return x - 210 * math.cos(ang), y - 150 - 210 * math.sin(ang)


def diaoyu(lt, dur, t):
    X = Txt(False); pos = {}
    TC = T_CANNON; t_rel = TC - 0.50; uf = (t - t_rel) / 0.50; ui = t - TC
    MX, MY = 700, 880; HX, HY = MX + 20, MY - 350
    ang = -0.55 if t < t_rel else -0.55 + 2.2 * eout((t - t_rel) / 0.16, 2)

    def under(c): _cliff(c, t, 0)

    def d(c):
        # 城头：投石机 + 宋军
        sx, sy = _trebuchet(c, 1420, 300, ang)
        for i, x in enumerate((1560, 1700, 1830)):
            happy = ui > 0.3
            RG.head(c, x, 212 - (22 * abs(math.sin(t * 8 + i)) if happy else 0), 54, C.SB, dict(front=True, eye='happy' if happy else 'fierce', brow='raised' if happy else 'angry', mouth='shout' if happy else 'grit'), t)
        c.rectangle(1500, 262, 400, 42); fs(c, (0.70, 0.66, 0.58), 5)
        X.T('钓鱼城', 1610, 352, 60, fill=(20, 82, 124), stroke=7, halo=(240, 236, 220))
        # 石头
        if t < t_rel: c.arc(sx, sy - 6, 34, 0, TAU); fs(c, (0.40, 0.38, 0.37), 5)
        elif uf < 1:
            x0, y0 = 1235, 150; u = uf; px = x0 + (HX - x0) * u; py = y0 + (HY - y0) * u - 300 * math.sin(u * PI) * (1 - u * 0.4)
            for k in range(1, 6): uu = max(0, u - k * 0.03); c.arc(x0 + (HX - x0) * uu, y0 + (HY - y0) * uu - 300 * math.sin(uu * PI) * (1 - uu * 0.4), 34 - k * 4, 0, TAU); c.set_source_rgba(0.3, 0.28, 0.27, 0.35 - k * 0.05); c.fill()
            c.arc(px, py, 36, 0, TAU); fs(c, (0.40, 0.38, 0.37), 5)
        # 大纛
        tilt = eout((ui - 0.9) / 0.7, 2) if ui > 0.9 else 0
        c.save(); c.translate(400, 880); c.rotate(-tilt * 1.45)
        c.move_to(0, 0); c.line_to(0, -560); c.set_source_rgb(*OL); c.set_line_width(16); c.stroke()
        wv = 14 * math.sin(t * 6); c.move_to(0, -560); c.curve_to(90, -560 + wv, 170, -560 - wv, 250, -550 + wv); c.line_to(250, -330 + wv); c.curve_to(170, -340 - wv, 90, -330 + wv, 0, -340); c.close_path(); fs(c, (0.93, 0.72, 0.20), 5)
        c.restore()
        if tilt < 0.3: X.T('汗', 400 + 125, 880 - 448, 110, fill=(120, 20, 14), stroke=0)
        # 随从
        for i, x in enumerate((90, 260)):
            if ui > 0: kw = dict(eye='shock', brow='raised', mouth='o', fx=('shocklines', 'sweat'))
            else: kw = dict(eye='dot', brow='angry', mouth='flat')
            Q(c, x, 880, 330, (C.MGB2, C.MGB)[i], 1, 'stand', t + i, **kw)
        # 蒙哥
        if ui < 0:
            mx = MX - 420 * (1 - eout(lt / 0.9))
            if uf > 0.45: kw = dict(eye='shock', brow='raised', mouth='o', fx=('shocklines',), hd=-0.3)
            elif t >= st('e3') - 0.05: kw = dict(eye='closed', brow='raised', mouth=mouth_of(t, 'e3', 'shout', 'smirk', 'smirk'), lean=-0.14, sf=0.9, ef=2.4, sb=-0.9, eb=-2.4)
            elif t >= en('e2') + 0.2: kw = dict(eye='closed', brow='raised', mouth='smirk')
            else: kw = dict(eye='fierce', brow='angry', mouth='grit')
            nm = 'walk' if lt < 0.9 else 'point' if t < en('e2') + 0.2 else 'fold'
            J, P, S = Q(c, mx, MY, 460, C.MGK, 1, nm, t, **kw); pos['m'] = wpos(J, P, S)
        else:
            u = cl(ui / 0.85)
            if u < 1:
                e = eout(u, 1.6); x = MX - 470 * e; y = MY - 760 * e + 160 * u * u; hh = 460 * (1 - 0.86 * e)
                J, P, S = Q(c, x, y, hh, C.MGK, 1, 'cheer', t, eye='dizzy', brow='worried', mouth='o', fx=('stars',), rot=-ui * 16, sq=0.35 * max(0, 1 - ui / 0.08)); pos['m'] = wpos(J, P, S)
            else:
                tw = 1 + 0.5 * math.sin(t * 20); x, y, r = 160, 300, 26 * tw * (1 - cl((ui - 0.85) / 0.6) * 0.8)
                c.move_to(x, y - r * 2); c.line_to(x + r * 0.3, y - r * 0.3); c.line_to(x + r * 2, y); c.line_to(x + r * 0.3, y + r * 0.3); c.line_to(x, y + r * 2); c.line_to(x - r * 0.3, y + r * 0.3); c.line_to(x - r * 2, y); c.line_to(x - r * 0.3, y - r * 0.3); c.close_path()
                c.set_source_rgb(1, 0.98, 0.8); c.fill(); pos['m'] = (x, y)
            # 坑 + 掉下来的帽子
            c.save(); c.translate(MX, MY); c.scale(1, 0.28); c.arc(0, 0, 150, 0, TAU); c.restore(); fs(c, (0.30, 0.26, 0.22), 5)
            c.arc(MX + 30, MY - 24, 40, 0, TAU); fs(c, (0.40, 0.38, 0.37), 5)
            poof(c, MX, MY - 60, ui / 0.7, 2.0, (0.85, 0.80, 0.70))
            hat_drop(c, MX - 40, MY - 6, ui - 1.0, (0.93, 0.72, 0.20), 1.2)
            impact_lines(c, HX, HY + 60, ui / 0.45)

    sh = 30 * math.exp(-ui * 6) if ui > 0 else 0
    fr = scene('day', d, lt, t, under=under, shake=sh, flash=0.95 * math.exp(-ui * 9) if ui > 0 else 0)
    chips(X, t); tag(X, '1259 年 · 钓鱼城下'); subtitle(X, t)
    if ui < 0 and lt > 1.0 and t < st('e3') - 0.2: X.T('蒙古大汗 · 蒙哥', pos['m'][0] + 60, pos['m'][1] - 310, 50, fill=(165, 22, 18), stroke=6)
    if ui < 0: say(X, t, 'e3', pos['m'][0] + 150, pos['m'][1] - 330, (pos['m'][0] + 40, pos['m'][1] - 170), size=78, hold=0.0)
    if 0 <= ui < 0.8:
        X.T('砰！', 1040, 600, 260 * (1 + 0.6 * (1 - eout(ui / 0.14))), fill=(200, 26, 18), stroke=14, halo=(255, 240, 200), a=1 - ease((ui - 0.55) / 0.25))
        if ui > 0.08: bubble(X, '啊——！', pos['m'][0] + 230, max(300, pos['m'][1] - 60), None, ui - 0.08, 78)
    if ui > 0: X.T('注：蒙哥死因有炮石击伤、病亡等说法，本片取炮石说', 60, 1050, 30, fill=(70, 56, 44), anchor='lm', stroke=4)
    return finish(fr, X)
