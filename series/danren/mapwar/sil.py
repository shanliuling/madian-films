"""mapwar.sil — 剪影人物 + 光效 + 标志物。

素材约定（用 prep() 从生图结果转换）：
  剪影：白底纯黑人形  -> RGBA，alpha = 暗度
  标志物：黑底白色线稿 -> RGBA，alpha = 亮度（线条），颜色由代码上
画法：
  stage(t, col)                     暗色舞台：底色 + 背光 + 烟 + 火星（夜色/燃的镜头）
  paper_stage(...)                  宣纸舞台：纸底 + 朱日/冷月（水墨段落）
  emblem(fr, em, cx, cy, h, cols, a, reveal, mode)   标志物：渐变上色 + 辉光；mode='add' 暗底发光 / 'ink' 纸上着色
  figure(fr, s, cx, bottom, h, rim, a, dark, flip)   剪影：实心身体 + 阵营色轮廓光 + 背后光晕
  giant(fr, s, cx, bottom, h, a, tint, side)         地图上的"执棋者"：半透明巨型剪影，脚下渐隐，靠画面边缘
全部在 float RGB (H,W,3) 上操作，返回新数组。
"""
import os, math
import numpy as np, cv2
from PIL import Image
from .util import SW, SH, TAU, fbm, hsh, ease, cl, rng

_c = {}


def prep(src, dst, kind='sil', lo=30, hi=232, scale=2.0):
    """生图结果 -> 干净的 RGBA。kind='sil' 白底黑剪影；'emblem' 黑底白线。会去噪点、裁边、放大并平滑锯齿。
    尽量用模型原图（有抗锯齿灰边），不要用已经二值化的图——二值化后放大边缘全是台阶。"""
    a = np.asarray(Image.open(src).convert('L')).astype(np.float32)
    al = np.clip((a - 18) / (235 - 18), 0, 1) if kind == 'emblem' else np.clip((hi - a) / (hi - lo), 0, 1)
    m = (al > 0.5).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.r_[False, st[1:, cv2.CC_STAT_AREA] >= (8 if kind == 'emblem' else 30)]
    al = al * (cv2.dilate(keep[lab].astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
    ys, xs = np.where(al > 0.03); p = 6
    al = al[max(0, ys.min() - p):ys.max() + p, max(0, xs.min() - p):xs.max() + p]
    al = np.clip(cv2.resize(al, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC), 0, 1)
    al = np.clip((cv2.GaussianBlur(al, (0, 0), 0.9) - 0.5) * 1.6 + 0.5, 0, 1)
    rgb = np.ones_like(al) if kind == 'emblem' else np.zeros_like(al)
    Image.fromarray((np.dstack([rgb] * 3 + [al]) * 255).astype(np.uint8), 'RGBA').save(dst)


def load(path, h, flip=False):
    """-> alpha (h 高)，缓存。"""
    key = (path, int(h), flip)
    if key not in _c:
        im = Image.open(path); w = max(2, int(im.width * h / im.height))
        a = np.asarray(im.split()[-1].resize((w, int(h)), Image.LANCZOS)).astype(np.float32) / 255
        _c[key] = a[:, ::-1].copy() if flip else a
    return _c[key]


def _place(fr, layer, x0, y0):
    """把 layer(h,w,...) 的可见部分与 fr 对齐，返回 (fr 切片, layer 切片) 或 None。"""
    h, w = layer.shape[:2]; xa, ya = max(0, x0), max(0, y0); xb, yb = min(SW, x0 + w), min(SH, y0 + h)
    if xb <= xa or yb <= ya: return None
    return (slice(ya, yb), slice(xa, xb)), layer[ya - y0:yb - y0, xa - x0:xb - x0]


def _grad(h, cols):
    """竖向渐变色 (h,1,3)：cols = 上色 / (上色, 下色)。"""
    c0 = np.float32(cols[0] if isinstance(cols[0], (tuple, list)) else cols); c1 = np.float32(cols[1] if isinstance(cols[0], (tuple, list)) else cols)
    k = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]; return c0 * (1 - k) + c1 * k


# ---------------------------------------------------------------- stages
def stage(t, glow=(1.0, 0.5, 0.2), gx=SW / 2, gy=SH * 0.55, base=(0.03, 0.03, 0.045), smoke=0.10, embers=60, seed=0, glow_r=0.75, glow_a=0.55):
    """暗色舞台。glow 是背光颜色（阵营色）。"""
    key = ('stg', seed)
    if key not in _c:
        _c[key] = (fbm(SH // 2, SW // 2, 90, 5, 61 + seed), fbm(SH // 2, SW // 2, 40, 4, 71 + seed))
    n1, n2 = _c[key]; yy, xx = np.mgrid[0:SH // 2, 0:SW // 2].astype(np.float32)
    d = np.hypot((xx * 2 - gx) / (SW * glow_r), (yy * 2 - gy) / (SH * glow_r * 0.9))
    g = np.exp(-d * d * 2.2)
    sm = np.roll(n1, int(t * 18) % n1.shape[1], 1) * 0.6 + np.roll(n2, -int(t * 30) % n2.shape[1], 1) * 0.4
    f = np.float32(base) + g[..., None] * np.float32(glow) * glow_a + (sm[..., None] - 0.45) * smoke * (0.3 + g[..., None]) * np.float32(glow)
    f = cv2.resize(np.clip(f, 0, 2), (SW, SH), interpolation=cv2.INTER_LINEAR)
    if embers: f = f + ember_layer(t, embers, seed, glow)
    return f


def ember_layer(t, n=60, seed=0, col=(1.0, 0.6, 0.25)):
    eb = np.zeros((SH // 2, SW // 2), np.float32)
    for i in range(n):
        ph = (t * (0.10 + 0.18 * hsh(i, 7 + seed)) + hsh(i, 8 + seed)) % 1.0
        x = (hsh(i, 9 + seed) * SW + math.sin(t * 1.3 + i) * 50 + ph * 140) / 2; y = SH * (1.05 - ph * (0.7 + 0.5 * hsh(i, 10))) / 2
        cv2.circle(eb, (int(x), int(y)), 1 + int(2 * hsh(i, 11)), float((1 - ph) * (0.5 + 0.5 * hsh(i, 12))), -1)
    return cv2.resize(cv2.GaussianBlur(eb, (0, 0), 1.4), (SW, SH))[..., None] * (np.float32(col) * 0.6 + 0.4)


def paper_stage(sun=None, moon=None, tint=(0.93, 0.89, 0.80)):
    """宣纸舞台：sun=(x,y,r,色) 朱红日 / moon=(x,y,r) 冷月。"""
    key = ('paper', sun, moon, tint)
    if key not in _c:
        n = fbm(SH, SW, 180, 5, 41); fib = cv2.GaussianBlur(rng.random((SH, SW)).astype(np.float32), (0, 0), sigmaX=9, sigmaY=0.6)
        f = np.float32(tint) * (0.88 + 0.2 * n[..., None]) * (1 + 1.2 * (fib[..., None] - 0.5)).clip(0.93, 1.07)
        yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
        if sun:
            x, y, r, col = sun; d = np.hypot(xx - x, yy - y)
            disk = np.clip((r - d) / 3, 0, 1) * (0.85 + 0.15 * fbm(SH, SW, 30, 3, 44)); halo = np.exp(-(np.maximum(d - r, 0) / (r * 0.9)) ** 2) * 0.25
            f = f * (1 - (disk + halo)[..., None] * (1 - np.float32(col)))
        if moon:
            x, y, r = moon; d = np.hypot(xx - x, yy - y); disk = np.clip((r - d) / 3, 0, 1)
            f = f * (1 - disk[..., None] * 0.12) + np.exp(-(np.maximum(d - r, 0) / (r * 1.2)) ** 2)[..., None] * 0.04
        _c[key] = f.astype(np.float32)
    return _c[key].copy()


# ---------------------------------------------------------------- emblem
def emblem(fr, path, cx, cy, h, cols, a=1.0, reveal=1.0, mode='add', glow=1.0, flip=False):
    """标志物。reveal 0..1 从下往上"点亮"。mode='add' 暗底发光；'ink' 纸上着色（不发光）。"""
    al = load(path, h, flip); H, W = al.shape
    if reveal < 1:
        yy = np.linspace(1, 0, H, dtype=np.float32)[:, None]; al = al * np.clip((reveal * 1.25 - yy) / 0.25, 0, 1)
    al = al * a; pl = _place(fr, al, int(cx - W / 2), int(cy - H / 2))
    if pl is None: return fr
    (sy, sx), sub = pl; col = _grad(H, cols)[sy.start - int(cy - H / 2):sy.stop - int(cy - H / 2)]
    fr = fr.copy()
    if mode == 'add':
        line = sub[..., None] * col
        bloom = cv2.GaussianBlur(line, (0, 0), 6) * 1.2 + cv2.GaussianBlur(line, (0, 0), 22) * 0.9
        fr[sy, sx] += (line * 1.1 + bloom * glow)
    else:
        fr[sy, sx] = fr[sy, sx] * (1 - sub[..., None]) + col * sub[..., None]
    return fr


# ---------------------------------------------------------------- figure
def figure(fr, path, cx, bottom, h, rim=(1.0, 0.5, 0.2), a=1.0, body=(0.012, 0.012, 0.018), flip=False, rim_w=1.0, halo=0.55, dx=0.0):
    """剪影：实心身体 + 轮廓光（往光源方向偏的亮边）+ 背后大光晕。暗底用。"""
    al = load(path, h, flip); H, W = al.shape; x0 = int(cx + dx - W / 2); y0 = int(bottom - H)
    pad = int(60 * rim_w + 40); big = np.pad(al, pad)
    edge = np.clip(cv2.dilate(big, np.ones((3, 3), np.uint8), iterations=max(1, int(3 * rim_w))) - big, 0, 1)
    rimL = cv2.GaussianBlur(edge, (0, 0), 1.5 * rim_w) * 1.6 + cv2.GaussianBlur(edge, (0, 0), 6 * rim_w) * 0.9
    glow = cv2.GaussianBlur(big, (0, 0), 28 * rim_w + 10) * halo
    rc = np.float32(rim); fr = fr.copy()
    pl = _place(fr, np.dstack([big, rimL, glow]), x0 - pad, y0 - pad)
    if pl is None: return fr
    (sy, sx), sub = pl; A = sub[..., 0:1] * a; Rm = sub[..., 1:2] * a; G = sub[..., 2:3] * a
    reg = fr[sy, sx] + G * (rc * 0.9 + 0.1)                                  # 背后光晕
    reg = reg * (1 - A) + np.float32(body) * A                              # 身体
    reg = reg + Rm * (1 - A * 0.85) * (rc * 0.8 + 0.35)                     # 轮廓光（压在边上，略溢进身体）
    fr[sy, sx] = reg; return fr


def ink_figure(fr, path, cx, bottom, h, a=1.0, col=(0.06, 0.05, 0.05), flip=False, wash=None, dx=0.0):
    """宣纸上的剪影：浓墨实心 + 外缘一圈淡墨晕（wash=颜色时晕染带阵营色）。"""
    al = load(path, h, flip); H, W = al.shape; x0 = int(cx + dx - W / 2); y0 = int(bottom - H); pad = 50; big = np.pad(al, pad)
    soft = cv2.GaussianBlur(big, (0, 0), 14); fr = fr.copy()
    pl = _place(fr, np.dstack([big, soft]), x0 - pad, y0 - pad)
    if pl is None: return fr
    (sy, sx), sub = pl; A = sub[..., 0:1] * a; S = sub[..., 1:2] * a * 0.35
    wc = np.float32(wash) if wash is not None else np.float32(col)
    reg = fr[sy, sx] * (1 - S * (1 - wc))
    fr[sy, sx] = reg * (1 - A) + np.float32(col) * A; return fr


def giant(fr, path, cx, bottom, h, a=0.5, tint=(0.8, 0.2, 0.15), flip=False, style='ink', fade_from=0.55):
    """地图上的执棋者：半透明巨型剪影，下半身渐隐进地图。style='ink' 墨色+阵营色晕；'night' 黑身+亮轮廓。"""
    al = load(path, h, flip); H, W = al.shape
    k = np.clip((1 - np.linspace(0, 1, H, dtype=np.float32) - (1 - fade_from - 0.35)) / 0.35, 0, 1)[:, None] ** 1.3   # 脚下渐隐
    al2 = al * k; x0 = int(cx - W / 2); y0 = int(bottom - H); pad = 70; big = np.pad(al2, pad)
    soft = cv2.GaussianBlur(big, (0, 0), 26); edge = np.clip(cv2.dilate(big, np.ones((3, 3), np.uint8), iterations=3) - big, 0, 1)
    edge = cv2.GaussianBlur(edge, (0, 0), 2.5)
    pl = _place(fr, np.dstack([big, soft, edge]), x0 - pad, y0 - pad)
    if pl is None: return fr
    (sy, sx), sub = pl; A = sub[..., 0:1] * a; S = sub[..., 1:2] * a; E = sub[..., 2:3] * a; tc = np.float32(tint); fr = fr.copy()
    if style == 'ink':
        reg = fr[sy, sx] * (1 - S * 0.55 * (1 - (tc * 0.6 + 0.4)))            # 阵营色淡晕
        reg = reg * (1 - A * 0.85) + np.float32([0.07, 0.06, 0.06]) * A * 0.85
        reg = reg * (1 - E * 0.5 * (1 - tc))
    else:
        reg = fr[sy, sx] + S * tc * 0.35
        reg = reg * (1 - A * 0.8) + np.float32([0.01, 0.01, 0.02]) * A * 0.8 + E * (tc * 0.9 + 0.2) * 1.2
    fr[sy, sx] = reg; return fr
