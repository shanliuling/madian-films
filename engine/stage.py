"""stage — 逐帧动画引擎：多层视差背景 + 每帧用 cairo 画会动的人（姿态插值、走路循环）+ 每帧打光 + 镜头关键帧。
    sc = Scene(); sc.bg.append((plate, depth)); sc.add('sil', draw_fn, **light)   # draw_fn(c, t) 在场景坐标（1920×1080）里画
    fr = sc.render(t, (cx, cy, z), R)                                              # R = Out(960, 540)
场景坐标系：1920×1080，镜头 (cx, cy, z) = 画面中心对准的场景点和放大倍数；depth：0=无穷远，1=人物所在平面，>1=前景。"""
import math, numpy as np, cv2, cairo
from paper import layer, rgba
from looks import lit, glow_add, over
import tallfig as F

class Out:
    def __init__(s, w=960, h=540): s.w, s.h, s.k = w, h, w / 1920
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def lerp(a, b, k):
    if isinstance(a, dict): return {q: lerp(a[q], b.get(q, a[q]), k) for q in a}
    if isinstance(a, (tuple, list)): return tuple(lerp(x, y, k) for x, y in zip(a, b))
    return a + (b - a) * k
def kf(keys, t, smooth=True):
    """keys = [(t0, v0), (t1, v1), ...]，v 可以是数、元组、姿态字典；区间内缓入缓出。"""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t < t1: u = (t - t0) / (t1 - t0); return lerp(v0, v1, ease(u) if smooth else u)
    return keys[-1][1]
def pose(name='stand', **o): p = dict(F.POSES[name]); p.update(o); return p
def walk(ph, amp=24, arm=16, lean=4, head=0, bound=False, carry=None):
    """走路循环：ph = 相位（弧度），一圈两步。"""
    s = math.sin(ph); cs = math.cos(ph)
    def leg(sv, cv): th = amp * sv; return (th, th - 6 - 40 * max(0.0, cv) ** 1.3)
    p = dict(lean=lean, head=head, lf=leg(s, cs), lb=leg(-s, -cs))
    if bound: p['af'] = (-24, -50); p['ab'] = (-28, -54)
    elif carry: p['af'], p['ab'] = carry
    else: p['af'] = (-arm * s, -arm * s + 14); p['ab'] = (arm * s, arm * s + 14)
    return p
def step_phase(dist, H): return dist / (0.30 * H) * math.pi                             # 走过 dist 像素对应的相位（一步约 0.30H）

class Scene:
    def __init__(s): s.bg = []; s.items = []; s.fg = []; s.post = None
    def add(s, kind, fn, **kw): s.items.append((kind, fn, kw))
    def _M(s, cam, d, R, ox=0.0, oy=0.0):
        cx, cy, z = cam; zz = (1 + (z - 1) * d) if d <= 1 else z * (1 + (d - 1) * 0.35); px = 960 + (cx - 960) * d; py = 540 + (cy - 540) * d
        return zz * R.k, R.w / 2 - px * zz * R.k + ox * R.k, R.h / 2 - py * zz * R.k + oy * R.k
    def render(s, t, cam, R):
        fr = None
        for (pl, d) in s.bg:
            rgb, al = pl if isinstance(pl, tuple) else (pl, None); ps = rgb.shape[1] / 1920; zz, tx, ty = s._M(cam, d, R); M = np.float32([[zz / ps, 0, tx], [0, zz / ps, ty]])
            w = cv2.warpAffine(rgb, M, (R.w, R.h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT if al is None else cv2.BORDER_CONSTANT)
            if al is None: fr = w
            else: a = cv2.warpAffine(al, M, (R.w, R.h), flags=cv2.INTER_LINEAR); fr = fr * (1 - a[..., None]) + w
        zz, tx, ty = s._M(cam, 1.0, R)
        for (kind, fn, kw) in s.items:
            if kind == 'np': fr = fn(fr, t, (zz, tx, ty), R); continue                 # 直接改帧的效果（光、粒子）
            sf, c = layer(R.w, R.h); c.translate(tx, ty); c.scale(zz, zz); fn(c, t); q = zz                                 # q：场景像素 → 输出像素
            if kind == 'sil': fr = lit(fr, sf, light=kw.get('light', (-1, -0.75)), rim=kw.get('rim', (0.5, 0.68, 0.95)), rim_w=max(1.2, kw.get('rim_w', 3) * q), rim_a=kw.get('rim_a', 0.75), half_w=9 * q, half_a=kw.get('half_a', 0.10), shade_a=0)
            elif kind == 'col': fr = lit(fr, sf, light=kw.get('light', (-1, -0.9)), rim=kw.get('rim', (0.8, 0.9, 1.0)), rim_w=max(1.2, 3.5 * q), rim_a=kw.get('rim_a', 0.7), half_w=12 * q, half_a=0.13, shade_w=20 * q, shade_a=kw.get('shade_a', 0.45))
            elif kind == 'white': fr = glow_add(fr, sf, blur=max(1, kw.get('blur', 22) * q), k=kw.get('k', 0.28)); fr = over(fr, sf, opacity=0.96)
            elif kind == 'glow': fr = glow_add(fr, sf, blur=max(1, kw.get('blur', 12) * q), k=kw.get('k', 0.6)); fr = over(fr, sf)
            else: fr = over(fr, sf, blur=kw.get('blur', 0) * q, opacity=kw.get('opacity', 1.0))
        for (rgb, al, d, bob) in s.fg:
            oy = bob(t) if bob else 0.0; ps = rgb.shape[1] / 1920; zz2, tx2, ty2 = s._M(cam, d, R, 0, oy); M = np.float32([[zz2 / ps, 0, tx2], [0, zz2 / ps, ty2]])
            w = cv2.warpAffine(rgb, M, (R.w, R.h), flags=cv2.INTER_LINEAR); a = cv2.warpAffine(al, M, (R.w, R.h), flags=cv2.INTER_LINEAR); a = a[..., None] if a.ndim == 2 else a; fr = fr * (1 - a) + w
        if s.post: fr = s.post(fr, t, R)
        return fr

def fig(c, S, x, gy, Hh, p, face=-1, mono=None, keep=(), **ex):
    S = dict(F.CAST[S]) if isinstance(S, str) else dict(S); S.update(ex); return F.fig(c, x, gy, Hh, S, 'stand', face, P=p, mono=mono, keep=keep)

# ---------- 碎裂：把一张图切成 Voronoi 碎片，从 impact 向外依次脱落
class Shatter:
    def __init__(s, img, mask, impact, n=260, seed=3):
        r = np.random.default_rng(seed); h, w = img.shape[:2]; s.h, s.w = h, w; ys, xs = np.nonzero(mask > 0.5); idx = r.choice(len(xs), n, replace=False); pts = np.stack([xs[idx], ys[idx]], 1)
        seeds = np.ones((h, w), np.uint8); seeds[pts[:, 1], pts[:, 0]] = 0; _, lab = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL); lab = np.where(mask > 0.5, lab, 0)
        s.sh = []; s.rest = img * (1 - (mask > 0.5)[..., None])                         # rest：窗框和墙
        for L in np.unique(lab):
            if L == 0: continue
            m = (lab == L); yy, xx = np.nonzero(m); x0, x1, y0, y1 = xx.min(), xx.max() + 1, yy.min(), yy.max() + 1; mm = m[y0:y1, x0:x1].astype(np.float32)[..., None]; cx, cy = xx.mean(), yy.mean()
            d = math.hypot(cx - impact[0], cy - impact[1]); ang = math.atan2(cy - impact[1], cx - impact[0]) + r.normal(0, 0.3)
            s.sh.append(dict(x0=x0, y0=y0, rgb=(img[y0:y1, x0:x1] * mm).astype(np.float32), a=mm, t0=d / (w * 1.5) + r.uniform(0, 0.06), vx=math.cos(ang) * r.uniform(60, 260) * w / 1920, vy=math.sin(ang) * r.uniform(40, 200) * w / 1920 - r.uniform(0, 120) * w / 1920, rot=r.normal(0, 2.2), c=(cx - x0, cy - y0)))
    def frame(s, t, g=2600.0, dim=1.0, fade=1.1):
        fr = s.rest.copy() * dim; G = g * s.w / 1920
        for q in s.sh:
            u = t - q['t0']
            if u <= 0: dx = dy = 0.0; a = 0.0; k = 1.0
            else: dx = q['vx'] * u; dy = q['vy'] * u + 0.5 * G * u * u; a = q['rot'] * u; k = max(0.0, 1 - u / fade)
            if k <= 0: continue
            rgb, al = q['rgb'], q['a']; ph, pw = rgb.shape[:2]
            if u > 0:
                M = cv2.getRotationMatrix2D(q['c'], math.degrees(a), 1.0); pad = int(max(ph, pw) * 0.5) + 2; M[0, 2] += pad; M[1, 2] += pad
                rgb = cv2.warpAffine(rgb, M, (pw + 2 * pad, ph + 2 * pad)); al = cv2.warpAffine(al, M, (pw + 2 * pad, ph + 2 * pad))[..., None]; x0 = int(q['x0'] + dx) - pad; y0 = int(q['y0'] + dy) - pad; ph, pw = rgb.shape[:2]
            else: x0, y0 = q['x0'], q['y0']
            xa, ya, xb, yb = max(0, x0), max(0, y0), min(s.w, x0 + pw), min(s.h, y0 + ph)
            if xa >= xb or ya >= yb: continue
            sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0)); reg = fr[ya:yb, xa:xb]; reg *= (1 - al[sl] * k); reg += rgb[sl] * k * (1.0 + 0.6 * min(1, u * 6) * (u < 0.25))
        return fr
