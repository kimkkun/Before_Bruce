from pathlib import Path
import av,json,hashlib,shutil,numpy as np
from faster_whisper.audio import decode_audio
O=Path(__file__).parent;src=Path('/Users/kim.kkun/Movies/CapCut/2026-09-19_owner-emotions_v001.mov');dst=O/src.name
c=av.open(str(src));st=c.streams.video[0];info={'duration':c.duration/1e6,'width':st.width,'height':st.height,'fps':str(st.average_rate),'codec':st.codec_context.name};count=0;targets=[.6,2.2,8,43.9,71,75,99,109.7];captured=[]
for frame in c.decode(st):
 count+=1
 if targets and frame.time>=targets[0]:
  t=targets.pop(0);f=frame.reformat(width=540,height=960,format='rgb24');out=av.open(str(O/f'export-{t}.png'),'w');s=out.add_stream('png',rate=1);s.width=f.width;s.height=f.height;s.pix_fmt='rgb24'
  for pkt in s.encode(f):out.mux(pkt)
  for pkt in s.encode():out.mux(pkt)
  out.close();captured.append(t)
  if t==.6:
   out=av.open(str(O/'thumbnail-v001.png'),'w');s=out.add_stream('png',rate=1);s.width=frame.width;s.height=frame.height;s.pix_fmt='rgb24';f=frame.reformat(format='rgb24')
   for pkt in s.encode(f):out.mux(pkt)
   for pkt in s.encode():out.mux(pkt)
   out.close()
c.close();assert abs(count-3332)<=1,(count,info);assert not targets
if not dst.exists():shutil.copy2(src,dst)
assert hashlib.sha256(src.read_bytes()).digest()==hashlib.sha256(dst.read_bytes()).digest()
x=decode_audio(str(dst),sampling_rate=16000);np.save(O/'export-audio.npy',x)
info.update(decoded_frames=count,sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),source_originals_unchanged=all(hashlib.sha256((O.parent/'01_원본'/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in json.loads((O/'source-manifest.json').read_text())),audio_peak_dbfs=float(20*np.log10(np.max(np.abs(x))+1e-10)),clipped_samples=int(np.sum(np.abs(x)>=1)),full_human_listening=False,thumbnail='Opening frame extracted with title, provisional')
(O/'v001-verification.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));print(json.dumps(info,ensure_ascii=False),flush=True)
