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
    if name in ('stele', 'hall', 'border'): return getattr(sets, name)(R)
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

SHOTS = [(0, 4, s_hook), (4, 32, s_stele)]
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
