from pathlib import Path
import json,copy,uuid,math,av,numpy as np,wave
from faster_whisper.audio import decode_audio
from faster_whisper.vad import get_speech_timestamps,VadOptions
O=Path(__file__).parent;R=O.parent/'01_원본';U=lambda:str(uuid.uuid4()).upper();us=lambda t:round(round(t*30)*1e6/30)
D=json.loads((O/'v000-original-project.json').read_text());ref=json.loads((O.parents[1]/'2026-09-11_order-list/02_AI편집/v007-final-content.json').read_text())
x=np.load(O/'source-audio.npy')
v=get_speech_timestamps(x,VadOptions(threshold=.35,min_speech_duration_ms=50,min_silence_duration_ms=50,speech_pad_ms=20))
exclude=[(27.5,29.95),(36,39.75),(57,59.48),(131,133.9),(136.5,138.5),(183,189.4),(212,214.5)]
intervals=[]
for r in v:
 parts=[(max(0,math.floor(r['start']/16000*30)),min(6715,math.ceil(r['end']/16000*30)))]
 for lo,hi in exclude:
  a,b=round(lo*30),round(hi*30);parts=[piece for l,h in parts for piece in ([(l,h)] if h<=a or l>=b else [(l,min(h,a)),(max(l,b),h)]) if piece[1]>piece[0]]
 for a,b in parts:
  if intervals and a<=intervals[-1][1]+1:intervals[-1][1]=max(b,intervals[-1][1])
  else:intervals.append([a,b])
keeps=[];cursor=0
for a,b in intervals:keeps.append({'source_start':a/30,'source_end':b/30,'start':cursor/30,'end':(cursor+b-a)/30});cursor+=b-a
duration=cursor/30
def mapped(t):return sum(max(0,min(t,k['source_end'])-k['source_start']) for k in keeps)
segments=[];template=copy.deepcopy(D['tracks'][0]['segments'][0]);audio=[]
for k in keeps:
 s=copy.deepcopy(template);s['id']=U();s['source_timerange']={'start':us(k['source_start']),'duration':us(k['end'])-us(k['start'])};s['target_timerange']={'start':us(k['start']),'duration':us(k['end'])-us(k['start'])};segments.append(s);audio.append(x[round(k['source_start']*16000):round(k['source_end']*16000)])
y=np.concatenate(audio);np.save(O/'cut-audio.npy',y)
rms=float(np.sqrt(np.mean(y*y)));peak=float(np.max(np.abs(y)));gain=min(10**((-20-20*math.log10(rms+1e-10))/20),.83/(peak+1e-10))
for s in segments:s['volume']=gain;s['last_nonzero_volume']=gain
D['tracks']=D['tracks'][:1];D['tracks'][0]['segments']=segments;D['duration']=us(duration)
def track(kind,name):
 t={'id':U(),'type':kind,'segments':[],'attribute':0,'flag':0,'is_default_name':False,'name':name};D['tracks'].append(t);return t
def clone_refs(s):
 ids=[]
 for oldid in s.get('extra_material_refs',[]):
  for key,items in ref['materials'].items():
   if not isinstance(items,list):continue
   m=next((m for m in items if m.get('id')==oldid),None)
   if m:
    m=copy.deepcopy(m);m['id']=U();D['materials'].setdefault(key,[]).append(m);ids.append(m['id']);break
 s['extra_material_refs']=ids
def text_template(accent=False,pov=False):
 t=next(t for t in ref['materials']['texts'] if ('POV:' in json.loads(t['content'])['text'] if pov else json.loads(t['content'])['text']==('바로 이런 틈이에요' if accent else '김꾼입니다')))
 s=next(s for tr in ref['tracks'] for s in tr['segments'] if s['material_id']==t['id']);return copy.deepcopy(t),copy.deepcopy(s)
def addtext(tr,txt,start,end,accent=False,pov=False,pos=None):
 t,s=text_template(accent,pov);t['id']=U();s['id']=U();s['material_id']=t['id'];s['target_timerange']={'start':us(start),'duration':us(end)-us(start)};s['render_index']=14000+len(D['materials']['texts']);s['track_render_index']=len(D['tracks'])-1
 c=json.loads(t['content']);c['text']=txt;c['styles']=c['styles'][:1];c['styles'][0]['range']=[0,len(txt.encode('utf-16-le'))//2];t['content']=json.dumps(c,ensure_ascii=False);t['group_id']='three-causes-v001';t['words']={'start_time':[],'end_time':[],'text':[]};t['current_words']=copy.deepcopy(t['words']);t['recognize_text']='';t['base_content']=''
 if pos is not None:s['clip']['transform']['y']=pos
 clone_refs(s);D['materials']['texts'].append(t);tr['segments'].append(s)
 return s
caps=[]
for line in (O/'caption-source.txt').read_text().splitlines():
 row=line.split('|');caps.append({'source':float(row[0]),'start':us(mapped(float(row[0])))/1e6,'text':row[1],'emphasis':len(row)>2})
caps[0]['start']=0
overlays=[(69.52,73.38,0,35.5),(76.04,80.4,0,40),(121.42,125.6,0,43),(134,136.4,0,67),(189.46,194.55,0,10),(198.71,203.7,1,24)]
broll=[{'start':mapped(a),'end':mapped(b),'file':sorted(R.glob('*.MP4'))[idx].name,'source_start':src} for a,b,idx,src in overlays]
# Hide talking head during screen inserts; native black canvas makes the screen readable.
for i,s in enumerate(list(segments)):
 a=s['target_timerange']['start']/1e6;b=a+s['target_timerange']['duration']/1e6
 points=sorted({us(a),us(b)}|{us(p) for r in broll for p in [r['start'],r['end']] if a<p<b})
 new=[]
 for lo,hi in zip(points,points[1:]):
  n=copy.deepcopy(s);n['id']=U();n['target_timerange']={'start':lo,'duration':hi-lo};n['source_timerange']={'start':s['source_timerange']['start']+lo-us(a),'duration':hi-lo}
  if any(us(r['start'])<=lo<us(r['end']) for r in broll):n['clip']['alpha']=0
  else:
   cap=next((c for j,c in enumerate(caps) if c['start']<=(lo+hi)/2e6<(caps[j+1]['start'] if j+1<len(caps) else duration)),None)
   if cap and cap['emphasis']:n['clip']['scale']={'x':1.17,'y':1.17};n['clip']['transform']={'x':0,'y':-.10}
  new.append(n)
 segments[i]=new
D['tracks'][0]['segments']=[s for group in segments for s in group]
vt=track('video','설명에 맞춘 참고 화면')
matbase=copy.deepcopy(D['materials']['videos'][0])
for r in broll:
 m=copy.deepcopy(matbase);m.update(id=U(),path=str(R/r['file']),material_name=r['file'],width=1320,height=2868,duration=us(76.461 if '51-07' in r['file'] else 31.186));D['materials']['videos'].append(m)
 s=copy.deepcopy(template);s.update(id=U(),material_id=m['id'],volume=0,last_nonzero_volume=0,extra_material_refs=[],render_index=1,track_render_index=1);s['source_timerange']={'start':us(r['source_start']),'duration':us(r['end'])-us(r['start'])};s['target_timerange']={'start':us(r['start']),'duration':us(r['end'])-us(r['start'])};s['clip']['scale']={'x':.84,'y':.84};s['clip']['transform']={'x':0,'y':.14};vt['segments'].append(s)
ct=track('text','한 줄 의미 단위 자막')
for i,c in enumerate(caps):
 c['end']=caps[i+1]['start'] if i+1<len(caps) else duration
 # Split only position at overlay boundaries, preserving the same phrase.
 points=sorted({us(c['start']),us(c['end'])}|{us(p) for r in broll for p in [r['start'],r['end']] if c['start']<p<c['end']})
 for a,b in zip(points,points[1:]):
  pos=-.80 if any(us(r['start'])<=a<us(r['end']) for r in broll) else None
  addtext(ct,c['text'],a/1e6,b/1e6,c['emphasis'],pos=pos)
pt=track('text','POV 도입 제목');addtext(pt,'POV:\n좋은 직원이\n망가지는 가게',0,mapped(14.15),pov=True)
def writewav(path,data,sr):
 with wave.open(str(path),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(data,-1,1)*32767).astype('<i2').tobytes())
bg=decode_audio(str(next(R.glob('*.mp3'))),sampling_rate=44100);n=round(duration*44100)
if len(bg)<n:
 cross=44100;buf=bg.copy()
 while len(buf)<n:
  buf[-cross:]=buf[-cross:]*(1-np.linspace(0,1,cross))+bg[:cross]*np.linspace(0,1,cross);buf=np.concatenate([buf,bg[cross:]])
 bg=buf
bg=bg[:n].copy();fadein=min(n,15435);fadeout=min(n,79380);bg[:fadein]*=np.linspace(0,1,fadein);bg[-fadeout:]*=np.linspace(1,0,fadeout)
bg_gain=min(10**((-40-20*math.log10(float(np.sqrt(np.mean(bg*bg)))+1e-10))/20),.1)
writewav(O/'v001-bgm.wav',bg,44100)
def addaudio(tr,path,start,length,volume):
 m=copy.deepcopy(ref['materials']['audios'][0]);m.update(id=U(),path=str(path),name=Path(path).name,duration=us(length));D['materials'].setdefault('audios',[]).append(m)
 old=next(s for t in ref['tracks'] if t['type']=='audio' for s in t['segments']);s=copy.deepcopy(old);s.update(id=U(),material_id=m['id'],volume=volume,last_nonzero_volume=volume,extra_material_refs=[]);s['source_timerange']={'start':0,'duration':us(length)};s['target_timerange']={'start':us(start),'duration':us(length)};tr['segments'].append(s)
bt=track('audio','Pocket Money · 대사 아래 배경음');addaudio(bt,O/'v001-bgm.wav',0,duration,bg_gain)
st=track('audio','강조 효과음');oldroot=O.parents[1]/'2026-09-11_order-list/02_AI편집'
sfx=[]
for c in caps:
 if not c['emphasis']:continue
 p=oldroot/('v007-sfx-drum.mp3' if c['source'] in [142.36,221.08] else 'v007-sfx-wood.mp3')
 a=decode_audio(str(p),sampling_rate=16000);vol=.075/(float(np.max(np.abs(a)))+1e-10);length=min(len(a)/16000,duration-c['start']);addaudio(st,p,c['start'],length,vol);sfx.append({'start':c['start'],'file':str(p),'gain':vol})
(O/'v001-content.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
(O/'v001-plan.json').write_text(json.dumps({'duration':duration,'keeps':keeps,'excluded_retakes':exclude,'captions':caps,'broll':broll,'voice_gain':gain,'voice_rms_db':20*math.log10(rms*gain),'voice_peak_db':20*math.log10(peak*gain),'bgm_gain':bg_gain,'sfx':sfx},ensure_ascii=False,indent=2))
print(json.dumps({'duration':duration,'clips':len(D['tracks'][0]['segments']),'captions':len(caps),'screens':len(broll),'voice_gain_db':20*math.log10(gain),'voice_peak_db':20*math.log10(peak*gain),'bgm_gain_db':20*math.log10(bg_gain)},ensure_ascii=False),flush=True)
