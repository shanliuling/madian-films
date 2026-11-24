"""yunlan — 云岚宗山顶广场（小说：山顶、青石板、近千名月白袍弟子盘坐成半圆、上方石台坐着白袍长老）。
plates(R) → [(板, 深度)]，从远到近；地面 GY = 860。白天、高饱和：人和火要在这上面跳出来。"""
import math, numpy as np, cv2, cairo
from paper import layer, rgba
from action import rnd
GY = 860
def _noise(h, w, s, seed):
    r = np.random.default_rng(seed); a = cv2.GaussianBlur(r.random((h, w), dtype=np.float32), (0, 0), s); return (a - a.min()) / (a.max() - a.min() + 1e-6)
def _pl(draw, x0, y0, w, h, ps, alpha=True):
    s, c = layer(int(w * ps), int(h * ps)); c.scale(ps, ps); c.translate(-x0, -y0); draw(c); rgb, al = rgba(s); return dict(rgb=np.ascontiguousarray(rgb), a=np.ascontiguousarray(al[..., 0]) if alpha else None, x0=x0, y0=y0, ps=ps)
def _fig(c, x, y, s, k=1.0):
    """一个盘坐的白袍弟子。"""
    c.move_to(x - s * 0.62, y); c.curve_to(x - s * 0.5, y - s * 0.5, x - s * 0.3, y - s * 1.0, x, y - s * 1.02); c.curve_to(x + s * 0.3, y - s * 1.0, x + s * 0.5, y - s * 0.5, x + s * 0.62, y); c.close_path(); c.set_source_rgb(0.86 * k, 0.9 * k, 0.97 * k); c.fill_preserve(); c.set_source_rgb(0.34 * k, 0.42 * k, 0.58 * k); c.set_line_width(s * 0.07); c.stroke()
    c.arc(x, y - s * 1.18, s * 0.22, 0, 7); c.set_source_rgb(0.12 * k, 0.12 * k, 0.18 * k); c.fill()
def _roof(c, x, y, w, h, col, edge):
    c.move_to(x - w / 2 - h * 0.5, y); c.curve_to(x - w / 2, y - h * 0.15, x - w * 0.3, y - h * 0.8, x - w * 0.12, y - h); c.line_to(x + w * 0.12, y - h); c.curve_to(x + w * 0.3, y - h * 0.8, x + w / 2, y - h * 0.15, x + w / 2 + h * 0.5, y); c.close_path(); c.set_source_rgb(*col); c.fill_preserve(); c.set_source_rgb(*edge); c.set_line_width(3); c.stroke()
def plates(R):
    q = R.k * 2; out = []
    # 天：深蓝到地平线的亮青，右上角的太阳，大团的云
    W, H = 2600, 1700; yy, xx = np.mgrid[0:int(H * q * 0.5), 0:int(W * q * 0.5)].astype(np.float32); v = np.clip(yy / (H * q * 0.5) * 1.35, 0, 1)[..., None]
    sky = np.float32((0.05, 0.27, 0.70)) * (1 - v) + np.float32((0.60, 0.86, 0.98)) * v; sx, sy = 0.76 * sky.shape[1], 0.30 * sky.shape[0]; d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2) / sky.shape[1]
    sky += np.float32((1.0, 0.95, 0.8)) * (np.exp(-d * 9)[..., None] * 0.55 + np.exp(-d * 60)[..., None] * 0.9)
    n = _noise(sky.shape[0], sky.shape[1], 46 * q, 3) * 0.6 + _noise(sky.shape[0], sky.shape[1], 14 * q, 4) * 0.3 + _noise(sky.shape[0], sky.shape[1], 4 * q, 5) * 0.1; band = np.clip((yy / sky.shape[0] - 0.36) * 2.4, 0, 1)
    cl = np.clip((n - 0.50 + 0.14 * band) * 9, 0, 1)[..., None]; sh = np.clip((n - 0.56 + 0.14 * band) * 6, 0, 1)[..., None]; sky = sky * (1 - cl * 0.92) + (np.float32((0.70, 0.80, 0.94)) * (1 - sh) + np.float32((1.0, 1.0, 1.0)) * sh) * cl * 0.92
    out.append((dict(rgb=np.clip(sky, 0, 1), a=None, x0=960 - W / 2, y0=420 - H / 2, ps=q * 0.5), 0.03))
    # 远山
    def peaks(c):
        for j, (base, amp, col) in enumerate(((640, 300, (0.42, 0.62, 0.86)), (700, 210, (0.30, 0.50, 0.76)))):
            c.move_to(-900, 1300); x = -900
            while x < 2900: i = int(x / 90) + j * 40; c.line_to(x, base - amp * rnd(i, j) ** 1.6 - 40 * math.sin(x / 300 + j)); x += 60 + 60 * rnd(i, j + 7)
            c.line_to(2900, 1300); c.close_path(); g = cairo.LinearGradient(0, base - amp, 0, base + 160); g.add_color_stop_rgb(0, *col); g.add_color_stop_rgb(1, 0.72, 0.88, 0.98); c.set_source(g); c.fill()
    out.append((_pl(peaks, -900, 100, 3800, 1200, q * 0.5), 0.10))
    # 云岚宗大殿：高台、长阶、层层飞檐，被空气染蓝
    def hall(c):
        wall, tile, edge, col = (0.80, 0.88, 0.96), (0.16, 0.36, 0.56), (0.10, 0.22, 0.40), (0.62, 0.30, 0.34)
        c.rectangle(-700, 690, 3400, 500); c.set_source_rgb(0.56, 0.68, 0.84); c.fill()                                                # 高台
        for (x, y, w, h, n) in ((960, 690, 760, 250, 3), (300, 690, 360, 170, 2), (1620, 690, 360, 170, 2), (-260, 690, 300, 140, 2), (2180, 690, 300, 140, 2)):
            for i in range(n):
                ww = w * (1 - 0.24 * i); hh = h / n; yb = y - hh * i; c.rectangle(x - ww * 0.42, yb - hh, ww * 0.84, hh); c.set_source_rgb(*wall); c.fill()
                for k in range(-3, 4): c.rectangle(x + k * ww * 0.13 - 5, yb - hh * 0.62, 10, hh * 0.62); c.set_source_rgb(*col); c.fill()
                _roof(c, x, yb - hh * 0.58, ww, hh * 0.5, tile, edge)
        for sx in (560, 1360):                                                           # 殿前两柄石剑
            c.move_to(sx - 22, 690); c.line_to(sx - 22, 430); c.line_to(sx, 380); c.line_to(sx + 22, 430); c.line_to(sx + 22, 690); c.close_path(); c.set_source_rgb(0.5, 0.62, 0.78); c.fill_preserve(); c.set_source_rgb(0.3, 0.42, 0.6); c.set_line_width(4); c.stroke(); c.rectangle(sx - 50, 600, 100, 16); c.fill()
        c.move_to(820, 1190); c.line_to(900, 690); c.line_to(1020, 690); c.line_to(1100, 1190); c.close_path(); c.set_source_rgb(0.70, 0.80, 0.92); c.fill(); c.set_source_rgb(0.5, 0.62, 0.78); c.set_line_width(2)
        for i in range(14): y = 700 + i * 12; c.move_to(900 - (y - 690) * 0.16, y); c.line_to(1020 + (y - 690) * 0.16, y); c.stroke()
    out.append((_pl(hall, -700, 300, 3400, 900, q * 0.6), 0.30))
    # 观战的人：石台上的长老、一排排盘坐的弟子、旗
    def crowd(c):
        c.rectangle(-900, 742, 3800, 500); c.set_source_rgb(0.50, 0.60, 0.74); c.fill()
        c.move_to(660, 742); c.line_to(700, 640); c.line_to(1220, 640); c.line_to(1260, 742); c.close_path(); c.set_source_rgb(0.62, 0.71, 0.83); c.fill_preserve(); c.set_source_rgb(0.3, 0.4, 0.56); c.set_line_width(3); c.stroke()      # 长老的石台
        for i in range(13): _fig(c, 730 + i * 38.5, 640, 26, 0.96)
        for px in (-380, 140, 520, 1400, 1780, 2300):                                    # 旗
            c.rectangle(px - 4, 420, 8, 330); c.set_source_rgb(0.22, 0.3, 0.44); c.fill(); c.move_to(px + 4, 430); c.curve_to(px + 50, 440, px + 70, 420, px + 110, 436); c.line_to(px + 104, 560); c.curve_to(px + 70, 548, px + 44, 566, px + 4, 556); c.close_path(); c.set_source_rgb(0.92, 0.96, 1.0); c.fill_preserve(); c.set_source_rgb(0.3, 0.5, 0.7); c.set_line_width(3); c.stroke()
            c.move_to(px + 56, 456); c.line_to(px + 56, 532); c.move_to(px + 36, 512); c.line_to(px + 76, 512); c.set_source_rgb(0.2, 0.62, 0.72); c.set_line_width(6); c.stroke()
        for row in range(5):
            y = 742 + row * 15; s = 21 + row * 4.5; x = -880 + (row % 2) * s * 0.9
            while x < 2880:
                if not (640 < x < 1280 and row < 1): _fig(c, x + (rnd(int(x), row) - 0.5) * 6, y + (rnd(int(x), row + 9) - 0.5) * 3, s, 0.80 + 0.045 * row)
                x += s * 1.8
    out.append((_pl(crowd, -900, 400, 3800, 800, q * 0.8), 0.72))
    # 青石板地面
    def floor(c):
        g = cairo.LinearGradient(0, 800, 0, 1500); g.add_color_stop_rgb(0, 0.60, 0.69, 0.80); g.add_color_stop_rgb(0.25, 0.50, 0.58, 0.70); g.add_color_stop_rgb(1, 0.30, 0.36, 0.48); c.set_source(g); c.rectangle(-2200, 800, 6400, 800); c.fill()
        c.set_source_rgba(0.16, 0.22, 0.34, 0.55)
        for i in range(12): y = 800 + 5 * i + 5.2 * i * i; c.set_line_width(1.5 + i * 0.5); c.move_to(-2200, y); c.line_to(4200, y); c.stroke()
        for i in range(-60, 100): x = i * 130; c.set_line_width(2.2); c.move_to(960 + (x - 960) * 0.42, 800); c.line_to(960 + (x - 960) * 2.6, 1600); c.stroke()
        c.set_source_rgba(1, 1, 1, 0.5); c.set_line_width(3); c.move_to(-2200, 801); c.line_to(4200, 801); c.stroke()
    out.append((_pl(floor, -2200, 790, 6400, 820, q, alpha=True), 1.0))
    return out
