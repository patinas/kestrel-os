import json,socket,sys,time,urllib.request
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import uimeasure as uim
from pathlib import Path
v=Path(sys.argv[1]);s=socket.socket(socket.AF_UNIX);s.connect(str(v/'ui-qmp.sock'));f=s.makefile('rw');f.readline()
def cmd(n,a=None):
 d={'execute':n}
 if a:d['arguments']=a
 f.write(json.dumps(d)+'\n');f.flush()
 while True:
  r=json.loads(f.readline())
  if 'error' in r:raise RuntimeError(r)
  if 'return' in r:return r

def key(*k):cmd('send-key',{'keys':[{'type':'qcode','data':x} for x in k],'hold-time':100});time.sleep(.3)
def text(t):
 for c in t:
  if c.isupper():key('shift',c.lower())
  else:key(c)
def shot(n):cmd('screendump',{'filename':str(v/('ui-'+n+'.ppm'))})
cmd('qmp_capabilities');time.sleep(150);shot('terms');text('ACCEPT');key('ret')
ready=False
for _ in range(120):
 try:
  req=urllib.request.Request('http://127.0.0.1:18765/status',headers={'Host':'127.0.0.1:8765'})
  with urllib.request.urlopen(req,timeout=20) as r:state=json.load(r)
  if state.get('chrome_running'):ready=True;break
 except Exception as error:print(type(error).__name__,str(error),flush=True)
 time.sleep(2)
if not ready:raise RuntimeError('Chrome readiness failed')
print('WAYBAR_DIAGNOSTIC',json.dumps({'running':state.get('waybar_running'),'log':state.get('waybar_log')}),flush=True)
time.sleep(8);shot('maximized-urlbar')
key('ctrl','n');time.sleep(6);shot('second-window')
key('alt','tab');time.sleep(2);shot('alt-tab-previous')
key('alt','f9');time.sleep(3);shot('minimized-taskbar')
key('alt','tab');time.sleep(3);shot('restored')
key('alt','f10');time.sleep(3);shot('unmaximized')
key('alt','f10');time.sleep(3);shot('maximized-controls')
key('ctrl','n');time.sleep(4);key('alt','f4');time.sleep(4);shot('close-window')

key("meta_l");time.sleep(3);shot("launcher-grid");key("esc")
key("alt","shift","s");time.sleep(8);shot("quick-settings");key("esc");time.sleep(1)
key("alt","bracket_left");time.sleep(3);shot("snap-left");key("alt","equal");time.sleep(3);shot("shortcut-maximize")
# Append to existing genuine QMP key evidence. Only isolated CI guest uses CDP.
import websocket,random,string
ws=None
for _ in range(30):
 try:
  pages=json.load(urllib.request.urlopen('http://127.0.0.1:19222/json'))
  page=next(x for x in pages if x['type']=='page')
  ws=websocket.create_connection(page['webSocketDebuggerUrl'].replace('localhost:9222','127.0.0.1:19222').replace('127.0.0.1:9222','127.0.0.1:19222'),origin='http://localhost',timeout=60);break
 except Exception as e:time.sleep(1)
if ws is None:raise RuntimeError('CI Chrome debug unavailable')
seq=0
results=[]
def cdp(method,params={}):
 global seq
 seq+=1;ws.send(json.dumps({'id':seq,'method':method,'params':params}))
 while True:
  x=json.loads(ws.recv())
  if x.get('id')==seq:
   if 'error' in x:raise RuntimeError(x['error'])
   return x.get('result',{})
def js(expression):return cdp('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True}).get('result',{}).get('value')
def mouse(x,y):
 for type in ['mousePressed','mouseReleased']:cdp('Input.dispatchMouseEvent',{'type':type,'x':x,'y':y,'button':'left','clickCount':1})
def click(selector):
 point=js("(()=>{let e=document.querySelector("+json.dumps(selector)+");e.scrollIntoView({block:'center'});let r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
 mouse(*point);time.sleep(1)
def record(name,condition):
 results.append({'control':name,'result':'PASS' if condition else 'FAIL'});print('CONTROL_RESULT',name,results[-1]['result'],flush=True)
def guest_click(x,y):
 # Deliver motion, allow the compositor to update hover/focus, then a human-length press.
 cmd('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':int(x*32767/1280)}},{'type':'abs','data':{'axis':'y','value':int(y*32767/800)}}]})
 time.sleep(.25)
 cmd('input-send-event',{'events':[{'type':'btn','data':{'down':True,'button':'left'}}]});time.sleep(.12)
 cmd('input-send-event',{'events':[{'type':'btn','data':{'down':False,'button':'left'}}]});time.sleep(2)
import re,math
def fmt_audio(t):
 m=re.search(r'Volume:\s*([\d.]+)',t)
 if not m:return 'Unavailable'
 v=str(math.floor(float(m.group(1))*100+0.5))+'%'
 return 'Muted ('+v+')' if 'MUTED' in t else v
existing_settings={x['id'] for x in json.load(urllib.request.urlopen('http://127.0.0.1:19222/json')) if '#settings' in x.get('url','')}
def quick_layout(name):
 shot(name);lay=uim.qs_layout(uim.load_ppm(v/('ui-'+name+'.ppm')))
 return lay if lay and lay['mute'] and len(lay['tiles'])==2 and len(lay['wide'])==2 else None
def open_quick(name):
 # Reuse the panel when it is already open (a second press would exit on the single-instance lock), otherwise open it and
 # wait until the 360 px panel is measurable on screen before any click. Retries the shortcut; Escape first to clear stray popups.
 lay=quick_layout(name)
 if lay:return lay
 for attempt in range(3):
  key('esc');key('alt','shift','s')
  for _ in range(8):
   time.sleep(1.5);lay=quick_layout(name)
   if lay:time.sleep(1);return lay
  print('QUICK_OPEN_RETRY',attempt,flush=True)
 raise RuntimeError('quick settings panel did not appear (frame ui-'+name+'.ppm)')
def live_audio():
 req=urllib.request.Request('http://127.0.0.1:18765/status',headers={'Host':'127.0.0.1:8765'})
 return json.load(urllib.request.urlopen(req,timeout=30))['audio']
def quick_section():
 global L
 L=open_quick('click-quick-before-all')
 if not L or not L['mute'] or len(L['tiles'])!=2 or len(L['wide'])!=2:raise RuntimeError('quick settings layout not measurable: '+json.dumps(L))
 C=uim.center
 # Genuine QMP mouse coordinates grounded in sourcee881015 1280x800 full frame.
 # Panel x911..1271 y282..735, mute y530, slider x995..1251, bottom Close y704.
 before=live_audio();guest_click(C(L['tiles'][1])[0],C(L['mute'])[1]);after=live_audio();record('Quick slider mouse effect',before!=after);shot('quick-mouse-slider')
 before=live_audio();guest_click(*C(L['mute']));after=live_audio();record('Quick mute mouse effect',('MUTED' in before)!=('MUTED' in after));shot('quick-mouse-mute');guest_click(*C(L['mute']))
 guest_click(*C(L['tiles'][0]));shot('quick-mouse-network');key('alt','f4')
 guest_click(*C(L['tiles'][1]));shot('quick-mouse-bluetooth');key('alt','f4')
 guest_click(*C(L['wide'][1]));shot('quick-mouse-close');L=open_quick('click-quick-reopened')
 # Keyboard activates the focused real All settings.

 guest_click(*C(L['wide'][0]));time.sleep(8);shot('click-all-settings-first');shot('click-all-settings-result')

try:
 quick_section()
except Exception as e:
 print('QUICK_SECTION_ERROR',repr(e),flush=True);record('Quick settings mouse section',False)
 # fall back to opening Settings directly so the Settings checks still run
 cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(5)
print('SETTINGS_TARGETS_AFTER_MOUSE',json.dumps([{'id':p['id'],'url':p.get('url','')} for p in json.load(urllib.request.urlopen('http://127.0.0.1:19222/json'))]),flush=True)
# Existing CDP target may not be the newly opened Settings tab; reconnect to the actual pane.
ws.close()
pages=json.load(urllib.request.urlopen('http://127.0.0.1:19222/json'))
cand=[x for x in pages if x['type']=='page' and '#settings' in x['url'] and x['id'] not in existing_settings]
if not cand:
 record('Quick settings All settings opens a Settings page',False)
 cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(5)
 pages=json.load(urllib.request.urlopen('http://127.0.0.1:19222/json'))
 cand=[x for x in pages if x['type']=='page' and '#settings' in x['url']]
page=cand[0]
ws=websocket.create_connection(page['webSocketDebuggerUrl'].replace('localhost:9222','127.0.0.1:19222').replace('127.0.0.1:9222','127.0.0.1:19222'),origin='http://localhost',timeout=60)
record('Quick settings All settings',js("document.querySelector('#settings').open"))
record('Shelf process',bool(state.get('waybar_running')));record('Settings direct entry',js("document.querySelector('#settings').open"));shot('click-settings-open')
def settings_layout():
 keys=js("[...document.querySelectorAll('#settings .row .key')].map(e=>e.getBoundingClientRect().left)")
 btns=js("[...document.querySelectorAll('#settings .row button')].map(e=>e.getBoundingClientRect().right)")
 heads=js("[...document.querySelectorAll('#settings h2,#settings h3')].map(e=>e.getBoundingClientRect().left)")
 record('Settings: row labels share one left edge',keys and max(keys)-min(keys)<=1)
 record('Settings: row buttons share one right edge',btns and max(btns)-min(btns)<=1)
 record('Settings: headings share the label left edge',heads and keys and max(heads+keys)-min(heads+keys)<=1)
 record('Settings: no horizontal overflow',js("document.querySelector('#settings').scrollWidth<=document.querySelector('#settings').clientWidth+1"))
 record('Settings: no raw nmcli text',not js("/enp0s3:|:connected|Volume: 0\\./.test(document.querySelector('#settings').textContent)"))
 record('Settings: Bluetooth and status lines are separate elements',js("document.querySelector('#bluetooth-state').textContent.split('\\n').length===1"))
 for pos,name in ((0,'top'),(0.5,'middle'),(1,'bottom')):
  js("(()=>{let d=document.querySelector('#settings');d.scrollTop=(d.scrollHeight-d.clientHeight)*"+str(pos)+"})()");time.sleep(1);shot('settings-'+name)
 js("document.querySelector('#settings').scrollTop=0")
settings_layout()
for button in ['volume-up','volume-down','mute']:
 actual_before=live_audio()
 before=js("document.querySelector('#audio-state').textContent");click('button[onclick="callBridge(\'/'+button+'\')"]');js('refresh()');time.sleep(2)
 actual_after=live_audio();print('AUDIO_EFFECT',button,repr(actual_before),repr(actual_after),flush=True)
 record('Settings '+button+' effect',actual_before!=actual_after);js('refresh()');record('Settings '+button+' display',fmt_audio(actual_after)==js("document.querySelector('#audio-state').textContent"));shot('click-'+button)
# Unmute again so the owner starts with normal audio state.
click('button[onclick="callBridge(\'/mute\')"]');js('refresh()')
record('Advanced initially off',not js("document.querySelector('#advanced').checked"));record('Terminal initially disabled',js("document.querySelector('#terminal').disabled"));shot('click-advanced-off')
record('Installer options unavailable disclosure',js("document.querySelector('#settings').textContent.includes('pending installer work')"))
record('Touchpad/lid/lock unavailable disclosure',js("document.querySelector('#settings').textContent.includes('not available in this alpha UI')"))
record('Hardware battery truthful',js("document.querySelector('#battery-state').textContent.includes('No battery')"))
record('Network state displayed',bool(js("document.querySelector('#network-state').textContent")))
record('Bluetooth unavailable truthful',js("document.querySelector('#bluetooth-state').textContent.includes('No Bluetooth')"))
# Actual clicks launch bounded network/bluetooth tools. Capture and close, no device mutations.
for button in ['network','bluetooth']:

 if button=='bluetooth' and js("document.querySelector('button[onclick=\"callBridge(\\\'/bluetooth\\\')\"]').disabled"):
  shot('click-bluetooth-unavailable');record('Bluetooth setup disabled without hardware',True);continue
 click('button[onclick="callBridge(\'/'+button+'\')"]');time.sleep(3);shot('click-'+button);key('alt','f4');results.append({'control':'Settings '+button+' setup','result':'PIXEL_REVIEW'})
click('button[onclick="location.href=\'https://www.google.com\'"]');time.sleep(3);record('Settings Close returns to Google',js("location.hostname==='www.google.com'"));shot('click-settings-closed')
# Window controls by real mouse (Chrome titlebar buttons at their measured 1280x800 positions) and taskbar middle-click close.
def wstate():
 try:return cdp('Browser.getWindowForTarget')['bounds'].get('windowState')
 except Exception as e:return 'error '+repr(e)
def guest_middle(x,y):
 cmd('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':int(x*32767/1280)}},{'type':'abs','data':{'axis':'y','value':int(y*32767/800)}}]});time.sleep(.3)
 cmd('input-send-event',{'events':[{'type':'btn','data':{'down':True,'button':'middle'}}]});time.sleep(.12)
 cmd('input-send-event',{'events':[{'type':'btn','data':{'down':False,'button':'middle'}}]});time.sleep(2)
try:
 w0=wstate();guest_click(1241,13);time.sleep(2);w1=wstate();shot('titlebar-maximize-click');record('Titlebar maximize/restore button by mouse changes window state',w0!=w1 and not str(w1).startswith('error'))
 guest_click(1241,13);time.sleep(2);w2=wstate();record('Titlebar maximize/restore button toggles back',w2==w0)
except Exception as e:record('Titlebar maximize/restore by mouse',False);print('TITLEBAR_ERROR',repr(e),flush=True)
try:
 key('ctrl','n');time.sleep(6)
 shot('taskbar-two-windows');im=uim.load_ppm(v/'ui-taskbar-two-windows.ppm');shb=uim.bbox(uim.mask(im,'#e0e8f6',7,(0,700,1280,800)),2000)
 els=uim.shelf_elements(im,shb) if shb else []
 centre=[e for e in els if 300<=e[0] and e[2]<=980];n0=len(centre)
 record('Taskbar shows app buttons for two windows',n0>=4)
 if n0>=4:
  guest_middle(*C(centre[-1]));shot('taskbar-after-middle-close');im2=uim.load_ppm(v/'ui-taskbar-after-middle-close.ppm');els2=uim.shelf_elements(im2,shb);n1=len([e for e in els2 if 300<=e[0] and e[2]<=980])
  record('Taskbar middle-click closes that window',n1==n0-1)
except Exception as e:record('Taskbar middle-click close',False);print('TASKBAR_ERROR',repr(e),flush=True)
# Launcher search via real keys, no script-generated result.
key('meta_l');time.sleep(2);text('mail');time.sleep(2);shot('click-launcher-search');key('esc')
# Every unsupported effect remains blocked rather than fabricated as a test pass.
for control in ['New quick-panel Close mouse','Quick panel Close pixel review','Shelf launcher/clock pixel review','Shelf launcher/clock mouse','Launcher Browser tile mouse','Launcher Mail/Video/Settings/Terminal tile launches','Quick panel Network setup mouse','PWA install/relaunch','Installer options','Hardware media/brightness/touchpad/lid','Chrome sync/keyring','Advanced password enable/disable','Signed OS update','Gaming mode','Refresh Chrome']:
 results.append({'control':control,'result':'UNVERIFIED'})
cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(4);shot('settings-after-controls')
v.joinpath('control-results.json').write_text(json.dumps(results,indent=2));[print('CONTROL_FINAL',json.dumps(x),flush=True) for x in results]
cdp('Page.navigate',{'url':'https://www.google.com'});time.sleep(3);shot('click-final-desktop');ws.close()
for _ in range(4):key('alt','f4');time.sleep(1)
shot('wallpaper');key('meta_l','b');time.sleep(4);shot('owner-ready')

req=urllib.request.Request('http://127.0.0.1:18765/status',headers={'Host':'127.0.0.1:8765'})
final_state=json.load(urllib.request.urlopen(req,timeout=20));print('FINAL_WAYBAR_DIAGNOSTIC',json.dumps(final_state),flush=True)
if any(x['result']=='FAIL' for x in results):raise RuntimeError('A control assertion failed; inspect CONTROL_RESULTS')
