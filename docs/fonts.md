# The font

Blood Omen 2 draws all text (menus, hints, captions) with one bitmap font that lives inside the archives. It has no
real upper/lower case and no Polish letters, so the translation needs a modified font. `tools/font_tool.py` extracts it
into files an image editor can open and puts the edited result back.

## What is where

Both `data/PreCode.big` and `data/Code.big` contain a copy: a 256x256 **uncompressed A8R8G8B8 DDS** (128 byte header +
262144 bytes of pixels) and two glyph tables (chunks `texfont`, identical in the shipped game). In `Code.big` the rows are
stored upside down; `font_tool.py` detects that and always gives you an upright image. Which copy the game draws is
**not known** (inject both; if only one matters, the other is harmless).

Glyph table: 24 byte header (`u16 0, u16 0xffff, f32 20.0 line height, f32 2.0, f32 5.0, f32 8.0, u8 0, u8 0xff, u16 count`)
and 87 records of 20 bytes: `u8 code, 3 bytes 0xFF, f32 x, y, w, h` (pixels, y from the top).

The atlas (see `GameData/_work/font/*/guides.png` after extracting):

* `a`-`z`, digits and punctuation: the letters (all drawn as one alphabet, small caps style; no separate capitals);
* `A`-`Z`: **accented foreign letters**, used as codes in the French/Italian/German/Spanish texts (`B`=ü, `C`=é, `E`=ä, `O`=ö,
  `T`=á, `V`=ó, `W`=ú, `X`=ñ, `Y`=¿, `Z`=¡ ...; the code `S` shares the cell of `?`, so it has no art of its own) and the PlayStation button icons (codes 0xc8-0xd3);
* the lower part of the atlas holds solid colour blocks (probably flat-colour quads); leave it alone.

Game text is lower case, with the foreign letters written as those upper-case codes.

## Tool

    python3 tools/font_tool.py extract <game>/data work/font      # atlas.png, guides.png, glyphs0.tsv, glyphs1.tsv, font.json per archive
    python3 tools/font_tool.py preview work/font precode "text"   # render a test line from the edited atlas and table
    python3 tools/font_tool.py inject  <game>/data work/font --out-dir out   # write edited archives (in place without --out-dir)
    python3 tools/font_tool.py check   <game>/data                # extract + inject gives byte-identical archives

Edit `atlas.png` (keep it 256x256, RGBA, white glyphs with alpha) and the `glyphs*.tsv` tables (`code, char, x, y, w, h`). Rules:
the tables keep exactly 87 rows (the archive has no room for more); edit both tables of an archive consistently; the
code of a row is the character code the text will use.

To ship an edited font: keep the edited `work/font` directory in the repo (for example `fonts/`) and run
`python3 tools/build_patch.py <game dir> --fonts fonts`; the manifest then also carries the font ranges. The patcher backs
up and restores `PreCode.big` and `Code.big` like the exe.

## Adding the Polish letters (plan)

ą ć ę ł ń ś ź ż need glyphs (ó exists as `V`). Cells to reuse are the foreign-letter cells `A`-`Z`, which a Polish-only text
does not use. Because the art has no case, one glyph per letter is enough. The text files then use the chosen codes
(a small Unicode-to-code table in the build step, still to be written). Colour blocks and button icons stay untouched.
