"""生成旁白与蛋蛋人萌音，并排出实际时间线 → vo/timeline.json"""
import os, json, asyncio, subprocess
import edge_tts
from script import LINES, VOICES, TOTAL

HERE = os.path.dirname(os.path.abspath(__file__))
VO = os.path.join(HERE, 'vo'); os.makedirs(VO, exist_ok=True)
TRIM = 'silenceremove=start_periods=1:start_threshold=-42dB,areverse,silenceremove=start_periods=1:start_threshold=-42dB,areverse'


async def gen(lid, who, text):
    voice, rate, pitch, k = VOICES[who]
    mp3, wav = os.path.join(VO, lid + '.mp3'), os.path.join(VO, lid + '.wav')
    for attempt in range(4):
        try:
            await edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch).save(mp3); break
        except Exception as e:
            if attempt == 3: raise
            await asyncio.sleep(1.5)
    af = TRIM
    if k != 1.0:   # 萌音：整体升调 + 共振峰上移，再把语速补回一部分
        af = f'asetrate=24000*{k},aresample=44100,atempo={1 / k * 1.06:.4f},' + TRIM
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp3, '-af', af, '-ar', '44100', '-ac', '1', wav], check=True)
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav])
    return float(out)


async def main():
    tl, t_prev_end = [], 0.0
    for lid, who, at, text, sub in LINES:
        d = await gen(lid, who, text)
        t = max(at, t_prev_end + 0.04) if at > 3 else t_prev_end + (at or 0.10)
        late = t - at if at > 3 else 0.0
        tl.append(dict(id=lid, who=who, t=round(t, 3), d=round(d, 3), text=text, sub=sub))
        print(f'{lid} {who:5s} {t:6.2f}–{t + d:6.2f} ({d:4.2f}s){"  LATE %.2f" % late if late > 0.05 else ""} | {text}')
        t_prev_end = t + d
    print('end %.2f / total %.2f' % (t_prev_end, TOTAL))
    json.dump(tl, open(os.path.join(VO, 'timeline.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


asyncio.run(main())
