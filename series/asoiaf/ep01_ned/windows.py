"""五扇彩窗：片名 + 四次选择。 get(k) → (glass, mask)，600×940。"""
import math, numpy as np, cairo
import tallfig as F, glass
C = F.CAST; SK = (0.93, 0.74, 0.58)
NED = dict(C['ned'], body=(0.34, 0.38, 0.48), legs=(0.20, 0.22, 0.30), cloak=(0.62, 0.68, 0.76), fur=(0.90, 0.90, 0.86), hair=(0.36, 0.22, 0.12), beard=(0.30, 0.19, 0.11), skin=SK, belt=(0.16, 0.12, 0.10))
NEDP = dict(C['ned_prison'], body=(0.86, 0.84, 0.78), legs=(0.50, 0.50, 0.56), hair=(0.36, 0.22, 0.12), beard=(0.30, 0.19, 0.11), skin=SK)
CER = dict(C['cersei'], body=(0.78, 0.08, 0.14), gown=(0.66, 0.06, 0.12), sleeve=(0.86, 0.14, 0.14), hair=(0.99, 0.84, 0.34), skin=(0.95, 0.78, 0.64))
ILYN = dict(C['ilyn'], body=(0.20, 0.12, 0.30), legs=(0.13, 0.08, 0.22), skin=(0.86, 0.72, 0.62))
ICE = dict(col=(0.90, 0.95, 1.0), hilt=(0.55, 0.42, 0.20))

def w_title(c, gy):
    o = F.fig(c, 300, gy, 560, NED, 'stand', 1, P=dict(af=(38, 62), ab=(30, 56)))
    F.sword(c, (o['hand'][0] + 6, o['hand'][1] - 10), 0, gy - o['hand'][1] + 6, 1, w=24, **ICE)
def w_baby(c, gy):
    o = F.fig(c, 300, gy, 540, NED, 'hold', 1, P=dict(af=(40, 96), ab=(34, 90)))
    hx, hy = o['hand']; c.save(); c.translate(hx - 22, hy - 16); c.rotate(-0.35); c.scale(62, 34); c.set_source_rgb(0.97, 0.95, 0.90); c.arc(0, 0, 1, 0, math.tau); c.fill(); c.restore()
    c.set_source_rgb(*SK); c.arc(hx + 26, hy - 40, 17, 0, math.tau); c.fill()
def w_wood(c, gy):
    c.set_source_rgb(0.95, 0.93, 0.88); c.move_to(262, gy); c.curve_to(280, gy - 250, 270, gy - 420, 250, gy - 560); c.line_to(350, gy - 560); c.curve_to(330, gy - 420, 320, gy - 250, 340, gy); c.close_path(); c.fill()   # 鱼梁木
    for (x, y, rr) in ((300, gy - 640, 150), (170, gy - 560, 100), (430, gy - 570, 105), (240, gy - 740, 90), (380, gy - 730, 86)): c.set_source_rgb(0.74, 0.08, 0.08); c.arc(x, y, rr, 0, math.tau); c.fill()
    F.fig(c, 150, gy, 440, NED, 'stand', 1, P=dict(af=(40, 80))); F.fig(c, 455, gy, 410, CER, 'stand', -1)
def w_night(c, gy):
    c.set_source_rgb(0.42, 0.24, 0.14); c.rectangle(330, gy - 110, 250, 110); c.fill(); c.rectangle(560, gy - 230, 22, 230); c.fill()                       # 床
    c.set_source_rgb(0.92, 0.90, 0.96); c.move_to(340, gy - 110); c.curve_to(400, gy - 170, 480, gy - 160, 560, gy - 120); c.line_to(560, gy - 100); c.line_to(340, gy - 100); c.close_path(); c.fill()
    c.set_source_rgb(*SK); c.arc(530, gy - 150, 24, 0, math.tau); c.fill(); c.set_source_rgb(0.99, 0.86, 0.36); c.arc(540, gy - 162, 22, math.pi * 1.1, math.pi * 2.2); c.fill()
    F.fig(c, 190, gy, 500, NED, 'walk', -1, P=dict(head=14))
def w_sword(c, gy):
    F.fig(c, 240, gy, 480, NEDP, 'kneel', -1); il = F.fig(c, 440, gy, 486, ILYN, 'strike', -1, P=dict(af=(150, 186), ab=(144, 182))); F.sword(c, il['hand'], 176, 300, -1, w=24, **ICE)
SPEC = dict(
    title=(w_title, dict(seed=21, core=(0.80, 0.84, 0.92), cold=[(0.20, 0.24, 0.34), (0.13, 0.16, 0.24), (0.28, 0.33, 0.44), (0.16, 0.20, 0.30)], warm=[(0.70, 0.78, 0.90), (0.50, 0.60, 0.78), (0.86, 0.90, 0.96), (0.40, 0.50, 0.70)], sun=(0.5, 0.40))),
    baby=(w_baby, dict(seed=22, core=(0.30, 0.52, 0.86), warm=[(0.80, 0.90, 0.98), (0.56, 0.74, 0.94), (0.95, 0.97, 1.0), (0.42, 0.62, 0.90)], sun=(0.52, 0.44))),
    wood=(w_wood, dict(seed=23, core=(0.98, 0.84, 0.40), warm=[(0.50, 0.74, 0.36), (0.30, 0.58, 0.28), (0.70, 0.84, 0.44), (0.22, 0.46, 0.26)], cold=[(0.10, 0.30, 0.24), (0.06, 0.20, 0.18), (0.14, 0.38, 0.30), (0.08, 0.26, 0.20)], sun=(0.5, 0.30), R=0.20)),
    night=(w_night, dict(seed=24, core=(0.96, 0.94, 0.78), warm=[(0.46, 0.30, 0.70), (0.32, 0.20, 0.56), (0.60, 0.42, 0.80), (0.26, 0.16, 0.48)], cold=[(0.12, 0.10, 0.34), (0.08, 0.07, 0.24), (0.16, 0.14, 0.42), (0.10, 0.08, 0.28)], sun=(0.72, 0.24), R=0.15)),
    sword=(w_sword, dict(seed=25, core=(0.80, 0.12, 0.10), sun=(0.5, 0.52))))
_cache = {}
def get(k):
    if k not in _cache: fn, kw = SPEC[k]; _cache[k] = glass.window(fn, **kw)
    return _cache[k]
if __name__ == '__main__':
    from paper import to_pil
    ks = ['title', 'baby', 'wood', 'night', 'sword']; img, M = glass.wall([(*get(k), 30 + i * 372, 70) for i, k in enumerate(ks)] if False else [(*[a[::2, ::2] for a in get(k)], 60 + i * 370, 300) for i, k in enumerate(ks)])
    to_pil(img).save('out/_windows.jpg', quality=90)
