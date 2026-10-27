#!/usr/bin/env python3
"""
Build the NeoRAM utils boot menu, the first file on the disk:

    mkmenu.py [outdir]      -> menu.prg (C64, $0801)

LOAD"*",8 and RUN show it; 1 starts GEODIAG, 2 NEOCOPY. The chosen program
is loaded from the same drive by a small helper in the cassette buffer
(the menu itself is overwritten by the load) and RUN, as LOAD and RUN
typed by hand would.

Needs VICE's petcat.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from asm import assemble  # noqa: E402

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else HERE
VER = "1.0"

# SETLFS 1,DEV,1 / SETNAM / LOAD to the file's own address, then the end of
# the program into VARTAB and RUN. A failed load comes back to BASIC with
# the KERNAL's error number in ERR.
ML = """
        lda #1
        ldx DEV
        ldy #1
        jsr SETLFS
        lda NLEN
        ldx #<NAME
        ldy #>NAME
        jsr SETNAM
        lda #0
        jsr LOAD
        bcs lderr
        stx $2D
        sty $2E
        jsr $A659       ; CLR, and TXTPTR to the start of the program
        jmp $A7AE       ; RUN
lderr:  sta ERR
        rts
DEV:    .byte 8
NLEN:   .byte 0
ERR:    .byte 0
NAME:   .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
"""

BASIC = r"""
10 rem neoram utils {VER}: choose geodiag or neocopy
20 ml={ORG}:for i=0 to {LEN}-1:read v:poke ml+i,v:next
30 dv=peek(186):if dv<8 or dv>30 then dv=8
40 print chr$(147)chr$(142)"neoram utils {VER}":print
50 print " 1  geodiag {GVER}: test the card,":print "    every ram pin and every byte":print
60 print " 2  neocopy {NVER}: enthusi's neoram-drive":print "    install, format, copy files, start":print
70 print " q  quit":print
80 get k$:if k$="1" then n$="geodiag":goto 200
90 if k$="2" then n$="neocopy":goto 200
100 if k$="q" then end
110 goto 80
200 print "loading "n$" from drive"dv
210 poke {DEV},dv:poke {NLEN},len(n$):poke {ERR},0
220 for i=1 to len(n$):poke {NAME}+i-1,asc(mid$(n$,i,1)):next
230 sys ml
240 print "could not load it (error"peek({ERR})")":end
"""


def build(out, gver, nver):
    org = 0x033C
    eq = {"SETLFS": 0xFFBA, "SETNAM": 0xFFBD, "LOAD": 0xFFD5}
    code, syms = assemble(ML, org, eq)
    assert org + len(code) <= 0x03FC
    subs = {k: syms[k] for k in ("DEV", "NLEN", "ERR", "NAME")}
    subs.update(ORG=org, LEN=len(code), VER=VER, GVER=gver, NVER=nver)
    src = BASIC
    for k, v in subs.items():
        src = src.replace("{%s}" % k, str(v))
    assert "{" not in src, src[src.index("{"):][:20]
    lines = src.strip("\n").splitlines()
    n = 9600
    for i in range(0, len(code), 18):
        lines.append("%d data %s" % (n, ",".join(str(c) for c in code[i:i + 18])))
        n += 1
    bas = os.path.join(OUT, "menu.bas")
    with open(bas, "w") as f:
        f.write("\n".join(lines) + "\n")
    subprocess.check_call(["petcat", "-w2", "-o", out, "--", bas])
    print("%s: %d bytes (helper %d bytes at $%04X)" % (out, os.path.getsize(out), len(code), org))


if __name__ == "__main__":
    build(os.path.join(OUT, "menu.prg"), sys.argv[2], sys.argv[3])
