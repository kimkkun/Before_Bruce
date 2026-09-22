from faster_whisper import WhisperModel
import numpy as np
m=WhisperModel('/Users/kim.kkun/Projects/sandbox/mcp-cut/whisper-small',device='cpu',compute_type='int8',cpu_threads=6)
y=np.load('/private/tmp/order-list-v006-after.npy')
for a,b in [(0,4.12),(44.6,48.6),(48,54.5),(79.8,81.23)]:
 segs,_=m.transcribe(y[round(a*16000):round(b*16000)],language='ko',beam_size=5,vad_filter=False,initial_prompt='직원은 말을 했고 사장은 들었습니다. 수량 제출하고 사장님이 확인하고 끝. 재고를 보면서 필요한 수량을 골라 제출하면 됩니다. 댓글에 남겨주세요.')
 print(a,b,' '.join(s.text for s in segs),flush=True)
