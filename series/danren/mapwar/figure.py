"""mapwar.figure — 代码画的"线稿小人"：平涂 + 深色勾边，Q 版比例（约 5 头身），特征鲜明，不用生图。

    figure(c, x, y, h, spec, pose='stand', face=1, t=0)     y 是脚底，h 是全身高（像素），face=1 朝右 / -1 朝左
    spec = dict(robe=颜色, armor=颜色或None, cape=颜色或None, skin, hair, hat='crown'|'helmet'|'bun'|'cap'|None,
                plume=颜色, beard=True/False, brow=True(浓眉), weapon='ji'|'sword'|'flag'|'spear'|'bow'|None, flag=颜色, sleeve='wide'|None, skirt=颜色)
    预设人物：CAST['xiangyu'] 等；姿势：stand / hold(持兵器) / point(指向) / dance(舞) / kneel(跪) / walk / raise(举兵器) / bow(拱手)
小道具：tent / palisade / boat / reeds / fire / flagpole / table，都是同一套勾边平涂画法。
"""
import math
import numpy as np, cairo

OL = (0.20, 0.15, 0.12)                     # 勾边色：深褐
SKIN = (0.93, 0.80, 0.66)
HAIR = (0.13, 0.11, 0.10)


def _ow(h): return max(1.2, h * 0.011)


def shape(c, pts, fill, ol, close=True, curve=False):
    c.move_to(*pts[0])
    if curve and len(pts) >= 3:
        for i in range(1, len(pts) - 1, 2): c.curve_to(*pts[i], *pts[i], *pts[i + 1])
    else:
        for p in pts[1:]: c.line_to(*p)
    if close: c.close_path()
    if fill is not None: c.set_source_rgb(*fill); c.fill_preserve()
    c.set_source_rgb(*OL); c.set_line_width(ol); c.stroke()


def limb(c, pts, w, col, ol):
    """勾边粗线（手臂、腿、兵杆）。"""
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    for lw, cc in ((w + 2 * ol, OL), (w, col)):
        c.set_source_rgb(*cc); c.set_line_width(lw); c.move_to(*pts[0])
        for p in pts[1:]: c.line_to(*p)
        c.stroke()


def disc(c, x, y, r, fill, ol):
    c.arc(x, y, r, 0, 2 * math.pi); c.set_source_rgb(*fill); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(ol); c.stroke()


POSES = {   # 手臂（肩→肘→手）与腿（跨步）参数：(前手肘角, 前手角, 后手肘角, 后手角, 步幅, 身体前倾)
    'stand': (-80, -95, -95, -85, 0.25, 0), 'hold': (-40, 20, -100, -80, 0.3, 0), 'point': (-10, -5, -110, -70, 0.35, 0.05),
    'raise': (-150, -170, -100, -70, 0.45, -0.05), 'walk': (-60, -80, -120, -100, 0.6, 0.06), 'bow': (-30, 40, -30, 40, 0.15, 0.12),
    'dance': (-160, -200, -20, 10, 0.5, -0.1), 'kneel': (-50, 10, -95, -80, 0.0, 0.1), 'ride': (-40, 15, -100, -60, 0.0, 0.0), 'rideup': (-150, -170, -110, -60, 0.0, -0.05)}


def figure(c, x, y, h, spec, pose='stand', face=1, t=0.0):
    u = h / 5.0; ol = _ow(h); f = face; a1, a2, b1, b2, stride, lean = POSES[pose]; bw = spec.get('bulk', 1.0)
    S = dict(spec); robe = S.get('robe', (0.3, 0.45, 0.5)); armor = S.get('armor'); skin = S.get('skin', SKIN)
    kneel = pose == 'kneel'; dy = 0.8 * u if kneel else 0.0
    hip = (x + lean * u * f, y - 2.2 * u + dy); sh = (x + (lean * 2.2) * u * f, y - 3.65 * u + dy); hd = (sh[0] + 0.08 * u * f, y - 4.4 * u + dy)
    sw = math.sin(t * 2.0) * 0.05 * u
    # 披风（最底层）
    if S.get('cape'):
        fl = math.sin(t * 3) * 0.15 * u
        shape(c, [(sh[0] + 0.2 * u * f, sh[1]), (sh[0] - 0.4 * u * f, sh[1] + 0.1 * u), (x - 1.25 * u * f + fl * f, y - 1.0 * u + dy * 0.5), (x - 0.9 * u * f, y - 0.6 * u + dy * 0.5), (x - 0.1 * u * f, y - 2.0 * u + dy)], S['cape'], ol)
    # 后手臂
    def arm(base, e_ang, h_ang, col, front):
        ea, ha = math.radians(e_ang), math.radians(h_ang)
        el = (base[0] + math.cos(ea) * 0.75 * u * f, base[1] - math.sin(-ea) * 0.75 * u * (-1)); el = (base[0] + math.cos(ea) * 0.75 * u * f, base[1] + math.sin(ea) * -0.75 * u * -1)
        el = (base[0] + math.cos(ea) * 0.75 * u * f, base[1] - math.sin(ea) * 0.75 * u)
        hn = (el[0] + math.cos(ha) * 0.7 * u * f, el[1] - math.sin(ha) * 0.7 * u)
        limb(c, [base, el, hn], 0.36 * u if S.get('sleeve') == 'wide' else 0.28 * u, col, ol); disc(c, hn[0], hn[1], 0.13 * u, skin, ol); return hn
    back_sh = (sh[0] - 0.3 * bw * u * f, sh[1] + 0.08 * u); front_sh = (sh[0] + 0.32 * bw * u * f, sh[1] + 0.05 * u)
    hb = arm(back_sh, b1, b2, tuple(np.float32(armor or robe) * 0.82), False)
    # 腿
    legc = S.get('legs', (0.25, 0.22, 0.20))
    if pose in ('ride', 'rideup'):                                                   # 骑马：大腿前伸、小腿垂下
        kx, ky = hip[0] + 0.7 * u * f, hip[1] + 0.35 * u; fx_, fy_ = kx - 0.15 * u * f, ky + 0.95 * u
        limb(c, [hip, (kx, ky), (fx_, fy_)], 0.36 * u, legc, ol); shape(c, [(fx_ - 0.15 * u * f, fy_ + 0.1 * u), (fx_ + 0.35 * u * f, fy_ + 0.1 * u), (fx_ + 0.3 * u * f, fy_ - 0.12 * u), (fx_ - 0.15 * u * f, fy_ - 0.15 * u)], (0.18, 0.15, 0.13), ol)
    elif kneel:
        limb(c, [(hip[0] - 0.1 * u * f, hip[1]), (x - 0.2 * u * f, y - 0.1 * u), (x - 0.9 * u * f, y)], 0.34 * u, legc, ol)
        limb(c, [(hip[0] + 0.15 * u * f, hip[1]), (x + 0.75 * u * f, y - 1.0 * u), (x + 0.8 * u * f, y)], 0.34 * u, legc, ol)
    else:
        ph = math.sin(t * 6) * stride * 0.4 if pose == 'walk' else 0
        for s_, k in ((-1, 0.9), (1, 1.0)):
            fx = x + (s_ * stride + ph * s_) * u * f
            limb(c, [(hip[0] + s_ * 0.18 * u * f, hip[1]), ((hip[0] + fx) / 2 + 0.05 * u * f, y - 1.0 * u), (fx, y - 0.12 * u)], 0.34 * u, tuple(np.float32(legc) * k), ol)
            shape(c, [(fx - 0.18 * u * f, y), (fx + 0.32 * u * f, y), (fx + 0.32 * u * f, y - 0.18 * u), (fx - 0.15 * u * f, y - 0.22 * u)], (0.18, 0.15, 0.13), ol)   # 靴
    # 身体：袍 / 甲
    hem = y - (0.35 * u if not armor else 1.25 * u) + dy * (0.2 if kneel else 1)
    if kneel: hem = y - 0.5 * u
    if pose in ('ride', 'rideup'): hem = hip[1] + 0.55 * u
    flare = 0.75 * u if S.get('sleeve') == 'wide' or not armor else 0.55 * u
    body = [(sh[0] - 0.48 * bw * u, sh[1]), (sh[0] + 0.48 * bw * u, sh[1]), (hip[0] + 0.42 * bw * u, hip[1]), (x + flare * bw + sw, hem), (x - flare * bw + sw, hem), (hip[0] - 0.42 * bw * u, hip[1])]
    shape(c, body, robe, ol)
    if S.get('trim'): shape(c, [(sh[0] - 0.1 * u * f, sh[1]), (sh[0] + 0.12 * u * f, sh[1]), (hip[0] + 0.22 * u * f, hip[1] + 0.1 * u), (x + 0.15 * u * f, hem), (x - 0.02 * u * f, hem), (hip[0] + 0.05 * u * f, hip[1])], S['trim'], ol)
    if armor:
        shape(c, [(sh[0] - 0.5 * bw * u, sh[1] - 0.05 * u), (sh[0] + 0.5 * bw * u, sh[1] - 0.05 * u), (hip[0] + 0.45 * bw * u, hip[1] - 0.1 * u), (hip[0] - 0.45 * bw * u, hip[1] - 0.1 * u)], armor, ol)
        if S.get('gold'):
            c.set_source_rgb(*S['gold']); c.set_line_width(max(1, 0.06 * u)); c.move_to(sh[0] - 0.42 * bw * u, sh[1] + 0.02 * u); c.line_to(hip[0] + 0.05 * u * f, hip[1] - 0.15 * u); c.line_to(sh[0] + 0.42 * bw * u, sh[1] + 0.02 * u); c.stroke()
        c.set_source_rgba(*OL, 0.55); c.set_line_width(ol * 0.6)
        for k in range(1, 4):                                                         # 甲片横纹
            yy = sh[1] + (hip[1] - sh[1]) * k / 4; c.move_to(sh[0] - 0.46 * u + k * 0.01 * u, yy); c.line_to(sh[0] + 0.46 * u, yy)
        c.stroke()
        sk = S.get('skirt', armor)
        sky = hem if pose in ('ride', 'rideup') else y - 1.2 * u + dy
        shape(c, [(hip[0] - 0.47 * bw * u, hip[1] - 0.05 * u), (hip[0] + 0.47 * bw * u, hip[1] - 0.05 * u), (x + 0.62 * bw * u, sky), (x - 0.62 * bw * u, sky)], sk, ol)   # 甲裙
        for s_ in (-1, 1):
            disc(c, sh[0] + s_ * 0.5 * bw * u, sh[1] + 0.05 * u, 0.22 * bw * u, armor, ol)                                            # 肩甲
            if S.get('gold'): c.set_source_rgb(*S['gold']); c.set_line_width(max(1, 0.05 * u)); c.arc(sh[0] + s_ * 0.5 * bw * u, sh[1] + 0.05 * u, 0.15 * bw * u, 0, 2 * math.pi); c.stroke()
    shape(c, [(hip[0] - 0.44 * u, hip[1] - 0.12 * u), (hip[0] + 0.44 * u, hip[1] - 0.12 * u), (hip[0] + 0.44 * u, hip[1] + 0.06 * u), (hip[0] - 0.44 * u, hip[1] + 0.06 * u)], S.get('belt', (0.55, 0.20, 0.15)), ol)   # 腰带
    # 头
    hx, hy = hd; r = 0.55 * u
    shape(c, [(hx - 0.14 * u, hy + 0.45 * u), (hx + 0.14 * u, hy + 0.45 * u), (hx + 0.12 * u, hy + 0.7 * u), (hx - 0.12 * u, hy + 0.7 * u)], skin, ol)   # 脖子
    disc(c, hx, hy, r, skin, ol)
    hair = S.get('hair', HAIR)
    a0, a1_ = (0.85, 1.9) if f > 0 else (1.1, 2.15)
    if S.get('hat') in ('helmet', 'cap'): a0, a1_ = (0.55, 1.15) if f > 0 else (1.85, 2.45)     # 戴盔只露后脑的头发
    c.arc(hx - 0.08 * u * f, hy - 0.05 * u, r * 1.02, math.pi * a0, math.pi * a1_); c.close_path()
    c.set_source_rgb(*hair); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(ol); c.stroke()
    ex = hx + 0.22 * u * f; ey = hy + 0.02 * u                                       # 眼、眉
    for dx in (0, -0.26 * u * f):
        if S.get('eyes') == 'double':                                                 # 重瞳：白眼眶里两颗瞳仁
            c.save(); c.translate(ex + dx, ey); c.scale(1, 0.55); c.arc(0, 0, 0.085 * u, 0, 2 * math.pi); c.restore()
            c.set_source_rgb(0.98, 0.96, 0.9); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(max(0.8, ol * 0.6)); c.stroke()
            for px in (-0.028 * u, 0.028 * u): c.set_source_rgb(*OL); c.arc(ex + dx + px + 0.012 * u * f, ey, max(0.7, 0.03 * u), 0, 2 * math.pi); c.fill()
            if S.get('glint', 0) > 0: c.set_source_rgba(1.0, 0.85, 0.4, S['glint']); c.arc(ex + dx, ey, 0.2 * u, 0, 2 * math.pi); c.fill()
            continue
        c.set_source_rgb(*OL); c.arc(ex + dx, ey, max(0.8, 0.05 * u), 0, 2 * math.pi); c.fill()

    if S.get('blush'): c.set_source_rgba(0.95, 0.55, 0.5, 0.6); c.arc(ex + 0.02 * u * f, ey + 0.17 * u, 0.08 * u, 0, 2 * math.pi); c.fill()
    if S.get('beard') == 'full':                                                      # 满髯
        shape(c, [(hx - 0.12 * u * f, hy + 0.36 * u), (hx + 0.44 * u * f, hy + 0.3 * u), (hx + 0.36 * u * f, hy + 0.72 * u), (hx + 0.24 * u * f, hy + 0.62 * u), (hx + 0.16 * u * f, hy + 0.85 * u), (hx + 0.06 * u * f, hy + 0.66 * u), (hx - 0.05 * u * f, hy + 0.72 * u)], hair, ol)
        c.set_source_rgb(*OL); c.set_line_width(max(1, 0.06 * u)); c.move_to(hx + 0.02 * u * f, hy + 0.28 * u); c.curve_to(hx + 0.2 * u * f, hy + 0.2 * u, hx + 0.3 * u * f, hy + 0.22 * u, hx + 0.45 * u * f, hy + 0.32 * u); c.stroke()
    elif S.get('beard'): shape(c, [(hx + 0.08 * u * f, hy + 0.36 * u), (hx + 0.36 * u * f, hy + 0.32 * u), (hx + 0.24 * u * f, hy + 0.9 * u), (hx + 0.1 * u * f, hy + 0.72 * u)], hair, ol)
    hat = S.get('hat')
    if hat == 'crown':                                                                # 刘氏冠：高而窄的竹皮冠，向后斜
        M = lambda d: hx + d * u * f
        shape(c, [(M(-0.3), hy - 0.4 * u), (M(0.2), hy - 0.44 * u), (M(0.02), hy - 1.3 * u), (M(-0.36), hy - 1.24 * u)], (0.12, 0.10, 0.09), ol)
        c.set_source_rgb(0.6, 0.15, 0.12); c.set_line_width(max(1, 0.035 * u)); c.move_to(M(-0.3), hy - 0.38 * u); c.line_to(M(-0.12), hy + 0.5 * u); c.stroke()
    elif hat == 'helmet':                                                             # 盔 + 雉尾翎
        M = lambda d: hx + d * u * f
        shape(c, [(M(-0.62), hy + 0.05 * u), (M(-0.52), hy - 0.5 * u), (M(0.0), hy - 0.72 * u), (M(0.5), hy - 0.5 * u), (M(0.6), hy - 0.12 * u), (M(0.28), hy - 0.22 * u), (M(-0.3), hy - 0.18 * u), (M(-0.4), hy + 0.1 * u)], S.get('helm', armor or (0.3, 0.32, 0.35)), ol)
        disc(c, hx, hy - 0.78 * u, 0.1 * u, (0.85, 0.65, 0.2), ol * 0.7)
        if S.get('plume'):
            w = math.sin(t * 2.5) * 0.15 * u
            for k, s_ in enumerate((1, -1)):
                pts = [(hx + 0.05 * u * s_, hy - 0.8 * u), (hx - (0.25 + 0.15 * k) * u * f + s_ * 0.08 * u, hy - 1.55 * u + w), (hx - (0.85 + 0.25 * k) * u * f + w, hy - 1.75 * u - 0.12 * k * u)]
                c.set_line_cap(cairo.LINE_CAP_ROUND)
                for lw, cc in ((0.1 * u + 2 * ol, OL), (0.1 * u, S['plume'])):
                    c.set_source_rgb(*cc); c.set_line_width(lw); c.move_to(*pts[0]); c.curve_to(*pts[1], *pts[1], *pts[2]); c.stroke()
    elif hat == 'bun':                                                                # 发髻 + 簪
        disc(c, hx - 0.15 * u * f, hy - 0.62 * u, 0.3 * u, hair, ol); limb(c, [(hx - 0.55 * u * f, hy - 0.75 * u), (hx + 0.25 * u * f, hy - 0.55 * u)], 0.04 * u, (0.85, 0.7, 0.3), ol * 0.5)
        if S.get('flower'): disc(c, hx + 0.2 * u * f, hy - 0.62 * u, 0.1 * u, S['flower'], ol * 0.7)
    elif hat == 'cap':                                                                # 士卒巾帻
        shape(c, [(hx - 0.55 * u, hy - 0.05 * u), (hx - 0.45 * u, hy - 0.5 * u), (hx + 0.45 * u, hy - 0.5 * u), (hx + 0.55 * u, hy - 0.05 * u)], S.get('capc', (0.2, 0.2, 0.22)), ol)
    if S.get('brow'):                                                                 # 剑眉倒竖（画在盔之后）
        c.set_source_rgb(*OL); c.set_line_width(max(1, 0.075 * u))
        for dx in (0, -0.26 * u * f):
            c.move_to(ex + dx - 0.11 * u * f, ey - 0.09 * u); c.line_to(ex + dx + 0.11 * u * f, ey - 0.17 * u) if dx == 0 else c.line_to(ex + dx - 0.0 * u * f, ey - 0.16 * u)
            c.stroke()
    # 前手臂 + 兵器
    hf = arm(front_sh, a1, a2, armor or robe, True)
    wpn = S.get('weapon')
    if wpn in ('ji', 'spear'):
        up_ = pose in ('raise', 'rideup'); L_ = S.get('wlen', 1.0)
        top = (hf[0] + 0.15 * u * f, hf[1] - 2.6 * u * L_) if not up_ else (hf[0] + 2.2 * u * f * L_, hf[1] - 1.6 * u * L_)
        bot = (hf[0] - 0.1 * u * f, hf[1] + 1.4 * u) if not up_ else (hf[0] - 1.1 * u * f, hf[1] + 0.8 * u)
        limb(c, [bot, top], 0.07 * u * S.get('wthick', 1.0), (0.45, 0.30, 0.18) if not S.get('shaft') else S['shaft'], ol * 0.8)
        dx, dy_ = top[0] - bot[0], top[1] - bot[1]; L = math.hypot(dx, dy_); ux, uy = dx / L, dy_ / L; px, py = -uy, ux
        K = S.get('wscale', 1.0)
        shape(c, [(top[0] + ux * 0.45 * u * K, top[1] + uy * 0.45 * u * K), (top[0] + px * 0.08 * u * K, top[1] + py * 0.08 * u * K), (top[0] - px * 0.08 * u * K, top[1] - py * 0.08 * u * K)], (0.70, 0.74, 0.80), ol * 0.8)
        if wpn == 'ji':                                                               # 戟的月牙侧刃
            b0 = (top[0] - ux * 0.25 * u * K, top[1] - uy * 0.25 * u * K); sd = f if not up_ else -f
            R0 = 0.3 * u * K; cx_, cy_ = b0[0] + px * 0.06 * u * K * sd - ux * 0.12 * u * K, b0[1] + py * 0.06 * u * K * sd - uy * 0.12 * u * K
            outer = [(cx_ + (px * math.sin(a) * sd + ux * math.cos(a)) * R0, cy_ + (py * math.sin(a) * sd + uy * math.cos(a)) * R0) for a in np.linspace(0.15, math.pi - 0.15, 9)]
            inner = [(cx_ + px * 0.2 * u * K * sd + (px * math.sin(a) * sd + ux * math.cos(a)) * R0 * 0.55, cy_ + py * 0.2 * u * K * sd + (py * math.sin(a) * sd + uy * math.cos(a)) * R0 * 0.55) for a in np.linspace(math.pi - 0.3, 0.3, 9)]
            shape(c, outer + inner, (0.70, 0.74, 0.80), ol * 0.8)
        tr = (top[0] - ux * 0.45 * u * K, top[1] - uy * 0.45 * u * K); wv = math.sin(t * 4) * 0.1 * u
        if S.get('tassel'): shape(c, [tr, (tr[0] - px * 0.25 * u * K * f - ux * 0.1 * u + wv, tr[1] - py * 0.25 * u * K * f + 0.35 * u * K), (tr[0] + px * 0.1 * u * K * f + wv, tr[1] + 0.45 * u * K)], S['tassel'], ol * 0.6)
        else: disc(c, tr[0], tr[1], 0.09 * u, (0.75, 0.15, 0.12), ol * 0.6)   # 红缨
    elif wpn == 'sword':
        tip = (hf[0] + 1.3 * u * f, hf[1] - 0.9 * u) if pose in ('dance', 'raise', 'point') else (hf[0] + 0.2 * u * f, hf[1] + 1.3 * u)
        limb(c, [hf, tip], 0.07 * u, (0.82, 0.84, 0.86), ol * 0.8)
    elif wpn == 'flag':
        top = (hf[0], hf[1] - 2.8 * u); limb(c, [(hf[0], hf[1] + 1.2 * u), top], 0.07 * u, (0.45, 0.30, 0.18), ol * 0.8)
        wv = math.sin(t * 3) * 0.12 * u
        shape(c, [top, (top[0] - 1.4 * u * f, top[1] + 0.15 * u + wv), (top[0] - 1.35 * u * f, top[1] + 1.0 * u - wv), (top[0], top[1] + 0.9 * u)], S.get('flag', (0.75, 0.15, 0.12)), ol)
    if pose == 'dance':                                                               # 水袖
        wv = math.sin(t * 2.5) * 0.3 * u
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for hand, s_ in ((hf, 1), (hb, -1)):
            pts = [hand, (hand[0] + 0.8 * u * f * s_, hand[1] - 0.6 * u + wv), (hand[0] + 1.4 * u * f * s_, hand[1] + 0.8 * u - wv)]
            for lw, cc in ((0.16 * u + 2 * ol, OL), (0.16 * u, S.get('sleevec', (0.95, 0.93, 0.88)))):
                c.set_source_rgb(*cc); c.set_line_width(lw); c.move_to(*pts[0]); c.curve_to(*pts[1], *pts[1], *pts[2]); c.stroke()
    return hd


CAST = {
    'xiangyu': dict(robe=(0.14, 0.13, 0.14), armor=(0.17, 0.16, 0.18), helm=(0.15, 0.14, 0.16), skirt=(0.22, 0.20, 0.22), gold=(0.85, 0.66, 0.25), cape=(0.70, 0.10, 0.08),
                    hat='helmet', plume=(0.80, 0.60, 0.25), brow=True, eyes='double', beard='full', bulk=1.3, weapon='ji', wlen=1.25, wscale=1.6, wthick=1.6,
                    shaft=(0.12, 0.10, 0.10), tassel=(0.75, 0.12, 0.10), legs=(0.14, 0.13, 0.14), belt=(0.85, 0.66, 0.25)),
    'liubang': dict(robe=(0.55, 0.14, 0.12), trim=(0.12, 0.10, 0.09), hat='crown', beard=True, weapon='sword', sleeve='wide', belt=(0.12, 0.10, 0.09), legs=(0.12, 0.10, 0.09)),
    'hanxin': dict(robe=(0.25, 0.40, 0.45), armor=(0.40, 0.48, 0.50), helm=(0.30, 0.36, 0.38), hat='helmet', plume=(0.70, 0.15, 0.12), weapon='flag', flag=(0.72, 0.14, 0.12), belt=(0.55, 0.2, 0.15)),
    'yuji': dict(robe=(0.92, 0.86, 0.84), trim=(0.75, 0.30, 0.35), hat='bun', flower=(0.85, 0.30, 0.35), weapon='sword', sleeve='wide', sleevec=(0.96, 0.94, 0.92), blush=True, belt=(0.75, 0.30, 0.35), legs=(0.85, 0.75, 0.75)),
    'zhangliang': dict(robe=(0.35, 0.50, 0.48), trim=(0.92, 0.90, 0.85), hat='crown', beard=True, sleeve='wide', belt=(0.2, 0.3, 0.3)),
    'chu_soldier': dict(robe=(0.20, 0.30, 0.48), armor=(0.30, 0.34, 0.40), hat='cap', capc=(0.15, 0.22, 0.38), weapon='spear', belt=(0.4, 0.3, 0.2)),
    'han_soldier': dict(robe=(0.60, 0.18, 0.14), armor=(0.42, 0.36, 0.30), hat='cap', capc=(0.45, 0.12, 0.10), weapon='spear', belt=(0.4, 0.3, 0.2)),
    'boatman': dict(robe=(0.55, 0.50, 0.40), hat='cap', capc=(0.35, 0.30, 0.22), beard=True, belt=(0.4, 0.3, 0.2)),
}


# ---------------------------------------------------------------- 道具
def tent(c, x, y, w, col=(0.86, 0.80, 0.66), h=None):
    h = h or w * 0.75; ol = _ow(w * 0.9)
    shape(c, [(x - w / 2, y), (x - w * 0.42, y - h * 0.55), (x, y - h), (x + w * 0.42, y - h * 0.55), (x + w / 2, y)], col, ol)
    shape(c, [(x - w * 0.12, y), (x, y - h * 0.5), (x + w * 0.12, y)], tuple(np.float32(col) * 0.55), ol)
    limb(c, [(x, y - h), (x, y - h * 1.25)], w * 0.02, (0.45, 0.3, 0.18), ol * 0.6)


def palisade(c, x0, x1, y, h, n=None):
    n = n or int(abs(x1 - x0) / (h * 0.18)); ol = _ow(h * 2)
    for k in range(n):
        x = x0 + (x1 - x0) * k / max(1, n - 1); hh = h * (0.9 + 0.2 * ((k * 7) % 3) / 2)
        shape(c, [(x - h * 0.06, y), (x - h * 0.06, y - hh), (x, y - hh - h * 0.12), (x + h * 0.06, y - hh), (x + h * 0.06, y)], (0.55, 0.40, 0.26), ol)
    limb(c, [(x0, y - h * 0.65), (x1, y - h * 0.65)], h * 0.05, (0.45, 0.32, 0.2), ol)


def boat(c, x, y, w):
    ol = _ow(w * 0.6)
    shape(c, [(x - w / 2, y - w * 0.12), (x + w / 2, y - w * 0.16), (x + w * 0.4, y), (x - w * 0.38, y + w * 0.02)], (0.50, 0.36, 0.22), ol)
    shape(c, [(x - w * 0.15, y - w * 0.13), (x - w * 0.12, y - w * 0.32), (x + w * 0.18, y - w * 0.32), (x + w * 0.2, y - w * 0.14)], (0.78, 0.70, 0.52), ol)


def reeds(c, x0, x1, y, h, seed=0, t=0.0):
    r = np.random.default_rng(seed); ol = _ow(h * 1.5)
    for k in range(int(abs(x1 - x0) / (h * 0.08))):
        x = x0 + r.random() * (x1 - x0); hh = h * r.uniform(0.6, 1.1); lean = (r.random() - 0.5) * h * 0.3 + math.sin(t * 1.5 + k) * h * 0.04
        limb(c, [(x, y), (x + lean * 0.5, y - hh * 0.6), (x + lean, y - hh)], h * 0.025, (0.55, 0.52, 0.36), ol * 0.5)
        if r.random() < 0.5: shape(c, [(x + lean, y - hh), (x + lean + h * 0.05, y - hh - h * 0.18), (x + lean - h * 0.03, y - hh - h * 0.15)], (0.80, 0.72, 0.55), ol * 0.5)


def fire(c, x, y, s, t=0.0):
    ol = _ow(s * 3)
    for k in range(3): limb(c, [(x - s * 0.6 + k * s * 0.6, y), (x + s * 0.6 - k * s * 0.6, y - s * 0.25)], s * 0.12, (0.4, 0.28, 0.18), ol * 0.6)
    fl = math.sin(t * 9) * s * 0.1
    shape(c, [(x - s * 0.45, y - s * 0.1), (x - s * 0.2 + fl, y - s * 0.9), (x, y - s * 0.55), (x + s * 0.15 - fl, y - s * 1.2), (x + s * 0.45, y - s * 0.1)], (0.95, 0.55, 0.15), ol * 0.7)
    shape(c, [(x - s * 0.2, y - s * 0.1), (x + fl, y - s * 0.6), (x + s * 0.2, y - s * 0.1)], (1.0, 0.85, 0.35), ol * 0.5)


def flagpole(c, x, y, h, col, t=0.0, face=1):
    ol = _ow(h * 0.8); limb(c, [(x, y), (x, y - h)], h * 0.025, (0.45, 0.30, 0.18), ol * 0.7)
    wv = math.sin(t * 3 + x) * h * 0.04
    shape(c, [(x, y - h), (x + h * 0.42 * face, y - h * 0.96 + wv), (x + h * 0.4 * face, y - h * 0.62 - wv), (x, y - h * 0.66)], col, ol)


def table(c, x, y, w, col=(0.45, 0.28, 0.18)):
    ol = _ow(w * 0.7)
    shape(c, [(x - w / 2, y - w * 0.3), (x + w / 2, y - w * 0.3), (x + w / 2, y - w * 0.36), (x - w / 2, y - w * 0.36)], col, ol)
    for s_ in (-1, 1): limb(c, [(x + s_ * w * 0.4, y - w * 0.3), (x + s_ * w * 0.4, y)], w * 0.04, col, ol * 0.6)


def horse(c, x, y, h, col=(0.10, 0.09, 0.10), t=0.0, gait='gallop', face=1, rear=0.0, saddle=(0.70, 0.12, 0.10), trim=(0.85, 0.66, 0.25), dapple=True, mane=None):
    """侧面的马（勾边平涂）。y 是蹄底，h 是肩高。gait: gallop / walk / stand；rear 0..1 人立。返回鞍座点（骑手 hip）。"""
    ol = _ow(h * 1.4); c.save(); c.translate(x, y); c.scale(face, 1)
    hind = (-0.45 * h, 0.0)
    if rear > 0:
        c.translate(*hind); c.rotate(-math.radians(32) * rear); c.translate(-hind[0], -hind[1])
    ph = t * (11 if gait == 'gallop' else 5); amp = {'gallop': 1.0, 'walk': 0.45, 'stand': 0.0}[gait]
    bob = abs(math.sin(ph)) * 0.04 * h * amp; by = -0.75 * h - bob
    dark = tuple(np.float32(col) * 0.75)
    def leg(hx, phase, front, near):
        cc = col if near else dark; sw_ = math.sin(ph + phase) * amp
        if rear > 0 and front: sw_ = 0.9 * rear + sw_ * (1 - rear)
        knee = (hx + 0.12 * h * sw_, by + 0.38 * h); hoof = (hx + (0.28 * h * sw_ if front else 0.2 * h * sw_) - (0.05 * h if front else -0.05 * h), -0.02 * h - (0.18 * h * rear if front else 0))
        if rear > 0 and front: knee = (hx + 0.3 * h * rear, by + 0.25 * h); hoof = (hx + 0.2 * h * rear, by + 0.5 * h)
        limb(c, [(hx, by + 0.1 * h), knee, hoof], 0.085 * h, cc, ol); shape(c, [(hoof[0] - 0.05 * h, hoof[1] + 0.02 * h), (hoof[0] + 0.07 * h, hoof[1] + 0.02 * h), (hoof[0] + 0.05 * h, hoof[1] - 0.05 * h), (hoof[0] - 0.05 * h, hoof[1] - 0.05 * h)], (0.15, 0.12, 0.1), ol * 0.7)
    leg(0.38 * h, 1.9, True, False); leg(-0.45 * h, 3.4, False, False)
    tw = math.sin(t * 5) * 0.06 * h; ta = 0.25 * h * amp
    for k in range(3):                                                                                                                               # 马尾：几缕飘动
        w_ = (k - 1) * 0.05 * h; pts = [(-0.62 * h, by - 0.1 * h), (-0.85 * h - ta * 0.6, by - 0.12 * h + tw + w_), (-1.0 * h - ta, by + 0.25 * h + tw * 1.5 + w_)]
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for lw, cc in ((0.06 * h + 2 * ol, OL), (0.06 * h, dark)): c.set_source_rgb(*cc); c.set_line_width(lw); c.move_to(*pts[0]); c.curve_to(*pts[1], *pts[1], *pts[2]); c.stroke()
    c.save(); c.translate(0, by); c.scale(1, 0.4); c.arc(0, 0, 0.66 * h, 0, 2 * math.pi); c.restore()                                                       # 马身
    c.set_source_rgb(*col); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(ol); c.stroke()
    nk = [(0.3 * h, by - 0.22 * h), (0.55 * h, by - 0.62 * h), (0.74 * h, by - 0.76 * h), (0.8 * h, by - 0.55 * h), (0.66 * h, by - 0.2 * h), (0.6 * h, by + 0.12 * h)]
    shape(c, nk, col, ol)                                                                                                                            # 马颈
    shape(c, [(0.62 * h, by - 0.66 * h), (0.80 * h, by - 0.78 * h), (1.10 * h, by - 0.50 * h), (1.10 * h, by - 0.40 * h), (1.0 * h, by - 0.36 * h), (0.74 * h, by - 0.46 * h)], col, ol)   # 马头
    shape(c, [(0.70 * h, by - 0.74 * h), (0.68 * h, by - 0.9 * h), (0.77 * h, by - 0.78 * h)], col, ol * 0.8)                                       # 耳
    c.set_source_rgb(0.95, 0.9, 0.8); c.arc(0.86 * h, by - 0.63 * h, 0.025 * h, 0, 2 * math.pi); c.fill()                                           # 眼
    mc = mane or tuple(np.float32(col) * 0.5)
    for k in range(7):                                                                                                                               # 鬃毛：沿颈背的飘发
        u_ = k / 6; bx, byy = 0.33 * h + 0.4 * h * u_, by - 0.25 * h - 0.5 * h * u_; fl = math.sin(t * 6 + k) * 0.03 * h
        pts = [(bx, byy), (bx - 0.12 * h - 0.06 * h * amp, byy - 0.04 * h + fl), (bx - 0.22 * h - 0.1 * h * amp, byy + 0.04 * h + fl)]
        for lw, cc in ((0.045 * h + 2 * ol * 0.6, OL), (0.045 * h, mc)): c.set_source_rgb(*cc); c.set_line_width(lw); c.move_to(*pts[0]); c.curve_to(*pts[1], *pts[1], *pts[2]); c.stroke()
    if dapple:
        r = np.random.default_rng(3)
        for k in range(14):
            px, py = r.uniform(-0.5, 0.4) * h, r.uniform(-0.15, 0.12) * h
            c.set_source_rgba(0.85, 0.85, 0.82, 0.35); c.arc(px, by + py, r.uniform(0.02, 0.045) * h, 0, 2 * math.pi); c.fill()
    shape(c, [(-0.22 * h, by - 0.27 * h), (0.25 * h, by - 0.27 * h), (0.3 * h, by + 0.12 * h), (-0.27 * h, by + 0.12 * h)], saddle, ol)          # 鞍鞯
    if trim: c.set_source_rgb(*trim); c.set_line_width(max(1, 0.02 * h)); c.move_to(-0.26 * h, by + 0.08 * h); c.line_to(0.29 * h, by + 0.08 * h); c.stroke()
    limb(c, [(1.02 * h, by - 0.42 * h), (0.3 * h, by - 0.3 * h)], 0.012 * h, (0.3, 0.2, 0.12), ol * 0.4)                                            # 缰绳
    leg(0.45 * h, 0.0, True, True); leg(-0.38 * h, 1.4, False, True)
    c.restore()
    px, py = 0.0, by - 0.27 * h
    if rear > 0:
        a = -math.radians(32) * rear; dx, dy = px - hind[0], py - hind[1]
        px, py = hind[0] + dx * math.cos(a) - dy * math.sin(a), hind[1] + dx * math.sin(a) + dy * math.cos(a)
    return (x + px * face, y + py), (-math.radians(32) * rear) * face
