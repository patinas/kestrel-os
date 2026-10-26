import json,socket,sys,time,urllib.request
from pathlib import Path
v=Path(sys.argv[1]);s=socket.socket(socket.AF_UNIX);s.connect(str(v/'flatpak-qmp.sock'));f=s.makefile('rw');f.readline()
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
def shot(n):cmd('screendump',{'filename':str(v/('flatpak-'+n+'.ppm'))})
cmd('qmp_capabilities');shot('chrome-terms')
# Chrome terms gate: kestrel-session runs chrome-setup before labwc, so the
# desktop never starts until the terms are accepted. Owner accepted Google's
# terms in authenticated WhatsApp Oct4 12:40:56 ("Ja", verified from channel
# history, +4523261420). This test types into a disposable guest only.
text('ACCEPT');key('ret')
# Session + network readiness: the guest shell server reports chrome_running only
# after first-boot Chrome download, so Flathub is reachable by then too.
ready=False
for _ in range(180):
 try:
  req=urllib.request.Request('http://127.0.0.1:18765/status',headers={'Host':'127.0.0.1:8765'})
  with urllib.request.urlopen(req,timeout=20) as r: state=json.load(r)
  if state.get('chrome_running'):ready=True;break
 except Exception as error:
  print("Readiness check:",type(error).__name__,str(error),flush=True)
 time.sleep(2)
if not ready:raise RuntimeError('guest shell never became ready')
# Console on tty2, log in as kestrel (password deleted by kestrel-firstboot).
key('ctrl','alt','f2');time.sleep(15);text('kestrel');key('ret');time.sleep(8)
shot('login')
# Run the smoke; it prints SMOKE_RESULT=PASS|FAIL full-screen at the end.
text('clear; sh /usr/local/lib/kestrel-ci/flatpak-smoke.sh');key('ret')
time.sleep(300);shot('smoke-mid')
time.sleep(120);shot('smoke-verdict')
# The calculator window should be on the desktop session on tty1.
key('ctrl','alt','f1');time.sleep(8);shot('flatpak-app')
# Launcher grid should list the app; W-space opens kestrel-launcher.
key('meta_l','spc');time.sleep(6);shot('flatpak-launcher');key('esc');time.sleep(2)
# Back to the console verdict for a final capture.
key('ctrl','alt','f2');time.sleep(4);shot('smoke-verdict-final')
cmd('quit')
