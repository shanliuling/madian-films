"""mapwar.mapshot — 地图镜头：倾斜沙盘 / 垂直全局，两种风格（'ink' 宣纸水墨，'night' 夜色水墨），
势力晕染、立牌（山/城/军）、行军箭头、交火、易手特效、日期与占地比例、字卡。

MapShot(world, sc) 的 sc（dict，全部可选，按需给）：
  style      callable(t) -> 'ink' | 'night'                    默认全程 'ink'
  camseg     [[(t, lon, lat, zoom, tilt), ...], ...]            每段是一次连续的地图镜头；tilt 1=斜视沙盘 0=垂直俯视（可在段内渐变）
  armies     [dict(n=名, o=势力, cav=0/1, path=[(t, lon, lat, 万人)], rout=[(t0,t1)], tags=[(t0,t1,'56万')], die=t)]
  arrows     [(t_start, t_full, t_fade, owner, width, [(lon,lat),...])]
  fires      [(lon, lat, t0, t1)]                               交火点
  dates      [(t, 主日期, 副日期)]                                左上角
  cards      [(t0, t1, 大字, 底部一句, mode)]                     mode: 'corner' 横排砸到正中再缩到左上角日期下面(默认) / 'side' 右侧竖排（手机上会被平台按钮挡，少用）/ 'slam' 居中砸下再移到右侧 / 'huge' 单个巨字
  shakes     [(t, 幅度)]     flashes [t, ...]
  regions    [(名, lon, lat)]   全局俯视时显示的地区名      keycity  {城名}  全局俯视时仍显示名字的城
  hud        dict(share=True, order=[势力id...], note='…为示意')
  ground_fx  callable(ms, c, t, Sp, st)          画在地面上的自定义图形（Sp(lon,lat)->(x,y,scale)）
  overlay    callable(ms, X, t, Sp, st, tilt)    自定义文字（X 是 util.Txt）
  post       callable(frame, t, st) -> frame     自定义调色（如某段压暗）
  top        callable(ms, img, t) -> img         最后叠加（如贴人物）
"""
import math
import numpy as np, cairo, cv2
from .util import SW, SH, FPS, TAU, cl, ease, eout, hsh, surf_rgba, to_img, Txt, VR, HAZE, grain

NEUTRAL_FLAG = {'ink': (0.45, 0.42, 0.38), 'night': (0.5, 0.45, 0.4)}


def figs(wan):
    """兵力（万）-> 方阵里画几个人。开方缩放：差距看得出，小部队也看得见。"""
    return 3 if wan < 0.005 else 5 if wan < 0.05 else int(max(7, min(84, 4 + 10.5 * math.sqrt(wan))))


class MapShot:
    def __init__(self, world, sc):
        self.w = world; self.sc = sc
        self.cps = [self._cam_path(k) for k in sc.get('camseg', [[(0, (world.LON0 + world.LON1) / 2, (world.LAT0 + world.LAT1) / 2, 0.62, 0)]])]
        self.splines = [self._spline(a[5]) for a in sc.get('arrows', [])]
        self.mount = []
        for ri, (pl, big_) in enumerate(world.cfg.get('ranges', [])):
            step = 0.26 * world.ds
            for i in range(len(pl) - 1):
                (a0, b0), (a1, b1) = pl[i], pl[i + 1]; n = max(2, int(math.hypot((a1 - a0) * world.KX, b1 - b0) / step))
                for k in range(n):
                    u = (k + hsh(ri * 31 + i, k) * 0.6) / n
                    self.mount.append((a0 + (a1 - a0) * u + (hsh(ri, k * 7 + i) - 0.5) * step, b0 + (b1 - b0) * u + (hsh(ri + 5, k * 3 + i) - 0.5) * step, big_ * (0.7 + 0.6 * hsh(ri * 13 + i, k + 9)), ri * 100 + i * 10 + k))
        self.Qm = np.diag([world.q, world.q, 1.0])

    def col(self, o, st): return self.w.sides[o][st]

    # ---------------------------------------------------------------- camera
    def _cam_path(self, keys):
        keys = [k if len(k) == 5 else tuple(k) + (1,) for k in keys]
        t0, t1 = keys[0][0], keys[-1][0]; ts = np.arange(t0, t1 + 2 / FPS, 1 / FPS)
        arr = np.stack([np.interp(ts, [k[0] for k in keys], [k[j] for k in keys]) for j in (1, 2, 3, 4)], 1)
        pad = 12; a = np.concatenate([np.repeat(arr[:1], pad, 0), arr, np.repeat(arr[-1:], pad, 0)])
        ker = np.exp(-np.linspace(-2.2, 2.2, 2 * pad + 1) ** 2); ker /= ker.sum()                  # 平滑，避免镜头一顿一顿
        return ts, np.stack([np.convolve(a[:, j], ker, 'valid') for j in range(4)], 1)

    def camera(self, t):
        """-> (3x3 单应矩阵：纹理坐标->屏幕, tilt)。zoom 越大越近；tilt=0 时画面是纹理上的一个正矩形。"""
        seg = self.cps[0]
        for ts, arr in self.cps:
            if t >= ts[0] - 1e-6: seg = (ts, arr)
        ts, arr = seg
        lo, la, z, tl = [float(np.interp(t, ts, arr[:, j])) for j in range(4)]; tl = cl(tl); sx = sy = 0.0
        for h, a in self.sc.get('shakes', []):
            if 0 <= t - h < 1:
                e = math.exp(-(t - h) / 0.13); sx += a * e * math.sin((t - h) * 85); sy += a * e * math.sin((t - h) * 67 + 1.3)
                if a >= 20: z *= 1 + 0.07 * math.exp(-(t - h) * 6)
        ccx, ccy = self.w.P(lo, la); hw = 620 / z; hh = hw * SH / SW
        tq = np.float32([[ccx - 500 / z, ccy + 330 / z], [ccx + 500 / z, ccy + 330 / z], [ccx + 1040 / z, ccy - 560 / z], [ccx - 1040 / z, ccy - 560 / z]])
        vq = np.float32([[ccx - hw, ccy + hh], [ccx + hw, ccy + hh], [ccx + hw, ccy - hh], [ccx - hw, ccy - hh]])
        dst = np.float32([[0, SH + 40 * tl], [SW, SH + 40 * tl], [SW, 150 * tl], [0, 150 * tl]]) + np.float32([sx, sy])
        return cv2.getPerspectiveTransform(np.float32(vq + (tq - vq) * tl), np.float32(dst)), tl      # 注意必须是 float32

    # ---------------------------------------------------------------- billboards
    @staticmethod
    def mountain(c, x, y, s, seed, st):
        w = 46 * s; h = 40 * s * (0.8 + 0.5 * hsh(seed, 1))
        for k, (ox, hk) in enumerate([(-0.55, 0.62), (0.5, 0.74), (0, 1.0)]):
            px = x + ox * w * 0.8; ph = h * hk; pw = w * (0.55 + 0.2 * hk); lean = (hsh(seed, k + 2) - 0.5) * pw * 0.5
            c.move_to(px - pw, y); c.curve_to(px - pw * 0.45, y - ph * 0.35, px + lean - pw * 0.18, y - ph * 0.92, px + lean, y - ph)
            c.curve_to(px + lean + pw * 0.2, y - ph * 0.8, px + pw * 0.55, y - ph * 0.3, px + pw, y); c.close_path()
            g = cairo.LinearGradient(px - pw, y - ph, px + pw, y)
            if st == 'ink':
                g.add_color_stop_rgba(0, 0.80, 0.76, 0.66, 0.95); g.add_color_stop_rgba(0.55, 0.42, 0.44, 0.43, 0.95); g.add_color_stop_rgba(1, 0.20, 0.22, 0.24, 0.9)
                c.set_source(g); c.fill_preserve(); c.set_source_rgba(0.08, 0.08, 0.09, 0.9); c.set_line_width(max(1.0, 1.7 * s)); c.stroke()
            else:
                g.add_color_stop_rgba(0, 0.34, 0.40, 0.52, 1); g.add_color_stop_rgba(0.6, 0.13, 0.16, 0.24, 1); g.add_color_stop_rgba(1, 0.05, 0.06, 0.10, 1)
                c.set_source(g); c.fill_preserve(); c.set_source_rgba(0.72, 0.80, 0.95, 0.7); c.set_line_width(max(1.0, 1.3 * s)); c.stroke()

    @staticmethod
    def city_icon(c, x, y, s, flagcol, show, st, pulse=0.0):
        wall = (0.10, 0.09, 0.09) if st == 'ink' else (0.93, 0.90, 0.82)          # 夜色里城是象牙白：主角要比底图亮
        k = {1: 1.0, 2: 1.45, 3: 0.9}[show] * (1 + 0.35 * pulse); w = 20 * s * k; h = 13 * s * k
        def fin(): c.set_source_rgb(*wall); c.fill()
        if show == 3:        # 关隘：两墩夹一门
            for sx in (-1, 1): c.rectangle(x + sx * w * 0.75 - w * 0.3, y - h * 1.5, w * 0.6, h * 1.5); fin()
            c.rectangle(x - w * 0.9, y - h * 1.9, w * 1.8, h * 0.4); fin()
        else:
            c.rectangle(x - w, y - h, 2 * w, h); fin()
            for i in range(5): c.rectangle(x - w + i * w * 0.45, y - h * 1.3, w * 0.25, h * 0.32)
            fin()
            c.move_to(x - w * 0.75, y - h * 1.25); c.line_to(x - w * 0.5, y - h * 1.95); c.line_to(x + w * 0.5, y - h * 1.95); c.line_to(x + w * 0.75, y - h * 1.25); c.close_path(); fin()
            c.set_source_rgb(*((0.88, 0.80, 0.63) if st == 'ink' else (0.08, 0.09, 0.13))); c.arc(x, y - h * 0.38, w * 0.2, math.pi, TAU); c.rectangle(x - w * 0.2, y - h * 0.38, w * 0.4, h * 0.38); c.fill()
        fh = h * (3.6 if show == 2 else 2.9)
        c.set_source_rgb(*wall); c.set_line_width(max(1.2, 2 * s)); c.move_to(x + w * 0.1, y - h * 1.5); c.line_to(x + w * 0.1, y - fh); c.stroke()
        c.set_source_rgb(*flagcol); c.move_to(x + w * 0.1, y - fh); c.line_to(x + w * 1.15, y - fh + h * 0.3); c.line_to(x + w * 0.1, y - fh + h * 0.75); c.close_path(); c.fill()

    @staticmethod
    def army_egg(c, x, y, s, oc, n, facing, st, t, moving, rout, seed, look, cav=0):
        """大头兵方阵（Q 版题材）：look = dict(body 衣服色, hat 'bajiao'|'helmet'|'junmao'|'strawhat'|'ancient', hatcol 帽色, star 红星,
        weapon 'rifle'(默认)|'spear'|'ji', plume 盔缨色, band 盔沿色)。cav=1 时骑马。返回旗顶 y。"""
        body = look.get('body', oc); hatc = look.get('hatcol', tuple(v * 0.8 for v in body)); hat = look.get('hat', 'helmet'); OLc = (0.1, 0.08, 0.08); skin = (0.96, 0.84, 0.70)
        rows = 1 if n <= 5 else 2 if n < 14 else 3 if n < 34 else 4 if n < 58 else 5
        cols = int(math.ceil(n / rows)); u = 13.0 * s; al = 1 - 0.75 * rout; lw = max(1.0, u * 0.11)
        c.set_source_rgba(0, 0, 0, (0.22 if st == 'ink' else 0.45) * al); c.save(); c.translate(x, y + u * 0.3); c.scale(1, 0.3); c.arc(0, 0, max(2.2, cols * 0.78 + rout * 3) * u, 0, TAU); c.fill(); c.restore()
        if st == 'night':
            rr = max(3.0, cols * 1.3) * u; g = cairo.RadialGradient(x, y - u * 1.2, 0, x, y - u * 1.2, rr)
            g.add_color_stop_rgba(0, *oc, 0.5 * al); g.add_color_stop_rgba(0.5, *oc, 0.18 * al); g.add_color_stop_rgba(1, *oc, 0)
            c.save(); c.translate(0, (y - u * 1.2) * 0.45); c.scale(1, 0.55); c.set_source(g); c.arc(x, y - u * 1.2, rr, 0, TAU); c.fill(); c.restore()
        c.set_line_cap(cairo.LINE_CAP_ROUND); k_ = 0
        for r in range(rows):
            for k in range(cols):
                k_ += 1
                if k_ > n: break
                jx = (hsh(k + seed, r) - 0.5); jy = (hsh(k + seed, r + 9) - 0.5)
                fx = x + (k - (cols - 1) / 2) * u * 1.4 + r * u * 0.5 * facing + jx * u * (0.25 + 9 * rout)
                ph = t * 10 + k * 1.7 + r; bob = abs(math.sin(ph)) * u * 0.25 * moving
                fy = y - (rows - 1 - r) * u * 0.85 - bob + jy * u * 5 * rout; sw = math.sin(ph) * u * 0.28 * moving
                wp = look.get('weapon', 'rifle')
                if cav:                                                          # 骑兵：先画马，人整体抬高
                    hb = (0.42, 0.28, 0.16) if (k + r) % 3 else (0.22, 0.16, 0.12); gal = math.sin(ph * 1.3) * u * 0.35 * moving
                    c.set_source_rgba(*OLc, al); c.set_line_width(u * 0.22)
                    for q, d_ in ((-0.75, 1), (-0.45, -1), (0.45, 1), (0.75, -1)): c.move_to(fx + q * u * facing, fy - u * 0.9); c.line_to(fx + q * u * facing + d_ * gal, fy + bob * 0.3); c.stroke()
                    c.save(); c.translate(fx, fy - u * 1.15 - bob * 0.5); c.scale(1.15, 0.55); c.arc(0, 0, u, 0, TAU); c.restore(); c.set_source_rgba(*hb, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.set_line_width(lw); c.stroke()
                    c.move_to(fx + facing * u * 0.8, fy - u * 1.3 - bob * 0.5); c.line_to(fx + facing * u * 1.35, fy - u * 2.1 - bob * 0.5); c.set_source_rgba(*hb, al); c.set_line_width(u * 0.5); c.stroke()
                    c.save(); c.translate(fx + facing * u * 1.55, fy - u * 2.05 - bob * 0.5); c.scale(1.0, 0.6); c.arc(0, 0, u * 0.42, 0, TAU); c.restore(); c.set_source_rgba(*hb, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.stroke()
                    fy -= u * 1.2 + bob * 0.5; bob = 0
                else:
                    c.set_source_rgba(*OLc, al); c.set_line_width(u * 0.26)
                    for q in (-1, 1): c.move_to(fx + q * u * 0.16, fy - u * 0.5); c.line_to(fx + q * u * 0.16 + q * sw, fy + bob); c.stroke()
                if rout < 0.3 and wp in ('spear', 'ji'):                        # 长枪/戟：竖握，枪头朝上
                    gx = fx + facing * u * 0.55; c.set_source_rgba(*look.get('shaft', (0.55, 0.38, 0.2)), al); c.set_line_width(u * 0.16); c.move_to(gx, fy - u * 0.3); c.line_to(gx + facing * u * 0.15, fy - u * 3.0); c.stroke()
                    tx, ty = gx + facing * u * 0.17, fy - u * 3.1; c.move_to(tx, ty - u * 0.45); c.line_to(tx - u * 0.13, ty); c.line_to(tx + u * 0.13, ty); c.close_path(); c.set_source_rgba(0.85, 0.87, 0.9, al); c.fill()
                    if wp == 'ji': c.move_to(tx, ty + u * 0.1); c.curve_to(tx + facing * u * 0.35, ty, tx + facing * u * 0.4, ty + u * 0.35, tx + facing * u * 0.15, ty + u * 0.4); c.fill()
                    c.arc(tx, ty + u * 0.12, u * 0.13, 0, TAU); c.set_source_rgba(0.9, 0.12, 0.08, al); c.fill()
                elif rout < 0.3:                                                # 枪：背在肩上，枪口朝上
                    c.set_source_rgba(0.45, 0.28, 0.14, al); c.set_line_width(u * 0.2); c.move_to(fx - facing * u * 0.3, fy - u * 0.5); c.line_to(fx - facing * u * 0.52, fy - u * 1.5); c.stroke()
                    c.set_source_rgba(0.15, 0.15, 0.17, al); c.set_line_width(u * 0.12); c.move_to(fx - facing * u * 0.52, fy - u * 1.5); c.line_to(fx - facing * u * 0.66, fy - u * 2.15); c.stroke()
                c.rectangle(fx - u * 0.38, fy - u * 1.2, u * 0.76, u * 0.8); c.set_source_rgba(*body, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.set_line_width(lw); c.stroke()
                hx, hy, R = fx + facing * u * 0.06, fy - u * 1.72, u * 0.56
                c.arc(hx, hy, R, 0, TAU); c.set_source_rgba(*skin, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.stroke()
                if hat == 'bajiao':
                    c.move_to(hx - 1.05 * R, hy - 0.25 * R); c.line_to(hx - 1.1 * R, hy - 0.9 * R); c.line_to(hx - 0.5 * R, hy - 1.2 * R); c.line_to(hx + 0.5 * R, hy - 1.2 * R); c.line_to(hx + 1.1 * R, hy - 0.9 * R); c.line_to(hx + 1.05 * R, hy - 0.25 * R)
                    c.line_to(hx + facing * 1.5 * R, hy - 0.2 * R); c.line_to(hx + facing * 1.0 * R, hy - 0.32 * R); c.close_path(); c.set_source_rgba(*hatc, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.stroke()
                    if look.get('star', True): c.arc(hx + facing * 0.4 * R, hy - 0.7 * R, 0.2 * R, 0, TAU); c.set_source_rgba(0.92, 0.1, 0.08, al); c.fill()
                elif hat == 'strawhat':
                    c.save(); c.translate(hx, hy - 0.5 * R); c.scale(1, 0.3); c.arc(0, 0, 1.5 * R, 0, TAU); c.restore(); c.set_source_rgba(*hatc, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.stroke()
                    c.save(); c.translate(hx, hy - 0.68 * R); c.scale(1, 0.7); c.arc(0, 0, 0.75 * R, math.pi, TAU); c.restore(); c.close_path(); c.set_source_rgba(*hatc, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.stroke()
                elif hat == 'ancient':                                          # 古代头盔：圆顶 + 盔沿 + 盔缨
                    c.move_to(hx - 1.15 * R, hy - 0.05 * R); c.curve_to(hx - 1.2 * R, hy - 1.45 * R, hx + 1.2 * R, hy - 1.45 * R, hx + 1.15 * R, hy - 0.05 * R); c.close_path(); c.set_source_rgba(*hatc, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.stroke()
                    c.move_to(hx - 1.15 * R, hy - 0.25 * R); c.line_to(hx + 1.15 * R, hy - 0.25 * R); c.set_source_rgba(*look.get('band', (0.85, 0.7, 0.25)), al); c.set_line_width(u * 0.18); c.stroke(); c.set_line_width(lw)
                    c.move_to(hx, hy - 1.05 * R); c.curve_to(hx - facing * 0.2 * R, hy - 1.7 * R, hx - facing * 0.7 * R, hy - 1.9 * R, hx - facing * 1.0 * R, hy - 1.6 * R); c.set_source_rgba(*look.get('plume', (0.9, 0.12, 0.08)), al); c.set_line_width(u * 0.3); c.stroke(); c.set_line_width(lw)
                elif hat == 'junmao':
                    c.rectangle(hx - 0.95 * R, hy - 1.0 * R, 1.9 * R, 0.62 * R); c.set_source_rgba(*hatc, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.stroke()
                    c.save(); c.translate(hx, hy - 1.0 * R); c.scale(1.3, 0.38); c.arc(0, 0, R, 0, TAU); c.restore(); c.set_source_rgba(*hatc, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.stroke()
                    c.move_to(hx + facing * 0.3 * R, hy - 0.36 * R); c.line_to(hx + facing * 1.4 * R, hy - 0.3 * R); c.set_source_rgba(*OLc, al); c.set_line_width(u * 0.16); c.stroke(); c.set_line_width(lw)
                else:
                    c.move_to(hx - 1.2 * R, hy - 0.1 * R); c.curve_to(hx - 1.2 * R, hy - 1.5 * R, hx + 1.2 * R, hy - 1.5 * R, hx + 1.2 * R, hy - 0.2 * R); c.close_path(); c.set_source_rgba(*hatc, al); c.fill_preserve(); c.set_source_rgba(*OLc, al); c.stroke()
                c.set_source_rgba(*OLc, al)
                for q in (-1, 1): c.arc(hx + facing * 0.28 * R + q * 0.3 * R, hy + 0.15 * R, 0.11 * R, 0, TAU); c.fill()
        bx = x - facing * min(cols, 6) * u * 0.3; by = y - rows * u * 0.95; fl = math.sin(t * 7) * u * 0.25; bf = -facing
        c.set_source_rgba(*((0.08, 0.07, 0.07) if st == 'ink' else (1.0, 0.9, 0.7)), al); c.set_line_width(max(1.5, u * 0.2)); c.move_to(bx, by + u * 2.0); c.line_to(bx, by - u * 4.6); c.stroke()
        c.set_source_rgba(*oc, al); c.move_to(bx, by - u * 4.6)
        c.curve_to(bx + bf * u * 1.3, by - u * 5.0 + fl, bx + bf * u * 2.2, by - u * 4.1 - fl, bx + bf * u * 3.3, by - u * 4.4 + fl)
        c.line_to(bx + bf * u * 3.1, by - u * 2.7 + fl); c.curve_to(bx + bf * u * 2.1, by - u * 2.4 - fl, bx + bf * u * 1.2, by - u * 3.2 + fl, bx, by - u * 2.8); c.close_path(); c.fill()
        return by - u * 5.0

    @staticmethod
    def army(c, x, y, s, oc, n, cav, facing, st, t, moving, rout=0.0, seed=0):
        """小人方阵：n 个人（由 figs(兵力) 得出），cav=1 画骑兵。rout 0..1 溃散。返回旗顶 y（放名字用）。"""
        if st == 'ink': body, rimc = (0.08, 0.07, 0.07), oc
        else: body, rimc = tuple(min(1, v * 0.85 + 0.28) for v in oc), (1.0, 0.96, 0.88)       # 夜色：亮色小人
        rows = 1 if n <= 5 else 2 if n < 14 else 3 if n < 34 else 4 if n < 58 else 5
        cols = int(math.ceil(n / rows)); u = 12.5 * s; al = 1 - 0.75 * rout
        c.set_source_rgba(0, 0, 0, (0.25 if st == 'ink' else 0.5) * al); c.save(); c.translate(x, y + u * 0.3); c.scale(1, 0.3); c.arc(0, 0, max(2.2, cols * 0.72 + rout * 3) * u, 0, TAU); c.fill(); c.restore()
        if st == 'night':        # 火把光晕
            rr = max(3.0, cols * 1.3) * u; g = cairo.RadialGradient(x, y - u * 1.2, 0, x, y - u * 1.2, rr)
            g.add_color_stop_rgba(0, *oc, 0.55 * al); g.add_color_stop_rgba(0.5, *oc, 0.2 * al); g.add_color_stop_rgba(1, *oc, 0)
            c.save(); c.translate(0, (y - u * 1.2) * 0.45); c.scale(1, 0.55); c.set_source(g); c.arc(x, y - u * 1.2, rr, 0, TAU); c.fill(); c.restore()
        c.set_line_cap(cairo.LINE_CAP_ROUND); k_ = 0
        for r in range(rows):
            for k in range(cols):
                k_ += 1
                if k_ > n: break
                jx = (hsh(k + seed, r) - 0.5); jy = (hsh(k + seed, r + 9) - 0.5)
                fx = x + (k - (cols - 1) / 2) * u * 1.25 + r * u * 0.45 * facing + jx * u * (0.3 + 9 * rout)
                bob = abs(math.sin(t * (12 if cav else 9) + k * 1.7 + r)) * u * 0.28 * moving
                fy = y - (rows - 1 - r) * u * 0.78 - bob + jy * u * 5 * rout; hh = u * 2.5; lean = facing * u * 0.25 * moving
                if cav:
                    c.set_source_rgba(*body, al); c.set_line_width(u * 0.5); c.move_to(fx - facing * u * 0.75, fy - hh * 0.16); c.line_to(fx + facing * u * 0.85, fy - hh * 0.2); c.stroke()
                    c.arc(fx + facing * u * 1.0, fy - hh * 0.3, u * 0.22, 0, TAU); c.fill()
                c.set_source_rgba(*rimc, al); c.set_line_width(u * 0.62); c.move_to(fx - facing * u * 0.1, fy - hh * 0.2); c.line_to(fx - facing * u * 0.1 + lean, fy - hh * 0.62); c.stroke()
                c.set_source_rgba(*body, al); c.set_line_width(u * 0.5); c.move_to(fx, fy - hh * (0.18 if cav else 0)); c.line_to(fx + lean, fy - hh * 0.62); c.stroke()
                c.arc(fx + lean * 1.2, fy - hh * 0.8, u * 0.33, 0, TAU); c.fill()
                if rout < 0.3:
                    c.set_line_width(max(1, u * 0.14)); c.move_to(fx + facing * u * 0.35, fy - hh * 0.2); c.line_to(fx + facing * u * (0.75 + 0.5 * moving), fy - hh * 1.35); c.stroke()
        bx = x - facing * min(cols, 6) * u * 0.25; by = y - rows * u * 0.9; fl = math.sin(t * 7) * u * 0.25; bf = -facing
        c.set_source_rgba(*((0.08, 0.07, 0.07) if st == 'ink' else (1.0, 0.9, 0.7)), al); c.set_line_width(max(1.5, u * 0.22)); c.move_to(bx, by + u * 2.2); c.line_to(bx, by - u * 5.2); c.stroke()
        c.set_source_rgba(*oc, al); c.move_to(bx, by - u * 5.2)
        c.curve_to(bx + bf * u * 1.5, by - u * 5.7 + fl, bx + bf * u * 2.6, by - u * 4.6 - fl, bx + bf * u * 3.9, by - u * 5.0 + fl)
        c.line_to(bx + bf * u * 3.6, by - u * 2.9 + fl); c.curve_to(bx + bf * u * 2.5, by - u * 2.6 - fl, bx + bf * u * 1.4, by - u * 3.5 + fl, bx, by - u * 3.0); c.close_path(); c.fill()
        return by - u * 5.6

    def _spline(self, pts):
        pp = [self.w.P(*p) for p in pts]; out = []
        for i in range(len(pp) - 1):
            p0 = pp[max(0, i - 1)]; p1 = pp[i]; p2 = pp[i + 1]; p3 = pp[min(len(pp) - 1, i + 2)]
            for s in np.linspace(0, 1, 18, endpoint=False):
                out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * s + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * s * s + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * s ** 3) for j in (0, 1)))
        out.append(pp[-1]); return out

    @staticmethod
    def draw_arrow(c, Hm, sp, k, w, col, a):
        """笔触箭头：由细到粗，躺在地面上（随镜头透视）。k=生长进度。"""
        n = max(6, int(len(sp) * cl(k))); sp = sp[:n]
        pts = cv2.perspectiveTransform(np.float32(sp)[None], Hm)[0]; pts2 = cv2.perspectiveTransform(np.float32(sp)[None] + np.float32([8, 0]), Hm)[0]
        sc = np.abs(pts2[:, 0] - pts[:, 0]) / 8; L, Rr = [], []
        for i in range(n):
            a0 = pts[max(0, i - 1)]; a1 = pts[min(n - 1, i + 1)]; dx, dy = a1 - a0; l = math.hypot(dx, dy) + 1e-6; nx, ny = -dy / l, dx / l
            u = i / (n - 1); ww = w * sc[i] * (0.3 + 0.7 * u ** 0.7) * (1 + 0.12 * math.sin(i * 0.9))
            L.append((pts[i][0] + nx * ww, pts[i][1] + ny * ww * 0.6)); Rr.append((pts[i][0] - nx * ww, pts[i][1] - ny * ww * 0.6))
        c.set_source_rgba(*col, a); c.move_to(*L[0])
        for p in L[1:-3]: c.line_to(*p)
        for p in reversed(Rr[:-3]): c.line_to(*p)
        c.close_path(); c.fill()
        d = pts[-1] - pts[-5]; ang = math.atan2(d[1], d[0]); ws = w * sc[-1]
        c.save(); c.translate(*pts[-4]); c.rotate(ang); c.move_to(ws * 3.4, 0); c.line_to(-ws * 0.6, -ws * 2.0); c.line_to(ws * 0.2, 0); c.line_to(-ws * 0.6, ws * 2.0); c.close_path(); c.fill(); c.restore()

    # ---------------------------------------------------------------- ground
    def _ground(self, st, Hm, tilt, Ms, heat, heat_s):
        W = self.w; NO = W.NO
        b_ = cv2.warpPerspective(W.BASE, Hm, (SW, SH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0.88, 0.80, 0.63, 0.5))
        frame = b_[..., :3].copy(); g = b_[..., 3]
        # 两个最大势力交界处：焦墨线 / 亮线
        big = sorted(range(NO), key=lambda o: -float(Ms[..., o].sum()))[:2]
        bd = np.clip(cv2.GaussianBlur(Ms[..., big[0]], (0, 0), 5) * cv2.GaussianBlur(Ms[..., big[1]], (0, 0), 5) * 6, 0, 1) if NO > 1 else np.zeros((SH, SW), np.float32)
        if st == 'night':        # 同一张图"入夜"：底图反相压暗，势力变成发光的晕染
            lum = frame.mean(-1, keepdims=True); v = np.clip((0.80 - lum) / 0.55, 0, 1)
            frame = np.float32([0.040, 0.050, 0.075]) * (0.7 + 0.6 * lum) + v ** 1.5 * np.float32([0.30, 0.44, 0.62])
            for o in range(NO):
                m = Ms[..., o]; colo = np.float32(self.col(o, st)); ws = W.sides[o].get('wash', 1.0)
                edge = np.clip(cv2.GaussianBlur(m, (0, 0), 2.5) - cv2.GaussianBlur(m, (0, 0), 11), 0, 1) * 2.2
                frame += (m * (0.17 + 0.13 * g) * ws)[..., None] * colo + (edge * 0.42 * ws)[..., None] * (colo * 0.75 + 0.25)
            frame += bd[..., None] * np.float32([1.0, 0.85, 0.6]) * 0.45 + np.clip(heat_s, 0, 1)[..., None] * np.float32([1.0, 0.8, 0.4]) * 0.35
            if heat.max() > 0.03:        # 易手瞬间：金色格子一闪即逝（格子只当特效，不常驻）
                nx, ny, cx, cy, cland, vrand = W.CELLS
                hcell = np.zeros(ny * nx + 1, np.float32); hcell[:ny * nx] = (np.clip(heat[np.ix_(np.minimum(cy // W.q, W.oh - 1), np.minimum(cx // W.q, W.ow - 1))], 0, 1) * vrand * cland).reshape(-1)
                geo = cv2.warpPerspective(W.GEO, Hm, (SW, SH), flags=cv2.INTER_LINEAR)
                cid = cv2.warpPerspective(W.CID, Hm, (SW, SH), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=float(ny * nx))
                hh = hcell[np.clip(cid.astype(np.int32), 0, ny * nx)][..., None]
                frame += hh * (geo[..., 0:1] * np.float32([1.0, 0.72, 0.28]) * 0.3 + geo[..., 1:2] * np.float32([1.0, 0.95, 0.8]) * 0.5)
            hz = np.float32([0.03, 0.04, 0.06])
        else:                    # 宣纸：势力是"乘"上去的淡彩，边缘颜料堆积
            for o in range(NO):
                m = Ms[..., o]; ws = W.sides[o].get('wash', 1.0)
                edge = np.clip(cv2.GaussianBlur(m, (0, 0), 2.5) - cv2.GaussianBlur(m, (0, 0), 11), 0, 1) * 2.2
                a = np.clip(m * (0.50 + 0.38 * g) + edge * 0.55, 0, 0.9) * ws
                frame *= (1 - a[..., None] * (1 - (np.float32(self.col(o, st)) * 0.75 + 0.25)))
            frame *= (1 - 0.6 * bd[..., None])
            frame *= (1 - np.clip(heat_s, 0, 1)[..., None] * np.float32([0.16, 0.26, 0.30]))      # 易手：湿墨前锋
            hz = np.float32([0.93, 0.88, 0.76])
        HZ = HAZE * tilt
        return frame * (1 - HZ) + hz * HZ, HZ

    # ---------------------------------------------------------------- frame
    def frame(self, t):
        W = self.w; sc = self.sc; st = sc['style'](t) if sc.get('style') else 'ink'
        Hm, tilt = self.camera(t)
        own, stg, M, heat, share = W.ownership(t)
        Ms = cv2.warpPerspective(np.dstack([M, heat]), Hm @ self.Qm, (SW, SH), flags=cv2.INTER_LINEAR); heat_s = Ms[..., W.NO]
        frame, HZ = self._ground(st, Hm, tilt, Ms, heat, heat_s)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, SH); c = cairo.Context(surf)

        def Sp(lo, la):
            x, y = W.P(lo, la); v = Hm @ np.float64([x, y, 1]); sx, sy = v[0] / v[2], v[1] / v[2]
            v2 = Hm @ np.float64([x + 10, y, 1]); return sx, sy, abs(v2[0] / v2[2] - sx) / 10
        if sc.get('ground_fx'): sc['ground_fx'](self, c, t, Sp, st)
        for i, (t0, t1, tf, o, w, pts) in enumerate(sc.get('arrows', [])):
            if t0 <= t < tf + 0.5:
                oc = np.float32(self.col(o, st)); col = tuple(oc * 0.78) if st == 'ink' else tuple(np.minimum(1, oc * 1.15 + 0.12))
                self.draw_arrow(c, Hm, self.splines[i], eout((t - t0) / max(1e-3, t1 - t0), 1.6), w, col, 0.9 * (1 - ease((t - tf) / 0.5)))
        items = []; labels = []
        for lo, la, big_, seed in self.mount:
            sx, sy, s_ = Sp(lo, la)
            if -90 < sx < SW + 90 and 150 * tilt - 30 < sy < SH + 70: items.append((sy, 0, sx, s_, big_, seed))
        for i, (nm, lo, la, _, show) in enumerate(W.cities):
            if not show: continue
            sx, sy, s_ = Sp(lo, la)
            if -60 < sx < SW + 60 and 160 * tilt - 20 < sy < SH + 40:
                prev, o, k, tf = W.city_state(i, t); items.append((sy, 1, sx, s_, (nm, o if k > 0.4 else prev, show, k, tf), i))
        for ai, A in enumerate(sc.get('armies', [])):
            path = A['path']
            if t < path[0][0] or t > A.get('die', 1e9): continue
            ts_ = [p[0] for p in path]; f = lambda j, tt=t: float(np.interp(tt, ts_, [p[j] for p in path]))
            lo, la, wan = f(1), f(2), f(3); lo2, la2 = f(1, t + 0.1), f(2, t + 0.1)
            mv = cl(math.hypot((lo2 - lo) * W.KX, la2 - la) / (0.03 * W.ds)); fac = 1 if lo2 >= lo - 1e-4 else -1
            if mv < 0.05: fac = A.get('face', 1)
            r = 0.0; rl = A.get('rout', [])
            for (r0, r1) in rl:
                if r0 <= t <= r1: r = math.sin(math.pi * cl((t - r0) / (r1 - r0))) ** 0.7 * 0.9
            if A.get('die') and rl and t > rl[-1][0]: r = max(r, ease((t - rl[-1][0]) / max(1e-3, A['die'] - rl[-1][0])))
            sx, sy, s_ = Sp(lo, la); appear = ease((t - path[0][0]) / 0.25)
            tag = next((tx for (a0, a1, tx) in A.get('tags', []) if a0 <= t < a1), None)
            items.append((sy, 2, sx, s_, (A['n'], A['o'], max(3, int(figs(wan) * appear * sc.get('fig_scale', 1.0))), A.get('cav', 0), fac, mv, r, tag), ai))
        items.sort(key=lambda z: z[0])               # 远的先画
        for sy, kind, sx, s_, dat, seed in items:
            if kind == 0: self.mountain(c, sx, sy, s_ * dat * 0.8, seed, st)
            elif kind == 1:
                nm, o, show, k, tf = dat; pulse = math.exp(-(t - tf) * 5) if t >= tf else 0; neutral = W.sides[o].get('neutral')
                if 0 <= t - tf < 0.7 and not neutral:      # 易手：一圈墨环 / 金环
                    w = (t - tf) / 0.7; rr = (30 + 150 * eout(w)) * s_
                    c.save(); c.translate(sx, sy); c.scale(1, 0.5 + 0.5 * (1 - tilt)); c.set_source_rgba(*(self.col(o, st) if st == 'ink' else (1.0, 0.85, 0.5)), 0.85 * (1 - w)); c.set_line_width(10 * s_ * (1 - w) + 2); c.arc(0, 0, rr, 0, TAU); c.stroke(); c.restore()
                self.city_icon(c, sx, sy, s_ * 0.85, NEUTRAL_FLAG[st] if neutral else self.col(o, st), show, st, pulse); labels.append((sx, sy, s_, nm, show, None))
            else:
                nm, o, n, cav, fac, mv, r, tag = dat
                oc = self.col(o, st) if not W.sides[o].get('neutral') else (0.45, 0.42, 0.36)
                egg = sc.get('egg')                                             # 可选：军队画成大头兵。sc['egg'] = {势力下标或军队名: dict(body, hat, hatcol)}
                top = self.army_egg(c, sx, sy, s_, oc, n, fac, st, t, mv, r, seed, egg.get(nm, egg.get(o, {})), cav) if egg else self.army(c, sx, sy, s_, oc, n, cav, fac, st, t, mv, r, seed)
                if r < 0.8: labels.append((sx, top, s_, nm, -1 - o, tag))
        for (lo, la, f0, f1) in sc.get('fires', []):
            if f0 <= t < f1:
                amt = ease((t - f0) / 0.3) * (1 - ease((t - (f1 - 0.5)) / 0.5)); fx, fy, fs = Sp(lo, la)
                for i in range(14):
                    ph = (t * (1.2 + hsh(i)) + hsh(i, 5)) % 1.0
                    px_ = fx + (hsh(i, 1) - 0.5) * 80 * fs; py_ = fy - ph * 70 * fs - hsh(i, 2) * 20; rr = (16 + 34 * hsh(i, 3)) * fs * (1 - ph * 0.6)
                    g_ = cairo.RadialGradient(px_, py_, 0, px_, py_, rr)
                    g_.add_color_stop_rgba(0, 1.0, 0.75, 0.3, 0.6 * amt * (1 - ph)); g_.add_color_stop_rgba(0.5, 0.95, 0.3, 0.08, 0.25 * amt * (1 - ph)); g_.add_color_stop_rgba(1, 0.9, 0.2, 0.05, 0)
                    c.set_source(g_); c.arc(px_, py_, rr, 0, TAU); c.fill()
        brgb, ba = surf_rgba(surf); hzk = 1 - HZ * 0.75
        frame = frame * (1 - ba * hzk) + brgb * hzk
        # ---- 后期
        if st == 'night':
            eb = np.zeros((SH // 2, SW // 2), np.float32)        # 火星
            for i in range(90):
                ph = (t * (0.12 + 0.2 * hsh(i, 7)) + hsh(i, 8)) % 1.0
                cv2.circle(eb, (int((hsh(i, 9) * SW + math.sin(t * 1.5 + i) * 40 + ph * 160) / 2), int(SH * (1.05 - ph * (0.6 + 0.5 * hsh(i, 10))) / 2)), 1 + int(2 * hsh(i, 11)), float(1 - ph), -1)
            frame += cv2.resize(cv2.GaussianBlur(eb, (0, 0), 1.6), (SW, SH))[..., None] * np.float32([1.0, 0.6, 0.22]) * 0.9
            br = np.maximum(frame - 0.5, 0); frame = frame + 0.5 * cv2.GaussianBlur(br, (0, 0), 9) + 0.3 * cv2.GaussianBlur(br, (0, 0), 30)      # 辉光
            frame = frame * (1 - 0.62 * VR); fcol = np.float32([1.0, 0.85, 0.55])
        else:
            frame = frame * (1 - 0.42 * VR); fcol = np.float32([1.0, 0.97, 0.9])
        for t0 in sc.get('flashes', []):
            if 0 <= t - t0 < 1: frame += fcol * 0.45 * math.exp(-(t - t0) * 9)
        if sc.get('post'): frame = sc['post'](frame, t, st)
        frame = frame + grain()
        # ---- 文字
        X = Txt(st == 'night'); T = X.T
        tint = lambda o, ka=0.8, kb=1.5: (tuple(int(v * 255) for v in W.sides[o]['label']) if W.sides[o].get('label') and st == 'ink' else tuple(min(255, int(v * 255 * (ka if st == 'ink' else kb))) for v in (self.col(o, st) if not W.sides[o].get('neutral') else (0.5, 0.47, 0.42))))     # sides[o]['label'] 可单独指定文字色
        self.tint = tint
        for sx, sy, s_, nm, show, tag in sorted(labels, key=lambda z: (z[4] >= 0, -z[4])):       # 军队名字优先，其次都城
            if show < 0:
                X.place(nm + (' ' + tag if tag else ''), [(sx, sy - 14), (sx - 90, sy + 10), (sx + 90, sy + 10), (sx, sy - 70), (sx, sy - 130)], 54, fill=tint(-1 - show), stroke=7)
            elif tilt > 0.5 or nm in sc.get('keycity', ()):
                sz = 40 if show == 2 else 33; off = sz * 0.5 * len(nm) + 24 * s_ + 8
                X.place(nm, [(sx, sy + sz * 0.72), (sx + off, sy - 8), (sx - off, sy - 8), (sx, sy - 52 * s_ - sz * 0.5)], sz, stroke=5)
        if tilt < 0.5:
            for nm, lo, la in sc.get('regions', []):
                sx, sy, s_ = Sp(lo, la); X.place(nm, [(sx, sy), (sx, sy - 44), (sx, sy + 44), (sx + 70, sy)], 46, fill=X.SUB, stroke=6, a=(1 - tilt * 2) * 0.95)
        dates = sc.get('dates')
        if dates:
            di = max([i for i, k in enumerate(dates) if t >= k[0]] or [0]); a_d = ease((t - dates[di][0]) / 0.15)
            T(dates[di][1], 70, 78, 70, fill=X.ACC, anchor='lm', stroke=6, a=0.4 + 0.6 * a_d)
            if len(dates[di]) > 2 and dates[di][2]: T(dates[di][2], 74, 142, 38, anchor='lm', stroke=4)
        hud = sc.get('hud', {})
        if hud.get('share', True) and W.NO > 1:          # 顶部占地比例条：最左、最右两方标数字
            order = hud.get('order', list(range(W.NO))); bx0, bx1, by = 700, 1330, 70; xx_ = bx0
            X.d.rectangle([bx0 - 4, by - 17, bx1 + 4, by + 17], fill=X.HALO + (255,))
            for o in order:
                w_ = (bx1 - bx0) * float(share[o]); X.d.rectangle([xx_, by - 12, xx_ + w_, by + 12], fill=tint(o, 1, 1.2) + (255,)); xx_ += w_
            a_, b_ = order[0], order[-1]
            T(f"{W.sides[a_]['name']} {int(round(share[a_] * 100))}%", bx0 - 18, by, 46, anchor='rm', stroke=5, fill=tint(a_, 0.8, 1.4))
            T(f"{int(round(share[b_] * 100))}% {W.sides[b_]['name']}", bx1 + 18, by, 46, anchor='lm', stroke=5, fill=tint(b_, 0.8, 1.6))
            if hud.get('label', True): T('占地', (bx0 + bx1) / 2, by + 40, 26, fill=X.SUB, stroke=3)
        for card in sc.get('cards', []):
            t0, t1, big, sub = card[:4]; mode = card[4] if len(card) > 4 else 'corner'
            if t0 <= t < t1:
                lt = t - t0; a = ease(lt / 0.1) * (1 - ease((t - (t1 - 0.15)) / 0.15)); sc_ = 1 + 0.45 * (1 - eout(lt / 0.16)); x0 = 1775
                if mode == 'corner':                                            # 横排砸到正中 → 缩小飞到左上角（日期下面），避开右侧平台按钮
                    k = ease((lt - 0.7) / 0.28); size0 = 250 * (1 + 0.6 * (1 - eout(lt / 0.18))); size1 = 104
                    size = size0 + (size1 - size0) * k; cy = 470 + (sc.get('card_y', 196) - 470) * k
                    cx = SW / 2 + (sc.get('card_x', 70) + len(big) * size1 * 0.5 - SW / 2) * k
                    col = (168, 26, 16) if st == 'ink' else (255, 226, 150)
                    if k < 1: T(big, cx + 6 * (1 - k), cy + 6 * (1 - k), size, fill=(20, 16, 14) if st == 'ink' else (200, 40, 20), stroke=0, a=a * 0.9 * (1 - k))
                    T(big, cx, cy, size, fill=col, stroke=10 - 2 * k, a=a)
                elif mode == 'slam':
                    size = 250 * (1 + 0.6 * (1 - eout(lt / 0.18))); aa = a * (1 - ease((lt - 0.75) / 0.25))
                    T(big, SW / 2 + 6, 476, size, fill=(20, 16, 14) if st == 'ink' else (200, 40, 20), stroke=0, a=aa * 0.9)
                    T(big, SW / 2, 470, size, fill=(168, 26, 16) if st == 'ink' else (255, 226, 150), stroke=10, a=aa)
                    X.V(big, x0, 330, 128, fill=X.ACC, stroke=8, a=a * ease((lt - 0.95) / 0.2))
                elif mode == 'huge': T(big, 520, 470, 520 * sc_, fill=(168, 26, 16) if st == 'ink' else (255, 226, 150), stroke=14, a=a)
                else:
                    size = (190 if len(big) == 1 else 150 if len(big) == 2 else 128) * sc_
                    X.V(big, x0, 330 if len(big) > 2 else 420, size, fill=X.ACC, stroke=8, a=a)
                if sub: T(sub, SW / 2, 968, 64, stroke=7, a=ease((lt - 0.12) / 0.2) * (1 - ease((t - (t1 - 0.15)) / 0.15)))
        if sc.get('overlay'): sc['overlay'](self, X, t, Sp, st, tilt)
        if hud.get('note'): T(hud['note'], SW - 40, SH - 30, 24, fill=X.SUB, anchor='rm', stroke=3)
        img = to_img(frame)
        if sc.get('top'): img = sc['top'](self, img, t)
        return X.over(img)
