"""《谁惹了蒙古》角色库：在工具包的 Q 版骨架上加蒙古皮帽、缠头、王冠、幞头。"""
import sys, math
KIT = '/home/ubuntu/kunyang/zhanju-kit'
if KIT not in sys.path: sys.path.insert(0, KIT)
import cairo
from mapwar import qrig as RG
from mapwar.qdraw import lin, rad, poly, rrect, gold_metal, head_path
OL = (0.09, 0.08, 0.08); TAU = 2 * math.pi


def _fs(c, src, lw):
    if isinstance(src, tuple): c.set_source_rgb(*src)
    else: c.set_source(src)
    c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(lw); c.stroke()


def _dome(c, R, shape, cut, col, k=1.07):
    c.save(); c.rectangle(-2 * R, -2 * R, 4 * R, cut * R); c.clip(); head_path(c, 0, -0.03 * R, R, shape, k)
    _fs(c, rad(-0.3 * R, -0.8 * R, 0.05 * R, 1.3 * R, [(0, tuple(min(1, v * 1.25) for v in col)), (1, tuple(v * 0.7 for v in col))]), 0.05 * R); c.restore()


def _fur(c, R, y, x0, x1, col, h=0.30):
    n = int((x1 - x0) / 0.24) + 1
    for i in range(n):
        x = x0 + (x1 - x0) * i / max(1, n - 1); c.arc(x * R, y * R, h * 0.62 * R, 0, TAU); _fs(c, col, 0.04 * R)
    c.rectangle(x0 * R, (y - h * 0.42) * R, (x1 - x0) * R, h * 0.84 * R); c.set_source_rgb(*col); c.fill()
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(0.025 * R)
    for i in range(n * 2): x = x0 + (x1 - x0) * (i + 0.5) / (n * 2); c.move_to(x * R, (y - 0.1) * R); c.line_to((x + 0.05) * R, (y + 0.12) * R); c.stroke()


def _gear(c, R, spec, P, t):
    g = spec.get('gear'); shape = spec.get('head', 'round'); hc = spec.get('hatcol', (0.70, 0.13, 0.10)); fur = spec.get('fur', (0.42, 0.28, 0.16))
    if g == 'mongol':                                   # 尖顶皮帽 + 护耳 + 红缨
        if spec.get('_front'):
            for k in (-1, 1): poly(c, [(k * 0.86 * R, -0.45 * R), (k * 1.16 * R, -0.45 * R), (k * 1.12 * R, 0.42 * R), (k * 0.93 * R, 0.42 * R)]); _fs(c, tuple(v * 0.85 for v in fur), 0.045 * R)
        else: poly(c, [(-1.08 * R, -0.45 * R), (-0.95 * R, 0.55 * R), (-0.45 * R, 0.45 * R), (-0.5 * R, -0.45 * R)]); _fs(c, tuple(v * 0.85 for v in fur), 0.045 * R)
        poly(c, [(-0.95 * R, -0.5 * R), (-0.1 * R, -1.62 * R), (0.2 * R, -1.62 * R), (1.0 * R, -0.5 * R)])
        _fs(c, lin(-R, 0, R, 0, [(0, tuple(v * 0.7 for v in hc)), (0.6, hc), (1, tuple(min(1, v * 1.2) for v in hc))]), 0.05 * R)
        _fur(c, R, -0.50, -1.02, 1.05, fur)
        c.arc(0.05 * R, -1.7 * R, 0.13 * R, 0, TAU); _fs(c, gold_metal(-0.1 * R, -1.8 * R, 0.2 * R, -1.6 * R), 0.035 * R)
        for k in range(5):
            sw = 0.08 * R * math.sin(t * 8 + k); c.move_to(0.02 * R, -1.75 * R); c.curve_to(-0.25 * R, -2.0 * R, -0.6 * R + sw, -1.9 * R, -0.75 * R + sw - k * 0.04 * R, -1.5 * R + k * 0.05 * R)
            c.set_source_rgb(0.85, 0.12, 0.08); c.set_line_width(0.05 * R); c.stroke()
        return True
    if g == 'turban':                                   # 缠头
        tc = spec.get('hatcol', (0.95, 0.93, 0.88))
        c.save(); c.translate(0, -0.72 * R); c.scale(1.22, 0.70); c.arc(0, 0, R, 0, TAU); c.restore()
        _fs(c, rad(0.2 * R, -1.0 * R, 0.05 * R, 1.4 * R, [(0, tuple(min(1, v * 1.05) for v in tc)), (1, tuple(v * 0.72 for v in tc))]), 0.05 * R)
        c.save(); c.translate(0, -0.72 * R); c.scale(1.22, 0.70); c.arc(0, 0, R, 0, TAU); c.restore(); c.save(); c.clip()
        c.set_source_rgba(0, 0, 0, 0.22); c.set_line_width(0.035 * R)
        for k in range(-3, 5): c.move_to((-1.3 + k * 0.3) * R, -0.25 * R); c.curve_to((-0.6 + k * 0.3) * R, -0.7 * R, (0.0 + k * 0.3) * R, -1.1 * R, (0.9 + k * 0.3) * R, -1.5 * R); c.stroke()
        c.restore()
        jx = 0.0 if spec.get('_front') else 0.55 * R
        c.arc(jx, -0.78 * R, 0.15 * R, 0, TAU); _fs(c, rad(jx - 0.03 * R, -0.82 * R, 0.01 * R, 0.16 * R, [(0, (1, 0.6, 0.6)), (1, spec.get('jewel', (0.75, 0.08, 0.10)))]), 0.035 * R)
        if spec.get('plume_t'):
            c.move_to(0.55 * R, -0.92 * R); c.curve_to(0.5 * R, -1.6 * R, 0.75 * R, -1.9 * R, 1.0 * R, -1.95 * R); c.curve_to(0.85 * R, -1.6 * R, 0.8 * R, -1.3 * R, 0.68 * R, -0.92 * R); c.close_path(); _fs(c, (0.98, 0.96, 0.9), 0.035 * R)
        return True
    if g == 'crown':                                    # 罗斯王公：皮边金冠 + 十字
        _dome(c, R, shape, 1.55, (0.90, 0.70, 0.22), 1.08)
        for k in (-0.5, 0.0, 0.5): c.arc(k * R, -0.82 * R, 0.09 * R, 0, TAU); _fs(c, ((0.75, 0.1, 0.1), (0.2, 0.5, 0.8), (0.15, 0.6, 0.35))[int(k * 2) % 3], 0.03 * R)
        _fur(c, R, -0.48, -1.05, 1.08, fur, 0.34)
        c.set_source_rgb(*OL); c.set_line_width(0.16 * R); c.move_to(0, -1.08 * R); c.line_to(0, -1.62 * R); c.move_to(-0.2 * R, -1.42 * R); c.line_to(0.2 * R, -1.42 * R); c.stroke()
        c.set_source(gold_metal(-0.2 * R, -1.6 * R, 0.2 * R, -1.1 * R)); c.set_line_width(0.08 * R); c.move_to(0, -1.08 * R); c.line_to(0, -1.6 * R); c.move_to(-0.18 * R, -1.42 * R); c.line_to(0.18 * R, -1.42 * R); c.stroke()
        return True
    if g == 'futou':                                    # 金使：展脚幞头
        for k in (-1, 1):
            w = 0.05 * R * math.sin(t * 9 + k); rrect(c, (0.55 * k - (0.95 if k < 0 else 0)) * R, -0.95 * R + w, 0.95 * R, 0.16 * R, 0.07 * R); _fs(c, (0.08, 0.08, 0.09), 0.035 * R)
        _dome(c, R, shape, 1.62, (0.10, 0.10, 0.12), 1.06)
        rrect(c, -0.5 * R, -1.42 * R, 0.85 * R, 0.5 * R, 0.14 * R); _fs(c, (0.10, 0.10, 0.12), 0.045 * R)
        c.move_to(-0.98 * R, -0.42 * R); c.line_to(1.02 * R, -0.42 * R); c.set_source(gold_metal(0, -0.46 * R, 0, -0.38 * R)); c.set_line_width(0.07 * R); c.stroke()
        return True
    return False


_orig = RG.headgear
def _patched(c, R, spec, P, t):
    if not _gear(c, R, spec, P, t): _orig(c, R, spec, P, t)
RG.headgear = _patched

SK = (0.96, 0.84, 0.70)
TMZ = dict(head='square', gear='mongol', hatcol=(0.72, 0.12, 0.10), beard='goatee', brow_w=1.6, robe=(0.20, 0.30, 0.52), collar=(0.92, 0.74, 0.30), belt=(0.70, 0.14, 0.10), trim=(0.92, 0.74, 0.30), weapon=None, skin=(0.93, 0.78, 0.62))      # 铁木真 / 成吉思汗
MGK = dict(head='wide', gear='mongol', hatcol=(0.93, 0.72, 0.20), fur=(0.90, 0.88, 0.82), beard='hang', brow_w=1.7, robe=(0.82, 0.60, 0.14), collar=(0.60, 0.10, 0.08), belt=(0.60, 0.10, 0.08), trim=(0.60, 0.10, 0.08), emblem=True, weapon=None, skin=(0.93, 0.78, 0.62))  # 蒙哥
MGB = dict(head='round', gear='mongol', hatcol=(0.72, 0.12, 0.10), robe=(0.50, 0.34, 0.20), collar=(0.72, 0.12, 0.10), belt=(0.25, 0.16, 0.10), weapon=None, skin=(0.94, 0.80, 0.64))                                # 蒙古兵 / 使者
MGB2 = dict(MGB, robe=(0.34, 0.42, 0.30), beard='long')
MGB3 = dict(MGB, robe=(0.46, 0.26, 0.30), beard='long', head='square')
JSZ = dict(head='round', gear='futou', beard='goatee', robe=(0.62, 0.16, 0.14), collar=(0.95, 0.90, 0.80), belt=(0.92, 0.74, 0.30), emblem=True, weapon='scroll', skin=SK)                                             # 金国使者
JB = dict(head='round', gear='han', tabard='金', armor=(0.80, 0.62, 0.16), limb=(0.58, 0.44, 0.10), weapon='spear', pauldron=False, rim=(0.5, 0.36, 0.1), skin=SK)                                                     # 金兵
SB = dict(head='round', gear='han', tabard='宋', armor=(0.16, 0.42, 0.62), limb=(0.12, 0.30, 0.46), weapon='spear', pauldron=False, rim=(0.6, 0.75, 0.9), skin=SK)                                                     # 宋兵
SJ = dict(head='wide', gear='turban', hatcol=(0.93, 0.92, 0.86), jewel=(0.10, 0.55, 0.35), beard='goatee', brow_w=1.4, robe=(0.14, 0.46, 0.34), collar=(0.92, 0.74, 0.30), belt=(0.92, 0.74, 0.30), trim=(0.92, 0.74, 0.30), weapon=None, skin=(0.84, 0.66, 0.50))   # 讹答剌守将
WG = dict(head='square', gear='crown', fur=(0.36, 0.22, 0.12), beard='wild', beardcol=(0.72, 0.52, 0.22), browcol=(0.62, 0.44, 0.18), brow_w=1.7, armor=(0.62, 0.66, 0.72), limb=(0.40, 0.42, 0.50), cape=(0.70, 0.10, 0.10), weapon='sword', rim=(0.9, 0.9, 0.95), skin=(0.98, 0.86, 0.78))   # 罗斯王公
WG2 = dict(WG, head='round', beardcol=(0.45, 0.28, 0.14), browcol=(0.4, 0.25, 0.12), cape=(0.18, 0.30, 0.55))
HLF = dict(head='round', gear='turban', hatcol=(0.97, 0.95, 0.90), jewel=(0.80, 0.10, 0.12), plume_t=True, beard='long', brow_w=1.5, robe=(0.13, 0.12, 0.15), collar=(0.92, 0.74, 0.30), belt=(0.92, 0.74, 0.30), trim=(0.92, 0.74, 0.30), emblem=True, weapon=None, skin=(0.86, 0.68, 0.52))   # 哈里发（阿拔斯尚黑）
CAST = dict(铁木真=TMZ, 蒙哥=MGK, 蒙古兵=MGB, 金使=JSZ, 金兵=JB, 守将=SJ, 罗斯王公=WG, 哈里发=HLF, 宋兵=SB, 使者乙=MGB2)
