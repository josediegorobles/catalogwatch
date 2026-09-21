#!/usr/bin/env bash
# Live demo used for the product video/GIF. Reads a real public store; no keys required.
set -euo pipefail

STORE="${1:-https://www.allbirds.com}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

CW="${CATALOGWATCH_BIN:-}"
if [ -z "$CW" ]; then
  if [ -x ".venv/bin/catalogwatch" ]; then
    CW=".venv/bin/catalogwatch"
  else
    CW="catalogwatch"
  fi
fi

echo "\$ catalogwatch fetch --store $STORE --out catalog.csv --max-pages 1"
"$CW" fetch --store "$STORE" --out "$WORK/catalog.csv" --max-pages 1
echo
echo "\$ head -3 catalog.csv"
head -3 "$WORK/catalog.csv"
echo
echo "\$ catalogwatch watch --store $STORE --out changes.csv --state-dir state --max-pages 1"
"$CW" watch --store "$STORE" --out "$WORK/changes.csv" --state-dir "$WORK/state" --max-pages 1
echo
echo "\$ catalogwatch watch ... (second run: nothing changed)"
"$CW" watch --store "$STORE" --out "$WORK/changes.csv" --state-dir "$WORK/state" --max-pages 1
echo
echo "\$ catalogwatch watch ... --telegram --dry-run --notify-empty"
"$CW" watch --store "$STORE" --out "$WORK/changes.csv" --state-dir "$WORK/state" --max-pages 1 \
  --telegram --dry-run --notify-empty
