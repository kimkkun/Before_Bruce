from pathlib import Path
import av,json,hashlib
from faster_whisper import WhisperModel
b=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집');p=b/'2026-09-11_order-list_v002-cut.mp4';plan=json.loads((b/'v002-cut-plan.json').read_text());c=av.open(str(p))
result={'duration':c.duration/1e6,'streams':[]}
for s in c.streams:result['streams'].append({'type':s.type,'start':float(s.start_time*s.time_base),'duration':float(s.duration*s.time_base)})
c.close();assert abs(result['duration']-plan['duration'])<.06
assert all(abs(s['start'])<.05 for s in result['streams'])
assert hashlib.sha256(Path(plan['source']).read_bytes()).hexdigest()==plan['source_sha256']
for stream_type in ['video','audio']:
 c=av.open(str(p));s=next(s for s in c.streams if s.type==stream_type);last=-1;n=0
 for f in c.decode(s):
  assert float(f.time)>last;last=float(f.time);n+=1
 c.close();result[stream_type+'_frames']=n
print('MEDIA CHECK',result,flush=True)
m=WhisperModel('/Users/kim.kkun/Projects/sandbox/mcp-cut/whisper-small',device='cpu',compute_type='int8',cpu_threads=8)
segments,info=m.transcribe(str(p),language='ko',beam_size=5,vad_filter=False,condition_on_previous_text=False,initial_prompt='김꾼, 더크루, 발주, 주문표, 소스 두 통, 카톡')
rows=[]
for s in segments:
 rows.append({'start':s.start,'end':s.end,'text':s.text});print(f'{s.start:.2f}-{s.end:.2f} {s.text}',flush=True)
result['asr']=rows;result['source_unchanged']=True;result['validation_scope']='full media decode and ASR; not full human listening'
(b/'v002-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('DONE',flush=True)
