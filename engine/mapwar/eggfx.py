"""斜视角战场的近现代道具和特效：沙包、战壕、爆炸、弹坑、曳光弹、手榴弹、飞机、河、浮桥、木船、山坡。
道具（放进 eggfield.scene 的 props，和兵一起按远近排序）：sandbag_line()、blast()、crater()
画在兵下面/上面的（放进 under/over 回调）：trench()、river()、bridge()、boat()、tracers()、grenade()、plane()、hill()
"""
import math, cairo, numpy as np
from .eggfield import px, rr, fs, tube, OL, TAU


def sandbag_line(p0, p1, n=None, rows=2):
    """从 p0 到 p1 垒一道沙包墙，返回 props 列表。"""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); n = n or max(2, int(L / 0.9)); out = []
    for i in range(n):
        u = i / (n - 1); x = p0[0] + (p1[0] - p0[0]) * u; y = p0[1] + (p1[1] - p0[1]) * u
        def fn(c, sx, sy, s, i=i):
            for r in range(rows):
                off = 0.45 * s if r % 2 else 0
                rr(c, sx - 0.55 * s + off * 0.5, sy - (0.42 + r * 0.36) * s, 1.05 * s, 0.42 * s, 0.18 * s); fs(c, (0.74 - 0.05 * r, 0.64 - 0.05 * r, 0.44 - 0.04 * r), max(0.8, 0.04 * s))
                c.move_to(sx - 0.3 * s + off * 0.5, sy - (0.36 + r * 0.36) * s); c.line_to(sx + 0.3 * s + off * 0.5, sy - (0.36 + r * 0.36) * s); c.set_source_rgba(0, 0, 0, 0.15); c.set_line_width(max(0.6, 0.03 * s)); c.stroke()
        out.append((x, y, fn))
    return out


def blast(x, y, age, size=1.0, seed=0):
    """一次炮弹/手榴弹爆炸（age 秒，约 0.9 秒放完）：闪光 → 火球 → 泥土 → 烟。返回一个 prop。"""
    def fn(c, sx, sy, s):
        if age < 0 or age > 1.3: return
        s = s * size; r = np.random.default_rng(seed); k = min(1, age / 0.18)
        if age < 0.1: c.arc(sx, sy - 0.6 * s, (2.5 + 20 * age) * s, 0, TAU); c.set_source_rgba(1, 0.97, 0.85, 0.85 * (1 - age / 0.1)); c.fill()
        for j in range(9):                                                     # 泥土碎块
            a = -math.pi * (0.12 + 0.76 * r.random()); v = (3 + 4 * r.random()) * s; g = 9 * s
            dx_ = math.cos(a) * v * age; dy_ = math.sin(a) * v * age + 0.5 * g * age * age
            if dy_ < 0.3 * s: c.arc(sx + dx_, sy + dy_, (0.14 + 0.12 * r.random()) * s, 0, TAU); c.set_source_rgba(0.25, 0.18, 0.12, 1); c.fill()
        if age < 0.55:
            f = 1 - age / 0.55
            for rad_, col in ((1.9, (0.95, 0.35, 0.08)), (1.35, (1.0, 0.7, 0.15)), (0.8, (1.0, 0.96, 0.7))):
                c.save(); c.translate(sx, sy - (0.5 + 1.4 * k) * s); c.scale(1, 1.15); c.arc(0, 0, rad_ * s * (0.4 + 0.6 * k) * (0.6 + 0.4 * f), 0, TAU); c.restore(); c.set_source_rgba(*col, min(1, f * 1.6)); c.fill()
        if age > 0.12:                                                         # 烟
            f = min(1, (age - 0.12) / 0.3); al = 0.75 * (1 - max(0, age - 0.6) / 0.7)
            for j in range(5):
                ox = (r.random() - 0.5) * 1.6 * s; c.arc(sx + ox, sy - (1.2 + 2.6 * (age - 0.12) + j * 0.5) * s, (0.7 + 0.25 * j + age) * s * f, 0, TAU); c.set_source_rgba(0.22, 0.2, 0.2, max(0, al) * 0.7); c.fill()
    return (x, y, fn)


def crater(x, y, a=1.0):
    def fn(c, sx, sy, s):
        c.save(); c.translate(sx, sy); c.scale(1, 0.4); c.arc(0, 0, 1.3 * s, 0, TAU); c.restore(); c.set_source_rgba(0.2, 0.15, 0.1, 0.5 * a); c.fill()
        c.save(); c.translate(sx, sy); c.scale(1, 0.4); c.arc(0, 0, 0.8 * s, 0, TAU); c.restore(); c.set_source_rgba(0.1, 0.08, 0.06, 0.6 * a); c.fill()
    return (x, y - 0.01, fn)


def _poly(c, cam, pts):
    P, _ = px(cam, [(p[0], p[1], p[2] if len(p) > 2 else 0) for p in pts]); c.move_to(*P[0]); [c.line_to(*q) for q in P[1:]]; c.close_path()


def trench(c, cam, p0, p1, w=1.6):
    """地上的一条战壕（深色沟 + 两侧土埂）。"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy); nx, ny = -dy / L * w / 2, dx / L * w / 2
    _poly(c, cam, [(p0[0] - nx * 1.7, p0[1] - ny * 1.7), (p1[0] - nx * 1.7, p1[1] - ny * 1.7), (p1[0] + nx * 1.7, p1[1] + ny * 1.7), (p0[0] + nx * 1.7, p0[1] + ny * 1.7)]); c.set_source_rgba(0.62, 0.5, 0.33, 0.9); c.fill()
    _poly(c, cam, [(p0[0] - nx, p0[1] - ny), (p1[0] - nx, p1[1] - ny), (p1[0] + nx, p1[1] + ny), (p0[0] + nx, p0[1] + ny)]); c.set_source_rgb(0.2, 0.15, 0.11); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(2.5); c.stroke()


def river(c, cam, pts, w, t, col=(0.42, 0.52, 0.56), night=False):
    """沿折线 pts 的一条河（宽 w 米），带流动的波纹。"""
    L, Rr = [], []
    for i, p in enumerate(pts):
        a = pts[min(i + 1, len(pts) - 1)]; b = pts[max(i - 1, 0)]; dx, dy = a[0] - b[0], a[1] - b[1]; n = math.hypot(dx, dy) + 1e-6
        L.append((p[0] - dy / n * w / 2, p[1] + dx / n * w / 2)); Rr.append((p[0] + dy / n * w / 2, p[1] - dx / n * w / 2))
    if night: col = tuple(v * 0.75 for v in col)
    _poly(c, cam, L + Rr[::-1]); c.set_source_rgb(*col); c.fill_preserve(); c.set_source_rgba(*OL, 0.8); c.set_line_width(3); c.stroke()
    r = np.random.default_rng(4)
    for k in range(46):
        u = (r.random() + t * 0.06) % 1.0; v = r.random() * 0.8 + 0.1; i = min(len(pts) - 2, int(u * (len(pts) - 1))); f = u * (len(pts) - 1) - i
        a = (L[i][0] + (L[i + 1][0] - L[i][0]) * f, L[i][1] + (L[i + 1][1] - L[i][1]) * f); b = (Rr[i][0] + (Rr[i + 1][0] - Rr[i][0]) * f, Rr[i][1] + (Rr[i + 1][1] - Rr[i][1]) * f)
        m = (a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v); dx, dy = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]; n = math.hypot(dx, dy) + 1e-6
        P, _ = px(cam, [(m[0], m[1], 0), (m[0] + dx / n * 1.6, m[1] + dy / n * 1.6, 0)]); c.move_to(*P[0]); c.line_to(*P[1]); c.set_source_rgba(1, 1, 1, 0.28); c.set_line_width(2.5); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()


def bridge(c, cam, p0, p1, w=2.4):
    """浮桥：一排木船托着桥板。"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; nx, ny = -uy, ux
    for k in range(int(L / 3.2) + 1):
        m = (p0[0] + ux * (1.2 + k * 3.2), p0[1] + uy * (1.2 + k * 3.2))
        if (m[0] - p0[0]) * ux + (m[1] - p0[1]) * uy > L: break
        _poly(c, cam, [(m[0] - nx * 3.2, m[1] - ny * 3.2), (m[0] - nx * 2.2 + ux * 0.8, m[1] - ny * 2.2 + uy * 0.8), (m[0] + nx * 2.2 + ux * 0.8, m[1] + ny * 2.2 + uy * 0.8), (m[0] + nx * 3.2, m[1] + ny * 3.2),
                       (m[0] + nx * 2.2 - ux * 0.8, m[1] + ny * 2.2 - uy * 0.8), (m[0] - nx * 2.2 - ux * 0.8, m[1] - ny * 2.2 - uy * 0.8)]); c.set_source_rgb(0.42, 0.28, 0.15); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(2.5); c.stroke()
    _poly(c, cam, [(p0[0] - nx * w / 2, p0[1] - ny * w / 2, 0.25), (p1[0] - nx * w / 2, p1[1] - ny * w / 2, 0.25), (p1[0] + nx * w / 2, p1[1] + ny * w / 2, 0.25), (p0[0] + nx * w / 2, p0[1] + ny * w / 2, 0.25)])
    c.set_source_rgb(0.78, 0.62, 0.38); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(3); c.stroke()
    for k in range(int(L / 0.9)):
        a = (p0[0] + ux * k * 0.9, p0[1] + uy * k * 0.9); P, _ = px(cam, [(a[0] - nx * w / 2, a[1] - ny * w / 2, 0.25), (a[0] + nx * w / 2, a[1] + ny * w / 2, 0.25)])
        c.move_to(*P[0]); c.line_to(*P[1]); c.set_source_rgba(0.3, 0.2, 0.1, 0.5); c.set_line_width(1.5); c.stroke()


def boat(c, cam, x, y, ang, L=7.0, w=2.4):
    """一条木船（船身），人另外用兵摆在上面。"""
    ux, uy = math.cos(ang), math.sin(ang); nx, ny = -uy, ux
    pts = [(x + ux * L / 2, y + uy * L / 2), (x + ux * L * 0.3 + nx * w / 2, y + uy * L * 0.3 + ny * w / 2), (x - ux * L * 0.4 + nx * w / 2, y - uy * L * 0.4 + ny * w / 2), (x - ux * L / 2, y - uy * L / 2),
           (x - ux * L * 0.4 - nx * w / 2, y - uy * L * 0.4 - ny * w / 2), (x + ux * L * 0.3 - nx * w / 2, y + uy * L * 0.3 - ny * w / 2)]
    _poly(c, cam, pts); c.set_source_rgb(0.5, 0.33, 0.17); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(3); c.stroke()
    _poly(c, cam, [(x + (p[0] - x) * 0.78, y + (p[1] - y) * 0.78) for p in pts]); c.set_source_rgb(0.68, 0.5, 0.28); c.fill()
    P, _ = px(cam, [(x - ux * L * 0.7, y - uy * L * 0.7, 0), (x - ux * L * 1.5, y - uy * L * 1.5, 0)]); c.move_to(*P[0]); c.line_to(*P[1]); c.set_source_rgba(1, 1, 1, 0.35); c.set_line_width(5); c.stroke()   # 尾迹


def tracers(c, cam, shots):
    """曳光弹：shots = [(起点xyz, 终点xyz, 进度0..1), ...]。"""
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for a, b, u in shots:
        if not 0 <= u <= 1: continue
        p = [a[i] + (b[i] - a[i]) * u for i in range(3)]; q = [a[i] + (b[i] - a[i]) * max(0, u - 0.18) for i in range(3)]; P, S_ = px(cam, [p, q])
        c.move_to(*P[1]); c.line_to(*P[0]); c.set_source_rgba(1, 0.75, 0.2, 0.45); c.set_line_width(max(3, 0.2 * S_[0])); c.stroke()
        c.move_to(*P[1]); c.line_to(*P[0]); c.set_source_rgba(1, 0.98, 0.8, 0.95); c.set_line_width(max(1.2, 0.07 * S_[0])); c.stroke()


def grenade(c, cam, a, b, u, h=4.0):
    """木柄手榴弹沿抛物线从 a 飞到 b（u 0..1）。"""
    if not 0 <= u <= 1: return
    p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, 1.2 + 4 * h * u * (1 - u)); P, S_ = px(cam, [p]); s = S_[0]; x, y = P[0]
    c.save(); c.translate(x, y); c.rotate(u * 14); tube(c, (-0.35 * s, 0), (0.1 * s, 0), max(1.5, 0.12 * s), (0.7, 0.5, 0.25), max(0.6, 0.03 * s)); rr(c, 0.05 * s, -0.14 * s, 0.32 * s, 0.28 * s, 0.06 * s); fs(c, (0.25, 0.27, 0.25), max(0.6, 0.03 * s)); c.restore()


def plane(c, cam, x, y, z, ang, size=1.0):
    """一架螺旋桨飞机（俯视轮廓）+ 地面影子。"""
    ux, uy = math.cos(ang), math.sin(ang); nx, ny = -uy, ux; k = 5.0 * size
    def shape(zz):
        f = lambda a, b: (x + ux * a * k + nx * b * k, y + uy * a * k + ny * b * k, zz)
        return [f(1.3, 0), f(1.0, 0.16), f(0.5, 0.18), f(0.45, 1.5), f(0.1, 1.5), f(0.0, 0.2), f(-0.9, 0.12), f(-1.0, 0.55), f(-1.25, 0.55), f(-1.2, 0), f(-1.25, -0.55), f(-1.0, -0.55), f(-0.9, -0.12), f(0.0, -0.2), f(0.1, -1.5), f(0.45, -1.5), f(0.5, -0.18), f(1.0, -0.16)]
    _poly(c, cam, shape(0)); c.set_source_rgba(0, 0, 0, 0.22); c.fill()
    _poly(c, cam, shape(z)); c.set_source_rgb(0.42, 0.46, 0.42); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(3); c.stroke()
    P, S_ = px(cam, [(x + ux * 1.35 * k, y + uy * 1.35 * k, z)]); c.arc(*P[0], 0.55 * k * S_[0] * 0.5, 0, TAU); c.set_source_rgba(0.9, 0.9, 0.9, 0.35); c.fill()


def hill(c, cam, x, y, rx, ry, h, col=(0.50, 0.55, 0.40)):
    """一座圆山包（画在兵的下面，当高地）。"""
    for k in range(6, 0, -1):
        f = k / 6; pts = [(x + math.cos(a) * rx * f, y + math.sin(a) * ry * f, h * (1 - f) ** 0.7) for a in np.linspace(0, TAU, 28)[:-1]]
        _poly(c, cam, pts); cc = tuple(v * (0.82 + 0.22 * (1 - f)) for v in col); c.set_source_rgb(*cc); c.fill_preserve(); c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(1.5); c.stroke()
