"""fx — 斗破系列自己的招牌手法：漫画分格、火烧转场、墨稿定格、出场名牌、石碑等级牌、莲花绽放、翅膀、正面的萧炎、敌人的背影。
画在 cairo 上的（lotus / petals / wing / front / back）用场景坐标；处理整帧的（panels / burn / ink / tag / badge）吃 float32 的帧。"""
import os, math, functools, numpy as np, cv2, cairo
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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
def burn(a, b, k, col, R, seed=1, mode='lr', t=0.0):
    """火烧转场：a 被一条火线烧穿，露出 b。k: 0→1；col: 这一段的火色。火线会舔（跟着 t 抖），前面是烧焦的黑边，后面飘火星。"""
    n = _noise(R.w, R.h, seed, mode); lick = _noise(R.w, R.h, seed + 7, 'up'); ph = (t * 2.3) % 1.0; n = n + 0.05 * np.sin((lick + ph) * 6.2832 * 3)
    d = k * 1.34 - 0.17 - n; m = np.clip(d / 0.02, 0, 1); char = np.clip(1 + d / 0.13, 0, 1) * (1 - m); edge = np.exp(-(d / 0.05) ** 2); core = np.exp(-(d / 0.014) ** 2); halo = np.exp(-(np.minimum(d, 0) / 0.10) ** 2) * (d < 0)
    em = _noise(R.w, R.h, seed + 13 + int(t * 14) % 5, 'lr'); embers = ((em * 997 % 1) > 0.992) * np.clip(1 - d / 0.25, 0, 1) * (d > 0.01)
    out = a * (1 - m) * (1 - 0.9 * char) + b * m; c3 = np.float32(col); return np.clip(out + edge * c3 * 1.2 + halo * c3 * 0.35 + core * np.float32((1.0, 0.95, 0.8)) + embers * (c3 * 0.6 + 0.4) * 1.5, 0, 1)
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
def badge(fr, R, text, flip=1.0, a=1.0, z=1.5):
    """左上角的小石碑：他现在的等级。flip: 0→1 换字时翻出来。"""
    if a <= 0: return fr
    if (text, R.w) not in _bc:
        f = ImageFont.truetype(FONT, int(40 * z * R.k)); w = int(f.getlength(text) + 84 * z * R.k); h = int(78 * z * R.k); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); q = 14 * z * R.k
        d.polygon([(q, 0), (w - q, 0), (w, q), (w, h), (0, h), (0, q)], fill=(10, 10, 16, 235), outline=(200, 160, 70, 255), width=max(1, int(3 * R.k))); d.text((w / 2, h / 2), text, font=f, fill=(255, 208, 100, 255), anchor='mm'); b = np.asarray(im, np.float32) / 255; _bc[(text, R.w)] = (b[..., :3] * b[..., 3:], b[..., 3:])
    rgb, al = _bc[(text, R.w)]; k = _cl(flip); h0, w = al.shape[:2]; h = max(1, int(h0 * (1 - (1 - k) ** 2)))
    if h != h0: rgb = cv2.resize(rgb, (w, h)); al = cv2.resize(al, (w, h))[..., None]
    x0 = int(56 * R.k); y0 = int(48 * R.k + (h0 - h) / 2); fr = fr.copy(); fl = max(0.0, 1 - flip / 3.0) if flip >= 1 else 1.0; fr[y0:y0 + h, x0:x0 + w] = fr[y0:y0 + h, x0:x0 + w] * (1 - al * a) + (rgb + fl * 1.2 * al * np.float32((1, 0.8, 0.4))) * a; return fr

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

# ---------------- v3：漫画页（大小不等的格子、贯通的斜缝、白纸黑框）、高燃文字、特写
PAGE = [(40, 40), (1880, 40), (1880, 1040), (40, 1040)]
def _clip(poly, a, b, c):
    out = []; n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]; dp = a * p[0] + b * p[1] + c; dq = a * q[0] + b * q[1] + c
        if dp >= 0: out.append(p)
        if (dp >= 0) != (dq >= 0): u = dp / (dp - dq); out.append((p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u))
    return out
def split(poly, p0, p1, gut=24):
    """用直线 p0→p1 把一个格子切成两格，各自从切线退半条缝，所以缝一定是贯通、等宽的。线从上往下画：返回 (左格, 右格)；线从左往右画：返回 (下格, 上格)。"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy); a, b = -dy / L, dx / L; c = -(a * p0[0] + b * p0[1]); return _clip(poly, a, b, c - gut / 2), _clip(poly, -a, -b, -c - gut / 2)
def page(R, items, t, paper=(0.96, 0.95, 0.92), line=(0.03, 0.03, 0.05)):
    """一页漫画。items = [dict(poly=格子, fr=这一格的画面(整帧), t0=进场秒, focus=(x, y, 放大), slide=(dx, dy) 从哪边滑进来)]。"""
    out = np.empty((R.h, R.w, 3), np.float32); out[:] = paper
    for it in items:
        t0 = it.get('t0', 0.0)
        if t < t0: continue
        k = _cl((t - t0) / 0.16); e = 1 - (1 - k) ** 3; sx, sy = it.get('slide', (0, -90)); P_ = (np.float32(it['poly']) + np.float32((sx, sy)) * (1 - e)) * R.k; x0, y0 = P_.min(0); x1, y1 = P_.max(0); fx_, fy_, z = it.get('focus', (960, 540, 1.0)); sc = max((x1 - x0) / R.w, (y1 - y0) / R.h) * z * (1 + 0.10 * (1 - e))
        M = np.float32([[sc, 0, (x0 + x1) / 2 - fx_ * R.k * sc], [0, sc, (y0 + y1) / 2 - fy_ * R.k * sc]]); img = cv2.warpAffine(it['fr'], M, (R.w, R.h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE); Q = P_.astype(np.int32); m = np.zeros((R.h, R.w), np.float32); cv2.fillPoly(m, [Q], 1.0, cv2.LINE_AA); m = m[..., None] * min(1.0, k * 2.5)
        out = out * (1 - m) + (img + (1 - img) * 0.8 * (1 - k)) * m; cv2.polylines(out, [Q], True, line, max(2, int(9 * R.k)), cv2.LINE_AA)
    return out
_gc = {}
def _glyph(ch, px, col, glow, edge=(8, 10, 16)):
    key = (ch, px, col, glow)
    if key not in _gc:
        f = ImageFont.truetype(BRUSH, px); pad = int(px * 0.5); W = px + 2 * pad; im = Image.new('RGBA', (W, W), (0, 0, 0, 0)); g = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((W / 2, W / 2), ch, font=f, fill=glow + (255,), anchor='mm', stroke_width=int(px * 0.10), stroke_fill=glow + (255,)); ImageDraw.Draw(im).text((W / 2, W / 2), ch, font=f, fill=col + (255,), anchor='mm', stroke_width=max(2, int(px * 0.055)), stroke_fill=edge + (255,))
        g = g.filter(ImageFilter.GaussianBlur(px * 0.12)); a = np.asarray(g, np.float32) / 255; b = np.asarray(im, np.float32) / 255; r = np.random.default_rng(abs(hash(ch)) % 9973); yy = np.mgrid[0:W, 0:W][0].astype(np.float32) / W
        nz = cv2.resize(r.random((7, 7)).astype(np.float32), (W, W), interpolation=cv2.INTER_CUBIC); _gc[key] = (b[..., :3] * b[..., 3:], b[..., 3].copy(), a[..., :3] * a[..., 3:] * 0.9, 0.62 * (1 - yy) + 0.38 * nz)
    return _gc[key]
def vcol(x, y0, px, n, gap=1.0): return [(x, y0 + i * px * gap) for i in range(n)]
def hrow(x0, y, px, n, gap=0.95, rot=0.0): r = math.radians(rot); return [(x0 + i * px * gap * math.cos(r), y - i * px * gap * math.sin(r)) for i in range(n)]
def arc(center, rad, a0, a1, n): return [(center[0] + rad * math.cos(math.radians(a0 + (a1 - a0) * i / max(1, n - 1))), center[1] - rad * math.sin(math.radians(a0 + (a1 - a0) * i / max(1, n - 1)))) for i in range(n)]
def ktext(fr, R, t, text, t0, t1, pos, px=200, style='slam', col=(255, 255, 255), glow=(60, 255, 210), step=0.0, rot=0.0, origin=None, seed=0):
    """高燃文字，一个字一个字出场。pos = 每个字的中心（1920×1080）；t0 = 第一个字的秒，之后每字晚 step 秒；t1 = 消失。
    style：slam 砸下来（带裂纹）/ drop 从上面掉下来砸地 / burst 从 origin 炸出来 / burn 从下往上烧出来 / drag 从两边被锁链拖进来。"""
    if t < t0 or t >= t1: return fr
    out = fr; fade = min(1.0, (t1 - t) / 0.12); P = max(8, int(px * R.k)); g3 = np.float32(glow) / 255
    for i, ch in enumerate(text):
        ti = t0 + i * step
        if ch == ' ' or t < ti: continue
        rgb, al, gl, nz = _glyph(ch, P, col, glow); S_ = al.shape[0]; dt = t - ti; x, y = pos[i]; sc = 1.0; ro = rot; a = fade; extra = None
        if style == 'slam':
            u = min(1.0, dt / 0.11); sc = 1 + 1.9 * (1 - u) ** 3; a *= min(1.0, u * 3); jx, jy = A.shake(t, [(ti + 0.11, 16, 0.10)]); x += jx; y += jy; ro += (rnd(i, seed) - 0.5) * 9
            if 0.11 <= dt < 0.75:
                ov = np.zeros((R.h, R.w), np.float32)
                for j in range(9):
                    th = j / 9 * 6.2832 + rnd(i, j + seed); px_, py_ = x * R.k, y * R.k; rr = P * 0.45
                    for q in range(4): nx, ny = px_ + math.cos(th + (rnd(j, q + i) - 0.5)) * rr, py_ + math.sin(th + (rnd(j, q + i) - 0.5)) * rr * 0.8; cv2.line(ov, (int(px_), int(py_)), (int(nx), int(ny)), 1.0, max(1, int((5 - q) * R.k)), cv2.LINE_AA); px_, py_, rr = nx, ny, rr * 0.75
                extra = ov[..., None] * g3 * 0.9 * (1 - (dt - 0.11) / 0.64)
        elif style == 'drop':
            u = min(1.0, dt / 0.15); y -= 760 * (1 - u ** 2.4); land = dt - 0.15; sc = 1 + (0.16 * math.exp(-land / 0.05) if land >= 0 else 0.0); jx, jy = A.shake(t, [(ti + 0.15, 22, 0.14)]); x += jx; y += jy
        elif style == 'burst':
            u = min(1.0, dt / 0.12); e = 1 - (1 - u) ** 3; ox, oy = origin or (x, y); x = ox + (x - ox) * e; y = oy + (y - oy) * e; sc = 0.3 + 0.7 * e + (0.3 * math.exp(-(dt - 0.12) / 0.06) if u >= 1 else 0.0); a *= min(1.0, u * 4)
            if dt < 0.3 and origin: ov = np.zeros((R.h, R.w), np.float32); cv2.line(ov, (int(ox * R.k), int(oy * R.k)), (int(x * R.k), int(y * R.k)), 1.0, max(2, int(P * 0.16)), cv2.LINE_AA); extra = cv2.GaussianBlur(ov, (0, 0), 3 * R.k)[..., None] * g3 * (1 - dt / 0.3)
        elif style == 'burn':
            k = min(1.0, dt / 0.42); d = k * 1.3 - nz; m = np.clip(d / 0.07, 0, 1); ed = np.exp(-(d / 0.07) ** 2) * (k < 1); gl = gl * m[..., None] + (ed * np.maximum(al, gl.max(2)))[..., None] * (g3 * 0.7 + 0.5); rgb = rgb * m[..., None]; al = al * m; y -= 10 * (1 - k)
        elif style == 'drag':
            u = min(1.0, dt / 0.24); e = 1 - (1 - u) ** 3; sd = -1 if i % 2 == 0 else 1; x += sd * 1000 * (1 - e); a *= min(1.0, u * 3); jx, jy = A.shake(t, [(ti + 0.24, 18, 0.12)]); x += jx; y += jy
            if dt < 1.2:
                ov = np.zeros((R.h, R.w), np.float32); xe = 0 if sd < 0 else R.w
                for q in range(0, 60): xa = x * R.k + (xe - x * R.k) * q / 60; xb = x * R.k + (xe - x * R.k) * (q + 0.6) / 60; cv2.line(ov, (int(xa), int(y * R.k + 6 * math.sin(q))), (int(xb), int(y * R.k + 6 * math.sin(q + 1))), 1.0, max(2, int(9 * R.k)), cv2.LINE_AA)
                extra = ov[..., None] * g3 * 0.8 * min(1.0, (1.2 - dt) / 0.5)
        M = cv2.getRotationMatrix2D((S_ / 2, S_ / 2), ro, sc); M[0, 2] += x * R.k - S_ / 2; M[1, 2] += y * R.k - S_ / 2; w = lambda q: cv2.warpAffine(q, M, (R.w, R.h), flags=cv2.INTER_LINEAR); A_ = w(al)[..., None] * a
        if extra is not None: out = out + extra * a
        out = out * (1 - A_) + w(rgb) * a + w(gl) * a * (1 - A_)
    return out
SKIN = (1.0, 0.87, 0.76); ROBE = (0.09, 0.09, 0.13); RED = (0.74, 0.13, 0.15)
def _cap(c, p, q, w, fill, lw=7, ink=INK):
    """一节手指/一段胳膊：圆头的粗线，带墨线。"""
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.new_path(); c.move_to(*p); c.line_to(*q); c.set_source_rgb(*ink); c.set_line_width(w + 2 * lw); c.stroke(); c.new_path(); c.move_to(*p); c.line_to(*q); c.set_source_rgb(*fill); c.set_line_width(w); c.stroke()
def _lines(c, n, r0, r1, col, a, t, seed=0):
    for i in range(n): th = rnd(i, seed) * 6.2832; rr = r0 * (0.8 + 0.5 * rnd(i, seed + 1 + int(t * 12))); c.move_to(math.cos(th) * rr, math.sin(th) * rr * 0.6); c.line_to(math.cos(th) * r1, math.sin(th) * r1 * 0.6)
    c.set_source_rgba(*col, a); c.set_line_width(5); c.stroke()
def pinch(c, t, t0):
    """特写：两指夹住剑刃。坐标原点 = 夹住的那一点。她握剑的手在左，他的手从右上伸进来；食指压在剑身前面，中指垫在后面。"""
    dt = t - t0; tr = math.sin(t * 80) * 0.007 * math.exp(-max(0.0, dt) / 0.45) if dt >= 0 else 0.0; c.set_line_join(cairo.LINE_JOIN_ROUND); _lines(c, 46, 520, 1300, (1, 1, 1), 0.35, t, 3)
    f = (-0.82, 0.57); p = (0.57, 0.82); O = (-f[0] * 300, -f[1] * 300); pt = lambda a, b, o=O: (o[0] + f[0] * a + p[0] * b, o[1] + f[1] * a + p[1] * b)
    c.new_path(); c.move_to(*pt(-250, -175)); c.line_to(*pt(-900, -300)); c.line_to(*pt(-900, 330)); c.line_to(*pt(-250, 215)); c.close_path(); c.set_source_rgb(*ROBE); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(8); c.stroke()      # 袖子
    c.new_path(); c.move_to(*pt(-250, -175)); c.line_to(*pt(-310, -187)); c.line_to(*pt(-310, 226)); c.line_to(*pt(-250, 215)); c.close_path(); c.set_source_rgb(*RED); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke()
    _cap(c, pt(0, 42), pt(170, 50), 68, [v * 0.92 for v in SKIN]); _cap(c, pt(170, 50), pt(352, 34), 62, [v * 0.92 for v in SKIN])                                    # 中指（在剑身后面）
    c.save(); c.rotate(math.radians(-14) + tr)                                              # 剑
    g = cairo.LinearGradient(0, -32, 0, 32); g.add_color_stop_rgb(0, 0.97, 0.99, 1); g.add_color_stop_rgb(0.5, 0.66, 0.78, 0.92); g.add_color_stop_rgb(0.52, 0.86, 0.93, 1); g.add_color_stop_rgb(1, 0.78, 0.88, 0.98)
    c.new_path(); c.move_to(-1500, -36); c.line_to(420, -28); c.line_to(600, 0); c.line_to(420, 28); c.line_to(-1500, 36); c.close_path(); c.set_source(g); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(7); c.stroke(); c.new_path(); c.move_to(-1500, 0); c.line_to(600, 0); c.set_source_rgba(0.25, 0.35, 0.5, 0.7); c.set_line_width(3); c.stroke()
    gx = -1500 + (t * 1400) % 2400; c.new_path(); c.move_to(gx, -30); c.line_to(gx + 90, -30); c.line_to(gx + 50, 30); c.line_to(gx - 40, 30); c.close_path(); c.set_source_rgba(1, 1, 1, 0.7); c.fill()
    for sgn in (-1, 1):                                                                     # 翼形护手、红宝石、她的拳
        c.new_path(); c.move_to(-700, sgn * 20); c.curve_to(-640, sgn * 120, -700, sgn * 230, -800, sgn * 270); c.curve_to(-770, sgn * 190, -790, sgn * 120, -760, sgn * 20); c.close_path(); c.set_source_rgb(0.97, 0.97, 1); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(7); c.stroke()
    c.new_path(); c.arc(-730, 0, 34, 0, 7); c.set_source_rgb(0.86, 0.14, 0.2); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke(); c.rectangle(-1500, -30, 730, 60); c.set_source_rgb(0.5, 0.12, 0.16); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke()
    for i in range(4): _cap(c, (-830 - i * 62, -64), (-830 - i * 62, 58), 54, SKIN)
    _cap(c, (-800, 70), (-960, 84), 50, SKIN); c.new_path(); c.move_to(-1085, -95); c.line_to(-1700, -160); c.line_to(-1700, 330); c.line_to(-1085, 105); c.close_path(); c.set_source_rgb(0.96, 0.96, 1.0); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke()
    c.new_path(); c.move_to(-1085, -95); c.line_to(-1130, -100); c.line_to(-1130, 122); c.line_to(-1085, 105); c.close_path(); c.set_source_rgb(0.55, 0.36, 0.78); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke(); c.restore()
    c.new_path(); c.move_to(*pt(8, -88)); c.line_to(*pt(8, 218)); c.line_to(*pt(-250, 215)); c.line_to(*pt(-250, -175)); c.close_path(); c.set_source_rgb(*SKIN); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(8); c.stroke()                 # 手背
    for b_, r_ in ((116, 50), (176, 44)): c.new_path(); c.arc(*pt(26, b_), r_, 0, 7); c.set_source_rgb(*SKIN); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(7); c.stroke()                                                       # 蜷着的无名指、小指
    _cap(c, pt(-170, 226), pt(-30, 248), 58, SKIN); _cap(c, pt(-30, 248), pt(70, 200), 52, SKIN)                                                                           # 拇指
    _cap(c, pt(0, -42), pt(172, -52), 70, SKIN); _cap(c, pt(172, -52), pt(346, -30), 64, SKIN)                                                                               # 食指（压在剑身前面）
    for a_, b_ in ((2, -42), (2, 42), (10, 116), (14, 176)): c.new_path(); c.arc(*pt(a_ - 12, b_), 26, math.radians(100), math.radians(250)); c.set_source_rgba(*INK, 0.7); c.set_line_width(5); c.stroke()
    c.new_path(); c.arc(*pt(172, -52), 20, math.radians(120), math.radians(230)); c.stroke(); e_ = pt(346, -30); c.new_path(); c.arc(e_[0] - 6, e_[1] + 4, 20, 0, 7); c.set_source_rgba(1, 0.96, 0.92, 0.8); c.fill()
    if dt >= 0: A.sparks(c, t, t0, (0, 0), 60, 200, 150, 300, 2000, 0.55, (1, 0.95, 0.8), seed=3, w=5); A.ring(c, t, t0, (0, 0), 800, 0.4, (1, 1, 1), sq=1.0, w=20); A.burst(c, (0, 0), 150 * math.exp(-dt / 0.08) + 26, (1, 1, 1), min(1.0, 0.35 + math.exp(-dt / 0.1)))
def cu_grip(c, t):
    """特写：握着玄重尺尺柄的手（勒白的指节、缠布、汗）。"""
    g = cairo.LinearGradient(0, -540, 0, 540); g.add_color_stop_rgb(0, 0.30, 0.46, 0.36); g.add_color_stop_rgb(1, 0.10, 0.20, 0.16); c.set_source(g); c.paint(); _lines(c, 30, 420, 1300, (1, 1, 1), 0.25, t, 5); j = math.sin(t * 46) * 4; c.save(); c.translate(j, -j * 0.5); c.rotate(math.radians(-38)); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.rectangle(-1300, -95, 2600, 190); c.set_source_rgb(0.07, 0.07, 0.10); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(9); c.stroke()
    for i in range(14): c.new_path(); c.move_to(-900 + i * 130, -95); c.line_to(-840 + i * 130, 95); c.set_source_rgba(0.55, 0.5, 0.45, 0.8); c.set_line_width(12); c.stroke()
    _cap(c, (-210, 150), (40, 205), 120, SKIN, 9)
    for i in range(4): _cap(c, (-240 + i * 150, -150), (-225 + i * 150, 120), 128 - i * 8, SKIN, 9); c.new_path(); c.arc(-240 + i * 150, -150, 40, math.radians(200), math.radians(340)); c.set_source_rgba(1, 1, 1, 0.85); c.set_line_width(10); c.stroke()
    c.new_path(); c.move_to(-330, 60); c.line_to(-1300, 420); c.line_to(-1300, 900); c.line_to(420, 240); c.line_to(380, 120); c.close_path(); c.set_source_rgb(*ROBE); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(9); c.stroke(); c.restore()
    for i in range(5): k = (t * 0.9 + rnd(i, 2)) % 1; x = -300 + 160 * i; c.new_path(); c.arc(x, -60 + 520 * k * k, 13, 0, 7); c.set_source_rgba(0.8, 0.93, 1, 0.9 * (1 - k)); c.fill()
def cu_foot(c, t):
    """特写：一脚踩进地里，石板裂开。"""
    g = cairo.LinearGradient(0, -540, 0, 540); g.add_color_stop_rgb(0, 0.52, 0.66, 0.60); g.add_color_stop_rgb(0.5, 0.40, 0.52, 0.40); g.add_color_stop_rgb(0.5, 0.36, 0.33, 0.27); g.add_color_stop_rgb(1, 0.20, 0.18, 0.15); c.set_source(g); c.paint(); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(*INK)
    for i in range(13):
        th = math.radians(-8 + 196 * rnd(i, 1)); x, y = 30, 110; c.new_path(); c.move_to(x, y); L = 260 + 520 * rnd(i, 2)
        for q in range(5): x += math.cos(th + (rnd(i, q + 3) - 0.5) * 1.0) * L / 5; y += abs(math.sin(th + (rnd(i, q + 3) - 0.5) * 1.0)) * L / 5 * 0.45; c.line_to(x, y)
        c.set_line_width(13 - i % 5 * 2); c.stroke()
    c.new_path(); c.move_to(-170, -540); c.line_to(-230, -40); c.curve_to(-240, 60, -200, 120, -90, 120); c.line_to(360, 120); c.curve_to(420, 110, 400, 30, 300, 10); c.curve_to(200, -10, 150, -60, 140, -160); c.line_to(170, -540); c.close_path(); c.set_source_rgb(0.13, 0.12, 0.15); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(10); c.stroke()
    c.new_path(); c.move_to(-226, -80); c.line_to(144, -130); c.set_source_rgb(*RED); c.set_line_width(26); c.stroke()
    for i in range(12): k = (t * 1.6 + rnd(i, 7)) % 1; th = math.radians(200 + 140 * rnd(i, 8)); d = 120 + 520 * k; x, y = 60 + math.cos(th) * d, 110 + math.sin(th) * d * 0.7 + 300 * k * k; s_ = 40 * (1 - k) + 10; c.save(); c.translate(x, y); c.rotate(k * 5 + i); c.rectangle(-s_ / 2, -s_ / 2, s_, s_ * 0.8); c.set_source_rgb(0.5, 0.47, 0.42); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(5); c.stroke(); c.restore()
    for i in range(6): k = (t * 1.2 + rnd(i, 11)) % 1; c.new_path(); c.arc(60 + (rnd(i, 12) - 0.5) * 700 * (0.4 + k), 120 - 60 * k, 60 + 90 * k, 0, 7); c.set_source_rgba(0.88, 0.84, 0.78, 0.5 * (1 - k)); c.fill()
def cu_eye(c, t, col, op=1.0, dark=0.0):
    """特写：一只眼。op=睁开多少；dark=脸在阴影里。"""
    sk = [v * (1 - 0.45 * dark) for v in SKIN]; c.set_source_rgb(*sk); c.paint(); c.set_line_cap(cairo.LINE_CAP_ROUND); o = max(0.03, op)
    c.save(); c.translate(0, 40); c.scale(1, 0.60 * o); c.new_path(); c.arc(0, 0, 330, 0, 7); c.restore(); c.set_source_rgb(1, 1, 1); c.fill_preserve(); c.save(); c.clip(); c.new_path(); c.arc(20, 44, 170, 0, 7); c.set_source_rgb(*col); c.fill(); c.new_path(); c.arc(20, 44, 74, 0, 7); c.set_source_rgb(0.02, 0.05, 0.08); c.fill(); c.new_path(); c.arc(-40, -10, 34, 0, 7); c.set_source_rgb(1, 1, 1); c.fill(); c.restore()
    c.new_path(); c.move_to(-370, 50 - 40 * o); c.curve_to(-180, -190 * o + 10, 180, -200 * o + 10, 370, 30 - 60 * o); c.set_source_rgb(*INK); c.set_line_width(38); c.stroke(); c.new_path(); c.move_to(-320, 60 + 150 * o); c.curve_to(-120, 60 + 230 * o, 160, 60 + 220 * o, 330, 50 + 120 * o); c.set_line_width(12); c.stroke()
    c.new_path(); c.move_to(-470, -250 - 30 * o); c.line_to(400, -190 + 50 * (1 - o)); c.set_line_width(56); c.stroke()
    for i in range(9): x = -960 + i * 240; c.new_path(); c.move_to(x - 170, -545); c.line_to(x + 30 * math.sin(i * 2.1), -545 + 150 + 130 * rnd(i, 3)); c.line_to(x + 170, -545); c.close_path(); c.set_source_rgb(0.06, 0.07, 0.14); c.fill()
    if op > 0.5: A.burst(c, (20, 44), 300 + 30 * math.sin(t * 11), col, 0.35)
def cu_fist(c, t):
    """特写：攥紧的拳，指甲掐进掌心，一滴血往下掉。"""
    g = cairo.LinearGradient(0, -540, 0, 540); g.add_color_stop_rgb(0, 0.22, 0.10, 0.07); g.add_color_stop_rgb(1, 0.08, 0.04, 0.04); c.set_source(g); c.paint(); j = math.sin(t * 52) * 5; c.save(); c.translate(j, 0); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.new_path(); c.move_to(-200, -540); c.line_to(-250, -160); c.line_to(250, -160); c.line_to(210, -540); c.close_path(); c.set_source_rgb(*ROBE); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(10); c.stroke(); c.rectangle(-256, -200, 512, 46); c.set_source_rgb(*RED); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke()
    c.new_path(); c.move_to(-210, -156); c.line_to(-250, 60); c.curve_to(-250, 190, -150, 240, 0, 240); c.curve_to(170, 240, 250, 180, 240, 40); c.line_to(210, -156); c.close_path(); c.set_source_rgb(*SKIN); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(10); c.stroke()
    for i in range(4): _cap(c, (-180 + i * 118, 60), (-176 + i * 118, 200), 100, SKIN, 8); c.new_path(); c.arc(-180 + i * 118, 60, 34, math.radians(200), math.radians(340)); c.set_source_rgba(1, 1, 1, 0.8); c.set_line_width(9); c.stroke()
    _cap(c, (-260, -40), (-150, 110), 96, SKIN, 8); c.restore()
    for i in range(3): k = (t * 0.8 + i * 0.37) % 1; y = 250 + 300 * k * k; c.new_path(); c.arc(20 + i * 40 - 30, y, 16 - 4 * i, 0, 7); c.set_source_rgba(0.75, 0.06, 0.08, 1 - k * 0.6); c.fill()
def cape(c, cx, fy, H, t, wind=1.0):
    """正面人物身后被气浪掀起来的衣摆。"""
    u = H; pts = [(cx - 0.11 * u, fy - 0.76 * u), (cx + 0.11 * u, fy - 0.76 * u)]; n = 9
    for i in range(n + 1): k = i / n; x = cx + (0.42 - 0.84 * k) * u * (0.8 + 0.2 * wind); pts.append((x + 0.03 * u * math.sin(t * 5 + i * 1.3), fy - (0.16 + 0.10 * math.sin(i * 1.9 + t * 6) * wind + 0.12 * abs(0.5 - k)) * u))
    c.new_path(); c.move_to(*pts[0]); [c.line_to(*q) for q in pts[1:]]; c.close_path(); c.set_source_rgb(0.06, 0.06, 0.09); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(0.011 * u); c.stroke()
    c.new_path(); c.move_to(*pts[2]); [c.line_to(*q) for q in pts[3:]]; c.set_source_rgb(*RED); c.set_line_width(0.012 * u); c.stroke()
