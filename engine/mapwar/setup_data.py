"""下载真实地形渲染用的数据；人物、阵战和虚构地图不依赖这些下载。"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZipFile

from .world import DEFAULT_DATA_DIR

NATURAL_EARTH = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson'
LAYERS = ('ne_50m_land', 'ne_10m_rivers_lake_centerlines', 'ne_10m_lakes')


def prepare(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=data_dir) as tmp:
        tmp = Path(tmp)
        for layer in LAYERS:
            name = f'{layer}.geojson'
            if not (data_dir / name).is_file():
                print(f'Downloading {name}', flush=True)
                with urlopen(f'{NATURAL_EARTH}/{name}', timeout=60) as src, (tmp / name).open('wb') as dst:
                    shutil.copyfileobj(src, dst)
                (tmp / name).replace(data_dir / name)
        name = 'shadedrelief.jpg'
        if not (data_dir / name).is_file():
            subprocess.run([
                sys.executable, '-m', 'pip', 'download', '--only-binary=:all:', '--no-deps',
                '--dest', str(tmp), 'basemap-data==2.0.0',
            ], check=True)
            with ZipFile(next(tmp.glob('basemap_data-*.whl'))) as wheel:
                image = next(path for path in wheel.namelist() if path.endswith(f'/{name}'))
                with wheel.open(image) as src, (tmp / name).open('wb') as dst:
                    shutil.copyfileobj(src, dst)
            (tmp / name).replace(data_dir / name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA_DIR)
    prepare(parser.parse_args().data_dir)
