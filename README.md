# GEODIAG: a GeoRAM / NeoRAM diagnostic for the C64 and C128

GEODIAG tests a **GeoRAM**, **NeoRAM** or compatible RAM expansion (such as the **NeoRAM Remix** or an
Ultimate II+'s GeoRAM emulation). It finds the card's size, checks every data line and both
registers, tests every byte, and for a bad card says **which RAM chip and which pins** are not
making contact, with a drawing of the chip.

Version 1.4. A BASIC program with a small machine-code helper, for C64 mode and for C128 mode.

## Files

| file | what |
|---|---|
| [`release/geodiag64.d64`](release/geodiag64.d64) | a disk with one file, `geodiag` (the C64 version): `LOAD"GEODIAG",8` then `RUN` |
| [`release/geodiag64-v1.4.prg`](release/geodiag64-v1.4.prg) | the C64 version as a PRG |
| [`release/geodiag128-v1.4.prg`](release/geodiag128-v1.4.prg) | the C128 version (C128 mode, `$1C01`); adds a full test at 2 MHz |
| `release/geodiag64.bas`, `geodiag128.bas` | the BASIC listings, for reading |

**On an Ultimate II+ with its I/O lines switched off** (for example on an expansion port expander, so a
real GeoRAM can use `$DE00`-`$DFFF`), the Ultimate cannot run a PRG directly: mount the D64 and
load it from the drive instead.

## What it does

At start it runs the **quick checks** and reports them in plain words:

- **Raw reads** of `$DE00`-`$DE07` and the registers, before anything is written.
- **Data lines D0-D7**: does each one store both a 0 and a 1? A card that stores nothing is reported as
  "no card is answering".
- **Page register** (bits 0-5): does each bit select memory of its own?
- **Block register** (bits 0-7): finds where memory ends (the size: 512 KB, 1 MB, 2 MB or 4 MB) and any hole.

Then the menu:

| key | test | the card's contents |
|---|---|---|
| `1` | **test all RAM pins**, each chip in turn: see below. Start here | kept |
| `2` | **full test**, every byte: each page is saved, filled with `$55`, `$AA` and an address pattern, checked and put back | kept |
| `3` | the same at **2 MHz** (C128 only, FAST mode) | kept |
| `4` | **read stability**: one byte read 65536 times, counting reads that differ from the first | kept |
| `5` | **look at a page** in hex | kept |
| `6` | the quick checks again | kept |
| `7` | **whole-card test**: every byte gets a value of its own, and only then is it all read back, so a write that lands in the wrong place shows. Twice (the second time inverted), then 65536 random accesses; repeats until STOP | **erased** |
| `8` | **retention, step 1**: writes a pattern over the whole card and checks it. Then turn the machine off | **erased** |
| `9` | **retention, step 2**: after power comes back, checks what the card kept, and says whether it points to the battery, one chip, or a stray write | checked |
| `Q` | quit | |

Everything tests 1-6 write is saved first and put back, so a NeoRAM keeps its contents (the battery
holds them through a power-off). The error report lists the error count, glitches (wrong on one read,
right on the next), which data bits were wrong, the first 16 errors (block, page, offset, wrote, read)
and a map of the blocks with errors.

### Test all RAM pins (menu 1)

A card is built from 512 KB chips, one per 32 blocks. Menu 1 writes one byte in each chip with walking
1s and 0s (twice) and its own value, and reports each chip:

- `ok`;
- `same chip as U1`: the card ends here, or a block select line is stuck;
- `reads back wrong`;
- `no data at all`: the chip is not selected or has no power;
- **`2 pins not connecting:`** followed by each pin, e.g. `pin 17 (D0): bottom row, 4th from the right end`,
  and a drawing of the chip with the bad pins in reverse video.

Chip names (U1-U8) and pin numbers are for the **NeoRAM Remix**, a 32-pin RAM (AS6C4008-style, 512K x 8)
per 512 KB. Its data lines are not wired in order, so GEODIAG translates the C64 data bit to the chip pin:

| C64 data bit | D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 |
|---|---|---|---|---|---|---|---|---|
| RAM pin | 17 | 15 | 18 | 14 | 19 | 13 | 20 | 21 |

Reflow each pin it names, with flux, pressing the lead down onto its pad. With a meter, the lead itself
(not its pad) should beep through to the same pin on a good chip. On other cards the data bit is still
right, but the chip names and pin numbers may not be.

It was written to find real faults: on a 2 MB NeoRAM Remix it named U2 pins 17-19 and U4 pins 14-15 as
open, and after those joints were reflowed every chip passed.

### Retention (menus 8 and 9)

Step 1 fills the card and checks it right away. Turn the machine off for a minute, an hour or a night,
then load GEODIAG again and choose 9. If almost nothing was kept, backup power did not hold: check the
battery (2.8 V or more, and the right way round), the diode, and that SJ5 is open; with the machine off,
RAM pin 32 should read about the battery voltage less 0.3 V, and pin 22 about the same. Bits flipped
all over the card point to a low or dipping backup voltage or a chip that is not a low-power (L/LL) part;
one chip alone points to that chip or its pin 32 joint.

## How a GeoRAM works

A 256-byte window at `$DE00`-`$DEFF` shows one page of the card. `$DFFE` selects the page (0-63) within
a 16 KB block, and `$DFFF` selects the block (0-255, so up to 4 MB). Both registers are write-only.

## Building

```bash
./build.sh            # -> release/: both PRGs, the D64, the BASIC listings and md5.txt
```

Needs python3 and VICE's `petcat` and `c1541`. [`src/mkgeodiag.py`](src/mkgeodiag.py) holds the BASIC
program and the helper's 6502 source; it assembles the helper with [`src/asm.py`](src/asm.py) (the small
assembler from [MeshCore 64](https://github.com/pskerrett/meshcore64)), puts it in DATA lines after the
program, and tokenises the result with `petcat`. The helper sits at `$C000` on the C64 and `$1300` on
the C128. The build is reproducible: it gives the files in `release/` byte for byte.

## Tested

- VICE (C64) with emulated GeoRAMs, including data line faults injected into single chips.
- A real C64 with two 2 MB NeoRAM Remix cards: one with a battery holder fitted backwards (found by the
  retention test), one with open data pin joints (found by the RAM pin test).
