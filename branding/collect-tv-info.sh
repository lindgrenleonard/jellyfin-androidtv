#!/usr/bin/env bash
# Collects hardware/software info from an Android TV over adb, to decide on build
# optimizations. It only runs queries and changes no settings or data; the one visible
# effect is that it launches and closes the installed Jellyfin app 3 times to time startup.
#
# Usage: ./branding/collect-tv-info.sh <tv-ip>[:port] [output-file]
#        ./branding/collect-tv-info.sh usb [output-file]     (USB-connected device)
set -uo pipefail

ADB="${ADB:-$HOME/Android/Sdk/platform-tools/adb}"
target="${1:?usage: $0 <tv-ip>[:port] | usb [output-file]}"
out="${2:-tv-info-$(date +%Y%m%d-%H%M%S).txt}"

if [ "$target" != "usb" ]; then
	[[ "$target" == *:* ]] || target="$target:5555"
	"$ADB" connect "$target" >&2
	export ANDROID_SERIAL="$target"
fi

"$ADB" wait-for-device
sh() { "$ADB" shell "$@" 2>&1 | tr -d '\r'; }
section() { printf '\n===== %s =====\n' "$1"; }

{
	section "Device / OS"
	for p in ro.product.brand ro.product.manufacturer ro.product.model ro.product.device ro.product.board \
		ro.board.platform ro.hardware ro.build.version.release ro.build.version.sdk ro.build.fingerprint \
		ro.product.cpu.abi ro.product.cpu.abi2 ro.product.cpu.abilist ro.product.cpu.abilist32 ro.product.cpu.abilist64 \
		ro.sf.lcd_density ro.config.low_ram persist.sys.dalvik.vm.lib.2 \
		dalvik.vm.heapsize dalvik.vm.heapgrowthlimit dalvik.vm.heapstartsize dalvik.vm.isa.arm.variant; do
		printf '%-34s %s\n' "$p" "$(sh getprop "$p")"
	done

	section "CPU (/proc/cpuinfo)"
	sh cat /proc/cpuinfo
	section "CPU max frequencies (kHz)"
	sh 'for f in /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_max_freq; do echo "$f: $(cat $f)"; done'

	section "Memory (/proc/meminfo)"
	sh cat /proc/meminfo | head -8

	section "Display"
	sh wm size
	sh wm density
	sh dumpsys display | grep -iE 'mDisplayInfos|DisplayDeviceInfo|density|refresh|fps|hdr|mode' | head -30

	section "Storage"
	sh df /data

	section "OpenGL ES"
	sh dumpsys SurfaceFlinger | grep -iE 'GLES|OpenGL' | head -5

	section "Media codec config files"
	for f in $(sh ls /system/etc/media_codecs*.xml /vendor/etc/media_codecs*.xml 2>/dev/null | grep -v 'No such'); do
		printf '\n--- %s\n' "$f"
		sh cat "$f"
	done

	section "Audio (HDMI / passthrough hints)"
	sh dumpsys audio | grep -iE 'hdmi|encoding|passthrough|surround|ac3|dts' | head -30
	sh dumpsys media.audio_flinger | grep -iE 'hdmi|direct|ac3|dts|channel|format' | head -40

	section "Installed Jellyfin apps"
	for pkg in org.jellyfin.androidtv org.jellyfin.androidtv.debug; do
		info="$(sh dumpsys package "$pkg" | grep -E 'versionName|versionCode|firstInstallTime|lastUpdateTime|primaryCpuAbi' | sed 's/^ *//')"
		[ -n "$info" ] && printf '%s\n%s\n' "$pkg" "$info"
	done

	section "Jellyfin memory usage (only if the app is running)"
	sh dumpsys meminfo org.jellyfin.androidtv | head -40

	section "Cold start time of the installed Jellyfin app (3 runs)"
	if sh pm list packages | grep -q '^package:org.jellyfin.androidtv$'; then
		for i in 1 2 3; do
			sh am force-stop org.jellyfin.androidtv
			sleep 2
			sh am start -W -n org.jellyfin.androidtv/.ui.startup.StartupActivity | grep -E 'ThisTime|TotalTime|WaitTime'
			sleep 4
		done
		sh am force-stop org.jellyfin.androidtv
	else
		echo "org.jellyfin.androidtv not installed"
	fi
} > "$out"

echo "Wrote $out ($(wc -l < "$out") lines)" >&2
