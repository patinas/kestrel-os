"""Pixel measurement helpers shared by the UI tests. Elements are found by the CSS colours shipped in the shell stylesheets.
A colour that is not found returns None; callers must treat that as UNMEASURED, never as a pass."""
import numpy as np
def hexc(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
def load_ppm(path):
    raw=open(path,'rb').read();parts=raw.split(maxsplit=4);w,h=int(parts[1]),int(parts[2]);assert parts[0]==b'P6'
    return np.frombuffer(raw[len(raw)-w*h*3:],np.uint8).reshape(h,w,3).astype(int)
def mask(img,c,tol,reg=None):
    m=np.all(np.abs(img-np.array(hexc(c) if isinstance(c,str) else c))<=tol,axis=2)
    if reg:
        z=np.zeros_like(m);x1,y1,x2,y2=reg;z[y1:y2,x1:x2]=m[y1:y2,x1:x2];return z
    return m
def bbox(m,minpx=3000):
    if m.sum()<minpx:return None
    ys,xs=np.where(m);return [int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]
def runs(a,minv,gap=1):
    idx=np.where(a>=minv)[0];out=[]
    for i in idx:
        if out and i-out[-1][1]<=gap:out[-1][1]=i
        else:out.append([i,i])
    return [(a0,a1+1) for a0,a1 in out]
def shelf_elements(img,sh,shelf_hex='#e0e8f6'):
    """Pills on the shelf. X extents come from a 8 px band at the vertical middle, where the shelf's rounded caps are square, then Y extents are read per element."""
    non=~mask(img,shelf_hex,9);mid=(sh[1]+sh[3])//2
    out=[]
    for e in blocks(non,1,(sh[0],mid-4,sh[2],mid+4),1,3):
        if e[2]-e[0]<20:continue
        col=non[sh[1]+4:sh[3]-4,e[0]:e[2]];ys=np.where(col.sum(1)>=0.6*(e[2]-e[0]))[0]
        if len(ys):out.append([e[0],int(sh[1]+4+ys.min()),e[2],int(sh[1]+4+ys.max()+1)])
    return out
def blocks(m,rowmin,box,rgap=2,cgap=2):
    x1,y1,x2,y2=box;sub=m[y1:y2,x1:x2];res=[]
    for r0,r1 in runs(sub.sum(1),rowmin,rgap):
        for c0,c1 in runs(sub[r0:r1].sum(0),1,cgap):res.append([int(x1+c0),int(y1+r0),int(x1+c1),int(y1+r1)])
    return res
def center(r): return ((r[0]+r[2])//2,(r[1]+r[3])//2)
def qs_panel(img):
    """360 px quick-settings panel by its fill colour. Rows/columns need many matching pixels, so stray page pixels of a similar colour cannot stretch the box."""
    m=mask(img,'#f3f6fc',3,(880,0,1280,744))
    rows=np.where(m.sum(1)>=200)[0];cols=np.where(m.sum(0)>=150)[0]
    if len(rows)<100 or len(cols)<300:return None
    b=[int(cols.min()+0),int(rows.min()),int(cols.max()+1),int(rows.max()+1)]
    return b if 352<=b[2]-b[0]<=368 else None
def qs_layout(img):
    """quick settings: panel, tiles(2), mute, wide(All settings, Close) rects"""
    pan=qs_panel(img)
    if not pan:return None
    bl=blocks(mask(img,'#e2eaf6',3,tuple(pan)),30,tuple(pan))
    bl=[b for b in bl if b[2]-b[0]>=40 and b[3]-b[1]>=30]
    wide=sorted([b for b in bl if b[2]-b[0]>=300],key=lambda b:b[1])
    rest=sorted([b for b in bl if b[2]-b[0]<300],key=lambda b:(b[1],b[0]))
    tiles=rest[:2];mute=rest[2] if len(rest)>2 else None
    return {'panel':pan,'tiles':tiles,'mute':mute,'wide':wide}
def dominant(img,r):
    reg=img[r[1]:r[3],r[0]:r[2]].reshape(-1,3);v,c=np.unique(reg,axis=0,return_counts=True);return tuple(int(x) for x in v[c.argmax()])
def glyph_box(img,r,thresh=70):
    """bbox of pixels clearly different from the element's own fill, ignoring a 6 px rim (rounded corners). None if empty."""
    i=[r[0]+6,r[1]+6,r[2]-6,r[3]-6];bg=np.array(dominant(img,i));reg=img[i[1]:i[3],i[0]:i[2]]
    m=np.abs(reg-bg).sum(2)>thresh;ys,xs=np.where(m)
    if len(xs)<8:return None
    return [int(i[0]+xs.min()),int(i[1]+ys.min()),int(i[0]+xs.max()+1),int(i[1]+ys.max()+1)]
def luma(c): return 0.299*c[0]+0.587*c[1]+0.114*c[2]
