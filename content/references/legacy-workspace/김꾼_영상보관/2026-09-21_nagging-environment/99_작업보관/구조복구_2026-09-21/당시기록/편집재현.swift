import Cocoa
import AVFoundation
let cfg=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))) as! [[String:Any]]
func tm(_ s:Double)->CMTime { CMTime(seconds:s,preferredTimescale:600) }
for task in cfg {
 let out=task["out"] as! String
 let comp=AVMutableComposition()
 let track=comp.addMutableTrack(withMediaType:.video,preferredTrackID:kCMPersistentTrackID_Invalid)!
 var instructions=[AVMutableVideoCompositionInstruction]()
 var cursor=0.0
 for seg in task["segments"] as! [[String:Any]] {
  let a=AVURLAsset(url:URL(fileURLWithPath:seg["path"] as! String))
  let st=a.tracks(withMediaType:.video)[0]
  let from=seg["from"] as! Double, dur=seg["dur"] as! Double
  try track.insertTimeRange(CMTimeRange(start:tm(from),duration:tm(dur)),of:st,at:tm(cursor))
  let size=st.naturalSize
  let scale=max(720.0/size.width,1280.0/size.height)
  let transform=CGAffineTransform(a:scale,b:0,c:0,d:scale,tx:(720-size.width*scale)/2,ty:(1280-size.height*scale)/2)
  let layer=AVMutableVideoCompositionLayerInstruction(assetTrack:track);layer.setTransform(transform,at:tm(cursor))
  let inst=AVMutableVideoCompositionInstruction();inst.timeRange=CMTimeRange(start:tm(cursor),duration:tm(dur));inst.layerInstructions=[layer];instructions.append(inst)
  cursor += dur
 }
 let vc=AVMutableVideoComposition();vc.renderSize=CGSize(width:720,height:1280);vc.frameDuration=CMTime(value:1,timescale:30);vc.instructions=instructions
 if let labels=task["labels"] as? [[String:Any]] {
  let parent=CALayer();parent.frame=CGRect(x:0,y:0,width:720,height:1280)
  let video=CALayer();video.frame=parent.bounds;parent.addSublayer(video)
  for x in labels {
   let box=CALayer();box.frame=CGRect(x:28,y:1150,width:664,height:80);box.backgroundColor=NSColor.black.withAlphaComponent(0.65).cgColor;box.cornerRadius=10;box.opacity=0
   let tx=CATextLayer();tx.frame=CGRect(x:20,y:21,width:624,height:42);tx.string=NSAttributedString(string:x["text"] as! String,attributes:[.font:NSFont(name:"AppleSDGothicNeo-Bold",size:28) ?? NSFont.boldSystemFont(ofSize:28),.foregroundColor:NSColor.white]);tx.contentsScale=2;box.addSublayer(tx)
   let anim=CABasicAnimation(keyPath:"opacity");anim.fromValue=1;anim.toValue=1;anim.beginTime=AVCoreAnimationBeginTimeAtZero+(x["at"] as! Double);anim.duration=x["dur"] as! Double;anim.isRemovedOnCompletion=false;anim.fillMode = .removed
   box.add(anim,forKey:"show");parent.addSublayer(box)
  }
  vc.animationTool=AVVideoCompositionCoreAnimationTool(postProcessingAsVideoLayer:video,in:parent)
 }
 let ex=AVAssetExportSession(asset:comp,presetName:AVAssetExportPresetHighestQuality)!
 ex.outputURL=URL(fileURLWithPath:out);ex.outputFileType = .mp4;ex.videoComposition=vc;ex.shouldOptimizeForNetworkUse=true
 let sem=DispatchSemaphore(value:0);ex.exportAsynchronously {sem.signal()}
 while sem.wait(timeout:.now()+0.1) == .timedOut { RunLoop.current.run(until:Date(timeIntervalSinceNow:0.05)) }
 if ex.status != .completed {fatalError(ex.error?.localizedDescription ?? "export failed")}
 print("Saved",out,cursor)
}
