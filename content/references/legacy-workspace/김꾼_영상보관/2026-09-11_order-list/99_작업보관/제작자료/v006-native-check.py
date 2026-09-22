from pathlib import Path
import json,numpy as np
from faster_whisper.audio import decode_audio
O=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집')
x=decode_audio('/Users/kim.kkun/Movies/CapCut/0911.mov',sampling_rate=16000);np.save('/private/tmp/order-list-v006-native.npy',x)
y=np.load('/private/tmp/order-list-v006-before.npy');raw=np.load('/private/tmp/order-list-v006-source.npy');d=json.loads((O/'v006-analysis-base.json').read_text());y2=np.zeros(len(y),dtype=np.float32)
for s in d['tracks'][0]['segments']:
 lo=round(s['source_timerange']['start']/1e6*16000);dst=round(s['target_timerange']['start']/1e6*16000);n=min(round(s['target_timerange']['duration']/1e6*16000),len(y2)-dst);y2[dst:dst+n]=raw[lo:lo+n]
for name,b in [('honor_audio_pts',y),('normalized_audio',y2)]:
 n=min(len(x),len(b));a=x[:n];b=b[:n];corr=float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)));print(name,corr,'length',n/16000,flush=True)
np.save('/private/tmp/order-list-v006-normalized.npy',y2)
