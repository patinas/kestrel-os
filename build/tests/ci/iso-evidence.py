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
 cmd('send-key',{'keys':[{'type':'qcode','data':k} for k in keys]}); time.sleep(.12)
key('ctrl','alt','f2'); time.sleep(3)
for k in ['k','e','s','t','r','e','l','ret']: key(k)
time.sleep(3)
# No shell writes: show running session processes and live ISO kernel cmdline.
text='pgrep -a cage; pgrep -a chromium; cat /proc/cmdline'
mapkey={' ':'spc','-':'minus',';':'semicolon','/':'slash'}
for c in text: key(mapkey.get(c,c))
key('ret'); time.sleep(4)
cmd('screendump',{'filename':str(v/'iso-console.ppm')})
cmd('quit')
