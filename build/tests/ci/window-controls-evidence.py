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
time.sleep(8);shot('maximized-urlbar')
key('ctrl','n');time.sleep(6);shot('second-window')
key('alt','tab');time.sleep(2);shot('alt-tab-previous')
key('alt','f9');time.sleep(3);shot('minimized-taskbar')
key('alt','tab');time.sleep(3);shot('restored')
key('alt','f10');time.sleep(3);shot('unmaximized')
key('alt','f10');time.sleep(3);shot('maximized-controls')
key('ctrl','n');time.sleep(4);key('alt','f4');time.sleep(4);shot('close-window')
