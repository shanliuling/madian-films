"""fighter — 斗破系列的人物：能打的骨架 + 漫画式画法（墨线、平涂、一层阴影），头发衣摆跟着动作甩。
造型按漫画版：萧炎（深蓝黑刺猬短发、黑袍、玄重尺）、纳兰嫣然（黑长发、月白袍、淡青长剑）。
姿态是一个 dict，角度全用度：
    x          骨盆的场景 x；y 由脚自动落地，air = 离地多高
    face       1 朝右，-1 朝左；rot 整个人绕骨盆转（空翻）
    lean       躯干前倾；head 头相对躯干的俯仰
    a1 / a2    近臂 / 远臂 (上臂, 前臂)，0 = 垂下，90 = 向前平举，180 = 向上
    l1 / l2    近腿 / 远腿 (大腿, 小腿)，0 = 垂直向下，正 = 向前
    w          兵器方向：0 = 向前，90 = 向上，180 = 向后；g2 = 远手也握在柄上（离近手多远，单位身高）
    eye / mouth / bend(剑被压弯多少)"""
import math, cairo
from action import chain, smooth, ribbon_path, rnd
INK = (0.05, 0.05, 0.08); SKIN = (0.99, 0.87, 0.76); SKIN_S = (0.88, 0.68, 0.60)
R_ = math.radians
STAND = dict(x=0, air=0, face=1, rot=0, lean=2, head=0, a1=(8, 22), a2=(-10, 6), l1=(9, 2), l2=(-9, -6), w=-70, g2=0, eye=1.0, mouth=0, bend=0.0, tw=1.0)
def P(**o): p = dict(STAND); p.update(o); return p

def kin(p, H, gy):
    """姿态 → 各关节的场景坐标。"""
    T, UA, LA, UL, LL, FL = 0.27 * H, 0.150 * H, 0.150 * H, 0.245 * H, 0.245 * H, 0.085 * H
    v = lambda a, L: (math.sin(R_(a)) * L, math.cos(R_(a)) * L); add = lambda a, b: (a[0] + b[0], a[1] + b[1])
    le = p['lean']; up = (math.sin(R_(le)), -math.cos(R_(le))); fw = (math.cos(R_(le)), math.sin(R_(le))); tw = p.get('tw', 1.0); J = {'pel': (0.0, 0.0)}
    J['neck'] = (up[0] * T, up[1] * T); J['chest'] = (up[0] * T * 0.6, up[1] * T * 0.6); ha = le + p.get('head', 0); J['head'] = add(J['neck'], (math.sin(R_(ha)) * 0.10 * H, -math.cos(R_(ha)) * 0.10 * H)); J['ha'] = ha
    sb = (up[0] * T * 0.93, up[1] * T * 0.93); J['s1'] = add(sb, (-fw[0] * 0.045 * H * tw, -fw[1] * 0.045 * H * tw)); J['s2'] = add(sb, (fw[0] * 0.05 * H * tw, fw[1] * 0.05 * H * tw))
    J['p1'] = (-0.03 * H * tw, 0.0); J['p2'] = (0.03 * H * tw, 0.0)
    for k in ('1', '2'):
        a = p['a' + k]; J['e' + k] = add(J['s' + k], v(a[0], UA)); J['h' + k] = add(J['e' + k], v(a[1], LA))
        l = p['l' + k]; J['k' + k] = add(J['p' + k], v(l[0], UL)); J['f' + k] = add(J['k' + k], v(l[1], LL)); J['t' + k] = add(J['f' + k], v(p.get('ft' + k, min(90, l[1] + 78) if p.get('air', 0) < 12 else l[1] + 40), FL))
    wd = (math.cos(R_(p['w'])), -math.sin(R_(p['w']))); J['wd'] = wd
    if p.get('g2'):                                                                     # 远手也握柄：两段骨 IK
        tg = add(J['h1'], (wd[0] * p['g2'] * H, wd[1] * p['g2'] * H)); dx, dy = tg[0] - J['s2'][0], tg[1] - J['s2'][1]; d = min(math.hypot(dx, dy), UA + LA - 1e-3); d = max(d, 1e-3)
        a0 = math.atan2(dy, dx); b = math.acos(max(-1, min(1, (UA * UA + d * d - LA * LA) / (2 * UA * d)))); J['e2'] = (J['s2'][0] + math.cos(a0 + b) * UA, J['s2'][1] + math.sin(a0 + b) * UA); J['h2'] = (J['s2'][0] + math.cos(a0) * d, J['s2'][1] + math.sin(a0) * d)
    ro = R_(p.get('rot', 0)); co, si = math.cos(ro), math.sin(ro); rt = lambda q: (q[0] * co - q[1] * si, q[0] * si + q[1] * co)
    for k in list(J):
        if k != 'ha': J[k] = rt(J[k])
    low = max(J['f1'][1], J['f2'][1], J['t1'][1], J['t2'][1]) + 0.02 * H; f = 1 if p.get('face', 1) >= 0 else -1; ox, oy = p['x'], gy - low - p.get('air', 0)
    for k in list(J):
        if k == 'wd': J[k] = (J[k][0] * f, J[k][1])
        elif k != 'ha': J[k] = (J[k][0] * f + ox, J[k][1] + oy)
    J['f'] = f; J['H'] = H; J['rot'] = p.get('rot', 0); J['p'] = p; return J
def wpts(J, L, off=0.0):
    """兵器的根和尖（场景坐标）。L、off 单位是身高。"""
    h, d, H = J['h1'], J['wd'], J['H']; return (h[0] + d[0] * off * H, h[1] + d[1] * off * H), (h[0] + d[0] * L * H, h[1] + d[1] * L * H)

# ---------- 画法
def _ink(c, fill, lw, ink=INK):
    c.set_source_rgb(*fill); c.fill_preserve(); c.set_source_rgb(*ink); c.set_line_width(lw); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke()
def _cap(c, a, b, wa, wb):
    g = math.atan2(b[1] - a[1], b[0] - a[0]); c.new_path(); c.arc(a[0], a[1], wa, g + math.pi / 2, g + 3 * math.pi / 2); c.arc(b[0], b[1], wb, g - math.pi / 2, g + math.pi / 2); c.close_path()
def limb(c, a, b, wa, wb, fill, lw, shade=None, sd=(0.35, 0.5)):
    _cap(c, a, b, wa, wb); c.set_source_rgb(*fill); c.fill_preserve()
    if shade:                                                                           # 背光的半边压一层暗色
        c.save(); c.clip_preserve(); c.new_path(); o = max(wa, wb); _cap(c, (a[0] + sd[0] * o, a[1] + sd[1] * o), (b[0] + sd[0] * o, b[1] + sd[1] * o), wa, wb); c.set_source_rgb(*shade); c.fill(); c.restore(); _cap(c, a, b, wa, wb)
    c.set_source_rgb(*INK); c.set_line_width(lw); c.stroke()
def panel(c, pts, w0, w1, fill, lw, shade=None, trim=None):
    """一片衣摆 / 一束头发：沿跟随链铺开。"""
    sp = smooth(pts, 4); n = len(sp) - 1; ws = [w0 + (w1 - w0) * (i / n) ** 0.8 for i in range(n + 1)]; ribbon_path(c, sp, ws); c.set_source_rgb(*fill); c.fill_preserve()
    if shade: c.save(); c.clip_preserve(); c.new_path(); ribbon_path(c, [(q[0] + w1 * 0.9, q[1] + w1 * 0.25) for q in sp], ws); c.set_source_rgb(*shade); c.fill(); c.restore(); ribbon_path(c, sp, ws)
    c.set_source_rgb(*INK); c.set_line_width(lw); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke()
    if trim:
        a, b = sp[-2], sp[-1]; d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1; nx, ny = -(b[1] - a[1]) / d, (b[0] - a[0]) / d; c.move_to(b[0] + nx * w1 * 0.9, b[1] + ny * w1 * 0.9); c.line_to(b[0] - nx * w1 * 0.9, b[1] - ny * w1 * 0.9); c.set_source_rgb(*trim); c.set_line_width(lw * 1.6); c.stroke()
def _head_ctx(c, J):
    c.save(); c.translate(*J['head']); c.scale(J['f'], 1); c.rotate(R_(J['ha'] + J['rot'])); r = 0.077 * J['H']; c.scale(r, r); return r
def face(c, J, look, lw):
    """侧脸（单位：头骨半径；x 朝脸的方向）。漫画式：尖下巴、一只大眼、斜眉。"""
    r = _head_ctx(c, J); u = lw / r; p = J['p']; eo = p.get('eye', 1.0); mo = p.get('mouth', 0)
    c.new_path(); c.move_to(-0.62, 0.35); c.curve_to(-1.1, -0.2, -0.9, -1.12, 0.0, -1.12); c.curve_to(0.6, -1.12, 0.95, -0.75, 0.95, -0.3); c.line_to(0.93, -0.02); c.line_to(1.10, 0.36); c.line_to(0.93, 0.44); c.line_to(0.96, 0.60); c.line_to(0.90, 0.66); c.line_to(0.93, 0.80); c.curve_to(0.9, 1.0, 0.75, 1.12, 0.55, 1.08); c.curve_to(0.2, 1.0, -0.15, 0.85, -0.3, 0.6); c.close_path(); _ink(c, SKIN, u)
    c.save(); c.move_to(-0.62, 0.35); c.curve_to(-1.1, -0.2, -0.9, -1.12, 0.0, -1.12); c.curve_to(0.6, -1.12, 0.95, -0.75, 0.95, -0.3); c.line_to(0.93, -0.02); c.line_to(1.10, 0.36); c.line_to(0.93, 0.44); c.line_to(0.93, 0.80); c.curve_to(0.9, 1.0, 0.75, 1.12, 0.55, 1.08); c.curve_to(0.2, 1.0, -0.15, 0.85, -0.3, 0.6); c.close_path(); c.clip()
    c.move_to(-0.4, 0.5); c.curve_to(0.0, 0.75, 0.3, 0.95, 0.7, 1.2); c.line_to(-0.6, 1.3); c.close_path(); c.set_source_rgb(*SKIN_S); c.fill(); c.restore()                    # 下颌的阴影
    c.arc(-0.12, 0.2, 0.17, 0, 7); _ink(c, SKIN, u * 0.8)                                 # 耳
    ey = look.get('eye_y', 0.08); ex = 0.56; h = look.get('eye_h', 0.20) * max(0.12, eo)
    if eo > 0.15:
        c.move_to(ex - 0.24, ey + 0.02); c.curve_to(ex - 0.1, ey - h, ex + 0.14, ey - h * 1.05, ex + 0.26, ey - h * 0.35); c.line_to(ex + 0.24, ey + h * 0.55); c.curve_to(ex + 0.1, ey + h * 0.8, ex - 0.1, ey + h * 0.7, ex - 0.24, ey + 0.02); c.close_path(); c.set_source_rgb(1, 1, 1); c.fill_preserve(); c.save(); c.clip()
        c.save(); c.translate(ex + 0.07, ey - h * 0.1); c.scale(0.13, h * 0.95); c.arc(0, 0, 1, 0, 7); c.restore(); c.set_source_rgb(*look['iris']); c.fill(); c.arc(ex + 0.08, ey - h * 0.1, 0.05, 0, 7); c.set_source_rgb(0.02, 0.02, 0.04); c.fill()
        if p.get('glint'): c.arc(ex + 0.07, ey - h * 0.1, 0.16, 0, 7); c.set_source_rgba(*look.get('glint', (0.3, 1, 0.8)), p['glint']); c.fill()
        c.arc(ex + 0.02, ey - h * 0.45, 0.045, 0, 7); c.set_source_rgb(1, 1, 1); c.fill(); c.restore()
    c.move_to(ex - 0.28, ey + 0.05 - (0 if eo > 0.15 else -0.04)); c.curve_to(ex - 0.1, ey - h * 1.05, ex + 0.16, ey - h * 1.15, ex + 0.30, ey - h * 0.35); c.set_source_rgb(*INK); c.set_line_width(look.get('lash', 0.085)); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    b = look.get('brow', 0.09); by = ey - look.get('eye_h', 0.2) - 0.20; c.move_to(ex - 0.34, by - 0.10 + look.get('brow_tilt', 0.1) * -1); c.line_to(ex + 0.34, by + 0.10 + look.get('brow_tilt', 0.1)); c.set_source_rgb(*look['hair']); c.set_line_width(b); c.stroke()
    if mo > 0.1: c.move_to(0.60, 0.60); c.line_to(0.92, 0.58); c.line_to(0.88, 0.60 + 0.26 * mo); c.line_to(0.66, 0.60 + 0.2 * mo); c.close_path(); c.set_source_rgb(0.45, 0.08, 0.1); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(u * 0.7); c.stroke(); c.move_to(0.66, 0.615); c.line_to(0.9, 0.60); c.set_source_rgb(1, 1, 1); c.set_line_width(0.05); c.stroke()
    else: c.move_to(0.66, 0.64); c.line_to(0.9, 0.63 + look.get('smirk', 0.0)); c.set_source_rgb(*INK); c.set_line_width(u * 0.8); c.stroke()
    c.restore(); return r
def hair_cap(c, J, look, lw, bangs):
    """头顶和后脑的头发 + 刘海（bangs = [(根x, 根y, 尖x, 尖y, 半宽)]）。"""
    r = _head_ctx(c, J); u = lw / r
    c.new_path(); c.move_to(0.98, -0.42); c.curve_to(0.95, -1.0, 0.5, -1.3, -0.05, -1.28); c.curve_to(-0.85, -1.25, -1.22, -0.6, -1.05, 0.1); c.curve_to(-1.0, 0.4, -0.85, 0.62, -0.6, 0.7); c.line_to(-0.34, 0.36); c.line_to(-0.1, 0.42); c.line_to(0.08, -0.05); c.line_to(0.3, -0.42); c.close_path(); _ink(c, look['hair'], u)
    for (bx, by, tx, ty, hw) in bangs: c.move_to(bx - hw, by); c.curve_to(bx - hw * 0.6, (by + ty) / 2, tx - 0.05, ty - 0.2, tx, ty); c.curve_to(tx + 0.02, ty - 0.3, bx + hw * 0.8, (by + ty) / 2, bx + hw, by); c.close_path(); _ink(c, look['hair'], u)
    c.move_to(-0.55, -0.95); c.curve_to(-0.2, -1.12, 0.25, -1.1, 0.55, -0.9); c.set_source_rgb(*look['hair_hi']); c.set_line_width(0.09); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke(); c.restore()
def hand(c, q, H, lw): c.arc(q[0], q[1], 0.021 * H, 0, 7); _ink(c, SKIN, lw)
def torso(c, J, col, shade, lw, collar=None, inner=(0.93, 0.93, 0.95), belt=None, w=(0.078, 0.092, 0.066, 0.078)):
    H = J['H']; a, b = J['pel'], J['neck']; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; nx, ny = -uy * J['f'], ux * J['f'] if False else (-uy, ux)[1]
    nx, ny = (uy, -ux) if J['f'] > 0 else (-uy, ux); nx, ny = (nx, ny) if True else (nx, ny)
    pt = lambda s, o: (a[0] + ux * L * s + nx * o * H, a[1] + uy * L * s + ny * o * H)
    def path(): c.new_path(); c.move_to(*pt(1.0, -w[0])); c.curve_to(*pt(0.75, -w[1]), *pt(0.45, -w[2] * 1.05), *pt(0.0, -w[3])); c.line_to(*pt(-0.06, 0)); c.line_to(*pt(0.0, w[3])); c.curve_to(*pt(0.45, w[2]), *pt(0.75, w[1] * 1.05), *pt(0.98, w[0] * 0.9)); c.close_path()
    path(); c.set_source_rgb(*col); c.fill_preserve(); c.save(); c.clip(); c.new_path(); c.move_to(*pt(1.05, -w[0] * 1.3)); c.line_to(*pt(1.05, -w[0] * 0.25)); c.line_to(*pt(-0.1, -w[3] * 0.1)); c.line_to(*pt(-0.1, -w[3] * 1.4)); c.close_path(); c.set_source_rgb(*shade); c.fill()
    if collar: c.move_to(*pt(1.02, 0.045)); c.line_to(*pt(0.55, 0.075)); c.line_to(*pt(0.98, -0.02)); c.close_path(); c.set_source_rgb(*inner); c.fill(); c.move_to(*pt(1.02, 0.05)); c.line_to(*pt(0.5, 0.085)); c.set_source_rgb(*collar); c.set_line_width(lw * 2.2); c.stroke(); c.move_to(*pt(1.0, -0.03)); c.line_to(*pt(0.34, 0.08)); c.stroke()
    if belt: c.move_to(*pt(0.26, -0.11)); c.line_to(*pt(0.26, 0.11)); c.line_to(*pt(0.10, 0.11)); c.line_to(*pt(0.10, -0.11)); c.close_path(); c.set_source_rgb(*belt); c.fill()
    c.restore(); path(); c.set_source_rgb(*INK); c.set_line_width(lw); c.stroke(); return pt

def ruler(c, J, lw, L=0.92, flame=0.0):
    """玄重尺：漆黑的宽尺，柄短，尺身有看不清的纹路。画在近手里。"""
    H = J['H']; h = J['h1']; d = J['wd']; c.save(); c.translate(*h); c.rotate(math.atan2(d[1], d[0])); W = 0.075 * H; x0, x1 = 0.10 * H, L * H
    c.rectangle(-0.07 * H, -0.016 * H, 0.18 * H, 0.032 * H); _ink(c, (0.22, 0.2, 0.22), lw)
    c.new_path(); c.move_to(x0, -W * 0.62); c.line_to(x0 + 0.03 * H, -W); c.line_to(x1 - 0.03 * H, -W); c.line_to(x1, -W * 0.55); c.line_to(x1, W * 0.55); c.line_to(x1 - 0.03 * H, W); c.line_to(x0 + 0.03 * H, W); c.line_to(x0, W * 0.62); c.close_path(); _ink(c, (0.07, 0.07, 0.10), lw * 1.2)
    c.move_to(x0 + 0.04 * H, -W * 0.72); c.line_to(x1 - 0.035 * H, -W * 0.72); c.set_source_rgb(0.42, 0.46, 0.56); c.set_line_width(lw * 0.9); c.stroke(); c.move_to(x0 + 0.04 * H, W * 0.72); c.line_to(x1 - 0.035 * H, W * 0.72); c.set_source_rgb(0.2, 0.22, 0.3); c.stroke()
    c.set_source_rgb(0.36 + 0.3 * flame, 0.2 + 0.7 * flame, 0.22 + 0.55 * flame); c.set_line_width(lw * 0.8)                                  # 纹路（催动时发青）
    for i in range(5):
        x = x0 + (0.11 + 0.15 * i) * H; c.move_to(x - 0.04 * H, -W * 0.35); c.line_to(x, W * 0.3); c.line_to(x + 0.04 * H, -W * 0.35); c.move_to(x - 0.02 * H, W * 0.45); c.line_to(x + 0.02 * H, W * 0.45)
    c.stroke(); c.restore()
def sword(c, J, lw, L=0.66, bend=0.0, col=(0.72, 0.97, 0.95), a=1.0, at=None, d=None, guard=(0.55, 0.8, 0.82), hilt=(0.2, 0.32, 0.4)):
    """淡青长剑；bend ≠ 0 时剑身被压成弧。at/d 给了就画一把不在手里的剑（残影）。"""
    H = J['H'] if J else 300; h = at or J['h1']; d = d or J['wd']; c.save(); c.translate(*h); c.rotate(math.atan2(d[1], d[0])); n = 14; Lp = L * H; x0 = 0.035 * H
    pts = [(x0 + (Lp - x0) * i / n, -bend * Lp * math.sin(math.pi * i / n) * (1 if d[0] >= 0 else -1)) for i in range(n + 1)]; ribbon_path(c, pts, lambda u: 0.013 * H * (1 - u ** 6 * 0.95))
    c.set_source_rgba(*col, a); c.fill_preserve(); c.set_source_rgba(*INK, a); c.set_line_width(lw * 0.8); c.stroke(); c.move_to(*pts[0])
    for q in pts[1:]: c.line_to(*q)
    c.set_source_rgba(1, 1, 1, a); c.set_line_width(lw * 0.7); c.stroke()
    if a >= 1: c.rectangle(-0.06 * H, -0.011 * H, 0.085 * H, 0.022 * H); _ink(c, hilt, lw * 0.8); c.move_to(x0 - 0.01 * H, 0); c.curve_to(x0 - 0.03 * H, -0.05 * H, x0 + 0.02 * H, -0.05 * H, x0 + 0.05 * H, -0.012 * H); c.line_to(x0 + 0.05 * H, 0.012 * H); c.curve_to(x0 + 0.02 * H, 0.05 * H, x0 - 0.03 * H, 0.05 * H, x0 - 0.01 * H, 0); c.close_path(); _ink(c, guard, lw * 0.8)   # 翼形护手
    c.restore()

XIAOYAN = dict(hair=(0.07, 0.10, 0.20), hair_hi=(0.26, 0.42, 0.66), iris=(0.10, 0.12, 0.20), robe=(0.15, 0.16, 0.23), robe_s=(0.06, 0.06, 0.10), trim=(0.55, 0.12, 0.14), eye_h=0.17, brow=0.12, brow_tilt=0.13, lash=0.09, glint=(0.3, 1.0, 0.8))
NALAN = dict(hair=(0.09, 0.08, 0.13), hair_hi=(0.36, 0.34, 0.5), iris=(0.35, 0.62, 0.78), robe=(0.97, 0.98, 1.0), robe_s=(0.74, 0.83, 0.93), trim=(0.45, 0.85, 0.88), eye_h=0.22, brow=0.055, brow_tilt=0.05, lash=0.10, eye_y=0.10)

def xiaoyan(c, Jat, t, held=True, back=False):
    """Jat(dt) = t−dt 时刻的关节。held：尺握在手里；back：尺背在背上。"""
    J = Jat(0); H = J['H']; f = J['f']; lw = 0.011 * H; K = XIAOYAN; rb, rs = K['robe'], K['robe_s']; g = lambda k: (lambda dt: Jat(dt)[k])
    if back: c.save(); m = J['chest']; c.translate(m[0] - f * 0.05 * H, m[1]); JJ = dict(J, h1=(0, 0), wd=(f * math.cos(R_(118)), -math.sin(R_(118)))); c.translate(-JJ['wd'][0] * 0.42 * H, -JJ['wd'][1] * 0.42 * H); ruler(c, JJ, lw); c.restore()
    limb(c, J['s2'], J['e2'], 0.034 * H, 0.03 * H, rs, lw); limb(c, J['e2'], J['h2'], 0.032 * H, 0.036 * H, rs, lw); hand(c, J['h2'], H, lw)
    limb(c, J['p2'], J['k2'], 0.05 * H, 0.04 * H, rs, lw); limb(c, J['k2'], J['f2'], 0.038 * H, 0.03 * H, rs, lw); limb(c, J['f2'], J['t2'], 0.028 * H, 0.02 * H, (0.02, 0.02, 0.03), lw)
    panel(c, chain(lambda dt: (Jat(dt)['pel'][0] - Jat(dt)['f'] * 0.035 * H, Jat(dt)['pel'][1] - 0.03 * H), 5, 0.062 * H, 0.022, (-0.25 * f, 0.97), t, 0.10, 1.0), 0.05 * H, 0.085 * H, rs, lw, trim=K['trim'])     # 后摆
    panel(c, chain(lambda dt: (Jat(dt)['pel'][0] - Jat(dt)['f'] * 0.02 * H, Jat(dt)['pel'][1] - 0.07 * H), 6, 0.05 * H, 0.03, (-0.5 * f, 0.87), t, 0.22, 2.0), 0.014 * H, 0.02 * H, K['trim'], lw * 0.8)                 # 腰带的飘带
    limb(c, J['p1'], J['k1'], 0.054 * H, 0.043 * H, rb, lw, rs); limb(c, J['k1'], J['f1'], 0.04 * H, 0.032 * H, rb, lw, rs); limb(c, J['f1'], J['t1'], 0.03 * H, 0.021 * H, (0.04, 0.04, 0.06), lw)
    torso(c, J, rb, rs, lw, collar=K['trim'], belt=K['trim'])
    panel(c, chain(lambda dt: (Jat(dt)['pel'][0] + Jat(dt)['f'] * 0.03 * H, Jat(dt)['pel'][1] - 0.03 * H), 4, 0.06 * H, 0.02, (0.12 * f, 0.99), t, 0.08, 3.0), 0.045 * H, 0.07 * H, rb, lw, rs, trim=K['trim'])     # 前摆
    limb(c, J['neck'], J['head'], 0.026 * H, 0.03 * H, SKIN_S, lw)
    hv = Jat(0.05)['head']; vx, vy = (J['head'][0] - hv[0]) / (0.05 * H), (J['head'][1] - hv[1]) / (0.05 * H); r = 0.077 * H; ha = R_(J['ha'] + J['rot'])
    for i, (ang, ln) in enumerate(((-158, 0.8), (-128, 1.25), (-98, 1.05), (-70, 1.5), (-42, 1.15), (-12, 1.45), (20, 1.0), (48, 0.8))):       # 后脑的刺：往后上方炸开，跟着速度甩
        th = ha + R_(ang) - math.pi / 2; bx, by = J['head'][0] + f * math.cos(th) * -r * 0.78, J['head'][1] + math.sin(th) * -r * 0.78 - r * 0.1
        dx, dy = f * -math.cos(th), -math.sin(th); sw = 0.10 * math.sin(t * 11 + i * 1.7); tx, ty = bx + (dx * math.cos(sw) - dy * math.sin(sw)) * r * ln - vx * r * 0.22 * ln, by + (dx * math.sin(sw) + dy * math.cos(sw)) * r * ln - vy * r * 0.22 * ln
        px, py = -dy * r * 0.42, dx * r * 0.42; c.move_to(bx + px, by + py); c.line_to(tx, ty); c.line_to(bx - px, by - py); c.close_path(); _ink(c, K['hair'], lw)
    face(c, J, K, lw); hair_cap(c, J, K, lw, ((0.30, -0.80, 0.34, 0.02, 0.16), (0.58, -0.86, 0.70, -0.12, 0.17), (0.84, -0.72, 1.02, -0.16, 0.13)))
    if held: ruler(c, J, lw, flame=J['p'].get('fire', 0.0))
    if J['p'].get('g2'): hand(c, J['h2'], H, lw)
    limb(c, J['s1'], J['e1'], 0.04 * H, 0.034 * H, rb, lw, rs); limb(c, J['e1'], J['h1'], 0.036 * H, 0.042 * H, rb, lw, rs); hand(c, J['h1'], H, lw)

def nalan(c, Jat, t, held=True):
    J = Jat(0); H = J['H']; f = J['f']; lw = 0.011 * H; K = NALAN; rb, rs = K['robe'], K['robe_s']; r = 0.077 * H
    hb = lambda dt: (Jat(dt)['head'][0] - Jat(dt)['f'] * r * 0.5, Jat(dt)['head'][1] - r * 0.1)
    panel(c, chain(hb, 8, 0.058 * H, 0.028, (-0.22 * f, 0.975), t, 0.10, 0.5), 0.05 * H, 0.03 * H, K['hair'], lw)                                    # 长发
    limb(c, J['s2'], J['e2'], 0.03 * H, 0.03 * H, rs, lw); limb(c, J['e2'], J['h2'], 0.03 * H, 0.05 * H, rs, lw); hand(c, J['h2'], H, lw)
    limb(c, J['p2'], J['k2'], 0.042 * H, 0.034 * H, rs, lw); limb(c, J['k2'], J['f2'], 0.032 * H, 0.026 * H, rs, lw); limb(c, J['f2'], J['t2'], 0.024 * H, 0.017 * H, (0.8, 0.86, 0.92), lw)
    panel(c, chain(lambda dt: (Jat(dt)['pel'][0] - Jat(dt)['f'] * 0.03 * H, Jat(dt)['pel'][1] - 0.03 * H), 7, 0.062 * H, 0.024, (-0.3 * f, 0.955), t, 0.10, 1.0), 0.055 * H, 0.12 * H, rs, lw, trim=K['trim'])      # 裙后摆
    panel(c, chain(lambda dt: (Jat(dt)['pel'][0] - Jat(dt)['f'] * 0.02 * H, Jat(dt)['pel'][1] - 0.08 * H), 7, 0.055 * H, 0.032, (-0.55 * f, 0.84), t, 0.25, 2.0), 0.012 * H, 0.02 * H, K['trim'], lw * 0.8)        # 飘带
    limb(c, J['p1'], J['k1'], 0.045 * H, 0.036 * H, rb, lw, rs); limb(c, J['k1'], J['f1'], 0.034 * H, 0.027 * H, rb, lw, rs); limb(c, J['f1'], J['t1'], 0.025 * H, 0.018 * H, (0.9, 0.94, 0.98), lw)
    torso(c, J, rb, rs, lw, collar=K['trim'], inner=(0.8, 0.93, 0.95), belt=K['trim'], w=(0.066, 0.078, 0.05, 0.068))
    panel(c, chain(lambda dt: (Jat(dt)['pel'][0] + Jat(dt)['f'] * 0.02 * H, Jat(dt)['pel'][1] - 0.03 * H), 6, 0.065 * H, 0.02, (0.08 * f, 0.996), t, 0.08, 3.0), 0.05 * H, 0.10 * H, rb, lw, rs, trim=K['trim'])      # 裙前摆
    limb(c, J['neck'], J['head'], 0.022 * H, 0.026 * H, SKIN_S, lw)
    face(c, J, K, lw); hair_cap(c, J, K, lw, ((0.34, -0.82, 0.40, -0.02, 0.2), (0.66, -0.84, 0.78, -0.2, 0.19), (0.9, -0.66, 1.0, -0.24, 0.1)))
    panel(c, chain(lambda dt: (Jat(dt)['head'][0] + Jat(dt)['f'] * r * 0.05, Jat(dt)['head'][1] + r * 0.3), 5, 0.045 * H, 0.03, (0.04 * f, 1.0), t, 0.12, 4.0), 0.016 * H, 0.008 * H, K['hair'], lw * 0.8)          # 鬓发
    c.arc(J['head'][0] - f * r * 0.55, J['head'][1] - r * 0.75, r * 0.2, 0, 7); _ink(c, K['trim'], lw * 0.8)                                       # 发饰
    if held: sword(c, J, lw, bend=J['p'].get('bend', 0.0))
    limb(c, J['s1'], J['e1'], 0.033 * H, 0.032 * H, rb, lw, rs); panel(c, chain(lambda dt: Jat(dt)['h1'], 3, 0.045 * H, 0.03, (-0.2 * f, 0.98), t, 0.15, 5.0), 0.04 * H, 0.016 * H, rs, lw)                    # 宽袖垂下的一角
    limb(c, J['e1'], J['h1'], 0.032 * H, 0.05 * H, rb, lw, rs); hand(c, J['h1'], H, lw)

# ---------- 数据驱动的通用人物：造型写成一个 dict，figure() 照着画
def _look(**o):
    d = dict(hair=(0.1, 0.1, 0.14), hair_hi=(0.4, 0.4, 0.5), iris=(0.2, 0.2, 0.3), robe=(0.9, 0.92, 0.96), robe_s=(0.7, 0.76, 0.86), trim=(0.4, 0.6, 0.8), leg=None, boot=(0.2, 0.2, 0.26), eye_h=0.2, brow=0.07, brow_tilt=0.06, lash=0.09,
             cut='robe', hairdo='long', pads=None, cape=None, beard=None, ghost=False, bow=None, weapon=None, sword=((0.72, 0.97, 0.95), (0.55, 0.8, 0.82), (0.2, 0.32, 0.4)), mark=None, tw=1.0)
    d.update(o); return d
LOOKS = dict(
    nalan=_look(hair=(0.96, 0.32, 0.56), hair_hi=(1.0, 0.66, 0.8), iris=(0.92, 0.2, 0.5), robe=(0.98, 0.98, 1.0), robe_s=(0.80, 0.82, 0.93), trim=(0.36, 0.22, 0.6), leg=(0.97, 0.97, 1.0), boot=(0.9, 0.9, 0.97), eye_h=0.23, brow=0.06, eye_y=0.10,
                cut='short', skirt=((0.9, 0.2, 0.42), (0.68, 0.1, 0.3)), hairdo='twin', pads=(0.95, 0.74, 0.3), bow=(0.9, 0.2, 0.42), weapon='sword', sword=((0.96, 0.98, 1.0), (1.0, 1.0, 1.0), (0.8, 0.14, 0.2))),
    yaolao=_look(hair=(0.96, 0.97, 1.0), hair_hi=(0.8, 0.86, 1.0), iris=(0.8, 0.1, 0.12), robe=(0.16, 0.36, 0.78), robe_s=(0.08, 0.2, 0.55), trim=(0.94, 0.96, 1.0), eye_h=0.16, brow=0.08, brow_tilt=0.1, hairdo='long', ghost=True),
    yunyun=_look(hair=(0.86, 0.95, 0.96), hair_hi=(1, 1, 1), iris=(0.5, 0.3, 0.8), robe=(0.2, 0.4, 0.8), robe_s=(0.1, 0.24, 0.6), trim=(0.94, 0.97, 1.0), leg=(0.2, 0.38, 0.76), boot=(0.9, 0.95, 1.0), eye_h=0.21, brow=0.055, eye_y=0.10,
                 cut='short', skirt=((0.97, 0.98, 1.0), (0.8, 0.86, 0.95)), hairdo='long', pads=(0.5, 0.88, 0.84), cape=((0.55, 0.88, 0.84), (0.36, 0.7, 0.7)), mark=(0.4, 0.8, 0.85), weapon='sword'),
    xuner=_look(hair=(0.16, 0.10, 0.26), hair_hi=(0.45, 0.35, 0.65), iris=(0.3, 0.72, 0.74), robe=(0.97, 0.98, 0.99), robe_s=(0.8, 0.88, 0.9), trim=(0.3, 0.62, 0.6), eye_h=0.23, brow=0.055, eye_y=0.10, cut='robe', hairdo='long'),
    xiaozhan=_look(hair=(0.1, 0.1, 0.13), iris=(0.15, 0.15, 0.2), robe=(0.36, 0.2, 0.2), robe_s=(0.22, 0.1, 0.12), trim=(0.8, 0.66, 0.36), eye_h=0.15, brow=0.11, brow_tilt=0.1, hairdo='bun', beard=(0.1, 0.1, 0.13)),
    geye=_look(hair=(0.7, 0.72, 0.76), iris=(0.2, 0.2, 0.25), robe=(0.9, 0.93, 0.98), robe_s=(0.7, 0.78, 0.9), trim=(0.3, 0.55, 0.75), eye_h=0.13, brow=0.08, hairdo='bun', beard=(0.75, 0.77, 0.8)),
    yunleng=_look(hair=(0.82, 0.84, 0.88), iris=(0.2, 0.2, 0.25), robe=(0.92, 0.95, 1.0), robe_s=(0.7, 0.78, 0.9), trim=(0.3, 0.55, 0.75), eye_h=0.13, brow=0.1, brow_tilt=0.14, hairdo='bun', beard=(0.85, 0.86, 0.9)),
    yunshan=_look(hair=(0.2, 0.2, 0.24), hair_hi=(0.5, 0.5, 0.6), iris=(0.3, 0.5, 0.7), robe=(0.96, 0.97, 1.0), robe_s=(0.72, 0.8, 0.92), trim=(0.75, 0.62, 0.3), eye_h=0.15, brow=0.1, brow_tilt=0.12, hairdo='long', cape=((0.92, 0.95, 1.0), (0.7, 0.78, 0.9))),
    hood=_look(hair=(0.03, 0.03, 0.05), iris=(0.8, 0.1, 0.1), robe=(0.05, 0.05, 0.08), robe_s=(0.02, 0.02, 0.03), trim=(0.3, 0.1, 0.14), hairdo='hood', cape=((0.05, 0.05, 0.08), (0.02, 0.02, 0.03)), skin=(0.1, 0.1, 0.13)),
)
def figure(c, Jat, t, K, held=True, alpha=1.0):
    """按 K（LOOKS 里的一项）画一个人。ghost：没有腿，袍子往下收成一缕（戒指里的药老）。"""
    if alpha < 1 or K.get('ghost'): c.push_group()
    J = Jat(0); H = J['H']; f = J['f']; lw = 0.011 * H; rb, rs, tr = K['robe'], K['robe_s'], K['trim']; r = 0.077 * H; lg = K['leg'] or rs; cut = K['cut']; hd = K['hairdo']; gh = K['ghost']
    pel = lambda dx, dy: (lambda dt: (Jat(dt)['pel'][0] + Jat(dt)['f'] * dx * H, Jat(dt)['pel'][1] + dy * H)); head = lambda dx, dy: (lambda dt: (Jat(dt)['head'][0] + Jat(dt)['f'] * dx * r, Jat(dt)['head'][1] + dy * r))
    if K['cape']: panel(c, chain(lambda dt: (Jat(dt)['neck'][0] - Jat(dt)['f'] * 0.03 * H, Jat(dt)['neck'][1] + 0.02 * H), 8, 0.085 * H, 0.03, (-0.32 * f, 0.95), t, 0.12, 0.3), 0.07 * H, 0.17 * H, K['cape'][1], lw, trim=tr)
    if hd == 'long': panel(c, chain(head(-0.5, -0.1), 9, 0.06 * H, 0.028, (-0.22 * f, 0.975), t, 0.10, 0.5), 0.055 * H, 0.03 * H, K['hair'], lw)
    if hd == 'twin': panel(c, chain(head(-0.7, -0.7), 12, 0.07 * H, 0.03, (-0.5 * f, 0.87), t, 0.14, 0.9), 0.04 * H, 0.014 * H, K['hair'], lw)                 # 远侧的马尾
    limb(c, J['s2'], J['e2'], 0.03 * H, 0.03 * H, rs, lw); limb(c, J['e2'], J['h2'], 0.03 * H, 0.04 * H, rs, lw); hand(c, J['h2'], H, lw)
    if not gh:
        limb(c, J['p2'], J['k2'], 0.044 * H, 0.035 * H, lg if cut == 'short' else rs, lw); limb(c, J['k2'], J['f2'], 0.033 * H, 0.027 * H, lg if cut == 'short' else rs, lw); limb(c, J['f2'], J['t2'], 0.025 * H, 0.018 * H, K['boot'], lw)
    if cut == 'robe' or gh: panel(c, chain(pel(-0.03, -0.03), 7 if not gh else 9, 0.062 * H, 0.024, (-0.3 * f, 0.955), t, 0.10, 1.0), 0.055 * H, 0.12 * H if not gh else 0.012 * H, rs, lw, trim=None if gh else tr)
    if not gh: limb(c, J['p1'], J['k1'], 0.047 * H, 0.037 * H, lg if cut == 'short' else rb, lw, None if cut == 'short' else rs); limb(c, J['k1'], J['f1'], 0.035 * H, 0.028 * H, lg if cut == 'short' else rb, lw); limb(c, J['f1'], J['t1'], 0.026 * H, 0.019 * H, K['boot'], lw)
    if cut == 'short':                                                                  # 短裙：两片随腿摆的裙片
        for (dx, rest, ph) in ((-0.035, (-0.5 * f, 0.87), 1.0), (0.035, (0.35 * f, 0.94), 3.0)): panel(c, chain(pel(dx, -0.03), 3, 0.055 * H, 0.02, rest, t, 0.12, ph), 0.06 * H, 0.10 * H, K['skirt'][0], lw, K['skirt'][1])
    torso(c, J, rb, rs, lw, collar=tr, inner=K.get('inner', (0.95, 0.95, 0.97)), belt=tr, w=(0.066, 0.08, 0.052, 0.068) if cut == 'short' else (0.074, 0.088, 0.062, 0.076))
    if cut == 'robe' and not gh: panel(c, chain(pel(0.02, -0.03), 6, 0.065 * H, 0.02, (0.08 * f, 0.996), t, 0.08, 3.0), 0.05 * H, 0.10 * H, rb, lw, rs, trim=tr)
    if K['bow']: n = J['neck']; c.move_to(n[0] + f * 0.02 * H, n[1] + 0.03 * H); c.rel_line_to(-0.04 * H, -0.03 * H); c.rel_line_to(0, 0.06 * H); c.close_path(); c.move_to(n[0] + f * 0.02 * H, n[1] + 0.03 * H); c.rel_line_to(0.04 * H, -0.03 * H); c.rel_line_to(0, 0.06 * H); c.close_path(); _ink(c, K['bow'], lw * 0.8)
    if K.get('skin'): c.arc(J['head'][0], J['head'][1], r * 1.02, 0, 7); _ink(c, K['skin'], lw)
    else: limb(c, J['neck'], J['head'], 0.022 * H, 0.026 * H, SKIN_S, lw); face(c, J, K, lw)
    if hd == 'hood':
        r0 = _head_ctx(c, J); c.new_path(); c.move_to(0.9, -0.6); c.curve_to(0.6, -1.5, -1.3, -1.5, -1.3, 0.2); c.line_to(-1.1, 1.3); c.line_to(0.1, 1.2); c.curve_to(-0.3, 0.4, 0.2, -0.3, 0.9, -0.6); c.close_path(); _ink(c, K['robe'], lw / r0); c.arc(0.5, 0.1, 0.1, 0, 7); c.set_source_rgb(*K['iris']); c.fill(); c.restore()
    else:
        hair_cap(c, J, K, lw, ((0.34, -0.82, 0.40, -0.02, 0.2), (0.66, -0.84, 0.78, -0.2, 0.19), (0.9, -0.66, 1.0, -0.24, 0.1)) if not K['beard'] else ((0.5, -0.9, 0.6, -0.5, 0.2),))
        if hd in ('long', 'twin'): panel(c, chain(head(0.05, 0.3), 5, 0.045 * H, 0.03, (0.04 * f, 1.0), t, 0.12, 4.0), 0.016 * H, 0.008 * H, K['hair'], lw * 0.8)
        if hd == 'twin': c.arc(J['head'][0] - f * r * 0.55, J['head'][1] - r * 0.95, r * 0.3, 0, 7); _ink(c, K['hair'], lw); panel(c, chain(head(-0.55, -0.95), 12, 0.07 * H, 0.026, (-0.42 * f, 0.9), t, 0.14, 0.2), 0.05 * H, 0.016 * H, K['hair'], lw)
        if hd == 'bun': c.arc(J['head'][0] - f * r * 0.3, J['head'][1] - r * 1.25, r * 0.36, 0, 7); _ink(c, K['hair'], lw)
        if K['beard']: panel(c, chain(head(0.72, 0.9), 3, 0.035 * H, 0.03, (0.1 * f, 0.99), t, 0.1, 2.0), 0.03 * H, 0.006 * H, K['beard'], lw * 0.8)
        if K['mark']: c.arc(J['head'][0] + f * r * 0.78, J['head'][1] - r * 0.42, r * 0.08, 0, 7); c.set_source_rgb(*K['mark']); c.fill()
    if K['pads']: s1 = J['s1']; c.save(); c.translate(s1[0], s1[1] - 0.01 * H); c.scale(f, 1); c.move_to(-0.07 * H, 0.015 * H); c.curve_to(-0.06 * H, -0.05 * H, 0.04 * H, -0.05 * H, 0.06 * H, 0.0); c.curve_to(0.03 * H, 0.03 * H, -0.03 * H, 0.035 * H, -0.07 * H, 0.015 * H); c.close_path(); c.restore(); _ink(c, K['pads'], lw)
    if held and K['weapon'] == 'sword': sword(c, J, lw, bend=J['p'].get('bend', 0.0), col=K['sword'][0], guard=K['sword'][1], hilt=K['sword'][2])
    limb(c, J['s1'], J['e1'], 0.033 * H, 0.032 * H, rb, lw, rs); limb(c, J['e1'], J['h1'], 0.032 * H, 0.046 * H, rb, lw, rs); hand(c, J['h1'], H, lw)
    if alpha < 1 or gh: c.pop_group_to_source(); c.paint_with_alpha(alpha * (0.82 if gh else 1.0))
def nalan(c, Jat, t, held=True): figure(c, Jat, t, LOOKS['nalan'], held)
