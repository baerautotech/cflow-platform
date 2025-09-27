#!/bin/sh
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
OVERLAY_DIR="$ROOT_DIR/.vendor-overrides/bmad"
VENDOR_DIR="$ROOT_DIR/vendor/bmad"

if [ ! -d "$OVERLAY_DIR" ] || [ ! -d "$VENDOR_DIR" ]; then
  echo "Missing overlay or vendor dir" >&2
  exit 1
fi

echo "Checking vendor overrides alignment..."
STATUS=0
while IFS= read -r -d '' file; do
  rel="${file#$OVERLAY_DIR/}"
  left="$file"
  right="$VENDOR_DIR/$rel"
  if [ ! -f "$right" ]; then
    echo "MISSING in vendor: $rel" >&2
    STATUS=2
    continue
  fi
  if ! diff -u "$left" "$right" >/dev/null; then
    echo "DIFFERS: $rel" >&2
    STATUS=3
  fi
done < <(find "$OVERLAY_DIR" -type f -print0)

if [ $STATUS -eq 0 ]; then
  echo "All overrides match vendor."
else
  echo "Override drift detected (status=$STATUS)." >&2
fi
exit $STATUS

