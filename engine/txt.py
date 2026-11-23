"""txt — 文字图层（缓存）和贴字。坐标都是 1920×1080 空间，R = stage.Out。"""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from paper import FONT
TXT = {}
STY = dict(gold=((240, 196, 110), (255, 150, 40), 0.9), sub=((238, 238, 242), None, 0), tag=((200, 208, 220), None, 0), keep=((250, 236, 200), (255, 180, 80), 0.5), cost=((240, 96, 76), (255, 60, 30), 0.5), brand=((250, 244, 230), (255, 190, 90), 0.7))
PX = dict(sub=60, gold=78, tag=30, keep=66, cost=66, brand=120)
def tlayer(s, px, sty, R):
    key = (s, px, sty, R.w)
    if key not in TXT:
        K = R.k; col, glow, gk = STY[sty]; f = ImageFont.truetype(FONT, max(8, int(px * K))); sp = int(px * K * 0.08); pad = int(px * K * 0.8) + 4
        w = int(sum(f.getlength(ch) + sp for ch in s)) + pad * 2; h = int(px * K * 1.5) + pad * 2; m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m); x = pad
        for ch in s: d.text((x, pad), ch, font=f, fill=255); x += f.getlength(ch) + sp
        a = np.asarray(m, np.float32) / 255; sh = np.asarray(m.filter(ImageFilter.GaussianBlur(max(1.5, px * K * 0.07))), np.float32) / 255; sh = np.clip(np.roll(sh, int(2 * K + 1), 0) * 1.6, 0, 1) * 0.85
        rgb = a[..., None] * (np.float32(col) / 255); al = np.maximum(a, sh)[..., None]; add = None
        if glow: g = np.asarray(m.filter(ImageFilter.GaussianBlur(px * K * 0.22)), np.float32) / 255; add = g[..., None] * (np.float32(glow) / 255) * gk * 0.5
        TXT[key] = (rgb, al, add)
    return TXT[key]
def put(fr, L, x, y, R, a=1.0, sc=1.0, anchor='m'):
    rgb, al, add = L; K = R.k
    if sc != 1.0:
        sz = (max(1, int(rgb.shape[1] * sc)), max(1, int(rgb.shape[0] * sc))); rgb = cv2.resize(rgb, sz); al = cv2.resize(al, sz)[..., None]; add = cv2.resize(add, sz) if add is not None else None
    h, w = rgb.shape[:2]; x0 = int(x * K - (w / 2 if anchor == 'm' else (h * 0.27 if anchor == 'l' else w - h * 0.27))); y0 = int(y * K - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(R.w, x0 + w), min(R.h, y0 + h)
    if xa >= xb or ya >= yb: return
    sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0)); reg = fr[ya:yb, xa:xb]; reg *= (1 - al[sl] * a); reg += rgb[sl] * a
    if add is not None: reg += add[sl] * a
class Titles:
    """ev: (t0, t1, sty, s, x, y, px, anchor)，时间单位秒。"""
    def __init__(s): s.ev = []
    def add(s, t0, t1, sty, text, x=960, y=None, px=None, anchor='m'): s.ev.append((t0, t1 - 0.06, sty, text, x, y if y is not None else (965 if sty == 'sub' else 300), px or PX[sty], anchor))
    def draw(s, fr, t, R):
        for (t0, t1, sty, text, x, y, px, an) in s.ev:
            if t0 <= t < t1:
                u = t - t0; a = min(1, u / 0.12) * min(1, (t1 - t) / 0.18); sc = 1 + 0.22 * max(0, 1 - u / 0.14) ** 2 if sty != 'sub' and sty != 'tag' else 1.0; put(fr, tlayer(text, px, sty, R), x, y, R, a, sc, an)
