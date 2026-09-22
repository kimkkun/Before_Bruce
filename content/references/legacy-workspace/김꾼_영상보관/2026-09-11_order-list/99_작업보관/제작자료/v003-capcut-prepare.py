from pathlib import Path
import json,copy,uuid,hashlib,time
root=Path.home()/'Movies/CapCut/User Data/Projects/com.lveditor.draft/0911'
out=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집')
plan=json.loads((out/'v002-cut-plan.json').read_text());src=Path(plan['source']);dest=root/'Resources'/src.name
raw=(root/'draft_info.json').read_bytes();d=json.loads(raw)
assert not (root/'.locked').exists();assert d['duration']==0 and not d['tracks']
old=json.loads(Path('/private/tmp/capcut-before-tight.json').read_text());tr=next(t for t in old['tracks'] if t['type']=='video');seg=tr['segments'][0]
needed=set([seg['material_id']]+seg['extra_material_refs']);uid=lambda:str(uuid.uuid4()).upper();mapping={x:uid() for x in needed}
for key,arr in old['materials'].items():
 for m in arr if isinstance(arr,list) else []:
  if isinstance(m,dict) and m.get('id') in needed:
   n=copy.deepcopy(m);n['id']=mapping[m['id']];d['materials'].setdefault(key,[]).append(n)
v=d['materials']['videos'][0];v.update(path=str(dest),duration=round(plan['source_duration']*1e6),unique_id=uid(),has_audio=True,material_name=src.name,local_material_id='')
v['stable']['time_range']['duration']=v['duration']
t=copy.deepcopy(tr);t['id']=uid();t['segments']=[];cursor=0
for keep in plan['keeps']:
 s=copy.deepcopy(seg);s['id']=uid();s['material_id']=mapping[seg['material_id']];s['extra_material_refs']=[mapping[x] for x in seg['extra_material_refs']]
 end=round((keep['target_start']+keep['duration'])*1e6);s['source_timerange']={'start':round(keep['source_start']*1e6),'duration':end-cursor};s['target_timerange']={'start':cursor,'duration':end-cursor};cursor=end;t['segments'].append(s)
d['tracks']=[t];d['duration']=cursor;d['canvas_config'].update(width=720,height=1280,ratio='9:16');d['fps']=30.0
refs={m['id'] for arr in d['materials'].values() if isinstance(arr,list) for m in arr if isinstance(m,dict) and 'id' in m}
assert all(s['material_id'] in refs and all(x in refs for x in s['extra_material_refs']) for s in t['segments'])
(out/'v003-capcut-content.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
targets=[]
for p in root.rglob('*'):
 if p.name not in ('draft_info.json','draft_info.json.bak','template-2.tmp','template.tmp'):continue
 try:x=json.loads(p.read_text())
 except:continue
 if x.get('id')==d['id'] and 'tracks' in x:targets.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
manifest={'root':str(root),'targets':targets,'source':str(src),'source_sha256':plan['source_sha256'],'destination':str(dest),'duration':cursor,'segments':len(t['segments'])}
(out/'v003-capcut-apply-plan.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('prepared',len(targets),'native files',len(t['segments']),'clips',cursor)
