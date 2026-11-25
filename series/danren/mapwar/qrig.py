"""精致Q版小人骨架：大头 + 可动四肢（肩肘髋膝）+ 整体翻转/空翻 + 表情系统 + 兵器。
本地坐标：髋为原点，+x 朝前，y 向下。角度：0 = 朝下，正 = 朝前（向量 (sin a, cos a)）。
"""
import math, cairo, numpy as np
from .qdraw import head_path, rrect, poly, lin, rad, gold_metal, scale_tile, lamellar_tile, beast, GOLD, GOLD_L, GOLD_D
from . import qcostume as opera
PI = math.pi
OL = (0.10, 0.08, 0.08)


def V(a, L): return (math.sin(a) * L, math.cos(a) * L)
def add(p, q): return (p[0] + q[0], p[1] + q[1])


# ================================================================ 运动学
def joints(P, S):
    """返回本地坐标下各关节。"""
    hipf, hipb = (0.05 * S, 0), (-0.05 * S, 0)
    lean = P.get('lean', 0); Lt = 0.27 * S
    neck = (math.sin(lean) * Lt, -math.cos(lean) * Lt)
    shf = add(neck, (math.sin(lean) * -0.03 * S + 0.05 * S, 0.035 * S)); shb = add(neck, (-0.06 * S, 0.035 * S))
    J = dict(hip=(0, 0), neck=neck, shf=shf, shb=shb)
    for side, sh in (('f', shf), ('b', shb)):
        el = add(sh, V(P['s' + side], 0.13 * S)); hd = add(el, V(P['e' + side], 0.12 * S)); J['el' + side] = el; J['hd' + side] = hd
    for side, hp in (('f', hipf), ('b', hipb)):
        kn = add(hp, V(P['h' + side], 0.155 * S)); ft = add(kn, V(P['k' + side], 0.15 * S)); J['hp' + side] = hp; J['kn' + side] = kn; J['ft' + side] = ft
    hd_a = lean + P.get('hd', 0); R = 0.24 * S * P.get('hs', 1.0)
    J['head'] = add(neck, (math.sin(hd_a) * R * 0.95, -math.cos(hd_a) * R * 0.95)); J['R'] = R; J['hd_a'] = hd_a
    return J


def to_world(P, S, p):
    f = P.get('f', 1); rot = P.get('rot', 0); c0 = (0, -0.3 * S); sq = P.get('sq', 0)
    x, y = p[0] * (1 - 0.4 * sq), p[1] * (1 + sq)
    dx, dy = x - c0[0], y - c0[1]; cr, sr = math.cos(rot), math.sin(rot)
    x, y = c0[0] + cr * dx - sr * dy, c0[1] + sr * dx + cr * dy
    return (P['x'] + f * x, P['y'] + y)


def weapon_pts(P, S, J, spec):
    w = P.get('w', PI); kind = spec.get('weapon')
    hand = J['hdf']; d = (math.sin(w), math.cos(w))
    if kind in ('ji', 'ji2'): Lf, Lb = 0.82 * S, 0.45 * S
    elif kind == 'dao': Lf, Lb = 0.6 * S, 0.06 * S
    elif kind == 'spear': Lf, Lb = 0.7 * S, 0.35 * S
    elif kind == 'sword': Lf, Lb = 0.42 * S, 0.06 * S
    elif kind in ('rifle', 'bayonet'): Lf, Lb = 0.62 * S, 0.3 * S
    else: return hand, hand, hand
    return (hand[0] - d[0] * Lb, hand[1] - d[1] * Lb), (hand[0] + d[0] * Lf, hand[1] + d[1] * Lf), hand


def tip_world(P, S, spec):
    J = joints(P, S); b, tp, h = weapon_pts(P, S, J, spec); return to_world(P, S, tp)


# ================================================================ 画法小件
def limb(c, pts, ws, col, olw, hi=None):
    """seamless 双段肢体：先整体描黑边，再整体填色，最后一道受光高光。"""
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    for k in range(2): c.move_to(*pts[k]); c.line_to(*pts[k + 1]); c.set_source_rgb(*OL); c.set_line_width(ws[k] + 2 * olw); c.stroke()
    for k in range(2): c.move_to(*pts[k]); c.line_to(*pts[k + 1]); c.set_source_rgb(*col); c.set_line_width(ws[k]); c.stroke()
    if hi:
        for k in range(2):
            (x0, y0), (x1, y1) = pts[k], pts[k + 1]; L = math.hypot(x1 - x0, y1 - y0) + 1e-6; nx, ny = -(y1 - y0) / L, (x1 - x0) / L
            o = ws[k] * 0.22; c.move_to(x0 - nx * o, y0 - ny * o); c.line_to(x1 - nx * o, y1 - ny * o); c.set_source_rgba(*hi, 0.35); c.set_line_width(ws[k] * 0.25); c.stroke()


def fs(c, src, lw, col=OL):
    c.set_source(src) if not isinstance(src, tuple) else c.set_source_rgb(*src); c.fill_preserve(); c.set_source_rgb(*col); c.set_line_width(lw); c.stroke()


def pompom(c, x, y, r):
    for k in range(8): a = k / 8 * 2 * PI; c.arc(x + math.cos(a) * r * 0.4, y + math.sin(a) * r * 0.4, r * 0.6, 0, 2 * PI)
    c.set_source(rad(x, y, 0, r * 1.1, [(0, (1, 0.5, 0.4)), (0.7, (0.8, 0.08, 0.06)), (1, (0.45, 0.02, 0.02))], x - r * 0.3, y - r * 0.4)); c.fill()


# ================================================================ 表情
def face(c, R, spec, P, t):
    eye = P.get('eye', 'dot'); brow = P.get('brow', 'none'); mouth = P.get('mouth', 'flat'); fx = P.get('fx', ())
    ox = 0.0 if P.get('front') else 0.22 * R; lw = max(1.5, 0.045 * R)
    eyes = ((-0.34 * R, 0.02 * R, 1.0), (0.34 * R, 0.02 * R, 1.0)) if P.get('front') else ((ox - 0.33 * R, 0.02 * R, 0.85), (ox + 0.31 * R, 0.02 * R, 1.0))
    for (x, y, k) in eyes:
        r = 0.115 * R * k
        if eye == 'lady': continue
        if eye in ('dot', 'dot2', 'glint'):
            c.save(); c.translate(x, y); c.scale(1, 1.15); c.arc(0, 0, r, 0, 2 * PI); c.restore(); c.set_source_rgb(*OL); c.fill()
            if eye in ('dot2', 'glint'): c.arc(x - r * 0.15, y + r * 0.3, r * 0.42, 0, 2 * PI); c.set_source_rgb(0.35, 0.05, 0.05); c.fill()   # 重瞳：第二颗瞳仁
            c.arc(x - r * 0.35, y - r * 0.4, r * 0.35, 0, 2 * PI); c.set_source_rgb(1, 1, 1); c.fill()
            if eye == 'glint':
                c.save(); c.translate(x + r * 0.6, y - r * 0.9); s_ = r * (1.4 + 0.5 * math.sin(t * 12))
                c.move_to(0, -s_); c.line_to(s_ * 0.2, -s_ * 0.2); c.line_to(s_, 0); c.line_to(s_ * 0.2, s_ * 0.2); c.line_to(0, s_); c.line_to(-s_ * 0.2, s_ * 0.2); c.line_to(-s_, 0); c.line_to(-s_ * 0.2, -s_ * 0.2); c.close_path()
                c.set_source_rgb(1, 0.95, 0.6); c.fill(); c.restore()
        elif eye == 'fierce':
            c.save(); c.translate(x, y); c.scale(1.3, 0.85); c.arc(0, 0, r * 1.15, 0, 2 * PI); c.restore(); c.set_source_rgb(1, 0.98, 0.95); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(lw * 0.8); c.stroke()
            if P.get('front'):                                                      # 正面：瞳孔居中，眼皮外高内低、左右对称
                io = 1 if x < 0 else -1; c.arc(x + io * r * 0.15, y + r * 0.1, r * 0.55, 0, 2 * PI); c.set_source_rgb(*OL); c.fill()
                c.move_to(x - io * r * 1.5, y - r * 1.25); c.line_to(x + io * r * 1.5, y - r * 0.35); c.set_line_width(lw * 1.6); c.stroke()
            else:
                c.arc(x + r * 0.35, y, r * 0.55, 0, 2 * PI); c.set_source_rgb(*OL); c.fill()
                c.move_to(x - r * 1.5, y - r * 1.2 * (1 if x < ox else 0.6)); c.line_to(x + r * 1.5, y - r * 0.5 * (1 if x > ox else 1.6)); c.set_line_width(lw * 1.6); c.stroke()
        elif eye == 'shock':
            c.arc(x, y, r * 1.5, 0, 2 * PI); c.set_source_rgb(1, 1, 1); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(lw * 0.8); c.stroke()
            c.arc(x + r * 0.2, y, r * 0.35, 0, 2 * PI); c.fill()
        elif eye in ('closed', 'happy'):
            sgn = -1 if eye == 'happy' else 1
            c.move_to(x - r * 1.2, y - sgn * r * 0.1); c.curve_to(x - r * 0.4, y + sgn * r * 0.8, x + r * 0.4, y + sgn * r * 0.8, x + r * 1.2, y - sgn * r * 0.1); c.set_source_rgb(*OL); c.set_line_width(lw * 1.3); c.stroke()
        elif eye == 'squeeze':
            c.move_to(x - r, y - r); c.line_to(x + r, y); c.line_to(x - r, y + r); c.set_source_rgb(*OL); c.set_line_width(lw * 1.3); c.stroke()
        elif eye == 'dizzy':
            c.move_to(x, y)
            for k_ in range(30): a = k_ * 0.5 + t * 8; rr = r * 0.05 * k_; c.line_to(x + math.cos(a) * rr, y + math.sin(a) * rr)
            c.set_source_rgb(*OL); c.set_line_width(lw * 0.8); c.stroke()
    if eye == 'lady': opera.lady_eyes(c, eyes, R, t)
    # 眉
    if brow != 'none':
        c.set_source_rgb(*spec.get('browcol', OL)); c.set_line_width(lw * 2.2 * spec.get('brow_w', 1.0)); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for (x, y, k) in eyes:
            inner = 1 if x < ox else -1; yb = y - 0.27 * R
            if P.get('front') and brow in ('angry', 'worried'):                     # 正面：外端→内端，怒眉内低、愁眉内高
                d_ = 0.07 if brow == 'angry' else -0.07; c.move_to(x - inner * 0.17 * R, yb - d_ * R); c.line_to(x + inner * 0.15 * R, yb + d_ * R)
            elif brow == 'angry': c.move_to(x - inner * -0.16 * R, yb - 0.08 * R); c.line_to(x + inner * 0.14 * R, yb + 0.06 * R)
            elif brow == 'worried': c.move_to(x - inner * -0.16 * R, yb + 0.04 * R); c.line_to(x + inner * 0.14 * R, yb - 0.08 * R)
            elif brow == 'raised': c.move_to(x - 0.15 * R, yb - 0.06 * R); c.curve_to(x - 0.05 * R, yb - 0.14 * R, x + 0.05 * R, yb - 0.14 * R, x + 0.15 * R, yb - 0.06 * R)
            else: c.move_to(x - 0.15 * R, yb); c.line_to(x + 0.15 * R, yb)
            c.stroke()
    # 胡子（嘴的后面先画髯，嘴画在上面）
    mx, my = ox + 0.02 * R, 0.46 * R; bc = spec.get('beardcol', (0.07, 0.06, 0.06))
    bt = 0.14 if mouth in ('shout', 'o', 'grit', 'wavy', 'gasp') else 0.05
    if spec.get('beard') == 'hang':
        c.move_to(mx - 0.3 * R, my + bt * R); c.curve_to(mx - 0.3 * R, my + 0.45 * R, mx - 0.1 * R, my + 0.65 * R, mx + 0.04 * R, my + 0.82 * R)
        c.curve_to(mx + 0.16 * R, my + 0.62 * R, mx + 0.32 * R, my + 0.45 * R, mx + 0.3 * R, my + bt * R); c.curve_to(mx + 0.1 * R, my + (bt + 0.06) * R, mx - 0.1 * R, my + (bt + 0.06) * R, mx - 0.3 * R, my + bt * R); c.close_path(); c.set_source_rgb(*bc); c.fill()
    elif spec.get('beard') in ('goatee', 'long'):
        L_ = 0.45 if spec['beard'] == 'goatee' else 0.75
        c.move_to(mx - 0.1 * R, my + 0.1 * R); c.line_to(mx + 0.1 * R, my + 0.1 * R); c.line_to(mx + 0.02 * R, my + L_ * R); c.close_path(); c.set_source_rgb(*bc); c.fill()
        c.set_line_width(0.04 * R); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in (-1, 1): c.move_to(mx + k * 0.03 * R, my - 0.08 * R); c.curve_to(mx + k * 0.15 * R, my - 0.14 * R, mx + k * 0.25 * R, my - 0.05 * R, mx + k * 0.3 * R, my + 0.08 * R); c.stroke()
    elif spec.get('beard') == 'mustache':
        c.set_source_rgb(*bc); c.save(); c.translate(mx, my - (0.17 if mouth in ('shout', 'o', 'grit', 'gasp') else 0.12) * R); c.scale(1, 0.3); c.arc(0, 0, 0.25 * R, 0, 2 * PI); c.restore(); c.fill()
    elif spec.get('beard') == 'full':
        c.save(); head_path(c, 0, 0, R, spec.get('head', 'round')); c.clip(); c.new_path()
        c.move_to(-0.55 * R, 0.3 * R); c.curve_to(-0.4 * R, my + 0.05 * R, mx - 0.2 * R, my - 0.12 * R, mx, my - 0.1 * R); c.curve_to(mx + 0.2 * R, my - 0.12 * R, mx + 0.35 * R, my + 0.02 * R, 0.85 * R, 0.3 * R)
        c.curve_to(0.8 * R, 1.0 * R, -0.5 * R, 1.0 * R, -0.55 * R, 0.3 * R); c.close_path(); c.set_source_rgba(*bc, 0.8); c.fill(); c.restore()
        c.arc(mx, my, 0.09 * R, 0, 2 * PI); c.set_source_rgb(*tuple(v * 0.92 for v in spec.get('skin', (0.95, 0.82, 0.68)))); c.fill()
    elif spec.get('beard') == 'wild':
        c.save(); c.move_to(-1.3 * R, -0.05 * R); c.line_to(1.3 * R, -0.05 * R); c.line_to(1.3 * R, 1.4 * R); c.line_to(-1.3 * R, 1.4 * R); c.close_path(); c.clip()
        head_path(c, 0, 0, R, spec.get('head', 'round')); c.clip(); c.new_path()
        c.move_to(-1.2 * R, 0.1 * R)
        for k in range(14): xx = -1.2 * R + k * 0.18 * R; c.line_to(xx, 0.1 * R + (0.12 * R if k % 2 else 0) + 0.25 * R * (1 - abs(xx / R)))
        c.line_to(1.3 * R, 1.4 * R); c.line_to(-1.3 * R, 1.4 * R); c.close_path(); c.set_source_rgb(*bc); c.fill(); c.restore()
        c.move_to(mx - 0.35 * R, my + 0.2 * R); c.curve_to(mx - 0.3 * R, my + 0.7 * R, mx + 0.3 * R, my + 0.7 * R, mx + 0.38 * R, my + 0.2 * R); c.set_source_rgb(*bc); c.fill()
    # 嘴
    c.set_source_rgb(*OL); c.set_line_width(lw)
    if mouth == 'lips': c.save(); c.translate(mx, my + 0.02 * R); c.scale(1.3, 0.8); c.arc(0, 0, 0.07 * R, 0, 2 * PI); c.restore(); c.set_source_rgb(0.85, 0.15, 0.2); c.fill()
    elif mouth == 'flat': c.move_to(mx - 0.1 * R, my); c.line_to(mx + 0.1 * R, my); c.stroke()
    elif mouth == 'smirk': c.move_to(mx - 0.12 * R, my + 0.02 * R); c.curve_to(mx, my + 0.05 * R, mx + 0.1 * R, my, mx + 0.16 * R, my - 0.08 * R); c.set_line_width(lw * 1.2); c.stroke()
    elif mouth == 'smile': c.arc(mx, my - 0.06 * R, 0.15 * R, 0.15 * PI, 0.85 * PI); c.set_line_width(lw * 1.2); c.stroke()
    elif mouth == 'gasp':                                                       # 惊掉下巴：竖长大圆嘴
        c.save(); c.translate(mx, my + 0.12 * R); c.scale(0.75, 1); c.arc(0, 0, 0.2 * R, 0, 2 * PI); c.restore(); fs(c, (0.4, 0.05, 0.05), lw)
        c.save(); c.translate(mx, my + 0.24 * R); c.scale(1.2, 0.6); c.arc(0, 0, 0.08 * R, 0, 2 * PI); c.restore(); c.set_source_rgb(0.9, 0.35, 0.35); c.fill()
    elif mouth in ('shout', 'o', 'grit', 'wavy'):
        if mouth == 'shout':
            c.move_to(mx - 0.22 * R, my - 0.1 * R); c.line_to(mx + 0.24 * R, my - 0.12 * R); c.curve_to(mx + 0.22 * R, my + 0.35 * R, mx - 0.18 * R, my + 0.35 * R, mx - 0.22 * R, my - 0.1 * R); c.close_path()
            fs(c, (0.45, 0.06, 0.06), lw); c.save(); c.move_to(mx - 0.22 * R, my - 0.1 * R); c.line_to(mx + 0.24 * R, my - 0.12 * R); c.curve_to(mx + 0.22 * R, my + 0.35 * R, mx - 0.18 * R, my + 0.35 * R, mx - 0.22 * R, my - 0.1 * R); c.clip()
            c.rectangle(mx - 0.3 * R, my - 0.15 * R, 0.6 * R, 0.1 * R); c.set_source_rgb(1, 1, 1); c.fill(); c.arc(mx, my + 0.32 * R, 0.14 * R, 0, 2 * PI); c.set_source_rgb(0.9, 0.35, 0.35); c.fill(); c.restore()
        elif mouth == 'o': c.save(); c.translate(mx, my + 0.05 * R); c.scale(0.8, 1); c.arc(0, 0, 0.1 * R, 0, 2 * PI); c.restore(); fs(c, (0.4, 0.05, 0.05), lw)
        elif mouth == 'grit':
            rrect(c, mx - 0.2 * R, my - 0.07 * R, 0.4 * R, 0.16 * R, 0.04 * R); fs(c, (1, 1, 1), lw)
            for k in range(1, 5): c.move_to(mx - 0.2 * R + k * 0.08 * R, my - 0.07 * R); c.line_to(mx - 0.2 * R + k * 0.08 * R, my + 0.09 * R)
            c.move_to(mx - 0.2 * R, my + 0.01 * R); c.line_to(mx + 0.2 * R, my + 0.01 * R); c.set_source_rgb(*OL); c.set_line_width(lw * 0.6); c.stroke()
        else:
            c.move_to(mx - 0.18 * R, my)
            for k in range(6): c.line_to(mx - 0.18 * R + (k + 1) * 0.06 * R, my + (0.04 if k % 2 == 0 else -0.04) * R)
            c.set_line_width(lw); c.stroke()
    if spec.get('beard') == 'hang':                                           # 八字须压在嘴上
        c.set_source_rgb(*bc); c.set_line_width(0.06 * R); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in (-1, 1): c.move_to(mx + k * 0.04 * R, my - 0.11 * R); c.curve_to(mx + k * 0.18 * R, my - 0.16 * R, mx + k * 0.32 * R, my - 0.06 * R, mx + k * 0.38 * R, my + 0.14 * R); c.stroke()
    if spec.get('beard') == 'stubble':                                        # 剃过的胡茬：下半张脸一片小点
        c.save(); head_path(c, 0, 0, R, spec.get('head', 'round')); c.clip(); c.new_path(); c.set_source_rgba(*bc, 0.55)
        for i in range(9):
            for j in range(6):
                px_ = mx + (i - 4 + 0.5 * (j % 2)) * 0.15 * R; py_ = my - 0.14 * R + j * 0.115 * R
                if abs(px_ - mx) < 0.17 * R and abs(py_ - my) < 0.09 * R: continue
                if j < 2 and abs(px_ - mx) > 0.32 * R: continue
                if py_ - my > 0.52 * R - 0.25 * abs(px_ - mx): continue
                c.arc(px_, py_, 0.024 * R, 0, 2 * PI); c.fill()
        c.restore()
    if spec.get('mole'): c.arc(mx + spec['mole'][0] * R, my + spec['mole'][1] * R, 0.055 * R, 0, 2 * PI); c.set_source_rgb(0.25, 0.14, 0.1); c.fill()
    # 腮红 / 附加符号
    if spec.get('blush'): [c.arc(x, y + 0.24 * R, 0.08 * R, 0, 2 * PI) or c.set_source_rgba(0.95, 0.4, 0.4, 0.45) or c.fill() for (x, y, k) in eyes]
    if 'sweat' in fx:
        x, y = -0.75 * R, -0.35 * R + 0.06 * R * math.sin(t * 6)
        c.move_to(x, y - 0.18 * R); c.curve_to(x + 0.12 * R, y, x + 0.1 * R, y + 0.12 * R, x, y + 0.12 * R); c.curve_to(x - 0.1 * R, y + 0.12 * R, x - 0.12 * R, y, x, y - 0.18 * R)
        fs(c, (0.65, 0.85, 1.0), lw * 0.6)
    if 'tear' in fx:
        for (x, y, k) in eyes:
            ty = y + 0.15 * R + (t * 0.5 % 1) * 0.35 * R
            c.move_to(x, ty - 0.1 * R); c.curve_to(x + 0.06 * R, ty, x + 0.05 * R, ty + 0.07 * R, x, ty + 0.07 * R); c.curve_to(x - 0.05 * R, ty + 0.07 * R, x - 0.06 * R, ty, x, ty - 0.1 * R); fs(c, (0.65, 0.85, 1.0), lw * 0.5)
            c.move_to(x, y + 0.1 * R); c.line_to(x, ty - 0.08 * R); c.set_source_rgba(0.65, 0.85, 1.0, 0.7); c.set_line_width(0.03 * R); c.stroke()
    if 'anger' in fx:
        x, y = 0.75 * R, -0.62 * R; s_ = 0.16 * R * (1 + 0.15 * math.sin(t * 20))
        c.set_source_rgb(0.9, 0.1, 0.08); c.set_line_width(0.05 * R)
        for a in (0, PI / 2, PI, 3 * PI / 2):
            c.save(); c.translate(x, y); c.rotate(a); c.move_to(s_ * 0.3, -s_); c.curve_to(s_ * 0.3, -s_ * 0.3, s_ * 0.3, -s_ * 0.3, s_, -s_ * 0.3); c.stroke(); c.restore()
    if 'shocklines' in fx:
        c.set_source_rgba(0.35, 0.45, 0.85, 0.8); c.set_line_width(0.035 * R)
        for k in range(5): xx = -0.5 * R + k * 0.18 * R; c.move_to(xx, -0.85 * R); c.line_to(xx, -0.45 * R); c.stroke()


def extras_world(c, P, S, J, R, t):
    fx = P.get('fx', ())
    hc = to_world(P, S, J['head'])
    if 'q' in fx:
        c.select_font_face('Noto Serif CJK SC', 0, 1); c.set_font_size(1.7 * R); c.set_source_rgb(0.15, 0.15, 0.2)
        c.move_to(hc[0] + 0.6 * R, hc[1] - 1.1 * R + 6 * math.sin(t * 5)); c.text_path('?'); c.fill_preserve(); c.set_source_rgb(1, 1, 1); c.set_line_width(0.06 * R); c.stroke()
    if 'stars' in fx:
        for k in range(5):
            a = t * 5 + k * 2 * PI / 5; x, y = hc[0] + math.cos(a) * 1.1 * R, hc[1] - 1.05 * R + math.sin(a) * 0.25 * R; s_ = 0.16 * R
            c.save(); c.translate(x, y); c.move_to(0, -s_)
            for j in range(1, 10): rr = s_ if j % 2 == 0 else s_ * 0.45; aa = j * PI / 5; c.line_to(math.sin(aa) * rr, -math.cos(aa) * rr)
            c.close_path(); c.set_source_rgb(1, 0.85, 0.2); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(2); c.stroke(); c.restore()


# ================================================================ 头盔 / 发型
def headgear(c, R, spec, P, t):
    g = spec.get('gear'); vel = P.get('vx', 0)
    if g == 'bawang2': opera.bawang2(c, R, P, t, spec.get('head', 'square')); return
    if g in ('mian', 'guan', 'douli', 'bun', 'oldbun'): opera.hat(c, R, g, spec.get('head', 'round'), t, spec); return
    if spec.get('modern_hair'): opera.modern_hair(c, R, spec)
    if g in ('bajiao', 'junmao', 'helmet', 'strawhat'): opera.modern_cap(c, R, g, spec, t); return
    if g == 'bawang':                                                          # 霸王盔
        c.save(); c.rectangle(-2 * R, -2 * R, 4 * R, 1.62 * R); c.clip(); head_path(c, 0, -0.04 * R, R, spec.get('head', 'square'), 1.07)
        c.set_source(rad(-0.3 * R, -0.8 * R, 0.05 * R, 1.3 * R, [(0, (0.5, 0.48, 0.55)), (0.5, (0.12, 0.11, 0.14)), (1, (0.03, 0.03, 0.04))])); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(0.05 * R); c.stroke(); c.restore()
        c.move_to(-1.05 * R, -0.36 * R); c.line_to(1.08 * R, -0.36 * R); c.set_source(gold_metal(0, -0.42 * R, 0, -0.3 * R)); c.set_line_width(0.13 * R); c.stroke()
        poly(c, [(0.15 * R, -0.4 * R), (0.32 * R, -0.85 * R), (0.49 * R, -0.4 * R)]); fs(c, gold_metal(0.15 * R, -0.85 * R, 0.5 * R, -0.4 * R), 0.03 * R)
        c.arc(0.32 * R, -0.5 * R, 0.07 * R, 0, 2 * PI); c.set_source_rgb(0.85, 0.1, 0.08); c.fill()
        for k in (-1, 1):                                                       # 金翅
            c.move_to(k * 0.85 * R, -0.5 * R); c.curve_to(k * 1.2 * R, -0.75 * R, k * 1.45 * R, -1.0 * R, k * 1.55 * R, -1.35 * R); c.curve_to(k * 1.2 * R, -1.05 * R, k * 1.0 * R, -0.85 * R, k * 0.7 * R, -0.72 * R); c.close_path()
            fs(c, gold_metal(0, -1.35 * R, 0, -0.5 * R), 0.025 * R)
        pompom(c, 0.0, -1.05 * R, 0.16 * R)
        for k in range(16):                                                    # 红缨：随速度往后飘
            a = (k - 8) / 8; sw = 0.12 * R * math.sin(t * 9 + k * 0.5) - vel * 0.0006 * R
            c.move_to(0, -1.12 * R); c.curve_to(-0.2 * R + a * 0.1 * R, -1.5 * R, -0.8 * R + sw + a * 0.15 * R, -1.45 * R, -1.3 * R + sw * 2 + a * 0.2 * R, -1.0 * R + abs(a) * 0.2 * R)
            c.set_source_rgba(0.9 - 0.25 * abs(a), 0.1, 0.07, 1); c.set_line_width(0.05 * R); c.stroke()
    elif g == 'han':                                                           # 汉兵圆盔 + 红缨
        c.save(); c.rectangle(-2 * R, -2 * R, 4 * R, 1.72 * R); c.clip(); head_path(c, 0, -0.03 * R, R, spec.get('head', 'round'), 1.06)
        c.set_source(rad(-0.3 * R, -0.8 * R, 0.05 * R, 1.2 * R, [(0, (0.8, 0.78, 0.76)), (1, (0.3, 0.28, 0.3))])); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(0.05 * R); c.stroke(); c.restore()
        c.move_to(-1.0 * R, -0.28 * R); c.line_to(1.0 * R, -0.28 * R); c.set_source_rgb(0.55, 0.1, 0.08); c.set_line_width(0.1 * R); c.stroke()
        for k in range(8): c.move_to(0, -1.05 * R); c.curve_to(-0.2 * R, -1.3 * R, -0.5 * R - k * 0.04 * R, -1.3 * R, -0.75 * R - k * 0.05 * R, -1.0 * R + k * 0.03 * R); c.set_source_rgb(0.85, 0.12, 0.08); c.set_line_width(0.045 * R); c.stroke()
    elif g == 'headband':                                                      # 樊哙：乱发 + 红抹额
        c.save(); head_path(c, 0, 0, R, spec.get('head', 'wide')); c.clip(); c.rectangle(-2 * R, -2 * R, 4 * R, 1.55 * R); c.set_source_rgb(0.07, 0.06, 0.06); c.fill(); c.restore()
        c.move_to(-1.1 * R, -0.75 * R)
        for k in range(9): c.line_to(-1.1 * R + k * 0.275 * R, -1.15 * R - (0.25 * R if k % 2 else 0));
        c.line_to(1.2 * R, -0.75 * R); c.close_path(); c.set_source_rgb(0.07, 0.06, 0.06); c.fill()
        c.move_to(-1.15 * R, -0.5 * R); c.line_to(1.15 * R, -0.5 * R); c.set_source(lin(0, -0.6 * R, 0, -0.4 * R, [(0, (0.9, 0.2, 0.15)), (1, (0.55, 0.05, 0.04))])); c.set_line_width(0.2 * R); c.stroke()
        for k in range(3): wv = 0.1 * R * math.sin(t * 8 + k); c.move_to(-1.1 * R, -0.5 * R); c.curve_to(-1.4 * R, -0.45 * R + wv, -1.6 * R, -0.3 * R, -1.8 * R + wv, -0.2 * R + k * 0.12 * R); c.set_source_rgb(0.8, 0.12, 0.08); c.set_line_width(0.08 * R); c.stroke()


# ================================================================ 整个人
def draw(c, P, S, spec, t):
    J = joints(P, S); R = J['R']; f = P.get('f', 1); sq = P.get('sq', 0)
    c.save(); c.translate(P['x'], P['y']); c.scale(f, 1); c.translate(0, -0.3 * S); c.rotate(P.get('rot', 0)); c.translate(0, 0.3 * S); c.scale(1 - 0.4 * sq, 1 + sq)
    olw = max(1.6, 0.012 * S); armor = spec.get('armor', (0.15, 0.14, 0.17)); limbc = spec.get('limb', (0.13, 0.12, 0.15)); vel = P.get('vx', 0)
    neck = J['neck']
    # 靠旗 + 披风（身后）
    if spec.get('flags') == 'kao' and P.get('flags', True): opera.kaoqi(c, neck, S, t, P.get('lean', 0))
    elif spec.get('flags'):
        for k, a in enumerate((-0.55, -0.25)):
            base = (neck[0] - 0.08 * S, neck[1] + 0.06 * S); L = 0.55 * S; ang = a + 0.06 * math.sin(t * 7 + k) - 0.15 * P.get('lean', 0)
            tip = (base[0] + math.sin(ang) * L, base[1] - math.cos(ang) * L)
            c.move_to(*base); c.line_to(*tip); c.set_source(gold_metal(0, tip[1], 0, base[1])); c.set_line_width(0.02 * S); c.stroke()
            wv = 0.04 * S * math.sin(t * 10 + k); d = (math.sin(ang), -math.cos(ang)); n = (-d[1], d[0])
            p1 = (tip[0] - n[0] * 0.18 * S + wv, tip[1] - n[1] * 0.18 * S + d[1] * -0.05 * S); p2 = (tip[0] - d[0] * 0.3 * S, tip[1] - d[1] * 0.3 * S)
            poly(c, [tip, p1, p2]); fs(c, lin(tip[0], tip[1], p2[0], p2[1], [(0, (0.18, 0.17, 0.2)), (1, (0.04, 0.04, 0.05))]), olw * 0.8); poly(c, [tip, p1, p2]); c.set_source(gold_metal(0, tip[1], 0, p2[1])); c.set_line_width(olw); c.stroke()
            c.arc(*tip, 0.025 * S, 0, 2 * PI); c.set_source_rgb(0.8, 0.08, 0.06); c.fill()
    if spec.get('cloak'): opera.cloak(c, neck, S, t, vel, spec['cloak'])
    if spec.get('cape') and spec.get('kao'): opera.cape(c, neck, S, t, vel, spec['cape'])
    elif spec.get('cape'):
        cc = spec['cape']; wv = math.sin(t * 6); fl = min(1, abs(vel) / 900)
        a0 = (neck[0] - 0.02 * S, neck[1] + 0.03 * S)
        e1 = (-0.45 * S - 0.45 * S * fl, 0.05 * S - 0.25 * S * fl + 0.05 * S * wv); e2 = (-0.2 * S - 0.3 * S * fl, 0.22 * S - 0.1 * S * fl)
        c.move_to(*a0); c.curve_to(a0[0] - 0.2 * S, a0[1] + 0.05 * S, e1[0] + 0.1 * S, e1[1] - 0.15 * S + 0.04 * S * wv, *e1); c.curve_to(e1[0] + 0.1 * S, e1[1] + 0.1 * S, e2[0] - 0.05 * S, e2[1], *e2); c.line_to(-0.05 * S, 0.1 * S); c.close_path()
        fs(c, lin(a0[0], a0[1], e1[0], e1[1], [(0, cc), (1, tuple(v * 0.5 for v in cc))]), olw)
    # 后臂、后腿
    if spec.get('robe'): opera.sleeve(c, J['shb'], J['elb'], J['hdb'], S, olw, dict(spec, robe=tuple(v * 0.75 for v in spec['robe'])))
    else: limb(c, [J['shb'], J['elb'], J['hdb']], (0.085 * S, 0.075 * S), tuple(v * 0.75 for v in limbc), olw)
    if spec.get('shield') == 'beast': opera.beast_shield(c, J['hdb'][0], J['hdb'][1], S, olw)
    elif spec.get('shield'):
        hb = J['hdb']; c.arc(hb[0], hb[1], 0.2 * S, 0, 2 * PI); fs(c, rad(hb[0] - 0.05 * S, hb[1] - 0.06 * S, 0.01 * S, 0.22 * S, [(0, (0.75, 0.32, 0.18)), (1, (0.35, 0.10, 0.06))]), olw * 1.2)
        c.arc(hb[0], hb[1], 0.07 * S, 0, 2 * PI); c.set_source(gold_metal(hb[0] - 0.07 * S, hb[1] - 0.07 * S, hb[0] + 0.07 * S, hb[1] + 0.07 * S)); c.fill()
        for k in range(8): a = k * PI / 4; c.arc(hb[0] + math.cos(a) * 0.15 * S, hb[1] + math.sin(a) * 0.15 * S, 0.015 * S, 0, 2 * PI); c.fill()
    else: c.arc(*J['hdb'], 0.045 * S, 0, 2 * PI); fs(c, spec.get('skin', (0.96, 0.84, 0.70)), olw * 0.8)
    robe_ = spec.get('robe')
    if robe_: opera.shoe(c, J['ftb'], S, olw, 0.75)
    elif not P.get('ride'):
        limb(c, [J['hpb'], J['knb'], J['ftb']], (0.11 * S, 0.095 * S), tuple(v * 0.75 for v in limbc), olw)
        if spec.get('puttee'): opera.puttee(c, J['knb'], J['ftb'], S, tuple(v * 0.75 for v in spec['puttee']))
        (opera.opera_boot if spec.get('kao') else opera.straw_shoe if spec.get('shoe') == 'straw' else boot)(c, J['knb'], J['ftb'], S, olw, 0.75)
    # 甲裙 + 躯干
    lean = P.get('lean', 0)
    c.save(); c.rotate(lean)
    if spec.get('robe'): opera.robe(c, S, olw, spec, t, lean)
    elif spec.get('uniform'): opera.uniform(c, S, olw, spec)
    if not spec.get('robe') and not spec.get('uniform'):
     poly(c, [(-0.17 * S, -0.02 * S), (0.17 * S, -0.02 * S), (0.2 * S, 0.12 * S), (-0.2 * S, 0.12 * S)]); fs(c, lamellar_tile(tuple(v * 1.1 for v in armor), (int(0.07 * S), int(0.045 * S))), olw)
     rrect(c, -0.17 * S, -0.29 * S, 0.34 * S, 0.3 * S, 0.06 * S)
     pat = scale_tile(base=armor, rim=spec.get('rim', (0.78, 0.58, 0.22)), s=max(10, int(0.06 * S))) if spec.get('scale', True) else armor
     fs(c, pat, olw)
     c.save(); rrect(c, -0.17 * S, -0.29 * S, 0.34 * S, 0.3 * S, 0.06 * S); c.clip(); c.set_source(lin(-0.17 * S, 0, 0.17 * S, 0, [(0, (0, 0, 0, 0.45)), (0.55, (0, 0, 0, 0)), (1, (1, 0.9, 0.7, 0.18))])); c.paint(); c.restore()
     c.move_to(-0.17 * S, -0.27 * S); c.line_to(0.17 * S, -0.27 * S); c.set_source(gold_metal(0, -0.3 * S, 0, -0.24 * S)); c.set_line_width(0.035 * S); c.stroke()
     c.rectangle(-0.18 * S, -0.06 * S, 0.36 * S, 0.06 * S); c.set_source(lin(0, -0.06 * S, 0, 0, [(0, (0.3, 0.2, 0.12)), (1, (0.08, 0.05, 0.03))])); c.fill()
    if spec.get('tiger'): opera.tiger(c, S)
    if spec.get('tabard'): opera.tabard(c, S, spec['tabard'])
    if spec.get('kao'): opera.kao_front(c, S, olw, t)
    elif spec.get('mirror'): c.arc(0.06 * S, -0.16 * S, 0.06 * S, 0, 2 * PI); fs(c, rad(0.05 * S, -0.17 * S, 0.005 * S, 0.065 * S, [(0, (1, 0.97, 0.8)), (0.4, GOLD), (1, GOLD_D)]), olw * 0.8)
    if not spec.get('kao') and not spec.get('robe') and not spec.get('uniform'): beast(c, 0.0, -0.03 * S, 0.04 * S)
    c.restore()
    if spec.get('robe') and P.get('arm_under_head', True): opera.sleeve(c, J['shf'], J['elf'], J['hdf'], S, olw, spec); c.arc(*J['hdf'], 0.045 * S, 0, 2 * PI); fs(c, spec.get('skin', (0.96, 0.84, 0.70)), olw * 0.8)
    # 头
    hc = J['head']
    c.save(); c.translate(*hc); c.rotate(J['hd_a'])
    if spec.get('hairback'): head_path(c, -0.08 * R, 0.05 * R, R, spec.get('head', 'round'), 1.05); c.set_source_rgb(0.07, 0.06, 0.06); c.fill()
    head_path(c, 0, 0, R, spec.get('head', 'round')); sk = spec.get('skin', (0.96, 0.84, 0.70))
    fs(c, rad(0.25 * R, -0.25 * R, 0.1 * R, 1.3 * R, [(0, tuple(min(1, v * 1.04) for v in sk)), (1, tuple(v * 0.86 for v in sk))]), olw * 1.1)
    c.save(); head_path(c, 0, 0, R, spec.get('head', 'round')); c.clip(); c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); c.rectangle(-3 * R, -3 * R, 6 * R, 6 * R); head_path(c, 0.2 * R, -0.14 * R, R, spec.get('head', 'round'))
    c.set_source_rgba(0.6, 0.3, 0.2, 0.22); c.fill(); c.set_fill_rule(cairo.FILL_RULE_WINDING); c.restore()
    face(c, R, spec, P, t)
    headgear(c, R, spec, P, t)
    c.restore()
    # 前腿、前臂、兵器
    if spec.get('robe'): opera.shoe(c, J['ftf'], S, olw)
    else:
        limb(c, [J['hpf'], J['knf'], J['ftf']], (0.11 * S, 0.095 * S), limbc, olw, hi=(1, 1, 1))
        if spec.get('puttee'): opera.puttee(c, J['knf'], J['ftf'], S, spec['puttee'])
        (opera.opera_boot if spec.get('kao') else opera.straw_shoe if spec.get('shoe') == 'straw' else boot)(c, J['knf'], J['ftf'], S, olw, 1.0)
    if spec.get('kao'): opera.flap(c, S, olw, P.get('lean', 0), t, armor)
    kind = spec.get('weapon'); b_, tp, hand = weapon_pts(P, S, J, spec); w = P.get('w', PI)
    if kind == 'ji2': opera.ji2(c, b_, tp, w, S, olw, t)
    elif kind == 'dao': opera.dao(c, hand, w, S, olw)
    elif kind in ('ji', 'spear'):
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(*b_); c.line_to(*tp); c.set_source_rgb(*OL); c.set_line_width(0.035 * S + 2 * olw); c.stroke()
        c.move_to(*b_); c.line_to(*tp); c.set_source(lin(b_[0], b_[1], tp[0], tp[1], [(0, (0.55, 0.32, 0.15)), (1, (0.30, 0.16, 0.07))])); c.set_line_width(0.035 * S); c.stroke()
        c.save(); c.translate(*tp); c.rotate(math.atan2(math.cos(w), math.sin(w))); u = 0.06 * S
        poly(c, [(0, -u * 0.35), (u * 2.4, 0), (0, u * 0.35)]); fs(c, lin(0, -u, 0, u, [(0, (0.97, 0.98, 1)), (1, (0.5, 0.53, 0.6))]), olw * 0.7)
        if kind == 'ji':
            c.move_to(-u * 0.2, u * 0.25); c.curve_to(u * 0.3, u * 1.6, u * 1.5, u * 2.1, u * 2.2, u * 1.6); c.curve_to(u * 1.3, u * 1.5, u * 0.7, u * 1.0, u * 0.6, u * 0.25); c.close_path()
            fs(c, lin(0, 0, 0, u * 2, [(0, (0.97, 0.98, 1)), (1, (0.5, 0.53, 0.6))]), olw * 0.7)
        for k in range(8): c.move_to(-u * 0.3, 0); c.curve_to(-u * 0.8, -u * 0.4 - k * 0.04 * u, -u * 1.2, -u * 0.3 + k * 0.1 * u, -u * 1.7 - 0.2 * u * math.sin(t * 8 + k), -u * 0.1 + k * 0.12 * u); c.set_source_rgb(0.85, 0.1, 0.07); c.set_line_width(0.012 * S); c.stroke()
        c.restore()
    elif kind in ('fan', 'scroll'): opera.prop(c, kind, hand, w, S, olw, t)
    elif kind in ('rifle', 'bayonet'): opera.rifle(c, hand, w, S, olw, kind == 'bayonet')
    elif kind == 'sword':
        c.save(); c.translate(*hand); c.rotate(math.atan2(math.cos(w), math.sin(w)))
        poly(c, [(0, -0.03 * S), (0.4 * S, -0.04 * S), (0.46 * S, 0.0), (0.4 * S, 0.03 * S), (0, 0.025 * S)]); fs(c, lin(0, -0.04 * S, 0, 0.03 * S, [(0, (0.97, 0.98, 1)), (1, (0.5, 0.53, 0.6))]), olw * 0.7)
        c.rectangle(-0.02 * S, -0.06 * S, 0.03 * S, 0.12 * S); c.set_source(gold_metal(0, -0.06 * S, 0, 0.06 * S)); c.fill(); c.restore()
    if spec.get('robe'):
        if not P.get('arm_under_head', True): opera.sleeve(c, J['shf'], J['elf'], J['hdf'], S, olw, spec)
    else: limb(c, [J['shf'], J['elf'], J['hdf']], (0.085 * S, 0.075 * S), limbc, olw, hi=(1, 1, 1))
    if spec.get('robe'): pass
    elif spec.get('kao'): opera.arm_armor(c, J['shf'], J['elf'], J['hdf'], S, olw)
    elif spec.get('uniform'): pass
    else:
      for p in (J['shf'],): c.arc(p[0] + 0.01 * S, p[1] - 0.005 * S, 0.058 * S, 0, 2 * PI); fs(c, gold_metal(p[0] - 0.07 * S, p[1] - 0.07 * S, p[0] + 0.07 * S, p[1] + 0.07 * S) if spec.get('pauldron', True) else limbc, olw)
    c.arc(*J['hdf'], 0.045 * S, 0, 2 * PI); fs(c, spec.get('skin', (0.96, 0.84, 0.70)), olw * 0.8)
    c.restore()
    extras_world(c, P, S, J, R, t)
    return J


def boot(c, kn, ft, S, olw, k=1.0):
    a = math.atan2(ft[1] - kn[1], ft[0] - kn[0]) - PI / 2
    c.save(); c.translate(*ft); c.rotate(a); rrect(c, -0.05 * S, -0.03 * S, 0.13 * S, 0.06 * S, 0.025 * S); fs(c, tuple(v * k for v in (0.12, 0.08, 0.06)), olw); c.restore()


# ================================================================ 角色设定


def head(c, x, y, R, spec, P, t=0.0, olw=None):
    """单独画一个头（大头特写用）。P 里给表情；P['front']=True 时五官居中（正面）。"""
    olw = olw or max(2.0, 0.055 * R); sk = spec.get('skin', (0.96, 0.84, 0.70)); off = 0.0 if P.get('front') else 0.2 * R
    if P.get('front'): spec = dict(spec, _front=True)                         # 头发、帽子也画正面版
    c.save(); c.translate(x, y); c.rotate(P.get('tilt', 0.0))
    head_path(c, 0, 0, R, spec.get('head', 'round'))
    fs(c, rad(off, -0.25 * R, 0.1 * R, 1.3 * R, [(0, tuple(min(1, v * 1.04) for v in sk)), (1, tuple(v * 0.86 for v in sk))]), olw * 1.1)
    if P.get('front'):
        for k in (-1, 1):                                                       # 正面：两只耳朵
            c.save(); c.translate(k * 0.98 * R, 0.08 * R); c.scale(0.55, 1); c.arc(0, 0, 0.22 * R, 0, 2 * PI); c.restore(); fs(c, sk, olw * 0.8)
        head_path(c, 0, 0, R, spec.get('head', 'round')); fs(c, rad(0, -0.25 * R, 0.1 * R, 1.3 * R, [(0, tuple(min(1, v * 1.04) for v in sk)), (1, tuple(v * 0.86 for v in sk))]), olw * 1.1)
    face(c, R, spec, P, t)
    headgear(c, R, spec, P, t)
    c.restore()
