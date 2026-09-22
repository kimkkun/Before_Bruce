from pathlib import Path
import json,zipfile,time
O=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집');R=Path.home()/'Movies/CapCut/User Data/Projects/com.lveditor.draft/0911';assert not (R/'.locked').exists(),'Project still open'
old=json.loads((R/'draft_info.json').read_text());base=json.loads((O/'v006-analysis-base.json').read_text());new=json.loads((O/'v006-capcut-content.json').read_text())
def sig(d):
 return [(t['type'],[(s['material_id'],round(s['target_timerange']['start']/1e6*30),round(s['target_timerange']['duration']/1e6*30),round(s['source_timerange']['start']/1e6*30) if s.get('source_timerange') else None,s['clip']) for s in t['segments']]) for t in d['tracks']]
assert sig(old)==sig(base),'Project changed since analysis'
assert [(t['id'],json.loads(t['content'])) for t in old['materials']['texts']]==[(t['id'],json.loads(t['content'])) for t in base['materials']['texts']],'Captions changed'
targets=[]
for p in R.rglob('*'):
 if p.name not in ('draft_info.json','draft_info.json.bak','template-2.tmp','template.tmp'):continue
 try:d=json.loads(p.read_text())
 except:continue
 if d.get('id')==old['id'] and 'tracks' in d:targets.append(p)
meta=R/'draft_meta_info.json';cache=R.parent/'root_meta_info.json';manifest=R/'Timelines/project.json'
with zipfile.ZipFile(O/'v006-before-tight.zip','x',zipfile.ZIP_DEFLATED) as z:
 for p in targets+[meta,cache,manifest]:
  if p.exists():z.write(p,'root_meta_info.json' if p==cache else '0911/'+str(p.relative_to(R)))
old['tracks']=new['tracks'];old['duration']=new['duration'];payload=json.dumps(old,ensure_ascii=False,separators=(',',':')).encode()
for p in targets:p.write_bytes(payload)
stamp=int(time.time()*1e6);m=json.loads(meta.read_text());m.update(tm_draft_modified=stamp,tm_duration=old['duration']);meta.write_text(json.dumps(m,ensure_ascii=False,separators=(',',':')))
if cache.exists():
 d=json.loads(cache.read_text())
 for e in d.get('all_draft_store',[]):
  if e.get('draft_fold_path')==str(R):e.update(tm_draft_modified=stamp,tm_duration=old['duration'],tm_duration_milli=old['duration']//1000)
 cache.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
if manifest.exists():
 d=json.loads(manifest.read_text());d['update_time']=stamp
 for t in d.get('timelines',[]):
  if t.get('id')==old['id']:t['update_time']=stamp
 manifest.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
for p in targets:assert p.read_bytes()==payload
with zipfile.ZipFile(O/'v006-capcut-project.zip','x',zipfile.ZIP_DEFLATED) as z:
 for p in targets+[meta,manifest]:
  if p.exists():z.write(p,str(p.relative_to(R)))
print('Applied',old['duration']/1e6,'seconds; tracks:',[(t['type'],len(t['segments'])) for t in old['tracks']])
