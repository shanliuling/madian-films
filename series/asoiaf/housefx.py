"""housefx — 带家族身份的字效：箴言、家族台词、人物名牌。都是直接画到一帧上（fr = float32 RGB，输出分辨率），u = 这段字出现后过了几秒。
    fr = motto(fr, '凛冬将至', 'stark', u, R)             # 按家族选字效；fx= 可以指定：frost 结霜飘雪 | roar 砸下来带冲击波 | debt 熔金滴落和金币 | fury 火烧起来往两边蔓延
    fr = nametag(fr, '艾德·史塔克', 'stark', u, R, x, y)   # 人物出场：小圆章 + 名字 + 家族色下划线
python housefx.py 出一段演示 out/_housefx.mp4。新家族没有专属字效时，默认是家族色的字加圆章；想做专属的就照下面的写一个。"""
import math, os, sys, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'engine'))
from PIL import Image, ImageDraw, ImageFont
from paper import FONT
import heraldry as HR
_C = {}
def _ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def _blur(a, s): return cv2.GaussianBlur(a, (0, 0), max(0.3, s))
def _shift(a, dx, dy): return cv2.warpAffine(a, np.float32([[1, 0, dx], [0, 1, dy]]), (a.shape[1], a.shape[0]))
def _grid(R):
    if ('g', R.w) not in _C: _C[('g', R.w)] = np.mgrid[0:R.h, 0:R.w].astype(np.float32)
    return _C[('g', R.w)]
def _text(text, px, R, x, y):
    key = ('t', text, px, R.w, x, y)
    if key not in _C:
        K = R.k; f = ImageFont.truetype(FONT, max(8, int(px * K))); sp = int(px * K * 0.10); w = sum(f.getlength(ch) + sp for ch in text) - sp
        im = Image.new('L', (R.w, R.h), 0); d = ImageDraw.Draw(im); cx = x * K - w / 2; x0 = cx
        for ch in text: d.text((cx, y * K), ch, font=f, fill=255, anchor='lm'); cx += f.getlength(ch) + sp
        _C[key] = (np.asarray(im, np.float32) / 255, (x0, x0 + w))
    return _C[key]
def _noise(R, seed, sx, sy=None):
    key = ('n', R.w, seed, sx, sy)
    if key not in _C: n = cv2.GaussianBlur(np.random.default_rng(seed).random((R.h, R.w)).astype(np.float32), (0, 0), sigmaX=sx * R.k, sigmaY=(sy or sx) * R.k); _C[key] = np.clip((n - n.mean()) / (n.std() + 1e-6) * 0.25 + 0.5, 0, 1)
    return _C[key]
def _metal(m, R, y, px, top, bot, u=None, t0=0.5, t1=1.2):
    """金属字：上下渐变 + 上亮下暗的倒角 + 一道扫过去的高光。"""
    K = R.k; yy, xx = _grid(R); g = np.clip((yy - (y - px * 0.5) * K) / (px * K), 0, 1)[..., None]; col = np.float32(top) * (1 - g) + np.float32(bot) * g
    b = _blur(m, 1.6 * K); hi = np.clip(m - _shift(b, 0, 2.2 * K), 0, 1); lo = np.clip(m - _shift(b, 0, -2.2 * K), 0, 1); col = col * (1 + 0.45 * hi - 0.45 * lo)[..., None]
    if u is not None and t0 < u < t1: pos = (-0.1 + 1.2 * (u - t0) / (t1 - t0)) * R.w; col = col + (np.exp(-((xx + (yy - y * K) * 0.5 - pos) / (46 * K)) ** 2) * 0.55)[..., None]
    return col
def _dots(R, pts, col):
    L = np.zeros((R.h, R.w), np.float32)
    for (x, y, r, a) in pts:
        if 0 <= x < R.w and 0 <= y < R.h: cv2.circle(L, (int(x), int(y)), max(1, int(r)), float(a), -1, cv2.LINE_AA)
    return _blur(L, 0.8 * R.k)[..., None] * np.float32(col)
# ---------------- 史塔克：字从左到右显出来，边上长冰晶，飘雪，整个画面变冷
def frost(fr, text, u, R, x=960, y=540, px=130, dur=2.6):
    K = R.k; m, (xa, xb) = _text(text, px, R, x, y); yy, xx = _grid(R); key = ('frost', text, px, R.w, x, y)
    if key not in _C:
        r = np.random.default_rng(7); ys, xs = np.nonzero(cv2.Canny((m * 255).astype(np.uint8), 50, 150)); sp = np.zeros(m.shape, np.float32); s = K * px / 130
        for i in r.choice(len(xs), min(len(xs), 420), replace=False):
            an = r.uniform(0, math.tau); L = r.uniform(6, 30) * s; x1, y1 = xs[i] + math.cos(an) * L, ys[i] + math.sin(an) * L; cv2.line(sp, (int(xs[i]), int(ys[i])), (int(x1), int(y1)), float(r.uniform(.35, .8)), 1, cv2.LINE_AA)
            for k in (0.45, 0.7):
                for sg in (-1, 1): bx, by = xs[i] + math.cos(an) * L * k, ys[i] + math.sin(an) * L * k; cv2.line(sp, (int(bx), int(by)), (int(bx + math.cos(an + sg * 1.0) * L * 0.3), int(by + math.sin(an + sg * 1.0) * L * 0.3)), 0.6, 1, cv2.LINE_AA)
        dist = cv2.distanceTransform(((m < 0.5) * 255).astype(np.uint8), cv2.DIST_L2, 3) / (30 * s); _C[key] = (sp, dist, r.random((150, 5)).astype(np.float32))
    sp, dist, sn = _C[key]; fo = min(1.0, max(0.0, (dur - u) / 0.3)); rev = np.clip((u / 0.7 * 1.25 - (xx - xa) / (xb - xa)) * 5, 0, 1); grow = _ease((u - 0.15) / 1.5); a = m * rev * fo
    fr = fr * (1 - 0.40 * fo * _ease(u / 0.4)) * np.float32((0.86, 0.95, 1.08))
    fr = fr + _blur(m * rev, 24 * K)[..., None] * np.float32((0.22, 0.42, 0.85)) * 0.6 * fo + (sp * np.clip((grow * 1.3 - dist) * 4, 0, 1) * rev)[..., None] * np.float32((0.74, 0.88, 1.0)) * 0.6 * fo
    fr = fr * (1 - 0.8 * np.clip(_blur(m * rev, 3.5 * K) * 1.8, 0, 1) * fo)[..., None]
    col = _metal(m, R, y, px, (0.97, 0.99, 1.0), (0.50, 0.63, 0.82)); rime = np.clip(_noise(R, 3, 2.2) * 2.6 - 1.0, 0, 1) * np.clip((yy - (y + px * 0.05) * K) / (px * 0.4 * K), 0, 1) * grow; col = col + rime[..., None] * 0.5
    fr = fr * (1 - a[..., None]) + col * a[..., None]
    pts = [((p[0] * R.w + u * (40 + 60 * p[2]) * K + math.sin(u * 2 + p[4] * 9) * 12 * K) % R.w, (p[1] * R.h + u * (70 + 130 * p[3]) * K) % R.h, (1 + 2.2 * p[4]) * K, (0.35 + 0.6 * p[2]) * fo * min(1, u / 0.3)) for p in sn]
    return fr + _dots(R, pts, (0.9, 0.95, 1.0))
# ---------------- 兰尼斯特「听我怒吼」：字砸下来，画面一震，一圈冲击波推开
def roar(fr, text, u, R, x=960, y=540, px=170, dur=2.4, top=(1.0, 0.93, 0.62), bot=(0.86, 0.55, 0.14), ring=(1.0, 0.72, 0.28), heat=(1.0, 0.42, 0.10)):
    K = R.k; m, _ = _text(text, px, R, x, y); yy, xx = _grid(R); H, W = m.shape; cx, cy = x * K, y * K; fo = min(1.0, max(0.0, (dur - u) / 0.25)); hit = u - 0.16
    sc = 1 + 1.6 * (1 - _ease(u / 0.16)) ** 2; ms = cv2.warpAffine(m, cv2.getRotationMatrix2D((cx, cy), 0, sc), (W, H)) if sc > 1.002 else m; a = ms * min(1.0, u / 0.07) * fo
    if hit >= 0:
        amp = 30 * K * math.exp(-hit * 7)
        if amp > 0.4: fr = _shift(fr, amp * math.sin(u * 91), amp * math.cos(u * 77))
        st = math.exp(-hit * 3.0); d = np.hypot(xx - cx, (yy - cy) * 1.25) + 1e-3; band = np.exp(-((d - hit * 1900 * K) / (80 * K)) ** 2) * st
        if st > 0.04: fr = cv2.remap(fr, xx - (xx - cx) / d * band * 34 * K, yy - (yy - cy) / d * band * 34 * K, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fr = fr + band[..., None] * np.float32(ring) * 0.40 + np.float32(heat) * 0.38 * math.exp(-hit * 14); zs = math.exp(-hit * 4.5)
        if zs > 0.05:
            acc = np.zeros_like(m)
            for i in range(1, 7): acc += cv2.warpAffine(m, cv2.getRotationMatrix2D((cx, cy), 0, 1 + 0.05 * i * (1 + hit * 4)), (W, H))
            fr = fr + _blur(acc / 6, 3 * K)[..., None] * np.float32(heat) * 1.1 * zs
    fr = fr * (1 - 0.75 * np.clip(_shift(_blur(ms, 6 * K), 0, 5 * K) * 1.4, 0, 1) * min(1.0, u / 0.07) * fo)[..., None] + _blur(ms, 26 * K)[..., None] * np.float32(heat) * 0.35 * fo * min(1, u / 0.1)
    col = _metal(ms, R, y, px, top, bot, u, 0.55, 1.25); return fr * (1 - a[..., None]) + col * a[..., None]
# ---------------- 兰尼斯特「有债必还」：金字像铸出来一样从左到右显现，熔金往下滴，金币落下
def debt(fr, text, u, R, x=960, y=540, px=120, dur=2.8):
    K = R.k; m, (xa, xb) = _text(text, px, R, x, y); yy, xx = _grid(R); H, W = m.shape; key = ('debt', text, px, R.w, x, y)
    if key not in _C:
        r = np.random.default_rng(5); dr = []
        while len(dr) < 18:
            xc = int(r.uniform(xa, xb)); col = np.nonzero(m[:, min(W - 1, xc)] > 0.6)[0]
            if len(col): dr.append((xc, int(col.max()), r.uniform(0.25, 1.15) * px * K, (xc - xa) / (xb - xa) * 0.6 + r.uniform(0.2, 0.5), r.uniform(2.6, 5.5) * K))
        _C[key] = (dr, r.random((11, 5)).astype(np.float32))
    dr, cn = _C[key]; fo = min(1.0, max(0.0, (dur - u) / 0.3)); rev = np.clip((u / 0.7 * 1.25 - (xx - xa) / (xb - xa)) * 5, 0, 1); D = np.zeros(m.shape, np.float32)
    for (xc, y0, L, dl, th) in dr:
        p = _ease((u - dl) / 1.4)
        if p > 0: y1 = int(y0 + L * p); cv2.line(D, (xc, y0 - int(3 * K)), (xc, y1), 1.0, max(1, int(th)), cv2.LINE_AA); cv2.circle(D, (xc, y1), max(1, int(th * (0.9 + 0.5 * p))), 1.0, -1, cv2.LINE_AA)
    mm = np.maximum(m * rev, _blur(D, 0.7 * K)); a = mm * fo; edge = np.clip((u / 0.7 * 1.25 - (xx - xa) / (xb - xa)) * 5, 0, 1); hot = (edge * (1 - edge) * 4) * m      # 刚显出来的那一道是烧红的
    fr = fr * (1 - 0.30 * fo * _ease(u / 0.4)) + _blur(mm, 22 * K)[..., None] * np.float32((1.0, 0.55, 0.12)) * 0.45 * fo
    fr = fr * (1 - 0.7 * np.clip(_shift(_blur(mm, 5 * K), 0, 4 * K) * 1.4, 0, 1) * fo)[..., None]
    col = _metal(mm, R, y + px * 0.25, px * 1.6, (1.0, 0.92, 0.58), (0.80, 0.48, 0.10), u, 0.9, 1.7) + hot[..., None] * np.float32((1.0, 0.75, 0.4)); fr = fr * (1 - a[..., None]) + col * a[..., None]
    for p in cn:                                    # 金币：边落边翻
        t = u - 0.3 - p[0] * 1.3
        if t <= 0: continue
        px_, py_ = xa - 80 * K + p[1] * (xb - xa + 160 * K), (-0.05 + 0.10 * p[2]) * H + 0.5 * 2600 * K * t * t + 240 * K * t; rr = (20 + 12 * p[3]) * K; wv = abs(math.cos(t * (7 + 6 * p[4]) + p[4] * 6)); ax = (max(2, int(rr * (0.12 + 0.88 * wv))), int(rr))
        if py_ > H + rr: continue
        L = np.zeros((H, W), np.float32); cv2.ellipse(L, (int(px_), int(py_)), ax, 12 * (p[2] - 0.5) * 20, 0, 360, 1.0, -1, cv2.LINE_AA); I = np.zeros((H, W), np.float32); cv2.ellipse(I, (int(px_), int(py_)), (max(1, int(ax[0] * 0.68)), int(ax[1] * 0.68)), 12 * (p[2] - 0.5) * 20, 0, 360, 1.0, -1, cv2.LINE_AA)
        c_ = np.float32((0.78, 0.50, 0.12)) * (0.6 + 0.6 * wv) * (1 - I[..., None]) + np.float32((1.0, 0.86, 0.45)) * (0.55 + 0.6 * wv) * I[..., None]; fr = fr * (1 - L[..., None] * fo) + c_ * L[..., None] * fo
    return fr
# ---------------- 拜拉席恩「怒火燎原」：烧得发亮的金字，黑边，火从字后面窜起来，再沿地面往两边烧开
def fury(fr, text, u, R, x=960, y=540, px=130, dur=2.8):
    K = R.k; m, (xa, xb) = _text(text, px, R, x, y); yy, xx = _grid(R); H, W = m.shape; key = ('fury', R.w)
    if key not in _C: _C[key] = np.random.default_rng(9).random((140, 5)).astype(np.float32)
    em = _C[key]; fo = min(1.0, max(0.0, (dur - u) / 0.3)); ign = min(1.0, u / 0.35); spread = _ease((u - 0.3) / 1.6); yb = (y + px * 0.60) * K; half = (xb - xa) / 2 + spread * 760 * K
    bar = np.exp(-((yy - yb) / (3.5 * K)) ** 2) * np.clip((half - np.abs(xx - x * K)) / (40 * K), 0, 1) * np.clip(u / 0.3, 0, 1); src = np.maximum(m * ign, bar * 0.9)
    L = int(px * K * 0.95) | 1; up = _shift(cv2.blur(src, (int(7 * K) | 1, L)), 0, -L * 0.48) * 3.4 + _shift(cv2.blur(src, (int(5 * K) | 1, L // 3 | 1)), 0, -L * 0.15) * 2.0
    n = 0.6 * np.roll(_noise(R, 1, 9, 22), -int(u * 520 * K), 0) + 0.4 * np.roll(_noise(R, 2, 4, 10), -int(u * 900 * K), 0); fl = np.clip(up * (0.25 + 1.5 * n) - 0.34, 0, 1) * fo
    fr = fr * (1 - 0.35 * fo * _ease(u / 0.4)) + fl[..., None] * np.float32((1.0, 0.30, 0.03)) * 1.05 + (fl ** 2)[..., None] * np.float32((1.0, 0.72, 0.20)) * 0.95 + (fl ** 4)[..., None] * np.float32((1.0, 1.0, 0.75)) * 0.5
    fr = fr + _blur(src, 30 * K)[..., None] * np.float32((1.0, 0.36, 0.06)) * 0.5 * fo
    a = m * ign * fo; fk = 0.85 + 0.15 * math.sin(u * 23) * math.sin(u * 7.1); fr = fr * (1 - 0.9 * np.clip(_blur(cv2.dilate(m, np.ones((int(5 * K) | 1,) * 2, np.uint8)), 2.5 * K) * 1.6, 0, 1) * ign * fo)[..., None]
    col = _metal(m, R, y, px, (1.0, 0.96, 0.72), (1.0, 0.56, 0.12)) * fk; fr = fr * (1 - a[..., None]) + col * a[..., None]
    pts = [(x * K + (p[0] - 0.5) * 2 * half + math.sin(u * 3 + p[4] * 20) * 18 * K, yb - (((u * (0.35 + 0.5 * p[2]) + p[1]) % 1.0) * 520 * K), (1 + 1.6 * p[3]) * K, (1 - ((u * (0.35 + 0.5 * p[2]) + p[1]) % 1.0)) * fo * ign) for p in em]
    return fr + _dots(R, pts, (1.0, 0.62, 0.18))
# ---------------- 默认：家族色的字 + 圆章
def plain(fr, text, house, u, R, x=960, y=540, px=110, dur=2.4):
    K = R.k; P = HR.HOUSES[house]; m, (xa, xb) = _text(text, px, R, x, y); fo = min(1.0, max(0.0, (dur - u) / 0.3)) * min(1.0, u / 0.2); a = (m * fo)[..., None]; c0 = np.float32(HR.hx(P['sub'])); c1 = np.float32(HR.hx(P['main']))
    lo = c1 / max(0.5, float(c1.max())); hi = np.float32((0.97, 0.95, 0.92))
    fr = fr * (1 - 0.30 * fo) + _blur(m, 22 * K)[..., None] * lo * 0.8 * fo; fr = fr * (1 - 0.7 * np.clip(_shift(_blur(m, 5 * K), 0, 4 * K) * 1.4, 0, 1) * fo)[..., None]
    fr = fr * (1 - a) + _metal(m, R, y, px, hi, hi * 0.45 + lo * 0.55, u) * a; s = int(px * 1.5 * K); rgb, al = HR.sigil(house, s, 'round'); HR.put(fr, rgb, al, xa - s * 0.75, y * K, fo); return fr
FX = dict(stark=frost, lannister=roar, baratheon=fury, stannis=fury)
def motto(fr, text, house, u, R, fx=None, **kw):
    f = dict(frost=frost, roar=roar, debt=debt, fury=fury).get(fx) or FX.get(house)
    return f(fr, text, u, R, **kw) if f else plain(fr, text, house, u, R, **kw)
def nametag(fr, name, house, u, R, x=300, y=900, px=46, dur=2.4):
    """人物出场名牌：小圆章 + 名字 + 一道家族色的下划线从左划出来。(x, y) 是圆章中心。"""
    K = R.k; P = HR.HOUSES[house]; fo = min(1.0, max(0.0, (dur - u) / 0.25)); k = _ease(u / 0.25) * fo; s = int(px * 1.9 * K); rgb, al = HR.sigil(house, s, 'round'); HR.put(fr, rgb, al, x * K, y * K, k)
    f = ImageFont.truetype(FONT, max(8, int(px * K))); w = int(f.getlength(name)); key = ('nt', name, px, R.w)
    if key not in _C: im = Image.new('L', (w + 8, int(px * K * 1.6)), 0); ImageDraw.Draw(im).text((4, im.size[1] / 2), name, font=f, fill=255, anchor='lm'); _C[key] = np.asarray(im, np.float32) / 255
    m = _C[key]; h = m.shape[0]; x0, y0 = int(x * K + s * 0.62), int(y * K - h / 2 - px * K * 0.10); x1, y1 = min(R.w, x0 + m.shape[1]), min(R.h, y0 + h)
    if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0: return fr
    mm = m[:y1 - y0, :x1 - x0]; sh = np.clip(_blur(mm, 3 * K) * 1.5, 0, 1); reg = fr[y0:y1, x0:x1]; reg *= (1 - 0.8 * sh * k)[..., None]; reg *= (1 - mm * k)[..., None]; reg += (mm * k)[..., None] * np.float32((0.96, 0.94, 0.90))
    c = np.float32(HR.hx(P['main'])); c = c / max(0.45, c.max()) * 0.9; ww = int(m.shape[1] * _ease(u / 0.45)); yb = y1 - int(px * K * 0.16); fr[yb:yb + max(2, int(3 * K)), x0:min(R.w, x0 + ww)] = np.clip(c, 0, 1) * fo + fr[yb:yb + max(2, int(3 * K)), x0:min(R.w, x0 + ww)] * (1 - fo)
    return fr
if __name__ == '__main__':
    import subprocess
    from stage import Out
    R = Out(1920, 1080) if os.environ.get('RES') == '1080' else Out(960, 540); os.makedirs('out', exist_ok=True)
    SEQ = [('stark', '凛冬将至', None, 150, '艾德·史塔克'), ('lannister', '听我怒吼', None, 190, '泰温·兰尼斯特'), ('lannister', '兰尼斯特有债必还', 'debt', 120, '提利昂·兰尼斯特'), ('baratheon', '怒火燎原', None, 150, '劳勃·拜拉席恩'), ('tully', '家族，责任，荣誉', None, 100, '凯特琳·徒利')]
    D = 2.8; yy, xx = _grid(R); vig = np.clip(1.15 - np.hypot((xx - R.w / 2) / R.w, (yy - R.h / 2) / R.h) * 1.5, 0.15, 1)[..., None]
    def bg(h):
        if ('bg', h, R.w) not in _C:
            b = np.zeros((R.h, R.w, 3), np.float32) + np.float32((0.050, 0.045, 0.055)); s = int(R.h * 0.86); rgb, al = HR.sigil(h, s); HR.put(b, rgb * 0.30, al, R.w / 2, R.h / 2); _C[('bg', h, R.w)] = (b + _blur(b, 30 * R.k) * 0.5) * vig
        return _C[('bg', h, R.w)]
    def frame(t):
        i = min(len(SEQ) - 1, int(t / D)); u = t - i * D; h, s, fx, px, nm = SEQ[i]; fr = bg(h).copy(); fr = motto(fr, s, h, u, R, fx=fx, px=px, dur=D - 0.1, y=500); return nametag(fr, nm, h, u, R, 150, 960, dur=D - 0.1)
    if len(sys.argv) > 1 and sys.argv[1] == 'sheet':
        ts = [i * D + k for i in range(len(SEQ)) for k in (0.25, 0.9, 1.9)]; ims = [cv2.resize(np.clip(frame(t), 0, 1), (640, 360), interpolation=cv2.INTER_AREA) for t in ts]
        cv2.imwrite('out/_housefx.jpg', (np.vstack([np.hstack(ims[i:i + 3]) for i in range(0, len(ims), 3)])[..., ::-1] * 255).astype(np.uint8)); print('out/_housefx.jpg')
    else:
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{R.w}x{R.h}', '-r', '30', '-i', '-', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', f'out/_housefx_{R.h}p.mp4'], stdin=subprocess.PIPE)
        for i in range(int(D * len(SEQ) * 30)): p.stdin.write((np.clip(frame(i / 30), 0, 1) * 255).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait(); print(f'out/_housefx_{R.h}p.mp4')
