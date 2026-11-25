import sys, glob, math
from PIL import Image
pat, out, cols = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3
fs = []
for p in pat.split(','): fs += sorted(glob.glob(p))
tw, th = 800, 450; rows = math.ceil(len(fs) / cols); sh = Image.new('RGB', (cols * tw, rows * th))
for i, f in enumerate(fs): sh.paste(Image.open(f).resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
sh.save(out, quality=88); print(out, len(fs))
