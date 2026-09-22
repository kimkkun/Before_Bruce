from pathlib import Path
import av,json,math,numpy as np,hashlib
from fractions import Fraction
base=Path('/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-11_order-list');outdir=base/'02_AI편집';src=next((base/'01_원본').glob('*.MOV'))
c=av.open(str(src));astream=c.streams.audio[0];sr=astream.codec_context.sample_rate
aframes=list(c.decode(astream));offset=float(aframes[0].time);a=np.concatenate([f.to_ndarray() for f in aframes],axis=1);c.close()
regions=json.loads((outdir/'v001-speech-regions.json').read_text());ranges=[]
for i,r in enumerate(regions):
 if 138<r['start']<140:r={**r,'end':141.04} # Keep first clause, remove incomplete '사장님도 흩어진'.
 if i==2:continue # 7.548–8.932 s incomplete take, next take is complete.
 lo=max(0,math.floor((r['start']-.30+offset)*30));hi=math.ceil((r['end']+.07+offset)*30)
 if ranges and lo-ranges[-1][1]<=3:ranges[-1][1]=hi
 else:ranges.append([lo,hi])
keeps=[];cursor=0;pieces=[];times=[]
for lo,hi in ranges:
 n=hi-lo;start=lo/30;end=hi/30
 x=round((start-offset)*sr);count=n*(sr//30)
 assert x>=0 and x+count<=a.shape[1]
 piece=a[:,x:x+count].copy();fade=min(176,count//2);ramp=np.linspace(0,1,fade);piece[:,:fade]*=ramp;piece[:,-fade:]*=ramp[::-1]
 pieces.append(piece);times.extend(np.arange(lo,hi)/30)
 keeps.append({'source_start':start,'source_end':end,'target_start':cursor/30,'duration':n/30});cursor+=n
cut_audio=np.concatenate(pieces,axis=1);dest=outdir/'2026-09-11_order-list_v002-cut.mp4'
plan={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_duration':179.349342,'asr_to_source_offset_seconds':offset,'retake_removed_asr':[[7.248,9.002],[141.11,143.28]],'fps':30,'duration':cursor/30,'clips':len(keeps),'keeps':keeps,'stage':'cut only; original framing, no captions or music','audio':'original stereo 44100 Hz; 4 ms cut-edge fades'}
(outdir/'v002-cut-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2));print('PLAN',cursor/30,len(keeps),flush=True)
output=av.open(str(dest),'w',options={'movflags':'+faststart'});vs=output.add_stream('libx264',rate=30);vs.width=720;vs.height=1280;vs.pix_fmt='yuv420p';vs.options={'crf':'18','preset':'fast'};vs.codec_context.color_primaries=1;vs.codec_context.color_trc=1;vs.codec_context.colorspace=1
ats=output.add_stream('aac',rate=sr);ats.layout='stereo';ats.bit_rate=192000
acursor=0

def feed_audio(until):
 global acursor
 while acursor<cut_audio.shape[1] and acursor<until:
  arr=np.ascontiguousarray(cut_audio[:,acursor:acursor+1024]);af=av.AudioFrame.from_ndarray(arr,format='fltp',layout='stereo');af.sample_rate=sr;af.pts=acursor;af.time_base=Fraction(1,sr)
  for pkt in ats.encode(af):output.mux(pkt)
  acursor+=arr.shape[1]
input=av.open(str(src));i=0
for frame in input.decode(video=0):
 t=float(frame.time)
 while i<len(times) and t>=times[i]-.5/30:
  vf=frame.reformat(720,1280,'yuv420p');vf.pts=i;vf.time_base=Fraction(1,30)
  for pkt in vs.encode(vf):output.mux(pkt)
  i+=1;feed_audio(round(i/30*sr))
  if i%600==0:print('render',i,'/',len(times),flush=True)
 if i==len(times):break
assert i==len(times)
feed_audio(cut_audio.shape[1])
for pkt in vs.encode():output.mux(pkt)
for pkt in ats.encode():output.mux(pkt)
output.close();input.close();print('DONE',dest,flush=True)
