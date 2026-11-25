"""《谁惹了蒙古》主片：大地图推演 + 蛋蛋人小剧场。"""
import os, sys, math
import numpy as np, cairo, cv2
from PIL import Image
from common import *
from mapwar.mapshot import MapShot
from mapwar.film import Film
from geo import make_world
import skits as S

import fights as FT

a4, c3, d5 = st('a4'), st('c3'), st('d5')
# ---- 分镜切点（C_JIN1 / C_YH* / C_BG* / C_CA2 / C_BQ0 / T_FEINT / T_TURN 在 common 里）
C_JIN0 = st('a1') - 0.07                                      # 金：小剧场
C_KH0, C_KH1 = st('b1') + 2.15, st('b4') - 1.05              # 花剌子模：小剧场；之后是成吉思汗特写
C_RU0, C_RU1 = st('c1') + 1.8, T_FEINT                        # 罗斯：小剧场
C_CA0, C_CA1 = en('d1') + 0.05, st('d3') - 0.17
C_DY0, C_DY1 = st('e2') - 0.14, st('f1') - 0.10
T_DIVE = st('e1') + 2.0
T_SLAM = st('f1') + 3.75                                      # 「折在了这里」
D3 = [C_JIN1 + 0.10 + 0.42 * k for k in range(3)]             # 金：三路出发的鼓点
H4 = [T_DROP2 + 1.0 + 0.47 * k for k in range(4)]             # 花剌子模：四路落点
B3 = [C_CA2 + 0.10 + 0.42 * k for k in range(3)]              # 巴格达：三路出发

TARGETS = [('金国', 116.4, 39.9, C.JB, 1), ('花剌子模', 66.9, 39.7, C.SJ, 4), ('罗斯', 30.5, 50.5, C.WG, 5), ('巴格达', 44.4, 33.3, C.HLF, 7)]
WHIPS = [(B(9), B(9) + 0.6), (T_NIGHT, T_NIGHT + 0.62), (T_BAG, T_BAG + 0.62), (T_DIVE, T_DIVE + 0.9), (T_SLAM - 0.75, T_SLAM)]
DIVES = [C_YH0, C_BG0]                                        # 地图扎进战场
LYR = [(1.15, '不小心'), (1.95, '惹了'), (2.55, '上帝～')]
ST = {}


def build():
    Wd = make_world()
    camseg = [
        [(0.0, 76, 42, 0.40, 0.0), (T0, 76, 42, 0.43, 0.0)],
        [(T0, 76, 42, 0.40, 0.0), (C_JIN0, 76, 42, 0.42, 0.0)],
        [(C_JIN1, 111.5, 43.8, 1.0, 0.74), (C_YH0 - 0.5, 112.6, 42.8, 1.12, 0.78), (C_YH0, 114.6, 41.0, 2.5, 0.86)],
        [(C_YH1, 114.8, 40.0, 1.7, 0.84), (C_YH1 + 0.5, 118.6, 38.9, 1.12, 0.8), (B(9), 118.8, 38.2, 1.05, 0.78)],
        [(B(9), 108, 39, 1.0, 0.78), (B(9) + 0.6, 68.3, 42.6, 1.3, 0.8), (C_KH0, 67.6, 42.2, 1.45, 0.82)],
        [(T_DROP2, 101, 46.5, 0.78, 0.62), (T_DROP2 + 0.85, 73, 44.2, 1.5, 0.76), (H4[0], 67.2, 43.0, 1.95, 0.8), (H4[3] + 0.5, 66.0, 42.0, 2.0, 0.82), (T_END2 - 0.3, 61.5, 40.0, 1.05, 0.76), (T_NIGHT, 60, 39.5, 0.95, 0.74)],
        [(T_NIGHT, 58, 42, 0.9, 0.7), (T_NIGHT + 0.62, 32, 50, 1.2, 0.76), (C_RU0, 31, 50.3, 1.34, 0.8)],
        [(C_RU1, 33.2, 50.5, 1.9, 0.78), (T_TURN, 35.4, 49.7, 2.0, 0.8), (T_TURN + 0.5, 35.2, 49.6, 2.25, 0.82), (T_END3 + 0.3, 35.0, 50.2, 1.25, 0.78), (C_BQ0, 35.0, 50.6, 1.12, 0.76)],
        [(T_BAG, 36, 49, 1.0, 0.72), (T_BAG + 0.62, 44.6, 34, 1.3, 0.8), (C_CA0, 44.4, 33.5, 1.45, 0.82)],
        [(C_CA2, 46.8, 33.9, 1.55, 0.76), (C_BG0 - 0.5, 46.0, 33.7, 1.75, 0.8), (C_BG0, 44.4, 33.3, 2.8, 0.86)],
        [(C_BG1, 44.6, 33.5, 1.9, 0.82), (T_DY, 45.3, 33.9, 1.15, 0.76)],
        [(T_DY, 77, 41.5, 0.40, 0.0), (T_DIVE, 79, 41, 0.42, 0.0), (T_DIVE + 0.9, 106.3, 30.6, 1.55, 0.78), (C_DY0, 106.3, 30.1, 1.9, 0.84)],
        [(C_DY1, 52, 36, 0.62, 0.35), (C_DY1 + 2.0, 72, 40, 0.45, 0.0), (T_SLAM - 0.75, 78, 41, 0.43, 0.0), (T_SLAM, 106.3, 30.4, 1.35, 0.62), (TOTAL, 106.3, 30.15, 1.55, 0.66)],
    ]
    J_MID = [(108.5, 46.6), (112, 44.2), (114.6, 41.0)]; J_W = [(102.5, 45.6), (106.2, 43.2), (109.6, 40.6)]; J_E = [(114.5, 48.3), (118.2, 46.6), (121, 44.2)]
    KH0 = (70.8, 43.7)                                                           # 花剌子模边境：四路在这里分兵
    arrows = [
        # ① 金：1211 三路南下 → 野狐岭；战后 1213 三路横扫华北
        (D3[0], C_YH0 + 0.2, C_YH0 + 0.1, 0, 17, J_MID), (D3[1], C_YH0 + 0.2, C_YH0 + 0.1, 0, 13, J_W), (D3[2], C_YH0 + 0.2, C_YH0 + 0.1, 0, 12, J_E),
        (C_YH1 - 1.0, C_YH1 + 1.2, B(9), 0, 17, J_MID + [(116.4, 39.9), (117, 36.7)]),
        (C_YH1 - 1.0, C_YH1 + 1.3, B(9), 0, 14, J_W + [(112.5, 37.9), (113.6, 35.6), (114.3, 34.8)]),
        (C_YH1 - 1.0, C_YH1 + 1.1, B(9), 0, 12, J_E + [(122.4, 42.6), (123.2, 41.3)]),
        # ② 花剌子模：一路杀到边境，兵分四路；之后追着沙王往西
        (T_DROP2 + 0.05, T_DROP2 + 0.95, T_NIGHT, 0, 19, [(102.8, 47.2), (91, 46.2), (79, 44.4), KH0]),
        (T_DROP2 + 0.9, H4[0], T_NIGHT, 0, 7, [KH0, (69.5, 43.4), (68.3, 42.9)]),
        (T_DROP2 + 0.9, H4[1], T_NIGHT, 0, 7, [KH0, (68.0, 44.8), (64.6, 45.3), (61.8, 45.9)]),
        (T_DROP2 + 0.9, H4[2], T_NIGHT, 0, 6, [KH0, (70.6, 42.0), (69.6, 40.3)]),
        (T_DROP2 + 0.9, H4[3] + 0.35, T_NIGHT, 0, 9, [KH0, (67.0, 43.3), (64.0, 42.0), (63.6, 40.6), (64.4, 39.8), (66.9, 39.7)]),
        (H4[3] + 0.5, H4[3] + 1.4, T_NIGHT, 0, 10, [(64.4, 39.8), (61.5, 41.3), (59.1, 42.3)]),
        (H4[3] + 0.5, H4[3] + 1.7, T_NIGHT, 0, 13, [(64.4, 39.8), (60.5, 38.2), (56, 36.5), (51.4, 35.6)]),
        # ③ 罗斯：佯退九天（往东）→ 回头反杀（往西）
        (T_FEINT + 0.2, T_TURN - 0.3, T_TURN + 0.1, 0, 6, [(31.8, 48.9), (34.5, 48.2), (37.2, 47.5)]),
        (T_FEINT + 0.7, T_TURN, T_TURN + 0.5, 5, 8, [(30.5, 50.5), (32.2, 49.5), (34.6, 48.6), (36.6, 47.9)]),
        (T_TURN, T_TURN + 0.8, C_BQ0, 0, 11, [(38.0, 47.3), (36.3, 47.8), (34.2, 48.8), (32.2, 49.7), (30.5, 50.5)]),
        (T_TURN + 0.1, T_TURN + 0.8, C_BQ0, 0, 7, [(38.2, 47.6), (37.4, 49.4), (35.4, 50.1), (33.6, 49.6)]),
        (T_TURN + 0.1, T_TURN + 0.8, C_BQ0, 0, 7, [(38.0, 47.0), (36.2, 46.3), (34.0, 46.9), (33.0, 48.3)]),
        # ④ 巴格达：三路合围
        (B3[0], C_BG0, T_DY, 0, 11, [(51.4, 35.6), (48.6, 34.7), (46.4, 34.0), (44.4, 33.3)]),
        (B3[1], C_BG0, T_DY, 0, 8, [(43.1, 36.3), (42.7, 34.9), (43.3, 33.9), (44.4, 33.3)]),
        (B3[2], C_BG0, T_DY, 0, 8, [(49.6, 31.4), (47.4, 31.9), (45.7, 32.5), (44.4, 33.3)]),
        # 回师
        (C_DY1 + 0.3, C_DY1 + 2.2, T_SLAM + 0.3, 0, 16, [(37.5, 34.2), (45, 36.2), (55, 38.2), (67, 41.5), (82, 45.5), (100, 47.2)]),
    ]
    armies = [
        dict(n='成吉思汗', o=0, cav=1, path=[(C_JIN1, 109.2, 46.2, 2.5), (C_YH0, 113.4, 42.4, 2.5)], die=C_YH0 + 0.1),
        dict(n='三位皇子', o=0, cav=1, path=[(D3[1], 103.0, 45.3, 0.8), (C_YH0, 108.6, 41.5, 0.8)], die=C_YH0 + 0.1),
        dict(n='哲别', o=0, cav=1, path=[(D3[2], 115.0, 48.1, 0.5), (C_YH0, 120.0, 45.2, 0.5)], die=C_YH0 + 0.1),
        dict(n='金军主力', o=1, path=[(C_JIN1, 115.6, 40.2, 8), (C_YH0, 115.6, 40.2, 8)], face=-1, die=C_YH0 + 0.1),
        dict(n='成吉思汗', o=0, cav=1, path=[(C_YH1, 115.7, 40.4, 2.5), (C_YH1 + 1.2, 116.9, 37.4, 2.5)], die=B(9)),
        dict(n='三位皇子', o=0, cav=1, path=[(C_YH1, 110.4, 39.9, 0.8), (C_YH1 + 1.3, 113.5, 35.9, 0.8)], die=B(9)),
        dict(n='哲别', o=0, cav=1, path=[(C_YH1, 121.3, 43.8, 0.5), (C_YH1 + 1.1, 122.9, 41.7, 0.5)], die=B(9)),
        dict(n='成吉思汗', o=0, cav=1, path=[(T_DROP2, 101, 47, 4), (T_DROP2 + 0.9, 71.6, 43.9, 4), (T_DROP2 + 1.0, 70.4, 43.6, 1.6), (H4[3], 63.9, 40.9, 1.6), (H4[3] + 0.4, 66.3, 40.0, 1.6), (T_NIGHT, 66.3, 40.0, 1.6)], die=T_NIGHT),
        dict(n='察合台 窝阔台', o=0, cav=1, path=[(T_DROP2 + 0.9, 70.6, 43.6, 0.6), (H4[0], 68.8, 43.2, 0.6), (T_NIGHT, 68.8, 43.2, 0.6)], die=T_NIGHT),
        dict(n='术赤', o=0, cav=1, path=[(T_DROP2 + 0.9, 70.6, 43.8, 0.6), (H4[1], 62.6, 45.8, 0.6), (T_NIGHT, 62.6, 45.8, 0.6)], die=T_NIGHT),
        dict(n='偏师', o=0, cav=1, path=[(T_DROP2 + 0.9, 70.7, 43.5, 0.2), (H4[2], 69.9, 40.9, 0.2), (T_NIGHT, 69.9, 40.9, 0.2)], die=T_NIGHT),
        dict(n='哲别 速不台', o=0, cav=1, path=[(C_RU1, 32.4, 48.7, 0.8), (T_FEINT + 0.2, 32.4, 48.7, 0.6), (T_TURN - 0.3, 38.4, 47.1, 0.6), (T_TURN, 38.4, 47.1, 0.6), (T_TURN + 0.8, 35.4, 48.3, 0.6), (C_BQ0, 33.4, 49.3, 0.6)], die=C_BQ0),
        dict(n='罗斯联军', o=5, path=[(C_RU1, 30.7, 50.3, 2), (T_FEINT + 0.7, 30.7, 50.3, 2), (T_TURN, 35.4, 48.4, 2), (T_TURN + 1.5, 33.6, 49.1, 1)], rout=[(T_TURN + 0.35, T_TURN + 1.5)], die=T_TURN + 1.7),
        dict(n='旭烈兀', o=0, cav=1, path=[(C_CA2, 51.0, 35.5, 2.5), (C_BG0, 46.9, 34.2, 2.5)], die=C_BG0 + 0.1),
        dict(n='拜住', o=0, cav=1, path=[(B3[1], 43.0, 36.2, 0.7), (C_BG0, 42.9, 34.5, 0.7)], die=C_BG0 + 0.1),
        dict(n='怯的不花', o=0, cav=1, path=[(B3[2], 49.5, 31.5, 0.7), (C_BG0, 46.6, 32.1, 0.7)], die=C_BG0 + 0.1),
        dict(n='旭烈兀', o=0, cav=1, path=[(C_BG1, 45.7, 33.9, 2.5), (T_DY, 45.7, 33.9, 2.5)], face=-1, die=T_DY),
        dict(n='旭烈兀', o=0, cav=1, path=[(C_DY1, 38.5, 34.2, 15), (C_DY1 + 0.5, 38.5, 34.2, 15), (C_DY1 + 2.4, 62, 40, 15), (T_SLAM, 72, 42.5, 15)], die=T_SLAM + 0.2),
    ]
    fires = [(114.6, 41.0, C_YH0 - 0.6, C_YH1 + 0.9), (116.4, 39.9, C_YH1 + 0.2, C_YH1 + 1.8), (114.3, 34.8, C_YH1 + 1.2, B(9)),
             (68.3, 42.9, H4[0], H4[0] + 1.6), (64.6, 45.3, H4[1], H4[1] + 1.4), (69.6, 40.3, H4[2], H4[2] + 1.4), (64.4, 39.8, H4[3], H4[3] + 1.6), (66.9, 39.7, H4[3] + 0.35, H4[3] + 2.4),
             (36.6, 47.8, T_TURN + 0.3, T_TURN + 2.0), (44.4, 33.3, C_BG1 - 0.2, T_DY)]
    shakes = [(T0, 22)] + [(x, 9) for x in D3] + [(T_END1, 18), (T_DROP2, 26)] + [(x, 12) for x in H4] + [(T_END2, 18), (T_TURN + 0.45, 20), (T_END3, 18)] + [(x, 9) for x in B3] + [(T_SLAM, 26)]
    flashes = [T0, T_DROP2, T_TURN, T_SLAM]
    HEADS = [i for i, a in enumerate(arrows)]

    def style(t): return 'night' if (t < T0 or T_NIGHT <= t < T_BAG) else 'ink'

    def ground_fx(ms, c, t, Sp, st_):
        if t < C_JIN0:                                                           # 蒙古高原的红点
            x, y, s = Sp(102.8, 47.2); k = 1 if t < T0 else 0.6
            for r, a in ((150, 0.10), (95, 0.18), (55, 0.34)): c.arc(x, y, r * s * k * (1 + 0.12 * math.sin(t * 7)), 0, TAU); c.set_source_rgba(1, 0.16, 0.08, a); c.fill()
        Hm = None                                                                # 箭头前锋拖着的尘土
        for i in HEADS:
            (t0, t1, tf, o, w, pts) = arrows[i]
            if not (t0 <= t < t1 + 0.35): continue
            if Hm is None: Hm = ms.camera(t)[0]
            sp = ms.splines[i]; n = max(6, int(len(sp) * cl(eout((t - t0) / max(1e-3, t1 - t0), 1.6)))); fade = 1 - cl((t - t1) / 0.35)
            idx = [max(0, n - 1 - 2 * j) for j in range(9)]; P = cv2.perspectiveTransform(np.float32([sp[k] for k in idx])[None], Hm)[0]
            P2 = cv2.perspectiveTransform(np.float32([sp[k] for k in idx])[None] + np.float32([8, 0]), Hm)[0]
            for j in range(8, -1, -1):
                s_ = abs(P2[j][0] - P[j][0]) / 8; r = w * s_ * (1.3 + 0.32 * j) * (0.8 + 0.4 * hsh(i * 13 + j, int(t * 12)))
                ox = (hsh(i, j + int(t * 9)) - 0.5) * w * s_ * 1.6; col = (0.50, 0.40, 0.28) if st_ == 'ink' else (0.85, 0.72, 0.5)
                c.arc(P[j][0] + ox, P[j][1] - r * 0.25, r, 0, TAU); c.set_source_rgba(*col, (0.34 - 0.034 * j) * fade); c.fill()
        if T_DY + 0.2 <= t < C_DY0 or t >= C_DY1:                               # 钓鱼城的蓝色光圈
            x, y, s = Sp(106.3, 30.0)
            for k in range(3):
                u = ((t * 0.9 + k / 3) % 1); c.arc(x, y, (30 + 190 * u) * max(0.35, s), 0, TAU); c.set_source_rgba(0.2, 0.62, 1.0, 0.75 * (1 - u)); c.set_line_width(7); c.stroke()

    def post(frame, t, st_):
        if t < T0: frame = frame * 0.55
        for (w0, w1) in WHIPS:
            if w0 <= t < w1:
                k = int(150 * math.sin((t - w0) / (w1 - w0) * math.pi)) | 1
                if k > 3: frame = cv2.blur(frame, (k, max(1, k // 5) | 1))
        for d in DIVES:                                                          # 扎进战场：径向推镜 + 提亮
            u = (t - (d - 0.42)) / 0.42
            if 0 < u <= 1.05: frame = zoomblur(frame, 0.30 * u * u) + np.float32([1, 0.96, 0.88]) * 0.35 * u ** 3
        for d in (C_YH1, C_BG1):
            u = (t - d) / 0.22
            if 0 <= u < 1: frame = zoomblur(frame, 0.16 * (1 - u) ** 2) + np.float32([1, 0.96, 0.88]) * 0.3 * (1 - u) ** 2
        return frame

    def overlay(ms, X, t, Sp, st_, tilt):
        ST['Sp'] = Sp; night = st_ == 'night'
        if t < T0:                                                               # 歌词
            x = 960 - (sum(X.d.textlength(s, font=font(150)) for _, s in LYR) + 28) / 2
            for (tl, s) in LYR:
                w = X.d.textlength(s, font=font(150))
                if t >= tl: u = t - tl; X.T(s, x + w / 2, 520, 150 * (1 + 0.35 * (1 - eout(u / 0.14))), fill=(255, 236, 200) if s != '上帝～' else (255, 70, 40), stroke=10, halo=(20, 6, 4), a=ease(u / 0.06))
                x += w + 14
            return
        chips(X, t, night); subtitle(X, t)
        if t < C_JIN0:
            u = t - T0; X.T('13 世纪 · 欧亚大陆', 960, 232, 60, fill=(60, 44, 34), stroke=7, a=ease(u / 0.2))
            x, y, s = Sp(102.8, 47.2); X.T('蒙古', x, y - 70, 96 * (1 + 0.5 * (1 - eout(u / 0.16))), fill=(190, 24, 18), stroke=9, a=ease(u / 0.06))
        for (t0, s, n) in ((B(9) + 0.6, '花剌子模', '②'), (T_NIGHT + 0.62, '罗斯王公', '③'), (T_BAG + 0.62, '巴格达 · 哈里发', '④')):
            u = t - t0
            if 0 <= u < 1.7: X.T(n + ' ' + s, 960, 360, 150 * (1 + 0.5 * (1 - eout(u / 0.15))), fill=(255, 226, 150) if night else (168, 26, 16), stroke=12, a=ease(u / 0.05) * (1 - ease((u - 1.45) / 0.25)))
        RED = (255, 120, 70) if night else (168, 26, 16); INK = (255, 236, 200) if night else (60, 44, 34)
        def slam(s, x, y, size, u, hold, col=RED):
            if 0 <= u < hold: X.T(s, x, y, size * (1 + 0.5 * (1 - eout(u / 0.14))), fill=col, stroke=max(7, size // 12), a=ease(u / 0.05) * (1 - ease((u - hold + 0.2) / 0.2)))
        if C_JIN1 <= t < C_YH0:
            tag(X, '1211 年 · 蒙古大举南下'); slam('三路齐发', 1380, 330, 130, t - D3[0], C_YH0 - D3[0] - 0.3)
        if C_YH1 <= t < B(9):
            tag(X, '1213 年 · 兵分三路 横扫华北')
        if T_DROP2 <= t < T_NIGHT:
            tag(X, '1219 年 · 成吉思汗西征'); slam('兵分四路', 1470, 560, 140, t - (T_DROP2 + 0.9), 1.5)
            u = t - H4[3] + 0.5
            if 0 <= u and t < T_END2: x, y, s = Sp(62.6, 41.4); X.T('穿过沙漠 抄后路', x - 60 * s, y, 54, fill=RED, stroke=6, a=ease(u / 0.2))
        if T_FEINT <= t < C_BQ0:
            tag(X, '1223 年 · 迦勒迦河', True)
            if t < T_TURN:
                u = cl((t - T_FEINT - 0.2) / (T_TURN - T_FEINT - 0.5)); n = 1 + int(8.999 * u)
                X.T(f'假装撤退  第 {n} 天', 960, 310, 100, fill=INK, stroke=9, a=ease((t - T_FEINT) / 0.2))
            else: slam('回头！', 960, 320, 230, t - T_TURN, 0.85)
        if C_CA2 <= t < C_BG0:
            tag(X, '1258 年 · 旭烈兀西征'); slam('三路合围', 1400, 300, 130, t - B3[0], C_BG0 - B3[0] - 0.3)
        if C_BG1 <= t < T_DY: tag(X, '1258 年 · 巴格达')
        stamp(X, '金 · 亡', t, T_END1, x=650, y=470, hold=B(9) - T_END1 + 0.1, sub='1211 野狐岭惨败 → 1234 亡国')
        stamp(X, '两年 · 亡国', t, T_END2, y=470, hold=T_NIGHT - T_END2 + 0.1, sub='1219–1221 成吉思汗西征')
        stamp(X, '一战全崩', t, T_END3, y=480, hold=C_BQ0 - T_END3 + 0.1, sub='1223 迦勒迦河 → 1240 基辅陷落')
        stamp(X, '13 天 · 陷落', t, T_END4, y=640, hold=T_DY - T_END4 + 0.1, sub='1258 年 2 月 10 日')
        if T_DIVE + 0.9 <= t < C_DY0:
            u = t - T_DIVE - 0.9; n = int(round(36 * eout(u / 1.6, 1.5))); x, y, s = Sp(106.3, 30.0)
            X.T('钓鱼城', x, y - 170, 100, fill=(20, 82, 124), stroke=10)
            X.T(f'守了 {n} 年', 1420, 660, 150, fill=(20, 82, 124), stroke=12); X.T('1243 —— 1279', 1420, 780, 60, fill=(60, 44, 34), stroke=7)
        if C_DY1 <= t < T_SLAM - 0.8:
            u = t - C_DY1 - 0.5
            if u > 0: X.T('西征大军 · 回师', 700, 290, 96 * (1 + 0.4 * (1 - eout(u / 0.15))), fill=(168, 26, 16), stroke=10, a=ease(u / 0.06))
        if t >= T_SLAM:
            u = t - T_SLAM; X.T('上帝折鞭处', 960, 370, 250 * (1 + 0.6 * (1 - eout(u / 0.16))), fill=(190, 24, 18), stroke=16, a=ease(u / 0.05))
            X.T('1259 年 · 重庆钓鱼城', 960, 545, 70, fill=(40, 30, 24), stroke=8, a=ease((u - 0.25) / 0.2))

    sc = dict(style=style, camseg=camseg, arrows=arrows, armies=armies, egg={0: dict(body=(0.78, 0.14, 0.12), hat='ancient', hatcol=(0.88, 0.72, 0.22), weapon='spear'),
              1: dict(body=(0.80, 0.62, 0.16), hat='ancient', hatcol=(0.5, 0.36, 0.1), weapon='spear'), 5: dict(body=(0.45, 0.42, 0.66), hat='ancient', hatcol=(0.8, 0.8, 0.9), weapon='spear')},
              fig_scale=0.8, fires=fires, shakes=shakes, flashes=flashes, ground_fx=ground_fx, post=post, overlay=overlay,
              regions=[('蒙古高原', 103.5, 49.5), ('金', 114.5, 36.5), ('南宋', 114, 28.5), ('花剌子模', 62, 37.5), ('罗斯', 36, 54), ('阿拔斯', 43, 31)],
              keycity={'哈拉和林', '中都', '撒马尔罕', '巴格达', '基辅', '钓鱼城', '讹答剌', '临安'}, hud=dict(share=False, note='版图为历史推演示意'))
    return MapShot(Wd, sc)


_MS = None
def MS():
    global _MS
    if _MS is None: _MS = build()
    return _MS


def portrait(c, x, y, R, spec, t, ring=(0.75, 0.10, 0.08), **P):
    c.arc(x, y, R * 1.55, 0, TAU); fs(c, (0.96, 0.92, 0.82), 7); c.arc(x, y, R * 1.55, 0, TAU); c.set_source_rgb(*ring); c.set_line_width(12); c.stroke()
    c.save(); c.arc(x, y, R * 1.5, 0, TAU); c.clip(); RG.head(c, x, y + R * 0.3, R, spec, dict(front=True, **P), t); c.restore()


def mapf(lt, dur, t):
    img = MS().frame(t); Sp = ST['Sp']; items = []
    if T0 <= t < C_JIN0:                                                         # 点名：四个头像落到地图上
        def d(c):
            for i, (nm, lo, la, sp, o) in enumerate(TARGETS):
                u = t - (T0 + 0.6 + i * 0.4)
                if u < 0: continue
                x, y, s = Sp(lo, la); k = 1 + 1.2 * (1 - eout(u / 0.16)); y -= 20
                c.save(); c.translate(x, y); c.scale(k, k); portrait(c, 0, 0, 62, sp, t, eye='dot', brow='angry', mouth='smirk'); c.restore()
                items.append((nm, x, y + 130, i))
        A = layer(d); fr = over(np.asarray(img).astype(np.float32) / 255, A); X = Txt(False)
        for nm, x, y, i in items: X.T('①②③④'[i] + nm, x, y, 50, fill=(168, 26, 16), stroke=7)
        return X.over(to_img(fr))
    pop = None
    if talking(t, 'a5', 0.35): pop = ('a5', C.JB, 1540, 790, dict(eye='squeeze', brow='worried', mouth=mouth_of(t, 'a5', 'shout', 'o', 'wavy'), fx=('tear', 'sweat')), (0.62, 0.45, 0.10), 84)
    if talking(t, 'f2', 1.5): pop = ('f2', C.SB, 1500, 900, dict(eye='closed', brow='raised', mouth='smirk'), (0.12, 0.40, 0.62), 96)
    if pop:
        lid, sp, x, y, P, ring, sz = pop; u = t - st(lid) + 0.15; k = eout(u / 0.16, 3)
        def d(c): c.save(); c.translate(x, y + (1 - k) * 300); portrait(c, 0, 0, 96, sp, t, ring=ring, **P); c.restore()
        fr = over(np.asarray(img).astype(np.float32) / 255, layer(d)); X = Txt(False)
        say(X, t, lid, x - 60, y - 225, (x - 30, y - 140), size=sz, hold=1.5)
        return X.over(to_img(fr))
    return img


SHOTS = [
    (0.0, C_JIN0, mapf), (C_JIN0, C_JIN1, S.jin), (C_JIN1, C_YH0, mapf), (C_YH0, C_YH1, FT.yehuling), (C_YH1, C_KH0, mapf),
    (C_KH0, C_KH1, S.khwarazm), (C_KH1, T_DROP2, S.khan), (T_DROP2, C_RU0, mapf),
    (C_RU0, C_RU1, S.rus), (C_RU1, C_BQ0, mapf), (C_BQ0, T_BAG, S.banquet),
    (T_BAG, C_CA0, mapf), (C_CA0, C_CA1, S.caliph), (C_CA1, C_CA2, S.lonely), (C_CA2, C_BG0, mapf), (C_BG0, C_BG1, FT.baghdad),
    (C_BG1, C_DY0, mapf), (C_DY0, C_DY1, S.diaoyu), (C_DY1, TOTAL, mapf),
]


def make_film(): return Film(SHOTS, TOTAL, audio=os.path.join(HERE, 'out', 'mix.wav'), fade_out=0.8)


if __name__ == '__main__':
    make_film().cli()
