"""精致 Q 版马（侧面），与 rig.py 同一画风：描边、渐变、高光。"""
import math, cairo
from .qrig import limb, lin, rad, gold_metal, rrect, poly, OL
from . import qcostume as opera
PI = math.pi; TAU = 2 * PI


def _fs(c, src, lw):
    if isinstance(src, tuple): c.set_source_rgb(*src)
    else: c.set_source(src)
    c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(lw); c.stroke()


def _V(a, L): return (math.sin(a) * L, math.cos(a) * L)


def legs_pose(gait, ph, rear):
    """返回四条腿 (上段角, 下段角)：顺序 远后, 远前, 近后, 近前"""
    out = []
    for k, (front, off) in enumerate(((False, PI), (True, 0.0), (False, 0.0), (True, PI))):
        if rear > 0.05 and front:
            u, l = 1.0 + 0.3 * math.sin(ph + off), -0.6
        elif rear > 0.05:
            u, l = -0.25 + 0.6 * rear * 0.55 * -1, 0.2
        elif gait == 'gallop':
            s_ = math.sin(ph + off + (0.6 if front else 0)); u = (0.55 if front else 0.5) * s_ + (0.1 if front else -0.05)
            l = u - (0.9 * max(0, -math.cos(ph + off)) if front else -0.6 * max(0, math.cos(ph + off)))
        elif gait == 'walk':
            s_ = math.sin(ph + off + (0.5 if front else 0)); u = 0.25 * s_; l = u - (0.4 * max(0, -math.cos(ph + off)) if front else -0.3 * max(0, math.cos(ph + off)))
        else:
            u, l = (0.03, 0.0) if front else (-0.05, 0.08)
        out.append((front, u, l))
    return out


def horse(c, x, y, h, col=(0.16, 0.17, 0.22), face=1, t=0.0, gait='stand', rear=0.0,
          cloth=(0.75, 0.10, 0.08), sheen=(0.45, 0.5, 0.62), mane=(0.06, 0.06, 0.08), head_a=0.0):
    """(x, y) 蹄底中点；h = 马背高。返回世界坐标鞍点。"""
    f = face; lw = max(1.5, 0.028 * h); ph = t * (12 if gait == 'gallop' else 6)
    bob = (0.05 * h * abs(math.sin(ph)) if gait == 'gallop' else 0.015 * h * abs(math.sin(ph)) if gait == 'walk' else 0.008 * h * math.sin(t * 2))
    c.save(); c.translate(x, y); c.scale(f, 1)
    piv = (-0.42 * h, 0); c.translate(*piv); c.rotate(-rear * 0.6); c.translate(-piv[0], -piv[1])
    c.translate(0, -bob)
    dark = tuple(v * 0.55 for v in col); lite = tuple(min(1, v + 0.5 * (s - v)) for v, s in zip(col, sheen))
    hip_b, hip_f = (-0.38 * h, -0.66 * h), (0.36 * h, -0.64 * h); LU, LL = 0.36 * h, 0.34 * h
    LP = legs_pose(gait, ph, rear)

    def leg(front, u, l, shade):
        hp = hip_f if front else hip_b; hp = (hp[0] + (0.06 * h if shade < 1 else 0), hp[1])
        kn = (hp[0] + _V(u, LU)[0], hp[1] + _V(u, LU)[1]); ft = (kn[0] + _V(l, LL)[0], kn[1] + _V(l, LL)[1])
        cc = tuple(v * shade for v in col)
        limb(c, [hp, kn, ft], (0.13 * h, 0.085 * h), cc, lw, hi=None if shade < 1 else (1, 1, 1))
        c.save(); c.translate(*ft); c.rotate(-l * 0.6); rrect(c, -0.06 * h, -0.05 * h, 0.12 * h, 0.07 * h, 0.02 * h); _fs(c, (0.12, 0.10, 0.09), lw * 0.8)
        c.rectangle(-0.06 * h, -0.075 * h, 0.12 * h, 0.03 * h); c.set_source_rgba(1, 1, 1, 0.75 if col[0] < 0.4 else 0.0); c.fill(); c.restore()   # 白蹄踝（踏雪）

    # 远侧腿
    leg(*LP[0][:1], *LP[0][1:], 0.62); leg(*LP[1][:1], *LP[1][1:], 0.62)
    # 尾巴
    tb = (-0.62 * h, -0.86 * h); sw = math.sin(t * (9 if gait == 'gallop' else 3))
    lift = 0.35 if gait == 'gallop' else 0.0
    for k, (w_, cc) in enumerate(((0.16 * h + 2 * lw, OL), (0.16 * h, mane))):
        c.move_to(*tb); c.curve_to(tb[0] - 0.25 * h, tb[1] - 0.1 * h - lift * 0.2 * h, tb[0] - 0.35 * h - lift * 0.25 * h, tb[1] + 0.2 * h - lift * 0.4 * h + 0.05 * h * sw, tb[0] - 0.28 * h - lift * 0.45 * h, tb[1] + 0.55 * h - lift * 0.55 * h + 0.06 * h * sw)
        c.set_source_rgb(*cc); c.set_line_width(w_); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    for k in range(3):
        c.move_to(tb[0] - 0.05 * h, tb[1] + 0.02 * h); c.curve_to(tb[0] - 0.3 * h, tb[1] - 0.05 * h + k * 0.04 * h, tb[0] - 0.36 * h - lift * 0.25 * h, tb[1] + 0.25 * h - lift * 0.4 * h + k * 0.03 * h, tb[0] - 0.3 * h - lift * 0.45 * h + k * 0.03 * h, tb[1] + 0.5 * h - lift * 0.55 * h + 0.06 * h * sw)
        c.set_source_rgba(*sheen, 0.45); c.set_line_width(0.012 * h); c.stroke()
    # 身体
    c.save(); c.translate(0, -0.84 * h); c.scale(1, 0.56); c.arc(0, 0, 0.62 * h, 0, TAU); c.restore()
    _fs(c, rad(0.1 * h, -1.05 * h, 0.05 * h, 0.8 * h, [(0, lite), (0.55, col), (1, dark)]), lw * 1.1)
    c.save(); c.translate(0, -0.84 * h); c.scale(1, 0.56); c.arc(0, 0, 0.62 * h, 0, TAU); c.restore(); c.save(); c.clip()
    c.move_to(-0.45 * h, -1.0 * h); c.curve_to(-0.2 * h, -1.07 * h, 0.2 * h, -1.07 * h, 0.45 * h, -1.0 * h); c.set_source_rgba(1, 1, 1, 0.22); c.set_line_width(0.04 * h); c.stroke(); c.restore()
    # 近侧腿
    leg(*LP[2][:1], *LP[2][1:], 1.0); leg(*LP[3][:1], *LP[3][1:], 1.0)
    # 脖子 + 头
    na = 0.55 + head_a + (0.08 * math.sin(ph) if gait == 'gallop' else 0) - rear * 0.2
    nb = (0.38 * h, -0.95 * h); hc = (nb[0] + math.sin(na) * 0.42 * h, nb[1] - math.cos(na) * 0.42 * h - 0.05 * h)
    neck = [(0.18 * h, -1.02 * h), (hc[0] - 0.12 * h, hc[1] - 0.12 * h), (hc[0] + 0.05 * h, hc[1] + 0.05 * h), (0.52 * h, -0.72 * h)]
    c.move_to(*neck[0]); c.curve_to(0.3 * h, -1.2 * h, neck[1][0] - 0.05 * h, neck[1][1] + 0.05 * h, *neck[1]); c.line_to(*neck[2]); c.curve_to(hc[0] + 0.05 * h, hc[1] + 0.3 * h, 0.58 * h, -0.85 * h, *neck[3]); c.close_path()
    _fs(c, lin(0.2 * h, 0, 0.6 * h, 0, [(0, dark), (0.5, col), (1, lite)]), lw * 1.1)
    # 鬃毛
    for k in range(7):
        u = k / 6; bx = 0.2 * h + (hc[0] - 0.12 * h - 0.2 * h) * u; by = -1.05 * h + (hc[1] - 0.15 * h + 1.05 * h) * u
        wv = 0.05 * h * math.sin(t * (10 if gait == 'gallop' else 3) + k)
        tip = (bx - 0.2 * h - (0.12 * h if gait == 'gallop' else 0) + wv, by + 0.02 * h - (0.06 * h if gait == 'gallop' else -0.05 * h))
        c.move_to(bx + 0.05 * h, by - 0.02 * h); c.curve_to(bx - 0.05 * h, by - 0.12 * h, tip[0] + 0.05 * h, tip[1] - 0.08 * h, *tip); c.curve_to(tip[0] + 0.08 * h, tip[1] + 0.02 * h, bx - 0.02 * h, by + 0.04 * h, bx + 0.05 * h, by + 0.03 * h); c.close_path()
        _fs(c, lin(bx, by, tip[0], tip[1], [(0, mane), (1, tuple(min(1, v * 2.2) for v in mane))]), lw * 0.7)
    # 头
    c.save(); c.translate(*hc); c.rotate(na * 0.6 - 0.2)
    c.move_to(-0.16 * h, -0.12 * h); c.curve_to(-0.02 * h, -0.2 * h, 0.22 * h, -0.12 * h, 0.34 * h, 0.02 * h); c.curve_to(0.42 * h, 0.12 * h, 0.36 * h, 0.22 * h, 0.24 * h, 0.21 * h)
    c.curve_to(0.08 * h, 0.2 * h, -0.08 * h, 0.16 * h, -0.17 * h, 0.06 * h); c.close_path()
    _fs(c, rad(0.05 * h, -0.08 * h, 0.02 * h, 0.4 * h, [(0, lite), (0.6, col), (1, dark)]), lw * 1.1)
    c.save(); c.translate(0.31 * h, 0.13 * h); c.scale(1, 0.75); c.arc(0, 0, 0.1 * h, 0, TAU); c.restore(); c.set_source_rgba(*sheen, 0.35); c.fill()
    c.save(); c.translate(0.32 * h, 0.1 * h); c.scale(1.2, 0.7); c.arc(0, 0, 0.02 * h, 0, TAU); c.restore(); c.set_source_rgb(*OL); c.fill()       # 鼻孔
    for k, dx in enumerate((-0.07 * h, -0.13 * h)):                                       # 耳
        poly(c, [(dx, -0.12 * h), (dx - 0.02 * h, -0.3 * h + 0.02 * h * math.sin(t * 2 + k)), (dx + 0.07 * h, -0.13 * h)]); _fs(c, col if k == 0 else dark, lw * 0.8)
    c.arc(0.06 * h, -0.03 * h, 0.06 * h, 0, TAU); c.set_source_rgb(*OL); c.fill()            # 大眼
    c.arc(0.045 * h, -0.05 * h, 0.022 * h, 0, TAU); c.set_source_rgb(1, 1, 1); c.fill(); c.arc(0.08 * h, -0.01 * h, 0.01 * h, 0, TAU); c.fill()
    c.move_to(0.01 * h, -0.1 * h); c.line_to(0.11 * h, -0.08 * h); c.set_source_rgb(*OL); c.set_line_width(0.018 * h); c.stroke()   # 眉，显精神
    # 笼头
    c.set_line_width(0.025 * h); c.set_source(gold_metal(0, -0.1 * h, 0, 0.2 * h))
    c.move_to(-0.1 * h, -0.12 * h); c.line_to(-0.04 * h, 0.15 * h); c.stroke(); c.move_to(-0.06 * h, 0.06 * h); c.line_to(0.34 * h, 0.04 * h); c.stroke()
    for p in ((-0.05 * h, 0.06 * h), (0.24 * h, 0.17 * h)): c.arc(*p, 0.03 * h, 0, TAU); c.fill()
    c.restore()
    # 胸前红缨
    px, py = 0.5 * h, -0.8 * h
    for k in range(9):
        a = -0.5 + k * 0.12 + 0.08 * math.sin(t * 6 + k); c.move_to(px, py); c.line_to(px + math.sin(a) * 0.17 * h, py + math.cos(a) * 0.17 * h)
        c.set_source_rgb(0.85, 0.08, 0.06); c.set_line_width(0.02 * h); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    c.arc(px, py, 0.035 * h, 0, TAU); c.set_source(gold_metal(px - 0.04 * h, py - 0.04 * h, px + 0.04 * h, py + 0.04 * h)); c.fill()
    c.move_to(px, py); c.line_to(0.2 * h, -0.98 * h); c.set_source(gold_metal(0, -1, 0, 1)); c.set_line_width(0.022 * h); c.stroke()
    # 鞍鞯
    pth = [(-0.32 * h, -1.07 * h), (0.24 * h, -1.07 * h), (0.28 * h, -0.62 * h), (-0.34 * h, -0.62 * h)]
    c.move_to(*pth[0]); c.curve_to(-0.1 * h, -1.13 * h, 0.1 * h, -1.13 * h, *pth[1]); c.line_to(*pth[2]); c.curve_to(0.05 * h, -0.58 * h, -0.15 * h, -0.58 * h, *pth[3]); c.close_path()
    _fs(c, lin(0, -1.1 * h, 0, -0.6 * h, [(0, cloth), (1, tuple(v * 0.55 for v in cloth))]), lw)
    c.move_to(0.27 * h, -0.66 * h); c.curve_to(0.05 * h, -0.62 * h, -0.15 * h, -0.62 * h, -0.33 * h, -0.66 * h); c.set_source(gold_metal(0, -0.7 * h, 0, -0.6 * h)); c.set_line_width(0.035 * h); c.stroke()
    for k in range(7): c.arc(-0.3 * h + k * 0.095 * h, -0.6 * h + 0.012 * h * math.sin(k * 1.3), 0.018 * h, 0, TAU); c.fill()
    opera.pearl(c, -0.03 * h, -0.85 * h, 0.06 * h, (0.98, 0.8, 0.3))
    c.move_to(-0.26 * h, -1.12 * h); c.curve_to(-0.2 * h, -1.02 * h, 0.12 * h, -1.02 * h, 0.2 * h, -1.14 * h); c.curve_to(0.22 * h, -1.2 * h, 0.12 * h, -1.2 * h, 0.1 * h, -1.13 * h)
    c.curve_to(0.0, -1.08 * h, -0.15 * h, -1.08 * h, -0.2 * h, -1.16 * h); c.close_path(); _fs(c, lin(0, -1.2 * h, 0, -1.05 * h, [(0, (0.55, 0.32, 0.15)), (1, (0.28, 0.14, 0.06))]), lw * 0.8)
    m = c.get_matrix(); sx, sy = m.transform_point(-0.1 * h, -1.1 * h)
    c.restore()
    return (sx, sy)
