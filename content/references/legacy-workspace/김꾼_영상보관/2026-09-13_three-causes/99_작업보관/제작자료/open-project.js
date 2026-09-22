ObjC.import('Cocoa');ObjC.import('CoreGraphics');
const proc=Application('System Events').processes.byName('CapCut');proc.frontmost=true;delay(.5);
let target=proc.windows.byName('CapCut').uiElements().find(el=>{try{return el.description()==='HomePageDraftTitle:2026-09-13_three-causes_v001'}catch(e){return false}});
if(!target)throw Error('Project label missing');
let pos=target.position(),sz=target.size(),point=$.CGPointMake(pos[0]+sz[0]/2,pos[1]-45);
for(let n=1;n<=2;n++){for(let type of [1,2]){let ev=$.CGEventCreateMouseEvent(null,type,point,0);$.CGEventSetIntegerValueField(ev,1,n);$.CGEventPost(0,ev)}delay(.12)}
delay(2);
JSON.stringify({opened:'2026-09-13_three-causes_v001'});
