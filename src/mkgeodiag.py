#!/usr/bin/env python3
"""
Build GEODIAG, a GeoRAM / NeoRAM diagnostic, for C64 mode and C128 mode:

    mkgeodiag.py [outdir]   -> geodiag64-vX.prg ($0801), geodiag128-vX.prg ($1C01)

A BASIC program (the menu and the quick checks) with a machine code helper
in DATA lines for the full-card test and the read stability test. The
helper sits at $C000 on the C64 and $1300 on the C128 (both free while
BASIC runs). Needs VICE's petcat. Everything it writes to the card is
saved first and put back: a NeoRAM keeps its contents through a power-off.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from asm import assemble  # noqa: E402

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else HERE

# GeoRAM: a 256 byte window at $DE00 into page $DFFE (0-63) of 16K block $DFFF.
ML = """
        jmp full
        jmp stab
        jmp clr
        jmp wall
        jmp rnd
FBLK:   .byte 0         ; full test: first block
NBLK:   .byte 0         ;   blocks to test (0 = 256)
ERRL:   .byte 0,0,0     ;   errors (24 bit)
GLL:    .byte 0,0       ;   of those, wrong on one read and right on the next
FEB:    .byte 0         ;   first error: block
FEP:    .byte 0         ;     page
FEO:    .byte 0         ;     offset
FEX:    .byte 0         ;     wrote
FEG:    .byte 0         ;     read
FEF:    .byte 0         ;     1 once there is one
ABORT:  .byte 0         ;   1 = STOP pressed
BITS:   .byte 0         ;   every data bit seen wrong
NLIST:  .byte 0         ;   entries in ELIST (16 at most, 5 bytes each:
                        ;   block, page, offset, wrote, read)
SB:     .byte 0         ; stability test: block
SPG:    .byte 0         ;   page
SOF:    .byte 0         ;   offset
SCL:    .byte 0,0,0     ;   reads that differed from the first (of 65536)
SBIT:   .byte 0         ;   bits that changed
SVAL:   .byte 0         ;   the first read
CB:     .byte 0
CP:     .byte 0
NB:     .byte 0
PAT:    .byte 0
GOT:    .byte 0
TMP:    .byte 0
OUTER:  .byte 0
SEED:   .byte 0         ; whole-card pattern: (offset + 3 page + 29 block
INV:    .byte 0         ;   + SEED) eor INV, different for every address
WMODE:  .byte 0         ;   bit
BMASK:  .byte 0         ; random test: blocks - 1
RCNT:   .byte 0,0       ;   accesses (0 = 65536)
RL:     .byte $E1,$AC   ;   random state
BASE:   .byte 0
TMP2:   .byte 0
PD:     .byte 0,0       ; progress bar: pages (or accesses) done,
SHF:    .byte 0         ;   >> SHF = cells filled (of 32)
LASTC:  .byte $FF       ;   cells drawn

; all the error counts back to 0
clr:    lda #0
        tax
fclr:   sta ECNT,x
        sta EBIT,x
        inx
        bne fclr
        ldx #13
fclr2:  sta ERRL,x          ; ERRL .. NLIST
        dex
        bpl fclr2
        rts

full:   jsr clr
        lda FBLK
        sta CB
        lda NBLK
        sta NB
fblk:   lda #0
        sta CP
fpage:  lda CP
        sta PG
        lda CB
        sta BK
        jsr prog
        ldx #0
fsave:  lda WIN,x
        sta SAVE,x
        inx
        bne fsave
        lda #$55
        jsr fillchk
        lda #$AA
        jsr fillchk
        jsr addrchk
        ldx #0
frest:  lda SAVE,x
        sta WIN,x
        inx
        bne frest
        inc PD
        bne fpd
        inc PD+1
fpd:    lda STKEY
        cmp #$7F
        beq fstop
        inc CP
        lda CP
        cmp #64
        bne fpage
        inc CB
        dec NB
        bne fblk
        rts
fstop:  inc ABORT
; until STOP is let go, or BASIC stops on it as this returns
fstopw: lda STKEY
        cmp #$7F
        beq fstopw
        rts

; whole card, every block: WMODE 0 writes the pattern, 1 checks it
wall:   lda #0
        sta CB
        lda NBLK
        sta NB
wblk:   lda #0
        sta CP
wpage:  lda CP
        sta PG
        lda CB
        sta BK
        jsr prog
        jsr pbase
        ldx #0
        lda WMODE
        bne wchk
wfill:  txa
        clc
        adc BASE
        eor INV
        sta WIN,x
        inx
        bne wfill
        jmp wnext
wchk:   txa
        clc
        adc BASE
        eor INV
        sta PAT
        lda WIN,x
        cmp PAT
        beq wok
        jsr bad
wok:    inx
        bne wchk
wnext:  inc PD
        bne wpd
        inc PD+1
wpd:    lda STKEY
        cmp #$7F
        beq fstop
        inc CP
        lda CP
        cmp #64
        bne wpage
        inc CB
        dec NB
        bne wblk
        rts

; BASE = 3 page + 29 block + SEED (29 block = 32 block - 2 block - block)
pbase:  lda CB
        asl
        sta TMP2
        asl
        asl
        asl
        asl
        sec
        sbc TMP2
        sec
        sbc CB
        sta TMP2
        lda CP
        asl
        clc
        adc CP
        clc
        adc TMP2
        clc
        adc SEED
        sta BASE
        rts

; after a WMODE 0 pass: RCNT accesses anywhere on the card, the block and
; page changed every time; each checks the pattern, writes the inverse,
; checks that, and puts the pattern back
rnd:    jsr rand
        and BMASK
        sta CB
        sta BK
        jsr rand
        and #63
        sta CP
        sta PG
        jsr prog
        jsr pbase
        jsr rand
        tax
        clc
        adc BASE
        eor INV
        sta PAT
        lda WIN,x
        cmp PAT
        beq rnd1
        jsr bad
rnd1:   lda PAT
        eor #$FF
        sta PAT
        sta WIN,x
        lda WIN,x
        cmp PAT
        beq rnd2
        jsr bad
rnd2:   lda PAT
        eor #$FF
        sta WIN,x
        inc PD
        bne rpd
        inc PD+1
rpd:    lda STKEY
        cmp #$7F
        beq fstop
        lda RCNT
        bne rnd3
        dec RCNT+1
rnd3:   dec RCNT
        lda RCNT
        ora RCNT+1
        bne rnd
        rts

; 16 bit Galois LFSR, 8 steps a call
rand:   ldy #8
rand1:  lsr RL+1
        ror RL
        bcc rand2
        lda RL+1
        eor #$B4
        sta RL+1
rand2:  dey
        bne rand1
        lda RL
        rts

; every byte of the page = A, then read them all back
fillchk: sta PAT
        ldx #0
fw:     sta WIN,x
        inx
        bne fw
fr:     lda WIN,x
        cmp PAT
        beq fnext
        jsr bad
fnext:  inx
        bne fr
        rts

; a different value in every byte (offset eor block, plus page): finds
; offset lines that are shorted or open
addrchk: ldx #0
aw:     txa
        eor CB
        clc
        adc CP
        sta WIN,x
        inx
        bne aw
ar:     txa
        eor CB
        clc
        adc CP
        sta PAT
        lda WIN,x
        cmp PAT
        beq anext
        jsr bad
anext:  inx
        bne ar
        rts

; A read wrong at offset X (PAT expected). X is kept.
bad:    sta GOT
        lda WIN,x
        cmp PAT
        bne bcount
        inc GLL
        bne bcount
        inc GLL+1
bcount: inc ERRL
        bne b2
        inc ERRL+1
        bne b2
        inc ERRL+2
b2:     lda GOT
        eor PAT
        sta TMP
        ora BITS
        sta BITS
        ldy CB
        lda TMP
        ora EBIT,y
        sta EBIT,y
        lda ECNT,y
        cmp #$FF
        beq b3
        clc
        adc #1
        sta ECNT,y
b3:     lda NLIST
        cmp #16
        bcs b5
        asl
        asl
        clc
        adc NLIST
        tay
        lda CB
        sta ELIST,y
        lda CP
        sta ELIST+1,y
        txa
        sta ELIST+2,y
        lda PAT
        sta ELIST+3,y
        lda GOT
        sta ELIST+4,y
        inc NLIST
b5:     lda FEF
        bne b4
        inc FEF
        lda CB
        sta FEB
        lda CP
        sta FEP
        stx FEO
        lda PAT
        sta FEX
        lda GOT
        sta FEG
b4:     rts

; block and page in hex, top right of the 40 column screen
prog:   lda CB
        ldy #0
        jsr hex
        lda CP
        ldy #3
        jsr hex
; the bar, row 22: PD >> SHF cells of 32, redrawn when that changes
bar:    lda PD
        sta TMP2
        lda PD+1
        ldx SHF
        beq bar2
bar1:   lsr
        ror TMP2
        dex
        bne bar1
bar2:   lda TMP2
        cmp LASTC
        beq bar5
        sta LASTC
        ldx #0
bar3:   lda #$A0                ; reverse space
        cpx TMP2
        bcc bar4
        lda #$2E                ; "."
bar4:   sta SCR+884,x
        inx
        cpx #32
        bne bar3
bar5:   rts
hex:    pha
        lsr
        lsr
        lsr
        lsr
        jsr dig
        sta SCR+35,y
        iny
        pla
        and #$0F
        jsr dig
        sta SCR+35,y
        rts
dig:    cmp #10
        bcc dnum
        sbc #9                  ; carry set: 10 -> 1
        ora #$40                ; screen code of "A" in the lower case set
        rts
dnum:   ora #$30
        rts

; read one byte 65536 times; count the reads that differ from the first
stab:   lda SPG
        sta PG
        lda SB
        sta BK
        ldx SOF
        lda #0
        sta SCL
        sta SCL+1
        sta SCL+2
        sta SBIT
        sta OUTER
        tay
        lda WIN,x
        sta SVAL
sloop:  lda WIN,x
        cmp SVAL
        beq sok
        eor SVAL
        ora SBIT
        sta SBIT
        inc SCL
        bne sok
        inc SCL+1
        bne sok
        inc SCL+2
sok:    dey
        bne sloop
        dec OUTER
        bne sloop
        rts
"""

# fclr2 needs bpl, which the assembler does not have; spelled out instead
ML = ML.replace("""        dex
        bpl fclr2""", """        dex
        cpx #$FF
        bne fclr2""")

BASIC = r"""
1 rem geodiag {VER}: georam / neoram diagnostics ({MACH} mode)
2 rem 1-6 save what they write and put it back; 7-9 erase the card
10 ml={ORG}:fb={FBLK}:nb={NBLK}:eu={ERRL}:gl={GLL}:fe={FEB}:ab={ABORT}:bt={BITS}
20 sp={SB}:sc={SCL}:sx={SBIT}:ec={ECNT}:eb={EBIT}:c8={C128}
25 nl={NLIST}:lz={ELIST}:sq={SEED}:iv={INV}:wm={WMODE}:bm={BMASK}:rc={RCNT}:mc={clr}:mw={wall}:mr={rnd}
27 pd={PD}
30 w=56832:p=57342:b=57343:x$="0123456789ABCDEF"
40 dim bv(8),ss(8),sv(8),rd(8),d(255),qo(8),qe(8),qa(8),qz(8),pn(8),mk(32)
50 print chr$(147)chr$(14)"GeoRAM / NeoRAM diagnostics {VER}":print
60 print "Loading the test routine...":cs=0
70 for i=0 to {LEN}-1:read v:poke ml+i,v:cs=cs+v:next
80 if cs<>{SUM} then print "Bad DATA lines (checksum)":end
90 v=1:for i=1 to 8:bv(i)=v:v=v*2:next:bv(0)=0
95 q$="1715181419132021":for i=0 to 7:pn(i)=val(mid$(q$,i*2+1,2)):next
100 print chr$(147)"GeoRAM / NeoRAM diagnostics {VER}":print
110 print "Raw reads, before writing anything:"
120 print " $DE00-07";:for i=0 to 7:v=peek(w+i):gosub 9000:print " "h$;:next:print
130 print " again   ";:for i=0 to 7:v=peek(w+i):gosub 9000:print " "h$;:next:print
140 print " $DFFE/F ";:v=peek(p):gosub 9000:print " "h$;:v=peek(b):gosub 9000:print " "h$
150 print " (the registers are write-only on a":print " GeoRAM: open bus, or a clone's own)":print
200 rem --- data lines: walking 1s and 0s at block 0, page 0, offset 0
210 poke p,0:poke b,0:o=peek(w):sl=0:sh=0
220 for i=1 to 8:v=bv(i):for k=0 to 1:poke w,v:r=peek(w)
230 sl=sl or (v and not r):sh=sh or (r and not v):v=255-v:next k,i
240 for v=0 to 255 step 255:poke w,v:r=peek(w):sl=sl or (v and not r):sh=sh or (r and not v):next
250 poke w,o
260 print "Data lines D0-D7 (block 0, page 0):"
270 if sl=0 and sh=0 then print " all 8 store 0 and 1":goto 300
280 if sl=255 and sh=255 then print " nothing stores: no card is answering":print " at $DE00.":goto 8000
290 for i=0 to 7:v=bv(i+1):if (sl or sh) and v then gosub 9100
295 next:print "(a data line fault: the edge connector,":print " the card's buffer, or a RAM chip)":fl=1
300 rem --- page register: pages 1,2,4..32 against page 0
310 print:print "Page register (bits 0-5):"
320 poke b,0:for i=0 to 6:poke p,bv(i):sv(i)=peek(w):next
330 n=6:gosub 9200:if bd then fl=1
340 for i=6 to 0 step -1:poke p,bv(i):poke w,sv(i):next
350 for i=1 to 6:if ss(i)<>0 then print " bit"i-1"(page"bv(i)") ";:gosub 9300
360 next:if bd=0 then print " all 6 select their own memory"
400 rem --- block register: blocks 1,2,4..128 against block 0
410 print:print "Block register (bits 0-7):"
420 poke p,0:for i=0 to 8:poke b,bv(i):sv(i)=peek(w):next
440 n=8:gosub 9200
450 for i=8 to 0 step -1:poke b,bv(i):poke w,sv(i):next:poke b,0
460 sz=256:for i=1 to 8:if ss(i)<>0 then sz=bv(i):goto 480
470 next
480 for i=1 to 8:if bv(i)<sz then 495
485 if ss(i)=0 then print " bit"i-1"works above the end: a hole":fl=1
490 if ss(i)>1 then print " bit"i-1"(block"bv(i)") ";:gosub 9300:fl=1
495 next
500 kb=sz*16:print " memory ends at block"sz-1:print " size:"kb"KB";:if kb>=1024 then print " ="kb/1024"MB";
505 ls=1:v=sz
506 if v>1 then v=v/2:ls=ls+1:goto 506
510 print:if sz<32 then print " (expected 512 KB, 1 MB, 2 MB or 4 MB)":fl=1
520 print:if fl then print "** Faults found above. **":print "Menu 1 tests all RAM pins.":goto 540
530 print "Quick checks passed."
540 print "Press a key.":gosub 9500
600 rem --- menu
610 print chr$(147)"GeoRAM / NeoRAM diagnostics {VER}":print:print " card:"kb"KB,"sz"blocks":print
620 print " 1  test all RAM pins (each chip)"
630 print " 2  full test, every byte (1 MHz)"
640 if c8 then print " 3  full test at 2 MHz (FAST)"
650 print " 4  read stability (65536 reads)"
660 print " 5  look at a page (hex)"
662 print " 6  quick checks again"
664 print " 7  whole-card test (ERASES the card)"
666 print " 8  retention, step 1: write (ERASES)"
668 print " 9  retention, step 2: check":print
670 print " 1-6 keep what is on the card.":print " Q  quit"
680 gosub 9500:if k$="1" then 4000
681 if k$="2" then f2=0:goto 700
682 if k$="3" and c8 then f2=1:goto 700
683 if k$="4" then 1000
684 if k$="5" then 1200
685 if k$="6" then 100
686 if k$="7" then 2500
687 if k$="8" then 3000
688 if k$="9" then 3100
689 if k$="q" then print chr$(147);:end
690 goto 680
700 rem --- full test
710 print chr$(147)"Full test of"kb"KB";:if f2 then print " at 2 MHz";
720 print:print:print "Every page is saved, filled with $55,"
730 print "$AA and an address pattern, checked and"
740 print "put back. Top right: block, page (hex)."
745 if f2 then print "(The 40 column screen blanks at 2 MHz.)"
750 print "STOP ends it.":print
760 poke fb,0:poke nb,sz and 255:v=ls:gosub 2960:t=ti:if f2 then poke 53296,1
770 sys ml:poke 53296,0:t=int((ti-t)/60+.5):gosub 2970
775 if peek(ab) then print "Stopped by STOP at block";peek({CB})
777 print "Time:"t"s":print
780 gosub 2000
900 print:print "Press a key.":gosub 9500:goto 600
1000 rem --- read stability: block 0 page 0, last block page 63
1010 print chr$(147)"Read stability":print:print "Each byte is read 65536 times; any read"
1020 print "that differs from the first is counted.":print " (block/page/offset, hex)":print
1030 for j=0 to 1:bl=0:pg=0:of=0:if j then bl=sz-1:pg=63:of=255
1040 poke p,pg:poke b,bl:o=peek(w+of)
1050 for k=0 to 1:v=85+85*k:poke w+of,v
1060 poke sp,bl:poke sp+1,pg:poke sp+2,of:sys ml+3
1070 n=peek(sc)+256*peek(sc+1)+65536*peek(sc+2)
1075 u=v:v=bl:gosub 9000:print " "h$"/";:v=pg:gosub 9000:print h$"/";:v=of:gosub 9000:print h$;
1080 v=u:gosub 9000:print " $"h$":"n"bad";
1090 if n then v=peek(sx):gosub 9000:print " bits "h$;
1095 print
1100 next k:poke p,pg:poke b,bl:poke w+of,o:next j
1110 if c8 then print:print "Again at 2 MHz:":poke 53296,1:gosub 1150:poke 53296,0
1120 print:print "Press a key.":gosub 9500:goto 600
1150 for j=0 to 1:bl=0:pg=0:of=0:if j then bl=sz-1:pg=63:of=255
1160 poke p,pg:poke b,bl:o=peek(w+of):v=85:poke w+of,v
1170 poke sp,bl:poke sp+1,pg:poke sp+2,of:sys ml+3:poke w+of,o
1180 n=peek(sc)+256*peek(sc+1)+65536*peek(sc+2):s8(j)=n:s9(j)=peek(sx)
1185 next:poke 53296,0
1190 for j=0 to 1:print " "mid$("first last",j*6+1,5)" byte:"s8(j)"bad";
1195 if s8(j) then v=s9(j):gosub 9000:print " bits "h$;
1197 print:next:return
1200 rem --- hex dump of a page
1210 print chr$(147);:input "block, page";bl,pg
1220 if bl<0 or bl>255 or pg<0 or pg>63 then 1210
1230 poke b,bl:poke p,pg:for i=0 to 255:d(i)=peek(w+i):next
1240 for i=0 to 255 step 8:v=i:gosub 9000:print h$":";
1250 for k=0 to 7:v=d(i+k):gosub 9000:print " "h$;:next:print
1260 if i=120 then print "Press a key.":gosub 9500
1270 next:print "Press a key.":gosub 9500:goto 600
2000 rem --- the error report
2010 e=peek(eu)+256*peek(eu+1)+65536*peek(eu+2):g=peek(gl)+256*peek(gl+1)
2020 if e=0 then print "No errors.":return
2030 print "Errors:"e:print " glitches:"g"(wrong, then right)"
2040 print " data bits wrong (D):";:v=peek(bt):for i=0 to 7:if v and bv(i+1) then print mid$(str$(i),1);
2050 next:print:n=peek(nl):if n>6 then n=6
2060 print " first errors, in hex:":print "  blk  pg   ofs  wrote read"
2070 for i=0 to n-1:print "  ";:for k=0 to 4:v=peek(lz+i*5+k):gosub 9000:print h$"   ";:next:print:next
2080 print " blocks with errors (. none, x some),":print " 32 to a row = 512 KB:"
2090 for r=0 to int((sz-1)/32):print "  ";:for c=0 to 31:i=r*32+c:v$=" ":if i<sz then v$=".":if peek(ec+i) then v$="x"
2100 print v$;:next:print r+1:next
2110 print "Press a key.":gosub 9500:print:if rt then return
2120 goto 8500
2500 rem --- whole-card test: erases
2510 print chr$(147)"Whole-card test,"kb"KB":print:print "This ERASES the card. Every byte gets a"
2520 print "value of its own; only then is it all":print "read back, so a write that lands in the"
2530 print "wrong place shows. Twice (the second"
2540 print "time inverted), then 65536 accesses at":print "random places. It repeats until STOP."
2550 print:print "Sure (y/n)?":gosub 9500:if k$<>"y" then 600
2560 f2=0:if c8 then print "At 2 MHz (y/n)?":gosub 9500:if k$="y" then f2=1
2570 sys mc:ps=0:sd=0:t=ti:poke nb,sz and 255:poke bm,sz-1
2580 ps=ps+1:print chr$(147)"Whole-card test, pass"ps:print "STOP ends it. Top right: block, page.":print
2590 for j=0 to 1:poke sq,sd:poke iv,255*j
2600 print " pattern"j+1"write";:poke wm,0:gosub 2900:if peek(ab) then 2680
2610 print ", check";:poke wm,1:gosub 2900:if peek(ab) then 2680
2620 gosub 2980:next
2630 print " random accesses";:poke rc,0:poke rc+1,0:v=11:gosub 2960:if f2 then poke 53296,1
2640 sys mr:poke 53296,0:gosub 2970:if peek(ab) then 2680
2650 gosub 2980:sd=(sd+77) and 255:goto 2580
2680 t=int((ti-t)/60+.5):print:print:print "Stopped after"ps"passes,"t"s."
2685 print "The card is erased."
2690 print "Press a key for the report.":gosub 9500
2700 print chr$(147)"Whole-card test:"ps"passes":print:gosub 2000:goto 900
2900 v=ls:gosub 2960:if f2 then poke 53296,1
2910 sys mw:poke 53296,0:gosub 2970:return
2960 rem progress bar on row 22, shift v
2962 poke pd,0:poke pd+1,0:poke pd+2,v:poke pd+3,255:poke 1907,27:poke 1940,29
2964 for i=1907 to 1940:poke i+54272,1:next:return
2970 for i=1904 to 1943:poke i,32:next:return
2980 e=peek(eu)+256*peek(eu+1)+65536*peek(eu+2):print ":"e"errors":return
3000 rem --- retention, step 1
3010 print chr$(147)"Retention test, step 1 of 2":print:print "Writes a pattern over the whole card"
3020 print "(this ERASES it) and reads it back.":print "Then turn the machine OFF. Leave it off"
3030 print "a minute, or better an hour or a night.":print "Turn it on, load GEODIAG, choose 9."
3040 print "(A reset alone tests less: try both.)":print:print "Sure (y/n)?"
3050 gosub 9500:if k$<>"y" then 600
3060 f2=0:sys mc:poke nb,sz and 255:poke sq,165:poke iv,0:poke wm,0:print:print "Writing...":gosub 2900
3070 if peek(ab) then print "Stopped.":goto 900
3080 print "Checking...":poke wm,1:gosub 2900:gosub 2010
3090 if e then print:print "It does not even read back right away:":print "run test 7 first.":goto 900
3095 print:print "The pattern is on the card. Turn the":print "machine off now.":end
3100 rem --- retention, step 2
3110 print chr$(147)"Retention test, step 2 of 2":print:print "Checking the pattern from step 1..."
3115 rt=1
3120 f2=0:sys mc:poke nb,sz and 255:poke sq,165:poke iv,0:poke wm,1:gosub 2900
3130 if peek(ab) then print "Stopped.":goto 900
3140 gosub 2000:rt=0:print chr$(147)"Retention test result":print
3145 if e=0 then print "Every byte was kept.":goto 900
3150 if e<sz*16384*.9 then 3200
3160 print "Almost nothing was kept (or step 1 was":print "not run). Backup power did not hold:"
3170 print "the battery (2.8 V or more), D1, SJ5":print "open. With the machine off, RAM pin 32"
3180 print "should read about the battery less":print "0.3 V, and pin 22 about the same."
3190 goto 900
3200 n=peek(nl):c=0:for i=0 to n-1:a=peek(lz+i*5+3):v=peek(lz+i*5+4)
3205 x=(a or v) and not (a and v):if (x and (x-1))=0 then c=c+1
3210 next:r=0:for i=0 to sz-1 step 32:k=0:for j=i to i+31:if j<sz then if peek(ec+j) then k=1
3215 next:r=r+k:next
3220 print "Part of it was lost:"e"bytes,":print " in"r"of"int((sz+31)/32)"rows (512 KB each)."
3225 if r<int((sz+31)/32) or c<n*.75 then 3260
3230 print:print "Single bits flipped all over the card:":print "the RAM was kept powered, but at too"
3235 print "low a voltage, or it dipped. Check with":print "the machine off: the battery (2.8 V or"
3240 print "more), RAM pin 32 on each chip (about":print "battery less 0.3 V), pin 22 on each"
3245 print "chip (within 0.2 V of pin 32), SJ5":print "open, and all chips low-power (L/LL)"
3250 print "parts. Then see if it gets worse with":print "a longer time off.":goto 900
3260 if r=1 and sz>32 then print:print "One chip only: that RAM chip, its pin":print "32 joint, or a non-L part.":goto 900
3270 print:print "One page or a few: a stray write at":print "power on or off.":goto 900
4000 rem --- each chip: 512 KB banks (blocks n*32..n*32+31), one byte each
4010 print chr$(147)"Test all RAM pins":print
4020 print "One byte per 512 KB chip gets walking":print "1s and 0s (twice) and its own value."
4025 print "Saved and put back. Chip names and pins":print "are for the NeoRAM Remix.":print:print "Testing...";
4030 poke p,63:for qc=0 to 7:poke b,qc*32+31:qo(qc)=peek(w+255):qa(qc)=-1:qz(qc)=0:next
4040 for qc=0 to 7:poke b,qc*32+31:qe(qc)=0
4045 for k=1 to 4:v=1
4050 for i=1 to 8:x=v:if k and 1 then x=255-v
4055 poke w+255,x:r=peek(w+255):qe(qc)=qe(qc) or (x and not r) or (r and not x):v=v*2:next i,k,qc
4060 for qc=0 to 7:poke b,qc*32+31:poke w+255,qc*16+5:if peek(w+255)<>qc*16+5 then qa(qc)=-2
4070 if qc=0 then 4110
4080 for qj=0 to qc-1:if qa(qj)<>-1 or qa(qc)>=0 then 4100
4090 poke b,qj*32+31:if peek(w+255)<>qj*16+5 then qa(qc)=qj:poke w+255,qj*16+5
4100 next qj
4110 next qc
4120 for qc=7 to 0 step -1:poke b,qc*32+31:poke w+255,qo(qc):next:poke b,0:poke p,0
4130 qn=8:for qc=1 to 7:if qa(qc)=0 then qn=qc:qc=7
4140 next:fl=0:qd=0:qs=0:print chr$(13)chr$(145)"          ";chr$(13)chr$(145);
4150 for qc=0 to qn-1:q$=mid$(str$(qc+1),2):print " U"q$" (bank"qc"):";
4160 if qa(qc)>=0 then print " same chip as U"mid$(str$(qa(qc)+1),2):fl=1:qs=1:goto 4200
4165 qk=0:for i=0 to 7:if qe(qc) and bv(i+1) then qk=qk+1
4168 next
4170 if qk=0 and qa(qc)=-1 then print " ok":goto 4200
4175 fl=1:if qk=0 then print " reads back wrong":goto 4200
4180 if qk>=7 then print " no data at all":qz(qc)=1:goto 4200
4182 qd=1:if qk>3 then 4194
4184 print qk"pin";:if qk>1 then print "s";
4185 print " not connecting:"
4186 for i=0 to 7:if (qe(qc) and bv(i+1))=0 then 4192
4188 qp=pn(i):r$="bottom":n=17-qp:if qp>16 then r$="top":n=qp-16
4190 gosub 4800:print "   pin"qp"(D"mid$(str$(i),2)"): "r$" row,":print "     "o$" from the right end"
4192 next:goto 4200
4194 print qk"data pins bad:":print "   pins";:for i=0 to 7:if qe(qc) and bv(i+1) then print pn(i);
4196 next:print:print "   (a lifted row of pins or a bad chip)"
4200 next
4210 if qn<8 then print " (U"mid$(str$(qn+1),2)" would be U1 again: the end)"
4215 print " size:"qn*512"KB";:if qn>=2 then print " ="qn/2"MB";
4220 print:if fl=0 then print:print "All chips pass.":print:print "Press a key.":gosub 9500:goto 600
4225 print:if qd then print "Pins: chip with its dot at lower left."
4230 if qd then print "Reflow each pin named, with flux,":print "pressing the lead down onto its pad."
4235 if qd then print "Meter: the lead (not its pad) should":print "beep to the same pin on a good chip."
4240 if qz(1) and qz(3) then print "U2 and U4 dead: the select line they":print "share, SJ3 and the '273 pin 15."
4245 if qz(2) and qz(3) then print "U3 and U4 dead: the select line they":print "share, SJ4 and the '273 pin 16."
4250 q=0:for qc=0 to 3:q=q+qz(qc):next:if q=0 then 4260
4255 print "No data: check that chip's pins 29 WE,":print "24 OE, 22 CS, 32 power and 16 GND."
4260 if qs then print "A chip answers as another: SJ3/SJ4,":print "the '273 (pins 15, 16) or the '138."
4270 if qd or q then print "Still failing after that: the chip."
4290 print:print "Press a key: each faulty chip's pins.";:gosub 9500:if fl=0 then 600
4300 rem --- a drawing of each faulty chip, bad pins marked
4302 for qc=0 to 3:if qc>=qn then 4390
4305 if qe(qc)=0 then 4390
4310 for i=0 to 32:mk(i)=0:next:q$="U"+mid$(str$(qc+1),2)
4315 if qz(qc) then mk(29)=1:mk(24)=1:mk(22)=1:mk(32)=1:mk(16)=1:goto 4325
4320 for i=0 to 7:if qe(qc) and bv(i+1) then mk(pn(i))=1
4322 next
4325 print chr$(147)q$" (bank"qc") seen from above:":print
4330 a$="   ":c$="   ":for j=0 to 15:qp=32-j:gosub 4700:next:print a$:print c$
4335 a$="   ":for j=0 to 15:qp=32-j:gosub 4750:next:print a$
4340 a$="  "+chr$(176):for j=1 to 32:a$=a$+chr$(96):next:print a$+chr$(174)
4345 print "  "chr$(125)"o             "q$"                "chr$(125)
4350 a$="  "+chr$(173):for j=1 to 32:a$=a$+chr$(96):next:print a$+chr$(189)
4355 a$="   ":for j=0 to 15:qp=j+1:gosub 4750:next:print a$
4360 a$="   ":c$="   ":for j=0 to 15:qp=j+1:gosub 4700:next:print a$:print c$
4365 print:print "Pin 1 is at the dot, lower left. Solid":print "blocks are the pins to fix.":print
4370 if qz(qc)=0 then 4376
4372 print "No data at all. Check the marked pins:":print " 29 WE  24 OE  22 CS  32 power  16 GND"
4374 goto 4384
4376 for i=0 to 7:if (qe(qc) and bv(i+1))=0 then 4382
4378 qp=pn(i):r$="bottom":n=17-qp:if qp>16 then r$="top":n=qp-16
4380 gosub 4800:print " pin"qp"(D"mid$(str$(i),2)") "r$" row, "o$" from right"
4382 next
4384 print:print "Reflow the marked pins with flux,":print "pressing each lead down onto its pad."
4386 print:print "Press a key.";:gosub 9500
4390 next:goto 600
4700 l$="  ":if mk(qp) or qp=1 or qp=16 or qp=17 or qp=32 then l$=left$(mid$(str$(qp),2)+" ",2)
4710 if j and 1 then c$=c$+l$:a$=a$+"  ":return
4720 a$=a$+l$:c$=c$+"  ":return
4750 if mk(qp) then a$=a$+chr$(18)+" "+chr$(146)+" ":return
4760 a$=a$+chr$(125)+" ":return
4800 o$=mid$(str$(n),2)+"th":if n=1 then o$="1st"
4810 if n=2 then o$="2nd"
4820 if n=3 then o$="3rd"
4830 return
8000 print:print "Check: the card is pushed fully home,":print "the edge connector is clean, and the"
8010 print "machine is off when it goes in. On a":print "C128 try it in C64 mode too."
8020 end
8500 rem --- what the pattern suggests
8510 if g>0 and g*2>=e then print "Mostly glitches: a contact or timing":print "fault (clean the edge connector).":return
8515 n=peek(nl):if n<2 then 8520
8516 c=1:for i=1 to n-1:if peek(lz+i*5)<>peek(lz) or peek(lz+i*5+1)<>peek(lz+1) then c=0
8517 next:if c and e<=256 then print "All in one page: a stray write, as at":print "power on or off.":return
8520 n=0:for i=0 to sz-1:if peek(ec+i) then n=n+1
8530 next:if n=sz and sz>1 then print "Every block: a shared fault, likely a":print "data line or the card's buffer.":return
8535 c=0:for r=0 to int((sz-1)/32):k=0:for i=r*32 to r*32+31:if i<sz then if peek(ec+i) then k=1
8536 next:c=c+k:next:if c=1 and sz>32 then print "One row (512 KB) only: one RAM chip":print "or its chip select.":return
8540 print "Some blocks only: one RAM chip or an":print "address line of the card.":return
9000 h$=mid$(x$,int(v/16)+1,1)+mid$(x$,(v and 15)+1,1):return
9100 print " D"mid$(str$(i),2)" = U1 pin"pn(i)":";:if (sl and v) and (sh and v) then print " won't hold a value":return
9110 if sl and v then print " stuck at 0":return
9120 print " stuck at 1":return
9200 rem marks register bits 1..n against value 0 (register in rg)
9205 bd=0:rg=p:if n=8 then rg=b
9210 poke rg,0:poke w,0
9220 for i=1 to n:poke rg,bv(i):poke w,i:r=peek(w):ss(i)=0
9230 if r<>i then ss(i)=2:goto 9260
9240 poke rg,0:if peek(w)<>0 then ss(i)=1:poke w,0
9260 next
9270 for i=1 to n:poke rg,bv(i):rd(i)=peek(w):if ss(i)=0 and rd(i)<>i then ss(i)=3
9280 next:for i=1 to n:if n=6 and ss(i) then bd=1
9290 next:return
9300 if ss(i)=1 then print "is ignored (= 0)":return
9310 if ss(i)=2 then print "reads back wrong":return
9320 v=rd(i):if v>=1 and v<=n then print "shares with"bv(v):return
9330 print "reads back wrong":return
9500 get k$:if k$="" then 9500
9510 return
"""


VER = "1.4"


def build(mach, org, scr, out):
    # code up to org+$3FF, the error list after it; the three page tables
    # above it on the C64, in the cassette and RS-232 buffers on the C128
    # (its free area ends at $17FF)
    eq = {"WIN": 0xDE00, "PG": 0xDFFE, "BK": 0xDFFF, "STKEY": 0x91, "SCR": scr,
          "ELIST": org + 0x400}
    if mach == "c64":
        eq.update(SAVE=org + 0x500, ECNT=org + 0x600, EBIT=org + 0x700)
    else:
        eq.update(SAVE=0x0B00, ECNT=0x0C00, EBIT=0x0D00)
    code, syms = assemble(ML, org, eq)
    assert len(code) <= 0x400, "helper overruns its buffers: %d bytes" % len(code)
    subs = {k: syms[k] for k in ("FBLK", "NBLK", "ERRL", "GLL", "FEB", "ABORT", "BITS",
                                 "SB", "SCL", "SBIT", "CB", "NLIST", "SEED", "INV", "WMODE",
                                 "BMASK", "RCNT", "clr", "wall", "rnd", "PD")}
    subs.update(ORG=org, ECNT=eq["ECNT"], EBIT=eq["EBIT"], ELIST=eq["ELIST"], LEN=len(code),
                SUM=sum(code), C128=1 if mach == "c128" else 0, MACH=mach.upper(), VER=VER)
    src = BASIC
    for k, v in subs.items():
        src = src.replace("{%s}" % k, str(v))
    assert "{" not in src, src[src.index("{"):][:20]
    lines = src.strip("\n").splitlines()
    # the helper as DATA, after the program
    n = 9600
    for i in range(0, len(code), 18):
        lines.append("%d data %s" % (n, ",".join(str(c) for c in code[i:i + 18])))
        n += 1
    bas = os.path.join(OUT, "geodiag%s.bas" % mach[1:])
    with open(bas, "w") as f:
        f.write("\n".join(lines) + "\n")
    args = ["petcat", "-w2", "-o", out, "--", bas] if mach == "c64" else \
           ["petcat", "-w70", "-l", "1c01", "-o", out, "--", bas]
    subprocess.check_call(args)
    print("%s: %d bytes (helper %d bytes at $%04X)" % (out, os.path.getsize(out), len(code), org))


if __name__ == "__main__":
    build("c64", 0xC000, 0x0400, os.path.join(OUT, "geodiag64-v%s.prg" % VER))
    build("c128", 0x1300, 0x0400, os.path.join(OUT, "geodiag128-v%s.prg" % VER))
