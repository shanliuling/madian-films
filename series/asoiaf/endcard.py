"""endcard — 冰火系列片尾署名画面：绿先知坐在鱼梁木树根里，三眼乌鸦停在膝头（第三只眼在 0.5–1.0 秒睁开），灯挂在树枝上。
greenseer(x, gy, Hh, t, hide=家族) → (rgb, alpha, add, (灯x, 灯y))，1920×1080 画布，float32；hide 是下一集人物的家族，家徽藏在右边的黑暗里，第三只眼睁开时闪一下；python endcard.py 出一张静帧 out/_endcard.jpg"""
import math, numpy as np, cv2, cairo
W, H = 1920, 1080
def _layer():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); return s, cairo.Context(s)
def _alpha(s): return np.frombuffer(s.get_data(), np.uint8).reshape(H, W, 4)[..., 3].astype(np.float32) / 255
_G = {}
def _shift(a, dx, dy): return cv2.warpAffine(a, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H))
# ---------------- 绿先知 + 三眼乌鸦（片尾署名）：鱼梁木白树干、红叶、树上刻脸；斗篷人坐在树根里；三眼乌鸦停在他膝上，第三只眼发红光；灯挂在树枝上
def _leafpath(c, x, y, r, rot):
    for i in range(5):
        an = rot + (i - 2) * 0.62; c.move_to(x, y); c.line_to(x + math.cos(an - 0.24) * r * 0.5, y + math.sin(an - 0.24) * r * 0.5); c.line_to(x + math.cos(an) * r, y + math.sin(an) * r); c.line_to(x + math.cos(an + 0.24) * r * 0.5, y + math.sin(an + 0.24) * r * 0.5); c.close_path(); c.fill()
def _taper(c, pts, w0, w1):
    n = len(pts) - 1
    for i in range(n): c.set_line_width(w0 + (w1 - w0) * i / max(1, n - 1)); c.move_to(*pts[i]); c.line_to(*pts[i + 1]); c.stroke()
def _bez(p0, p1, p2, p3, n=18): return [tuple((1 - v) ** 3 * np.float32(p0) + 3 * (1 - v) ** 2 * v * np.float32(p1) + 3 * (1 - v) * v * v * np.float32(p2) + v ** 3 * np.float32(p3)) for v in np.linspace(0, 1, n)]
def greenseer(x=560, gy=900, Hh=600, t=0.0, hide=None):
    u = Hh; th = 0.09 * math.sin(t * 1.9) + 0.03 * math.sin(t * 4.3); rr = np.random.default_rng(11)
    def X(a): return x + a * u
    def Y(b): return gy - b * u
    def XY(a, b): return (X(a), Y(b))
    def new():
        s, c = _layer(); c.set_source_rgb(1, 1, 1); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND); return s, c
    px, py = X(0.56), Y(1.03); L = 0.17 * u; lx, ly = px + math.sin(th) * L, py + math.cos(th) * L; cw, ch = 0.036 * u, 0.058 * u
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); near = np.exp(-np.sqrt((xx - lx) ** 2 + (yy - ly) ** 2) / (0.80 * u))
    # 1 树：树干、枝、后面的根
    s, c = new(); c.move_to(*XY(-0.40, 0.0)); c.curve_to(*XY(-0.33, 0.25), *XY(-0.33, 0.9), *XY(-0.35, 1.7)); c.line_to(*XY(-0.13, 1.7)); c.curve_to(*XY(-0.12, 0.9), *XY(-0.10, 0.3), *XY(-0.02, 0.0)); c.close_path(); c.fill()
    _taper(c, _bez(XY(-0.14, 0.98), XY(0.10, 1.10), XY(0.34, 1.10), XY(0.60, 1.02)), 0.050 * u, 0.012 * u); _taper(c, _bez(XY(-0.16, 1.22), XY(0.05, 1.42), XY(0.25, 1.50), XY(0.50, 1.56)), 0.045 * u, 0.012 * u); _taper(c, _bez(XY(-0.34, 1.10), XY(-0.50, 1.30), XY(-0.62, 1.40), XY(-0.80, 1.44)), 0.045 * u, 0.012 * u)
    _taper(c, _bez(XY(0.20, 1.09), XY(0.24, 1.22), XY(0.32, 1.28), XY(0.42, 1.30)), 0.022 * u, 0.008 * u)
    _taper(c, _bez(XY(-0.36, 0.10), XY(-0.50, 0.06), XY(-0.62, 0.03), XY(-0.80, 0.0)), 0.06 * u, 0.012 * u); _taper(c, _bez(XY(-0.06, 0.08), XY(0.20, 0.07), XY(0.50, 0.03), XY(0.78, 0.0)), 0.05 * u, 0.008 * u)
    atree = _alpha(s)
    # 2 斗篷人（坐在树根里，背靠树干）
    s, c = new(); c.move_to(*XY(-0.105, 0.60)); c.curve_to(*XY(-0.10, 0.70), *XY(-0.03, 0.745), *XY(0.04, 0.735)); c.curve_to(*XY(0.10, 0.725), *XY(0.125, 0.67), *XY(0.112, 0.60)); c.curve_to(*XY(0.105, 0.565), *XY(0.09, 0.545), *XY(0.085, 0.53))
    c.curve_to(*XY(0.12, 0.47), *XY(0.13, 0.40), *XY(0.17, 0.345)); c.curve_to(*XY(0.21, 0.335), *XY(0.26, 0.345), *XY(0.295, 0.315)); c.curve_to(*XY(0.33, 0.26), *XY(0.33, 0.12), *XY(0.375, 0.0))
    for (a_, b_) in ((0.34, 0.03), (0.31, 0.0), (0.27, 0.035), (0.23, 0.0), (0.18, 0.03), (0.13, 0.0), (0.06, 0.02), (-0.04, 0.0)): c.line_to(*XY(a_, b_))
    c.curve_to(*XY(-0.13, 0.15), *XY(-0.15, 0.42), *XY(-0.105, 0.60)); c.close_path(); c.fill(); afig = _alpha(s)
    s, c = new(); c.move_to(*XY(0.100, 0.565)); c.curve_to(*XY(0.118, 0.61), *XY(0.112, 0.675), *XY(0.075, 0.705)); c.curve_to(*XY(0.035, 0.68), *XY(0.025, 0.60), *XY(0.045, 0.555)); c.close_path(); c.fill(); fh = cv2.GaussianBlur(_alpha(s), (0, 0), 2.5)
    s, c = new(); c.set_line_width(0.012 * u); c.move_to(*XY(0.075, 0.575)); c.curve_to(*XY(0.095, 0.50), *XY(0.085, 0.44), *XY(0.115, 0.385)); c.stroke(); c.set_line_width(0.007 * u); c.move_to(*XY(0.060, 0.57)); c.curve_to(*XY(0.065, 0.50), *XY(0.055, 0.45), *XY(0.075, 0.41)); c.stroke(); ahair = _alpha(s) * afig
    s, c = new(); c.set_line_width(0.007 * u)
    for (p0, p1, p2) in (((-0.02, 0.50), (0.02, 0.30), (0.10, 0.04)), ((-0.07, 0.48), (-0.06, 0.28), (-0.01, 0.04)), ((0.20, 0.33), (0.26, 0.18), (0.29, 0.04))): c.move_to(*XY(*p0)); c.curve_to(*XY(p0[0], p0[1] - 0.08), *XY(*p1), *XY(*p2)); c.stroke()
    fold = cv2.GaussianBlur(_alpha(s), (0, 0), 2.0) * afig
    # 3 前面的根：缠过肩膀和腿
    s, c = new(); _taper(c, _bez(XY(-0.16, 0.50), XY(-0.02, 0.60), XY(0.07, 0.50), XY(0.04, 0.38)), 0.032 * u, 0.010 * u); _taper(c, _bez(XY(-0.20, 0.14), XY(0.00, 0.34), XY(0.20, 0.30), XY(0.24, 0.10)), 0.040 * u, 0.014 * u); _taper(c, _bez(XY(0.24, 0.10), XY(0.26, 0.05), XY(0.32, 0.02), XY(0.46, 0.0)), 0.014 * u, 0.006 * u)
    _taper(c, _bez(XY(-0.10, 0.04), XY(0.02, 0.16), XY(0.10, 0.12), XY(0.16, 0.0)), 0.030 * u, 0.010 * u); aroot = _alpha(s)
    # 4 三眼乌鸦：停在膝头
    hd = 1 if math.sin(t * 0.9 + 0.6) > -0.55 else -1; k = u / 600 * 1.45; rx, ry = X(0.262), Y(0.335) - 46 * k
    s, c = new(); c.save(); c.translate(rx, ry); c.scale(k, k); c.save(); c.rotate(-0.72); c.scale(1.0, 0.60); c.arc(0, 0, 48, 0, math.tau); c.fill(); c.restore()
    c.move_to(-24, 0); c.line_to(-70, 78); c.line_to(-52, 84); c.line_to(-40, 70); c.line_to(-8, 30); c.close_path(); c.fill(); c.arc(22, -40, 20, 0, math.tau); c.fill(); c.move_to(22, -22); c.line_to(22 + hd * 16, -8); c.line_to(22 + hd * 4, -2); c.close_path(); c.fill()
    c.move_to(22 + hd * 10, -54); c.curve_to(22 + hd * 40, -54, 22 + hd * 58, -44, 22 + hd * 62, -28); c.curve_to(22 + hd * 50, -36, 22 + hd * 34, -32, 22 + hd * 12, -30); c.close_path(); c.fill()
    c.set_line_width(6); c.move_to(2, 26); c.line_to(4, 46); c.move_to(14, 24); c.line_to(18, 44); c.stroke(); c.restore(); arav = _alpha(s)
    s, c = new(); op = min(1.0, max(0.0, (t - 0.5) / 0.5))                                 # 第三只眼在 0.5–1.0 秒睁开
    for (ex, ey, er, o) in ((22 + hd * 9, -43, 3.6, 1.0), (22 + hd * 5, -53, 4.4 * op, op)):
        if er > 0.3: c.arc(rx + ex * k, ry + ey * k, er * k, 0, math.tau); c.fill()
    reye = _alpha(s)
    s, c = new(); c.arc(*XY(0.083, 0.632), 0.007 * u, 0, math.tau); c.fill(); geye = _alpha(s)
    # 5 灯
    s, c = new(); c.set_line_width(0.005 * u); c.move_to(px, py); c.line_to(lx, ly - ch * 1.1); c.stroke(); c.save(); c.translate(lx, ly); c.rotate(-th * 0.6)
    c.move_to(-cw * 0.55, -ch); c.line_to(cw * 0.55, -ch); c.line_to(cw, -ch * 0.7); c.line_to(cw, ch * 0.75); c.line_to(cw * 0.6, ch); c.line_to(-cw * 0.6, ch); c.line_to(-cw, ch * 0.75); c.line_to(-cw, -ch * 0.7); c.close_path(); c.fill(); c.arc(0, -ch * 1.12, cw * 0.32, 0, math.tau); c.stroke(); c.restore(); alamp = _alpha(s)
    s, c = new(); c.save(); c.translate(lx, ly); c.rotate(-th * 0.6); c.rectangle(-cw * 0.62, -ch * 0.62, cw * 1.24, ch * 1.3); c.fill(); c.restore(); core = _alpha(s)
    # 6 红叶：枝头一簇簇，几片往下飘；树上刻的脸
    s, c = new()
    for (ca, cb, n, sp) in ((0.05, 1.16, 16, 0.16), (0.36, 1.12, 14, 0.15), (0.30, 1.36, 14, 0.15), (0.52, 1.50, 12, 0.14), (-0.05, 1.46, 16, 0.18), (-0.52, 1.36, 16, 0.18), (-0.74, 1.50, 12, 0.14), (-0.24, 1.62, 16, 0.2), (0.62, 1.08, 6, 0.07)):
        for i in range(n): _leafpath(c, X(ca + rr.normal(0, sp)), Y(cb + rr.normal(0, sp * 0.6)), u * rr.uniform(0.035, 0.06), rr.uniform(0, math.tau) + 0.15 * math.sin(t * 1.4 + i))
    for i in range(7): ph = (rr.random() + t * rr.uniform(0.05, 0.09)) % 1; _leafpath(c, X(rr.uniform(-0.5, 0.75) + 0.05 * math.sin(t * 1.1 + i * 2) + ph * 0.12), Y(1.25 - ph * 1.25), u * 0.036, t * rr.uniform(0.6, 1.6) + i)
    aleaf = _alpha(s)
    s, c = new()
    for sgn in (-1, 1):                                                                   # 两只斜向下的眼、淌下来的红树汁、一道往下撇的嘴
        c.save(); c.translate(X(-0.225 + sgn * 0.060), Y(0.90)); c.rotate(sgn * 0.42); c.scale(0.034 * u, 0.012 * u); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
        c.set_line_width(0.005 * u); c.move_to(X(-0.225 + sgn * 0.070), Y(0.895)); c.curve_to(X(-0.225 + sgn * 0.078), Y(0.85), X(-0.225 + sgn * 0.070), Y(0.80), X(-0.225 + sgn * 0.076), Y(0.74 + sgn * 0.03)); c.stroke()
    c.move_to(*XY(-0.275, 0.735)); c.curve_to(*XY(-0.255, 0.775), *XY(-0.195, 0.775), *XY(-0.175, 0.735)); c.curve_to(*XY(-0.20, 0.752), *XY(-0.25, 0.752), *XY(-0.275, 0.735)); c.close_path(); c.fill(); aface = _alpha(s) * atree
    # 合成
    def dark(a, rim=1.0):
        ab = cv2.GaussianBlur(a, (0, 0), 3.0); thick = np.clip(cv2.GaussianBlur(a, (0, 0), 7) * 1.5 - 0.15, 0.12, 1); warm = a * np.clip(1 - _shift(ab, -7, 3), 0, 1) * (0.25 + 1.2 * near) * thick; cold = a * np.clip(1 - _shift(ab, 6, 1), 0, 1) * 0.35 * thick
        wide = a * np.clip(1 - _shift(cv2.GaussianBlur(a, (0, 0), 16), -30, 10), 0, 1) * near * 0.28
        return a[..., None] * np.float32((0.012, 0.012, 0.018)) + ((warm + wide) * rim)[..., None] * np.float32((1.0, 0.64, 0.30)) + (cold * rim)[..., None] * np.float32((0.30, 0.52, 0.95))
    def pale(a):
        sh = 0.45 + 0.55 * np.clip(cv2.GaussianBlur(a, (0, 0), 9) * 1.5 - 0.5, 0, 1); grain_ = 0.9 + 0.1 * np.sin(xx * 0.09 + np.sin(yy * 0.013) * 3)
        return a[..., None] * (np.float32((0.80, 0.74, 0.64)) * ((0.035 + 0.85 * near) * sh * grain_)[..., None] + np.float32((0.010, 0.016, 0.030)))
    rgb = pale(atree); rgb = rgb * (1 - aface[..., None]) + aface[..., None] * np.float32((0.50, 0.03, 0.03)) * (0.25 + 1.2 * near)[..., None]; al = atree.copy()
    f = dark(afig) + (fold * (0.04 + 0.18 * near))[..., None] * np.float32((1.0, 0.62, 0.32)); f = f * (1 - 0.95 * fh[..., None]); f = f * (1 - ahair[..., None]) + ahair[..., None] * np.float32((0.86, 0.84, 0.80)) * (0.08 + 0.9 * near)[..., None]
    rgb = rgb * (1 - afig[..., None]) + f; al = np.maximum(al, afig)
    rgb = rgb * (1 - aroot[..., None]) + pale(aroot); al = np.maximum(al, aroot)
    rgb = rgb * (1 - arav[..., None]) + dark(arav, 1.25); al = np.maximum(al, arav)
    rgb = rgb * (1 - alamp[..., None]) + alamp[..., None] * np.float32((0.20, 0.13, 0.08)) * (0.25 + 1.6 * near)[..., None]; al = np.maximum(al, alamp)
    rgb = rgb * (1 - aleaf[..., None]) + aleaf[..., None] * np.float32((0.66, 0.06, 0.04)) * (0.10 + 1.0 * near)[..., None]; al = np.maximum(al, aleaf)
    fl = 0.86 + 0.14 * math.sin(t * 15) * math.sin(t * 6.1 + 1)
    add = (cv2.GaussianBlur(core, (0, 0), 70)[..., None] * 1.5 + cv2.GaussianBlur(core, (0, 0), 16)[..., None] * 1.0 + core[..., None] * 0.9) * np.float32((1.0, 0.78, 0.40)) * fl
    add = add + (cv2.GaussianBlur(reye, (0, 0), 7)[..., None] * 1.1 + reye[..., None] * 1.0) * np.float32((1.0, 0.16, 0.10)) + (cv2.GaussianBlur(geye, (0, 0), 5)[..., None] * 0.7 + geye[..., None] * 0.8) * np.float32((1.0, 0.14, 0.10))
    if hide:                                                                              # 下一集的家徽：第三只眼睁开时在黑暗里闪一下，然后只剩很淡的影子
        import heraldry
        if hide not in _G: n = int(1.24 * u); g = np.zeros((H, W, 3), np.float32); x0, y0 = int(x + 1.17 * u - n / 2), int(gy - 0.64 * u - n / 2); sr, sa = heraldry.sigil(hide, n); g[y0:y0 + n, x0:x0 + n] = sr * (sa if sa.ndim == 3 else sa[..., None]); _G[hide] = g / max(0.4, float(np.percentile(g.max(-1)[g.max(-1) > 0.02], 90)))
        add = add + _G[hide] * (1 - al[..., None]) * (op * (0.022 + 0.085 * math.exp(-max(0.0, t - 1.0) * 2.0)) * fl)
    return rgb.astype(np.float32), al, add.astype(np.float32), (lx, ly)
if __name__ == '__main__':
    import os, sys
    from PIL import Image
    rgb, a, add, _ = greenseer(t=float(sys.argv[2]) if len(sys.argv) > 2 else 1.5, hide=sys.argv[1] if len(sys.argv) > 1 else None); os.makedirs('out', exist_ok=True)
    Image.fromarray((np.clip(rgb + add, 0, 1) * 255).astype(np.uint8)).save('out/_endcard.jpg', quality=90)
