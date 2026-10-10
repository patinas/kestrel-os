#!/usr/bin/env python3
"""Taskbar grouping regression, no VM: real kestrel-taskbar daemon <-> mock wlr-foreign-toplevel compositor
over a real Wayland socket. Checks one icon per app, count badge, single-window activate, multi-window
list choice, close handling, and that ignored apps never get an icon."""
import json,os,subprocess,sys,tempfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]/'profile/airootfs'
LIB=str(R/'usr/local/lib/kestrel');BIN=str(R/'usr/local/bin/kestrel-taskbar')
run=tempfile.mkdtemp();os.chmod(run,0o700)
env={**os.environ,'XDG_RUNTIME_DIR':run,'WAYLAND_DISPLAY':'wl-tb-test','KESTREL_LIB':LIB,'KESTREL_TASKBAR_SIGNAL':'USR2','PYTHONFAULTHANDLER':'1'}
fails=[]
def check(name,ok,detail=''):
 print(('PASS ' if ok else 'FAIL ')+name+(' '+str(detail) if detail and not ok else ''),flush=True)
 if not ok:fails.append(name)
mock=subprocess.Popen([sys.executable,str(Path(__file__).with_name('mock_toplevel_compositor.py')),'wl-tb-test'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,env=env)
assert mock.stdout.readline().startswith('READY')
daemon=subprocess.Popen([sys.executable,BIN,'daemon'],env=env,stderr=subprocess.PIPE,text=True)
import select
end=time.time()+15;bound=False
while time.time()<end and not bound:
 if select.select([mock.stdout],[],[],0.5)[0]:bound=mock.stdout.readline().strip()=='BOUND'
if not bound:print('daemon never bound the manager:',daemon.stderr.read() if daemon.poll() is not None else 'still running');sys.exit(1)
def send(line):mock.stdin.write(line+'\n');mock.stdin.flush()
def tb(*a):return subprocess.run([sys.executable,BIN,*a],env=env,capture_output=True,text=True,timeout=15)
def status():
 return json.loads(tb('status').stdout)['groups']
def wait(pred,t=8):
 end=time.time()+t
 while time.time()<end:
  try:
   g=status()
   if pred(g):return g
  except Exception:pass
  time.sleep(.15)
 try:return status()
 except Exception:return None
try:
 for _ in range(60):
  if (Path(run)/'kestrel-taskbar/sock').exists():break
  time.sleep(.1)
 send('open google-chrome Kestrel start page');send('open google-chrome Second window');send('open foot Terminal')
 send('open kestrel-launcher Kestrel apps');send('open kestrel-quick-settings Kestrel quick settings')
 g=wait(lambda g:len(g)==2 and g[0]['count']==2)
 check('two apps, three windows -> two icons',g is not None and [(x['app_id'],x['count']) for x in g]==[('google-chrome',2),('foot',1)],g)
 check('launcher and quick settings never get an icon',g is not None and all(x['app_id'] not in ('kestrel-launcher','kestrel-quick-settings') for x in g))
 s0=tb('slot','0').stdout.strip();s1=tb('slot','1').stdout.strip();s2=tb('slot','2').stdout.strip()
 check('slot 0 and 1 have images, slot 2 is empty (hidden)',Path(s0).is_file() and Path(s1).is_file() and s2=='',(s0,s1,s2))
 from PIL import Image
 a=Image.open(s0).convert('RGBA');b=Image.open(s1).convert('RGBA')
 check('slot images are 48x48 (40x40 pill + 4px margin)',a.size==(48,48) and b.size==(48,48),(a.size,b.size))
 def badge(im):return im.getpixel((36,36))
 check('count badge drawn on the 2-window icon only',badge(a)[3]>200 and badge(a)[:3]!=badge(b)[:3] or badge(b)[3]<50,(badge(a),badge(b)))
 # single window: activate
 tb('click','1');time.sleep(.5)
 # activated state from compositor -> active pill
 send('state 2 activated');g=wait(lambda g:g[1]['active'])
 check('compositor activation shows as active icon',g is not None and g[1]['active'] and not g[0]['active'],g)
 ia=Image.open(tb('slot','1').stdout.strip()).convert('RGBA')
 check('active icon has the #a6c4eb pill',ia.getpixel((7,24))[:3]==(0xa6,0xc4,0xeb),ia.getpixel((7,24)))
 # minimized single window: click must unminimize then activate
 send('state 2 minimized');wait(lambda g:g[1]['minimized'])
 tb('click','1');time.sleep(.5)
 # multi window: menu choice, stubbed with the second line
 stub=Path(run)/'pick.sh';stub.write_text('#!/bin/sh\ncat >/dev/null\necho "2. Second window"\n');stub.chmod(0o755)
 env2={**env,'KESTREL_TASKBAR_MENU':str(stub)}
 r=subprocess.run([sys.executable,BIN,'click','0'],env=env2,capture_output=True,text=True,timeout=15)
 time.sleep(.5)
 # closing one of two windows leaves one window, badge gone
 send('close 0');g=wait(lambda g:g[0]['count']==1)
 check('closing one of two windows drops the count to 1',g is not None and g[0]['count']==1 and g[0]['windows'][0]['title']=='Second window',g)
 send('close 2');g=wait(lambda g:len(g)==1)
 check('closing the last window of an app removes its icon',g is not None and [x['app_id'] for x in g]==['google-chrome'],g)
 mock.stdin.close();out=mock.stdout.read().split()
finally:
 daemon.terminate();mock.kill()
reqs=[]
it=iter(out)
for tok in it:
 if tok in('ACTIVATE','UNMINIMIZE','MINIMIZE','CLOSE'):reqs.append((tok,next(it)))
check('single-window click sent ACTIVATE for the foot window (index 2)',('ACTIVATE','2') in reqs,reqs)
check('click on minimized window sent UNMINIMIZE before ACTIVATE',reqs.count(('UNMINIMIZE','2'))==1 and reqs.index(('UNMINIMIZE','2'))<len(reqs)-1,reqs)
check('multi-window click activated the window picked from the list (index 1)',('ACTIVATE','1') in reqs and ('ACTIVATE','0') not in reqs,reqs)
print('taskbar-test:',('FAILED '+str(fails)) if fails else 'all passed');sys.exit(1 if fails else 0)
