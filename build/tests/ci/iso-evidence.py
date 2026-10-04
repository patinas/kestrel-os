import json,socket,sys,time
from pathlib import Path
v=Path(sys.argv[1]);s=socket.socket(socket.AF_UNIX);s.connect(str(v/'iso-qmp.sock'));f=s.makefile('rw');f.readline()
def cmd(name,args=None):
 d={'execute':name}
 if args:d['arguments']=args
 f.write(json.dumps(d)+'\n');f.flush()
 while True:
  r=json.loads(f.readline())
  if 'error' in r:raise RuntimeError(r)
  if 'return' in r:return r
def key(*keys):
 cmd('send-key',{'keys':[{'type':'qcode','data':k} for k in keys],'hold-time':100});time.sleep(.3)
def text(t):
 keys={' ':'spc','-':'minus',';':'semicolon','/':'slash','.':'dot','=':'equal'}
 for c in t:
  if c==':':key('shift','semicolon')
  elif c.isupper():key('shift',c.lower())
  else:key(keys.get(c,c))
def shot(n):cmd('screendump',{'filename':str(v/('iso-'+n+'.ppm'))})
cmd('qmp_capabilities');shot('chrome-terms')
# Owner accepted Google's terms in authenticated WhatsApp Oct4 12:40:57.
# This test types into a disposable guest only. ISO never has an auto-consent flag.
text('ACCEPT');key('ret');time.sleep(180);shot('shell')
text('kestrel os');shot('search-input');key('ret');time.sleep(25);shot('search-query-result')
key('alt','left');time.sleep(5);key('ctrl','a');key('backspace')
# Each shortcut is reached with genuine keyboard focus and Enter. External pages may block CI IPs.
for count,name in enumerate(['search','mail','video','games'],1):
 key('ctrl','l');text('http://127.0.0.1:8765');key('ret');time.sleep(5)
 for _ in range(count):key('tab')
 shot(name+'-focus');key('ret');time.sleep(30);shot(name+'-destination')
 key('alt','left');time.sleep(5);shot(name+'-back')
key('ctrl','l');text('http://127.0.0.1:8765');key('ret');time.sleep(8)
key('shift','tab');key('ret');time.sleep(8);shot('settings-status')
key('esc')
# Fresh virtual terminal login. Give getty time to settle before typing.
key('ctrl','alt','f2');time.sleep(15);text('kestrel');key('ret');time.sleep(8);shot('console-login')
text('getent hosts example.com; ip route; cat /proc/asound/cards; cat /run/kestrel-gpu');key('ret');time.sleep(8);shot('network-audio-gpu')
text('pgrep -a cage; pgrep -a chrome');key('ret');time.sleep(4);shot('processes')
# Exercise reversible user mode commands in this disposable live guest.
text('kestrel-mode bad');key('ret');time.sleep(2);shot('mode-invalid')
text('kestrel-mode gaming');key('ret');time.sleep(20);key('ctrl','alt','f1');time.sleep(15);shot('gaming-mode')
key('ctrl','alt','f2');time.sleep(5);text('kestrel-mode desktop');key('ret');time.sleep(20);key('ctrl','alt','f1');time.sleep(10);shot('desktop-restored')
cmd('quit')
