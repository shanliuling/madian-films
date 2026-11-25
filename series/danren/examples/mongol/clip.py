"""只渲染一段：python clip.py t0 t1 out.mp4 [scale] [procs]。帧号与整片对齐（f/30）。"""
import sys, os, math, subprocess
from multiprocessing import Pool
from PIL import Image
import film as FM

FPS = 30
_f = None


def _one(a):
    global _f
    f, scale, d = a
    if _f is None: _f = FM.make_film()
    img = _f.render(f / FPS)
    if scale != 1.0: img = img.resize((int(img.width * scale) // 2 * 2, int(img.height * scale) // 2 * 2), Image.LANCZOS)
    img.save(os.path.join(d, 'f%06d.png' % f), compress_level=1); return f


if __name__ == '__main__':
    t0, t1, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]; scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0; procs = int(sys.argv[5]) if len(sys.argv) > 5 else 7
    fa, fb = math.ceil(t0 * FPS - 1e-6), math.ceil(t1 * FPS - 1e-6); d = out + '.frames'; os.makedirs(d, exist_ok=True)
    with Pool(procs) as p:
        for k, f in enumerate(p.imap_unordered(_one, [(f, scale, d) for f in range(fa, fb)])):
            if k % 30 == 0: print(k, '/', fb - fa, flush=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-start_number', str(fa), '-i', os.path.join(d, 'f%06d.png'), '-frames:v', str(fb - fa),
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', out], check=True)
    print('done', out, fa, fb, fb - fa)
