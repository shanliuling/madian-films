"""完整示例：楚汉争霸（约 63 秒，卡点燃剪，无旁白）。
这是一部已经做完的片子的数据和镜头写法，**拿来看写法，不是模板**——新题材的地图范围、势力、镜头数、战斗怎么打，都按新题材自己定。

  python examples/chuhan/scenario.py info
  python examples/chuhan/scenario.py still out 6 16 24 30 41 50 60
  python examples/chuhan/scenario.py render 楚汉.mp4 2 0.5        # 540p 预览
时间线按 BGM 的小节写（BAR=1.7195s），音频请自备（Film(audio=...)）。
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
import numpy as np, cairo
from PIL import Image
from mapwar.util import SW, SH, TAU, ease, eout, cl, Txt, to_img, VR, grain
from mapwar.world import World
from mapwar.mapshot import MapShot
from mapwar import field as F
from mapwar import chars as CH

A = lambda n: os.path.join(HERE, 'assets', n)

# ================================================================ 时间线（全部按 BGM 小节定）
BAR = 1.7195; BEAT = BAR / 4
T_A = 4.55; D1 = T_A + 6 * BAR; R1 = D1 + 1.5 * BAR; E1 = D1 + 11 * BAR; G0 = E1 + 4 * BAR; G1 = G0 + 2 * BAR; S0 = E1 + 12.41; D2 = S0 + 2.25
M5 = D2 + BAR; W0 = D2 + 3 * BAR; F0 = D2 + 6 * BAR; T_END = D2 + 8 * BAR + 1.0; HP = D1 + 4 * BAR
J0 = HP + 1.5 * BAR; J1 = HP + 3 * BAR; WS0 = HP + 3.5 * BAR; WS1 = HP + 5 * BAR; HG0 = WS1 + 1.05
b = lambda x: T_A + x * 1.115

# ================================================================ 世界
H_, C_, Q_, N_ = 0, 1, 2, 3
SIDES = [dict(name='汉', ink=(0.80, 0.22, 0.15), night=(0.95, 0.26, 0.14)), dict(name='楚', ink=(0.16, 0.30, 0.50), night=(0.16, 0.46, 0.95)),
         dict(name='齐', ink=(0.50, 0.50, 0.22), night=(0.75, 0.6, 0.2)), dict(name='诸侯', ink=(0.42, 0.38, 0.32), night=(0.33, 0.32, 0.30), wash=0.5, neutral=True)]
CITIES = [
    ('南郑', 107.03, 33.07, H_, 1), ('成都', 104.07, 30.66, H_, 0), ('江州', 106.55, 29.56, H_, 0), ('巴', 107.8, 31.2, H_, 0),
    ('陈仓', 107.37, 34.35, N_, 1), ('咸阳', 108.71, 34.33, N_, 0), ('栎阳', 109.23, 34.70, N_, 1), ('上邽', 105.72, 34.58, N_, 0),
    ('北地', 107.6, 35.9, N_, 0), ('上郡', 109.7, 37.4, N_, 0), ('武关', 110.4, 33.5, N_, 3), ('函谷关', 110.88, 34.55, N_, 3),
    ('安邑', 111.2, 35.15, N_, 1), ('平阳', 111.52, 36.08, N_, 0), ('晋阳', 112.55, 37.87, N_, 1), ('邯郸', 114.49, 36.61, N_, 1),
    ('襄国', 114.5, 37.07, N_, 0), ('井陉', 114.05, 38.03, N_, 3), ('代', 114.3, 39.6, N_, 0), ('蓟', 116.4, 39.9, N_, 0),
    ('洛阳', 112.45, 34.70, N_, 1), ('荥阳', 113.38, 34.79, N_, 1), ('宛', 112.53, 33.0, N_, 1), ('阳翟', 113.47, 34.16, N_, 0), ('朝歌', 114.2, 35.6, N_, 0),
    ('彭城', 117.18, 34.27, C_, 2), ('下邳', 118.0, 34.1, C_, 1), ('睢阳', 115.65, 34.45, C_, 1), ('陈', 114.88, 33.73, C_, 1),
    ('大梁', 114.35, 34.80, C_, 1), ('定陶', 115.57, 35.07, C_, 1), ('鲁', 116.99, 35.60, C_, 0), ('寿春', 116.78, 32.57, C_, 1),
    ('六', 116.5, 31.75, C_, 0), ('吴', 120.62, 31.30, C_, 0), ('广陵', 119.43, 32.39, C_, 0), ('会稽', 120.58, 30.0, C_, 0),
    ('江陵', 112.19, 30.35, C_, 0), ('邾', 114.87, 30.45, C_, 0), ('番阳', 116.67, 29.0, C_, 0), ('临湘', 112.97, 28.2, C_, 0),
    ('濮阳', 115.0, 35.7, C_, 0), ('东海', 118.8, 34.6, C_, 0), ('鄣', 119.0, 30.6, C_, 0), ('汝南', 114.4, 32.9, C_, 0),
    ('昌邑', 116.1, 35.15, C_, 0), ('东郡', 115.9, 36.05, C_, 0), ('薛', 117.3, 34.9, C_, 0),
    ('临淄', 118.31, 36.83, Q_, 1), ('历下', 117.0, 36.67, Q_, 0), ('即墨', 120.45, 36.39, Q_, 0), ('莒', 118.83, 35.58, Q_, 0),
    ('博阳', 117.1, 36.2, Q_, 0), ('胶东', 121.2, 37.3, Q_, 0), ('平原', 116.4, 37.2, Q_, 0),
    ('高密', 119.75, 36.38, Q_, 1), ('垓下', 117.55, 33.3, C_, 1), ('阴陵', 117.45, 32.6, C_, 0), ('东城', 117.95, 32.3, C_, 0), ('乌江', 118.45, 31.85, C_, 1)]
FLIPS = {
    '陈仓': [(b(.6), H_)], '咸阳': [(b(1.0), H_)], '上邽': [(b(1.0), H_)], '栎阳': [(b(1.4), H_)], '北地': [(b(1.8), H_)], '上郡': [(b(1.8), H_)],
    '武关': [(b(1.9), H_)], '函谷关': [(b(2.5), H_)], '洛阳': [(b(3.2), H_)], '阳翟': [(b(3.6), H_)], '宛': [(b(3.9), H_)], '荥阳': [(b(4.3), H_)],
    '朝歌': [(b(4.0), H_), (R1 + 2.0, N_), (J1 + .1, H_)], '安邑': [(b(3.5), H_), (R1 + 2.3, N_), (HP + .5 * BAR + .3, H_)], '平阳': [(b(3.6), H_), (R1 + 2.3, N_), (HP + .5 * BAR + .45, H_)],
    '大梁': [(b(5.1), H_), (R1 + 4 * BEAT, C_), (36.3, H_)], '定陶': [(b(5.8), H_), (R1 + 2 * BEAT, C_), (WS1 + .55, H_)], '睢阳': [(b(6.4), H_), (R1 + 2 * BEAT, C_), (37.0, H_)],
    '昌邑': [(b(6.6), H_), (R1 + BEAT, C_), (WS1 + .5, H_)], '彭城': [(b(7.4), H_), (R1 + .02, C_), (38.3, H_)], '薛': [(b(7.6), H_), (R1 + .02, C_), (38.0, H_)],
    '晋阳': [(HP + .5 * BAR + .9, H_)], '代': [(HP + .5 * BAR + 1.0, H_)], '井陉': [(J1 + .03, H_)], '邯郸': [(J1 + .08, H_)], '襄国': [(J1 + .08, H_)], '蓟': [(J1 + .3, H_)],
    '平原': [(J1 + .45, H_)], '历下': [(J1 + .55, H_)], '临淄': [(J1 + .7, H_)], '博阳': [(WS1 + .1, H_)], '高密': [(WS1 + .03, H_)], '即墨': [(WS1 + .2, H_)], '胶东': [(WS1 + .3, H_)], '莒': [(WS1 + .25, H_)],
    '东郡': [(WS1 + .5, H_)], '濮阳': [(WS1 + .6, H_)], '六': [(36.2, H_)], '陈': [(36.8, H_)], '汝南': [(36.9, H_)], '寿春': [(37.4, H_)], '下邳': [(38.5, H_)], '东海': [(38.6, H_)],
    '广陵': [(39.2, H_)], '垓下': [(M5 + .15, H_)], '阴陵': [(M5 + 1.3, H_)], '东城': [(M5 + 2.2, H_)],
    '乌江': [(F0 + .25, H_)], '邾': [(F0 + .3, H_)], '江陵': [(F0 + .4, H_)], '吴': [(F0 + .45, H_)], '鄣': [(F0 + .5, H_)], '番阳': [(F0 + .5, H_)], '会稽': [(F0 + .65, H_)],
    '临湘': [(F0 + .65, H_)], '鲁': [(F0 + .85, H_)]}
RANGES = [
    ([(104.5, 34.2), (106.5, 34.0), (108, 33.9), (109.5, 33.95), (110.5, 34.25), (111.5, 34.2)], 1.25), ([(111.6, 33.9), (112.6, 33.6), (113.3, 33.25)], 0.9),
    ([(106, 32.5), (107.5, 32.3), (109, 31.9), (110.3, 31.5), (110.2, 30.4)], 1.05), ([(113.3, 35.4), (113.6, 36.2), (113.9, 37.2), (114.2, 38.2), (114.8, 39.3), (115.5, 40.0)], 1.1),
    ([(111, 36), (111.3, 37.2), (111.6, 38.4)], 0.85), ([(115.8, 40.4), (117, 40.5), (118.5, 40.4), (119.5, 40.2)], 0.9), ([(116.9, 36.25), (117.6, 36.2), (118.2, 36.0), (118.3, 35.6)], 0.8),
    ([(113.8, 31.9), (114.8, 31.4), (115.8, 31.1), (116.6, 30.9)], 0.9), ([(110.6, 34.95), (111.6, 35.15), (112.3, 35.3)], 0.7), ([(106.2, 36.0), (106.4, 34.9)], 0.9),
    ([(103.4, 33.2), (103.9, 32.0), (103.4, 30.8), (102.8, 29.6)], 1.4), ([(109.2, 29.6), (110.3, 28.8), (110.8, 27.8)], 0.9), ([(117.8, 30.2), (118.8, 30.15), (119.5, 30.3)], 0.75),
    ([(113.8, 29.0), (114.6, 28.6)], 0.7), ([(113.9, 27.4), (114.2, 26.2)], 0.8), ([(116.8, 27.8), (117.6, 27.2), (118.2, 26.4)], 0.95),
    ([(106.5, 41.2), (109, 41.1), (111.5, 41.0), (113.5, 40.9)], 1.0), ([(105.9, 39.4), (106.1, 38.4)], 0.9), ([(100.0, 38.6), (101.5, 37.8), (103, 37.0)], 1.3),
    ([(100, 35), (101.5, 34.5), (103, 34.2)], 1.3), ([(99.5, 31.5), (101, 30.5), (101.8, 29.0)], 1.5), ([(110.5, 26.2), (112, 25.5), (113.6, 25.3)], 0.9)]
HUANGHE_OLD = [(113.55, 34.95), (114.2, 35.2), (114.9, 35.65), (115.3, 36.1), (115.6, 36.6), (116.1, 37.1), (116.6, 37.6), (117.1, 38.1), (117.6, 38.5)]   # 汉代黄河下游走北边
HONGGOU = [(113.48, 34.86), (113.9, 34.78), (114.35, 34.74), (114.65, 34.25), (114.9, 33.7), (115.3, 33.2), (115.8, 32.9)]


def river_filter(nm, p0, p1):      # 今黄河下游（东经 113.6 以东）画细，换成上面的古河道
    return 'thin' if 'Huang' in nm and (p0[0] > 113.6 or p1[0] > 113.6) else None


W = World(dict(bbox=(98, 127, 24, 43), px_per_deg=116, sides=SIDES, cities=CITIES, flips=FLIPS, reach=(1.55, 2.6), ranges=RANGES,
               main_rivers=('Chang Jiang', 'Yangtze', 'Huang'), major_rivers=('Han', 'Huai', 'Wei', 'Gan', 'Xiang', 'Fen', 'Jialing', 'Min'), river_filter=river_filter,
               extra_rivers=[dict(pts=HUANGHE_OLD, width=6.5), dict(pts=HONGGOU, width=4.5, dash=True, ink=(0.05, 0.04, 0.04), gold=(1.0, 0.9, 0.6))]),
          os.path.join(ROOT, 'data'))

# ================================================================ 地图镜头数据
ARMIES = [
    dict(n='刘邦', o=H_, path=[(T_A, 107.0, 33.1, 8), (b(.7), 107.4, 34.3, 8), (b(1.6), 108.9, 34.45, 12), (b(2.6), 110.9, 34.6, 18), (b(3.4), 112.4, 34.72, 28), (b(4.4), 113.4, 34.8, 38),
                                (b(5.4), 114.6, 34.9, 48), (b(6.3), 115.7, 34.85, 56), (b(7.3), 117.0, 34.3, 56), (R1, 117.0, 34.3, 56), (R1 + 1.2, 115.7, 34.5, 20), (R1 + 2.5, 113.25, 34.72, 8),
                                (E1 + .6, 113.3, 34.78, 16), (35.8, 114.85, 34.1, 20), (36.6, 114.85, 33.98, 14), (38.5, 114.9, 33.8, 20), (40.3, 116.85, 33.42, 22), (99, 116.85, 33.42, 22)],
         rout=[(R1, R1 + 2.6), (36.5, 37.4)], tags=[(b(5.6), R1 + .4, '56万')]),
    dict(n='项羽', o=C_, cav=1, path=[(b(8.3), 118.7, 35.6, 3), (b(8.8), 117.2, 35.55, 3), (R1 - .05, 117.1, 34.3, 3), (R1 + .6, 117.15, 34.27, 3), (R1 + 1.7, 115.6, 34.55, 3), (R1 + 2.9, 113.82, 34.9, 4),
                                       (HP + 2, 113.82, 34.9, 10), (E1 + .3, 113.82, 34.9, 10), (34.6, 114.6, 34.3, 10), (36.3, 114.95, 33.86, 10), (37.6, 115.9, 33.6, 10), (39.0, 117.55, 33.3, 10),
                                       (M5 - .01, 117.55, 33.3, 10), (M5, 117.55, 33.22, .08), (M5 + .75, 117.5, 32.9, .08), (M5 + 1.4, 117.45, 32.55, .011), (M5 + 2.25, 117.95, 32.3, .0028),
                                       (M5 + 3.3, 118.45, 31.87, .0028), (99, 118.45, 31.87, .0028)],
         rout=[(W0 - .3, W0)], die=W0, tags=[(b(8.3), R1 + 3.2, '3万骑'), (38.6, S0, '约10万'), (M5, M5 + 1.35, '800骑'), (M5 + 1.35, M5 + 2.2, '百余骑'), (M5 + 2.2, W0, '28骑')]),
    dict(n='韩信', o=H_, path=[(HP + .5 * BAR, 113.1, 34.95, 3), (HP + .5 * BAR + .4, 111.3, 35.15, 3), (HP + .5 * BAR + 1.0, 112.5, 37.6, 3), (J0, 113.7, 38.0, 3), (J1, 114.3, 37.9, 3),
                                (J1 + .3, 114.75, 37.0, 5), (WS0, 118.9, 36.6, 8), (WS1, 119.45, 36.5, 9), (33.0, 119.2, 36.5, 30), (37.0, 118.3, 35.6, 30), (38.2, 117.3, 34.4, 30),
                                (40.0, 117.8, 33.65, 30), (99, 117.8, 33.65, 30)], tags=[(HP + .5 * BAR, WS0, '数万'), (36.6, S0, '30万')]),
    dict(n='陈馀', o=N_, path=[(HP + .5 * BAR + .9, 114.5, 37.95, 14), (99, 114.5, 37.95, 14)], rout=[(J1, J1 + .6)], tags=[(HP, J1 + .3, '号称20万')], die=J1 + .6),
    dict(n='龙且', o=C_, path=[(J1 + .15, 117.3, 34.5, 14), (WS0, 119.85, 36.3, 14), (99, 119.85, 36.3, 14)], rout=[(WS1, WS1 + .5)], tags=[(J1, WS1 + .3, '号称20万')], die=WS1 + .5),
    dict(n='彭越', o=H_, path=[(WS1 + .4, 115.95, 35.5, 3), (38.0, 115.95, 35.5, 3), (39.8, 117.2, 33.78, 3), (99, 117.2, 33.78, 3)]),
    dict(n='英布', o=H_, path=[(36.0, 116.5, 31.8, 3), (37.5, 116.8, 32.6, 3), (39.9, 117.3, 32.98, 3), (99, 117.3, 32.98, 3)])]
ARROWS = [
    (T_A + .2, b(1.4), b(3.2), H_, 15, [(107.03, 33.07), (107.0, 33.8), (107.37, 34.35), (108.7, 34.35), (109.23, 34.7)]),
    (b(2.3), b(4.4), D1, H_, 16, [(109.3, 34.65), (110.9, 34.58), (112.45, 34.72), (113.38, 34.8)]),
    (b(4.5), b(7.4), D1, H_, 18, [(113.4, 34.8), (114.35, 34.86), (115.57, 35.0), (116.4, 34.6), (117.12, 34.3)]),
    (b(8.45), D1, R1 + 2.2, C_, 15, [(118.83, 35.58), (117.0, 35.6), (116.6, 34.95), (116.93, 34.2), (117.15, 34.27)]),
    (R1 + .5, R1 + 2.9, E1 - .3, C_, 19, [(117.1, 34.3), (116.1, 34.55), (115.2, 34.75), (114.4, 34.95), (113.74, 34.87)]),
    (HP + .5 * BAR + .1, J0, E1 - .3, H_, 14, [(113.1, 34.95), (111.25, 35.2), (111.7, 36.3), (112.6, 37.5), (113.7, 38.05)]),
    (J1, WS0, E1 - .3, H_, 13, [(114.3, 37.9), (114.7, 36.9), (116.4, 37.25), (118.0, 36.85), (118.9, 36.6)]),
    (J1 + .15, WS0, WS1 + .6, C_, 12, [(117.3, 34.5), (118.2, 35.4), (119.3, 36.0), (119.8, 36.25)]),
    (WS1 + .5, WS1 + 1.1, E1 - .3, H_, 9, [(115.95, 35.35), (115.9, 34.95), (116.15, 34.6)]),
    (34.0, 38.9, S0, C_, 14, [(113.8, 34.85), (114.6, 34.3), (114.95, 33.86), (115.9, 33.6), (117.45, 33.32)]),
    (35.0, 40.2, S0, H_, 13, [(113.5, 34.75), (114.8, 34.12), (114.9, 33.78), (116.8, 33.44)]),
    (37.0, 40.0, S0, H_, 15, [(119.1, 36.4), (118.3, 35.6), (117.3, 34.4), (117.75, 33.7)]),
    (38.0, 39.9, S0, H_, 9, [(116.0, 35.3), (116.8, 34.4), (117.2, 33.85)]),
    (37.5, 39.9, S0, H_, 9, [(116.55, 31.9), (116.8, 32.6), (117.28, 32.95)]),
    (M5 + .1, M5 + 3.3, W0, C_, 7, [(117.55, 33.25), (117.5, 32.9), (117.45, 32.55), (117.95, 32.3), (118.45, 31.9)])]
GV = (113.6, 33.9, 0.62, 0)          # 全局垂直俯视：开局、转折、结尾都回到这里看全局占地
CAMSEG = [
    [(T_A,) + GV, (T_A + .8,) + GV, (T_A + 1.7, 107.8, 33.8, 1.7, 1), (b(2.7), 110.3, 34.6, 1.5, 1), (b(4.4), 113.0, 34.8, 1.45, 1), (b(7.4), 116.5, 34.55, 1.55, 1), (D1, 117.0, 34.6, 1.9, 1)],
    [(R1, 117.0, 34.6, 1.42, 1), (R1 + .7, 116.9, 34.6, 1.5, 1), (R1 + 1.8, 115.4, 34.75, 1.45, 1), (R1 + 2.9, 113.9, 34.95, 1.6, 1), (R1 + 3.5,) + GV, (HP,) + GV],
    [(HP + .5 * BAR, 112.4, 35.4, 1.4, 1), (J0, 113.4, 37.6, 1.5, 1)],
    [(J1, 114.3, 37.6, 1.4, 1), (WS0, 117.6, 36.7, 1.3, 1)],
    [(WS1, 118.6, 36.4, 1.4, 1), (WS1 + .55,) + GV, (E1 - .1, 113.6, 34.3, 0.68, 0), (34.7, 114.6, 34.2, 1.5, 1), (36.6, 114.9, 33.95, 1.65, 1), (38.4, 116.3, 33.95, 1.12, 1), (G0, 117.35, 33.5, 1.5, 1)],
    [(G1, 117.5, 33.4, 1.5, 1), (S0, 117.55, 33.35, 1.8, 1)],
    [(M5, 117.55, 33.2, 1.7, 1), (M5 + 1.3, 117.5, 32.65, 1.9, 1), (M5 + 2.3, 117.9, 32.3, 2.0, 1), (W0, 118.4, 31.95, 2.25, 1)],
    [(F0, 116.6, 32.7, 1.2, 1), (F0 + 1.0,) + GV, (T_END + 1,) + GV]]
DATES = [(T_A, '汉元年 八月', '前206年'), (b(2.3), '汉二年 十月', '前206年'), (b(3.1), '汉二年 三月', '前205年'), (b(5.0), '汉二年 四月', '前205年'), (R1 + 3.2, '汉二年 五月', '前205年'),
         (HP, '汉二年 九月', '前205年'), (J1, '汉三年 十月', '前205年'), (J1 + .45, '汉四年 十月', '前204年'), (WS1, '汉四年 十一月', '前204年'), (HG0, '汉四年 九月', '前203年'),
         (E1 + .1, '汉五年 十月', '前203年'), (38.3, '汉五年 十二月', '前202年'), (F0, '汉五年 二月', '前202年')]
CARDS = [(T_A + .15, b(2.25), '暗度陈仓', '汉王刘邦出陈仓 还定三秦'), (b(2.45), b(4.85), '东出函谷', '魏、河南、韩、殷 望风而降'), (b(5.05), D1 - .95, '直取彭城', '诸侯联军 五十六万'),
         (R1, R1 + 3.4, '彭城之战', '项羽三万精骑 大破五十六万', 'slam'), (R1 + 3.5, HP, '天下形势', '诸侯倒向项羽 刘邦退守荥阳'), (HP + .5 * BAR, J0, '韩信北伐', '灭魏 · 破代'),
         (J1, WS0 - .02, '赵燕归汉', '韩信挥师东进 击齐'), (WS1, HG0 - .03, '北线尽取', '魏、代、赵、燕、齐 尽归汉'), (HG0, E1 - .88, '楚河汉界', '以鸿沟为界 中分天下'),
         (E1 - .85, E1 - .05, '汉王背约', '张良、陈平：此天亡楚之时也'), (E1 + .1, 36.4, '追击', '项羽引兵东归 汉军尾随'), (36.5, 38.2, '固陵', '韩信、彭越不至 汉军大败'),
         (38.3, G0, '垓下', '韩信、彭越、英布 三路会师'), (G1, S0, '四面楚歌', '夜闻汉军四面皆楚歌'), (M5, W0, '突围', '项羽夜率八百骑 溃围南走'), (F0 + .9, 99, '汉', '前202年 刘邦即皇帝位', 'huge')]


def style_at(t):                       # 夜里发生的段落（四面楚歌 → 夜突围）用夜色，其余宣纸
    return 'night' if G0 <= t < W0 else 'ink'


def ground_fx(ms, c, t, Sp, st):       # 鸿沟：楚河汉界时描一道粗墨
    if HG0 <= t < E1 + 0.4:
        a = ease((t - HG0) / 0.2) * (1 - ease((t - E1) / 0.4)); pts = [Sp(*p)[:2] for p in HONGGOU]
        for wd, al in ((30, 0.18), (15, 0.45), (7, 1.0)):
            c.set_source_rgba(0.08, 0.06, 0.06, al * a); c.set_line_width(wd); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(*pts[0])
            for p in pts[1:]: c.line_to(*p)
            c.stroke()


def post(frame, t, st):
    if D1 - 0.9 < t < D1:              # 重拍前半拍压暗去色，留给"而项羽，只带了三万骑兵"
        dk = ease((t - (D1 - 0.9)) / 0.8); g = frame.mean(-1, keepdims=True); frame = (frame * (1 - 0.6 * dk) + g * 0.6 * dk) * (1 - 0.62 * dk)
    if G1 <= t < S0:                   # 四面楚歌：再压暗、偏冷
        dk = ease((t - G1) / 0.6); frame = frame * (1 - 0.35 * dk) * np.float32([0.88, 0.95, 1.12])
    return frame


def overlay(ms, X, t, Sp, st, tilt):
    T = X.T; tint = ms.tint
    if HG0 <= t < E1:
        a = ease((t - HG0) / 0.2); hx, hy, _ = Sp(114.6, 34.3)
        T('汉', hx - 380, hy - 40, 260, fill=tint(H_), stroke=12, a=a * 0.92); T('楚', hx + 380, hy - 40, 260, fill=tint(C_, 0.8, 1.7), stroke=12, a=a * 0.92)
    if D1 - 0.85 <= t < D1: T('而项羽，只带了三万骑兵', SW / 2, 968, 70, fill=(255, 240, 215), stroke=7, halo=(10, 8, 8), a=ease((t - (D1 - 0.85)) / 0.2))
    if R1 + 1.08 <= t < R1 + 3.4:
        lt = t - R1 - 1.08; a = ease(lt / 0.1) * (1 - ease((t - R1 - 3.25) / 0.15))
        T('3 万', 300, 500, 190 * (1 + 0.4 * (1 - eout(lt / 0.15))), fill=tint(C_, 0.85, 1), stroke=9, a=a); T('破 56 万', 300, 650, 86, fill=tint(H_, 0.8, 1), stroke=7, a=a * ease((lt - 0.43) / 0.12))
    if M5 + 1.35 <= t < W0:
        big = '28 骑' if t >= M5 + 2.2 else '百余骑'; l2 = t - (M5 + 2.2 if big == '28 骑' else M5 + 1.35)
        T(big, 320, 520, 180 * (1 + 0.4 * (1 - eout(l2 / 0.15))), fill=tint(C_, 0.85, 1.4), stroke=9, a=ease(l2 / 0.1)); T('十万 → ' + big.replace(' ', ''), 320, 665, 60, stroke=6, a=ease((l2 - .2) / .15))
    if F0 + 1.6 <= t: T('楚汉争霸 · 战局推演', 520, 760, 54, stroke=6, a=ease((t - F0 - 1.6) / 0.3))


def top(ms, img, t):
    if t >= F0 + 1.2: img = CH.paste(img, A('liubang.png'), 1500, 1075, 900, ease((t - F0 - 1.2) / 0.3), dx=(1 - eout((t - F0 - 1.2) / 0.35)) * 300)
    return img


MS = MapShot(W, dict(style=style_at, camseg=CAMSEG, armies=ARMIES, arrows=ARROWS, dates=DATES, cards=CARDS,
                     shakes=[(R1, 20), (R1 + BEAT, 8), (R1 + 2 * BEAT, 8), (R1 + 4 * BEAT, 8), (J1, 14), (WS1, 14), (M5, 14), (G1, 10), (F0 + .25, 10)],
                     flashes=[T_A, R1, HP + .5 * BAR, J1, WS1, G1, M5, F0],
                     fires=[(117.1, 34.32, R1, R1 + 2.4), (113.6, 34.86, R1 + 2.7, R1 + 3.4), (114.9, 33.92, 36.4, 37.4), (117.55, 33.32, 39.6, S0)],
                     regions=[('巴蜀', 105.3, 30.9), ('汉中', 107.0, 32.6), ('关中', 108.6, 35.0), ('河东', 111.4, 36.1), ('赵', 114.7, 37.6), ('齐', 118.7, 36.4), ('梁', 115.5, 35.0),
                              ('楚', 117.7, 33.3), ('江东', 120.0, 30.7), ('九江', 116.5, 31.5), ('临江', 112.3, 30.3)],
                     keycity={'栎阳', '彭城', '荥阳', '洛阳', '邯郸', '临淄', '垓下', '乌江', '南郑', '成都'},
                     hud=dict(share=True, order=[H_, N_, Q_, C_], note='势力范围按城池归属推算，为示意'),
                     ground_fx=ground_fx, post=post, overlay=overlay, top=top))


def map_shot(lt, dur, t): return MS.frame(t)


# ================================================================ 人物镜头
def opening(lt, dur, t):
    h1, h2 = 3.45, 4.0
    frame = CH.cover(A('hongmen_bg.png'), 1.0 + 0.05 * lt / dur + (0.05 * math.exp(-(lt - h1) * 6) if lt >= h1 else 0)) * (0.9 if lt < h1 else 0.6) * (ease(lt / 0.25) * 0.5 + 0.5)
    img = to_img(frame); pz = 1 + (0.06 * math.exp(-(lt - h1) * 7) if lt >= h1 else 0)
    if lt > 0.25: img = CH.paste(img, A('xiangyu.png'), 500, 1070, 930 * pz, ease((lt - 0.25) / 0.08), dx=-(1 - eout((lt - 0.25) / 0.22)) * 380, halo=0.45)
    if lt > 1.1: img = CH.paste(img, A('liubang.png'), 1430, 1070, 900 * pz, ease((lt - 1.1) / 0.08), dx=(1 - eout((lt - 1.1) / 0.22)) * 380, halo=0.45)
    arr = np.asarray(img).astype(np.float32) / 255
    for h_ in (0.25, 1.1): arr += np.float32([1.0, 0.9, 0.7]) * 0.3 * math.exp(-max(0, lt - h_) * 12) * (lt >= h_)
    for h_ in (h1, h2): arr += np.float32([1.0, 0.93, 0.8]) * 0.6 * math.exp(-max(0, lt - h_) * 10) * (lt >= h_)
    arr = arr * (1 - 0.5 * VR) + grain(); X = Txt(True)
    if 0.25 < lt < h2: X.V('项羽', 150, 330, 150, fill=(130, 195, 255), stroke=9, a=ease((lt - 0.3) / 0.1))
    if 1.1 < lt < h2: X.V('刘邦', SW - 150, 330, 150, fill=(255, 140, 105), stroke=9, a=ease((lt - 1.15) / 0.1))
    if lt < 2.1: X.T('前206年 · 秦亡，项羽分封十八诸侯', SW / 2, 968, 62, stroke=7, a=ease((lt - 0.4) / 0.2) * (1 - ease((lt - 1.95) / 0.15)))
    elif lt < h1: X.T('刘邦被封到巴蜀汉中，他不甘心', SW / 2, 968, 62, stroke=7, a=ease((lt - 2.15) / 0.2))
    if h1 <= lt < h2:
        l1 = lt - h1; X.T('楚', 610, 470, 330 * (1 + 0.5 * (1 - eout(l1 / 0.14))), fill=(130, 195, 255), stroke=12, a=ease(l1 / 0.05)); X.T('汉', 1310, 470, 330 * (1 + 0.5 * (1 - eout(l1 / 0.14))), fill=(255, 120, 90), stroke=12, a=ease(l1 / 0.05))
    if lt >= h2:
        sz = 300 * (1 + 0.6 * (1 - eout((lt - h2) / 0.16))); X.T('楚汉争霸', SW / 2 + 7, 477, sz, fill=(200, 40, 20), stroke=0, a=0.9); X.T('楚汉争霸', SW / 2, 470, sz, fill=(255, 226, 150), stroke=12)
    return X.over(to_img(arr))


PORTRAITS = {'xiangyu': ('项羽', '西楚霸王', -1, (150, 205, 255)), 'hanxin': ('韩信', '汉大将军 · 兵仙', -1, (255, 165, 125)), 'yuji': ('霸王别姬', '虞兮虞兮奈若何', 1, (255, 236, 200))}


def portrait(who):
    def shot(lt, dur, t):
        name, sub, side, col = PORTRAITS[who]; quiet = who == 'yuji'; frame = CH.ink_bg().copy() * (0.8 if quiet else 1)
        if not quiet:
            import cv2; e = math.exp(-lt / 0.12)
            frame = cv2.warpAffine(frame, np.float32([[1.06, 0, -0.03 * SW + 26 * e * math.sin(lt * 85)], [0, 1.06, -0.03 * SH + 22 * e * math.sin(lt * 67 + 1)]]), (SW, SH), borderMode=cv2.BORDER_REFLECT)
        h = 1010 * (1 + 0.05 * lt / dur); cx = SW / 2 + side * 330
        img = CH.paste(to_img(frame), A(who + '.png'), cx, 1060 if quiet else 1065, h, ease(lt / (0.7 if quiet else 0.06)), dx=0 if quiet else side * (1 - eout(lt / 0.2)) * 420, halo=0.55 if quiet else 0.5)
        arr = np.asarray(img).astype(np.float32) / 255 * (1 - 0.4 * VR) + (0 if quiet else np.float32([1.0, 0.95, 0.85]) * 0.5 * math.exp(-lt * 11)) + grain()
        if quiet: arr *= ease(lt / 0.5)
        X = Txt(True); tx = SW / 2 - side * 520
        if quiet: X.V(name, tx, 250, 150, fill=col, stroke=9, a=ease((lt - 0.5) / 0.5)); X.T(sub, tx, 930, 60, stroke=6, a=ease((lt - 1.0) / 0.5))
        else: X.V(name, tx, 330, 290 * (1 + 0.5 * (1 - eout(lt / 0.14))), fill=col, stroke=12, a=ease(lt / 0.06)); X.T(sub, tx, 900, 70, stroke=7, a=ease((lt - 0.2) / 0.12))
        return X.over(to_img(arr))
    return shot


def wujiang(lt, dur, t):
    k = lt / dur; frame = CH.cover(A('wujiang_bg.png'), 1.02 + 0.06 * k, 0.5 + 0.2 * k, 0.5)
    arr = np.asarray(CH.paste(to_img(frame), A('wujiang.png'), 1120 - 40 * k, 1068, 860, ease(lt / 0.5), halo=0.25)).astype(np.float32) / 255
    red = ease((lt - 2 * BAR) / 1.2); g = arr.mean(-1, keepdims=True); arr = arr * (1 - 0.35 * red) + g * np.float32([1.12, 0.82, 0.78]) * 0.35 * red
    arr = arr * (1 - 0.5 * VR) * ease(lt / 0.4) + grain(0.03)
    if lt > dur - 0.35: arr = arr + ease((lt - (dur - 0.35)) / 0.35) * 0.9
    X = Txt(False); seg = int(lt // BAR); l_ = lt - seg * BAR
    if seg == 0: X.V('乌江', 300, 330, 220 * (1 + 0.4 * (1 - eout(l_ / 0.16))), fill=(150, 28, 18), stroke=10, a=ease(l_ / 0.08)); X.T('只剩二十八骑，退到江边', SW / 2, 968, 66, stroke=7, a=ease((l_ - .2) / .2))
    elif seg == 1:
        X.T('“天之亡我，我何渡为！”', SW / 2 - 300, 300, 92, fill=(150, 28, 18), stroke=9, a=ease(l_ / 0.12)); X.T('——《史记·项羽本纪》', SW / 2 - 110, 400, 40, stroke=5, a=ease((l_ - .3) / .2))
        X.T('亭长备船相迎，他不肯过江', SW / 2, 968, 66, stroke=7, a=ease((l_ - .15) / .2))
    else: X.V('自刎', 300, 360, 250 * (1 + 0.4 * (1 - eout(l_ / 0.16))), fill=(150, 28, 18), stroke=11, a=ease(l_ / 0.08)); X.T('汉五年十二月 · 前202年  项羽，时年三十一', SW / 2, 968, 62, stroke=7, a=ease((l_ - .2) / .2))
    return X.over(to_img(arr))


# ================================================================ 俯视战场
RED_T, BLUE_T, INK_T = (160, 26, 18), (22, 46, 100), (22, 18, 16)
COLS = {'H': (0.77, 0.10, 0.12), 'C': (0.10, 0.20, 0.42), 'Z': (0.15, 0.13, 0.12)}
SD = {k: F.side_cols(v, 'ink') for k, v in COLS.items()}; SD['Z'] = ((0.15, 0.13, 0.12), (0.55, 0.50, 0.44))       # 赵军：墨色身体浅头
SDN = {k: F.side_cols(v, 'night') for k, v in {'H': (0.98, 0.33, 0.18), 'C': (0.30, 0.55, 1.0)}.items()}
_B = {}


def card_titles(X, lt, big, place, date, x0=1775):
    X.V(big, x0, 330, 128 * (1 + 0.45 * (1 - eout(lt / 0.16))), fill=X.ACC if X.dark else RED_T, stroke=8, a=ease(lt / 0.08))
    X.T(place, 250, 110, 120, fill=X.TXT, stroke=8, a=ease(lt / .1)); X.T(date, 250, 195, 40, stroke=5, a=ease((lt - .15) / .15))


def wedge(key, night, texts, rows, nreg, seed, speed):
    def shot(lt, dur, t):
        if key not in _B: _B[key] = F.Wedge(rows, nreg, dur, seed, speed=speed)
        Bw = _B[key]; st = 'night' if night else 'ink'; surf, c = F.canvas(); e = math.exp(-lt / 0.13); k = lt / dur; z = 1.42 - 0.2 * k; cxm = 620 + 760 * ease(k)
        c.translate(SW / 2 + 22 * e * math.sin(lt * 85) + 5 * math.sin(lt * 31), SH / 2 + 22 * e * math.sin(lt * 67 + 1) + 5 * math.sin(lt * 37)); c.rotate(-0.06 + 0.03 * k); c.scale(z, z); c.translate(-cxm, -560)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        if key == 'pengcheng':      # 汉军营地临泗水：右侧河 + 营帐被冲翻
            rc = (0.30, 0.42, 0.52); g = cairo.LinearGradient(1990, 0, 2350, 0); g.add_color_stop_rgba(0, *rc, 0); g.add_color_stop_rgba(0.3, *rc, 0.8); g.add_color_stop_rgba(1, *rc, 0.9)
            c.set_source(g); c.move_to(1990, -400); c.curve_to(1930, 300, 2080, 700, 2010, 1500); c.line_to(2700, 1500); c.line_to(2700, -400); c.close_path(); c.fill()
            tip = Bw.frames[min(len(Bw.frames) - 1, int(round(lt * 30)))]['tip']
            for (tx, ty) in Bw.camps: F.camp(c, tx, ty, st, 0.6 * (tip > tx - 40 and abs(ty - 560) < 60 + (tip - tx) * 0.4))
        sd = SDN if night else SD
        fr = Bw.draw(c, lt, sd['H'], sd['C'], st)
        x, y = fr['tip'], 560; c.set_source_rgba(*((0.16, 0.46, 0.95) if night else (0.10, 0.20, 0.42)), 1); c.move_to(x - 8, y - 12); c.line_to(x - 70, y - 34 + 5 * math.sin(lt * 30)); c.line_to(x - 60, y - 10); c.close_path(); c.fill()
        X = Txt(night); big, sub, low = texts; sc_ = 1 + 0.5 * (1 - eout(lt / 0.16))
        X.T(big, 500, 250, 170 * sc_, fill=(130, 195, 255) if night else BLUE_T, stroke=10, a=ease(lt / 0.08)); X.T(sub, 500, 382, 54, stroke=6, a=ease((lt - 0.2) / 0.15))
        if lt > 2 * BEAT: l2 = lt - 2 * BEAT; X.T(low, SW / 2, 968, 76 * (1 + 0.3 * (1 - eout(l2 / 0.14))), fill=(255, 130, 95) if night else RED_T, stroke=8, a=ease(l2 / 0.08))
        return F.finish(surf, lt, X, st)
    return shot


def jingxing(lt, dur, t, tF=None):          # 背水阵 + 轻骑袭营拔旗（tF=骑兵换旗的时刻）
    tF = BAR if tF is None else tF; mk = F.mk
    if 'jx' not in _B:
        U = []; pr = lambda x0, x1, y: [(0, x0, y), (0.8, x1, y), (tF, x1 - 18, y), (tF + .25, x1 + 40, y), (dur, x1 + 420, y)]
        hp = lambda x: [(0, x, 560), (0.8, x, 560), (tF, x - 26, 560), (tF + .3, x, 560), (dur, x + 190, 560)]
        U.append(mk('shield', 'H', 640, 560, 2, 34, seed=1, path=hp(640), face=[(0, 0)], cas=[(0, 0), (.7, 0), (tF, .16), (dur, .2)], order='front'))
        U.append(mk('spear', 'H', 588, 560, 3, 34, seed=2, path=hp(588), face=[(0, 0)], cas=[(0, 0), (1.0, 0), (tF, .06), (dur, .08)]))
        U.append(mk('bow', 'H', 520, 560, 2, 30, seed=3, path=hp(520), face=[(0, 0)]))
        U.append(mk('cav', 'H', 0, 0, 6, 4, sp=42, seed=4, path=[(0, 700, 1040), (0.6, 1150, 1010), (1.15, 1620, 930), (tF - .08, 1800, 640), (dur, 1790, 580)]))
        for k, (x0, y) in enumerate([(1180, 250), (1180, 560), (1180, 870), (1360, 400), (1360, 720)]):
            U.append(mk('spear', 'Z', x0, y, 7, 10, seed=10 + k, path=pr(x0, 760 + (x0 - 1180) * 0.75, y), face=[(0, math.pi)], cas=[(0, 0), (.8, 0), (tF, .12), (dur, .45)], scat=[(0, 0), (tF + .15, 0), (dur, 230)], order='front'))
        for k, y in enumerate((300, 800)):
            U.append(mk('bow', 'Z', 1520, y, 3, 12, seed=20 + k, path=pr(1520, 1060, y), face=[(0, math.pi)], scat=[(0, 0), (tF + .15, 0), (dur, 260)], cas=[(0, 0), (tF, 0), (dur, .3)]))
        U.append(mk('cav', 'Z', 1300, 70, 6, 3, sp=40, seed=30, path=[(0, 1300, 70), (0.8, 900, 110), (tF, 880, 120), (dur, 1500, -60)], cas=[(0, 0), (tF, 0), (dur, .3)]))
        _B['jx'] = F.Battle(U, dur)
    cam = F.FCam([(0, 880, 560, 1.1), (0.9, 940, 560, 1.06), (tF - .2, 1330, 600, 1.12), (tF + .2, 1330, 600, 1.12), (dur, 1010, 560, 0.94)], lt, [(0, 16), (tF, 22)])
    surf, c = F.canvas(); cam.apply(c)
    F.river(c, [(250 + 40 * math.sin(k * 0.8), -300 + k * 170) for k in range(11)], 330, lt)
    c.set_source_rgba(0.35, 0.28, 0.2, 0.9); c.set_line_width(7); c.set_dash([16, 7]); c.rectangle(1660, 420, 260, 300); c.stroke(); c.set_dash([])        # 赵营
    for k in range(5): F.camp(c, 1705 + (k % 3) * 80, 480 + (k // 3) * 130)
    for k in range(8):
        fl = lt >= tF + k * 0.03; F.banner(c, 1670 + (k % 4) * 78, 440 + (k // 4) * 260, COLS['H'] if fl else COLS['Z'], lt + k, 1.25 * (1 + 0.5 * math.exp(-(lt - tF - k * 0.03) * 8) if fl else 1.0))
    F.volley(c, lt, 0.25, (1300, 560), (600, 560), 60, 3, COLS['Z'], (120, 520)); F.volley(c, lt, 0.55, (520, 560), (800, 560), 46, 9, COLS['H'], (60, 520))
    _B['jx'].draw(c, lt, SD); F.banner(c, 470, 560, COLS['H'], lt, 1.7)
    X = Txt(False); card_titles(X, lt, '背水一战', '井陉', '汉三年十月')
    X.T('汉军 数万 · 背水列阵', *cam.S(560, 900), 50, fill=RED_T, stroke=6, a=ease((lt - .2) / .15) * (1 - ease((lt - tF + .3) / .2)))
    X.T('赵军 号称二十万', *cam.S(1250, 80), 50, fill=INK_T, stroke=6, a=ease((lt - .35) / .15) * (1 - ease((lt - tF + .3) / .2)))
    X.slam('拔旗易帜', SW / 2 - 120, 300, 210, lt, tF, RED_T, 11)
    X.T('韩信背水列阵 赵军空营来攻' if lt < tF else '两千轻骑袭营换旗 赵军大乱', SW / 2, 968, 64, stroke=7, a=ease((lt - (0.2 if lt < tF else tF + .1)) / 0.15))
    return F.finish(surf, lt, X, 'ink', [tF])


def weishui(lt, dur, t, tF=None):           # 佯败诱敌 → 上游决水 → 半渡而击（tF=决水时刻）
    tF = BAR / 2 if tF is None else tF; mk = F.mk
    if 'ws' not in _B:
        U = []
        for k, y in enumerate((420, 700)): U.append(mk('spear', 'H', 0, 0, 5, 9, seed=40 + k, path=[(0, 1090, y), (tF * 0.81, 600, y), (dur, 640, y)], face=[(0, math.pi), (tF * 0.79, math.pi), (tF * 0.93, 0), (dur, 0)]))
        U.append(mk('shield', 'H', 0, 0, 2, 38, seed=43, path=[(0, 520, 560), (tF, 520, 560), (tF + .5, 640, 560), (dur, 690, 560)], face=[(0, 0)]))
        U.append(mk('bow', 'H', 0, 0, 2, 34, seed=44, path=[(0, 440, 560), (tF, 440, 560), (dur, 520, 560)], face=[(0, 0)]))
        for k, (y0, y1) in enumerate(((130, 300), (990, 820))): U.append(mk('cav', 'H', 0, 0, 5, 4, sp=42, seed=46 + k, path=[(0, 480, y0), (tF, 480, y0), (tF + .5, 830, y0), (tF + 1.0, 880, y1), (dur, 860, y1)]))
        for k, y in enumerate((440, 680)): U.append(mk('spear', 'C', 0, 0, 7, 10, seed=50 + k, path=[(0, 1380, y), (tF * 0.87, 800, y), (dur, 780, 560 + (y - 560) * 0.8)], face=[(0, math.pi)], cas=[(0, 0), (tF + .3, 0), (dur, .92)], scat=[(0, 0), (tF + .4, 0), (dur, 40)]))
        for k, y in enumerate((340, 560, 780)): U.append(mk('spear' if k != 1 else 'shield', 'C', 0, 0, 6, 9, seed=55 + k, path=[(0, 1620, y), (tF, 1010, y), (tF + .7, 1030, y + 760), (dur, 1040, y + 900)], face=[(0, math.pi)], cas=[(0, 0), (tF, 0), (tF + .5, 1)], scat=[(0, 0), (tF, 0), (tF + .5, 120)]))
        for k, y in enumerate((300, 560, 820)): U.append(mk('bow' if k == 1 else 'spear', 'C', 0, 0, 6, 9, seed=60 + k, path=[(0, 1900, y), (tF, 1300, y), (tF + .5, 1310, y), (dur, 1750, y)], face=[(0, math.pi)], scat=[(0, 0), (tF + .5, 0), (dur, 240)], cas=[(0, 0), (tF + .6, 0), (dur, .2)]))
        _B['ws'] = F.Battle(U, dur)
    cam = F.FCam([(0, 1060, 560, 1.0), (tF, 980, 560, 1.04), (dur, 900, 560, 1.12)], lt, [(0, 14), (tF, 24)])
    surf, c = F.canvas(); cam.apply(c)
    yf = -400 + (lt - tF) / 0.4 * 1900 if lt >= tF else -9999; pts = [(1010 + 26 * math.sin(k * 0.9), -400 + k * 110) for k in range(18)]
    F.river(c, pts, lambda i: 300 if pts[i][1] < yf else 74, lt * (3 if lt >= tF else 1))
    if lt >= tF and yf < 1500: c.set_source_rgba(0.96, 0.97, 0.97, 0.9); c.set_line_width(26); c.move_to(860, yf - 20); c.curve_to(940, yf + 50, 1080, yf + 50, 1160, yf - 20); c.stroke()
    if lt < tF:
        c.set_source_rgba(0.45, 0.33, 0.2, 1)
        for k in range(9): c.arc(940 + k * 18, -120 + (k % 2) * 10, 11, 0, TAU); c.fill()
    F.volley(c, lt, tF + .15, (440, 560), (800, 560), 60, 5, COLS['H'], (60, 560))
    fr = _B['ws'].draw(c, lt, SD); F.banner(c, 400, 560, COLS['H'], lt, 1.7)
    if lt < tF + .9: x_, y_ = fr[8]['c']; F.banner(c, x_ + 40, y_ + 120, COLS['C'], lt, 1.5)
    X = Txt(False); card_titles(X, lt, '潍水之战', '潍水', '汉四年十一月')
    X.T('龙且 号称二十万', *cam.S(1500, 150), 50, fill=BLUE_T, stroke=6, a=ease((lt - .15) / .15) * (1 - ease((lt - tF - .6) / .2)))
    X.slam('决水！', SW / 2 + 40, 300, 240, lt, tF, BLUE_T, 12, hold=0.8); X.slam('半渡而击', 420, 330, 150, lt, tF + .86, RED_T, 10)
    X.T('韩信佯败 引楚军渡河' if lt < tF else '上游决壅放水 楚军被截为两段', SW / 2, 968, 64, stroke=7, a=ease((lt - (0.15 if lt < tF else tF + .1)) / 0.15))
    return F.finish(surf, lt, X, 'ink', [tF])


def gaixia_ring(lt, dur, t):       # 夜：层层合围（Ring）
    if 'ring' not in _B: _B['ring'] = F.Ring()
    k = lt / dur; surf, c = F.canvas(); e = math.exp(-lt / 0.13); hits = [n * BAR / 2 for n in range(1, 4)]; pz = sum(0.03 * math.exp(-(lt - h) * 7) for h in hits if lt >= h)
    z = 0.78 + 0.34 * ease(k) + pz
    c.translate(SW / 2 + 18 * e * math.sin(lt * 85), SH / 2 + 18 * e * math.sin(lt * 67 + 1)); c.rotate(0.05 - 0.1 * k); c.scale(z, z); c.translate(-960, -560); c.set_line_cap(cairo.LINE_CAP_ROUND)
    _B['ring'].draw(c, k, lt, SDN['C'], SDN['H']); c.set_source_rgba(1.0, 0.95, 0.8, 1); c.arc(960, 560, 9, 0, TAU); c.fill()
    X = Txt(True); sc_ = 1 + 0.5 * (1 - eout(lt / 0.16))
    X.V('十面埋伏', 1775, 330, 128 * sc_, fill=(255, 210, 120), stroke=8, a=ease(lt / 0.08))
    X.T('垓下', 330, 230, 190 * sc_, fill=(255, 226, 150), stroke=10, a=ease(lt / 0.08)); X.T('汉五年十二月 · 前202', 330, 360, 46, stroke=5, a=ease((lt - 0.2) / 0.15))
    if lt > BAR / 2: l2 = lt - BAR / 2; X.T('韩信将三十万', 330, 470, 84 * (1 + 0.3 * (1 - eout(l2 / 0.14))), fill=(255, 130, 95), stroke=8, a=ease(l2 / 0.08))
    if lt > BAR: l2 = lt - BAR; X.T('楚军 约十万', 330, 575, 84 * (1 + 0.3 * (1 - eout(l2 / 0.14))), fill=(130, 195, 255), stroke=8, a=ease(l2 / 0.08))
    X.T('汉军层层合围 楚军兵少食尽', SW / 2, 968, 64, stroke=7, a=ease((lt - 0.3) / 0.2))
    return F.finish(surf, lt, X, 'night', hits)


def gaixia_layers(lt, dur, t):     # 另一种打法（全水墨版本里用的）：《高祖本纪》的多层阵——先合不利 → 两翼纵击 → 复乘之
    q_ = dur / 4; T1, T2, T3 = q_, 2 * q_, 3 * q_; mk = F.mk
    if 'g2' not in _B:
        U = []; cx = lambda d: [(0, 690 + d, 560), (T1, 840 + d, 560), (T2, 1040 + d, 560), (T3, 1050 + d, 560), (dur, 880 + d, 560)]
        ccas = [(0, 0), (T1 - .2, 0), (T2, .08), (T3, .3), (dur, .78)]; csc = [(0, 0), (T3, 0), (dur, 90)]
        U.append(mk('shield', 'C', 0, 0, 2, 26, seed=70, path=cx(70), face=[(0, 0)], cas=ccas, scat=csc, order='front'))
        U.append(mk('spear', 'C', 0, 0, 6, 26, seed=71, path=cx(0), face=[(0, 0)], cas=ccas, scat=csc))
        U.append(mk('bow', 'C', 0, 0, 2, 22, seed=72, path=cx(-80), face=[(0, 0)], cas=[(0, 0), (T3, .05), (dur, .6)], scat=csc))
        for k, y in enumerate((300, 820)):
            U.append(mk('cav', 'C', 0, 0, 4, 3, sp=42, seed=73 + k, path=[(0, 660, y), (T1, 820, y), (T2, 1060, y), (T3, 1040, y + (60 if k == 0 else -60)), (dur, 900, 560)], cas=[(0, 0), (T2, 0), (T3, .4), (dur, .9)]))
        hx = lambda d: [(0, 1330 + d, 0), (T1, 1010 + d, 0), (T2, 1330 + d, 0), (T3, 1330 + d, 0), (dur, 1110 + d, 0)]
        for k, y in enumerate((330, 560, 790)):
            U.append(mk('shield', 'H', 0, 0, 2, 12, seed=80 + k, path=[(t_, x_ - 75, y) for (t_, x_, _) in hx(0)], face=[(0, math.pi)], cas=[(0, 0), (T1 - .2, 0), (T2, .3), (dur, .34)], order='front'))
            U.append(mk('spear', 'H', 0, 0, 6, 12, seed=83 + k, path=[(t_, x_, y) for (t_, x_, _) in hx(0)], face=[(0, math.pi)], cas=[(0, 0), (T1, 0), (T2, .1), (dur, .12)]))
            U.append(mk('bow', 'H', 0, 0, 2, 11, seed=86 + k, path=[(t_, x_ + 85, y) for (t_, x_, _) in hx(0)], face=[(0, math.pi)]))
        for k, (y0, y1, a1) in enumerate(((90, 255, 2.2), (1030, 865, -2.2))):
            U.append(mk('spear', 'H', 0, 0, 6, 14, seed=90 + k, path=[(0, 1280, y0), (T2, 1280, y0), (T3, 1030, y1), (dur, 960, y1 + (40 if k == 0 else -40))], face=[(0, math.pi), (T2, math.pi), (T2 + .4, a1), (dur, a1)]))
            U.append(mk('cav', 'H', 0, 0, 5, 3, sp=42, seed=92 + k, path=[(0, 1500, y0 - (30 if k == 0 else -30)), (T2, 1500, y0), (T3, 900, y0 + (30 if k == 0 else -30)), (dur, 620, 560 + (y1 - 560) * 0.55)]))
        U.append(mk('spear', 'H', 0, 0, 5, 18, seed=95, path=[(0, 1660, 560), (T3, 1640, 560), (dur, 1520, 560)], face=[(0, math.pi)]))
        U.append(mk('chariot', 'H', 0, 0, 1, 5, sp=64, seed=96, path=[(0, 1770, 560), (T3, 1750, 560), (dur, 1630, 560)], face=[(0, math.pi)]))
        U.append(mk('spear', 'H', 0, 0, 4, 16, seed=97, path=[(0, 1900, 560), (dur, 1800, 560)], face=[(0, math.pi)]))
        _B['g2'] = F.Battle(U, dur)
    cam = F.FCam([(0, 1080, 560, 0.9), (T2, 1120, 560, 0.9), (dur, 1000, 560, 0.98)], lt, [(0, 16), (T1, 12), (T2, 12), (T3, 20)])
    surf, c = F.canvas(); cam.apply(c)
    F.volley(c, lt, 0.1, (1420, 560), (860, 560), 70, 11, COLS['H'], (60, 600)); F.volley(c, lt, 0.2, (610, 560), (1000, 560), 50, 12, COLS['C'], (60, 420)); F.volley(c, lt, T3 + .05, (1200, 560), (950, 560), 70, 13, COLS['H'], (60, 600))
    fr = _B['g2'].draw(c, lt, SD)
    x_, y_ = fr[1]['c']; F.banner(c, x_ - 30, y_, COLS['C'], lt, 1.8); x_, y_ = fr[8]['c']; F.banner(c, x_ + 60, y_, COLS['H'], lt, 1.8); F.banner(c, 1700, 560, COLS['H'], lt, 1.5)
    X = Txt(False); X.V('垓下之战', 1790, 330, 128 * (1 + 0.45 * (1 - eout(lt / 0.16))), fill=RED_T, stroke=8, a=ease(lt / 0.08))
    lab = lambda txt, wx, wy, col, a=1.0, sz=44: X.T(txt, *cam.S(wx, wy), sz, fill=col, stroke=6, a=a); a0 = ease((lt - .15) / .15)
    lab('项羽 约十万', fr[1]['c'][0] - 40, 230, BLUE_T, a0, 52); lab('韩信 三十万', fr[8]['c'][0] + 250, 440, RED_T, a0, 52)
    lab('孔将军', fr[14]['c'][0] + 150, fr[14]['c'][1] - 10, RED_T, a0); lab('费将军', fr[16]['c'][0] + 150, fr[16]['c'][1] + 10, RED_T, a0); lab('汉王', 1690, 330, RED_T, a0)
    caps = [(0, '韩信先合'), (T1, '不利，却'), (T2, '孔、费两翼纵击'), (T3, '韩信复乘之 · 楚军大败')]
    k = max(i for i, (t0, _) in enumerate(caps) if lt >= t0); l2 = lt - caps[k][0]
    X.T(caps[k][1], SW / 2, 962, 76 * (1 + 0.3 * (1 - eout(l2 / 0.14))), fill=RED_T if k != 1 else BLUE_T, stroke=8, a=ease(l2 / 0.07))
    X.T('阵型据《史记·高祖本纪》，为示意', 40, SH - 30, 24, fill=X.SUB, anchor='lm', stroke=3)
    return F.finish(surf, lt, X, 'ink', [T1, T2, T3])


# ================================================================ 片
SHOTS = [(0, T_A, opening), (T_A, D1, map_shot), (D1, D1 + BAR / 2, portrait('xiangyu')),
         (D1 + BAR / 2, R1, wedge('pengcheng', False, ('三万精骑', '项羽 · 拂晓自西突入', '汉军五十六万  溃'), 15, 17, 5, 2250)),
         (R1, HP, map_shot), (HP, HP + BAR / 2, portrait('hanxin')), (HP + BAR / 2, J0, map_shot), (J0, J1, jingxing), (J1, WS0, map_shot), (WS0, WS1, weishui),
         (WS1, G0, map_shot), (G0, G1, gaixia_ring), (G1, S0, map_shot), (S0, D2, portrait('yuji')),
         (D2, M5, wedge('breakout', True, ('八百骑', '项羽 · 乘夜溃围南走', '汉骑五千 追之'), 7, 22, 8, 2500)),
         (M5, W0, map_shot), (W0, F0, wujiang), (F0, T_END, map_shot)]

ALT = {'gaixia_layers': (G0, G0 + 4 * BAR, gaixia_layers)}      # 没用进片里的备选镜头：python scenario.py alt gaixia_layers out_dir 1.0 3.5 5.5

if __name__ == '__main__':
    from mapwar.film import Film
    if len(sys.argv) > 2 and sys.argv[1] == 'alt':
        t0, t1, fn = ALT[sys.argv[2]]; os.makedirs(sys.argv[3], exist_ok=True)
        for x in sys.argv[4:]: fn(float(x), t1 - t0, t0 + float(x)).save(os.path.join(sys.argv[3], f'{sys.argv[2]}_{float(x):.2f}.jpg'), quality=92)
    else: Film(SHOTS, T_END, audio=os.environ.get('MAPWAR_AUDIO')).cli()
