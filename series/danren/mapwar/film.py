"""mapwar.film — 把一串镜头渲染成片。

    film = Film(shots, total, audio='mix.wav')         # shots = [(t0, t1, fn)]，fn(lt, dur, t) -> PIL.Image（1920x1080）
    film.cli()                                          # 在脚本末尾调用，然后：
        python scenario.py still out_dir 3.2 14.9 48.5   抽静帧（先看静帧再渲染）
        python scenario.py sheet out.jpg 12              全片均匀抽 12 帧拼成一张总览图
        python scenario.py render out.mp4 [procs] [scale]   并行渲染 + 拼接 + 混音；scale=0.5 出 540p 预览
        python scenario.py part i n out.mp4 [scale]      （内部用）渲染第 i/n 段
"""
import os, sys, subprocess, math
from PIL import Image
from .util import SW, SH, FPS


class Film:
    def __init__(self, shots, total=None, audio=None, fade_out=0.9):
        self.shots = sorted(shots, key=lambda s: s[0]); self.total = total or self.shots[-1][1]; self.audio = audio; self.fade = fade_out

    def render(self, t):
        shot = self.shots[-1]
        for s in self.shots:
            if s[0] <= t < s[1]: shot = s; break
        img = shot[2](t - shot[0], shot[1] - shot[0], t).convert('RGB')
        if self.fade and t > self.total - self.fade: img = Image.blend(img, Image.new('RGB', img.size, (0, 0, 0)), min(1, (t - (self.total - self.fade)) / (self.fade * 0.9)))
        return img

    def _part(self, i, n, out, scale=1.0):
        N = int(round(self.total * FPS)); a, b = N * i // n, N * (i + 1) // n; w, h = int(SW * scale) // 2 * 2, int(SH * scale) // 2 * 2
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for f in range(a, b):
            img = self.render(f / FPS)
            if scale != 1.0: img = img.resize((w, h), Image.LANCZOS)
            p.stdin.write(img.tobytes())
            if (f - a) % 60 == 0: print(f'[part {i}] {f - a}/{b - a}', flush=True)
        p.stdin.close(); p.wait()

    def cli(self, argv=None):
        argv = argv or sys.argv; cmd = argv[1] if len(argv) > 1 else 'info'; script = os.path.abspath(argv[0])
        if cmd == 'still':
            os.makedirs(argv[2], exist_ok=True)
            for ts in argv[3:]: self.render(float(ts)).save(os.path.join(argv[2], 't%07.2f.jpg' % float(ts)), quality=92); print('still', ts, flush=True)
        elif cmd == 'sheet':
            n = int(argv[3]) if len(argv) > 3 else 12; cols = 4; rows = math.ceil(n / cols); tw, th = 640, 360; sh = Image.new('RGB', (cols * tw, rows * th))
            for k in range(n): sh.paste(self.render(self.total * (k + 0.5) / n).resize((tw, th)), ((k % cols) * tw, (k // cols) * th))
            sh.save(argv[2], quality=90)
        elif cmd == 'part': self._part(int(argv[2]), int(argv[3]), argv[4], float(argv[5]) if len(argv) > 5 else 1.0)
        elif cmd == 'render':
            out = argv[2]; n = int(argv[3]) if len(argv) > 3 else 2; scale = argv[4] if len(argv) > 4 else '1'; d = out + '.parts'; os.makedirs(d, exist_ok=True)
            ps = [subprocess.Popen([sys.executable, script, 'part', str(i), str(n), os.path.join(d, f'p{i}.mp4'), scale]) for i in range(n)]
            if any(p.wait() for p in ps): raise SystemExit('有分段渲染失败（内存不够时进程会被杀，减少 procs 再试）')
            N = int(round(self.total * FPS)); got = 0
            for i in range(n):        # 核对帧数：被杀的分段不会报错，只会少帧
                r = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', os.path.join(d, f'p{i}.mp4')], capture_output=True, text=True)
                got += int(r.stdout.strip() or 0)
            if got != N: raise SystemExit(f'帧数不对：应为 {N}，实际 {got}')
            lst = os.path.join(d, 'list.txt'); open(lst, 'w').write(''.join(f"file 'p{i}.mp4'\n" for i in range(n)))
            cmdl = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst]
            if self.audio and os.path.exists(self.audio): cmdl += ['-i', self.audio, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest']
            else: cmdl += ['-c:v', 'copy']
            subprocess.run(cmdl + ['-movflags', '+faststart', out], check=True); print('done', out, f'{N} frames')
        else:
            print(f'total {self.total:.2f}s, {len(self.shots)} shots')
            for s in self.shots: print(f'  {s[0]:7.2f} - {s[1]:7.2f}  {getattr(s[2], "__name__", "shot")}')
