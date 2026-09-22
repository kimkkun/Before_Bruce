import Cocoa
import ApplicationServices
print("trusted",AXIsProcessTrusted())
let app = NSRunningApplication.runningApplications(withBundleIdentifier:"com.lemon.lvoverseas").first
print("app",app?.processIdentifier as Any)
let src=CGEventSource(stateID:.hidSystemState)
for down in [true,false] { let e=CGEvent(keyboardEventSource:src,virtualKey:53,keyDown:down)!;e.flags=[];e.post(tap:.cghidEventTap);usleep(100000) }
