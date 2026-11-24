"""萧炎（上）的封面：python mkcover.py → out/cover_4x3.jpg、out/cover_3x4.jpg（抖音要这两张）"""
import _env, action as A, fx
from cover import cover
CYAN = (0.25, 1.0, 0.80); PURP = (0.72, 0.35, 1.0); HH = 560

def figure(c, t, glow):
    """展开紫云翼，掌心托着开满三层的青紫火莲（正片 106–110 拍那个正面镜头）。"""
    for sd in (-1, 1): fx.wing(c, (sd * 26, -0.70 * HH), sd, 600, 1.0, t, glow=glow, cb=PURP, seed=sd)
    if not glow: fx.cape(c, 0, 0, HH, t, wind=1.0); figure.an = fx.front(c, 0, 0, HH, t, arms='cup', eyes=(CYAN, CYAN))
    an = figure.an; p = ((an['hands'][0][0] + an['hands'][1][0]) / 2, an['hands'][0][1] - 34)
    if not glow: fx.lotus(c, p, 160, t, CYAN, PURP, (1, 1, 1), solid=True)
    else:
        fx.lotus(c, p, 160, t, CYAN, PURP, (1, 1, 1), a=0.3); A.burst(c, p, 150, CYAN, 0.3)
        for (x, y) in an.get('eyes', []): A.burst(c, (x, y), 26, CYAN, 0.9)

for shape, out in (('4:3', 'out/cover_4x3.jpg'), ('3:4', 'out/cover_3x4.jpg')):
    print(cover('萧炎', ['斗之力三段的废物，', '凭什么敢说莫欺少年穷？'], 1, CYAN, figure, out, shape=shape, part='上'))
