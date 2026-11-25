"""夜间突围：不走模拟，直接用公式摆每个兵 —— 楔形骑兵凿穿围阵，领头的主角放大、带翎子和披风，镜头在侧前方跟着他。
演示 mapwar.eggfield.scene 的用法。"""
import math, numpy as np
from mapwar.eggfield import scene, make_cam

_S = {}


def _setup():
    r = np.random.default_rng(5); cav = []
    for row in range(13):
        n = min(row + 1, 9)
        for j in range(n): cav.append((-3.2 * row + r.uniform(-0.4, 0.4) * (row > 0), (j - (n - 1) / 2) * 2.3 + r.uniform(-0.3, 0.3) * (row > 0)))
    cav = np.float32(cav)
    xs = [x for x in np.arange(-5, 60, 1.35) if (x + 5) % 15 < 12]; ys = [y for y in np.arange(-34, 34.1, 1.35) if (y + 34) % 12 < 9.5]
    han = np.float32([(x, y) for x in xs for y in ys]) + r.uniform(-0.12, 0.12, (len(xs) * len(ys), 2)).astype(np.float32)
    n = len(han)
    _S.update(cav=cav, han=han, rnd=r.random((n, 4)).astype(np.float32), cph=r.uniform(0, 6, len(cav)).astype(np.float32), torch=np.r_[np.zeros(len(cav), bool), r.random(n) < 0.035])


def breakout_frame(lt):
    if not _S: _setup()
    cav, han, rnd = _S['cav'], _S['han'], _S['rnd']; t = 2.9 + lt * 0.95; X = -45 + 13 * t; nc, nh = len(cav), len(han)
    cp = cav + np.float32([X, 0]); cp[:, 1] += 0.25 * np.sin(t * 3 + _S['cph'])
    x0, y0 = han[:, 0], han[:, 1]; ay = np.abs(y0); sg = np.where(y0 >= 0, 1.0, -1.0)
    inside = ay < 10.5; Xh = x0 + 2 * np.maximum(0, ay - 1.2); th = np.where(inside, (Xh + 45) / 13, (x0 - 7 + 45) / 13 + 0.15 + rnd[:, 0] * 0.6 + (ay - 10.5) * 0.035)
    u = t - th; hit = u > 0; fall = inside & (rnd[:, 1] < 0.3)
    hp = han.copy(); z = np.zeros(nh, np.float32); stt = np.zeros(nh, np.int32); face = np.arctan2(-y0, X - x0).astype(np.float32); spd = np.zeros(nh, np.float32)
    uc = np.clip(u, 0, None)
    m = hit & fall; uu = np.minimum(uc, 0.7)
    hp[m, 0] += 5 * uu[m] * (0.5 + rnd[m, 2]); hp[m, 1] += sg[m] * (3 + 8 * rnd[m, 3]) * uu[m]; z[m] = np.maximum(0, 6 * uu[m] - 8.6 * uu[m] ** 2); stt[m] = np.where(uc[m] > 0.7, 3, 2)
    m = hit & inside & ~fall; e = np.clip(uc / 0.45, 0, 1); e = e * e * (3 - 2 * e)
    tgt = sg * (11.5 + 3 * rnd[:, 2]); hp[m, 1] = (y0 + (tgt - y0) * e + sg * 4.5 * np.maximum(0, uc - 0.45))[m]; stt[m] = 2; face[m] = (sg * math.pi / 2)[m]; spd[m] = 5
    m = hit & ~inside; hp[m, 1] += (sg * 4.5 * uc)[m]; hp[m, 0] += (1.5 * uc * (rnd[:, 3] - 0.3))[m]; stt[m] = 2; face[m] = (sg * math.pi / 2)[m]; spd[m] = 5
    F = dict(pos=np.r_[cp, hp].astype(np.float32), z=np.r_[np.zeros(nc, np.float32), z], face=np.r_[np.zeros(nc, np.float32), face], state=np.r_[np.zeros(nc, np.int32), stt],
             fall=np.r_[np.zeros(nc, np.float32), rnd[:, 0] * 6.28], phase=np.r_[t * 12 + _S['cph'], uc * 11 + rnd[:, 1] * 6], spd=np.r_[np.full(nc, 13, np.float32), spd])
    chu = np.r_[np.ones(nc, bool), np.zeros(nh, bool)]; k = lt / 2.6
    e = math.exp(-lt / 0.2)
    cam = make_cam(X + 1.5 - 2 * k + 0.6 * e * math.sin(lt * 60), 1.0 + 0.5 * e * math.sin(lt * 47), 17 + 5 * k, 27 + 5 * k, 128 - 8 * k)
    fr, hp_ = scene(cam, F, chu, chu.copy(), t, np.r_[np.ones(nc, bool), np.hypot(hp[:, 0] - X, hp[:, 1]) < 8], hero=0, night=True, torches=_S['torch'])
    return fr
