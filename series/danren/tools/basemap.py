"""看一眼某个范围的空底图（两种风格），用来定 bbox / px_per_deg / 镜头。
  python tools/basemap.py 西经度 东经度 南纬度 北纬度 [px_per_deg] [out.jpg]
  例：python tools/basemap.py 98 127 24 43 116 china.jpg      python tools/basemap.py -10 40 34 60 60 europe.jpg"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from PIL import Image
from mapwar.world import World
from mapwar.mapshot import MapShot

a = sys.argv; lon0, lon1, lat0, lat1 = map(float, a[1:5]); k = float(a[5]) if len(a) > 5 else 60; out = a[6] if len(a) > 6 else 'basemap.jpg'
W = World(dict(bbox=(lon0, lon1, lat0, lat1), px_per_deg=k, sides=[dict(name='', ink=(0.5, 0.5, 0.5), night=(0.5, 0.5, 0.5), wash=0.0)], cities=[('_', (lon0 + lon1) / 2, (lat0 + lat1) / 2, 0, 0)],
               reach=(0.5, 1.0)), os.path.join(ROOT, 'data'))
z = 620 / (W.TW / 2) * 1.02; cx, cy = (lon0 + lon1) / 2, (lat0 + lat1) / 2
ims = []
for st in ('ink', 'night'):
    ms = MapShot(W, dict(style=lambda t, s=st: s, camseg=[[(0, cx, cy, z, 0), (1, cx, cy, z, 0)]], hud=dict(share=False))); ims.append(ms.frame(0.5))
tl = MapShot(W, dict(camseg=[[(0, cx, cy, z * 1.6, 1), (1, cx, cy, z * 1.6, 1)]], hud=dict(share=False))).frame(0.5)
sh = Image.new('RGB', (1920, 1080 * 3)); [sh.paste(im, (0, 1080 * i)) for i, im in enumerate(ims + [tl])]; sh.save(out, quality=88); print('saved', out, 'texture', W.TW, 'x', W.TH)
