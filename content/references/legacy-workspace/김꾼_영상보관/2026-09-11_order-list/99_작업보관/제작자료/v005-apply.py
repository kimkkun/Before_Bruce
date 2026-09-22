from pathlib import Path
import json,zipfile,time,hashlib
O=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집');R=Path.home()/'Movies/CapCut/User Data/Projects/com.lveditor.draft/0911'
assert not (R/'.locked').exists(),'Close project first'
old=json.loads((R/'draft_info.json').read_text());expected=json.loads((O/'v005-base.json').read_text());
retry=(O/'v005-capcut-project.zip').exists()
if retry:
 with zipfile.ZipFile(O/'v005-capcut-project.zip') as z: previous=json.loads(z.read('draft_info.json'))
 def signatures(d):
  return [(t['type'],[(s['material_id'],round(s['target_timerange']['start']/1000),round(s['target_timerange']['duration']/1000),round(s['source_timerange']['start']/1000) if s.get('source_timerange') else None,s['clip']) for s in t['segments']]) for t in d['tracks']]
 assert signatures(previous)==signatures(old),'Current project changed'
else: assert old['tracks']==expected['tracks'],'Current clips changed; rebase needed'
assert retry or not old['materials']['texts'];new=json.loads((O/'v005-capcut-content.json').read_text());assert old['id']==new['id']
targets=[]
for p in R.rglob('*'):
 if p.name not in ('draft_info.json','draft_info.json.bak','template-2.tmp','template.tmp'):continue
 try:d=json.loads(p.read_text())
 except:continue
 if d.get('id')==old['id'] and 'tracks' in d:targets.append(p)
meta=R/'draft_meta_info.json';cache=R.parent/'root_meta_info.json';manifest=R/'Timelines/project.json'
if not retry:
 with zipfile.ZipFile(O/'v005-before-captions.zip','x',zipfile.ZIP_DEFLATED) as z:
  for p in targets+[meta,cache,manifest]:
   if p.exists():z.write(p,'root_meta_info.json' if p==cache else '0911/'+str(p.relative_to(R)))
# Keep editor's latest non-edit metadata; transplant prepared track/material edits only.
old['tracks']=new['tracks'];old['materials']=new['materials'];payload=json.dumps(old,ensure_ascii=False,separators=(',',':')).encode()
for p in targets:p.write_bytes(payload)
stamp=int(time.time()*1e6);m=json.loads(meta.read_text());m['tm_draft_modified']=stamp;meta.write_text(json.dumps(m,ensure_ascii=False,separators=(',',':')))
if cache.exists():
 d=json.loads(cache.read_text())
 for e in d.get('all_draft_store',[]):
  if e.get('draft_fold_path')==str(R):e['tm_draft_modified']=stamp
 cache.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
if manifest.exists():
 d=json.loads(manifest.read_text());d['update_time']=stamp
 for t in d.get('timelines',[]):
  if t.get('id')==old['id']:t['update_time']=stamp
 manifest.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
for p in targets:assert p.read_bytes()==payload
with zipfile.ZipFile(O/'v005-capcut-project.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in targets+[meta,manifest]:
  if p.exists():z.write(p,str(p.relative_to(R)))
(O/'v005-apply-verification.json').write_text(json.dumps({'duration':old['duration'],'captions':len(old['materials']['texts']),'video_clips':len(old['tracks'][0]['segments']),'files_updated':len(targets),'render_verified':False},indent=2))
print('Applied captions and style to native CapCut project:',len(targets),'files,',len(old['materials']['texts']),'captions')
