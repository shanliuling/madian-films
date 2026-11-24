"""cast — 定妆图：萧炎、纳兰嫣然。 → out/cast.png"""
import _env, math, numpy as np, cairo
from PIL import Image, ImageDraw, ImageFont
from paper import layer, rgba, FONT
import fighter as F
s, c = layer(1920, 1080); g = cairo.LinearGradient(0, 0, 0, 1080); g.add_color_stop_rgb(0, 0.80, 0.86, 0.92); g.add_color_stop_rgb(1, 0.55, 0.62, 0.72); c.set_source(g); c.paint()
c.set_source_rgb(0.45, 0.5, 0.6); c.rectangle(0, 960, 1920, 120); c.fill()
def put(fn, p, H, **kw): fn(c, lambda dt: F.kin(p, H, 960), 0.0, **kw)
def who(k, x, H=560, face=1, **o): F.figure(c, lambda dt: F.kin(F.P(x=x, face=face, **o), H, 960), 0.0, F.LOOKS[k])
put(F.xiaoyan, F.P(x=200, a1=(6, 16), a2=(-6, 10), w=-80), 600, held=False, back=True)
who('nalan', 520, 560, a1=(30, 80), w=30); who('yaolao', 820, 560, air=60, a1=(60, 110)); who('yunyun', 1100, 570, face=-1, a1=(20, 70), w=40); who('xuner', 1360, 520, face=-1)
who('xiaozhan', 1560, 600, face=-1); who('yunshan', 1760, 600, face=-1); who('hood', 1010, 330, face=-1, air=560)
rgb, al = rgba(s); im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im); f = ImageFont.truetype(_env.BRUSH, 110); f2 = ImageFont.truetype(FONT, 34)
f2 = ImageFont.truetype(_env.BRUSH, 54)
for x, n in ((200, '萧炎'), (520, '纳兰嫣然'), (820, '药老'), (1100, '云韵'), (1360, '萧薰儿'), (1560, '萧战'), (1760, '云山')): d.text((x, 1010), n, font=f2, fill=(20, 20, 30), anchor='mm')
im.save('out/cast.png'); print('out/cast.png')
