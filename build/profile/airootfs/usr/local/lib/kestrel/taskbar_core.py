"""Pure taskbar logic: group windows per app, decide click behaviour, render slot icons.
No Wayland here, so it is unit-testable. The daemon is /usr/local/bin/kestrel-taskbar."""
import math
IGNORE={'kestrel-launcher','kestrel-quick-settings'}
APP_MAP={'chrome':'google-chrome'}
MAX_SLOTS=8
PILL_ACTIVE=(0xa6/255,0xc4/255,0xeb/255)
INK=(0x23/255,0x30/255,0x44/255)

def groups(windows):
 """windows: dicts with id, app_id, title, minimized, activated, seq. One group per app, ordered by first window."""
 by={}
 for w in sorted(windows,key=lambda w:w['seq']):
  a=APP_MAP.get(w.get('app_id') or '',w.get('app_id') or 'unknown')
  if a in IGNORE:continue
  g=by.setdefault(a,{'app_id':a,'windows':[]});g['windows'].append(w)
 out=list(by.values())
 for g in out:
  g['count']=len(g['windows']);g['active']=any(w['activated'] for w in g['windows'])
  g['minimized']=all(w['minimized'] for w in g['windows'])
 return out[:MAX_SLOTS]

def click_plan(group):
 """One window: activate it (restores it when minimized), as the old per-window button did.
 Two or more: show a list to pick from."""
 ws=group['windows']
 if len(ws)==1:return ('activate',ws[0]['id'])
 return ('menu',[(w['id'],w['title'] or w['app_id'] or 'Window') for w in ws])

def menu_lines(items):
 return [f"{i+1}. {t.replace(chr(10),' ')}" for i,(_,t) in enumerate(items)]

def parse_choice(line,items):
 try:n=int(line.strip().split('.',1)[0])
 except ValueError:return None
 return items[n-1][0] if 1<=n<=len(items) else None

def signature(gs):
 return [(g['app_id'],g['count'],g['active'],g['minimized']) for g in gs]

PILL_IDLE=(0xd8/255,0xe3/255,0xf3/255)

def render_png(path,icon,count,active,minimized):
 """40x40 slot image. icon: a 32x32 cairo surface or None. Active pill is drawn here because
 Waybar image modules cannot take CSS classes."""
 import cairo
 s=cairo.ImageSurface(cairo.FORMAT_ARGB32,48,48);c=cairo.Context(s);c.translate(4,4)
 if True:
  r=12;c.new_sub_path()
  for cx,cy,a0 in ((40-r,r,-90),(40-r,40-r,0),(r,40-r,90),(r,r,180)):c.arc(cx,cy,r,math.radians(a0),math.radians(a0+90))
  c.close_path();c.set_source_rgb(*(PILL_ACTIVE if active else PILL_IDLE));c.fill()
 if icon is not None:
  c.set_source_surface(icon,4,4);c.paint_with_alpha(.65 if minimized else 1)
 if count>1:
  c.arc(32,32,7,0,2*math.pi);c.set_source_rgb(*INK);c.fill()
  c.set_source_rgb(1,1,1);c.select_font_face('Noto Sans',cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD);c.set_font_size(10)
  t=str(count) if count<10 else '9+';e=c.text_extents(t);c.move_to(32-e.width/2-e.x_bearing,32-e.height/2-e.y_bearing);c.show_text(t)
 s.write_to_png(path)

ICON_ROOTS=('/usr/share/icons/Papirus','/usr/share/icons/hicolor','/usr/share/pixmaps')

def find_icon_file(names,roots=ICON_ROOTS):
 """First existing icon file for any of the names, preferring raster sizes near 32 px, then scalable."""
 import glob,os
 for n in names:
  if os.path.isabs(n) and os.path.exists(n):return n
  for root in roots:
   hits=[]
   for ext in ('png','svg'):
    hits+=glob.glob(os.path.join(root,'**',n+'.'+ext),recursive=True)
   def rank(f):
    import re
    m=re.search(r'/(\d+)(?:x\d+)?/',f)
    return (0,abs(int(m.group(1))-32)) if m else ((1,0) if '/scalable/' in f else (2,0))
   if hits:return sorted(hits,key=rank)[0]
 return None

def surface_from_file(path,size=32):
 """cairo surface from an icon file via GdkPixbuf. No GDK display needed (a Gdk import would open a second Wayland connection)."""
 import cairo,gi
 gi.require_version('GdkPixbuf','2.0')
 from gi.repository import GdkPixbuf
 pb=GdkPixbuf.Pixbuf.new_from_file_at_size(path,size,size)
 if not pb.get_has_alpha():pb=pb.add_alpha(False,0,0,0)
 w,h,rs,ch=pb.get_width(),pb.get_height(),pb.get_rowstride(),pb.get_n_channels();px=pb.get_pixels()
 surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,size,size);st=surf.get_stride();buf=surf.get_data()
 ox,oy=(size-w)//2,(size-h)//2
 for y in range(h):
  for x in range(w):
   r,g,b,a=px[y*rs+x*ch:y*rs+x*ch+4]
   o=(y+oy)*st+(x+ox)*4;buf[o]=b*a//255;buf[o+1]=g*a//255;buf[o+2]=r*a//255;buf[o+3]=a
 surf.mark_dirty();return surf

def icon_surface(app_id):
 """Icon for an app_id via its .desktop entry (Gio, no display), else the app_id as icon name, else a generic icon."""
 names=[]
 try:
  import gi
  from gi.repository import Gio
  for cand in (app_id+'.desktop',app_id.lower()+'.desktop'):
   app=Gio.DesktopAppInfo.new(cand)
   if app and app.get_icon():
    ic=app.get_icon();names+=list(ic.get_names()) if hasattr(ic,'get_names') else [ic.to_string()];break
 except Exception:pass
 names+=[app_id,app_id.lower(),'application-x-executable']
 f=find_icon_file(names)
 return surface_from_file(f) if f else None
