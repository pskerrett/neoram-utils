#!/usr/bin/env bash
# Build NeoRAM utils from source.
#   ./build.sh [outdir]   -> outdir/neoram-utils.d64, the PRGs on it, the BASIC listings and md5.txt
# Needs python3 and VICE's petcat and c1541.
set -eu
cd "$(dirname "$0")"
OUT=$(mkdir -p "${1:-release}" && cd "${1:-release}" && pwd)
GV=$(sed -n 's/^VER = "\(.*\)"$/\1/p' src/mkgeodiag.py)
NV=$(sed -n 's/^VER = "\(.*\)"$/\1/p' src/mkneocopy.py)
python3 src/mkgeodiag.py "$OUT"
python3 src/mkneocopy.py "$OUT"
python3 src/mkmenu.py "$OUT" "$GV" "$NV"
rm -f "$OUT/neoram-utils.d64"
# the menu first, so LOAD"*",8 finds it; short names, easy to type
c1541 -format "neoram utils,nu" d64 "$OUT/neoram-utils.d64" \
      -write "$OUT/menu.prg" "neoram utils" \
      -write "$OUT/geodiag64-v$GV.prg" "geodiag" \
      -write "$OUT/neocopy-v$NV.prg" "neocopy" \
      -write "$OUT/geodiag128-v$GV.prg" "geodiag128" >/dev/null
rm "$OUT/menu.prg"
( cd "$OUT" && md5sum neoram-utils.d64 geodiag64-v"$GV".prg geodiag128-v"$GV".prg neocopy-v"$NV".prg | tee md5.txt )
