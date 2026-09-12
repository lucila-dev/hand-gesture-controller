#!/bin/bash
# Build Gesture Control.app for macOS (requires Apple Silicon or Intel Mac).
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

pip install -q -r requirements.txt -r requirements-build.txt

echo "Building Gesture Control.app …"
pyinstaller gesture_control.spec --noconfirm --clean

OUT="dist/Gesture Control.app"
if [[ ! -d "$OUT" ]]; then
  echo "Build failed — $OUT not found" >&2
  exit 1
fi

echo "Built: $OUT"
echo "Test: open \"$OUT\""

ZIP="dist/Gesture-Control-macOS.zip"
rm -f "$ZIP"
ditto -c -k --keepParent "$OUT" "$ZIP"
echo "Archive: $ZIP"

