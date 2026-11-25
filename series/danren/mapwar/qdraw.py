"""Q 版人物的绘图零件：渐变、金属、甲片纹理、兽面、圆角矩形、头型。"""
import math, cairo

PI = math.pi
GOLD = (0.88, 0.68, 0.25); GOLD_L = (1.0, 0.92, 0.62); GOLD_D = (0.42, 0.27, 0.08)
INK = (0.08, 0.06, 0.05)


# ================================================================ 基础
def grad(g, stops):
    for o, c in stops: g.add_color_stop_rgba(o, *c) if len(c) == 4 else g.add_color_stop_rgb(o, *c)
    return g


def lin(x0, y0, x1, y1, stops): return grad(cairo.LinearGradient(x0, y0, x1, y1), stops)


def rad(cx, cy, r0, r1, stops, fx=None, fy=None): return grad(cairo.RadialGradient(cx if fx is None else fx, cy if fy is None else fy, r0, cx, cy, r1), stops)


def path(c, pts, close=True):
    c.move_to(*pts[0])
    for p in pts[1:]:
        if p[0] == 'c': c.curve_to(*p[1:])
        else: c.line_to(*p)
    if close: c.close_path()


def fill_stroke(c, src, lw=4, col=INK):
    c.set_source(src) if not isinstance(src, tuple) else c.set_source_rgb(*src); c.fill_preserve(); c.set_source_rgb(*col); c.set_line_width(lw); c.stroke()


def shade(c, x0, x1, a0=0.0, a1=0.45, col=(0, 0, 0)):
    """在当前 clip 内铺一层左右明暗。"""
    c.set_source(lin(x0, 0, x1, 0, [(0, col + (a0,)), (1, col + (a1,))])); c.paint()


def gold_metal(x0, y0, x1, y1): return lin(x0, y0, x1, y1, [(0, GOLD_L), (0.35, GOLD), (0.7, (0.62, 0.44, 0.14)), (1, GOLD_D)])


def scale_tile(base=(0.18, 0.17, 0.19), rim=GOLD, s=26):
    """鱼鳞甲：每片有金边、上亮下暗、一道高光。"""
    t = cairo.ImageSurface(cairo.FORMAT_ARGB32, s, s); c = cairo.Context(t)
    c.set_source_rgb(*[v * 0.5 for v in base]); c.paint()
    for ox, oy in ((0, -s / 2), (s / 2, 0), (-s / 2, 0), (s, -s / 2), (0, s / 2), (s / 2, s), (-s / 2, s), (s, s / 2)):
        x, y = ox, oy
        c.move_to(x - s / 2, y); c.curve_to(x - s / 2, y + s * 0.78, x + s / 2, y + s * 0.78, x + s / 2, y); c.close_path()
        c.set_source(lin(x, y, x, y + s * 0.6, [(0, tuple(min(1, v * 1.9) for v in base)), (1, tuple(v * 0.6 for v in base))])); c.fill_preserve()
        c.set_source_rgb(*rim); c.set_line_width(1.8); c.stroke()
        c.arc(x - s * 0.12, y + s * 0.22, s * 0.16, PI * 1.05, PI * 1.6); c.set_source_rgba(1, 1, 1, 0.35); c.set_line_width(1.2); c.stroke()
    p = cairo.SurfacePattern(t); p.set_extend(cairo.EXTEND_REPEAT); return p


def lamellar_tile(base=(0.20, 0.18, 0.20), s=(34, 22)):
    """札甲：长方甲片 + 金色编绳点。"""
    w, h = s; t = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h); c = cairo.Context(t)
    c.set_source_rgb(*[v * 0.45 for v in base]); c.paint()
    for ox in (0, w / 2 * 0 + w):
        pass
    for k, ox in enumerate((-w / 2, w / 2)):
        c.rectangle(ox + 2, 1, w - 4, h - 3); c.set_source(lin(0, 0, 0, h, [(0, tuple(min(1, v * 1.8) for v in base)), (1, tuple(v * 0.6 for v in base))])); c.fill_preserve()
        c.set_source_rgb(*GOLD); c.set_line_width(1.4); c.stroke()
        c.arc(ox + w / 2, h * 0.3, 1.8, 0, 2 * PI); c.set_source_rgb(0.85, 0.15, 0.1); c.fill()
    p = cairo.SurfacePattern(t); p.set_extend(cairo.EXTEND_REPEAT); return p


def beast(c, x, y, r):
    """吞肩兽 / 带扣兽面。"""
    c.arc(x, y, r, 0, 2 * PI); fill_stroke(c, rad(x, y, 0, r, [(0, GOLD_L), (0.55, GOLD), (1, GOLD_D)], x - r * 0.35, y - r * 0.4), r * 0.05, (0.28, 0.16, 0.05))
    for k in range(18):
        a = k / 18 * 2 * PI; c.move_to(x + math.cos(a) * r * 0.6, y + math.sin(a) * r * 0.6)
        c.curve_to(x + math.cos(a + 0.1) * r * 0.8, y + math.sin(a + 0.1) * r * 0.8, x + math.cos(a + 0.25) * r * 0.92, y + math.sin(a + 0.25) * r * 0.92, x + math.cos(a + 0.35) * r * 0.62, y + math.sin(a + 0.35) * r * 0.62)
        c.set_source_rgb(0.58, 0.38, 0.12); c.fill()
    c.arc(x, y + r * 0.04, r * 0.56, 0, 2 * PI); c.set_source(rad(x, y, 0, r * 0.6, [(0, GOLD_L), (1, (0.66, 0.46, 0.16))], x - r * 0.1, y - r * 0.25)); c.fill()
    c.set_source_rgb(0.26, 0.13, 0.04); c.set_line_width(r * 0.055); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in (-1, 1):
        c.move_to(x + k * r * 0.36, y - r * 0.26); c.curve_to(x + k * r * 0.25, y - r * 0.12, x + k * r * 0.14, y - r * 0.2, x + k * r * 0.06, y - r * 0.08); c.stroke()
        path(c, [(x + k * r * 0.3, y - r * 0.06), ('c', x + k * r * 0.24, y - r * 0.14, x + k * r * 0.12, y - r * 0.12, x + k * r * 0.1, y - r * 0.02), ('c', x + k * r * 0.16, y + r * 0.03, x + k * r * 0.26, y + r * 0.02, x + k * r * 0.3, y - r * 0.06)])
        c.set_source_rgb(0.85, 0.12, 0.05); c.fill(); c.set_source_rgb(0.26, 0.13, 0.04)
    path(c, [(x - r * 0.1, y + r * 0.08), (x + r * 0.1, y + r * 0.08), (x, y + r * 0.2)]); c.fill()
    path(c, [(x - r * 0.3, y + r * 0.27), ('c', x - r * 0.1, y + r * 0.42, x + r * 0.1, y + r * 0.42, x + r * 0.3, y + r * 0.27), ('c', x + r * 0.15, y + r * 0.48, x - r * 0.15, y + r * 0.48, x - r * 0.3, y + r * 0.27)]); c.set_source_rgb(0.45, 0.04, 0.03); c.fill()
    for k in (-1, 1): path(c, [(x + k * r * 0.2, y + r * 0.3), (x + k * r * 0.14, y + r * 0.46), (x + k * r * 0.09, y + r * 0.32)]); c.set_source_rgb(1, 0.97, 0.9); c.fill()



OL = (0.13, 0.11, 0.10)

def rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -PI / 2, 0); c.arc(x + w - r, y + h - r, r, 0, PI / 2)
    c.arc(x + r, y + h - r, r, PI / 2, PI); c.arc(x + r, y + r, r, PI, 1.5 * PI); c.close_path()


def poly(c, pts):
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.close_path()



def head_path(c, x, hy, R, shape, k=1.0):
    """头形路径：round 圆 / square 方（小圆角）/ tofu 软方 / egg 竖蛋 / wide 扁方"""
    R = R * k
    if shape == 'round': c.new_sub_path(); c.arc(x, hy, R, 0, 2 * PI); return
    if shape == 'egg': c.save(); c.translate(x, hy); c.scale(0.86, 1.06); c.new_sub_path(); c.arc(0, 0, R, 0, 2 * PI); c.restore(); return
    w, h_, r = {'square': (1.0, 0.94, 0.16), 'tofu': (1.0, 0.94, 0.42), 'wide': (1.12, 0.86, 0.3)}[shape]
    rrect(c, x - w * R, hy - h_ * R, 2 * w * R, 2 * h_ * R, r * R)

