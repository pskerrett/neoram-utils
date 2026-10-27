1 rem neocopy 1.1: install, format, start and fill enthusi's neoram-drive
2 rem writes the drive's own layout on the card; needs no load or save
3 rem neoram-drive v0.40 (c) 2007,2008 martin wendt / enthusi, gpl v3+
10 ml=49152:dl=49155:lm=49158:cl=49160:rs=49163:sv=49164
20 w=56832:p=57342:b=57343:dv=peek(186):nf=0:q$=chr$(34):if dv<8 or dv>30 then dv=8
30 dim n$(144),t$(144),bz(144),d$(200),bv(8),s(8)
40 print chr$(147)chr$(142)"neocopy 1.1 for neoram-drive v0.40":print
50 cs=0:for i=0 to 176-1:read v:poke ml+i,v:cs=cs+v:next
60 if cs<>20047 then print "bad data lines (checksum)":end
70 v=1:for i=1 to 8:bv(i)=v:v=v*2:next
80 gosub 5000
100 rem --- menu
110 print chr$(147)"neocopy 1.1 for neoram-drive v0.40":print
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
5660 restore:for i=1 to 176:read v:next:print "writing";:e=0
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
6110 ki=1:if peek(w+168)<>76 or peek(w+169)<>0 or peek(w+170)<>222 or peek(w+62)<>20 or peek(w+63)<>8 or peek(w+64)<>9 or peek(w+65)<>19 or peek(w+66)<>32 or peek(w+67)<>9 or peek(w+68)<>19 or peek(w+69)<>32 then ki=0
6120 v=peek(817):if v>=202 and v<=207 then ru=1
6130 return
7000 bl=int(la/16384):pg=int(la/256)-bl*64:poke b,bl:poke p,pg:v=peek(w+la-int(la/256)*256):return
7100 bl=int(la/16384):pg=int(la/256)-bl*64:poke b,bl:poke p,pg:poke w+la-int(la/256)*256,v:return
7200 v2=int(v/65536):v1=int((v-v2*65536)/256):v0=v-v2*65536-v1*256:return
9000 h$=mid$("0123456789abcdef",int(v/16)+1,1)+mid$("0123456789abcdef",(v and 15)+1,1):return
9500 get k$:if k$="" then 9500
9510 return
9600 data 76,14,192,0,0,0,0,0,0,0,0,0,0,0,169,0,141,8
9601 data 192,141,9,192,141,10,192,141,11,192,141,12,192,162,2,32,198,255
9602 data 144,8,169,4,141,11,192,76,172,192,32,207,255,168,173,144,0,141
9603 data 12,192,41,131,240,8,169,2,141,11,192,76,172,192,173,4,192,205
9604 data 6,192,208,16,173,5,192,205,7,192,208,8,169,1,141,11,192,76
9605 data 172,192,173,4,192,41,63,141,254,223,173,4,192,141,13,192,173,5
9606 data 192,14,13,192,42,14,13,192,42,141,255,223,174,3,192,152,157,0
9607 data 222,238,8,192,208,8,238,9,192,208,3,238,10,192,238,3,192,208
9608 data 8,238,4,192,208,3,238,5,192,173,12,192,41,64,208,12,173,145
9609 data 0,201,127,208,135,169,3,141,11,192,32,204,255,96
9700 data 162,25,189,0,222,141,0,201,232,240,6,238,6,222,76,2,222,169
9701 data 0,141,6,222,76,0,201,162,0,169,1,141,254,223,189,0,222,141
9702 data 0,202,232,208,3,238,3,201,238,11,201,208,3,238,12,201,173,12
9703 data 201,201,208,208,224,76,0,202,20,8,9,19,32,9,19,32,20,8
9704 data 5,32,12,1,21,14,3,8,5,18,3,15,4,5,46,16,18,5
9705 data 19,5,14,20,5,4,32,20,15,32,25,15,21,32,2,25,32,5
9706 data 14,20,8,21,19,9,32,15,6,32,15,14,19,12,1,21,7,8
9707 data 20,46,16,12,5,1,19,5,32,18,5,16,15,18,20,32,2,21
9708 data 7,19,32,1,14,4,32,6,5,1,20,21,18,5,32,18,5,17
9709 data 21,5,19,20,19,46,76,0,222,20,8,1,14,11,19,32,20,15
9710 data 32,24,49,53,52,49,32,6,15,18,32,20,8,5,32,4,5,19
9711 data 9,7,14,32,15,6,32,20,8,5,32,14,5,15,18,1,13,33
9712 data 3,15,14,20,1,3,20,32,13,5,32,22,9,1,32,13,1,9
9713 data 12,32,3,54,52,0,5,14,20,8,21,19,9,46,4,5,32,47
9714 data 50,48,48,56,169,2,133,2,173,48,3,141,112,202,173,49,3,141
9715 data 113,202,169,135,141,48,3,169,203,141,49,3,173,50,3,141,110,202
9716 data 173,51,3,141,111,202,169,114,141,50,3,169,202,141,51,3,169,0
9717 data 141,32,208,162,0,189,67,202,32,210,255,240,3,232,208,245,96,147
9718 data 13,32,42,42,32,78,69,79,82,65,77,45,68,82,73,86,69,32
9719 data 78,50,67,47,79,78,83,76,65,85,71,72,84,32,86,48,46,52
9720 data 48,32,42,42,13,0,234,245,162,244,164,186,196,2,240,3,108,110
9721 data 202,120,32,198,207,32,51,203,32,33,203,32,33,203,32,33,203,160
9722 data 0,140,12,3,172,12,3,177,187,160,0,32,155,207,32,33,203,172
9723 data 12,3,200,196,183,240,3,76,141,202,169,0,160,0,32,155,207,32
9724 data 33,203,165,193,32,155,207,32,33,203,165,194,32,155,207,32,33,203
9725 data 165,194,197,175,208,6,165,193,197,174,240,14,177,193,32,155,207,32
9726 data 33,203,32,44,203,76,194,202,169,0,32,155,207,165,251,141,12,3
9727 data 165,252,141,13,3,165,253,141,14,3,32,33,203,169,0,32,155,207
9728 data 32,33,203,169,0,32,155,207,32,51,203,173,12,3,32,155,207,32
9729 data 33,203,173,13,3,32,155,207,32,33,203,173,14,3,32,155,207,24
9730 data 32,205,207,88,96,230,251,208,6,230,252,208,2,230,253,96,230,193
9731 data 208,2,230,194,96,169,7,133,252,169,0,133,251,133,253,160,0,32
9732 data 129,207,133,167,32,33,203,32,129,207,133,168,32,33,203,32,129,207
9733 data 133,169,165,167,208,11,165,168,208,7,165,169,208,3,76,114,203,166
9734 data 167,134,251,166,168,134,252,166,169,134,253,76,61,203,165,251,56,233
9735 data 2,133,251,165,252,233,0,133,252,165,253,233,0,133,253,24,96,72
9736 data 165,186,197,2,240,4,104,108,112,202,104,133,147,160,0,177,187,201
9737 data 95,208,3,76,74,207,201,92,208,3,76,241,205,201,36,208,3,76
9738 data 202,204,120,32,198,207,32,28,204,165,185,208,17,165,195,133,193,165
9739 data 196,133,194,32,33,203,32,33,203,76,218,203,32,129,207,133,193,32
9740 data 33,203,32,129,207,133,194,32,33,203,165,253,197,176,208,12,165,252
9741 data 197,175,208,6,165,251,197,174,240,34,165,147,208,14,32,129,207,145
9742 data 193,32,33,203,32,44,203,76,218,203,32,129,207,209,193,240,240,32
9743 data 205,207,88,169,28,76,21,247,166,193,164,194,32,205,207,88,169,64
9744 data 133,144,24,96,169,7,133,252,169,0,133,251,133,253,160,0,140,12
9745 data 3,165,251,133,193,165,252,133,194,165,253,133,170,32,129,207,133,167
9746 data 32,33,203,32,129,207,133,168,32,33,203,32,129,207,133,169,165,167
9747 data 208,11,165,168,208,7,165,169,208,3,76,165,204,165,167,133,174,165
9748 data 168,133,175,165,169,133,176,32,33,203,172,12,3,177,187,201,42,240
9749 data 74,201,63,240,15,160,0,72,32,129,207,240,24,133,171,104,197,171
9750 data 208,40,172,12,3,196,183,240,33,200,140,12,3,32,33,203,76,106
9751 data 204,104,172,12,3,196,183,208,15,32,33,203,160,0,96,104,104,32
9752 data 205,207,88,76,4,247,165,174,133,251,165,175,133,252,165,176,133,253
9753 data 76,38,204,160,0,32,33,203,32,129,207,208,248,76,159,204,120,162
9754 data 255,232,189,188,205,32,210,255,208,247,32,198,207,169,7,133,175,133
9755 data 252,169,0,133,251,133,253,133,174,133,176,160,0,32,129,207,133,167
9756 data 32,33,203,32,129,207,133,168,32,33,203,32,129,207,133,169,165,167
9757 data 208,11,165,168,208,7,165,169,208,3,76,143,205,56,165,167,229,174
9758 data 141,223,205,165,168,229,175,141,224,205,32,205,207,174,224,205,224,100
9759 data 176,5,169,32,32,210,255,224,10,176,5,169,32,32,210,255,232,138
9760 data 32,212,207,169,32,32,210,255,169,34,32,210,255,32,198,207,165,167
9761 data 133,174,165,168,133,175,165,169,133,176,160,0,32,33,203,32,129,207
9762 data 240,16,72,32,205,207,88,104,32,210,255,120,32,198,207,76,86,205
9763 data 165,174,133,251,165,175,133,252,165,176,133,253,32,205,207,88,169,34
9764 data 32,210,255,169,13,32,210,255,120,32,198,207,76,233,204,32,205,207
9765 data 88,169,13,32,210,255,56,169,255,229,252,170,169,31,229,253,32,205
9766 data 189,162,0,189,210,205,240,6,32,210,255,232,208,245,24,166,45,164
9767 data 46,169,64,133,144,96,13,18,32,32,78,69,79,82,65,77,45,68
9768 data 82,73,86,69,32,32,146,13,13,0,32,66,76,79,67,75,83,32
9769 data 70,82,69,69,0,0,0,0,0,0,0,0,0,0,0,0,0,0
9770 data 0,0,0,0,0,120,32,198,207,198,183,230,187,208,2,230,188,32
9771 data 28,204,32,51,203,32,33,203,32,33,203,32,33,203,32,33,203,165
9772 data 251,141,238,205,165,252,141,239,205,165,253,141,240,205,56,165,174,141
9773 data 229,205,229,193,141,235,205,165,175,141,230,205,229,194,141,236,205,165
9774 data 176,141,231,205,229,170,141,237,205,165,193,141,232,205,165,194,141,233
9775 data 205,165,170,141,234,205,173,229,205,133,251,173,230,205,133,252,173,231
9776 data 205,133,253,32,129,207,72,32,33,203,165,251,141,229,205,165,252,141
9777 data 230,205,165,253,141,231,205,173,232,205,133,251,173,233,205,133,252,173
9778 data 234,205,133,253,104,32,155,207,32,33,203,165,251,141,232,205,165,252
9779 data 141,233,205,165,253,141,234,205,173,229,205,205,238,205,208,174,173,230
9780 data 205,205,239,205,208,166,173,230,205,205,239,205,208,158,160,0,165,193
9781 data 133,251,165,194,133,252,165,170,133,253,32,129,207,141,223,205,56,237
9782 data 235,205,141,226,205,8,32,155,207,32,33,203,32,129,207,141,224,205
9783 data 40,237,236,205,141,227,205,8,32,155,207,32,33,203,32,129,207,141
9784 data 225,205,40,237,237,205,141,228,205,32,155,207,173,223,205,208,49,173
9785 data 224,205,208,44,173,225,205,208,39,165,251,56,233,2,133,251,165,252
9786 data 233,0,133,252,165,253,233,0,133,253,169,0,32,155,207,32,33,203
9787 data 32,155,207,32,33,203,32,155,207,76,60,207,173,226,205,133,251,173
9788 data 227,205,133,252,173,228,205,133,253,76,188,206,24,166,45,164,46,32
9789 data 205,207,88,169,64,133,144,96,120,238,32,208,32,198,207,169,7,133
9790 data 252,169,0,133,251,133,253,32,155,207,32,33,203,32,155,207,32,33
9791 data 203,32,155,207,32,33,203,32,155,207,32,33,203,133,251,133,252,133
9792 data 253,32,205,207,206,32,208,88,96,165,252,133,254,41,63,141,254,223
9793 data 165,253,6,254,42,6,254,42,141,255,223,166,251,189,0,222,96,142
9794 data 192,207,140,194,207,141,196,207,168,165,252,133,254,41,63,141,254,223
9795 data 165,253,6,254,42,6,254,42,141,255,223,166,251,152,157,0,222,162
9796 data 0,160,0,169,0,96,165,1,41,253,133,1,96,165,1,9,3,133
9797 data 1,96,162,0,32,236,207,72,232,192,0,240,4,152,76,214,207,104
9798 data 9,48,32,210,255,202,208,247,56,160,255,200,233,10,176,251,105,10
9799 data 96,0,0,0,0,0,0,0,0,0
