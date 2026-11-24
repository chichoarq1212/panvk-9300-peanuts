#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORK=$ROOT/work
BASE=3c82008657f3edd44cc5fbed4c2f80f8a29c90fc
MESA_SHA=5a07217f034b3e50d8c7c7794f97a2df1742613b
MODE=$1
[[ "$MODE" == baseline || "$MODE" == e01 ]]
: "$ANDROID_NDK_ROOT"
mkdir -p "$WORK" "$ROOT/out/$MODE"
UP="$WORK/zenith-$MODE"
MESA="$UP/work/mesa"
[[ ! -e "$UP" ]]
git init -q "$UP"
git -C "$UP" remote add origin https://github.com/zenithblue-oss/panvk-kbase-android.git
git -C "$UP" fetch --depth=1 origin "$BASE"
git -C "$UP" checkout --detach FETCH_HEAD
[[ $(git -C "$UP" rev-parse HEAD) == "$BASE" ]]
mkdir -p "$MESA"
git init -q "$MESA"
git -C "$MESA" remote add origin https://gitlab.freedesktop.org/mesa/mesa.git
if ! git -C "$MESA" fetch --depth=1 origin "$MESA_SHA"; then
  git -C "$MESA" fetch --depth=1 https://github.com/chaotic-cx/mesa-mirror.git "$MESA_SHA"
fi
git -C "$MESA" checkout --detach FETCH_HEAD
[[ $(git -C "$MESA" rev-parse HEAD) == "$MESA_SHA" ]]
git -C "$MESA" config user.name 'PANVK9300 build'
git -C "$MESA" config user.email 'build@example.invalid'
"$UP/scripts/prepare-rc5-tree.sh" --mesa "$MESA" --csf-max 233 --wip-max 0175
if [[ "$MODE" == e01 ]]; then
  python3 "$ROOT/scripts/apply_e01.py" "$MESA"
  git -C "$MESA" diff --check
  git -C "$MESA" diff > "$ROOT/out/$MODE/e01-applied.patch"
  git -C "$MESA" add src/panfrost/vulkan/panvk_vX_cmd_meta.c
  git -C "$MESA" commit -m 'E01: guard meta descriptor copies and trace color clears on arch 12'
fi
export MESA
export PANVK_JOBS=4
export BDIR="$UP/build/android-bionic"
export DDIR="$UP/dist/android-g615-v11-csf"
"$UP/scripts/build-android.sh" --profile g615-v11-csf --api 29 --ndk "$ANDROID_NDK_ROOT"
SO="$DDIR/libvulkan_panfrost.so"
"$UP/scripts/validate-binary.sh" --abi android "$SO"
RAW=$(find "$BDIR" -name libvulkan_panfrost.so -type f -print -quit)
[[ -n "$RAW" ]]
cp "$RAW" "$ROOT/out/$MODE/libvulkan_panfrost.unstripped.so"
python3 "$ROOT/scripts/package.py" "$SO" "$ROOT/out/$MODE" "$MODE" "$UP" "$MESA"
