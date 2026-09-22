from faster_whisper import WhisperModel
import numpy as np,json
from pathlib import Path
x=np.load('/private/tmp/order-list-v006-after.npy');m=WhisperModel('/Users/kim.kkun/Projects/sandbox/mcp-cut/whisper-small',device='cpu',compute_type='int8',cpu_threads=6);segs,info=m.transcribe(x,language='ko',beam_size=5,word_timestamps=True,vad_filter=False,initial_prompt='김꾼, 더크루, 사장님, 소스 두 통, 발주, 주문표')
a=[]
for s in segs:
 d={'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word} for w in s.words]};a.append(d);print(f'{s.start:.2f}-{s.end:.2f} {s.text}',flush=True)
Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집/v006-cut-asr.json').write_text(json.dumps(a,ensure_ascii=False,indent=2))
