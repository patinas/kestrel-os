import json,socket,sys,time,urllib.request
from pathlib import Path
v=Path(sys.argv[1]);s=socket.socket(socket.AF_UNIX);s.connect(str(v/'install-qmp.sock'));f=s.makefile('rw');f.readline()
def cmd(name,args=None):
 d={'execute':name}
 if args:d['arguments']=args
 f.write(json.dumps(d)+'\n');f.flush()
 while True:
  r=json.loads(f.readline())
  if 'error' in r:raise RuntimeError(r)
  if 'return' in r:return r
def shot(n):cmd('screendump',{'filename':str(v/('install-'+n+'.ppm'))})
cmd('qmp_capabilities')
time.sleep(10)
shot('boot')  # firmware/sd-boot window: proves the disk alone boots over UEFI
# Host-forwarded readiness is a real guest HTTP/process assertion, not a timed guess.
ready=False
for _ in range(180):
 try:
  req=urllib.request.Request('http://127.0.0.1:18766/status',headers={'Host':'127.0.0.1:8765'})
  with urllib.request.urlopen(req,timeout=20) as r: state=json.load(r)
  if state.get('chrome_running'):ready=True;break
 except Exception as error:
  print("Readiness check:",type(error).__name__,str(error),flush=True)
 time.sleep(2)
shot('shell')
if not ready:raise RuntimeError('Installed system: Chrome/guest shell server failed readiness gate')
time.sleep(10)
shot('shell-settled')
cmd('quit')
