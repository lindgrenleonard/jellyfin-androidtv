#!/usr/bin/env bash
# Builds a signed, optimized release APK of the custom build.
#
# Signing credentials are read from ~/.android/jellyfin-custom-signing.env
# (KEYSTORE_FILE, KEYSTORE_PASSWORD, SIGNING_KEY_ALIAS, SIGNING_KEY_PASSWORD).
# Keep that file and the keystore backed up: updates must be signed with the same key.
#
# Usage: ./branding/build-release.sh [extra gradle args, e.g. -Pcustom.abi=arm64-v8a]
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
signing_env="${SIGNING_ENV:-$HOME/.android/jellyfin-custom-signing.env}"

# shellcheck disable=SC1090
source "$signing_env"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
# Version name/code shown in the app (code 191099 for 0.19.10)
export JELLYFIN_VERSION="${JELLYFIN_VERSION:-0.19.10}"

cd "$root"
./gradlew :app:assembleRelease "$@"

ls -lh app/build/outputs/apk/release/*.apk
