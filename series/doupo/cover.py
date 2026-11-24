"""cover — 斗破系列的封面模板。每集在自己目录里写一个 mkcover.py 调 cover()（见 ep01_xiaoyan/mkcover.py）。
版式：墨黑的底，一条斜线切开，一边是这个人的本命火，人物出招的定格压在火上、可以越过斜线；另一边是字，自上而下：
「人物志 | 集数」、毛笔人名、一道火色短线、那一句问题。不加边框，不写原作名，不写「码点小人」，不加水印。
只出抖音要的两张：4:3（1440×1080，人在右、字在左）、3:4（1080×1440，人放大占满画面，字居中压在他下半身上，底边留一成空）。字的位置和大小不要改，要改就全系列一起改。"""
import math, os, types, numpy as np, cairo
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from paper import layer, rgba, FONT
import action as A, fx
from action import rnd
# 每种画幅：画布、斜线两端（火在线的右/上那一边）、人物（脚的 x、y、缩放）、字（左对齐的 x 或居中的 x、最宽、系列行/人名/短线/第一行问题的 y、人名字号）
SHAPES = {'4:3': dict(W=1440, H=1080, cut=((760, 0), (560, 1080)), fig=(1060, 1030, 1.30), X=84, mid=False, maxw=670, y=(240, 314, 648, 694), name=290),
          '3:4': dict(W=1080, H=1440, cut=((0, 800), (1080, 640)), fig=(540, 990, 1.50), X=540, mid=True, maxw=880, y=(722, 784, 1056, 1090), name=230)}
def _w(s, px, sp=0, font=FONT): f = ImageFont.truetype(font, px); return sum(f.getlength(ch) + sp for ch in s) - sp
def _fit(s, px, sp, maxw, font=FONT):
    while _w(s, px, sp, font) > maxw: px -= 2
    return px
def _txt(im, xy, s, px, fill, sp=0, shadow=10, font=FONT):
    """带投影的字（fill 是一个颜色，或 (上, 下) 两个颜色的渐变），返回右边界 x。"""
    f = ImageFont.truetype(font, px); x, y = xy; sh = Image.new('L', im.size, 0); d = ImageDraw.Draw(sh); cx = x
    for ch in s: d.text((cx, y), ch, font=f, fill=255); cx += f.getlength(ch) + sp
    im.paste(Image.new('RGB', im.size, (0, 0, 0)), (0, int(px * 0.05)), sh.filter(ImageFilter.GaussianBlur(shadow)).point(lambda v: min(255, int(v * 1.8))))
    if isinstance(fill[0], tuple):
        g = np.clip((np.arange(im.size[1], dtype=np.float32)[:, None, None] - (y + px * 0.15)) / px, 0, 1)
        im.paste(Image.fromarray(np.broadcast_to(np.float32(fill[0]) * (1 - g) + np.float32(fill[1]) * g, (im.size[1], im.size[0], 3)).astype(np.uint8)), (0, 0), sh)
    else: im.paste(Image.new('RGB', im.size, fill), (0, 0), sh)
    return cx

def cover(name, question, ep, fire, figure, out, shape='4:3', series='人物志', part='', t=3.0):
    """name 人名；question 一两行问题；ep 集数；part 分上下集时写 '上' / '下'；fire 本命火色（0–1）。
    figure(c, t, glow) 画人物：原点在脚下正中，单位是场景坐标；glow=True 时只画会发光的部分。"""
    L = SHAPES[shape]; W, H = L['W'], L['H']; R = types.SimpleNamespace(w=W, h=H, k=1.0); fr = np.zeros((H, W, 3), np.float32); fr[:] = (0.035, 0.032, 0.05); (ax, ay), (bx, by) = L['cut']; fxp, fyp, fs = L['fig']
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); ln = math.hypot(bx - ax, by - ay); dl = ((xx - ax) * (by - ay) - (yy - ay) * (bx - ax)) / ln; dl = -dl                          # >0：字那一边，离斜线多远
    def place(c): c.translate(fxp, fyp); c.scale(fs, fs)
    s, c = layer(W, H); g = cairo.RadialGradient(fxp, fyp - 330 * fs, 30, fxp, fyp - 330 * fs, max(W, H) * 0.85)                                                            # 火那一边
    g.add_color_stop_rgb(0, *[0.35 + 0.6 * v for v in fire]); g.add_color_stop_rgb(0.2, *[0.62 * v for v in fire]); g.add_color_stop_rgb(0.6, *[0.26 * v for v in fire]); g.add_color_stop_rgb(1, *[0.08 * v for v in fire]); c.set_source(g); c.paint(); rgb, al = rgba(s); fr = rgb
    s, c = layer(W, H); A.flame(c, t, lambda dt, sv: (W * sv, H + 30) if not L['mid'] else (W * sv, by + 60), 150, 1.3, H * 0.8, 150, fire, a=0.35, seed=3, wob=40)
    A.flame(c, t, lambda dt, sv: (ax + (bx - ax) * sv, ay + (by - ay) * sv), 110, 0.7, 240, 50, fire, a=0.8, seed=5, wob=20)                                            # 沿着斜线的一排火舌
    for i in range(110): c.new_path(); c.arc(W * rnd(i, 1), H * rnd(i, 2), 2 + 5 * rnd(i, 3), 0, 7); c.set_source_rgba(*[0.6 + 0.4 * v for v in fire], 0.25 + 0.6 * rnd(i, 4)); c.fill()
    fr = A.add_glow(fr, s, 14, 0.8); fr = fr * (1 - 0.90 * np.clip(dl / 130, 0, 1))[..., None]                                                                              # 字那一边压回墨黑，火只舔过来一点
    s, c = layer(W, H); place(c); figure(c, t, False); rgb, al = rgba(s); fr = fr * (1 - al) + rgb
    s, c = layer(W, H); place(c); figure(c, t, True); fr = A.add_glow(fr, s, 10, 0.55)
    fr = A.grade(np.clip(A.bloom(fr, R, 0.86, 0.35), 0, 1)); fr = fr * (1 - 0.62 * np.clip((dl - 20) / 260, 0, 1))[..., None]                                                 # 越过斜线的那部分人物压暗，给字让位
    fr = fr * (1 - 0.35 * np.clip((np.hypot((xx - W / 2) / W, (yy - H / 2) / H) - 0.35) / 0.45, 0, 1) ** 2)[..., None]
    im = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8)); tc = tuple(int(255 * (0.25 + 0.75 * v)) for v in fire); y1, y2, yr, y3 = L['y']; eps = f'{ep:02d}'
    at = (lambda w: int(L['X'] - w / 2)) if L['mid'] else (lambda w: L['X'])
    wp = (18 + _w(part, 44)) if part else 0; X = at(_w(series, 44, 6) + 6 + 50 + _w(eps, 54, 4) + wp); x1 = _txt(im, (X, y1), series, 44, (214, 206, 190), sp=6); ImageDraw.Draw(im).rectangle((x1 + 22, y1 + 18, x1 + 26, y1 + 58), fill=tc); x2 = _txt(im, (x1 + 50, y1 - 6), eps, 54, tc, sp=4)
    if part: _txt(im, (x2 + 18, y1), part, 44, tc)
    px = _fit(name, L['name'], 0, L['maxw'], fx.BRUSH); _txt(im, (at(_w(name, px, 0, fx.BRUSH)), y2), name, px, ((255, 252, 244), (206, 200, 190)), sp=0, shadow=16, font=fx.BRUSH)
    X = at(150); ImageDraw.Draw(im).rectangle((X, yr, X + 150, yr + 6), fill=tc)
    px = min(_fit(q, 88, 2, L['maxw']) for q in question)
    for i, q in enumerate(question): _txt(im, (at(_w(q, px, 2)), y3 + i * int(px * 1.42)), q, px, ((255, 226, 150), (226, 150, 52)), sp=2, shadow=12)
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True); im.save(out, quality=94); return out
