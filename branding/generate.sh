#!/usr/bin/env bash
# Regenerates the app's launcher icon, TV banner and splash logo from the
# source images in this directory. Requires ImageMagick (`convert`).
#
#   branding/icon.png         square                    -> mipmap-*/app_icon.png
#   branding/banner.png       16:9                      -> mipmap-*/app_banner.png  (Android TV home screen tile)
#   branding/splash_logo.png  any size, transparent bg  -> drawable-nodpi/splash_logo.png
#
# Pixel art: icon.png, banner.png, splash_logo.png and toolbar_logo.png are built by pixel_assets.py
# (40x40, 80x45 and 73x60 canvases). When a target size is an exact multiple of the source,
# it is scaled with nearest-neighbour so every art pixel stays crisp; otherwise it is
# resized smoothly (for high-resolution, non-pixel-art images).
#
# Usage: ./branding/generate.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
res="$here/../app/src/main/res"

# density -> launcher icon size (px), banner size (px)
declare -A icon=([mdpi]=80 [hdpi]=120 [xhdpi]=160 [xxhdpi]=240 [xxxhdpi]=320)
declare -A banner=([mdpi]=160x90 [hdpi]=240x135 [xhdpi]=320x180 [xxhdpi]=480x270 [xxxhdpi]=640x360)

# Pixel-art masters are generated from the sprite when present
if [ -f "$here/cloudberry.png" ] && [ -f "$here/pixel_assets.py" ]; then
	python3 -I "$here/pixel_assets.py"
fi

# scale <src> <WxH> <dst>: nearest-neighbour for exact integer multiples, smooth otherwise
scale() {
	local src="$1" size="$2" dst="$3" sw sh tw th
	read -r sw sh < <(identify -format '%w %h\n' "$src")
	tw="${size%x*}"; th="${size#*x}"
	if (( tw % sw == 0 && th % sh == 0 && tw / sw == th / sh )); then
		convert "$src" -filter point -resize "$((tw / sw * 100))%" -strip "PNG32:$dst"
	else
		convert "$src" -resize "${size}^" -gravity center -extent "$size" -strip "$dst"
	fi
}

for d in "${!icon[@]}"; do
	mkdir -p "$res/mipmap-$d"
	scale "$here/icon.png" "${icon[$d]}x${icon[$d]}" "$res/mipmap-$d/app_icon.png"
	scale "$here/banner.png" "${banner[$d]}" "$res/mipmap-$d/app_banner.png"
done

# Splash logo: copied as-is (the app scales pixel art itself); oversized images are capped at 1200px
mkdir -p "$res/drawable-nodpi"
convert "$here/splash_logo.png" -resize '1200x1200>' -strip "PNG32:$res/drawable-nodpi/splash_logo.png"
# Toolbar logo: pixel art, scaled by the app (PixelArtImage)
convert "$here/toolbar_logo.png" -strip "PNG32:$res/drawable-nodpi/toolbar_logo.png"

echo "Branding assets regenerated."
