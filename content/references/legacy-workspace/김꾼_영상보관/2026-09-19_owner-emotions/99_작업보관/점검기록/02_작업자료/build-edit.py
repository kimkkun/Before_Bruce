from pathlib import Path
import json,copy,uuid,zipfile,math,wave,av
import numpy as np
from faster_whisper.audio import decode_audio
O=Path(__file__).parent.resolve(); R=O.parent/'01_원본'; U=lambda:str(uuid.uuid4()).upper();us=lambda t:round(round(t*30)*1e6/30)
refdir=O.parents[1]/'2026-09-13_three-causes/03_수환수정'
oldcache='/Users/kim.kkun/Library/Containers/com.lemon.lvoverseas/Data/Movies/CapCut/User Data/Cache/'
cache=O/'resources/cache';cache.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(refdir/'2026-09-18-capcut-reference.zip') as z:
 for n in z.namelist():
  prefix='files'+oldcache
  if n.startswith(prefix) and not n.endswith('/'):
   relative=Path(n[len(prefix):]);assert '..' not in relative.parts
   f=cache/relative;f.parent.mkdir(parents=True,exist_ok=True)
   if not f.exists():f.write_bytes(z.read(n))
ref=json.loads((refdir/'2026-09-18-project.json').read_text().replace(oldcache,str(cache)+'/'))
D=json.loads((O/'v000-original-project.json').read_text());plan=json.loads((O/'v001-preparation-plan.json').read_text());duration=plan['duration'];caps=plan['captions'];keeps=plan['keeps'];template=copy.deepcopy(D['tracks'][0]['segments'][0]);mapped=lambda t:sum(max(0,min(t,k['source_end'])-k['source_start']) for k in keeps)
x=np.load(O/'cut-audio-preview.npy');rms=float(np.sqrt(np.mean(x*x)));peak=float(np.max(np.abs(x)));gain=min(10**((-20-20*math.log10(rms+1e-10))/20),.85/(peak+1e-10))
D['tracks'][0]['segments']=[];D['duration']=us(duration)
# Reference screen shows checklist, text entry, then published comment.
broll=[{'start':mapped(129.92),'end':mapped(135.52),'source_start':2.0,'file':next(R.glob('Screen*.MP4')),'scale':1.04,'y':.04},{'start':mapped(135.52),'end':mapped(143.07),'source_start':20.0,'file':next(R.glob('Screen*.MP4')),'scale':1.04,'y':.04},{'start':mapped(178.60),'end':mapped(184.78),'source_start':6.0,'file':next(R.glob('_talk*.MP4')),'scale':1.0,'y':.16}]
for k in keeps:
 a,b=us(k['start']),us(k['end']);points=sorted({a,b}|{us(p) for c in caps for p in (c['start'],c['end']) if a<us(p)<b}|{us(p) for r in broll for p in (r['start'],r['end']) if a<us(p)<b})
 for lo,hi in zip(points,points[1:]):
  s=copy.deepcopy(template);s.update(id=U(),volume=gain,last_nonzero_volume=gain);s['source_timerange']={'start':us(k['source_start'])+lo-a,'duration':hi-lo};s['target_timerange']={'start':lo,'duration':hi-lo}
  mid=(lo+hi)/2e6;cap=next((c for c in caps if c['start']<=mid<c['end']),None)
  if any(r['start']<=mid<r['end'] for r in broll):s['clip']['alpha']=0
  elif cap and cap['emphasis']:s['clip']['scale']={'x':1.2,'y':1.2};s['clip']['transform']={'x':0,'y':-.08}
  D['tracks'][0]['segments'].append(s)
def track(kind,name):
 t={'id':U(),'type':kind,'segments':[],'attribute':0,'flag':0,'is_default_name':False,'name':name};D['tracks'].append(t);return t
def refs(s):
 ids=[]
 for ident in s.get('extra_material_refs',[]):
  for key,items in ref['materials'].items():
   if not isinstance(items,list):continue
   m=next((x for x in items if x.get('id')==ident),None)
   if m:
    m=copy.deepcopy(m);m['id']=U();D['materials'].setdefault(key,[]).append(m);ids.append(m['id']);break
 s['extra_material_refs']=ids
vt=track('video','설명에 맞춘 자료 화면')
for r in broll:
 c=av.open(str(r['file']));v=c.streams.video[0];m=copy.deepcopy(D['materials']['videos'][0]);m.update(id=U(),path=str(r['file']),material_name=r['file'].name,width=v.width,height=v.height,duration=c.duration);c.close();D['materials']['videos'].append(m)
 s=copy.deepcopy(template);s.update(id=U(),material_id=m['id'],volume=0,last_nonzero_volume=0,extra_material_refs=[],track_render_index=1,render_index=1);s['source_timerange']={'start':us(r['source_start']),'duration':us(r['end'])-us(r['start'])};s['target_timerange']={'start':us(r['start']),'duration':us(r['end'])-us(r['start'])};s['clip']['scale']={'x':r['scale'],'y':r['scale']};s['clip']['transform']={'x':0,'y':r['y']};vt['segments'].append(s)
ct=track('text','한 줄 의미 단위 자막')
def addtext(tr,txt,a,b,kind='basic'):
 lookup={'basic':'직원들 망가지는 거','accent':'사장님은 다시 하래요','quote':'내가 해놓은 건 아무도 모르는데','intro':'Kim.kkun 입니다'}
 t=next((t for t in ref['materials']['texts'] if lookup[kind] in json.loads(t['content'])['text']),None)
 assert t,kind
 t=copy.deepcopy(t);s=copy.deepcopy(next(s for tr0 in ref['tracks'] for s in tr0['segments'] if s['material_id']==t['id']));t['id']=U();s.update(id=U(),material_id=t['id'],track_render_index=len(D['tracks'])-1,render_index=14000+len(D['materials']['texts']));s['target_timerange']={'start':us(a),'duration':us(b)-us(a)};s['clip']['transform']={'x':0,'y':-.13720930232558137};s['clip']['scale']={'x':.8946752491035556,'y':.8946752491035556}
 c=json.loads(t['content']);c['text']=txt;c['styles']=c['styles'][:1];c['styles'][0]['range']=[0,len(txt.encode('utf-16-le'))//2];t['content']=json.dumps(c,ensure_ascii=False);t.update(group_id='owner-emotions-v001',words={'start_time':[],'end_time':[],'text':[]},current_words={'start_time':[],'end_time':[],'text':[]},recognize_text='',base_content='');refs(s);D['materials']['texts'].append(t);tr['segments'].append(s)
for c in caps:
 kind='intro' if c['text']=='김꾼입니다' else ('quote' if 82<c['source']<88 else ('accent' if c['emphasis'] else 'basic'))
 addtext(ct,c['text'],c['start'],c['end'],kind)
# Opening title stays clear of face and one-line body captions.
pt=track('text','도입 제목');addtext(pt,'매장을 지키려다\n나를 잃어갔다',0,mapped(11.47))
ps=pt['segments'][0];ps['clip']['transform']['y']=.78
pm=next(t for t in D['materials']['texts'] if t['id']==ps['material_id']);pc=json.loads(pm['content']);pc['styles'][0]['size']=14;pm['font_size']=14;pm['content']=json.dumps(pc,ensure_ascii=False)
def writewav(path,data,sr):
 with wave.open(str(path),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(data,-1,1)*32767).astype('<i2').tobytes())
bg=decode_audio(str(next(R.glob('*.mp3'))),sampling_rate=44100);n=round(duration*44100);cross=22050;buf=bg.copy()
while len(buf)<n:
 buf[-cross:]=buf[-cross:]*(1-np.linspace(0,1,cross))+bg[:cross]*np.linspace(0,1,cross);buf=np.concatenate([buf,bg[cross:]])
bg=buf[:n].copy();bg[:15435]*=np.linspace(0,1,15435);bg[-79380:]*=np.linspace(1,0,79380);bgain=10**((-34-20*math.log10(float(np.sqrt(np.mean(bg*bg)))+1e-10))/20);writewav(O/'v001-bgm.wav',bg,44100)
def audio(tr,path,start,length,vol):
 m=copy.deepcopy(ref['materials']['audios'][0]);m.update(id=U(),path=str(path),name=Path(path).name,duration=us(length));D['materials'].setdefault('audios',[]).append(m)
 s=copy.deepcopy(next(s for t in ref['tracks'] if t['type']=='audio' for s in t['segments']));s.update(id=U(),material_id=m['id'],volume=vol,last_nonzero_volume=vol,extra_material_refs=[],common_keyframes=[]);s['source_timerange']={'start':0,'duration':us(length)};s['target_timerange']={'start':us(start),'duration':us(length)};tr['segments'].append(s)
bt=track('audio','ZISO · 대사 아래 배경음');audio(bt,O/'v001-bgm.wav',0,duration,bgain)
st=track('audio','강조와 화면 등장 효과음');sfx=[]
for start,name in [(c['start'],'Japanese drum' if c==caps[-1] else '拍 木') for c in caps if c['emphasis']]+[(max(0,r['start']-1/30),'Click_Mouse') for r in broll]:
 m=next(m for m in ref['materials']['audios'] if name in m.get('name',''));path=Path(m['path']);assert path.exists();a=decode_audio(str(path),sampling_rate=16000);vol=.11/(float(np.max(np.abs(a)))+1e-10);length=min(len(a)/16000,duration-start);audio(st,path,start,length,vol);sfx.append({'start':start,'path':str(path),'gain':vol})
(O/'v001-content.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
plan.update(status='built_not_applied',broll=[{**r,'file':str(r['file'])} for r in broll],voice_gain=gain,bgm_gain=bgain,sfx=sfx)
(O/'v001-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2));print({'duration':duration,'clips':len(D['tracks'][0]['segments']),'captions':len(caps),'voice_gain_db':20*math.log10(gain),'bgm_gain_db':20*math.log10(bgain)})
