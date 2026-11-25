"""战场内部视角（斜视角蛋蛋兵）：野狐岭骑兵凿穿、巴格达攻城。函数 (lt, dur, t) -> PIL.Image。"""
import sys, math
import common as CM
sys.path.append('/home/ubuntu/kunyang/film')          # 只借 eggkit；放在最后，免得那边的 script.py 盖住本片的
import numpy as np, cairo
import eggkit as K
from mapwar import eggfield as E, eggfx as FX
from mapwar.eggfield import px
from common import Txt, finish, chips, subtitle, stamp, tag, zoomblur, ease, eout, cl, hsh, T_YH, T_BG, T_END4, C_BG1, grain, W, H

TAU = 2 * math.pi; OL = (0.10, 0.08, 0.08)
MG = dict(body=(0.74, 0.13, 0.10), head=(0.42, 0.28, 0.16), square=False, band=(0.93, 0.89, 0.80), plume='ball', chest=False, fierce=True, hat='helmet', weapon='spear', shaft=E.WOOD, belt=(0.25, 0.16, 0.10))
JIN = dict(body=(0.86, 0.66, 0.16), head=(0.36, 0.25, 0.14), square=False, band=(0.99, 0.86, 0.40), plume=None, chest=False, fierce=False, hat='helmet', weapon='spear', shaft=E.WOOD, belt=(0.42, 0.27, 0.10))
ABB = dict(body=(0.15, 0.14, 0.17), head=(0.95, 0.93, 0.88), square=False, band=(0.80, 0.12, 0.10), plume=None, chest=False, fierce=False, hat='helmet', weapon='spear', shaft=E.WOOD, belt=(0.92, 0.74, 0.30))
_S = {}
kfn = lambda keys, x: float(np.interp(x, [a for a, _ in keys], [b for _, b in keys]))


def _post(fr, lt, flash_u=None):
    fr = zoomblur(fr.astype(np.float32), 0.22 * (1 - cl(lt / 0.2)) ** 2)
    if lt < 0.18: fr = fr + np.float32([1, 0.96, 0.88]) * 0.5 * (1 - lt / 0.18)
    if flash_u is not None and flash_u >= 0: fr = fr + np.float32([1, 0.95, 0.85]) * 0.75 * math.exp(-flash_u / 0.07)
    return fr + grain(0.02)


# ================================================================ 野狐岭：蒙古轻骑围着金军方阵转圈骑射
HJ = 12.3; FL = 0.42; NV = 7; SUB = 3            # 方阵半边、箭飞行时间、每人放几轮、每轮几支
_BOW = [False]; _weapon0 = E.weapon


def _weapon(c, b, t, s, chu, lod, firing=0.0, kind=None):
    if chu and _BOW[0]: return                    # 骑射手不拿长矛，弓在 over 层自己画
    return _weapon0(c, b, t, s, chu, lod, firing, kind)


E.weapon = _weapon


def _riders(C, tau, tc):
    q = ease((tau - tc) / 0.7); ra = C['ra'] * (1 - 0.34 * q); an = C['a0'] + C['om'] * tau
    return np.c_[ra * np.cos(an), ra * np.sin(an)].astype(np.float32), (an + math.pi / 2 + 0.95 * q).astype(np.float32), an


def yehuling(lt, dur, t):
    E.set_looks(MG, JIN); ti = T_YH - (t - lt)
    if 'yh' not in _S:
        r = np.random.default_rng(15); ax = np.arange(-HJ, HJ + 0.1, 1.45)
        g = np.float32([(x, y) for x in ax for y in ax]); g += r.uniform(-0.12, 0.12, g.shape).astype(np.float32); n = len(g)
        ra = np.concatenate([np.full(26, 21.5), np.full(32, 27.0)]) + r.uniform(-0.9, 0.9, 58); a0 = np.concatenate([np.arange(26) * TAU / 26, np.arange(32) * TAU / 32 + 0.1]) + r.uniform(-0.05, 0.05, 58)
        nr = len(ra); rel = np.zeros((nr, NV), np.float32); rel[:, 1:] = (np.arange(1, NV)[None] - 0.5 + r.random((nr, NV - 1))) * 0.36
        _S['yh'] = dict(g=g, rnd=r.random((n, 5)).astype(np.float32), ra=ra.astype(np.float32), a0=a0.astype(np.float32), om=(19.0 / ra).astype(np.float32), rel=rel,
                        ar=r.random((nr, NV, SUB, 4)).astype(np.float32), rph=r.uniform(0, 6, nr).astype(np.float32), aim=r.uniform(-0.25, 0.25, nr).astype(np.float32))
        gy = math.radians(118); an = _S['yh']['a0'][:26] + _S['yh']['om'][:26] * ti                   # 主角：定格那一拍离镜头最近的内圈骑手
        _S['yh']['hero'] = int(np.argmax(-np.cos(an) * math.cos(gy) - np.sin(an) * math.sin(gy) - 0.6 * np.abs(np.sin(an - gy))))
    C = _S['yh']; u = lt - ti; g = C['g']; rnd = C['rnd']; n = len(g); hero = C['hero']
    tau = lt if u < 0 else ti + 0.30 * min(u, 0.45) + max(0.0, u - 0.45)          # 第一轮箭落地后顿帧慢放
    tc = ti + 1.0; rp, rface, ran = _riders(C, tau, tc); nr = len(rp)
    # ---- 金军：外圈先倒，一层层往里塌；没倒的往中间挤
    d = HJ - np.maximum(np.abs(g[:, 0]), np.abs(g[:, 1])); th = ti + d * 0.078 + rnd[:, 0] * 0.24; us = tau - th; hit_ = us > 0; uc = np.clip(us, 0, None)
    fall = rnd[:, 1] < np.where(d < 8.5, 0.74, 0.46)
    hp = g.copy(); z = np.zeros(n, np.float32); st_ = np.zeros(n, np.int32); spd = np.zeros(n, np.float32)
    face = np.where(np.abs(g[:, 0]) > np.abs(g[:, 1]), np.where(g[:, 0] > 0, 0.0, math.pi), np.where(g[:, 1] > 0, math.pi / 2, -math.pi / 2)).astype(np.float32)
    m = hit_ & fall; uu = np.minimum(uc, 0.28); hp[m] *= (1 - 0.05 * uu[m] / 0.28)[:, None]; z[m] = np.maximum(0, 4.2 * uu[m] - 15 * uu[m] ** 2); st_[m] = np.where(uc[m] > 0.28, 3, 2)
    m = hit_ & ~fall; e_ = np.clip(uc / 1.1, 0, 1); e_ = e_ * e_ * (3 - 2 * e_); hp[m] *= (1 - 0.42 * e_[m])[:, None]; hp[m, 0] += 0.18 * np.sin(tau * 17 + rnd[m, 2] * 6); st_[m] = 2; spd[m] = 5
    face[m] = np.arctan2(-g[m, 1], -g[m, 0])
    F, han, cav, lower, torch, N = K.mk([dict(pos=rp, han=True, cav=True, face=rface, phase=tau * 12 + C['rph'], spd=19.0),
                                         dict(pos=hp, z=z, face=face, state=st_, phase=uc * 11 + rnd[:, 1] * 6, spd=spd, lower=d < 3.2)])
    e = math.exp(-u / 0.2) if u >= 0 else 0.0
    D = kfn([(0, 76), (ti, 37), (ti + 0.9, 48), (dur, 50)], lt) * (1 - 0.07 * e); pit = kfn([(0, 46), (ti, 25), (ti + 0.9, 33), (dur, 38)], lt); yaw = kfn([(0, 96), (ti, 118), (dur, 146)], lt)
    off = kfn([(0, 0), (ti, 9), (ti + 0.9, 3), (dur, 0)], lt); yr = math.radians(yaw)
    cam = E.make_cam(-off * math.cos(yr) + 0.8 * e * math.sin(lt * 60), -off * math.sin(yr) + 0.6 * e * math.sin(lt * 47), D, pit, yaw)
    props = [K.banner(0.6, 0.6, txt='金', tilt=ease((tau - (ti + 1.25)) / 0.6), t=t)]
    gy = math.radians(yaw); gx, gy_ = math.cos(gy), math.sin(gy)

    def under(c, cam_):
        for (a_, dist, rx, ry, h_) in ((-0.5, 105, 80, 26, 17), (0.45, 120, 90, 26, 19), (0.0, 170, 60, 40, 24)):
            FX.hill(c, cam_, dist * math.cos(math.radians(118) + a_), dist * math.sin(math.radians(118) + a_), rx, ry, h_, (0.56, 0.58, 0.44))
        c.set_line_cap(cairo.LINE_CAP_ROUND)                                                          # 马蹄扬尘：每个骑手身后拖几团
        for i in range(nr):
            for k in range(1, 5):
                tk = tau - k * 0.09; a2 = C['a0'][i] + C['om'][i] * tk; q2 = ease((tk - tc) / 0.7); rr2 = C['ra'][i] * (1 - 0.34 * q2)
                P, S_ = px(cam_, [(rr2 * math.cos(a2), rr2 * math.sin(a2), 0.5 + 0.3 * k)]); c.arc(P[0][0], P[0][1], (0.7 + 0.35 * k) * S_[0], 0, TAU); c.set_source_rgba(0.80, 0.74, 0.60, 0.22 - 0.04 * k); c.fill()

    def over(c, cam_):
        c.set_line_cap(cairo.LINE_CAP_ROUND); Z = np.float32([0, 0, 1])
        # ---- 箭：每人每轮 SUB 支，第一轮齐射卡在 ti 落地；落地后插在地上一会儿
        for k in range(NV):
            R_ = ti - FL + C['rel'][:, k]; uu_ = (tau - R_) / FL; act = np.where((uu_ > 0) & (uu_ < 2.6) & (R_ < tc + 0.25))[0]
            for i in act:
                a1 = C['a0'][i] + C['om'][i] * R_[i]; r1 = C['ra'][i] * (1 - 0.34 * ease((R_[i] - tc) / 0.7)); sx_, sy_ = r1 * math.cos(a1), r1 * math.sin(a1)
                for j in range(SUB):
                    q = C['ar'][i, k, j]; rho = min(16.5, max(1.5, (13.5 - (R_[i] + FL - ti) * 10.5))) * (0.45 + 0.6 * q[0]); a2 = a1 + (q[1] - 0.5) * 0.9
                    bx, by = rho * math.cos(a2), rho * math.sin(a2); w_ = uu_[i] - j * 0.07
                    if w_ <= 0: continue
                    f = lambda w: (sx_ + (bx - sx_) * w, sy_ + (by - sy_) * w, 2.6 * (1 - w) + 0.1 * w + 4 * (4.0 + 3 * q[2]) * w * (1 - w))
                    if w_ < 1:
                        P, S_ = px(cam_, [f(w_), f(max(0, w_ - 0.10))]); s = S_[0]
                        c.move_to(*P[1]); c.line_to(*P[0]); c.set_source_rgb(0.10, 0.08, 0.08); c.set_line_width(max(2.4, 0.11 * s)); c.stroke()
                        c.arc(P[0][0], P[0][1], max(1.6, 0.08 * s), 0, TAU); c.set_source_rgb(0.97, 0.95, 0.90); c.fill()
                    elif w_ < 2.4 and j == 0:
                        P, S_ = px(cam_, [(bx, by, 0), (bx - 0.35 * math.cos(a2), by - 0.35 * math.sin(a2), 1.15)]); c.move_to(*P[0]); c.line_to(*P[1])
                        c.set_source_rgba(0.12, 0.10, 0.10, min(1, (2.4 - w_) / 0.5)); c.set_line_width(max(1.8, 0.08 * S_[0])); c.stroke()
        # ---- 弓：朝圈里拉满，放完回弹
        dep = (np.c_[rp, np.zeros(nr)] - cam_.C) @ cam_.v
        for i in np.argsort(-dep):
            hk = 1.5 if i == hero else 1.0; a1 = ran[i] + math.pi + C['aim'][i]; nv = np.float32([math.cos(a1), math.sin(a1), 0]); p = np.float32([rp[i][0], rp[i][1], 0])
            R_ = ti - FL + C['rel'][i]; nx_ = R_[R_ > tau]; pv = R_[R_ <= tau]
            dr = 0.0 if tau > tc + 0.25 else (cl((tau - (pv[-1] if len(pv) else -0.6)) / max(0.12, (nx_[0] - (pv[-1] if len(pv) else -0.6)) * 0.8)) if len(nx_) else 0.0)
            G = p + nv * 0.85 * hk + Z * 2.5 * hk; top = G + Z * 1.05 * hk - nv * 0.32 * hk; bot = G - Z * 1.05 * hk - nv * 0.32 * hk
            c1 = G + nv * 0.38 * hk + Z * 0.55 * hk; c2 = G + nv * 0.38 * hk - Z * 0.55 * hk; nock = G - nv * (0.32 + 0.62 * dr) * hk; tipA = nock + nv * 1.75 * hk; sh = p + nv * 0.15 * hk + Z * 2.35 * hk
            P, S_ = px(cam_, [top, c1, c2, bot, nock, tipA, G, sh]); s = S_[6] * hk
            if not (-60 < P[6][0] < W + 60 and -60 < P[6][1] < H + 60): continue
            c.move_to(*P[7]); c.line_to(*P[6]); c.set_source_rgb(*OL); c.set_line_width(0.30 * s + 3); c.stroke(); c.move_to(*P[7]); c.line_to(*P[6]); c.set_source_rgb(*MG['body']); c.set_line_width(0.30 * s); c.stroke()
            c.move_to(*P[0]); c.line_to(*P[4]); c.line_to(*P[3]); c.set_source_rgb(0.95, 0.92, 0.85); c.set_line_width(max(1.2, 0.05 * s)); c.stroke()
            for wd, col in ((0.20 * s + 3, OL), (0.20 * s, (0.62, 0.40, 0.18))):
                c.move_to(*P[0]); c.curve_to(P[1][0], P[1][1], P[2][0], P[2][1], P[3][0], P[3][1]); c.set_source_rgb(*col); c.set_line_width(max(2.0, wd)); c.stroke()
            if dr > 0.12:
                c.move_to(*P[4]); c.line_to(*P[5]); c.set_source_rgb(0.12, 0.10, 0.10); c.set_line_width(max(2.0, 0.09 * s)); c.stroke()
                c.arc(P[5][0], P[5][1], max(1.6, 0.09 * s), 0, TAU); c.set_source_rgb(0.97, 0.95, 0.90); c.fill()
            c.arc(P[6][0], P[6][1], 0.17 * s, 0, TAU); c.set_source_rgb(0.96, 0.84, 0.70); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(max(1.2, 0.04 * s)); c.stroke()

    _BOW[0] = True
    try: fr, hero_xy = E.scene(cam, F, han, cav, tau, lower, hero=hero, props=props, under=under, over=over)
    finally: _BOW[0] = False
    fr = _post(fr, lt, u)
    X = Txt(False); chips(X, t); tag(X, '1211 年 · 野狐岭'); subtitle(X, t)
    if u < 0:
        P, _ = px(cam, [(0, 0, 8.5)]); a_ = ease(lt / 0.2)
        if hero_xy is not None: X.T('蒙古轻骑', min(1620, max(300, hero_xy[0] + 290)), max(300, hero_xy[1] - 10), 60, fill=(175, 22, 18), stroke=7, a=a_)
        X.T('金军主力', P[0][0], P[0][1], 66, fill=(130, 88, 12), stroke=7, a=a_)
    elif u < 1.3:
        X.T('围射！', 1360, 330, 240 * (1 + 0.6 * (1 - eout(u / 0.14))), fill=(200, 26, 18), stroke=14, halo=(255, 240, 200), a=1 - ease((u - 1.05) / 0.25))
    return finish(fr, X)


# ================================================================ 巴格达：投石机齐射，城墙塌一段
HS, WH, WW = 62.0, 6.0, 2.6            # 城墙半长、高、厚
BR0, BR1 = -6.5, 6.5                   # 缺口
TREB = [(-40, -31), (-21, -34), (0, -50), (21, -34), (40, -31)]
WALLC, WTOP = (0.82, 0.70, 0.50), (0.92, 0.82, 0.62)


def _wall(c, cam, x0, x1, merlon=True):
    K.box(c, cam, x0, 0, x1, WW, 0, WH, WALLC, 2.5, WTOP)
    if merlon:
        for x in np.arange(x0 + 0.4, x1 - 1.0, 1.9): K.box(c, cam, x, 0, x + 1.0, 0.5, WH, WH + 0.9, WALLC, 1.2)


def _dome(c, cam, x, y, w, h, r, col, spire=True):
    K.box(c, cam, x - w, y - w, x + w, y + w, 0, h, (0.90, 0.82, 0.66), 2.0, (0.94, 0.88, 0.74))
    P, S_ = px(cam, [(x, y, h), (x, y, h + r * 1.9)]); s = S_[0]
    c.save(); c.translate(P[0][0], P[0][1]); c.scale(1, 1.12); c.arc(0, 0, r * s, math.pi, TAU); c.close_path(); c.restore()
    c.set_source_rgb(*col); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(2.5); c.stroke()
    if spire: c.move_to(P[0][0], P[0][1] - r * s * 1.12); c.line_to(*P[1]); c.set_source_rgb(*OL); c.set_line_width(3); c.stroke(); c.arc(P[1][0], P[1][1], 0.35 * s, 0, TAU); c.set_source_rgb(0.95, 0.78, 0.25); c.fill()


def _treb(cam, x, y, th):
    """投石机 prop：长臂角 th（0.6 待发 → -2.0 甩出）。"""
    def fn(c, sx, sy, s):
        pv = (x, y, 7.0); tip = (x, y - 8.0 * math.cos(th), 7.0 - 8.0 * math.sin(th)); cw = (x, y + 2.8 * math.cos(th), 7.0 + 2.8 * math.sin(th))
        P, S_ = px(cam, [(x - 2.4, y, 0), (x + 2.4, y, 0), pv, tip, cw, (x - 2.4, y - 3, 0), (x + 2.4, y - 3, 0)]); s_ = S_[2]
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        def ln(a, b, wd, col):
            c.move_to(*P[a]); c.line_to(*P[b]); c.set_source_rgb(*OL); c.set_line_width(wd * s_ + 3); c.stroke(); c.move_to(*P[a]); c.line_to(*P[b]); c.set_source_rgb(*col); c.set_line_width(wd * s_); c.stroke()
        wood = (0.58, 0.38, 0.18)
        ln(5, 0, 0.35, wood); ln(6, 1, 0.35, wood); ln(0, 1, 0.35, wood); ln(0, 2, 0.42, wood); ln(1, 2, 0.42, wood); ln(4, 3, 0.36, (0.68, 0.46, 0.24))
        c.rectangle(P[4][0] - 1.0 * s_, P[4][1] - 0.4 * s_, 2.0 * s_, 1.9 * s_); c.set_source_rgb(0.34, 0.32, 0.32); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(2.5); c.stroke()
    return (x, y, fn)


def _stone(c, cam, a, b, q, hgt=16.0, r=0.75):
    if q <= 0 or q >= 1: return
    f = lambda q: (a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q, a[2] + (b[2] - a[2]) * q + 4 * hgt * q * (1 - q))
    for k in range(6, -1, -1):
        qq = max(0.0, q - k * 0.022); P, S_ = px(cam, [f(qq)]); s = S_[0]
        c.arc(P[0][0], P[0][1], r * s * (1 - k * 0.09), 0, TAU)
        if k: c.set_source_rgba(0.95, 0.55, 0.2, 0.30 - k * 0.04); c.fill()
        else: c.set_source_rgb(0.36, 0.34, 0.33); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(2.5); c.stroke()


def baghdad(lt, dur, t):
    E.set_looks(MG, ABB); ti = T_BG - (t - lt); u = lt - ti
    if 'bg' not in _S:
        r = np.random.default_rng(7)
        inf = np.concatenate([K.block(7, 13, 1.7, cx, cy, math.pi / 2, 0.2, 40 + i) for i, (cx, cy) in enumerate(((-45, -15), (-23, -17), (23, -17), (45, -15)))])
        wd = K.wedge(9, 3.2, 2.5, 8, 9); wd = np.c_[wd[:, 1], wd[:, 0]]                       # 楔形朝 +y
        dx = np.arange(-HS + 2, HS - 2, 2.1); dfn = np.c_[dx, np.full(len(dx), 1.4)].astype(np.float32)
        deb = np.c_[r.uniform(BR0, BR1, 26), r.uniform(-0.4, 0.4, 26), r.uniform(-9, 9, 26), r.uniform(-13, 6, 26), r.uniform(9, 20, 26), r.uniform(0.5, 1.3, 26)]
        rub = np.c_[r.uniform(BR0 - 1, BR1 + 0.2, 16), r.uniform(-3.5, 3.0, 16), r.uniform(0.9, 2.2, 16), r.uniform(0.5, 2.0, 16)]
        _S['bg'] = dict(inf=inf, wd=wd, dfn=dfn, deb=deb, rub=rub, rnd=r.random((900, 4)).astype(np.float32))
    G = _S['bg']; rnd = G['rnd']
    # 兵
    up = np.clip(u - 0.25 - rnd[:len(G['inf']), 0] * 0.5, 0, None); inf = G['inf'].copy(); tgt = np.float32([0, -3]) - inf; tgt /= np.linalg.norm(tgt, axis=1)[:, None]
    inf += tgt * (5.5 * up)[:, None]
    cy0 = -27 + 15.0 * max(0.0, u + 0.1); wd = G['wd'] + np.float32([0, min(cy0, 14.0)])
    dfn = G['dfn']; nd = len(dfn); near = np.abs(dfn[:, 0]) < BR1 + 1.5; ud = max(0.0, u); dz = np.full(nd, WH, np.float32); dpos = dfn.copy(); dst = np.zeros(nd, np.int32)
    if u >= 0:
        k = rnd[:nd]; dpos[near, 0] += (k[near, 0] - 0.5) * 26 * ud; dpos[near, 1] += -4 * ud + (k[near, 1] - 0.5) * 8 * ud
        dz[near] = np.maximum(0, WH + (9 + 9 * k[near, 2]) * ud - 16 * ud * ud); dst[near] = np.where(dz[near] <= 0.01, 3, 2)
    crouch = (np.sin(t * 5 + np.arange(nd) * 1.7) < 0.2) & ~near
    F, han, cav, lower, torch, N = K.mk([dict(pos=inf, face=math.pi / 2, han=True, phase=t * 11 + rnd[:len(inf), 1] * 6, spd=np.where(up > 0, 5.5, 0.0), lower=up > 0),
                                         dict(pos=wd, face=math.pi / 2, han=True, cav=True, phase=t * 12 + rnd[:len(wd), 2] * 6, spd=15.0 if u > -0.1 else 0.0),
                                         dict(pos=dpos, z=dz, face=-math.pi / 2, state=dst, phase=t * 9, spd=0.0, lower=False, crouch=crouch)])
    e = math.exp(-u / 0.22) if u >= 0 else 0.0
    cam = E.make_cam(kfn([(0, -5), (dur, 2)], lt) + 1.0 * e * math.sin(lt * 61), kfn([(0, -13), (ti, -9), (dur, -4)], lt) + 0.8 * e * math.cos(lt * 49),
                     kfn([(0, 72), (ti, 56), (dur, 45)], lt) * (1 - 0.07 * e), kfn([(0, 26), (dur, 22)], lt), kfn([(0, 77), (dur, 98)], lt))
    # 投石机：第一轮 ti-0.75 放、ti 落；第二轮 ti+0.55 放、ti+1.3 落
    def th(k):
        for rel in (ti - 0.75 + k * 0.03, ti + 0.55 + k * 0.05):
            q = lt - rel
            if -0.2 <= q < 0.9: return 0.6 - 2.6 * eout((q + 0.2) / 0.22, 2) * (1 - 0.65 * ease((q - 0.25) / 0.6))
        return 0.6
    props = [_treb(cam, x, y, th(k)) for k, (x, y) in enumerate(TREB)]
    tg1 = [(-30, 1, WH), (-14, 14, 0.5), (0, 1, 3.5), (15, 1, WH), (33, 22, 0.5)]; tg2 = [(-44, 1, WH), (-22, 1, WH), (4, 18, 0.5), (26, 1, WH), (46, 12, 0.5)]
    for k, g in enumerate(tg1):
        if k != 2: props.append(FX.blast(g[0], g[1] - 0.5, u, 2.6, 30 + k))
    for k, g in enumerate(tg2): props.append(FX.blast(g[0], g[1] - 0.5, u - 1.3 - k * 0.05, 2.6, 40 + k))
    if u >= 0: props += [FX.blast(0, -1.5, u * 0.75, 6.0, 3), FX.blast(-4, -1.0, (u - 0.1) * 0.8, 3.5, 5), FX.blast(4.5, -1.0, (u - 0.16) * 0.8, 3.5, 6)]

    def under(c, cam_):
        FX.river(c, cam_, [(x, 96 + 9 * math.sin(x / 40)) for x in range(-220, 221, 20)], 20, t * 4, (0.45, 0.62, 0.70))
        FX._poly(c, cam_, [(-HS, 0), (HS, 0), (HS, 78), (-HS, 78)]); c.set_source_rgb(0.80, 0.72, 0.56); c.fill()
        for (x, y, w_, h_, r_, col) in ((-34, 52, 5, 7, 5.5, (0.20, 0.62, 0.62)), (30, 58, 4, 8, 4.5, (0.93, 0.76, 0.28)), (0, 44, 9, 9, 10, (0.93, 0.76, 0.28)), (-16, 30, 3.5, 5, 3.8, (0.20, 0.62, 0.62)), (18, 28, 3.5, 5, 3.8, (0.20, 0.62, 0.62))): _dome(c, cam_, x, y, w_, h_, r_, col)
        for (x, y) in ((-48, 38), (46, 40), (-8, 62), (12, 60)): _dome(c, cam_, x, y, 1.1, 17, 1.4, (0.20, 0.62, 0.62))
        _wall(c, cam_, -HS, BR0); _wall(c, cam_, BR1, HS)
        if u < 0: _wall(c, cam_, BR0, BR1)
        else:
            for (x, y, w_, h_) in G['rub']: K.box(c, cam_, x, y, x + w_, y + w_ * 0.8, 0, h_ * (1 - 0.3 * cl(u / 0.6)), tuple(v * (0.8 + 0.2 * hsh(int(x * 7))) for v in WALLC), 1.6)
        for x in (-48, -24, 24, 48):
            K.box(c, cam_, x - 2.6, -1.0, x + 2.6, WW + 0.8, 0, WH + 2.6, tuple(v * 0.95 for v in WALLC), 2.5, WTOP)
            for xx in (x - 2.4, x - 0.5, x + 1.4): K.box(c, cam_, xx, -1.0, xx + 1.0, -0.5, WH + 2.6, WH + 3.5, WALLC, 1.2)

    def over(c, cam_):
        for k, (x, y) in enumerate(TREB):
            a = (x, y + 4, 13.0); _stone(c, cam_, a, tg1[k], (lt - (ti - 0.75 + k * 0.03)) / (0.75 - k * 0.03)); _stone(c, cam_, a, tg2[k], (lt - (ti + 0.55 + k * 0.05)) / 0.75)
        if 0 <= u < 1.6:                                                         # 飞出去的城砖
            for (x0, y0, vx, vy, vz, sz) in G['deb']:
                zz = 3 + vz * u - 14 * u * u
                if zz < 0: continue
                P, S_ = px(cam_, [(x0 + vx * u, y0 + vy * u, zz)]); s = S_[0] * sz
                c.save(); c.translate(*P[0]); c.rotate(u * 7 + x0); c.rectangle(-0.6 * s, -0.4 * s, 1.2 * s, 0.8 * s); c.set_source_rgb(*WALLC); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(2); c.stroke(); c.restore()
        if 0 <= u < 0.6:
            P, S_ = px(cam_, [(0, 0, 3)]); s = S_[0]; c.arc(P[0][0], P[0][1], (6 + 60 * u) * s, 0, TAU); c.set_source_rgba(1, 0.9, 0.6, 0.8 * (1 - u / 0.6)); c.set_line_width(12 * (1 - u / 0.6) + 2); c.stroke()

    fr, _ = E.scene(cam, F, han, cav, t, lower, props=props, under=under, over=over, tint=(1.06, 0.99, 0.86))
    if u >= 0:
        P, _ = px(cam, [(0, 0, 3)]); fr = K.glow(fr, P[0][0], P[0][1], 320, (1.0, 0.6, 0.25), 0.5 * math.exp(-u / 0.5))
    fr = _post(fr, lt, u)
    X = Txt(False); chips(X, t); tag(X, '1258 年 · 巴格达城下'); subtitle(X, t)
    if u < 0: X.T('投石机齐射', 960, 300, 96, fill=(175, 22, 18), stroke=9, a=ease(lt / 0.15))
    elif u < 0.5: X.T('轰！', 960, 330, 260 * (1 + 0.6 * (1 - eout(u / 0.14))), fill=(200, 26, 18), stroke=14, halo=(255, 240, 200), a=1 - ease((u - 0.3) / 0.2))
    stamp(X, '13 天 · 陷落', t, T_END4, y=640, hold=C_BG1 - T_END4 + 0.1, sub='1258 年 2 月 10 日')
    return finish(fr, X)
