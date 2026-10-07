"""Executed in window-controls-evidence.py's namespace, using its live QMP/CDP session."""
import subprocess,secrets

def probe(path='/status',data=None):
 body=json.dumps(data).encode() if data is not None else None
 req=urllib.request.Request('http://127.0.0.1:18766'+path,data=body,headers={'Content-Type':'application/json'})
 return json.load(urllib.request.urlopen(req,timeout=90))
def image_text(name):
 park_pointer();shot('extra-'+name)
 r=subprocess.run(['tesseract',str(v/('ui-extra-'+name+'.ppm')),'stdout'],capture_output=True,text=True,timeout=25)
 if r.returncode:raise RuntimeError('OCR failed')
 return r.stdout.lower()
def safe_section(name,fn):
 try:fn()
 except Exception as e:record(name,False,type(e).__name__+': '+str(e)[:250])
def connect_page(p):
 global ws,page
 try:ws.close()
 except Exception:pass
 page=p
 ws=websocket.create_connection(p['webSocketDebuggerUrl'].replace('localhost:9222','127.0.0.1:19222').replace('127.0.0.1:9222','127.0.0.1:19222'),origin='http://localhost',timeout=60)
def pages_now():return [p for p in json.load(urllib.request.urlopen('http://127.0.0.1:19222/json',timeout=10)) if p['type']=='page']
def launcher_tiles(name):
 key('meta_l');time.sleep(3)
 if name:text(name.lower().replace(' ','') if name!='CI PWA' else 'ci');time.sleep(2)
 park_pointer();shot('extra-launcher-'+name)
 im=uim.load_ppm(v/('ui-extra-launcher-'+name+'.ppm'));lw=uim.bbox(uim.mask(im,'#eef3fb',3,(0,0,1280,744)),20000)
 if not lw:raise RuntimeError('Launcher absent')
 tiles=[t for t in uim.blocks(uim.mask(im,'#e2eaf6',8),40,(lw[0]+20,lw[1]+110,lw[2]-20,lw[3]-20),3,3) if t[2]-t[0]>=80 and t[3]-t[1]>=80]
 return lw,tiles

def shelf_effects():
 park_pointer();shot('extra-shelf-before');im=uim.load_ppm(v/'ui-extra-shelf-before.ppm');sh=uim.shelf_band(im);els=uim.shelf_elements(im,sh)
 guest_click(*uim.center(next(e for e in els if e[2]<300)))
 park_pointer();shot('extra-shelf-launcher');lw=uim.bbox(uim.mask(uim.load_ppm(v/'ui-extra-shelf-launcher.ppm'),'#eef3fb',3,(0,0,1280,744)),20000)
 record('Shelf launcher mouse opens visible launcher',bool(lw) and 632<=lw[2]-lw[0]<=648,lw);key('esc')
 guest_click(*uim.center(els[-1]));lay=quick_layout('extra-shelf-clock')
 record('Shelf clock mouse opens visible Quick settings',bool(lay),lay)
 if not lay:raise RuntimeError('No Quick settings after clock click')
 guest_click(*uim.center(lay['wide'][1]));park_pointer();shot('extra-quick-closed')
 record('Quick panel Close mouse removes visible panel',uim.qs_panel(uim.load_ppm(v/'ui-extra-quick-closed.ppm')) is None)
 lay=open_quick('extra-quick-network-before');before=probe()['processes']['kestrel-network']
 guest_click(*uim.center(lay['tiles'][0]));t=image_text('quick-network');after=probe()['processes']['kestrel-network']
 record('Quick Network mouse opens visible no-adapter window',after>before and 'wi-fi' in t and 'adapter' in t,{'processes':[before,after],'text':t[:300]});key('alt','f4');key('esc')
safe_section('Shelf and Quick mouse effects',shelf_effects)

def launch_tiles():
 for name,needle in [('Browser',None),('Mail','mail.google.com'),('Video','youtube.com'),('Settings','#settings'),('Terminal','#settings')]:
  old={p['id'] for p in pages_now()};lw,tiles=launcher_tiles(name)
  if len(tiles)!=1:raise RuntimeError('Filtered '+name+' tile count '+str(len(tiles)))
  guest_click(*uim.center(tiles[0]));time.sleep(6)
  park_pointer();shot('extra-tile-dismiss-'+name.lower());gone=uim.bbox(uim.mask(uim.load_ppm(v/('ui-extra-tile-dismiss-'+name.lower()+'.ppm')),'#eef3fb',3,(0,0,1280,744)),20000)
  record('Launcher '+name+' tile dismisses launcher',gone is None or not (632<=gone[2]-gone[0]<=648 and 460<=gone[3]-gone[1]<=500))
  fresh=[p for p in pages_now() if p['id'] not in old and not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))]
  record('Launcher '+name+' mouse launch',bool(fresh) and (needle is None or any(needle in p['url'] for p in fresh)),[p['url'][:120] for p in fresh])
  park_pointer();shot('extra-tile-'+name.lower())
  if fresh:
   connect_page(fresh[0]);cdp('Page.bringToFront')
   if name in ('Settings','Terminal'):record('Launcher '+name+' shows Settings with advanced access off',js("document.querySelector('#settings').open && document.querySelector('#terminal').disabled"))
   cdp('Page.close');time.sleep(2);connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
safe_section('Launcher tile mouse effects',launch_tiles)

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
 cdp('Page.bringToFront');time.sleep(1);target=page['id'];info=cdp('Browser.getWindowForTarget',{'targetId':target});key('alt','f9');time.sleep(2)
 record('Taskbar minimize keyboard makes current browser minimized',cdp('Browser.getWindowForTarget',{'targetId':target})['bounds']['windowState']=='minimized')
 park_pointer();shot('extra-taskbar-minimized');im=uim.load_ppm(v/'ui-extra-taskbar-minimized.ppm');els=uim.shelf_elements(im,uim.shelf_band(im));buttons=[e for e in els if 300<=e[0] and e[2]<=980][2:]
 found=False
 for i,e in enumerate(buttons):
  guest_click(*uim.center(e));state=cdp('Browser.getWindowForTarget',{'targetId':target})['bounds']['windowState'];shot('extra-taskbar-activate-'+str(i))
  if state!='minimized':found=True;break
 record('Taskbar browser mouse activation restores minimized target',found,{'targetId':target,'windowId':info['windowId']})
safe_section('Taskbar activate/minimize',taskbar_activate)

def advanced_interactive():
 password=''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(24))
 try:
  cdp('Page.bringToFront');cdp('Page.navigate',{'url':'http://127.0.0.1:8765/#settings'});time.sleep(3);cdp('Page.enable')
  # Click through the real checkbox and JS confirmation, then type only into getpass.
  point=js("(()=>{let e=document.querySelector('#advanced');e.scrollIntoView({block:'center'});let r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
  mouse(*point);cdp('Page.handleJavaScriptDialog',{'accept':True});time.sleep(3)
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
  probe('/advanced-cleanup',{});password=None
  # Recover a browser target even if terminal focus or a failed check interrupted the section.
  connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
safe_section('Advanced interactive enable/disable',advanced_interactive)

def signatures():
 proof=probe('/signature-check',{})
 record('Signed fixture accepted by real minisign',proof['signed_fixture_verified'])
 record('Real updater rejects tampered signature before entry changes',proof['real_updater_rejected_tamper'] and proof['entries_unchanged'],proof['scope'])
safe_section('Update signature/tamper live VM',signatures)

def pwa_install():
 # CDP installs through Chrome's own PWA subsystem. This proves integration,
 # not the browser menu's human install flow, which stays separately unverified.
 manifest='http://127.0.0.1:8766/pwa/'
 try:
  cdp('PWA.install',{'manifestId':manifest,'installUrlOrBundleUrl':manifest});time.sleep(4)
  launch=cdp('PWA.launch',{'manifestId':manifest});time.sleep(3)
  p=next(p for p in pages_now() if p['id']==launch['targetId']);connect_page(p);cdp('Page.bringToFront')
  record('PWA installs and opens standalone through Chrome subsystem',js("matchMedia('(display-mode: standalone)').matches && document.title==='Kestrel CI PWA'"));shot('extra-pwa-installed');cdp('Page.close');time.sleep(2)
  connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
  old={p['id'] for p in pages_now()};lw,tiles=launcher_tiles('CI PWA')
  record('Installed PWA has launcher tile',len(tiles)==1)
  if len(tiles)!=1:raise RuntimeError('PWA launcher tile missing')
  guest_click(*uim.center(tiles[0]));time.sleep(4);fresh=next(p for p in pages_now() if p['id'] not in old and p['url'].startswith(manifest));connect_page(fresh)
  record('PWA mouse relaunch from Kestrel launcher remains standalone',js("matchMedia('(display-mode: standalone)').matches"));shot('extra-pwa-relaunched')
 finally:
  try:cdp('PWA.uninstall',{'manifestId':manifest})
  finally:connect_page(next(p for p in pages_now() if not p['url'].startswith(('chrome://omnibox-popup','chrome-untrusted:'))))
safe_section('PWA subsystem install and launcher relaunch',pwa_install)
