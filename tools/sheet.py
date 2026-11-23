"""sheet — 把一个视频每隔几秒抽一帧拼成一张联系表，用来快速看全片。只在用户要求自查时用。
python tools/sheet.py 视频.mp4 [间隔秒=2] [每行几格=8] → 视频同目录下的 _sheet.jpg"""
import subprocess, sys, os, json
v = sys.argv[1]; step = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 8
dur = float(json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', v], capture_output=True, text=True).stdout)['format']['duration'])
n = int(dur / step) + 1; rows = -(-n // cols); out = os.path.join(os.path.dirname(os.path.abspath(v)), '_sheet.jpg')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', v, '-vf', f'fps=1/{step},scale=320:180,tile={cols}x{rows}', '-frames:v', '1', out], check=True); print(out, f'{n} 格，每格 {step} 秒')
