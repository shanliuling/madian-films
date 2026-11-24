"""sets — 斗破上集的其余场景（云岚宗广场在 yunlan.py）。每个函数返回 [(板, 深度)]，地面都在 GY = 860。"""
import math, numpy as np, cv2, cairo
from yunlan import _pl, _noise, _fig, _roof, GY
from action import rnd
def _sky(R, top, bot, W=2600, H=1700, stars=0, moon=None, glow=None):
    q = R.k; h, w = int(H * q), int(W * q); yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); v = np.clip(yy / h * 1.3, 0, 1)[..., None]; sky = np.float32(top) * (1 - v) + np.float32(bot) * v
    if stars: r = np.random.default_rng(2); pts = r.integers(0, [w, int(h * 0.6)], (stars, 2)); sky[pts[:, 1], pts[:, 0]] += r.uniform(0.3, 0.9, (stars, 1)).astype(np.float32)
    for g in ([moon] if moon else []) + ([glow] if glow else []):
        (gx, gy, rad, col, hard) = g; d = np.sqrt((xx - gx * w) ** 2 + (yy - gy * h) ** 2) / w; sky += np.float32(col) * (np.exp(-d / rad)[..., None] * 0.6 + (np.clip((hard - d) * 400, 0, 1)[..., None] if hard else 0))
    return (dict(rgb=np.clip(sky, 0, 1).astype(np.float32), a=None, x0=960 - W / 2, y0=420 - H / 2, ps=q), 0.03)
def _ridge(c, base, amp, col, col2, seed, step=70):
    c.move_to(-1200, 1500); x = -1200
    while x < 3200: i = int(x / step) + seed * 31; c.line_to(x, base - amp * rnd(i, seed) ** 1.5 - 30 * math.sin(x / 260 + seed)); x += step * (0.6 + 0.8 * rnd(i, seed + 5))
    c.line_to(3200, 1500); c.close_path(); g = cairo.LinearGradient(0, base - amp, 0, base + 200); g.add_color_stop_rgb(0, *col); g.add_color_stop_rgb(1, *col2); c.set_source(g); c.fill()
def _ground(c, col0, col1, y=GY - 60, lines=(0, 0, 0, 0.25)):
    g = cairo.LinearGradient(0, y, 0, y + 700); g.add_color_stop_rgb(0, *col0); g.add_color_stop_rgb(1, *col1); c.set_source(g); c.rectangle(-2200, y, 6400, 800); c.fill(); c.set_source_rgba(*lines)
    for i in range(10): yy = y + 6 * i + 6 * i * i; c.set_line_width(1.5 + i * 0.5); c.move_to(-2200, yy); c.line_to(4200, yy); c.stroke()
def stele(R):
    """萧家的测验广场：正中一块漆黑的测验魔石碑，四周是看热闹的族人。"""
    q = R.k * 2
    def back(c):
        _ridge(c, 700, 200, (0.55, 0.60, 0.70), (0.80, 0.80, 0.82), 1)
        for x in (-300, 250, 1500, 2100): c.rectangle(x - 160, 520, 320, 230); c.set_source_rgb(0.58, 0.52, 0.5); c.fill(); _roof(c, x, 540, 420, 120, (0.3, 0.26, 0.3), (0.2, 0.17, 0.2))
    def mid(c):
        c.rectangle(-900, 742, 3800, 500); c.set_source_rgb(0.52, 0.5, 0.52); c.fill()
        for row in range(5):
            y = 745 + row * 16; s = 26 + row * 5; x = -880 + (row % 2) * s
            while x < 2880:
                if abs(x - 960) > 330: k = 0.5 + 0.08 * row; c.move_to(x - s * 0.5, y); c.line_to(x - s * 0.4, y - s * 1.6); c.line_to(x + s * 0.4, y - s * 1.6); c.line_to(x + s * 0.5, y); c.close_path(); c.set_source_rgb(0.5 * k + 0.3 * rnd(int(x), row), 0.42 * k + 0.2, 0.45 * k + 0.2); c.fill(); c.arc(x, y - s * 1.85, s * 0.3, 0, 7); c.set_source_rgb(0.12, 0.1, 0.12); c.fill()
                x += s * 1.5
        c.move_to(790, 870); c.line_to(810, 150); c.line_to(880, 90); c.line_to(1040, 90); c.line_to(1110, 150); c.line_to(1130, 870); c.close_path(); g = cairo.LinearGradient(790, 0, 1130, 0); g.add_color_stop_rgb(0, 0.10, 0.10, 0.13); g.add_color_stop_rgb(0.5, 0.03, 0.03, 0.05); g.add_color_stop_rgb(1, 0.0, 0.0, 0.02); c.set_source(g); c.fill_preserve(); c.set_source_rgb(0.3, 0.3, 0.36); c.set_line_width(5); c.stroke()
    def fl(c): _ground(c, (0.66, 0.63, 0.62), (0.36, 0.34, 0.38))
    return [_sky(R, (0.42, 0.52, 0.70), (0.86, 0.84, 0.80)), (_pl(back, -900, 100, 3800, 1200, q * 0.5), 0.2), (_pl(mid, -900, 60, 3800, 1140, q * 0.8), 0.8), (_pl(fl, -2200, 790, 6400, 820, q), 1.0)]
def hall(R):
    """萧家大厅：深色木墙、红柱、灯笼；首位的高座在右边。"""
    q = R.k * 2
    def wall(c):
        g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgb(0, 0.10, 0.06, 0.06); g.add_color_stop_rgb(1, 0.30, 0.17, 0.13); c.set_source(g); c.rectangle(-900, -300, 3800, 1200); c.fill()
        for x in range(-800, 2900, 260): c.rectangle(x - 80, 250, 160, 330); c.set_source_rgba(0.95, 0.78, 0.5, 0.10); c.fill(); c.set_source_rgba(0.05, 0.03, 0.03, 0.8); c.set_line_width(6); c.rectangle(x - 80, 250, 160, 330); c.stroke(); c.move_to(x, 250); c.line_to(x, 580); c.move_to(x - 80, 415); c.line_to(x + 80, 415); c.stroke()
    def cols(c):
        for x in range(-700, 2900, 520):
            c.rectangle(x - 34, -300, 68, 1170); c.set_source_rgb(0.5, 0.1, 0.1); c.fill(); c.rectangle(x - 34, -300, 20, 1170); c.set_source_rgba(1, 0.6, 0.4, 0.18); c.fill()
            c.arc(x + 130, 250, 38, 0, 7); gr = cairo.RadialGradient(x + 130, 250, 0, x + 130, 250, 150); gr.add_color_stop_rgba(0, 1, 0.8, 0.45, 0.9); gr.add_color_stop_rgba(0.25, 1, 0.55, 0.25, 0.5); gr.add_color_stop_rgba(1, 1, 0.5, 0.2, 0); c.set_source(gr); c.arc(x + 130, 250, 150, 0, 7); c.fill()
        c.rectangle(1560, 610, 300, 260); c.set_source_rgb(0.2, 0.1, 0.09); c.fill(); c.rectangle(1540, 450, 340, 170); c.set_source_rgb(0.34, 0.14, 0.12); c.fill(); c.set_source_rgb(0.8, 0.62, 0.3); c.set_line_width(5); c.rectangle(1540, 450, 340, 170); c.stroke()                 # 首位
        c.rectangle(1000, 760, 380, 26); c.set_source_rgb(0.32, 0.16, 0.1); c.fill(); c.rectangle(1020, 786, 20, 80); c.rectangle(1340, 786, 20, 80); c.fill()                                                              # 桌
    def fl(c): _ground(c, (0.40, 0.25, 0.19), (0.14, 0.08, 0.07), lines=(0, 0, 0, 0.35))
    return [(dict(_pl(wall, -900, -300, 3800, 1200, q * 0.5), a=None), 0.55), (_pl(cols, -900, -300, 3800, 1200, q * 0.8), 0.85), (_pl(fl, -2200, 790, 6400, 820, q), 1.0)]
def night(R, kind='cliff'):
    """夜里的野外。cliff：悬崖和月亮；gate：萧家大门；cave：山洞；wild：山林。"""
    q = R.k * 2
    def far(c): _ridge(c, 690, 260, (0.10, 0.14, 0.30), (0.20, 0.26, 0.42), 3); _ridge(c, 760, 170, (0.06, 0.09, 0.20), (0.12, 0.16, 0.30), 4)
    def cliff(c):
        c.move_to(-2200, GY - 40); c.line_to(1250, GY - 40); c.curve_to(1330, GY - 20, 1290, GY + 120, 1220, 1700); c.line_to(-2200, 1700); c.close_path(); g = cairo.LinearGradient(0, GY - 40, 0, 1500); g.add_color_stop_rgb(0, 0.20, 0.24, 0.36); g.add_color_stop_rgb(1, 0.04, 0.05, 0.10); c.set_source(g); c.fill()
    def gate(c):
        c.rectangle(-900, 380, 3800, 500); c.set_source_rgb(0.13, 0.13, 0.19); c.fill(); c.rectangle(700, 330, 520, 550); c.set_source_rgb(0.08, 0.05, 0.06); c.fill(); _roof(c, 960, 350, 760, 150, (0.07, 0.08, 0.13), (0.2, 0.2, 0.28)); c.rectangle(820, 372, 280, 80); c.set_source_rgb(0.05, 0.04, 0.05); c.fill_preserve(); c.set_source_rgb(0.5, 0.4, 0.22); c.set_line_width(5); c.stroke()
        c.rectangle(760, 470, 195, 410); c.rectangle(965, 470, 195, 410); c.set_source_rgb(0.22, 0.07, 0.07); c.fill()
    def cave(c):
        c.rectangle(-900, -400, 3800, 1700); c.set_source_rgb(0.05, 0.05, 0.08); c.fill()
        for i in range(40): x = -800 + i * 95; h = 120 + 260 * rnd(i, 7); c.move_to(x - 70, -400); c.line_to(x, -100 + h); c.line_to(x + 70, -400); c.close_path(); c.set_source_rgb(0.09, 0.09, 0.13); c.fill()
    def fl(c): _ground(c, (0.16, 0.19, 0.30), (0.04, 0.05, 0.10), lines=(0, 0, 0, 0.3))
    sky = _sky(R, (0.01, 0.02, 0.08), (0.10, 0.16, 0.34), stars=260, moon=(0.70, 0.22, 0.05, (0.8, 0.86, 1.0), 0.028))
    if kind == 'cliff': return [sky, (_pl(far, -1200, 100, 4400, 1200, q * 0.5), 0.12), (_pl(cliff, -2200, 780, 6400, 920, q), 1.0)]
    if kind == 'gate': return [sky, (_pl(gate, -900, 100, 3800, 800, q * 0.8), 0.8), (_pl(fl, -2200, 790, 6400, 820, q), 1.0)]
    if kind == 'cave': return [(dict(_pl(cave, -900, -400, 3800, 1700, q * 0.5), a=None), 0.5), (_pl(fl, -2200, 790, 6400, 820, q), 1.0)]
    return [sky, (_pl(far, -1200, 100, 4400, 1200, q * 0.5), 0.12), (_pl(fl, -2200, 790, 6400, 820, q), 1.0)]
def border(R):
    """清晨，加玛帝国的边关。"""
    q = R.k * 2
    def far(c): _ridge(c, 720, 200, (0.45, 0.32, 0.42), (0.95, 0.66, 0.5), 5)
    def wall(c):
        c.rectangle(1100, 430, 2200, 450); c.set_source_rgb(0.22, 0.16, 0.2); c.fill()
        for x in range(1100, 3300, 90): c.rectangle(x, 395, 50, 40); c.fill()
        c.move_to(1380, 880); c.line_to(1380, 640); c.curve_to(1380, 540, 1580, 540, 1580, 640); c.line_to(1580, 880); c.close_path(); c.set_source_rgb(0.98, 0.78, 0.55); c.fill()
    def fl(c): _ground(c, (0.60, 0.42, 0.38), (0.2, 0.13, 0.16), lines=(0, 0, 0, 0.2))
    return [_sky(R, (0.20, 0.22, 0.45), (1.0, 0.72, 0.48), glow=(0.56, 0.60, 0.10, (1.0, 0.8, 0.5), 0)), (_pl(far, -1200, 100, 4400, 1200, q * 0.5), 0.12), (_pl(wall, -900, 300, 4400, 600, q * 0.8), 0.8), (_pl(fl, -2200, 790, 6400, 820, q), 1.0)]
