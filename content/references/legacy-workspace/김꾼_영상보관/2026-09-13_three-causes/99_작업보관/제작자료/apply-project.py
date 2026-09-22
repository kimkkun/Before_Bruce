from pathlib import Path
import json,zipfile,shutil,time,hashlib
O=Path(__file__).parent;R=Path.home()/'Movies/CapCut/User Data/Projects/com.lveditor.draft/2026-09-13_three-causes_v001'
assert not (R/'.locked').exists(),'Close project normally first'
old=json.loads((R/'draft_info.json').read_text());base=json.loads((O/'v000-original-project.json').read_text());new=json.loads((O/'v001-content.json').read_text())
def sig(d):
 return [(t['type'],[(s['material_id'],round(s['target_timerange']['start']*30/1e6),round(s['target_timerange']['duration']*30/1e6)) for s in t['segments']]) for t in d['tracks']]
expected=json.loads((O/'v001-applied-content.json').read_text()) if (O/'v001-applied-content.json').exists() else base
assert sig(old)==sig(expected),'Project changed since last application'
targets=[]
for p in R.rglob('*'):
 if p.name not in ('draft_info.json','draft_info.json.bak','template-2.tmp','template.tmp'):continue
 try:d=json.loads(p.read_text())
 except:continue
 if d.get('id')==old['id'] and 'tracks' in d:targets.append(p)
meta=R/'draft_meta_info.json';cache=R.parent/'root_meta_info.json';manifest=R/'Timelines/project.json'
with zipfile.ZipFile(O/('before-apply-'+str(time.time_ns())+'.zip'),'x',zipfile.ZIP_DEFLATED) as z:
 for p in targets+[meta,cache,manifest]:
  if p.exists():z.write(p,'gallery/root_meta_info.json' if p==cache else str(p.relative_to(R)))
media=R/'mcp_cut_media';media.mkdir(exist_ok=True)
for key in ('videos','audios'):
 for m in new['materials'].get(key,[]):
  p=m.get('path','')
  if not p or p.startswith('##_draftpath'):continue
  src=Path(p);assert src.is_file(),p
  dst=media/src.name
  if dst.exists() and hashlib.sha256(dst.read_bytes()).digest()!=hashlib.sha256(src.read_bytes()).digest():dst=media/(src.stem+'-'+hashlib.sha256(src.read_bytes()).hexdigest()[:8]+src.suffix)
  if src!=dst:
   if dst.exists():assert hashlib.sha256(dst.read_bytes()).digest()==hashlib.sha256(src.read_bytes()).digest()
   else:shutil.copy2(src,dst)
  m['path']=str(dst)
payload=json.dumps(new,ensure_ascii=False,separators=(',',':')).encode()
for p in targets:p.write_bytes(payload)
stamp=int(time.time()*1e6);m=json.loads(meta.read_text());m.update(tm_draft_modified=stamp,tm_duration=new['duration']);meta.write_text(json.dumps(m,ensure_ascii=False))
if cache.exists():
 d=json.loads(cache.read_text())
 for e in d.get('all_draft_store',[]):
  if e.get('draft_fold_path')==str(R) or e.get('draft_name')==R.name:e.update(tm_draft_modified=stamp,tm_duration=new['duration'],tm_duration_milli=new['duration']//1000)
 cache.write_text(json.dumps(d,ensure_ascii=False))
if manifest.exists():
 d=json.loads(manifest.read_text());d['update_time']=stamp
 for t in d.get('timelines',[]):
  if t.get('id')==new['id']:t['update_time']=stamp
 manifest.write_text(json.dumps(d,ensure_ascii=False))
(O/'v001-applied-content.json').write_bytes(payload)
assert all(p.read_bytes()==payload for p in targets)
print('Applied',new['duration']/1e6,'seconds;',len(targets),'synced timeline files;',[(t['type'],len(t['segments'])) for t in new['tracks']])
