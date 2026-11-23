"""westeros — 维斯特洛地图：海岸线、河流、湖泊取自一张参考图提取的 mask（map/*.png），画法是自己的：羊皮纸陆地 + 墨线山 + 蓝灰海 + 自排地名。
    tex = texture()                         # uint8 RGB，参考图像素 ×SC
    fr, proj = pview(tex, cx, cy, span, tilt, R)     # cx,cy,span 是贴图像素；proj((x,y) 贴图像素) → 屏幕像素
    XY('kl') 或 XY((显示坐标x, y)) → 贴图像素。地点坐标是我从参考图上读的（参考图 764 宽显示坐标）。"""
import math, os, numpy as np, cv2, cairo
from PIL import Image, ImageDraw, ImageFont
from paper import layer, rgba, FONT
SC = 2; DS = 1652 / 764 * SC                                                              # 显示坐标 → 贴图像素
PLACE = dict(winterfell=(362, 470), kl=(462, 1108), eyrie=(527, 876), riverrun=(313, 940), rock=(140, 1052), storm=(580, 1213), highgarden=(218, 1268), sunspear=(630, 1462), whiteharbor=(432, 606), castleblack=(443, 243),
             pyke=(135, 880), twins=(325, 800), trident=(420, 905), harrenhal=(428, 955), oldtown=(135, 1385), joy=(340, 1325), dragonstone=(700, 1030))
NAME = dict(winterfell='临冬城', kl='君临', eyrie='鹰巢城', riverrun='奔流城', rock='凯岩城', storm='风息堡', highgarden='高庭', sunspear='阳戟城', whiteharbor='白港', castleblack='黑城堡', pyke='派克', twins='孪河城', harrenhal='赫伦堡', oldtown='旧镇', joy='极乐塔', dragonstone='龙石岛', trident='三叉戟河')
KINGSROAD = [(443, 243), (420, 330), (362, 470), (352, 600), (345, 720), (372, 820), (420, 905), (440, 1000), (462, 1108)]
RANGES = [([(500, 790), (540, 830), (575, 870), (600, 905)], 1.0, 34), ([(470, 850), (510, 900)], 0.6, 20), ([(160, 950), (200, 1000), (235, 1050)], 0.6, 26), ([(250, 1330), (330, 1345), (400, 1310), (430, 1290)], 0.9, 30), ([(330, 1380), (400, 1400)], 0.5, 20),
          ([(335, 290), (370, 340), (400, 400)], 0.8, 28), ([(440, 400), (490, 440)], 0.5, 18), ([(300, 110), (350, 160), (395, 210)], 0.9, 30)]
FOREST = [((285, 450), 44, 26), ((505, 1150), 34, 22), ((560, 1290), 30, 20), ((400, 130), 40, 22), ((215, 1140), 22, 14)]
REGION = [('北 境', (300, 540), 120), ('河 间 地', (370, 960), 70), ('谷 地', (560, 930), 64), ('西 境', (190, 1010), 64), ('王 领', (470, 1060), 50), ('风 暴 地', (520, 1250), 64), ('河 湾 地', (300, 1200), 84), ('多 恩', (480, 1440), 96), ('塞 外', (250, 120), 84)]
def XY(p): p = PLACE[p] if isinstance(p, str) else p; return (p[0] * DS, p[1] * DS)
def smoothline(pts, n=12):
    P = np.float32(pts); out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(len(P) - 1, i + 2)]
        for k in range(n): t = k / n; out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1]); return np.float32(out)
MAPDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'map')
def texture(cache='out/_westeros.png'):
    os.makedirs(os.path.dirname(cache) or '.', exist_ok=True)
    if os.path.exists(cache): return cv2.cvtColor(cv2.imread(cache), cv2.COLOR_BGR2RGB)
    r = np.random.default_rng(3); L0 = cv2.imread(os.path.join(MAPDIR, 'land.png'), 0); h0, w0 = L0.shape; W, H = w0 * SC, h0 * SC
    up = lambda m, s=2.5: (cv2.GaussianBlur(cv2.resize(m.astype(np.float32) / 255, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), s))
    land = np.clip((up(L0) - 0.5) * 6 + 0.5, 0, 1); lk = cv2.imread(os.path.join(MAPDIR, 'lakes.png'), 0); n, lab, st, _ = cv2.connectedComponentsWithStats((lk > 0).astype(np.uint8), 8)
    for i in range(1, n):
        if st[i, 4] / (st[i, 2] * st[i, 3]) > 0.8: lk[lab == i] = 0                        # 去掉被误当成湖的地名框
    water = np.clip(np.maximum((up(lk, 1.5) - 0.5) * 6 + 0.5, up(cv2.dilate(cv2.imread(os.path.join(MAPDIR, 'rivers.png'), 0), np.ones((2, 2), np.uint8)), 1.2) * 2.2), 0, 1) * land
    def nz(s): a = cv2.GaussianBlur(r.random((H // 4, W // 4)).astype(np.float32), (0, 0), s / 4); a = cv2.resize(a, (W, H)); return (a - a.mean()) / (a.std() + 1e-6)
    paper = np.float32((0.86, 0.78, 0.60)) * (1 + 0.05 * nz(90) + 0.035 * nz(14) + 0.02 * nz(3))[..., None]; paper = paper * np.float32((1.0, 0.985, 0.96)) ** np.clip(nz(160), -2, 2)[..., None]
    el = np.zeros((H, W), np.float32)
    for (pts, hh, ww) in RANGES: k = np.zeros((H // 4, W // 4), np.float32); cv2.polylines(k, [np.int32(smoothline([XY(p) for p in pts]) / 4)], False, 1.0, int(ww * DS / 4), cv2.LINE_AA); k = cv2.resize(cv2.GaussianBlur(k, (0, 0), ww * DS / 10), (W, H)); el = np.maximum(el, k / (k.max() + 1e-6) * hh)
    rid = np.clip(1 - np.abs(nz(10)) * 0.9, 0, 1) ** 1.5; elev = el * (0.4 + 0.9 * rid); gy, gx = np.gradient(cv2.GaussianBlur(elev, (0, 0), 1.5) * 90); shade = np.clip(0.5 + (gx + gy) * 0.55, 0, 1.3)
    img = paper * (1 - 0.55 * el[..., None] * (1 - np.clip(shade, 0, 1))[..., None]) + np.float32((0.10, 0.09, 0.06)) * (el * np.clip(shade - 0.75, 0, 1) * 0.6)[..., None]
    lb = (land > 0.5).astype(np.uint8); dl = cv2.distanceTransform(lb, cv2.DIST_L2, 5); ds = cv2.distanceTransform(1 - lb, cv2.DIST_L2, 5)
    img = img * (1 - 0.22 * np.exp(-dl / 14))[..., None]                                    # 岸边一圈压深
    sea = np.float32((0.30, 0.41, 0.48)) * (1 + 0.10 * nz(120) + 0.04 * nz(10))[..., None] * (1 - 0.25 * np.exp(-ds / 60))[..., None]
    for d0 in (16, 34, 56): sea = sea + (np.clip(1 - np.abs(ds - d0) / 1.6, 0, 1) * 0.10 * math.exp(-d0 / 60))[..., None] * np.float32((0.8, 0.9, 1.0))
    wc = np.float32((0.34, 0.45, 0.52)); img = img * (1 - water[..., None]) + wc * water[..., None]; img = img * land[..., None] + sea * (1 - land[..., None])
    ink = np.clip(1 - np.abs(dl - 1.2) / 2.2, 0, 1) * (lb > 0); img = img * (1 - 0.8 * ink[..., None]) + np.float32((0.16, 0.12, 0.08)) * 0.8 * ink[..., None]
    s, c = layer(W, H); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND); INKC = (0.20, 0.14, 0.09)
    for (pts, hh, ww) in RANGES:                                                            # 墨线山形
        q = smoothline([XY(p) for p in pts], 10); nn = int(len(q) * ww / 20)
        for i in range(nn):
            x, y = q[r.integers(0, len(q))] + r.normal(0, ww * DS * 0.22, 2); k = r.uniform(16, 30) * (0.7 + 0.5 * hh)
            if not lb[min(H - 1, max(0, int(y))), min(W - 1, max(0, int(x)))]: continue
            c.set_source_rgba(0.93, 0.88, 0.76, 0.95); c.move_to(x - k, y + k * 0.55); c.line_to(x, y - k * 0.75); c.line_to(x + k * 0.9, y + k * 0.55); c.close_path(); c.fill()
            c.set_source_rgba(*INKC, 0.55); c.move_to(x, y - k * 0.75); c.line_to(x + k * 0.9, y + k * 0.55); c.line_to(x + k * 0.25, y + k * 0.55); c.close_path(); c.fill()
            c.set_source_rgba(*INKC, 0.9); c.set_line_width(2.6); c.move_to(x - k, y + k * 0.55); c.line_to(x, y - k * 0.75); c.line_to(x + k * 0.9, y + k * 0.55); c.stroke()
    for (p, a, b) in FOREST:                                                                # 森林
        for i in range(int(a * b * 0.9)):
            x, y = XY((p[0] + r.normal(0, a * 0.45), p[1] + r.normal(0, b * 0.45))); k = r.uniform(7, 11)
            if not lb[min(H - 1, max(0, int(y))), min(W - 1, max(0, int(x)))]: continue
            c.set_source_rgba(0.30, 0.36, 0.22, 0.9); c.arc(x, y, k, 0, math.tau); c.fill(); c.set_source_rgba(*INKC, 0.7); c.set_line_width(1.8); c.arc(x, y, k, 0.3, 3.6); c.stroke(); c.move_to(x, y + k); c.line_to(x, y + k * 1.7); c.stroke()
    q = smoothline([XY(p) for p in KINGSROAD], 12); c.set_source_rgba(0.62, 0.22, 0.14, 0.8); c.set_line_width(4.5); c.set_dash([18, 10]); c.move_to(*q[0]); [c.line_to(*p) for p in q[1:]]; c.stroke(); c.set_dash([])
    x0, y0 = XY((350, 262)); x1, y1 = XY((520, 232)); c.set_source_rgba(0.95, 0.97, 1.0, 0.95); c.set_line_width(13); c.move_to(x0, y0); c.line_to(x1, y1); c.stroke(); c.set_source_rgba(*INKC, 0.9); c.set_line_width(2.5)   # 长城
    for d in (-7, 7): c.move_to(x0, y0 + d); c.line_to(x1, y1 + d); c.stroke()
    for k, p in PLACE.items():
        if k in ('trident',): continue
        x, y = XY(p); c.set_source_rgb(0.93, 0.88, 0.76); c.arc(x, y, 11, 0, math.tau); c.fill(); c.set_source_rgb(0.62, 0.16, 0.10); c.set_line_width(4); c.arc(x, y, 11, 0, math.tau); c.stroke(); c.arc(x, y, 4, 0, math.tau); c.fill()
    rgb, al = rgba(s); img = img * (1 - al) + rgb; im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA'); ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for (name, p, px) in REGION: d.text(XY(p), name, font=ImageFont.truetype(FONT, px), fill=(90, 60, 36, 90), anchor='mm')
    f = ImageFont.truetype(FONT, 40)
    for k, p in PLACE.items():
        x, y = XY(p); t = NAME[k]; w = d.textlength(t, font=f); bx = x + 22; by = y - 26
        if k in ('winterfell', 'kl', 'eyrie', 'riverrun', 'rock', 'storm', 'highgarden', 'sunspear', 'joy', 'castleblack'): d.rectangle((bx - 8, by - 4, bx + w + 8, by + 54), fill=(238, 226, 196, 235), outline=(60, 42, 26, 255), width=3)
        d.text((bx, by), t, font=f, fill=(48, 32, 20, 255))
    a = np.asarray(Image.alpha_composite(im, ov).convert('RGB')); cv2.imwrite(cache, cv2.cvtColor(a, cv2.COLOR_RGB2BGR)); return a
def pview(tex, cx, cy, span, tilt, R, lamp=None, dark=0.30):
    """看向正北的倾斜镜头；lamp=(贴图像素 x, y, 半径) 时做成「桌上的地图被提灯照亮」，其余压暗。"""
    wn = span / 2; wf = wn * (1 + tilt); d = span * R.h / R.w * (1 + 1.6 * tilt); yn = cy + d * 0.42; yf = cy - d * 0.58
    Hm = cv2.getPerspectiveTransform(np.float32([(cx - wf, yf), (cx + wf, yf), (cx + wn, yn), (cx - wn, yn)]), np.float32([(0, 0), (R.w, 0), (R.w, R.h), (0, R.h)]))
    fr = cv2.warpPerspective(tex, Hm, (R.w, R.h), flags=cv2.INTER_AREA if span > R.w * 1.5 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(70, 96, 112)).astype(np.float32) / 255
    def proj(p): q = cv2.perspectiveTransform(np.float32([[p]]), Hm)[0, 0]; return (float(q[0]), float(q[1]))
    if lamp is not None:
        lx, ly = proj(lamp[:2]); rad = lamp[2] / span * R.w; yy, xx = np.mgrid[0:R.h, 0:R.w].astype(np.float32); g = np.exp(-(((xx - lx) / rad) ** 2 + ((yy - ly) / (rad * 0.8)) ** 2)); fr = fr * (dark + (1.15 - dark) * g[..., None]) * (np.float32((0.80, 0.86, 1.0)) * (1 - g[..., None]) + np.float32((1.0, 0.93, 0.80)) * g[..., None])
    return fr, proj
if __name__ == '__main__':
    from stage import Out
    R = Out(960, 540); tex = texture(); print(tex.shape); H, W = tex.shape[:2]
    a, _ = pview(tex, W / 2, H * 0.55, H * 0.92 * 16 / 9, 0.0, R); c = XY((420, 905)); b, _ = pview(tex, c[0], c[1], 2400, 0.45, R, lamp=(c[0], c[1], 1100)); c = XY('winterfell'); c2, _ = pview(tex, c[0], c[1], 1500, 0.5, R, lamp=(c[0], c[1], 700))
    Image.fromarray((np.clip(np.hstack([a, b, c2]), 0, 1) * 255).astype(np.uint8)).save('out/_westeros_test.jpg', quality=90)
