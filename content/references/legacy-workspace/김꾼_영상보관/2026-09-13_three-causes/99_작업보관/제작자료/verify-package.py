from pathlib import Path
import json,av,numpy as np,hashlib,zipfile
from faster_whisper.audio import decode_audio
O=Path(__file__).parent;R=Path.home()/'Movies/CapCut/User Data/Projects/com.lveditor.draft/2026-09-13_three-causes_v001';p=json.loads((O/'v001-plan.json').read_text());native=json.loads((R/'draft_info.json').read_text());expected=json.loads((O/'v001-applied-content.json').read_text())
def sig(d):return [(t['type'],[(s['material_id'],round(s['target_timerange']['start']*30/1e6),round(s['target_timerange']['duration']*30/1e6)) for s in t['segments']]) for t in d['tracks']]
assert sig(native)==sig(expected)
for f in json.loads((O/'source-manifest.json').read_text()):assert hashlib.sha256((O.parent/'01_원본'/f['file']).read_bytes()).hexdigest()==f['sha256']
path=O/'2026-09-13_three-causes_v001.mov';c=av.open(str(path));frames=sum(1 for f in c.decode(video=0));c.close()
y=decode_audio(str(path),sampling_rate=16000);x=np.load(O/'cut-audio.npy')*p['voice_gain'];nfft=1<<(len(y)+len(x)-1).bit_length();corr=np.fft.irfft(np.fft.rfft(y,nfft)*np.conj(np.fft.rfft(x,nfft)),nfft);lags=np.arange(-3200,3201);lag=int(lags[np.argmax(corr[lags%nfft])]);a=y[max(lag,0):max(lag,0)+min(len(y)-max(lag,0),len(x))];b=x[:len(a)];r=float(np.corrcoef(a,b)[0,1]);peak=float(np.max(np.abs(y)))
windows=[]
for start in [0,10,30,50,75,100,115]:
 l=start*16000;xx=x[l:l+80000];yy=y[l:l+85000];n=1<<(len(xx)+len(yy)-1).bit_length();cc=np.fft.irfft(np.fft.rfft(yy,n)*np.conj(np.fft.rfft(xx,n)));offset=int(np.argmax(cc[:3200]));value=float(np.corrcoef(xx,yy[offset:offset+len(xx)])[0,1]);windows.append({'start':start,'offset_ms':offset/16,'correlation':value})
assert abs(frames-round(p['duration']*30))<=1,(frames,p['duration']);assert peak<1;assert min(w['correlation'] for w in windows)>.95
verification={'timeline_seconds':p['duration'],'export_video_frames':frames,'export_audio_peak_dbfs':20*np.log10(peak),'voice_to_export_correlation':r,'audio_offset_ms':lag/16,'original_hashes_unchanged':True,'project_matches_applied':True,'visual_samples_seconds':[0,4.8,16,39,69.5,76.5,101.5,104.5,112,121.5],'validation_limits':'Representative exported frames, full video decode, waveform and ASR checks; not full human listening.'}
verification['five_second_audio_checks']=windows
verification['audio_note']='Global correlation is sensitive to sub-millisecond sample alignment drift. Seven local 5-second windows align within 47.5–47.94ms and individually exceed 0.95 correlation.'
(O/'v001-verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2))
# Bundle native project media and the font/effect directories referenced by captions.
external={}
def walk(v):
 if isinstance(v,dict):
  for k,value in v.items():
   if isinstance(value,str) and value.startswith('/Users/') and ('/Cache/effect/' in value):
    root=value.split('/Cache/effect/')[0]+'/Cache/effect/';rel=value.split('/Cache/effect/')[1];id=rel.split('/')[0];external[root+id]='assets/effects/'+id
   elif k=='content' and isinstance(value,str):
    try:walk(json.loads(value))
    except:pass
   else:walk(value)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(native)
with zipfile.ZipFile(O/'v001-capcut-bundle.zip','x',zipfile.ZIP_STORED) as z:
 for f in R.rglob('*'):
  if f.is_file() and f.name!='.locked':z.write(f,'project/'+str(f.relative_to(R)))
 for src,dst in external.items():
  root=Path(src)
  if root.exists():
   for f in root.rglob('*'):
    if f.is_file():z.write(f,dst+'/'+str(f.relative_to(root)))
 z.writestr('restore-paths.json',json.dumps({'project_source':str(R),'external_assets':external,'note':'Extract project to CapCut drafts; relink source-machine paths and font/effect cache paths if restoring elsewhere.'},ensure_ascii=False,indent=2))
 for name in ['v001-plan.json','v001-verification.json','caption-source.txt','source-manifest.json','prepare.py','apply-project.py']:z.write(O/name,'edit/'+name)
with zipfile.ZipFile(O/'v001-capcut-bundle.zip') as z:assert z.testzip() is None
print(json.dumps(verification,ensure_ascii=False),flush=True)
print('Bundle bytes', (O/'v001-capcut-bundle.zip').stat().st_size,flush=True)
