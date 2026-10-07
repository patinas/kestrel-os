"""Disposable VM only. This file is injected into the CI build, not the profile."""
import hashlib,http.server,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and Path('/dev/virtio-ports/kestrel-ci-check').exists()
D=Path('/var/lib/kestrel')
def run(args,**kw):return subprocess.run(args,capture_output=True,timeout=40,**kw)
def status():
 counts={n:0 for n in ('kestrel-network','kestrel-bluetooth','foot')}
 for p in Path('/proc').glob('[0-9]*/cmdline'):
  try:
   args=p.read_bytes().split(b'\0');names={Path(x.decode()).name for x in args[:2] if x}
   for n in counts:counts[n]+=int(n in names)
  except (OSError,UnicodeError):pass
 return {'processes':counts,'enabled':(D/'terminal-enabled').exists(),'password_present':(D/'sudo-password').exists()}
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
  elif self.path=='/status':self.reply(status());return
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',kind);self.end_headers();self.wfile.write(body)
 def reply(self,data):
  body=json.dumps(data).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
 def do_POST(self):
  # Only a disposable named-port VM exposes this test listener. Never add it to a shipped profile.
  if self.headers.get('Origin') or self.headers.get('Sec-Fetch-Site'):self.send_error(403);return
  if self.path not in ('/advanced-check','/advanced-cleanup','/signature-check'):self.send_error(404);return
  size=int(self.headers.get('Content-Length',0))
  if not 0<=size<=1024:self.send_error(400);return
  data=json.loads(self.rfile.read(size) or b'{}')
  if self.path=='/advanced-check':
   cmd=['runuser','-u','kestrel','--','sudo','-k','-S','/usr/bin/id','-u']
   good=run(cmd,input=(data['password']+'\n').encode());bad=run(cmd,input=b'wrong-test-password\n')
   self.reply({**status(),'correct_sudo':good.returncode==0 and good.stdout.strip()==b'0','wrong_sudo_rejected':bad.returncode!=0})
  elif self.path=='/advanced-cleanup':
   r=run(['runuser','-u','kestrel','--','sudo','/usr/local/bin/kestrel-advanced-toggle','disable'])
   self.reply({**status(),'disabled':r.returncode==0})
  else:
   import tempfile
   with tempfile.TemporaryDirectory() as t:
    p=Path(t);pub=p/'key.pub';key=p/'key';img=p/'root.tar.zst';img.write_bytes(b'Kestrel CI signature fixture, not an OS image')
    run(['minisign','-G','-W','-f','-p',str(pub),'-s',str(key)])
    signed=run(['minisign','-S','-s',str(key),'-m',str(img)])
    valid=run(['minisign','-V','-p',str(pub),'-m',str(img)])
    sig=Path(str(img)+'.minisig');rows=sig.read_text().splitlines();row=rows[1];rows[1]=row[:10]+('B' if row[10]=='A' else 'A')+row[11:];sig.write_text('\n'.join(rows)+'\n')
    before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/boot/loader/entries').glob('*.conf')}
    env={**os.environ,'KESTREL_ALLOW_VM_UPDATE':'yes','KESTREL_UPDATE_PUB':str(pub)}
    rejected=run(['/usr/local/bin/kestrel-update',str(img),str(sig)],env=env)
    after={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/boot/loader/entries').glob('*.conf')}
    self.reply({'signed_fixture_verified':signed.returncode==0 and valid.returncode==0,'real_updater_rejected_tamper':rejected.returncode!=0 and b'signature verification FAILED' in rejected.stderr+rejected.stdout,'entries_unchanged':before==after,'scope':'Live-VM signature gate only; A/B write/reboot requires installed sequence CI.'})
http.server.ThreadingHTTPServer(('0.0.0.0',8766),Handler).serve_forever()
