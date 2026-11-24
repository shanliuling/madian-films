"""action — 打斗片用的工具（任何系列都能用）：带缓动的关键帧、可旋转可震的镜头、跟随链（头发衣摆）、粒子（火花/尘/碎石/火焰）、刀光拖影、冲击帧、速度线、集中线、泛光、砸字。
全部无状态：每样东西都是时间 t 的函数，任意一帧可以单独渲染（分段并行渲染不会错位）。
    f = track([(0, a), (0.3, b, 'i'), (0.4, c, 'snap')]); v = f(t)         # 第三项是「到达这一帧」用的缓动
    M = cam_m((cx, cy, z, rot), depth, R); c.set_matrix(cairo.Matrix(M[0,0], M[1,0], M[0,1], M[1,1], M[0,2], M[1,2]))"""
import math, numpy as np, cv2, cairo
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from paper import layer, rgba

# ---------- 缓动和关键帧
EASE = dict(lin=lambda u: u, io=lambda u: u * u * (3 - 2 * u), i=lambda u: u ** 2.6, o=lambda u: 1 - (1 - u) ** 2.6, snap=lambda u: 1 - (1 - u) ** 5,
            back=lambda u: 1 + 2.4 * (u - 1) ** 3 + 1.4 * (u - 1) ** 2, hold=lambda u: 0.0, ii=lambda u: u ** 4)
def mix(a, b, k):
    if isinstance(a, dict): return {q: (mix(a[q], b[q], k) if q in b else a[q]) for q in a} | {q: b[q] for q in b if q not in a}
    if isinstance(a, (tuple, list)): return tuple(mix(x, y, k) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)): return a + (b - a) * k
    return a if k < 0.5 else b
def track(keys, default='io'):
    ks = [(k[0], k[1], k[2] if len(k) > 2 else default) for k in keys]
    def f(t):
        if t <= ks[0][0]: return ks[0][1]
        for (t0, v0, _), (t1, v1, e) in zip(ks, ks[1:]):
            if t < t1: return mix(v0, v1, EASE[e]((t - t0) / (t1 - t0)))
        return ks[-1][1]
    return f
def rnd(i, j=0): return (math.sin(i * 127.1 + j * 311.7 + 1.3) * 43758.5453) % 1.0          # 确定性的伪随机数（0–1）
def pulse(t, t0, up, down): return 0.0 if t < t0 else (min(1.0, (t - t0) / up) if t < t0 + up else math.exp(-(t - t0 - up) / down))

# ---------- 镜头：cam = (cx, cy, z, rot°)。depth 同 stage：0 无穷远，1 人物平面
def cam_m(cam, d, R, ox=0.0, oy=0.0):
    cx, cy, z, rot = cam; zz = (1 + (z - 1) * d) * R.k; px = 960 + (cx - 960) * d; py = 540 + (cy - 540) * d; a = math.radians(rot); co, si = math.cos(a) * zz, math.sin(a) * zz
    return np.float64([[co, -si, R.w / 2 + ox * R.k - co * px + si * py], [si, co, R.h / 2 + oy * R.k - si * px - co * py]])
def ctx(R, M):
    s, c = layer(R.w, R.h); c.set_matrix(cairo.Matrix(M[0, 0], M[1, 0], M[0, 1], M[1, 1], M[0, 2], M[1, 2])); return s, c
def plate(fr, pl, M, R):
    """把一张背景板合进帧。pl = dict(rgb, a(可无), x0, y0, ps)：板的左上角在场景 (x0, y0)，ps = 板像素 / 场景像素。"""
    P = M @ np.float64([[1 / pl['ps'], 0, pl['x0']], [0, 1 / pl['ps'], pl['y0']], [0, 0, 1]]); w = cv2.warpAffine(pl['rgb'], P, (R.w, R.h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE if pl.get('a') is None else cv2.BORDER_CONSTANT)
    if pl.get('a') is None: return w
    a = cv2.warpAffine(pl['a'], P, (R.w, R.h), flags=cv2.INTER_LINEAR)[..., None]; return fr * (1 - a) + w
def shake(t, hits, f=60):
    """hits = [(t0, 幅度, 衰减秒)] → (dx, dy)，场景像素。"""
    x = y = 0.0; n = int(t * f)
    for i, (t0, amp, dec) in enumerate(hits):
        if t >= t0: k = amp * math.exp(-(t - t0) / dec); x += k * (rnd(n, i) * 2 - 1); y += k * (rnd(n, i + 50) * 2 - 1)
    return x, y

# ---------- 跟随链：头发、衣摆、飘带。get(dt) = 挂点在 t−dt 的位置；越靠末端越滞后，长度不变
def chain(get, n, seg, lag, rest=(0, 1), t=0.0, flut=0.0, ph=0.0):
    q = [get(i * lag) for i in range(n + 1)]; q = [(p[0] + rest[0] * seg * i, p[1] + rest[1] * seg * i) for i, p in enumerate(q)]; pts = [q[0]]
    for i in range(1, n + 1):
        dx, dy = q[i][0] - q[i - 1][0], q[i][1] - q[i - 1][1]; L = math.hypot(dx, dy) or 1e-6; a = math.atan2(dy, dx) + flut * math.sin(t * 13 + i * 1.1 + ph) * i / n
        pts.append((pts[-1][0] + math.cos(a) * seg, pts[-1][1] + math.sin(a) * seg))
    return pts
def smooth(pts, k=4):
    """Catmull-Rom 加密一条折线。"""
    P = [pts[0]] + list(pts) + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(k):
            u = j / k; out.append(tuple(0.5 * (2 * p1[q] + (-p0[q] + p2[q]) * u + (2 * p0[q] - 5 * p1[q] + 4 * p2[q] - p3[q]) * u * u + (-p0[q] + 3 * p1[q] - 3 * p2[q] + p3[q]) * u ** 3) for q in (0, 1)))
    out.append(pts[-1]); return out
def ribbon_path(c, pts, ws):
    """沿折线铺一条宽度变化的带子（ws = 每个点的半宽）。"""
    L, Rr = [], []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(len(pts) - 1, i + 1)]; dx, dy = b[0] - a[0], b[1] - a[1]; d = math.hypot(dx, dy) or 1e-6; nx, ny = -dy / d, dx / d; w = ws[i] if not callable(ws) else ws(i / (len(pts) - 1))
        L.append((p[0] + nx * w, p[1] + ny * w)); Rr.append((p[0] - nx * w, p[1] - ny * w))
    c.new_path(); c.move_to(*L[0])
    for p in L[1:] + Rr[::-1]: c.line_to(*p)
    c.close_path()

# ---------- 刀光拖影：samples = [(根, 尖)]，从新到旧
def trail(c, samples, col, a=0.9, core=(1, 1, 1)):
    n = len(samples) - 1
    for i in range(n):
        (b0, p0), (b1, p1) = samples[i], samples[i + 1]; k = (1 - i / n) ** 1.6 * a
        if k <= 0.004: continue
        m0 = (b0[0] + (p0[0] - b0[0]) * (0.35 + 0.5 * i / n), b0[1] + (p0[1] - b0[1]) * (0.35 + 0.5 * i / n)); m1 = (b1[0] + (p1[0] - b1[0]) * (0.35 + 0.5 * (i + 1) / n), b1[1] + (p1[1] - b1[1]) * (0.35 + 0.5 * (i + 1) / n))
        c.move_to(*m0); c.line_to(*p0); c.line_to(*p1); c.line_to(*m1); c.close_path(); c.set_source_rgba(*col, k * 0.55); c.fill()
        e0 = (p0[0] + (b0[0] - p0[0]) * 0.07, p0[1] + (b0[1] - p0[1]) * 0.07); e1 = (p1[0] + (b1[0] - p1[0]) * 0.07, p1[1] + (b1[1] - p1[1]) * 0.07)
        c.move_to(*e0); c.line_to(*p0); c.line_to(*p1); c.line_to(*e1); c.close_path(); c.set_source_rgba(*core, k); c.fill()

# ---------- 粒子（都按出生时间算位置，无状态）
def sparks(c, t, t0, pos, n, ang, spread, v0, v1, life, col, seed=0, g=1500, w=3.0, drag=1.8):
    """一把火花：t0 时刻从 pos 朝 ang（度，0 右、90 上）±spread 喷出，画成带尾巴的亮线。"""
    for i in range(n):
        lf = life * (0.45 + 0.55 * rnd(i, seed)); a = t - t0 - 0.02 * rnd(i, seed + 9)
        if a < 0 or a > lf: continue
        th = math.radians(ang + spread * (rnd(i, seed + 1) * 2 - 1)); v = v0 + (v1 - v0) * rnd(i, seed + 2) ** 1.5; e = (1 - math.exp(-drag * a)) / drag; e2 = (1 - math.exp(-drag * max(0, a - 0.035))) / drag
        x, y = pos[0] + math.cos(th) * v * e, pos[1] - math.sin(th) * v * e + 0.5 * g * a * a; a2 = max(0, a - 0.035); x2, y2 = pos[0] + math.cos(th) * v * e2, pos[1] - math.sin(th) * v * e2 + 0.5 * g * a2 * a2
        k = (1 - a / lf) ** 0.7; c.set_line_width(w * (0.5 + 0.8 * rnd(i, seed + 3)) * (0.4 + 0.6 * k)); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_source_rgba(*col, k); c.move_to(x2, y2); c.line_to(x, y); c.stroke()
def emit(c, t, t0, t1, rate, posf, **kw):
    """持续喷火花：t0–t1 之间每秒 rate 次，每次 1 颗，从 posf(出生时刻) 出来。"""
    i0 = max(0, int((t - kw.get('life', 0.4) - t0) * rate)); i1 = int((min(t, t1) - t0) * rate); sd = kw.pop('seed', 0)
    for i in range(i0, i1 + 1):
        tb = t0 + i / rate
        if tb <= t: sparks(c, t, tb, posf(tb), 1, seed=sd + i * 7, **kw)
def puff(c, t, t0, pos, n, spread, rise, r0, r1, life, col, seed=0, vx=0.0):
    """尘烟：一团团软圆，往外散、慢慢升、变大变淡。"""
    for i in range(n):
        lf = life * (0.6 + 0.4 * rnd(i, seed)); a = t - t0 - 0.05 * rnd(i, seed + 5)
        if a < 0 or a > lf: continue
        u = a / lf; e = 1 - (1 - u) ** 3; x = pos[0] + (rnd(i, seed + 1) * 2 - 1) * spread * (0.25 + e) + vx * e * (0.5 + rnd(i, seed + 4)); y = pos[1] - rise * e * (0.3 + rnd(i, seed + 2)); r = r0 + (r1 - r0) * e * (0.6 + 0.4 * rnd(i, seed + 3)); k = (1 - u) ** 1.3 * col[3]
        gr = cairo.RadialGradient(x, y, 0, x, y, r); gr.add_color_stop_rgba(0, *col[:3], k); gr.add_color_stop_rgba(0.6, *col[:3], k * 0.6); gr.add_color_stop_rgba(1, *col[:3], 0); c.set_source(gr); c.arc(x, y, r, 0, 7); c.fill()
def debris(c, t, t0, pos, n, v0, v1, col, seed=0, g=2200, size=14, floor=None, ink=(0.1, 0.11, 0.15)):
    """碎石：带棱角的小块，抛出去、打转、落地后停住淡掉。"""
    for i in range(n):
        a = t - t0
        if a < 0: continue
        th = math.radians(20 + 140 * rnd(i, seed)); v = v0 + (v1 - v0) * rnd(i, seed + 1); vx, vy = math.cos(th) * v, -math.sin(th) * v; x = pos[0] + vx * a; y = pos[1] + vy * a + 0.5 * g * a * a; al = 1.0
        if floor is not None and y > floor + 40 * rnd(i, seed + 6):
            tl = (-vy + math.sqrt(max(0, vy * vy + 2 * g * (floor + 40 * rnd(i, seed + 6) - pos[1])))) / g; x = pos[0] + vx * tl + vx * 0.08 * (1 - math.exp(-(a - tl) * 6)); y = floor + 40 * rnd(i, seed + 6); al = max(0.0, 1 - (a - tl) / 1.2); a = tl
        if al <= 0: continue
        s = size * (0.4 + 1.1 * rnd(i, seed + 2)); ro = a * (rnd(i, seed + 3) * 2 - 1) * 14; c.save(); c.translate(x, y); c.rotate(ro); c.move_to(-s, -s * 0.5); c.line_to(s * 0.2, -s * 0.9); c.line_to(s, s * 0.1); c.line_to(s * 0.1, s * 0.8); c.close_path()
        k = 0.75 + 0.5 * rnd(i, seed + 4); c.set_source_rgba(col[0] * k, col[1] * k, col[2] * k, al); c.fill_preserve(); c.set_source_rgba(*ink, al); c.set_line_width(2.2); c.stroke(); c.restore()
def flame(c, t, posf, n, life, rise, r0, col, core=(1, 1, 1), seed=0, a=1.0, wob=18, vel=(0, 0)):
    """火：n 团小火舌循环出生。posf(dt, s) = 火源在 t−dt 时的位置（s∈0–1 是火源上的哪一点）——火舌留在出生的地方往上蹿，所以挥动时会拖出火尾。"""
    for i in range(n):
        lf = life * (0.55 + 0.45 * rnd(i, seed)); age = (t + rnd(i, seed + 1) * lf) % lf; u = age / lf; p = posf(age, rnd(i, seed + 2))
        if p is None: continue
        x = p[0] + vel[0] * age + wob * math.sin(t * 9 + i * 2.4) * u + (rnd(i, seed + 3) - 0.5) * r0 * 0.8; y = p[1] - rise * age * (0.6 + 0.8 * rnd(i, seed + 4)) + vel[1] * age; r = r0 * (0.5 + 0.9 * rnd(i, seed + 5)) * (1 - u) ** 0.8 * (0.5 + 2.2 * min(u * 5, 1) * 0.5); k = a * (1 - u) ** 1.2 * min(1, u * 9)
        if r < 0.5: continue
        gr = cairo.RadialGradient(x, y, 0, x, y, r); h = max(0.0, 1 - u * 2.2); gr.add_color_stop_rgba(0, col[0] + (core[0] - col[0]) * h, col[1] + (core[1] - col[1]) * h, col[2] + (core[2] - col[2]) * h, k); gr.add_color_stop_rgba(0.5, *col, k * 0.55); gr.add_color_stop_rgba(1, col[0] * 0.3, col[1] * 0.5, col[2] * 0.5, 0)
        c.set_source(gr); c.arc(x, y, r, 0, 7); c.fill()
def ring(c, t, t0, pos, r1, life, col, sq=0.32, w=26):
    """气浪：贴地的椭圆环（sq = 压扁比例，1 就是正圆）。"""
    a = t - t0
    if a < 0 or a > life: return
    u = a / life; e = 1 - (1 - u) ** 3; c.save(); c.translate(*pos); c.scale(1, sq); c.set_line_width(w * (1 - u) + 2); c.set_source_rgba(*col, (1 - u) ** 1.5); c.arc(0, 0, r1 * e, 0, 7); c.restore(); c.stroke()
def burst(c, pos, r, col, a=1.0, rays=0, t=0.0, seed=0, core=(1, 1, 1)):
    """一团光 + 放射的光芒。"""
    gr = cairo.RadialGradient(pos[0], pos[1], 0, pos[0], pos[1], r); gr.add_color_stop_rgba(0, *core, a); gr.add_color_stop_rgba(0.25, *col, a * 0.8); gr.add_color_stop_rgba(1, *col, 0); c.set_source(gr); c.arc(pos[0], pos[1], r, 0, 7); c.fill()
    for i in range(rays):
        th = rnd(i, seed) * 6.283 + 0.25 * math.sin(t * 5 + i); L = r * (1.0 + 1.6 * rnd(i, seed + 1 + int(t * 30))); wd = 0.012 + 0.03 * rnd(i, seed + 2)
        c.move_to(*pos); c.line_to(pos[0] + math.cos(th - wd) * L, pos[1] + math.sin(th - wd) * L); c.line_to(pos[0] + math.cos(th + wd) * L, pos[1] + math.sin(th + wd) * L); c.close_path(); c.set_source_rgba(*core, a * 0.8); c.fill()
def crescent(c, pos, ang, L, col, a=1.0, thick=0.2, core=(1, 1, 1)):
    """一弯月牙（风刃、剑气）：朝 ang（度）飞。"""
    c.save(); c.translate(*pos); c.rotate(-math.radians(ang)); c.move_to(0, -L / 2); c.curve_to(L * 0.42, -L * 0.25, L * 0.42, L * 0.25, 0, L / 2); c.curve_to(L * (0.42 - thick), L * 0.2, L * (0.42 - thick), -L * 0.2, 0, -L / 2); c.close_path(); c.set_source_rgba(*col, a); c.fill_preserve(); c.set_source_rgba(*core, a); c.set_line_width(L * 0.03); c.stroke(); c.restore()

# ---------- 屏幕空间的效果（直接改帧）
def add_glow(fr, s, blur, k=1.0, body=1.0):
    rgb, al = rgba(s); return fr * (1 - al * 0.35 * body) + rgb * body + cv2.GaussianBlur(rgb, (0, 0), blur) * k
def bloom(fr, R, th=0.72, k=0.8, blur=14):
    b = np.clip(fr - th, 0, 1); return fr + cv2.GaussianBlur(b, (0, 0), blur * R.k * 2) * k
def mblur(img, dx, dy=0):
    """按镜头速度做方向模糊（dx, dy 单位输出像素）。"""
    k = int(max(abs(dx), abs(dy)));
    if k < 3: return img
    k = min(k, 90) | 1; ker = np.zeros((k, k), np.float32); cv2.line(ker, (0, k // 2) if abs(dx) >= abs(dy) else (k // 2, 0), (k - 1, k // 2) if abs(dx) >= abs(dy) else (k // 2, k - 1), 1.0, 1)
    if abs(dx) >= abs(dy) and dy: M = cv2.getRotationMatrix2D((k / 2 - 0.5, k / 2 - 0.5), -math.degrees(math.atan2(dy, dx)), 1); ker = cv2.warpAffine(ker, M, (k, k))
    return cv2.filter2D(img, -1, ker / max(ker.sum(), 1e-6), borderType=cv2.BORDER_REPLICATE)
def speedlines(fr, t, R, a=0.5, n=46, ang=0.0, col=(1, 1, 1), f=30):
    """速度线：横贯画面的细亮线，上下两边密、中间留给人。"""
    s, c = layer(R.w, R.h); fi = int(t * f); c.translate(R.w / 2, R.h / 2); c.rotate(math.radians(ang))
    for i in range(n):
        y = (rnd(i, fi) * 2 - 1); y = math.copysign(abs(y) ** 0.6, y) * R.h * 0.62; x = (rnd(i, fi + 3) * 2 - 1) * R.w * 0.6; L = R.w * (0.25 + 0.7 * rnd(i, fi + 5)); w = (0.6 + 2.6 * rnd(i, fi + 7)) * R.k * 2 * (0.5 + abs(y) / R.h)
        gr = cairo.LinearGradient(x - L / 2, 0, x + L / 2, 0); gr.add_color_stop_rgba(0, *col, 0); gr.add_color_stop_rgba(0.5, *col, a * (0.3 + 0.7 * rnd(i, fi + 9))); gr.add_color_stop_rgba(1, *col, 0); c.set_source(gr); c.rectangle(x - L / 2, y - w / 2, L, w); c.fill()
    rgb, al = rgba(s); return fr * (1 - al) + rgb
def focuslines(fr, t, R, pos, a=0.8, n=70, r0=0.42, col=(1, 1, 1), f=20):
    """集中线：从四周指向 pos（输出像素坐标）的尖楔。"""
    s, c = layer(R.w, R.h); fi = int(t * f); D = math.hypot(R.w, R.h)
    for i in range(n):
        th = (i + rnd(i, fi)) / n * 6.283; wd = 0.006 + 0.022 * rnd(i, fi + 2); rr = D * (r0 + 0.22 * rnd(i, fi + 4))
        c.move_to(pos[0] + math.cos(th) * rr, pos[1] + math.sin(th) * rr); c.line_to(pos[0] + math.cos(th - wd) * D * 1.2, pos[1] + math.sin(th - wd) * D * 1.2); c.line_to(pos[0] + math.cos(th + wd) * D * 1.2, pos[1] + math.sin(th + wd) * D * 1.2); c.close_path()
    c.set_source_rgba(*col, a); c.fill(); rgb, al = rgba(s); return fr * (1 - al) + rgb
def impact(fr, mask, glow, mode, R, pos, t, tint=(0.55, 1.0, 0.9)):
    """冲击帧。mask = 人物 alpha，glow = 特效层亮度。mode 1：白底黑人黑线；mode 2：黑底白人，特效染色；mode 3：只是闪白。"""
    g = np.clip(glow.max(-1, keepdims=True) * 1.6, 0, 1)
    if mode == 1: out = np.ones_like(fr) * (1 - mask) * (1 - g); return focuslines(out, t, R, pos, a=1.0, n=90, r0=0.16, col=(0, 0, 0), f=60)
    if mode == 2: out = np.zeros_like(fr) + mask; out = out * (1 - g) + g * np.float32(tint); return focuslines(out, t, R, pos, a=1.0, n=90, r0=0.2, col=(1, 1, 1), f=60)
    return fr + (1 - fr) * 0.6
def grade(fr, sat=1.12, con=1.06, vig=0.28):
    h, w = fr.shape[:2]; l = fr.mean(-1, keepdims=True); fr = l + (fr - l) * sat; fr = (fr - 0.5) * con + 0.5
    if not hasattr(grade, 'v') or grade.v.shape[:2] != (h, w):
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.414; grade.v = (1 - vig * np.clip(d, 0, 1) ** 2.4)[..., None]
    return fr * grade.v

# ---------- 砸字：毛笔大字（竖排或横排），放大着砸下来、震一下、停住
class Slam:
    def __init__(s, text, font, px, R, col=(255, 255, 255), edge=(8, 10, 16), glow=(60, 255, 210), vertical=True, gap=0.92):
        px = int(px * R.k); f = ImageFont.truetype(font, px); pad = int(px * 0.6); n = len(text)
        W, H = (px + 2 * pad, int(px * gap * n) + 2 * pad) if vertical else (int(px * gap * n) + 2 * pad, px + 2 * pad); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); dg = ImageDraw.Draw(g)
        for i, ch in enumerate(text):
            xy = (W / 2, pad + px * gap * (i + 0.5)) if vertical else (pad + px * gap * (i + 0.5), H / 2)
            dg.text(xy, ch, font=f, fill=glow + (255,), anchor='mm', stroke_width=int(px * 0.10), stroke_fill=glow + (255,)); d.text(xy, ch, font=f, fill=col + (255,), anchor='mm', stroke_width=max(2, int(px * 0.055)), stroke_fill=edge + (255,))
        g = g.filter(ImageFilter.GaussianBlur(px * 0.12)); a = np.asarray(g, np.float32) / 255; b = np.asarray(im, np.float32) / 255
        s.glow = a[..., :3] * a[..., 3:] * 0.9; s.rgb = b[..., :3] * b[..., 3:]; s.al = b[..., 3]; s.W, s.H = W, H
    def draw(s, fr, t, t0, t1, pos, R, big=2.6, din=0.13, dout=0.12, rot=0.0):
        """pos = 字的中心（场景 1920×1080 坐标）。"""
        if t < t0 or t > t1: return fr
        u = min(1.0, (t - t0) / din); sc = 1 + (big - 1) * (1 - u) ** 3; al = min(1.0, u * 3) * min(1.0, (t1 - t) / dout); jx, jy = shake(t, [(t0 + din, 14, 0.09)]); cx, cy = (pos[0] + jx) * R.k, (pos[1] + jy) * R.k
        M = cv2.getRotationMatrix2D((s.W / 2, s.H / 2), rot, sc); M[0, 2] += cx - s.W / 2; M[1, 2] += cy - s.H / 2
        w = lambda a: cv2.warpAffine(a, M, (R.w, R.h), flags=cv2.INTER_LINEAR); a = w(s.al)[..., None] * al
        return (fr + w(s.glow) * al) * (1 - a) + w(s.rgb) * al
