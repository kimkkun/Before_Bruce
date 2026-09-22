ObjC.import('Cocoa');ObjC.import('CoreGraphics');
function click(x,y){for(let type of [1,2])$.CGEventPost(0,$.CGEventCreateMouseEvent(null,type,$.CGPointMake(x,y),0));delay(.3)}
function wins(){return ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1,0))).filter(w=>w.kCGWindowOwnerName==='CapCut')}
function run(args){let proc=Application('System Events').processes.byName('CapCut');proc.frontmost=true;delay(.3);
let main=wins().find(w=>w.kCGWindowName==='CapCut');let mb=main.kCGWindowBounds;
if(mb.X>200){let a=$.CGPointMake(mb.X+220,mb.Y+18),b=$.CGPointMake(260,58);$.CGEventPost(0,$.CGEventCreateMouseEvent(null,1,a,0));delay(.15);$.CGEventPost(0,$.CGEventCreateMouseEvent(null,6,b,0));delay(.25);$.CGEventPost(0,$.CGEventCreateMouseEvent(null,2,b,0));delay(.5)}
let w=wins().find(w=>(w.kCGWindowName||'').startsWith('내보내기'));
if(!w){for(let el of proc.windows.byName('CapCut').uiElements()){try{if(el.description()==='MainWindowTitleBarExportBtn'){let p=el.position(),s=el.size();click(p[0]+s[0]/2,p[1]+s[1]/2);break}}catch(e){}}delay(1.5);w=wins().find(w=>(w.kCGWindowName||'').startsWith('내보내기'))}
if(!w)throw Error('Export panel missing');
let b=w.kCGWindowBounds;
if(args[0]==='name'){click(b.X+530,b.Y+102);Application('System Events').keystroke('a',{using:'command down'});Application('System Events').keystroke('2026-09-13_three-causes_v001');Application('System Events').keyCode(48);}
let task=$.NSTask.alloc.init;task.launchPath='/usr/sbin/screencapture';task.arguments=['-x','-l',String(w.kCGWindowNumber),'/Users/kim.kkun/Projects/김꾼_영상보관/2026-09-13_three-causes/02_AI편집/export-panel.png'];task.launch;task.waitUntilExit;
return JSON.stringify(w);}
