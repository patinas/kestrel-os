"""Disposable VM only. This file is injected into the CI build, not the profile."""
import hashlib,http.server,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and Path('/dev/virtio-ports/kestrel-ci-check').exists()
D=Path('/var/lib/kestrel')
def run(args,**kw):return subprocess.run(args,capture_output=True,timeout=40,**kw)
def status():
 counts={n:0 for n in ('kestrel-network','kestrel-bluetooth','kestrel-launcher','kestrel-quick-settings','foot')}
 for p in Path('/proc').glob('[0-9]*/cmdline'):
  try:
   args=p.read_bytes().split(b'\0');names={Path(x.decode()).name for x in args[:2] if x}
   for n in counts:counts[n]+=int(n in names)
  except (OSError,UnicodeError):pass
 ownership={}
 for name in ('/etc/sudoers','/etc/sudoers.d','/etc/sudoers.d/kestrel-advanced','/etc/pam.d/kestrel-sudo','/usr/local/bin/kestrel-advanced-toggle'):
  p=Path(name)
  if p.exists():
   st=p.stat();ownership[name]={'uid':st.st_uid,'gid':st.st_gid,'mode':oct(st.st_mode & 0o777)}
 return {'ownership':ownership,'processes':counts,'enabled':(D/'terminal-enabled').exists(),'password_present':(D/'sudo-password').exists()}
# Test doubles below exist only in a named-port disposable CI VM.
MEDIA=Path('/tmp/kestrel-ci-media');player=None;input_fd=None
KEYS={'play':164,'next':163,'previous':165,'bright-up':225,'bright-down':224}
def media_status():
 out={}
 for name in ('player','brightness'):
  p=MEDIA/(name+'.json');out[name]=json.loads(p.read_text()) if p.exists() else None
 return out

def media_stop():
 global player,input_fd
 if player:
  import signal
  try:os.killpg(player.pid,signal.SIGTERM);player.wait(timeout=5)
  except (OSError,subprocess.TimeoutExpired):pass
  player=None
 if input_fd is not None:
  import fcntl
  fcntl.ioctl(input_fd,0x5502);os.close(input_fd);input_fd=None
 Path('/usr/local/bin/brightnessctl').unlink(missing_ok=True)

def media_start():
 global player,input_fd
 import fcntl,struct,time,pwd
 media_stop();MEDIA.mkdir(exist_ok=True);uid=pwd.getpwnam('kestrel').pw_uid;gid=pwd.getpwnam('kestrel').pw_gid;os.chown(MEDIA,uid,gid)
 for p in MEDIA.glob('*.json'):p.unlink()
 (MEDIA/'brightness.json').write_text(json.dumps({'value':50,'events':[]}));os.chown(MEDIA/'brightness.json',uid,gid)
 wrapper=Path('/usr/local/bin/brightnessctl');assert not wrapper.exists()
 wrapper.write_text("#!/usr/bin/python3\nimport json,sys\nfrom pathlib import Path\np=Path('/tmp/kestrel-ci-media/brightness.json');d=json.loads(p.read_text());a=sys.argv[1:];assert a in [['set','+5%'],['set','5%-']];d['events'].append(a);d['value']+=5 if a[1]=='+5%' else -5;p.write_text(json.dumps(d));print(d['value'])\n");wrapper.chmod(0o755)
 env=['env','XDG_RUNTIME_DIR=/run/user/'+str(uid),'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/'+str(uid)+'/bus']
 player=subprocess.Popen(['runuser','-u','kestrel','--',*env,'python3','/usr/local/lib/kestrel-ci/test-media-player.py',str(MEDIA/'player.json')],start_new_session=True)
 for _ in range(40):
  r=run(['runuser','-u','kestrel','--',*env,'playerctl','--list-all'])
  if b'kestrel_ci' in r.stdout:break
  if player.poll() is not None:raise RuntimeError('MPRIS fixture exited')
  time.sleep(.1)
 else:raise RuntimeError('MPRIS fixture not registered')
 run(['modprobe','uinput']);input_fd=os.open('/dev/uinput',os.O_WRONLY|os.O_NONBLOCK)
 for typ in (0,1):fcntl.ioctl(input_fd,0x40045564,typ)
 for code in [30,*KEYS.values()]:fcntl.ioctl(input_fd,0x40045565,code)
 os.write(input_fd,struct.pack('80sHHHHI',b'Kestrel CI keyboard',3,0x1234,1,1,0)+bytes(4*64*4));fcntl.ioctl(input_fd,0x5501);time.sleep(3)
 return {**media_status(),'scope':'Real compositor key dispatch and real playerctl to test MPRIS; brightness command dispatch to a test double, not physical backlight.'}

def media_key(name):
 import struct,time
 assert input_fd is not None and name in KEYS
 for down in (1,0):
  os.write(input_fd,struct.pack('llHHi',0,0,1,KEYS[name],down));os.write(input_fd,struct.pack('llHHi',0,0,0,0,0));time.sleep(.15)
 time.sleep(.6);return media_status()

class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/pwa/':
   body=b'<html><head><title>Kestrel CI PWA</title><link rel="manifest" href="/pwa/manifest.json"></head><body><h1>Kestrel CI PWA</h1><script>navigator.serviceWorker.register("/pwa/sw.js")</script></body></html>';kind='text/html'
  elif self.path=='/pwa/manifest.json':
   body=json.dumps({'id':'/pwa/','name':'Kestrel CI PWA','short_name':'CI PWA','start_url':'/pwa/','scope':'/pwa/','display':'standalone','icons':[{'src':'/pwa/icon.png','sizes':'192x192','type':'image/png'}]}).encode();kind='application/manifest+json'
  elif self.path=='/pwa/sw.js':body=b'self.addEventListener("fetch",e=>e.respondWith(fetch(e.request)))';kind='application/javascript'
  elif self.path=='/pwa/icon.png':
   import struct,zlib
   def chunk(k,v):return struct.pack('!I',len(v))+k+v+struct.pack('!I',zlib.crc32(k+v)&0xffffffff)
   body=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',192,192,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+bytes([70,111,167])*192)*192))+chunk(b'IEND',b'');kind='image/png'
  elif self.path=='/diagnostics':
   r=run(['journalctl','-u','kestrel-ci-ui-probe.service','--no-pager','-n','35','-o','cat']);self.reply({'stderr':r.stdout.decode(errors='replace')[-4000:]});return
  elif self.path=='/taskbar-log':
   out={}
   for f in list(Path('/run/user').glob('*/kestrel-taskbar/log'))+list(Path('/home').glob('*/.local/state/kestrel/taskbar.log'))+list(Path('/home').glob('*/.local/state/kestrel/waybar.log')):
    try:out[str(f)]=f.read_text(errors='replace')[-4000:]
    except OSError as e:out[str(f)]=repr(e)
   r=run(['pgrep','-a','-f','kestrel-taskbar|waybar|wofi']);out['processes']=r.stdout.decode(errors='replace')
   self.reply(out);return
  elif self.path=='/status':self.reply(status());return
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',kind);self.end_headers();self.wfile.write(body)
 def reply(self,data):
  body=json.dumps(data).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
 def do_POST(self):
  # Only a disposable named-port VM exposes this test listener. Never add it to a shipped profile.
  if self.headers.get('Origin') or self.headers.get('Sec-Fetch-Site'):self.send_error(403);return
  if self.path not in ('/advanced-check','/advanced-cleanup','/signature-check','/panels-close','/terminals-close','/media-start','/media-key','/media-stop'):self.send_error(404);return
  size=int(self.headers.get('Content-Length',0))
  if not 0<=size<=1024:self.send_error(400);return
  data=json.loads(self.rfile.read(size) or b'{}')
  try:self.action(data)
  except Exception as e:
   import traceback;traceback.print_exc()
   self.reply({'error':type(e).__name__,'message':str(e)[:300]})
 def action(self,data):
  if self.path=='/media-start':self.reply(media_start())
  elif self.path=='/media-key':self.reply(media_key(data['key']))
  elif self.path=='/media-stop':media_stop();self.reply({'stopped':True})
  elif self.path=='/terminals-close':
   run(['pkill','-u','kestrel','-x','foot']);self.reply(status())
  elif self.path=='/panels-close':
   import signal
   for p in Path('/proc').glob('[0-9]*/cmdline'):
    try:
     names={Path(x.decode()).name for x in p.read_bytes().split(b'\0')[:2] if x}
     if names & {'kestrel-launcher','kestrel-quick-settings'}:os.kill(int(p.parent.name),signal.SIGTERM)
    except (OSError,UnicodeError):pass
   self.reply(status())
  elif self.path=='/advanced-check':
   cmd=['runuser','-u','kestrel','--','sudo','-k','-S','/usr/bin/id','-u']
   good=run(cmd,input=(data['password']+'\n').encode());bad=run(cmd,input=b'wrong-test-password\n')
   self.reply({**status(),'correct_sudo':good.returncode==0 and good.stdout.strip()==b'0','wrong_sudo_rejected':bad.returncode!=0})
  elif self.path=='/advanced-cleanup':
   r=run(['runuser','-u','kestrel','--','sudo','-n','/usr/local/bin/kestrel-advanced-toggle','disable'])
   self.reply({**status(),'disabled':r.returncode==0})
  else:
   import tempfile
   with tempfile.TemporaryDirectory() as t:
    p=Path(t);pub=p/'key.pub';key=p/'key';img=p/'root.tar.zst';img.write_bytes(b'Kestrel CI signature fixture, not an OS image')
    import shutil
    if not shutil.which('minisign'):raise RuntimeError('minisign missing in disposable UI build')
    generated=run(['minisign','-G','-W','-f','-p',str(pub),'-s',str(key)])
    if generated.returncode:raise RuntimeError('minisign key generation exit '+str(generated.returncode))
    signed=run(['minisign','-S','-s',str(key),'-m',str(img)])
    valid=run(['minisign','-V','-p',str(pub),'-m',str(img)])
    if signed.returncode or valid.returncode:raise RuntimeError('minisign sign/verify failed: '+str([signed.returncode,valid.returncode]))
    sig=Path(str(img)+'.minisig');rows=sig.read_text().splitlines();row=rows[1];rows[1]=row[:10]+('B' if row[10]=='A' else 'A')+row[11:];sig.write_text('\n'.join(rows)+'\n')
    before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/boot/loader/entries').glob('*.conf')}
    env={**os.environ,'KESTREL_ALLOW_VM_UPDATE':'yes','KESTREL_UPDATE_PUB':str(pub)}
    # Live profile carries the updater script but installer alone creates the bin symlink.
    rejected=run(['bash','/usr/local/lib/kestrel/update.sh',str(img),str(sig)],env=env)
    after={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/boot/loader/entries').glob('*.conf')}
    self.reply({'signed_fixture_verified':signed.returncode==0 and valid.returncode==0,'real_updater_rejected_tamper':rejected.returncode!=0 and b'signature verification FAILED' in rejected.stderr+rejected.stdout,'entries_unchanged':before==after,'scope':'Live-VM signature gate only; A/B write/reboot requires installed sequence CI.'})
http.server.ThreadingHTTPServer(('0.0.0.0',8766),Handler).serve_forever()
