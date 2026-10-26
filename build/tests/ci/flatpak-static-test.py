#!/usr/bin/env python3
"""Flatpak support static checks, no VM: package set, Flathub remote drop-in,
session environment, launcher integration and the polkit rule."""
import re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
fails=[]
def check(name,ok,detail=''):
 print(('PASS ' if ok else 'FAIL ')+name+('' if ok or not detail else ' '+str(detail)),flush=True)
 if not ok:fails.append(name)

pkgs=(R/'profile/packages.x86_64').read_text().split()
for pkg in ('flatpak','xdg-desktop-portal','xdg-desktop-portal-gtk','xdg-desktop-portal-wlr'):
 check(f'package {pkg}',pkg in pkgs)

rem=R/'profile/airootfs/etc/flatpak/remotes.d/flathub.flatpakrepo'
check('flathub.flatpakrepo present',rem.is_file())
if rem.is_file():
 body=rem.read_text()
 check('remote name flathub (filename-derived or explicit)',rem.name=='flathub.flatpakrepo' and (re.search(r'^Name=(\S+)$',body,re.M) is None or re.search(r'^Name=flathub$',body,re.M) is not None))
 check('remote Url is dl.flathub.org','Url=https://dl.flathub.org/repo/' in body)
 check('remote carries GPGKey',re.search(r'^GPGKey=\S{100,}',body,re.M) is not None)

sess=(R/'profile/airootfs/usr/local/bin/kestrel-session').read_text()
check('session exports XDG_DATA_DIRS','export XDG_DATA_DIRS=' in sess)
check('session XDG_DATA_DIRS has system flatpak exports','/var/lib/flatpak/exports/share' in sess)
check('session XDG_DATA_DIRS has user flatpak exports','$HOME/.local/share/flatpak/exports/share' in sess)
check('session XDG_DATA_DIRS keeps defaults',"${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" in sess)
check('session sets XDG_CURRENT_DESKTOP=wlroots','export XDG_CURRENT_DESKTOP=wlroots' in sess)

launcher=(R/'profile/airootfs/usr/local/bin/kestrel-launcher').read_text()
check('launcher lists flatpak apps',"cmd.startswith('/usr/bin/flatpak run ')" in launcher)
check('launcher keeps chrome PWA filter',"'--app-id=' in cmd" in launcher)

rule=R/'profile/airootfs/etc/polkit-1/rules.d/50-kestrel-flatpak.rules'
check('polkit flatpak rule present',rule.is_file())
if rule.is_file():
 body=rule.read_text()
 check('polkit rule matches Flatpak actions','org.freedesktop.Flatpak.' in body)
 check('polkit rule scoped to wheel','isInGroup("wheel")' in body)
 code=re.sub(r'/\*.*?\*/','',body,flags=re.S)  # strip comments: exclusions apply to rule logic
 check('polkit rule has no wildcard','indexOf("org.freedesktop.Flatpak.' not in code)
 for aid in ('app-install','runtime-install','app-update','runtime-update','app-uninstall','runtime-uninstall','appstream-update','metadata-update'):
  check(f'polkit allows {aid}',f'"org.freedesktop.Flatpak.{aid}"' in code)
 for aid in ('configure-remote','modify-repo','install-bundle','app-downgrade','runtime-downgrade','configure"','update-remote','override'):
  check(f'polkit excludes {aid}',aid not in code)

cand=(R.parent/'.github/workflows/iso-candidate.yml').read_text()
check('candidate runs flatpak smoke step','08-flatpak-smoke.sh' in cand)
check('candidate sets KESTREL_FLATPAK_SMOKE','KESTREL_FLATPAK_SMOKE' in cand)
check('guest smoke script exists',(R/'tests/ci/flatpak-smoke-guest.sh').is_file())
check('smoke driver exists',(R/'tests/ci/flatpak-evidence.py').is_file())
check('smoke host step exists',(R/'tests/ci/08-flatpak-smoke.sh').is_file())
inj=(R/'tests/ci/01-build-iso.sh').read_text()
check('build injects guest script CI-only','KESTREL_FLATPAK_SMOKE' in inj and 'kestrel-ci/flatpak-smoke.sh' in inj)
check('guest script not in repo profile',not (R/'profile/airootfs/usr/local/lib/kestrel-ci').exists())

print(f'{len(fails)} failures',flush=True)
sys.exit(1 if fails else 0)
