from pathlib import Path
import json,copy,uuid,zipfile
O=Path(__file__).parent;P=Path('/Users/kim.kkun/Movies/CapCut/User Data/Projects/com.lveditor.draft/0919');raw=(P/'draft_info.json').read_bytes();D=json.loads(raw);U=lambda:str(uuid.uuid4()).upper();us=lambda t:round(round(t*30)*1e6/30)
with zipfile.ZipFile(O/'v001-exported-project.zip','x',zipfile.ZIP_DEFLATED) as z:
 for f in P.glob('*'):
  if f.is_file():z.write(f,f.name)
vt=next(t for t in D['tracks'] if t.get('name')=='설명에 맞춘 자료 화면');vt['segments'][1]['source_timerange']['start']=14000000
ref=json.loads((O.parents[1]/'2026-09-13_three-causes/03_수환수정/2026-09-18-project.json').read_text());oldcache='/Users/kim.kkun/Library/Containers/com.lemon.lvoverseas/Data/Movies/CapCut/User Data/Cache/'
ref=json.loads(json.dumps(ref,ensure_ascii=False).replace(oldcache,str(P/'owner-emotions-resources/cache')+'/'))
plan=json.loads((O/'v001-plan.json').read_text());mapped=lambda t:sum(max(0,min(t,k['source_end'])-k['source_start']) for k in plan['keeps'])
t={'id':U(),'type':'sticker','segments':[],'attribute':0,'flag':0,'name':'현재 즐겨찾기에서 확인한 반응','is_default_name':False}
for name,a,b in [('US Labor Day EN Worker',15.49,17.69),('Labor Day',50.84,57.56)]:
 m=copy.deepcopy(next(m for m in ref['materials']['stickers'] if m.get('name')==name));s=copy.deepcopy(next(s for tr in ref['tracks'] for s in tr['segments'] if s['material_id']==m['id']));m['id']=U();s.update(id=U(),material_id=m['id'],extra_material_refs=[],common_keyframes=[]);s['target_timerange']={'start':us(mapped(a)),'duration':us(mapped(b))-us(mapped(a))};s['clip']['transform']={'x':.60,'y':-.48};s['clip']['scale']={'x':.30,'y':.30};D['materials']['stickers'].append(m);t['segments'].append(s)
D['tracks'].append(t);assert (P/'draft_info.json').read_bytes()==raw
payload=json.dumps(D,ensure_ascii=False,separators=(',',':'))
for n in ['draft_info.json','template.tmp','template-2.tmp']:(P/n).write_text(payload)
(O/'v002-applied-content.json').write_text(payload)
plan['broll'][1]['source_start']=14.;plan['stickers']=[{'name':m,'source_start':a,'source_end':b} for m,a,b in [('US Labor Day EN Worker',15.49,17.69),('Labor Day',50.84,57.56)]];plan['status']='applied';(O/'v002-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2));print('v002 applied: comment screen at source14s, two currently favorited stickers')
