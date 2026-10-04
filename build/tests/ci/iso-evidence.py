import json,socket,sys,time
from pathlib import Path
v=Path(sys.argv[1]); s=socket.socket(socket.AF_UNIX); s.connect(str(v/'iso-qmp.sock')); f=s.makefile('rw'); f.readline()
def cmd(name,args=None):
 d={'execute':name}
 if args: d['arguments']=args
 f.write(json.dumps(d)+'\n'); f.flush()
 while True:
  r=json.loads(f.readline())
  if 'error' in r: raise RuntimeError(r)
  if 'return' in r:return r
cmd('qmp_capabilities'); cmd('screendump',{'filename':str(v/'iso-shell.ppm')})
def key(*keys):
 cmd('send-key',{'keys':[{'type':'qcode','data':k} for k in keys], 'hold-time':80}); time.sleep(.25)
# Capture real shell states and public shortcut destination, no account sign-in.
for k in ['k','e','s','t','r','e','l','spc','o','s']: key(k)
cmd('screendump',{'filename':str(v/'iso-search-input.ppm')})
key('ctrl','a'); key('backspace'); key('tab')
cmd('screendump',{'filename':str(v/'iso-search-launcher.ppm')})
key('ret'); time.sleep(25)
cmd('screendump',{'filename':str(v/'iso-search-page.ppm')})
cmd('quit')
