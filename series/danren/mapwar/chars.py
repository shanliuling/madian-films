"""mapwar.chars — 人物/整图素材：绿幕抠像、带纸晕贴入、水墨人物底、整图推拉。
人物怎么表现（水墨立绘 / 黑剪影 + 光效 / 不出人物只出字）由每部片自己定，这里只给通用零件。"""
import os
import numpy as np, cairo, cv2
from PIL import Image
from .util import SW, SH, fbm, hsh, to_img, rng

_c = {}


def key_green(src, dst):
    """绿幕 PNG/JPG -> 透明 PNG（按 g - max(r,b) 取 alpha，并去绿溢色）。白衣人物请用绿幕生成，米色底抠不干净。"""
    a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255; r, g, b = a[..., 0], a[..., 1], a[..., 2]
    k = np.clip((g - np.maximum(r, b)) * 3.2, 0, 1); alpha = cv2.GaussianBlur(1 - k, (0, 0), 0.8); alpha = np.clip((alpha - 0.12) / 0.8, 0, 1)
    g2 = np.minimum(g, np.maximum(r, b) * 1.02)
    Image.fromarray((np.dstack([r, g2, b, alpha]) * 255).astype(np.uint8)).save(dst)


def sprite(path, h):
    """读一张透明 PNG 并缩到高度 h -> (rgba float, 光晕 mask)。有缓存。"""
    key = (path, int(h))
    if key not in _c:
        im = Image.open(path).convert('RGBA'); w = int(im.width * h / im.height)
        a = np.asarray(im.resize((w, int(h)), Image.LANCZOS)).astype(np.float32) / 255
        _c[key] = (a, cv2.GaussianBlur(cv2.dilate(a[..., 3], np.ones((9, 9), np.uint8)), (0, 0), 16))
    return _c[key]


def paste(img, path, cx, bottom, h, alpha=1.0, dx=0.0, halo=0.8, halo_col=(0.93, 0.88, 0.76), flip=False, tint=None):
    """把人物贴到画面上（底边对齐 bottom）。halo 是人物背后的一圈晕：浅色画面用纸色，深色画面可给亮色当轮廓光。
    tint=(0,0,0) 可把立绘压成纯黑剪影。"""
    a, hl = sprite(path, h)
    if flip: a = a[:, ::-1]; hl = hl[:, ::-1]
    arr = np.asarray(img).astype(np.float32) / 255
    x0 = int(cx + dx - a.shape[1] / 2); y0 = int(bottom - a.shape[0]); xa, ya = max(0, x0), max(0, y0); xb, yb = min(SW, x0 + a.shape[1]), min(SH, y0 + a.shape[0])
    if xb <= xa or yb <= ya: return img
    sub = a[ya - y0:yb - y0, xa - x0:xb - x0]; hs = hl[ya - y0:yb - y0, xa - x0:xb - x0][..., None] * halo * alpha
    reg = arr[ya:yb, xa:xb] * (1 - hs) + np.float32(halo_col) * hs
    rgb = sub[..., :3] if tint is None else sub[..., :3] * np.float32(tint); al = sub[..., 3:] * alpha
    arr[ya:yb, xa:xb] = reg * (1 - al) + rgb * al
    return to_img(arr)


def ink_bg(band=True):
    """宣纸底 + 一道浓墨横扫（人物亮相用）。-> float HxWx3"""
    key = ('inkbg', band)
    if key not in _c:
        n = fbm(SH, SW, 180, 5, 41); n2 = fbm(SH, SW, 9, 2, 42); fib = cv2.GaussianBlur(rng.random((SH, SW)).astype(np.float32), (0, 0), sigmaX=9, sigmaY=0.6)
        paper = np.float32([0.93, 0.89, 0.80]) * (0.88 + 0.2 * n[..., None] + 0.06 * (n2[..., None] - 0.5)) * (1 + 1.2 * (fib[..., None] - 0.5)).clip(0.92, 1.08)
        s_ = cairo.ImageSurface(cairo.FORMAT_A8, SW, SH); c = cairo.Context(s_); c.set_source_rgba(1, 1, 1, 1)
        if band:
            for k in range(46):
                y = 250 + k * 13 + (hsh(k) - .5) * 26; x0 = -100 + hsh(k, 1) * 300 - k * 3; x1 = SW + 100 - hsh(k, 2) * 380 - k * 2
                c.set_line_width(18 + hsh(k, 3) * 16); c.move_to(x0, y + 110); c.curve_to(x0 + 500, y + 30, x1 - 500, y - 30, x1, y - 110); c.stroke()
        m = np.ndarray((SH, s_.get_stride()), np.uint8, s_.get_data())[:, :SW].astype(np.float32) / 255
        m = np.clip(cv2.GaussianBlur(m, (0, 0), 3) * (0.55 + 0.6 * fbm(SH, SW, 6, 2, 43)), 0, 1)[..., None]
        _c[key] = (paper * (1 - 0.82 * m) + np.float32([0.10, 0.09, 0.09]) * 0.82 * m).astype(np.float32)
    return _c[key]


def cover(path, zoom=1.0, cx=0.5, cy=0.5):
    """整张图铺满画面并可缓慢推拉/平移（cx, cy 为 0..1 的取景位置）。-> float HxWx3"""
    key = ('cov', path)
    if key not in _c:
        im = Image.open(path).convert('RGB'); s = max(SW / im.width, SH / im.height) * 1.25
        _c[key] = np.asarray(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)).astype(np.float32) / 255
    a = _c[key]; w, h = SW * 1.25 / zoom, SH * 1.25 / zoom; x0 = (a.shape[1] - w) * cx; y0 = (a.shape[0] - h) * cy
    return cv2.warpAffine(a, np.float32([[SW / w, 0, -x0 * SW / w], [0, SH / h, -y0 * SH / h]]), (SW, SH), flags=cv2.INTER_LINEAR)
