from pathlib import Path
import json,av,numpy as np
from faster_whisper.audio import decode_audio
from faster_whisper.vad import get_speech_timestamps,VadOptions
O=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집');R=Path.home()/'Movies/CapCut/User Data/Projects/com.lveditor.draft/0911'
d=json.loads((R/'draft_info.json').read_text());(O/'v006-analysis-base.json').write_text(json.dumps(d,ensure_ascii=False))
vid=next(t for t in d['tracks'] if t['type']=='video');m={m['id']:m for m in d['materials']['videos']}
rawpath=m[vid['segments'][0]['material_id']]['path'];path=R/rawpath.split('_##/',1)[1] if rawpath.startswith('##_draftpath_') else Path(rawpath);c=av.open(str(path));offset=float(next(c.decode(c.streams.audio[0])).time);c.close()
a=decode_audio(str(path),sampling_rate=16000);np.save('/private/tmp/order-list-v006-source.npy',a)
# Construct analysis audio on the native timeline, honoring each original source offset.
y=np.zeros(round(d['duration']/1e6*16000),dtype=np.float32)
for s in vid['segments']:
 t=s['target_timerange'];r=s['source_timerange'];lo=round((r['start']/1e6-offset)*16000);n=round(t['duration']/1e6*16000);dst=round(t['start']/1e6*16000);p=a[lo:lo+n];n=min(len(p),len(y)-dst);y[dst:dst+n]=p[:n]
np.save('/private/tmp/order-list-v006-before.npy',y)
for threshold in [.2,.3,.4]:
 v=get_speech_timestamps(y,VadOptions(threshold=threshold,min_speech_duration_ms=50,min_silence_duration_ms=50,speech_pad_ms=0))
 intervals=[]
 for r in v:
  # Keep one video frame of phonetic protection total, then cut to frame boundaries.
  lo=max(0,int(np.floor((r['start']/16000-.015)*30)));hi=min(round(len(y)/16000*30),int(np.ceil((r['end']/16000+.015)*30)))
  if intervals and lo-intervals[-1][1]<=1:intervals[-1][1]=hi
  else:intervals.append([lo,hi])
 print(threshold,'regions',len(intervals),'duration',sum(b-a for a,b in intervals)/30,'removed',len(y)/16000-sum(b-a for a,b in intervals)/30)
 if threshold==.3:
  keeps=[{'start':a/30,'end':b/30} for a,b in intervals];p={'source_offset':offset,'before':len(y)/16000,'after':sum(b-a for a,b in intervals)/30,'keeps':keeps,'vad_threshold':threshold,'silence_ms':50,'margin_ms':15}
  (O/'v006-tight-plan.json').write_text(json.dumps(p,indent=2));z=np.concatenate([y[round(a/30*16000):round(b/30*16000)] for a,b in intervals]);np.save('/private/tmp/order-list-v006-after.npy',z)
  gaps=[];last=0
  for a,b in intervals:
   if a/30>last:gaps.append([round(last,3),round(a/30,3),round(a/30-last,3)])
   last=b/30
  if len(y)/16000-last>.01:gaps.append([last,len(y)/16000,len(y)/16000-last])
  print('cuts',gaps)
