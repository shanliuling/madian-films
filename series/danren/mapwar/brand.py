"""署名：画面内印章 + 片尾页（+ 可选的右上角标），顺便把成片压到适合上传的体积。渲染完成后对成片跑一遍：
  python -m mapwar.brand 成片.mp4 输出.mp4 [账号名=码点小人] [片尾第二行=原创作品]
  可选：--corner 加右上角「@账号名」角标（默认不加，用户要求时才加）；--logo 图片 在左上角加 logo（商单）。
  印章：右下角一枚较淡的红印，长在画面里不好裁；角标：右上角半透明「@账号名」（底部和右侧会被平台界面挡住）；
  片尾页：最后 tail 秒压暗（dim 越大越暗），浮现 印章 + 账号名 + 第二行。叠在原有最后一个镜头上，不加片长；
  最后一个镜头上有大字或气泡时，时间线结尾多留 tail 秒并把 dim 调到 230 左右，免得和署名叠在一起。
"""
import os, sys, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .util import font


def seal(text='码点小人', sz=150, col=(190, 30, 25), seed=3):
    """红底镂空字的方印，边缘做旧。4 个字排成 2×2（右起竖读），其他字数排成一列。"""
    im = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, sz - 4, sz - 4), sz // 15, fill=col + (235,))
    if len(text) == 4: f = font(int(sz * 0.36)); pos = [(.70, .30), (.70, .70), (.30, .30), (.30, .70)]
    else: n = len(text); f = font(int(sz * 0.8 / max(n, 2))); pos = [(.5, (i + .5) / n * .84 + .08) for i in range(n)]
    for ch, (x, y) in zip(text, pos): d.text((x * sz, y * sz), ch, font=f, anchor='mm', fill=(0, 0, 0, 0))
    d.rounded_rectangle((sz * .08, sz * .08, sz * .92, sz * .92), sz // 25, outline=(0, 0, 0, 0), width=max(2, sz // 50))
    a = np.array(im); m = np.random.default_rng(seed).random(a.shape[:2]) < 0.06; a[m, 3] = (a[m, 3] * 0.3).astype(np.uint8)
    return Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.6))


def _stamp(img, x, y, text, sz, a=1.0):
    s = seal(text, sz); s.putalpha(s.getchannel('A').point(lambda v: int(v * a))); img.alpha_composite(s, (int(x), int(y)))


def _corner(d, W, name):
    d.text((W - 48, 40), '@' + name, font=font(40), anchor='ra', fill=(255, 255, 255, 150), stroke_width=3, stroke_fill=(0, 0, 0, 90))


def logo_rgba(path):
    """读入 logo；白底图会按「白底反混合」抠成透明底（保留渐变和软边）。"""
    im = Image.open(path).convert('RGBA'); a = np.asarray(im).astype(np.float32)
    if a[..., 3].min() < 250: return im
    rgb = a[..., :3]; al = (255 - rgb.min(-1)) / 255; al = np.where(al < 0.04, 0, al)
    col = (rgb - 255 * (1 - al[..., None])) / np.maximum(al[..., None], 1e-3)
    return Image.fromarray(np.dstack([col.clip(0, 255), al * 255]).astype(np.uint8))


def watermark(name='码点小人', size=(1920, 1080), seal_a=0.6, corner=False, logo=None, logo_h=96, logo_a=0.95):
    """全片叠加层（透明底）：右下淡印章；corner=True 时加右上角标；logo=图片路径时左上角加 logo（商单用）。"""
    W, H = size; a = Image.new('RGBA', size, (0, 0, 0, 0))
    if corner: _corner(ImageDraw.Draw(a), W, name)
    _stamp(a, W - 165, H - 165, name, 110, seal_a)
    if logo:
        L = logo_rgba(logo); L = L.resize((int(L.width * logo_h / L.height), logo_h), Image.LANCZOS); L.putalpha(L.getchannel('A').point(lambda v: int(v * logo_a)))
        a.alpha_composite(L, (36, 30))
    return a


def endcard(name='码点小人', line2='原创作品', size=(1920, 1080), dim=170, corner=False):
    """片尾页叠加层：压暗 + 印章 + 账号名 + 第二行。"""
    W, H = size; e = Image.new('RGBA', size, (0, 0, 0, dim)); d = ImageDraw.Draw(e)
    _stamp(e, W // 2 - 120, 290, name, 240)
    d.text((W // 2, 650), name, font=font(120), anchor='mm', fill=(255, 240, 215), stroke_width=7, stroke_fill=(40, 20, 10))
    if line2: d.text((W // 2, 770), line2, font=font(52), anchor='mm', fill=(235, 220, 195), stroke_width=4, stroke_fill=(40, 20, 10))
    if corner: _corner(d, W, name)
    return e


def apply(src, dst, name='码点小人', line2='原创作品', tail=1.7, crf=24, corner=False, logo=None, dim=170):
    """给成片加印章、片尾页（corner=True 时再加右上角标）并重新编码（crf 24 时 1080p 约 6 Mbps；平台上传后还会再压一遍）。"""
    pr = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.split()
    W, H = map(int, pr[0].split(',')[:2]); dur = float(pr[1]); t0 = dur - tail
    with tempfile.TemporaryDirectory() as tmp:
        wm, ec = os.path.join(tmp, 'wm.png'), os.path.join(tmp, 'end.png')
        base = (1920, 1080)
        watermark(name, base, corner=corner, logo=logo).resize((W, H), Image.LANCZOS).save(wm); endcard(name, line2, base, dim=dim, corner=corner).resize((W, H), Image.LANCZOS).save(ec)
        fc = (f"[0:v][1:v]overlay=0:0:enable='lt(t,{t0 + 0.05:.3f})'[a];[2:v]format=rgba,fade=in:st=0:d=0.35:alpha=1,setpts=PTS+{t0:.3f}/TB[e];"
              f"[a][e]overlay=0:0:eof_action=repeat[v]")
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-i', wm, '-loop', '1', '-t', f'{tail:.3f}', '-i', ec, '-filter_complex', fc, '-map', '[v]', '-map', '0:a?',
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', dst], check=True)
    return dst


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('name', nargs='?', default='码点小人'); ap.add_argument('line2', nargs='?', default='原创作品')
    ap.add_argument('--corner', action='store_true', help='加右上角 @账号名（默认不加）'); ap.add_argument('--no-corner', action='store_true', help='旧参数，现在默认就不加'); ap.add_argument('--dim', type=int, default=170, help='片尾页压暗程度 0–255'); ap.add_argument('--logo', help='左上角 logo 图片（白底会自动抠图）')
    A = ap.parse_args(); apply(A.src, A.dst, A.name, A.line2, corner=A.corner and not A.no_corner, logo=A.logo, dim=A.dim)
