10 rem neoram utils 1.0: choose geodiag or neocopy
20 ml=828:for i=0 to 62-1:read v:poke ml+i,v:next
30 dv=peek(186):if dv<8 or dv>30 then dv=8
40 print chr$(147)chr$(142)"neoram utils 1.0":print
50 print " 1  geodiag 1.4: test the card,":print "    every ram pin and every byte":print
60 print " 2  neocopy 1.1: enthusi's neoram-drive":print "    install, format, copy files, start":print
70 print " q  quit":print
80 get k$:if k$="1" then n$="geodiag":goto 200
90 if k$="2" then n$="neocopy":goto 200
100 if k$="q" then end
110 goto 80
200 print "loading "n$" from drive"dv
210 poke 871,dv:poke 872,len(n$):poke 873,0
220 for i=1 to len(n$):poke 874+i-1,asc(mid$(n$,i,1)):next
230 sys ml
240 print "could not load it (error"peek(873)")":end
9600 data 169,1,174,103,3,160,1,32,186,255,173,104,3,162,106,160,3,32
9601 data 189,255,169,0,32,213,255,176,12,142,45,0,140,46,0,32,89,166
9602 data 76,174,167,141,105,3,96,8,0,0,0,0,0,0,0,0,0,0
9603 data 0,0,0,0,0,0,0,0
