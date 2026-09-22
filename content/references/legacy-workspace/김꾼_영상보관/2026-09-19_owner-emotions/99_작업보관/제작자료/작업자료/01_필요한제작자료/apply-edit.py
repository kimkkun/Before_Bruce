from pathlib import Path
import json,zipfile,hashlib
O=Path(__file__).parent;P=Path('/Users/kim.kkun/Movies/CapCut/User Data/Projects/com.lveditor.draft/0919');raw=(P/'draft_info.json').read_bytes();old=json.loads(raw);assert old['duration']==207900000
with zipfile.ZipFile(O/'v000-original-loaded-backup.zip','x',zipfile.ZIP_DEFLATED) as z:
 for f in P.rglob('*'):
  if f.is_file():z.write(f,f.relative_to(P))
d=json.loads((O/'v001-content.json').read_text());assert d['id']==old['id'];assert (P/'draft_info.json').read_bytes()==raw
# Check every media path referenced by timeline.
for key in ['videos','audios']:
 for m in d['materials'].get(key,[]):
  assert Path(m['path']).is_file(),m['path']
for tr in d['tracks']:
 for s in tr['segments']:assert s['target_timerange']['duration']>0
payload=json.dumps(d,ensure_ascii=False,separators=(',',':'))
for n in ['draft_info.json','template.tmp','template-2.tmp']:(P/n).write_text(payload)
m=json.loads((P/'draft_meta_info.json').read_text());m['tm_duration']=d['duration'];(P/'draft_meta_info.json').write_text(json.dumps(m,ensure_ascii=False))
(O/'v001-applied-content.json').write_text(payload);print('Applied',d['duration']/1e6,'seconds with original backup')
