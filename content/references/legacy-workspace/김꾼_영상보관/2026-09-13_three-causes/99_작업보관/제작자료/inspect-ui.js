ObjC.import('Cocoa');ObjC.import('CoreGraphics');
let p=Application('System Events').processes.byName('CapCut');p.frontmost=true;delay(.3);
let found=[];for(let e of p.windows.byName('CapCut').uiElements()){try{let d=e.description();if(/MainTimeLineRoot|MainTimeLine|quicklyAdjustZoomFit|TimeLineRuler|currentProgress|ExportBtn/.test(d))found.push({d,position:e.position(),size:e.size()})}catch(err){}}
let windows=ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1,0))).filter(w=>w.kCGWindowOwnerName==='CapCut');JSON.stringify({found,windows});
