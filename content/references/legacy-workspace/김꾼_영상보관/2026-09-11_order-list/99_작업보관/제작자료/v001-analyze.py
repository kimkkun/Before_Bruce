import json,hashlib,time
from pathlib import Path
import av,numpy as np
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from faster_whisper.vad import get_speech_timestamps,VadOptions
base=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list')
src=next((base/'01_원본').glob('*.MOV'));out=base/'02_AI편집'
a=decode_audio(str(src),sampling_rate=16000);np.save('/private/tmp/order-list-audio.npy',a)
regions=get_speech_timestamps(a,VadOptions(threshold=.4,min_speech_duration_ms=100,min_silence_duration_ms=300,speech_pad_ms=100))
(out/'v001-speech-regions.json').write_text(json.dumps([{'start':r['start']/16000,'end':r['end']/16000} for r in regions],indent=2))
model=WhisperModel('/Users/kim.kkun/Projects/sandbox/mcp-cut/whisper-small',device='cpu',compute_type='int8',cpu_threads=8)
segments,info=model.transcribe(a,language='ko',beam_size=5,word_timestamps=True,vad_filter=True,condition_on_previous_text=False,initial_prompt='김꾼, 더크루, 발주, 주문표, 소스 두 통, 카톡')
rows=[]
for s in segments:
 rows.append({'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word,'probability':w.probability} for w in s.words]})
 print(f'{s.start:.2f}–{s.end:.2f} {s.text}',flush=True)
(out/'v001-source-asr.json').write_text(json.dumps({'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'duration':info.duration,'segments':rows},ensure_ascii=False,indent=2))
print('DONE',flush=True)
