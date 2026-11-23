"""glass — 彩窗：window(draw, ...) 画一扇尖拱彩窗（玻璃 + 铅条），wall(...) 把几扇窗嵌进石墙。
    g, m = window(lambda c, gy: ..., w=600, h=940, seed=1, core=(r,g,b))      # draw 在 w×h 的 cairo 上画人物，gy = 地面 y
    img = wall([(g, m, x, y), ...])                                            # 1920×1080
"""
import math, numpy as np, cv2, cairo
from paper import layer, rgba
WARM = [(0.98, 0.78, 0.30), (0.95, 0.56, 0.16), (0.99, 0.88, 0.52), (0.90, 0.40, 0.14)]
COLD = [(0.16, 0.28, 0.62), (0.10, 0.18, 0.46), (0.22, 0.40, 0.72), (0.12, 0.22, 0.52)]
FLOOR = [(0.30, 0.22, 0.30), (0.38, 0.28, 0.34), (0.24, 0.18, 0.28)]
LEAD = np.float32((0.03, 0.025, 0.03))

def _edges(a, thr):
    e = np.zeros(a.shape[:2], np.float32); a3 = a if a.ndim == 3 else a[..., None]
    e[:, 1:] = np.maximum(e[:, 1:], np.abs(a3[:, 1:] - a3[:, :-1]).max(-1) > thr); e[1:] = np.maximum(e[1:], np.abs(a3[1:] - a3[:-1]).max(-1) > thr); return e
def _fat(e, k): return cv2.dilate(e, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))

def arch_mask(w, h, pad=6):
    s, c = layer(w, h); c.set_source_rgb(1, 1, 1); x0, x1 = pad, w - pad; sp = h * 0.36; top = pad; mid = w / 2
    c.move_to(x0, h - pad); c.line_to(x0, sp); c.curve_to(x0, sp - h * 0.16, mid - w * 0.16, top + h * 0.065, mid, top); c.curve_to(mid + w * 0.16, top + h * 0.065, x1, sp - h * 0.16, x1, sp); c.line_to(x1, h - pad); c.close_path(); c.fill()
    return rgba(s)[1]

def window(draw, w=600, h=940, seed=1, core=(0.80, 0.12, 0.10), warm=WARM, cold=COLD, floor=FLOOR, sun=(0.5, 0.50), R=0.36, gy=0.90, cell=84, ring=(0.99, 0.90, 0.60), mask=None, warm_r=2.4):
    r = np.random.default_rng(seed); GY = h * gy; SX, SY = w * sun[0], h * sun[1]; RR = w * R
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ang = np.degrees(np.arctan2(yy - SY, xx - SX)); d = np.sqrt((xx - SX) ** 2 + (yy - SY) ** 2)
    wedge = np.floor((ang + 180) / 12).astype(int); rg = np.floor(d / (RR * 0.62)).astype(int); warm = np.float32(warm); cold = np.float32(cold)
    flat = np.where((d < RR * warm_r)[..., None], warm[(wedge + rg) % 4], cold[(wedge + rg) % 4])
    flat = np.where((d < RR)[..., None], np.float32(core), flat); flat = np.where((np.abs(d - RR * 1.08) < RR * 0.08)[..., None], np.float32(ring), flat)
    tile = (np.floor(xx / 86) + np.floor((yy - GY) / 34) * 3).astype(int); flat = np.where((yy > GY)[..., None], np.float32(floor)[tile % 3], flat).astype(np.float32)
    s, c = layer(w, h); draw(c, GY); rgb, al = rgba(s); fa = al[..., 0]; flat = flat * (1 - al) + rgb
    seeds = np.ones((h, w), np.uint8)
    for gyy in range(0, h + cell, cell):
        for gx in range(0, w + cell, cell): seeds[int(np.clip(gyy + r.uniform(-30, 30), 0, h - 1)), int(np.clip(gx + r.uniform(-30, 30), 0, w - 1))] = 0
    _, lab = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    jit = r.uniform(0.80, 1.14, lab.max() + 1).astype(np.float32)[lab]; hue = r.uniform(-0.05, 0.05, (lab.max() + 1, 3)).astype(np.float32)[lab]
    glass = np.where((fa < 0.5)[..., None], np.clip(flat * jit[..., None] + hue, 0, 1), flat * (0.94 + 0.10 * cv2.GaussianBlur(r.random((h, w)).astype(np.float32), (0, 0), 14))[..., None])
    lead = _fat(_edges(flat, 0.07), 4); lead = np.maximum(lead, _fat(_edges(lab.astype(np.float32), 0.5) * (fa < 0.5), 4)); lead = np.maximum(lead, _fat(_edges(fa, 0.5), 7)); lead = cv2.GaussianBlur(lead, (0, 0), 0.8)
    soft = cv2.GaussianBlur(lead, (0, 0), 9); glass = glass * (1 - 0.38 * np.clip(soft * 1.6, 0, 1))[..., None]
    streak = cv2.GaussianBlur(r.random((h, w)).astype(np.float32), (0, 0), sigmaX=2, sigmaY=22); streak = (streak - streak.mean()) / streak.std()
    glass = np.clip(glass * (1 + 0.05 * streak)[..., None], 0, 1) * (0.74 + 0.48 * np.exp(-d / (RR * 2.6)))[..., None]
    glass = glass * (1 - lead[..., None]) + LEAD * lead[..., None]
    m = arch_mask(w, h) if mask is None else mask; border = np.clip(m[..., 0] - cv2.erode(m[..., 0], np.ones((13, 13), np.uint8)), 0, 1)[..., None]; glass = glass * (1 - border) + LEAD * border
    return glass.astype(np.float32), m

def wall(wins, W=1920, H=1080, seed=5, bloom=0.34):
    r = np.random.default_rng(seed); G = np.zeros((H, W, 3), np.float32); M = np.zeros((H, W, 1), np.float32)
    for g, m, x, y in wins:
        h, w = g.shape[:2]; G[y:y + h, x:x + w] = g * m + G[y:y + h, x:x + w] * (1 - m); M[y:y + h, x:x + w] = np.maximum(M[y:y + h, x:x + w], m)
    bl = cv2.GaussianBlur(G * M, (0, 0), 26); stone = np.float32((0.050, 0.045, 0.050)) * (0.8 + 0.4 * cv2.GaussianBlur(r.random((H, W)).astype(np.float32), (0, 0), 3))[..., None]
    edge = np.clip(cv2.GaussianBlur(M[..., 0], (0, 0), 5) - M[..., 0], 0, 1)[..., None]
    return np.clip(stone * (1 - M) + G * M + bl * bloom * (1 - M) + bl * 0.16 * M + edge * np.float32((0.30, 0.24, 0.18)) * 0.6, 0, 1), M

def triptych_mask(W=1920, H=1080):
    s, c = layer(W, H); c.set_source_rgb(1, 1, 1)
    for i in range(3):
        x0 = 96 + i * 588; x1 = x0 + 552; sp = 350; top = 52; mid = (x0 + x1) / 2
        c.move_to(x0, 936); c.line_to(x0, sp); c.curve_to(x0, sp - 150, mid - 90, top + 60, mid, top); c.curve_to(mid + 90, top + 60, x1, sp - 150, x1, sp); c.line_to(x1, 936); c.close_path(); c.fill()
    return rgba(s)[1]
