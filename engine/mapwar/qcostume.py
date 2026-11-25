"""演义 / 戏曲式夸张扮相部件：霸王盔（雉鸡翎、绒球、额冠、珠串）、大靠（护心镜、靠肚、靠腿、披膊、狮蛮带）、四面靠旗、厚底靴、霸王戟（吞口、月牙、大红缨）、樊哙虎皮、汉兵号衣。
全部画在 rig.draw 的本地坐标里。"""
import math, cairo, numpy as np
from .qdraw import lin, rad, gold_metal, beast, GOLD, GOLD_L, GOLD_D, head_path, rrect, poly
PI = math.pi; TAU = 2 * PI
OL = (0.10, 0.08, 0.08)
RED = (0.80, 0.10, 0.08); DRED = (0.45, 0.04, 0.03)


def fs(c, src, lw, col=OL):
    c.set_source(src) if not isinstance(src, tuple) else c.set_source_rgb(*src); c.fill_preserve(); c.set_source_rgb(*col); c.set_line_width(lw); c.stroke()


def pompom(c, x, y, r, col=(0.85, 0.08, 0.06)):
    for k in range(9): a = k / 9 * TAU; c.arc(x + math.cos(a) * r * 0.42, y + math.sin(a) * r * 0.42, r * 0.62, 0, TAU)
    c.set_source(rad(x, y, 0, r * 1.15, [(0, tuple(min(1, v + 0.3) for v in col)), (0.7, col), (1, tuple(v * 0.5 for v in col))], x - r * 0.3, y - r * 0.4)); c.fill()


def pearl(c, x, y, r, col=(0.98, 0.96, 0.9)):
    c.arc(x, y, r, 0, TAU); c.set_source(rad(x, y, 0, r, [(0, (1, 1, 1)), (1, tuple(v * 0.7 for v in col))], x - r * 0.4, y - r * 0.4)); c.fill()


def gold_rim(c, w, a=1.0):
    c.set_source(gold_metal(-1, -1, 1, 1)); c.set_line_width(w); c.stroke()


# ================================================================ 霸王盔
def bawang2(c, R, P, t, shape='square'):
    vel = P.get('vx', 0); sw = -vel * 0.0005
    # 雉鸡翎（先画，在盔后）
    for k, (ox, L, ph) in enumerate(((-0.15, 4.4, 0.0), (0.12, 4.0, 1.3))):
        x0, y0 = ox * 0.6 * R, -1.25 * R
        pts = []
        for i in range(40):
            u = i / 39; ang = -PI / 2 - 0.25 - u * (2.0 + 0.25 * k) + (0.18 * math.sin(t * 3 + ph + u * 3) + sw) * u
            if i == 0: x, y = x0, y0
            else: x, y = pts[-1][0] + math.cos(ang) * L * R / 39, pts[-1][1] + math.sin(ang) * L * R / 39
            pts.append((x, y))
        for i in range(len(pts) - 1):
            w = 0.14 * R * (1 - 0.6 * i / 40)
            c.move_to(*pts[i]); c.line_to(*pts[i + 1]); c.set_source_rgb(*OL); c.set_line_width(w + 0.05 * R); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        for i in range(len(pts) - 1):
            w = 0.14 * R * (1 - 0.6 * i / 40); band = (i // 2) % 2
            c.move_to(*pts[i]); c.line_to(*pts[i + 1]); c.set_source_rgb(*((0.92, 0.86, 0.68) if band else (0.36, 0.26, 0.16))); c.set_line_width(w); c.stroke()
    # 盔体
    c.save(); c.rectangle(-2 * R, -2.5 * R, 4 * R, 2.12 * R); c.clip(); head_path(c, 0, -0.06 * R, R, shape, 1.1)
    c.set_source(rad(-0.3 * R, -0.85 * R, 0.05 * R, 1.35 * R, [(0, (0.52, 0.5, 0.58)), (0.45, (0.12, 0.11, 0.14)), (1, (0.03, 0.03, 0.04))])); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(0.05 * R); c.stroke()
    for k in (-1, 1):                                                          # 金线卷草
        c.move_to(k * 0.1 * R, -1.05 * R); c.curve_to(k * 0.5 * R, -1.1 * R, k * 0.8 * R, -0.85 * R, k * 0.95 * R, -0.5 * R); c.set_source(gold_metal(0, -1.1 * R, 0, -0.5 * R)); c.set_line_width(0.045 * R); c.stroke()
        c.arc(k * 0.55 * R, -0.85 * R, 0.1 * R, PI * 0.8, PI * 2.4); c.stroke()
    c.restore()
    # 简化：金箍 + 小额饰 + 顶上一颗红缨球，主角是两根雉鸡翎
    c.move_to(-1.05 * R, -0.36 * R); c.line_to(1.1 * R, -0.36 * R); c.set_source(gold_metal(0, -0.43 * R, 0, -0.29 * R)); c.set_line_width(0.13 * R); c.stroke()
    poly(c, [(0.12 * R, -0.42 * R), (0.32 * R, -0.82 * R), (0.52 * R, -0.42 * R)]); fs(c, gold_metal(0.12 * R, -0.82 * R, 0.52 * R, -0.42 * R), 0.03 * R)
    c.arc(0.32 * R, -0.52 * R, 0.08 * R, 0, TAU); c.set_source(rad(0.32 * R, -0.52 * R, 0, 0.09 * R, [(0, (1, 0.6, 0.55)), (1, (0.55, 0.02, 0.02))], 0.29 * R, -0.55 * R)); c.fill()
    c.move_to(0, -1.0 * R); c.line_to(0, -1.4 * R); c.set_source(gold_metal(-0.05 * R, 0, 0.05 * R, 0)); c.set_line_width(0.07 * R); c.stroke()
    pompom(c, 0, -1.1 * R, 0.17 * R)


# ================================================================ 靠旗（四面）
def kaoqi(c, neck, S, t, lean):
    base = (neck[0] - 0.1 * S, neck[1] + 0.08 * S)
    for k, a in enumerate((-0.85, -0.55, -0.25, 0.05)):
        L = 0.78 * S; ang = a + 0.05 * math.sin(t * 6 + k * 0.9) - 0.2 * lean
        tip = (base[0] + math.sin(ang) * L, base[1] - math.cos(ang) * L)
        c.move_to(*base); c.line_to(*tip); c.set_source_rgb(*OL); c.set_line_width(0.028 * S); c.stroke()
        c.move_to(*base); c.line_to(*tip); c.set_source(gold_metal(0, tip[1], 0, base[1])); c.set_line_width(0.017 * S); c.stroke()
        d = (math.sin(ang), -math.cos(ang)); n = (d[1], -d[0])                     # n 指向身后（翻转后画面里朝后）
        wv = 0.05 * S * math.sin(t * 9 + k * 1.1)
        p0 = (tip[0] - d[0] * 0.03 * S, tip[1] - d[1] * 0.03 * S); p2 = (tip[0] - d[0] * 0.42 * S, tip[1] - d[1] * 0.42 * S)
        p1 = (p0[0] - n[0] * 0.24 * S + wv * 0.3, p0[1] - n[1] * 0.24 * S + 0.04 * S + wv)
        c.move_to(*p0); c.curve_to(p0[0] - n[0] * 0.1 * S, p0[1] - n[1] * 0.1 * S + wv * 0.4, p1[0], p1[1] - 0.04 * S, *p1); c.line_to(*p2); c.close_path()
        fs(c, lin(p0[0], p0[1], p2[0], p2[1], [(0, (0.20, 0.18, 0.22)), (1, (0.04, 0.04, 0.05))]), 0.008 * S)
        c.move_to(*p0); c.curve_to(p0[0] - n[0] * 0.1 * S, p0[1] - n[1] * 0.1 * S + wv * 0.4, p1[0], p1[1] - 0.04 * S, *p1); c.line_to(*p2); c.close_path(); gold_rim(c, 0.012 * S)
        cx_, cy_ = (p0[0] + p1[0] + p2[0]) / 3, (p0[1] + p1[1] + p2[1]) / 3
        c.arc(cx_, cy_, 0.045 * S, 0, TAU); c.set_source_rgb(*RED); c.fill(); c.arc(cx_, cy_, 0.045 * S, 0, TAU); gold_rim(c, 0.006 * S)
        c.arc(cx_, cy_, 0.022 * S, 0.3, 5.0); c.set_source(gold_metal(cx_ - 1, cy_ - 1, cx_ + 1, cy_ + 1)); c.set_line_width(0.007 * S); c.stroke()
        for j in range(5):                                                       # 旗边红穗
            u = (j + 0.5) / 5; ex = p1[0] + (p2[0] - p1[0]) * u; ey = p1[1] + (p2[1] - p1[1]) * u
            c.move_to(ex, ey); c.line_to(ex - n[0] * 0.04 * S, ey - n[1] * 0.04 * S + 0.02 * S); c.set_source_rgb(*RED); c.set_line_width(0.01 * S); c.stroke()
        pompom(c, tip[0], tip[1], 0.03 * S)
        poly(c, [(tip[0] + d[0] * 0.02 * S - n[0] * 0.012 * S, tip[1] + d[1] * 0.02 * S - n[1] * 0.012 * S), (tip[0] + d[0] * 0.09 * S, tip[1] + d[1] * 0.09 * S), (tip[0] + d[0] * 0.02 * S + n[0] * 0.012 * S, tip[1] + d[1] * 0.02 * S + n[1] * 0.012 * S)])
        c.set_source(gold_metal(tip[0] - 1, tip[1] - 1, tip[0] + 1, tip[1] + 1)); c.fill()


# ================================================================ 披风（大红绣金边）
def cape(c, neck, S, t, vel, col=(0.72, 0.07, 0.05)):
    wv = math.sin(t * 6); fl = min(1, abs(vel) / 900)
    a0 = (neck[0] - 0.02 * S, neck[1] + 0.02 * S)
    e1 = (-0.55 * S - 0.5 * S * fl, 0.08 * S - 0.3 * S * fl + 0.06 * S * wv); e2 = (-0.25 * S - 0.35 * S * fl, 0.28 * S - 0.12 * S * fl)
    def p():
        c.move_to(*a0); c.curve_to(a0[0] - 0.25 * S, a0[1] + 0.05 * S, e1[0] + 0.12 * S, e1[1] - 0.18 * S + 0.05 * S * wv, *e1)
        c.curve_to(e1[0] + 0.05 * S, e1[1] + 0.12 * S + 0.03 * S * wv, e2[0] - 0.1 * S, e2[1] + 0.02 * S, *e2); c.curve_to(e2[0] + 0.1 * S, e2[1] - 0.05 * S, 0.0, 0.15 * S, -0.04 * S, 0.1 * S); c.close_path()
    p(); fs(c, lin(a0[0], a0[1], e1[0], e1[1], [(0, col), (1, tuple(v * 0.45 for v in col))]), 0.012 * S)
    c.save(); p(); c.clip()
    for k in range(4): c.move_to(a0[0] - 0.05 * S * k, a0[1]); c.curve_to(-0.2 * S - 0.1 * S * k, 0.0, e1[0] * 0.6, e1[1] * 0.6 + 0.08 * S * k, e1[0], e1[1] + 0.06 * S * k); c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(0.03 * S); c.stroke()
    c.restore()
    p(); c.set_source(gold_metal(e1[0], e1[1], a0[0], a0[1])); c.set_line_width(0.012 * S); c.set_dash([0.03 * S, 0.012 * S]); c.stroke(); c.set_dash([])


# ================================================================ 大靠正面
def kao_front(c, S, olw, t):
    # 护项（高领）
    rrect(c, -0.13 * S, -0.33 * S, 0.27 * S, 0.07 * S, 0.02 * S); fs(c, lin(0, -0.33 * S, 0, -0.26 * S, [(0, (0.85, 0.15, 0.1)), (1, DRED)]), olw)
    c.move_to(-0.13 * S, -0.27 * S); c.line_to(0.14 * S, -0.27 * S); c.set_source(gold_metal(0, -0.28 * S, 0, -0.26 * S)); c.set_line_width(0.012 * S); c.stroke()
    # 护心镜（大）
    x, y, r = 0.05 * S, -0.18 * S, 0.075 * S
    c.arc(x, y, r, 0, TAU); fs(c, rad(x, y, 0.004 * S, r, [(0, (1, 0.98, 0.85)), (0.35, GOLD), (1, GOLD_D)], x - r * 0.35, y - r * 0.4), olw)
    for rr in (0.78, 0.55): c.arc(x, y, r * rr, 0, TAU); c.set_source_rgba(0.4, 0.22, 0.05, 0.7); c.set_line_width(0.004 * S); c.stroke()
    c.arc(x, y, r * 0.22, 0, TAU); c.set_source(rad(x, y, 0, r * 0.25, [(0, (1, 0.55, 0.5)), (1, (0.55, 0.02, 0.02))], x - r * 0.08, y - r * 0.08)); c.fill()
    for k in range(8): a = k * TAU / 8; c.arc(x + math.cos(a) * r * 0.66, y + math.sin(a) * r * 0.66, 0.008 * S, 0, TAU); c.set_source_rgb(0.98, 0.95, 0.85); c.fill()
    # 狮蛮带
    c.rectangle(-0.19 * S, -0.075 * S, 0.38 * S, 0.055 * S); c.set_source(gold_metal(0, -0.075 * S, 0, -0.02 * S)); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(olw * 0.8); c.stroke()
    for k in range(-3, 4):
        if k: rrect(c, k * 0.05 * S - 0.016 * S, -0.068 * S, 0.032 * S, 0.04 * S, 0.006 * S); c.set_source(lin(0, -0.07 * S, 0, -0.03 * S, [(0, (0.6, 0.85, 0.7)), (1, (0.2, 0.45, 0.35))])); c.fill()
    # 靠肚：腰下红绣兽面
    c.move_to(-0.13 * S, -0.02 * S); c.line_to(0.15 * S, -0.02 * S); c.curve_to(0.17 * S, 0.06 * S, 0.12 * S, 0.12 * S, 0.01 * S, 0.14 * S); c.curve_to(-0.1 * S, 0.12 * S, -0.15 * S, 0.06 * S, -0.13 * S, -0.02 * S); c.close_path()
    fs(c, lin(0, -0.02 * S, 0, 0.14 * S, [(0, (0.88, 0.16, 0.12)), (1, DRED)]), olw)
    for k in range(3): c.arc(0.01 * S, 0.14 * S, 0.035 * S + k * 0.018 * S, PI * 1.15, PI * 1.85); c.set_source_rgba(*GOLD, 0.9); c.set_line_width(0.006 * S); c.stroke()
    beast(c, 0.01 * S, 0.045 * S, 0.045 * S)


def flap(c, S, olw, lean, t, armor):
    """靠腿：从腰间垂到膝下的两片甲（画在前腿之上）。"""
    c.save(); c.rotate(lean * 0.5)
    for k, (x0, rot) in enumerate(((0.07 * S, -0.08), (-0.06 * S, 0.06))):
        c.save(); c.translate(x0, 0.0); c.rotate(rot + 0.03 * math.sin(t * 5 + k))
        path = [(-0.07 * S, -0.02 * S), (0.07 * S, -0.02 * S), (0.09 * S, 0.2 * S), (0.0, 0.24 * S), (-0.09 * S, 0.2 * S)]
        poly(c, path); from .qdraw import scale_tile
        fs(c, scale_tile(base=armor, rim=(0.8, 0.6, 0.22), s=max(8, int(0.045 * S))), olw)
        poly(c, path); c.set_source(gold_metal(-1, -1, 1, 1)); c.set_line_width(0.012 * S); c.stroke()
        for j in range(7): xx = -0.08 * S + j * 0.027 * S; yy = 0.2 * S + (0.04 * S if j == 3 else 0.02 * S); c.move_to(xx, yy); c.line_to(xx + 0.004 * S, yy + 0.05 * S); c.set_source_rgb(*RED); c.set_line_width(0.012 * S); c.stroke()
        c.restore()
    c.restore()


def arm_armor(c, sh, el, hd, S, olw):
    """披膊三层 + 吞肩兽 + 护腕。"""
    a = math.atan2(el[1] - sh[1], el[0] - sh[0])
    for j in (2, 1, 0):
        c.save(); c.translate(sh[0] + math.cos(a) * 0.03 * S * j, sh[1] + math.sin(a) * 0.03 * S * j); c.rotate(a - PI / 2)
        c.move_to(-0.075 * S, -0.01 * S); c.curve_to(-0.07 * S, 0.06 * S, 0.07 * S, 0.06 * S, 0.075 * S, -0.01 * S); c.curve_to(0.05 * S, 0.0, -0.05 * S, 0.0, -0.075 * S, -0.01 * S); c.close_path()
        fs(c, lin(0, -0.01 * S, 0, 0.06 * S, [(0, (0.32, 0.30, 0.36)), (1, (0.05, 0.05, 0.06))]), olw * 0.8)
        c.move_to(-0.07 * S, 0.02 * S); c.curve_to(-0.06 * S, 0.055 * S, 0.06 * S, 0.055 * S, 0.07 * S, 0.02 * S); c.set_source(gold_metal(0, 0.02 * S, 0, 0.05 * S)); c.set_line_width(0.01 * S); c.stroke()
        c.restore()
    beast(c, sh[0] + 0.005 * S, sh[1] - 0.01 * S, 0.055 * S)
    b = math.atan2(hd[1] - el[1], hd[0] - el[0]); px, py = el[0] + (hd[0] - el[0]) * 0.62, el[1] + (hd[1] - el[1]) * 0.62
    c.save(); c.translate(px, py); c.rotate(b); rrect(c, -0.035 * S, -0.045 * S, 0.07 * S, 0.09 * S, 0.012 * S); fs(c, gold_metal(-0.03 * S, -0.04 * S, 0.03 * S, 0.04 * S), olw * 0.8)
    for k in (-1, 1): c.arc(k * 0.018 * S, 0, 0.006 * S, 0, TAU); c.set_source_rgb(0.45, 0.25, 0.05); c.fill()
    c.restore()


def opera_boot(c, kn, ft, S, olw, k=1.0):
    a = math.atan2(ft[1] - kn[1], ft[0] - kn[0]) - PI / 2
    c.save(); c.translate(*ft); c.rotate(a)
    rrect(c, -0.06 * S, -0.06 * S, 0.15 * S, 0.075 * S, 0.03 * S); fs(c, tuple(v * k for v in (0.10, 0.08, 0.10)), olw)
    rrect(c, -0.065 * S, 0.01 * S, 0.165 * S, 0.045 * S, 0.012 * S); fs(c, tuple(v * k for v in (0.96, 0.94, 0.9)), olw)
    c.move_to(-0.05 * S, -0.03 * S); c.line_to(0.08 * S, -0.03 * S); c.set_source(gold_metal(0, -0.04 * S, 0, -0.02 * S)); c.set_line_width(0.01 * S); c.stroke()
    c.restore()


# ================================================================ 霸王戟（华丽）
def ji2(c, b_, tp, w, S, olw, t):
    d = (math.sin(w), math.cos(w)); L = math.hypot(tp[0] - b_[0], tp[1] - b_[1])
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(*b_); c.line_to(*tp); c.set_source_rgb(*OL); c.set_line_width(0.04 * S + 2 * olw); c.stroke()
    c.move_to(*b_); c.line_to(*tp); c.set_source(lin(b_[0], b_[1], tp[0], tp[1], [(0, (0.45, 0.06, 0.05)), (1, (0.62, 0.10, 0.07))])); c.set_line_width(0.04 * S); c.stroke()
    for k in range(1, 8):                                                      # 金箍
        u = k / 8; x, y = b_[0] + (tp[0] - b_[0]) * u, b_[1] + (tp[1] - b_[1]) * u
        c.move_to(x - d[1] * 0.024 * S, y + d[0] * 0.024 * S); c.line_to(x + d[1] * 0.024 * S, y - d[0] * 0.024 * S); c.set_source(gold_metal(x - 1, y - 1, x + 1, y + 1)); c.set_line_width(0.012 * S); c.stroke()
    c.save(); c.translate(*tp); c.rotate(math.atan2(d[1], d[0])); u = 0.085 * S
    # 大红缨（蓬松）
    for k in range(22):
        a = (k - 11) / 11; c.move_to(-0.1 * u, 0); c.curve_to(-0.6 * u, a * 0.6 * u, -1.1 * u, a * 1.1 * u, -1.7 * u - 0.3 * u * math.sin(t * 7 + k), a * 1.4 * u + 0.4 * u)
        c.set_source_rgb(0.9 - 0.25 * abs(a), 0.08, 0.06); c.set_line_width(0.016 * S); c.stroke()
    # 吞口（兽首金件）
    c.move_to(-0.1 * u, -0.55 * u); c.curve_to(0.4 * u, -0.75 * u, 0.9 * u, -0.5 * u, 1.0 * u, 0); c.curve_to(0.9 * u, 0.5 * u, 0.4 * u, 0.75 * u, -0.1 * u, 0.55 * u); c.close_path()
    fs(c, gold_metal(0, -0.7 * u, 0, 0.7 * u), olw * 0.8)
    c.arc(0.45 * u, -0.2 * u, 0.12 * u, 0, TAU); c.set_source_rgb(0.85, 0.1, 0.05); c.fill()
    # 枪尖（长菱形）
    poly(c, [(0.9 * u, -0.32 * u), (3.6 * u, 0), (0.9 * u, 0.32 * u), (1.3 * u, 0)]); fs(c, lin(0, -0.32 * u, 0, 0.32 * u, [(0, (0.98, 0.99, 1)), (0.5, (0.78, 0.82, 0.9)), (1, (0.45, 0.48, 0.55))]), olw * 0.7)
    c.move_to(1.2 * u, 0); c.line_to(3.3 * u, 0); c.set_source_rgba(1, 1, 1, 0.7); c.set_line_width(0.006 * S); c.stroke()
    # 月牙（大、带镂空）
    c.move_to(0.6 * u, 0.4 * u); c.curve_to(0.6 * u, 2.2 * u, 2.6 * u, 2.8 * u, 3.3 * u, 1.6 * u); c.curve_to(2.6 * u, 2.0 * u, 1.6 * u, 1.6 * u, 1.5 * u, 0.45 * u); c.close_path()
    fs(c, lin(0, 0.4 * u, 0, 2.6 * u, [(0, (0.98, 0.99, 1)), (1, (0.5, 0.53, 0.62))]), olw * 0.7)
    c.arc(1.4 * u, 1.3 * u, 0.22 * u, 0, TAU); c.set_source_rgb(0.25, 0.25, 0.3); c.fill()
    c.move_to(0.8 * u, 0.6 * u); c.curve_to(0.85 * u, 1.9 * u, 2.3 * u, 2.4 * u, 3.0 * u, 1.75 * u); c.set_source_rgba(1, 1, 1, 0.6); c.set_line_width(0.006 * S); c.stroke()
    c.restore()


# ================================================================ 樊哙：虎皮 + 兽面盾 + 大砍刀；汉兵号衣
def tiger(c, S):
    c.save(); rrect(c, -0.17 * S, -0.29 * S, 0.34 * S, 0.3 * S, 0.06 * S); c.clip()
    c.set_source_rgb(0.85, 0.52, 0.18); c.paint()
    for k in range(9):
        y = -0.28 * S + k * 0.035 * S; c.move_to(-0.18 * S, y); c.curve_to(-0.08 * S, y + 0.02 * S, -0.02 * S, y - 0.015 * S, 0.06 * S + (k % 3) * 0.02 * S, y + 0.01 * S); c.line_to(0.02 * S, y + 0.02 * S)
        c.curve_to(-0.04 * S, y + 0.01 * S, -0.1 * S, y + 0.03 * S, -0.18 * S, y + 0.02 * S); c.close_path(); c.set_source_rgb(0.12, 0.08, 0.05); c.fill()
    c.set_source(lin(-0.17 * S, 0, 0.17 * S, 0, [(0, (0, 0, 0, 0.4)), (0.6, (0, 0, 0, 0)), (1, (1, 1, 1, 0.12))])); c.paint(); c.restore()
    rrect(c, -0.17 * S, -0.29 * S, 0.34 * S, 0.3 * S, 0.06 * S); c.set_source_rgb(*OL); c.set_line_width(0.012 * S); c.stroke()


def beast_shield(c, x, y, S, olw):
    r = 0.22 * S; c.arc(x, y, r, 0, TAU); fs(c, rad(x, y, 0.01 * S, r, [(0, (0.55, 0.22, 0.12)), (1, (0.25, 0.08, 0.05))], x - r * 0.3, y - r * 0.3), olw * 1.2)
    c.arc(x, y, r * 0.93, 0, TAU); c.set_source(gold_metal(x - r, y - r, x + r, y + r)); c.set_line_width(0.02 * S); c.stroke()
    for k in range(12): a = k * TAU / 12; c.arc(x + math.cos(a) * r * 0.82, y + math.sin(a) * r * 0.82, 0.012 * S, 0, TAU); c.set_source(gold_metal(x - 1, y - 1, x + 1, y + 1)); c.fill()
    beast(c, x, y, r * 0.62)


def dao(c, hand, w, S, olw):
    c.save(); c.translate(*hand); c.rotate(math.atan2(math.cos(w), math.sin(w)))
    c.move_to(0.05 * S, -0.022 * S); c.line_to(0.56 * S, -0.03 * S); c.line_to(0.64 * S, -0.005 * S); c.curve_to(0.6 * S, 0.06 * S, 0.45 * S, 0.085 * S, 0.3 * S, 0.06 * S); c.curve_to(0.18 * S, 0.042 * S, 0.1 * S, 0.03 * S, 0.05 * S, 0.026 * S); c.close_path()
    fs(c, lin(0, -0.03 * S, 0, 0.08 * S, [(0, (0.55, 0.58, 0.66)), (0.35, (0.85, 0.88, 0.94)), (1, (0.98, 0.99, 1))]), olw * 0.8)
    c.move_to(0.06 * S, -0.012 * S); c.line_to(0.55 * S, -0.018 * S); c.set_source_rgba(0.3, 0.3, 0.35, 0.6); c.set_line_width(0.005 * S); c.stroke()
    for k in range(3): c.arc(0.12 * S + k * 0.07 * S, -0.04 * S, 0.012 * S, 0, TAU); c.set_source(gold_metal(-1, -1, 1, 1)); c.set_line_width(0.005 * S); c.stroke()
    rrect(c, -0.02 * S, -0.06 * S, 0.04 * S, 0.12 * S, 0.01 * S); fs(c, gold_metal(0, -0.06 * S, 0, 0.06 * S), olw * 0.7)
    c.rectangle(-0.12 * S, -0.015 * S, 0.1 * S, 0.03 * S); c.set_source_rgb(0.35, 0.1, 0.06); c.fill()
    c.arc(-0.14 * S, 0, 0.025 * S, 0, TAU); c.set_source(gold_metal(-1, -1, 1, 1)); c.set_line_width(0.008 * S); c.stroke()
    for k in range(3): c.move_to(-0.14 * S, 0.02 * S); c.curve_to(-0.16 * S, 0.06 * S, -0.2 * S - k * 0.02 * S, 0.08 * S, -0.22 * S - k * 0.03 * S, 0.12 * S); c.set_source_rgb(*RED); c.set_line_width(0.012 * S); c.stroke()
    c.restore()


def tabard(c, S, ch='汉'):
    c.arc(0.02 * S, -0.15 * S, 0.075 * S, 0, TAU); fs(c, (0.96, 0.92, 0.82), 0.008 * S)
    c.select_font_face('Noto Serif CJK SC', 0, 1); c.set_font_size(0.1 * S); e = c.text_extents(ch); c.move_to(0.02 * S - e.width / 2 - e.x_bearing, -0.15 * S - e.height / 2 - e.y_bearing)
    c.set_source_rgb(0.75, 0.1, 0.08); c.show_text(ch); c.new_path()


# ================================================================ 文官 / 帝王 / 女子：长袍、帽冠、发髻
def robe(c, S, olw, spec, t, lean=0.0):
    col = spec.get('robe', (0.15, 0.13, 0.16)); collar = spec.get('collar', (0.80, 0.14, 0.10)); trim = spec.get('trim', GOLD)
    sway = 0.012 * S * math.sin(t * 3)
    pth = [(-0.16 * S, -0.3 * S), (0.17 * S, -0.3 * S), (0.27 * S + sway, 0.31 * S), (-0.27 * S + sway, 0.31 * S)]
    poly(c, pth); fs(c, lin(-0.27 * S, 0, 0.27 * S, 0, [(0, tuple(v * 0.6 for v in col)), (0.6, col), (1, tuple(min(1, v * 1.35) for v in col))]), olw)
    c.save(); poly(c, pth); c.clip()
    for k in range(-3, 4): c.move_to(k * 0.06 * S, -0.1 * S); c.line_to(k * 0.08 * S + sway, 0.31 * S); c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(0.01 * S); c.stroke()
    c.rectangle(-0.3 * S, 0.27 * S, 0.6 * S, 0.04 * S); c.set_source(gold_metal(0, 0.27 * S, 0, 0.31 * S) if trim == GOLD else lin(0, 0, 0, 1, [(0, trim), (1, trim)])); c.fill()
    if spec.get('bixi'):                                                        # 蔽膝（帝王）
        poly(c, [(0.0, -0.02 * S), (0.13 * S, -0.02 * S), (0.16 * S + sway, 0.26 * S), (-0.02 * S + sway, 0.26 * S)]); fs(c, lin(0, 0, 0, 0.26 * S, [(0, (0.85, 0.14, 0.1)), (1, DRED)]), olw * 0.7)
        for j in range(3): pearl(c, 0.07 * S + sway * 0.5, 0.05 * S + j * 0.07 * S, 0.018 * S, (0.98, 0.8, 0.3))
    c.restore()
    # 交领
    for (a, b) in (((-0.07 * S, -0.3 * S), (0.06 * S, -0.08 * S)), ((0.12 * S, -0.3 * S), (0.0, -0.12 * S))):
        c.move_to(*a); c.line_to(*b); c.set_source_rgb(*OL); c.set_line_width(0.05 * S); c.stroke(); c.move_to(*a); c.line_to(*b); c.set_source_rgb(*collar); c.set_line_width(0.035 * S); c.stroke()
    c.rectangle(-0.18 * S, -0.06 * S, 0.37 * S, 0.045 * S); c.set_source_rgb(*spec.get('belt', collar)); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(olw * 0.7); c.stroke()
    if spec.get('emblem'):                                                      # 金色团纹
        cx_, cy_ = -0.08 * S, -0.18 * S
        for k in range(6): a = k / 6 * TAU; pearl(c, cx_ + math.cos(a) * 0.03 * S, cy_ + math.sin(a) * 0.03 * S, 0.012 * S, (0.98, 0.8, 0.3))
        pearl(c, cx_, cy_, 0.016 * S, (0.98, 0.8, 0.3))
    if spec.get('pibo'):                                                        # 披帛
        for k in (-1, 1):
            c.move_to(-0.12 * S, -0.28 * S); c.curve_to(-0.35 * S, -0.1 * S + 0.05 * S * math.sin(t * 2 + k), -0.25 * S, 0.15 * S, -0.42 * S + 0.04 * S * math.sin(t * 1.6 + k), 0.35 * S + k * 0.03 * S)
            c.set_source_rgba(0.95, 0.55, 0.65, 0.85); c.set_line_width(0.03 * S); c.stroke()


def sleeve(c, sh, el, hd, S, olw, spec):
    col = spec.get('robe', (0.15, 0.13, 0.16)); cuff = spec.get('collar', (0.8, 0.14, 0.1))
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    dr = [el, hd, (hd[0] - 0.02 * S, hd[1] + 0.11 * S), (el[0] - 0.01 * S, el[1] + 0.06 * S)]          # 下垂的宽袖
    for w, cc in ((0.085 * S + 2 * olw, OL), (0.085 * S, col)):
        c.move_to(*sh); c.line_to(*el); c.line_to(*hd); c.set_source_rgb(*cc); c.set_line_width(w); c.stroke()
        poly(c, dr); c.set_source_rgb(*cc); c.fill_preserve(); c.set_line_width(w * 0.6 if cc == OL else 0.001); c.stroke()
    poly(c, dr); c.set_source_rgba(0, 0, 0, 0.12); c.fill()
    dx, dy = hd[0] - el[0], hd[1] - el[1]; L = math.hypot(dx, dy) + 1e-6; ux, uy = dx / L, dy / L
    cx, cy = hd[0] - ux * 0.02 * S, hd[1] - uy * 0.02 * S
    c.move_to(cx - uy * 0.07 * S, cy + ux * 0.07 * S); c.line_to(cx + uy * 0.07 * S, cy - ux * 0.07 * S); c.set_source_rgb(*cuff); c.set_line_width(0.04 * S); c.stroke()


def shoe(c, ft, S, olw, k=1.0):
    c.save(); c.translate(*ft); rrect(c, -0.05 * S, -0.03 * S, 0.13 * S, 0.055 * S, 0.025 * S); fs(c, tuple(v * k for v in (0.12, 0.08, 0.08)), olw); c.restore()


def hair(c, R, shape, col=(0.07, 0.06, 0.06), line=-0.42):
    c.save(); head_path(c, 0, 0, R, shape); c.clip(); c.move_to(-1.2 * R, line * R + 0.25 * R)
    c.curve_to(-0.4 * R, (line - 0.12) * R, 0.4 * R, (line - 0.05) * R, 1.2 * R, (line + 0.1) * R); c.line_to(1.2 * R, -1.3 * R); c.line_to(-1.2 * R, -1.3 * R); c.close_path(); c.set_source_rgb(*col); c.fill(); c.restore()
    head_path(c, 0, 0, R, shape); c.set_source_rgb(*OL); c.set_line_width(0.05 * R); c.stroke()


def hat(c, R, kind, shape, t, spec):
    hc = spec.get('hair', (0.07, 0.06, 0.06))
    if kind in ('mian', 'guan', 'douli'): hair(c, R, shape, hc)
    if kind == 'mian':
        rrect(c, -0.42 * R, -1.45 * R, 0.84 * R, 0.62 * R, 0.06 * R); fs(c, lin(-0.42 * R, 0, 0.42 * R, 0, [(0, (0.25, 0.22, 0.26)), (1, (0.05, 0.05, 0.06))]), 0.04 * R)
        c.move_to(-1.0 * R, -0.95 * R); c.line_to(1.05 * R, -1.05 * R); c.set_source(gold_metal(0, -1.1 * R, 0, -0.9 * R)); c.set_line_width(0.07 * R); c.stroke()
        poly(c, [(-1.35 * R, -1.42 * R), (1.45 * R, -1.62 * R), (1.48 * R, -1.48 * R), (-1.32 * R, -1.28 * R)]); fs(c, lin(0, -1.6 * R, 0, -1.3 * R, [(0, (0.3, 0.28, 0.32)), (1, (0.04, 0.04, 0.05))]), 0.04 * R)
        for i, x in enumerate(np.linspace(0.5, 1.4, 6)):                       # 前旒
            y0 = -1.5 * R - (x - 0.5) * 0.05 * R; sw = 0.04 * R * math.sin(t * 3 + i)
            c.move_to(x * R, y0); c.line_to(x * R + sw, y0 + 0.95 * R); c.set_source_rgba(0.2, 0.15, 0.1, 0.8); c.set_line_width(0.012 * R); c.stroke()
            for j in range(5): pearl(c, x * R + sw * j / 5, y0 + 0.15 * R + j * 0.18 * R, 0.055 * R, ((0.9, 0.2, 0.15), (0.98, 0.92, 0.6), (0.3, 0.65, 0.5), (0.98, 0.98, 0.95))[(i + j) % 4])
        for i, x in enumerate(np.linspace(-1.25, -0.7, 4)):
            y0 = -1.33 * R; c.move_to(x * R, y0); c.line_to(x * R, y0 + 0.75 * R); c.set_source_rgba(0.2, 0.15, 0.1, 0.8); c.set_line_width(0.012 * R); c.stroke()
            for j in range(4): pearl(c, x * R, y0 + 0.15 * R + j * 0.17 * R, 0.05 * R, ((0.9, 0.2, 0.15), (0.98, 0.92, 0.6))[(i + j) % 2])
    elif kind == 'guan':
        poly(c, [(-0.35 * R, -0.85 * R), (-0.05 * R, -1.65 * R), (0.42 * R, -1.58 * R), (0.45 * R, -0.85 * R)]); fs(c, lin(-0.35 * R, 0, 0.45 * R, 0, [(0, (0.26, 0.24, 0.28)), (1, (0.05, 0.05, 0.06))]), 0.04 * R)
        c.move_to(-0.6 * R, -1.05 * R); c.line_to(0.75 * R, -1.15 * R); c.set_source(gold_metal(0, -1.2 * R, 0, -1.0 * R)); c.set_line_width(0.06 * R); c.stroke()
    elif kind == 'douli':
        poly(c, [(-1.6 * R, -0.35 * R), (0.0, -1.5 * R), (1.7 * R, -0.35 * R)]); fs(c, lin(0, -1.5 * R, 0, -0.35 * R, [(0, (0.86, 0.74, 0.48)), (1, (0.6, 0.48, 0.28))]), 0.04 * R)
        for k in (-0.9, -0.45, 0.45, 0.9): c.move_to(0, -1.45 * R); c.line_to(k * 1.6 * R, -0.4 * R); c.set_source_rgba(0.35, 0.25, 0.12, 0.6); c.set_line_width(0.02 * R); c.stroke()
    elif kind in ('bun', 'oldbun'):
        hair(c, R, shape, hc, line=-0.35)
        if kind == 'bun':
            for (bx, by, r) in ((-0.3 * R, -1.12 * R, 0.45 * R), (0.25 * R, -1.22 * R, 0.38 * R)):
                c.arc(bx, by, r, 0, TAU); c.set_source(rad(bx, by, 0, r, [(0, (0.25, 0.22, 0.26)), (1, hc)], bx - r * 0.3, by - r * 0.4)); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(0.04 * R); c.stroke()
            c.move_to(-0.7 * R, -1.0 * R); c.line_to(0.75 * R, -1.45 * R); c.set_source(gold_metal(0, -1.45 * R, 0, -1.0 * R)); c.set_line_width(0.06 * R); c.stroke()
            for j in range(3): sw = 0.05 * R * math.sin(t * 3 + j); px = 0.6 * R - j * 0.12 * R; c.move_to(px, -1.4 * R + j * 0.04 * R); c.line_to(px + sw, -0.95 * R + j * 0.05 * R); c.set_source(gold_metal(0, -1.4 * R, 0, -0.9 * R)); c.set_line_width(0.02 * R); c.stroke(); pearl(c, px + sw, -0.92 * R + j * 0.05 * R, 0.06 * R, (0.95, 0.25, 0.3))
            for k in range(5): a = k / 5 * TAU; c.arc(-0.75 * R + math.cos(a) * 0.1 * R, -0.75 * R + math.sin(a) * 0.1 * R, 0.09 * R, 0, TAU); c.set_source_rgb(0.95, 0.45, 0.55); c.fill()
            c.arc(-0.75 * R, -0.75 * R, 0.06 * R, 0, TAU); c.set_source(gold_metal(-1, -1, 1, 1)); c.fill()
        else:
            c.arc(-0.1 * R, -1.1 * R, 0.3 * R, 0, TAU); c.set_source_rgb(*hc); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(0.04 * R); c.stroke()
            c.move_to(-0.5 * R, -1.1 * R); c.line_to(0.35 * R, -1.15 * R); c.set_source(gold_metal(0, -1.2 * R, 0, -1.0 * R)); c.set_line_width(0.05 * R); c.stroke()


def lady_eyes(c, eyes, R, t):
    for (x, y, k) in eyes:
        r = 0.12 * R * k
        c.save(); c.translate(x, y); c.scale(1, 1.2); c.arc(0, 0, r, 0, TAU); c.restore(); c.set_source_rgb(*OL); c.fill()
        c.arc(x - r * 0.35, y - r * 0.4, r * 0.35, 0, TAU); c.set_source_rgb(1, 1, 1); c.fill()
        c.set_source_rgb(*OL); c.set_line_width(0.03 * R)
        for j in range(3): a = -0.4 - j * 0.35; c.move_to(x + r * 0.9, y - r * 0.6); c.line_to(x + r * 0.9 + math.cos(a) * r * 0.9, y - r * 0.6 + math.sin(a) * r * 0.9); c.stroke()


def prop(c, kind, hand, w, S, olw, t):
    c.save(); c.translate(*hand); c.rotate(math.atan2(math.cos(w), math.sin(w)))
    if kind == 'fan':                                                           # 羽扇
        c.move_to(0, 0); c.line_to(0.12 * S, 0); c.set_source_rgb(0.5, 0.3, 0.15); c.set_line_width(0.02 * S); c.stroke()
        c.move_to(0.1 * S, 0); c.curve_to(0.2 * S, -0.16 * S, 0.38 * S, -0.12 * S, 0.4 * S, 0); c.curve_to(0.38 * S, 0.12 * S, 0.2 * S, 0.16 * S, 0.1 * S, 0); fs(c, lin(0.1 * S, 0, 0.4 * S, 0, [(0, (0.85, 0.85, 0.82)), (1, (1, 1, 1))]), olw * 0.8)
        for k in range(-3, 4): c.move_to(0.11 * S, 0); c.line_to(0.38 * S, k * 0.03 * S); c.set_source_rgba(0.5, 0.5, 0.5, 0.5); c.set_line_width(0.004 * S); c.stroke()
    elif kind == 'scroll':                                                      # 竹简
        c.rotate(-math.atan2(math.cos(w), math.sin(w)))
        rrect(c, -0.12 * S, -0.04 * S, 0.24 * S, 0.1 * S, 0.02 * S); fs(c, lin(0, -0.04 * S, 0, 0.06 * S, [(0, (0.92, 0.82, 0.55)), (1, (0.7, 0.58, 0.32))]), olw * 0.8)
        for k in range(1, 8): c.move_to(-0.12 * S + k * 0.03 * S, -0.04 * S); c.line_to(-0.12 * S + k * 0.03 * S, 0.06 * S); c.set_source_rgba(0.35, 0.25, 0.1, 0.6); c.set_line_width(0.004 * S); c.stroke()
    c.restore()


# ================================================================ 近现代：军装、军帽、步枪、绑腿
def uniform(c, S, olw, spec):
    """近现代军装上衣：立领、四个口袋、纽扣、皮带（可选武装带）。画在 qrig.draw 的躯干坐标里。"""
    col = spec.get('uniform', (0.42, 0.45, 0.42)); dk = tuple(v * 0.7 for v in col); hi = tuple(min(1, v * 1.25) for v in col)
    poly(c, [(-0.17 * S, -0.04 * S), (0.17 * S, -0.04 * S), (0.19 * S, 0.1 * S), (-0.19 * S, 0.1 * S)]); fs(c, lin(-0.2 * S, 0, 0.2 * S, 0, [(0, dk), (1, col)]), olw)      # 上衣下摆
    rrect(c, -0.17 * S, -0.30 * S, 0.34 * S, 0.30 * S, 0.06 * S); fs(c, lin(-0.17 * S, 0, 0.17 * S, 0, [(0, dk), (0.6, col), (1, hi)]), olw)
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(0.006 * S); c.move_to(0.04 * S, -0.28 * S); c.line_to(0.04 * S, 0.08 * S); c.stroke()
    for k in range(4): c.arc(0.06 * S, -0.24 * S + k * 0.07 * S, 0.011 * S, 0, 2 * PI); c.set_source_rgb(*spec.get('button', (0.25, 0.22, 0.18))); c.fill()
    for px_, py_ in ((-0.1 * S, -0.22 * S), (-0.1 * S, -0.04 * S)):                                                   # 口袋
        rrect(c, px_ - 0.045 * S, py_, 0.09 * S, 0.075 * S, 0.012 * S); c.set_source_rgba(0, 0, 0, 0.12); c.fill_preserve(); c.set_source_rgba(0, 0, 0, 0.35); c.set_line_width(0.004 * S); c.stroke()
        poly(c, [(px_ - 0.05 * S, py_), (px_ + 0.05 * S, py_), (px_ + 0.045 * S, py_ + 0.025 * S), (px_, py_ + 0.032 * S), (px_ - 0.045 * S, py_ + 0.025 * S)]); fs(c, col, 0.004 * S)
    poly(c, [(-0.06 * S, -0.32 * S), (0.13 * S, -0.32 * S), (0.12 * S, -0.27 * S), (-0.05 * S, -0.27 * S)]); fs(c, spec.get('collar', dk), olw * 0.7)             # 立领
    if spec.get('collar_tab'):                                                                                     # 领章
        for x_ in (-0.03 * S, 0.08 * S): rrect(c, x_, -0.315 * S, 0.035 * S, 0.035 * S, 0.004 * S); c.set_source_rgb(*spec['collar_tab']); c.fill()
    c.rectangle(-0.18 * S, -0.06 * S, 0.36 * S, 0.05 * S); c.set_source_rgb(*spec.get('belt', (0.36, 0.22, 0.12))); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(olw * 0.6); c.stroke()
    rrect(c, 0.02 * S, -0.065 * S, 0.06 * S, 0.06 * S, 0.008 * S); c.set_source(gold_metal(0, -0.06 * S, 0, 0)); c.fill()
    if spec.get('sam_browne'):                                                                                     # 武装带
        c.move_to(0.14 * S, -0.3 * S); c.line_to(-0.12 * S, -0.05 * S); c.set_source_rgb(*spec.get('belt', (0.36, 0.22, 0.12))); c.set_line_width(0.035 * S); c.stroke()
    if spec.get('bandolier'):                                                                                      # 子弹带
        c.move_to(-0.15 * S, -0.29 * S); c.line_to(0.13 * S, -0.06 * S); c.set_source_rgb(*spec['bandolier']); c.set_line_width(0.05 * S); c.stroke()
        for k in range(5):
            u = 0.15 + k * 0.17; x_ = -0.15 * S + u * 0.28 * S; y_ = -0.29 * S + u * 0.23 * S
            c.rectangle(x_ - 0.012 * S, y_ - 0.015 * S, 0.024 * S, 0.03 * S); c.set_source_rgba(0, 0, 0, 0.3); c.fill()


def puttee(c, kn, ft, S, col=(0.55, 0.52, 0.42)):
    """绑腿：小腿上的斜缠布带。"""
    dx, dy = ft[0] - kn[0], ft[1] - kn[1]; L = math.hypot(dx, dy) + 1e-6; ux, uy = dx / L, dy / L; nx, ny = -uy, ux; w = 0.05 * S
    for k in range(5):
        u0 = 0.2 + k * 0.14; u1 = u0 + 0.09
        p0 = (kn[0] + dx * u0 - nx * w, kn[1] + dy * u0 - ny * w); p1 = (kn[0] + dx * u1 + nx * w, kn[1] + dy * u1 + ny * w)
        c.move_to(*p0); c.line_to(*p1); c.set_source_rgba(0, 0, 0, 0.35); c.set_line_width(0.012 * S); c.stroke()
    c.move_to(kn[0] + dx * 0.2, kn[1] + dy * 0.2); c.line_to(kn[0] + dx * 0.88, kn[1] + dy * 0.88); c.set_source_rgba(*col, 0.35); c.set_line_width(0.1 * S); c.stroke()


def straw_shoe(c, kn, ft, S, olw, k=1.0):
    a = math.atan2(ft[1] - kn[1], ft[0] - kn[0]) - PI / 2
    c.save(); c.translate(*ft); c.rotate(a); rrect(c, -0.05 * S, -0.02 * S, 0.13 * S, 0.045 * S, 0.02 * S); fs(c, tuple(v * k for v in (0.78, 0.66, 0.40)), olw)
    for j in range(3): c.move_to(-0.02 * S + j * 0.035 * S, -0.025 * S); c.line_to(0.0 + j * 0.035 * S, 0.02 * S); c.set_source_rgba(0.4, 0.3, 0.15, 0.8); c.set_line_width(0.008 * S); c.stroke()
    c.restore()


def modern_cap(c, R, kind, spec, t):
    """八角帽（红五星可选）、大檐帽、德式钢盔、斗笠式草帽。画在头的坐标里。"""
    col = spec.get('capcol', spec.get('uniform', (0.42, 0.45, 0.42))); dk = tuple(v * 0.65 for v in col)
    if kind == 'bajiao' and spec.get('_front'):                                # 正面八角帽：对称，帽檐是一条横带，五星居中
        c.save(); c.rectangle(-2 * R, -2 * R, 4 * R, 1.62 * R); c.clip(); head_path(c, 0, -0.02 * R, R, spec.get('head', 'round'), 1.06); c.set_source(lin(-R, 0, R, 0, [(0, dk), (0.5, col), (1, dk)])); c.fill(); c.restore()
        poly(c, [(-1.1 * R, -0.42 * R), (-1.2 * R, -0.95 * R), (-0.55 * R, -1.18 * R), (0.55 * R, -1.18 * R), (1.2 * R, -0.95 * R), (1.1 * R, -0.42 * R)]); fs(c, lin(-R, 0, R, 0, [(0, dk), (0.5, tuple(min(1, v * 1.15) for v in col)), (1, dk)]), 0.05 * R)
        for x_ in (-0.55 * R, 0.55 * R): c.move_to(x_, -1.16 * R); c.line_to(x_ * 0.95, -0.45 * R); c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(0.03 * R); c.stroke()
        poly(c, [(-1.12 * R, -0.44 * R), (1.12 * R, -0.44 * R), (0.98 * R, -0.24 * R), (-0.98 * R, -0.24 * R)]); fs(c, dk, 0.04 * R)
        if spec.get('star', True):
            sx, sy, r = 0.0, -0.76 * R, 0.22 * R
            pts = [(sx + (r if k % 2 == 0 else r * 0.42) * math.sin(k * PI / 5), sy - (r if k % 2 == 0 else r * 0.42) * math.cos(k * PI / 5)) for k in range(10)]
            poly(c, pts); fs(c, (0.88, 0.1, 0.08), 0.03 * R)
    elif kind == 'bajiao':
        c.save(); c.rectangle(-2 * R, -2 * R, 4 * R, 1.62 * R); c.clip(); head_path(c, 0, -0.02 * R, R, spec.get('head', 'round'), 1.06); c.set_source(lin(-R, 0, R, 0, [(0, dk), (1, col)])); c.fill(); c.restore()
        poly(c, [(-1.05 * R, -0.42 * R), (-1.12 * R, -0.92 * R), (-0.5 * R, -1.16 * R), (0.55 * R, -1.16 * R), (1.22 * R, -0.9 * R), (1.15 * R, -0.42 * R)]); fs(c, lin(-R, 0, R, 0, [(0, dk), (0.6, col), (1, tuple(min(1, v * 1.2) for v in col))]), 0.05 * R)
        for x_ in (-0.5 * R, 0.55 * R): c.move_to(x_, -1.14 * R); c.line_to(x_ * 0.95, -0.45 * R); c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(0.03 * R); c.stroke()
        poly(c, [(-0.2 * R, -0.42 * R), (1.45 * R, -0.42 * R), (1.32 * R, -0.25 * R), (-0.1 * R, -0.3 * R)]); fs(c, dk, 0.04 * R)                 # 帽檐
        if spec.get('star', True):
            sx, sy, r = 0.6 * R, -0.74 * R, 0.21 * R
            pts = [(sx + (r if k % 2 == 0 else r * 0.42) * math.sin(k * PI / 5), sy - (r if k % 2 == 0 else r * 0.42) * math.cos(k * PI / 5)) for k in range(10)]
            poly(c, pts); fs(c, (0.88, 0.1, 0.08), 0.03 * R)
    elif kind == 'junmao':
        c.save(); c.rectangle(-2 * R, -2 * R, 4 * R, 1.62 * R); c.clip(); head_path(c, 0, -0.02 * R, R, spec.get('head', 'round'), 1.06); c.set_source_rgb(*dk); c.fill(); c.restore()
        c.save(); c.translate(0.1 * R, -1.05 * R); c.scale(1.35, 0.42); c.arc(0, 0, R, 0, 2 * PI); c.restore(); fs(c, lin(-R, 0, R, 0, [(0, dk), (1, col)]), 0.05 * R)
        c.rectangle(-0.95 * R, -1.0 * R, 2.0 * R, 0.5 * R); fs(c, col, 0.04 * R)
        c.rectangle(-0.95 * R, -0.62 * R, 2.0 * R, 0.13 * R); c.set_source_rgb(*spec.get('capband', (0.12, 0.1, 0.1))); c.fill()
        poly(c, [(0.1 * R, -0.5 * R), (1.45 * R, -0.45 * R), (1.25 * R, -0.25 * R), (0.2 * R, -0.36 * R)]); fs(c, (0.1, 0.08, 0.07), 0.04 * R)
        c.arc(0.55 * R, -0.85 * R, 0.13 * R, 0, 2 * PI); c.set_source(gold_metal(0.4 * R, -1.0 * R, 0.7 * R, -0.7 * R)); c.fill()
    elif kind == 'helmet':
        c.move_to(-1.15 * R, -0.25 * R); c.curve_to(-1.2 * R, -1.6 * R, 1.2 * R, -1.6 * R, 1.15 * R, -0.4 * R); c.line_to(1.35 * R, -0.3 * R); c.line_to(1.3 * R, -0.15 * R)
        c.line_to(-1.3 * R, -0.05 * R); c.close_path(); fs(c, rad(-0.3 * R, -1.0 * R, 0.1 * R, 1.6 * R, [(0, tuple(min(1, v * 1.5) for v in col)), (0.5, col), (1, dk)]), 0.05 * R)
        c.move_to(-1.1 * R, -0.3 * R); c.line_to(1.2 * R, -0.42 * R); c.set_source_rgba(0, 0, 0, 0.3); c.set_line_width(0.04 * R); c.stroke()
    elif kind == 'strawhat':
        c.save(); c.translate(0, -0.55 * R); c.scale(1.0, 0.28); c.arc(0, 0, 1.6 * R, 0, 2 * PI); c.restore(); fs(c, (0.82, 0.70, 0.45), 0.04 * R)
        c.save(); c.translate(0, -0.85 * R); c.scale(1.0, 0.55); c.arc(0, 0, 0.85 * R, PI, 2 * PI); c.restore(); c.close_path(); fs(c, (0.86, 0.74, 0.50), 0.04 * R)
        c.rectangle(-0.85 * R, -0.75 * R, 1.7 * R, 0.12 * R); c.set_source_rgb(0.5, 0.3, 0.15); c.fill()


def modern_hair(c, R, spec):
    """八角帽下露出的头发：side（侧分）、long（偏长、盖到耳下）、bald（光头）、short（平头）。"""
    h = spec.get('modern_hair', 'short'); hc = spec.get('hair', (0.08, 0.07, 0.07)); shape = spec.get('head', 'round')
    if h == 'bald':
        c.save(); head_path(c, 0, 0, R, shape); c.clip(); c.arc(-0.3 * R, -0.5 * R, 0.5 * R, 0, 2 * PI); c.set_source_rgba(1, 1, 1, 0.25); c.fill(); c.restore(); return
    c.save(); head_path(c, 0, 0, R, shape); c.clip()
    if spec.get('_front'):                                                     # 正面：左右对称，long 盖住两鬓
        e = 0.38 if h == 'long' else 0.05
        c.move_to(-1.2 * R, e * R); c.curve_to(-0.9 * R, e * R, -0.75 * R, -0.3 * R, -0.3 * R, -0.4 * R); c.curve_to(-0.1 * R, -0.44 * R, 0.1 * R, -0.44 * R, 0.3 * R, -0.4 * R)
        c.curve_to(0.75 * R, -0.3 * R, 0.9 * R, e * R, 1.2 * R, e * R); c.line_to(1.2 * R, -1.3 * R); c.line_to(-1.2 * R, -1.3 * R); c.close_path(); c.set_source_rgb(*hc); c.fill()
    elif h == 'long':                                                            # 偏长的头发：后脑垂到耳下，额前一绺
        c.move_to(-1.2 * R, 0.45 * R); c.curve_to(-0.75 * R, 0.5 * R, -0.45 * R, 0.25 * R, -0.35 * R, -0.25 * R); c.curve_to(-0.1 * R, -0.42 * R, 0.4 * R, -0.36 * R, 0.75 * R, -0.18 * R)
        c.curve_to(0.6 * R, -0.42 * R, 0.4 * R, -0.5 * R, 1.2 * R, -0.5 * R); c.line_to(1.2 * R, -1.3 * R); c.line_to(-1.2 * R, -1.3 * R); c.close_path(); c.set_source_rgb(*hc); c.fill()
        c.save(); c.translate(-0.42 * R, 0.08 * R); c.scale(0.7, 1); c.arc(0, 0, 0.13 * R, 0, 2 * PI); c.restore(); c.set_source_rgb(*tuple(v * 0.9 for v in spec.get('skin', (0.95, 0.82, 0.68)))); c.fill()
    else:
        c.move_to(-1.2 * R, 0.15 * R); c.curve_to(-0.8 * R, -0.45 * R, 0.4 * R, -0.55 * R, 1.2 * R, -0.35 * R); c.line_to(1.2 * R, -1.3 * R); c.line_to(-1.2 * R, -1.3 * R); c.close_path(); c.set_source_rgb(*hc); c.fill()
    c.restore()


def cloak(c, neck, S, t, vel, col):
    """军用斗篷：从双肩垂下的大披风。"""
    wv = math.sin(t * 4); fl = min(1, abs(vel) / 900)
    a0 = (neck[0] + 0.12 * S, neck[1] + 0.02 * S); a1 = (neck[0] - 0.14 * S, neck[1] + 0.02 * S)
    c.move_to(*a0); c.curve_to(a0[0] + 0.06 * S, a0[1] + 0.2 * S, a0[0] + 0.05 * S, 0.1 * S, a0[0] + 0.02 * S, 0.22 * S)
    c.line_to(-0.3 * S - 0.25 * S * fl, 0.24 * S - 0.12 * S * fl + 0.02 * S * wv); c.curve_to(-0.32 * S, 0.0, a1[0] - 0.12 * S, a1[1] + 0.12 * S, *a1); c.close_path()
    fs(c, lin(-0.3 * S, 0, 0.2 * S, 0, [(0, tuple(v * 0.55 for v in col)), (1, col)]), max(1.6, 0.012 * S))


def rifle(c, hand, w, S, olw, bayonet=False):
    """步枪：木枪托 + 枪管（可上刺刀）。手握在护木处，w 是枪口方向。"""
    c.save(); c.translate(*hand); c.rotate(math.atan2(math.cos(w), math.sin(w)))
    L, Lb = 0.42 * S, 0.3 * S; h = 0.035 * S
    poly(c, [(-Lb, -h * 0.4), (-0.08 * S, -h * 0.5), (0.25 * S, -h * 0.45), (0.25 * S, h * 0.45), (-0.06 * S, h * 0.55), (-0.14 * S, h * 1.6), (-Lb, h * 1.7)])
    fs(c, lin(0, -h, 0, h * 1.7, [(0, (0.72, 0.45, 0.22)), (1, (0.40, 0.22, 0.10))]), olw * 0.8)                            # 木托
    c.rectangle(-0.06 * S, -h * 0.75, L + 0.06 * S, h * 0.42); c.set_source(lin(0, -h, 0, 0, [(0, (0.55, 0.58, 0.62)), (1, (0.18, 0.19, 0.22))])); c.fill_preserve()
    c.set_source_rgb(*OL); c.set_line_width(olw * 0.5); c.stroke()
    c.move_to(-0.1 * S, -h * 0.75); c.line_to(-0.12 * S, -h * 1.3); c.set_source_rgb(0.2, 0.2, 0.22); c.set_line_width(0.012 * S); c.stroke()       # 枪栓
    if bayonet:
        poly(c, [(L - 0.01 * S, -h * 0.75), (L + 0.2 * S, -h * 0.55), (L - 0.01 * S, -h * 0.35)]); fs(c, lin(0, -h, 0, 0, [(0, (0.98, 0.99, 1)), (1, (0.6, 0.63, 0.7))]), olw * 0.5)
    c.restore()
