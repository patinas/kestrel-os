import socket,json,sys
s=socket.socket(socket.AF_UNIX);s.connect('/src/out/m2-tests/qmp.sock');f=s.makefile('rw')
f.readline()
def cmd(name,args=None):
 d={'execute':name}
 if args: d['arguments']=args
 f.write(json.dumps(d)+'\n');f.flush()
 while True:
  r=json.loads(f.readline())
  if 'return' in r or 'error' in r:return r
print(cmd('qmp_capabilities'))
if sys.argv[1]=='shot':print(cmd('screendump',{'filename':'/src/out/m2-tests/'+sys.argv[2]+'.ppm'}))
else: print(cmd(sys.argv[1]))
