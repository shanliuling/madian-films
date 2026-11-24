"""fight — 试片：三年之约，开打的头几招（小说第 335 章，见 NOVEL.md）。约 9 秒。
    python fight.py            → out/fight_540p.mp4（RES=1080 出 1080p；FPS=30 出 30 帧）
    python fight.py still 3.66 → out/_still.png（看某一秒）
时间轴按系列 BGM 的拍子排：片子从第 96 拍起（96–98 拍音乐正好空两拍：睁眼、喊话），98 拍满编制进来的那一下萧炎冲出去。
    98 冲锋拖尺 · 100 风刃叮当被尺挡掉 · 102 尺砸剑尖、剑被压弯 · 103 青芒弹开、她掠上半空 · 104–106 五道剑形残影
    106 踏地炸响冲天 · 107「风灵分形剑」· 108 半空硬接，青光大盛 · 109 片名"""
import _env, os, sys, math, subprocess, functools, numpy as np, cv2, cairo
from PIL import Image
from stage import Out
from paper import layer, rgba, over, to_pil
from looks import sub
import action as A, fighter as F, yunlan
from action import track, rnd, pulse
RES = int(os.environ.get('RES', 540)); R = Out(RES * 16 // 9, RES); FPS = int(os.environ.get('FPS', 60))
BEAT = 0.59413; B0 = 96; LEAD = 0.10
def bt(b): return LEAD + (b - B0) * BEAT                                                 # 第 b 拍在片子里的秒数
DUR = bt(110.9); GY = yunlan.GY; XH, NH = 330, 305; RL = 0.92; SL = 0.66                 # 身高、尺长、剑长
T_GO, T_X, T_HIT, T_POP, T_STOMP, T_NAME, T_END, T_CARD = bt(98), bt(100), bt(102), bt(103), bt(106), bt(107), bt(108), bt(109)
T_PH = [bt(104 + 0.5 * i) for i in range(5)]                                            # 五道残影各在半拍上
CYAN = (0.25, 1.0, 0.80); WIND = (0.62, 0.98, 1.0); P = F.P

BLADES = [(2.375 + 0.075 * i, T_X + 0.085 * i, 0.30 + 0.24 * i) for i in range(3)]                                                         # 三道风刃：(出剑, 打到尺上, 打在尺的哪一段)
# ---------- 萧炎
_xk = track([(0, P(x=420, lean=20, head=-6, a1=(-42, -18), a2=(34, 78), l1=(46, -10), l2=(-34, -56), w=200, eye=0.0)),
    (0.34, P(x=420, lean=20, head=-6, a1=(-42, -18), a2=(34, 78), l1=(46, -10), l2=(-34, -56), w=200, eye=0.0)), (0.40, P(x=420, lean=20, head=-8, a1=(-42, -18), a2=(34, 78), l1=(46, -10), l2=(-34, -56), w=200, eye=1.15, glint=1.0), 'snap'),
    (0.50, P(x=420, lean=21, head=-8, a1=(-42, -18), a2=(34, 78), l1=(46, -10), l2=(-34, -56), w=200, eye=1.0, glint=0.8, mouth=1)), (1.0, P(x=420, lean=22, head=-8, a1=(-44, -20), a2=(36, 80), l1=(48, -10), l2=(-34, -58), w=200, glint=0.3, mouth=1)),
    (T_GO - 0.04, P(x=404, lean=40, head=-22, a1=(-52, -26), a2=(50, 96), l1=(66, -22), l2=(-22, -76), w=200, glint=0.3, mouth=0.4), 'o'),                # 往下一沉
    (T_GO + 0.10, P(x=520, lean=60, head=-44, a1=(-62, -42), a2=(64, 100), l1=(70, -20), l2=(-60, -40), w=200, mouth=1), 'i'),
    (2.20, P(x=1090, lean=60, head=-44, a1=(-62, -42), a2=(64, 100), l1=(70, -20), l2=(-60, -40), w=200, mouth=1), 'lin'),
    (2.40, P(x=1158, lean=-10, head=4, a1=(52, 112), a2=(40, 100), l1=(58, 34), l2=(-14, -52), w=97, g2=-0.085), 'o'),                                    # 急停，尺提起来挡
    (2.80, P(x=1166, lean=-6, head=2, a1=(52, 112), a2=(40, 100), l1=(54, 30), l2=(-14, -48), w=96, g2=-0.085)),
    (3.00, P(x=1170, lean=4, head=0, a1=(80, 135), a2=(50, 110), l1=(30, 10), l2=(-14, -30), w=92, g2=-0.085)),
    (3.01, P(x=1170, face=-1, lean=-4, head=0, a1=(100, 145), a2=(60, 110), l1=(14, 30), l2=(-30, -10), w=88, g2=-0.085), 'hold'),                        # 转身
    (3.42, P(x=1182, face=-1, lean=-18, head=6, a1=(150, 176), a2=(60, 110), l1=(20, 26), l2=(-34, -20), w=156, g2=-0.085), 'io'),                        # 尺抡到身后
    (T_HIT, P(x=1140, face=-1, lean=34, head=-22, a1=(74, 84), a2=(60, 80), l1=(56, -4), l2=(-40, -52), w=-6, g2=-0.085, mouth=1), 'i'),                   # 横砸
    (T_POP, P(x=1112, face=-1, lean=38, head=-24, a1=(70, 86), a2=(60, 80), l1=(60, -8), l2=(-42, -56), w=-12, g2=-0.085, mouth=0.6), 'o'),               # 往下压
    (T_POP + 0.22, P(x=1330, face=-1, lean=-24, head=14, a1=(150, 170), a2=(-30, -60), l1=(46, 30), l2=(-16, -36), w=120), 'snap'),                       # 被弹开，滑退
    (4.75, P(x=1420, face=-1, lean=-8, head=6, a1=(120, 150), a2=(-20, -30), l1=(40, 22), l2=(-16, -36), w=104), 'o'),
    (5.15, P(x=1424, face=-1, lean=8, head=-30, a1=(46, 92), a2=(-16, 10), l1=(30, 4), l2=(-22, -30), w=-78), 'io'),                                      # 重尺插地，抬头
    (5.90, P(x=1424, face=-1, lean=24, head=-40, a1=(50, 96), a2=(-30, -50), l1=(58, -24), l2=(-34, -78), w=-74, fire=1.0, glint=0.9), 'io'),             # 蓄势
    (T_STOMP, P(x=1424, face=-1, lean=28, head=-42, a1=(50, 96), a2=(-30, -50), l1=(62, -30), l2=(-30, -84), w=-74, fire=1.0, glint=1.0, mouth=1), 'i'),
    (T_STOMP + 0.16, P(x=1380, air=110, face=-1, rot=22, lean=26, head=-40, a1=(-30, -8), a2=(120, 150), l1=(72, -30), l2=(-20, -30), w=215, fire=1.0, glint=1.0, mouth=1), 'snap'),
    (6.62, P(x=1210, air=262, face=-1, rot=24, lean=24, head=-36, a1=(-40, -16), a2=(130, 150), l1=(80, -40), l2=(-30, -60), w=212, fire=1.0, glint=1.0, mouth=1), 'o'),
    (7.08, P(x=1090, air=300, face=-1, rot=-8, lean=-18, head=-10, a1=(156, 170), a2=(140, 150), l1=(50, -50), l2=(-10, -80), w=146, g2=-0.085, fire=1.0, glint=1.0, mouth=1), 'io'),   # 半空里尺举过头
    (T_END, P(x=1056, air=312, face=-1, rot=16, lean=40, head=-26, a1=(72, 82), a2=(60, 80), l1=(74, -30), l2=(-40, -70), w=-24, g2=-0.085, fire=1.0, glint=1.0, mouth=1), 'ii'),         # 砸下去
    (T_END + 0.6, P(x=1066, air=308, face=-1, rot=18, lean=42, head=-26, a1=(70, 84), a2=(60, 80), l1=(74, -30), l2=(-40, -70), w=-28, g2=-0.085, fire=1.0, glint=1.0, mouth=1), 'o')])
_drag = track([(0, 1.0), (2.22, 1.0), (2.34, 0.0, 'o'), (4.9, 0.0), (5.15, 1.0), (T_STOMP, 1.0), (T_STOMP + 0.08, 0.0)])                 # 尺尖贴地的程度（冲锋时拖着，蓄势时插着）
def xy_pose(t):
    p = dict(_xk(t))
    if T_GO + 0.10 < t < 2.20:                                                          # 冲锋：腿跑起来
        ph = (p['x'] - 520) / 150 * math.pi; s, co = math.sin(ph), math.cos(ph); leg = lambda sv, cv: (18 + 62 * sv, 18 + 62 * sv - 20 - 86 * max(0.0, cv)); p['l1'] = leg(s, co); p['l2'] = leg(-s, -co); p['lean'] += 3 * math.sin(2 * ph)
    for (_, tb, _) in BLADES: k = pulse(t, tb, 0.02, 0.07); p['lean'] -= 5 * k; p['x'] += 7 * k; p['w'] += 4 * k                                      # 风刃打在尺上，震一下
    if T_HIT < t < T_POP: k = math.sin(t * 150) * 1.2; p['w'] += k; p['a1'] = (p['a1'][0] + k, p['a1'][1] - k)                               # 角力时发抖
    d = _drag(t)
    if d > 0:
        J = F.kin(p, XH, GY); q = max(-1.0, min(1.0, (GY + 6 - J['h1'][1]) / (RL * XH))); wl = (180 + math.degrees(math.asin(q))) if t < 3 else -math.degrees(math.asin(q)); p['w'] = p['w'] + (wl - p['w']) * d
    return p
@functools.lru_cache(maxsize=4096)
def _JX(t): return F.kin(xy_pose(t), XH, GY)
def JX(t): return _JX(round(t, 4))
def ruler_at(t, s): b, e = F.wpts(JX(t), RL, 0.10); return (b[0] + (e[0] - b[0]) * s, b[1] + (e[1] - b[1]) * s)

# ---------- 纳兰嫣然
_c = ruler_at(T_HIT, 0.60); _th = P(x=0, lean=30, head=-12, a1=(84, 92), a2=(-46, -70), l1=(54, 6), l2=(-46, -58), w=14)
for _ in range(6): _j = F.kin(_th, NH, GY); _t = F.wpts(_j, SL)[1]; _th['w'] += math.degrees(math.atan2(_t[1] - _c[1], SL * NH)); _th['x'] += _c[0] - F.wpts(F.kin(_th, NH, GY), SL)[1][0]     # 让剑尖正好点在尺上
NX, NW = _th['x'], _th['w']; HOV = dict(lean=-6, head=6, l1=(18, -26), l2=(-6, -52), a2=(-40, -62))
_nk = track([(0, P(x=1500, face=-1, lean=3, a1=(58, 80), a2=(-24, -14), l1=(14, 0), l2=(-12, -8), w=10)), (2.14, P(x=1500, face=-1, lean=3, a1=(58, 80), a2=(-24, -14), l1=(14, 0), l2=(-12, -8), w=10)),
    (2.28, P(x=1496, face=-1, lean=10, a1=(120, 150), a2=(-30, -30), l1=(30, -24), l2=(-6, -40), w=120), 'o'),                                             # 脚尖一点
    (2.40, P(x=1440, air=70, face=-1, rot=20, lean=18, head=-10, a1=(60, 70), a2=(-50, -70), l1=(40, -50), l2=(-30, -60), w=-40), 'o'),                    # 横削
    (2.78, P(x=1130, air=112, face=-1, rot=38, lean=14, head=-20, a1=(20, 40), a2=(-60, -80), l1=(20, -30), l2=(-40, -70), w=-150), 'lin'),                # 贴着他飘过去
    (3.10, P(x=NX - 70, air=14, face=-1, rot=8, lean=8, a1=(10, 40), a2=(-40, -40), l1=(30, -20), l2=(-20, -50), w=-170), 'lin'),
    (3.11, P(x=NX - 70, air=14, face=1, rot=0, lean=6, a1=(-10, 40), a2=(30, 60), l1=(26, -20), l2=(-26, -50), w=-10), 'hold'),
    (3.32, P(x=NX - 56, face=1, lean=18, head=-8, a1=(-34, 50), a2=(40, 70), l1=(46, -30), l2=(-30, -66), w=-4), 'o'),                                     # 落地一沉，剑收到腰间
    (T_HIT, dict(_th, face=1), 'i'),                                                                                                                       # 暴刺
    (T_POP, dict(_th, face=1, x=NX - 28, lean=22, a1=(70, 112), l1=(50, 14), l2=(-40, -46), bend=0.26), 'o'),                                              # 剑被压弯
    (T_POP + 0.07, dict(_th, face=1, x=NX - 34, lean=20, a1=(86, 90), bend=0.0, w=NW + 14), 'snap'),
    (4.56, P(x=NX - 96, air=310, face=1, rot=-26, lean=-10, head=8, w=156, a1=(160, 172), a2=(-60, -90), l1=(52, -60), l2=(12, -80)), 'o'),
    (4.95, P(x=NX - 150, air=430, face=1, w=128, a1=(150, 168), **HOV), 'o'),                                                                              # 借力掠上半空
    (T_PH[1] - 0.06, P(x=NX - 160, air=444, face=1, w=128, a1=(150, 168), **HOV)), (T_PH[1], P(x=NX - 160, air=446, face=1, w=96, a1=(140, 150), **HOV), 'snap'),
    (T_PH[2] - 0.06, P(x=NX - 164, air=450, face=1, w=96, a1=(140, 150), **HOV)), (T_PH[2], P(x=NX - 164, air=452, face=1, w=62, a1=(120, 126), **HOV), 'snap'),
    (T_PH[3] - 0.06, P(x=NX - 168, air=456, face=1, w=62, a1=(120, 126), **HOV)), (T_PH[3], P(x=NX - 168, air=458, face=1, w=28, a1=(100, 104), **HOV), 'snap'),
    (T_PH[4] - 0.06, P(x=NX - 172, air=460, face=1, w=28, a1=(100, 104), **HOV)), (T_PH[4], P(x=NX - 172, air=462, face=1, w=-6, a1=(80, 84), **HOV), 'snap'),
    (T_NAME - 0.16, P(x=NX - 174, air=464, face=1, w=100, a1=(150, 170), lean=-12, head=10, l1=(18, -26), l2=(-6, -52), a2=(-40, -62)), 'io'),             # 剑扬起
    (T_NAME, P(x=NX - 180, air=468, face=1, w=-38, a1=(62, 58), lean=20, head=-18, l1=(30, -40), l2=(-30, -70), a2=(-60, -80), mouth=1), 'ii'),            # 剑指下方
    (T_END + 0.5, P(x=NX - 300, air=520, face=1, w=-38, a1=(62, 58), lean=14, head=-18, l1=(30, -40), l2=(-30, -70), a2=(-60, -80), mouth=1), 'o')])       # 急退
def nl_pose(t):
    p = dict(_nk(t))
    if T_HIT < t < T_POP: p['bend'] = p.get('bend', 0) + 0.012 * math.sin(t * 150)
    if 4.9 < t < T_NAME - 0.16: p['air'] += 7 * math.sin(t * 3.2); p['w'] += 2.2 * math.sin(t * 120)                                         # 悬着，剑急颤
    return p
@functools.lru_cache(maxsize=4096)
def _JN(t): return F.kin(nl_pose(t), NH, GY)
def JN(t): return _JN(round(t, 4))
def sword_at(t, s): b, e = F.wpts(JN(t), SL, 0.04); return (b[0] + (e[0] - b[0]) * s, b[1] + (e[1] - b[1]) * s)

HITP = ruler_at(T_HIT, 0.60); ENDP = ruler_at(T_END, 0.55); STOMP = (JX(T_STOMP)['f1'][0], GY)
PH = [(JN(tp + 0.001)['h1'], JN(tp + 0.001)['wd']) for tp in T_PH]                      # 五道残影：剑每停一下留一道
_pd = math.atan2(ENDP[1] - PH[2][0][1], ENDP[0] - PH[2][0][0]); PDIR = (math.cos(_pd), math.sin(_pd))
def phantom(i, t):
    """第 i 道残影此刻的 (位置, 方向, 透明度)；T_NAME 之后首尾相接地射向萧炎。"""
    if t < T_PH[i]: return None
    (h, d) = PH[i]; a = min(1.0, (t - T_PH[i]) / 0.08) * (0.75 + 0.2 * math.sin(t * 40 + i))
    if t < T_NAME: return h, d, a
    u = min(1.0, max(0.0, (t - T_NAME - 0.02 * i) / (T_END - T_NAME - 0.02 * i))); e = u ** 2.2; tg = (ENDP[0] - PDIR[0] * (SL * NH * (i * 0.92 + 1.0)), ENDP[1] - PDIR[1] * (SL * NH * (i * 0.92 + 1.0)))
    k = min(1.0, u * 4); dd = (d[0] + (PDIR[0] - d[0]) * k, d[1] + (PDIR[1] - d[1]) * k); return (h[0] + (tg[0] - h[0]) * e, h[1] + (tg[1] - h[1]) * e), dd, (a if t < T_END else 0.0)

# ---------- 镜头
_cam = track([(0, (452, 596, 3.3, -5)), (0.84, (470, 600, 3.7, -3), 'lin'), (1.02, (940, 660, 1.02, 0), 'snap'), (T_GO - 0.02, (930, 664, 1.06, 0), 'lin'),
    (T_GO + 0.22, (720, 700, 1.62, 3), 'i'), (2.20, (1200, 700, 1.55, 3), 'lin'), (2.44, (1290, 640, 1.32, 0), 'o'), (2.80, (1150, 640, 1.3, -2), 'io'), (3.25, (860, 650, 1.3, 0), 'io'), (3.50, (850, 655, 1.42, 0), 'io'),
    (T_HIT + 0.02, (HITP[0], HITP[1] + 20, 2.25, -7), 'ii'), (T_POP, (HITP[0] - 10, HITP[1] + 16, 2.55, -5), 'lin'), (T_POP + 0.5, (1010, 500, 1.0, 0), 'snap'), (T_PH[0] + 0.1, (1000, 480, 1.03, 0), 'lin'),
    (T_PH[0] + 0.12, (PH[2][0][0] + 30, PH[2][0][1] + 40, 1.75, 6), 'hold'), (T_PH[2] + 0.28, (PH[2][0][0] + 40, PH[2][0][1] + 30, 1.95, 3), 'lin'),                 # 切：她在半空画剑
    (T_PH[2] + 0.30, (1400, 690, 1.9, -5), 'hold'), (T_STOMP - 0.02, (1410, 700, 2.25, -8), 'lin'),                                                                # 切：他插尺蓄势
    (T_STOMP + 0.26, (1010, 480, 1.1, -3), 'snap'), (T_NAME + 0.2, (960, 430, 1.16, -6), 'lin'), (T_END, (ENDP[0] + 20, ENDP[1] + 10, 1.5, -12), 'i'), (T_END + 0.6, (ENDP[0], ENDP[1], 1.7, -9), 'o')])
SHAKES = [(T_GO, 10, 0.12), (T_X, 5, 0.05), (T_X + 0.085, 5, 0.05), (T_X + 0.17, 5, 0.05), (T_HIT, 24, 0.14), (T_POP, 20, 0.16), (T_STOMP, 30, 0.2), (T_END, 40, 0.3)] + [(tp, 4, 0.06) for tp in T_PH]
def camera(t): cx, cy, z, ro = _cam(t); dx, dy = A.shake(t, SHAKES, FPS); return (cx + dx / z, cy + dy / z, z, ro)
_aura = track([(0, 0.0), (0.34, 0.0), (0.44, 1.0, 'snap'), (T_GO, 0.8), (2.3, 0.6), (2.6, 0.25), (T_HIT, 0.5), (T_POP, 0.7), (4.8, 0.3), (5.2, 0.5), (5.9, 1.0), (T_END + 1, 1.0)])
_fire = track([(0, 0.0), (5.15, 0.0), (5.9, 1.0), (9, 1.0)])

# ---------- 一帧
PL = None; NAME = None; CARD = None
def body_pts(J): return [J['f1'], J['f2'], J['k1'], J['k2'], J['pel'], J['chest'], J['neck'], J['e1'], J['e2'], J['head']]
def frame(t):
    global PL, NAME, CARD
    if PL is None: PL = yunlan.plates(R); NAME = A.Slam('风灵分形剑', _env.BRUSH, 190, R, glow=(70, 240, 255)); CARD = A.Slam('三年之约', _env.BRUSH, 300, R, col=(235, 255, 248), glow=(40, 255, 200), vertical=False)
    if t >= T_CARD: return card(t)
    cam = camera(t); c0 = _cam(t - 1 / 60); c1 = _cam(t); vx = (c1[0] - c0[0]) * 60 * c1[2] * R.k; vy = (c1[1] - c0[1]) * 60 * c1[2] * R.k; fr = None
    for i, (pl, d) in enumerate(PL):
        fr = A.plate(fr, pl, A.cam_m(cam, d, R), R)
        if i == 3 and abs(c1[2] - c0[2]) < 0.2: fr = A.mblur(fr, vx * 0.02, vy * 0.02)                                                   # 镜头快移时远处糊成线
    fr = A.mblur(fr, vx * 0.006, vy * 0.006) if abs(c1[2] - c0[2]) < 0.2 else fr
    M = A.cam_m(cam, 1.0, R); q = cam[2] * R.k; X, N = JX(t), JN(t); au = _aura(t); fi = _fire(t)
    # 地面：影子、尺拖出的沟、踏裂的缝
    s, c = A.ctx(R, M)
    for J in (X, N): h = GY - J['pel'][1]; k = max(0.25, 1 - h / 900); c.save(); c.translate(J['pel'][0], GY + 6); c.scale(1, 0.22); c.arc(0, 0, 105 * k, 0, 7); c.restore(); c.set_source_rgba(0.05, 0.08, 0.2, 0.42 * k); c.fill()
    if t > T_GO:
        x0 = ruler_at(T_GO, 1.0)[0]; x1 = ruler_at(min(t, 2.26), 1.0)[0]; c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(x0, GY + 9); c.line_to(x1, GY + 9); c.set_source_rgba(0.08, 0.09, 0.16, 0.9); c.set_line_width(9); c.stroke(); c.move_to(x0, GY + 5); c.line_to(x1, GY + 5); c.set_source_rgba(0.85, 0.92, 1, 0.5); c.set_line_width(2); c.stroke()
    if t > T_STOMP:
        k = min(1.0, (t - T_STOMP) / 0.07); c.set_source_rgba(0.05, 0.06, 0.12, 0.95); c.set_line_join(cairo.LINE_JOIN_ROUND)
        for i in range(13):
            th = i / 13 * 6.283 + rnd(i, 3); L = (150 + 240 * rnd(i, 4)) * k; x, y = STOMP[0], STOMP[1] + 16; c.move_to(x, y)
            for j in range(1, 5): x += math.cos(th + (rnd(i, j) - 0.5) * 0.9) * L / 4; y += math.sin(th + (rnd(i, j) - 0.5) * 0.9) * L / 4 * 0.3; c.line_to(x, y)
            c.set_line_width(7 - 1.0 * (i % 4)); c.stroke()
    fr = over(fr, s)
    # 身后的斗气：萧炎青色，纳兰淡青的风
    s, c = A.ctx(R, M)
    if au > 0.02:
        A.flame(c, t, lambda dt, sv: (lambda b: (b[int(sv * 9.99)][0] + (rnd(int(sv * 1000), 1) - 0.5) * 70, b[int(sv * 9.99)][1] + 20))(body_pts(JX(t - dt))), 46, 0.5, 520, 54, CYAN, a=0.5 * au, seed=11, wob=26)
    wn = 0.35 + 0.65 * pulse(t, T_POP - 0.5, 0.5, 0.5) + (0.5 if t > T_PH[0] else 0)
    A.flame(c, t, lambda dt, sv: (lambda b: (b[int(sv * 9.99)][0] + (rnd(int(sv * 1000), 2) - 0.5) * 60, b[int(sv * 9.99)][1] + 10))(body_pts(JN(t - dt))), 26, 0.5, 380, 44, WIND, a=0.26 * wn, seed=21, wob=40)
    fr = A.add_glow(fr, s, 16 * q, 0.9, body=0.9)
    # 人
    s, c = A.ctx(R, M)
    if T_GO < t < 2.42 or T_STOMP < t < T_END:                                           # 冲得快时拖几道黑影
        for k in (4, 3, 2, 1): c.push_group(); F.xiaoyan(c, lambda dt, k=k: JX(t - 0.022 * k - dt), t); c.pop_group_to_source(); c.paint_with_alpha(0.30 - 0.055 * k)
    if 2.3 < t < 3.12 or T_POP < t < 4.9:
        for k in (3, 2, 1): c.push_group(); F.nalan(c, lambda dt, k=k: JN(t - 0.03 * k - dt), t); c.pop_group_to_source(); c.paint_with_alpha(0.26 - 0.06 * k)
    F.xiaoyan(c, lambda dt: JX(t - dt), t); F.nalan(c, lambda dt: JN(t - dt), t); mask = rgba(s)[1]; fr = over(fr, s)
    # 尘和碎石
    s, c = A.ctx(R, M); DU = (0.86, 0.9, 0.96, 0.75)
    A.puff(c, t, T_GO, (430, GY + 6), 16, 110, 90, 26, 120, 0.9, DU, 1, vx=-160); A.puff(c, t, 2.26, (1190, GY + 6), 14, 80, 70, 22, 100, 0.8, DU, 2, vx=120)
    for i in range(8): tb = T_GO + 0.1 + i * 0.1; A.puff(c, t, tb, (ruler_at(tb, 1.0)[0], GY + 6), 4, 30, 60, 14, 70, 0.6, DU, 30 + i, vx=-90)
    A.puff(c, t, 2.26, (1490, GY + 6), 8, 60, 40, 16, 70, 0.6, DU, 3); A.puff(c, t, 3.12, (NX - 70, GY + 6), 9, 70, 40, 16, 70, 0.6, DU, 4); A.puff(c, t, T_HIT, ((HITP[0] + NX) / 2 + 80, GY + 6), 16, 260, 60, 22, 110, 0.7, DU, 5)
    A.puff(c, t, T_POP, (1200, GY + 6), 20, 200, 80, 26, 130, 1.0, DU, 6, vx=200); A.puff(c, t, T_POP, (NX, GY + 6), 14, 150, 60, 24, 120, 0.9, DU, 7)
    A.puff(c, t, T_STOMP, STOMP, 34, 330, 190, 40, 210, 1.5, DU, 8); A.debris(c, t, T_STOMP, (STOMP[0], GY), 30, 500, 1500, (0.50, 0.57, 0.68), seed=9, floor=GY + 10)
    fr = over(fr, s)
    # 发光的东西：刀光、火、火花、风刃、残影、气浪
    s, c = A.ctx(R, M); tr = [F.wpts(JX(t - k / 300), RL, 0.12) for k in range(34)]; sp = math.hypot(tr[0][1][0] - tr[4][1][0], tr[0][1][1] - tr[4][1][1]) * 75
    if sp > 1500: A.trail(c, tr, (0.25 + 0.3 * fi, 0.5 + 0.5 * fi, 0.7), a=min(1.0, (sp - 1500) / 3500), core=(0.8, 1, 0.97) if fi > 0.5 else (0.92, 0.95, 1))
    tr = [F.wpts(JN(t - k / 300), SL, 0.05) for k in range(30)]; sp = math.hypot(tr[0][1][0] - tr[4][1][0], tr[0][1][1] - tr[4][1][1]) * 75
    if sp > 1200: A.trail(c, tr, WIND, a=min(1.0, (sp - 1200) / 2500))
    A.emit(c, t, T_GO, 2.26, 150, lambda tb: (ruler_at(tb, 1.0)[0], GY + 4), ang=150, spread=45, v0=200, v1=1000, life=0.36, col=(1.0, 0.82, 0.45), w=3.2, g=1600)                 # 尺尖擦地的火花
    if fi > 0.02:
        A.flame(c, t, lambda dt, sv: ruler_at(t - dt, 0.12 + 0.88 * sv), 90, 0.42, 300, 34, CYAN, a=0.95 * fi, seed=31, wob=14); b, e = F.wpts(X, RL, 0.12); c.move_to(*b); c.line_to(*e); c.set_source_rgba(0.5, 1, 0.85, 0.5 * fi); c.set_line_width(46); c.set_line_cap(cairo.LINE_CAP_BUTT); c.stroke()
    for i in range(4):                                                                   # 剑身上的小风卷
        u = (t * 1.6 + i / 4) % 1.0; p0 = sword_at(t, 0.15 + 0.8 * u); d = N['wd']; c.save(); c.translate(*p0); c.rotate(math.atan2(d[1], d[0])); c.scale(0.34, 1); c.arc(0, 0, 30 + 10 * wn, t * 20 + i, t * 20 + i + 4.4); c.restore(); c.set_source_rgba(*WIND, 0.5 * min(1, wn + 0.2) * math.sin(u * math.pi)); c.set_line_width(4); c.stroke()
    for i, (ta, tb, sv) in enumerate(BLADES):                                            # 风刃
        if ta <= t < tb: u = (t - ta) / (tb - ta); a0 = sword_at(ta, 0.8); a1 = ruler_at(tb, sv); p0 = (a0[0] + (a1[0] - a0[0]) * u, a0[1] + (a1[1] - a0[1]) * u); an = math.degrees(math.atan2(-(a1[1] - a0[1]), a1[0] - a0[0])); A.crescent(c, p0, an, 84, WIND, 0.95); A.crescent(c, (p0[0] - (a1[0] - a0[0]) * 0.12, p0[1] - (a1[1] - a0[1]) * 0.12), an, 70, WIND, 0.4)
        A.sparks(c, t, tb, ruler_at(tb, sv), 12, 20, 80, 200, 900, 0.3, (0.8, 1, 1), seed=40 + i, w=2.6); A.ring(c, t, tb, ruler_at(tb, sv), 90, 0.18, WIND, sq=1.0, w=8)
    A.ring(c, t, 2.26, (1492, GY + 8), 190, 0.4, WIND, w=14)
    A.sparks(c, t, T_HIT, HITP, 60, 90, 180, 300, 1900, 0.5, (1.0, 0.95, 0.75), seed=50, w=3.6); A.ring(c, t, T_HIT, HITP, 330, 0.32, (1, 1, 1), sq=1.0, w=22); A.ring(c, t, T_HIT, ((HITP[0] + NX) / 2 + 60, GY + 8), 520, 0.5, (0.9, 0.97, 1), w=18)
    A.emit(c, t, T_HIT + 0.05, T_POP, 110, lambda tb: HITP, ang=90, spread=180, v0=150, v1=900, life=0.3, col=(0.75, 1.0, 0.95), w=2.6, seed=60)
    if T_HIT < t < T_POP + 0.5: k = (t - T_HIT) / (T_POP - T_HIT); a = min(1.0, k) ** 2 if t < T_POP else math.exp(-(t - T_POP) / 0.07); A.burst(c, sword_at(min(t, T_POP), 0.7), 60 + 150 * min(k, 1.0) + (340 * (1 - math.exp(-(t - T_POP) / 0.08)) if t > T_POP else 0), WIND, a, rays=14 if t > T_POP - 0.3 else 0, t=t, seed=70)
    A.sparks(c, t, T_POP, HITP, 50, 60, 120, 400, 2200, 0.5, WIND, seed=80, w=3.4); A.ring(c, t, T_POP, HITP, 620, 0.4, WIND, sq=1.0, w=30); A.ring(c, t, T_POP, (NX + 60, GY + 8), 700, 0.6, WIND, w=20)
    for i in range(5):
        ph = phantom(i, t)
        if ph and ph[2] > 0:
            h, d, a = ph; c.move_to(*h); c.line_to(h[0] + d[0] * SL * NH, h[1] + d[1] * SL * NH); c.set_source_rgba(*WIND, a * 0.45); c.set_line_width(20); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke(); F.sword(c, None, 3.2, L=SL * NH / 300, col=(0.55, 1.0, 1.0), a=a * 0.8, at=h, d=d); A.ring(c, t, T_PH[i], (h[0] + d[0] * 90, h[1] + d[1] * 90), 150, 0.25, WIND, sq=1.0, w=10)
            if t > T_NAME: tp = (h[0] + d[0] * SL * NH, h[1] + d[1] * SL * NH); A.burst(c, tp, 46, WIND, 0.9); c.move_to(*tp); c.line_to(tp[0] - PDIR[0] * 420 * min(1, (t - T_NAME) * 5), tp[1] - PDIR[1] * 420 * min(1, (t - T_NAME) * 5)); c.set_source_rgba(*WIND, 0.35); c.set_line_width(22 - 3 * i); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    A.sparks(c, t, T_STOMP, STOMP, 50, 90, 80, 500, 2400, 0.55, CYAN, seed=90, w=4, g=900); A.ring(c, t, T_STOMP, (STOMP[0], GY + 10), 760, 0.55, (0.7, 1, 0.9), w=30); A.ring(c, t, T_STOMP + 0.05, (STOMP[0], GY + 10), 480, 0.5, CYAN, w=16)
    if T_STOMP - 0.02 < t < T_STOMP + 0.4: A.burst(c, STOMP, 420 * (1 - math.exp(-(t - T_STOMP + 0.02) / 0.05)), CYAN, math.exp(-max(0, t - T_STOMP) / 0.1), rays=18, t=t, seed=95)
    if t >= T_END: k = t - T_END; A.sparks(c, t, T_END, ENDP, 90, 90, 180, 600, 3200, 0.7, (0.8, 1, 0.95), seed=100, w=4.5, g=300); A.ring(c, t, T_END, ENDP, 1500, 0.5, (0.8, 1, 0.95), sq=1.0, w=44); A.burst(c, ENDP, 220 + 5200 * k ** 1.3, CYAN, 1.0, rays=26, t=t, seed=110)
    glow = rgba(s)[0]; fr = A.add_glow(fr, s, 14 * q, 1.1)
    fr = A.bloom(fr, R, 0.80, 0.55)
    # 屏幕上的效果
    if T_GO + 0.05 < t < 2.3: fr = A.speedlines(fr, t, R, a=0.55 * min(1, (t - T_GO) * 6) * min(1, (2.3 - t) * 8), ang=-cam[3])
    if T_STOMP + 0.08 < t < T_END: fr = A.speedlines(fr, t, R, a=0.35, ang=24 - cam[3], n=30, col=(0.85, 1, 0.95))
    scr = lambda p: (M[0, 0] * p[0] + M[0, 1] * p[1] + M[0, 2], M[1, 0] * p[0] + M[1, 1] * p[1] + M[1, 2])
    if 0.36 < t < 0.84: fr = A.focuslines(fr, t, R, scr(X['head']), a=0.5 * min(1, (0.84 - t) * 6), n=60, r0=0.36)
    if T_PH[2] + 0.30 < t < T_STOMP: fr = A.focuslines(fr, t, R, scr(X['chest']), a=0.35, n=50, r0=0.40, col=(0.8, 1, 0.93))
    for (t0, pos, seq) in ((T_HIT, HITP, (1, 1, 2, 2, 3)), (T_POP, HITP, (3, 2, 3)), (T_STOMP, STOMP, (2, 2, 3)), (T_END, ENDP, (1, 1, 2, 2, 2, 1, 3))):
        n = int(round((t - t0) * 60))
        if 0 <= n < len(seq): fr = A.impact(fr, mask, glow, seq[n], R, scr(pos), t)
    if t > T_END + 0.1: k = min(1.0, (t - T_END - 0.1) / 0.42) ** 1.5; fr = fr + (np.float32((0.86, 1.0, 0.96)) - fr) * k                             # 青光大盛
    fr = A.grade(np.clip(fr, 0, 1)); fr = NAME.draw(fr, t, T_NAME - 0.04, T_END, (1640, 520), R, rot=-4)
    if 0.42 < t < T_GO + 0.5: im = to_pil(fr); sub(im, '战吧！纳兰嫣然！三年了！', y=int(960 * R.k), px=int(52 * R.k)) if R.k == 1 else _sub(im, '战吧！纳兰嫣然！三年了！'); fr = np.asarray(im, np.float32) / 255
    return fr
def _sub(im, s):
    big = im.resize((1920, 1080), Image.BILINEAR); sub(big, s, y=968, px=54); im.paste(big.resize(im.size, Image.LANCZOS))
def card(t):
    """片尾一张字卡：黑底，青火色的毛笔字。"""
    fr = np.zeros((R.h, R.w, 3), np.float32); s, c = layer(R.w, R.h); c.scale(R.k, R.k)
    A.flame(c, t, lambda dt, sv: (360 + 1200 * sv, 700 + 40 * math.sin(sv * 9)), 120, 0.9, 420, 70, CYAN, a=0.42, seed=5, wob=30); fr = A.add_glow(fr, s, 20 * R.k, 1.0)
    fr = CARD.draw(fr, t, T_CARD, DUR + 1, (960, 500), R, big=1.8, din=0.16); im = to_pil(np.clip(fr, 0, 1)); _sub(im, '斗破苍穹 · 萧炎   试片') if t > T_CARD + 0.3 else None; fr = np.asarray(im, np.float32) / 255
    return fr * min(1.0, (DUR - t) / 0.5) * (1 if t > T_CARD + 0.06 else 3.0)
def u8(fr): return (np.clip(fr, 0, 1) * 255).astype(np.uint8)
def _enc(out, extra=()): return subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{R.w}x{R.h}', '-r', str(FPS), '-i', '-', *extra, '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'full'
    if cmd == 'still': Image.fromarray(u8(frame(float(sys.argv[2])))).save(sys.argv[3] if len(sys.argv) > 3 else 'out/_still.png')
    elif cmd == 'strip':
        ims = [cv2.resize(u8(frame(float(x))), (480, 270), interpolation=cv2.INTER_AREA) for x in sys.argv[2:]]
        while len(ims) % 4: ims.append(np.zeros_like(ims[0]))
        Image.fromarray(np.vstack([np.hstack(ims[i:i + 4]) for i in range(0, len(ims), 4)])).save('out/_strip.jpg', quality=88)
    elif cmd == 'seg':
        i, k = int(sys.argv[2]), int(sys.argv[3]); n = int(DUR * FPS); p = _enc(f'out/_seg{R.h}_{i:02d}.mp4')
        for j in range(n * i // k, n * (i + 1) // k): p.stdin.write(u8(frame(j / FPS)).tobytes())
        p.stdin.close(); p.wait()
    else:
        k = max(1, (os.cpu_count() or 2) - 1); out = f'out/fight_{R.h}p.mp4'; subprocess.run([sys.executable, 'mix.py'], check=True)
        if any(p.wait() for p in [subprocess.Popen([sys.executable, 'fight.py', 'seg', str(i), str(k)]) for i in range(k)]): sys.exit('有分段渲染失败')
        open('out/_cat.txt', 'w').write(''.join(f"file '_seg{R.h}_{i:02d}.mp4'\n" for i in range(k)))
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'out/_cat.txt', '-i', 'out/mix.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out], check=True); print('done', out)
