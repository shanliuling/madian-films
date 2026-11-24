"""cover — 冰火系列的封面模板，每集版式一样：左边主角的彩窗像，右边集数 / 人物名 / 那一句问题，右下家徽和箴言，四周家族色边框。
    cover('stark', '奈德·史塔克', ['最重荣誉的人，', '为什么第一个死？'], 1, (glass, mask), 'out/cover.jpg')    # (glass, mask) = engine/glass.window(...) 画的主角彩窗，600×940
各集在自己目录里写一个 mkcover.py 调它（见 ep01_ned/mkcover.py）。字的位置和大小不要改，要改就全系列一起改。"""
import math, os, sys, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'engine'))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from paper import FONT
import glass as G, heraldry as HR
W, H = 1920, 1080
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
def cover(house, name, question, ep, window, out, series='冰与火之歌'):
    P = HR.HOUSES[house]; main = np.float32(HR.hx(P['main'])); sub = np.float32(HR.hx(P['sub'])); tint = main / max(0.5, float(main.max())); g, m = window
    fr, M = G.wall([(g, m, 150, 70)], bloom=0.42); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    fr = fr + (np.exp(-np.hypot(xx - 1300, (yy - 520) * 1.4) / 620) * 0.10)[..., None] * tint * (1 - M)                  # 右半边一点家族色的底光
    big = cv2.resize(HR.charge(house, 512), (900, 900)); reg = fr[90:990, 960:1860]; reg += (big * 0.045)[..., None] * tint                         # 字后面很淡的大徽
    fr = fr * np.clip(1.12 - np.hypot((xx - W / 2) / W, (yy - H / 2) / H) * 0.9, 0.35, 1)[..., None]
    b = np.zeros((H, W), np.float32)                                                    # 边框：外粗内细两道线，四角各一枚菱形
    cv2.rectangle(b, (28, 28), (W - 29, H - 29), 1.0, 6); cv2.rectangle(b, (46, 46), (W - 47, H - 47), 0.8, 2)
    for (cx, cy) in ((37, 37), (W - 38, 37), (37, H - 38), (W - 38, H - 38)): cv2.fillConvexPoly(b, np.int32([(cx - 22, cy), (cx, cy - 22), (cx + 22, cy), (cx, cy + 22)]), 1.0)
    edge = np.float32(HR.hx(P['sub'] if float(sub.max()) > float(main.max()) or house == 'lannister' else P['main'])); edge = edge / max(0.6, float(edge.max())); fr = fr * (1 - b[..., None]) + b[..., None] * edge * 0.92
    s = 250; rgb, al = HR.sigil(house, s); HR.put(fr, rgb, al, 1700, 850)
    im = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8)); X = 880; tc = tuple(int(v * 255) for v in np.clip(tint * 0.75 + 0.25, 0, 1))
    x1 = _txt(im, (X, 132), f'{series}', 44, (214, 206, 190), sp=6); d = ImageDraw.Draw(im); d.rectangle((x1 + 22, 150, x1 + 26, 190), fill=tc); _txt(im, (x1 + 50, 126), f'{ep:02d}', 54, tc, sp=4)
    _txt(im, (X - 6, 230), name, 150, ((252, 248, 238), (200, 196, 188)), sp=4, shadow=14); ImageDraw.Draw(im).rectangle((X, 432, X + 150, 438), fill=tc)
    for i, q in enumerate(question): _txt(im, (X, 500 + i * 128), q, 96, ((255, 226, 150), (226, 150, 52)), sp=2, shadow=12)
    if P['motto']: f = ImageFont.truetype(FONT, 38); w = sum(f.getlength(ch) + 10 for ch in P['motto']); _txt(im, (int(1700 - 140 - w), 880), P['motto'], 38, tc, sp=10)
    _txt(im, (X, 930), '码点小人', 40, (214, 206, 190), sp=8); os.makedirs(os.path.dirname(out) or '.', exist_ok=True); im.save(out, quality=94); return out
