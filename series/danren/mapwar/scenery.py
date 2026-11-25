"""人物镜头的背景和道具（全部代码画）。
  landscape(kind) -> HxWx3 float32：水墨感场景底（天空渐变 + 层叠远山 + 地面肌理 + 宣纸纤维），kind: day / dusk / night / hall
  burn(a, b, k)   -> 火焰烧穿转场（从 a 烧出 b）
  grass / reeds / tent / fire / snow / boat / dust：画在 cairo 上的小道具
"""
import math, cairo, numpy as np
from scipy.ndimage import gaussian_filter, zoom
W, H = 1920, 1080
_C = {}


def _noise1d(n, seed, octaves=((900, 1.0), (380, 0.45), (150, 0.2), (60, 0.08))):
    r = np.random.default_rng(seed); x = np.arange(n, dtype=np.float32); out = np.zeros(n, np.float32)
    for wl, a in octaves:
        k = int(n / wl) + 3; g = r.standard_normal(k).astype(np.float32)
        out += a * np.interp(x / wl, np.arange(k), g)
    return out


def _noise2d(seed, s=(54, 96), sig=0):
    r = np.random.default_rng(seed); g = r.standard_normal(s).astype(np.float32)
    z = zoom(g, (H / s[0], W / s[1]), order=3)[:H, :W]
    return gaussian_filter(z, sig) if sig else z


def _paper(seed=3):
    r = np.random.default_rng(seed)
    fib = gaussian_filter(r.standard_normal((H, W)).astype(np.float32), (0.6, 3.0)) * 0.6 + gaussian_filter(r.standard_normal((H, W)).astype(np.float32), (3.0, 0.6)) * 0.6
    blot = _noise2d(seed + 1, (12, 20)) * 0.5 + _noise2d(seed + 2, (40, 70)) * 0.25
    return 1 + 0.035 * fib + 0.03 * blot


def _vgrad(top, bot, y0=0, y1=H, gamma=1.0):
    yy = np.clip((np.arange(H, dtype=np.float32) - y0) / max(1, y1 - y0), 0, 1) ** gamma
    col = np.float32(top)[None] * (1 - yy[:, None]) + np.float32(bot)[None] * yy[:, None]
    return np.repeat(col[:, None, :], W, 1)


def _ridge(img, base, amp, col, seed, edge=(0.0, 0.0, 0.0), mist=180, edge_w=5, sharp=1.0, haze=None):
    """一层山：山脊线 = base - amp*噪声；山体从脊线往下渐隐成雾。"""
    n = _noise1d(W, seed); n = (n - n.min()) / (np.ptp(n) + 1e-6)
    pk = np.abs(np.sin(np.arange(W) / W * math.pi * (2 + seed % 3) + seed)) ** 1.5 * 0.35
    ry = base - amp * (n * 0.75 + pk) ** sharp
    yy = np.arange(H, dtype=np.float32)[:, None]; d = yy - ry[None, :]
    a = np.clip(d / 2.0, 0, 1) * np.clip(1 - d / mist, 0.0, 1) ** 1.2                     # 山脚起雾
    a = a * (0.75 + 0.25 * gaussian_filter(np.random.default_rng(seed).random((H, W)).astype(np.float32), 6))
    e = np.exp(-np.clip(d, 0, None) / edge_w) * (d > -1)                                        # 墨色山脊
    img[:] = img * (1 - a[..., None]) + np.float32(col) * a[..., None]
    img[:] = img * (1 - 0.55 * e[..., None]) + np.float32(edge) * 0.55 * e[..., None]
    return ry


def landscape(kind):
    if kind in _C: return _C[kind]
    P = _paper()[..., None]
    if kind == 'day':
        img = _vgrad((0.86, 0.84, 0.78), (0.95, 0.92, 0.84), 0, 720, 0.8)
        _ridge(img, 560, 200, (0.70, 0.73, 0.72), 11, (0.45, 0.48, 0.48), 260, 4)
        _ridge(img, 640, 160, (0.56, 0.61, 0.58), 12, (0.30, 0.33, 0.32), 200, 5)
        _ridge(img, 720, 120, (0.42, 0.48, 0.44), 13, (0.18, 0.20, 0.19), 150, 6)
        g = _vgrad((0.80, 0.74, 0.60), (0.66, 0.58, 0.44), 760, H)
        m = np.clip((np.arange(H, dtype=np.float32) - 760) / 20, 0, 1)[:, None, None]
        tex = 1 + 0.025 * _noise2d(21, (14, 26))[..., None] + 0.02 * _noise2d(22, (60, 110), 1.5)[..., None]
        img = img * (1 - m) + g * tex * m
    elif kind == 'dusk':
        img = _vgrad((0.36, 0.30, 0.42), (0.98, 0.66, 0.40), 0, 690, 1.1)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.hypot(xx - 560, yy - 650)
        img += (np.exp(-(d / 260) ** 2) * 0.35)[..., None] * np.float32([1.0, 0.6, 0.25])
        img = np.where((d < 120)[..., None], np.float32([1.0, 0.62, 0.30]), img)
        _ridge(img, 600, 170, (0.62, 0.42, 0.45), 31, (0.40, 0.25, 0.30), 220, 4)
        _ridge(img, 680, 110, (0.45, 0.30, 0.36), 32, (0.25, 0.15, 0.20), 120, 5)
        wat = _vgrad((0.62, 0.50, 0.50), (0.30, 0.32, 0.40), 700, H)
        m = (yy >= 700).astype(np.float32)[..., None]
        sh = np.exp(-((xx - 560) / (90 + np.maximum(yy - 700, 0) * 0.9)) ** 2) * (yy >= 700) * (0.5 + 0.5 * np.sin(yy * 0.9 + np.sin(xx * 0.02) * 2)) ** 6 * 0.6
        img = img * (1 - m) + (wat + sh[..., None] * np.float32([1.0, 0.65, 0.35]) * 0.7) * m
    elif kind == 'night':
        img = _vgrad((0.05, 0.07, 0.14), (0.20, 0.24, 0.36), 0, 700, 0.9)
        r = np.random.default_rng(5); ys, xs = r.integers(0, 600, 260), r.integers(0, W, 260); b = r.uniform(0.3, 1.0, 260)
        st = np.zeros((H, W), np.float32); st[ys, xs] = b; st = gaussian_filter(st, 0.8) * 6
        img += np.clip(st, 0, 1)[..., None] * np.float32([0.9, 0.92, 1.0])
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.hypot(xx - 1500, yy - 200)
        img += (np.exp(-(d / 180) ** 2) * 0.25)[..., None] * np.float32([0.8, 0.85, 1.0])
        img = np.where((d < 62)[..., None], np.float32([0.95, 0.93, 0.85]), img)
        _ridge(img, 600, 160, (0.16, 0.19, 0.28), 41, (0.06, 0.07, 0.11), 220, 4)
        _ridge(img, 690, 110, (0.11, 0.13, 0.20), 42, (0.03, 0.04, 0.07), 140, 5)
        g = _vgrad((0.30, 0.31, 0.36), (0.20, 0.21, 0.26), 760, H)
        m = np.clip((yy - 760) / 20, 0, 1)[..., None]
        tex = 1 + 0.035 * _noise2d(51, (14, 26))[..., None] + 0.03 * _noise2d(52, (60, 110), 1.5)[..., None]
        img = img * (1 - m) + g * tex * m
    elif kind == 'hall':                                                               # 营帐内：暖色帷幕 + 地毯
        img = _vgrad((0.42, 0.20, 0.14), (0.62, 0.36, 0.22), 0, 760)
        xx = np.arange(W, dtype=np.float32)[None, :, None]
        img = img * (0.88 + 0.12 * np.cos(xx / 70) ** 2)
        g = _vgrad((0.55, 0.40, 0.28), (0.40, 0.28, 0.20), 760, H); m = np.clip((np.arange(H, dtype=np.float32) - 760) / 8, 0, 1)[:, None, None]
        img = img * (1 - m) + g * m
    else: raise ValueError(kind)
    out = np.clip(img * P, 0, 1).astype(np.float32)
    _C[kind] = out
    return out


# ================================================================ 火焰转场
_N = {}
def _noise(seed=7):
    if seed not in _N:
        r = np.random.default_rng(seed); acc = np.zeros((1080, 1920), np.float32)
        for s, a in ((12, 1.0), (27, 0.5), (60, 0.25), (130, 0.12)):
            g = r.standard_normal((s * 9 // 16 + 2, s + 2)).astype(np.float32)
            acc += a * zoom(g, (1080 / g.shape[0], 1920 / g.shape[1]), order=3)[:1080, :1920]
        _N[seed] = (acc - acc.mean()) / acc.std()
    return _N[seed]
_D = None
def burn(a, b, k, cx=0.5, cy=0.5, seed=7, edge=0.045):
    """a, b: HxWx3 float32 0..1 同尺寸。返回合成帧"""
    global _D
    H, W = a.shape[:2]; n = _noise(seed)
    if n.shape != (H, W): n = zoom(n, (H / n.shape[0], W / n.shape[1]), order=1)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx / W - cx) * 1.78) ** 2 + (yy / H - cy) ** 2) / 1.02 + 0.09 * n
    front = -0.12 + 1.25 * k
    e = (front - d) / edge                                   # >0 已烧穿
    hole = np.clip(e, 0, 1)[..., None]
    char = np.clip(1 - (d - front) / (edge * 3.5), 0, 1)[..., None] * (e < 0)[..., None]   # 未烧处焦黑边
    glow = np.exp(-((d - front) / (edge * 0.9)) ** 2)[..., None]
    out = a * (1 - 0.85 * char) + np.float32([0.25, 0.08, 0.02]) * char * 0.6
    out = out * (1 - hole) + b * hole
    out = out + glow * np.float32([1.0, 0.55, 0.12]) * 1.3 + glow ** 3 * np.float32([1, 0.95, 0.6]) * 0.6
    return np.clip(out, 0, 1)


# ================================================================ 道具
from .qdraw import poly, OL


def _fs(c, col, lw):
    c.set_source_rgb(*col); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(lw); c.stroke()




def grass(c, x0, x1, y0, y1, n=60, seed=1, col=(0.25, 0.22, 0.15), t=0.0):
    r = np.random.default_rng(seed)
    for _ in range(n):
        x, y = r.uniform(x0, x1), r.uniform(y0, y1); s = 0.6 + 0.8 * (y - y0) / max(1, y1 - y0); c.set_source_rgba(*col, 0.55); c.set_line_width(2.2 * s)
        for k in (-1, 0, 1):
            c.move_to(x, y); c.curve_to(x + k * 6 * s, y - 14 * s, x + k * 10 * s + 3 * math.sin(t * 2 + x), y - 22 * s, x + k * 14 * s + 4 * math.sin(t * 2 + x), y - 30 * s); c.stroke()


def tent(c, x, y, w, col):
    poly(c, [(x - w / 2, y), (x, y - w * 0.62), (x + w / 2, y)]); _fs(c, col, 4)
    c.save(); poly(c, [(x - w / 2, y), (x, y - w * 0.62), (x + w / 2, y)]); c.clip(); c.set_source_rgba(0, 0, 0, 0.18); c.rectangle(x, y - w, w, w); c.fill(); c.restore()
    poly(c, [(x - w * 0.08, y), (x, y - w * 0.3), (x + w * 0.08, y)]); _fs(c, (0.25, 0.2, 0.16), 3)


def fire(c, x, y, s, t):
    for k, (col, sc_) in enumerate((((1.0, 0.45, 0.1), 1.0), ((1.0, 0.8, 0.25), 0.6))):
        w = s * 0.5 * sc_; h = s * sc_ * (1 + 0.12 * math.sin(t * 13 + k))
        c.move_to(x - w, y); c.curve_to(x - w, y - h * 0.5, x - w * 0.2, y - h * 0.7, x + 0.1 * w * math.sin(t * 9), y - h); c.curve_to(x + w * 0.3, y - h * 0.6, x + w, y - h * 0.5, x + w, y); c.close_path(); c.set_source_rgb(*col); c.fill()


def snow(c, t, n=160, seed=4):
    r = np.random.default_rng(seed); x0 = r.uniform(0, W, n); sp = r.uniform(30, 90, n); ph = r.uniform(0, H, n); sz = r.uniform(2, 5, n)
    c.set_source_rgba(1, 1, 1, 0.8)
    for i in range(n):
        y = (ph[i] + t * sp[i]) % (H + 20) - 10; x = x0[i] + math.sin(t * 0.8 + i) * 20; c.arc(x, y, sz[i], 0, 2 * math.pi); c.fill()


def boat(c, bx, by, w):
    poly(c, [(bx - w / 2, by), (bx + w / 2, by), (bx + w * 0.38, by + 0.12 * w), (bx - w * 0.38, by + 0.12 * w)]); _fs(c, (0.50, 0.34, 0.20), 4)
    c.set_source_rgba(0, 0, 0, 0.2); c.rectangle(bx - w * 0.38, by + 0.07 * w, w * 0.76, 0.05 * w); c.fill()
    c.set_source_rgba(1, 0.75, 0.45, 0.35); c.set_line_width(3)
    for k in range(4): c.move_to(bx - w * 0.4 + k * 12, by + 0.16 * w + k * 9); c.line_to(bx + w * 0.4 - k * 12, by + 0.16 * w + k * 9); c.stroke()


def reeds(c, x0, x1, base, hgt, seed, t, col=(0.18, 0.13, 0.10), a=0.85):
    r = np.random.default_rng(seed)
    for _ in range(int((x1 - x0) / 9)):
        x = r.uniform(x0, x1); hh = hgt * r.uniform(0.5, 1.0); sway = 10 * math.sin(t * 1.5 + x * 0.01)
        c.set_source_rgba(*col, a); c.set_line_width(r.uniform(2, 4)); c.move_to(x, base); c.curve_to(x, base - hh * 0.5, x + sway * 0.5, base - hh * 0.8, x + sway, base - hh); c.stroke()
        if r.random() < 0.4:
            c.save(); c.translate(x + sway, base - hh); c.rotate(0.3 * math.sin(x)); c.scale(1, 3); c.arc(0, 0, 5, 0, 2 * math.pi); c.restore(); c.fill()


def dust(c, x, y, t, seed, n=6, s=1.0):
    r = np.random.default_rng(seed)
    for k in range(n):
        ph = (t * 1.5 + r.random()) % 1.0; px = x - ph * 160 * s + r.normal(0, 20); py = y - ph * 40 * s; rr = (14 + 40 * ph) * s
        c.set_source_rgba(0.90, 0.86, 0.74, 0.75 * (1 - ph)); c.arc(px, py, rr, 0, 2 * math.pi); c.fill_preserve(); c.set_source_rgba(*OL, 0.5 * (1 - ph)); c.set_line_width(1.5); c.stroke()
