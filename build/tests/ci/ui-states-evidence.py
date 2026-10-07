#!/usr/bin/env python3
"""Interaction states + pixel-measured symmetry for the Kestrel shell, run in the disposable CI guest after window-controls-evidence.py.
Usage: ui-states-evidence.py VMDIR. Frames: ui-st-*.ppm. Results: ui-state-results.json. Exit 1 on any FAIL.
Elements are found by the CSS colours of the shipped stylesheets. A colour not found means UNMEASURED, never a pass.
State checks are relative (base > hover > pressed in brightness at a point away from the pointer and glyphs), because the pointer is drawn in screendumps."""
import json,socket,sys,time,urllib.request,os
from pathlib import Path
import numpy as np
here=Path(__file__).resolve().parent;sys.path.insert(0,str(here));sys.path.insert(0,str(here.parents[0]/'ui'))
import uimeasure as U
import symmetry_check
v=Path(sys.argv[1])
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
def key(*k):cmd('send-key',{'keys':[{'type':'qcode','data':x} for x in k],'hold-time':100});time.sleep(.4)
def text(t):
 for c in t:key(c)
def move(x,y):
 cmd('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':int(x*32767/1280)}},{'type':'abs','data':{'axis':'y','value':int(y*32767/800)}}]});time.sleep(.5)
def btn(down):cmd('input-send-event',{'events':[{'type':'btn','data':{'down':down,'button':'left'}}]});time.sleep(.4)
def click(x,y):move(x,y);btn(True);btn(False);time.sleep(1.5)
def frame(n):
 p=v/('ui-st-'+n+'.ppm');cmd('screendump',{'filename':str(p)});time.sleep(.8);return U.load_ppm(p)
results=[]
def rec(name,ok,detail=''):
 r={'check':name,'result':'UNMEASURED' if ok is None else ('PASS' if bool(ok) else 'FAIL'),'detail':str(detail)};results.append(r);print('UI_STATE',r['result'],name,detail,flush=True)
def rules(name,d):
 for n,ok,det in symmetry_check.run(d):rec(name+': '+n,ok,det)
def audio():
 req=urllib.request.Request('http://127.0.0.1:18765/status',headers={'Host':'127.0.0.1:8765'});return json.load(urllib.request.urlopen(req,timeout=30))['audio']
def clear():
 move(640,300)
 for _ in range(4):key('alt','f4');time.sleep(1)
def state_check(label,base,rect,wait_img_name,pressed=True):
 """hover then pressed (released off the element so nothing fires): brightness must fall base > hover > pressed at the top-centre sample"""
 sx,sy=(rect[0]+rect[2])//2,rect[1]+5
 move(rect[0]+12,rect[3]-10);hv=frame(wait_img_name+'-hover')
 btn(True);pr=frame(wait_img_name+'-pressed');move(rect[0]-30 if rect[0]>40 else rect[2]+30,rect[1]-30);btn(False);time.sleep(1)
 b,h,p=(U.luma(x[sy,sx]) for x in (base,hv,pr))
 rec(label+' hover is darker than idle',h<b-2,f'{b:.0f}->{h:.0f}')
 if pressed:rec(label+' pressed is darker than hover',p<h-2,f'{h:.0f}->{p:.0f}')
 else:rec(label+' pressed state',None,f'hover {h:.0f} pressed {p:.0f}; Waybar custom modules are GTK event boxes that never get :active, so no pressed styling is possible there (known limitation, buttons in the taskbar do)')
SHELF='#e0e8f6'
def shelf_report(img,label):
 sh=U.bbox(U.mask(img,SHELF,7,(0,700,1280,800)),2000)
 if sh is None:rec(label+': shelf found by colour',None,'no #e0e8f6 shelf');return None,[]
 els=U.shelf_elements(img,sh)
 rec(label+': shelf elements measured',len(els)>=5,els)
 cy=(sh[1]+sh[3])/2;sc=640
 rec(label+': every element is 40 px tall',all(abs((e[3]-e[1])-40)<=1 for e in els),[e[3]-e[1] for e in els])
 rec(label+': every element is vertically centred in the 48 px shelf',all(abs((e[1]+e[3])/2-cy)<=1 for e in els),[round((e[1]+e[3])/2-cy,1) for e in els])
 left=[e for e in els if e[2]<300];centre=[e for e in els if 300<=e[0] and e[2]<=980];right=[e for e in els if e[0]>980]
 icons=left+centre
 rec(label+': icon buttons (left+centre) are one size',len({(e[2]-e[0],e[3]-e[1]) for e in icons})==1,sorted({(e[2]-e[0],e[3]-e[1]) for e in icons}))
 if centre:
  c0,c1=min(e[0] for e in centre),max(e[2] for e in centre);rec(label+': centre group is centred on the screen (+-2 px)',abs((c0+c1)/2-sc)<=2,f'centre {(c0+c1)/2} vs {sc}')
 for gname,g in (('left',left),('centre',centre),('right',right)):
  gaps=[g[i+1][0]-g[i][2] for i in range(len(g)-1)]
  if gaps:rec(f'{label}: {gname} group gaps equal',max(gaps)-min(gaps)<=1,gaps)
 if left and right:rec(label+': left margin == right margin inside shelf',abs((left[0][0]-sh[0])-(sh[2]-right[-1][2]))<=1,f'{left[0][0]-sh[0]} vs {sh[2]-right[-1][2]}')
 if left and centre and right:
  gl=centre[0][0]-left[-1][2];gr=right[0][0]-centre[-1][2];rec(label+': space left of centre group vs right of it (informational, centre is pinned to screen centre)',True,f'{gl} vs {gr}')
 off=[]
 for e in els:
  g=U.glyph_box(img,e)
  if g:off.append((round((g[0]+g[2])/2-(e[0]+e[2])/2,1),round((g[1]+g[3])/2-(e[1]+e[3])/2,1)))
  else:off.append(None)
 rec(label+': glyph/text is centred inside its pill (+-2 px both axes)',all(o is not None and abs(o[0])<=2 and abs(o[1])<=2 for o in off),off)
 act=[e for e in centre if np.all(np.abs(img[(e[1]+e[3])//2,e[0]+2]-np.array(U.hexc('#a6c4eb')))<=14)] if centre else []
 if 'window open' in label:
  if not act:rec(label+': active taskbar button found by its #a6c4eb highlight',None,'none of the centre elements has the active fill')
  else:
   a=act[0];h=a[3]-a[1];w=a[2]-a[0];yy,xx=np.mgrid[0:h,0:w];circ=((xx-(w-1)/2)**2+(yy-(h-1)/2)**2)<=(min(w,h)/2-1.5)**2
   diff=np.abs(img[a[1]:a[3],a[0]:a[2]]-np.array(U.hexc('#a6c4eb'))).sum(2)>90;ink=diff&circ;ys,xs=np.where(ink)
   if len(xs)<50:rec(label+': active taskbar icon measurable',None,'no icon ink')
   else:
    ib=[a[0]+int(xs.min()),a[1]+int(ys.min()),a[0]+int(xs.max())+1,a[1]+int(ys.max())+1];dx=(ib[0]+ib[2])/2-(a[0]+a[2])/2;dy=(ib[1]+ib[3])/2-(a[1]+a[3])/2
    rec(label+': active taskbar icon is centred in its highlight (+-1 px both axes)',abs(dx)<=1 and abs(dy)<=1,f'highlight {a} icon {ib} offset ({dx:+.1f},{dy:+.1f})')
    rec(label+': active highlight is 40x40 and centred in the shelf',abs(w-40)<=1 and abs(h-40)<=1 and abs((a[1]+a[3])/2-cy)<=1,a)
    # the highlight is a rounded square with a 4 px margin around the 32 px icon: its fill must reach the circle edge equally on all four sides at the middle row/column
    mr=img[(a[1]+a[3])//2,a[0]-3:a[2]+3];mc=img[a[1]-3:a[3]+3,(a[0]+a[2])//2]
    fl=lambda arr:[i for i,c in enumerate(arr) if np.abs(c-np.array(U.hexc('#a6c4eb'))).sum()<=40]
    fr,fc=fl(mr),fl(mc)
    if fr and fc:
     L0,R0=fr[0]-3+a[0],fr[-1]+1-3+a[0];T0,B0=fc[0]-3+a[1],fc[-1]+1-3+a[1]
     rec(label+': highlight is symmetric around the icon (equal left/right and top/bottom margin, +-2 px)',abs((ib[0]-L0)-(R0-ib[2]))<=2 and abs((ib[1]-T0)-(B0-ib[3]))<=2,f'fill x {L0}..{R0}, y {T0}..{B0}; icon {ib}')
 d={'screen':[0,0,1280,800],'shelf':sh}
 rules(label,d)
 return sh,els
# ---- 0. shelf, empty desktop ----
clear();time.sleep(3);img0=frame('shelf');sh,els=shelf_report(img0,'shelf (no windows)')
launch=[e for e in els if e[2]<300]
if launch:state_check('shelf launcher button',img0,launch[0],'shelf',pressed=False);key('esc')
# ---- 0b. shelf with a window open ----
clear();key('meta_l','b');time.sleep(12);move(640,300);imgw=frame('shelf-window');shelf_report(imgw,'shelf (window open)')
clear()
# ---- 1. quick settings ----
key('alt','shift','s');time.sleep(6);img=frame('qs-open');L=U.qs_layout(img)
if not L or len(L['tiles'])!=2 or not L['mute'] or len(L['wide'])!=2:rec('quick settings layout found by colour',None,json.dumps(L))
else:
 pan,tiles,mute,wide=L['panel'],L['tiles'],L['mute'],L['wide']
 rec('panel rect',True,pan);rec('quick: 2 tiles, Mute, All settings, Close found',True,L)
 d={'screen':[0,0,1280,800],'panel':pan,'panel_tiles':tiles}
 if sh:d['shelf']=sh
 rules('quick',d)
 span=(tiles[0][0],tiles[1][2])
 rec('quick: tile row, Mute+slider row and wide buttons share the same left and right edges',all(abs(b[0]-span[0])<=1 for b in [mute]+wide) and all(abs(b[2]-span[1])<=1 for b in wide),f'tiles {span}, mute {mute[0]}, wide {[(b[0],b[2]) for b in wide]}')
 rec('quick: Mute width == tile width (aligned to tile column)',abs((mute[2]-mute[0])-(tiles[0][2]-tiles[0][0]))<=1,(mute[2]-mute[0],tiles[0][2]-tiles[0][0]))
 rec('quick: Mute, All settings and Close are all 48 px tall',all(abs((b[3]-b[1])-48)<=4 for b in [mute]+wide),[b[3]-b[1] for b in [mute]+wide])
 for i,wb in enumerate(wide):rec(f'quick: wide button {i} left inset == right inset in panel',abs((wb[0]-pan[0])-(pan[2]-wb[2]))<=1,f'{wb[0]-pan[0]} vs {pan[2]-wb[2]}')
 rec('quick: panel has no titlebar (top of panel is the Quick settings heading)',pan[3]-pan[1]<=420,pan)
 state_check('quick Network tile',img,tiles[0],'qs')
 time.sleep(1);rec('quick panel still open after a cancelled press (no accidental click)',U.qs_panel(frame('qs-after-cancel'))==pan)
 key('tab');fc=frame('qs-focus');ring=U.mask(fc,'#4680bc',12,tuple(pan));rec('quick focus ring visible after Tab',int(ring.sum())>=60,int(ring.sum()))
 a0=audio();click(*U.center(mute));a1=audio();rec('quick Mute button toggles real mute state',('MUTED' in a0)!=('MUTED' in a1),f'{a0!r}->{a1!r}');click(*U.center(mute))
 frame('qs-after-mute')
 click(*U.center(wide[1]));rec('quick Close button dismisses panel',U.qs_panel(frame('qs-closed')) is None)
 key('alt','shift','s');time.sleep(5);again=U.qs_panel(frame('qs-reopen'));rec('quick panel reopens at the same rect',again==pan,f'{again} vs {pan}')
 key('esc');time.sleep(1);rec('quick panel Escape dismisses',U.qs_panel(frame('qs-escape')) is None)
 key('alt','shift','s');time.sleep(5);click(*U.center(wide[0]));time.sleep(8);gone=U.qs_panel(frame('qs-all-settings'))
 rec('quick All settings closes the panel',gone is None,gone)
 try:
  pages=json.load(urllib.request.urlopen('http://127.0.0.1:19222/json'));rec('quick All settings opens the Settings page',any('#settings' in p.get('url','') for p in pages),[p.get('url','')[:60] for p in pages])
 except Exception as e:rec('quick All settings opens the Settings page',None,repr(e))
clear()
# ---- 2. launcher ----
key('meta_l');time.sleep(4);img=frame('launcher-open')
lw=U.bbox(U.mask(img,'#eef3fb',2,(0,0,1280,744)),20000)
if not lw:rec('launcher window found by colour',None,'no #eef3fb window')
else:
 white=U.bbox(U.mask(img,'#ffffff',2,(lw[0],lw[1],lw[2],lw[1]+104)),2000)
 top=(white[3]+4) if white else lw[1]+100
 non=~U.mask(img,'#eef3fb',3);tl=[t for t in U.blocks(non,1,(lw[0],top,lw[2],lw[3]-1),2,2) if t[2]-t[0]>=80 and t[3]-t[1]>=80]
 rec('launcher rect',True,lw);rec('launcher is 640x480 with no titlebar',(lw[2]-lw[0],lw[3]-lw[1])==(640,480),(lw[2]-lw[0],lw[3]-lw[1]))
 rec('launcher tiles measured (5 expected)',len(tl)==5,tl)
 row1=[t for t in tl if t[1]==min(x[1] for x in tl)] if tl else [];last=[t for t in tl if t not in row1]
 d={'screen':[0,0,1280,800],'launcher':lw,'launcher_floating':True,'launcher_tiles':row1}
 if sh:d['shelf']=sh
 rules('launcher',d)
 rec('launcher: all tiles are one size',len({(t[2]-t[0],t[3]-t[1]) for t in tl})==1,sorted({(t[2]-t[0],t[3]-t[1]) for t in tl}))
 rec('launcher is centred horizontally on the screen (+-1 px)',abs((lw[0]+lw[2])/2-640)<=1,(lw[0]+lw[2])/2)
 rec('launcher bottom gap above shelf == shelf side gutter',bool(sh) and abs((sh[1]-lw[3])-sh[0])<=1,f'{sh[1]-lw[3] if sh else None} vs {sh[0] if sh else None}')
 for t in last:rec('launcher: short last row is centred in the window',abs((t[0]+t[2])/2-(lw[0]+lw[2])/2)<=1,f'{(t[0]+t[2])/2} vs {(lw[0]+lw[2])/2}')
 if tl:
  state_check('launcher tile',img,tl[0],'launcher');rec('launcher still open after cancelled press',U.bbox(U.mask(frame('launcher-after-cancel'),'#eef3fb',2,(0,0,1280,744)),20000)==lw)
 if white:click((white[0]+white[2])//2,(white[1]+white[3])//2)   # focus the search field by mouse so typing cannot land on a tile
 text('mail');time.sleep(2);sf=frame('launcher-search-mail');ft=[t for t in U.blocks(~U.mask(sf,'#eef3fb',3),1,(lw[0],top,lw[2],lw[3]-1),2,2) if t[2]-t[0]>=80 and t[3]-t[1]>=80]
 rec('launcher search "mail" leaves exactly 1 tile',len(ft)==1,ft)
 if ft:rec('launcher filtered tile is centred',abs((ft[0][0]+ft[0][2])/2-(lw[0]+lw[2])/2)<=1,(ft[0][0]+ft[0][2])/2)
 key('esc');rec('launcher Escape dismisses',U.bbox(U.mask(frame('launcher-escape'),'#eef3fb',2,(0,0,1280,744)),20000) is None)
 key('meta_l');time.sleep(4);re=U.bbox(U.mask(frame('launcher-reopen'),'#eef3fb',2,(0,0,1280,744)),20000);rec('launcher reopens at the same rect',re==lw,f'{re} vs {lw}');key('esc')
clear()
# ---- 3. media keys ----
try:
 a0=audio();key('volumedown');key('volumedown');a1=audio();key('volumeup');key('volumeup');a2=audio()
 rec('media key Volume Down changes real volume',a0!=a1,f'{a0!r}->{a1!r}');rec('media key Volume Up restores volume',a2!=a1,f'{a1!r}->{a2!r}')
 key('audiomute');m1=audio();rec('media key Mute toggles real mute state',('MUTED' in a2)!=('MUTED' in m1),f'{a2!r}->{m1!r}');key('audiomute')
except Exception as e:rec('media keys',False,repr(e))
for c in ('Brightness keys','Play/Pause/Next/Prev keys'):rec(c+' not exercised here',None,'Requires physical brightness device or a test MPRIS player; not proven')
controls=json.loads(v.joinpath('control-results.json').read_text()) if v.joinpath('control-results.json').exists() else []
for label,needed in (
 ('Taskbar mouse activate/minimize/middle-close',('Taskbar browser mouse activation restores minimized target','Taskbar minimize keyboard makes current browser minimized','Taskbar middle-click closes that window')),
 ('Titlebar maximize/restore by mouse',('Titlebar maximize/restore button by mouse changes window state','Titlebar maximize/restore button toggles back'))):
 found=[next((r for r in controls if r['control']==n),None) for n in needed]
 rec(label,all(r and r['result']=='PASS' for r in found),'Referenced actual controls evidence: '+str(found))
v.joinpath('ui-state-results.json').write_text(json.dumps(results,indent=1))
print('UI_STATE_SUMMARY',json.dumps({k:sum(1 for r in results if r['result']==k) for k in ('PASS','FAIL','UNMEASURED')}),flush=True)
sys.exit(1 if any(r['result']=='FAIL' for r in results) else 0)
