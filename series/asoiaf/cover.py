"""cover — 冰火系列的封面模板，每集版式一样：主角的彩窗像，集数 / 人物名 / 那一句问题，字后面是压暗的大家徽，四周家族色边框。
    cover('stark', '奈德·史塔克', ['最重荣誉的人，', '为什么第一个死？'], 1, (glass, mask), 'out/cover.jpg')    # (glass, mask) = engine/glass.window(...) 画的主角彩窗，600×940
    cover(..., 'out/cover_4x3.jpg', shape='4:3')    # 画幅：'16:9' 1920×1080（默认）、'4:3' 1440×1080、'3:4' 1080×1440（彩窗在上、字在下居中）。抖音要 4:3 和 3:4 两张
各集在自己目录里写一个 mkcover.py 调它（见 ep01_ned/mkcover.py）。字的位置和大小不要改，要改就全系列一起改。"""
import math, os, sys, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'engine'))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from paper import FONT
import glass as G, heraldry as HR
# 每种画幅：画布、彩窗（缩放, x, y）、家徽（边长, 中心）、字（左对齐的 x 或居中的 x、字最宽多少、系列名/人名/短横线/第一行问题的 y、问题行距）
SHAPES = {'16:9': dict(W=1920, H=1080, win=(1.0, 150, 70), sig=(940, 1380, 540), glow=(1300, 520), X=880, mid=False, maxw=960, y=(132, 230, 432, 500), dy=128),
          '4:3': dict(W=1440, H=1080, win=(0.86, 78, 136), sig=(800, 1030, 540), glow=(1000, 520), X=648, mid=False, maxw=716, y=(252, 334, 524, 588), dy=116),
          '3:4': dict(W=1080, H=1440, win=(0.74, 318, 146), sig=(640, 540, 1084), glow=(540, 1120), X=540, mid=True, maxw=860, y=(70, 862, 1066, 1112), dy=114)}
def _w(s, px, sp=0): f = ImageFont.truetype(FONT, px); return sum(f.getlength(ch) + sp for ch in s) - sp
def _fit(s, px, sp, maxw):
    while _w(s, px, sp) > maxw: px -= 2
    return px
def _txt(im, xy, s, px, fill, sp=0, shadow=10):
    """带投影的字，返回右边界 x。"""
    f = ImageFont.truetype(FONT, px); x, y = xy; sh = Image.new('L', im.size, 0); d = ImageDraw.Draw(sh); cx = x
    for ch in s: d.text((cx, y), ch, font=f, fill=255); cx += f.getlength(ch) + sp
    dark = Image.new('RGB', im.size, (0, 0, 0)); im.paste(dark, (0, int(px * 0.05)), sh.filter(ImageFilter.GaussianBlur(shadow)).point(lambda v: min(255, int(v * 1.6))))
    if isinstance(fill, tuple) and isinstance(fill[0], tuple):                         # 上下渐变
        g = np.linspace(0, 1, im.size[1], dtype=np.float32)[:, None, None]; y0, y1 = y + px * 0.15, y + px * 1.15; g = np.clip((np.arange(im.size[1], dtype=np.float32)[:, None, None] - y0) / (y1 - y0), 0, 1)
        col = Image.fromarray((np.broadcast_to(np.float32(fill[0]) * (1 - g) + np.float32(fill[1]) * g, (im.size[1], im.size[0], 3))).astype(np.uint8)); im.paste(col, (0, 0), sh)
    else: im.paste(Image.new('RGB', im.size, fill), (0, 0), sh)
    return cx
def cover(house, name, question, ep, window, out, series='权力的游戏', shape='16:9'):
    L = SHAPES[shape]; W, H = L['W'], L['H']; P = HR.HOUSES[house]; main = np.float32(HR.hx(P['main'])); sub = np.float32(HR.hx(P['sub'])); tint = main / max(0.5, float(main.max())); g, m = window
    k, wx, wy = L['win']
    if k != 1: g = cv2.resize(g, None, fx=k, fy=k, interpolation=cv2.INTER_AREA); m = cv2.resize(m, None, fx=k, fy=k, interpolation=cv2.INTER_AREA).reshape(g.shape[0], g.shape[1], 1)
    fr, M = G.wall([(g, m, wx, wy)], W, H, bloom=0.42); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); gx, gy = L['glow']
    fr = fr + (np.exp(-np.hypot(xx - gx, (yy - gy) * 1.4) / 620) * 0.10)[..., None] * tint * (1 - M)                    # 字那一边一点家族色的底光
    n, sx, sy = L['sig']; sr, sa = HR.sigil(house, n); x0, y0 = sx - n // 2, sy - n // 2; sa = sa * (1 - M[y0:y0 + n, x0:x0 + n]); reg = fr[y0:y0 + n, x0:x0 + n]; reg[:] = reg * (1 - 0.9 * sa) + sr * sa * 0.24   # 字后面压暗的大家徽，不盖彩窗
    fr = fr * np.clip(1.12 - np.hypot((xx - W / 2) / W, (yy - H / 2) / H) * 0.9, 0.35, 1)[..., None]
    b = np.zeros((H, W), np.float32)                                                    # 边框：外粗内细两道线，四角各一枚菱形
    cv2.rectangle(b, (28, 28), (W - 29, H - 29), 1.0, 6); cv2.rectangle(b, (46, 46), (W - 47, H - 47), 0.8, 2)
    for (cx, cy) in ((37, 37), (W - 38, 37), (37, H - 38), (W - 38, H - 38)): cv2.fillConvexPoly(b, np.int32([(cx - 22, cy), (cx, cy - 22), (cx + 22, cy), (cx, cy + 22)]), 1.0)
    edge = np.float32(HR.hx(P['sub'] if float(sub.max()) > float(main.max()) or house == 'lannister' else P['main'])); edge = edge / max(0.6, float(edge.max())); fr = fr * (1 - b[..., None]) + b[..., None] * edge * 0.92
    im = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8)); tc = tuple(int(v * 255) for v in np.clip(tint * 0.75 + 0.25, 0, 1)); y1, y2, yr, y3 = L['y']; eps = f'{ep:02d}'
    at = (lambda w: int(L['X'] - w / 2)) if L['mid'] else (lambda w: L['X'])            # 居中的画幅每行按自己的宽度居中
    X = at(_w(series, 44, 6) + 6 + 50 + _w(eps, 54, 4)); x1 = _txt(im, (X, y1), series, 44, (214, 206, 190), sp=6); ImageDraw.Draw(im).rectangle((x1 + 22, y1 + 18, x1 + 26, y1 + 58), fill=tc); _txt(im, (x1 + 50, y1 - 6), eps, 54, tc, sp=4)
    px = _fit(name, 150, 4, L['maxw']); X = at(_w(name, px, 4)); _txt(im, (X - (0 if L['mid'] else 6), y2), name, px, ((252, 248, 238), (200, 196, 188)), sp=4, shadow=14)
    X = at(150); ImageDraw.Draw(im).rectangle((X, yr, X + 150, yr + 6), fill=tc)
    px = min(_fit(q, 96, 2, L['maxw']) for q in question)
    for i, q in enumerate(question): _txt(im, (at(_w(q, px, 2)), y3 + i * L['dy']), q, px, ((255, 226, 150), (226, 150, 52)), sp=2, shadow=12)
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True); im.save(out, quality=94); return out
