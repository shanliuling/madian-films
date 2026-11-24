"""film — 萧炎（上）《莫欺少年穷》。分镜见 script.md，时间轴按系列 BGM 的拍子（第 n 拍 = 0.50 + 0.59413n 秒），全曲从头放到尾。
    python film.py                → out/xiaoyan1_540p.mp4（RES=1080 出 1080p；FPS=30 出 30 帧）
    python film.py strip 10 12.5  → out/_strip.jpg（看这几拍的画面）
每个镜头是一个函数 shot(t)（t = 全片秒数），登记在 SHOTS 里：(起拍, 止拍, 函数)。三年之约开打那段直接用 fight.py。"""
import _env, os, sys, math, subprocess, functools, numpy as np, cv2, cairo
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from stage import Out
from paper import layer, rgba, FONT
import action as A, fighter as F, yunlan, sets, fight, fx
from action import track, rnd, pulse
R = fight.R; FPS = fight.FPS; BEAT = 0.59413; GY = yunlan.GY; P = F.P
def bt(b): return 0.50 + b * BEAT
DUR = 0.50 + 254 * 0.59413; CYAN = (0.25, 1.0, 0.80); PURP = (0.72, 0.35, 1.0); WHITEF = (0.82, 0.92, 1.0); WIND = (0.62, 0.98, 1.0); GOLD = (1.0, 0.80, 0.36)
@functools.lru_cache(maxsize=None)
def PL(name):
    if name == 'yunlan': return yunlan.plates(R)
    if name == 'dusk': return A.tint(yunlan.plates(R), (0.95, 0.60, 0.62))
    if name in ('stele', 'hall', 'border', 'wild'): return getattr(sets, name)(R)
    return sets.night(R, 'wild' if name == 'wild_n' else name)
class Act:
    """一个演员：造型 + 姿态关键帧。who='xiaoyan' 用萧炎的专门画法，其余走 F.figure。"""
    def __init__(s, who, keys, H=330, mod=None, **kw): s.who, s.f, s.H, s.mod, s.kw = who, track(keys), H, mod, kw; s.c = {}
    def J(s, t):
        t = round(t, 4)
        if t not in s.c:
            if len(s.c) > 6000: s.c.clear()
            p = dict(s.f(t)); p = s.mod(p, t) if s.mod else p; s.c[t] = F.kin(p, s.H, GY)
        return s.c[t]
    wingf = None
    def draw(s, c, t, alpha=1.0, **kw):
        if s.wingf and alpha >= 1.0:
            o = s.wingf(t)
            if o > 0.02: wings(c, s.J(t), t, op=o)
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
    """侧面看的火莲（glow 层）。"""
    fx.lotus(c, pos, r * 1.3, t, ca, cb, tilt=0.62, a=a * 0.62, spin=3.0)
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
NOCAP = False
KEEP = ('祖传的玉片里，父亲的灵魂光点还在——人还活着', '萧家大厅', '云岚宗 · 三年之约', '乌坦城 · 萧家', '云岚宗', '加玛帝国 · 边境', '上 · 莫欺少年穷', '三年前', '他是萧家百年之内，最年轻的斗者', '一夜之间，斗之气旋化为乌有', '云岚宗送来一枚聚气散，当作退婚的赔礼', '吞噬异火，就算备齐了丹药，成功率也只有一成', '纳兰嫣然，败？',
        '三年前那张休证。纸折旧了，血手印还在', '三天前，三个黑袍人夜袭萧家', '父亲萧战追了出去，再没有回来', '黑袍人留下的能量痕迹，属于云岚宗的首席长老', '赢了三年之约的人，成了加玛帝国容不下的人', '路上，药老第一次提起了一个名字')
def cap(fr, t, b0, b1, s, force=False, **kw):
    if not force and (NOCAP or s.startswith('「好一句') or not (s.startswith('「') or s in KEEP or '：「' in s)): return fr
    if bt(b0) <= t < bt(b1): fr = caption(fr, s, a=min(1.0, (t - bt(b0)) / 0.12, (bt(b1) - t) / 0.12), **kw)
    return fr
_slc = {}
KT = {'莫欺少年穷': dict(style='slam', lay=lambda p, px: fx.vcol(290, 190, px, 5, 1.05), px=165, step=0.5, glow=(255, 70, 50), hold=1),            # 竖排，半拍砸一个字
      '焚诀': dict(style='burn', lay=lambda p, px: fx.vcol(p[0], p[1] - px * 0.5, px, 2, 1.05), step=0.3, glow=(200, 230, 255)),
      '玄重尺': dict(style='drop', lay=lambda p, px: fx.vcol(p[0], p[1] - px, px, 3, 1.02), step=0.18),
      '青莲地心火': dict(style='burn', lay=lambda p, px: fx.hrow(p[0] - 2 * px * 0.95, p[1], px, 5), step=0.2),
      '八极崩': dict(style='burst', lay=lambda p, px: fx.hrow(300, 480, px * 0.9, 3, rot=12), px=290, step=0.1, rot=12, origin=(1120, 640)),         # 从命中点沿出拳方向炸出去
      '风之极 陨杀': dict(style='drop', lay=lambda p, px: fx.hrow(p[0] - 2.5 * px * 0.95, p[1], px, 6), step=0.12),
      '佛怒火莲': dict(style='burn', lay=lambda p, px: fx.arc((p[0], p[1] + 330), 440, 138, 42, 4), px=215, step=0.25),                              # 沿着莲花外圈烧出来
      '云山': dict(style='drop', lay=lambda p, px: fx.hrow(p[0] - px * 0.5, p[1], px, 2, 1.0), step=0.3),
      '骨灵冷火': dict(style='burn', lay=lambda p, px: fx.hrow(p[0] - 1.5 * px * 0.95, p[1], px, 4), step=0.2),
      '炎帝': dict(style='burn', lay=lambda p, px: fx.hrow(p[0] - px * 0.5, p[1], px, 2, 1.0), step=0.6),
      '魂殿': dict(style='drag', lay=lambda p, px: [(p[0] - px * 0.52, p[1]), (p[0] + px * 0.52, p[1])], step=0.25)}                                  # 两边的锁链拖进来
def slam(fr, t, b0, b1, s, pos, px=220, vertical=False, glow=(60, 255, 210), col=(255, 255, 255), big=2.6, rot=0.0):
    if NOCAP: return fr
    if s in KT:
        k = KT[s]; return fx.ktext(fr, R, t, s, bt(b0), bt(b1 + k.get('hold', 0)), k['lay'](pos, k.get('px', px)), px=k.get('px', px), style=k['style'], glow=k.get('glow', glow), step=k.get('step', 0) * BEAT, rot=k.get('rot', 0), origin=k.get('origin'))
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
CAMO = None
def camk(keys, shakes=()):
    f = track(keys)
    def cam(t): cx, cy, z, ro = f(t); dx, dy = A.shake(t, shakes, FPS); base = (cx + dx / z, cy + dy / z, z, ro); return CAMO(t, base) if CAMO else base
    return cam
def withcam(fn, t, camo):
    """用另一个镜头重拍 fn 的这一刻（不带字幕）。camo(t, 原镜头) → (cx, cy, 放大, 旋转)。"""
    global CAMO, NOCAP; CAMO, NOCAP = camo, True
    try: return fn(t)
    finally: CAMO, NOCAP = None, False
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
        if b > 135: A.burst(c, (330, GY - 60), 50 + 90 * (b - 135), WIND, 0.3 * (b - 135))                                                              # 尘里亮起风的青光
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
        if b >= 145.2: d = NJ['wd']; q = _nl.wp(t, 0.66, 0.6); A.burst(c, q, 110, (1.0, 0.96, 0.75), 0.9, rays=10, t=t, seed=6); c.move_to(*q); c.line_to(q[0] - d[0] * 1500 * min(1, (b - 145.2)), q[1] - d[1] * 1500 * min(1, (b - 145.2))); c.set_source_rgba(1, 0.97, 0.8, 0.6); c.set_line_width(30); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        if b >= 139:
            k = min(1.0, (b - 139) / 0.6)
            for (hh, col, sd) in ((h1, CYAN, 3), (h2, PURP, 4)): A.flame(c, t, lambda dt, sv, hh=hh: (hh[0] + (m[0] - hh[0]) * u + (sv - 0.5) * 20, hh[1] + (m[1] - hh[1]) * u - 6), 34, 0.4, 280, 30 * (1 - 0.4 * u), col, a=0.95 * k, seed=sd)
            if u > 0.3: lotus(c, m, 16 + 70 * (u - 0.3) / 0.7 + (60 * (b - 145) / 3 if b > 145 else 0), t, a=min(1.0, (u - 0.3) * 3))
        A.ring(c, t, bt(145), (1420, GY + 8), 800, 0.5, CYAN, w=26); A.sparks(c, t, bt(145), (1420, GY), 50, 90, 80, 500, 2400, 0.55, CYAN, seed=7, g=900)
    fr, mask, gl, M = A.render(R, PL('yunlan'), _cl(t), [('over', ground), ('back', lambda c: (aura(c, _nl, t, WIND, k=0.6, seed=21), aura(c, _xl, t, CYAN if int(t * 8) % 2 else PURP, k=0.5 * min(1, max(0, b - 139))))), ('chars', lambda c: [a.draw(c, t) for a in acts]), ('glow', glow)])
    fr = hits(fr, t, mask, gl, M, [(bt(136.6), (330, GY - 100), (2, 3)), (bt(140), tip, (3, 2, 3)), (bt(145), (1420, GY), (2, 2, 3))])
    if 145.1 < b: fr = A.speedlines(fr, t, R, a=0.45, ang=-14, n=40, col=(1, 1, 0.9))
    if 141 <= b < 144.6: fr = A.focuslines(fr, t, R, (R.w * 0.5, R.h * 0.5), a=0.4, n=60, r0=0.42, col=(0.85, 0.9, 1))
    fr = fin(fr); fr = fr + (1 - fr) * max(0.0, (b - 147.6) / 0.4) ** 2
    fr = cap(fr, t, 136.8, 139.8, '她没败。斗气铠甲，日光聚到剑上'); fr = slam(fr, t, 140, 143.6, '风之极 陨杀', (1300, 420), px=200, glow=(255, 230, 120), big=2.6, rot=4); fr = cap(fr, t, 141.2, 144.6, '青莲地心火，加上一朵紫火，硬压进一朵莲里')
    return slam(fr, t, 145.2, 147.8, '佛怒火莲', (560, 820), px=240, glow=(170, 90, 255), big=2.8, rot=-4)

# ================= 148–166 约毕：休书、两指夹剑
_na = Act('nalan', [(0, P(x=900, air=420, face=1, rot=-70, lean=-30, head=30, a1=(130, 160), a2=(110, 150), l1=(70, 30), l2=(50, 10), w=140)), (bt(149.6), P(x=700, air=0, face=1, rot=0, lean=40, head=20, a1=(30, 40), a2=(20, 30), l1=(80, -70), l2=(10, -88), w=-80), 'i'),
                    (bt(156), P(x=700, face=1, lean=34, head=24, a1=(30, 40), a2=(20, 30), l1=(80, -70), l2=(10, -88), w=-80)), (bt(158.6), P(x=700, face=1, lean=4, head=-10, a1=(60, 150), a2=(20, 30), l1=(80, -70), l2=(10, -88), w=186, eye=0.0), 'io'),          # 横剑
                    (bt(166), P(x=700, face=1, lean=6, head=-6, a1=(60, 150), a2=(20, 30), l1=(80, -70), l2=(10, -88), w=186, eye=1.0))], H=305)
_xa = Act('xiaoyan', [(0, P(x=1150, air=440, face=-1, lean=-6, a1=(100, 92), a2=(60, 110), l1=(26, -30), l2=(-10, -56))), (bt(149.8), P(x=1180, face=-1, lean=30, head=10, a1=(30, 40), a2=(20, 30), l1=(70, -60), l2=(0, -80)), 'i'), (bt(151), P(x=1180, face=-1, lean=10, head=-10, a1=(20, 40), a2=(10, 30), l1=(20, 0), l2=(-20, -20)), 'io'),
                      (bt(152), P(x=1180, face=-1, lean=4, head=6, a1=(60, 110), a2=(10, 30), l1=(20, 0), l2=(-20, -20))), (bt(159.5), P(x=1180, face=-1, lean=4, head=6, a1=(60, 110), a2=(10, 30), l1=(20, 0), l2=(-20, -20))),
                      (bt(160), P(x=840, face=-1, lean=30, head=-10, a1=(96, 84), a2=(-30, -40), l1=(50, 0), l2=(-40, -40)), 'i'), (bt(164), P(x=840, face=-1, lean=22, head=-6, a1=(96, 84), a2=(-30, -40), l1=(44, 0), l2=(-36, -36))),
                      (bt(164.4), P(x=860, face=1, lean=6, head=0, a1=(6, 16), a2=(-6, 10), l1=(10, 0), l2=(-10, -10)), 'io'), (bt(166), P(x=1100, face=1, lean=10, head=4, a1=(6, 16), a2=(-6, 10))), ], held=False,
            mod=lambda p, t: dict(p, l1=(26 * math.sin(p['x'] / 30), 26 * math.sin(p['x'] / 30) - 14), l2=(-26 * math.sin(p['x'] / 30), -26 * math.sin(p['x'] / 30) - 14)) if t > bt(164.4) else p)
_pap = track([(bt(150), (760, 560)), (bt(151), (900, 480), 'io'), (bt(152), (1110, 640), 'io'), (bt(166), (1110, 640))])
_ca = camk([(bt(148), (960, 480, 1.0, 0)), (bt(150), (940, 620, 1.25, 0), 'io'), (bt(152), (960, 640, 1.4, 0), 'lin'), (bt(156), (800, 660, 1.6, 0), 'hold'), (bt(159.6), (760, 650, 1.9, 0), 'lin'), (bt(161.5), (770, 640, 2.0, 0), 'hold'), (bt(164), (780, 640, 2.2, 0), 'lin'), (bt(166), (900, 620, 1.3, 0), 'io')], [(bt(149.6), 20, 0.2), (bt(160), 20, 0.2)])
def _closeup(t, draw, bg0, bg1, shakes=()):
    s, c = layer(R.w, R.h); c.scale(R.k, R.k); sh = A.shake(t, shakes, FPS); c.translate(960 + sh[0], 540 + sh[1]); g = cairo.LinearGradient(0, -540, 0, 540); g.add_color_stop_rgb(0, *bg0); g.add_color_stop_rgb(1, *bg1); c.set_source(g); c.paint(); draw(c); return rgba(s)[0].copy()
def s_after(t):
    b = (t - 0.5) / BEAT
    if 152 <= b < 156:                                                                    # ▲ 那张纸
        def d(c):
            z = 1.1 + 0.08 * (b - 152) / 4; c.scale(z, z); c.rotate(0.06 + 0.02 * math.sin(t * 2)); c.rectangle(-330, -430, 660, 860); c.set_source_rgb(0.86, 0.80, 0.66); c.fill()
            for x in (-110, 110): c.move_to(x, -430); c.line_to(x, 430); c.set_source_rgba(0.4, 0.3, 0.2, 0.5); c.set_line_width(4); c.stroke()
            c.move_to(-330, 0); c.line_to(330, 0); c.stroke()
            for i in range(7):
                c.set_source_rgba(0.1, 0.1, 0.12, 0.6); c.set_line_width(9); x = 250 - i * 62
                for j in range(9): y = -370 + j * 46; c.move_to(x - 14 + 8 * rnd(i, j), y); c.line_to(x + 12 * rnd(j, i), y + 26); c.stroke()
            c.set_source_rgba(0.42, 0.10, 0.08, 0.85); c.save(); c.translate(-120, 190); c.arc(0, 30, 78, 0, 7); c.fill()
            for i, (ax, ln) in enumerate(((-66, 110), (-30, 150), (8, 160), (44, 140))): c.save(); c.translate(ax, -30); c.rotate((i - 1.5) * 0.12); c.rectangle(-17, -ln, 34, ln); c.arc(0, -ln, 17, 0, 7); c.fill(); c.restore()
            c.save(); c.translate(86, 30); c.rotate(1.0); c.rectangle(-19, -100, 38, 100); c.arc(0, -100, 19, 0, 7); c.fill(); c.restore(); c.restore()
        fr = fin(_closeup(t, d, (0.45, 0.62, 0.86), (0.78, 0.86, 0.95))); return cap(fr, t, 152.3, 156, '三年前那张休证。纸折旧了，血手印还在')
    if 160 <= b < 163:                                                                    # ▲ 两指夹住剑刃
        def d(c): z = 0.86 + 0.035 * (b - 160); c.scale(z, z); c.translate(40, 30); fx.pinch(c, t, bt(160))
        fr = _closeup(t, d, (0.42, 0.60, 0.86), (0.80, 0.88, 0.96), [(bt(160), 30, 0.25)]); n = int(round((t - bt(160)) * 60))
        if 0 <= n < 3: fr = 1 - fr
        return cap(fin(fr), t, 161.4, 164, '「我对收你为奴为婢，并没有太大兴趣。」')
    pp = _pap(t); acts = [_na, _xa]
    def chars(c):
        [a.draw(c, t, held=(b < 149 or b >= 157) if a is _na else False) for a in acts]
        if 150 <= b < 152: c.save(); c.translate(pp[0], pp[1]); c.rotate(math.sin(t * 5) * 0.5 * (1 if b < 152 else 0)); c.rectangle(-14, -20, 28, 40); c.set_source_rgb(0.9, 0.85, 0.7); c.fill_preserve(); c.set_source_rgb(0.05, 0.06, 0.1); c.set_line_width(3); c.stroke(); c.restore()
    def ground(c): shadow(c, acts, t); A.puff(c, t, bt(149.6), (700, GY + 6), 22, 240, 100, 30, 160, 1.1, (0.86, 0.9, 0.96, 0.75), 1); A.puff(c, t, bt(149.8), (1180, GY + 6), 16, 160, 80, 26, 130, 0.9, (0.86, 0.9, 0.96, 0.7), 2)
    fr, mask, gl, M = A.render(R, PL('yunlan'), _ca(t), [('over', ground), ('chars', chars), ('glow', lambda c: A.emit(c, t, bt(148), bt(151), 40, lambda tb: (500 + 900 * rnd(int(tb * 61), 1), 200 + 300 * rnd(int(tb * 61), 2)), ang=270, spread=60, v0=100, v1=500, life=1.2, col=PURP if int(t * 7) % 2 else CYAN, w=4, g=300, seed=5))])
    fr = fin(fr); fr = fr + (1 - fr) * max(0.0, 1 - (b - 148) / 1.4)
    fr = cap(fr, t, 150.2, 152, '她怀里，飘出一张白纸'); fr = cap(fr, t, 156.3, 159.8, '她认了输，横剑就往脖子上抹'); fr = cap(fr, t, 161.5, 164, '「我对收你为奴为婢，并没有太大兴趣。」'); fr = slam(fr, t, 164.3, 166, '三年之约 结束', (960, 330), px=200, glow=(40, 255, 200), big=2.0)
    return fr * min(1.0, max(0.0, (166 - b) / 0.5) + 0.0) if b > 165.5 else fr

# ================= 166–193 代价：萧家被袭、父亲失踪（音乐安静）
_wlk = lambda p, t: dict(p, l1=(24 * math.sin(p['x'] / 30), 24 * math.sin(p['x'] / 30) - 12), l2=(-24 * math.sin(p['x'] / 30), -24 * math.sin(p['x'] / 30) - 12))
_xg = Act('xiaoyan', [(bt(166), P(x=120, lean=8, a1=(6, 16), a2=(-6, 10))), (bt(169), P(x=640, lean=8, a1=(6, 16), a2=(-6, 10)), 'lin'), (bt(169.3), P(x=650, lean=0, head=-10, a1=(6, 16), a2=(-6, 10)), 'o'), (bt(170), P(x=650, lean=0, head=-10))], back=True, held=False, mod=lambda p, t: _wlk(p, t) if t < bt(169) else p)
_zg = Act('xiaozhan', [(0, P(x=960, lean=0, head=-20, a1=(10, 30), a2=(-10, 0))), (bt(172), P(x=960, lean=-6, head=-24, a1=(40, 100), a2=(-30, -20), l1=(20, 0), l2=(-20, -20))), (bt(173.8), P(x=940, lean=-10, head=-20, a1=(60, 120), a2=(40, 110), l1=(24, 0), l2=(-24, -20), mouth=1)),
                       (bt(174), P(x=1000, lean=34, head=-10, a1=(90, 90), a2=(80, 86), l1=(50, -4), l2=(-40, -50), mouth=1), 'ii'), (bt(175.6), P(x=1010, lean=20, head=-20, a1=(40, 60), a2=(-20, -30), l1=(40, 0), l2=(-30, -40))), (bt(178), P(x=2300, lean=40, head=-20, a1=(-30, 40), a2=(40, 90), mouth=1), 'i')], H=340, mod=lambda p, t: _wlk(p, t) if t > bt(175.6) else p)
_hg = [Act('hood', [(0, P(x=x0, air=900, face=fc, lean=0)), (bt(170.6 + 0.3 * i), P(x=x0, air=900, face=fc)), (bt(172 + 0.3 * i), P(x=x0, air=230 + 40 * i, face=fc, lean=4), 'o'), (bt(173.9), P(x=x0, air=220 + 40 * i, face=fc, lean=10, a1=(70, 100))),
                    (bt(174.3), P(x=x0 + 80, air=300, face=1, lean=-10, a1=(30, 60)), 'o'), (bt(176.6), P(x=x0 + 1700, air=700, face=1, lean=40), 'i'), (bt(178), P(x=x0 + 2600, air=900, face=1, lean=40))], H=340, mod=lambda p, t, i=i: dict(p, air=p['air'] + 12 * math.sin(t * 2 + i))) for i, (x0, fc) in enumerate(((620, 1), (1330, -1), (1560, -1)))]
_cg = camk([(bt(166), (700, 560, 1.0, 0)), (bt(170), (860, 580, 1.15, 0), 'lin'), (bt(170.02), (960, 480, 0.95, 0), 'hold'), (bt(174), (980, 500, 1.05, 0), 'lin'), (bt(178), (1250, 520, 1.1, 0), 'io')], [(bt(174), 26, 0.25)])
_xd = Act('xiaoyan', [(0, P(x=960, lean=6, head=26, a1=(6, 16), a2=(-6, 10), eye=0.0)), (bt(188.6), P(x=960, lean=6, head=26, a1=(6, 16), a2=(-6, 10), eye=0.0)), (bt(190), P(x=960, lean=2, head=-4, a1=(6, 16), a2=(-6, 10), eye=0.0), 'io'), (bt(190.1), P(x=960, lean=2, head=-6, eye=1.2, glint=1.0), 'snap'), (bt(193), P(x=960, lean=2, head=-6, eye=1.0, glint=1.0))], back=True, held=False)
_HD = _xd.J(bt(192))['head']; _cd = camk([(bt(186), (_HD[0] + 30, _HD[1] + 30, 2.6, 0)), (bt(190), (_HD[0] + 30, _HD[1] + 10, 3.2, 0), 'lin'), (bt(190.1), (_HD[0] + 30, _HD[1], 3.8, -3), 'snap'), (bt(193), (_HD[0] + 30, _HD[1], 4.2, -3), 'lin')], [(bt(190.1), 14, 0.2)])
def s_home(t):
    b = (t - 0.5) / BEAT
    if b < 170:
        fr, mask, gl, M = A.render(R, PL('gate'), _cg(t), [('over', lambda c: shadow(c, [_xg], t)), ('chars', lambda c: _xg.draw(c, t))]); fr = fin(fr) * min(1.0, (b - 166) * 2)
        fr = cap(fr, t, 166.4, 170, '乌坦城 · 萧家', y=80, px=58, col=(255, 226, 170)); return cap(fr, t, 166.8, 170, '他回到家。大门口，一个门卫都没有')
    if b < 178:                                                                           # 三天前（整个画面压成暗红）
        acts = [_zg] + _hg
        def glow(c):
            A.ring(c, t, bt(174), (1160, 560), 800, 0.5, (1, 0.3, 0.3), sq=1.0, w=30); A.sparks(c, t, bt(174), (1160, 560), 60, 0, 180, 400, 2400, 0.6, (1, 0.4, 0.3), seed=4)
            if 174 <= b < 174.8: A.burst(c, (1160, 560), 500 * (1 - math.exp(-(t - bt(174)) / 0.05)), (1, 0.3, 0.3), math.exp(-(t - bt(174)) / 0.12), rays=18, t=t, seed=5)
        fr, mask, gl, M = A.render(R, PL('gate'), _cg(t), [('over', lambda c: shadow(c, [_zg], t)), ('back', lambda c: [aura(c, h, t, (0.5, 0.1, 0.6), n=20, k=0.5, seed=30 + i) for i, h in enumerate(_hg)]), ('chars', lambda c: [a.draw(c, t) for a in acts]), ('glow', glow)])
        fr = hits(fr, t, mask, gl, M, [(bt(174), (1160, 560), (2, 2, 3))]); fr = fin(fr); g = fr.mean(-1, keepdims=True); fr = g * np.float32((1.25, 0.62, 0.58)) * 0.6 + fr * 0.4
        fr = cap(fr, t, 170.2, 174, '三天前，三个黑袍人夜袭萧家'); return cap(fr, t, 174.4, 178, '父亲萧战追了出去，再没有回来')
    if b < 186:                                                                           # ▲ 玉片里的光点
        def d(c):
            c.scale(1.9, 1.9); c.rotate(-0.06); c.new_path(); c.arc(-170, -120, 60, 3.14, 4.71); c.arc(170, -120, 60, 4.71, 6.283); c.arc(170, 120, 60, 0, 1.57); c.arc(-170, 120, 60, 1.57, 3.14); c.close_path(); g = cairo.LinearGradient(0, -180, 0, 180); g.add_color_stop_rgb(0, 0.62, 0.86, 0.74); g.add_color_stop_rgb(1, 0.30, 0.56, 0.48); c.set_source(g); c.fill_preserve(); c.set_source_rgb(0.03, 0.08, 0.08); c.set_line_width(8); c.stroke()
            c.set_source_rgba(0.1, 0.3, 0.26, 0.6); c.set_line_width(4); c.rectangle(-190, -140, 380, 280); c.stroke(); wtext(c, '萧', 0, 0, 200, (0.1, 0.3, 0.26), 0.35)
            p = (150 * math.sin(t * 1.1), 90 * math.sin(t * 1.7 + 1)); A.burst(c, p, 30 + 6 * math.sin(t * 9), (1.0, 0.95, 0.7), 1.0)
            for k in range(1, 14): tt = t - k * 0.03; A.burst(c, (150 * math.sin(tt * 1.1), 90 * math.sin(tt * 1.7 + 1)), 14 - k * 0.8, (1.0, 0.9, 0.6), 0.5 - k * 0.035)
        fr = fin(_closeup(t, d, (0.02, 0.03, 0.08), (0.06, 0.08, 0.16))) * min(1.0, (b - 178) * 3)
        fr = cap(fr, t, 178.4, 182, '祖传的玉片里，父亲的灵魂光点还在——人还活着'); return cap(fr, t, 182.3, 186, '黑袍人留下的能量痕迹，属于云岚宗的首席长老')
    k = min(1.0, max(0.0, (b - 190) * 10)); fr, mask, gl, M = A.render(R, PL('wild_n'), _cd(t), [('back', lambda c: aura(c, _xd, t, CYAN, n=50, k=0.7 * k, rise=600)), ('chars', lambda c: _xd.draw(c, t))])
    fr = hits(fr, t, mask, gl, M, [(bt(190.1), _HD, (2, 3))]); fr = fin(fr) * (0.25 + 0.75 * min(1.0, max(0.0, (b - 186) / 4)) if b < 190 else 1.0)
    return cap(fr, t, 187, 193, '「此次，他必须死。谁阻，谁死。」')

# ================= 193–248 再上云岚宗：云韵、云棱、云山、药老借体
def wings(c, J, t, op=1.0, S=430, glow=False, qi=False, cb=PURP):
    """侧面的一对翼（紫云翼；qi=True 是斗气化翼）：远的一只小一点、在后面。"""
    o = J['chest']; f = J['f']; fx.wing(c, (o[0] - f * 16, o[1] - 12), -f, S * 0.76, op, t, glow=glow, qi=qi, cb=cb, flap=26, seed=2); fx.wing(c, (o[0] - f * 6, o[1]), -f, S, op, t, glow=glow, qi=qi, cb=cb, flap=4)
_x2 = Act('xiaoyan', [(bt(193), P(x=-300, air=700, rot=64, lean=20, head=-30, a1=(-40, -20), a2=(-30, -10), l1=(-10, -20), l2=(-30, -40))), (bt(197.6), P(x=960, air=440, rot=58, lean=20, head=-30, a1=(-40, -20), a2=(-30, -10), l1=(-10, -20), l2=(-30, -40)), 'lin'),
    (bt(198), P(x=1100, lean=44, head=-20, a1=(40, 60), a2=(-30, -40), l1=(74, -40), l2=(-40, -84)), 'i'), (bt(199.4), P(x=1100, lean=6, head=-8, a1=(10, 30), a2=(-10, 0), l1=(20, 0), l2=(-20, -20)), 'io'), (bt(199.5), P(x=1100, face=-1, lean=4, head=-14, a1=(10, 30), a2=(-10, 0), l1=(20, 0), l2=(-20, -20)), 'hold'),
    (bt(207.6), P(x=1100, face=-1, lean=4, head=-4, a1=(10, 30), a2=(-10, 0), l1=(20, 0), l2=(-20, -20))), (bt(208.4), P(x=1100, face=-1, lean=14, head=-6, a1=(64, 110), a2=(20, 100), l1=(44, -10), l2=(-40, -44), glint=1.0, mouth=1), 'o'), (bt(210.8), P(x=1100, face=-1, lean=4, head=-8, a1=(60, 120), a2=(40, 110), l1=(44, -10), l2=(-40, -44), glint=1.0, mouth=1)),
    (bt(211), P(x=1060, face=-1, lean=36, head=-20, a1=(90, 90), a2=(-40, -60), l1=(66, -10), l2=(-50, -60), glint=1.0, mouth=1), 'ii'), (bt(214), P(x=1060, face=-1, lean=14, head=-30, a1=(30, 50), a2=(-10, 0), l1=(30, 0), l2=(-24, -24))),
    (bt(217), P(x=1060, face=-1, lean=24, head=-20, a1=(30, 60), a2=(10, 40), l1=(50, -30), l2=(-10, -60), mouth=1), 'io'), (bt(222), P(x=1060, face=-1, lean=40, head=-10, a1=(40, 50), a2=(20, 30), l1=(80, -70), l2=(10, -88), mouth=1), 'io'), (bt(226.5), P(x=1060, face=-1, lean=74, head=30, a1=(60, 80), a2=(50, 70), l1=(86, -80), l2=(30, -90), eye=0.0), 'io'), (bt(230.8), P(x=1060, face=-1, lean=74, head=30, a1=(60, 80), a2=(50, 70), l1=(86, -80), l2=(30, -90), eye=0.0)),
    (bt(231.7), P(x=1150, air=300, face=-1, lean=-6, head=-4, a1=(30, 60), a2=(-30, -10), l1=(10, -10), l2=(-10, -30), glint=1.0), 'io'), (bt(232), P(x=1010, air=330, face=-1, rot=-8, lean=30, head=-16, a1=(90, 90), a2=(-40, -60), l1=(40, -30), l2=(-50, -60), glint=1.0, mouth=1), 'ii'),
    (bt(232.5), P(x=600, air=400, face=-1, lean=20, head=-10, a1=(60, 80), a2=(-40, -60), l1=(30, -30), l2=(-40, -60), glint=1.0), 'o'), (bt(233.5), P(x=480, air=430, face=1, lean=10, head=-10, a1=(-40, 30), a2=(40, 80), l1=(20, -30), l2=(-30, -60), glint=1.0), 'hold'),
    (bt(234), P(x=880, air=450, face=1, rot=8, lean=30, head=-16, a1=(90, 90), a2=(-40, -60), l1=(40, -30), l2=(-50, -60), glint=1.0, mouth=1), 'ii'), (bt(234.5), P(x=1250, air=340, face=1, lean=20, head=-10, a1=(60, 80), a2=(-40, -60), l1=(30, -30), l2=(-40, -60), glint=1.0), 'o'),
    (bt(235.5), P(x=1340, air=320, face=-1, lean=-10, head=-6, a1=(20, 60), a2=(-20, 20), l1=(60, -40), l2=(-20, -60), glint=1.0), 'hold'), (bt(236), P(x=1060, air=370, face=-1, rot=-30, lean=-20, head=10, a1=(-30, 20), a2=(-60, -20), l1=(96, 90), l2=(-20, -80), glint=1.0, mouth=1), 'ii'),             # 一脚
    (bt(237), P(x=1260, air=360, face=-1, lean=-8, head=-6, a1=(150, 170), a2=(140, 160), l1=(10, -20), l2=(-20, -50), glint=1.0), 'io'), (bt(239.8), P(x=1270, air=370, face=-1, lean=-12, head=-8, a1=(156, 176), a2=(146, 166), l1=(10, -20), l2=(-20, -50), glint=1.0, mouth=1)),
    (bt(240), P(x=1240, air=360, face=-1, lean=26, head=-14, a1=(90, 92), a2=(84, 90), l1=(40, -20), l2=(-40, -60), glint=1.0, mouth=1), 'snap'), (bt(244), P(x=1200, air=360, face=-1, lean=30, head=-14, a1=(90, 92), a2=(84, 90), l1=(44, -20), l2=(-44, -60), glint=1.0, mouth=1)),
    (bt(244.6), P(x=1240, air=380, face=1, rot=40, lean=20, head=-30, a1=(-40, -20), a2=(-30, -10), l1=(-10, -20), l2=(-30, -40), glint=1.0), 'hold'), (bt(248), P(x=3200, air=900, face=1, rot=58, lean=20, head=-30, a1=(-40, -20), a2=(-30, -10), l1=(-10, -20), l2=(-30, -40)), 'i')], back=True, held=False,
    mod=lambda p, t: dict(p, x=p['x'] + (4 * math.sin(t * 70) if bt(216) < t < bt(226) or bt(240) < t < bt(244) else 0), air=p['air'] + (8 * math.sin(t * 4) if p['air'] > 200 and bt(236.4) < t < bt(240) else 0)))
_yy = Act('yunyun', [(0, P(x=300, air=900, face=1)), (bt(198.2), P(x=300, air=900, face=1)), (bt(199.6), P(x=520, air=300, face=1, lean=-4, a1=(20, 40), a2=(-20, -10), l1=(6, -10), l2=(-10, -30)), 'o'), (bt(203), P(x=520, air=300, face=1, lean=-8, head=4, a1=(30, 120), a2=(-20, -10), l1=(6, -10), l2=(-10, -30), mouth=1)),
                     (bt(206), P(x=520, air=300, face=1, lean=-4, a1=(20, 40), a2=(-20, -10), l1=(6, -10), l2=(-10, -30))), (bt(207.6), P(x=-500, air=420, face=1, lean=-10, a1=(20, 40), a2=(-20, -10), l1=(6, -10), l2=(-10, -30)), 'i')], H=320, held=False, mod=lambda p, t: dict(p, air=p['air'] + 10 * math.sin(t * 2.2)))
_yl = Act('yunleng', [(0, P(x=-400, face=1)), (bt(206), P(x=-400, face=1, lean=30, a1=(-30, 40), a2=(40, 90))), (bt(207.6), P(x=300, face=1, lean=10, head=-6, a1=(60, 100), a2=(-30, -40), l1=(30, 0), l2=(-30, -30), mouth=1), 'o'), (bt(210.8), P(x=300, face=1, lean=4, head=-6, a1=(140, 170), a2=(-30, -40), l1=(30, 0), l2=(-30, -30), mouth=1)),
                      (bt(211.2), P(x=480, face=1, lean=40, head=-20, a1=(90, 90), a2=(-40, -60), l1=(64, -10), l2=(-50, -60), mouth=1), 'ii'), (bt(212), P(x=520, face=1, lean=-20, head=10, a1=(120, 150), a2=(110, 140), l1=(30, 10), l2=(-30, -20), mouth=1), 'o'), (bt(214), P(x=520, face=1, lean=-20))], H=320)
_ys = Act('yunshan', [(0, P(x=420, air=1100, face=1)), (bt(214), P(x=420, air=1100, face=1, a1=(-10, -20), a2=(-14, -24))), (bt(215.6), P(x=420, air=290, face=1, lean=-2, a1=(-10, -20), a2=(-14, -24), l1=(4, -6), l2=(-8, -20)), 'o'), (bt(219.5), P(x=420, air=290, face=1, lean=-2, a1=(-10, -20), a2=(-14, -24), l1=(4, -6), l2=(-8, -20))),
    (bt(220), P(x=420, air=290, face=1, lean=4, a1=(96, 70), a2=(-14, -24), l1=(4, -6), l2=(-8, -20)), 'o'), (bt(231.7), P(x=420, air=290, face=1, lean=4, a1=(96, 70), a2=(-14, -24), l1=(4, -6), l2=(-8, -20))), (bt(232), P(x=910, air=330, face=1, rot=8, lean=30, a1=(90, 90), a2=(-40, -60), l1=(40, -30), l2=(-50, -60), mouth=1), 'ii'),
    (bt(232.5), P(x=1300, air=420, face=1, lean=20, a1=(60, 80), a2=(-40, -60), l1=(30, -30), l2=(-40, -60)), 'o'), (bt(233.5), P(x=1420, air=440, face=-1, lean=10, a1=(-40, 30), a2=(40, 80), l1=(20, -30), l2=(-30, -60)), 'hold'), (bt(234), P(x=980, air=450, face=-1, rot=-8, lean=30, a1=(90, 90), a2=(-40, -60), l1=(40, -30), l2=(-50, -60), mouth=1), 'ii'),
    (bt(234.5), P(x=620, air=330, face=-1, lean=20, a1=(60, 80), a2=(-40, -60), l1=(30, -30), l2=(-40, -60)), 'o'), (bt(235.5), P(x=560, air=320, face=1, lean=4, a1=(40, 100), a2=(-20, 20), l1=(10, -20), l2=(-20, -50)), 'hold'), (bt(236), P(x=940, air=360, face=1, lean=30, a1=(90, 90), a2=(-40, -60), l1=(40, -30), l2=(-50, -60), mouth=1), 'ii'),
    (bt(236.25), P(x=640, air=400, face=1, rot=-40, lean=-30, head=20, a1=(130, 160), a2=(110, 150), l1=(70, 30), l2=(50, 10), mouth=1), 'snap'), (bt(237.2), P(x=440, air=360, face=1, lean=-6, a1=(150, 170), a2=(140, 160), l1=(10, -20), l2=(-20, -50)), 'io'), (bt(239.8), P(x=430, air=370, face=1, lean=-12, a1=(156, 176), a2=(146, 166), l1=(10, -20), l2=(-20, -50), mouth=1)),
    (bt(240), P(x=460, air=360, face=1, lean=26, a1=(90, 92), a2=(84, 90), l1=(40, -20), l2=(-40, -60), mouth=1), 'snap'), (bt(243.6), P(x=440, air=360, face=1, lean=16, a1=(90, 92), a2=(84, 90), l1=(44, -20), l2=(-44, -60), mouth=1)), (bt(244), P(x=200, air=330, face=1, rot=-40, lean=-30, head=20, a1=(130, 160), a2=(110, 150), l1=(70, 30), l2=(50, 10), mouth=1), 'snap'), (bt(248), P(x=60, air=200, face=1, rot=-30, lean=-20, a1=(130, 160), a2=(110, 150), l1=(70, 30), l2=(50, 10)), 'o')], H=340,
    mod=lambda p, t: dict(p, x=p['x'] + (4 * math.sin(t * 64) if bt(240) < t < bt(244) else 0), air=p['air'] + (8 * math.sin(t * 2) if bt(215.6) < t < bt(231.7) else 0)))
_YH = _yy.J(bt(201))['head']; _XH2 = _x2.J(bt(204))['head']; CL = [(bt(232), (960, 350)), (bt(234), (930, 230)), (bt(236), (1000, 330))]
_c2 = camk([(bt(193), (300, 250, 1.0, -6)), (bt(197.6), (900, 420, 1.1, -4), 'lin'), (bt(198), (1100, 640, 1.6, 0), 'i'), (bt(199.8), (820, 520, 1.0, 0), 'io'), (bt(200), (_YH[0] + 20, _YH[1] + 10, 3.2, 0), 'hold'), (bt(203), (_YH[0] + 30, _YH[1] + 10, 3.6, 0), 'lin'), (bt(203.02), (_XH2[0] - 20, _XH2[1] + 10, 3.2, 0), 'hold'), (bt(206), (_XH2[0] - 30, _XH2[1] + 10, 3.6, 0), 'lin'),
    (bt(206.02), (700, 600, 1.05, 0), 'hold'), (bt(208), (720, 610, 1.1, 0), 'lin'), (bt(208.02), (1080, 650, 2.0, 4), 'hold'), (bt(210.9), (1070, 650, 2.4, 6), 'lin'), (bt(211), (760, 620, 1.15, 0), 'snap'), (bt(212), (560, 640, 1.5, -5), 'i'), (bt(214), (700, 520, 0.95, 0), 'o'), (bt(215.6), (720, 480, 0.95, 0), 'lin'), (bt(219.8), (500, 440, 1.5, 0), 'io'),
    (bt(220), (1040, 660, 1.5, 3), 'hold'), (bt(226.5), (1060, 720, 2.0, 5), 'lin'), (bt(228), (1060, 720, 2.1, 5), 'lin'), (bt(231), (1100, 620, 1.3, 0), 'hold'), (bt(231.8), (980, 440, 1.0, 0), 'io'), (bt(236.4), (960, 420, 1.0, 0), 'lin'), (bt(239.8), (900, 420, 1.1, 0), 'lin'), (bt(240), (860, 430, 1.15, 0), 'snap'), (bt(244), (780, 430, 1.3, 0), 'lin'), (bt(244.3), (1000, 400, 0.95, 0), 'o'), (bt(248), (1100, 360, 0.95, 0), 'lin')],
    [(bt(198), 40, 0.3), (bt(212), 50, 0.4), (bt(214), 10, 0.2), (bt(216), 14, 0.3), (bt(218), 14, 0.3), (bt(220), 18, 0.4), (bt(222), 14, 0.3), (bt(224), 14, 0.3), (bt(232), 30, 0.2), (bt(234), 30, 0.2), (bt(236), 40, 0.3), (bt(240), 16, 2.4), (bt(244), 50, 0.4)])
LT = (520, GY - 190)
def s_y2(t):
    b = (t - 0.5) / BEAT
    if 228 <= b < 231: return s_eyes(t)
    XJ = _x2.J(t); SJ = _ys.J(t); poss = b >= 231; h1, h2 = XJ['h1'], XJ['h2']; m = ((h1[0] + h2[0]) / 2 - 26, (h1[1] + h2[1]) / 2); u = min(1.0, max(0.0, (b - 208.4) / 2.2)); fl = min(1.0, max(0.0, (b - 211) / 1.0)); acts = [_x2] + ([_yy] if 198 <= b < 207.6 else []) + ([_yl] if 206 <= b < 212.05 else []) + ([_ys] if b >= 214 else [])
    def ground(c):
        shadow(c, acts, t); A.puff(c, t, bt(198), (1100, GY + 6), 34, 330, 190, 40, 210, 1.5, (0.9, 0.82, 0.86, 0.75), 1); A.debris(c, t, bt(198), (1100, GY), 30, 500, 1500, (0.55, 0.5, 0.6), seed=2, floor=GY + 10); A.debris(c, t, bt(212), (LT[0], GY), 50, 600, 2200, (0.55, 0.5, 0.6), seed=3, floor=GY + 10, size=24)
        for i in range(8): A.puff(c, t, bt(212) + 0.07 * i, (LT[0] + (rnd(i, 5) - 0.5) * 400, GY - 20 - 160 * rnd(i, 6)), 9, 260, 160, 60, 260, 2.0, (0.9, 0.86, 0.9, 0.8), 20 + i)
        if b >= 216:                                                                      # 威压把石板一圈圈压裂
            k = min(1.0, (b - 216) / 8); c.set_source_rgba(0.08, 0.05, 0.1, 0.95); c.set_line_join(cairo.LINE_JOIN_ROUND)
            for i in range(16):
                th = i / 16 * 6.283 + rnd(i, 3); L = (200 + 420 * rnd(i, 4)) * k; x, y = 1060, GY + 20; c.move_to(x, y)
                for j in range(1, 6): x += math.cos(th + (rnd(i, j) - 0.5) * 0.9) * L / 5; y += math.sin(th + (rnd(i, j) - 0.5) * 0.9) * L / 5 * 0.3; c.line_to(x, y)
                c.set_line_width(8 - 1.2 * (i % 4)); c.stroke()
            for i in range(5): A.debris(c, t, bt(216 + 2 * i), (1060 + (rnd(i, 8) - 0.5) * 300, GY), 10, 200, 800, (0.55, 0.5, 0.6), seed=40 + i, floor=GY + 10, g=1200)
    def back(c):
        if b < 198.3 or 244.6 <= b: wings(c, XJ, t, glow=True)
        if 198.6 <= b < 207.6: wings(c, _yy.J(t), t, S=380, qi=True, cb=CYAN)
        if b >= 214.5: wings(c, SJ, t, S=440, qi=True, cb=(0.86, 0.95, 1.0))
        aura(c, _x2, t, WHITEF if poss else CYAN, n=50, k=(0.85 if poss else 0.5 * (1 if b < 214 else max(0.0, 1 - (b - 214) / 6))), rise=600 if poss else 480)
        if b >= 214: aura(c, _ys, t, (0.75, 0.95, 1.0), n=40, k=0.6, seed=31, rise=560)
        if 206 <= b < 212: aura(c, _yl, t, WIND, n=24, k=0.5, seed=41)
    def chars(c):
        if poss and b < 244.6:                                                            # 背后是药老的虚影
            p = XJ['p']; F.figure(c, lambda dt: F.kin(P(x=XJ['pel'][0] - XJ['f'] * 50, air=GY - XJ['pel'][1] - 165, face=XJ['f'], lean=p['lean'] * 0.5, a1=p['a1'], a2=p['a2']), 660, GY + 150), t, F.LOOKS['yaolao'], alpha=0.5 * min(1.0, (b - 231) * 2))
        for k_, (a, tb0, tb1) in enumerate(((_x2, 231.8, 236.3), (_ys, 231.8, 236.3), (_x2, 244.6, 248), (_x2, 193, 198))):
            if tb0 < b < tb1:
                for k in (3, 2, 1): a.draw(c, t - 0.028 * k, alpha=0.3 - 0.07 * k)
        [a.draw(c, t) for a in acts[1:]]; _x2.draw(c, t)
    def glow(c):
        A.ring(c, t, bt(198), (1100, GY + 10), 760, 0.55, (0.9, 0.8, 1), w=30); A.sparks(c, t, bt(198), (1100, GY), 50, 90, 80, 500, 2400, 0.55, PURP, seed=5, g=900)
        if 208.4 <= b < 211:
            for (hh, col, sd) in ((h1, CYAN, 3), (h2, WHITEF, 4)): A.flame(c, t, lambda dt, sv, hh=hh: (hh[0] + (m[0] - hh[0]) * u + (sv - 0.5) * 20, hh[1] + (m[1] - hh[1]) * u - 6), 34, 0.4, 280, 30 * (1 - 0.4 * u), col, a=0.95, seed=sd)
            if u > 0.3: lotus(c, m, 16 + 70 * (u - 0.3) / 0.7, t, ca=CYAN, cb=WHITEF, a=min(1.0, (u - 0.3) * 3))
        if 211 <= b < 212: p0 = _x2.J(bt(211))['h1']; q = (p0[0] + (LT[0] - p0[0]) * fl, p0[1] + (LT[1] - p0[1]) * fl); lotus(c, q, 90, t, ca=CYAN, cb=WHITEF); c.move_to(*q); c.line_to(q[0] + 300, q[1] - 20); c.set_source_rgba(*CYAN, 0.5); c.set_line_width(40); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        if 206 <= b < 212: wtrail(c, _yl, t, 0.66, WIND, th=900)
        if 212 <= b < 214: k = t - bt(212); A.burst(c, LT, 300 + 2600 * k ** 1.2, WHITEF, math.exp(-k / 0.5), rays=24, t=t, seed=6); lotus(c, LT, 200 + 900 * k, t, ca=CYAN, cb=WHITEF, a=math.exp(-k / 0.3))
        A.ring(c, t, bt(212), LT, 1700, 0.6, (0.85, 1, 0.97), sq=1.0, w=50); A.sparks(c, t, bt(212), LT, 110, 90, 180, 600, 3400, 0.8, CYAN, seed=7, w=4.5, g=300)
        if b >= 214 and b < 231:
            for i in range(9): A.ring(c, t, bt(214 + 2 * i), (SJ['pel'][0], GY + 10), 1900, 1.1, (0.9, 0.95, 1.0), w=26)
            if b >= 220: A.burst(c, SJ['h1'], 60 + 14 * math.sin(t * 10), (0.8, 0.95, 1.0), 0.8, rays=10, t=t, seed=8)
        for i, (tc, pc) in enumerate(CL):
            A.sparks(c, t, tc, pc, 80, 0, 180, 600, 3200, 0.55, WHITEF if i % 2 == 0 else WIND, seed=50 + i, w=4.5, g=200); A.ring(c, t, tc, pc, 1100, 0.4, (1, 1, 1), sq=1.0, w=40); A.ring(c, t, tc + 0.05, pc, 700, 0.4, WHITEF, sq=0.4, w=20)
            if 0 <= t - tc < 0.5: A.burst(c, pc, 520 * (1 - math.exp(-(t - tc) / 0.04)), WHITEF, math.exp(-(t - tc) / 0.1), rays=20, t=t, seed=60 + i)
        if 231.8 < b < 236.3:
            for a_, col in ((_x2, WHITEF), (_ys, WIND)):
                tr = [(a_.J(t - k / 240)['pel'], a_.J(t - k / 240)['chest']) for k in range(40)]; sp = math.hypot(tr[0][0][0] - tr[6][0][0], tr[0][0][1] - tr[6][0][1]) * 40
                if sp > 900: A.trail(c, tr, col, a=min(0.9, (sp - 900) / 2500))
        if 236.5 <= b < 240:
            g = (b - 236.5) / 3.5
            for (J_, col, sd) in ((XJ, WHITEF, 70), (SJ, WIND, 71)): p0 = ((J_['h1'][0] + J_['h2'][0]) / 2, min(J_['h1'][1], J_['h2'][1]) - 40 - 60 * g); A.burst(c, p0, 50 + 170 * g, col, 0.95, rays=14, t=t, seed=sd); A.flame(c, t, lambda dt, sv, p0=p0: (p0[0] + (sv - 0.5) * 200 * g, p0[1] + 40), 40, 0.5, 400, 40, col, a=0.8, seed=sd)
        if 240 <= b < 244:
            g = (b - 240) / 4; xa = (XJ['h1'][0] - 30, XJ['h1'][1]); sa = (SJ['h1'][0] + 30, SJ['h1'][1]); mx = 860 - 330 * g ** 1.6 + 26 * math.sin(t * 31); my = (xa[1] + sa[1]) / 2
            for (p0, col, w_) in ((xa, WHITEF, 130), (sa, WIND, 110)):
                for (wd, al, cc) in ((w_ + 20 * math.sin(t * 50), 0.55, col), (w_ * 0.4, 0.95, (1, 1, 1))): c.move_to(*p0); c.line_to(mx, my); c.set_source_rgba(*cc, al); c.set_line_width(wd); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
            A.burst(c, (mx, my), 260 + 60 * math.sin(t * 40), (1, 1, 1), 1.0, rays=26, t=t, seed=80); A.emit(c, t, bt(240), t, 160, lambda tb: (860 - 330 * ((tb - bt(240)) / (4 * BEAT)) ** 1.6, my), ang=90, spread=180, v0=500, v1=2600, life=0.4, col=WHITEF, w=4, g=0, seed=81)
        if 244 <= b < 246: k = t - bt(244); A.burst(c, (520, 430), 400 + 3000 * k, WHITEF, math.exp(-k / 0.35), rays=24, t=t, seed=90); A.ring(c, t, bt(244), (520, 430), 2000, 0.6, (1, 1, 1), sq=1.0, w=50)
        if b >= 244.6: tr = [(_x2.J(t - k / 200)['pel'], _x2.J(t - k / 200)['chest']) for k in range(40)]; A.trail(c, tr, WHITEF, a=0.8)
    fr, mask, gl, M = A.render(R, PL('dusk'), _c2(t), [('over', ground), ('back', back), ('chars', chars), ('glow', glow)])
    fr = hits(fr, t, mask, gl, M, [(bt(198), (1100, GY), (2, 2, 3)), (bt(212), LT, (1, 1, 1, 2, 2, 2, 3, 3)), (bt(244), (520, 430), (1, 1, 2, 2, 3, 3))] + [(tc, pc, (1, 1, 2, 2, 3)) for tc, pc in CL])
    if b < 197.9 or b > 244.7: fr = A.speedlines(fr, t, R, a=0.45, ang=-18)
    if 208.02 <= b < 210.9: fr = A.focuslines(fr, t, R, (R.w * 0.5, R.h * 0.5), a=0.4, n=60, r0=0.42, col=(0.85, 1, 0.95))
    if 240 <= b < 244: fr = A.focuslines(fr, t, R, (R.w * 0.5, R.h * 0.45), a=0.35 + 0.3 * (b - 240) / 4, n=70, r0=0.36)
    fr = fin(fr)
    if 212 <= b < 213.5: fr = fr + (1 - fr) * max(0.0, 0.9 - (b - 212) / 1.5)
    if 226.5 <= b < 228: fr = fr * max(0.0, 1 - (b - 226.5) / 1.3)
    if 231 <= b < 231.5: fr = fr + (1 - fr) * (1 - (b - 231) * 2)
    fr = cap(fr, t, 193.4, 197.8, '他展开紫云翼，第二次上了云岚宗'); fr = cap(fr, t, 198.4, 199.9, '云岚宗', y=80, px=58, col=(255, 226, 170)); fr = cap(fr, t, 200.2, 203, '云岚宗宗主 云韵：「……药岩？」'); fr = cap(fr, t, 203.2, 206, '「云芝？」'); fr = cap(fr, t, 206.3, 208, '可他要的，是首席长老云棱的命')
    fr = cap(fr, t, 208.3, 210.9, '青莲地心火，加上药老的骨灵冷火'); fr = slam(fr, t, 211, 213.6, '佛怒火莲', (1340, 330), px=250, glow=(60, 255, 210), big=3.0, rot=4); fr = slam(fr, t, 214, 218, '云山', (1400, 380), px=330, glow=(170, 220, 255), big=2.6); fr = cap(fr, t, 214.6, 219.8, '云岚宗上代宗主出关——斗宗')
    fr = cap(fr, t, 220.3, 226.4, '斗宗的威压下，力竭的他连站都站不住'); fr = slam(fr, t, 232, 235.6, '骨灵冷火', (960, 880), px=200, glow=(170, 210, 255), big=2.6); fr = cap(fr, t, 236.6, 239.8, '森白的火，异火榜第十一')
    return cap(fr, t, 244.4, 248, '「我若是要离开，你云岚宗，还无人能阻我。」')
def s_eyes(t):
    """▲ 正面特写：闭着的眼睁开，一青一白。"""
    b = (t - 0.5) / BEAT; op = min(1.0, max(0.0, (b - 228) / 0.12))
    def d(c):
        c.rectangle(-960, -230, 1920, 460); c.set_source_rgb(*[v * (0.5 + 0.5 * op) for v in F.SKIN]); c.fill()
        for sx, col in ((-1, CYAN), (1, WHITEF)):
            x = sx * 330
            if op > 0:
                c.save(); c.translate(x, 20); c.scale(1, 0.62 * op + 0.02); c.arc(0, 0, 190, 0, 7); c.restore(); c.set_source_rgb(1, 1, 1); c.fill(); c.save(); c.arc(x, 20, 190, 0, 7); c.clip(); c.arc(x, 24, 96, 0, 7); c.set_source_rgb(*col); c.fill(); c.arc(x, 24, 96, 0, 7); c.set_source_rgb(0.05, 0.06, 0.1); c.set_line_width(10); c.stroke(); c.arc(x, 24, 34, 0, 7); c.set_source_rgb(0.03, 0.03, 0.05) if sx < 0 else c.set_source_rgb(0.55, 0.62, 0.75); c.fill(); c.arc(x - 34, -10, 20, 0, 7); c.set_source_rgb(1, 1, 1); c.fill(); c.restore()
                c.save(); c.rectangle(x - 260, -230, 520, 460); c.clip(); A.burst(c, (x, 24), 260 + 30 * math.sin(t * 12), col, 0.5 * op); c.restore()
            c.move_to(x - 210, 20 - 30 * op); c.curve_to(x - 100, -100 * op - 10, x + 100, -110 * op - 10, x + 210, 10 - 40 * op); c.set_source_rgb(0.05, 0.06, 0.1); c.set_line_width(22); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
            c.move_to(x - sx * 250, -170 - 20 * op); c.line_to(x + sx * 190, -150 + 40 * op * 0 - 16); c.set_line_width(30); c.stroke()
        for i in range(13): x = -900 + i * 150; c.move_to(x - 110, -232); c.line_to(x + 20 * math.sin(i * 2.1), -232 + 90 + 80 * rnd(i, 3)); c.line_to(x + 110, -232); c.close_path(); c.set_source_rgb(0.06, 0.08, 0.2); c.fill()
        c.set_source_rgb(0, 0, 0); c.rectangle(-960, -540, 1920, 310); c.fill(); c.rectangle(-960, 230, 1920, 310); c.fill()
    fr = _closeup(t, d, (0, 0, 0), (0, 0, 0), [(bt(228), 24, 0.25)]); n = int(round((t - bt(228)) * 60))
    if 0 <= n < 4: fr = 1 - fr if n < 2 else fr + (1 - fr) * 0.6
    fr = fin(fr); return cap(fr, t, 228.6, 231, '「接下来，便交给为师吧。」')

# ================= 248–262 地图：逃出加玛帝国
_MA, _MB, _MC = (-600, -130), (-40, 90), (600, -30)
def s_map(t):
    b = (t - 0.5) / BEAT; g = min(1.0, max(0.0, (b - 249) / 11)); INKC = (0.14, 0.11, 0.10)
    def route(u): return (_MA[0] + (_MB[0] - _MA[0]) * u * 2, _MA[1] + (_MB[1] - _MA[1]) * u * 2 + 50 * math.sin(u * 12)) if u < 0.5 else (_MB[0] + (_MC[0] - _MB[0]) * (u * 2 - 1), _MB[1] + (_MC[1] - _MB[1]) * (u * 2 - 1) + 40 * math.sin(u * 12))
    def d(c):
        z = 1.0 + 0.06 * g; c.scale(z, z); c.set_line_join(cairo.LINE_JOIN_ROUND)
        for i in range(90):                                                               # 山
            x = -900 + 1800 * rnd(i, 1); y = -420 + 840 * rnd(i, 2); s_ = 26 + 50 * rnd(i, 3) * (2.0 if abs(x - _MB[0]) < 330 else 1.0); c.move_to(x - s_, y + s_ * 0.6); c.line_to(x, y - s_ * 0.6); c.line_to(x + s_, y + s_ * 0.6); c.set_source_rgba(*INKC, 0.25 + 0.4 * rnd(i, 4)); c.set_line_width(5); c.stroke()
        c.move_to(700, -540)
        for i in range(12): c.line_to(700 + 50 * math.sin(i * 1.7), -540 + i * 100)
        c.set_source_rgba(0.55, 0.1, 0.1, 0.8); c.set_line_width(8); c.set_dash([26, 18]); c.stroke(); c.set_dash([])
        c.move_to(*_MA)
        for k in range(1, int(g * 80) + 1): c.line_to(*route(k / 80))
        c.set_source_rgba(0.6, 0.08, 0.08, 0.95); c.set_line_width(10); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        for i in range(16):                                                               # 搜山的云岚宗弟子
            th = -0.9 + 1.9 * rnd(i, 6); r_ = (80 + 520 * rnd(i, 7)) * min(1.0, (b - 248) / 9); p = (_MA[0] + math.cos(th) * r_, _MA[1] + math.sin(th) * r_ * 0.8); c.new_path(); c.arc(p[0], p[1], 11, 0, 7); c.set_source_rgb(0.96, 0.98, 1); c.fill_preserve(); c.set_source_rgb(*INKC); c.set_line_width(4); c.stroke()
        for (p, s_) in ((_MA, '云岚山'), (_MB, '魔兽山脉'), ((_MC[0] + 160, _MC[1]), '边境')): c.new_path(); c.arc(p[0], p[1], 16, 0, 7); c.set_source_rgb(*INKC); c.fill(); wtext(c, s_, p[0], p[1] - 70, 62, INKC)
        wtext(c, '加玛帝国', -100, -400, 110, INKC, 0.35); q = route(g); A.burst(c, q, 40 + 6 * math.sin(t * 10), CYAN, 1.0); A.flame(c, t, lambda dt, sv: (q[0] + (sv - 0.5) * 20, q[1]), 20, 0.4, 160, 20, CYAN, a=0.9, seed=3)
    fr = fin(_closeup(t, d, (0.90, 0.85, 0.72), (0.78, 0.70, 0.56))); fr = fr * min(1.0, (b - 248) * 3 + 0.2) * min(1.0, (262 - b) * 3 + 0.0)
    fr = cap(fr, t, 248.5, 254.5, '云岚宗满山搜捕。他钻进魔兽山脉，一路逃向边境'); return cap(fr, t, 255, 261.6, '赢了三年之约的人，成了加玛帝国容不下的人')

# ================= 262–295 尾：边境、魂殿、下集
_xe = Act('xiaoyan', [(bt(262), P(x=250, lean=8, a1=(6, 16), a2=(-6, 10))), (bt(268), P(x=1150, lean=8, a1=(6, 16), a2=(-6, 10)), 'lin'), (bt(268.6), P(x=1160, lean=2, head=0), 'o'), (bt(269), P(x=1160, face=-1, lean=0, head=-12), 'hold'), (bt(290), P(x=1160, face=-1, lean=0, head=-14))], back=True, held=False, mod=lambda p, t: _wlk(p, t) if t < bt(268) else p)
_ye = Act('yaolao', [(0, P(x=900, air=230, face=1, lean=4, a1=(10, 30), a2=(-10, 10))), (bt(290), P(x=900, air=236, face=1, lean=4, a1=(30, 80), a2=(-10, 10)))], H=340, mod=lambda p, t: dict(p, air=p['air'] + 10 * math.sin(t * 1.6)))
_ce = camk([(bt(262), (700, 560, 1.0, 0)), (bt(268), (1000, 580, 1.1, 0), 'lin'), (bt(278), (1040, 600, 1.4, 0), 'io'), (bt(282), (1050, 600, 1.6, 0), 'lin'), (bt(288), (1050, 590, 1.8, 0), 'lin')], [(bt(282), 30, 0.3)])
def s_end(t):
    b = (t - 0.5) / BEAT
    if b >= 288:                                                                          # 下集
        fr = np.zeros((R.h, R.w, 3), np.float32); s, c = layer(R.w, R.h); c.scale(R.k, R.k); A.flame(c, t, lambda dt, sv: (260 + 1400 * sv, 960 + 40 * math.sin(sv * 9)), 130, 0.9, 460, 70, (1.0, 0.5, 0.15), a=0.5, seed=5, wob=30); fr = A.add_glow(fr, s, 20 * R.k, 1.0)
        fr = slam(fr, t, 288, 296, '炎帝', (960, 500), px=380, glow=(255, 130, 30), big=2.0); fr = caption(fr, '下集', y=250, px=64, col=(255, 226, 170)); fr = caption(fr, '斗之力三段的废物，凭什么成了炎帝？', y=760, px=50); return fr * min(1.0, max(0.0, (175.2 - t) / 1.2))
    ya = min(1.0, max(0.0, (b - 272) / 1.5)); dark = min(1.0, max(0.0, (b - 282) * 8))
    def glow(c):
        if dark > 0:
            A.flame(c, t, lambda dt, sv: (200 + 1700 * sv, GY + 60), 90, 1.0, 700, 90, (0.45, 0.15, 0.8), a=0.5, seed=7, wob=40)
            for i in range(5): x0 = 300 + i * 340; c.move_to(x0, 60); c.line_to(x0 + 260 * (1 if i % 2 else -1), GY + 40); c.set_source_rgba(0.55, 0.3, 0.9, 0.8); c.set_line_width(14); c.set_dash([34, 16], t * 60); c.stroke(); c.set_dash([])
    fr, mask, gl, M = A.render(R, PL('border'), _ce(t), [('over', lambda c: shadow(c, [_xe], t)), ('chars', lambda c: (_ye.draw(c, t, alpha=ya) if ya > 0 else None, _xe.draw(c, t)))])
    if dark > 0: s2, c2 = A.ctx(R, M); glow(c2); fr = fr * (1 - 0.82 * dark); fr = A.add_glow(fr, s2, 14 * R.k, 1.0)
    fr = fin(fr) * min(1.0, (b - 262) * 2 + 0.1)
    if 0 <= int(round((t - bt(282)) * 60)) < 3: fr = fr + (1 - fr) * 0.7
    fr = cap(fr, t, 262.4, 268.4, '加玛帝国 · 边境', y=80, px=58, col=(255, 226, 170)); fr = cap(fr, t, 263, 268.6, '他穿出魔兽山脉，走到了帝国的边境'); fr = cap(fr, t, 269.4, 277.6, '父亲失踪，家族被迫迁走——这笔账，他说下次回来自己算')
    fr = cap(fr, t, 278, 281.9, '路上，药老第一次提起了一个名字'); fr = slam(fr, t, 282, 288, '魂殿', (960, 440), px=400, glow=(150, 60, 255), big=2.6); return fr * (min(1.0, (288 - b) * 3) if b > 287.6 else 1.0)

# ======================================================================================
# v2 装配：每个镜头还是用自己原来的拍号当时钟；SEG 把成片的拍（fb）接到镜头的拍上。成片 228 拍 ≈ 2 分 16 秒。
_air = lambda a: (lambda t: min(1.0, max(0.0, (a.f(t)['air'] - 120) / 140)))
_xl.wingf = _air(_xl); _xa.wingf = _air(_xa); _x2.wingf = lambda t: 1.0 if (t < bt(198.3) or t >= bt(244.6)) else 0.0
def scr(M, x, y): return ((M[0, 0] * x + M[0, 1] * y + M[0, 2]) / R.k, (M[1, 0] * x + M[1, 1] * y + M[1, 2]) / R.k)
def nocap(fn, t):
    global NOCAP; NOCAP = True
    try: return fn(t)
    finally: NOCAP = False

def s_ots(tl, ev, look='nalan', pl='yunlan', ca=CYAN, cb=PURP, twin=True, pov=False, grow=9.5):
    """过肩：敌人的后脑勺压在前景，萧炎从盲区升上来 → 展翼 → 莲花一拍开一层 → 推向镜头。tl=本地秒；ev=(展翼, 一层, 二层, 三层, 出手) 的本地拍。"""
    lb = tl / BEAT; e_w, e1, e2, e3, e_t = ev; g = lambda e, d=0.20: min(1.0, max(0.0, (lb - e) * BEAT / d)); rise = 1 - (1 - min(1.0, max(0.0, (lb - (e_w - 1.0)) / 1.0))) ** 3
    cx = 960 if pov else 1090; HH = 660 if pov else 560; fy = (1010 if pov else 1560 - 700 * rise + 10 * math.sin(tl * 2.2)); wop = 0.10 + 0.90 * g(e_w, 0.14); op = (g(e1), g(e2), g(e3)); th = max(0.0, (lb - e_t) * BEAT); thrown = th > 0; lr = (40 + 40 * op[0] + 34 * op[1] + 30 * op[2]) * (1 if not thrown else math.exp(th * grow))
    sh = A.shake(tl, [(e_w * BEAT, 26, 0.25)] + [(e * BEAT, 12, 0.14) for e in (e1, e2, e3)] + [(e_t * BEAT, 30, 0.3)], FPS); z = 1.0 + 0.06 * g(e_w) + 0.035 * (op[0] + op[1] + op[2]) + 0.02 * math.sin(tl); cam = (960 + sh[0], 500 + sh[1] - 30 * (1 - rise), z, -2.5 + 1.5 * math.sin(tl * 0.8)); an = {}; K = F.LOOKS[look]
    lp = lambda: ((an['hands'][0][0] + an['hands'][1][0]) / 2 + (960 - cx) * min(1.0, th * 5), an['hands'][0][1] - 34 + (560 - fy + 0.6 * 560) * 0 - 10 * min(1.0, th * 5))
    def chars(c):
        if not pov:
            for sd in (-1, 1): fx.wing(c, (cx + sd * 26, fy - 0.70 * 560), sd, 600, wop, tl, flap=(18 * (1 - g(e_w, 0.5)) if lb >= e_w else 0), seed=sd)
        fx.cape(c, cx, fy, HH, tl, wind=0.6 + 0.4 * (op[0] + op[1] + op[2]) / 3); c.save(); c.translate(cx, fy - HH * 0.5); c.rotate(math.radians(2.5 * math.sin(tl * 1.7))); c.translate(-cx, -(fy - HH * 0.5))
        an.update(fx.front(c, cx, fy, HH, tl, arms='push' if thrown else 'cup', eyes=(ca, cb if cb != PURP else ca), hand=1.5 if thrown else 1.0)); c.restore()
        if op[0] > 0 and lr < 900: fx.lotus(c, lp(), lr, tl, ca, cb, op, solid=True)
        if not pov and (not thrown or th < 0.25): fx.back(c, 450 - 30 * g(e_w, 0.3), 1150 + 12 * math.sin(tl * 1.3), 780, K, tl, twin=twin, turn=-g(e_w, 0.3))
    def back(c):
        if not pov:
            for sd in (-1, 1): fx.wing(c, (cx + sd * 26, fy - 0.70 * 560), sd, 600, wop, tl, glow=True, cb=PURP, seed=sd)
        A.flame(c, tl, lambda dt, sv: (cx + (sv - 0.5) * 300, fy - 60 - 380 * rnd(int(sv * 997), 3)), 46, 0.5, 520, 60, ca, a=0.55, seed=11, wob=26)
    def glow(c):
        if not pov: fx.feathers(c, (cx, fy - 400), tl, e_w * BEAT, PURP, n=30, r=640); A.ring(c, tl, e_w * BEAT, (cx, fy - 400), 1300, 0.5, (0.85, 0.7, 1.0), w=34)
        if pov and lb < e1 + 0.4 and an.get('hands'):
            for (hx_, hy_), cl in zip(an['hands'], (ca, cb)): A.flame(c, tl, lambda dt, sv, hx_=hx_, hy_=hy_: (hx_ + (sv - 0.5) * 30, hy_ - 10), 30, 0.4, 300, 34, cl, a=0.95, seed=int(hx_))
        for e_, (x_, y_) in zip((ca, cb if cb != PURP else ca), an.get('eyes', [])): A.burst(c, (x_, y_), 26, e_, 0.9)
        if op[0] > 0:
            p = lp(); fx.lotus(c, p, lr, tl, ca, cb, op, a=0.42 if lr < 900 else 0.9)
            for k_, e in enumerate((e1, e2, e3)): A.ring(c, tl, e * BEAT, p, 520 + 160 * k_, 0.35, ca if k_ % 2 == 0 else cb, w=22); A.sparks(c, tl, e * BEAT, p, 26, 0, 180, 300, 1500, 0.45, ca if k_ % 2 == 0 else cb, seed=20 + k_, g=200)
    fr, mask, gl, M = A.render(R, PL(pl), cam, [('back', back), ('chars', chars), ('glow', glow)])
    if thrown: fr = A.focuslines(fr, tl, R, (R.w * 0.5, R.h * 0.5), a=0.5, n=70, r0=0.35, col=(0.85, 1, 0.95))
    fr = fin(fr); return fr + (1 - fr) * min(1.0, max(0.0, (lr - 700) / 1500)) if thrown else fr
def s_hook2(tl): fr = s_ots(tl, (0.0, 0.8, 1.6, 2.4, 3.15)); return caption(fr, '「去吧，佛怒莲！」', a=min(1.0, max(0.0, (tl - 2.5 * BEAT) / 0.1))) if tl > 2.5 * BEAT else fr
def s_ots_duel(tl): return s_ots(tl, (0.0, 1.0, 2.0, 3.0, 3.45))
def s_pov_y2(tl): return s_ots(tl, (-9.0, 0.0, 1.0, 2.0, 3.0), pl='dusk', cb=WHITEF, pov=True, grow=4.6)                # 云棱的主观视角：火莲迎面飞来，4 拍

def _cu(fn, *a):
    s_, c = layer(R.w, R.h); c.scale(R.k, R.k); c.translate(960, 540); fn(c, *a); return rgba(s_)[0].copy()
_LC, _BIG = fx.split(fx.PAGE, (700, 0), (590, 1080)); _lo, _G1 = fx.split(_LC, (0, 372), (760, 330)); _G3, _G2 = fx.split(_lo, (0, 722), (760, 690))
def s_page_train(tl):
    """苦修（回忆，5 拍）：左边三个小格是特写——握尺的手、陷进地里的脚、眼睛；右边大格是他抡起玄重尺砸下去。"""
    lb = tl / BEAT; tb = bt(92.0) + max(0.0, tl - 2.25 * BEAT) * 0.75; big = withcam(s_train, tb, lambda t, base: (_xt.J(t)['chest'][0] + 90, _xt.J(t)['chest'][1] + 10, 1.5, -8)) if lb >= 2.25 else None
    its = [dict(poly=_G1, fr=_cu(fx.cu_grip, tl), t0=0.0, slide=(-160, 0)), dict(poly=_G2, fr=_cu(fx.cu_foot, tl), t0=0.75 * BEAT, slide=(-160, 0)), dict(poly=_G3, fr=_cu(fx.cu_eye, tl, (0.16, 0.20, 0.34), 1.0), t0=1.5 * BEAT, slide=(-160, 0))]
    if big is not None: its.append(dict(poly=_BIG, fr=fin(big), t0=2.25 * BEAT, slide=(0, -200)))
    fr = fx.page(R, its, tl); fr = caption(fr, '魔兽山脉 · 三年', y=96, px=54, col=(40, 36, 30), x=1290) if lb < 2.2 else fr
    return fx.ktext(fr, R, tl, '玄重尺', 2.35 * BEAT, 5.2 * BEAT, fx.vcol(1700, 250, 200, 3, 1.02), px=200, style='drop', step=0.18 * BEAT, glow=(120, 140, 255))
_B3, _R3 = fx.split(fx.PAGE, (1190, 0), (1060, 1080)); _R3b, _R3a = fx.split(_R3, (1000, 560), (1920, 500))
def s_p3(t):
    """退婚（v1 拍 40–44）：大格是她指着他；右上是他攥紧的拳，右下是他垂着的眼，最后一拍抬起来。"""
    big = withcam(s_hall, t, lambda t_, base: (_nh.J(t_)['chest'][0] - 70, _nh.J(t_)['chest'][1] - 10, 2.2, 4)); op = 0.3 + 0.7 * min(1.0, max(0.0, (t - bt(43.3)) / 0.18))
    fr = fx.page(R, [dict(poly=_B3, fr=fin(big), t0=bt(40), slide=(-200, 0)), dict(poly=_R3a, fr=_cu(fx.cu_fist, t), t0=bt(41), slide=(200, 0)), dict(poly=_R3b, fr=_cu(fx.cu_eye, t, (0.16, 0.20, 0.34), op, 0.5 * (1 - op)), t0=bt(42), slide=(200, 0))], t)
    return cap(fr, t, 40.2, 43.9, '「现在的你，就是一个废物！」', x=620)
_L2, _R2 = fx.split(fx.PAGE, (1150, 0), (770, 1080))
def s_p2(t):
    """认出彼此（v1 拍 200–206）：一条斜缝，左格云韵，右格萧炎。"""
    its = [dict(poly=_L2, fr=nocap(s_y2, bt(201.4) + (t - bt(200)) * 0.25), t0=bt(200), focus=(700, 430, 1.0), slide=(-220, 0))]
    if t >= bt(202.6): its.append(dict(poly=_R2, fr=nocap(s_y2, bt(204.4) + (t - bt(202.6)) * 0.25), t0=bt(202.6), focus=(1040, 430, 1.0), slide=(220, 0)))
    fr = fx.page(R, its, t); fr = cap(fr, t, 200.2, 206, '云岚宗宗主 云韵：「……药岩？」', x=470, y=930, px=44); return cap(fr, t, 202.9, 206, '「云芝？」', x=1420, y=930, px=44)

EMBER = (1.0, 0.62, 0.25); CP = (0.48, 0.70, 0.92)
def s_sign(tl):
    """片尾署名：穿斗篷的码点小人盘坐在药鼎前，炉火是这一集人物的火色。"""
    Lb = 13.4 * BEAT; k2 = min(1.0, max(0.0, (tl - (Lb - 2.6)) / 0.5)); col = tuple(a + (b - a) * k2 for a, b in zip(CYAN, (1.0, 0.55, 0.15))); fl = 0.85 + 0.15 * math.sin(tl * 9) * math.sin(tl * 5.3); X0, Y0 = 760, 770
    fr = np.zeros((R.h, R.w, 3), np.float32); s, c = layer(R.w, R.h); c.scale(R.k, R.k); c.translate(-170, -160); c.scale(1.15, 1.15); g = cairo.RadialGradient(X0, Y0 - 140, 20, X0, Y0 - 140, 900); g.add_color_stop_rgba(0, *col, 0.34 * fl); g.add_color_stop_rgba(0.45, *col, 0.08); g.add_color_stop_rgba(1, 0, 0, 0, 0); c.set_source(g); c.paint()
    c.set_source_rgba(*col, 0.10); c.rectangle(0, Y0 + 96, 1920, 3); c.fill(); rgb, al = rgba(s); fr = fr * (1 - al) + rgb
    s, c = layer(R.w, R.h); c.scale(R.k, R.k); c.translate(-170, -160); c.scale(1.15, 1.15); A.flame(c, tl, lambda dt, sv: (X0 + (sv - 0.5) * 170, Y0 - 150), 60, 0.7, 420, 46, col, a=0.9, seed=3, wob=22); A.burst(c, (X0, Y0 - 170), 110 * fl, (1, 1, 1), 0.5); fr = A.add_glow(fr, s, 16 * R.k, 1.1)
    s, c = layer(R.w, R.h); c.scale(R.k, R.k); c.translate(-170, -160); c.scale(1.15, 1.15); c.set_line_join(cairo.LINE_JOIN_ROUND); DK = (0.075, 0.07, 0.10)
    for sx in (-1, 0, 1): c.new_path(); c.move_to(X0 + sx * 120 - 22, Y0 + 10); c.line_to(X0 + sx * 150 - 16, Y0 + 100); c.line_to(X0 + sx * 150 + 16, Y0 + 100); c.line_to(X0 + sx * 120 + 22, Y0 + 10); c.close_path(); c.set_source_rgb(*DK); c.fill()
    c.new_path(); c.move_to(X0 - 170, Y0 - 150); c.curve_to(X0 - 230, Y0 - 40, X0 - 170, Y0 + 60, X0, Y0 + 60); c.curve_to(X0 + 170, Y0 + 60, X0 + 230, Y0 - 40, X0 + 170, Y0 - 150); c.close_path(); c.set_source_rgb(*DK); c.fill_preserve(); c.set_source_rgba(*col, 0.5 * fl); c.set_line_width(4); c.stroke()
    c.rectangle(X0 - 196, Y0 - 172, 392, 30); c.set_source_rgb(0.07, 0.06, 0.09); c.fill_preserve(); c.set_source_rgba(*col, 0.7 * fl); c.set_line_width(3); c.stroke()
    for sx in (-1, 1): c.new_path(); c.arc(X0 + sx * 205, Y0 - 190, 34, 0, 7); c.set_source_rgb(*DK); c.set_line_width(14); c.stroke()
    for i in range(7): c.new_path(); c.arc(X0 - 150 + i * 50, Y0 - 60, 9, 0, 7); c.set_source_rgba(*col, 0.35 * fl); c.fill()
    # 码点小人：斗篷、兜帽，脸藏在帽檐的黑里，面朝炉火盘坐
    px_, py_ = 300, Y0 + 100; br = 3 * math.sin(tl * 1.4); c.translate(px_, py_); c.scale(1.25, 1.25); c.translate(-px_, -py_); c.new_path(); c.move_to(px_ - 150, py_); c.curve_to(px_ - 150, py_ - 150, px_ - 90, py_ - 290 - br, px_ - 30, py_ - 372 - br); c.curve_to(px_ + 6, py_ - 430 - br, px_ + 70, py_ - 420 - br, px_ + 96, py_ - 372 - br)
    c.curve_to(px_ + 112, py_ - 330 - br, px_ + 100, py_ - 300, px_ + 78, py_ - 282); c.curve_to(px_ + 120, py_ - 220, px_ + 150, py_ - 120, px_ + 215, py_ - 60); c.curve_to(px_ + 250, py_ - 30, px_ + 250, py_, px_ + 215, py_); c.close_path(); gg = cairo.LinearGradient(px_ - 150, 0, px_ + 230, 0); gg.add_color_stop_rgb(0, 0.03, 0.03, 0.05); gg.add_color_stop_rgb(1, *[0.10 + 0.16 * v for v in col]); c.set_source(gg); c.fill_preserve(); c.set_source_rgba(*col, 0.3 * fl); c.set_line_width(3); c.stroke()
    c.new_path(); c.move_to(px_ + 96, py_ - 372 - br); c.curve_to(px_ + 112, py_ - 330 - br, px_ + 100, py_ - 300, px_ + 78, py_ - 282); c.curve_to(px_ + 120, py_ - 220, px_ + 150, py_ - 120, px_ + 215, py_ - 60); c.set_source_rgba(*col, 0.75 * fl); c.set_line_width(5); c.stroke()
    c.new_path(); c.move_to(px_ + 60, py_ - 390 - br); c.curve_to(px_ + 96, py_ - 372 - br, px_ + 100, py_ - 318, px_ + 70, py_ - 292); c.curve_to(px_ + 30, py_ - 300, px_ + 26, py_ - 362 - br, px_ + 60, py_ - 390 - br); c.close_path(); c.set_source_rgb(0.0, 0.0, 0.01); c.fill()
    c.new_path(); c.arc(px_ + 76, py_ - 344 - br, 5, 0, 7); c.set_source_rgba(*col, 0.9 * fl); c.fill()
    c.new_path(); c.move_to(px_ + 120, py_ - 200); c.curve_to(px_ + 190, py_ - 190, px_ + 230, py_ - 215, px_ + 262, py_ - 236); c.set_source_rgb(*DK); c.set_line_width(34); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke(); rgb, al = rgba(s); fr = fr * (1 - al) + rgb
    s, c = layer(R.w, R.h); c.scale(R.k, R.k); c.translate(-170, -160); c.scale(1.15, 1.15); A.sparks(c, tl % 1.3 + 0.01, 0.0, (X0, Y0 - 170), 14, 90, 50, 200, 520, 1.2, col, seed=int(tl / 1.3) + 3, g=-60); fr = A.add_glow(fr, s, 8 * R.k, 1.0)
    fr = caption(fr, '码点小人', y=440, px=170, x=1420, font=_env.BRUSH, a=min(1.0, max(0.0, (tl - 0.5) / 0.5))); fr = caption(fr, '炉火未熄，下一集见。', y=610, px=56, x=1420, col=(255, 232, 190), a=min(1.0, max(0.0, (tl - 1.3) / 0.5)))
    return fr * min(1.0, tl / 0.5) * min(1.0, max(0.0, (Lb - 0.15 - tl) / 1.2))

L0 = 1e6                                                                                  # 第 4 项写 L0 = 这个镜头吃本地秒（从 0 起）
SEG = [(0, 4, s_hook2, L0, None), (4, 32, s_stele, 4, None), (32, 40, s_hall, 32, None), (40, 44, s_p3, 40, None), (44, 51, s_hall, 44, None), (51, 53, s_hall, 53, None), (53, 57.5, s_hall, 56, None),
       (57.5, 59, s_ring, 65, EMBER), (59, 62, s_ring, 70.4, None), (62, 64, s_ring, 77, None),
       (64, 77, s_fight, 116, None),                                                       # 三年之约开打：BGM 的两拍空白 + 满编进场
       (77, 82, s_page_train, L0, WHITEF), (82, 84, s_swallow, 96, CYAN), (84, 89, s_swallow, 98, None), (89, 93, s_swallow, 112, None),      # 架中间的回忆：这三年
       (93, 100, s_baji, 129, CYAN), (100, 106, s_lotus, 136, None), (106, 110, s_ots_duel, L0, None), (110, 112, s_lotus, 146, None),
       (112, 118, s_after, 148, None, 1 / 3), (118, 134, s_after, 150, None),              # 命中后 6 拍慢放，再接约毕
       (134, 161, s_home, 166, CP),
       (161, 168, s_y2, 193, WHITEF), (168, 174, s_p2, 200, None), (174, 176, s_y2, 206, None), (176, 180, s_pov_y2, L0, None), (180, 216, s_y2, 212, None),
       (216, 222, s_map, 254, WHITEF), (222, 230, s_end, 274, None), (230, 236, s_end, 282, None), (236, 241, s_end, 288, None), (241, 254.5, s_sign, L0, None)]
def seg_frame(i, t): fb0, fb1, fn, vb = SEG[i][:4]; rate = SEG[i][5] if len(SEG[i]) > 5 else 1.0; return fn(t - bt(fb0)) if vb == L0 else fn(bt(vb) + (t - bt(fb0)) * rate)
BADGE = [(5, '斗之力 三段'), (64, '大斗师'), (77, '斗之力 三段'), (78.5, '斗者'), (79.25, '斗师'), (91, '大斗师')]; BADGE_OFF = ((0, 5), (14, 24), (40, 44), (48, 51), (106, 110), (134, 999))
TAGS = [(34.2, 37.2, '纳兰嫣然', '云岚宗 少宗主', WIND, 'r', 150), (59.3, 61.8, '药老', '戒指里的灵魂', WHITEF, 'l', 150), (174.1, 176, '云棱', '云岚宗 首席长老', WIND, 'l', 150), (182.4, 185.6, '云山', '云岚宗上代宗主 · 斗宗', (0.86, 0.95, 1.0), 'l', 150)]
INKS = [(96, 0.10, 0.26), (128, 0.09, 0.28)]                                               # (拍, 命中后多久定格, 定多久)：八极崩、两指夹剑
ONO = [(70, '锵', (1330, 300), 16, (120, 255, 235)), (112, '轰', (960, 420), 8, (190, 130, 255)), (128, '锵', (1380, 250), 12, (255, 255, 255)), (180, '轰', (560, 400), -8, (210, 240, 255)), (212, '轰', (960, 400), 10, (210, 240, 255))]
PETALS = [(112, CYAN, PURP), (180, CYAN, WHITEF)]
def frame(t):
    b = (t - 0.5) / BEAT; i = next((k for k, sg in enumerate(SEG) if sg[0] <= b < sg[1]), 0 if b < 0 else len(SEG) - 1); tt = t
    for (hb, d0, hold) in INKS:
        if bt(hb) + d0 <= t < bt(hb) + d0 + hold: tt = bt(hb) + d0
    fr = seg_frame(i, tt)
    if tt != t: fr = fx.ink(fr, R)
    col = SEG[i][4]
    if col and t - bt(SEG[i][0]) < 0.5: fr = fx.burn(seg_frame(i - 1, bt(SEG[i][0]) - 1 / 60), fr, (t - bt(SEG[i][0])) / 0.5, col, R, seed=i, mode=('lr', 'out', 'rl', 'up')[i % 4], t=t)
    for (hb, ca, cb) in PETALS:
        if 0 <= t - bt(hb) < 1.6: s, c = layer(R.w, R.h); c.scale(R.k, R.k); fx.petals(c, (960, 500), t, bt(hb), 330, ca, cb, n=34, life=1.6); fr = A.add_glow(fr, s, 8 * R.k, 1.0)
    for (hb, ch, pos, rot, gl) in ONO: fr = slam(fr, t, hb, hb + 1.1, ch, pos, px=330, glow=gl, big=2.2, rot=rot)
    if b >= 5 and not any(a <= b < z for a, z in BADGE_OFF):
        k = max(j for j, (bb, _) in enumerate(BADGE) if bb <= b); fr = fx.badge(fr, R, BADGE[k][1], flip=max(0.05, (t - bt(BADGE[k][0])) / 0.22))
    for (b0, b1, nm, sub, cl, side, y) in TAGS:
        if b0 <= b < b1: fr = fx.tag(fr, R, nm, sub, cl, min((t - bt(b0)) / 0.25, (bt(b1) - t) / 0.2), side=side, y=y)
    return fr
def badge_(fr, text, k): return fx.badge(fr, R, text, flip=min(1.0, max(0.05, k)))
def u8(fr): return (np.clip(fr, 0, 1) * 255).astype(np.uint8)
def _cat(k, out):
    open('out/_fcat.txt', 'w').write(''.join(f"file '_fseg{R.h}_{i:02d}.mp4'\n" for i in range(k)))
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'out/_fcat.txt', '-i', 'out/mixfilm.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out], check=True); print('done', out)

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
    elif cmd == 'cat':
        k = int(sys.argv[2]); out = f'out/xiaoyan1_{R.h}p.mp4'; _cat(k, out)
    else:
        k = max(1, (os.cpu_count() or 2)) * 2; out = f'out/xiaoyan1_{R.h}p.mp4'; subprocess.run([sys.executable, 'mixfilm.py'], check=True); nproc = os.cpu_count() or 2
        for g in range(0, k, nproc):
            if any([p.wait() for p in [subprocess.Popen([sys.executable, 'film.py', 'seg', str(i), str(k)]) for i in range(g, min(k, g + nproc))]]): sys.exit('有分段渲染失败')
        _cat(k, out)
