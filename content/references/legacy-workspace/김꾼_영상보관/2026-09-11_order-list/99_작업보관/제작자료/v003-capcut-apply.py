from pathlib import Path
import json,hashlib,zipfile,shutil,time,os,uuid
out=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집');plan=json.loads((out/'v003-capcut-apply-plan.json').read_text());root=Path(plan['root']);assert not (root/'.locked').exists()
for x in plan['targets']:assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'],'Native draft changed'
src=Path(plan['source']);dst=Path(plan['destination']);assert hashlib.sha256(src.read_bytes()).hexdigest()==plan['source_sha256'];assert not dst.exists()
meta=root/'draft_meta_info.json';cache=root.parent/'root_meta_info.json';timeline=root/'Timelines/project.json'
backup=out/'v003-before-capcut.zip'
with zipfile.ZipFile(backup,'x',zipfile.ZIP_DEFLATED) as z:
 for p in [Path(x['path']) for x in plan['targets']]+[meta,timeline,cache]:
  if p.exists():z.write(p,'root_meta_info.json' if p==cache else '0911/'+str(p.relative_to(root)))
shutil.copy2(src,dst);assert hashlib.sha256(dst.read_bytes()).hexdigest()==plan['source_sha256']
payload=(out/'v003-capcut-content.json').read_bytes()
for x in plan['targets']:Path(x['path']).write_bytes(payload)
m=json.loads(meta.read_text());m['tm_duration']=plan['duration'];m['tm_draft_modified']=int(time.time()*1e6)
entry={'ai_group_type':'','create_time':0,'duration':179349342,'enter_from':0,'extra_info':src.name,'file_Path':str(dst),'height':1280,'id':str(uuid.uuid4()).upper(),'import_time':int(time.time()),'import_time_ms':-1,'item_source':1,'material_color_tag':'','md5':'','metetype':'video','roughcut_time_range':{'duration':179349342,'start':0},'sub_time_range':{'duration':-1,'start':-1},'type':0,'width':720}
next(r for r in m['draft_materials'] if r['type']==0)['value'].append(entry)
meta.write_text(json.dumps(m,ensure_ascii=False,separators=(',',':')))
if cache.exists():
 data=json.loads(cache.read_text())
 for e in data.get('all_draft_store',[]):
  if e.get('draft_fold_path')==str(root):e.update(tm_duration=plan['duration'],tm_draft_modified=m['tm_draft_modified'],tm_duration_milli=plan['duration']//1000)
 cache.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
if timeline.exists():
 data=json.loads(timeline.read_text());data['update_time']=m['tm_draft_modified']
 for t in data.get('timelines',[]):
  if t.get('id')==json.loads(payload)['id']:t['update_time']=data['update_time']
 timeline.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
for x in plan['targets']:assert Path(x['path']).read_bytes()==payload
print('Applied 32 source-backed clips to CapCut 0911, 105.633333s; original copied and hash verified. Backup:',backup)
