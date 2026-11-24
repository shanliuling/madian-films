"""cast — 定妆图：萧炎、纳兰嫣然。 → out/cast.png"""
import _env, math, numpy as np, cairo
from PIL import Image, ImageDraw, ImageFont
from paper import layer, rgba, FONT
import fighter as F
s, c = layer(1920, 1080); g = cairo.LinearGradient(0, 0, 0, 1080); g.add_color_stop_rgb(0, 0.80, 0.86, 0.92); g.add_color_stop_rgb(1, 0.55, 0.62, 0.72); c.set_source(g); c.paint()
c.set_source_rgb(0.45, 0.5, 0.6); c.rectangle(0, 960, 1920, 120); c.fill()
def put(fn, p, H, **kw): fn(c, lambda dt: F.kin(p, H, 960), 0.0, **kw)
put(F.xiaoyan, F.P(x=330, a1=(6, 16), a2=(-6, 10), w=-80), 760, held=False, back=True)
put(F.xiaoyan, F.P(x=790, lean=24, head=-10, a1=(60, 100), a2=(30, 60), l1=(48, -8), l2=(-40, -62), w=28, g2=-0.10, mouth=1, fire=1), 600)
put(F.nalan, F.P(x=1560, face=-1, a1=(20, 70), a2=(-12, 4), w=40), 720)
put(F.nalan, F.P(x=1180, face=-1, lean=30, head=-14, a1=(70, 96), a2=(-50, -70), l1=(52, 6), l2=(-46, -60), w=6), 560)
rgb, al = rgba(s); im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im); f = ImageFont.truetype(_env.BRUSH, 110); f2 = ImageFont.truetype(FONT, 34)
d.text((60, 40), '萧炎', font=f, fill=(20, 20, 30)); d.text((64, 170), '黑袍 · 玄重尺 · 青色火焰', font=f2, fill=(40, 46, 60)); d.text((1860, 40), '纳兰嫣然', font=f, fill=(20, 20, 30), anchor='ra'); d.text((1856, 170), '月白袍 · 淡青长剑 · 风', font=f2, fill=(40, 46, 60), anchor='ra')
im.save('out/cast.png'); print('out/cast.png')
