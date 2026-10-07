"""Executed in window-controls-evidence.py's namespace, using its live QMP/CDP session."""
import subprocess,secrets

def probe(path='/status',data=None):
 body=json.dumps(data).encode() if data is not None else None
 req=urllib.request.Request('http://127.0.0.1:18766'+path,data=body,headers={'Content-Type':'application/json'})
 answer=json.load(urllib.request.urlopen(req,timeout=90))
 if 'error' in answer:raise RuntimeError('Probe '+answer['error']+': '+answer.get('message',''))
 return answer
def image_text(name):
 park_pointer();shot('extra-'+name)
 r=subprocess.run(['tesseract',str(v/('ui-extra-'+name+'.ppm')),'stdout'],capture_output=True,text=True,timeout=25)
 if r.returncode:raise RuntimeError('OCR failed')
 return r.stdout.lower()
def safe_section(name,fn):
 try:fn()
 except Exception as e:
  record(name,False,type(e).__name__+': '+str(e)[:250])
  if 'signature' in name.lower():
   try:print('PROBE_DIAGNOSTIC',json.dumps(probe('/diagnostics')),flush=True)
   except Exception as diagnostic:print('PROBE_DIAGNOSTIC_ERROR',type(diagnostic).__name__,flush=True)
def connect_page(p):
 global ws,page
 try:ws.close()
 except Exception:pass
 page=p
 ws=websocket.create_connection(p['webSocketDebuggerUrl'].replace('localhost:9222','127.0.0.1:19222').replace('127.0.0.1:9222','127.0.0.1:19222'),origin='http://localhost',timeout=60)
def pages_now():return [p for p in json.load(urllib.request.urlopen('http://127.0.0.1:19222/json',timeout=10)) if p['type']=='page']
def ocr_words(name):
 park_pointer();shot('extra-'+name)
 r=subprocess.run(['tesseract',str(v/('ui-extra-'+name+'.ppm')),'stdout','tsv'],capture_output=True,text=True,timeout=25)
 if r.returncode:raise RuntimeError('TSV OCR failed')
 import csv,io
 return [w for w in csv.DictReader(io.StringIO(r.stdout),delimiter='\t') if w.get('text','').strip() and float(w.get('conf',-1))>=35]
def word_rect(w):
 x,y,ww,hh=(int(w[k]) for k in ('left','top','width','height'));return [x,y,x+ww,y+hh]
def close_panels():
 probe('/panels-close',{});time.sleep(1)
 counts=probe()['processes']
 if counts['kestrel-launcher'] or counts['kestrel-quick-settings']:raise RuntimeError('Panel processes did not close')
 park_pointer();shot('extra-panels-closed')
def launcher_visible(name):
 words=ocr_words(name)
 tiles=[w for w in words if w['text'].lower().strip('()') in ('browser','mail','video','settings','terminal') and 250<int(w['top'])<720]
 return len(tiles)>=4,tiles
def launcher_tiles(name):
 close_panels();key('meta_l');time.sleep(3)
 words=ocr_words('launcher-'+name+'-before')
 # Find the focused entry by its white horizontal fill inside the actual
 # launcher content. Page whites outside this band are excluded.
 im=uim.load_ppm(v/('ui-extra-launcher-'+name+'-before.ppm'))
 title=next((w for w in words if w['text'].lower()=='apps' and 150<int(w['top'])<600),None)
 if not title:raise RuntimeError('Launcher title not visible')
 sy=int(title['top'])+25
 heading=[w for w in words if w['text'].lower() in ('kestrel','apps') and abs(int(w['top'])-int(title['top']))<=5]
 cx=(min(int(w['left']) for w in heading)+max(int(w['left'])+int(w['width']) for w in heading))//2
 search=uim.bbox(uim.mask(im,'#ffffff',4,(max(0,cx-310),sy,min(1280,cx+310),min(sy+60,720))),8000)
 if not search:raise RuntimeError('Launcher search entry not visible')
 guest_click(*uim.center(search));key('ctrl','a')
 query='ci' if name=='CI PWA' else name.lower()
 text(query);time.sleep(2)
 words=ocr_words('launcher-'+name+'-filtered')
 # Query text plus caret is unreliable OCR. Prove the search produced one
 # tile with the exact requested label and nonempty entry ink instead.
 needle='pwa' if name=='CI PWA' else name.lower()
 tiles=[word_rect(w) for w in words if w['text'].lower().strip('()')==needle and int(w['top'])>search[3]+24 and int(w['top'])<720 and search[0]<=int(w['left'])<search[2]]
 im=uim.load_ppm(v/('ui-extra-launcher-'+name+'-filtered.ppm'))
 import numpy as np
 ink=int((np.max(im[search[1]+10:search[3]-10,search[0]+36:search[0]+200],axis=2)<160).sum())
 record('Launcher '+name+' search focus and query visible',len(tiles)==1 and ink>=15,{'entryInk':ink,'filteredTile':tiles})
 if len(tiles)!=1 or ink<15:raise RuntimeError('Filtered tile or entry ink absent; refusing tile click')
 return search,tiles

def shelf_launcher():
 close_panels();park_pointer();shot('extra-shelf-before');im=uim.load_ppm(v/'ui-extra-shelf-before.ppm');els=uim.shelf_elements(im,uim.shelf_band(im))
 guest_click(*uim.center(next(e for e in els if e[2]<300)));time.sleep(2)
 visible,tiles=launcher_visible('shelf-launcher')
 record('Shelf launcher mouse opens visible launcher',probe()['processes']['kestrel-launcher']==1 and visible,[word_rect(w) for w in tiles]);close_panels()
def shelf_clock():
 close_panels();park_pointer();shot('extra-clock-before');im=uim.load_ppm(v/'ui-extra-clock-before.ppm');els=uim.shelf_elements(im,uim.shelf_band(im))
 guest_click(*uim.center(els[-1]));time.sleep(3);lay=quick_layout('extra-shelf-clock')
 record('Shelf clock mouse opens visible Quick settings',bool(lay),lay);close_panels()
def quick_close():
 close_panels();lay=open_quick('extra-quick-close-before')
 guest_click(*uim.center(lay['wide'][1]));park_pointer();shot('extra-quick-closed')
 record('Quick panel Close mouse removes visible panel',uim.qs_panel(uim.load_ppm(v/'ui-extra-quick-closed.ppm')) is None and probe()['processes']['kestrel-quick-settings']==0)
def quick_network():
 close_panels();lay=open_quick('extra-quick-network-before');before=probe()['processes']['kestrel-network']
 guest_click(*uim.center(lay['tiles'][0]));t=image_text('quick-network');after=probe()['processes']['kestrel-network']
 record('Quick Network mouse opens visible no-adapter window',after>before and 'wi-fi' in t and 'adapter' in t,{'processes':[before,after],'text':t[:300]});key('alt','f4');close_panels()
for name,fn in [('Shelf launcher mouse',shelf_launcher),('Shelf clock mouse',shelf_clock),('Quick Close mouse',quick_close),('Quick Network mouse',quick_network)]:safe_section(name,fn)

def launch_tile(name,needle):
  old={p['id'] for p in pages_now()};lw,tiles=launcher_tiles(name)
  if len(tiles)!=1:raise RuntimeError('Filtered '+name+' tile count '+str(len(tiles)))
  guest_click(*uim.center(tiles[0]));time.sleep(6)
  park_pointer();shot('extra-tile-dismiss-'+name.lower())
  record('Launcher '+name+' tile dismisses launcher',probe()['processes']['kestrel-launcher']==0)
  fresh=[p for p in pages_now() if p['id'] not in old and not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))]
  from urllib.parse import urlparse
  def destination(url):
   if name=='Mail':
    u=urlparse(url);return u.hostname in ('mail.google.com','accounts.google.com') or (u.hostname=='workspace.google.com' and '/gmail/' in u.path)
   return needle is None or needle in url
  record('Launcher '+name+' mouse launch',bool(fresh) and any(destination(p['url']) for p in fresh),[p['url'][:180] for p in fresh])
  park_pointer();shot('extra-tile-'+name.lower())
  if fresh:
   connect_page(fresh[0]);cdp('Page.bringToFront')
   if name in ('Settings','Terminal'):record('Launcher '+name+' shows Settings with advanced access off',js("document.querySelector('#settings').open && document.querySelector('#terminal').disabled"))
   cdp('Page.close');time.sleep(2);connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
for name,needle in [('Browser',None),('Mail','mail.google.com'),('Video','youtube.com'),('Settings','#settings'),('Terminal','#settings')]:
 safe_section('Launcher '+name+' tile mouse effects',lambda n=name,u=needle:launch_tile(n,u))

def native_dialogs():
 wi=cdp('Browser.getWindowForTarget');cdp('Browser.setWindowBounds',{'windowId':wi['windowId'],'bounds':{'windowState':'maximized'}})
 cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(4);cdp('Page.bringToFront')
 for name,words in [('network',('wi-fi','adapter')),('bluetooth',('bluetooth','adapter'))]:
  before=probe()['processes']['kestrel-'+name]
  click('button[onclick="callBridge(\'/'+name+'\')"]');time.sleep(3);t=image_text('settings-'+name)
  after=probe()['processes']['kestrel-'+name]
  record('Settings '+name+' visible no-adapter dialog',after>before and all(w in t for w in words),{'processes':[before,after],'text':t[:300]})
  key('alt','f4');time.sleep(2)
  record('Settings '+name+' dialog closes and returns',probe()['processes']['kestrel-'+name]==before and settings_visible('extra-'+name+'-closed'))
safe_section('Settings native dialogs',native_dialogs)

def taskbar_activate():
 close_panels();cdp('Page.bringToFront');cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(3)
 target=page['id'];info=cdp('Browser.getWindowForTarget',{'targetId':target})
 record('Taskbar target visible before minimize',settings_visible('extra-taskbar-before'))
 park_pointer();shot('extra-taskbar-titlebar');hit=uim.titlebar_maximize(uim.load_ppm(v/'ui-extra-taskbar-titlebar.ppm'),info['bounds'])
 if not hit:raise RuntimeError('No titlebar triplet for minimize click')
 guest_click(*uim.center(hit['glyphs'][0]));time.sleep(2)
 hidden=not settings_visible('extra-taskbar-minimized')
 record('Taskbar minimize mouse hides current browser pixels',hidden,{'targetId':target,'glyph':hit['glyphs'][0]})
 if not hidden:raise RuntimeError('Target still visible after minimize')
 im=uim.load_ppm(v/'ui-extra-taskbar-minimized.ppm');els=uim.shelf_elements(im,uim.shelf_band(im));buttons=[e for e in els if 300<=e[0] and e[2]<=980][2:]
 found=False
 for i,e in enumerate(buttons):
  guest_click(*uim.center(e))
  if settings_visible('extra-taskbar-activate-'+str(i)):found=True;break
 record('Taskbar browser mouse activation restores minimized target',found and cdp('Browser.getWindowForTarget',{'targetId':target})['windowId']==info['windowId'],{'targetId':target,'windowId':info['windowId']})
safe_section('Taskbar activate/minimize',taskbar_activate)

def click_with_confirm(point):
 # Arm the same target before QMP clicking. QMP is not blocked by the
 # synchronous JS dialog; read its opening event before sending accept.
 cdp('Page.enable');ws.settimeout(15);guest_click(*point)
 try:
  while True:
   event=json.loads(ws.recv())
   if event.get('method')=='Page.javascriptDialogOpening':
    print('DIALOG_OPEN',json.dumps({'type':event['params'].get('type'),'targetId':page['id']}),flush=True)
    if event['params'].get('type')!='confirm':raise RuntimeError('Unexpected dialog type')
    cdp('Page.handleJavaScriptDialog',{'accept':True});return
 finally:ws.settimeout(60)

def terminal_prompt(name):
 park_pointer();shot('extra-'+name)
 im=uim.load_ppm(v/('ui-extra-'+name+'.ppm'))
 # Terminal has a large #242424 content rectangle; row support excludes
 # dark page text and keeps the OCR inside the real terminal.
 import numpy as np
 m=uim.mask(im,'#242424',12,(0,100,1280,720));rows=np.where(m.sum(1)>500)[0]
 if len(rows)<150:raise RuntimeError('Terminal content rectangle absent')
 cols=np.where(m[rows].sum(0)>120)[0]
 if len(cols)<500:raise RuntimeError('Terminal width not measurable')
 x=int(cols.min());y=int(rows.min());right=int(cols.max()+1)
 crop=v/(name+'-crop.png')
 subprocess.run(['convert',str(v/('ui-extra-'+name+'.ppm')),'-crop',str(right-x)+'x100+'+str(x)+'+'+str(y),'-resize','400%','-negate',str(crop)],check=True,capture_output=True)
 r=subprocess.run(['tesseract',str(crop),'stdout','--psm','6'],capture_output=True,text=True,timeout=20)
 if r.returncode:raise RuntimeError('Terminal crop OCR failed')
 return r.stdout.lower()

def advanced_interactive():
 password=''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(24))
 try:
  print('ADVANCED_OWNERSHIP',json.dumps(probe().get('ownership',{})),flush=True)
  close_panels();cdp('Page.bringToFront');cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(3);cdp('Page.enable')
  # Click through the real checkbox and JS confirmation, then type only into getpass.
  point=js("(()=>{let e=document.querySelector('#advanced');e.scrollIntoView({block:'center'});let r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
  # QMP uses full-screen coordinates, unlike DOM viewport coordinates.
  bb=settings_visible('extra-advanced-before')
  if not bb:raise RuntimeError('Settings not visible before Advanced')
  pixel=uim.settings_card(uim.load_ppm(v/'ui-extra-advanced-before.ppm'))
  dom=js("(()=>{let r=document.querySelector('#settings').getBoundingClientRect();return [r.x,r.y]})()")
  point=[point[0]+pixel[0]-dom[0],point[1]+pixel[1]-dom[1]]
  print('DIALOG_CLICK',json.dumps({'targetId':page['id'],'screenPoint':point,'offset':[pixel[0]-dom[0],pixel[1]-dom[1]]}),flush=True)
  click_with_confirm(point);time.sleep(3)
  t=terminal_prompt('advanced-password-prompt')
  if not ('advanced sudo password' in t and '12 characters' in t and probe()['processes']['foot']>=1):raise RuntimeError('Exact getpass prompt not visible; no secret typed')
  text(password);key('ret');time.sleep(1)
  t=terminal_prompt('advanced-repeat-prompt')
  if 'repeat password' not in t:raise RuntimeError('Repeat getpass prompt not visible; second secret not typed')
  text(password);key('ret');time.sleep(3)
  proof=probe('/advanced-check',{'password':password})
  record('Advanced real interactive password enables correct sudo and rejects wrong sudo',proof['enabled'] and proof['password_present'] and proof['correct_sudo'] and proof['wrong_sudo_rejected'])
  # Do not Alt-F4 an assumed terminal: if absent that closes Settings.
  probe('/terminals-close',{});time.sleep(1);cdp('Page.bringToFront')
  cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(2);js('refresh()');time.sleep(1)
  enabled=probe()['enabled'];ui=js("document.querySelector('#advanced').checked && !document.querySelector('#terminal').disabled")
  print('ADVANCED_STATE',json.dumps({'phase':'before-terminal','enabled':enabled,'uiEnabled':ui,'targetId':page['id']}),flush=True)
  record('Advanced enabled state survives setup-terminal close',enabled and ui)
  if not enabled or not ui:raise RuntimeError('Enabled flag/UI missing before terminal click')
  before=probe()['processes']['foot'];click('#terminal');time.sleep(2)
  opened=probe()['processes']['foot']>before
  record('Settings enabled Terminal mouse opens foot',opened);shot('extra-advanced-terminal')
  probe('/terminals-close',{});time.sleep(1);cdp('Page.bringToFront');js('refresh()')
  # Observe the real checkbox change and scoped disable response without
  # logging the bridge token, headers, password or unrelated traffic.
  js("""(()=>{window.__disableEvidence={changes:[],started:0,responses:[],errors:[]};let e=document.querySelector('#advanced');e.addEventListener('change',()=>window.__disableEvidence.changes.push(e.checked));let f=window.fetch;window.fetch=async(...a)=>{let disable=a[0]==='/disable';if(disable)window.__disableEvidence.started++;try{let r=await f(...a);if(disable)window.__disableEvidence.responses.push(r.status);return r}catch(e){if(disable)window.__disableEvidence.errors.push(e.name);throw e}}})()""")
  point=js("(()=>{let e=document.querySelector('#advanced');e.scrollIntoView({block:'center'});let r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
  if not settings_visible('extra-advanced-disable-before'):raise RuntimeError('Settings absent before disable')
  pixel=uim.settings_card(uim.load_ppm(v/'ui-extra-advanced-disable-before.ppm'))
  dom=js("(()=>{let r=document.querySelector('#settings').getBoundingClientRect();return [r.x,r.y]})()")
  screen=[point[0]+pixel[0]-dom[0],point[1]+pixel[1]-dom[1]]
  print('ADVANCED_STATE',json.dumps({'phase':'disable-before','enabled':probe()['enabled'],'checked':js("document.querySelector('#advanced').checked"),'screenPoint':screen}),flush=True)
  guest_click(*screen)
  for _ in range(12):
   if not probe()['enabled']:break
   time.sleep(1)
  off=probe('/advanced-check',{'password':password});js('refresh()');time.sleep(1)
  ui=js("({checked:document.querySelector('#advanced').checked,terminalDisabled:document.querySelector('#terminal').disabled,status:document.querySelector('#state').textContent,evidence:window.__disableEvidence})")
  detail={'enabled':off['enabled'],'passwordPresent':off['password_present'],'correctSudo':off['correct_sudo'],'wrongSudoRejected':off['wrong_sudo_rejected'],'ui':ui}
  print('ADVANCED_STATE',json.dumps({'phase':'disable-after',**detail}),flush=True);shot('extra-advanced-disable-after')
  record('Advanced UI disable removes password and revokes sudo',not off['enabled'] and not off['password_present'] and not off['correct_sudo'],detail)
  record('Advanced disabled Terminal button unavailable again',ui['terminalDisabled'] and not ui['checked'],ui)

 finally:
  # Accept/cancel only on the original target; do not replay a mutating click.
  try:cdp('Page.handleJavaScriptDialog',{'accept':False})
  except Exception:pass
  probe('/advanced-cleanup',{});password=None
  # Recover a browser target even if terminal focus or a failed check interrupted the section.
  connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
safe_section('Advanced interactive enable/disable',advanced_interactive)

def signatures():
 close_panels();proof=probe('/signature-check',{})
 record('Signed fixture accepted by real minisign',proof['signed_fixture_verified'])
 record('Real updater rejects tampered signature before entry changes',proof['real_updater_rejected_tamper'] and proof['entries_unchanged'],proof['scope'])
safe_section('Update signature/tamper live VM',signatures)

def menu_click(needles,name):
 words=ocr_words(name)
 matches=[w for w in words if any(n in w['text'].lower() for n in needles) and int(w['left'])>(300 if name=='pwa-install-confirm' else 600)]
 if not matches:raise RuntimeError('Menu item not visible: '+str(needles))
 # Select the first item in visual order; subsequent frames prove next menu.
 item=min(matches,key=lambda w:int(w['top']));guest_click(*uim.center(word_rect(item)))
def pwa_confirm_install():
 park_pointer();shot('extra-pwa-install-confirm')
 # Only the lower action row of Chrome's centred install dialog. Excludes
 # heading at y140 and address-bar Install at y89.
 crop=v/'pwa-confirm-buttons.png'
 subprocess.run(['convert',str(v/'ui-extra-pwa-install-confirm.ppm'),'-crop','450x100+415+215','-resize','300%',str(crop)],check=True,capture_output=True)
 import csv,io
 r=subprocess.run(['tesseract',str(crop),'stdout','--psm','6','tsv'],capture_output=True,text=True,timeout=20)
 found=[w for w in csv.DictReader(io.StringIO(r.stdout),delimiter='\t') if w.get('text','').lower()=='install' and float(w['conf'])>=50]
 if len(found)!=1:raise RuntimeError('Install confirmation action not unique')
 w=found[0];point=[415+(int(w['left'])+int(w['width'])/2)/3,215+(int(w['top'])+int(w['height'])/2)/3]
 print('PWA_CONFIRM_CLICK',json.dumps(point),flush=True);guest_click(*point)

def pwa_install():
 manifest='http://127.0.0.1:8766/pwa/';installed=False
 close_panels()
 try:
  cdp('Page.navigate',{'url':manifest});time.sleep(3)
  print('PWA_INSTALLABILITY',json.dumps(cdp('Page.getInstallabilityErrors')),flush=True)
  print('PWA_MANIFEST',json.dumps(cdp('Page.getAppManifest'))[:700],flush=True)
  # PWA experimental CDP is absent in this Chrome. Exercise the real menu.
  cdp('Page.bringToFront');time.sleep(1)
  key('esc');park_pointer();shot('extra-pwa-address-install')
  crop=v/'pwa-address.png'
  subprocess.run(['convert',str(v/'ui-extra-pwa-address-install.ppm'),'-crop','250x45+950+65','-resize','300%',str(crop)],check=True,capture_output=True)
  import csv,io
  r=subprocess.run(['tesseract',str(crop),'stdout','--psm','6','tsv'],capture_output=True,text=True,timeout=20)
  words=[]
  for w in csv.DictReader(io.StringIO(r.stdout),delimiter='\t'):
   if w.get('text','').strip():
    w['left']=str(950+int(w['left'])//3);w['top']=str(65+int(w['top'])//3);w['width']=str(max(1,int(w['width'])//3));w['height']=str(max(1,int(w['height'])//3));words.append(w)
  install=[w for w in words if w['text'].lower()=='install' and 60<=int(w['top'])<=105 and 900<=int(w['left'])<1200]
  if len(install)!=1:raise RuntimeError('Address-bar Install button not unambiguously visible')
  guest_click(*uim.center(word_rect(install[0])));time.sleep(1)
  pwa_confirm_install();time.sleep(5)
  after=image_text('pwa-after-confirm')
  record('PWA Install confirmation dialog disappears', 'install app' not in after)
  if 'install app' in after:raise RuntimeError('Install dialog still visible after click')
  candidates=[p for p in pages_now() if p['url'].startswith(manifest)]
  print('PWA_TARGETS',json.dumps([{'id':p['id'],'url':p['url']} for p in candidates]),flush=True)
  installed=False
  for candidate in candidates:
   connect_page(candidate)
   standalone=bool(js("matchMedia('(display-mode: standalone)').matches && document.title==='Kestrel CI PWA'"))
   print('PWA_STANDALONE',candidate['id'],standalone,flush=True)
   if standalone:installed=True;break
  if not installed:raise RuntimeError('No standalone PWA among manifest targets (including reused IDs)')
  cdp('Page.bringToFront')
  record('PWA installs and opens standalone through Chrome subsystem',installed);shot('extra-pwa-installed');cdp('Page.close');time.sleep(2)
  connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
  old={p['id'] for p in pages_now()};lw,tiles=launcher_tiles('CI PWA')
  record('Installed PWA has launcher tile',len(tiles)==1)
  if len(tiles)!=1:raise RuntimeError('PWA launcher tile missing')
  guest_click(*uim.center(tiles[0]));time.sleep(4);candidates=[p for p in pages_now() if p['url'].startswith(manifest)]
  relaunched=False
  for candidate in candidates:
   connect_page(candidate)
   if js("matchMedia('(display-mode: standalone)').matches"):relaunched=True;break
  if not relaunched:raise RuntimeError('No standalone target after launcher click')
  record('PWA mouse relaunch from Kestrel launcher remains standalone',js("matchMedia('(display-mode: standalone)').matches"));shot('extra-pwa-relaunched')
 finally:
  if installed:
   # Disposable profile expires with the VM; do not call unsupported PWA cleanup.
   print('PWA_CLEANUP','Fixture remains only in disposable VM profile',flush=True)
  close_panels();connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
safe_section('PWA subsystem install and launcher relaunch',pwa_install)
