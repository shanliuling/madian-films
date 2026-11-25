"""mapwar.field — 垂直俯视战场：一个兵 = 肩线 + 头 + 兵器，几百上千个兵排成阵。

坐标：战场"世界坐标"大致就是 1920x1080 的像素（中心 960,560），镜头 FCam 可推拉平移。
典型一场战斗：
    B = Battle([mk('shield','H', ...), mk('cav','Z', ...), ...], dur)      # 预演一次，缓存
    每帧: surf, c = canvas(); cam = FCam(keys, lt, hits); cam.apply(c)
          river(...); volley(...); fr = B.draw(c, lt, SIDES); banner(...)
          X = Txt(style == 'night'); ...写字...; return finish(surf, lt, X, style, hits)
SIDES = {'H': side_cols((0.77,0.10,0.12), style), ...}   每方 (身体色, 头色)
兵种 kind: 'spear' 长矛 / 'shield' 盾 / 'bow' 弓 / 'cav' 骑 / 'chariot' 战车 / 'run' 溃兵（无兵器）
要新兵种（象兵、投石机、火器、船）就照 unit() 的画法加一个分支：俯视下只要"轮廓 + 一个识别特征"。
"""
import math
import numpy as np, cairo, cv2
from .util import SW, SH, FPS, TAU, cl, ease, eout, hsh, kf, fbm, surf_rgba, to_img, VR, grain, rng


def side_cols(rgb, style='ink'):
    """势力主色 -> (身体色, 头色)。夜色下身体提亮、头近白，才能从暗底里跳出来。"""
    r = np.float32(rgb)
    if style == 'night': return tuple(np.minimum(1, r * 0.75 + 0.3)), tuple(np.minimum(1, r * 0.15 + 0.85))
    return tuple(r), tuple(r * 0.4)


# ---------------------------------------------------------------- glyphs
def foot(c, x, y, fx, fy, col, head, S_=1.25, spear=True, streak=0.0):
    px, py = -fy, fx
    if streak > 0: c.set_source_rgba(*col, 0.4); c.set_line_width(3.4 * S_); c.move_to(x - fx * (streak + 6), y - fy * (streak + 6)); c.line_to(x - fx * 5, y - fy * 5); c.stroke()
    c.set_source_rgba(*col, 1); c.set_line_width(4.6 * S_); c.move_to(x - px * 4 * S_, y - py * 4 * S_); c.line_to(x + px * 4 * S_, y + py * 4 * S_); c.stroke()
    c.set_source_rgba(*head, 1); c.arc(x + fx * 1.2, y + fy * 1.2, 2.6 * S_, 0, TAU); c.fill()
    if spear: c.set_line_width(1.2 * S_); c.set_source_rgba(*col, 0.9); c.move_to(x + px * 3.4, y + py * 3.4); c.line_to(x + px * 3.4 + fx * 17, y + py * 3.4 + fy * 17); c.stroke()


def rider(c, x, y, col, head, big=1.0):
    """朝 +x 的骑兵（外面用 rotate 转向）。big>1 画主将。"""
    c.set_source_rgba(*col, 0.32); c.set_line_width(7 * big); c.move_to(x - 78 * big, y); c.line_to(x - 22 * big, y); c.stroke()         # 速度拖尾
    c.set_source_rgba(*col, 1); c.set_line_width(9.5 * big); c.move_to(x - 15 * big, y); c.line_to(x + 14 * big, y); c.stroke()
    c.set_line_width(5.2 * big); c.move_to(x - 1, y - 6.5 * big); c.line_to(x - 1, y + 6.5 * big); c.stroke()
    c.set_source_rgba(*head, 1); c.arc(x + 1, y, 3.3 * big, 0, TAU); c.fill(); c.arc(x + 19 * big, y, 2.6 * big, 0, TAU); c.fill()
    c.set_source_rgba(*col, 1); c.set_line_width(1.6 * big); c.move_to(x + 2, y + 5 * big); c.line_to(x + 40 * big, y + 8 * big); c.stroke()


def unit(c, x, y, fx, fy, kind, col, head, S_=1.25, streak=0.0):
    if kind == 'cav':
        c.save(); c.translate(x, y); c.rotate(math.atan2(fy, fx)); rider(c, 0, 0, col, head, 0.95); c.restore(); return
    if kind == 'chariot':
        c.save(); c.translate(x, y); c.rotate(math.atan2(fy, fx))
        c.set_source_rgba(*col, 1); c.rectangle(-16, -11, 24, 22); c.fill()
        c.set_line_width(3); c.move_to(-4, -15); c.line_to(-4, 15); c.stroke(); c.set_line_width(2); c.move_to(8, 0); c.line_to(40, 0); c.stroke()
        for sy_ in (-7, 7):
            c.set_line_width(7); c.move_to(22, sy_); c.line_to(42, sy_); c.stroke(); c.arc(46, sy_, 2.6, 0, TAU); c.fill()
        c.set_source_rgba(*head, 1)
        for hx_, hy_ in ((-8, -4), (-8, 5), (0, 0)): c.arc(hx_, hy_, 3.2, 0, TAU); c.fill()
        c.restore(); return
    foot(c, x, y, fx, fy, col, head, S_, kind == 'spear', streak)
    px, py = -fy, fx
    if kind == 'shield':
        c.set_source_rgba(*head, 1); c.set_line_width(3.6 * S_); c.move_to(x + fx * 6.5 - px * 5.5, y + fy * 6.5 - py * 5.5); c.line_to(x + fx * 6.5 + px * 5.5, y + fy * 6.5 + py * 5.5); c.stroke()
    elif kind == 'bow':
        a = math.atan2(fy, fx); c.set_source_rgba(*col, 1); c.set_line_width(1.7 * S_); c.arc(x + fx * 2, y + fy * 2, 8.5 * S_, a - 0.95, a + 0.95); c.stroke()


# ---------------------------------------------------------------- formations
def mk(kind, side, cx=0, cy=0, depth=4, width=10, sp=17, seed=0, shape='block', **kw):
    """一个方阵。depth 纵深(排) x width 正面(列)，sp 间距(骑兵用 40 左右)。
    shape: 'block' 方阵 / 'wedge' 锥形(楔) / 'crescent' 偃月(两翼前伸) / 'ring' 圆阵
    关键帧（时间均为镜头内秒）：
      path=[(t,x,y)...] 阵心轨迹     face=[(t,弧度)...] 朝向（不给则朝行进方向）
      cas=[(t,0..1)...] 累计伤亡比例   scat=[(t,像素)...] 溃散半径      order='front' 表示前排先倒"""
    r = np.random.default_rng(seed); gx, gy = np.meshgrid(np.arange(depth), np.arange(width)); gx = gx.ravel().astype(float); gy = gy.ravel().astype(float)
    ox = (gx - (depth - 1) / 2) * sp; oy = (gy - (width - 1) / 2) * sp
    if shape == 'wedge':
        keep = np.abs(gy - (width - 1) / 2) <= (depth - 1 - gx) / max(1, depth - 1) * (width - 1) / 2 + 0.5; ox, oy = ox[keep], oy[keep]
    elif shape == 'crescent': ox = ox + (oy / (width * sp / 2)) ** 2 * depth * sp * 0.9
    elif shape == 'ring':
        ang = gy / width * TAU; rad = (width * sp / TAU) + gx * sp; ox, oy = np.cos(ang) * rad, np.sin(ang) * rad
    n = len(ox); ox = ox + r.normal(0, 2.2, n); oy = oy + r.normal(0, 2.2, n)
    d = dict(kind=kind, side=side, ox=ox, oy=oy, u=r.random(n), rd=r.uniform(0, TAU, n), rs=r.uniform(0.35, 1.0, n), path=[(0, cx, cy)], face=None, cas=[(0, 0)], scat=[(0, 0)], order='rand', name=None)
    d.update(kw)
    if d['order'] == 'front': d['u'] = (ox.max() - ox) / max(1e-3, ox.max() - ox.min()) * 0.8 + d['u'] * 0.2
    return d


class Battle:
    """关键帧驱动的阵战：构造时预演全部帧（倒下的人留在原地），draw() 按时间取帧画。"""

    def __init__(self, units, dur):
        self.units = units; self.frames = []
        state = [dict(dead=np.zeros(len(u['ox']), bool), fx=np.zeros(len(u['ox'])), fy=np.zeros(len(u['ox']))) for u in units]
        for f in range(int(dur * FPS) + 3):
            t = f / FPS; fr = []
            for u, stt in zip(units, state):
                cx, cy = kf(u['path'], t, 1), kf(u['path'], t, 2); cx2, cy2 = kf(u['path'], t + 0.08, 1), kf(u['path'], t + 0.08, 2)
                if u['face'] is not None: ang = kf(u['face'], t)
                else: ang = math.atan2(cy2 - cy, cx2 - cx) if math.hypot(cx2 - cx, cy2 - cy) > 0.5 else u.get('_a', 0.0)
                u['_a'] = ang; ca, sa = math.cos(ang), math.sin(ang); sc = kf(u['scat'], t)
                x = cx + u['ox'] * ca - u['oy'] * sa + np.cos(u['rd']) * u['rs'] * sc + np.sin(t * 9 + u['rd'] * 3) * 1.5
                y = cy + u['ox'] * sa + u['oy'] * ca + np.sin(u['rd']) * u['rs'] * sc + np.cos(t * 8 + u['rd'] * 2) * 1.5
                newdead = (u['u'] < kf(u['cas'], t)) & ~stt['dead']
                stt['fx'][newdead] = x[newdead]; stt['fy'][newdead] = y[newdead]; stt['dead'] |= newdead
                x = np.where(stt['dead'], stt['fx'], x); y = np.where(stt['dead'], stt['fy'], y)
                fr.append(dict(x=x.copy(), y=y.copy(), dead=stt['dead'].copy(), ang=ang, sc=sc, mv=math.hypot(cx2 - cx, cy2 - cy) / 0.08, c=(cx, cy)))
            self.frames.append(fr)

    def draw(self, c, lt, sides):
        """-> 该帧各方阵状态列表（fr[i]['c'] 是第 i 个方阵的阵心，可用来跟随放旗、放标签）。"""
        fr = self.frames[min(len(self.frames) - 1, max(0, int(round(lt * FPS))))]
        for u, f in zip(self.units, fr):          # 倒地痕迹先画
            col = sides[u['side']][0]
            for i in np.flatnonzero(f['dead']):
                c.set_source_rgba(*col, 0.42); c.save(); c.translate(f['x'][i], f['y'][i]); c.rotate(u['rd'][i]); c.scale(1, 0.45); c.arc(0, 0, 10, 0, TAU); c.restore(); c.fill()
        for u, f in zip(self.units, fr):
            col, head = sides[u['side']]; run = f['sc'] > 18
            for i in np.flatnonzero(~f['dead']):
                fx, fy = (math.cos(u['rd'][i]), math.sin(u['rd'][i])) if run else (math.cos(f['ang']), math.sin(f['ang']))
                kd = u['kind'] if (not run or u['kind'] in ('cav', 'chariot')) else 'run'
                unit(c, f['x'][i], f['y'][i], fx, fy, kd, col, head, 1.25, 14 if (run or (f['mv'] > 160 and kd != 'cav')) else 0)
        return fr


class Wedge:
    """物理模拟的骑兵凿穿：锥形骑队从左向右冲进一片密集方阵，近者倒、稍远者溃逃、其余原地被挤开。
    rows 锥形排数（15 排≈120骑）；nreg 敌方方阵数（每阵 9x7）；speed 冲过的总距离(px)。"""

    def __init__(self, rows, nreg, dur, seed=5, spread=(620, 370), speed=2250, center=(1260, 560)):
        from scipy.spatial import cKDTree
        r = np.random.default_rng(seed); dt = 1 / FPS; cs = []; X0, Y0 = center; tries = 0
        while len(cs) < nreg and tries < 20000:
            tries += 1; x, y = r.uniform(-1, 1, 2)
            if x * x + y * y < 1 and all(math.hypot(x * spread[0] - a, y * spread[1] - b_) > 150 for a, b_ in cs): cs.append((x * spread[0], y * spread[1]))
        X_, Y_ = [], []
        for (cx, cy) in cs:
            gx, gy = np.meshgrid(np.arange(9), np.arange(7))
            X_ += list(X0 + cx + (gx.ravel() - 4.5) * 17 + r.normal(0, 2.5, 63)); Y_ += list(Y0 + cy + (gy.ravel() - 3.5) * 17 + r.normal(0, 2.5, 63))
        bx, by = np.array(X_), np.array(Y_); nb = len(bx); hx, hy = bx.copy(), by.copy(); bvx = np.zeros(nb); bvy = np.zeros(nb); st = np.zeros(nb, np.int8); fdx = np.full(nb, -1.0); fdy = np.zeros(nb)
        off = np.array([(-(row * 46) - r.uniform(0, 18), (k - row / 2) * 40 + r.normal(0, 6)) for row in range(rows) for k in range(row + 1)]); nr = len(off)
        self.frames = []; self.trail = []; self.cy = Y0
        for f in range(int(dur * FPS) + 3):
            t = f * dt; tip = -200 + speed * (t / dur) ** 0.9
            rx = tip + off[:, 0] + r.normal(0, 2, nr); ry = Y0 + off[:, 1] + np.sin(t * 20 + np.arange(nr)) * 3
            if f % 2 == 0:
                for i in r.choice(nr, min(6, nr), replace=False): self.trail.append((rx[i], ry[i], t, r.uniform(30, 70)))
            alive = st != 2; d, idx = cKDTree(np.c_[rx, ry]).query(np.c_[bx, by], k=1)
            st[alive & (d < 24) & (r.random(nb) < 0.45)] = 2; st[(st == 0) & (d < 190) & (r.random(nb) < 0.35)] = 3            # 0 列阵 2 倒 3 逃
            ux = (bx - rx[idx]) / np.maximum(d, 1); uy = (by - ry[idx]) / np.maximum(d, 1)
            m0 = st == 0; bvx[m0] = bvx[m0] * 0.8 + (hx[m0] - bx[m0]) * 0.6; bvy[m0] = bvy[m0] * 0.8 + (hy[m0] - by[m0]) * 0.6
            m3 = st == 3; fx = ux[m3] * 0.5 + 0.55 + r.normal(0, 0.35, m3.sum()); fy = uy[m3] + np.sign(by[m3] - Y0) * 0.35 + r.normal(0, 0.35, m3.sum()); fn = np.hypot(fx, fy) + 1e-3
            bvx[m3] = bvx[m3] * 0.8 + fx / fn * 330 * 0.2; bvy[m3] = bvy[m3] * 0.8 + fy / fn * 330 * 0.2
            m2 = st == 2; bvx[m2] *= 0.6; bvy[m2] *= 0.6
            al = np.flatnonzero(st != 2); pr = cKDTree(np.c_[bx[al], by[al]]).query_pairs(11.0, output_type='ndarray')
            if len(pr):
                a_, b_ = al[pr[:, 0]], al[pr[:, 1]]; ddx, ddy = bx[a_] - bx[b_], by[a_] - by[b_]; q_ = np.maximum(np.hypot(ddx, ddy), 0.5); push = (11.0 - q_) / q_ * 0.5
                np.add.at(bx, a_, ddx * push); np.add.at(by, a_, ddy * push); np.add.at(bx, b_, -ddx * push); np.add.at(by, b_, -ddy * push)
            bx += bvx * dt; by += bvy * dt; spd = np.hypot(bvx, bvy); mv = spd > 25
            fdx = np.where(mv, bvx / np.maximum(spd, 1), fdx); fdy = np.where(mv, bvy / np.maximum(spd, 1), fdy)
            self.frames.append(dict(bx=bx.copy(), by=by.copy(), st=st.copy(), fdx=fdx.copy(), fdy=fdy.copy(), spd=spd.copy(), rx=rx, ry=ry, tip=tip))
        self.dead_ang = r.uniform(0, TAU, nb); self.camps = [(X0 + cx + 95, Y0 + cy - 80) for cx, cy in cs[::2]]

    def draw(self, c, lt, foe, cav, style='ink', kinds=('spear', 'shield', 'bow')):
        """foe / cav 各为 (身体色, 头色)。-> 该帧状态（fr['tip'] 是锥尖 x）。"""
        fr = self.frames[min(len(self.frames) - 1, max(0, int(round(lt * FPS))))]
        dust = (0.45, 0.5, 0.62) if style == 'night' else (0.42, 0.35, 0.26); deadc = (0.42, 0.14, 0.10, 0.8) if style == 'night' else (0.25, 0.18, 0.14, 0.75)
        for x, y, t0, r_ in self.trail:
            a = lt - t0
            if 0 <= a < 1.6: c.set_source_rgba(*dust, 0.07 * (1 - a / 1.6)); c.arc(x, y, r_ * (1 + a * 0.9), 0, TAU); c.fill()
        st, bx, by, fdx, fdy, spd = fr['st'], fr['bx'], fr['by'], fr['fdx'], fr['fdy'], fr['spd']
        for i in np.flatnonzero(st == 2):
            c.set_source_rgba(*deadc); c.save(); c.translate(bx[i], by[i]); c.rotate(self.dead_ang[i]); c.scale(1, 0.45); c.arc(0, 0, 10, 0, TAU); c.restore(); c.fill()
        for i in np.flatnonzero(st != 2):
            kd = kinds[(i // 63) % len(kinds)]
            unit(c, bx[i], by[i], fdx[i], fdy[i], kd if st[i] == 0 else 'run', *foe, 1.25, min(26, spd[i] * 0.09) if (st[i] == 3 and spd[i] > 60) else 0)
        for x, y in zip(fr['rx'], fr['ry']): rider(c, x, y, *cav)
        rider(c, fr['tip'], self.cy, *cav, 1.6)
        return fr


class Ring:
    """四面合围：中间一个方阵，外面 n 个兵从半径 r0 收到 r1，被围者由外向内倒下。"""

    def __init__(self, n=1300, inner=(28, 15), seed=21):
        r = np.random.default_rng(seed); gx, gy = np.meshgrid(np.arange(inner[0]), np.arange(inner[1]))
        self.cx = (gx.ravel() - (inner[0] - 1) / 2) * 17 + r.normal(0, 2.5, gx.size); self.cy = (gy.ravel() - (inner[1] - 1) / 2) * 17 + r.normal(0, 2.5, gx.size)
        self.cd = np.hypot(self.cx / 1.25, self.cy / 0.8) + r.normal(0, 14, gx.size); self.ang = r.uniform(0, TAU, gx.size)
        self.th = r.uniform(0, TAU, n); self.dep = r.exponential(1.0, n) * 46; self.ph = r.uniform(0, TAU, n); self.late = r.uniform(0, 0.25, n)

    def draw(self, c, k, lt, inner, outer, center=(960, 560), r0=840, r1=200):
        R = lambda kk: r0 - (r0 - r1) * ease(kk); X0, Y0 = center; dead = self.cd > R(k) * 0.86 - 20
        for i in np.flatnonzero(dead):
            c.set_source_rgba(*inner[0], 0.5); c.save(); c.translate(X0 + self.cx[i], Y0 + self.cy[i]); c.rotate(self.ang[i]); c.scale(1, 0.45); c.arc(0, 0, 10, 0, TAU); c.restore(); c.fill()
        for i in np.flatnonzero(~dead):
            d_ = math.hypot(self.cx[i], self.cy[i]) + 1e-3; foot(c, X0 + self.cx[i], Y0 + self.cy[i], self.cx[i] / d_, self.cy[i] / d_, *inner, 1.25)
        kk = np.clip(k - self.late * (1 - k), 0, 1); rad = np.array([R(v) for v in kk]) + self.dep; mvg = (ease(min(1, k + 0.02)) - ease(k)) > 0.004
        hx = X0 + np.cos(self.th) * rad * 1.25 + np.sin(lt * 9 + self.ph) * 3; hy = Y0 + np.sin(self.th) * rad * 0.8 + np.cos(lt * 8 + self.ph) * 3
        for i in range(len(hx)):
            if -200 < hx[i] < 2120 and -300 < hy[i] < 1400: foot(c, hx[i], hy[i], -math.cos(self.th[i]), -math.sin(self.th[i]), *outer, 1.25, True, 16 if mvg else 0)


# ---------------------------------------------------------------- props
def volley(c, lt, t0, src, dst, n, seed, col, spread=(60, 260), flight=0.5):
    """一轮箭雨：从 src 附近抛到 dst 附近（带地面影子，落地后插在地上渐隐）。"""
    for i in range(n):
        ts = t0 + hsh(i, seed) * 0.3; u = (lt - ts) / flight
        sx, sy = src[0] + (hsh(i, seed + 1) - .5) * spread[0], src[1] + (hsh(i, seed + 2) - .5) * spread[1]
        ex, ey = dst[0] + (hsh(i, seed + 3) - .5) * spread[0] * 1.6, dst[1] + (hsh(i, seed + 4) - .5) * spread[1]
        if 0 <= u <= 1:
            x = sx + (ex - sx) * u; y = sy + (ey - sy) * u; h = math.sin(math.pi * u) * 46; ang = math.atan2(ey - sy, ex - sx)
            c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(2); c.move_to(x, y); c.line_to(x - math.cos(ang) * 14, y - math.sin(ang) * 14); c.stroke()
            c.set_source_rgba(*col, 0.95); c.set_line_width(1.8); c.move_to(x, y - h); c.line_to(x - math.cos(ang) * 18, y - h - math.sin(ang) * 18 + math.cos(math.pi * u) * 5); c.stroke()
        elif 1 < u < 4:
            c.set_source_rgba(*col, 0.5 * (1 - (u - 1) / 3)); c.set_line_width(1.5); c.move_to(ex, ey); c.line_to(ex - 5, ey - 9); c.stroke()


def banner(c, x, y, col, t, big=1.0, pole=(0.08, 0.07, 0.07)):
    c.set_source_rgba(*pole, 1); c.set_line_width(3 * big); c.move_to(x, y + 6); c.line_to(x, y - 46 * big); c.stroke()
    f = math.sin(t * 9) * 4; c.set_source_rgba(*col, 1); c.move_to(x, y - 46 * big); c.curve_to(x + 14 * big, y - 52 * big + f, x + 26 * big, y - 40 * big - f, x + 40 * big, y - 44 * big + f)
    c.line_to(x + 36 * big, y - 24 * big + f); c.curve_to(x + 24 * big, y - 20 * big - f, x + 12 * big, y - 30 * big + f, x, y - 24 * big); c.close_path(); c.fill()


def river(c, pts, w, t, a=0.85, style='ink'):
    """河带：pts 中线点，w 宽度（常数或 f(i)，可随时间变宽来表现决堤/涨水）。"""
    L, R_ = [], []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(0, i - 1)]; x1, y1 = pts[min(len(pts) - 1, i + 1)]; d = math.hypot(x1 - x0, y1 - y0) + 1e-6; nx, ny = -(y1 - y0) / d, (x1 - x0) / d
        ww = (w(i) if callable(w) else w) / 2 * (1 + 0.08 * math.sin(i * 1.7)); L.append((x + nx * ww, y + ny * ww)); R_.append((x - nx * ww, y - ny * ww))
    c.move_to(*L[0])
    for p in L[1:]: c.line_to(*p)
    for p in reversed(R_): c.line_to(*p)
    c.close_path(); c.set_source_rgba(*((0.30, 0.44, 0.54) if style == 'ink' else (0.20, 0.34, 0.52)), a); c.fill()
    c.set_source_rgba(0.93, 0.95, 0.95, 0.5); c.set_line_width(2)
    for i in range(1, len(pts) - 1, 2):
        (x, y) = pts[i]; ph = (t * 1.6 + i * 0.37) % 1.0; (x1, y1) = pts[i + 1]
        c.move_to(x + (x1 - x) * ph - 10, y + (y1 - y) * ph); c.line_to(x + (x1 - x) * ph + 12, y + (y1 - y) * ph + 16); c.stroke()


def camp(c, x, y, style='ink', tilt=0.0):
    """一顶营帐（菱形）。"""
    c.save(); c.translate(x, y); c.rotate(tilt); c.set_source_rgba(*((0.72, 0.66, 0.54) if style == 'ink' else (0.50, 0.44, 0.36)), 0.95)
    c.move_to(-30, 0); c.line_to(0, -23); c.line_to(30, 0); c.line_to(0, 23); c.close_path(); c.fill()
    c.set_source_rgba(*((0.12, 0.10, 0.09) if style == 'ink' else (0.9, 0.82, 0.66)), 0.9); c.set_line_width(2.2)
    c.move_to(-30, 0); c.line_to(0, -23); c.line_to(30, 0); c.line_to(0, 23); c.close_path(); c.move_to(-30, 0); c.line_to(30, 0); c.stroke(); c.restore()


# ---------------------------------------------------------------- camera / finish
class FCam:
    """战场镜头。keys=[(t, cx, cy, zoom)...]；hits=[(t, 幅度)] 在重拍处抖一下并轻微推近；rot 可给一点倾角。"""

    def __init__(self, keys, lt, hits=(), rot=0.0):
        self.cx, self.cy, self.z = [kf(keys, lt, j) for j in (1, 2, 3)]; self.sx = self.sy = 0.0; self.rot = rot
        for h, a in hits:
            if lt >= h:
                e = math.exp(-(lt - h) / 0.13); self.sx += a * e * math.sin((lt - h) * 85); self.sy += a * e * math.sin((lt - h) * 67 + 1); self.z *= 1 + 0.04 * math.exp(-(lt - h) * 7)

    def apply(self, c): c.translate(SW / 2 + self.sx, SH / 2 + self.sy); c.rotate(self.rot); c.scale(self.z, self.z); c.translate(-self.cx, -self.cy); c.set_line_cap(cairo.LINE_CAP_ROUND)

    def S(self, x, y):       # 世界坐标 -> 屏幕坐标（放文字用；rot 很小时忽略）
        return ((x - self.cx) * self.z + SW / 2, (y - self.cy) * self.z + SH / 2)


def canvas():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, SH); return s, cairo.Context(s)


_tex = {}


def ground(style='ink'):
    """战场底：宣纸 / 夜色。"""
    if style not in _tex:
        n = fbm(SH, SW, 180, 5, 41); n2 = fbm(SH, SW, 9, 2, 42); fib = cv2.GaussianBlur(rng.random((SH, SW)).astype(np.float32), (0, 0), sigmaX=9, sigmaY=0.6)
        base = np.float32([0.93, 0.89, 0.81]) if style == 'ink' else np.float32([0.075, 0.085, 0.12])
        _tex[style] = (base * (0.88 + 0.2 * n[..., None] + 0.06 * (n2[..., None] - 0.5)) * (1 + 1.2 * (fib[..., None] - 0.5)).clip(0.92, 1.08)).astype(np.float32)
    return _tex[style]


def finish(surf, lt, X=None, style='ink', hits=(), tex=None):
    """把 cairo 层压到底上 + 暗角 + 开场/重拍闪白 + 颗粒（夜色加辉光），最后叠文字。-> PIL.Image"""
    rgb, a = surf_rgba(surf); frame = (ground(style) if tex is None else tex) * (1 - a) + rgb
    if style == 'night':
        br = np.maximum(frame - 0.45, 0); frame = frame + 0.7 * cv2.GaussianBlur(br, (0, 0), 8) + 0.35 * cv2.GaussianBlur(br, (0, 0), 28)
        frame = frame * (1 - 0.62 * VR); fc = np.float32([1.0, 0.88, 0.6])
    else: frame = frame * (1 - 0.42 * VR); fc = np.float32([1.0, 0.97, 0.9])
    frame = frame + fc * 0.45 * math.exp(-lt * 10)
    for h in hits:
        if lt >= h: frame = frame + fc * 0.4 * math.exp(-(lt - h) * 10)
    img = to_img(frame + grain())
    return X.over(img) if X is not None else img
