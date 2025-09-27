#!/bin/sh
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
OVERLAY_DIR="$ROOT_DIR/.vendor-overrides/bmad"
VENDOR_DIR="$ROOT_DIR/vendor/bmad"

if [ ! -d "$OVERLAY_DIR" ]; then
  echo "No overlay dir: $OVERLAY_DIR" >&2
  exit 1
fi
if [ ! -d "$VENDOR_DIR" ]; then
  echo "No vendor dir: $VENDOR_DIR" >&2
  exit 1
fi

echo "Applying vendor overrides from $OVERLAY_DIR to $VENDOR_DIR..."
# Portable flags: -a (archive), --checksum for safety; DO NOT delete outside overlay scope
rsync -a --checksum "$OVERLAY_DIR/" "$VENDOR_DIR/"
echo "Done."

