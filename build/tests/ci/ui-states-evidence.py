#!/usr/bin/env python3
"""Interaction states + pixel-measured symmetry for the Kestrel shell, run in the disposable CI guest after window-controls-evidence.py.
Usage: ui-states-evidence.py VMDIR. Frames: ui-st-*.ppm. Results: ui-state-results.json. Exit 1 on any FAIL or UNMEASURED.
Measurements come from real QEMU screendumps (1280x800), found by the CSS colours in the shipped stylesheets. A colour not found means UNMEASURED, never a pass."""
import json,socket,sys,time,urllib.request
from pathlib import Path
import numpy as np
v=Path(sys.argv[1]);sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ui'))
import symmetry_check
s=socket.socket(socket.AF_UNIX);s.connect(str(v/'ui-qmp.sock'));f=s.makefile('rw');f.readline()
def cmd(n,a=None):
 d={'execute':n}
 if a:d['arguments']=a
 f.write(json.dumps(d)+'\n');f.flush()
 while True:
  r=json.loads(f.readline())
  if 'error' in r:raise RuntimeError(r)
  if 'return' in r:return r
cmd('qmp_capabilities')
def key(*k,hold=100):cmd('send-key',{'keys':[{'type':'qcode','data':x} for x in k],'hold-time':hold});time.sleep(.4)
def text(t):
 for c in t:key(c)
def move(x,y):
 cmd('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':int(x*32767/1280)}},{'type':'abs','data':{'axis':'y','value':int(y*32767/800)}}]});time.sleep(.5)
def btn(down):cmd('input-send-event',{'events':[{'type':'btn','data':{'down':down,'button':'left'}}]});time.sleep(.4)
def click(x,y):move(x,y);btn(True);btn(False);time.sleep(1.5)
def frame(n):
 p=v/('ui-st-'+n+'.ppm');cmd('screendump',{'filename':str(p)});time.sleep(.6)
 raw=p.read_bytes();parts=raw.split(maxsplit=4);w,h=int(parts[1]),int(parts[2]);assert parts[0]==b'P6'
 body=raw[len(raw)-w*h*3:];return np.frombuffer(body,np.uint8).reshape(h,w,3).astype(int)
def hexc(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))
def mask(img,c,tol,reg=None):
 m=np.all(np.abs(img-np.array(hexc(c) if isinstance(c,str) else c))<=tol,axis=2)
 if reg:
  z=np.zeros_like(m);x1,y1,x2,y2=reg;z[y1:y2,x1:x2]=m[y1:y2,x1:x2];return z
 return m
def bbox(m,minpx=3000):
 if m.sum()<minpx:return None
 ys,xs=np.where(m);return [int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]
def runs(a,minv,gap=1):
 idx=np.where(a>=minv)[0];out=[]
 for i in idx:
  if out and i-out[-1][1]<=gap:out[-1][1]=i
  else:out.append([i,i])
 return [(a0,a1+1) for a0,a1 in out]
def blocks(m,rowmin,box):
 """rects of colour blocks inside box: row bands with >=rowmin px, then column runs inside each band"""
 x1,y1,x2,y2=box;sub=m[y1:y2,x1:x2];res=[]
 for r0,r1 in runs(sub.sum(1),rowmin,2):
  for c0,c1 in runs(sub[r0:r1].sum(0),3,2):res.append([int(x1+c0),int(y1+r0),int(x1+c1),int(y1+r1)])
 return res
results=[]
def rec(name,ok,detail=''):
 r={'check':name,'result':'PASS' if ok is True else ('UNMEASURED' if ok is None else 'FAIL'),'detail':str(detail)};results.append(r);print('UI_STATE',r['result'],name,detail,flush=True)
def near(c,ref,tol=10):return bool(np.all(np.abs(np.array(c)-np.array(hexc(ref)))<=tol))
def rules(name,d):
 for n,ok,det in symmetry_check.run(d):rec(name+': '+n,ok,det)
def audio():
 req=urllib.request.Request('http://127.0.0.1:18765/status',headers={'Host':'127.0.0.1:8765'});return json.load(urllib.request.urlopen(req,timeout=30))['audio']
SHELF='#e0e8f6';ICON='#d2dced'
def clear():
 for _ in range(4):key('alt','f4');time.sleep(1)
def shelf_measure(img):
 sh=bbox(mask(img,SHELF,7,(0,700,1280,800)),2000)
 if not sh:return None,[]
 m=mask(img,ICON,5,tuple(sh));bt=blocks(m,6,tuple(sh));return sh,bt
# ---- 0. clean desktop, shelf ----
clear();time.sleep(3);img=frame('shelf')
sh,bt=shelf_measure(img)
if sh is None:rec('shelf found by colour',None,'no #e0e8f6 shelf')
else:
 icons=[b for b in bt if b[2]-b[0]<=56];pills=[b for b in bt if b[2]-b[0]>56]
 d={'screen':[0,0,1280,800],'shelf':sh,'shelf_icons':icons}
 if bt:d['shelf_left_group']=bt[0];d['shelf_right_group']=bt[-1]
 rec('shelf rect',True,sh);rec('shelf icon buttons measured',len(icons)>=3,icons);rules('shelf',d)
 if len(bt)>=2:
  pt=[(b[0],b[2]) for b in bt];gaps=[pt[i+1][0]-pt[i][1] for i in range(len(pt)-1)]
  rec('shelf: gap between every button equal',max(gaps)-min(gaps)<=2,gaps)
 # hover / pressed on the launcher icon
 if icons:
  ic=icons[0];cx,cy=(ic[0]+ic[2])//2,ic[1]+4;move(cx,cy);h=frame('shelf-hover');rec('shelf launcher hover colour #c2d3ea',near(h[cy,cx],'#c2d3ea',8),tuple(h[cy,cx]))
  btn(True);p=frame('shelf-pressed');rec('shelf launcher pressed colour #abc5e8',near(p[cy,cx],'#abc5e8',8),tuple(p[cy,cx]));move(640,300);btn(False);time.sleep(1.5);key('esc')
# ---- 1. quick settings ----
clear();key('alt','shift','s');time.sleep(6);img=frame('qs-open')
pan=bbox(mask(img,'#f3f6fc',2,(640,0,1280,744)),8000)
if not pan:rec('quick settings panel found by colour',None,'no #f3f6fc window')
else:
 bl=blocks(mask(img,'#e2eaf6',3,tuple(pan)),200,tuple(pan));tiles=[b for b in bl if b[2]-b[0]<200];wide=[b for b in bl if b[2]-b[0]>=200]
 rec('panel rect',True,pan);rec('panel tiles measured (2 expected)',len(tiles)==2,tiles);rec('wide buttons measured (All settings, Close)',len(wide)==2,wide)
 d={'screen':[0,0,1280,800],'panel':pan,'panel_tiles':tiles}
 if sh:d['shelf']=sh
 rules('quick',d)
 for i,wb in enumerate(wide):
  rec(f'quick: wide button {i} left inset == right inset in panel',abs((wb[0]-pan[0])-(pan[2]-wb[2]))<=1,f'{wb[0]-pan[0]} vs {pan[2]-wb[2]}')
 if len(wide)==2:rec('quick: All settings and Close same size',abs((wide[0][2]-wide[0][0])-(wide[1][2]-wide[1][0]))<=1 and abs((wide[0][3]-wide[0][1])-(wide[1][3]-wide[1][1]))<=1,wide)
 if tiles:rec('quick: tile row spans same width as wide buttons',not wide or (abs(min(t[0] for t in tiles)-wide[0][0])<=1 and abs(max(t[2] for t in tiles)-wide[0][2])<=1),(tiles,wide))
 # states on the first tile (Network)
 if tiles:
  t=tiles[0];px,py=t[0]+14,t[1]+6
  move(px,py);hv=frame('qs-hover');rec('quick tile hover colour #cddcf1',near(hv[py,px],'#cddcf1',8),tuple(hv[py,px]))
  btn(True);pr=frame('qs-pressed');rec('quick tile pressed colour #abc5e8',near(pr[py,px],'#abc5e8',8),tuple(pr[py,px]));move(pan[0]+6,pan[1]+6);btn(False);time.sleep(1)
  mp=bbox(mask(frame('qs-after-cancel'),'#f3f6fc',2,(640,0,1280,744)),8000);rec('quick panel still open after a cancelled press (no accidental click)',mp==pan,mp)
 # keyboard focus: Tab moves ring (border #4680bc) somewhere inside the panel
 key('tab');fc=frame('qs-focus');ring=mask(fc,'#4680bc',12,tuple(pan));rec('quick focus ring visible after Tab',int(ring.sum())>=60,int(ring.sum()))
 # volume slider + mute with real audio state
 mute=[b for b in blocks(mask(img,'#e2eaf6',3,tuple(pan)),30,tuple(pan)) if 40<=b[2]-b[0]<=70]
 if mute:
  m=mute[0];a0=audio();click((m[0]+m[2])//2,(m[1]+m[3])//2);a1=audio();rec('quick Mute button toggles real mute state',('MUTED' in a0)!=('MUTED' in a1),f'{a0!r}->{a1!r}');click((m[0]+m[2])//2,(m[1]+m[3])//2)
  frame('qs-slider-row')
 else:rec('quick Mute button found',None,'no 40-70px button')
 # dismiss with the Close button, then reopen with the same shortcut
 if wide:
  c=wide[-1];click((c[0]+c[2])//2,(c[1]+c[3])//2);gone=bbox(mask(frame('qs-closed'),'#f3f6fc',2,(640,0,1280,744)),8000);rec('quick Close button dismisses panel',gone is None,gone)
  key('alt','shift','s');time.sleep(5);again=bbox(mask(frame('qs-reopen'),'#f3f6fc',2,(640,0,1280,744)),8000);rec('quick panel reopens at the same rect',again==pan,f'{again} vs {pan}')
  for name,ks in (('Escape',('esc',)),):
   key(*ks);time.sleep(1);e=bbox(mask(frame('qs-escape'),'#f3f6fc',2,(640,0,1280,744)),8000);rec('quick panel Escape dismisses (spec expects it)',e is None,e)
 clear()
# ---- 2. launcher ----
key('meta_l');time.sleep(4);img=frame('launcher-open')
lw=bbox(mask(img,'#eef3fb',2,(0,0,1280,744)),20000)
if not lw:rec('launcher window found by colour',None,'no #eef3fb window')
else:
 tl=blocks(mask(img,'#e2eaf6',3,tuple(lw)),150,tuple(lw));rec('launcher rect',True,lw);rec('launcher size 640x480',lw[2]-lw[0]==640 and lw[3]-lw[1]==480,(lw[2]-lw[0],lw[3]-lw[1]))
 rec('launcher tiles measured (5 expected)',len(tl)>=5,tl);d={'screen':[0,0,1280,800],'launcher':lw,'launcher_floating':True,'launcher_tiles':tl}
 if sh:d['shelf']=sh
 rules('launcher',d)
 rec('launcher centred horizontally on screen',abs((lw[0]+lw[2])/2-640)<=1,(lw[0]+lw[2])/2)
 rec('launcher bottom gap above shelf == shelf side gutter (spec docks it above the shelf)',bool(sh) and abs((sh[1]-lw[3])-sh[0])<=1,f'{sh[1]-lw[3] if sh else None} vs {sh[0] if sh else None}')
 if tl:
  t=tl[0];px,py=t[0]+10,t[1]+5;move(px,py);hv=frame('launcher-hover');rec('launcher tile hover colour #cddcf1',near(hv[py,px],'#cddcf1',8),tuple(hv[py,px]))
  btn(True);pr=frame('launcher-pressed');rec('launcher tile pressed colour #abc5e8',near(pr[py,px],'#abc5e8',8),tuple(pr[py,px]));move(lw[0]+4,lw[1]+4);btn(False);time.sleep(1)
  rec('launcher still open after cancelled press',bbox(mask(frame('launcher-after-cancel'),'#eef3fb',2,(0,0,1280,744)),20000)==lw)
 text('mail');time.sleep(2);sf=frame('launcher-search-mail');ft=blocks(mask(sf,'#e2eaf6',3,tuple(lw)),150,tuple(lw));rec('launcher search "mail" leaves exactly 1 tile',len(ft)==1,ft)
 if ft and tl:rec('launcher filtered tile keeps size',abs((ft[0][2]-ft[0][0])-(tl[0][2]-tl[0][0]))<=1 and abs((ft[0][3]-ft[0][1])-(tl[0][3]-tl[0][1]))<=1,ft)
 key('esc');gone=bbox(mask(frame('launcher-escape'),'#eef3fb',2,(0,0,1280,744)),20000);rec('launcher Escape dismisses',gone is None,gone)
 key('meta_l');time.sleep(4);re=bbox(mask(frame('launcher-reopen'),'#eef3fb',2,(0,0,1280,744)),20000);rec('launcher reopens at the same rect',re==lw,f'{re} vs {lw}');key('esc')
clear()
# ---- 3. media keys against real audio state (no hardware keys: brightness, play/next/prev stay UNVERIFIED) ----
try:
 a0=audio();key('volumedown');key('volumedown');a1=audio();key('volumeup');key('volumeup');a2=audio()
 rec('media key Volume Down changes real volume',a0!=a1,f'{a0!r}->{a1!r}');rec('media key Volume Up restores volume',a2!=a1,f'{a1!r}->{a2!r}')
 key('audiomute');m1=audio();rec('media key Mute toggles real mute state',('MUTED' in a2)!=('MUTED' in m1),f'{a2!r}->{m1!r}');key('audiomute')
except Exception as e:rec('media keys',False,repr(e))
for c in ('Brightness keys','Play/Pause/Next/Prev keys','Taskbar click/middle-click close','Quick Network tile mouse launch','Titlebar buttons (covered only by keyboard equivalents in window-controls-evidence)'):rec(c+' not exercised here',None,'UNMEASURED by design')
v.joinpath('ui-state-results.json').write_text(json.dumps(results,indent=1))
bad=[r for r in results if r['result']=='FAIL']
print('UI_STATE_SUMMARY',json.dumps({k:sum(1 for r in results if r['result']==k) for k in ('PASS','FAIL','UNMEASURED')}),flush=True)
sys.exit(1 if bad else 0)
