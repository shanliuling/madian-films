"""mapwar.util — 通用小工具：缓动、噪声、字体、文字层。画布固定 1920x1080 / 30fps。"""
import os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

SW, SH, FPS = 1920, 1080, 30
TAU = math.tau
rng = np.random.default_rng(11)


def cl(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def ease(x): x = cl(x); return x * x * (3 - 2 * x)
def eout(x, p=2.5): return 1 - (1 - cl(x)) ** p
def sm(a, b, x): x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def hsh(i, j=0): return (math.sin(i * 127.1 + j * 311.7) * 43758.5453) % 1.0
def kf(lst, t, j=1): return float(np.interp(t, [k[0] for k in lst], [k[j] for k in lst]))


def fbm(h, w, base, octaves=4, seed=0):
    r = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for o in range(octaves):
        s = max(2, base / 2 ** o)
        g = r.random((int(h / s) + 3, int(w / s) + 3)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC); tot += amp; amp *= 0.5
    return out / tot


def surf_rgba(s):
    """cairo ARGB32 surface -> (rgb float HxWx3 预乘, alpha HxWx1)."""
    a = np.ndarray((s.get_height(), s.get_width(), 4), np.uint8, s.get_data()).astype(np.float32) / 255
    return a[..., [2, 1, 0]], a[..., 3:4]


def to_img(frame): return Image.fromarray((np.clip(frame, 0, 1) * 255).astype(np.uint8))


# ---- 字体：粗宋体。MAPWAR_FONT 可覆盖仓库通用的 MADIAN_FONT。
_FONT_CANDIDATES = [os.environ.get('MAPWAR_FONT', ''), os.environ.get('MADIAN_FONT', ''), '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', 'C:/Windows/Fonts/NotoSerifSC-Bold.otf', 'C:/Windows/Fonts/simsunb.ttf',
                    'C:/Windows/Fonts/STZHONGS.TTF', 'C:/Windows/Fonts/msyhbd.ttc', '/System/Library/Fonts/Supplemental/Songti.ttc', '/System/Library/Fonts/PingFang.ttc']
FONT = next((p for p in _FONT_CANDIDATES if p and os.path.exists(p)), None)
_f = {}


def font(px):
    px = int(px)
    if px not in _f:
        if FONT is None: raise RuntimeError('找不到中文字体：请设置 MADIAN_FONT 或 MAPWAR_FONT 指向一个粗宋体/黑体字体文件')
        try: _f[px] = ImageFont.truetype(FONT, px, index=2 if FONT.endswith('NotoSerifCJK-Bold.ttc') else 0)
        except Exception: _f[px] = ImageFont.truetype(FONT, px)
    return _f[px]


yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
VR = np.clip(((xx - SW / 2) / (SW / 2)) ** 2 * 0.55 + ((yy - SH / 2) / (SH / 2)) ** 2 * 0.6, 0, 1)[..., None]      # 暗角权重
HAZE = np.clip(1 - (np.linspace(0, 1, SH, dtype=np.float32)[:, None, None] - 0.10) / 0.33, 0, 1) ** 1.6                # 斜视时的远处雾


def grain(amount=0.035): return (rng.random((SH, SW, 1), dtype=np.float32) - 0.5) * amount


class Txt:
    """一层文字。dark=True 用于深色画面（浅字深描边），False 用于宣纸画面（深字浅描边）。
    place() 会避开已占用的区域（HUD、字卡、之前的标签），放不下就不放。"""

    def __init__(self, dark=False, reserved=((500, 20, 1560, 130), (40, 30, 480, 170), (1650, 220, 1900, 900), (300, 915, 1620, 1020))):
        self.ov = Image.new('RGBA', (SW, SH), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.ov); self.dark = dark
        if dark: self.TXT, self.HALO, self.ACC, self.SUB = (255, 236, 200), (14, 9, 6), (255, 210, 120), (225, 205, 170)
        else: self.TXT, self.HALO, self.ACC, self.SUB = (22, 18, 16), (236, 222, 190), (150, 28, 18), (60, 48, 40)
        self.boxes = list(reserved)

    def T(self, s, x, y, size, fill=None, anchor='mm', stroke=5, a=1.0, halo=None):
        a = int(255 * cl(a))
        if a > 0: self.d.text((x, y), s, font=font(size), fill=tuple(fill or self.TXT) + (a,), anchor=anchor, stroke_width=stroke, stroke_fill=tuple(halo or self.HALO) + (int(a * 0.92),))

    def V(self, s, x, y, size, gap=1.06, **kw):          # 竖排
        for i, ch in enumerate(s): self.T(ch, x, y + i * size * gap, size, **kw)

    def place(self, txt, cands, size, top=150, **kw):
        f = font(size)
        for (x, y) in cands:
            l, tp, r, b_ = self.d.textbbox((x, y), txt, font=f, anchor='mm'); bb = (l - 6, tp - 4, r + 6, b_ + 4)
            if bb[0] < 10 or bb[2] > SW - 10 or bb[1] < top or bb[3] > SH - 60: continue
            if any(not (bb[2] < o[0] or bb[0] > o[2] or bb[3] < o[1] or bb[1] > o[3]) for o in self.boxes): continue
            self.boxes.append(bb); self.T(txt, x, y, size, **kw); return (x, y)
        return None

    def slam(self, txt, x, y, size, lt, t0=0.0, fill=None, stroke=9, vertical=False, hold=99):
        """大字砸下：放大回弹 + 淡入，hold 秒后淡出。"""
        if lt < t0 or lt > t0 + hold: return
        l = lt - t0; sz = size * (1 + 0.45 * (1 - eout(l / 0.15))); a = ease(l / 0.07) * (1 - ease((l - hold + 0.15) / 0.15))
        (self.V if vertical else self.T)(txt, x, y, sz, fill=fill or self.ACC, stroke=stroke, a=a)

    def over(self, img): return Image.alpha_composite(img.convert('RGBA'), self.ov).convert('RGB')
