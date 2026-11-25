"""打斗样片（动作编排的写法示范）：项羽 vs 汉军 + 樊哙。空翻下劈、怒吼震退、格挡火花、抡戟风车、撑戟腾跃、上挑击飞、旋戟收势。
写法：KX/KF 关键帧（只写变化的量，自动沿用上一帧）→ SLOWS 慢放/顿帧窗口 → 冲击帧、集中线、拟声大字、兵器拖尾 → CAM 镜头关键帧。
  python fight.py still out.jpg t...   |   python fight.py render out.mp4
"""
import os, sys, math, subprocess, cairo, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from mapwar.qrig import draw, tip_world, joints, to_world, OL, PI, fs
from mapwar.qdraw import gold_metal, lin, rad
from mapwar.scenery import landscape
from mapwar.util import font
from cast.chuhan import XY, FK, HAN
from PIL import Image, ImageDraw
W, H, FPS = 1920, 1080, 30
OW, OH = 960, 540
SXY, SFK, SHAN = 360, 400, 270
TAU = 2 * PI


def sm(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def eout(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3


# ================================================================ 关键帧
STAND = dict(lean=0.05, hd=0.0, sf=0.5, ef=1.9, sb=-0.25, eb=0.15, hf=0.15, kf=0.02, hb=-0.15, kb=-0.05, w=PI - 0.12, sq=0.0, rot=0.0)
STEP = ('eye', 'brow', 'mouth', 'fx', 'f', 'run', 'flail', 'spin', 'shield')


def build(keys):
    out = []; cur = {}
    for t, d in keys: cur = dict(cur); cur.update(d); out.append((t, cur))
    return out


def pose_at(K, t):
    if t <= K[0][0]: return dict(K[0][1])
    if t >= K[-1][0]: return dict(K[-1][1])
    for i in range(len(K) - 1):
        if K[i][0] <= t < K[i + 1][0]: a, b = K[i], K[i + 1]; break
    u = (t - a[0]) / max(1e-6, b[0] - a[0]); e = u if b[1].get('lin') else sm(u)
    P = {}
    for k, v in a[1].items():
        if k in STEP or k == 'lin' or not isinstance(v, (int, float)) or k not in b[1]: P[k] = v
        else: P[k] = v + (b[1][k] - v) * e
    return P


def S0(**k): d = dict(STAND); d.update(k); return d


H0 = 0.3 * SXY
KX = build([
    (0.00, S0(x=-520, y=-H0, f=1, eye='dot2', brow='angry', mouth='smirk', fx=())),
    (1.50, dict(x=-500)),
    (1.75, dict(y=-80, lean=0.3, hf=0.7, kf=-0.3, hb=0.2, kb=-0.9, sf=1.2, ef=1.7, w=2.0, eye='fierce', mouth='grit')),
    (1.95, dict(y=-H0 - 4, lean=-0.2, hd=-0.25, sf=2.0, ef=2.7, sb=-1.7, eb=-2.3, w=2.6, hf=0.2, kf=0.0, hb=-0.2, kb=-0.05, mouth='shout', fx=('anger',))),
    (2.35, dict(lean=-0.22)),
    (2.55, dict(y=-70, lean=0.5, hd=0.0, hf=1.1, kf=-0.5, hb=0.4, kb=-1.3, sf=1.5, ef=1.8, sb=-0.2, eb=0.2, w=1.8, mouth='grit', fx=())),
    (2.66, dict(x=-470, y=-190, lean=0.2, hf=0.1, kf=0.1, hb=-0.3, kb=-0.3, sf=2.4, ef=2.8, w=3.0, sq=0.15)),
    (2.86, dict(x=-250, y=-480, hf=2.0, kf=-0.3, hb=1.8, kb=-0.5, sf=1.3, ef=2.2, w=2.0, sq=0.0)),
    (3.05, dict(x=-50, y=-610, rot=3.4)),
    (3.25, dict(x=120, y=-560, rot=TAU, hf=0.4, kf=0.1, hb=-0.4, kb=-0.2, sf=2.9, ef=3.1, w=PI + 0.8, lean=-0.1, mouth='shout')),
    (3.50, dict(x=310, y=-260, lean=0.3, sf=2.2, ef=2.6, w=PI + 0.2)),
    (3.60, dict(x=380, y=-62, lean=0.7, hf=1.2, kf=-0.5, hb=0.4, kb=-1.4, sf=1.4, ef=1.2, w=0.6, sq=-0.2, mouth='grit')),
    (3.75, dict(sq=0.0)),
    (4.20, dict()),
    (4.50, S0(x=380, y=-H0, rot=TAU, eye='dot2', mouth='smirk')),
    (5.20, dict(eye='fierce', mouth='grit')),
    (5.45, dict(sf=2.6, ef=2.25, sb=2.3, eb=2.5, w=PI / 2, hf=0.5, kf=-0.1, hb=-0.4, kb=-0.3, lean=-0.1)),
    (5.60, dict()),
    (5.75, dict(x=330, fx=('sweat',))),
    (6.10, dict(sf=1.0, ef=1.0, w=0.5, sb=-0.3, eb=0.1, hf=0.3, kf=0.0, hb=-0.3, kb=-0.1, lean=0.1, mouth='shout', fx=())),
    (6.20, dict(spin=(6.2, 7.0, 2))),
    (7.00, dict(spin=None, sf=0.6, ef=0.5, w=0.5)),
    (7.10, dict(x=360, lean=0.35, eye='dot2', mouth='smirk')),
    (7.20, dict(x=430, y=-140, sf=2.5, ef=2.3, w=0.35, lean=0.2)),
    (7.45, dict(x=600, y=-560, rot=TAU + PI, hf=0.4, kf=0.2, hb=-0.3, kb=-0.4, sf=2.7, ef=2.9, w=PI - 0.4)),
    (7.75, dict(x=820, y=-200, rot=2 * TAU)),
    (7.85, dict(x=850, y=-80, lean=0.4, hf=1.0, kf=-0.4, hb=0.3, kb=-1.1, sf=1.2, ef=1.6, w=1.8, sq=-0.12)),
    (7.95, dict(f=-1, sq=0.0)),
    (8.00, dict(y=-H0, lean=0.05, hf=0.15, kf=0.02, hb=-0.15, kb=-0.05, sf=0.5, ef=1.9, w=PI - 0.12, eye='fierce', mouth='grit')),
    (8.25, dict(x=820, y=-90, lean=0.45, sf=0.4, ef=0.6, w=0.4, hf=0.8, kf=-0.3, hb=0.2, kb=-1.0, mouth='shout')),
    (8.40, dict(x=600, y=-125, lean=-0.1, sf=2.6, ef=2.9, w=PI - 0.3, hf=0.3, kf=0.0, hb=-0.5, kb=-0.2)),
    (8.60, dict(x=580)),
    (9.20, dict(x=600, y=-H0, lean=0.05, hf=0.15, kf=0.02, hb=-0.15, kb=-0.05, sf=0.5, ef=1.9, w=PI - 0.12, eye='dot2', mouth='smile')),
    (9.30, dict(spin=(9.3, 10.1, 3))),
    (10.10, dict(spin=None)),
    (10.15, dict(sf=0.5, ef=1.9, w=PI, lean=-0.06, hd=-0.1, eye='glint', mouth='smirk', sq=-0.06)),
    (10.30, dict(sq=0.0)),
    (12.0, dict()),
])

H1 = 0.3 * SFK
KF = build([
    (0.00, S0(x=1900, y=-H1, f=-1, sf=1.0, ef=2.0, w=PI + 0.5, sb=1.3, eb=1.6, lean=0.35, eye='fierce', brow='angry', mouth='shout', fx=('anger',), run=True, shield=True)),
    (4.55, dict(x=1450)),
    (5.25, dict(x=800)),
    (5.32, dict(x=740, y=-260, run=False, hf=1.4, kf=-0.2, hb=0.3, kb=-0.8, sf=2.8, ef=3.0, w=PI + 0.9, lean=0.1)),
    (5.50, dict(x=580, y=-200, sf=2.0, ef=1.6, w=1.7)),
    (5.60, dict(x=530, y=-140, mouth='grit', fx=('sweat',))),
    (5.75, dict(x=640, y=-H1, hf=0.3, kf=0.0, hb=-0.3, kb=-0.1, lean=0.15)),
    (6.15, dict(x=660, sf=1.3, ef=2.0, w=PI * 0.75, sb=1.4, eb=1.6, eye='fierce', mouth='grit', fx=())),
    (6.30, dict(x=680, y=-95, hf=0.9, kf=-0.4, hb=0.2, kb=-1.0, eye='shock', mouth='o')),
    (6.45, dict(x=760, y=-380, rot=-PI, hf=2.0, kf=-0.3, hb=1.8, kb=-0.5)),
    (6.65, dict(x=880, y=-300, rot=-TAU)),
    (6.80, dict(x=900, y=-95, hf=0.9, kf=-0.4, hb=0.2, kb=-1.0, fx=('sweat',))),
    (7.00, dict(y=-H1, lean=0.5, sb=1.6, eb=1.5, sf=-0.3, ef=0.2, w=PI + 0.6, hf=0.3, kf=0.0, hb=-0.3, kb=-0.1, eye='fierce', mouth='shout', fx=())),
    (7.15, dict(x=860, run=True)),
    (7.65, dict(x=420)),
    (7.80, dict(x=360, run=False, lean=-0.1, sf=0.6, ef=0.3, w=0.4, sb=0.3, eb=0.5, eye='dot', brow='raised', mouth='flat', fx=('q',))),
    (8.15, dict(hd=0.25)),
    (8.20, dict(f=1, hd=0.0, eye='shock', mouth='o', fx=('shocklines',))),
    (8.40, dict(flail=True, shield=False, mouth='wavy')),
    (8.90, dict(x=120, y=-540, rot=-TAU - 2.6)),
    (9.35, dict(x=-30, y=-60, rot=-2 * TAU)),
    (9.40, dict(x=-40, y=-48, flail=False, hf=1.5, kf=1.4, hb=1.4, kb=1.6, sf=-0.6, ef=-0.2, sb=-0.7, eb=-0.3, lean=-0.15, w=-0.3, eye='dizzy', mouth='wavy', fx=('stars',), sq=-0.2)),
    (9.55, dict(sq=0.0)),
    (12.0, dict()),
])


def procedural(P, ta, S):
    if P.get('run'):
        ph = ta * 13
        P['hf'] = 0.9 * math.sin(ph); P['kf'] = P['hf'] - 1.0 * max(0, math.sin(ph + 0.8)) - 0.2
        P['hb'] = -0.9 * math.sin(ph); P['kb'] = P['hb'] - 1.0 * max(0, math.sin(ph + 0.8 + PI)) - 0.2
        P['y'] = P['y'] - 10 * abs(math.sin(ph))
    if P.get('flail'):
        for k, a in (('sf', 2.4), ('ef', 2.7), ('sb', -2.0), ('eb', -2.5), ('hf', 1.2), ('kf', 0.5), ('hb', -0.6), ('kb', -1.0)): P[k] = a + 0.5 * math.sin(ta * 22 + len(k))
        P['eye'] = 'dizzy'
    sp = P.get('spin')
    if sp and sp[0] <= ta <= sp[1]:
        u = (ta - sp[0]) / (sp[1] - sp[0]); a = 0.5 + TAU * sp[2] * (u if sp[2] == 2 else sm(u))
        if sp[2] == 2: P['sf'] = a - 0.1; P['ef'] = a; P['w'] = a
        else: P['sf'] = 2.9; P['ef'] = 3.05; P['w'] = PI + TAU * sp[2] * sm(u)
    return P


# ================================================================ 小兵
SOL = [(150, 0.0), (270, 0.6), (390, 1.2), (500, 1.9), (620, 2.4), (1020, 3.0), (1160, 3.6)]


def soldier(i, ta):
    x0, ph = SOL[i]; x = x0 - min(ta, 1.9) * 25
    P = dict(STAND, x=x, y=-0.3 * SHAN - 3 * abs(math.sin(ta * 6 + ph)), f=-1, sf=1.4, ef=1.55, w=1.5, eye='dot', brow='worried', mouth='wavy', fx=('sweat',), lean=0.05)
    if ta >= 1.95: P.update(eye='shock', mouth='o', fx=('shocklines',), lean=-0.25 + 0.03 * math.sin(ta * 30) * (ta < 2.4), hd=-0.15)
    if i < 5 and ta >= 3.6 + i * 0.015:
        a = ta - 3.6; r = np.random.default_rng(i); vx = (1 if x0 > 380 else -1) * r.uniform(500, 900); vy = -r.uniform(900, 1400)
        P.update(x=x + vx * a, y=P['y'] + vy * a + 1100 * a * a, rot=r.choice([-1, 1]) * r.uniform(7, 12) * a, eye='dizzy', mouth=r.choice(['o', 'wavy']), fx=(), flail=True)
        P = procedural(P, ta + i, SHAN)
        if P['y'] > 1500: return None
    if i >= 5 and ta >= 3.75:
        a = ta - 3.75; P.update(f=1, x=x + 820 * a, run=True, eye='shock', mouth='wavy', fx=('sweat',), lean=0.3, sf=2.6, ef=2.9, sb=2.4, eb=2.8, w=2.8); P = procedural(P, ta + i, SHAN)
        if a > 2.5: return None
    return P


# ================================================================ 时间重映射（慢放 / 顿帧）
SLOWS = [(2.98, 3.12, 0.3), (3.60, 3.606, 0.05), (5.60, 5.604, 0.05), (8.40, 8.405, 0.04), (8.405, 8.60, 0.35)]
ACT_END = 11.8
_tab = []
ta, tf = 0.0, 0.0; dt = 1 / 600
while ta < ACT_END:
    r = next((rt for a, b, rt in SLOWS if a <= ta < b), 1.0); _tab.append((tf, ta)); ta += dt * r; tf += dt
TF, TA = np.array([x[0] for x in _tab]), np.array([x[1] for x in _tab])
DUR = float(TF[-1]) + 0.2
def act(t): return float(np.interp(t, TF, TA))
def film_of(a): return float(np.interp(a, TA, TF))


# ================================================================ 镜头
CAM = [(0.0, -150, -300, 0.944), (1.5, -380, -270, 1.121), (1.95, -470, -265, 1.475), (2.4, -420, -270, 1.357), (2.6, -300, -330, 1.003), (3.05, -20, -480, 0.850),
       (3.45, 260, -300, 1.003), (3.6, 380, -220, 1.180), (4.4, 420, -250, 1.121), (5.0, 650, -260, 0.968), (5.6, 450, -290, 1.475), (5.9, 520, -270, 1.180), (6.3, 520, -270, 1.086),
       (7.0, 600, -270, 1.038), (7.45, 620, -380, 0.944), (7.9, 600, -260, 1.086), (8.4, 480, -260, 1.357), (8.7, 300, -300, 1.062), (9.4, 300, -240, 1.086), (10.1, 520, -260, 1.121),
       (10.3, 600, -300, 1.239), (12.0, 600, -330, 1.593)]
SHAKES = [(1.95, 16, 0.5), (3.6, 42, 0.55), (5.6, 22, 0.3), (8.4, 34, 0.45), (10.15, 14, 0.3)]


def cam_at(ta, tfilm):
    for i in range(len(CAM) - 1):
        if CAM[i][0] <= ta < CAM[i + 1][0]: a, b = CAM[i], CAM[i + 1]; break
    else: a = b = CAM[-1]
    u = sm((ta - a[0]) / max(1e-6, b[0] - a[0])) if a is not b else 0
    cx, cy, z = [a[k] + (b[k] - a[k]) * u for k in (1, 2, 3)]
    sx = sy = 0
    for t0, amp, d in SHAKES:
        f0 = film_of(t0)
        if 0 <= tfilm - f0 < d: e = amp * (1 - (tfilm - f0) / d) ** 2; sx += e * math.sin(tfilm * 91); sy += e * math.sin(tfilm * 73 + 1)
    return cx, cy, z, sx, sy


# ================================================================ 背景
_BG = {}


def bg(cx, cy, z):
    if 'b' not in _BG:
        b = landscape('day') * np.float32([1.04, 0.95, 0.84]); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        b = b + (np.exp(-((xx - 1300) ** 2 + (yy - 420) ** 2) / (2 * 380 ** 2)) * 0.25)[..., None] * np.float32([1, 0.75, 0.4])
        _BG['b'] = Image.fromarray((np.clip(b, 0, 1) * 255).astype(np.uint8)).resize((2400, 1350))
    B = _BG['b']; k = 1 + (z - 0.8) * 0.18; w, h = 1920 / k * 1.0, 1080 / k
    ox = 240 + cx * 0.06 - (w - 1920) / 2; oy = 135 + (cy + 280) * 0.12 - (h - 1080) / 2
    ox = min(max(ox, 0), 2400 - w); oy = min(max(oy, 0), 1350 - h)
    return np.asarray(B.crop((int(ox), int(oy), int(ox + w), int(oy + h))).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255


def ground(c, cx, z):
    x0, x1 = cx - 2000 / z, cx + 2000 / z
    c.rectangle(x0, 0, x1 - x0, 2500); c.set_source(lin(0, 0, 0, 900, [(0, (0.66, 0.54, 0.36)), (1, (0.40, 0.30, 0.18))])); c.fill()
    c.move_to(x0, 0); c.line_to(x1, 0); c.set_source_rgba(0.3, 0.22, 0.12, 0.6); c.set_line_width(3); c.stroke()
    for gx in range(int(x0 // 70) * 70, int(x1), 70):
        r = np.random.default_rng(gx & 0xffff); y = r.uniform(10, 600); s = 0.6 + y / 600
        for k in (-1, 0, 1): c.move_to(gx, y); c.curve_to(gx + k * 6 * s, y - 14 * s, gx + k * 10 * s, y - 22 * s, gx + k * 14 * s, y - 30 * s)
        c.set_source_rgba(0.28, 0.22, 0.10, 0.45); c.set_line_width(2.5 * s); c.stroke()
        if r.random() < 0.25: c.save(); c.translate(gx + 30, y + 10); c.scale(1, 0.5); c.arc(0, 0, 10 * s, 0, TAU); c.restore(); c.set_source_rgba(0.35, 0.3, 0.25, 0.7); c.fill()


# ================================================================ 特效
def dust(c, x, y, age, n=10, size=60, seed=1, spread=1.0):
    if age < 0 or age > 1.4: return
    r = np.random.default_rng(seed)
    for k in range(n):
        a = r.uniform(PI, TAU) if spread else r.uniform(0, PI); sp = r.uniform(150, 420) * spread
        px = x + math.cos(a) * sp * age; py = y + math.sin(a) * sp * 0.35 * age - 30 * age; rr = size * r.uniform(0.6, 1.2) * (0.6 + age)
        c.arc(px, py, rr, 0, TAU); c.set_source_rgba(0.88, 0.78, 0.62, 0.55 * (1 - age / 1.4)); c.fill()


def ring(c, x, y, age, rmax=600, flat=0.25, col=(1, 0.95, 0.8), dur=0.5, w=24):
    if age < 0 or age > dur: return
    u = eout(age / dur); c.save(); c.translate(x, y); c.scale(1, flat); c.arc(0, 0, 40 + rmax * u, 0, TAU); c.restore()
    c.set_source_rgba(*col, 0.85 * (1 - age / dur)); c.set_line_width(w * (1 - age / dur) + 2); c.stroke()


def sparks(c, x, y, age, seed=3, n=40, dur=0.6):
    if age < 0 or age > dur: return
    r = np.random.default_rng(seed); u = age / dur
    for k in range(n):
        a = r.uniform(0, TAU); sp = r.uniform(400, 1300); L = r.uniform(25, 80) * (1 - u)
        px, py = x + math.cos(a) * sp * age, y + math.sin(a) * sp * age + 700 * age * age
        c.move_to(px, py); c.line_to(px - math.cos(a) * L, py - math.sin(a) * L); c.set_source_rgba(1, 0.92 - 0.4 * u, 0.5, 1 - u); c.set_line_width(r.uniform(2.5, 6)); c.stroke()
    c.arc(x, y, 50 + 260 * u, 0, TAU); c.set_source(rad(x, y, 0, 50 + 260 * u, [(0, (1, 1, 0.9, 0.95 * (1 - u))), (0.3, (1, 0.8, 0.4, 0.5 * (1 - u))), (1, (1, 0.6, 0.2, 0))])); c.fill()


def debris(c, x, y, age, seed=5, n=16, col=(0.45, 0.36, 0.26), sz=22):
    if age < 0 or age > 1.6: return
    r = np.random.default_rng(seed)
    for k in range(n):
        vx = r.uniform(-700, 700); vy = -r.uniform(500, 1300); px = x + vx * age; py = y + vy * age + 1800 * age * age
        if py > 40: continue
        s_ = sz * r.uniform(0.5, 1.3); c.save(); c.translate(px, py); c.rotate(age * r.uniform(-12, 12)); c.move_to(-s_, -s_ * 0.6); c.line_to(s_ * 0.8, -s_); c.line_to(s_, s_ * 0.5); c.line_to(-s_ * 0.6, s_); c.close_path()
        fs(c, col, 2); c.restore()


def crack(c, x, age):
    if age < 0: return
    r = np.random.default_rng(11); L = 260 * eout(age / 0.15)
    for k in range(7):
        a = r.uniform(-0.5, 0.5) + (0 if k % 2 else PI); px, py = x, 0.0; c.move_to(px, py)
        for j in range(5): px += math.cos(a) * L / 5 * r.uniform(0.6, 1.2); py += r.uniform(-4, 24); c.line_to(px, py)
        c.set_source_rgba(0.12, 0.08, 0.05, 0.85); c.set_line_width(5); c.stroke()


def trail(c, K, ta, S, spec, n=10, dt=0.012, col=(1, 0.93, 0.6), minspd=900, wmax=34):
    pts = []
    for k in range(n):
        P = procedural(pose_at(K, ta - k * dt), ta - k * dt, S); pts.append(tip_world(P, S, spec))
    spd = math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]) / dt
    if spd < minspd: return
    a0 = min(1, (spd - minspd) / 1500)
    for k in range(n - 1):
        c.move_to(*pts[k]); c.line_to(*pts[k + 1]); c.set_source_rgba(*col, 0.9 * a0 * (1 - k / n)); c.set_line_width(wmax * (1 - k / n) + 2); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()


def focus_lines(c, cx, cy, a, seed=2, n=70):
    r = np.random.default_rng(seed + int(a * 1000) % 7)
    for k in range(n):
        ang = r.uniform(0, TAU); r0 = r.uniform(380, 620); r1 = 1400; w = r.uniform(2, 9)
        c.move_to(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0); c.line_to(cx + math.cos(ang + 0.012) * r1, cy + math.sin(ang + 0.012) * r1); c.line_to(cx + math.cos(ang - 0.012) * r1, cy + math.sin(ang - 0.012) * r1); c.close_path()
        c.set_source_rgba(0.05, 0.03, 0.02, 0.55 * a); c.fill()


def sfx(img, s_, x, y, age, size=170, col=(235, 60, 30), rot=-8, dur=0.7):
    if age < 0 or age > dur: return img
    sz = int(size * (1 + 0.6 * (1 - eout(age / 0.12)))); a = 1 - max(0, (age - dur + 0.2) / 0.2)
    lay = Image.new('RGBA', (sz * 3, sz * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((sz * 1.5, sz), s_, font=font(sz), anchor='mm', fill=col + (int(255 * a),), stroke_width=int(sz * 0.08), stroke_fill=(255, 245, 225, int(255 * a)))
    lay = lay.rotate(rot, resample=Image.BICUBIC); img.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2))); return img


# ================================================================ 帧
def frame(tfilm):
    ta = act(tfilm); cx, cy, z, sx, sy = cam_at(ta, tfilm)
    B = bg(cx, cy, z)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    c.translate(W / 2 + sx, H * 0.62 + sy); c.scale(z, z); c.translate(-cx, -cy)
    ground(c, cx, z); crack(c, 380, ta - 3.6)
    # 光芒（收势）
    if ta >= 10.1:
        P = pose_at(KX, ta); hc = to_world(P, SXY, joints(P, SXY)['head']); k = sm((ta - 10.1) / 0.4)
        for i in range(24):
            a = i / 24 * TAU + ta * 0.3; c.move_to(*hc); c.line_to(hc[0] + math.cos(a) * 1600, hc[1] + math.sin(a) * 1600); c.line_to(hc[0] + math.cos(a + 0.07) * 1600, hc[1] + math.sin(a + 0.07) * 1600); c.close_path()
            c.set_source_rgba(1, 0.85, 0.45, 0.16 * k); c.fill()
    # 小兵
    for i in range(len(SOL)):
        P = soldier(i, ta)
        if P: draw(c, P, SHAN, HAN, ta + i)
    # 樊哙
    PF = procedural(pose_at(KF, ta), ta, SFK); PF['vx'] = (pose_at(KF, ta)['x'] - pose_at(KF, ta - 0.03)['x']) / 0.03
    if ta >= 4.5: draw(c, PF, SFK, dict(FK, shield='beast' if PF.get('shield', True) else False), ta)
    if 4.5 <= ta < 9.4: trail(c, KF, ta, SFK, FK, col=(0.9, 0.95, 1.0), minspd=1100, wmax=26)
    # 项羽
    PX = procedural(pose_at(KX, ta), ta, SXY); PX['vx'] = (pose_at(KX, ta)['x'] - pose_at(KX, ta - 0.03)['x']) / 0.03
    PX['flags'] = abs(PX['vx']) < 350 and abs(math.remainder(PX.get('rot', 0), TAU)) < 0.15 and PX['y'] > -H0 - 40 and not PX.get('spin') and not (2.4 <= ta < 4.45 or 6.0 <= ta < 8.1)
    trail(c, KX, ta, SXY, XY)
    draw(c, PX, SXY, XY, ta)
    # 地面/打击特效
    dust(c, -470, 0, ta - 2.62, 8, 45, 1); dust(c, 380, 0, ta - 3.6, 18, 90, 2); ring(c, 380, 0, ta - 3.6, 900, 0.22, dur=0.6, w=40); debris(c, 380, 0, ta - 3.6)
    ring(c, -470, -480, ta - 1.95, 700, 1.0, col=(1, 1, 1), dur=0.45, w=26); ring(c, -470, -480, ta - 2.1, 700, 1.0, col=(1, 1, 1), dur=0.45, w=18)
    sparks(c, 470, -400, ta - 5.6, 3); ring(c, 470, -400, ta - 5.6, 400, 1.0, dur=0.3, w=16); dust(c, 330, 0, ta - 5.62, 6, 40, 4); dust(c, 640, 0, ta - 5.62, 6, 40, 5)
    dust(c, 900, 0, ta - 6.8, 8, 50, 6); dust(c, 430, 0, ta - 7.2, 6, 40, 7); dust(c, 850, 0, ta - 7.85, 10, 55, 8)
    sparks(c, 430, -260, ta - 8.4, 9, 50); ring(c, 430, -260, ta - 8.4, 500, 1.0, dur=0.35, w=22); debris(c, 420, -240, ta - 8.4, 12, 10, (0.55, 0.22, 0.12), 34); dust(c, -40, 0, ta - 9.4, 12, 60, 9)
    dust(c, 600, 0, ta - 10.15, 10, 50, 10); ring(c, 600, 0, ta - 10.15, 500, 0.22, dur=0.5, w=20)
    # 屏幕空间：集中线
    c.identity_matrix()
    def wpt(p): return (W / 2 + sx + (p[0] - cx) * z, H * 0.62 + sy + (p[1] - cy) * z)
    for (t0, t1, who) in ((1.95, 2.4, 'x'), (3.6, 3.85, 'i'), (5.6, 5.75, 'c'), (8.4, 8.62, 'h'), (10.15, 10.55, 'x')):
        if t0 <= ta < t1:
            a = 1 - (ta - t0) / (t1 - t0); p = {'x': to_world(PX, SXY, joints(PX, SXY)['head']), 'i': (380, -150), 'c': (470, -400), 'h': (430, -260)}[who]; focus_lines(c, *wpt(p), a)
    a = np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32) / 255
    fr = B * (1 - a[..., 3:4]) + a[..., [2, 1, 0]]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); vr = ((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2; fr = fr * (1 - 0.7 * vr[..., None])
    for t0 in (3.6, 8.4):                                                       # 闪白
        f0 = film_of(t0)
        if 0 <= tfilm - f0 < 0.25: fr = fr + (1 - (tfilm - f0) / 0.25) ** 2 * 0.5
    # 冲击帧：两帧黑白反转
    for t0 in (3.6, 8.4):
        f0 = film_of(t0); k = int(round((tfilm - f0) * FPS))
        if k in (0, 1):
            g = fr.mean(-1, keepdims=True); m = (g > 0.55).astype(np.float32)
            fr = (m * np.float32([0.08, 0.04, 0.03]) + (1 - m) * np.float32([1.0, 0.96, 0.9])) if k == 0 else (m * np.float32([1.0, 0.95, 0.85]) + (1 - m) * np.float32([0.6, 0.06, 0.04]))
    img = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    hx = wpt(to_world(PX, SXY, joints(PX, SXY)['head']))
    img = sfx(img, '喝！', hx[0] + 260, hx[1] - 200, ta - 1.95, 190, dur=0.55)
    p = wpt((380, -300)); img = sfx(img, '轰！', p[0], p[1] - 240, ta - 3.6, 240, rot=6, dur=0.6)
    p = wpt((470, -400)); img = sfx(img, '铛！', p[0] + 120, p[1] - 200, ta - 5.6, 170, col=(250, 200, 60), dur=0.45)
    p = wpt((430, -260)); img = sfx(img, '砰！', p[0] - 200, p[1] - 220, ta - 8.4, 210, rot=10, dur=0.6)
    if ta >= 10.15:
        l = ta - 10.15; sz = int(230 * (1 + 0.5 * (1 - eout(l / 0.16)))); d = ImageDraw.Draw(img)
        d.text((W / 2 + 10, 190), '西楚霸王', font=font(sz), anchor='mm', fill=(20, 10, 8, 220))
        d.text((W / 2, 180), '西楚霸王', font=font(sz), anchor='mm', fill=(205, 34, 22, 255), stroke_width=14, stroke_fill=(255, 236, 190, 255))
    if tfilm > DUR - 0.6: img = Image.fromarray((np.asarray(img.convert('RGB')) * (1 - (tfilm - DUR + 0.6) / 0.6)).astype(np.uint8))
    return img.convert('RGB')


if __name__ == '__main__':
    if sys.argv[1] == 'still':
        ims = [frame(float(x)).resize((OW, OH)) for x in sys.argv[3:]]
        sh = Image.new('RGB', (OW * 2, OH * ((len(ims) + 1) // 2)))
        for i, im in enumerate(ims): sh.paste(im, ((i % 2) * OW, (i // 2) * OH))
        sh.save(sys.argv[2], quality=85)
    else:
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', sys.argv[2]], stdin=subprocess.PIPE)
        for i in range(int(DUR * FPS)): p.stdin.write(np.asarray(frame(i / FPS).resize((OW, OH), Image.LANCZOS)).tobytes())
        p.stdin.close(); p.wait()
