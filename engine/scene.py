"""scene — 几种风格共用的布景件：大圣堂剪影、前景人群、飞鸟。"""
import math, numpy as np, cairo

def sept(c, cx, gy, k=1.0, col=(0, 0, 0), a=1.0, windows=True):
    """七塔一穹顶的大圣堂剪影；k = 缩放（k=1 时穹顶宽约 500）。"""
    c.set_source_rgba(*col, a)
    def rect(x0, y0, x1, y1): c.rectangle(cx + x0 * k, gy - y1 * k, (x1 - x0) * k, (y1 - y0) * k); c.fill()
    def spire(dx, h, w):
        x = cx + dx * k; w *= k; top = gy - h * k
        c.move_to(x - w / 2, gy); c.line_to(x - w / 2, top + w * 1.7); c.line_to(x - w * 0.64, top + w * 1.7); c.line_to(x - w * 0.64, top + w * 1.42); c.line_to(x - w * 0.32, top + w * 1.42); c.line_to(x, top)
        c.line_to(x + w * 0.32, top + w * 1.42); c.line_to(x + w * 0.64, top + w * 1.42); c.line_to(x + w * 0.64, top + w * 1.7); c.line_to(x + w / 2, top + w * 1.7); c.line_to(x + w / 2, gy); c.close_path(); c.fill()
    for dx, h, w in ((-520, 470, 62), (-400, 560, 66), (-285, 520, 60), (285, 520, 60), (400, 560, 66), (520, 470, 62)): spire(dx, h, w)
    spire(0, 720, 74)
    c.save(); c.translate(cx, gy - 300 * k); c.scale(245 * k, 215 * k); c.arc(0, 0, 1, math.pi, math.tau); c.restore(); c.close_path(); c.fill()
    rect(-30, 505, 30, 560); rect(-262, 280, 262, 310); rect(-245, 0, 245, 282); rect(-330, 182, 330, 212); rect(-310, 0, 310, 184)
    if windows:
        c.set_operator(cairo.OPERATOR_DEST_OUT)
        for i in range(11):
            x = cx + (-285 + i * 57) * k; r = 16 * k; c.set_source_rgba(0, 0, 0, 0.55); c.move_to(x - r, gy); c.line_to(x - r, gy - 132 * k); c.arc(x, gy - 132 * k, r, math.pi, math.tau); c.line_to(x + r, gy); c.close_path(); c.fill()
        for i in range(7):
            x = cx + (-180 + i * 60) * k; r = 9 * k; c.set_source_rgba(0, 0, 0, 0.5); c.move_to(x - r, gy - 224 * k); c.line_to(x - r, gy - 260 * k); c.arc(x, gy - 260 * k, r, math.pi, math.tau); c.line_to(x + r, gy - 224 * k); c.close_path(); c.fill()
        c.set_operator(cairo.OPERATOR_OVER)

def skyline(c, gy, r, col, a=1.0, w=1920, gap=None, hmin=30, hmax=95):
    c.set_source_rgba(*col, a); x = -10
    while x < w + 20:
        ww = r.uniform(26, 60); h = r.uniform(hmin, hmax)
        if gap and gap[0] < x < gap[1]: h *= 0.55
        c.rectangle(x, gy - h, ww, h + 2); c.fill()
        if r.random() < 0.25: c.move_to(x, gy - h); c.line_to(x + ww / 2, gy - h - ww * 0.8); c.line_to(x + ww, gy - h); c.close_path(); c.fill()
        x += ww * r.uniform(0.7, 1.0)

def crowd(c, y0, R0, n, r, col, w=1920, h=1080, fists=0.26, jit=16):
    c.set_source_rgb(*col); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(n):
        x = (i + 0.5) * w / n + r.uniform(-18, 18); y = y0 + r.uniform(-jit, jit); R = R0 * r.uniform(0.86, 1.12)
        c.save(); c.translate(x, y); c.scale(R * 0.86, R); c.arc(0, 0, 1, 0, math.tau); c.restore(); c.fill()
        c.rectangle(x - R * 0.36, y, R * 0.72, R * 1.5); c.fill()
        c.move_to(x - R * 2.1, h + 10); c.curve_to(x - R * 2.1, y + R * 1.5, x - R * 1.2, y + R * 1.25, x - R * 0.3, y + R * 1.15); c.line_to(x + R * 0.3, y + R * 1.15); c.curve_to(x + R * 1.2, y + R * 1.25, x + R * 2.1, y + R * 1.5, x + R * 2.1, h + 10); c.close_path(); c.fill()
        if r.random() < fists:
            fx = x + r.choice([-1, 1]) * R * 1.7; c.set_line_width(R * 0.5); c.move_to(fx, y + R * 1.9); c.line_to(fx + r.uniform(-10, 10), y - R * 1.3); c.stroke(); c.arc(fx, y - R * 1.45, R * 0.36, 0, math.tau); c.fill()

def birds(c, r, n, x0, y0, w, h, col, a=0.85, slope=0.16):
    c.set_source_rgba(*col, a); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(n):
        x = x0 + r.uniform(0, w); y = y0 + r.uniform(0, h) + (x - x0) * slope; k = r.uniform(9, 17); f = r.uniform(0.2, 0.9)
        c.set_line_width(k * 0.22); c.move_to(x - k, y - k * f); c.curve_to(x - k * 0.5, y - k * f * 0.2, x - k * 0.2, y, x, y + k * 0.15); c.curve_to(x + k * 0.2, y, x + k * 0.5, y - k * f * 0.3, x + k * 1.05, y - k * f * 0.8); c.stroke()
