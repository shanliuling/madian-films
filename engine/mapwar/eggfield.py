"""斜视角「蛋蛋兵」战场：逐兵模拟（队列槽位、接战、骑兵冲击、溃逃）+ 3D 镜头（俯视 ↔ 斜视连续过渡）+ 大头小人渲染。
远处的兵只画色块，近处才画脸和表情（人多不乱）；兵器亮色加粗；镜头放在冲锋方的侧前方，看得到脸；主角可以放大突出。
  S = simulate()                      # 约 5 秒；结果可以自己 pickle 缓存
  img, cam, ts = render(ft, S, keys)  # keys：镜头关键帧 (仿真秒, x, y, 距离, 俯仰, 朝向, 跟随权重)
  frame, hero_xy = scene(cam, F, ...) # 不走模拟、自己摆每个兵（见 examples/chuhan_q/breakout.py）
坐标：x 向东，y 向北，单位米。state: 0 列阵 1 接战 2 溃逃 3 倒地。
"""
import math
import numpy as np, cairo, cv2
from scipy.spatial import cKDTree
from PIL import Image
from .util import fbm, ease, cl


W, H, FPS = 960, 540, 30
FOC = 1.25 * H
LOD = 3.0
DUR = 14.0
rng = np.random.default_rng(3)

# ================================================================ 单位
SIDE = {'H': ((0.74, 0.12, 0.10), (0.30, 0.04, 0.03)), 'C': ((0.12, 0.24, 0.48), (0.04, 0.07, 0.16))}
KINDS = {'spear': 0, 'shield': 1, 'bow': 2, 'cav': 3}


def kf(keys, t):
    ts = [k[0] for k in keys]
    if t <= ts[0]: return keys[0][1:]
    if t >= ts[-1]: return keys[-1][1:]
    i = np.searchsorted(ts, t) - 1; u = (t - ts[i]) / (ts[i + 1] - ts[i]); u = u * u * (3 - 2 * u)
    a, b = np.array(keys[i][1:], float), np.array(keys[i + 1][1:], float)
    d = b - a
    if len(d) >= 3: d[2] = (d[2] + 180) % 360 - 180           # 朝向走最短弧
    return tuple(a + d * u)


class Unit:
    def __init__(self, side, kind, ranks, files, sp, keys, shape='block', rout=None, flee=(1, 0), vuln=0.25, charge=None, name=None):
        self.side, self.kind, self.keys, self.rout, self.flee, self.vuln, self.charge, self.name = side, kind, keys, rout, np.float32(flee), vuln, charge, name
        sl = []
        for r in range(ranks):
            nf = (r + 1) if shape == 'wedge' else files
            for c in range(nf): sl.append((-r * sp, (c - (nf - 1) / 2) * sp))
        self.slots = np.array(sl, np.float32) + rng.normal(0, sp * 0.06, (len(sl), 2))

    def frame(self, t):
        x, y, hd = kf(self.keys, t)[:3]; a = math.radians(hd); ca, sa = math.cos(a), math.sin(a)
        R = np.array([[ca, -sa], [sa, ca]], np.float32); return np.float32([x, y]), a, self.slots @ R.T


# 坐标：x 向东，y 向北，单位米。汉军守东边，楚军从西边攻。
TI = 5.7  # 撞击（仿真秒，由模拟得出）
UNITS = [
    Unit('H', 'spear', 8, 18, 1.0, [(0, 17.5, -61.0, 187)], vuln=0.12, rout=TI + 0.90, flee=(1, -0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 18.5, -35.1, 169)], vuln=0.12, rout=TI + 0.45, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 16.9, -8.5, 190)], vuln=0.12, rout=TI + 0.15, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 14.5, 11.8, 181)], vuln=0.12, rout=TI + 0.15, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 14.3, 33.1, 175)], vuln=0.12, rout=TI + 0.45, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 14.0, 64.1, 187)], vuln=0.12, rout=TI + 0.90, flee=(1, 0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 28.8, -55.1, 168)], vuln=0.12, rout=TI + 1.30, flee=(1, -0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 29.3, -33.3, 192)], vuln=0.12, rout=TI + 0.77, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 33.8, -7.7, 181)], vuln=0.12, rout=TI + 0.47, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 33.6, 15.6, 185)], vuln=0.12, rout=TI + 0.47, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 29.8, 46.1, 177)], vuln=0.12, rout=TI + 0.77, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 28.4, 65.2, 175)], vuln=0.12, rout=TI + 1.30, flee=(1, 0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 47.1, -66.0, 176)], vuln=0.12, rout=TI + 1.70, flee=(1, -0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 45.9, -34.5, 176)], vuln=0.12, rout=TI + 1.09, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 43.3, -10.4, 191)], vuln=0.12, rout=TI + 0.79, flee=(1, -0.90), name='汉军'),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 48.1, 14.0, 168)], vuln=0.12, rout=TI + 0.79, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 46.5, 35.9, 168)], vuln=0.12, rout=TI + 1.09, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 48.7, 59.4, 173)], vuln=0.12, rout=TI + 1.70, flee=(1, 0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 63.7, -52.6, 176)], vuln=0.12, rout=TI + 1.41, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 62.7, -30.8, 171)], vuln=0.12, rout=TI + 1.41, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 63.2, -3.6, 169)], vuln=0.12, rout=TI + 1.11, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 60.0, 14.7, 183)], vuln=0.12, rout=TI + 1.11, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 63.5, 41.7, 181)], vuln=0.12, rout=TI + 1.41, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 59.1, 66.5, 170)], vuln=0.12, rout=TI + 2.10, flee=(1, 0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 79.0, -60.5, 172)], vuln=0.12, rout=TI + 2.50, flee=(1, -0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 76.2, -33.1, 178)], vuln=0.12, rout=TI + 1.73, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 78.0, -11.2, 179)], vuln=0.12, rout=TI + 1.43, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 78.5, 8.4, 169)], vuln=0.12, rout=TI + 1.43, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 73.8, 39.7, 186)], vuln=0.12, rout=TI + 1.73, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 77.7, 63.0, 171)], vuln=0.12, rout=TI + 2.50, flee=(1, 0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 93.1, -58.8, 175)], vuln=0.12, rout=TI + 2.90, flee=(1, -0.50), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 93.1, -27.0, 191)], vuln=0.12, rout=TI + 2.05, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 92.4, -6.1, 179)], vuln=0.12, rout=TI + 1.75, flee=(1, -0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 88.9, 17.2, 177)], vuln=0.12, rout=TI + 1.75, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 91.8, 46.7, 180)], vuln=0.12, rout=TI + 2.05, flee=(1, 0.90), name=None),
    Unit('H', 'spear', 8, 18, 1.0, [(0, 89.6, 64.7, 187)], vuln=0.12, rout=TI + 2.90, flee=(1, 0.50), name=None),
    Unit('C', 'cav', 11, 0, 2.4, [(0, -60, -37, 0), (1.0, -60, -37, 0), (5.5, 6, -37, 0), (7.5, 40, -37, 5), (10, 80, -40, 0), (14, 125, -40, 0)], shape='wedge', vuln=0.0, charge=3.4),
    Unit('C', 'cav', 11, 0, 2.4, [(0, -60, 37, 0), (1.0, -60, 37, 0), (5.5, 6, 37, 0), (7.5, 40, 37, -5), (10, 80, 40, 0), (14, 125, 40, 0)], shape='wedge', vuln=0.0, charge=3.4),
    Unit('C', 'cav', 16, 0, 2.4, [(0, -58, 0, 0), (4.6, 12, 0, 0), (7, 42, 0, 0), (10, 82, 4, 0), (14, 125, 4, 0)], shape='wedge', vuln=0.0, charge=3.6, name='楚骑'),
]

# ================================================================ 模拟
def simulate(units=None, track=None):
    """units：Unit 列表（不给就用下面的示例布阵：一支楔形骑兵撞进多块步兵方阵）；track：镜头跟随的那一队的下标。"""
    units = UNITS if units is None else list(units)
    N = sum(len(u.slots) for u in units); uid = np.concatenate([np.full(len(u.slots), i) for i, u in enumerate(units)])
    side = np.array([units[i].side == 'C' for i in uid]); kind = np.array([KINDS[units[i].kind] for i in uid]); cav = kind == 3
    slot_i = np.concatenate([np.arange(len(u.slots)) for u in units])
    pos = np.zeros((N, 2), np.float32)
    for i, u in enumerate(units):
        c, a, off = u.frame(0); pos[uid == i] = c + off
    vel = np.zeros_like(pos); face = np.array([units[i].frame(0)[1] for i in uid], np.float32)
    state = np.zeros(N, np.int8)              # 0 列阵 1 接战 2 溃逃 3 死
    die_t = np.full(N, 1e9, np.float32); fall_dir = rng.uniform(0, 2 * math.pi, N).astype(np.float32)
    phase = rng.uniform(0, 2 * math.pi, N).astype(np.float32); jit = rng.normal(0, 1, (N, 2)).astype(np.float32)
    vmax = np.where(cav, 15.0, 8.6).astype(np.float32) * rng.uniform(0.9, 1.1, N).astype(np.float32)
    acc = np.where(cav, 14.0, 9.0).astype(np.float32)
    knock = np.zeros_like(pos); frames = []; dust = []; dt = 1 / FPS
    z = np.zeros(N, np.float32); vz = np.zeros(N, np.float32); imp = None
    for f in range(int(DUR * FPS) + 2):
        t = f * dt; alive = state < 3
        tgt = pos.copy(); spd_cap = vmax.copy(); want_face = face.copy()
        for i, u in enumerate(units):
            m = (uid == i) & alive; c, a, off = u.frame(t); tg = c + off[slot_i[m]]
            tgt[m] = tg; want_face[m] = a
            if u.rout is not None and t >= u.rout:
                st = m & (state < 2); state[st] = 2
        # 接战：找最近的敌人
        eng = np.zeros(N, bool); near_d = np.full(N, 99.0, np.float32); near_v = np.zeros_like(pos)
        for s in (False, True):
            me = alive & (side == s); en = alive & (side != s) & (state != 2)
            if en.sum() == 0 or me.sum() == 0: continue
            tr = cKDTree(pos[en]); d, j = tr.query(pos[me], k=1); ep = pos[en][j]; idx = np.flatnonzero(me)
            near_d[idx] = d; near_v[idx] = ep - pos[idx]
        rd = np.full(N, 99.0, np.float32); rv = np.zeros_like(pos)
        for s in (False, True):
            me = alive & (side == s); en = alive & (side != s) & (state == 2)
            if en.sum() == 0 or me.sum() == 0: continue
            d, j = cKDTree(pos[en]).query(pos[me], k=1); idx = np.flatnonzero(me); rd[idx] = d; rv[idx] = pos[en][j] - pos[idx]
        dirn = near_v / np.maximum(near_d[:, None], 1e-3)
        chg = np.array([units[i].charge is not None and t >= units[i].charge for i in uid])
        hunt = alive & (state < 2) & chg & (near_d < (22 * np.where(cav, 1.0, 0.5)))
        tgt[hunt] = pos[hunt] + dirn[hunt] * np.where(cav[hunt, None], 20.0, np.minimum(near_d[hunt, None], 8.0))
        chase = alive & (state < 2) & chg & (near_d > 14) & (rd < np.where(cav, 40, 16))
        tgt[chase] = pos[chase] + rv[chase] / np.maximum(rd[chase, None], 1e-3) * np.where(cav[chase, None], 20.0, np.minimum(rd[chase, None], 10.0))
        e = alive & (state < 2) & ~cav & (near_d < 1.7); eng[e] = True; state[e] = 1
        tgt[e] = pos[e] + near_v[e] - dirn[e] * 0.95 + jit[e] * 0.15 * math.sin(t * 9)
        spd_cap[e] = 1.6; want_face[e] = np.arctan2(dirn[e, 1], dirn[e, 0])
        state[(state == 1) & ~e] = 0
        # 溃逃：背向敌人跑
        r = alive & (state == 2)
        if r.any():
            fl = np.array([units[i].flee for i in uid[r]]); fl = fl / np.linalg.norm(fl, axis=1, keepdims=True)
            away = fl + jit[r] * 0.35 - dirn[r] * (near_d[r, None] < 6) * 0.8
            tgt[r] = pos[r] + away * 20; spd_cap[r] = np.where(cav[r], 14, 7.6) * (0.85 + 0.3 * np.abs(jit[r, 0]) % 0.3)
        # 追击：溃逃开始后，骑兵追最近的溃兵
        # 伤亡
        vul = np.array([units[i].vuln for i in uid], np.float32)
        kill = e & (rng.random(N) < vul * dt * 4.0)
        # 骑兵冲击：高速骑兵撞到步兵
        sp_now = np.linalg.norm(vel, axis=1)
        hc = alive & cav & (sp_now > 4)
        if hc.any():
            inf = alive & ~cav & (side != True)
            tr = cKDTree(pos[inf]); pairs = tr.query_ball_point(pos[hc], 1.6); ii = np.flatnonzero(inf)
            for k, lst in zip(np.flatnonzero(hc), pairs):
                if not lst: continue
                js = ii[lst]; dv = pos[js] - pos[k]; dn = np.linalg.norm(dv, axis=1, keepdims=True) + 1e-3
                knock[js] += dv / dn * 15.0 + vel[k] * 0.55; vel[k] *= 0.95
                up = js[z[js] < 0.01]; vz[up] = rng.uniform(5.0, 11.0, len(up)) * min(1.3, sp_now[k] / 11)
                if imp is None: imp = (t, float(pos[k, 0]), float(pos[k, 1]), float(math.atan2(vel[k, 1], vel[k, 0])))
                kill |= np.isin(np.arange(N), js[rng.random(len(js)) < 0.3])
        # 追杀溃兵
        rk = np.zeros(N, bool)
        for s in (False, True):
            ch = alive & (side == s) & (state < 2); vic = alive & (side != s) & (state == 2)
            if ch.any() and vic.any():
                d, j = cKDTree(pos[ch]).query(pos[vic], k=1); vi = np.flatnonzero(vic); rk[vi[(d < 1.8) & (rng.random(len(vi)) < 0.06)]] = True
        kill |= rk
        kill &= alive
        state[kill] = 3; die_t[kill] = t
        fall_dir[kill] = np.arctan2(-dirn[kill, 1] + knock[kill, 1] * 0.2, -dirn[kill, 0] + knock[kill, 0] * 0.2)
        alive = state < 3
        # 转向 + 加速度限制
        des = tgt - pos; dl = np.linalg.norm(des, axis=1, keepdims=True)
        des = des / np.maximum(dl, 1e-3) * np.minimum(dl * 2.2, spd_cap[:, None])
        dv = des - vel; dvl = np.linalg.norm(dv, axis=1, keepdims=True); dv = dv / np.maximum(dvl, 1e-6) * np.minimum(dvl, acc[:, None] * dt)
        vel = np.where(alive[:, None], vel + dv + knock * dt * 6, 0); knock *= 0.82
        # 互相避让
        al = np.flatnonzero(alive); tr = cKDTree(pos[al]); pr = tr.query_pairs(0.85, output_type='ndarray')
        if len(pr):
            a_, b_ = al[pr[:, 0]], al[pr[:, 1]]; dd = pos[a_] - pos[b_]; q = np.maximum(np.linalg.norm(dd, axis=1, keepdims=True), 0.05)
            rad = np.where(cav[a_] & cav[b_], 1.7, np.where(cav[a_] | cav[b_], 0.9, 0.85))[:, None]; push = np.clip((rad - q) / q, 0, 1) * 0.5 * dd
            np.add.at(pos, a_, push * 0.5); np.add.at(pos, b_, -push * 0.5)
        pos = np.where(alive[:, None] | (z[:, None] > 0), pos + np.where(z[:, None] > 0, knock * dt * 0.6, 0) + vel * dt * alive[:, None], pos)
        z = np.maximum(0, z + vz * dt); vz = np.where(z > 0, vz - 9.8 * dt, 0)
        sp_now = np.linalg.norm(vel, axis=1)
        mv = sp_now > 0.5; vf = np.arctan2(vel[:, 1], vel[:, 0])
        tf = np.where(mv & (state != 1), vf, want_face)
        dfa = (tf - face + np.pi) % (2 * np.pi) - np.pi; face = face + dfa * np.where(cav, 0.25, 0.3)
        phase += sp_now * dt * np.where(cav, 1.6, 3.4)
        # 扬尘
        if f % 2 == 0:
            src = np.flatnonzero(alive & (sp_now > 7) & cav)
            for k in src[rng.random(len(src)) < 0.55]: dust.append((pos[k, 0], pos[k, 1], t, rng.uniform(1.5, 3.0)))
        frames.append(dict(pos=pos.copy(), z=z.copy(), vel=vel.copy(), face=face.copy(), state=state.copy(), die_t=die_t.copy(), fall=fall_dir.copy(), phase=phase.copy(), spd=sp_now.copy(), eng=eng.copy()))
    flag = np.zeros(N, bool)
    for i, u in enumerate(units):
        idx = np.flatnonzero(uid == i)
        if u.kind == 'cav': flag[idx[9::30]] = True
        else:
            nf = max(1, int(round(np.ptp(u.slots[:, 1]) / 1.0)) + 1); rk1 = idx[nf:2 * nf] if len(idx) > 2 * nf else idx
            flag[rk1[[len(rk1) // 4, 3 * len(rk1) // 4]]] = True
    return dict(frames=frames, uid=uid, side=side, kind=kind, dust=dust, imp=imp, flag=flag, track=len(units) - 1 if track is None else track)


# ================================================================ 箭雨


CAM = [  # t, 目标x, 目标y, 距离, 俯仰(90=正俯视), 朝向, 跟随骑兵的权重
    (0, -8, -6, 92, 89.5, 90, 0), (4.0, -2, -6, 92, 89.5, 90, 0), (6.4, -30, -60, 42, 34, 50, 1), (8.4, 0, 0, 36, 30, 60, 1), (9.6, 0, 0, 34, 30, 70, 1),
    (11.6, 20, -22, 44, 34, 80, 0.4), (13.6, 24, -10, 60, 45, 88, 0), (16.0, 32, 0, 92, 80, 90, 0), (17.4, 36, 0, 100, 89.5, 90, 0), (21, 42, 2, 108, 89.5, 90, 0)]
TRACK = len(UNITS) - 1


class Cam:
    def __init__(self, t, S=None):
        tx, ty, D, p, y, w = kf(CAM, t)[:6]; p, y = math.radians(p), math.radians(y)
        if S is not None and w > 0.01:
            cx, cy = cav_state(S, t)[0] + (6, 4)
            tx, ty = tx * (1 - w) + cx * w, ty * (1 - w) + cy * w
        g = np.array([math.cos(y), math.sin(y), 0.0]); z = np.array([0, 0, 1.0]); b = -math.cos(p) * g + math.sin(p) * z
        self.C = np.array([tx, ty, 0.0]) + D * b; self.v = -b; self.r = np.cross(g, z); self.r /= np.linalg.norm(self.r); self.u = np.cross(self.r, self.v)
        self.pitch = p; self.tilt = cl((math.radians(89) - p) / math.radians(50))

    def proj(self, P):
        d = P - self.C; X = d @ self.r; Y = d @ self.u; Z = np.maximum(d @ self.v, 0.1)
        return np.stack([W / 2 + FOC * X / Z, H / 2 - FOC * Y / Z], -1), FOC / Z

    def ground_quad(self):
        """屏幕四角对应的地面点（射线与 z=0 相交）。"""
        out = []
        for sx, sy in ((0, 0), (W, 0), (W, H), (0, H)):
            d = self.v + self.r * (sx - W / 2) / FOC - self.u * (sy - H / 2) / FOC
            s = -self.C[2] / min(d[2], -1e-3); out.append(self.C[:2] + d[:2] * min(s, 900))
        return np.float32(out)


# ================================================================ 地面
TEXR = 0.25; TEXN = 1600; TEXO = -TEXN * TEXR / 2


def ground_tex():
    n = fbm(TEXN, TEXN, 220, 5, 7); n2 = fbm(TEXN, TEXN, 26, 3, 8); fib = cv2.GaussianBlur(rng.random((TEXN, TEXN)).astype(np.float32), (0, 0), sigmaX=1.2, sigmaY=1.2)
    base = np.float32([0.90, 0.85, 0.74]) * (0.86 + 0.22 * n[..., None]) * (1 + 0.25 * (fib[..., None] - 0.5))
    base *= 1 - 0.10 * np.clip((n2[..., None] - 0.5) * 3, 0, 1) * np.float32([0.6, 0.4, 0.5])           # 淡墨草色
    hl = fbm(TEXN, TEXN, 420, 3, 17); base *= (1 - 0.16 * np.clip((hl[..., None] - 0.45) * 2.5, 0, 1) * np.float32([0.7, 0.55, 0.6]))   # 起伏的墨色坡
    g = np.zeros((TEXN, TEXN), np.float32)
    for i in range(5000):                                                                               # 草点
        x, y = rng.integers(0, TEXN, 2); cv2.line(g, (int(x), int(y)), (int(x + rng.normal(0, 2)), int(y - rng.uniform(2, 5))), 1.0, 1)
    base *= 1 - 0.25 * cv2.GaussianBlur(g, (0, 0), 0.6)[..., None] * np.float32([0.7, 0.6, 0.65])
    return np.clip(base, 0, 1).astype(np.float32)


GT = None


RIDGE = None


def ridge(ang, layer):
    global RIDGE
    if RIDGE is None:
        r = np.random.default_rng(12); x = np.linspace(0, 1, 4096); acc = []
        for L in range(2):
            v = np.zeros_like(x)
            for o, amp in ((4, 1.0), (9, 0.5), (19, 0.25), (41, 0.12), (90, 0.06)):
                ph = r.uniform(0, 6.28, 3); v += amp * (np.sin(x * 6.283 * o + ph[0]) * 0.6 + np.sin(x * 6.283 * o * 1.7 + ph[1]) * 0.4)
            acc.append((v - v.min()) / (v.max() - v.min()))
        RIDGE = acc
    k = ((ang / (2 * math.pi)) % 1.0) * 4095; return RIDGE[layer][k.astype(int)]


def ground(cam):
    global GT
    if GT is None: GT = ground_tex()
    g = np.cross(np.array([0, 0, 1.0]), cam.r); g[2] = 0; g /= np.linalg.norm(g) + 1e-9
    base = cam.C[:2] + g[:2] * max(3.0, cam.C[2] * 0.2); side = cam.r[:2]
    gp = np.float32([base + side * -20, base + side * 20, base + g[:2] * 140 + side * 60, base + g[:2] * 140 - side * 60])
    sp_, _ = cam.proj(np.c_[gp, np.zeros(4)])
    Hm = cv2.getPerspectiveTransform(np.float32((gp - TEXO) / TEXR), np.float32(sp_))
    img = cv2.warpPerspective(GT, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    far = cam.C[:2] + g[:2] * 6000; yh = float(cam.proj(np.array([[far[0], far[1], 0.0]]))[0][0, 1])     # 地平线
    ys = np.arange(H, dtype=np.float32)[:, None, None]
    if yh > -400:
        dist = np.clip((ys - yh) / max(40.0, H * 0.9), 0, 1)                                                 # 越近地平线越雾
        hz = (1 - dist) ** 2.2 * 0.85; img = img * (1 - hz) + np.float32([0.92, 0.90, 0.84]) * hz
    if yh > 0:
        sky = np.float32([0.95, 0.93, 0.88]) * (0.92 + 0.08 * np.clip(ys / max(1, yh), 0, 1)); m = (ys < yh + 2)
        img = np.where(m, sky, img)
        xs = np.arange(W); ang = math.atan2(g[1], g[0]) + np.arctan((xs - W / 2) / FOC)
        for L, (amp, col, lift) in enumerate(((0.10, (0.74, 0.74, 0.72), 0.0), (0.065, (0.58, 0.59, 0.57), -0.01))):
            hgt = (ridge(ang, L) * amp + 0.02 + lift) * H; top = (yh - hgt).astype(int)
            mask = (np.arange(H)[:, None] >= top[None, :]) & (np.arange(H)[:, None] <= yh + 2)
            img = np.where(mask[..., None], img * 0.0 + np.float32(col), img)
    return img




def make_cam(tx, ty, D, pdeg, ydeg):
    c = Cam.__new__(Cam); p, y = math.radians(pdeg), math.radians(ydeg)
    g = np.array([math.cos(y), math.sin(y), 0.0]); zz = np.array([0, 0, 1.0]); b = -math.cos(p) * g + math.sin(p) * zz
    c.C = np.array([tx, ty, 0.0]) + D * b; c.v = -b; c.r = np.cross(g, zz); c.r /= np.linalg.norm(c.r); c.u = np.cross(c.r, c.v)
    c.pitch = p; c.tilt = cl((math.radians(89) - p) / math.radians(50)); return c


SLOW, RAMP, RATE = 1.6, 0.7, 0.3          # 撞击后：慢放时长（秒）、回到常速的过渡时长、慢放倍率


def sim_t(ft, S):
    if S['imp'] is None: return ft
    T = S['imp'][0]
    if ft < T: return ft
    u = ft - T
    if u < SLOW: return T + RATE * u
    if u < SLOW + RAMP: k = (u - SLOW) / RAMP; return T + RATE * SLOW + (RATE + (1 - RATE) * k / 2) * (u - SLOW)
    return T + RATE * SLOW + (RATE + 1) / 2 * RAMP + (u - SLOW - RAMP)


def film_len(S):
    if S['imp'] is None: return (len(S['frames']) - 1) / FPS
    T = S['imp'][0]; return T + SLOW + RAMP + (21 - (T + RATE * SLOW + (RATE + 1) / 2 * RAMP)) - 0.6


def hand(ft, a=1.0, seed=0):
    return a * (math.sin(ft * 1.7 + seed) * 0.6 + math.sin(ft * 3.1 + 2 * seed) * 0.3 + math.sin(ft * 7.3 + seed) * 0.1)


def cav_state(S, ts):
    fi = min(len(S['frames']) - 1, int(round(ts * FPS))); F = S['frames'][fi]; group = S['uid'] == S.get('track', TRACK)
    m = group & (F['state'] < 3)
    if not np.any(m): m = group if np.any(group) else np.ones_like(group)
    c = F['pos'][m].mean(0); v = F['vel'][m].mean(0); return c, math.atan2(v[1], v[0])


def impact_fx(c, cam, S, ts, ring_only=False):
    if S['imp'] is None: return
    T, ix, iy, ih = S['imp']; a = ts - T
    if a < 0 or a > 2.5: return
    r = np.random.default_rng(9)
    if ring_only and a < 1.4:                                                       # 冲击波：地面一圈尘环
        R = 2 + 22 * (a / 1.4) ** 0.6; th = np.linspace(0, 2 * math.pi, 48)
        pts, _ = cam.proj(np.c_[ix + R * np.cos(th), iy + R * np.sin(th), np.full(48, 0.2)]); _, s = cam.proj(np.array([[ix, iy, 0]]))
        c.set_source_rgba(0.93, 0.88, 0.76, 0.55 * (1 - a / 1.4)); c.set_line_width(max(1, 1.6 * s[0] * (1 - a / 1.4))); c.move_to(*pts[0])
        for q in pts[1:]: c.line_to(*q)
        c.close_path(); c.stroke()
    if ring_only: return
    n = 40; ang = r.uniform(0, 2 * math.pi, n); sp = r.uniform(4, 13, n); up = r.uniform(2, 8, n); sz = r.uniform(0.6, 1.8, n)
    x = ix + np.cos(ang) * sp * a; y = iy + np.sin(ang) * sp * a; zz = np.maximum(0, up * a - 4.9 * a * a) + 0.3
    pts, s = cam.proj(np.c_[x, y, zz])
    for k in range(n):                                                # 尘团
        al = 0.09 * max(0, 1 - a / 2.0); c.set_source_rgba(0.86, 0.80, 0.68, al); c.arc(pts[k, 0], pts[k, 1], sz[k] * (1 + a * 1.5) * s[k], 0, 2 * math.pi); c.fill()
    m = 28; ang = r.uniform(0, 2 * math.pi, m); sp = r.uniform(5, 15, m); up = r.uniform(4, 10, m)
    x = ix + np.cos(ang) * sp * a; y = iy + np.sin(ang) * sp * a; zz = np.maximum(0.05, up * a - 4.9 * a * a)
    pts, s = cam.proj(np.c_[x, y, zz])
    for k in range(m):                                                # 土块
        c.set_source_rgba(0.22, 0.17, 0.12, 0.9 * max(0, 1 - a / 2.0)); c.arc(pts[k, 0], pts[k, 1], max(0.7, 0.06 * s[k]), 0, 2 * math.pi); c.fill()




# ================================================================ 蛋蛋兵渲染
TAU = 2 * math.pi; OL = (0.10, 0.08, 0.08); SKIN = (0.97, 0.85, 0.71)
K = 2; EW, EH = W * K, H * K          # 蛋蛋兵按 1920×1080 画，地面按 960×540 画再放大
CHU_B, HAN_B = (0.13, 0.17, 0.30), (0.78, 0.13, 0.10)
CHU_H, HAN_H = (0.10, 0.10, 0.13), (0.60, 0.61, 0.64)
GOLD = (1.0, 0.80, 0.22); WOOD = (0.95, 0.80, 0.52); STEEL = (0.92, 0.95, 1.0); TASSEL = (0.95, 0.12, 0.08)
# 两方的长相。键 True = 模拟里 side 'C' 的一方（默认：楚骑），False = 'H' 的一方（默认：汉军步兵）。换题材时用 set_looks() 整体替换。
#   body 衣服  head 帽/盔色  square 方头  band 帽圈色  plume 'tall'|'ball'|None  chest 胸前白圆  fierce 怒眉
#   hat 'helmet'(盔，默认)|'bajiao'(八角帽+红星)|'junmao'(大檐帽)|'strawhat'(草帽)   weapon 'spear'|'ji'|'rifle'   shaft 杆/枪托色
LOOKS = {True: dict(body=CHU_B, head=CHU_H, square=True, band=GOLD, plume='tall', chest=False, fierce=True, hat='helmet', weapon='ji', shaft=GOLD),
         False: dict(body=HAN_B, head=HAN_H, square=False, band=(0.75, 0.12, 0.08), plume='ball', chest=True, fierce=False, hat='helmet', weapon='spear', shaft=WOOD)}


def set_looks(a=None, b=None):
    """a：side 'C' 那一方的长相（覆盖默认），b：side 'H' 那一方。只写要改的键。"""
    if a: LOOKS[True] = dict(LOOKS[True], **a)
    if b: LOOKS[False] = dict(LOOKS[False], **b)
CAM = [  # 仿真时间：t, x, y, 距离, 俯仰, 朝向, 跟随骑兵
    (0, 14, 0, 165, 89.5, 90, 0), (1.3, 12, 0, 150, 89.5, 90, 0),
    (3.0, -8, -4, 48, 34, 150, 1), (4.6, 0, 0, 36, 28, 145, 1), (TI - 0.2, 0, 0, 32, 25, 140, 1),
    (TI + 0.6, 0, 0, 58, 33, 130, 0.8), (TI + 1.8, 14, 0, 85, 44, 118, 0.5), (TI + 3.2, 40, 0, 130, 72, 100, 0.2), (TI + 4.4, 50, 0, 175, 89.5, 90, 0), (14, 62, 0, 185, 89.5, 90, 0)]


def shot_cam(ft, S, keys=None):
    ts = sim_t(ft, S); T = S['imp'][0] if S['imp'] else math.inf
    tx, ty, D, p, y, w = kf(keys or CAM, ts)[:6]
    if w > 0.01:
        c, h = cav_state(S, ts); tx, ty = tx * (1 - w) + (c[0] + 4) * w, ty * (1 - w) + c[1] * w
    e = math.exp(-(ft - T) / 0.22) if ft >= T else 0.0
    D *= 1 - 0.10 * e; p += 2.5 * e * math.sin((ft - T) * 55) if e else 0
    tx += hand(ts, 0.3); ty += hand(ts, 0.3, 1)
    return make_cam(tx, ty, D, min(89.5, p), y), ts


def rr(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2); c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2); c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()


def fs(c, col, lw): c.set_source_rgb(*col); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(lw); c.stroke()


def tube(c, p, q, w, col, lw, cap=cairo.LINE_CAP_ROUND):
    c.set_line_cap(cap); c.move_to(*p); c.line_to(*q); c.set_source_rgb(*OL); c.set_line_width(w + 2 * lw); c.stroke()
    c.move_to(*p); c.line_to(*q); c.set_source_rgb(*col); c.set_line_width(w); c.stroke()


def weapon(c, b, t, s, chu, lod, firing=0.0, kind=None):
    Lk = LOOKS[chu]; w = max(1.6, 0.11 * s)
    dx, dy = t[0] - b[0], t[1] - b[1]; L = math.hypot(dx, dy) + 1e-6; ux, uy = dx / L, dy / L; nx, ny = -uy, ux
    if kind == 'dao':                                                          # 大刀：短柄 + 宽刀身 + 红绸
        m = (b[0] + dx * 0.3, b[1] + dy * 0.3); tube(c, b, m, w * 1.1, (0.5, 0.3, 0.14), max(0.7, 0.03 * s))
        bw = max(2.0, 0.2 * s); e = (b[0] + dx * 0.95, b[1] + dy * 0.95)
        c.move_to(m[0] - nx * bw * 0.25, m[1] - ny * bw * 0.25); c.line_to(e[0] - nx * bw * 0.25, e[1] - ny * bw * 0.25); c.line_to(t[0] + nx * bw * 0.3, t[1] + ny * bw * 0.3)
        c.line_to(e[0] + nx * bw * 1.0, e[1] + ny * bw * 1.0); c.line_to(m[0] + nx * bw * 0.6, m[1] + ny * bw * 0.6); c.close_path(); fs(c, STEEL, max(0.6, 0.03 * s))
        c.move_to(*b); c.curve_to(b[0] - ux * 0.3 * s + nx * 0.3 * s, b[1] - uy * 0.3 * s + ny * 0.3 * s, b[0] - ux * 0.5 * s, b[1] - uy * 0.5 * s + 0.2 * s, b[0] - ux * 0.75 * s + nx * 0.2 * s, b[1] - uy * 0.75 * s + 0.35 * s)
        c.set_source_rgb(*TASSEL); c.set_line_width(max(1.2, 0.1 * s)); c.stroke(); return
    if Lk['weapon'] == 'rifle':                                                # 步枪：木托 + 黑枪管 + 刺刀；firing>0 时枪口火光
        m = (b[0] + dx * 0.45, b[1] + dy * 0.45)
        tube(c, b, m, w * 1.5, Lk.get('shaft', (0.62, 0.38, 0.18)), max(0.7, 0.03 * s)); tube(c, m, t, w * 0.8, (0.2, 0.2, 0.22), max(0.7, 0.03 * s))
        hl = max(2.5, 0.28 * s); hw = max(1.0, 0.07 * s)
        c.move_to(t[0] + ux * hl, t[1] + uy * hl); c.line_to(t[0] + nx * hw, t[1] + ny * hw); c.line_to(t[0] - nx * hw, t[1] - ny * hw); c.close_path(); fs(c, STEEL, max(0.5, 0.02 * s))
        if firing > 0:
            fx_, fy_ = t[0] + ux * hl * 1.2, t[1] + uy * hl * 1.2; r0 = (0.5 + 0.5 * firing) * 0.55 * s
            pts = [(fx_ + math.cos(a) * r0 * (1.0 if k % 2 == 0 else 0.4), fy_ + math.sin(a) * r0 * (1.0 if k % 2 == 0 else 0.4)) for k, a in enumerate(np.linspace(0, TAU, 13)[:-1])]
            c.move_to(*pts[0]); [c.line_to(*p_) for p_ in pts[1:]]; c.close_path(); c.set_source_rgba(1, 0.85, 0.3, firing); c.fill()
            c.arc(fx_, fy_, r0 * 0.35, 0, TAU); c.set_source_rgba(1, 1, 0.9, firing); c.fill()
        return
    tube(c, b, t, w, Lk.get('shaft', WOOD), max(0.7, 0.03 * s))
    hl = max(3.0, 0.38 * s); hw = max(1.6, 0.13 * s)
    c.move_to(t[0] + ux * hl, t[1] + uy * hl); c.line_to(t[0] + nx * hw, t[1] + ny * hw); c.line_to(t[0] - nx * hw, t[1] - ny * hw); c.close_path()
    fs(c, STEEL, max(0.6, 0.025 * s))
    if Lk['weapon'] == 'ji' and lod > 1:                                      # 戟的月牙
        c.arc(t[0] - ux * 0.1 * s + nx * 0.22 * s, t[1] - uy * 0.1 * s + ny * 0.22 * s, 0.17 * s, 0, TAU); fs(c, STEEL, max(0.6, 0.025 * s))
    c.arc(t[0] - ux * 0.12 * s, t[1] - uy * 0.12 * s, max(1.3, 0.12 * s), 0, TAU); c.set_source_rgb(*TASSEL); c.fill()


def egg(c, x, y, s, chu, fr, fa, st, ph, spd, lod, cav, ang, tm):
    """x,y：脚底（骑兵为鞍点）屏幕坐标；s：像素/米。"""
    Lk = LOOKS[chu]; body = Lk['body']; HC = Lk['head']; sq_ = Lk['square']; R = 0.42 * s; lw = max(0.6, 0.045 * s)
    if lod == 0:                                                              # 远：两笔色块
        c.rectangle(x - 0.26 * s, y - (1.05 if not cav else 0.6) * s, 0.52 * s, 0.6 * s); c.set_source_rgb(*body); c.fill()
        c.arc(x, y - (1.4 if not cav else 0.95) * s, R, 0, TAU); c.set_source_rgb(*HC); c.fill(); return
    sw = math.sin(ph) * 0.2 * s * min(1, spd / 3)
    if not cav:
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_source_rgb(*OL); c.set_line_width(0.17 * s)
        for k in (-1, 1): c.move_to(x + k * 0.13 * s, y - 0.5 * s); c.line_to(x + k * 0.13 * s + k * sw, y); c.stroke()
    by = y - (0.42 * s if not cav else 0.0)
    c.save(); c.translate(x, by); c.rotate(ang)
    rr(c, -0.29 * s, -0.66 * s, 0.58 * s, 0.68 * s, 0.14 * s); fs(c, body, lw)
    c.rectangle(-0.29 * s, -0.22 * s, 0.58 * s, 0.09 * s); c.set_source_rgb(*Lk.get('belt', GOLD)); c.fill()
    if Lk['chest'] and lod > 1: c.arc(0, -0.42 * s, 0.13 * s, 0, TAU); c.set_source_rgb(0.98, 0.92, 0.8); c.fill()          # 汉兵胸前白圆
    hx, hy = fr * 0.05 * s, -0.66 * s - R * 0.85
    hp_ = lambda: rr(c, hx - R, hy - R * 0.95, 2 * R, 1.9 * R, 0.24 * R) if sq_ else c.arc(hx, hy, R, 0, TAU)
    hp_(); fs(c, SKIN, lw)
    back = fa > 0.35; hat = Lk.get('hat', 'helmet')
    c.save(); hp_(); c.clip(); c.rectangle(hx - 1.2 * R, hy - 1.2 * R, 2.4 * R, R * ((0.78 if hat == 'helmet' else 0.62) if not back else (2.6 if hat == 'helmet' else 1.55))); c.set_source_rgb(*(HC if hat == 'helmet' else Lk.get('hair', (0.08, 0.07, 0.07)))); c.fill(); c.restore()
    hp_(); c.set_source_rgb(*OL); c.set_line_width(lw); c.stroke()
    if hat == 'helmet':
        if Lk.get('band'): c.rectangle(hx - R * 1.02, hy - R * 0.48, 2.04 * R, 0.16 * R); c.set_source_rgb(*Lk['band']); c.fill()
        if Lk.get('plume') == 'tall': c.move_to(hx, hy - R * 0.95); c.line_to(hx - 0.1 * R, hy - R * 1.45); c.set_source_rgb(*TASSEL); c.set_line_width(0.22 * R); c.stroke()
        elif Lk.get('plume') == 'ball': c.arc(hx, hy - R * 1.02, 0.15 * R, 0, TAU); c.set_source_rgb(*TASSEL); c.fill()
    elif hat == 'bajiao':                                                      # 八角帽 + 红星
        c.move_to(hx - 1.05 * R, hy - 0.3 * R); c.line_to(hx - 1.12 * R, hy - 0.95 * R); c.line_to(hx - 0.5 * R, hy - 1.22 * R); c.line_to(hx + 0.5 * R, hy - 1.22 * R)
        c.line_to(hx + 1.12 * R, hy - 0.95 * R); c.line_to(hx + 1.05 * R, hy - 0.3 * R); c.close_path(); fs(c, HC, lw)
        if not back:
            c.move_to(hx + (fr * 0.6 - 0.75) * R, hy - 0.32 * R); c.line_to(hx + (fr * 0.6 + 0.75) * R, hy - 0.32 * R); c.line_to(hx + (fr * 0.6 + 0.6) * R, hy - 0.12 * R); c.line_to(hx + (fr * 0.6 - 0.6) * R, hy - 0.12 * R); c.close_path(); fs(c, tuple(v * 0.7 for v in HC), lw * 0.7)
            if lod > 1 and Lk.get('star', True):
                sx_, sy_, r_ = hx + fr * 0.35 * R, hy - 0.72 * R, 0.24 * R
                for k in range(10): rr_ = r_ if k % 2 == 0 else r_ * 0.42; (c.move_to if k == 0 else c.line_to)(sx_ + rr_ * math.sin(k * math.pi / 5), sy_ - rr_ * math.cos(k * math.pi / 5))
                c.close_path(); c.set_source_rgb(0.9, 0.1, 0.08); c.fill()
            elif Lk.get('star', True): c.arc(hx + fr * 0.35 * R, hy - 0.72 * R, 0.16 * R, 0, TAU); c.set_source_rgb(0.9, 0.1, 0.08); c.fill()
    elif hat == 'junmao':
        c.rectangle(hx - 0.95 * R, hy - 1.05 * R, 1.9 * R, 0.6 * R); fs(c, HC, lw)
        c.save(); c.translate(hx, hy - 1.05 * R); c.scale(1.3, 0.38); c.arc(0, 0, R, 0, TAU); c.restore(); fs(c, tuple(min(1, v * 1.15) for v in HC), lw)
        c.rectangle(hx - 0.95 * R, hy - 0.62 * R, 1.9 * R, 0.16 * R); c.set_source_rgb(*(Lk.get('band') or (0.12, 0.1, 0.1))); c.fill()
    elif hat == 'strawhat':
        c.save(); c.translate(hx, hy - 0.5 * R); c.scale(1.0, 0.3); c.arc(0, 0, 1.55 * R, 0, TAU); c.restore(); fs(c, (0.84, 0.72, 0.46), lw)
        c.save(); c.translate(hx, hy - 0.7 * R); c.scale(1.0, 0.7); c.arc(0, 0, 0.8 * R, math.pi, TAU); c.restore(); c.close_path(); fs(c, (0.88, 0.76, 0.5), lw)
    if not back and lod > 1:                                                   # 脸
        ex = hx + fr * 0.28 * R; ey = hy + 0.12 * R
        for k in (-1, 1):
            if st == 2: c.arc(ex + k * 0.3 * R, ey, 0.18 * R, 0, TAU); c.set_source_rgb(1, 1, 1); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(0.04 * R); c.stroke(); c.arc(ex + k * 0.3 * R, ey, 0.07 * R, 0, TAU); c.fill()
            else: c.arc(ex + k * 0.3 * R, ey, 0.1 * R, 0, TAU); c.set_source_rgb(*OL); c.fill()
        c.set_source_rgb(*OL); c.set_line_width(0.09 * R); c.set_line_cap(cairo.LINE_CAP_ROUND)
        if Lk['fierce'] or st == 2:
            for k in (-1, 1):
                if Lk['fierce'] and st != 2: c.move_to(ex + k * 0.5 * R, ey - 0.34 * R); c.line_to(ex + k * 0.14 * R, ey - 0.18 * R)
                else: c.move_to(ex + k * 0.5 * R, ey - 0.2 * R); c.line_to(ex + k * 0.14 * R, ey - 0.34 * R)
                c.stroke()
        if st == 2 or (Lk['fierce'] and spd > 4):
            c.save(); c.translate(ex, ey + 0.45 * R); c.scale(1, 1.2 if st == 2 else 0.8); c.arc(0, 0, 0.14 * R, 0, TAU); c.restore(); c.set_source_rgb(0.45, 0.05, 0.05); c.fill()
        else: c.move_to(ex - 0.13 * R, ey + 0.42 * R); c.line_to(ex + 0.13 * R, ey + 0.42 * R); c.stroke()
        if st == 2 and lod > 1:
            x_, y_ = hx - 1.15 * R, hy - 0.4 * R + 0.1 * R * math.sin(tm * 9 + ph)
            c.move_to(x_, y_ - 0.25 * R); c.curve_to(x_ + 0.16 * R, y_, x_ + 0.13 * R, y_ + 0.16 * R, x_, y_ + 0.16 * R); c.curve_to(x_ - 0.13 * R, y_ + 0.16 * R, x_ - 0.16 * R, y_, x_, y_ - 0.25 * R)
            fs(c, (0.65, 0.85, 1.0), lw * 0.6)
    c.restore()


def horse(c, cam, p, f, s, ph, spd, i, lod, k=1.0, colr=None):
    col = colr or ((0.13, 0.12, 0.14), (0.38, 0.24, 0.14), (0.24, 0.17, 0.12), (0.85, 0.82, 0.76))[3 if i % 9 == 0 else i % 3]; s = s * k
    fx, fy = math.cos(f), math.sin(f); g = math.sin(ph); bob = abs(g) * 0.12
    side = 1 if (np.array([-fy, fx, 0]) @ cam.v) < 0 else -1                   # 朝镜头的一侧
    def Wp(a, b, h): a, b, h = a * k, b * k, h * k; return [p[0] + fx * a - fy * b, p[1] + fy * a + fx * b, h]
    L = [Wp(-0.72, 0, 1.2 + bob), Wp(0.62, 0, 1.25 + bob), Wp(1.0, 0, 1.95 + bob), Wp(1.5, 0, 1.75 + bob), Wp(-0.85, 0, 1.4 + bob), Wp(-1.45 - 0.2 * g, 0, 0.75 + 0.2 * spd / 10),
         Wp(0.55, 0.18, 1.0), Wp(0.55 + 0.55 * g, 0.18, 0.05), Wp(-0.55, 0.18, 1.0), Wp(-0.55 - 0.55 * g, 0.18, 0.05),
         Wp(0.55, -0.18, 1.0), Wp(0.55 - 0.55 * g, -0.18, 0.05), Wp(-0.55, -0.18, 1.0), Wp(-0.55 + 0.55 * g, -0.18, 0.05),
         Wp(-0.05, 0, 1.6 + bob), Wp(-0.32, 0, 1.55 + bob), Wp(0.25, 0, 1.55 + bob), Wp(1.32, 0.12 * side, 1.92 + bob), Wp(0.9, 0, 2.12 + bob), Wp(0.4, 0, 1.72 + bob)]
    P, _ = cam.proj(np.array(L)); P = P * K; lw = max(0.6, 0.04 * s)
    near = (6, 8) if side > 0 else (10, 12); far = (10, 12) if side > 0 else (6, 8)
    for a in far: tube(c, P[a], P[a + 1], 0.17 * s, tuple(v * 0.7 for v in col), lw)
    tube(c, P[4], P[5], 0.2 * s, (0.06, 0.05, 0.06), lw)                         # 尾
    tube(c, P[0], P[1], 0.78 * s, col, lw)                                       # 身
    if lod > 0:
        c.move_to(*P[0]); c.line_to(*P[1]); c.set_source_rgba(1, 1, 1, 0.18); c.set_line_width(0.3 * s); c.stroke()
    for a in near: tube(c, P[a], P[a + 1], 0.18 * s, col, lw)
    if lod > 0:
        for a in near: c.arc(*P[a + 1], 0.1 * s, 0, TAU); c.set_source_rgb(0.95, 0.95, 0.92); c.fill()          # 白蹄
    tube(c, P[19], P[2], 0.42 * s, col, lw); tube(c, P[2], P[3], 0.34 * s, col, lw)                              # 颈、头
    tube(c, P[19], P[18], 0.12 * s, (0.06, 0.05, 0.06), 0, )                                                     # 鬃
    tube(c, P[15], P[16], 0.86 * s, (0.78, 0.10, 0.08), lw, cairo.LINE_CAP_BUTT)                                  # 鞍鞯
    if lod > 0:
        c.move_to(*P[15]); c.line_to(*P[16]); c.set_source_rgb(*GOLD); c.set_line_width(0.12 * s); c.set_dash([0.15 * s, 0.1 * s]); c.stroke(); c.set_dash([])
    if lod > 1:
        c.arc(*P[17], 0.07 * s, 0, TAU); c.set_source_rgb(*OL); c.fill(); c.arc(P[17][0] - 0.02 * s, P[17][1] - 0.025 * s, 0.025 * s, 0, TAU); c.set_source_rgb(1, 1, 1); c.fill()
    return P[14]


def render(ft, S, keys=None):
    """模拟结果 S 在影片时刻 ft 的一帧（撞击后自动慢放）。返回 (PIL 图 1920×1080, 镜头, 仿真时刻)。"""
    cam, ts = shot_cam(ft, S, keys); T = S['imp'][0] if S['imp'] else math.inf; bg = ground(cam)
    F = S['frames'][min(len(S['frames']) - 1, int(round(ts * 30)))]; pos = F['pos']; N = len(pos)
    P0 = np.c_[pos, F['z']]; scr, sc = cam.proj(P0); scr = scr * K; sc = sc * K
    d = (P0 - cam.C) @ cam.v; order = np.argsort(-d)
    fwd = np.c_[np.cos(F['face']), np.sin(F['face']), np.zeros(N)]; fr = fwd @ cam.r; fa = fwd @ cam.v
    side = np.c_[-fwd[:, 1], fwd[:, 0], np.zeros(N)]
    cav_m = S['kind'] == 3; st = F['state']; chu_m = S['side'].astype(bool)
    # 武器 3D 端点
    eng = (F['eng'] > 0) if 'eng' in F else np.zeros(N, bool)
    lower = cav_m | (ts > TI - 1.2)
    base = P0 + fwd * 0.3 + side * 0.32 + np.c_[0, 0, 0][0] + np.where(cav_m, 2.0, 0.95)[:, None] * np.array([0, 0, 1.0])
    tipL = P0 + fwd * np.where(cav_m, 2.7, 2.3)[:, None] + side * 0.32 + np.where(cav_m, 2.5, 1.35)[:, None] * np.array([0, 0, 1.0])
    tipU = P0 + fwd * 0.45 + side * 0.36 + np.array([0, 0, 3.1])
    tip = np.where(lower[:, None], tipL, tipU)
    if F.get('crouch') is not None: dz = np.where(F['crouch'], -0.42, 0.0)[:, None] * Z1; base = base + dz; tip = tip + dz
    B2, _ = cam.proj(base); T2, _ = cam.proj(tip); B2 *= K; T2 *= K
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, EW, EH); c = cairo.Context(surf)
    c.save(); c.scale(K, K); impact_fx(c, cam, S, ts, ring_only=True); c.restore()
    sh = max(0.3, math.sin(cam.pitch))
    for i in order:                                                            # 影子先画
        x, y = scr[i]; s = sc[i]
        if not (-60 < x < EW + 60 and -60 < y < EH + 120) or st[i] == 3: continue
        c.save(); c.translate(x, y); c.scale(1, sh); c.arc(0, 0, (1.1 if cav_m[i] else 0.42) * s, 0, TAU); c.restore(); c.set_source_rgba(0, 0, 0, 0.15); c.fill()
    for i in order:
        x, y = scr[i]; s = sc[i]
        if not (-60 < x < EW + 60 and -60 < y < EH + 150): continue
        chu = chu_m[i]; cav = cav_m[i]; px = s
        lod = 0 if px < 6 else 1 if px < 16 else 2
        if st[i] == 3:                                                         # 倒地：躺平小人 + 掉落的矛
            c.save(); c.translate(x, y); c.rotate(F['fall'][i]); c.scale(1, sh * 0.8 + 0.2)
            rr(c, -0.55 * s, -0.22 * s, 0.7 * s, 0.44 * s, 0.12 * s); c.set_source_rgb(*LOOKS[chu]['body']); c.fill()
            c.arc(0.45 * s, 0, 0.36 * s, 0, TAU); c.set_source_rgb(*LOOKS[chu]['head']); c.fill()
            if lod > 0: c.move_to(-0.9 * s, 0.35 * s); c.line_to(0.9 * s, 0.6 * s); c.set_source_rgb(*WOOD); c.set_line_width(max(1, 0.08 * s)); c.stroke()
            c.restore(); continue
        if cav: x, y = horse(c, cam, pos[i], F['face'][i], s, F['phase'][i], F['spd'][i], i, lod)
        draw_w = (st[i] != 2) and lod > 0
        if draw_w and fa[i] > 0: weapon(c, B2[i], T2[i], s, chu, lod, F['fire'][i] if 'fire' in F else 0)          # 背对镜头：武器在身前→先画
        if cav: c.save(); c.scale(1, 1)
        egg(c, x, y, s, chu, fr[i], fa[i], st[i], F['phase'][i], F['spd'][i], lod, cav, 0.15 * fr[i] * min(1, F['spd'][i] / 6), ts)
        if cav: c.restore()
        if draw_w and fa[i] <= 0: weapon(c, B2[i], T2[i], s, chu, lod, F['fire'][i] if 'fire' in F else 0)
        if lod == 0 and st[i] != 2 and px > 2.5:                               # 远处也留一根亮色武器线
            c.move_to(*B2[i]); c.line_to(*T2[i]); c.set_source_rgb(*LOOKS[chu].get('shaft', WOOD)); c.set_line_width(max(1.0, 0.1 * s)); c.stroke()
    c.save(); c.scale(K, K); impact_fx(c, cam, S, ts); c.restore()
    a = np.ndarray((EH, EW, 4), np.uint8, surf.get_data()).astype(np.float32) / 255
    Bg = np.asarray(Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).resize((EW, EH), Image.BICUBIC)).astype(np.float32) / 255
    fr_ = Bg * (1 - a[..., 3:4]) + a[..., [2, 1, 0]]
    yy, xx = np.mgrid[0:EH, 0:EW].astype(np.float32); vr = np.clip(((xx - EW / 2) / (EW / 2)) ** 2 * 0.5 + ((yy - EH / 2) / (EH / 2)) ** 2 * 0.55, 0, 1)[..., None]
    fl = 0.5 * math.exp(-(ft - T) / 0.09) if ft >= T else 0
    fr_ = fr_ * (1 - 0.3 * vr) + np.float32([1.0, 0.95, 0.85]) * fl
    return Image.fromarray((np.clip(fr_, 0, 1) * 255).astype(np.uint8)), cam, ts


Z1 = np.array([0, 0, 1.0])


def scene(cam, F, chu_m, cav_m, ts, lower, hero=-1, night=False, torches=None, props=None, under=None, over=None, tint=None):
    """自己摆的一帧（不走模拟）：F 给每个兵的 pos/z/face/state/fall/phase/spd（可选 fire：0..1 枪口火光）；可选 dao（举大刀的人）、crouch（蹲着的人，只露上半身）；props=[(x, y, fn(c, sx, sy, s))] 按远近和兵一起排序的道具（沙包、爆炸…）；under(c, cam)/over(c, cam) 画在兵的下面/上面（河、弹道、飞机，用 px(cam, 点) 取屏幕坐标）；tint 整体乘色；hero 那一个放大并带翎子披风；night 入夜；torches 举火把的人。返回 (HxWx3 float, 主角屏幕位置)。"""
    pos = F['pos']; N = len(pos); st = F['state']
    P0 = np.c_[pos, F['z']]; scr, sc = cam.proj(P0); scr = scr * K; sc = sc * K
    d = (P0 - cam.C) @ cam.v; order = np.argsort(-d)
    fwd = np.c_[np.cos(F['face']), np.sin(F['face']), np.zeros(N)]; fr = fwd @ cam.r; fa = fwd @ cam.v
    side = np.c_[-fwd[:, 1], fwd[:, 0], np.zeros(N)]; hk = np.ones(N)
    if hero >= 0: hk[hero] = 1.5
    base = P0 + (fwd * 0.3 + side * 0.32) * hk[:, None] + (np.where(cav_m, 2.0, 0.95) * hk)[:, None] * Z1
    tipL = P0 + fwd * (np.where(cav_m, 2.7, 2.3) * hk)[:, None] + side * 0.32 * hk[:, None] + (np.where(cav_m, 2.5, 1.35) * hk)[:, None] * Z1
    tipU = P0 + fwd * 0.45 + side * 0.36 + np.array([0, 0, 3.1])
    tip = np.where(lower[:, None], tipL, tipU)
    B2, _ = cam.proj(base); T2, _ = cam.proj(tip); B2 *= K; T2 *= K
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, EW, EH); c = cairo.Context(surf)
    sh = max(0.3, math.sin(cam.pitch)); dao_m = F.get('dao'); cr_m = F.get('crouch')
    if under: under(c, cam)
    if props:                                                                  # 道具和兵一起按远近排
        PP = np.float32([[p_[0], p_[1], 0] for p_ in props]); pscr, psc = cam.proj(PP); pscr = pscr * K; psc = psc * K; pd = (PP - cam.C) @ cam.v
        order = sorted(list(order) + [-(j + 1) for j in range(len(props))], key=lambda q: -(d[q] if q >= 0 else pd[-q - 1]))
    for i in order:
        if i < 0: continue
        x, y = scr[i]; s = sc[i]
        if not (-60 < x < EW + 60 and -60 < y < EH + 120) or st[i] == 3: continue
        c.save(); c.translate(x, y); c.scale(1, sh); c.arc(0, 0, (1.1 if cav_m[i] else 0.42) * s * hk[i], 0, TAU); c.restore(); c.set_source_rgba(0, 0, 0, 0.18); c.fill()
    hp = None
    for i in order:
        if i < 0: j = -i - 1; props[j][2](c, pscr[j][0], pscr[j][1], psc[j]); continue
        x, y = scr[i]; s = sc[i]
        if not (-80 < x < EW + 80 and -80 < y < EH + 200): continue
        chu = chu_m[i]; cav = cav_m[i]; lod = 0 if s < 6 else 1 if s < 16 else 2
        wk = 'dao' if dao_m is not None and dao_m[i] else None; cro = cr_m is not None and cr_m[i]
        if st[i] == 3:
            c.save(); c.translate(x, y); c.rotate(F['fall'][i]); c.scale(1, sh * 0.8 + 0.2)
            rr(c, -0.55 * s, -0.22 * s, 0.7 * s, 0.44 * s, 0.12 * s); c.set_source_rgb(*LOOKS[chu]['body']); c.fill()
            c.arc(0.45 * s, 0, 0.36 * s, 0, TAU); c.set_source_rgb(*LOOKS[chu]['head']); c.fill()
            if lod > 0: c.move_to(-0.9 * s, 0.35 * s); c.line_to(0.9 * s, 0.6 * s); c.set_source_rgb(*WOOD); c.set_line_width(max(1, 0.08 * s)); c.stroke()
            c.restore(); continue
        he = i == hero; k = hk[i]
        if cav: x, y = horse(c, cam, pos[i], F['face'][i], s, F['phase'][i], F['spd'][i], i, 2 if he else lod, k, (0.10, 0.10, 0.13) if he else None)
        s2 = s * k
        if he:                                                                 # 披风
            wv = math.sin(ts * 9); bx = -1 if fr[i] >= 0 else 1
            c.move_to(x - 0.25 * s2, y - 0.62 * s2); c.curve_to(x + bx * 0.9 * s2, y - 0.9 * s2 + 0.15 * s2 * wv, x + bx * 1.6 * s2, y - 0.5 * s2, x + bx * 2.1 * s2, y - 0.2 * s2 + 0.2 * s2 * wv)
            c.curve_to(x + bx * 1.4 * s2, y + 0.1 * s2, x + bx * 0.8 * s2, y + 0.05 * s2, x + 0.25 * s2, y - 0.1 * s2); c.close_path(); fs(c, (0.78, 0.08, 0.06), max(1, 0.04 * s2))
        dw = st[i] != 2 and lod > 0
        if dw and fa[i] > 0: weapon(c, B2[i], T2[i], s2, chu, 2 if he else lod, F['fire'][i] if 'fire' in F else 0, wk)
        egg(c, x, y, s2, chu, fr[i], fa[i], st[i], F['phase'][i], F['spd'][i], 2 if he else lod, cav or cro, 0.15 * fr[i] * min(1, F['spd'][i] / 6), ts)
        if he:                                                                 # 雉鸡翎
            R = 0.42 * s2; hx, hy = x + fr[i] * 0.05 * s2, y - 0.66 * s2 - R * 1.8; bx = -1 if fr[i] >= 0 else 1
            for q, L in ((0, 4.6), (1, 4.0)):
                wv = 0.3 * R * math.sin(ts * 8 + q)
                for wd, col, dash in ((0.34 * R, (0.1, 0.08, 0.08), None), (0.24 * R, (0.95, 0.88, 0.7), None), (0.24 * R, (0.4, 0.26, 0.14), [0.3 * R, 0.35 * R])):
                    c.move_to(hx + (q - 0.5) * 0.5 * R, hy); c.curve_to(hx + (q - 0.5) * R, hy - L * 0.6 * R, hx + bx * L * 0.5 * R, hy - L * 0.75 * R + wv, hx + bx * L * 0.85 * R, hy - L * (0.35 - 0.1 * q) * R + wv)
                    c.set_source_rgb(*col); c.set_line_width(wd); c.set_dash(dash or []); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
            c.set_dash([]); c.arc(hx, hy + 0.05 * R, 0.2 * R, 0, TAU); c.set_source_rgb(0.9, 0.1, 0.08); c.fill(); hp = (x, y - s2)
        if dw and fa[i] <= 0: weapon(c, B2[i], T2[i], s2, chu, 2 if he else lod, F['fire'][i] if 'fire' in F else 0, wk)
        if lod == 0 and st[i] != 2 and s > 2.5:
            c.move_to(*B2[i]); c.line_to(*T2[i]); c.set_source_rgb(*LOOKS[chu].get('shaft', WOOD)); c.set_line_width(max(1.0, 0.1 * s)); c.stroke()
        if torches is not None and torches[i] and st[i] < 2 and lod > 0:
            tx, ty = x + 0.5 * s, y - 2.3 * s
            c.move_to(x + 0.4 * s, y - 1.0 * s); c.line_to(tx, ty); c.set_source_rgb(0.3, 0.2, 0.1); c.set_line_width(0.08 * s); c.stroke()
            for rr_, al in ((1.0, 0.10), (0.6, 0.25), (0.28, 1.0)): c.arc(tx, ty - 0.1 * s, rr_ * s * (1 + 0.15 * math.sin(ts * 20 + i)), 0, TAU); c.set_source_rgba(1.0, 0.75 if rr_ < 1 else 0.5, 0.25, al); c.fill()
    if over: over(c, cam)
    a = np.ndarray((EH, EW, 4), np.uint8, surf.get_data()).astype(np.float32) / 255
    Bg = np.asarray(Image.fromarray((np.clip(ground(cam), 0, 1) * 255).astype(np.uint8)).resize((EW, EH), Image.BICUBIC)).astype(np.float32) / 255
    if tint is not None: Bg = Bg * np.float32(tint)
    ch = a[..., [2, 1, 0]]
    if night: Bg = Bg * np.float32([0.26, 0.31, 0.52]); ch = ch * np.float32([0.86, 0.88, 1.0])
    out = Bg * (1 - a[..., 3:4]) + ch
    yy, xx = np.mgrid[0:EH, 0:EW].astype(np.float32)
    if night and hp is not None: out = out + np.exp(-((xx - hp[0]) ** 2 + (yy - hp[1]) ** 2) / (2 * 330 ** 2))[..., None] * np.float32([1.0, 0.6, 0.25]) * 0.22
    vr = np.clip(((xx - EW / 2) / (EW / 2)) ** 2 * 0.5 + ((yy - EH / 2) / (EH / 2)) ** 2 * 0.55, 0, 1)[..., None]
    return out * (1 - (0.5 if night else 0.3) * vr), hp


def px(cam, pts):
    """世界坐标（N×3 或单个点）→ 1920×1080 画布上的屏幕坐标和每米像素。"""
    P = np.atleast_2d(np.float32(pts)); a, b = cam.proj(P); return a * K, b * K
