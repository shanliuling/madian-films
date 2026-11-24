"""fx — 斗破系列自己的招牌手法：漫画分格、火烧转场、墨稿定格、出场名牌、石碑等级牌、莲花绽放、翅膀、正面的萧炎、敌人的背影。
画在 cairo 上的（lotus / petals / wing / front / back）用场景坐标；处理整帧的（panels / burn / ink / tag / badge）吃 float32 的帧。"""
import os, math, functools, numpy as np, cv2, cairo
from PIL import Image, ImageDraw, ImageFont
from paper import FONT
import action as A
from action import rnd
BRUSH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'MaShanZheng-Regular.ttf'); INK = (0.05, 0.05, 0.09)
def _cl(v): return max(0.0, min(1.0, v))

# ---------------- 整帧的手法
def panels(R, items, t, bg=(0.03, 0.03, 0.05), base=None):
    """漫画分格。items = [(四边形(1920×1080 坐标), 一整帧画面, 进场时刻, (焦点x, 焦点y, 放大))]；每格在自己的时刻砸进来。"""
    out = np.empty((R.h, R.w, 3), np.float32); out[:] = bg
    if base is not None: out = base.copy()
    for poly, fr, t0, (fx_, fy_, z) in items:
        if t < t0: continue
        k = _cl((t - t0) / 0.13); P_ = np.float32(poly) * R.k; x0, y0 = P_.min(0); x1, y1 = P_.max(0); s = max((x1 - x0) / R.w, (y1 - y0) / R.h) * z * (1 + 0.22 * (1 - k) ** 2)
        M = np.float32([[s, 0, (x0 + x1) / 2 - fx_ * R.k * s], [0, s, (y0 + y1) / 2 - fy_ * R.k * s]]); img = cv2.warpAffine(fr, M, (R.w, R.h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        c0 = P_.mean(0); Q = ((P_ - c0) * (1 + 0.10 * (1 - k) ** 2) + c0).astype(np.int32); m = np.zeros((R.h, R.w), np.float32); cv2.fillPoly(m, [Q], 1.0, cv2.LINE_AA); m = m[..., None]
        out = out * (1 - m) + (img + (1 - img) * 0.75 * (1 - k)) * m; cv2.polylines(out, [Q], True, (0.97, 0.97, 0.97), max(2, int(9 * R.k)), cv2.LINE_AA); cv2.polylines(out, [Q], True, (0.02, 0.02, 0.03), max(1, int(3 * R.k)), cv2.LINE_AA)
    return out
@functools.lru_cache(maxsize=8)
def _noise(w, h, seed, mode):
    r = np.random.default_rng(seed); n = cv2.resize(r.random((h // 24 + 2, w // 24 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC); n2 = cv2.resize(r.random((h // 90 + 2, w // 90 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); g = {'lr': xx / w, 'rl': 1 - xx / w, 'up': 1 - yy / h, 'out': np.hypot(xx - w / 2, (yy - h / 2) * 1.5) / (w * 0.62), 'in': 1 - np.hypot(xx - w / 2, (yy - h / 2) * 1.5) / (w * 0.62)}[mode]
    v = g * 0.76 + n * 0.08 + n2 * 0.16; return ((v - v.min()) / (v.max() - v.min()))[..., None]
def burn(a, b, k, col, R, seed=1, mode='lr'):
    """火烧转场：a 被一条火线烧穿，露出 b。k: 0→1；col: 这一段的火色。"""
    n = _noise(R.w, R.h, seed, mode); d = k * 1.24 - 0.12 - n; m = np.clip(d / 0.02, 0, 1); char = np.clip(1 + d / 0.10, 0, 1) * (1 - m); edge = np.exp(-(d / 0.035) ** 2); core = np.exp(-(d / 0.012) ** 2)
    out = a * (1 - m) * (1 - 0.85 * char) + b * m; return np.clip(out + edge * np.float32(col) * 1.3 + core * 0.9, 0, 1)
@functools.lru_cache(maxsize=2)
def _dots(w, h, p):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); u = (xx + yy) / p % 1 - 0.5; v = (xx - yy) / p % 1 - 0.5; return np.hypot(u, v)
def ink(fr, R, k=1.0, paper=(0.97, 0.95, 0.90), tint=None):
    """墨稿定格：这一帧变成黑白漫画稿（黑、网点、留白三档）。k=混合量；tint=给留白染一点火色。"""
    g = fr @ np.float32([0.3, 0.59, 0.11]); g = cv2.GaussianBlur(g, (0, 0), 0.8 * R.k * 2); lo, hi = np.quantile(g, 0.30), np.quantile(g, 0.78); d = _dots(R.w, R.h, max(4.0, 9 * R.k * 2))
    tone = np.where(g < lo, 0.0, np.where(g < hi, (d > 0.30 + 0.25 * (hi - g) / max(1e-3, hi - lo)).astype(np.float32), 1.0)); e = cv2.Laplacian(g, cv2.CV_32F, ksize=3); tone = np.clip(tone - np.clip(np.abs(e) * 10 - 0.35, 0, 1), 0, 1)
    out = tone[..., None] * np.float32(paper if tint is None else tint) + (1 - tone[..., None]) * np.float32((0.04, 0.04, 0.06)); return fr * (1 - k) + out * k
_tc = {}
def tag(fr, R, name, sub, col, k, side='l', y=800):
    """出场名牌：斜黑条 + 毛笔名字 + 小字（等级/身份）+ 一道火色。k: 0→1 滑进来。"""
    key = (name, sub, col, R.w)
    if key not in _tc:
        f1 = ImageFont.truetype(BRUSH, int(104 * R.k)); f2 = ImageFont.truetype(FONT, int(38 * R.k)); w = int(max(f1.getlength(name) + 130 * R.k, f2.getlength(sub) + 150 * R.k) + 120 * R.k); h = int(190 * R.k); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); sk = 46 * R.k
        d.polygon([(sk, 0), (w, 0), (w - sk, h), (0, h)], fill=(8, 8, 14, 225)); d.polygon([(sk, 0), (sk + 16 * R.k, 0), (16 * R.k, h), (0, h)], fill=tuple(int(v * 255) for v in col) + (255,))
        d.text((sk + 50 * R.k, 62 * R.k), name, font=f1, fill=(255, 255, 255, 255), anchor='lm'); d.text((sk + 40 * R.k, 148 * R.k), sub, font=f2, fill=tuple(int(120 + v * 135) for v in col) + (255,), anchor='lm'); b = np.asarray(im, np.float32) / 255; _tc[key] = (b[..., :3] * b[..., 3:], b[..., 3:])
    rgb, al = _tc[key]; h, w = al.shape[:2]; e = 1 - (1 - _cl(k)) ** 3; x0 = int((70 * R.k - (1 - e) * (w + 80 * R.k)) if side == 'l' else (R.w - w - 70 * R.k + (1 - e) * (w + 80 * R.k))); y0 = int(y * R.k); xa, xb = max(0, x0), min(R.w, x0 + w); ya, yb = max(0, y0), min(R.h, y0 + h)
    if xa >= xb or ya >= yb: return fr
    fr = fr.copy(); sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0)); fr[ya:yb, xa:xb] = fr[ya:yb, xa:xb] * (1 - al[sl]) + rgb[sl]; return fr
_bc = {}
def badge(fr, R, text, flip=1.0, a=1.0):
    """左上角的小石碑：他现在的等级。flip: 0→1 换字时翻出来。"""
    if a <= 0: return fr
    if (text, R.w) not in _bc:
        f = ImageFont.truetype(FONT, int(40 * R.k)); w = int(f.getlength(text) + 84 * R.k); h = int(78 * R.k); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); q = 14 * R.k
        d.polygon([(q, 0), (w - q, 0), (w, q), (w, h), (0, h), (0, q)], fill=(10, 10, 16, 235), outline=(200, 160, 70, 255), width=max(1, int(3 * R.k))); d.text((w / 2, h / 2), text, font=f, fill=(255, 208, 100, 255), anchor='mm'); b = np.asarray(im, np.float32) / 255; _bc[(text, R.w)] = (b[..., :3] * b[..., 3:], b[..., 3:])
    rgb, al = _bc[(text, R.w)]; k = _cl(flip); h0, w = al.shape[:2]; h = max(1, int(h0 * (1 - (1 - k) ** 2)))
    if h != h0: rgb = cv2.resize(rgb, (w, h)); al = cv2.resize(al, (w, h))[..., None]
    x0 = int(56 * R.k); y0 = int(48 * R.k + (h0 - h) / 2); fr = fr.copy(); fr[y0:y0 + h, x0:x0 + w] = fr[y0:y0 + h, x0:x0 + w] * (1 - al * a) + (rgb + (1 - k) * 1.5 * al * np.float32((1, 0.8, 0.4))) * a; return fr

# ---------------- 画在 cairo 上的
def _petal(c, L, w): c.new_path(); c.move_to(0, 0); c.curve_to(L * 0.30, -w, L * 0.72, -w * 0.9, L, 0); c.curve_to(L * 0.72, w * 0.9, L * 0.30, w, 0, 0); c.close_path()
def lotus(c, pos, r, t, ca, cb, op=(1, 1, 1), tilt=1.0, a=1.0, spin=0.6, solid=False):
    """佛怒火莲：三层花瓣，op=(外, 中, 内) 各自开了多少。tilt<1 是侧着看。solid=True 画成有墨线的实体（普通层），否则画光（glow 层）。"""
    c.save(); c.translate(*pos); c.scale(1, tilt)
    if not solid: A.burst(c, (0, 0), r * 1.8, ca, a * 0.30)
    for j, (n, L, w) in enumerate(((9, 1.0, 0.30), (7, 0.74, 0.27), (5, 0.48, 0.22))):
        o = _cl(op[j])
        if o <= 0: continue
        e = 1 - (1 - o) ** 3; Lj = r * L * (0.22 + 0.78 * e); wj = r * w * (0.30 + 0.70 * e)
        for i in range(n):
            col = ca if (i + j) % 2 == 0 else cb; c.save(); c.rotate(i / n * 6.2832 + t * spin * (1 if j % 2 == 0 else -1) + j * 0.4); _petal(c, Lj, wj); g = cairo.LinearGradient(0, 0, Lj, 0)
            if solid: g.add_color_stop_rgba(0, 1, 1, 1, a); g.add_color_stop_rgba(0.4, *col, a); g.add_color_stop_rgba(1, *[v * 0.55 for v in col], a); c.set_source(g); c.fill_preserve(); c.set_source_rgba(*INK, a); c.set_line_width(max(1.5, r * 0.016)); c.stroke()
            else: g.add_color_stop_rgba(0, 1, 1, 1, a * 0.9); g.add_color_stop_rgba(0.45, *col, a * 0.75); g.add_color_stop_rgba(1, *col, a * 0.25); c.set_source(g); c.fill()
            c.restore()
    if not solid: A.burst(c, (0, 0), r * 0.40, (1, 1, 1), a)
    c.restore()
def petals(c, pos, t, t0, r, ca, cb, n=28, tilt=1.0, life=1.0, seed=3):
    """莲花炸开：花瓣当冲击波飞出去。"""
    dt = t - t0
    if not 0 <= dt < life: return
    k = dt / life
    for i in range(n):
        th = i / n * 6.2832 + rnd(i, seed) * 0.5; d = r * (0.3 + (1.6 + 2.2 * rnd(i, seed + 1)) * (1 - (1 - k) ** 2.4)); L = r * (0.34 + 0.3 * rnd(i, seed + 2)) * (1 - 0.5 * k); c.save(); c.translate(pos[0] + math.cos(th) * d, pos[1] + math.sin(th) * d * tilt); c.rotate(th + dt * (4 + 6 * rnd(i, seed + 3)) * (1 if i % 2 else -1)); _petal(c, L, L * 0.3)
        c.set_source_rgba(*(ca if i % 2 else cb), 0.9 * (1 - k) ** 1.2); c.fill(); c.restore()
def lotus_mark(c, pos, r, a=1.0, n=9):
    """地上烧出来的莲花印（普通层）。"""
    c.save(); c.translate(*pos); c.scale(1, 0.24)
    for j, (L, al) in enumerate(((1.0, 0.55), (0.62, 0.7))):
        for i in range(n): c.save(); c.rotate(i / n * 6.2832 + j * 0.35); _petal(c, r * L, r * L * 0.3); c.set_source_rgba(0.04, 0.03, 0.06, al * a); c.fill(); c.restore()
    c.restore()
def wing(c, root, side, S, op, t, ca=(0.20, 0.08, 0.36), cb=(0.72, 0.35, 1.0), glow=False, qi=False, flap=0.0, n=10, seed=0):
    """一只翼。side=±1（往哪边展）；S=翼展；op: 0 收着 → 1 全开；glow=True 只画发光的边（放 back/glow 层）；qi=True 是斗气化成的翼（半透明）。"""
    op = _cl(op); e = 1 - (1 - op) ** 2.2; fl = math.radians(flap + 7 * math.sin(t * 7 + seed)); c.save(); c.translate(*root); c.rotate(-side * fl)
    wr = (side * S * 0.36 * (0.3 + 0.7 * e), -S * 0.40 * (0.2 + 0.8 * e)); tip = (side * S * (0.12 + 0.88 * e), -S * 0.16 * e)
    for i in range(n - 1, -1, -1):
        u = i / (n - 1); bx = (1 - u) ** 2 * 0 + 2 * u * (1 - u) * wr[0] + u * u * tip[0]; by = 2 * u * (1 - u) * wr[1] + u * u * tip[1]; ang = math.radians(112 - (112 - 14) * u ** 0.8 * e - 30 * (1 - e)); L = S * (0.26 + 0.34 * math.sin(math.pi * u ** 0.7) + 0.16 * u) * (0.35 + 0.65 * e)
        c.save(); c.translate(bx, by); c.rotate(math.atan2(math.sin(ang), side * math.cos(ang)) + 0.05 * math.sin(t * 9 + i)); _petal(c, L, L * 0.17)
        if glow or qi: g = cairo.LinearGradient(0, 0, L, 0); g.add_color_stop_rgba(0, *cb, 0.15 if glow and not qi else 0.5); g.add_color_stop_rgba(1, *cb, 0.9 if not qi else 0.75); c.set_source(g); c.fill() if qi else (c.set_line_width(max(2, S * 0.012)), c.stroke())
        else: g = cairo.LinearGradient(0, 0, L, 0); g.add_color_stop_rgb(0, *ca); g.add_color_stop_rgb(0.7, *[x * 0.6 + y * 0.4 for x, y in zip(ca, cb)]); g.add_color_stop_rgb(1, *cb); c.set_source(g); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(max(1.5, S * 0.007)); c.stroke()
        c.restore()
    if not glow and not qi: c.new_path(); c.move_to(0, 0); c.curve_to(wr[0] * 0.5, wr[1] * 1.1, wr[0], wr[1], tip[0], tip[1]); c.set_source_rgb(*INK); c.set_line_width(S * 0.034); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke_preserve(); c.set_source_rgb(*[x * 1.6 for x in ca]); c.set_line_width(S * 0.020); c.stroke()
    c.restore()
def feathers(c, pos, t, t0, col, n=22, r=500, life=0.9, seed=5):
    """展翼那一下抖出来的一圈羽毛。"""
    dt = t - t0
    if not 0 <= dt < life: return
    k = dt / life
    for i in range(n):
        th = rnd(i, seed) * 6.2832; d = r * (0.2 + rnd(i, seed + 1)) * (1 - (1 - k) ** 2); c.save(); c.translate(pos[0] + math.cos(th) * d, pos[1] + math.sin(th) * d * 0.8 + 200 * k * k); c.rotate(th + dt * 5 * (rnd(i, seed + 2) - 0.5)); _petal(c, 46, 9); c.set_source_rgba(*col, 0.85 * (1 - k)); c.fill(); c.restore()
def _poly(c, pts, fill, lw, ink=INK):
    c.new_path(); c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]; c.close_path(); c.set_source_rgb(*fill); c.fill_preserve(); c.set_source_rgb(*ink); c.set_line_width(lw); c.stroke()
ARMS = {'cup': ((0.19, -0.60), (0.055, -0.555)), 'open': ((0.26, -0.70), (0.40, -0.80)), 'down': ((0.165, -0.60), (0.17, -0.45)), 'push': ((0.17, -0.66), (0.075, -0.63)), 'up': ((0.20, -0.86), (0.10, -1.02))}
def front(c, cx, fy, H, t, arms='cup', eyes=((0.2, 1.0, 0.8), (0.2, 1.0, 0.8)), ruler=True, hand=1.0, sway=1.0, eye=1.0):
    """正面的萧炎（黑袍红边、背玄重尺）。fy=脚底。返回几个挂特效用的点：eyes / hands / chest / back。"""
    u = H; lw = 0.011 * u; ROBE = (0.09, 0.09, 0.13); RED = (0.74, 0.13, 0.15); SKIN = (1.0, 0.87, 0.76); HAIR = (0.07, 0.07, 0.11); sw = math.sin(t * 3.1) * 0.014 * u * sway; c.save(); c.translate(cx, fy); c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND)
    if ruler:
        c.save(); c.translate(0.01 * u, -0.60 * u); c.rotate(math.radians(-60)); c.rectangle(-0.40 * u, -0.055 * u, 0.86 * u, 0.11 * u); c.set_source_rgb(0.06, 0.06, 0.09); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(lw); c.stroke(); c.rectangle(0.46 * u, -0.02 * u, 0.16 * u, 0.04 * u); c.set_source_rgb(0.2, 0.18, 0.2); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke()
        for i in range(5): c.move_to((-0.3 + i * 0.15) * u, -0.03 * u); c.line_to((-0.26 + i * 0.15) * u, 0.03 * u)
        c.set_source_rgb(0.3, 0.3, 0.38); c.set_line_width(lw * 0.8); c.stroke(); c.restore()
    for s in (-1, 1):
        _poly(c, [(s * 0.02 * u, -0.40 * u), (s * 0.105 * u, -0.40 * u), (s * 0.088 * u + sw * 0.5, -0.04 * u), (s * 0.03 * u + sw * 0.5, -0.04 * u)], (0.08, 0.08, 0.12), lw); _poly(c, [(s * 0.022 * u + sw * 0.5, -0.06 * u), (s * 0.098 * u + sw * 0.5, -0.06 * u), (s * 0.112 * u + sw * 0.5, 0), (s * 0.016 * u + sw * 0.5, 0)], (0.15, 0.13, 0.15), lw)
    _poly(c, [(-0.125 * u, -0.775 * u), (0.125 * u, -0.775 * u), (0.088 * u, -0.50 * u), (0.185 * u + sw, -0.25 * u), (0.06 * u + sw * 0.6, -0.275 * u), (-0.05 * u + sw * 0.6, -0.245 * u), (-0.175 * u + sw, -0.27 * u), (-0.088 * u, -0.50 * u)], ROBE, lw)
    c.new_path(); c.move_to(-0.05 * u, -0.775 * u); c.line_to(0, -0.675 * u); c.line_to(0.05 * u, -0.775 * u); c.move_to(0, -0.675 * u); c.line_to(0.012 * u + sw * 0.5, -0.27 * u); c.set_source_rgb(*RED); c.set_line_width(lw * 1.7); c.stroke(); c.rectangle(-0.09 * u, -0.525 * u, 0.18 * u, 0.036 * u); c.set_source_rgb(*RED); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(lw); c.stroke()
    (ex_, ey_), (hx_, hy_) = ARMS[arms]; hands = []
    for s in (-1, 1):
        sh = (s * 0.122 * u, -0.750 * u); el = (s * ex_ * u, ey_ * u); hd = (s * hx_ * u, hy_ * u)
        for wd, col in ((0.064 * u + 2 * lw, INK), (0.064 * u, ROBE)): c.new_path(); c.move_to(*sh); c.line_to(*el); c.line_to(*hd); c.set_source_rgb(*col); c.set_line_width(wd); c.stroke()
        c.new_path(); c.arc(hd[0], hd[1], 0.03 * u * hand, 0, 7); c.set_source_rgb(*SKIN); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(lw); c.stroke(); hands.append((cx + hd[0], fy + hd[1]))
    hy = -0.868 * u; r = 0.084 * u; c.rectangle(-0.026 * u, -0.81 * u, 0.052 * u, 0.05 * u); c.set_source_rgb(*[v * 0.86 for v in SKIN]); c.fill()
    c.save(); c.translate(0, hy); c.scale(r * 0.93, r * 1.06); c.new_path(); c.arc(0, 0, 1, 0, 7); c.restore(); c.set_source_rgb(*SKIN); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(lw); c.stroke(); eyes_p = []
    for s, col in zip((-1, 1), eyes):
        x_, y_ = s * 0.037 * u, hy + 0.014 * u; c.save(); c.translate(x_, y_); c.scale(0.022 * u, 0.0145 * u * max(0.12, eye)); c.new_path(); c.arc(0, 0, 1, 0, 7); c.restore(); c.set_source_rgb(1, 1, 1); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(lw * 0.7); c.stroke()
        if eye > 0.3: c.new_path(); c.arc(x_, y_, 0.0115 * u, 0, 7); c.set_source_rgb(*col); c.fill(); c.new_path(); c.arc(x_, y_, 0.005 * u, 0, 7); c.set_source_rgb(0.02, 0.05, 0.08); c.fill()
        c.new_path(); c.move_to(x_ + s * 0.026 * u, y_ - 0.034 * u); c.line_to(x_ - s * 0.022 * u, y_ - 0.019 * u); c.set_source_rgb(*INK); c.set_line_width(lw * 1.5); c.stroke(); eyes_p.append((cx + x_, fy + y_))
    c.new_path(); c.move_to(-0.014 * u, hy + 0.056 * u); c.line_to(0.014 * u, hy + 0.056 * u); c.set_source_rgb(*INK); c.set_line_width(lw * 0.9); c.stroke()
    hp = [(-1.05, 0.01), (-1.32, -0.04), (-1.0, -0.06), (-1.28, -0.125), (-0.72, -0.115), (-0.78, -0.195), (-0.2, -0.15), (0.02, -0.225), (0.26, -0.15), (0.82, -0.19), (0.72, -0.115), (1.28, -0.12), (1.0, -0.06), (1.32, -0.035), (1.05, 0.01), (0.84, -0.045), (0.58, 0.0), (0.36, -0.05), (0.1, 0.004), (-0.14, -0.05), (-0.4, 0.0), (-0.64, -0.05), (-0.86, -0.008)]
    _poly(c, [(a * r + (sw * 0.3 if b < -0.1 else 0), hy + b * u) for a, b in hp], HAIR, lw); c.new_path(); c.move_to(-0.3 * r, hy - 0.13 * u); c.line_to(0.05 * r, hy - 0.19 * u); c.set_source_rgba(0.5, 0.52, 0.66, 0.8); c.set_line_width(lw * 1.2); c.stroke(); c.restore()
    return dict(eyes=eyes_p, hands=hands, chest=(cx, fy - 0.62 * u), back=(cx, fy - 0.70 * u), head=(cx, fy + hy))
def back(c, cx, by, S, K, t, twin=False, dark=0.8, turn=0.0):
    """敌人的背影（前景，过肩镜头用）：只到肩。S=肩宽；K=fighter.LOOKS 里的一项；dark=背光压暗。"""
    dk = lambda col: tuple(v * dark for v in col[:3]); hair, robe = dk(K['hair']), dk(K['robe']); lw = S * 0.012; hx = cx + turn * S * 0.06; hyy = by - S * 0.66; hr = S * 0.215; sw = math.sin(t * 2.3) * S * 0.015; c.set_line_join(cairo.LINE_JOIN_ROUND)
    if twin:
        for s in (-1, 1): _poly(c, [(hx + s * hr * 0.7, hyy - hr * 0.5), (hx + s * hr * 1.5, hyy - hr * 0.1), (hx + s * (S * 0.62) + sw * 3, by - S * 0.1), (hx + s * (S * 0.74) + sw * 5, by + S * 0.3), (hx + s * (S * 0.52) + sw * 4, by + S * 0.3), (hx + s * (S * 0.40) + sw * 2, by - S * 0.2), (hx + s * hr * 0.95, hyy + hr * 0.3)], hair, lw)
    c.new_path(); c.move_to(cx - S * 0.56, by + S * 0.3); c.line_to(cx - S * 0.52, by - S * 0.22); c.curve_to(cx - S * 0.44, by - S * 0.36, cx - S * 0.2, by - S * 0.40, cx - S * 0.10, by - S * 0.46); c.line_to(cx + S * 0.10, by - S * 0.46); c.curve_to(cx + S * 0.2, by - S * 0.40, cx + S * 0.44, by - S * 0.36, cx + S * 0.52, by - S * 0.22); c.line_to(cx + S * 0.56, by + S * 0.3); c.close_path(); c.set_source_rgb(*robe); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(lw); c.stroke()
    if K.get('pads'):
        for s in (-1, 1): c.save(); c.translate(cx + s * S * 0.43, by - S * 0.27); c.rotate(s * 0.35); c.scale(S * 0.17, S * 0.085); c.new_path(); c.arc(0, 0, 1, 0, 7); c.restore(); c.set_source_rgb(*dk(K['pads'] if isinstance(K['pads'], tuple) and len(K['pads']) == 3 and not isinstance(K['pads'][0], tuple) else (0.95, 0.78, 0.35))); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(lw); c.stroke()
    if not twin: _poly(c, [(hx - hr * 0.98, hyy), (hx - hr * 1.12 + sw, by - S * 0.05), (hx - hr * 0.5 + sw * 1.5, by + S * 0.3), (hx + hr * 0.5 + sw * 1.5, by + S * 0.3), (hx + hr * 1.12 + sw, by - S * 0.05), (hx + hr * 0.98, hyy)], hair, lw)
    c.new_path(); c.arc(hx, hyy, hr, 0, 7); c.set_source_rgb(*hair); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(lw); c.stroke()
    hi = K.get('hair_hi', (0.6, 0.6, 0.7)); c.new_path(); c.arc(hx, hyy, hr * 0.8, math.radians(200), math.radians(300)); c.set_source_rgba(*hi[:3], 0.55); c.set_line_width(lw * 1.6); c.stroke()
