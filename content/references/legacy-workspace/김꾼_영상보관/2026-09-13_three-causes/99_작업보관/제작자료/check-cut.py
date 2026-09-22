from pathlib import Path
from faster_whisper import WhisperModel
import json,numpy as np
O=Path(__file__).parent;m=WhisperModel('/Users/kim.kkun/Projects/sandbox/mcp-cut/whisper-small',device='cpu',compute_type='int8',cpu_threads=6)
ss,_=m.transcribe(np.load(O/'cut-audio.npy'),language='ko',word_timestamps=True,vad_filter=False,initial_prompt='김꾼입니다. 더크루. 직원들 망가지는 세 가지.')
rows=[]
for s in ss:
 rows.append({'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word} for w in s.words]});print(f'{s.start:.2f}-{s.end:.2f} {s.text}',flush=True)
 (O/'v001-cut-asr.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
