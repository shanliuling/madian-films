"""film — 萧炎（上）《莫欺少年穷》。分镜见 script.md，时间轴按系列 BGM 的拍子（第 n 拍 = 0.50 + 0.59413n 秒），全曲从头放到尾。
    python film.py                → out/xiaoyan1_540p.mp4（RES=1080 出 1080p；FPS=30 出 30 帧）
    python film.py strip 10 12.5  → out/_strip.jpg（看这几拍的画面）
每个镜头是一个函数 shot(t)（t = 全片秒数），登记在 SHOTS 里：(起拍, 止拍, 函数)。三年之约开打那段直接用 fight.py。"""
import _env, os, sys, math, subprocess, functools, numpy as np, cv2, cairo
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from stage import Out
from paper import layer, rgba, FONT
import action as A, fighter as F, yunlan, sets, fight
from action import track, rnd, pulse
R = fight.R; FPS = fight.FPS; BEAT = 0.59413; GY = yunlan.GY; P = F.P
def bt(b): return 0.50 + b * BEAT
DUR = 175.4; CYAN = (0.25, 1.0, 0.80); PURP = (0.72, 0.35, 1.0); WHITEF = (0.82, 0.92, 1.0); WIND = (0.62, 0.98, 1.0); GOLD = (1.0, 0.80, 0.36)
@functools.lru_cache(maxsize=None)
def PL(name):
    if name == 'yunlan': return yunlan.plates(R)
    if name == 'dusk': return A.tint(yunlan.plates(R), (0.95, 0.60, 0.62))
    if name in ('stele', 'hall', 'border', 'wild'): return getattr(sets, name)(R)
    return sets.night(R, name)
class Act:
    """一个演员：造型 + 姿态关键帧。who='xiaoyan' 用萧炎的专门画法，其余走 F.figure。"""
    def __init__(s, who, keys, H=330, mod=None, **kw): s.who, s.f, s.H, s.mod, s.kw = who, track(keys), H, mod, kw; s.c = {}
    def J(s, t):
        t = round(t, 4)
        if t not in s.c:
            p = dict(s.f(t)); p = s.mod(p, t) if s.mod else p; s.c[t] = F.kin(p, s.H, GY)
            if len(s.c) > 6000: s.c.clear()
        return s.c[t]
    def draw(s, c, t, alpha=1.0, **kw):
        k = dict(s.kw); k.update(kw)
        if s.who == 'xiaoyan':
            if alpha < 1: c.push_group()
            F.xiaoyan(c, lambda dt: s.J(t - dt), t, **k)
            if alpha < 1: c.pop_group_to_source(); c.paint_with_alpha(alpha)
        else: F.figure(c, lambda dt: s.J(t - dt), t, F.LOOKS[s.who], alpha=alpha, **k)
    def wp(s, t, L, u=1.0, off=0.1): b, e = F.wpts(s.J(t), L, off); return (b[0] + (e[0] - b[0]) * u, b[1] + (e[1] - b[1]) * u)
def shadow(c, acts, t):
    for a in acts: J = a.J(t); k = max(0.25, 1 - (GY - J['pel'][1]) / 900); c.save(); c.translate(J['pel'][0], GY + 6); c.scale(1, 0.22); c.arc(0, 0, a.H * 0.32 * k, 0, 7); c.restore(); c.set_source_rgba(0.02, 0.03, 0.1, 0.4 * k); c.fill()
def aura(c, a, t, col, n=40, k=0.5, rise=480, r0=50, seed=11):
    def pf(dt, sv): J = a.J(t - dt); b = [J['f1'], J['f2'], J['k1'], J['pel'], J['chest'], J['neck'], J['e1'], J['head']][int(sv * 7.99)]; return (b[0] + (rnd(int(sv * 1000), seed) - 0.5) * 70, b[1] + 16)
    A.flame(c, t, pf, n, 0.5, rise, r0, col, a=k, seed=seed, wob=26)
def wtrail(c, a, t, L, col, th=1400, core=(0.92, 0.96, 1)):
    tr = [F.wpts(a.J(t - k / 300), L, 0.12) for k in range(32)]; sp = math.hypot(tr[0][1][0] - tr[4][1][0], tr[0][1][1] - tr[4][1][1]) * 75
    if sp > th: A.trail(c, tr, col, a=min(1.0, (sp - th) / 3000), core=core)
def lotus(c, pos, r, t, ca=CYAN, cb=PURP, a=1.0):
    """火莲：两色花瓣交错着转，中间一团白。"""
    A.burst(c, pos, r * 2.2, ca, a * 0.5)
    for i in range(10):
        th = i / 10 * 6.283 + t * 5; col = ca if i % 2 else cb; c.save(); c.translate(pos[0] + math.cos(th) * r * 0.5, pos[1] + math.sin(th) * r * 0.5 * 0.55); c.rotate(th); c.scale(r * 0.62, r * 0.26); c.arc(0, 0, 1, 0, 7); c.restore(); c.set_source_rgba(*col, a * 0.85); c.fill()
    A.burst(c, pos, r * 0.7, (1, 1, 1), a)
def wtext(c, s, x, y, px, col, a=1.0, font='Noto Serif CJK SC'):
    """场景里的字（跟着镜头走），居中。"""
    c.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(px); e = c.text_extents(s); c.move_to(x - e.x_advance / 2, y + px * 0.36); c.set_source_rgba(*col, a); c.show_text(s)
_capc = {}
def caption(fr, s, y=968, px=50, col=(244, 244, 248), a=1.0, x=960, font=None):
    """屏幕上的一行字（台词在下方，地点在上方正中）。"""
    key = (s, px, col, font)
    if key not in _capc:
        f = ImageFont.truetype(font or FONT, int(px * R.k)); w = int(sum(f.getlength(ch) for ch in s) + px * R.k * 2); h = int(px * R.k * 2.2); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((w / 2, h / 2), s, font=f, fill=(0, 0, 0, 255), anchor='mm', stroke_width=max(2, int(px * R.k * 0.09)), stroke_fill=(0, 0, 0, 255)); sh = sh.filter(ImageFilter.GaussianBlur(max(1, px * R.k * 0.05))); ImageDraw.Draw(im).text((w / 2, h / 2), s, font=f, fill=col + (255,), anchor='mm')
        b = np.asarray(Image.alpha_composite(sh, im), np.float32) / 255; _capc[key] = (b[..., :3] * b[..., 3:], b[..., 3:])
    rgb, al = _capc[key]; h, w = al.shape[:2]; x0 = int(x * R.k - w / 2); y0 = int(y * R.k - h / 2); xa, xb = max(0, x0), min(R.w, x0 + w); ya, yb = max(0, y0), min(R.h, y0 + h)
    if xa >= xb or ya >= yb or a <= 0: return fr
    fr = fr.copy(); sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0)); fr[ya:yb, xa:xb] = fr[ya:yb, xa:xb] * (1 - al[sl] * a) + rgb[sl] * a; return fr
def cap(fr, t, b0, b1, s, **kw):
    if bt(b0) <= t < bt(b1): fr = caption(fr, s, a=min(1.0, (t - bt(b0)) / 0.12, (bt(b1) - t) / 0.12), **kw)
    return fr
_slc = {}
def slam(fr, t, b0, b1, s, pos, px=220, vertical=False, glow=(60, 255, 210), col=(255, 255, 255), big=2.6, rot=0.0):
    if not bt(b0) <= t < bt(b1): return fr
    key = (s, px, vertical, glow, col)
    if key not in _slc: _slc[key] = A.Slam(s, _env.BRUSH, px, R, col=col, glow=glow, vertical=vertical)
    return _slc[key].draw(fr, t, bt(b0), bt(b1), pos, R, big=big, rot=rot)
def hits(fr, t, mask, glow, M, events):
    """冲击帧：events = [(时刻, 场景坐标, 帧序列)]。"""
    for (t0, pos, seq) in events:
        n = int(round((t - t0) * 60))
        if 0 <= n < len(seq): fr = A.impact(fr, mask, glow, seq[n], R, (M[0, 0] * pos[0] + M[0, 1] * pos[1] + M[0, 2], M[1, 0] * pos[0] + M[1, 1] * pos[1] + M[1, 2]), t)
    return fr
def camk(keys, shakes=()):
    f = track(keys)
    def cam(t): cx, cy, z, ro = f(t); dx, dy = A.shake(t, shakes, FPS); return (cx + dx / z, cy + dy / z, z, ro)
    return cam
def fin(fr): return A.grade(np.clip(A.bloom(fr, R, 0.80, 0.5), 0, 1))
YOUNG = 262                                                                              # 十五岁的萧炎矮一截，没有尺

# ================= 0–4 钩子：云岚宗半空，火莲出手
_h0 = Act('xiaoyan', [(0, P(x=1060, air=430, face=-1, lean=6, head=-4, a1=(70, 120), a2=(50, 110), l1=(20, -30), l2=(-14, -50), glint=1.0, eye=1.0)), (bt(2.6), P(x=1060, air=436, face=-1, lean=4, head=-4, a1=(86, 96), a2=(70, 100), l1=(20, -30), l2=(-14, -50), glint=1.0, mouth=1)),
                      (bt(3.1), P(x=1075, air=440, face=-1, lean=-6, head=0, a1=(100, 92), a2=(60, 110), l1=(26, -30), l2=(-10, -56), glint=1.0, mouth=1), 'snap'), (bt(4), P(x=1085, air=446, face=-1, lean=-8, head=0, a1=(100, 92), a2=(60, 110), l1=(26, -30), l2=(-10, -56), glint=1.0, mouth=1))], held=False)
_c0 = camk([(0, (1040, 300, 3.4, -4)), (bt(1.2), (1010, 318, 2.5, -2), 'o'), (bt(3), (960, 320, 2.1, 3), 'lin'), (bt(4), (700, 300, 1.7, 8), 'i')], [(bt(3), 16, 0.2)])
def s_hook(t):
    J = _h0.J(t); h1, h2 = J['h1'], J['h2']; m = ((h1[0] + h2[0]) / 2 - 26, (h1[1] + h2[1]) / 2); u = min(1.0, t / bt(2.4)); fl = max(0.0, (t - bt(3)) / (bt(4) - bt(3)))
    def glow(c):
        if fl <= 0:
            for (hh, col, sd) in ((h1, CYAN, 3), (h2, PURP, 4)): A.flame(c, t, lambda dt, sv, hh=hh: (hh[0] + (m[0] - hh[0]) * u, hh[1] + (m[1] - hh[1]) * u - 6), 26, 0.4, 260, 26 * (1 - 0.5 * u), col, a=0.9, seed=sd)
            if u > 0.5: lotus(c, m, 44 * (u - 0.5) * 2, t, a=min(1.0, (u - 0.5) * 3))
        else: p = (m[0] - 620 * fl ** 1.5, m[1] - 60 * fl); lotus(c, p, 44 + 520 * fl ** 2, t); A.sparks(c, t, bt(3), m, 40, 0, 180, 300, 1600, 0.5, CYAN, seed=7, g=200)
    fr, mask, gl, M = A.render(R, PL('yunlan'), _c0(t), [('back', lambda c: aura(c, _h0, t, CYAN, k=0.6)), ('chars', lambda c: _h0.draw(c, t)), ('glow', glow)])
    fr = A.focuslines(fr, t, R, (M[0, 0] * m[0] + M[0, 1] * m[1] + M[0, 2], M[1, 0] * m[0] + M[1, 1] * m[1] + M[1, 2]), a=0.45, n=60, r0=0.4, col=(0.85, 1, 0.95)); fr = fin(fr); fr = fr + (1 - fr) * max(0.0, (t - bt(3.5)) / (bt(4) - bt(3.5))) ** 1.5
    return cap(fr, t, 2.5, 4, '「去吧，佛怒莲！」')

# ================= 4–32 石碑：斗之力三段 / 片名 / 三年前的天才 / 跌回三段 / 萧薰儿
_b1 = Act('xiaoyan', [(0, P(x=960, lean=10, head=24, a1=(4, 10), a2=(-4, 4), l1=(6, 0), l2=(-6, -4), eye=0.5)), (bt(15.5), P(x=960, lean=10, head=24, a1=(4, 10), a2=(-4, 4), l1=(6, 0), l2=(-6, -4), eye=0.5)),
                      (bt(16.3), P(x=960, lean=-4, head=-8, a1=(30, 100), a2=(-20, -10), l1=(14, 0), l2=(-14, -8)), 'o'), (bt(23.6), P(x=960, lean=-4, head=-8, a1=(30, 100), a2=(-20, -10), l1=(14, 0), l2=(-14, -8))),
                      (bt(24.6), P(x=960, lean=16, head=30, a1=(2, 8), a2=(-2, 2), l1=(4, 0), l2=(-4, -2), eye=0.4), 'o'), (bt(30), P(x=960, lean=12, head=18, a1=(2, 8), a2=(-2, 2), l1=(4, 0), l2=(-4, -2), eye=0.8)), (bt(32), P(x=960, lean=8, head=6, a1=(2, 8), a2=(-2, 2), l1=(4, 0), l2=(-4, -2)))], H=YOUNG, held=False)
_x1 = Act('xuner', [(0, P(x=1700, face=-1)), (bt(27.5), P(x=1700, face=-1)), (bt(29.6), P(x=1150, face=-1, lean=2), 'io'), (bt(30.4), P(x=1140, face=-1, lean=34, head=10, a1=(30, 60), a2=(20, 50)), 'io'), (bt(31.6), P(x=1140, face=-1, lean=30, head=6, a1=(30, 60), a2=(20, 50)))], H=236,
           mod=lambda p, t: dict(p, l1=(22 * math.sin(p['x'] / 26), 22 * math.sin(p['x'] / 26) - 8), l2=(-22 * math.sin(p['x'] / 26), -22 * math.sin(p['x'] / 26) - 8)) if bt(27.5) < t < bt(29.6) else p)
_c1 = camk([(bt(4), (960, 330, 2.3, 0)), (bt(5), (960, 350, 1.9, 0), 'o'), (bt(8), (960, 560, 1.05, 0), 'io'), (bt(14), (960, 580, 1.12, 0), 'lin'), (bt(16), (960, 470, 1.35, 0), 'io'), (bt(24), (960, 450, 1.5, 0), 'lin'), (bt(24.2), (960, 500, 1.3, 0), 'snap'), (bt(28), (980, 640, 1.5, 0), 'io'), (bt(32), (1040, 700, 2.0, 0), 'io')], [(bt(4), 26, 0.25), (bt(14), 14, 0.15), (bt(24), 22, 0.3)])
STELE = [(4, 14, ('斗之力', '三段'), 1.0), (16, 18, ('四岁', '练气'), 1), (18, 20, ('十岁', '九段'), 1), (20, 24, ('十一岁', '斗者'), 1), (24, 25, ('', '九段'), 0.9), (25, 26, ('', '七段'), 0.8), (26, 27, ('', '五段'), 0.7), (27, 32, ('斗之力', '三段'), 0.6)]
JEER = [(8, '废物', 420, 300), (9, '三段？', 1500, 380), (10, '果然不出所料', 380, 620), (11, '天才？呵', 1480, 640), (12, '真给家族丢人', 960, 250)]
def s_stele(t):
    b = (t - 0.5) / BEAT; genius = 16 <= b < 24
    def glow(c):
        for (b0, b1, (l1, l2), k) in STELE:
            if b0 <= b < b1:
                a = min(1.0, (b - b0) * 4) * k; col = GOLD if b < 24 or b >= 27 else (1.0, 0.45, 0.3); dy = (b - b0) * 60 if 24 <= b < 27 else 0
                for i, ch in enumerate(l1): wtext(c, ch, 960, 250 + i * 86, 80, col, a)
                for i, ch in enumerate(l2): wtext(c, ch, 960, 250 + (len(l1) + i) * 86 + (40 if l1 else 130) + dy, 96, col, a)
        if 24 <= b < 26: A.sparks(c, t, bt(24), (960, 420), 70, 90, 180, 200, 1500, 0.9, GOLD, seed=5, g=1800)
    layers = [('over', lambda c: shadow(c, [_b1, _x1], t)), ('back', lambda c: aura(c, _b1, t, GOLD, k=0.55 * (min(1, (b - 16) * 2) if genius else max(0, 1 - (b - 24) * 2) if 24 <= b < 25 else 0), r0=40)), ('chars', lambda c: (_x1.draw(c, t), _b1.draw(c, t))), ('glow', glow)]
    fr, mask, gl, M = A.render(R, PL('stele'), _c1(t), layers); fr = hits(fr, t, mask, gl, M, [(bt(4), (960, 400), (3, 2, 2, 3)), (bt(24), (960, 420), (2, 2, 3))]); fr = fin(fr)
    if b < 4.6: fr = fr + (1 - fr) * max(0.0, 1 - (b - 4) / 0.6)
    if 14 <= b < 16: fr = fr * 0.45
    for (jb, s, x, y) in JEER: fr = slam(fr, t, jb, 13.8, s, (x, y), px=84, glow=(20, 20, 30), col=(250, 250, 250), big=1.8, rot=(rnd(jb) - 0.5) * 16)
    fr = slam(fr, t, 14, 16, '萧炎', (960, 430), px=330, glow=(255, 150, 40), big=2.2); fr = cap(fr, t, 14.3, 16, '上 · 莫欺少年穷', y=700, px=64, col=(255, 226, 170))
    fr = cap(fr, t, 5, 8, '「萧炎，斗之力，三段！级别：低级！」'); fr = cap(fr, t, 16.3, 20, '三年前'); fr = cap(fr, t, 20, 24, '他是萧家百年之内，最年轻的斗者'); fr = cap(fr, t, 24.3, 27.8, '一夜之间，斗之气旋化为乌有'); return cap(fr, t, 29.8, 32, '「萧炎哥哥。」')

# ================= 32–64 萧家大厅：退婚、莫欺少年穷、休证
_st = dict(lean=4, head=0, a1=(4, 12), a2=(-4, 6), l1=(8, 0), l2=(-8, -4))
_xh = Act('xiaoyan', [(0, P(x=640, **dict(_st, lean=8, head=18, eye=0.6))), (bt(43.6), P(x=640, **dict(_st, lean=8, head=18, eye=0.6))), (bt(44.6), P(x=660, **dict(_st, lean=0, head=-4, a1=(10, 60), a2=(-10, 30))), 'o'), (bt(47.7), P(x=664, **dict(_st, lean=-6, head=-6, a1=(-20, 40), a2=(-10, 30)))),
                      (bt(48), P(x=700, lean=14, head=-10, a1=(90, 94), a2=(-30, -50), l1=(34, 4), l2=(-26, -34), mouth=1), 'snap'), (bt(55), P(x=704, lean=10, head=-8, a1=(60, 96), a2=(-20, -30), l1=(30, 4), l2=(-24, -30), mouth=0)),
                      (bt(62), P(x=1400, **_st), 'io'), (bt(63), P(x=1450, lean=30, head=30, a1=(30, 60), a2=(20, 50), l1=(20, -80), l2=(10, -85)), 'o'), (bt(64), P(x=1450, lean=42, head=40, a1=(30, 60), a2=(20, 50), l1=(20, -80), l2=(10, -85)))], H=YOUNG, held=False)
_nh = Act('nalan', [(0, P(x=1060, face=-1, **_st)), (bt(38), P(x=1060, face=-1, **_st)), (bt(38.6), P(x=1040, face=-1, lean=8, head=-4, a1=(88, 92), a2=(-20, -40), l1=(20, 0), l2=(-16, -20), mouth=1), 'snap'), (bt(44), P(x=1040, face=-1, lean=8, head=-4, a1=(88, 92), a2=(-20, -40), l1=(20, 0), l2=(-16, -20))),
                    (bt(48.2), P(x=1070, face=-1, lean=-10, head=6, a1=(30, 100), a2=(-10, 20), l1=(4, 0), l2=(-20, -10)), 'snap'), (bt(52), P(x=1070, face=-1, lean=-6, head=4, a1=(30, 100), a2=(-10, 20), l1=(4, 0), l2=(-20, -10))), (bt(52.5), P(x=1050, face=-1, lean=10, head=-6, a1=(92, 96), a2=(-30, -50), l1=(22, 0), l2=(-16, -20), mouth=1), 'snap'), (bt(64), P(x=1050, face=-1, lean=4, head=0, a1=(10, 40), a2=(-10, 10), l1=(10, 0), l2=(-10, -6)))], H=250, held=False)
_gh = Act('geye', [(0, P(x=1250, face=-1, **dict(_st, a1=(40, 100)))), (bt(64), P(x=1250, face=-1, **dict(_st, a1=(46, 104))))], H=300)
_fh = Act('xiaozhan', [(0, P(x=1650, face=-1, **_st)), (bt(49.6), P(x=1650, face=-1, **_st)), (bt(50), P(x=1600, face=-1, lean=16, head=-6, a1=(60, 30), a2=(-10, 10), l1=(20, 0), l2=(-14, -10), mouth=1), 'snap'), (bt(64), P(x=1610, face=-1, lean=6, head=0, a1=(20, 40), a2=(-10, 10), l1=(12, 0), l2=(-10, -6)))], H=320)
_ch = camk([(bt(32), (1100, 560, 0.98, 0)), (bt(37.5), (1120, 580, 1.08, 0), 'lin'), (bt(38.4), (1100, 650, 1.75, 2), 'snap'), (bt(43.8), (1080, 650, 1.9, 2), 'lin'), (bt(44.5), (690, 650, 2.0, -2), 'snap'), (bt(47.8), (690, 640, 2.3, -3), 'lin'), (bt(48), (760, 640, 2.0, -6), 'snap'), (bt(49.8), (790, 640, 1.8, -4), 'lin'),
             (bt(50), (1540, 620, 1.7, 3), 'hold'), (bt(52), (1520, 620, 1.8, 3), 'lin'), (bt(52.05), (1040, 650, 1.9, -3), 'hold'), (bt(56), (1020, 650, 2.1, -3), 'lin'), (bt(62), (1480, 620, 1.4, 0), 'hold'), (bt(64), (1500, 630, 1.6, 0), 'lin')], [(bt(48), 26, 0.25), (bt(50), 14, 0.15), (bt(38.5), 8, 0.1), (bt(52.5), 8, 0.1)])
def s_hall(t):
    b = (t - 0.5) / BEAT
    if 56 <= b < 62: return s_palm(t)
    gp = _gh.J(t)['h1']
    def glow(c):
        if 35 <= b < 44: A.burst(c, (gp[0] - 20, gp[1] - 10), 60 + 10 * math.sin(t * 8), (0.6, 1.0, 0.6), min(1.0, (b - 35) * 2) * 0.9, rays=8, t=t, seed=3)
    acts = [_fh, _gh, _nh, _xh]; fr, mask, gl, M = A.render(R, PL('hall'), _ch(t), [('over', lambda c: shadow(c, acts, t)), ('chars', lambda c: [a.draw(c, t) for a in acts]), ('glow', glow)])
    fr = hits(fr, t, mask, gl, M, [(bt(48), (760, 600), (1, 1, 2, 2, 3))]); fr = fin(fr)
    if 48 <= b < 50: fr = A.focuslines(fr, t, R, (R.w * 0.38, R.h * 0.5), a=0.7, n=70, r0=0.46)
    fr = cap(fr, t, 32.3, 36, '萧家大厅', y=80, px=58, col=(255, 226, 170)); fr = cap(fr, t, 34.5, 38.3, '云岚宗送来一枚聚气散，当作退婚的赔礼'); fr = cap(fr, t, 39, 43.8, '「现在的你，就是一个废物！」'); fr = cap(fr, t, 44.6, 47.9, '「三十年河东，三十年河西——」')
    fr = slam(fr, t, 48, 50, '莫欺少年穷', (1180, 420), px=250, glow=(255, 120, 40), big=3.0, rot=-5); fr = cap(fr, t, 50.1, 52, '「好一句莫欺少年穷！我萧战的儿子，就是不凡！」'); fr = cap(fr, t, 52.6, 56, '「三年之后，我在云岚宗等你！」'); return cap(fr, t, 62.2, 64, '他转身，向父亲跪下')
def s_palm(t):
    """▲俯拍：一只带血的手按在纸上。"""
    b = (t - 0.5) / BEAT; s, c = layer(R.w, R.h); c.scale(R.k, R.k); u = min(1.0, (b - 56) / 0.12); sh = A.shake(t, [(bt(56), 30, 0.2)], FPS); c.translate(960 + sh[0], 540 + sh[1]); z = 1.25 - 0.1 * min(1, (b - 56) / 6); c.scale(z, z); c.rotate(-0.12)
    g = cairo.LinearGradient(-1200, 0, 1200, 0); g.add_color_stop_rgb(0, 0.30, 0.15, 0.10); g.add_color_stop_rgb(1, 0.16, 0.08, 0.06); c.set_source(g); c.paint()
    c.rectangle(-330, -430, 660, 860); c.set_source_rgb(0.96, 0.94, 0.88); c.fill()
    for i in range(7):                                                                    # 几行墨字
        c.set_source_rgba(0.08, 0.08, 0.1, 0.85); c.set_line_width(9); x = 250 - i * 62
        for j in range(9): y = -370 + j * 46; c.move_to(x - 14 + 8 * rnd(i, j), y); c.line_to(x + 12 * rnd(j, i), y + 26); c.stroke()
    if u > 0:
        c.set_source_rgba(0.72, 0.03, 0.05, 0.95); c.save(); c.translate(-120, 190); c.arc(0, 30, 78, 0, 7); c.fill()
        for i, (ax, ln) in enumerate(((-66, 110), (-30, 150), (8, 160), (44, 140))): c.save(); c.translate(ax, -30); c.rotate((i - 1.5) * 0.12); c.rectangle(-17, -ln, 34, ln); c.arc(0, -ln, 17, 0, 7); c.fill(); c.restore()
        c.save(); c.translate(86, 30); c.rotate(1.0); c.rectangle(-19, -100, 38, 100); c.arc(0, -100, 19, 0, 7); c.fill(); c.restore(); c.restore()
        for i in range(26): th = rnd(i, 3) * 6.283; d = 120 + 260 * rnd(i, 4) * u; c.arc(-120 + math.cos(th) * d, 190 + math.sin(th) * d, 3 + 9 * rnd(i, 5), 0, 7); c.fill()
    rgb, al = rgba(s); fr = rgb.copy(); n = int(round((t - bt(56)) * 60))
    if 0 <= n < 4: fr = (1 - fr) if n < 2 else fr + (1 - fr) * 0.6
    fr = fin(fr); return cap(fr, t, 57, 62, '「这不是解除婚约的契约，是把你逐出萧家的休证！」')

# ================= 64–80 悬崖：戒指、药老、焚诀（音乐安静）
_xr = Act('xiaoyan', [(0, P(x=1000, **_st)), (bt(64.6), P(x=1000, lean=-14, head=-6, a1=(-150, -170), a2=(20, 40), l1=(-10, 0), l2=(20, -10))), (bt(65), P(x=1040, lean=26, head=-8, a1=(80, 70), a2=(-30, -20), l1=(30, 0), l2=(-26, -30)), 'snap'), (bt(67), P(x=1040, lean=14, head=10, a1=(10, 20), a2=(-6, 4), l1=(20, 0), l2=(-16, -10))),
                      (bt(69.5), P(x=1040, lean=10, head=10, a1=(10, 20), a2=(-6, 4), l1=(20, 0), l2=(-16, -10))), (bt(70.2), P(x=960, lean=-16, head=-20, a1=(40, 110), a2=(-30, -10), l1=(30, 10), l2=(-10, -30), mouth=1), 'snap'), (bt(76), P(x=960, lean=-6, head=-22, a1=(10, 30), a2=(-10, 0), l1=(16, 4), l2=(-10, -12))), (bt(80), P(x=970, lean=2, head=-24, a1=(10, 30), a2=(-10, 0), l1=(12, 2), l2=(-10, -8)))], H=YOUNG, held=False)
_yr = Act('yaolao', [(0, P(x=1260, air=250, face=-1, lean=4, a1=(10, 30), a2=(-10, 10))), (bt(73.6), P(x=1260, air=250, face=-1, lean=4, a1=(10, 30), a2=(-10, 10))), (bt(74.4), P(x=1250, air=256, face=-1, lean=8, a1=(60, 110), a2=(-10, 10)), 'o'), (bt(80), P(x=1250, air=262, face=-1, lean=8, a1=(64, 112), a2=(-10, 10)))], H=340, mod=lambda p, t: dict(p, air=p['air'] + 10 * math.sin(t * 1.6)))
_ringp = track([(bt(64.9), (1090, 560)), (bt(65.6), (1420, 420), 'o'), (bt(66.6), (1560, 900), 'i'), (bt(67.6), (1520, 1100), 'lin'), (bt(69.6), (1250, 600), 'io'), (bt(80), (1250, 600))])
_cr = camk([(bt(64), (1000, 500, 0.95, 0)), (bt(67), (1160, 540, 1.15, 0), 'io'), (bt(69.6), (1160, 600, 1.3, 0), 'io'), (bt(70.2), (1110, 610, 1.45, 0), 'snap'), (bt(80), (1110, 620, 1.6, 0), 'lin')], [(bt(70), 10, 0.12)])
def s_ring(t):
    b = (t - 0.5) / BEAT; rp = _ringp(t); ya = min(1.0, max(0.0, (b - 70) / 0.8)); yh = _yr.J(t)['h1']
    def glow(c):
        if b >= 64.9: A.burst(c, rp, 16 + (30 if b > 68 else 0) * min(1, (b - 68) / 1.5) + 4 * math.sin(t * 9), WHITEF, 0.95)
        if b > 68: A.flame(c, t, lambda dt, sv: (rp[0] + (sv - 0.5) * 30, rp[1]), 26, 0.7, 360 * min(1, (b - 68) / 2), 24, WHITEF, a=0.7, seed=3, wob=20)
        if b > 74.2: A.flame(c, t, lambda dt, sv: (yh[0] - 10 + (sv - 0.5) * 30, yh[1] - 16), 40, 0.5, 300, 30, WHITEF, a=min(1.0, (b - 74.2) * 2), seed=9, wob=16); A.burst(c, (yh[0] - 10, yh[1] - 30), 70, WHITEF, 0.5 * min(1.0, (b - 74.2) * 2))
        A.ring(c, t, bt(70), rp, 520, 0.6, WHITEF, sq=1.0, w=18)
    fr, mask, gl, M = A.render(R, PL('cliff'), _cr(t), [('over', lambda c: shadow(c, [_xr], t)), ('chars', lambda c: (_xr.draw(c, t), _yr.draw(c, t, alpha=ya) if ya > 0 else None)), ('glow', glow)]); fr = fin(fr)
    if b < 64.5: fr = fr * (b - 64) * 2
    fr = cap(fr, t, 64.4, 69.6, '那一夜，他把母亲留下的戒指扔下了悬崖'); fr = cap(fr, t, 70.4, 74, '「不就是吸收了你三年的斗之气嘛。」'); fr = cap(fr, t, 74.3, 77, '废了他三年的，是这枚戒指里的老人——药老')
    fr = cap(fr, t, 77.2, 80, '他给的功法，每进化一次，都必须吞噬一种异火'); return slam(fr, t, 77, 80, '焚诀', (420, 420), px=260, glow=(200, 230, 255), big=2.0)

# ================= 80–96 苦修：玄重尺（重鼓）
_wk = lambda p, t: dict(p, l1=(34 * math.sin(p['x'] / 34), 34 * math.sin(p['x'] / 34) - 30), l2=(-34 * math.sin(p['x'] / 34), -34 * math.sin(p['x'] / 34) - 30), air=6 * abs(math.cos(p['x'] / 34))) if bt(88.2) < t < bt(91.4) else p
_xt = Act('xiaoyan', [(0, P(x=760, lean=-10, head=-10, a1=(40, 100), a2=(-30, -20), l1=(20, 10), l2=(-14, -30), w=-80)), (bt(81.5), P(x=760, lean=-6, head=6, a1=(40, 100), a2=(-30, -20), l1=(20, 10), l2=(-14, -30), w=-80)), (bt(82.4), P(x=880, lean=30, head=10, a1=(60, 80), a2=(40, 70), l1=(40, 0), l2=(-30, -50), w=-80, g2=-0.085), 'io'),
                      (bt(83.7), P(x=880, lean=36, head=4, a1=(64, 84), a2=(40, 70), l1=(46, -6), l2=(-30, -56), w=-76, g2=-0.085, mouth=1)),
                      (bt(84), P(x=880, lean=-14, head=-6, a1=(150, 170), a2=(60, 110), l1=(30, 10), l2=(-24, -30), w=120, g2=-0.085, mouth=1), 'i'), (bt(84.7), P(x=880, lean=-10, head=-6, a1=(140, 165), a2=(60, 110), l1=(30, 10), l2=(-24, -30), w=110, g2=-0.085)),
                      (bt(85), P(x=930, lean=34, head=-20, a1=(70, 84), a2=(60, 80), l1=(56, -4), l2=(-40, -52), w=-20, g2=-0.085, mouth=1), 'ii'), (bt(85.7), P(x=930, lean=30, head=-18, a1=(70, 84), a2=(60, 80), l1=(52, -4), l2=(-40, -50), w=-26, g2=-0.085)),
                      (bt(86), P(x=980, lean=-8, head=-6, a1=(100, 100), a2=(60, 80), l1=(40, 0), l2=(-30, -40), w=40, g2=-0.085, mouth=1), 'ii'), (bt(86.7), P(x=980, lean=-12, head=-6, a1=(120, 130), a2=(60, 80), l1=(40, 0), l2=(-30, -40), w=80, g2=-0.085)),
                      (bt(87), P(x=1040, lean=40, head=-24, a1=(64, 80), a2=(60, 80), l1=(60, -6), l2=(-44, -56), w=-40, g2=-0.085, mouth=1), 'ii'), (bt(88.2), P(x=1040, lean=20, head=-10, a1=(6, 16), a2=(-6, 10), l1=(20, 0), l2=(-20, -20), w=-80)),
                      (bt(91.4), P(x=2500, lean=30, head=-20, a1=(-30, 40), a2=(40, 90), w=-80), 'lin'), (bt(91.7), P(x=2560, lean=-16, head=-6, a1=(150, 172), a2=(60, 110), l1=(30, 10), l2=(-24, -30), w=124, g2=-0.085, glint=0.8), 'o'),
                      (bt(92), P(x=2620, lean=44, head=-26, a1=(62, 78), a2=(60, 80), l1=(64, -8), l2=(-46, -60), w=-44, g2=-0.085, mouth=1, glint=1.0), 'ii'), (bt(96), P(x=2620, lean=40, head=-24, a1=(62, 78), a2=(60, 80), l1=(60, -8), l2=(-46, -58), w=-46, g2=-0.085, glint=1.0))], H=300, mod=_wk)
_ct = camk([(bt(80), (900, 600, 1.9, -4)), (bt(82), (880, 640, 1.5, 0), 'o'), (bt(84), (900, 640, 1.45, 0), 'lin'), (bt(88), (1000, 650, 1.6, 2), 'lin'), (bt(88.3), (1100, 640, 1.2, 0), 'io'), (bt(91.4), (2440, 640, 1.2, 0), 'lin'), (bt(92), (2700, 660, 1.7, -6), 'i'), (bt(96), (2720, 640, 1.9, -4), 'o')], [(bt(80), 40, 0.3), (bt(84), 8, 0.1), (bt(85), 14, 0.12), (bt(86), 8, 0.1), (bt(87), 16, 0.14), (bt(92), 44, 0.35)])
ROCK = (2790, GY)
def s_train(t):
    b = (t - 0.5) / BEAT; fall = min(1.0, max(0.0, (t - bt(79.7)) / (bt(80) - bt(79.7)))) ** 2; held = b >= 82.2; onback = 88.2 <= b < 91.5; J = _xt.J(t)
    def ground(c):
        shadow(c, [_xt], t)
        if b < 92:                                                                        # 路边一块大石头，等着挨那一尺
            c.move_to(ROCK[0] - 150, GY + 10); c.line_to(ROCK[0] - 120, GY - 190); c.line_to(ROCK[0] - 20, GY - 270); c.line_to(ROCK[0] + 110, GY - 210); c.line_to(ROCK[0] + 160, GY + 10); c.close_path(); c.set_source_rgb(0.42, 0.44, 0.46); c.fill_preserve(); c.set_source_rgb(0.08, 0.09, 0.12); c.set_line_width(5); c.stroke()
        if b < 82.2: c.save(); c.translate(905, GY + 40 - 900 * (1 - fall)); c.rotate(0.14); c.rectangle(-22, -300, 44, 300); c.set_source_rgb(0.05, 0.05, 0.08); c.fill_preserve(); c.set_source_rgb(0.3, 0.32, 0.4); c.set_line_width(4); c.stroke(); c.restore()
        A.debris(c, t, bt(80), (905, GY), 24, 400, 1300, (0.3, 0.36, 0.26), seed=3, floor=GY + 10); A.puff(c, t, bt(80), (905, GY + 6), 26, 260, 150, 34, 180, 1.2, (0.8, 0.84, 0.76, 0.7), 4)
        A.debris(c, t, bt(92), ROCK, 46, 500, 1900, (0.42, 0.44, 0.46), seed=6, floor=GY + 10, size=30); A.puff(c, t, bt(92), ROCK, 30, 300, 200, 40, 220, 1.4, (0.8, 0.82, 0.8, 0.75), 7)
        for i, tb in enumerate((85, 87)): A.puff(c, t, bt(tb), (J['pel'][0] + 150, GY + 6), 12, 120, 60, 20, 100, 0.7, (0.8, 0.84, 0.76, 0.6), 10 + i)
    def glow(c):
        if held and not onback: wtrail(c, _xt, t, 0.92, (0.5, 0.6, 0.9), th=900)
        A.ring(c, t, bt(80), (905, GY + 8), 700, 0.5, (1, 1, 1), w=24); A.sparks(c, t, bt(80), (905, GY), 50, 90, 80, 400, 2000, 0.5, GOLD, seed=5)
        A.ring(c, t, bt(92), ROCK, 900, 0.5, (1, 1, 1), w=30); A.sparks(c, t, bt(92), (ROCK[0] - 40, GY - 200), 70, 60, 170, 500, 2600, 0.6, GOLD, seed=8)
    fr, mask, gl, M = A.render(R, PL('wild'), _ct(t), [('over', ground), ('chars', lambda c: _xt.draw(c, t, held=held and not onback, back=onback)), ('glow', glow)])
    fr = hits(fr, t, mask, gl, M, [(bt(80), (905, GY - 100), (1, 1, 2, 2, 3)), (bt(92), (ROCK[0] - 40, GY - 200), (1, 1, 2, 2, 2, 3))])
    if 88.3 < b < 91.4: fr = A.speedlines(fr, t, R, a=0.5, ang=0)
    fr = fin(fr); fr = slam(fr, t, 80, 83.6, '玄重尺', (1440, 420), px=260, glow=(120, 140, 255), big=3.0); fr = cap(fr, t, 80.6, 83.8, '背上它，斗气就被压住——药老给他的第一件东西')
    fr = cap(fr, t, 84, 88, '斗之气 · 九段', y=110, px=64, col=(255, 226, 170)); fr = cap(fr, t, 88, 92, '斗者', y=110, px=72, col=(255, 226, 170)); fr = slam(fr, t, 92, 96, '斗师', (700, 300), px=230, glow=(255, 190, 60), big=2.6)
    fr = cap(fr, t, 88.4, 91.8, '魔兽山脉，然后是塔戈尔大沙漠'); return cap(fr, t, 92.6, 96, '焚诀要的第一种火，就埋在黄沙底下')

# ================= 96–116 山洞：吞噬青莲地心火
_xs = Act('xiaoyan', [(0, P(x=960, lean=6, head=22, a1=(40, 100), a2=(30, 96), l1=(82, -70), l2=(70, -84), eye=0.8)), (bt(97.8), P(x=960, lean=6, head=22, a1=(40, 100), a2=(30, 96), l1=(82, -70), l2=(70, -84), eye=0.8)),
                      (bt(98), P(x=960, lean=-10, head=-30, a1=(50, 160), a2=(40, 150), l1=(82, -70), l2=(70, -84), eye=0.0, mouth=1), 'snap'), (bt(99), P(x=960, lean=0, head=0, a1=(30, 80), a2=(20, 76), l1=(82, -70), l2=(70, -84), eye=0.0), 'o'),
                      (bt(104), P(x=960, lean=14, head=20, a1=(30, 80), a2=(20, 76), l1=(82, -70), l2=(70, -84), eye=0.0, mouth=1)), (bt(108), P(x=960, lean=-16, head=-26, a1=(-20, 40), a2=(-30, 30), l1=(82, -70), l2=(70, -84), eye=0.0, mouth=1), 'io'),
                      (bt(111.8), P(x=960, lean=2, head=0, a1=(30, 80), a2=(20, 76), l1=(82, -70), l2=(70, -84), eye=0.0), 'io'), (bt(112), P(x=960, lean=0, head=-4, a1=(30, 80), a2=(20, 76), l1=(82, -70), l2=(70, -84), eye=1.2, glint=1.0), 'snap'), (bt(116), P(x=960, lean=0, head=-4, a1=(30, 80), a2=(20, 76), l1=(82, -70), l2=(70, -84), eye=1.0, glint=1.0))], H=330, held=False,
           mod=lambda p, t: dict(p, x=p['x'] + (6 * math.sin(t * 70) if bt(98) < t < bt(111.5) else 2 * math.sin(t * 60) if t < bt(98) else 0)))
_EH = _xs.J(bt(113))['head']
_cs = camk([(bt(96), (1000, _EH[1] + 60, 2.8, 0)), (bt(97.9), (1000, _EH[1] + 56, 3.1, 0), 'lin'), (bt(98), (960, 600, 1.5, 0), 'snap'), (bt(104), (960, 580, 1.25, 0), 'lin'), (bt(108), (960, 560, 1.1, 3), 'lin'), (bt(111.8), (960, 600, 1.5, 0), 'io'), (bt(112), (_EH[0] + 20, _EH[1], 4.2, -4), 'snap'), (bt(114), (_EH[0] + 20, _EH[1], 4.6, -3), 'lin'), (bt(114.05), (960, 540, 1.0, 0), 'hold'), (bt(116), (960, 540, 1.1, 0), 'lin')], [(bt(98), 30, 0.3), (bt(104), 12, 2.2), (bt(112), 24, 0.25)])
def s_swallow(t):
    b = (t - 0.5) / BEAT; J = _xs.J(t); hp = ((J['h1'][0] + J['h2'][0]) / 2 + 10, (J['h1'][1] + J['h2'][1]) / 2 - 14); burn = min(1.0, max(0.0, (b - 98) / 1.0)) * (1.0 if b < 112 else max(0.35, 1 - (b - 112) / 2)); shell = max(0.0, min(1.0, (110.5 - b) / 10)) if b >= 98 else 0
    def seat(c):                                                                          # 青莲座
        for i in range(9): th = (i - 4) / 4 * 1.25; c.save(); c.translate(960 + math.sin(th) * 150, GY + 14 - math.cos(th) * 20); c.rotate(th * 0.9); c.scale(34, 78); c.arc(0, -0.6, 1, 0, 7); c.restore(); c.set_source_rgba(0.16, 0.62, 0.5, 0.95); c.fill_preserve(); c.set_source_rgb(0.03, 0.14, 0.12); c.set_line_width(4); c.stroke()
    def chars(c):
        _xs.draw(c, t)
        if shell > 0:                                                                     # 血莲丹化成的血色甲，一片片烧掉
            c.push_group(); _xs.draw(c, t); c.set_operator(cairo.OPERATOR_IN); c.set_source_rgba(0.75, 0.05, 0.08, 1); c.paint(); c.set_operator(cairo.OPERATOR_DEST_OUT)
            for i in range(60):
                if rnd(i, 9) > shell: c.arc(960 - 150 + 300 * rnd(i, 1), GY - 330 * rnd(i, 2), 46, 0, 7); c.set_source_rgba(0, 0, 0, 1); c.fill()
            c.set_operator(cairo.OPERATOR_OVER); c.pop_group_to_source(); c.paint_with_alpha(0.82)
    def glow(c):
        if b < 98: A.flame(c, t, lambda dt, sv: (hp[0] + (sv - 0.5) * 24, hp[1]), 30, 0.5, 200, 20, CYAN, a=0.95, seed=3, wob=10); A.burst(c, hp, 30, CYAN, 0.8)
        else:
            A.flame(c, t, lambda dt, sv: (960 + (sv - 0.5) * 420, GY + 10), 70, 0.8, 900, 70, CYAN, a=0.28 * burn, seed=13, wob=40)
            if b < 112: A.emit(c, t, bt(98), min(t, bt(110.5)), 30, lambda tb: (960 + (rnd(int(tb * 97), 1) - 0.5) * 160, GY - 60 - 240 * rnd(int(tb * 97), 2)), ang=90, spread=180, v0=200, v1=900, life=0.6, col=(1.0, 0.25, 0.2), w=4, g=-300, seed=17)
            A.ring(c, t, bt(98), (960, GY - 150), 1400, 0.6, CYAN, sq=1.0, w=40); A.ring(c, t, bt(112), (960, GY - 150), 1600, 0.6, (0.8, 1, 0.95), sq=1.0, w=40)
            if b >= 114: A.burst(c, (960, GY - 160), 500 + 60 * math.sin(t * 8), CYAN, 0.35, rays=20, t=t, seed=5)
    fr, mask, gl, M = A.render(R, PL('cave'), _cs(t), [('over', seat), ('back', lambda c: aura(c, _xs, t, CYAN, n=60, k=0.42 * burn * (1.6 if 106 < b < 111 else 1), rise=700, r0=56)), ('chars', chars), ('glow', glow)])
    fr = hits(fr, t, mask, gl, M, [(bt(98), (960, GY - 150), (1, 1, 2, 2, 3)), (bt(112), (960, GY - 200), (2, 2, 3))]); fr = fin(fr)
    if 112 <= b < 114: fr = A.focuslines(fr, t, R, (R.w * 0.5, R.h * 0.5), a=0.5, n=60, r0=0.4, col=(0.8, 1, 0.93))
    fr = cap(fr, t, 96.2, 98, '「吞下去…」'); fr = cap(fr, t, 99, 103.6, '吞噬异火，就算备齐了丹药，成功率也只有一成'); fr = cap(fr, t, 104, 108, '血莲丹化成的血甲，被一层层烧穿'); fr = cap(fr, t, 108.4, 111.8, '撑不过去，就是一把灰')
    fr = slam(fr, t, 114, 116, '青莲地心火', (960, 400), px=240, glow=(40, 255, 200), big=2.4); return cap(fr, t, 114.3, 116, '异火榜 · 第十九', y=640, px=60, col=(190, 255, 235))

# ================= 116–129 三年之约：开打（fight.py 那段，拍 96 ↔ 这里的拍 116）
def s_fight(t):
    fr = fight.frame(min(t - bt(116) + fight.LEAD, fight.T_CARD - 0.02)); return cap(fr, t, 118.3, 121.5, '云岚宗 · 三年之约', y=80, px=58, col=(255, 226, 170))

# ================= 129–136 八极崩
def free_ruler(c, pos, ang, H=330): F.ruler(c, dict(H=H, h1=pos, wd=(math.cos(math.radians(ang)), -math.sin(math.radians(ang)))), 0.011 * H)
_xb = Act('xiaoyan', [(0, P(x=700, air=300, rot=-30, lean=20, head=-10, a1=(60, 80), a2=(60, 80), l1=(60, -30), l2=(-30, -60), w=-30, g2=-0.085)), (bt(129.6), P(x=560, lean=44, head=-30, a1=(70, 60), a2=(-30, -40), l1=(70, -30), l2=(-50, -80), w=-70, glint=1.0), 'i'),
                      (bt(130.3), P(x=540, lean=-14, head=-6, a1=(-150, -170), a2=(40, 90), l1=(-20, -30), l2=(40, 10), w=150, glint=1.0), 'io'),                                              # 尺抡到身后
                      (bt(130.6), P(x=600, lean=40, head=-20, a1=(80, 86), a2=(-40, -60), l1=(60, -10), l2=(-50, -60), w=0, mouth=1, glint=1.0), 'ii'),                                         # 掷出去
                      (bt(130.9), P(x=600, lean=40, head=-20, a1=(80, 86), a2=(-40, -60), l1=(60, -10), l2=(-50, -60), mouth=1, glint=1.0)),
                      (bt(131.1), P(x=1640, face=-1, lean=30, head=-16, a1=(-60, -30), a2=(60, 100), l1=(50, -20), l2=(-50, -50), glint=1.0), 'hold'),                                           # 真身到她背后
                      (bt(131.86), P(x=1560, face=-1, lean=-20, head=4, a1=(-80, 40), a2=(70, 110), l1=(30, 0), l2=(-50, -30), glint=1.0), 'o'),                                               # 拳收到腰后
                      (bt(132), P(x=1470, face=-1, lean=42, head=-24, a1=(88, 90), a2=(-50, -70), l1=(70, -10), l2=(-56, -66), mouth=1, glint=1.0), 'ii'),                                       # 八极崩
                      (bt(133.5), P(x=1460, face=-1, lean=36, head=-20, a1=(84, 90), a2=(-50, -70), l1=(66, -10), l2=(-54, -62), mouth=1)), (bt(136), P(x=1440, face=-1, lean=8, head=-4, a1=(10, 30), a2=(-10, 0), l1=(20, 0), l2=(-20, -20)), 'io')], held=False)
_nb = Act('nalan', [(0, P(x=1200, air=320, face=-1, rot=20, lean=-10, a1=(60, 90), a2=(-20, -40), l1=(30, -30), l2=(-20, -50), w=40)), (bt(129.7), P(x=1330, face=-1, lean=10, head=-6, a1=(40, 90), a2=(-20, -30), l1=(40, -10), l2=(-30, -50), w=30), 'io'),
                    (bt(130.7), P(x=1330, face=-1, lean=6, head=-6, a1=(50, 100), a2=(-20, -30), l1=(30, -6), l2=(-30, -40), w=40)), (bt(131), P(x=1350, face=-1, lean=-14, head=0, a1=(110, 150), a2=(-30, -50), l1=(20, 10), l2=(-30, -20), w=100, mouth=1), 'snap'),   # 一剑挑飞重尺
                    (bt(131.9), P(x=1350, face=-1, lean=-8, head=14, a1=(100, 140), a2=(-30, -50), l1=(20, 10), l2=(-30, -20), w=96, mouth=1)),
                    (bt(132.04), P(x=1300, air=60, face=-1, rot=-50, lean=-40, head=30, a1=(120, 150), a2=(100, 140), l1=(60, 20), l2=(40, 10), w=120, mouth=1), 'snap'),                       # 中拳，弓着身子飞出去
                    (bt(133.2), P(x=480, air=120, face=-1, rot=-80, lean=-30, head=30, a1=(130, 160), a2=(110, 150), l1=(70, 30), l2=(50, 10), w=140, mouth=1), 'lin'), (bt(133.5), P(x=330, air=0, face=-1, rot=-86, lean=-10, head=10, a1=(150, 170), a2=(120, 160), l1=(80, 60), l2=(60, 40), w=170), 'i'),
                    (bt(136), P(x=300, air=0, face=-1, rot=-86, lean=-10, head=10, a1=(150, 170), a2=(120, 160), l1=(80, 60), l2=(60, 40), w=170))], H=305)
_rulp = track([(bt(130.6), (700, 600, 0)), (bt(131), (1260, 590, -700), 'lin'), (bt(131.7), (1500, 60, -1500), 'o'), (bt(132.6), (1620, 760, -1960), 'i'), (bt(136), (1620, 760, -1960))])       # 掷出的尺：(x, y, 角度)
_cb = camk([(bt(129), (960, 560, 1.0, 0)), (bt(130.2), (760, 640, 1.5, 3), 'io'), (bt(130.6), (800, 640, 1.5, 0), 'lin'), (bt(131), (1240, 620, 1.5, -3), 'lin'), (bt(131.1), (1500, 640, 1.9, 5), 'snap'), (bt(131.9), (1460, 640, 2.4, 8), 'lin'),
             (bt(132.04), (1420, 620, 2.0, 4), 'snap'), (bt(132.3), (1100, 600, 1.15, 0), 'o'), (bt(133.5), (760, 620, 1.2, 0), 'lin'), (bt(136), (420, 700, 1.7, 0), 'io')], [(bt(129.6), 16, 0.15), (bt(131), 14, 0.12), (bt(132), 46, 0.35), (bt(133.5), 30, 0.3)])
BJ = (1330, 640)
def s_baji(t):
    b = (t - 0.5) / BEAT; rp = _rulp(t); acts = [_nb, _xb]
    def ground(c):
        shadow(c, acts, t); A.puff(c, t, bt(129.6), (560, GY + 6), 22, 200, 100, 30, 150, 1.0, (0.86, 0.9, 0.96, 0.75), 1); A.puff(c, t, bt(131.1), (1640, GY + 6), 12, 120, 60, 22, 110, 0.7, (0.86, 0.9, 0.96, 0.7), 2)
        A.debris(c, t, bt(133.5), (340, GY), 40, 500, 1700, (0.5, 0.57, 0.68), seed=4, floor=GY + 10, size=22)
        for i in range(10): tb = bt(133.5) + 0.08 * i; A.puff(c, t, tb, (340 + (rnd(i, 5) - 0.5) * 260, GY - 10 - 90 * rnd(i, 6)), 9, 200, 140, 50, 230, 2.2, (0.86, 0.9, 0.96, 0.85), 20 + i)
        for i in range(7): tb = bt(132.3) + 0.1 * i; x = _nb.J(tb)['pel'][0]; A.puff(c, t, tb, (x, GY + 6), 5, 60, 50, 18, 90, 0.7, (0.86, 0.9, 0.96, 0.6), 40 + i)
    def chars(c):
        if b < 130.6: pass
        elif b < 136: free_ruler(c, (rp[0], rp[1]), rp[2])
        if 131.05 <= b < 131.5:                                                           # 掷尺的地方还留着一个残影
            _xb.draw(c, bt(130.88), alpha=0.5 * (1 - (b - 131.05) / 0.45))
        if 132.04 < b < 133.5:
            for k in (3, 2, 1): _nb.draw(c, t - 0.03 * k, alpha=0.26 - 0.06 * k)
        _nb.draw(c, t); _xb.draw(c, t, held=b < 130.6)
    def glow(c):
        if b < 130.6: wtrail(c, _xb, t, 0.92, (0.3, 0.9, 0.8), th=900)
        if 130.6 <= b < 132.6: tr = [(lambda q: ((q[0], q[1]), (q[0] + math.cos(math.radians(q[2])) * 300, q[1] - math.sin(math.radians(q[2])) * 300)))(_rulp(t - k / 300)) for k in range(30)]; A.trail(c, tr, (0.3, 0.6, 0.9), a=0.7)
        wtrail(c, _nb, t, 0.66, WIND, th=1000); A.sparks(c, t, bt(131), (1270, 600), 50, 60, 170, 400, 2200, 0.5, (1, 0.95, 0.75), seed=6); A.ring(c, t, bt(131), (1270, 600), 380, 0.3, (1, 1, 1), sq=1.0, w=20)
        if 131.1 <= b < 132: J = _xb.J(t); A.flame(c, t, lambda dt, sv: (J['h1'][0] + (sv - 0.5) * 30, J['h1'][1]), 40, 0.35, 240, 30, CYAN, a=min(1.0, (b - 131.1) * 2), seed=8); A.burst(c, J['h1'], 40 + 80 * (b - 131.1), CYAN, 0.8)
        A.sparks(c, t, bt(132), BJ, 90, 180, 70, 700, 3400, 0.6, CYAN, seed=9, w=4.5, g=300); A.ring(c, t, bt(132), BJ, 1300, 0.45, (0.8, 1, 0.95), sq=1.0, w=44); A.ring(c, t, bt(132) + 0.06, BJ, 800, 0.4, CYAN, sq=0.5, w=24); A.ring(c, t, bt(133.5), (340, GY), 800, 0.5, (1, 1, 1), w=24)
        if 132 <= b < 132.8: A.burst(c, BJ, 600 * (1 - math.exp(-(t - bt(132)) / 0.05)), CYAN, math.exp(-(t - bt(132)) / 0.12), rays=22, t=t, seed=11)
        if b > 135: A.burst(c, (330, GY - 60), 100 + 500 * (b - 135), WIND, 0.5 * (b - 135), rays=14, t=t, seed=13)                                                              # 尘里亮起风的青光
    fr, mask, gl, M = A.render(R, PL('yunlan'), _cb(t), [('over', ground), ('back', lambda c: aura(c, _xb, t, CYAN, k=0.5)), ('chars', chars), ('glow', glow)])
    fr = hits(fr, t, mask, gl, M, [(bt(131), (1270, 600), (3, 2, 3)), (bt(132), BJ, (1, 1, 1, 2, 2, 2, 1, 3)), (bt(133.5), (340, GY), (2, 3))])
    if 131.1 <= b < 132: fr = A.focuslines(fr, t, R, (R.w * 0.55, R.h * 0.5), a=0.5, n=60, r0=0.4, col=(0.8, 1, 0.93))
    if 132.05 < b < 133.4: fr = A.speedlines(fr, t, R, a=0.5, ang=0)
    fr = fin(fr)
    if b < 130: fr = fr + (np.float32((0.86, 1.0, 0.96)) - fr) * max(0.0, 1 - (b - 129) / 0.8)
    fr = slam(fr, t, 132, 134, '八极崩', (560, 400), px=300, glow=(40, 255, 200), big=3.2, rot=-6); fr = cap(fr, t, 130.2, 131.9, '重尺只是幌子'); return cap(fr, t, 134, 136, '纳兰嫣然，败？')

# ================= 136–148 风之极·陨杀 对 佛怒火莲
_nl = Act('nalan', [(0, P(x=330, face=1, lean=30, head=10, a1=(20, 40), a2=(10, 30), l1=(60, -60), l2=(-20, -80), w=-70)), (bt(136.6), P(x=330, face=1, lean=8, head=-10, a1=(30, 80), a2=(-20, -30), l1=(20, 0), l2=(-20, -20), w=20), 'io'),
                    (bt(138), P(x=360, air=330, face=1, lean=-6, head=-6, a1=(150, 176), a2=(-30, -50), l1=(10, -20), l2=(-20, -50), w=96), 'io'), (bt(144.8), P(x=360, air=350, face=1, lean=-10, head=-4, a1=(156, 178), a2=(-30, -50), l1=(10, -20), l2=(-20, -50), w=100)),
                    (bt(145.2), P(x=380, air=350, face=1, rot=24, lean=30, head=-20, a1=(84, 88), a2=(-40, -60), l1=(-30, -40), l2=(-50, -60), w=-20, mouth=1), 'snap'), (bt(147), P(x=440, air=340, face=1, rot=24, lean=34, head=-22, a1=(84, 88), a2=(-40, -60), l1=(-30, -40), l2=(-50, -60), w=-20, mouth=1)),
                    (bt(148), P(x=930, air=420, face=1, rot=10, lean=40, head=-24, a1=(86, 90), a2=(-40, -60), l1=(-40, -50), l2=(-60, -70), w=-8, mouth=1), 'ii')], H=305, mod=lambda p, t: dict(p, air=p['air'] + (8 * math.sin(t * 3) if p['air'] > 100 else 0)))
_xl = Act('xiaoyan', [(0, P(x=1440, face=-1, lean=8, head=-4, a1=(10, 30), a2=(-10, 0), l1=(20, 0), l2=(-20, -20))), (bt(138), P(x=1440, face=-1, lean=4, head=-16, a1=(30, 60), a2=(-20, 10), l1=(24, 0), l2=(-24, -20))),
                      (bt(139), P(x=1440, face=-1, lean=10, head=-10, a1=(70, 130), a2=(-50, 60), l1=(40, -10), l2=(-40, -40), glint=1.0), 'o'), (bt(142), P(x=1440, face=-1, lean=14, head=-6, a1=(64, 110), a2=(20, 100), l1=(44, -10), l2=(-40, -44), glint=1.0, mouth=1)),
                      (bt(144.6), P(x=1440, face=-1, lean=18, head=-10, a1=(60, 100), a2=(40, 104), l1=(54, -20), l2=(-40, -60), glint=1.0, mouth=1)), (bt(145), P(x=1400, air=140, face=-1, rot=-10, lean=10, head=-14, a1=(64, 104), a2=(44, 104), l1=(70, -30), l2=(-20, -30), glint=1.0, mouth=1), 'snap'),
                      (bt(147), P(x=1100, air=420, face=-1, lean=4, head=-4, a1=(86, 96), a2=(70, 100), l1=(20, -30), l2=(-14, -50), glint=1.0, mouth=1), 'o'), (bt(148), P(x=1075, air=440, face=-1, lean=-6, head=0, a1=(100, 92), a2=(60, 110), l1=(26, -30), l2=(-10, -56), glint=1.0, mouth=1), 'i')], held=False)
_cl = camk([(bt(136), (420, 700, 1.7, 0)), (bt(138), (420, 480, 1.5, -4), 'io'), (bt(140.9), (400, 440, 1.8, -6), 'lin'), (bt(141), (1400, 660, 2.3, 4), 'hold'), (bt(144.6), (1380, 650, 2.7, 6), 'lin'), (bt(145), (900, 520, 0.95, 0), 'snap'), (bt(147), (900, 470, 1.05, 0), 'lin'), (bt(148), (1000, 400, 1.5, -6), 'i')],
            [(bt(136.6), 10, 0.2), (bt(140), 16, 0.2), (bt(145), 30, 0.25), (bt(144), 6, 1.0)])
def s_lotus(t):
    b = (t - 0.5) / BEAT; acts = [_nl, _xl]; NJ = _nl.J(t); XJ = _xl.J(t); tip = _nl.wp(t, 0.66, 1.0); sun = min(1.0, max(0.0, (b - 138) / 6)); h1, h2 = XJ['h1'], XJ['h2']; m = ((h1[0] + h2[0]) / 2 - 26, (h1[1] + h2[1]) / 2); u = min(1.0, max(0.0, (b - 142) / 2.4))
    def ground(c):
        shadow(c, acts, t); A.puff(c, t, bt(136.6), (330, GY + 6), 24, 300, 120, 40, 200, 1.2, (0.86, 0.9, 0.96, 0.8), 1, vx=0); A.puff(c, t, bt(145), (1420, GY + 6), 30, 300, 160, 40, 200, 1.2, (0.86, 0.9, 0.96, 0.8), 2); A.debris(c, t, bt(145), (1420, GY), 30, 500, 1500, (0.5, 0.57, 0.68), seed=3, floor=GY + 10)
    def glow(c):
        A.ring(c, t, bt(136.6), (330, GY - 100), 700, 0.5, WIND, sq=1.0, w=24)
        if b >= 138 and b < 145.2:                                                        # 日光往剑尖上聚
            for i in range(26): ph = (t * 1.3 + rnd(i, 1)) % 1.0; th = rnd(i, 2) * 3.14 + 3.14; d = 900 * (1 - ph); p0 = (tip[0] + math.cos(th) * d, tip[1] + math.sin(th) * d * 0.8); c.move_to(*p0); c.line_to(p0[0] - math.cos(th) * 120, p0[1] - math.sin(th) * 96); c.set_source_rgba(1, 0.96, 0.75, 0.7 * ph * sun); c.set_line_width(5); c.stroke()
            A.burst(c, tip, 40 + 190 * sun, (1.0, 0.95, 0.7), 0.95, rays=16, t=t, seed=5)
        if b >= 145.2: d = NJ['wd']; q = _nl.wp(t, 0.66, 0.6); A.burst(c, q, 300, (1.0, 0.96, 0.75), 1.0, rays=10, t=t, seed=6); c.move_to(*q); c.line_to(q[0] - d[0] * 1500 * min(1, (b - 145.2)), q[1] - d[1] * 1500 * min(1, (b - 145.2))); c.set_source_rgba(1, 0.97, 0.8, 0.8); c.set_line_width(70); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        if b >= 139:
            k = min(1.0, (b - 139) / 0.6)
            for (hh, col, sd) in ((h1, CYAN, 3), (h2, PURP, 4)): A.flame(c, t, lambda dt, sv, hh=hh: (hh[0] + (m[0] - hh[0]) * u + (sv - 0.5) * 20, hh[1] + (m[1] - hh[1]) * u - 6), 34, 0.4, 280, 30 * (1 - 0.4 * u), col, a=0.95 * k, seed=sd)
            if u > 0.3: lotus(c, m, 12 + 60 * (u - 0.3) / 0.7 + (40 * (b - 145) / 3 if b > 145 else 0), t, a=min(1.0, (u - 0.3) * 3))
        A.ring(c, t, bt(145), (1420, GY + 8), 800, 0.5, CYAN, w=26); A.sparks(c, t, bt(145), (1420, GY), 50, 90, 80, 500, 2400, 0.55, CYAN, seed=7, g=900)
    fr, mask, gl, M = A.render(R, PL('yunlan'), _cl(t), [('over', ground), ('back', lambda c: (aura(c, _nl, t, WIND, k=0.6, seed=21), aura(c, _xl, t, CYAN if int(t * 8) % 2 else PURP, k=0.5 * min(1, max(0, b - 139))))), ('chars', lambda c: [a.draw(c, t) for a in acts]), ('glow', glow)])
    fr = hits(fr, t, mask, gl, M, [(bt(136.6), (330, GY - 100), (2, 3)), (bt(140), tip, (3, 2, 3)), (bt(145), (1420, GY), (2, 2, 3))])
    if 145.1 < b: fr = A.speedlines(fr, t, R, a=0.45, ang=-14, n=40, col=(1, 1, 0.9))
    if 141 <= b < 144.6: fr = A.focuslines(fr, t, R, (R.w * 0.5, R.h * 0.5), a=0.4, n=60, r0=0.42, col=(0.85, 0.9, 1))
    fr = fin(fr); fr = fr + (1 - fr) * max(0.0, (b - 147.6) / 0.4) ** 2
    fr = cap(fr, t, 136.8, 139.8, '她没败。斗气铠甲，日光聚到剑上'); fr = slam(fr, t, 140, 143.6, '风之极·陨杀', (1300, 420), px=200, glow=(255, 230, 120), big=2.6, rot=4); fr = cap(fr, t, 141.2, 144.6, '青莲地心火，加上一朵紫火，硬压进一朵莲里')
    return slam(fr, t, 145.2, 147.8, '佛怒火莲', (560, 820), px=240, glow=(170, 90, 255), big=2.8, rot=-4)

SHOTS = [(0, 4, s_hook), (4, 32, s_stele), (32, 64, s_hall), (64, 80, s_ring), (80, 96, s_train), (96, 116, s_swallow), (116, 129, s_fight), (129, 136, s_baji), (136, 148, s_lotus)]
def frame(t):
    b = (t - 0.5) / BEAT
    for (b0, b1, fn) in SHOTS:
        if b0 <= b < b1 or (b0 == 0 and b < 0): return fn(t)
    return np.zeros((R.h, R.w, 3), np.float32)
def u8(fr): return (np.clip(fr, 0, 1) * 255).astype(np.uint8)
if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'full'
    if cmd == 'strip':
        ims = [cv2.resize(u8(frame(bt(float(x)))), (480, 270), interpolation=cv2.INTER_AREA) for x in sys.argv[2:]]
        while len(ims) % 4: ims.append(np.zeros_like(ims[0]))
        Image.fromarray(np.vstack([np.hstack(ims[i:i + 4]) for i in range(0, len(ims), 4)])).save('out/_strip.jpg', quality=88)
    elif cmd == 'seg':
        i, k = int(sys.argv[2]), int(sys.argv[3]); n = int(DUR * FPS); p = fight._enc(f'out/_fseg{R.h}_{i:02d}.mp4')
        for j in range(n * i // k, n * (i + 1) // k): p.stdin.write(u8(frame(j / FPS)).tobytes())
        p.stdin.close(); p.wait()
    else:
        k = max(1, (os.cpu_count() or 2)) * 2; out = f'out/xiaoyan1_{R.h}p.mp4'; subprocess.run([sys.executable, 'mixfilm.py'], check=True); nproc = os.cpu_count() or 2
        for g in range(0, k, nproc):
            if any(p.wait() for p in [subprocess.Popen([sys.executable, 'film.py', 'seg', str(i), str(k)]) for i in range(g, min(k, g + nproc))]): sys.exit('有分段渲染失败')
        open('out/_fcat.txt', 'w').write(''.join(f"file '_fseg{R.h}_{i:02d}.mp4'\n" for i in range(k)))
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'out/_fcat.txt', '-i', 'out/mixfilm.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out], check=True); print('done', out)
