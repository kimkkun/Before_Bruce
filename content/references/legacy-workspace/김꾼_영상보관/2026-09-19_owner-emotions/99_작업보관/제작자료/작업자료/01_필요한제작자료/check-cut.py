from pathlib import Path
import numpy as np,json
from faster_whisper import WhisperModel
O=Path(__file__).parent
m=WhisperModel('/Users/kim.kkun/Projects/sandbox/mcp-cut/whisper-small',device='cpu',compute_type='int8',cpu_threads=6)
s,_=m.transcribe(np.load(O/'cut-audio-preview.npy'),language='ko',beam_size=5,word_timestamps=True,initial_prompt='김꾼입니다. 더크루. 체크리스트. 코멘트. 크루들.',vad_filter=False)
r=[]
for a in s:
 r.append({'start':a.start,'end':a.end,'text':a.text});print(f'{a.start:.2f}-{a.end:.2f} {a.text}',flush=True)
(O/'cut-preview-asr.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
