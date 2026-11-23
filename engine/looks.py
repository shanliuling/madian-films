"""looks — 合成用的小工具：轮廓光、颗粒、暗角、光柱、发光字。"""
import numpy as np, cv2, cairo
from PIL import Image, ImageDraw, ImageFilter
from paper import *

def shift(a, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]]); return cv2.warpAffine(a, M, (a.shape[1], a.shape[0]))

def lit(img, s, light=(1, -0.4), rim=(1.0, 0.9, 0.75), rim_w=5, rim_a=0.9, half_w=16, half_a=0.22, shade_w=22, shade_a=0.35, opacity=1.0):
    """把一层人物合到 img 上：朝光一侧加一道硬边轮廓光和一片半亮面，背光一侧压暗。light 指向光源。"""
    rgb, al = rgba(s); a = al[..., 0]; L = np.float32(light); L /= np.linalg.norm(L)
    def band(w): return np.clip(a - shift(a, -L[0] * w, -L[1] * w), 0, 1)[..., None]      # 离朝光边缘 w 像素内
    def back(w): return np.clip(a - shift(a, L[0] * w, L[1] * w), 0, 1)[..., None]
    col = rgb * (1 - shade_a * back(shade_w))
    col = col + np.float32(rim) * (half_a * band(half_w) + rim_a * band(rim_w)) * al
    return img * (1 - al * opacity) + np.clip(col, 0, 1) * opacity

def grain(img, amt=0.035, seed=1):
    r = np.random.default_rng(seed); n = r.normal(0, 1, img.shape[:2]).astype(np.float32); n = cv2.GaussianBlur(n, (0, 0), 0.7)
    return np.clip(img + amt * n[..., None], 0, 1)

def vignette(img, k=0.55, p=2.2):
    h, w = img.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.414
    return img * (1 - k * np.clip(d, 0, 1) ** p)[..., None]

def beam(img, apex, a0, a1, length, col=(0.75, 0.85, 1.0), a=0.35, blur=18):
    """从 apex 射出的一束体积光（角度制，0=朝右，90=朝下）。"""
    s, c = layer(img.shape[1], img.shape[0]); g = cairo.RadialGradient(apex[0], apex[1], 0, apex[0], apex[1], length)
    g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(0.6, *col, a * 0.45); g.add_color_stop_rgba(1, *col, 0)
    c.set_source(g); c.move_to(*apex); c.arc(apex[0], apex[1], length, np.radians(a0), np.radians(a1)); c.close_path(); c.fill()
    rgb, al = rgba(s); rgb = cv2.GaussianBlur(rgb, (0, 0), blur)
    return np.clip(img + rgb, 0, 1)

def glow_add(img, s, blur=12, k=1.0):
    rgb, al = rgba(s); return np.clip(img + cv2.GaussianBlur(rgb, (0, 0), blur) * k, 0, 1)

def gold_text(im, xy, s, px, anchor='mm', col=(240, 196, 110), glow=(255, 170, 60), spacing=6):
    g = Image.new('RGBA', im.size, (0, 0, 0, 0)); text(g, xy, s, px, glow + (255,), anchor, spacing=spacing)
    g = g.filter(ImageFilter.GaussianBlur(px * 0.22)); g.putalpha(g.getchannel('A').point(lambda v: int(v * 0.55)))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); text(sh, (xy[0] + 3, xy[1] + 4), s, px, (0, 0, 0, 200), anchor, spacing=spacing); sh = sh.filter(ImageFilter.GaussianBlur(3))
    im.paste(sh, (0, 0), sh); im.paste(g, (0, 0), g); text(im, xy, s, px, col, anchor, spacing=spacing)

def sub(im, s, y=1010, px=40, col=(236, 236, 240)):
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); text(sh, (962, y + 2), s, px, (0, 0, 0, 230), 'mm', spacing=3); sh = sh.filter(ImageFilter.GaussianBlur(3)); im.paste(sh, (0, 0), sh)
    text(im, (960, y), s, px, col, 'mm', spacing=3)
