#!/usr/bin/env python3
"""
Build NEOCOPY, an all-in-one tool for enthusi's NeoRAM-Drive (V0.40):

    mkneocopy.py [outdir]   -> neocopy-vX.prg (C64, $0801)

Installs the drive on the card (it carries the drive's own 7 pages, taken
from neoramdrive-040.prg), formats it, lists a source drive (the one it
was loaded from by default) and the NeoRAM-Drive, starts the drive
(SYS 57000), and copies PRG files from the source drive onto it.

It does not go through the drive's LOAD/SAVE hooks: loading a file to save
it again would land on top of this program for anything that is not a
BASIC program at $0801. Instead the file is read with OPEN/GET and written
straight into the drive's layout on the card (from neoram-040GPL.asm):

    card byte address L = block * 16384 + page * 256 + offset
    $0000-$06FF  the drive itself (page 0: the SYS 57000 starter at $DEA8)
    $0700 ...    files:  3 byte address of the next entry (lo, mid, hi)
                         name, 0
                         load address (lo, hi), then the data
                 the list ends with a next address of 0,0,0

A copy writes the name and data after the end marker, a new end marker
after the data, and only then points the old end marker at it: a copy that
fails part way leaves the drive as it was.

Needs VICE's petcat.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from asm import assemble  # noqa: E402

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else HERE
VER = "1.1"
DRIVE = os.path.join(HERE, "..", "third_party", "neoram-drive", "neoramdrive-040.prg")


def drive_pages():
    """The 7 pages neoramdrive-040's installer ($080d) writes to block 0:
    page 0 from launch_code ($08af), pages 1-6 from start_of_data ($09af),
    so card bytes $0000-$06ff are memory $08af-$0fae (past the file's end:
    0)."""
    d = open(DRIVE, "rb").read()
    assert d[:2] == b"\x01\x08" and len(d) == 1959, "not neoramdrive-040.prg"
    m = bytearray(65536)
    m[0x801:0x801 + len(d) - 2] = d[2:]
    # lda launch_code / sta $de00,x and, for pages 1-6, lda start_of_data
    assert m[0x815:0x818] == b"\xad\xaf\x08" and m[0x82b:0x82e] == b"\xad\xaf\x09"
    pages = bytes(m[0x8af:0x8af + 0x700])
    assert pages[0xA8:0xAB] == b"\x4c\x00\xde"     # SYS 57000: JMP $DE00
    return pages

# Copies the open logical file 2 onto the card from address DL/DM/DH on,
# stopping before page LM/LH (the end of the card, less a page for the
# end marker).
ML = """
        jmp copy
DL:     .byte 0,0,0     ; next card address (lo, mid, hi)
LM:     .byte 0,0       ; stop at this page (DM, DH)
CL:     .byte 0,0,0     ; bytes copied
RES:    .byte 0         ; 0 ok, 1 card full, 2 read error, 3 STOP, 4 not open
STV:    .byte 0         ; ST after the last read
TMP:    .byte 0

copy:   lda #0
        sta CL
        sta CL+1
        sta CL+2
        sta RES
        sta STV
        ldx #2
        jsr CHKIN
        bcc cloop
        lda #4
        sta RES
        jmp cdone
cloop:  jsr CHRIN
        tay
        lda ST
        sta STV
        and #$83                ; timeout, or no device; $40 is the end
        beq cspace
        lda #2
        sta RES
        jmp cdone
cspace: lda DL+1
        cmp LM
        bne cput
        lda DL+2
        cmp LM+1
        bne cput
        lda #1
        sta RES
        jmp cdone
; page = mid & 63; block = hi * 4 + mid / 64
cput:   lda DL+1
        and #63
        sta PG
        lda DL+1
        sta TMP
        lda DL+2
        asl TMP
        rol
        asl TMP
        rol
        sta BK
        ldx DL
        tya
        sta WIN,x
        inc CL
        bne cnext
        inc CL+1
        bne cnext
        inc CL+2
cnext:  inc DL
        bne cend
        inc DL+1
        bne cend
        inc DL+2
cend:   lda STV
        and #$40
        bne cdone
        lda STKEY
        cmp #$7F
        bne cloop
        lda #3
        sta RES
cdone:  jsr CLRCHN
        rts
"""

BASIC = r"""
1 rem neocopy {VER}: install, format, start and fill enthusi's neoram-drive
2 rem writes the drive's own layout on the card; needs no load or save
3 rem neoram-drive v0.40 (c) 2007,2008 martin wendt / enthusi, gpl v3+
10 ml={ORG}:dl={DL}:lm={LM}:cl={CL}:rs={RES}:sv={STV}
20 w=56832:p=57342:b=57343:dv=peek(186):nf=0:q$=chr$(34):if dv<8 or dv>30 then dv=8
30 dim n$(144),t$(144),bz(144),d$(200),bv(8),s(8)
40 print chr$(147)chr$(142)"neocopy {VER} for neoram-drive v0.40":print
50 cs=0:for i=0 to {LEN}-1:read v:poke ml+i,v:cs=cs+v:next
60 if cs<>{SUM} then print "bad data lines (checksum)":end
70 v=1:for i=1 to 8:bv(i)=v:v=v*2:next
80 gosub 5000
100 rem --- menu
110 print chr$(147)"neocopy {VER} for neoram-drive v0.40":print
120 gosub 6000:print
130 print " 1  list the source drive (drive "mid$(str$(dv),2)")"
140 print " 2  copy a file to the neoram-drive"
150 print " 3  list the neoram-drive"
160 print " 4  start neoram-drive (sys 57000)"
170 print " 5  install neoram-drive on the card"
180 print " 6  format the neoram-drive (erases it)"
185 print " 7  change the source drive"
190 print " q  quit":print
200 gosub 9500
210 if k$="7" then 1500
220 if k$="1" then gosub 2000:goto 900
230 if k$="3" then pr=1:print chr$(147);:gosub 3000:goto 900
240 if k$="2" then gosub 4000:goto 900
250 if k$="4" then gosub 5500:goto 900
255 if k$="5" then gosub 5600:goto 900
260 if k$="6" then gosub 3500:goto 900
270 if k$="q" then end
280 goto 200
900 print:print "press a key.":gosub 9500:goto 100
1500 rem --- source drive
1510 input "source drive (8-30)";dv:if dv<8 or dv>30 then 1510
1520 nf=0:goto 100
2000 rem --- list the source drive
2010 print chr$(147)"drive"dv:nf=0:ln=1
2020 open 15,dv,15:open 1,dv,0,"$":input#15,en,em$,et,es
2030 if en>=20 then print en;em$:goto 2190
2040 get#1,a$,a$
2050 get#1,a$,a$:if st then 2190
2060 get#1,a$,c$:bk=asc(a$+chr$(0))+256*asc(c$+chr$(0)):l$=""
2070 get#1,a$:if a$="" or st then 2090
2080 l$=l$+a$:goto 2070
2090 q1=0:q2=0:for i=1 to len(l$):if mid$(l$,i,1)<>q$ then 2110
2100 if q1=0 then q1=i:goto 2110
2105 if q2=0 then q2=i
2110 next
2120 if ln=1 or q2=0 or nf>=144 then print bk;l$:goto 2160
2130 nf=nf+1:n$(nf)=mid$(l$,q1+1,q2-q1-1):t$(nf)=mid$(l$,q2+1):bz(nf)=bk
2135 if left$(t$(nf),1)=" " then t$(nf)=mid$(t$(nf),2):goto 2135
2140 print right$("  "+str$(nf),4);right$("   "+str$(bk),5)" "q$n$(nf)q$;
2150 print tab(26)t$(nf)
2160 ln=ln+1:if ln<22 then 2050
2170 print "-- more: a key --";:gosub 9500:print:ln=2:goto 2050
2190 close 1:close 15:return
3000 rem --- walk the neoram-drive: te = end marker, ok = 0 if damaged
3005 la=1792:nd=0:ok=1:ln=0:if pr then print "neoram-drive ("mid$(str$(kb),2)" kb card)":print
3010 c0=la:gosub 7000:p0=v:la=c0+1:gosub 7000:p1=v:la=c0+2:gosub 7000
3020 pt=p0+256*p1+65536*v:la=c0
3030 if pt=0 then te=c0:goto 3200
3040 if pt<c0+6 or pt>ka-3 then ok=0:te=c0:goto 3200
3050 a$="":q=c0+3
3060 la=q:gosub 7000:if v=0 then 3080
3070 a$=a$+chr$(v):q=q+1:if len(a$)<32 then 3060
3075 ok=0:te=c0:goto 3200
3080 la=q+1:gosub 7000:l0=v:la=q+2:gosub 7000:ad=l0+256*v
3090 if nd<200 then nd=nd+1:d$(nd)=a$
3100 if pr=0 then 3150
3110 v=int((pt-c0)/256)+1:print right$("   "+str$(v),4)" "q$a$q$;tab(24)"load $";
3120 v=int(ad/256):gosub 9000:print h$;:v=ad and 255:gosub 9000:print h$
3130 ln=ln+1:if ln=20 then print "-- more: a key --";:gosub 9500:print:ln=0
3150 la=pt:goto 3010
3200 if pr=0 then return
3210 if ok=0 then print:print "** the file list is damaged or the":print "   card is not formatted (6) **":pr=0:return
3220 v=int((ka-te)/256):print:print v"blocks free"
3230 pr=0:return
3500 rem --- format
3510 print chr$(147)"format the neoram-drive: every file on"
3520 print "it is lost. the drive itself stays.":print:print "sure (y/n)?"
3530 gosub 9500:if k$<>"y" then print "not formatted.":return
3540 for la=1792 to 1795:v=0:gosub 7100:next:print "formatted.":return
4000 rem --- copy
4010 print chr$(147)"copy from drive"dv"to the neoram-drive":print
4020 if nf then print "file number from the list (1),"
4030 print "or a name (return: back)":input a$:if a$="" then return
4035 if val(a$)>0 and nf=0 then print "list the source drive first (1).":return
4040 nm$=a$:ty$="":if val(a$)>0 and val(a$)<=nf then nm$=n$(val(a$)):ty$=t$(val(a$))
4050 if ty$="" then 4070
4060 c=0:for i=1 to len(ty$)-2:if mid$(ty$,i,3)="prg" then c=1
4065 next:if c=0 then print q$nm$q$" is not a prg file.":return
4070 if len(nm$)>16 then print "name longer than 16.":return
4080 pr=0:gosub 3000:if ok=0 then print "the neoram-drive is damaged or not":print "formatted (6).":return
4090 for i=1 to nd:if d$(i)=nm$ then print q$nm$q$" is already on it.":return
4100 next
4110 ds=te+3+len(nm$)+1:if ds+256>ka then print "the neoram-drive is full.":return
4120 open 15,dv,15:open 2,dv,2,nm$+",p,r":input#15,en,em$,et,es
4130 if en>=20 then print en;em$:close 2:close 15:return
4140 la=te+3:for i=1 to len(nm$):v=asc(mid$(nm$,i,1)):gosub 7100:la=la+1:next:v=0:gosub 7100
4150 v=ds:gosub 7200:poke dl,v0:poke dl+1,v1:poke dl+2,v2
4160 v=ka-256:gosub 7200:poke lm,v1:poke lm+1,v2
4170 print "copying "q$nm$q$" (stop ends it)...":t=ti:sys ml
4180 r=peek(rs):n=peek(cl)+256*peek(cl+1)+65536*peek(cl+2)
4190 input#15,en,em$,et,es:close 2:close 15
4200 if r=0 and n>=2 then 4300
4210 if r=1 then print "the neoram-drive is full."
4220 if r=2 then print "read error (st"peek(sv)")":print en;em$
4230 if r=3 then print "stopped."
4240 if r=0 then print "the file is empty."
4250 print "nothing added: the neoram-drive is as":print "it was.":return
4300 e=ds+n:la=e:v=0:gosub 7100:la=e+1:gosub 7100:la=e+2:gosub 7100
4310 v=e:gosub 7200:la=te:v=v0:gosub 7100:la=te+1:v=v1:gosub 7100:la=te+2:v=v2:gosub 7100
4320 la=ds:gosub 7000:l0=v:la=ds+1:gosub 7000:ad=l0+256*v
4330 t=int((ti-t)/60+.5):print "copied"n-2"bytes in"t"s, load $";
4340 v=int(ad/256):gosub 9000:print h$;:v=ad and 255:gosub 9000:print h$
4350 if ad+n-2>51712 then print "** it reaches $ca00, where neoram-drive":print "   runs: it cannot be loaded from it **"
4360 print:print "load it with: load"q$nm$q$",2,1":return
5000 rem --- the card: present, and how big (bytes put back)
5010 poke p,0:poke b,0:o=peek(w+255):poke w+255,85:a=peek(w+255)
5020 poke w+255,170:c=peek(w+255):poke w+255,o
5030 if a<>85 or c<>170 then print "no neoram/georam found.":end
5040 for i=0 to 8:poke b,bv(i):s(i)=peek(w+255):next
5050 poke b,0:poke w+255,0:sz=256:for i=1 to 8:poke b,bv(i):poke w+255,i
5060 poke b,0:if peek(w+255)<>0 then sz=bv(i):i=8
5070 next:for i=8 to 0 step -1:poke b,bv(i):poke w+255,s(i):next:poke b,0
5080 kb=sz*16:ka=kb*1024:return
5500 rem --- start neoram-drive
5510 gosub 6100:if ki=0 then 5560
5520 poke b,0:poke p,0:sys 57000
5530 print:print "neoram-drive started: device"peek(2):return
5560 print chr$(147)"neoram-drive is not on the card:":print "install it first (5).":return
5600 rem --- install neoram-drive: its 7 pages, from the data after the helper
5610 print chr$(147)"install neoram-drive v0.40 on the card":print
5620 print "it takes the card's first 7 pages, and":print "sys 57000 starts it from then on. that"
5630 print "replaces whatever sys 57000 started":print "before (meshcore 64, maniac mansion...)."
5640 print "files already on the drive are kept.":print:print "sure (y/n)?"
5650 gosub 9500:if k$<>"y" then print "not installed.":return
5660 restore:for i=1 to {LEN}:read v:next:print "writing";:e=0
5670 for pg=0 to 6:poke b,0:poke p,pg:for i=0 to 255:read v:poke w+i,v:if peek(w+i)<>v then e=e+1
5680 next:print ".";:next:poke b,0:poke p,0:print
5690 if e then print e"bytes did not read back: test the":print "card with geodiag.":return
5700 print "installed.":pr=0:gosub 3000:if ok then return
5710 print:print "it has no valid file list yet: format":print "it now (y/n)?":gosub 9500
5720 if k$="y" then for la=1792 to 1795:v=0:gosub 7100:next:print "formatted."
5730 return
6000 rem --- status line
6010 gosub 6100:print " card:"kb"kb"
6020 if ki=0 then print " neoram-drive: not on the card (5)":return
6030 if ru=0 then print " neoram-drive: on the card, not started":return
6040 print " neoram-drive: running as device"peek(2):return
6100 poke b,0:poke p,0:ki=0:ru=0
6110 {SIG}
6120 v=peek(817):if v>=202 and v<=207 then ru=1
6130 return
7000 bl=int(la/16384):pg=int(la/256)-bl*64:poke b,bl:poke p,pg:v=peek(w+la-int(la/256)*256):return
7100 bl=int(la/16384):pg=int(la/256)-bl*64:poke b,bl:poke p,pg:poke w+la-int(la/256)*256,v:return
7200 v2=int(v/65536):v1=int((v-v2*65536)/256):v0=v-v2*65536-v1*256:return
9000 h$=mid$("0123456789abcdef",int(v/16)+1,1)+mid$("0123456789abcdef",(v and 15)+1,1):return
9500 get k$:if k$="" then 9500
9510 return
"""


def build(out):
    org = 0xC000                # below $C900, where NeoRAM-Drive puts itself
    eq = {"WIN": 0xDE00, "PG": 0xDFFE, "BK": 0xDFFF, "ST": 0x90, "STKEY": 0x91,
          "CHKIN": 0xFFC6, "CHRIN": 0xFFCF, "CLRCHN": 0xFFCC}
    code, syms = assemble(ML, org, eq)
    assert org + len(code) <= 0xC900
    subs = {k: syms[k] for k in ("DL", "LM", "CL", "RES", "STV")}
    pages = drive_pages()
    # installed = page 0 is the drive's starter: JMP $DE00 at $A8 (as
    # MeshCore 64's is too) and the "this is the launchercode" text at 62
    sig = [(0xA8, 76), (0xA9, 0), (0xAA, 222)] + [(62 + i, pages[62 + i]) for i in range(8)]
    sig = "ki=1:if " + " or ".join("peek(w+%d)<>%d" % (o, v) for o, v in sig) + " then ki=0"
    subs.update(ORG=org, LEN=len(code), SUM=sum(code), VER=VER, SIG=sig)
    src = BASIC
    for k, v in subs.items():
        src = src.replace("{%s}" % k, str(v))
    assert "{" not in src, src[src.index("{"):][:20]
    lines = src.strip("\n").splitlines()
    n = 9600
    for i in range(0, len(code), 18):
        lines.append("%d data %s" % (n, ",".join(str(c) for c in code[i:i + 18])))
        n += 1
    assert n <= 9700
    n = 9700                    # the drive's 7 pages, read only to install it
    for i in range(0, len(pages), 18):
        lines.append("%d data %s" % (n, ",".join(str(c) for c in pages[i:i + 18])))
        n += 1
    bas = os.path.join(OUT, "neocopy.bas")
    with open(bas, "w") as f:
        f.write("\n".join(lines) + "\n")
    subprocess.check_call(["petcat", "-w2", "-o", out, "--", bas])
    print("%s: %d bytes (helper %d bytes at $%04X)" % (out, os.path.getsize(out), len(code), org))


if __name__ == "__main__":
    build(os.path.join(OUT, "neocopy-v%s.prg" % VER))
