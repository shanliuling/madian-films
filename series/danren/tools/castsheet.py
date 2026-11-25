"""角色定妆表：把角色库里的每个人画成一排，检查长相、服装、表情。
  python tools/castsheet.py cast.chuhan out.jpg [表情: 如 eye=fierce,brow=angry,mouth=shout]
"""
import os, sys, importlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import numpy as np, cairo
from PIL import Image, ImageDraw
from mapwar.qchar import Q
from mapwar.scenery import landscape
from mapwar.util import font

mod = importlib.import_module(sys.argv[1]); cast = list(mod.CAST.items()); out = sys.argv[2]
ex = dict(kv.split('=') for kv in sys.argv[3].split(',')) if len(sys.argv) > 3 else {}
W, H, per = 1920, 1080, 5
rows = [cast[i:i + per] for i in range(0, len(cast), per)]; sheet = Image.new('RGB', (W, H * len(rows)))
for r, row in enumerate(rows):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); step = W / len(row)
    for i, (name, spec) in enumerate(row): Q(c, step * (i + 0.5), 900, 520, spec, 1, 'stand' if spec.get('weapon') else 'idle', 0.3, **ex)
    a = np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32) / 255
    img = Image.fromarray((np.clip(landscape('day') * (1 - a[..., 3:4]) + a[..., [2, 1, 0]], 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    for i, (name, spec) in enumerate(row): d.text((step * (i + 0.5), 1000), name, font=font(48), anchor='mm', fill=(30, 20, 15), stroke_width=5, stroke_fill=(245, 232, 205))
    sheet.paste(img, (0, H * r))
sheet.save(out, quality=90); print(out)
