"""四渡赤水的斜视角战场（自己摆兵）：开头合围、土城仰攻、娄山关冲锋、夜渡赤水、金沙江。每个函数返回 HxWx3 float。"""
import sys, math, numpy as np
import os; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
from mapwar import eggfield as E, eggfx as X
GREY = (0.46, 0.50, 0.52)
RED = dict(body=GREY, head=(0.40, 0.44, 0.47), square=False, hat='bajiao', weapon='rifle', shaft=(0.62, 0.38, 0.18), fierce=True, belt=(0.36, 0.22, 0.12), chest=False)
ZY = dict(body=(0.50, 0.50, 0.40), head=(0.36, 0.42, 0.36), square=False, hat='helmet', band=None, plume=None, weapon='rifle', shaft=(0.55, 0.34, 0.16), fierce=False, belt=(0.36, 0.22, 0.12), chest=False)
CJ = dict(ZY, body=(0.42, 0.44, 0.50), head=(0.33, 0.35, 0.42), hat='junmao')
QJ = dict(ZY, body=(0.56, 0.49, 0.34), head=(0.84, 0.72, 0.46), hat='strawhat')
Z = lambda n, v=0.0: np.full(n, v, np.float32)


def block(rows, cols, sp, cx, cy, ang=0.0, jit=0.15, seed=0):
    r = np.random.default_rng(seed); p = np.float32([((i - (rows - 1) / 2) * sp, (j - (cols - 1) / 2) * sp) for i in range(rows) for j in range(cols)]) + r.uniform(-jit, jit, (rows * cols, 2)).astype(np.float32)
    ca, sa = math.cos(ang), math.sin(ang); return np.c_[p[:, 0] * ca - p[:, 1] * sa + cx, p[:, 0] * sa + p[:, 1] * ca + cy].astype(np.float32)


def mk(parts):
    """parts: [(pos, face, state, phase, spd, extra dict)]，第一个是红军。"""
    n = [len(p[0]) for p in parts]; N = sum(n); F = dict(pos=np.concatenate([p[0] for p in parts]).astype(np.float32), z=Z(N), fall=(np.arange(N) * 2.399 % 6.28).astype(np.float32))
    for k, i in (('face', 1), ('state', 2), ('phase', 3), ('spd', 4)): F[k] = np.concatenate([np.broadcast_to(np.asarray(p[i]), (len(p[0]),)) for p in parts]).astype(np.int32 if k == 'state' else np.float32)
    for k in ('fire', 'dao', 'crouch', 'z'):
        if any(k in p[5] for p in parts): F[k] = np.concatenate([np.broadcast_to(np.asarray(p[5].get(k, 0)), (len(p[0]),)) for p in parts]).astype(bool if k in ('dao', 'crouch') else np.float32)
    red = np.r_[np.ones(n[0], bool), np.zeros(N - n[0], bool)]; return F, red, N


# ---------------------------------------------------------------- 开头：四面合围
_H = {}


def hook(lt):
    E.set_looks(RED, ZY)
    if not _H:
        _H['r'] = block(8, 10, 1.5, 0, 0, 0.3, 0.3, 1); _H['e'] = [block(11, 34, 1.5, 0, 0, 0, 0.2, 2 + k) for k in range(4)]; _H['ph'] = np.random.default_rng(1).uniform(0, 6, 5000).astype(np.float32)
    t = lt; d = 40 - 6.0 * t; parts = [(_H['r'], _H['ph'][:80] * 0 + np.linspace(0, 6.28, 80), 0, 0.0, 0.0, {})]
    for k, (ax, ay) in enumerate(((1, 0), (0, 1), (-1, 0), (0, -1))):
        a = math.atan2(-ay, -ax); b = _H['e'][k]; ca, sa = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
        pos = np.c_[b[:, 1] * ca - b[:, 0] * ax + ax * d, b[:, 1] * sa - b[:, 0] * ay + ay * d]
        parts.append((pos, a, 0, t * 9 + _H['ph'][k * 400:k * 400 + len(b)], 4.0, {}))
    F, red, N = mk(parts)
    cam = E.make_cam(0, -3, 60 - 5 * t, 40 - 3 * t, 100 + 5 * t)
    def over(c, cam):
        for k in range(3): X.plane(c, cam, -60 + 50 * t - k * 10, -12 + k * 12, 14, 0.1, 0.6)
    fr, _ = E.scene(cam, F, red, np.zeros(N, bool), t, np.ones(N, bool), over=over)
    return fr


# ---------------------------------------------------------------- 土城：仰攻高地，被炮火压回
_T = {}


def tucheng(lt, enemy=None):
    E.set_looks(RED, enemy or CJ)
    if not _T:
        r = np.random.default_rng(7); _T['r'] = block(7, 13, 1.9, -8, 0, 0, 0.5, 3); _T['e'] = np.float32([(19.6 + (j % 2) * 1.5, -15 + j * 0.86) for j in range(36)])
        _T['rnd'] = r.random((len(_T['r']), 3)).astype(np.float32); _T['ern'] = r.random(36).astype(np.float32)
        _T['bl'] = [(0.25 + 0.42 * k, 2 + r.uniform(-6, 10), r.uniform(-11, 11), 1.2 + 0.5 * r.random()) for k in range(8)]
    t = lt; R0 = _T['r']; rnd = _T['rnd']; nr = len(R0)
    adv = np.minimum(t, 1.7) * 6.5 - np.maximum(0, t - 2.0) * 4.5; pos = R0 + np.float32([adv, 0]); pos[:, 1] += 0.2 * np.sin(t * 8 + rnd[:, 0] * 6)
    st = np.zeros(nr, np.int32)
    for (bt, bx, by, sz) in _T['bl']:
        hit = (np.hypot(pos[:, 0] - bx, pos[:, 1] - by) < 2.6 * sz) & (t > bt + 0.05); st[hit] = 3
    face = 0.0
    ef = np.clip(np.sin(t * 15 + _T['ern'] * 30) * 3 - 2, 0, 1)
    F, red, N = mk([(pos, face, st, t * 10 + rnd[:, 1] * 6, 6.5, {}), (_T['e'], math.pi, 0, 0.0, 0.0, dict(fire=ef, crouch=True))])
    props = X.sandbag_line((18.6, -16), (18.6, 16), rows=3) + [X.crater(bx, by, min(1, (t - bt) * 3)) for (bt, bx, by, sz) in _T['bl'] if t > bt] + [X.blast(bx, by, t - bt, sz, k) for k, (bt, bx, by, sz) in enumerate(_T['bl'])]
    sk = 0.5 * sum(math.exp(-(t - bt) / 0.15) for (bt, *_) in _T['bl'] if t >= bt)
    cam = E.make_cam(7 + 0.8 * t + sk * math.sin(t * 70), -1 + sk * math.cos(t * 55), 30 + 1.5 * t, 25, 128)
    def under(c, cam): X.hill(c, cam, 30, 0, 16, 30, 2.2, (0.56, 0.56, 0.42))
    def over(c, cam):
        sh = []
        for j in range(0, 36, 2):
            u = (t * 2.2 + _T['ern'][j] * 3) % 1.3; e = _T['e'][j]; sh.append(((e[0] - 1, e[1], 1.2), (e[0] - 30, e[1] + (_T['ern'][j] - 0.5) * 8, 1.0), u))
        X.tracers(c, cam, sh)
    fr, _ = E.scene(cam, F, red, np.zeros(N, bool), t, np.ones(N, bool), props=props, under=under, over=over)
    fl = sum(0.35 * math.exp(-(t - bt) / 0.06) for (bt, *_) in _T['bl'] if t >= bt)
    return fr + np.float32([1, 0.9, 0.7]) * fl


# ---------------------------------------------------------------- 娄山关：大刀、刺刀、手榴弹，冲垮守军
_L = {}


def loushan(lt):
    E.set_looks(RED, QJ)
    if not _L:
        r = np.random.default_rng(3); _L['r'] = block(9, 13, 1.8, -6, 0, 0, 0.45, 5); _L['e'] = block(4, 20, 1.45, 23.5, 0, 0, 0.25, 6)
        _L['rnd'] = r.random((len(_L['e']), 3)).astype(np.float32); _L['rph'] = r.uniform(0, 6, len(_L['r'])).astype(np.float32)
        _L['gr'] = [(0.15 + 0.22 * k, r.uniform(-9, 9), r.uniform(-10, 10)) for k in range(7)]
    t = lt; R0 = _L['r']; nr = len(R0); E0 = _L['e']; ne = len(E0); rnd = _L['rnd']
    Xr = 3 + 8.5 * t; pos = R0 + np.float32([Xr, 0]); pos[:, 1] += 0.15 * np.sin(t * 9 + _L['rph'])
    dao = (np.arange(nr) // 13 >= 6) & (np.arange(nr) % 2 == 0)                 # 前排一半人举大刀
    en = E0.copy(); st = np.zeros(ne, np.int32); face = np.full(ne, math.pi, np.float32); spd = Z(ne)
    th = 1.15 + (E0[:, 0] - 21) * 0.1 + rnd[:, 1] * 0.45; u = np.clip(t - th, 0, None); m = u > 0
    en[m, 0] += 5.0 * u[m]; en[m, 1] += np.sign(E0[m, 1]) * 1.5 * u[m]; st[m] = 2; face[m] = 0.0; spd[m] = 6
    for (gt, gy, gy2) in _L['gr']:
        hit = (np.hypot(E0[:, 0] - 22, E0[:, 1] - gy2) < 2.2) & (t > gt + 0.55); st[hit] = 3
    ef = np.where(~m, np.clip(np.sin(t * 13 + rnd[:, 0] * 20) * 3 - 2, 0, 1), 0)
    F, red, N = mk([(pos, 0.0, 0, t * 11 + _L['rph'], 8.5, dict(dao=dao)), (en, face, st, u * 11 + rnd[:, 1] * 6, spd, dict(fire=ef, crouch=~m))])
    props = X.sandbag_line((20.2, -15), (20.2, 15), rows=2) + [X.blast(22, gy2, t - gt - 0.55, 1.0, k) for k, (gt, gy, gy2) in enumerate(_L['gr'])]
    sk = 0.4 * sum(math.exp(-(t - gt - 0.55) / 0.15) for (gt, *_) in _L['gr'] if t >= gt + 0.55)
    cam = E.make_cam(Xr + 5 + sk * math.sin(t * 70), -3 + sk * math.cos(t * 50), 20 + 2.2 * t, 24, 114)
    def under(c, cam): X.hill(c, cam, 30, 34, 40, 16, 9, (0.44, 0.52, 0.40)); X.hill(c, cam, 30, -34, 40, 16, 9, (0.44, 0.52, 0.40))
    def over(c, cam):
        for (gt, gy, gy2) in _L['gr']: X.grenade(c, cam, (Xr + 4, gy), (22, gy2), (t - gt) / 0.55)
    fr, _ = E.scene(cam, F, red, np.zeros(N, bool), t, np.r_[~dao, np.ones(ne, bool)], props=props, under=under, over=over)
    fl = sum(0.3 * math.exp(-(t - gt - 0.55) / 0.06) for (gt, *_) in _L['gr'] if t >= gt + 0.55)
    return fr + np.float32([1, 0.9, 0.7]) * fl


# ---------------------------------------------------------------- 夜渡赤水：浮桥上悄悄过河
_C = {}


def crossing(lt, night=True, back=False):
    E.set_looks(RED, ZY)
    if not _C: r = np.random.default_rng(9); _C['p'] = np.float32([(-(i * 1.25), (j - 0.5) * 1.1 + r.uniform(-0.12, 0.12)) for i in range(70) for j in range(2)]); _C['ph'] = r.uniform(0, 6, 140).astype(np.float32)
    t = lt; pos = _C['p'] + np.float32([18 + 3.0 * t, 0]); z = np.where(np.abs(pos[:, 0]) < 9.5, 0.3, 0.0)
    F, red, N = mk([(pos, 0.0, 0, t * 7 + _C['ph'], 3.0, dict(z=z))])
    cam = E.make_cam(1 + 0.6 * t, 0, 33 - 1.2 * t, 27, 128 + 2 * t)
    RV = [(3 * math.sin(y / 14), y) for y in range(-70, 71, 10)]
    def under(c, cam): X.river(c, cam, RV, 17, t, (0.36, 0.46, 0.50), night); X.bridge(c, cam, (-9.5, 0), (9.5, 0), 3.0)
    fr, _ = E.scene(cam, F, red, np.zeros(N, bool), t, np.zeros(N, bool), night=night, under=under)
    return fr


# ---------------------------------------------------------------- 金沙江：几条木船来回摆渡
_J = {}


def jinsha(lt):
    E.set_looks(RED, ZY)
    if not _J: r = np.random.default_rng(11); _J['q'] = block(6, 12, 1.4, -34, 0, 0, 0.3, 12); _J['ph'] = r.uniform(0, 6, 400).astype(np.float32); _J['done'] = block(5, 8, 1.4, 31, 4, 0, 0.3, 13)
    t = lt; boats = []; bp = []
    for k in range(6):
        u = ((t * 0.13 + k / 6) % 1.0); bx = -19 + 38 * u; by = -24 + k * 9.5 + 3 * math.sin(u * 3.1); boats.append((bx, by))
        bp += [(bx + (i - 1.5) * 1.25, by + (j - 0.5) * 0.9) for i in range(4) for j in range(2)]
    bp = np.float32(bp); nb = len(bp)
    F, red, N = mk([(_J['q'], 0.0, 0, _J['ph'][:len(_J['q'])], 0.0, {}), (bp, 0.0, 0, 0.0, 0.0, dict(crouch=True, z=0.35)), (_J['done'], 0.0, 0, t * 8 + _J['ph'][:40], 3.0, {})])
    red[:] = True
    cam = E.make_cam(0, 0, 60 - 2.5 * t, 34, 118 + 2 * t)
    RV = [(4 * math.sin(y / 20), y) for y in range(-110, 111, 10)]
    def under(c, cam):
        X.river(c, cam, RV, 46, t, (0.62, 0.52, 0.34))
        for (bx, by) in boats: X.boat(c, cam, bx, by, 0.0, 7.5, 2.8)
    fr, _ = E.scene(cam, F, red, np.zeros(N, bool), t, np.zeros(N, bool), under=under)
    return fr


if __name__ == '__main__':
    from PIL import Image
    fn = globals()[sys.argv[1]]; ims = [Image.fromarray((np.clip(fn(float(x)), 0, 1) * 255).astype(np.uint8)) for x in sys.argv[2:]]
    sh = Image.new('RGB', (1920, 540 * ((len(ims) + 1) // 2)))
    for i, im in enumerate(ims): sh.paste(im.resize((960, 540)), ((i % 2) * 960, (i // 2) * 540))
    sh.save(f'b_{sys.argv[1]}.jpg', quality=85)
