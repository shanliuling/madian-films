"""mapwar.world — 一张地图的"世界"：真实地理底图 + 城池归属 -> 势力范围。

World(cfg) 的 cfg（dict）：
  bbox          (lon_west, lon_east, lat_south, lat_north)     地图范围，随题材定（中国、欧亚、欧洲都行）
  px_per_deg    纹理每纬度多少像素（中国尺度 ~116；洲际尺度 ~30-40）。纹理宽高 = 范围 x 这个值
  sides         {owner_id: dict(name, ink=(r,g,b), night=(r,g,b), wash=1.0)}  势力及其在两种风格下的颜色；wash<1 表示淡（中立/诸侯）
  cities        [(name, lon, lat, owner_id, show)]   show: 0 仅作势力锚点 / 1 城 / 2 都城 / 3 关隘
  flips         {city: [(t, new_owner), ...]}        易手时间（影片秒）
  reach         (r0, r1) 度：离己方最近城 r0 以内算稳固控制，r1 以外无主。洲际尺度要放大（如 (5, 9)）
  cell_deg      易手时闪现的格子大小（度）
  ranges        [([(lon,lat),...], size)]  想强调的山脉（立牌山形），可为空
  extra_rivers  [dict(pts=[(lon,lat),...], width=6.5, dash=False, ink=None)]  手绘水系（古河道、运河）
  main_rivers / major_rivers   Natural Earth 河名关键字：最粗 / 次粗
  relief        地形晕染强度（默认 1；范围小、地形碎的地方可以调低）
  relief_raster 是否读取全球晕渲图（默认 True；自备虚构世界地形时可设 False）
  river_filter  可选 callable(name, p0, p1) -> None | 'thin' | 'skip'，用于改写个别河段（例：今黄河下游画细）
数据文件放 data_dir（可以用 python -m engine.mapwar.setup_data 下载，见 README.md）。
"""
import os, json, math
from pathlib import Path
import numpy as np, cairo, cv2
from PIL import Image
from .util import fbm, sm, hsh, surf_rgba, ease, cl

PAPER = (0.88, 0.80, 0.63)
DEFAULT_DATA_DIR = Path(__file__).with_name('data')


class World:
    def __init__(self, cfg, data_dir=DEFAULT_DATA_DIR):
        self.cfg = cfg; self.dd = data_dir
        self.LON0, self.LON1, self.LAT1, self.LAT0 = cfg['bbox']          # LAT0 = 北缘（纹理顶部）
        self.K = float(cfg.get('px_per_deg', 116)); self.KX = math.cos(math.radians((self.LAT0 + self.LAT1) / 2))
        self.TW, self.TH = int((self.LON1 - self.LON0) * self.KX * self.K), int((self.LAT0 - self.LAT1) * self.K)
        self.sides = cfg['sides']; self.NO = len(self.sides); self.cities = list(cfg['cities']); self.flips = cfg.get('flips', {})
        self.reach = cfg.get('reach', (1.55, 2.6)); self.ds = self.reach[1] / 2.6            # 尺度系数：所有"度"相关的效果按它缩放
        self.TAUF = 0.55
        print('[world] building static rasters %dx%d ...' % (self.TW, self.TH), flush=True)
        self.LAND = self._land(); self.HILL, self.ELEV = self._relief()
        self.SEA_D = cv2.distanceTransform((self.LAND < 0.5).astype(np.uint8), cv2.DIST_L2, 5)
        self.BASE = self._base_ink()                 # 宣纸底图 RGB + 颗粒通道
        self._tiles()
        self.q = 4; self.oh, self.ow = self.TH // self.q, self.TW // self.q
        yq, xq = np.mgrid[0:self.oh, 0:self.ow].astype(np.float32)
        self.lonq = self.LON0 + xq * self.q / (self.KX * self.K); self.latq = self.LAT0 - yq * self.q / self.K
        self.DIST = np.stack([np.hypot((self.lonq - lo) * self.KX, self.latq - la) for _, lo, la, _, _ in self.cities]).astype(np.float32)
        nz = ((fbm(self.oh, self.ow, 60, 4, 3) - 0.5) * 1.5 + (fbm(self.oh, self.ow, 14, 3, 4) - 0.5) * 0.35) * self.ds
        self.NZ = np.stack([np.roll(nz, 37 * o, 1) * (1.0 if o == 0 else 0.9) for o in range(self.NO)])
        self.LANDQ = cv2.resize(self.LAND, (self.ow, self.oh), interpolation=cv2.INTER_AREA)

    # ---------------------------------------------------------------- projection
    def P(self, lon, lat): return ((lon - self.LON0) * self.KX * self.K, (self.LAT0 - lat) * self.K)

    def _in(self, pts, pad=2):
        return any(self.LON0 - pad < p[0] < self.LON1 + pad and self.LAT1 - pad < p[1] < self.LAT0 + pad for p in pts[::4] + pts[-1:])

    def _load(self, name):
        with (Path(self.dd) / name).open(encoding='utf-8') as src:
            return json.load(src)['features']

    # ---------------------------------------------------------------- static rasters
    def _land(self):
        s = cairo.ImageSurface(cairo.FORMAT_A8, self.TW, self.TH); c = cairo.Context(s)
        for f in self._load('ne_50m_land.geojson'):
            g = f['geometry']; polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
            for poly in polys:
                if not self._in(poly[0], 8): continue
                for ring in poly:
                    c.move_to(*self.P(*ring[0][:2]))
                    for p in ring[1:]: c.line_to(*self.P(*p[:2]))
                    c.close_path()
                c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); c.fill()
        return np.ndarray((self.TH, s.get_stride()), np.uint8, s.get_data())[:, :self.TW].astype(np.float32) / 255

    def _relief(self):
        if not self.cfg.get('relief_raster', True):
            return np.zeros((self.TH, self.TW), np.float32), np.zeros((self.TH, self.TW), np.float32)
        with Image.open(os.path.join(self.dd, 'shadedrelief.jpg')) as im:
            W, Hh = im.size
            box = (int((self.LON0 + 180) / 360 * W), int((90 - self.LAT0) / 180 * Hh), int((self.LON1 + 180) / 360 * W), int((90 - self.LAT1) / 180 * Hh))
            a = np.asarray(im.crop(box).convert('RGB')).astype(np.float32) / 255
        a = cv2.resize(a, (self.TW, self.TH), interpolation=cv2.INTER_CUBIC)
        k = max(1.0, self.K / 116)                                                     # 纹理比底图数据细时，模糊半径跟着放大，免得晕渲成块
        lum = cv2.GaussianBlur(a.mean(-1), (0, 0), 2.2 * k * k); hill = lum - cv2.GaussianBlur(lum, (0, 0), 18 * k)
        hill *= float(self.cfg.get('relief', 1.0))
        elev = cv2.GaussianBlur(np.clip((a[..., 0] - a[..., 1]) * 9 + 0.25, 0, 1), (0, 0), 6 * k)     # 棕/白=高，绿=平原
        return hill, elev

    def _rivers(self, style):
        """-> (rgb 预乘, alpha)。ink: 墨蓝；night/gold: 金线。"""
        cfg = self.cfg; s = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.TW, self.TH); c = cairo.Context(s)
        c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND)
        RIV = (0.16, 0.30, 0.40) if style == 'ink' else (0.93, 0.74, 0.36)
        main = tuple(cfg.get('main_rivers', ())); major = tuple(cfg.get('major_rivers', ())); filt = cfg.get('river_filter')
        w = max(0.45, min(1.0, self.K / 116))
        for f in self._load('ne_10m_rivers_lake_centerlines.geojson'):
            pr = f['properties']; nm = (pr.get('name') or '') + ' ' + (pr.get('name_en') or ''); g = f['geometry']
            if not g: continue
            rank = pr.get('scalerank', 9) or 9
            for l in ([g['coordinates']] if g['type'] == 'LineString' else g['coordinates']):
                if not self._in(l): continue
                for i in range(len(l) - 1):
                    p0, p1 = l[i], l[i + 1]; mode = filt(nm, p0, p1) if filt else None
                    if mode == 'skip': continue
                    if mode == 'thin': wd, al = 2.4, 0.6
                    elif any(k in nm for k in main): wd, al = 6.5, 0.95
                    elif any(k in nm for k in major): wd, al = 3.2, 0.8
                    elif not main and rank <= 4: wd, al = 3.6, 0.85        # 没给关键字时按 Natural Earth 等级
                    else: wd, al = 1.4, 0.45
                    c.set_source_rgba(*RIV, al); c.set_line_width(wd * w); c.move_to(*self.P(*p0[:2])); c.line_to(*self.P(*p1[:2])); c.stroke()
        for f in self._load('ne_10m_lakes.geojson'):
            l = f['geometry']; rings = l['coordinates'] if l['type'] == 'Polygon' else [r for p in l['coordinates'] for r in p]
            for r in rings:
                if not self._in(r, 0): continue
                c.move_to(*self.P(*r[0][:2]))
                for p in r[1:]: c.line_to(*self.P(*p[:2]))
                c.close_path(); c.set_source_rgba(*RIV, 0.75); c.fill()
        for er in cfg.get('extra_rivers', ()):
            pts = [self.P(*p) for p in er['pts']]
            col = er.get('ink') if style == 'ink' else er.get('gold'); c.set_source_rgba(*(col or RIV), 0.95); c.set_line_width(er.get('width', 6.5) * w)
            if er.get('dash'): c.set_dash([14, 9])
            c.move_to(*pts[0])
            for i in range(1, len(pts)):
                a, b = pts[i - 1], pts[i]; m = ((a[0] + b[0]) / 2 + (hsh(i) - 0.5) * 18, (a[1] + b[1]) / 2 + (hsh(i, 2) - 0.5) * 18)
                if er.get('dash'): c.line_to(*b)
                else: c.curve_to(*m, *m, *b)
            c.stroke(); c.set_dash([])
        return surf_rgba(s)

    def _base_ink(self):
        TH, TW = self.TH, self.TW; r = np.random.default_rng(7)
        paper = np.empty((TH, TW, 3), np.float32); paper[:] = PAPER
        paper *= (0.90 + 0.20 * fbm(TH, TW, 260, 5, 1) + 0.06 * (fbm(TH, TW, 7, 2, 2) - 0.5))[..., None]
        ks = min(1.0, self.K / 116)                                                                              # 纹理越粗，纸纹/海岸线越要收着
        fib = cv2.GaussianBlur(r.random((TH, TW)).astype(np.float32), (0, 0), sigmaX=9 * ks, sigmaY=0.6)         # 纸纤维
        paper *= (1 + 1.4 * ks * (fib - 0.5))[..., None].clip(0.9, 1.1)
        out = paper * (1 - (1 - self.LAND)[..., None] * (1 - np.float32([0.66, 0.76, 0.74])))                     # 海：青灰淡彩
        kr = max(0.35, ks)
        for d0, a in ((7, 0.5), (17, 0.33), (30, 0.2), (46, 0.1)):                                              # 海岸水波线（古地图画法）
            out *= (1 - (np.exp(-((self.SEA_D - d0 * kr) / (1.6 * max(0.7, kr))) ** 2) * a)[..., None] * np.float32([0.6, 0.45, 0.4]))
        shade = np.clip(-self.HILL * 9, 0, 1) * self.LAND; gran = 0.75 + 0.5 * fbm(TH, TW, 5, 2, 9)
        out *= (1 - (0.34 * shade * (0.25 + 0.9 * self.ELEV) * gran)[..., None] * np.float32([1.0, 0.96, 0.9]))   # 地形：墨色晕染
        out *= (1 - (self.ELEV * self.LAND * 0.16)[..., None] * np.float32([0.9, 0.8, 0.6]))
        vr, va = self._rivers('ink'); dry = (0.72 + 0.5 * fbm(TH, TW, 4, 2, 31))[..., None].clip(0, 1)            # 枯笔
        out = out * (1 - va * dry) + vr * dry
        return np.dstack([out, fbm(TH, TW, 22, 4, 20)]).astype(np.float32)

    def _tiles(self):
        """格子几何（只用于"易手瞬间金色格子一闪"的特效）。"""
        cell = max(14.0, self.cfg.get('cell_deg', 0.30 * self.ds) * self.K); cw, ch, g_, hgt = cell * self.KX, cell, 1.6, min(8.0, cell * 0.25)
        yy, xx = np.mgrid[0:self.TH, 0:self.TW].astype(np.float32)
        ci = np.floor(xx / cw).astype(np.int32); cj = np.floor(yy / ch).astype(np.int32); u = xx - ci * cw; v = yy - cj * ch
        top = (u > g_) & (u < cw - g_) & (v > g_) & (v < ch - g_ - hgt); edge = top & ((u < g_ + 1.6) | (v < g_ + 1.6))
        nx = int(self.TW / cw) + 1; ny = int(self.TH / ch) + 1
        cx = np.minimum(self.TW - 1, ((np.arange(nx) + 0.5) * cw)).astype(int); cy = np.minimum(self.TH - 1, ((np.arange(ny) + 0.5) * ch)).astype(int)
        cland = self.LAND[np.ix_(cy, cx)] > 0.5; lm = cland[np.minimum(cj, ny - 1), np.minimum(ci, nx - 1)]
        self.GEO = np.dstack([top & lm, edge & lm]).astype(np.float32); self.CID = (cj * nx + ci).astype(np.float32)
        self.CELLS = (nx, ny, cx, cy, cland, (0.62 + 0.5 * np.random.default_rng(5).random((ny, nx))).astype(np.float32))

    # ---------------------------------------------------------------- ownership
    def city_state(self, i, t):
        """-> (上一任归属, 当前归属, 易手进度 0..1, 易手时刻)"""
        o = self.cities[i][3]; prev = o; tf = -99
        for (ft, no) in self.flips.get(self.cities[i][0], []):
            if t >= ft: prev = o; o = no; tf = ft
        return prev, o, cl((t - tf) / self.TAUF), tf

    def ownership(self, t):
        """-> own(低清归属图), stg(控制强度), M(各势力软掩膜 oh x ow x NO), heat(易手波纹), share(各势力占地比例)"""
        NO = self.NO; sw = 3.2 * self.ds
        Dm = np.full((NO, self.oh, self.ow), 99 * self.ds, np.float32); heat = np.zeros((self.oh, self.ow), np.float32)
        for i in range(len(self.cities)):
            prev, o, k, tf = self.city_state(i, t)
            if k >= 1: np.minimum(Dm[o], self.DIST[i], out=Dm[o])
            else:
                kk = ease(k); np.minimum(Dm[o], self.DIST[i] + (1 - kk) * sw, out=Dm[o]); np.minimum(Dm[prev], self.DIST[i] + kk * sw, out=Dm[prev])
            w = (t - tf) / 0.85
            if 0 < w < 1.25: heat += np.exp(-((self.DIST[i] - w * 2.3 * self.ds) / (0.33 * self.ds)) ** 2) * (1 - w / 1.25) * (self.DIST[i] < 2.6 * self.ds)
        Dm += self.NZ
        own = Dm.argmin(0); stg = (1 - sm(self.reach[0], self.reach[1], Dm.min(0))) * self.LANDQ
        M = np.stack([cv2.GaussianBlur(((own == o) * stg).astype(np.float32), (0, 0), 1.2) for o in range(NO)], -1)
        share = M.reshape(-1, NO).sum(0); share = share / max(float(share.sum()), 1e-6)
        return own, stg, M, np.clip(heat, 0, 1.5) * self.LANDQ, share
