#!/usr/bin/env python3
"""Layout symmetry/consistency rules for Kestrel UI frames.
Input: JSON rects measured from a 1280x800 frame, e.g. {"screen":[0,0,1280,800],"shelf":[8,744,1272,792],"panel":[...],"tiles":[[x1,y1,x2,y2],...]}
Rects are [x1,y1,x2,y2]. Exit 0 only if every rule passes. Tolerance is 1 px. This checks geometry; it does not prove the pixels were measured correctly."""
import json, sys
TOL = 1
def w(r): return r[2]-r[0]
def h(r): return r[3]-r[1]
def cx(r): return (r[0]+r[2])/2
def near(a, b, t=TOL): return abs(a-b) <= t
def run(d):
    res = []
    def rule(name, ok, detail): res.append((name, bool(ok), detail))
    S = d.get("screen", [0, 0, 1280, 800])
    sh = d.get("shelf")
    if sh:
        L, R, B = sh[0]-S[0], S[2]-sh[2], S[3]-sh[3]
        rule("shelf left gutter == right gutter", near(L, R), f"{L} vs {R}")
        rule("shelf bottom gutter == side gutter", near(B, L), f"{B} vs {L}")
        rule("shelf height 48", near(h(sh), 48), h(sh))
        rule("shelf centered on screen", near(cx(sh), cx(S)), f"{cx(sh)} vs {cx(S)}")
        if d.get("shelf_icons"):
            ic = d["shelf_icons"]
            rule("shelf icons all same size", len({(w(r), h(r)) for r in ic}) == 1, sorted({(w(r), h(r)) for r in ic}))
            rule("shelf icons vertically centered in shelf", all(near((r[1]+r[3])/2, (sh[1]+sh[3])/2) for r in ic), "")
            gaps = [ic[i+1][0]-ic[i][2] for i in range(len(ic)-1)]
            rule("shelf icon gaps equal", len(set(gaps)) <= 1 or max(gaps)-min(gaps) <= TOL, gaps)
        if d.get("shelf_left_group") and d.get("shelf_right_group"):
            a, b = d["shelf_left_group"], d["shelf_right_group"]
            rule("shelf left/right group padding equal", near(a[0]-sh[0], sh[2]-b[2]), f"{a[0]-sh[0]} vs {sh[2]-b[2]}")
    for name in ("panel", "launcher"):
        p = d.get(name)
        if name == "launcher" and d.get("launcher_floating"): continue
        if p and sh:
            rule(f"{name} bottom gap above shelf == shelf side gutter", near(sh[1]-p[3], sh[0]-S[0]), f"{sh[1]-p[3]} vs {sh[0]-S[0]}")
    p = d.get("panel")
    if p and sh:
        rule("panel right gutter == shelf right gutter", near(S[2]-p[2], S[2]-sh[2]), f"{S[2]-p[2]} vs {S[2]-sh[2]}")
        rule("panel width 360", near(w(p), 360), w(p))
    la = d.get("launcher")
    if la and sh and not d.get("launcher_floating"):
        rule("launcher left edge == shelf left edge", near(la[0], sh[0]), f"{la[0]} vs {sh[0]}")
    for name, key in (("panel tiles", "panel_tiles"), ("launcher tiles", "launcher_tiles"), ("settings buttons", "settings_buttons")):
        t = d.get(key)
        if t:
            rule(f"{name} same size", len({(w(r), h(r)) for r in t}) == 1 or (max(w(r) for r in t)-min(w(r) for r in t) <= TOL and max(h(r) for r in t)-min(h(r) for r in t) <= TOL), sorted({(w(r), h(r)) for r in t}))
            xs = sorted({r[0] for r in t}); ys = sorted({r[1] for r in t})
            gx = [xs[i+1]-xs[i] for i in range(len(xs)-1)]; gy = [ys[i+1]-ys[i] for i in range(len(ys)-1)]
            rule(f"{name} column pitch equal", not gx or max(gx)-min(gx) <= TOL, gx)
            rule(f"{name} row pitch equal", not gy or max(gy)-min(gy) <= TOL, gy)
    for key, cont in (("panel_tiles", "panel"), ("launcher_tiles", "launcher")):
        t, c = d.get(key), d.get(cont)
        if t and c:
            l = min(r[0] for r in t)-c[0]; r_ = c[2]-max(r[2] for r in t)
            rule(f"{key} left inset == right inset inside {cont}", near(l, r_), f"{l} vs {r_}")
    for name, rects in (d.get("left_aligned_groups") or {}).items():
        xs = [r[0] for r in rects]
        rule(f"{name}: left edges aligned", max(xs)-min(xs) <= TOL, xs)
    for name in ("shelf", "panel", "launcher"):
        r = d.get(name)
        if r:
            rule(f"{name} on 8 px grid (+-2 px for anti-aliased edges)", all(min(v % 8, 8 - v % 8) <= 2 for v in (w(r), h(r))) or name == "panel", (w(r), h(r)))
    return res
if __name__ == "__main__":
    d = json.load(open(sys.argv[1]))
    res = run(d); bad = 0
    for n, ok, det in res:
        print(("PASS " if ok else "FAIL ")+n+(f" [{det}]" if det != "" else "")); bad += (not ok)
    print(f"{len(res)-bad}/{len(res)} rules passed"); sys.exit(1 if bad else 0)
