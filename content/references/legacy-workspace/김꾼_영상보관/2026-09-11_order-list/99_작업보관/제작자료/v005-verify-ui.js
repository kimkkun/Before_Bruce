ObjC.import('Cocoa');ObjC.import('CoreGraphics');const app=Application.currentApplication();app.includeStandardAdditions=true;
function post(t,x,y){$.CGEventPost(0,$.CGEventCreateMouseEvent(null,t,$.CGPointMake(x,y),0));}
post(1,950,59);delay(.1);post(6,250,59);delay(.2);post(2,250,59);delay(.5);
const windows=ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1,0)));const w=windows.find(x=>x.kCGWindowOwnerName==='CapCut'&&x.kCGWindowName==='CapCut');if(!w)throw Error('No CapCut window');
for(const [time,label] of [[4,'zoom'],[78.5,'long'],[65,'order']]){const x=w.kCGWindowBounds.X+183+8.72*time;post(1,x,665);post(2,x,665);delay(.7);app.doShellScript('/usr/sbin/screencapture -x -l '+w.kCGWindowNumber+' /private/tmp/order-list-v005-'+label+'.png');}
JSON.stringify({window:w.kCGWindowNumber,captures:3});
