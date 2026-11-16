#!/usr/bin/env python3
"""
Builds the pixel-perfect branding masters from the cloudberry sprite.

Input:   branding/cloudberry.png  - the 21x28 sprite (one image pixel = one art pixel). Currently the
                                    Latvia/Sweden split design; the plain one is cloudberry-orange.png
Outputs: branding/icon.png        - 40x40 launcher icon canvas
         branding/banner.png      - 80x45 Android TV banner canvas
         branding/splash_logo.png - startup screen canvas (berry + glow + SPLASH_TEXT); the app
                                    draws it at the largest whole-number scale that fits
         branding/toolbar_logo.png - berry + NAME side by side, transparent, for the in-app toolbars
         branding/cloudberry.svg  - the sprite as a crisp vector (merged rectangles)

All Android sizes are integer multiples of these canvases (icon 2-8x, banner 2-8x),
so generate.sh scales them with nearest-neighbour and every art pixel stays square.

Requires numpy and ImageMagick (`convert`). Usage: python3 branding/pixel_assets.py
"""
import os
import subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_png(path):
    w, h = map(int, subprocess.check_output(["identify", "-format", "%w %h", path]).split())
    raw = subprocess.check_output(["convert", path, "-depth", "8", "rgba:-"])
    return np.frombuffer(raw, np.uint8).reshape(h, w, 4).copy()


def save_png(arr, path):
    h, w, _ = arr.shape
    subprocess.run(["convert", "-size", f"{w}x{h}", "-depth", "8", "rgba:-", "-strip", f"PNG32:{path}"],
                   input=np.ascontiguousarray(arr, np.uint8).tobytes(), check=True)


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)] + [255], np.uint8)


# Background ramp, centre to edge: a warm dark glow behind the berry (from the sprite's browns)
# fading into near-black navy. Deliberately avoids the leaf teals so the leaves stay readable.
RAMP = [hexrgb(c) for c in ("#4E2D1A", "#33231F", "#1A2329", "#0E1C24", "#081419")]
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
SHADOW = hexrgb("#081A23")
WHITE = hexrgb("#FFFFFF")


def background(w, h, cx, cy, radius):
    """Radial gradient quantised to RAMP with ordered (Bayer) dithering - classic pixel-art style."""
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt(((x + 0.5 - cx) / radius) ** 2 + ((y + 0.5 - cy) / radius) ** 2)
    t = np.clip(d, 0, 1) * (len(RAMP) - 1)
    lo = np.floor(t).astype(int)
    # Solid bands with dithering only in a narrow zone where two bands meet
    frac = np.clip((t - lo - 0.3) / 0.4, 0, 1)
    idx = np.minimum(lo + (frac > BAYER4[y % 4, x % 4]), len(RAMP) - 1)
    return np.stack(RAMP)[idx]


def paste(dst, src, x, y):
    m = src[..., 3] > 0
    dst[y:y + src.shape[0], x:x + src.shape[1]][m] = src[m]


ACCENT = hexrgb("#FECC02")          # Swedish flag yellow, matching the berry's cross
# Flag carmine #9E3039 and blue #006AA7, brightened slightly so the text stays legible on the dark navy
CARMINE, BLUE = hexrgb(os.environ.get("TEXT_CARMINE", "#C8414B")), hexrgb(os.environ.get("TEXT_BLUE", "#1E86CF"))
# Flag-striped letters: the stripe sits on font row 4, the middle of the lowercase x-height
# (rows 2-6), which gives both flags' 2:1:2 proportions on lowercase letters. Inks get the
# font row and the column within their segment.
SWEDEN_CROSS_COL = int(os.environ.get("SWEDEN_CROSS_COL", "6"))  # through the middle of the "a" (just left of centre, like the flag)
LATVIA = lambda row, col: WHITE if row == 4 else CARMINE
SWEDEN = lambda row, col: ACCENT if row == 4 or col == SWEDEN_CROSS_COL else BLUE

# Text as (text, ink) segments; ink is a colour or a function of the font row
NAME = [("Evve", LATVIA), ("nard", SWEDEN)]
SPLASH_TEXT = NAME + [(" TV", ACCENT)]
BANNER_LINES = (NAME, [("TV", ACCENT)])
SPLASH_BACKGROUND = "#081419"  # must match @color/splash_background (last RAMP colour)

# Pixel font, 9 rows: cap height 7, x-height 5, 2 rows of descender. '#' = ink.
GLYPHS = {
    " ": ["..", "..", "..", "..", "..", "..", "..", "..", ".."],
    "E": ["####", "#...", "#...", "###.", "#...", "#...", "####", "....", "...."],
    "J": ["..##", "...#", "...#", "...#", "#..#", "#..#", ".##.", "....", "...."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..", ".....", "....."],
    "V": ["#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#..", ".....", "....."],
    "a": ["....", "....", ".##.", "...#", ".###", "#..#", ".###", "....", "...."],
    "d": ["...#", "...#", ".###", "#..#", "#..#", "#..#", ".###", "....", "...."],
    "r": ["....", "....", "#.##", "##..", "#...", "#...", "#...", "....", "...."],
    "v": [".....", ".....", "#...#", "#...#", ".#.#.", ".#.#.", "..#..", ".....", "....."],
    "e": ["....", "....", ".##.", "#..#", "####", "#...", ".###", "....", "...."],
    "l": ["##.", ".#.", ".#.", ".#.", ".#.", ".#.", "..#", "...", "..."],
    "y": ["....", "....", "#..#", "#..#", "#..#", "#..#", ".###", "...#", ".##."],
    "f": ["..##", ".#..", "####", ".#..", ".#..", ".#..", ".#..", "....", "...."],
    "i": ["#", ".", "#", "#", "#", "#", "#", ".", "."],
    "n": ["....", "....", "###.", "#..#", "#..#", "#..#", "#..#", "....", "...."],
}


def wordmark(text, ink=WHITE, shadow=SHADOW):
    """Render text (a str, or a list of (text, ink) segments) in the pixel font with a 1px shadow.
    An ink is a colour or a function of (font row 0-8, column within its segment) returning a colour."""
    segments = [(text, ink)] if isinstance(text, str) else text
    cols, inks = [], []          # inks: (ink, column within segment) per output column
    for seg_text, seg_ink in segments:
        seg_col = 0
        for ch in seg_text:
            if cols:
                cols.append(np.zeros((9, 1), bool)); inks.append((seg_ink, seg_col - 1 if seg_col else -1))
            g = np.array([[c == "#" for c in row] for row in GLYPHS[ch]])
            cols.append(g)
            inks.extend((seg_ink, seg_col + i) for i in range(g.shape[1]))
            seg_col += g.shape[1] + 1
    mask = np.concatenate(cols, axis=1)
    h, w = mask.shape
    out = np.zeros((h + 1, w + 1, 4), np.uint8)
    out[1:, 1:][mask] = shadow          # 1px drop shadow, bottom-right
    for x in range(w):
        for y in range(h):
            if mask[y, x]:
                ink_x, seg_x = inks[x]
                out[y, x] = ink_x(y, seg_x) if callable(ink_x) else ink_x
    return out


def sprite_svg(sprite):
    """One <path> per colour; each path is the colour's pixels merged into maximal rectangles."""
    h, w, _ = sprite.shape
    paths = {}
    used = np.zeros((h, w), bool)
    for y in range(h):
        for x in range(w):
            if used[y, x] or sprite[y, x, 3] == 0: continue
            col = tuple(sprite[y, x, :3])
            same = lambda yy, xx: not used[yy, xx] and sprite[yy, xx, 3] > 0 and tuple(sprite[yy, xx, :3]) == col
            x2 = x
            while x2 + 1 < w and same(y, x2 + 1): x2 += 1
            y2 = y
            while y2 + 1 < h and all(same(y2 + 1, xx) for xx in range(x, x2 + 1)): y2 += 1
            used[y:y2 + 1, x:x2 + 1] = True
            paths.setdefault(col, []).append(f"M{x} {y}h{x2 - x + 1}v{y2 - y + 1}h-{x2 - x + 1}z")
    body = "\n".join(f'  <path fill="#{r:02X}{g:02X}{b:02X}" d="{"".join(d)}"/>' for (r, g, b), d in paths.items())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w * 16}" height="{h * 16}" '
            f'shape-rendering="crispEdges">\n{body}\n</svg>\n'), sum(len(d) for d in paths.values())


def main():
    berry = load_png(os.path.join(HERE, "cloudberry.png"))
    bh, bw = berry.shape[:2]

    # Icon: 40x40, berry centred (one pixel low so the leaves have room)
    icon = background(40, 40, 20, 21, 26)
    paste(icon, berry, (40 - bw) // 2, (40 - bh) // 2 + 1)
    save_png(icon, os.path.join(HERE, "icon.png"))

    # Banner: 80x45, berry left, two stacked lines right (left-aligned), block centred on the berry
    line1, line2 = wordmark(BANNER_LINES[0]), wordmark(BANNER_LINES[1])
    gap, cap, leading = 5, 7, 4
    text_w = max(line1.shape[1], line2.shape[1])
    left = (80 - bw - gap - text_w) // 2
    berry_y = (45 - bh) // 2 + 1
    text_y = berry_y + (bh - (cap + leading + cap)) // 2 + 1
    banner = background(80, 45, left + bw / 2, 22.5, 52)
    paste(banner, berry, left, berry_y)
    paste(banner, line1, left + bw + gap, text_y)
    paste(banner, line2, left + bw + gap, text_y + cap + leading)
    save_png(banner, os.path.join(HERE, "banner.png"))
    word = line1

    # Startup screen: berry with glow, text underneath. The glow fades fully into
    # SPLASH_BACKGROUND before the canvas edges, so it blends into the screen seamlessly.
    text = wordmark(SPLASH_TEXT)
    sw, sh = max(72, text.shape[1] + 16), 60
    by = 8
    glow_r = min(by + bh / 2, sw / 2) - 1
    splash = background(sw, sh, sw / 2, by + bh / 2, glow_r)
    assert all((splash[e] == hexrgb(SPLASH_BACKGROUND)).all() for e in (0, -1)), "glow must not reach the canvas edge"
    assert (splash[:, 0] == hexrgb(SPLASH_BACKGROUND)).all() and (splash[:, -1] == hexrgb(SPLASH_BACKGROUND)).all()
    paste(splash, berry, (sw - bw) // 2, by)
    paste(splash, text, (sw - text.shape[1]) // 2 + 1, by + bh + 6)
    save_png(splash, os.path.join(HERE, "splash_logo.png"))

    # Toolbar logo: berry + name side by side on a transparent background (it sits on backdrops).
    # The text's x-height (font rows 2-6) is centred on the berry body (sprite rows 9-27).
    name = wordmark(NAME)
    gap = 4
    toolbar = np.zeros((bh, bw + gap + name.shape[1], 4), np.uint8)
    paste(toolbar, berry, 0, 0)
    paste(toolbar, name, bw + gap, (9 + 27) // 2 - 4)
    save_png(toolbar, os.path.join(HERE, "toolbar_logo.png"))

    svg, rects = sprite_svg(berry)
    with open(os.path.join(HERE, "cloudberry.svg"), "w") as f: f.write(svg)
    print(f"icon 40x40, banner 80x45 (wordmark {word.shape[1]}x{word.shape[0]}), splash {sw}x{sh}, toolbar {toolbar.shape[1]}x{toolbar.shape[0]}, svg {rects} rects, "
          f"{len(np.unique(berry[berry[..., 3] > 0][:, :3], axis=0))} colours")


if __name__ == "__main__":
    main()
