#!/usr/bin/env bash
# Build GEODIAG from source.
#   ./build.sh [outdir]   -> outdir/geodiag64-vX.prg, geodiag128-vX.prg, geodiag64.d64 (+ the BASIC listings)
# Needs python3 and VICE's petcat and c1541.
set -eu
cd "$(dirname "$0")"
OUT=$(mkdir -p "${1:-release}" && cd "${1:-release}" && pwd)
python3 src/mkgeodiag.py "$OUT"
VER=$(sed -n 's/^VER = "\(.*\)"$/\1/p' src/mkgeodiag.py)
rm -f "$OUT/geodiag64.d64"
# one file called just "geodiag", so LOAD"GEODIAG",8 is easy to type
c1541 -format "geodiag $VER,gd" d64 "$OUT/geodiag64.d64" -write "$OUT/geodiag64-v$VER.prg" "geodiag" >/dev/null
( cd "$OUT" && md5sum geodiag64-v"$VER".prg geodiag128-v"$VER".prg geodiag64.d64 | tee md5.txt )
