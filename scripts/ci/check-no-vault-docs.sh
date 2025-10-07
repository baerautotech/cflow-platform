#!/usr/bin/env bash

set -euo pipefail

echo "[CI Guard] Checking for forbidden Vault documentation..."

violations=$(git ls-tree -r HEAD --name-only | grep -Ei 'vault' || true)

if [[ -n "${violations}" ]]; then
  echo "[ERROR] Vault-related files detected:" >&2
  echo "${violations}" >&2
  echo "Sealed Secrets is the authoritative system; remove or update these files." >&2
  exit 1
fi

echo "[CI Guard] Vault references absent."

