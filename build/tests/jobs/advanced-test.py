# Disposable guest test: no passwords or hashes are printed.
import hashlib,json,os,secrets,subprocess
from pathlib import Path
D=Path('/var/lib/kestrel');D.mkdir(exist_ok=True)
cmd=['runuser','-u','kestrel','--','sudo','-k','-S','/usr/bin/id','-u']
assert subprocess.run(cmd,input='bad\n',text=True,capture_output=True).returncode!=0
# Seed ONLY this disposable test record. Interactive UI password setup is a separate gate.
password=secrets.token_urlsafe(24);salt=secrets.token_bytes(32)
p=D/'sudo-password';p.write_text(json.dumps({'salt':salt.hex(),'hash':hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1).hex()}));p.chmod(0o600)
p=D/'sudoers';p.write_text('kestrel ALL=(ALL:ALL) ALL\n');p.chmod(0o440)
D.joinpath('terminal-enabled').touch()
r=subprocess.run(cmd,input=password+'\n',text=True,capture_output=True)
assert r.returncode==0 and r.stdout.strip()=='0', 'correct password rejected'
assert subprocess.run(cmd,input='bad\n',text=True,capture_output=True).returncode!=0
# Real signed package transaction in the writable development root, not host root.
assert subprocess.run(['pacman','-Q','jq'],capture_output=True).returncode!=0, 'test assumes host jq absent'
subprocess.run(['kestrel-packages','-S','--noconfirm','jq'],check=True)
subprocess.run(['systemd-nspawn','--quiet','-D','/var/lib/kestrel/devroot','/usr/bin/pacman','-Q','jq'],check=True)
assert subprocess.run(['pacman','-Q','jq'],capture_output=True).returncode!=0, 'container package escaped onto host'
assert 'ro' in subprocess.check_output(['findmnt','-no','OPTIONS','/'],text=True).strip().split(',')
print('signed container jq transaction passed; host stayed read-only and jq absent')
subprocess.run(['runuser','-u','kestrel','--','sudo','-n','/usr/local/bin/kestrel-advanced-toggle','disable'],check=True,capture_output=True,timeout=10)
assert not D.joinpath('terminal-enabled').exists() and not D.joinpath('sudo-password').exists()
assert subprocess.run(cmd,input=password+'\n',text=True,capture_output=True).returncode!=0
print('advanced default-off, correct-password, wrong-password, disable revocation assertions passed')
