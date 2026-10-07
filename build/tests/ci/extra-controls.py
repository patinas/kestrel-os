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
 entry=[w for w in words if search[0]<=int(w['left'])<search[2] and search[1]<=int(w['top'])<search[3] and w['text'].lower()==query]
 record('Launcher '+name+' search focus and query visible',bool(entry),search)
 if not entry:raise RuntimeError('Search text not visible; refusing tile click')
 needle='pwa' if name=='CI PWA' else name.lower()
 tiles=[word_rect(w) for w in words if w['text'].lower().strip('()')==needle and int(w['top'])>search[3]+24 and int(w['top'])<720]
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
  record('Launcher '+name+' mouse launch',bool(fresh) and (needle is None or any(needle in p['url'] for p in fresh)),[p['url'][:120] for p in fresh])
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

def advanced_interactive():
 password=''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(24))
 try:
  close_panels();cdp('Page.bringToFront');cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(3);cdp('Page.enable')
  # Click through the real checkbox and JS confirmation, then type only into getpass.
  point=js("(()=>{let e=document.querySelector('#advanced');e.scrollIntoView({block:'center'});let r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
  click_with_confirm(point);time.sleep(3)
  t=image_text('advanced-password-prompt')
  if 'password' not in t:raise RuntimeError('Password prompt not visible; no secret typed')
  text(password);key('ret');time.sleep(1)
  t=image_text('advanced-repeat-prompt')
  if 'repeat password' not in t:raise RuntimeError('Repeat getpass prompt not visible; second secret not typed')
  text(password);key('ret');time.sleep(3)
  proof=probe('/advanced-check',{'password':password})
  record('Advanced real interactive password enables correct sudo and rejects wrong sudo',proof['enabled'] and proof['password_present'] and proof['correct_sudo'] and proof['wrong_sudo_rejected'])
  # Close the setup terminal, then use the Settings Open terminal button.
  key('alt','f4');cdp('Page.bringToFront');js('refresh()');time.sleep(1)
  before=probe()['processes']['foot'];click('#terminal');time.sleep(2)
  record('Settings enabled Terminal mouse opens foot',probe()['processes']['foot']>before);shot('extra-advanced-terminal');key('alt','f4');cdp('Page.bringToFront');click('#advanced');time.sleep(3)
  off=probe('/advanced-check',{'password':password})
  record('Advanced UI disable removes password and revokes sudo',not off['enabled'] and not off['password_present'] and not off['correct_sudo']);js('refresh()')
  record('Advanced disabled Terminal button unavailable again',js("document.querySelector('#terminal').disabled"))
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

def browser_cdp(method,params):
 # PWA commands belong to the browser endpoint, not the page session.
 info=json.load(urllib.request.urlopen('http://127.0.0.1:19222/json/version',timeout=10))
 url=info['webSocketDebuggerUrl'].replace('localhost:9222','127.0.0.1:19222').replace('127.0.0.1:9222','127.0.0.1:19222')
 conn=websocket.create_connection(url,origin='http://localhost',timeout=25)
 try:
  conn.send(json.dumps({'id':1,'method':method,'params':params}))
  while True:
   reply=json.loads(conn.recv())
   if reply.get('id')==1:
    print('PWA_REPLY',method,json.dumps(reply)[:700],flush=True)
    if 'error' in reply:raise RuntimeError(reply['error'])
    return reply.get('result',{})
 finally:conn.close()
def pwa_install():
 manifest='http://127.0.0.1:8766/pwa/';installed=False
 close_panels()
 try:
  cdp('Page.navigate',{'url':manifest});time.sleep(3)
  print('PWA_INSTALLABILITY',json.dumps(cdp('Page.getInstallabilityErrors')),flush=True)
  print('PWA_MANIFEST',json.dumps(cdp('Page.getAppManifest'))[:700],flush=True)
  browser_cdp('PWA.install',{'manifestId':manifest,'installUrlOrBundleUrl':manifest});installed=True;time.sleep(4)
  launch=browser_cdp('PWA.launch',{'manifestId':manifest});time.sleep(3)
  p=next(p for p in pages_now() if p['id']==launch['targetId']);connect_page(p);cdp('Page.bringToFront')
  record('PWA installs and opens standalone through Chrome subsystem',js("matchMedia('(display-mode: standalone)').matches && document.title==='Kestrel CI PWA'"));shot('extra-pwa-installed');cdp('Page.close');time.sleep(2)
  connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
  old={p['id'] for p in pages_now()};lw,tiles=launcher_tiles('CI PWA')
  record('Installed PWA has launcher tile',len(tiles)==1)
  if len(tiles)!=1:raise RuntimeError('PWA launcher tile missing')
  guest_click(*uim.center(tiles[0]));time.sleep(4);fresh=next(p for p in pages_now() if p['id'] not in old and p['url'].startswith(manifest));connect_page(fresh)
  record('PWA mouse relaunch from Kestrel launcher remains standalone',js("matchMedia('(display-mode: standalone)').matches"));shot('extra-pwa-relaunched')
 finally:
  if installed:browser_cdp('PWA.uninstall',{'manifestId':manifest})
  close_panels();connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
safe_section('PWA subsystem install and launcher relaunch',pwa_install)
