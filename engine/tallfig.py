"""tallfig — 写实比例（约 7.5 头身）的侧面人物，cairo 平涂；明暗和轮廓光在合成时按 alpha 做（见 looks.py）。
    fig(c, x, y, H, S, pose, face=1, P=None, mono=None)   y = 脚底；face=1 朝右；mono=(r,g,b) 时整个人画成纯色剪影
角度：0 = 朝下，正 = 朝前（脸的方向），180 = 朝上。
"""
import math, cairo

SKIN = (0.78, 0.63, 0.52); STEEL = (0.80, 0.84, 0.88); GOLD = (0.86, 0.66, 0.22)
def mix(a, b, k): return tuple(a[i] * (1 - k) + b[i] * k for i in range(3))

POSES = {
    'stand': dict(lean=2, head=0, af=(4, 10), ab=(-8, -2), lf=(5, 2), lb=(-5, -8)),
    'walk': dict(lean=4, head=0, af=(-20, -6), ab=(22, 38), lf=(22, 6), lb=(-18, -34)),
    'point': dict(lean=3, head=-3, af=(80, 86), ab=(-10, -4), lf=(8, 2), lb=(-8, -12)),
    'kneel': dict(lean=14, head=28, af=(-24, -50), ab=(-28, -54), lf=(8, -92), lb=(4, -94)),
    'kneel1': dict(lean=8, head=18, af=(20, 40), ab=(-14, -6), lf=(86, 0), lb=(6, -94)),
    'strike': dict(lean=-5, head=8, af=(152, 184), ab=(146, 180), lf=(16, 4), lb=(-14, -22)),
    'reach': dict(lean=16, head=-4, af=(74, 84), ab=(62, 76), lf=(20, 8), lb=(-20, -30)),
    'hold': dict(lean=5, head=4, af=(48, 80), ab=(40, 74), lf=(10, 2), lb=(-9, -14)),
    'guard': dict(lean=0, head=0, af=(28, 92), ab=(-6, 0), lf=(4, 1), lb=(-4, -6)),
    'bow': dict(lean=20, head=16, af=(8, 24), ab=(-4, 8), lf=(5, 2), lb=(-5, -8)),
}


def sword(c, hand, ang, L, face=1, col=STEEL, hilt=(0.16, 0.14, 0.14), w=None):
    """ang：剑尖方向（0=朝下，180=朝上）。"""
    w = w or L * 0.050; r = math.radians(ang); d = (math.sin(r) * face, math.cos(r)); n = (-d[1], d[0])
    def P(u, v): return (hand[0] + d[0] * u + n[0] * v, hand[1] + d[1] * u + n[1] * v)
    c.set_source_rgb(*hilt); c.set_line_width(w * 0.8); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(*P(-L * 0.20, 0)); c.line_to(*P(L * 0.03, 0)); c.stroke()
    c.arc(*P(-L * 0.21, 0), w * 0.6, 0, math.tau); c.fill()
    c.set_line_width(w * 0.7); c.move_to(*P(L * 0.03, -w * 2.4)); c.line_to(*P(L * 0.03, w * 2.4)); c.stroke()
    c.set_source_rgb(*col); c.move_to(*P(L * 0.04, -w / 2)); c.line_to(*P(L * 0.93, -w * 0.36)); c.line_to(*P(L, 0)); c.line_to(*P(L * 0.93, w * 0.36)); c.line_to(*P(L * 0.04, w / 2)); c.close_path(); c.fill()
    c.set_source_rgba(*mix(col, (0, 0, 0), 0.35), 0.8); c.set_line_width(w * 0.16); c.move_to(*P(L * 0.06, 0)); c.line_to(*P(L * 0.72, 0)); c.stroke()
    return P(L, 0)


def _head(c, S, K):
    """头部局部坐标：头高 = 1，头心在原点，朝 +x，y 向下。"""
    skin = S.get('skin', SKIN); hair = S.get('hair', (0.20, 0.15, 0.11)); hs = S.get('hairstyle', 'short')
    if hs == 'long':                                                                    # 长发后片
        L = S.get('hairlen', 1.9); K(hair)
        c.move_to(-0.10, -0.46); c.curve_to(-0.50, -0.46, -0.58, 0.0, -0.52, 0.45); c.curve_to(-0.50, L * 0.6, -0.62, L * 0.85, -0.50, L); c.curve_to(-0.30, L * 1.04, -0.14, L * 0.9, -0.12, L * 0.7); c.curve_to(-0.10, 0.6, -0.06, 0.3, -0.02, 0.1); c.close_path(); c.fill()
    K(skin)
    c.move_to(0.02, -0.50); c.curve_to(0.20, -0.50, 0.33, -0.40, 0.355, -0.24)
    for p in ((0.385, -0.12), (0.345, -0.05), (0.49, 0.10), (0.385, 0.155), (0.405, 0.21), (0.36, 0.25), (0.39, 0.30), (0.35, 0.35), (0.375, 0.43), (0.29, 0.50), (0.02, 0.43), (-0.12, 0.28), (-0.28, 0.26)): c.line_to(*p)
    c.curve_to(-0.42, 0.20, -0.50, 0.0, -0.47, -0.20); c.curve_to(-0.44, -0.40, -0.20, -0.50, 0.02, -0.50); c.close_path(); c.fill()
    K(mix(skin, (0.25, 0.12, 0.08), 0.28)); c.save(); c.translate(-0.10, 0.03); c.scale(0.055, 0.085); c.arc(0, 0, 1, 0, math.tau); c.restore(); c.fill()       # 耳
    K(mix(skin, (0.2, 0.1, 0.08), 0.22)); c.move_to(0.02, 0.43); c.line_to(-0.12, 0.28); c.line_to(0.10, 0.30); c.line_to(0.29, 0.50); c.close_path(); c.fill()   # 下颌阴影面
    bd = S.get('beard')
    if bd:
        K(bd); c.move_to(-0.07, 0.06); c.line_to(-0.15, 0.30); c.line_to(-0.02, 0.50); c.line_to(0.20, 0.58 + S.get('beardlen', 0)); c.line_to(0.40, 0.52); c.line_to(0.44, 0.40)
        c.line_to(0.40, 0.31); c.line_to(0.33, 0.27); c.line_to(0.41, 0.25); c.line_to(0.44, 0.20); c.line_to(0.39, 0.165); c.line_to(0.27, 0.20); c.line_to(0.12, 0.14); c.line_to(0.02, 0.06); c.close_path(); c.fill()
    K((0.07, 0.05, 0.05)); c.move_to(0.20, -0.075); c.line_to(0.315, -0.07); c.line_to(0.30, -0.035); c.line_to(0.22, -0.045); c.close_path(); c.fill()      # 眼
    K(mix(hair, (0, 0, 0), 0.35) if hs != 'bald' else (0.25, 0.2, 0.18)); c.move_to(0.15, -0.135); c.line_to(0.375, -0.125); c.line_to(0.37, -0.165); c.line_to(0.18, -0.175); c.close_path(); c.fill()   # 眉
    if hs in ('short', 'ned', 'long'):
        K(hair); c.move_to(0.335, -0.31); c.curve_to(0.30, -0.50, 0.10, -0.56, -0.05, -0.55); c.curve_to(-0.35, -0.54, -0.54, -0.30, -0.52, -0.05)
        if hs == 'short': c.curve_to(-0.52, 0.12, -0.42, 0.24, -0.30, 0.28); c.line_to(-0.17, 0.16)
        elif hs == 'ned': c.curve_to(-0.54, 0.25, -0.50, 0.50, -0.42, 0.66); c.line_to(-0.30, 0.60); c.line_to(-0.22, 0.68); c.line_to(-0.12, 0.52); c.curve_to(-0.10, 0.40, -0.14, 0.30, -0.17, 0.16)
        else: c.curve_to(-0.54, 0.25, -0.50, 0.50, -0.42, 0.66); c.line_to(-0.12, 0.62); c.line_to(-0.17, 0.16)
        c.line_to(-0.05, 0.10); c.line_to(-0.03, -0.10); c.line_to(0.16, -0.22); c.line_to(0.22, -0.30); c.close_path(); c.fill()
    hat = S.get('hat')
    if hat == 'crown':
        K(S.get('crown', GOLD)); c.move_to(-0.44, -0.30); c.line_to(0.36, -0.30); c.line_to(0.40, -0.60)
        for i in range(1, 9): c.line_to(0.40 - i * 0.105 + 0.052, -0.42); c.line_to(0.40 - i * 0.105, -0.60 - 0.03 * (i % 2 == 0))
        c.close_path(); c.fill()
    elif hat == 'helm':
        K(S.get('helm', (0.30, 0.32, 0.35))); c.move_to(0.45, -0.14); c.curve_to(0.42, -0.50, 0.15, -0.66, -0.04, -0.66); c.curve_to(-0.36, -0.66, -0.58, -0.40, -0.56, -0.02)
        c.line_to(-0.54, 0.42); c.line_to(-0.20, 0.42); c.line_to(-0.16, -0.02); c.line_to(0.30, -0.10); c.line_to(0.34, 0.12); c.line_to(0.42, 0.12); c.close_path(); c.fill()
        c.move_to(-0.09, -0.64); c.line_to(-0.04, -0.86); c.line_to(0.01, -0.64); c.close_path(); c.fill()
    elif hat == 'hood':
        K(S.get('hoodc', (0.08, 0.07, 0.07))); c.move_to(0.40, -0.16); c.curve_to(0.36, -0.56, 0.05, -0.64, -0.12, -0.60); c.curve_to(-0.50, -0.52, -0.62, -0.1, -0.56, 0.60); c.line_to(-0.02, 0.62); c.line_to(-0.02, 0.30); c.line_to(0.06, 0.02); c.line_to(0.26, -0.14); c.close_path(); c.fill()


def fig(c, x, y, H, S, pose='stand', face=1, P=None, mono=None, keep=()):
    q = dict(POSES[pose]); q.update(P or {}); bulk = S.get('bulk', 1.0)
    def K(col, a=1.0, tag=None):
        if mono is not None and tag not in keep: col = mono
        c.set_source_rgba(*col, a)
    def D(a, l=1.0): r = math.radians(a); return (math.sin(r) * face * l, math.cos(r) * l)
    def A(p, v): return (p[0] + v[0], p[1] + v[1])
    def limb(p0, p1, w0, w1, col):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L; K(col)
        c.move_to(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2); c.line_to(p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2); c.line_to(p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2); c.line_to(p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2); c.close_path(); c.fill()
        c.arc(*p0, w0 / 2, 0, math.tau); c.fill(); c.arc(*p1, w1 / 2, 0, math.tau); c.fill()
    def spoly(pts, col, a=1.0):
        K(col, a); n = len(pts); c.move_to(*pts[0])
        for i in range(n):
            p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
            c.curve_to(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, *p2)
        c.close_path(); c.fill()
    def lpoly(pts, col, a=1.0):
        K(col, a); c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]; c.close_path(); c.fill()

    TH, SHN, FT, TOR, NK, HH = 0.245 * H, 0.245 * H, 0.035 * H, 0.295 * H, 0.05 * H, 0.130 * H
    UA, FA = 0.165 * H, 0.150 * H
    legs = []; low = 0
    for (a1, a2) in (q['lb'], q['lf']):
        k = D(a1, TH); an = A(k, D(a2, SHN)); legs.append((k, an))
        low = max(low, an[1] + (FT if abs(a2) < 50 else 0.03 * H), k[1] + 0.035 * H)
    hip = (x, y - low); stand_h = TH + SHN + FT
    up = D(180 - q['lean']); fw = (up[1] * -face * 1.0, up[0] * face); fw = (-up[1] * face, up[0] * face)   # 躯干朝前法向
    def T(u, v): return (hip[0] + up[0] * TOR * u + fw[0] * H * v * bulk, hip[1] + up[1] * TOR * u + fw[1] * H * v * bulk)
    sh = T(0.93, -0.005); nk0 = T(1.0, -0.008)
    ha = 180 - q['lean'] * 0.6 - q['head'] * 0.45; nk1 = A(nk0, D(ha, NK)); hc = A(nk1, D(180 - q['lean'] * 0.5 - q['head'], HH * 0.38))
    body = S.get('body', (0.14, 0.13, 0.14)); legc = S.get('legs', mix(body, (0, 0, 0), 0.35)); skin = S.get('skin', SKIN)
    sleeve = S.get('sleeve', mix(body, (0, 0, 0), 0.12)); dark = lambda col: mix(col, (0.02, 0.02, 0.04), 0.30)
    out = dict(hip=hip, head=hc, sh=sh, HH=HH)

    # 披风（身后）
    ck = S.get('cloak')
    if ck:
        drop = (stand_h - low) * 0.9; b = -face
        pts = [T(0.98, 0.035), T(1.02, -0.05), T(0.72, -0.085), (hip[0] + b * (0.085 * H * bulk + drop * 0.25), hip[1] + 0.02 * H),
               (x + b * (0.150 * H + drop), y - 0.035 * H), (x + b * (0.165 * H + drop), y - 0.004 * H), (x + b * (0.01 * H), y - 0.004 * H), (hip[0] + b * 0.01 * H, hip[1] + 0.05 * H), T(0.5, 0.0)]
        spoly(pts, ck)
        spoly([pts[2], pts[3], pts[4], (pts[4][0] - b * 0.05 * H, pts[4][1] - 0.01 * H), (hip[0] + b * 0.035 * H * bulk, hip[1])], mix(ck, (0, 0, 0), 0.22), 0.9)
    # 后臂
    def arm(ang, col, back):
        a1, a2 = ang; e = A(sh, D(a1, UA)); hd = A(e, D(a2, FA)); cc = dark(col) if back else col
        limb(sh, e, 0.058 * H * bulk, 0.046 * H * bulk, cc); limb(e, hd, 0.046 * H * bulk, 0.034 * H, cc)
        K(dark(skin) if back else skin); c.save(); c.translate(*A(hd, D(a2, 0.022 * H))); c.rotate(-math.radians(a2) * face); c.scale(0.019 * H, 0.030 * H); c.arc(0, 0, 1, 0, math.tau); c.restore(); c.fill()
        return A(hd, D(a2, 0.025 * H))
    out['hand_b'] = arm(q['ab'], sleeve, True)
    # 腿
    skirt = S.get('skirt')
    if skirt != 'gown':
        for i, (k, an) in enumerate(legs):
            cc = dark(legc) if i == 0 else legc; kp = A(hip, k); ap = A(hip, an); a2 = (q['lb'], q['lf'])[i][1]
            limb(A(hip, (0, -0.01 * H)), kp, 0.092 * H * bulk, 0.066 * H, cc); limb(kp, ap, 0.064 * H, 0.044 * H, cc)
            bt = S.get('boots', mix(legc, (0, 0, 0), 0.4)); bt = dark(bt) if i == 0 else bt
            if abs(a2) < 50: lpoly([A(ap, (-face * 0.030 * H, -0.01 * H)), A(ap, (face * 0.030 * H, -0.015 * H)), A(ap, (face * 0.105 * H, FT * 0.55)), A(ap, (face * 0.108 * H, FT)), A(ap, (-face * 0.034 * H, FT))], bt)
            else:                                                                           # 跪姿：脚背贴地向后
                d2 = D(a2, 1); lpoly([A(ap, (0, -0.022 * H)), A(ap, (d2[0] * 0.10 * H, 0.0)), A(ap, (d2[0] * 0.10 * H, 0.028 * H)), A(ap, (-d2[0] * 0.02 * H, 0.028 * H))], bt)
    # 躯干
    tb = S.get('tbulk', 1.0)
    tor = [T(0.0, 0.050), T(0.35, 0.056 * tb), T(0.72, 0.066 * tb), T(0.96, 0.036), T(1.03, 0.0), T(1.0, -0.040), T(0.80, -0.064 * tb), T(0.38, -0.048), T(0.0, -0.058), T(-0.10, 0.0)]
    if skirt == 'gown':
        gw = S.get('gown', body); b = -face; tr = S.get('train', 0.10)
        spoly([T(0.30, 0.050), T(0.0, 0.058), (x + face * 0.095 * H, y - 0.25 * H), (x + face * 0.125 * H, y - 0.004 * H), (x + b * (0.16 + tr) * H, y - 0.004 * H), (x + b * 0.14 * H, y - 0.22 * H), T(0.0, -0.066), T(0.30, -0.046)], gw)
        spoly([T(0.0, -0.066), (x + b * 0.14 * H, y - 0.22 * H), (x + b * (0.16 + tr) * H, y - 0.004 * H), (x + b * 0.03 * H, y - 0.004 * H), (x + b * 0.02 * H, y - 0.3 * H)], mix(gw, (0, 0, 0), 0.20), 0.85)
    spoly(tor, body)
    if skirt in ('tunic', 'coat'):
        ln = (0.13 if skirt == 'tunic' else 0.30) * H; b = -face
        spoly([T(0.12, 0.052), T(0.0, 0.058), (hip[0] + face * 0.070 * H * bulk, hip[1] + ln), (hip[0] + b * 0.075 * H * bulk, hip[1] + ln), T(0.0, -0.062), T(0.12, -0.05)], S.get('skirtc', body))
    if S.get('belt'): K(S['belt']); c.set_line_width(0.016 * H); c.move_to(*T(0.10, 0.056)); c.line_to(*T(0.10, -0.052)); c.stroke()
    if S.get('chest'): spoly([T(0.50, 0.062), T(0.86, 0.058), T(0.90, 0.0), T(0.50, 0.0)], S['chest'])
    # 脖子、头
    limb(T(0.97, -0.004), A(hc, D(180 - q['head'], -HH * 0.18)), 0.060 * H, 0.052 * H, mix(skin, (0.2, 0.1, 0.08), 0.25))
    if S.get('fur'):
        fur = S['fur']
        for i, (u, v, r) in enumerate(((0.90, -0.062, 0.036), (0.98, -0.045, 0.040), (1.02, -0.010, 0.038), (0.99, 0.030, 0.036), (0.92, 0.058, 0.030), (0.90, -0.02, 0.040), (0.90, 0.025, 0.036))):
            K(mix(fur, (0, 0, 0), 0.10 * (i % 3))); c.arc(*T(u, v), r * H, 0, math.tau); c.fill()
    c.save(); c.translate(*hc); c.scale(face, 1); c.rotate(math.radians(q['head'])); c.scale(HH, HH); _head(c, S, K); c.restore()
    # 前臂
    out['hand'] = arm(q['af'], sleeve, False)
    if S.get('bound'):                                                                  # 反绑的绳
        K((0.55, 0.45, 0.30)); c.set_line_width(0.012 * H); hb = out['hand']; c.move_to(hb[0] - 0.02 * H, hb[1] - 0.03 * H); c.line_to(hb[0] + 0.02 * H, hb[1] - 0.02 * H); c.stroke()
    held = S.get('held')
    if held:
        kind, ang, L = held
        if kind == 'sword':
            if mono is not None and 'steel' not in keep: out['tip'] = sword(c, out['hand'], ang, L * H / 100, face, col=mono, hilt=mono)
            else: out['tip'] = sword(c, out['hand'], ang, L * H / 100, face)
        elif kind == 'spear':
            d = D(ang, 1); h = out['hand']; LL = L * H / 100; K((0.20, 0.15, 0.11)); c.set_line_width(0.014 * H); c.move_to(h[0] - d[0] * LL * 0.42, h[1] - d[1] * LL * 0.42); c.line_to(h[0] + d[0] * LL * 0.58, h[1] + d[1] * LL * 0.58); c.stroke()
            tp = (h[0] + d[0] * LL * 0.58, h[1] + d[1] * LL * 0.58); n = (-d[1], d[0]); K(STEEL, tag='steel')
            c.move_to(tp[0] + n[0] * 0.016 * H, tp[1] + n[1] * 0.016 * H); c.line_to(tp[0] + d[0] * 0.09 * H, tp[1] + d[1] * 0.09 * H); c.line_to(tp[0] - n[0] * 0.016 * H, tp[1] - n[1] * 0.016 * H); c.close_path(); c.fill()
    return out


G = (0.13, 0.13, 0.15)
CAST = {
    'ned': dict(body=(0.20, 0.20, 0.22), legs=(0.12, 0.12, 0.13), skirt='tunic', belt=(0.08, 0.07, 0.07), cloak=(0.30, 0.33, 0.37), fur=(0.50, 0.49, 0.47), hair=(0.26, 0.19, 0.14), hairstyle='ned', beard=(0.30, 0.24, 0.19), bulk=1.08),
    'ned_prison': dict(body=(0.34, 0.31, 0.28), legs=(0.20, 0.19, 0.18), skirt='tunic', hair=(0.26, 0.19, 0.14), hairstyle='ned', beard=(0.30, 0.24, 0.19), bulk=1.05, bound=True),
    'ilyn': dict(body=(0.07, 0.07, 0.08), legs=(0.05, 0.05, 0.06), skirt='coat', hairstyle='bald', skin=(0.70, 0.62, 0.56), bulk=1.0, belt=(0.3, 0.3, 0.32)),
    'joffrey': dict(body=(0.55, 0.10, 0.09), legs=(0.10, 0.08, 0.08), skirt='tunic', cloak=(0.72, 0.56, 0.20), hair=(0.86, 0.72, 0.38), hairstyle='short', hat='crown', bulk=0.86, belt=GOLD),
    'cersei': dict(body=(0.55, 0.09, 0.09), gown=(0.50, 0.07, 0.08), skirt='gown', hair=(0.88, 0.74, 0.40), hairstyle='long', hairlen=2.3, bulk=0.82, tbulk=0.9, sleeve=(0.46, 0.06, 0.07), belt=GOLD),
    'sansa': dict(body=(0.50, 0.62, 0.74), gown=(0.46, 0.58, 0.72), skirt='gown', train=0.02, hair=(0.62, 0.26, 0.12), hairstyle='long', hairlen=2.1, bulk=0.78, tbulk=0.88, sleeve=(0.44, 0.56, 0.70)),
    'goldcloak': dict(body=(0.12, 0.12, 0.13), legs=(0.08, 0.08, 0.09), skirt='tunic', cloak=(0.78, 0.60, 0.18), hat='helm', hairstyle='bald', bulk=1.05),
    'lannguard': dict(body=(0.48, 0.09, 0.08), legs=(0.20, 0.06, 0.06), skirt='tunic', cloak=(0.56, 0.08, 0.08), hat='helm', helm=(0.72, 0.56, 0.22), hairstyle='bald', bulk=1.08),
    'little': dict(body=(0.12, 0.20, 0.19), legs=(0.07, 0.08, 0.08), skirt='coat', hair=(0.12, 0.10, 0.10), hairstyle='short', beard=(0.14, 0.12, 0.12), bulk=0.9),
}
