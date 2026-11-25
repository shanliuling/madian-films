"""下载地图数据到 kit 的 data/ 目录（只需一次，约 60MB）。  python tools/setup_data.py
- Natural Earth（公有领域）：陆地、河流、湖泊
- 晕渲地形图 shadedrelief.jpg：来自 PyPI 的 basemap-data 包（其中的 Natural Earth 晕渲图）
如果网络不通，也可以手动把这四个文件放进 data/。"""
import os, sys, urllib.request, zipfile, glob, shutil, subprocess, tempfile

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'); os.makedirs(D, exist_ok=True)
NE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/'
for f in ('ne_50m_land.geojson', 'ne_10m_rivers_lake_centerlines.geojson', 'ne_10m_lakes.geojson'):
    p = os.path.join(D, f)
    if not os.path.exists(p): print('downloading', f); urllib.request.urlretrieve(NE + f, p)
p = os.path.join(D, 'shadedrelief.jpg')
if not os.path.exists(p):
    tmp = tempfile.mkdtemp(); print('downloading basemap-data (relief) ...')
    subprocess.run([sys.executable, '-m', 'pip', 'download', 'basemap-data', '--no-deps', '-d', tmp], check=True)
    whl = glob.glob(os.path.join(tmp, '*.whl'))[0]
    with zipfile.ZipFile(whl) as z:
        name = next(n for n in z.namelist() if n.endswith('shadedrelief.jpg'))
        with z.open(name) as src, open(p, 'wb') as dst: shutil.copyfileobj(src, dst)
print('data ready:', sorted(os.listdir(D)))
