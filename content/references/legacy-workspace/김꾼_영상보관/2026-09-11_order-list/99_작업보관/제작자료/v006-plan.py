from pathlib import Path
import json,numpy as np
from faster_whisper.vad import get_speech_timestamps,VadOptions
O=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집');d=json.loads((O/'v006-analysis-base.json').read_text());y=np.load('/private/tmp/order-list-v006-before.npy')
v=get_speech_timestamps(y,VadOptions(threshold=.6,neg_threshold=.5,min_speech_duration_ms=50,min_silence_duration_ms=50,speech_pad_ms=0))
keeps=[]
for r in v:
 a=max(0,int(np.floor(r['start']/16000*30)));b=min(2724,int(np.ceil(r['end']/16000*30)))
 if keeps and a<=keeps[-1][1]:keeps[-1][1]=max(b,keeps[-1][1])
 else:keeps.append([a,b])
texts={t['id']:json.loads(t['content'])['text'] for t in d['materials']['texts']}
missing=[]
for s in next(t for t in d['tracks'] if t['type']=='text')['segments']:
 a=s['target_timerange']['start']/1e6*30;b=a+s['target_timerange']['duration']/1e6*30
 overlap=sum(max(0,min(b,e)-max(a,c)) for c,e in keeps)
 if overlap<1:missing.append({'text':texts[s['material_id']],'start':a/30,'end':b/30})
print('Missing caption overlap',missing)
assert not missing
p={'duration_before':90.8,'duration':sum(b-a for a,b in keeps)/30,'keeps':[{'start':a/30,'end':b/30} for a,b in keeps],'vad':{'threshold':.6,'neg_threshold':.5,'speech_pad_ms':0,'min_silence_ms':50},'native_audio_correlation':.97017133,'native_export_delay_seconds':.0478125,'boundary':'outward rounding to 30fps, no added pad'}
(O/'v006-tight-plan.json').write_text(json.dumps(p,indent=2));z=np.concatenate([y[round(a/30*16000):round(b/30*16000)] for a,b in keeps]);np.save('/private/tmp/order-list-v006-after.npy',z)
print('90.8 ->',p['duration'],'keeps',len(keeps),'removed',90.8-p['duration'])
print('ranges',keeps)
