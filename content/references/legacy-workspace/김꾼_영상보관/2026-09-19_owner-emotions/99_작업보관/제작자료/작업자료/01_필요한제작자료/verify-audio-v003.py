from pathlib import Path
import json,re,hashlib,shutil,zipfile
import av,numpy as np
from faster_whisper.audio import decode_audio
O=Path(__file__).parent;A=O.parent;P=Path('/Users/kim.kkun/Movies/CapCut/User Data/Projects/com.lveditor.draft/0919')
src=Path('/Users/kim.kkun/Movies/CapCut/2026-09-19_owner-emotions_v003.mov')
x=decode_audio(str(src),sampling_rate=16000);old=decode_audio(str(A/'2026-09-19_owner-emotions_v002.mov'),sampling_rate=16000)
n=min(len(x),len(old));delta=x[:n]-old[:n]
bg=decode_audio(str(P/'owner-emotions-media/v001-bgm.wav'),sampling_rate=16000)
# Compare identical picture/voice edits: v003-v002 should contain restored music.
u=delta[15*16000:25*16000];v=bg[15*16000:25*16000];fft_n=524288
c=np.fft.irfft(np.fft.rfft(u,fft_n)*np.conj(np.fft.rfft(v,fft_n)),fft_n);lags=np.arange(-2000,2001);lag=int(lags[np.argmax(c[lags%fft_n])])
parts=[]
for a,b in [(15,25),(40,50),(78,85),(100,106)]:
 i,j=int(a*16000),int(b*16000);u=bg[i:j];v=delta[i+lag:j+lag];gain=float(np.dot(u,v)/np.dot(u,u));corr=float(np.corrcoef(u,v)[0,1]);parts.append({'seconds':[a,b],'restored_bgm_gain':gain,'correlation':corr})
assert all(p['correlation']>.9 and .09<p['restored_bgm_gain']<.13 for p in parts),parts
# Each effect: regress restored-minus-original audio against intended effect and old click.
d=json.loads((P/'draft_info.json').read_text());mats={m['id']:m for m in d['materials']['audios']};effects=[]
for t in d['tracks']:
 if t['type']!='audio' or len(t['segments'])<2:continue
 for s in t['segments']:
  m=mats[s['material_id']];path=P/re.sub(r'^##_draftpath_placeholder_[^/]+_##/','',m['path']) if m['path'].startswith('##_') else Path(m['path'])
  assert path.name==m['name'] and m['effect_id']=='' and m['type']=='extract_music'
  if path.name.startswith('33f11'):continue
  sample=decode_audio(str(path),sampling_rate=16000);i=round(s['target_timerange']['start']/1e6*16000)+lag;length=min(len(sample),round(s['target_timerange']['duration']/1e6*16000),n-i)
  window=delta[i-400:i+length+400];fn=1<<((len(window)+length-1).bit_length());cc=np.fft.irfft(np.fft.rfft(window,fn)*np.conj(np.fft.rfft(sample[:length],fn)),fn);offset=int(np.argmax(cc[:801]))-400;i+=offset;length=min(length,n-i)
  click=decode_audio(str(P/'owner-emotions-media/33f11a55221681b3fefec3346290169e.mp3'),sampling_rate=16000);c=np.zeros(length);c[:min(length,len(click))]=click[:length]
  y=delta[i:i+length]-bg[i-lag:i-lag+length]*(.15848931924611134/np.sqrt(2))
  mat=np.stack([sample[:length],c],axis=1);coef=np.linalg.lstsq(mat,y,rcond=None)[0];fit=mat@coef;corr=float(np.corrcoef(fit,y)[0,1]);effects.append({'start':i/16000,'file':path.name,'restored_gain':float(coef[0]),'correlation':corr})
assert all(e['correlation']>.8 and e['restored_gain']>.16 for e in effects),effects
with av.open(str(src)) as container:
 st=container.streams.video[0];info={'duration':container.duration/1e6,'width':st.width,'height':st.height,'fps':str(st.average_rate),'decoded_frames':sum(1 for _ in container.decode(st))}
assert info['decoded_frames']==3332
assert float(np.max(np.abs(x)))<1
originals=json.loads((A/'source-manifest.json').read_text());assert all(hashlib.sha256((A.parent/'01_원본'/m['file']).read_bytes()).hexdigest()==m['sha256'] for m in originals)
with zipfile.ZipFile(O/'v003-before-audio-fix.zip') as z:before=json.loads(z.read('draft_info.json'))
assert [t for t in d['tracks'] if t['type']!='audio']==[t for t in before['tracks'] if t['type']!='audio']
with zipfile.ZipFile(A/'v003-capcut-project-bundle.zip','x',zipfile.ZIP_DEFLATED) as z:
 for f in P.rglob('*'):
  if f.is_file():z.write(f,f.relative_to(P))
with zipfile.ZipFile(A/'v003-capcut-project-bundle.zip') as z:assert z.testzip() is None
assert not (A/src.name).exists();shutil.copy2(src,A/src.name)
sha=hashlib.sha256(src.read_bytes()).hexdigest();assert hashlib.sha256((A/src.name).read_bytes()).hexdigest()==sha
info.update(audio_alignment_samples=lag,sha256=sha,bgm_checks=parts,effect_checks=effects,audio_peak_dbfs=float(20*np.log10(np.max(np.abs(x)))),clipped_samples=int(np.sum(np.abs(x)>=1)),originals_unchanged=True,non_audio_tracks_unchanged=True,full_human_listening=False)
(O/'v003-verification.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));print(json.dumps(info,ensure_ascii=False,indent=2))
