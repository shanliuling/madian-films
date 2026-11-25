"""mapwar.voice — 配音：旁白 + 蛋蛋人萌音。觉得这部片配音会更好时先问用户，用户同意加才用；不同意就只做字幕。

做法：edge-tts 调微软 Edge 的在线神经语音逐句生成（免费、不用 Key、要联网；不是本地模型）→ ffmpeg 在本地裁掉头尾静音、
把角色台词变成萌音 → 按每句的实际时长排出时间线，画面的字幕、气泡和混音都读这条时间线。

    pip install edge-tts
    VOICES = {'N': voice.NARRATOR,                                       # 旁白：低沉男声，不变声
              '小兵': voice.cute('zh-CN-XiaoyiNeural', 1.24, '+10%', '+15Hz')}   # 萌音：k 越大越尖
    LINES = [('i0', 'N', 3.8, '十三世纪，有四个人，不小心惹了蒙古。', '13 世纪  有四个人不小心惹了蒙古'),
             ('a2', '小兵', None, '老板，咱家没啦！', '老板，咱家没啦！'),      # None：紧跟上一句（隔 0.10 秒）
             ('a3', 'N', '+0.5', '两年，亡国。', '两年  亡国')]                  # '+0.5'：上一句说完再停 0.5 秒
    tl = voice.build(LINES, VOICES, 'vo')        # → vo/<id>.wav、vo/timeline.json；tl = [{id, who, t, d, text, sub}]
    mix = Mix(bgm, total); voice.lay(mix, tl, 'vo'); mix.add(boom(), 14.87); mix.save('mix.wav')   # 先铺人声再加音效
    L = voice.at(tl, t)                          # 画面里：此刻正在说的那一句（没有则 None），用 L['sub'] 画字幕

每句的第三项是开始时间：数字 = 最早从这一秒开始（卡拍子用；上一句没说完会顺延，build 会打印 LATE）；
'+秒数' = 接在上一句后面隔多久；None = 隔 0.10 秒。改了台词或音色只会重新生成改过的那几句。
试听一句：python -m mapwar.voice "老板，咱家没啦！" out.wav [音色] [变声倍率 k]；全部中文音色：edge-tts --list-voices | grep zh-CN
"""
import os, sys, json, time, asyncio, hashlib, subprocess
import numpy as np
from . import audio

SR = audio.SR
# (音色, 语速, 音调, 变声倍率 k)。k=1 不变声；k>1 整体升调并把共振峰上移（1.16 略尖，1.20–1.28 是蛋蛋人萌音）
NARRATOR = ('zh-CN-YunjianNeural', '+6%', '-4Hz', 1.0)
_TRIM = 'silenceremove=start_periods=1:start_threshold=-42dB,areverse,silenceremove=start_periods=1:start_threshold=-42dB,areverse'


def cute(voice='zh-CN-XiaoyiNeural', k=1.22, rate='+10%', pitch='+10Hz'):
    """萌音角色。常用底音：女声 XiaoyiNeural（小兵、使者）、少年 YunxiaNeural（怂包、贪财）、
    青年 YunxiNeural（主角、王公）、播音腔 YunyangNeural（宣旨、摆架子）、浑厚 YunjianNeural（大汗这类反差角色）。"""
    return (voice, rate, pitch, k)


def _tts(text, voice, rate, pitch, mp3, tries=4):
    import edge_tts
    for i in range(tries):
        try: asyncio.run(edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch).save(mp3)); return
        except Exception:
            if i == tries - 1: raise
            time.sleep(1.5)


def _dur(path): return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]))


def say(text, wav, spec=NARRATOR, comp=1.06):
    """生成一句 → wav（单声道 48k，头尾静音已裁掉），返回时长。comp：变声后语速比原速快多少（萌音略快一点更有喜感）。"""
    voice, rate, pitch, k = spec; mp3 = wav[:-4] + '.mp3'
    _tts(text, voice, rate, pitch, mp3); af = _TRIM
    if k != 1.0:
        sr0 = int(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=sample_rate', '-of', 'csv=p=0', mp3]))
        af = f'asetrate={sr0 * k:.0f},aresample={SR},atempo={comp / k:.4f},' + _TRIM
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', mp3, '-af', af, '-ar', str(SR), '-ac', '1', wav], check=True); os.remove(mp3)
    return _dur(wav)


def build(lines, voices, out_dir='vo', gap=0.10, log=True):
    """逐句生成并排时间线。lines: [(id, 角色, 开始, 台词, 字幕)]，写法见模块开头。返回并写入 out_dir/timeline.json。"""
    os.makedirs(out_dir, exist_ok=True); tl, end = [], 0.0
    for lid, who, at, text, sub in lines:
        wav = os.path.join(out_dir, lid + '.wav'); tag = wav + '.key'
        key = hashlib.md5(repr((text, tuple(voices[who]))).encode()).hexdigest()
        if not (os.path.exists(wav) and os.path.exists(tag) and open(tag).read() == key):
            say(text, wav, voices[who]); open(tag, 'w').write(key)
        d = _dur(wav); late = 0.0
        if at is None: t = end + gap
        elif isinstance(at, str): t = end + float(at)
        else: t = max(float(at), end + 0.04) if tl else float(at); late = t - float(at)
        tl.append(dict(id=lid, who=who, t=round(t, 3), d=round(d, 3), text=text, sub=sub)); end = t + d
        if log: print(f'{lid:>4s} {who:<6s} {t:6.2f}–{end:6.2f} ({d:4.2f}s){"  LATE %.2f" % late if late > 0.05 else ""} | {text}')
    json.dump(tl, open(os.path.join(out_dir, 'timeline.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return tl


def load(out_dir='vo'): return json.load(open(os.path.join(out_dir, 'timeline.json'), encoding='utf-8'))


def at(tl, t, hold=0.0):
    """t 时刻正在说的那一句（说完后再留 hold 秒），没有返回 None。"""
    for L in tl:
        if L['t'] - 0.03 <= t <= L['t'] + L['d'] + hold: return L
    return None


def lay(mix, tl, out_dir='vo', duck=0.45, gain=0.80, keep=(), pre=0.10, post=0.15, smooth=0.10):
    """把人声铺进 audio.Mix：说话的地方把 BGM 压到 duck 倍（前后各让出一点、边缘平滑），再叠上人声（峰值归一到 gain）。
    要在加音效之前调用，否则音效也会被压低。keep=[(t0, t1)] 是不压低的时段（比如开头有歌词的那几秒）。"""
    sr = mix.sr; n = len(mix.y); env = np.ones(n, np.float32)
    for L in tl: env[max(0, int((L['t'] - pre) * sr)):min(n, int((L['t'] + L['d'] + post) * sr))] = duck
    k = max(1, int(smooth * sr)); env = np.convolve(np.pad(env, k, mode='edge'), np.ones(k, np.float32) / k, 'same')[k:-k]
    for a, b in keep: env[max(0, int(a * sr)):min(n, int(b * sr))] = 1.0
    mix.y *= env[:, None]
    for L in tl:
        w = audio.load(os.path.join(out_dir, L['id'] + '.wav'), sr)[:, 0]; mix.add(w / (np.abs(w).max() + 1e-9) * gain, L['t'])
    return mix


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(1)
    spec = (a[2] if len(a) > 2 else NARRATOR[0], '+6%' if len(a) < 4 else '+10%', '-4Hz' if len(a) < 4 else '+10Hz', float(a[3]) if len(a) > 3 else 1.0)
    print('%.2fs' % say(a[0], a[1], spec), a[1])
