#!/usr/bin/env python3
"""Regenerate the hicolor app icons: a rounded colour tile with a white Phosphor Icons (MIT) fill glyph.
Usage: build-app-icons.py <phosphor svg dir> <hicolor scalable/apps dir>   (PNG 64x64 is rendered separately with ImageMagick/rsvg)"""
import sys,re
src,out=sys.argv[1:3]
ICONS={'launcher':('#566d98','squares-four'),'browser':('#427ac6','globe'),'mail':('#8171ba','envelope-simple'),'video':('#cc657c','video-camera'),'settings':('#4c938d','gear')}
for n,(c,g) in ICONS.items():
    d=' '.join(re.findall(r'\sd="([^"]+)"',open(f'{src}/{g}.svg').read()))
    open(f'{out}/kestrel-{n}.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"><rect width="48" height="48" rx="14" fill="{c}"/><g transform="translate(9 9) scale(0.1172)" fill="#fff"><path fill-rule="evenodd" d="{d}"/></g></svg>\n')
