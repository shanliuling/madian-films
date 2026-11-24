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
def _wolf(c, P):                                    # 史塔克：灰色冰原狼（侧面狼头，张口）
    _src(c, P['ink'])
    _poly(c, [(-.66, -.06), (-.50, -.14), (-.30, -.21), (-.17, -.35), (-.05, -.47), (.05, -.82), (.21, -.47), (.37, -.74), (.43, -.40), (.62, -.26), (.48, -.15), (.70, .02), (.52, .08), (.70, .27), (.50, .31), (.62, .54), (.38, .49), (.41, .74), (.18, .57), (.07, .76), (-.05, .50), (-.19, .60), (-.15, .36), (-.48, .40), (-.57, .30), (-.24, .15), (-.62, .08)])
    _src(c, P['field']); _poly(c, [(-.56, .08), (-.51, .22), (-.46, .09)]); _poly(c, [(-.40, .10), (-.37, .18), (-.33, .11)]); _poly(c, [(-.49, .33), (-.45, .20), (-.40, .31)]); _poly(c, [(-.32, -.19), (-.15, -.29), (-.17, -.20)])
    _src(c, tuple(v * 0.62 for v in hx(P['ink']))); _poly(c, [(-.66, -.06), (-.58, -.11), (-.55, -.02), (-.62, .03)]); _poly(c, [(.05, -.70), (.12, -.47), (.02, -.44)])
    _poly(c, [(.30, -.10), (.44, .00), (.34, .04), (.48, .20), (.34, .22), (.42, .40), (.26, .34), (.22, .06)])
def _lion(c, P):                                    # 兰尼斯特：金色雄狮（直立，张口）
    _src(c, P['ink'])
    _tube(c, [(.26, .42), (.58, .42), (.70, .14), (.52, -.08), (.52, -.34), (.68, -.50)], [.055, .05, .05, .05, .045, .04]); _smooth(c, [(.62, -.42), (.58, -.62), (.72, -.82), (.75, -.62), (.88, -.58), (.78, -.42)])
    _tube(c, [(-.10, -.20), (.03, .08), (.14, .34)], [.28, .16, .23])
    _tube(c, [(.16, .40), (.00, .62), (.13, .77), (-.04, .88)], [.15, .09, .07, .065]); _blob(c, -.11, .90, .13, .06)
    _tube(c, [(.06, .38), (-.18, .46), (-.36, .58)], [.14, .085, .065]); _blob(c, -.44, .62, .12, .06, .5)
    _tube(c, [(-.14, -.26), (-.42, -.30), (-.58, -.46)], [.13, .085, .065]); _blob(c, -.65, -.52, .12, .065, .8)
    _tube(c, [(-.12, -.04), (-.42, -.01), (-.60, .10)], [.13, .085, .065]); _blob(c, -.68, .14, .12, .065, .5)
    _smooth(c, [(-.30, -.78), (-.06, -.84), (.14, -.68), (.22, -.42), (.16, -.14), (.00, .02), (-.20, -.02), (-.16, -.30)])     # 鬃毛：一团加几绺
    for (bx, by, tx, ty) in ((-.02, -.80, .12, -.96), (.14, -.66, .34, -.74), (.20, -.46, .40, -.44), (.18, -.24, .36, -.14), (.08, -.04, .20, .12), (-.10, .00, -.08, .18)):
        d = math.hypot(tx - bx, ty - by); nx, ny = -(ty - by) / d * .10, (tx - bx) / d * .10; _poly(c, [(bx - nx, by - ny), (tx, ty), (bx + nx, by + ny)])
    _blob(c, -.27, -.56, .18, .17); _blob(c, -.17, -.75, .07, .08, -.3)
    _poly(c, [(-.34, -.71), (-.56, -.67), (-.65, -.57), (-.60, -.49), (-.36, -.47)]); _poly(c, [(-.40, -.47), (-.60, -.31), (-.50, -.25), (-.22, -.38)])
    _src(c, P['acc']); _poly(c, [(-.36, -.47), (-.56, -.42), (-.48, -.37)])
    _src(c, P['field']); _poly(c, [(-.60, -.50), (-.56, -.41), (-.52, -.49)]); _poly(c, [(-.56, -.31), (-.53, -.39), (-.49, -.32)]); _poly(c, [(-.44, -.63), (-.32, -.66), (-.34, -.59)])
    _src(c, tuple(v * 0.55 for v in hx(P['ink']))); _blob(c, -.63, -.585, .035, .03)
    for (x, y, a) in ((-.72, -.58, .8), (-.75, .16, .5), (-.52, .66, .5), (-.20, .93, 0)):
        for k in (-1, 0, 1): c.save(); c.translate(x, y); c.rotate(a); _poly(c, [(-.01, k * .04 - .014), (-.08, k * .04), (-.01, k * .04 + .014)]); c.restore()
    c.set_line_width(.018)
    for (x0, y0, x1, y1) in ((.02, -.62, .10, -.44), (-.04, -.40, .06, -.22), (-.08, -.22, -.02, -.08)): c.move_to(x0, y0); c.curve_to(x0 + .08, y0 + .04, x1 + .04, y1 - .08, x1, y1); c.stroke()
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
DRAW = dict(stark=(_wolf, None), lannister=(_lion, None), baratheon=(_stag, None), tully=(_trout, _trout_field), arryn=(_falcon, None), bolton=(_flayed, None), frey=(_towers, None), stannis=(_heart, None), baelish=(_mock, None))
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
if __name__ == '__main__':
    from PIL import Image, ImageDraw, ImageFont
    from paper import FONT
    names = list(HOUSES); px = 360; cols = 5; rows = math.ceil(len(names) / cols); fr = np.zeros((rows * (px + 90) + 40, cols * (px + 24) + 24, 3), np.float32) + np.float32((0.05, 0.045, 0.05))
    for i, n in enumerate(names): rgb, a = sigil(n, px, sys.argv[1] if len(sys.argv) > 1 else 'shield'); put(fr, rgb, a, 24 + (i % cols) * (px + 24) + px / 2, 30 + (i // cols) * (px + 90) + px / 2)
    im = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im); f = ImageFont.truetype(FONT, 34)
    for i, n in enumerate(names): d.text((24 + (i % cols) * (px + 24) + px / 2, 30 + (i // cols) * (px + 90) + px + 36), HOUSES[n]['zh'] + ('  ' + HOUSES[n]['motto'] if HOUSES[n]['motto'] else ''), font=f, fill=(230, 220, 200), anchor='mm')
    os.makedirs('out', exist_ok=True); im.save('out/_sigils.jpg', quality=92); print('out/_sigils.jpg')
