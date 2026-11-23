import numpy as np, cv2, cairo
from PIL import Image, ImageDraw, ImageFont
W, H = 1920, 1080
import os
# 字体：粗宋体。可用环境变量 MADIAN_FONT 指定，否则按顺序找系统里有的
FONT = next((p for p in [os.environ.get('MADIAN_FONT', ''), '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.otf', 'C:/Windows/Fonts/NotoSerifSC-Bold.otf', 'C:/Windows/Fonts/simsunb.ttf', 'C:/Windows/Fonts/msyhbd.ttc', '/System/Library/Fonts/Supplemental/Songti.ttc', '/System/Library/Fonts/PingFang.ttc'] if p and os.path.exists(p)), None)
if FONT is None: raise RuntimeError('找不到中文字体：请设置环境变量 MADIAN_FONT 指向一个粗宋体或黑体字体文件')
def font(px): return ImageFont.truetype(FONT, int(px))

def paper(seed=3, tint=(0.900, 0.850, 0.740), w=W, h=H):
    r = np.random.default_rng(seed)
    def n(s):
        a = cv2.GaussianBlur(r.random((h, w), dtype=np.float32), (0, 0), s); return (a - a.mean()) / (a.std() + 1e-6)
    v = 1 + 0.035 * n(90) + 0.022 * n(18) + 0.014 * n(3) + 0.012 * n(0.8)
    fib = np.zeros((h, w), np.float32)
    for _ in range(900):
        x, y = r.integers(0, w), r.integers(0, h); a = r.uniform(0, np.pi); L = r.uniform(8, 40)
        cv2.line(fib, (int(x), int(y)), (int(x + np.cos(a) * L), int(y + np.sin(a) * L)), float(r.uniform(-1, 1)), 1, cv2.LINE_AA)
    v += 0.02 * cv2.GaussianBlur(fib, (0, 0), 0.7)
    img = np.float32(tint)[None, None] * v[..., None]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.clip(((xx - w / 2) / (w / 2)) ** 2 * 0.6 + ((yy - h / 2) / (h / 2)) ** 2 * 0.75, 0, 1.6)
    edge = np.clip(d - 0.45, 0, 1)[..., None] * (1 + 0.5 * n(40)[..., None] * 0.3)
    img = img * (1 - 0.34 * edge) + np.float32((0.42, 0.26, 0.12)) * 0.34 * edge * 0.55
    return np.clip(img, 0, 1)

def layer(w=W, h=H):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h); return s, cairo.Context(s)

def rgba(s):
    a = np.ndarray((s.get_height(), s.get_width(), 4), np.uint8, s.get_data()).astype(np.float32) / 255
    return a[..., [2, 1, 0]], a[..., 3:4]            # 预乘 RGB, alpha

def over(img, s, blur=0, opacity=1.0, mode='normal'):
    rgb, al = rgba(s)
    if blur: rgb = cv2.GaussianBlur(rgb, (0, 0), blur); al = cv2.GaussianBlur(al, (0, 0), blur)[..., None]
    rgb = rgb * opacity; al = al * opacity
    if mode == 'mul':                                  # 墨色渗进纸里
        col = rgb / np.maximum(al, 1e-4); return img * (1 - al + al * col)
    return img * (1 - al) + rgb

def to_pil(img): return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

def text(im, xy, s, px, fill, anchor='la', stroke=0, sfill=None, spacing=0):
    d = ImageDraw.Draw(im)
    if spacing:
        x, y = xy; f = font(px)
        tot = sum(d.textlength(ch, font=f) for ch in s) + spacing * (len(s) - 1)
        if anchor[0] == 'm': x -= tot / 2
        if anchor[0] == 'r': x -= tot
        for ch in s:
            d.text((x, y), ch, font=f, fill=fill, anchor='l' + anchor[1], stroke_width=stroke, stroke_fill=sfill); x += d.textlength(ch, font=f) + spacing
    else: d.text(xy, s, font=font(px), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sfill)
