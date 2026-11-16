"""
Generates the Latvia/Sweden recolours of the cloudberry by mapping each colour role of the
plain sprite (leaf shades, berry shades, outline/rim/inner shadow) onto flag-colour ramps:
Sweden blue #006AA7 / yellow #FECC02, Latvia carmine #9E3039 / white.

The chosen design (split berry, Swedish cross offset like the flag) is branding/cloudberry.png.

Usage: python3 -I branding/flag_variants.py branding/cloudberry-orange.png <output-dir>
(must be given the plain orange sprite; it checks the palette.)
"""
import numpy as np, subprocess, sys, os
src, out = sys.argv[1], sys.argv[2]
def load(p):
    w, h = map(int, subprocess.check_output(["identify", "-format", "%w %h", p]).split())
    return np.frombuffer(subprocess.check_output(["convert", p, "-depth", "8", "rgba:-"]), np.uint8).reshape(h, w, 4).copy()
def save(a, p):
    h, w, _ = a.shape
    subprocess.run(["convert", "-size", f"{w}x{h}", "-depth", "8", "rgba:-", "-strip", f"PNG32:{p}"], input=np.ascontiguousarray(a).tobytes(), check=True)
def hx(c): return np.array([int(c[i:i+2], 16) for i in (1, 3, 5)], np.uint8)
def key(px): return "#%02X%02X%02X" % tuple(px[:3])

spr = load(src); H, W = spr.shape[:2]
LEAF = ["#063340", "#10474F", "#1A6061", "#248178"]                       # dark -> light
BODY = ["#87300A", "#A6430E", "#C05611", "#DA6E17", "#F0881D", "#FA9B25", "#FFC853", "#FEF8AD"]
INNER, RIM, OUTLINE = "#502215", "#2C2225", "#1B303F"
assert set(LEAF + BODY + [INNER, RIM, OUTLINE]) == {key(spr[y, x]) for y in range(H) for x in range(W) if spr[y, x, 3]}

# 8-step body ramps and 4-step leaf ramps built around the official flag colours
R = {
 "yellow":  ["#7A4A00", "#9C6400", "#BF8200", "#DDA000", "#F2B800", "#FECC02", "#FFE066", "#FFF6C2"],
 "carmine": ["#4E1015", "#651820", "#7E222B", "#9E3039", "#B53F48", "#C9555D", "#E3858B", "#F8D5D7"],
 "blue":    ["#00203F", "#002F5C", "#003F78", "#005590", "#006AA7", "#2A86C0", "#6FB0DE", "#CFE6F7"],
 "white":   ["#8C8F96", "#A3A6AD", "#B9BCC2", "#CDD0D5", "#DEE0E4", "#ECEEF0", "#F8F9FA", "#FFFFFF"],
 "orange":  BODY,
}
LR = {"blue": ["#001F3D", "#00437A", "#006AA7", "#3D93CF"], "blue_y": ["#001F3D", "#00437A", "#006AA7", "#FECC02"],
      "carmine_w": ["#3A0D12", "#6E1F27", "#9E3039", "#FFFFFF"], "teal": LEAF}
INNER_FOR = {"yellow": "#5A3600", "carmine": "#3A0D12", "blue": "#001A33", "white": "#6E7178", "orange": INNER}

def recolour(body_region, leaf_ramp, outline=OUTLINE, rim=RIM):
    a = spr.copy()
    for y in range(H):
        for x in range(W):
            if not a[y, x, 3]: continue
            c = key(a[y, x])
            if c in LEAF:  a[y, x, :3] = hx(LR[leaf_ramp][LEAF.index(c)])
            elif c in BODY: a[y, x, :3] = hx(R[body_region(x, y)][BODY.index(c)])
            elif c == INNER: a[y, x, :3] = hx(INNER_FOR[body_region(x, y)])
            elif c == OUTLINE: a[y, x, :3] = hx(outline)
            elif c == RIM: a[y, x, :3] = hx(rim)
    return a

# Body geometry: berry body is rows 9..27, cols 0..20; lobe rows divide at ~15/16 and ~21/22
lat_stripe = lambda y: 16 <= y <= 18                               # Latvian 2:1:2-ish white band
swe_cross  = lambda x, y: 16 <= y <= 18 or 6 <= x <= 8             # Nordic cross, offset to the hoist
variants = {
 "1_accent":         recolour(lambda x, y: "orange", "blue_y", outline="#7E222B"),
 "2_swedish":        recolour(lambda x, y: "yellow", "blue"),
 "3_latvia_body":    recolour(lambda x, y: "white" if lat_stripe(y) else "carmine", "blue_y"),
 "4_sweden_body":    recolour(lambda x, y: "yellow" if swe_cross(x, y) else "blue", "carmine_w"),
 "5_split":          recolour(lambda x, y: ("white" if lat_stripe(y) else "carmine") if x <= 10 else ("yellow" if swe_cross(x - 4, y) and x >= 10 else "blue"), "teal"),
}
for k, v in variants.items(): save(v, os.path.join(out, f"{k}.png"))

# 6: original berry on a split flag background (icon canvas 40x40): Latvia left, Sweden right
bg = np.zeros((40, 40, 4), np.uint8); bg[..., 3] = 255
for y in range(40):
    for x in range(40):
        if x < 20: bg[y, x, :3] = hx("#FFFFFF" if 16 <= y <= 23 else "#9E3039")
        else:      bg[y, x, :3] = hx("#FECC02" if (16 <= y <= 23 or 25 <= x <= 30) else "#006AA7")
m = spr[..., 3] > 0; bg[6:6 + H, 9:9 + W][m] = spr[m]
save(bg, os.path.join(out, "6_flag_backdrop_icon.png"))
print("ok", list(variants) + ["6_flag_backdrop_icon"])
