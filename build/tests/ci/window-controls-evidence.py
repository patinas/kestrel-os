import json,socket,sys,time,urllib.request
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
key("alt","shift","s");time.sleep(8);shot("quick-settings");key("alt","f4")
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
 cmd('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':int(x*32767/1280)}},{'type':'abs','data':{'axis':'y','value':int(y*32767/800)}},{'type':'btn','data':{'down':True,'button':'left'}}]})
 cmd('input-send-event',{'events':[{'type':'btn','data':{'down':False,'button':'left'}}]});time.sleep(2)
existing_settings={x['id'] for x in json.load(urllib.request.urlopen('http://127.0.0.1:19222/json')) if '#settings' in x.get('url','')}
key('alt','shift','s');time.sleep(8);shot('click-quick-before-all')
def live_audio():
 req=urllib.request.Request('http://127.0.0.1:18765/status',headers={'Host':'127.0.0.1:8765'})
 return json.load(urllib.request.urlopen(req,timeout=30))['audio']
# Coordinates measured from34aa0f4 original1280x800 quick-panel pixels.
for name,x in [('volume-down',978),('mute',1090),('volume-up',1204)]:
 before=live_audio();guest_click(x,479);after=live_audio();record('Quick panel '+name+' mouse effect',before!=after);shot('quick-mouse-'+name)
guest_click(1090,479) # unmute
# Real All settings button click.
guest_click(1090,627);time.sleep(4);shot('click-all-settings-result')
# Existing CDP target may not be the newly opened Settings tab; reconnect to the actual pane.
ws.close()
pages=json.load(urllib.request.urlopen('http://127.0.0.1:19222/json'))
page=next(x for x in pages if x['type']=='page' and '#settings' in x['url'] and x['id'] not in existing_settings)
ws=websocket.create_connection(page['webSocketDebuggerUrl'].replace('localhost:9222','127.0.0.1:19222').replace('127.0.0.1:9222','127.0.0.1:19222'),origin='http://localhost',timeout=60)
record('Quick settings All settings',js("document.querySelector('#settings').open"))
record('Shelf process',bool(state.get('waybar_running')));record('Settings direct entry',js("document.querySelector('#settings').open"));shot('click-settings-open')
for button in ['volume-up','volume-down','mute']:
 actual_before=live_audio()
 before=js("document.querySelector('#audio-state').textContent");click('button[onclick="callBridge(\'/'+button+'\')"]');js('refresh()');time.sleep(2)
 actual_after=live_audio();print('AUDIO_EFFECT',button,repr(actual_before),repr(actual_after),flush=True)
 record('Settings '+button+' effect',actual_before!=actual_after);js('refresh()');record('Settings '+button+' display',actual_after==js("document.querySelector('#audio-state').textContent"));shot('click-'+button)
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
# Launcher search via real keys, no script-generated result.
key('meta_l');time.sleep(2);text('mail');time.sleep(2);shot('click-launcher-search');key('esc')
# Shelf clock and panel Close coordinates measured from prior full-size frames.
guest_click(1234,768);time.sleep(8);shot('shelf-mouse-clock')
guest_click(1090,700);time.sleep(3);shot('quick-mouse-close')
guest_click(32,768);time.sleep(3);shot('shelf-mouse-launcher');key('esc')
# Every unsupported effect remains blocked rather than fabricated as a test pass.
for control in ['Quick panel Close pixel review','Shelf launcher/clock pixel review','Shelf launcher/clock mouse','Launcher Browser tile mouse','Taskbar mouse activate/close','Launcher Mail/Video/Settings/Terminal tile launches','Quick panel Network setup mouse','PWA install/relaunch','Installer options','Hardware media/brightness/touchpad/lid','Chrome sync/keyring','Advanced password enable/disable','Signed OS update','Gaming mode','Refresh Chrome']:
 results.append({'control':control,'result':'UNVERIFIED'})
cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(4);shot('settings-after-controls')
v.joinpath('control-results.json').write_text(json.dumps(results,indent=2));[print('CONTROL_FINAL',json.dumps(x),flush=True) for x in results]
cdp('Page.navigate',{'url':'https://www.google.com'});time.sleep(3);shot('click-final-desktop');ws.close()
for _ in range(4):key('alt','f4');time.sleep(1)
shot('wallpaper');key('meta_l','b');time.sleep(4);shot('owner-ready')

req=urllib.request.Request('http://127.0.0.1:18765/status',headers={'Host':'127.0.0.1:8765'})
final_state=json.load(urllib.request.urlopen(req,timeout=20));print('FINAL_WAYBAR_DIAGNOSTIC',json.dumps(final_state),flush=True)
if any(x['result']=='FAIL' for x in results):raise RuntimeError('A control assertion failed; inspect CONTROL_RESULTS')
