from pathlib import Path
import json,copy,zipfile,hashlib,datetime
P=Path('/Users/kim.kkun/Movies/CapCut/User Data/Projects/com.lveditor.draft/0919')
O=Path(__file__).parent
raw=(P/'draft_info.json').read_bytes();d=json.loads(raw)
ref=json.loads((O.parents[2]/'2026-09-13_three-causes/03_수환수정/2026-09-18-project.json').read_text())
local=next(m for m in ref['materials']['audios'] if m['type']=='extract_music')
assert len(d['materials']['audios'])==11
with zipfile.ZipFile(O/'v003-before-audio-fix.zip','x',zipfile.ZIP_DEFLATED) as z:
 for f in P.iterdir():
  if f.is_file():z.write(f,f.name)
old=copy.deepcopy(d);changes=[]
for i,m in enumerate(d['materials']['audios']):
 name=m['name'];path=P/'owner-emotions-media'/name
 assert path.is_file(),path
 n=copy.deepcopy(local);n.update(id=m['id'],name=name,path=str(path),duration=m['duration'])
 assert n['effect_id']=='' and n['type']=='extract_music'
 d['materials']['audios'][i]=n
 for t in d['tracks']:
  for s in t['segments']:
   if s['material_id']==m['id']:
    gain=.15848931924611134 if name=='v001-bgm.wav' else (.35 if name.startswith('094d89') else (.28 if name.startswith('bfa290') else s['volume']))
    s.update(volume=gain,last_nonzero_volume=gain)
    changes.append({'name':name,'start':s['target_timerange']['start']/1e6,'gain':gain,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
assert [t for t in old['tracks'] if t['type']!='audio']==[t for t in d['tracks'] if t['type']!='audio']
assert (P/'draft_info.json').read_bytes()==raw
payload=json.dumps(d,ensure_ascii=False,separators=(',',':'))
for n in ['draft_info.json','template.tmp','template-2.tmp']:(P/n).write_text(payload)
(O/'v003-audio-fix.json').write_text(json.dumps({'at':datetime.datetime.now().isoformat(),'cause':'all audio incorrectly reused click effect_id 6873506883139799041','changes':changes,'non_audio_tracks_unchanged':True},ensure_ascii=False,indent=2))
print(json.dumps(changes,ensure_ascii=False))
