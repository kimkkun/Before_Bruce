from pathlib import Path
import av,json,numpy as np,hashlib
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from faster_whisper.vad import get_speech_timestamps,VadOptions
O=Path(__file__).parent; R=O.parent/'01_원본'
p=next(R.glob('copy_*.MOV'))
manifest=[]
for f in R.iterdir():
 if f.is_file():manifest.append({'file':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(O/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
for f in sorted(R.glob('*.MP4'))+[p]:
 c=av.open(str(f)); s=c.streams.video[0]; duration=c.duration/1e6
 times=[2,10,20,30,45,60,72] if duration>70 and f!=p else ([2,8,15,23,29] if f!=p else [2,40,100,180])
 for i,t in enumerate(times):
  if t>=duration:continue
  c.seek(int(t/s.time_base),stream=s)
  frame=next(fr for fr in c.decode(s) if fr.time>=t)
  frame=frame.reformat(width=330,height=round(frame.height*330/frame.width),format='rgb24')
  out=av.open(str(O/(f.stem+f'-{t}s.png')),'w'); st=out.add_stream('png',rate=1);st.width=frame.width;st.height=frame.height;st.pix_fmt='rgb24'
  for packet in st.encode(frame):out.mux(packet)
  for packet in st.encode():out.mux(packet)
  out.close()
 c.close()
x=decode_audio(str(p),sampling_rate=16000);np.save(O/'source-audio.npy',x)
v=get_speech_timestamps(x,VadOptions(threshold=.5,min_speech_duration_ms=50,min_silence_duration_ms=50,speech_pad_ms=15))
(O/'speech-regions.json').write_text(json.dumps(v))
print('Frames and speech regions ready',flush=True)
m=WhisperModel('/Users/kim.kkun/Projects/sandbox/mcp-cut/whisper-small',device='cpu',compute_type='int8',cpu_threads=6)
segs,info=m.transcribe(x,language='ko',beam_size=5,word_timestamps=True,vad_filter=True,initial_prompt='김꾼입니다. 더크루. 직원들 망가지는 세 가지. 계속 바뀌는 기준, 업무 강도, 체크리스트 배정.')
a=[]
for s in segs:
 d={'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word} for w in s.words]};a.append(d);print(f'{s.start:.2f}-{s.end:.2f} {s.text}',flush=True)
 (O/'source-asr.json').write_text(json.dumps(a,ensure_ascii=False,indent=2))
print('DONE',flush=True)
