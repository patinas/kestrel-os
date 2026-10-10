#!/usr/bin/env python3
"""Test double: a Wayland server that only implements wl_seat and wlr-foreign-toplevel-management.
Commands on stdin: open APP_ID TITLE... | state INDEX minimized|activated|normal | close INDEX
It prints 'ACTIVATE n', 'UNMINIMIZE n', 'MINIMIZE n', 'CLOSE n' for requests it receives (n = index from open order)."""
import array,os,sys
sys.path.insert(0,os.environ.get('KESTREL_LIB','/usr/local/lib/kestrel'))
from pywayland.server import Display, Client
from pywayland.server.eventloop import EventLoop
FdMask=EventLoop.FdMask
from pywayland.protocol.wayland import WlSeatGlobal
from wlr_foreign_toplevel import ZwlrForeignToplevelManagerV1Global,ZwlrForeignToplevelHandleV1Resource

# pywayland 0.4.x cannot send array or new_id arguments from a server (wl_array.data is never set and
# ffi.new("void []") fails). The state event needs one, so patch that branch for this test double only.
import inspect,textwrap
from pywayland.protocol_core import message as _m
for _cls in (getattr(_m,n) for n in dir(_m) if inspect.isclass(getattr(_m,n))):
 f=getattr(_cls,'arguments_to_c',None)
 if f and 'new_data' in inspect.getsource(f):
  src=textwrap.dedent(inspect.getsource(f))
  src=src.replace('new_data: ffi.CData = ffi.new("void []", len(arg))','new_data = ffi.new("char[]", bytes(arg) or b"\\0");new_array.data = ffi.cast("void *", new_data)')
  src=src.replace('ffi.buffer(new_data)[:] = arg','pass').replace('new_array.alloc = new_array.size = len(arg)','new_array.alloc = new_array.size = len(arg);args_ptr[i].a = new_array')
  import re
  src=re.sub(r'args_ptr\[i\]\.o = ffi\.NULL\n(\s+)continue',lambda m:'_a = next(arg_iter, None)\n'+m.group(1)[:-0 or None]+'args_ptr[i].o = ffi.cast("struct wl_object *", _a._ptr) if _a is not None else ffi.NULL\n'+m.group(1)+'continue',src,count=1)
  ns=dict(vars(_m));exec("from __future__ import annotations\n"+src,ns);setattr(_cls,'arguments_to_c',ns['arguments_to_c'])
# pywayland 0.4.x server resources are registered with a NULL implementation pointer, so client requests
# reach dispatcher_func with no handle and crash. Re-register with the handle (test double only).
from pywayland import lib as _lib
from pywayland.protocol_core.resource import Resource as _Res
_orig_init=_Res.__init__
def _init(self,*a,**k):
 _orig_init(self,*a,**k);self.interface.registry[self._ptr]=self;_lib.wl_resource_set_dispatcher(self._ptr,_lib.dispatcher_func,self._handle,self._handle,_lib.resource_destroy_func)
_Res.__init__=_init
def say(*a):print(*a,flush=True)
display=Display();sock=display.add_socket(sys.argv[1]);mgrs=[];tops=[]
seat=WlSeatGlobal(display,version=1)
seats=[]
def bind_seat(res):
 seats.append(res);res.capabilities(0)
seat.bind_func=bind_seat
mg=ZwlrForeignToplevelManagerV1Global(display,version=3)
mg.bind_func=lambda res:(mgrs.append(res),say('BOUND'))
def send_state(h,kind):
 vals={'minimized':[1],'activated':[2],'normal':[]}[kind]
 h.state(array.array('I',vals).tobytes());h.done()
def cmd(fd,mask,data):
 line=os.read(0,4096).decode()
 if not line:display.terminate();return 0
 for l in line.splitlines():
  p=l.split(' ',2)
  if p[0]=='open':
   m=mgrs[0];h=ZwlrForeignToplevelHandleV1Resource(Client.from_resource(m._ptr),m.version,0);i=len(tops);tops.append(h)
   m.toplevel(h);h.title(p[2] if len(p)>2 else '');h.app_id(p[1]);h.state(b'');h.done()
   h.dispatcher['activate']=lambda r,s,i=i:say('ACTIVATE',i)
   h.dispatcher['unset_minimized']=lambda r,i=i:say('UNMINIMIZE',i)
   h.dispatcher['set_minimized']=lambda r,i=i:say('MINIMIZE',i)
   h.dispatcher['close']=lambda r,i=i:say('CLOSE',i)
  elif p[0]=='state':send_state(tops[int(p[1])],p[2])
  elif p[0]=='close':tops[int(p[1])].closed()
 display.flush_clients();return 0
loop=display.get_event_loop();src=loop.add_fd(0,cmd,FdMask.WL_EVENT_READABLE,None)
say('READY',sock);display.run()
