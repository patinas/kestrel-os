#!/usr/bin/env python3
"""Rebuild build/profile/airootfs/usr/share/fonts/kestrel/icons.ttf from Phosphor Icons (MIT) fill SVGs.
Usage: build-icon-font.py <dir with squares-four.svg globe.svg envelope-simple.svg video-camera.svg> out.ttf
Glyph order and code points stay U+E000 launcher, E001 browser, E002 mail, E003 video. Run center-icon-glyphs.py afterwards."""
import sys,re
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
src,out=sys.argv[1:3]
MAP=[('launcher',0xE000,'squares-four'),('browser',0xE001,'globe'),('mail',0xE002,'envelope-simple'),('video',0xE003,'video-camera')]
S=1000/256*0.86  # glyph fills ~86% of the em, like the old font
glyphs={'.notdef':TTGlyphPen(None).glyph()}
for name,cp,svg in MAP:
    d=' '.join(re.findall(r'\sd="([^"]+)"',open(f'{src}/{svg}.svg').read()))
    pen=TTGlyphPen(None)
    parse_path(d,TransformPen(Cu2QuPen(pen,1.0,reverse_direction=True),(S,0,0,-S,0,900)))
    glyphs[name]=pen.glyph()
order=['.notdef']+[m[0] for m in MAP]
fb=FontBuilder(1000,isTTF=True);fb.setupGlyphOrder(order)
fb.setupCharacterMap({cp:n for n,cp,_ in MAP})
fb.setupGlyf(glyphs)
fb.setupHorizontalMetrics({n:(1000,0) for n in order})
fb.setupHorizontalHeader(ascent=900,descent=-100)
fb.setupNameTable({'familyName':'Kestrel Icons','styleName':'Regular'})
fb.setupOS2(sTypoAscender=900,sTypoDescender=-100,usWinAscent=900,usWinDescent=100)
fb.setupPost();fb.save(out)
