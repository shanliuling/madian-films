"""每个脚本第一行 import _env：把引擎和系列目录加进 import 路径，工作目录切到本集目录（中间文件和成片都写在 out/）。"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); SERIES = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(SERIES))
sys.path[:0] = [HERE, os.path.join(ROOT, 'engine'), SERIES]; os.chdir(HERE); os.makedirs('out', exist_ok=True)
BGM = os.path.join(SERIES, 'audio', 'bgm.mp3')
BRUSH = os.path.join(SERIES, 'fonts', 'MaShanZheng-Regular.ttf')                        # 毛笔字（OFL 许可），招式名用
