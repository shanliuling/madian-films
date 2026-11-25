"""用 rig.py 画精致 Q 版人物的简便接口：脚底坐标 + 总高 + 常用姿势。"""
import math
from . import qrig as RG, qhorse
PI = math.pi; TAU = 2 * PI
STAND = dict(lean=0.05, hd=0.0, sf=0.5, ef=1.9, sb=-0.25, eb=0.15, hf=0.15, kf=0.02, hb=-0.15, kb=-0.05, w=PI - 0.12, sq=0.0, rot=0.0)
POSES = {
    'stand': {},
    'idle': dict(sf=0.25, ef=0.5, sb=-0.15, eb=0.1, w=1.0),
    'fold': dict(sf=0.25, ef=1.25, sb=-0.1, eb=0.7, w=1.3),
    'cheer': dict(sf=1.7, ef=2.2, sb=-1.7, eb=-2.2, w=2.4, lean=-0.05, hd=-0.12),
    'point': dict(sf=1.6, ef=1.6, sb=-0.2, eb=0.2, w=1.6),
    'kneel': dict(hf=1.45, kf=0.0, hb=0.25, kb=-1.45, lean=0.35, hd=0.25, sf=0.5, ef=0.6, sb=0.3, eb=0.5, w=0.7),
}


def pose(name, t=0.0, **kw):
    P = dict(STAND); P.update(POSES.get(name, {}))
    if name in ('run', 'walk'):
        a, sp = (0.75, 11) if name == 'run' else (0.35, 6); s = math.sin(t * sp)
        P.update(hf=a * s + 0.1, kf=a * s - 0.5 * max(0, -s) * (2 if name == 'run' else 1) + 0.05, hb=-a * s + 0.1, kb=-a * s - 0.5 * max(0, s) * (2 if name == 'run' else 1) + 0.05,
                 sf=-0.8 * a * s + 0.4, ef=-0.8 * a * s + 1.4, sb=0.8 * a * s - 0.2, eb=0.8 * a * s + 0.6, lean=0.25 if name == 'run' else 0.08, bob=abs(s))
    P.update(kw); return P


def Q(c, x, feet, h, spec, face=1, name='stand', t=0.0, **kw):
    """(x, feet) 脚底；h ≈ 总高（不含帽饰）。"""
    S = h / 1.05; P = pose(name, t, **kw); P['x'] = x; P['f'] = face
    drop = 0.15 * S if name == 'kneel' else 0.3 * S
    P['y'] = feet - drop - (0.04 * S * P.pop('bob', 0) if name == 'run' else 0) + kw.get('dy', 0)
    P.pop('dy', None)
    return RG.draw(c, P, S, spec, t), P, S


def rider(c, x, ground, h, spec, face=1, t=0.0, gait='stand', rear=0.0, hcol=(0.16, 0.17, 0.22), sheen=(0.45, 0.5, 0.62), hk=1.3, **kw):
    S = h / 1.05; sx, sy = qhorse.horse(c, x, ground, hk * S, hcol, face, t, gait, rear, sheen=sheen)
    P = pose('stand', t, ride=True, hf=1.35, kf=0.25, flags=False, rot=-rear * 0.2 * face); P.update(kw); P['x'] = sx; P['y'] = sy; P['f'] = face
    RG.draw(c, P, S, spec, t)
