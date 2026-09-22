from pathlib import Path
import json,copy,uuid,hashlib
O=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list/02_AI편집')
R=Path.home()/'Movies/CapCut/User Data/Projects/com.lveditor.draft/0911'
base=json.loads((O/'v005-base.json').read_text());assert base['duration']==90800000 and len(base['tracks'])==1
ref=json.loads(Path('/private/tmp/order-list-style-v5.json').read_text())
# Authored semantic boundaries; clip onsets correct ASR boundaries that absorb preceding silence.
rows='''0|직원은 말을 했고
1.24|사장은 들었습니다
2.967|그런데 주문은 안 들어갔죠|!
4.9|제가 더크루에서 풀고 싶은 게
6.36|바로 이런 틈이에요|!
7.833|김꾼입니다
8.867|직원이
9.26|“소스 얼마 안 남았어요” 하면
11.533|“어, 알았어”
12.20|이렇게 답하잖아요
13.7|그러다 손님이 부르고
14.90|배달 오고
15.933|영업 끝나면
17.2|“아까 뭐 시키라고 했더라?”
18.767|그럼 카톡으로 보내면 되잖아
20.967|“사장님, 내일 쓸 소스
22.3|두 통 주문해주세요”
23.767|그거 읽고 나서
24.54|“아, 이따 시켜야지”
26|이렇게 합니다
26.967|그런데 그 카톡 밑으로
28.3|근무 바꿔달라는 얘기
30.133|마감 사진 같은 게
31.24|막 쌓이잖아요
32.5|막상 주문할 때 되면
33.68|그 메시지가
34.40|위로 밀려 있는 거죠|!
35.767|직원은 말도 했고
36.94|카톡도 보냈어요
38.6|사장님도 챙기려고 했고요
40.433|그런데 주문할 때 볼 목록을
42.26|머릿속에서
43.333|카톡에서 다시 찾아
44.42|모아야 하잖아요
45.467|그 사이에 한두 개가
46.46|빠지는 겁니다|!
47.467|그래서 더크루 발주는
48.62|이렇게 쓰는 겁니다
50.033|상품 목록 적고
51.5|수량 제출하고
52.767|사장님이 확인하고
54.133|끝!|!
54.6|우리 가게에서 쓰는 상품을
56.02|미리 적어놓고
57.533|직원이 재고를 보면서
58.76|필요한 수량을 골라
60.233|제출하면 됩니다
61.433|홀에서 올린 거
62.36|주방에서 올린 거
63.533|이런 것들이
64.12|사장님 주문표에 다 모입니다|!
66.133|사장님은 그 표를 보고
68.367|거래처에 주문만 하면
69.58|되는 거예요
70.4|직원은 매번 상품을
71.66|안 적어도 되고
72.6|사장님도 흩어진 말을
73.72|모을 필요가 없습니다|!
75.167|물론 지금 당장 떨어지는 건
76.60|바로 알려야죠
77.633|다음 주문부터 빠트리지 않도록
79.5|재고를 확인하고
80.9|표를 올릴 시간을 정해주세요|!
82.833|“알았어” 했다고
84.36|주문이 들어가진 않잖아요|!
85.9|지금 사장님 가게는
86.9|주문할 재료를
87.76|어디에 모으십니까?
89.067|댓글에 남겨주세요'''
U=lambda:str(uuid.uuid4()).upper()
def template(text):
 t=next(t for t in ref['materials']['texts'] if json.loads(t['content'])['text']==text)
 s=next(s for tr in ref['tracks'] for s in tr['segments'] if s['material_id']==t['id'])
 return t,s
normal=template('김꾼입니다');accent=template('같이 보는 게 포인트입니다')
D=copy.deepcopy(base);track={'id':U(),'type':'text','segments':[],'attribute':0,'flag':0,'is_default_name':True,'name':''};caps=[]
for line in rows.splitlines():
 v=line.split('|');caps.append({'start':round(round(float(v[0])*30)*1e6/30),'text':v[1],'emphasis':len(v)>2})
for i,c in enumerate(caps):
 c['end']=caps[i+1]['start'] if i+1<len(caps) else D['duration'];assert c['end']>c['start']
 t,s=copy.deepcopy(accent if c['emphasis'] else normal);t['id']=U();s['id']=U();s['material_id']=t['id'];s['target_timerange']={'start':c['start'],'duration':c['end']-c['start']};s['render_index']=14000+i;s['track_render_index']=1
 t['group_id']='import_order_list_v005';t['words']={'start_time':[],'end_time':[],'text':[]};t['current_words']=copy.deepcopy(t['words']);t['recognize_text']='';t['base_content']=''
 content=json.loads(t['content']);content['text']=c['text'];content['styles']=content['styles'][:1];content['styles'][0]['range']=[0,len(c['text'].encode('utf-16-le'))//2]
 t['content']=json.dumps(content,ensure_ascii=False,separators=(',',':'));assert Path(t['font_path']).exists();assert Path(content['styles'][0]['effectStyle']['path']).exists()
 refs=[]
 for oldid in dict.fromkeys(s['extra_material_refs']):
  found=False
  for k,items in ref['materials'].items():
   if not isinstance(items,list):continue
   m=next((m for m in items if m.get('id')==oldid),None)
   if m:
    m=copy.deepcopy(m);m['id']=U();D['materials'].setdefault(k,[]).append(m);refs.append(m['id']);found=True;break
  assert found
 s['extra_material_refs']=refs;D['materials']['texts'].append(t);track['segments'].append(s)
D['tracks'].append(track)
# Restrained fixed punch-ins at selected key outcomes; source/time mapping is unchanged.
zooms=[(c['start'],c['end']) for c in caps if c['emphasis'] and c['text'] not in ['끝!','표를 올릴 시간을 정해주세요']]
new=[]
for s in D['tracks'][0]['segments']:
 a=s['target_timerange']['start'];b=a+s['target_timerange']['duration'];points=sorted({a,b}|{p for r in zooms for p in r if a+10<p<b-10})
 for x,y in zip(points,points[1:]):
  n=copy.deepcopy(s);n['id']=U();n['target_timerange']={'start':x,'duration':y-x};n['source_timerange']={'start':s['source_timerange']['start']+x-a,'duration':y-x}
  if any(lo-10<=x<hi-10 for lo,hi in zooms):n['clip']['scale']={'x':1.25,'y':1.25};n['clip']['transform']={'x':0.0,'y':-0.15}
  new.append(n)
D['tracks'][0]['segments']=new
# Verify every new piece has exactly the same original-media mapping as the accepted cut.
for n in new:
 x=n['target_timerange']['start'];s=next(s for s in base['tracks'][0]['segments'] if s['target_timerange']['start']<=x<s['target_timerange']['start']+s['target_timerange']['duration'])
 assert n['source_timerange']['start']==s['source_timerange']['start']+x-s['target_timerange']['start']
assert abs(sum(s['target_timerange']['duration'] for s in new)-D['duration'])<100
(O/'v005-base.json').write_text(json.dumps(base,ensure_ascii=False))
assert all('\n' not in c['text'] for c in caps)
(O/'v005-capcut-content.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
(O/'v005-captions.json').write_text(json.dumps(caps,ensure_ascii=False,indent=2))
def ts(us):
 ms=round(us/1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
(O/'v005-captions.srt').write_text('\n\n'.join(f'{i+1}\n{ts(c["start"])} --> {ts(c["end"])}\n{c["text"]}' for i,c in enumerate(caps))+'\n')
print('Prepared',len(caps),'captions;',sum(c['emphasis'] for c in caps),'emphasis;',len(zooms),'zoom ranges;',len(new),'video pieces; source mapping unchanged')
