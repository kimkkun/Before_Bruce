from pathlib import Path
import json,copy,uuid
O=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집');D=json.loads((O/'v006-analysis-base.json').read_text());P=json.loads((O/'v006-tight-plan.json').read_text());U=lambda:str(uuid.uuid4()).upper();us=lambda f:round(f*1e6/30)
intervals=[];cursor=0
for k in P['keeps']:
 a=round(k['start']*30);b=round(k['end']*30);intervals.append((a,b,cursor));cursor+=b-a
for tr in D['tracks']:
 result=[]
 for s in tr['segments']:
  a=round(s['target_timerange']['start']/1e6*30);b=round((s['target_timerange']['start']+s['target_timerange']['duration'])/1e6*30)
  for lo,hi,dst in intervals:
   x=max(a,lo);y=min(b,hi)
   if y<=x:continue
   n=copy.deepcopy(s);n['id']=U();ta=dst+x-lo;tb=dst+y-lo;n['target_timerange']={'start':us(ta),'duration':us(tb)-us(ta)}
   if n.get('source_timerange'):
    ss=round(s['source_timerange']['start']/1e6*30)+x-a;n['source_timerange']={'start':us(ss),'duration':us(ss+y-x)-us(ss)}
   if tr['type']=='text' and result and result[-1]['material_id']==n['material_id'] and abs(result[-1]['target_timerange']['start']+result[-1]['target_timerange']['duration']-n['target_timerange']['start'])<=1:
    result[-1]['target_timerange']['duration']=n['target_timerange']['start']+n['target_timerange']['duration']-result[-1]['target_timerange']['start']
   else:result.append(n)
 tr['segments']=sorted(result,key=lambda s:s['target_timerange']['start'])
D['duration']=us(cursor)
video=next(t for t in D['tracks'] if t['type']=='video');text=next(t for t in D['tracks'] if t['type']=='text');assert len(text['segments'])==69
assert video['segments'][0]['target_timerange']['start']==0
for a,b in zip(video['segments'],video['segments'][1:]):assert a['target_timerange']['start']+a['target_timerange']['duration']==b['target_timerange']['start']
assert sum(s['target_timerange']['duration'] for s in video['segments'])==D['duration']
assert all(s['target_timerange']['duration']>=33332 for t in D['tracks'] for s in t['segments'])
(O/'v006-capcut-content.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
tm={t['id']:json.loads(t['content'])['text'] for t in D['materials']['texts']};caps=[{'start':s['target_timerange']['start'],'end':s['target_timerange']['start']+s['target_timerange']['duration'],'text':tm[s['material_id']]} for s in text['segments']]
(O/'v006-captions.json').write_text(json.dumps(caps,ensure_ascii=False,indent=2))
def ts(us):
 ms=round(us/1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
(O/'v006-captions.srt').write_text('\n\n'.join(f'{i+1}\n{ts(c["start"])} --> {ts(c["end"])}\n{c["text"]}' for i,c in enumerate(caps))+'\n')
print('Prepared',D['duration']/1e6,'seconds;',len(video['segments']),'video clips;',len(caps),'captions')
