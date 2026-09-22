from pathlib import Path
import json,copy,zipfile,hashlib
O=Path(__file__).parent;P=Path('/Users/kim.kkun/Movies/CapCut/User Data/Projects/com.lveditor.draft/0919')
raw=(P/'draft_info.json').read_bytes();d=json.loads(raw);assert not d['tracks']
with zipfile.ZipFile(O/'v000-empty-project-backup.zip','x',zipfile.ZIP_DEFLATED) as z:
 for f in P.rglob('*'):
  if f.is_file():z.write(f,f.relative_to(P))
r=json.loads((O.parents[1]/'2026-09-13_three-causes/02_AI편집/v000-original-project.json').read_text())
d['tracks']=r['tracks'];d['materials']=r['materials'];d['duration']=207900000;d['canvas_config'].update(width=1080,height=1920,ratio='9:16')
v=d['materials']['videos'][0];v.update(path=str(next((O.parent/'01_원본').glob('copy_*.MOV')).resolve()),duration=207900000,width=1080,height=1920,material_name=next((O.parent/'01_원본').glob('copy_*.MOV')).name)
s=d['tracks'][0]['segments'][0];s['source_timerange']['duration']=207900000;s['target_timerange']['duration']=207900000
assert (P/'draft_info.json').read_bytes()==raw
payload=json.dumps(d,ensure_ascii=False,separators=(',',':'))
(O/'v000-original-project.json').write_text(payload)
for n in ['draft_info.json','template.tmp','template-2.tmp']:(P/n).write_text(payload)
m=json.loads((P/'draft_meta_info.json').read_text());m['tm_duration']=207900000;(P/'draft_meta_info.json').write_text(json.dumps(m,ensure_ascii=False))
print('Original 207.9s timeline seeded; empty project backed up')
