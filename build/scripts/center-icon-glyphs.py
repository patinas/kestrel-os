#!/usr/bin/env python3
"""Centre every glyph of the Kestrel icon font in its advance box and on the middle of the line box
(ascent 900, descent -100 -> middle at 400 units above the baseline), so shelf icons sit in the middle of their pills.
Usage: center-icon-glyphs.py icons.ttf   (rewrites the file in place; idempotent)"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
p=sys.argv[1];f=TTFont(p);gs=f.getGlyphSet();glyf=f['glyf'];hh=f['hhea']
mid=(hh.ascent+hh.descent)/2
for name in f.getGlyphOrder():
    if name=='.notdef':continue
    bp=BoundsPen(gs);gs[name].draw(bp)
    if not bp.bounds:continue
    x0,y0,x1,y1=bp.bounds;adv=f['hmtx'][name][0]
    dx=round((adv-(x1-x0))/2-x0);dy=round(mid-(y0+y1)/2)
    g=glyf[name]
    if g.isComposite():raise SystemExit('composite glyph '+name)
    g.coordinates.translate((dx,dy))
    g.recalcBounds(glyf)
    f['hmtx'][name]=(adv,round(x0+dx))
    print(name,'moved',dx,dy)
f.save(p)
