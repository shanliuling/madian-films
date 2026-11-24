"""heraldry — 冰火系列的家徽：按原著描述自己画的彩窗风格，全系列共用这一套。
    rgb, a = sigil('stark', px=256)                 # 预乘 RGB + alpha，float32；shape='shield' 盾 | 'round' 圆章（名字旁）| 'banner' 旗（地图上）
    a = charge('stark', px=256)                     # 只要图案的剪影（藏进画面里用）
    rgb, a = wave(rgb, a, t)                        # 让旗飘起来
    HOUSES['stark'] → zh / motto / main / sub / field / ink / acc
python heraldry.py 出一张总览 out/_sigils.jpg。要加新家族：写一个 _xxx(c, P) 画图案，在 HOUSES 和 DRAW 里各加一行。"""
import math, os, sys, numpy as np, cv2, cairo
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'engine'))
def hx(s): s = s.lstrip('#'); return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))
HOUSES = dict(
    stark=dict(zh='史塔克', motto='凛冬将至', main='#8A9099', sub='#E8EEF2', field='#E4EAEF', ink='#6B727C', acc='#C8D6E2'),
    lannister=dict(zh='兰尼斯特', motto='听我怒吼', main='#9B1B1E', sub='#D9A441', field='#9B1B1E', ink='#E2AE45', acc='#B8201E'),
    baratheon=dict(zh='拜拉席恩', motto='怒火燎原', main='#E0B43C', sub='#15130F', field='#E0B43C', ink='#15130F', acc='#E0B43C'),
    tully=dict(zh='徒利', motto='家族，责任，荣誉', main='#2F5D8C', sub='#8E2B2B', field='#2F5D8C', ink='#D5DAE0', acc='#8E2B2B'),
    arryn=dict(zh='艾林', motto='高如荣耀', main='#6FA8DC', sub='#F2F4F7', field='#5E9BD4', ink='#F2F4F7', acc='#5E9BD4'),
    bolton=dict(zh='波顿', motto='吾刃锋利', main='#D99AA5', sub='#8C1C1C', field='#D99AA5', ink='#A01A1A', acc='#5E1012'),
    frey=dict(zh='佛雷', motto='', main='#A9AEB5', sub='#2B4C7E', field='#B4B9C0', ink='#2B4C7E', acc='#B4B9C0'),
    stannis=dict(zh='史坦尼斯', motto='', main='#E3B92F', sub='#B3261E', field='#E6BE34', ink='#15130F', acc='#C22A1C'),
    greyjoy=dict(zh='葛雷乔伊', motto='强取胜于苦耕', main='#15130F', sub='#E0B43C', field='#15130F', ink='#E0B43C', acc='#15130F'),
    joffrey=dict(zh='乔佛里', motto='', main='#9B1B1E', sub='#D9A441', field='#E0B43C', ink='#15130F', acc='#9B1B1E'),
    baelish=dict(zh='贝里席', motto='', main='#2E5D45', sub='#C9CED4', field='#254E3A', ink='#CFD4D9', acc='#8E969E'),
)
LEAD = np.float32((0.035, 0.03, 0.035))
# ---------------- 画笔：都在 [-1, 1] 的单位坐标里画
def _src(c, col): c.set_source_rgb(*(hx(col) if isinstance(col, str) else col))
def _poly(c, pts):
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.close_path(); c.fill()
def _blob(c, x, y, rx, ry, rot=0.0): c.save(); c.translate(x, y); c.rotate(rot); c.scale(rx, ry); c.arc(0, 0, 1, 0, math.tau); c.restore(); c.fill()
def _spline(pts, n=14):
    P = np.float32(pts); P = np.vstack([P[0], P, P[-1]]); out = []
    for i in range(1, len(P) - 2):
        for u in np.linspace(0, 1, n, endpoint=False): out.append(0.5 * ((2 * P[i]) + (-P[i - 1] + P[i + 1]) * u + (2 * P[i - 1] - 5 * P[i] + 4 * P[i + 1] - P[i + 2]) * u * u + (-P[i - 1] + 3 * P[i] - 3 * P[i + 1] + P[i + 2]) * u ** 3))
    out.append(P[-1]); return np.float32(out)
def _tube(c, pts, r):
    """沿一条平滑曲线画一根粗细会变的管子：pts = [(x, y), ...]，r = 每个点的半径（或一个数）。腿、尾巴、脖子、鱼身都用它。"""
    q = _spline([(x, y, rr) for (x, y), rr in zip(pts, r if isinstance(r, (list, tuple)) else [r] * len(pts))])
    for i in range(len(q)):
        c.arc(q[i][0], q[i][1], max(1e-3, q[i][2]), 0, math.tau); c.fill()
        if i:
            (x0, y0, r0), (x1, y1, r1) = q[i - 1], q[i]; d = math.hypot(x1 - x0, y1 - y0) or 1e-6; nx, ny = -(y1 - y0) / d, (x1 - x0) / d
            _poly(c, [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1), (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)])
def _smooth(c, pts):
    q = _spline(list(pts) + [pts[0]]); _poly(c, [tuple(p) for p in q])
def _crown(c, x, y, w, h, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); _poly(c, [(-w, 0), (-w * 1.15, -h), (-w * 0.55, -h * 0.45), (0, -h * 1.15), (w * 0.55, -h * 0.45), (w * 1.15, -h), (w, 0)]); c.restore()
# ---------------- 图案
def _cs(c, pts, n=10):
    """闭合轮廓：点是 (x, y)，第三个值给 1 的是尖角，其余用平滑曲线连起来。"""
    P = [(p[0], p[1], len(p) > 2) for p in pts]; k = next((i for i, p in enumerate(P) if p[2]), 0); P = P[k:] + P[:k] + [P[k]]; runs = []; cur = [P[0]]
    for p in P[1:]:
        cur.append(p)
        if p[2]: runs.append(cur); cur = [p]
    if len(cur) > 1: runs.append(cur)
    c.move_to(P[0][0], P[0][1])
    for r in runs:
        for (x, y) in (_spline([(p[0], p[1]) for p in r], n) if len(r) > 2 else [(p[0], p[1]) for p in r]): c.line_to(float(x), float(y))
    c.close_path(); c.fill()
def _lock(c, bx, by, tx, ty, w, bend=0.0, edge=None):
    """一绺毛 / 一根爪：从根 (bx, by) 到尖 (tx, ty)，根部半宽 w，bend 是往一侧弯多少；edge 给颜色就再描一圈边。"""
    d = math.hypot(tx - bx, ty - by) or 1e-6; ux, uy = (tx - bx) / d, (ty - by) / d; nx, ny = -uy, ux; mx, my = bx + ux * d * .55 + nx * bend * d, by + uy * d * .55 + ny * bend * d
    c.move_to(bx + nx * w, by + ny * w); c.curve_to(bx + ux * d * .25 + nx * w, by + uy * d * .25 + ny * w, mx + nx * w * .55, my + ny * w * .55, tx, ty)
    c.curve_to(mx - nx * w * .55, my - ny * w * .55, bx + ux * d * .25 - nx * w, by + uy * d * .25 - ny * w, bx - nx * w, by - ny * w); c.close_path()
    if edge is None: c.fill(); return
    col = c.get_source(); c.fill_preserve(); _src(c, edge); c.set_line_width(.011); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke(); c.set_source(col)
def _line(c, pts, w):
    q = _spline(pts) if len(pts) > 2 else pts; c.set_line_width(w); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND); c.move_to(float(q[0][0]), float(q[0][1]))
    for p in q[1:]: c.line_to(float(p[0]), float(p[1]))
    c.stroke()
def _wolf(c, P):                                    # 史塔克：灰色冰原狼（侧面狼头，龇牙，颈毛往后扬）
    ink = np.float32(hx(P['ink'])); dk = tuple(ink * .60); lt = tuple(ink * .45 + .55 * np.float32((.93, .95, .97))); ink = tuple(ink); c.save(); c.translate(-.03, .0); c.scale(.90, .90)
    _src(c, dk)                                                                           # 后层颈毛
    for q in ((.22, -.34, .66, -.60, .12, -.22), (.34, -.20, .88, -.36, .13, -.22), (.40, -.02, .96, -.04, .14, -.20), (.42, .18, .94, .32, .14, -.18), (.36, .36, .78, .66, .14, -.18), (.22, .46, .50, .92, .13, -.16), (.06, .50, .14, .96, .12, -.14), (-.10, .44, -.22, .84, .10, -.12)): _lock(c, *q)
    _cs(c, [(.14, -.46, 1), (.50, -.90, 1), (.50, -.32, 1)])                               # 后耳
    _src(c, ink)
    _cs(c, [(-.78, -.14, 1), (-.60, -.20), (-.44, -.25), (-.32, -.34), (-.20, -.44), (-.06, -.51), (.10, -.50), (.26, -.40), (.38, -.22), (.44, .0), (.42, .22), (.34, .40), (.20, .52), (.02, .56), (-.10, .52), (-.18, .44, 1),
            (-.30, .43), (-.46, .42), (-.60, .36), (-.67, .30, 1), (-.63, .20, 1), (-.48, .21), (-.30, .16), (-.11, .03, 1), (-.34, .03), (-.56, .04), (-.70, .06), (-.80, .02, 1), (-.84, -.06)])
    for q in ((.28, -.32, .76, -.48, .11, -.22), (.40, -.12, .90, -.20, .12, -.20), (.42, .08, .94, .14, .12, -.20), (.40, .28, .86, .50, .12, -.18), (.28, .42, .64, .80, .12, -.16), (.12, .50, .32, .96, .11, -.14), (-.02, .50, -.02, .92, .10, -.12)): _lock(c, *q)
    _cs(c, [(-.04, -.46, 1), (.22, -.98, 1), (.32, -.36, 1)])                              # 前耳
    _src(c, dk); _cs(c, [(.05, -.50, 1), (.20, -.84, 1), (.24, -.44, 1)])
    _src(c, lt)                                                                           # 脸颊的浅色鬃毛
    for q in ((-.04, -.06, .30, -.04, .09, .10), (-.02, .06, .32, .16, .10, .08), (-.04, .18, .24, .36, .10, .06), (-.10, .26, .08, .50, .09, .04)): _lock(c, *q)
    _cs(c, [(-.10, -.16), (.02, -.06), (.00, .20), (-.10, .32), (-.20, .22), (-.16, .04), (-.22, -.08)])
    _src(c, (.13, .04, .05)); _cs(c, [(-.11, .03, 1), (-.34, .03), (-.56, .04), (-.70, .06, 1), (-.63, .20, 1), (-.48, .21), (-.30, .16)])       # 嘴里
    _src(c, (.74, .13, .12)); _cs(c, [(-.16, .06), (-.32, .08), (-.46, .12), (-.50, .17), (-.42, .19), (-.28, .15), (-.16, .10)])
    _src(c, (.95, .96, .97))
    for (x, w, h) in ((-.635, .045, .15), (-.55, .028, .07), (-.48, .026, .06), (-.41, .026, .06), (-.34, .024, .05)): _cs(c, [(x - w, .045, 1), (x + w, .035, 1), (x + w * .2, .04 + h, 1)])
    for (x, w, h) in ((-.57, .04, .13), (-.49, .026, .06), (-.42, .026, .06), (-.35, .024, .05)): y = .21 + (x + .6) * -.12; _cs(c, [(x - w, y, 1), (x + w, y - .01, 1), (x - w * .2, y - h, 1)])
    _src(c, (.07, .07, .09)); _cs(c, [(-.78, -.14, 1), (-.69, -.13), (-.67, -.05), (-.72, .01), (-.80, .02, 1), (-.845, -.06)])                   # 鼻头
    _lock(c, -.36, -.215, -.06, -.39, .030, -.10)                                         # 眉
    _src(c, (.96, .93, .80)); _cs(c, [(-.33, -.185, 1), (-.24, -.26), (-.13, -.29, 1), (-.20, -.215)])
    _src(c, (.07, .07, .09)); _blob(c, -.222, -.238, .030, .034)
    _src(c, dk); _line(c, [(-.70, -.02), (-.52, -.06), (-.36, -.10)], .012); _line(c, [(-.10, -.40), (.04, -.30), (.12, -.14)], .012); _line(c, [(.20, -.10), (.34, .02), (.40, .20)], .012); _line(c, [(.16, .20), (.24, .34), (.22, .46)], .012)
    c.restore()
def _paw(c, x, y, ang, s, claw):
    """一只爪子：ang 是脚趾指的方向。"""
    col = c.get_source(); c.save(); c.translate(x, y); c.rotate(ang); _blob(c, 0, 0, s * 1.0, s * .80)
    for a in (-.66, -.22, .22, .66): c.save(); c.rotate(a); _blob(c, s * .95, 0, s * .70, s * .30); c.restore()
    _src(c, claw)
    for a in (-.66, -.22, .22, .66): c.save(); c.rotate(a); _lock(c, s * 1.50, 0, s * 2.45, s * .42, s * .17, .25); c.restore()
    c.restore(); c.set_source(col)
def _lion(c, P):                                    # 兰尼斯特：金色雄狮（直立、张口吐舌、四爪张开、尾巴上卷）
    ink = np.float32(hx(P['ink'])); dk = tuple(ink * .42 + np.float32((.04, .0, .0))); ink = tuple(ink); red = (.80, .12, .10); c.save(); c.translate(.03, .03); c.scale(.92, .92)
    _src(c, ink)
    _tube(c, [(.30, .44), (.52, .52), (.70, .36), (.72, .08), (.60, -.14), (.59, -.38), (.70, -.54)], [.062, .060, .056, .054, .050, .046, .044])                     # 尾巴
    for q in ((.69, -.50, .58, -.98, .105, .30), (.72, -.52, .86, -.86, .07, -.20), (.72, -.50, .90, -.62, .055, -.30), (.68, -.50, .48, -.70, .055, .35)): _lock(c, *q, edge=dk)
    _tube(c, [(.22, .38), (.32, .58), (.38, .72), (.32, .86)], [.20, .125, .08, .075]); _paw(c, .22, .92, math.pi, .09, dk)                                              # 后腿（后）
    _lock(c, .40, .62, .52, .80, .05, .2)
    _tube(c, [(.12, .42), (-.14, .46), (-.30, .60), (-.34, .76)], [.19, .135, .09, .078]); _paw(c, -.44, .85, math.pi * .92, .09, dk)                                     # 后腿（前）
    _lock(c, -.22, .52, -.14, .70, .05, -.2)
    _tube(c, [(-.10, -.24), (.03, .08), (.18, .38)], [.26, .155, .21])                                                                                                  # 身子
    _tube(c, [(-.14, -.02), (-.38, .06), (-.56, .10)], [.14, .10, .085]); _paw(c, -.67, .11, math.pi * 1.0, .092, dk); _lock(c, -.36, .12, -.34, .30, .05, .2)            # 前腿（下）
    _tube(c, [(-.16, -.26), (-.42, -.30), (-.58, -.35)], [.14, .10, .085]); _paw(c, -.69, -.37, math.pi * 1.08, .092, dk); _lock(c, -.40, -.22, -.38, -.06, .05, .2)     # 前腿（上）
    for q in ((-.04, -.16, .20, .10, .10, -.08), (.00, -.26, .30, -.08, .10, -.10), (.02, -.38, .36, -.26, .10, -.10), (.02, -.50, .38, -.46, .10, -.10), (.02, -.62, .36, -.66, .10, -.12), (.00, -.74, .30, -.84, .09, -.14), (-.06, -.84, .16, -.97, .08, -.15),
              (-.08, -.40, -.06, -.04, .08, .06), (-.16, -.44, -.20, -.12, .08, .08), (-.24, -.44, -.33, -.18, .07, .10),
              (-.10, -.24, .08, -.02, .08, -.06), (-.06, -.34, .18, -.20, .08, -.08), (-.04, -.46, .22, -.40, .08, -.10), (-.04, -.58, .22, -.58, .08, -.12), (-.04, -.70, .20, -.75, .08, -.14)): _lock(c, *q, edge=dk)   # 鬃毛：外一圈、胸前、里一圈
    _cs(c, [(-.30, -.915), (-.20, -.905), (-.06, -.80), (-.03, -.62), (-.10, -.49), (-.26, -.44), (-.45, -.44, 1), (-.48, -.51, 1), (-.26, -.585, 1), (-.44, -.64), (-.585, -.64, 1), (-.635, -.72), (-.58, -.795), (-.46, -.815), (-.38, -.865)])   # 头
    _blob(c, -.12, -.875, .062, .075, -.5)                                                # 耳
    _src(c, (.20, .05, .04)); _cs(c, [(-.26, -.585, 1), (-.44, -.64), (-.585, -.64, 1), (-.48, -.51, 1)])
    _src(c, red); _cs(c, [(-.30, -.59, 1), (-.44, -.585), (-.57, -.55), (-.66, -.47, 1), (-.56, -.50), (-.44, -.535), (-.30, -.55, 1)])             # 舌头
    _src(c, (.97, .95, .88))
    for (x, y, w, h, d) in ((-.545, -.642, .024, .075, 1), (-.47, -.640, .016, .04, 1), (-.40, -.632, .014, .03, 1), (-.455, -.515, .022, .065, -1), (-.39, -.535, .014, .03, -1)): _cs(c, [(x - w, y, 1), (x + w, y, 1), (x, y + h * d, 1)])
    _src(c, dk); _blob(c, -.605, -.735, .034, .032); _cs(c, [(-.44, -.775, 1), (-.37, -.81), (-.29, -.79, 1), (-.37, -.765)]); _lock(c, -.47, -.815, -.24, -.845, .020, -.25)
    _line(c, [(-.13, -.90), (-.11, -.85)], .014); _line(c, [(-.52, -.70), (-.42, -.70), (-.34, -.67)], .011); _line(c, [(.04, .06), (.13, .18), (.14, .34)], .012); _line(c, [(.22, .24), (.10, .36), (.08, .48)], .012); _line(c, [(.36, .42), (.36, .56)], .012); _line(c, [(-.22, -.06), (-.30, -.02)], .011)
    c.restore()
def _stag(c, P):                                    # 拜拉席恩：黑色宝冠雄鹿（直立，冠套在颈上）
    c.save(); c.translate(0, .07); c.scale(.92, .92); _src(c, P['ink'])
    _tube(c, [(-.08, -.10), (.06, .14), (.20, .38)], [.20, .165, .20]); _tube(c, [(-.08, -.14), (-.15, -.32), (-.20, -.50)], [.16, .10, .09])
    _tube(c, [(-.18, -.54), (-.30, -.50), (-.43, -.43)], [.09, .075, .05]); _poly(c, [(-.12, -.60), (.04, -.66), (-.04, -.50)])
    for (beam, tines) in (([(-.19, -.60), (-.08, -.76), (.10, -.86), (.30, -.84)], ((-.02, -.80, -.02, -1.02), (.12, -.86, .16, -1.04), (.28, -.84, .38, -.98))), ([(-.22, -.60), (-.30, -.74), (-.30, -.90), (-.22, -1.02)], ((-.29, -.76, -.42, -.86), (-.30, -.90, -.42, -1.00)))):
        _tube(c, beam, [.036, .032, .028, .014])
        for (x0, y0, x1, y1) in tines: _tube(c, [(x0, y0), ((x0 + x1) / 2 - .02, (y0 + y1) / 2), (x1, y1)], [.028, .022, .008])
    _tube(c, [(-.12, -.06), (-.40, -.16), (-.50, .00)], [.075, .042, .032]); _tube(c, [(-.06, .06), (-.34, .10), (-.46, .28)], [.075, .042, .032])
    _tube(c, [(.16, .44), (-.02, .60), (.12, .76), (.00, .92)], [.11, .052, .037, .034]); _tube(c, [(.26, .42), (.38, .60), (.30, .78), (.42, .92)], [.11, .052, .037, .034]); _tube(c, [(.36, .32), (.48, .26)], [.05, .02])
    for (x, y) in ((-.52, .03), (-.48, .31), (-.02, .95), (.44, .95)): _blob(c, x, y, .055, .038)
    _src(c, P['acc']); _blob(c, -.27, -.545, .022, .017); c.translate(-.125, -.24); c.rotate(-.40); c.rectangle(-.115, -.02, .23, .05); c.fill()
    for k in (-1, 0, 1): _poly(c, [(k * .075 - .035, -.02), (k * .075, -.10), (k * .075 + .035, -.02)])
    c.restore()
def _trout(c, P):                                   # 徒利：银色鳟鱼跃起
    _src(c, P['ink'])
    _poly(c, [(.22, .40), (.06, .78), (.26, .66), (.50, .82), (.40, .40)]); _poly(c, [(.06, -.56), (.34, -.62), (.40, -.30), (.24, -.34)]); _poly(c, [(-.14, -.26), (-.20, .02), (.02, -.14)]); _poly(c, [(.14, .10), (.02, .34), (.24, .26)])
    _tube(c, [(-.50, -.46), (-.22, -.52), (.08, -.36), (.26, -.06), (.32, .26), (.30, .48)], [.10, .19, .21, .19, .13, .07])
    _src(c, P['acc']); _poly(c, [(-.64, -.50), (-.44, -.47), (-.60, -.40)])
    _src(c, tuple(v * 0.55 for v in hx(P['ink']))); _blob(c, -.36, -.53, .03, .03)
    c.set_line_width(.02); c.arc(-.10, -.40, .19, math.radians(110), math.radians(235)); c.stroke()
    for (x, y) in ((.02, -.36), (.14, -.24), (.20, -.08), (.26, .08), (.08, -.22), (.16, -.04), (.26, .24)): c.arc(x, y, .05, math.radians(-60), math.radians(60)); c.stroke()
def _trout_field(c, P):
    for i in range(7):
        _src(c, P['field'] if i % 2 == 0 else P['acc']); y0 = -1.1 + i * .34; c.move_to(-1.2, y0)
        for k in range(13): x = -1.2 + k * .2; c.curve_to(x + .07, y0 - .09, x + .13, y0 + .09, x + .2, y0)
        c.line_to(1.2, 1.3); c.line_to(-1.2, 1.3); c.close_path(); c.fill()
def _bird(c):                                       # 展翅的鹰（正面，头朝左）
    for sx in (-1, 1): _poly(c, [(sx * .06, -.26), (sx * .22, -.56), (sx * .44, -.90), (sx * .46, -.62), (sx * .68, -.78), (sx * .60, -.48), (sx * .82, -.50), (sx * .64, -.30), (sx * .78, -.16), (sx * .58, -.12), (sx * .60, .04), (sx * .36, .00), (sx * .10, .06)])
    _tube(c, [(0, -.34), (0, -.06), (0, .22)], [.10, .13, .07]); _poly(c, [(-.07, .18), (-.22, .58), (-.08, .48), (0, .62), (.08, .48), (.22, .58), (.07, .18)])
    _blob(c, -.01, -.44, .09, .085); _poly(c, [(-.07, -.51), (-.22, -.47), (-.21, -.37), (-.15, -.42), (-.07, -.38)])
def _falcon(c, P):                                  # 艾林：白色新月和猎鹰
    _src(c, P['ink']); c.arc(0, .14, .66, 0, math.tau); c.fill(); _src(c, P['field']); c.arc(0, -.06, .62, 0, math.tau); c.fill()
    _src(c, P['ink']); c.save(); c.translate(0, -.02); c.scale(.74, .74); _bird(c); _src(c, P['field']); _blob(c, -.04, -.455, .02, .02); c.restore()
def _flayed(c, P):                                  # 波顿：红色剥皮人（倒吊在 X 形架上）
    _src(c, P['acc']); c.set_line_width(.085); c.set_line_cap(cairo.LINE_CAP_BUTT)
    for sx in (-1, 1): c.move_to(sx * .62, -.74); c.line_to(-sx * .62, .74); c.stroke()
    _src(c, P['ink']); _tube(c, [(0, -.14), (0, .08), (0, .30)], [.12, .11, .14]); _blob(c, 0, .50, .095, .11)
    for sx in (-1, 1):
        _tube(c, [(sx * .09, .28), (sx * .30, .44), (sx * .50, .62)], [.065, .05, .04]); _blob(c, sx * .54, .66, .05, .04, sx * .8)
        _tube(c, [(sx * .06, -.12), (sx * .26, -.40), (sx * .46, -.62)], [.085, .06, .045]); _blob(c, sx * .50, -.68, .045, .06, -sx * .7)
    _src(c, P['acc']); c.set_line_width(.016)
    for y in (-.06, .04, .14, .24): c.move_to(-.09, y); c.curve_to(-.03, y + .04, .03, y + .04, .09, y); c.stroke()
    c.move_to(0, -.14); c.line_to(0, .34); c.stroke(); _blob(c, -.035, .52, .018, .014); _blob(c, .035, .52, .018, .014)
def _towers(c, P):                                  # 佛雷：蓝色双塔，中间一座桥
    _src(c, P['ink'])
    for sx in (-1, 1):
        c.rectangle(sx * .44 - .17, -.42, .34, 1.02); c.fill()
        for k in (-1, 0, 1): c.rectangle(sx * .44 + k * .14 - .05, -.56, .10, .16); c.fill()
    c.rectangle(-.30, -.02, .60, .22); c.fill(); c.rectangle(-.30, -.10, .60, .05); c.fill()
    for k in range(-2, 3): c.rectangle(k * .11 - .03, -.16, .06, .08); c.fill()
    c.set_line_width(.035)
    for y in (.70, .80):
        c.move_to(-.66, y)
        for k in range(8): x = -.66 + k * .165; c.curve_to(x + .055, y - .05, x + .11, y + .05, x + .165, y)
        c.stroke()
    _src(c, P['field']); c.arc(0, .22, .15, math.pi, math.tau); c.fill()
    for sx in (-1, 1):
        for y in (-.26, .30): c.rectangle(sx * .44 - .025, y, .05, .16); c.fill()
def _heart(c, P):                                   # 史坦尼斯：燃烧的红心里一头黑色宝冠雄鹿
    c.save(); c.translate(0, .14); c.scale(.80, .80); _src(c, '#E2671F')
    for i in range(11):
        an = math.radians(-155 + i * 13); r = 1.06 if i % 2 == 0 else .82; bx, by = math.cos(an) * .36, -.10 + math.sin(an) * .36; px, py = -math.sin(an) * .16, math.cos(an) * .16
        c.move_to(bx - px, by - py); c.curve_to(bx - px * .2 + math.cos(an) * r * .5, by - py * .2 + math.sin(an) * r * .5, math.cos(an + .22) * r * .8, -.10 + math.sin(an + .22) * r * .8, math.cos(an + .10) * r, -.10 + math.sin(an + .10) * r); c.line_to(bx + px, by + py); c.close_path(); c.fill()
    _src(c, P['acc']); c.move_to(0, .70); c.curve_to(-.20, .52, -.64, .20, -.64, -.16); c.curve_to(-.64, -.50, -.16, -.58, 0, -.24); c.curve_to(.16, -.58, .64, -.50, .64, -.16); c.curve_to(.64, .20, .20, .52, 0, .70); c.fill()
    _src(c, P['ink']); _poly(c, [(-.085, -.02), (.085, -.02), (.05, .30), (0, .36), (-.05, .30)]); _poly(c, [(-.085, .00), (-.22, -.06), (-.10, .08)]); _poly(c, [(.085, .00), (.22, -.06), (.10, .08)])
    for sx in (-1, 1):
        _tube(c, [(sx * .06, -.02), (sx * .22, -.16), (sx * .30, -.34)], [.028, .024, .012])
        for (x, y) in ((.15, -.10), (.24, -.20)): _tube(c, [(sx * x, y), (sx * (x - .02), y - .12)], [.02, .008])
    _crown(c, 0, -.06, .075, .10); _src(c, P['acc']); _blob(c, -.04, .10, .014, .014); _blob(c, .04, .10, .014, .014); c.restore()
def _mock(c, P):                                    # 贝里席：银色仿声鸟（侧面，尾巴上翘）
    _src(c, P['ink'])
    _poly(c, [(.16, .06), (.50, -.30), (.74, -.62), (.62, -.24), (.80, -.36), (.56, -.06), (.30, .20)])
    _tube(c, [(-.30, -.22), (-.10, -.02), (.18, .14)], [.13, .20, .12]); _blob(c, -.34, -.34, .13, .125); _poly(c, [(-.44, -.42), (-.70, -.44), (-.46, -.34)]); _poly(c, [(-.45, -.31), (-.66, -.28), (-.44, -.26)])
    c.set_line_width(.03); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for x in (-.08, .06): c.move_to(x, .12); c.line_to(x - .02, .44); c.line_to(x - .12, .50); c.move_to(x - .02, .44); c.line_to(x + .08, .50); c.stroke()
    _tube(c, [(-.62, .56), (-.10, .50), (.46, .58)], [.03, .035, .02])
    _src(c, P['acc']); _poly(c, [(-.20, -.12), (.02, -.14), (.30, .04), (.46, .20), (.12, .14), (-.10, .06)])
    _src(c, P['field']); _blob(c, -.38, -.37, .028, .028)
def _kraken(c, P):                                  # 葛雷乔伊：金色海怪（尖头朝上，触手向两边卷开）
    c.save(); c.translate(0, -.02); _src(c, P['ink'])
    for sx in (-1, 1):
        for pts, r in (([(.10, .02), (.44, -.04), (.70, -.28), (.64, -.56), (.44, -.56), (.44, -.40)], [.085, .075, .06, .045, .032, .018]),
                       ([(.12, .14), (.50, .18), (.80, .08), (.88, -.12), (.74, -.18), (.70, -.06)], [.085, .07, .055, .04, .028, .016]),
                       ([(.12, .22), (.42, .44), (.70, .52), (.84, .36), (.72, .26), (.64, .36)], [.085, .07, .055, .04, .028, .016]),
                       ([(.08, .26), (.22, .58), (.44, .82), (.62, .76), (.58, .60), (.48, .66)], [.08, .065, .05, .038, .027, .015]),
                       ([(.03, .28), (.05, .60), (.14, .86), (.28, .94), (.32, .84)], [.07, .055, .04, .028, .015])):
            _tube(c, [(sx * x, y) for (x, y) in pts], r)
        _poly(c, [(sx * .14, -.52), (sx * .40, -.62), (sx * .17, -.76)])
    _cs(c, [(0, -.98, 1), (.13, -.74), (.21, -.44), (.25, -.10), (.22, .16), (.10, .30), (0, .33), (-.10, .30), (-.22, .16), (-.25, -.10), (-.21, -.44), (-.13, -.74)])
    _src(c, P['field'])
    for sx in (-1, 1): _blob(c, sx * .105, .06, .05, .062); _line(c, [(sx * .06, -.60), (sx * .10, -.36), (sx * .12, -.16)], .016)
    _src(c, P['ink'])
    for sx in (-1, 1): _blob(c, sx * .105, .07, .02, .034)
    c.restore()
def _joff_field(c, P): _src(c, P['acc']); c.rectangle(0, -1.3, 1.3, 2.6); c.fill()
def _joff(c, P):                                    # 乔佛里：左半金底黑鹿、右半红底金狮，面对面
    c.save(); c.translate(-.34, 0); c.scale(-.50, .50); _stag(c, HOUSES['baratheon']); c.restore()
    c.save(); c.translate(.33, 0); c.scale(.50, .50); _lion(c, HOUSES['lannister']); c.restore()
DRAW = dict(greyjoy=(_kraken, None), joffrey=(_joff, _joff_field), stark=(_wolf, None), lannister=(_lion, None), baratheon=(_stag, None), tully=(_trout, _trout_field), arryn=(_falcon, None), bolton=(_flayed, None), frey=(_towers, None), stannis=(_heart, None), baelish=(_mock, None))
# ---------------- 出图
def _outline(c, shape):
    if shape == 'round': c.arc(0, 0, .96, 0, math.tau)
    elif shape == 'banner': c.move_to(-.64, -.96); c.line_to(.64, -.96); c.line_to(.64, .96); c.line_to(0, .70); c.line_to(-.64, .96); c.close_path()
    else: c.move_to(-.82, -.90); c.line_to(.82, -.90); c.line_to(.82, .04); c.curve_to(.82, .56, .36, .84, 0, .98); c.curve_to(-.36, .84, -.82, .56, -.82, .04); c.close_path()
_FIT = dict(shield=(0, -.07, .86), round=(0, 0, .80), banner=(0, -.12, .74))
def _layer(S):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(s); c.translate(S / 2, S / 2); c.scale(S / 2, S / 2); return s, c
def _np(s):
    a = np.ndarray((s.get_height(), s.get_width(), 4), np.uint8, s.get_data()).astype(np.float32) / 255; return a[..., [2, 1, 0]], a[..., 3]
def _edge(a, thr):
    a3 = a if a.ndim == 3 else a[..., None]; e = np.zeros(a.shape[:2], np.float32)
    e[:, 1:] = np.maximum(e[:, 1:], np.abs(a3[:, 1:] - a3[:, :-1]).max(-1) > thr); e[1:] = np.maximum(e[1:], np.abs(a3[1:] - a3[:-1]).max(-1) > thr); return e
def _fat(e, k): return cv2.dilate(e, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(1, int(k)) | 1,) * 2))
_C = {}
def _charge_layer(name, S, shape):
    P = HOUSES[name]; s, c = _layer(S); dx, dy, k = _FIT[shape]; c.translate(dx, dy); c.scale(k, k); DRAW[name][0](c, P); return _np(s)
def charge(name, px=256):
    """只要图案的剪影（alpha，px×px）。"""
    return cv2.resize(_charge_layer(name, px * 2, 'round')[1], (px, px), interpolation=cv2.INTER_AREA)
def sigil(name, px=256, shape='shield', glass=True):
    key = (name, px, shape, glass)
    if key in _C: return _C[key]
    P = HOUSES[name]; S = max(256, px * 2); r = np.random.default_rng(sum(map(ord, name)))
    s, c = _layer(S); _outline(c, shape); c.set_source_rgb(1, 1, 1); c.fill(); m = _np(s)[1]
    s, c = _layer(S); _src(c, P['field']); c.paint()
    if DRAW[name][1]: DRAW[name][1](c, P)
    field = _np(s)[0]; crgb, ca = _charge_layer(name, S, shape); flat = field * (1 - ca[..., None]) + crgb
    u = S / 512; lead = _fat(_edge(ca, 0.5), 7 * u); lead = np.maximum(lead, _fat(_edge(flat, 0.10), 3 * u))
    if glass:                                       # 底色切成一块块玻璃，每块明暗略有不同
        cell = int(S / 5); seeds = np.ones((S, S), np.uint8)
        for gy in range(0, S + cell, cell):
            for gx in range(0, S + cell, cell): seeds[int(np.clip(gy + r.uniform(-.35, .35) * cell, 0, S - 1)), int(np.clip(gx + r.uniform(-.35, .35) * cell, 0, S - 1))] = 0
        _, lab = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL); jit = r.uniform(0.84, 1.12, lab.max() + 1).astype(np.float32)[lab]
        flat = np.where((ca < 0.5)[..., None], flat * jit[..., None], flat); lead = np.maximum(lead, _fat(_edge(lab.astype(np.float32), 0.5) * (ca < 0.5), 3 * u))
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); d = np.hypot(xx - S * .5, yy - S * .42) / S
        streak = cv2.GaussianBlur(r.random((S, S)).astype(np.float32), (0, 0), sigmaX=1.5 * u, sigmaY=16 * u); streak = (streak - streak.mean()) / (streak.std() + 1e-6)
        flat = flat * (1 + 0.05 * streak)[..., None] * (1.12 - 0.55 * d)[..., None]; flat = flat * (1 - 0.30 * np.clip(cv2.GaussianBlur(lead, (0, 0), 7 * u) * 1.6, 0, 1))[..., None]
    lead = cv2.GaussianBlur(lead, (0, 0), 0.8 * u); flat = flat * (1 - lead[..., None]) + LEAD * lead[..., None]
    er = lambda k: cv2.erode(m, np.ones((int(k * u) | 1,) * 2, np.uint8)); rim = np.clip(m - er(17), 0, 1); gold = np.clip(er(17) - er(27), 0, 1)
    flat = flat * (1 - gold[..., None]) + gold[..., None] * np.float32(hx(P['sub'] if P['sub'] != P['field'] else P['main'])) * 0.9; flat = flat * (1 - rim[..., None]) + LEAD * rim[..., None]
    rgb = cv2.resize(np.clip(flat, 0, 1) * m[..., None], (px, px), interpolation=cv2.INTER_AREA).astype(np.float32); a = cv2.resize(m, (px, px), interpolation=cv2.INTER_AREA)[..., None].astype(np.float32)
    _C[key] = (rgb, a); return _C[key]
def wave(rgb, a, t, amp=0.035, n=1.6, speed=5.0):
    """旗面飘动：横向波纹 + 明暗。"""
    h, w = rgb.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); ph = xx / w * n * math.tau - t * speed + yy / h * 1.2; k = (yy / h) * 0.6 + 0.4
    mx = xx + np.sin(ph) * amp * w * k; my = yy + np.cos(ph * 0.8 + 1) * amp * 0.5 * h * k
    o = cv2.remap(rgb, mx, my, cv2.INTER_LINEAR, borderValue=0); oa = cv2.remap(a, mx, my, cv2.INTER_LINEAR, borderValue=0)
    return o * (1 + 0.22 * np.cos(ph))[..., None], oa[..., None] if oa.ndim == 2 else oa
def put(fr, rgb, a, x, y, k=1.0):
    """把家徽贴到画面 fr 上，(x, y) 是中心的像素坐标。"""
    h, w = rgb.shape[:2]; x0, y0 = int(x - w / 2), int(y - h / 2); xa, ya, xb, yb = max(0, x0), max(0, y0), min(fr.shape[1], x0 + w), min(fr.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0)); reg = fr[ya:yb, xa:xb]; reg *= (1 - a[sl] * k); reg += rgb[sl] * k
def flag(fr, name, x, y, h, t, grow=1.0, crown=False):
    """地图上的一面家徽旗：(x, y) 是旗杆脚的像素坐标，h 是旗面高（像素），grow 0→1 是升旗；crown=True 在杆顶加一顶王冠。"""
    if grow <= 0: return
    g = min(1.0, grow); g = 1 - (1 - g) ** 2; h = max(10.0, h); px = max(10, int(h * (0.55 + 0.45 * g))); yt = y - 1.28 * h * g; w = max(1, int(round(h * 0.045))); dk = (0.10, 0.07, 0.05)
    rgb, a = sigil(name, px, 'banner'); rgb, a = wave(rgb, a, t + x * 0.013, amp=0.028)
    cv2.line(fr, (int(x), int(y)), (int(x), int(yt - h * 0.05)), dk, w + 2, cv2.LINE_AA); cv2.line(fr, (int(x), int(y)), (int(x), int(yt - h * 0.05)), (0.55, 0.42, 0.26), w, cv2.LINE_AA)
    cv2.line(fr, (int(x - px * 0.36), int(yt)), (int(x + px * 0.36), int(yt)), dk, w + 2, cv2.LINE_AA); cv2.circle(fr, (int(x), int(y)), w + 2, dk, -1, cv2.LINE_AA)
    put(fr, rgb, a, x, yt + px * 0.5)
    if crown:
        s = h * 0.30 * g; cy = yt - h * 0.10; p = np.int32([(x - s, cy), (x - s * 1.12, cy - s * 0.95), (x - s * 0.5, cy - s * 0.45), (x, cy - s * 1.15), (x + s * 0.5, cy - s * 0.45), (x + s * 1.12, cy - s * 0.95), (x + s, cy)])
        cv2.fillPoly(fr, [p], (0.96, 0.78, 0.26), cv2.LINE_AA); cv2.polylines(fr, [p], True, dk, max(1, w), cv2.LINE_AA)
if __name__ == '__main__':
    from PIL import Image, ImageDraw, ImageFont
    from paper import FONT
    names = list(HOUSES); px = 360; cols = 5; rows = math.ceil(len(names) / cols); fr = np.zeros((rows * (px + 90) + 40, cols * (px + 24) + 24, 3), np.float32) + np.float32((0.05, 0.045, 0.05))
    for i, n in enumerate(names): rgb, a = sigil(n, px, sys.argv[1] if len(sys.argv) > 1 else 'shield'); put(fr, rgb, a, 24 + (i % cols) * (px + 24) + px / 2, 30 + (i // cols) * (px + 90) + px / 2)
    im = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im); f = ImageFont.truetype(FONT, 34)
    for i, n in enumerate(names): d.text((24 + (i % cols) * (px + 24) + px / 2, 30 + (i // cols) * (px + 90) + px + 36), HOUSES[n]['zh'] + ('  ' + HOUSES[n]['motto'] if HOUSES[n]['motto'] else ''), font=f, fill=(230, 220, 200), anchor='mm')
    os.makedirs('out', exist_ok=True); im.save('out/_sigils.jpg', quality=92); print('out/_sigils.jpg')
