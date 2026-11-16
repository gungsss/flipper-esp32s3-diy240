#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM="${UPSTREAM_URL:-https://github.com/Sor3nt/Flipper-Zero-ESP32-Port.git}"
PIN="e6ec11972a8e025d7ab686a6ef3016cf52360834"
TARGET="${SOURCE_DIR:-$ROOT/.work/upstream}"
if [[ -d "$TARGET/.git" ]]; then
  ACTUAL="$(git -C "$TARGET" rev-parse HEAD)"
  [[ "$ACTUAL" == "$PIN" ]] || { echo "Existing source checkout is $ACTUAL, not required $PIN. Move/remove $TARGET." >&2; exit 1; }
  echo "Upstream checkout verified: $ACTUAL"
  exit 0
fi
if [[ -e "$TARGET" ]]; then echo "Target is not an existing Git checkout: $TARGET" >&2; exit 1; fi
mkdir -p "$(dirname "$TARGET")" "$TARGET"
git -C "$TARGET" init -q
git -C "$TARGET" remote add origin "$UPSTREAM"
git -C "$TARGET" fetch --no-tags --depth 1 origin "$PIN"
git -C "$TARGET" checkout -q --detach FETCH_HEAD
ACTUAL="$(git -C "$TARGET" rev-parse HEAD)"
[[ "$ACTUAL" == "$PIN" ]] || { echo "Wrong upstream revision: $ACTUAL" >&2; exit 1; }
printf 'Fetched upstream commit: %s\n' "$ACTUAL"
