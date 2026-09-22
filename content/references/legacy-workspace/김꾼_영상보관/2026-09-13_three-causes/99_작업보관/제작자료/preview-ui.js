ObjC.import('Cocoa');ObjC.import('CoreGraphics');
function run(argv){let p=Application('System Events').processes.byName('CapCut');p.frontmost=true;delay(.3);let windows=ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1,0)));let w=windows.find(w=>w.kCGWindowOwnerName==='CapCut'&&w.kCGWindowName==='CapCut');let b=w.kCGWindowBounds;
let x=b.X+183+Number(argv[0]||40)*6.17,y=b.Y+624;
for(let type of [1,2])$.CGEventPost(0,$.CGEventCreateMouseEvent(null,type,$.CGPointMake(x,y),0));delay(1);
let task=$.NSTask.alloc.init;task.launchPath='/usr/sbin/screencapture';task.arguments=['-x','-l',String(w.kCGWindowNumber),'/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-13_three-causes/02_AI편집/preview-'+(argv[0]||40)+'.png'];task.launch;task.waitUntilExit;return JSON.stringify({clicked:[x,y]});}
