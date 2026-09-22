from pathlib import Path
import json,shutil,zipfile,hashlib
O=Path(__file__).parent.resolve();P=Path('/Users/kim.kkun/Movies/CapCut/User Data/Projects/com.lveditor.draft/0919');D=json.loads((O/'v001-content.json').read_text());media=P/'owner-emotions-media';media.mkdir(exist_ok=True)
with zipfile.ZipFile(O/'v001-before-localize.zip','x',zipfile.ZIP_DEFLATED) as z:
 for f in P.glob('*'):
  if f.is_file():z.write(f,f.name)
replacements={}
for k in ['videos','audios']:
 for m in D['materials'][k]:
  src=Path(m['path']);dst=media/src.name
  if not dst.exists():shutil.copy2(src,dst)
  assert hashlib.sha256(src.read_bytes()).digest()==hashlib.sha256(dst.read_bytes()).digest()
  replacements[str(src)]=str(dst)
newres=P/'owner-emotions-resources'
shutil.copytree(O/'resources',newres,dirs_exist_ok=True)
payload=json.dumps(D,ensure_ascii=False,separators=(',',':')).replace(str(O/'resources'),str(newres))
for a,b in replacements.items():payload=payload.replace(a,b)
for n in ['draft_info.json','template.tmp','template-2.tmp']:(P/n).write_text(payload)
(O/'v001-applied-content.json').write_text(payload)
print('Project-local media and resources copied with SHA256 verification')
