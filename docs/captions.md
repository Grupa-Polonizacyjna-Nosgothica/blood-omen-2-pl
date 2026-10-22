# How Blood Omen 2 shows captions (and what we changed)

The PC build of Blood Omen 2 contains a complete caption system, but ships no caption text. Nothing in
`data/` contains the dialogue, and the debug option that turns the drawing on is hidden. This is what the
engine does, found by reading `bo2.exe` (Ghidra) and by logging from inside the running game (Wine/Proton).
Addresses are virtual addresses of the shipped GOG `bo2.exe` (image base 0x400000, SHA-256 `4abee85a…9ade`).
**Observed** = seen in the code or the game's own log; **inferred** = a reading of the code that was not tested.

## The pipeline

1. **Speech starts.** `SpeechHandler::PhraseStart` (0x4b6420) is called for every spoken line, in cutscenes and
   for ambient NPCs alike. Its argument carries the *phrase key*: the lower-case sound name, e.g. `sl02_umah_01`
   (the voice stream `vo/SL02_UMAH_01` in `pc.rkv`). Observed.
2. **Phrase table lookup.** The key is looked up in a global map (`[0xa83cac]`, find at 0x75aa30). A hit gives a
   *phrase record* (below). On a miss PhraseStart still plays the sound, then **clears its text field and skips the
   whole caption section** (the check at 0x4b6759: `cmp [text string], 0` / `je 0x4b694b`). This is why the shipped
   game never shows captions: the map is empty. Observed (log lines `P ... record 0`).
3. **Caption creation.** With a record, PhraseStart parses the text (0x4b6c50, handles `\{...}` markup, see below)
   and calls `AddCaption` (0x520470) on the singleton manager (`[0x91eef0]`, created at 0x51ffd0). The record
   constructor (0x51fa90) word-wraps the text to the screen width. Observed.
4. **Drawing.** Every frame the main loop calls the manager's update (0x5206c0, timers and removal) and draw
   (0x5205b0) routines, at 0x4aed20 / 0x4aed2b. The draw routine starts with a debug-flag check,
   `getFlag(7, 2)` = "show captions", which is 0 in release builds (see "Debug flags"). Observed.
5. **Removal.** A caption lives until its speech ends (lifetime passed to `AddCaption` is `FLT_MAX`), then 0x520530
   removes it. Observed in the `D` log lines (the remaining-lifetime field stays `7F7FFFFF`).

## Where the phrase table comes from: `.cnv` files

`PhraseTable::Load` (0x75aa70, called from 0x794cd0 for every level or UI group that loads) asks the engine's
virtual file system for

    /gogames/bo2/resources/levels/<area>/<name>.cnv        e.g. .../ui/hud.cnv, .../slums/sl01.cnv, .../slums/sl02.cnv

where `<name>` is the archive name without `.big` (`sl01.big` -> `sl01.cnv`; the UI screens `optionscreen_01`,
`hud`, `darkgifts`, `pausemenu` load first). The virtual file system only knows the archives, none of which contains
a `.cnv`, so every request fails silently (no file access happens at all; checked with a `CreateFileA` logger).
The records of a loaded file are added to the one global table, so a line only has to be in *some* `.cnv` that
is loaded before it is spoken. Observed.

### Record format (parser at 0x75a2c0)

    <phrase key> "<label>"        first line: key up to the first space; optional quoted label
    <text line>                   one or more text lines, joined with single spaces
    <text line>
    (blank line)                  a line shorter than 3 characters ends the record (and is skipped between records)

* The key becomes the sound name; the sound `vo/SND/<key>` is loaded from it (the `vo/SND/` prefix is the static string
  at 0xa83ca8). A missing sound does not matter for captions.
* The quoted **label** is the speaker name drawn before the text ("UMAH:"). Without it the engine asks the speaking
  creature for its `captionedname` (tune data) via `GetCaptionedNameMsg` and logs an error if it cannot answer.
  Leaving the quotes out was not tested.
* CR/LF are stripped, lines are read with a 512 byte buffer. Keep text lines at least 3 characters long.
* Timing markup `\{...}` in the text is understood by the parser (0x4b6c50: it looks for `\{`, a space, `,` and `}` and reads a
  number as a duration, warning "duration ... is probably an error" below 0.001 s). Plain text works without it. The exact
  grammar is **inferred and untested**.

### The patch that makes the game read them from disk

`FUN_00758e60` (0x758e60, the engine's "read the whole file into memory" routine) jumps to its epilogue at 0x758e76 when
the virtual file system has no such file. `patch/cave.s` replaces that jump: for paths ending in `.cnv` it opens
`.\data\texts\<basename>` from disk, allocates a zeroed buffer through the engine's allocator, reads the file in and sets
the file object's size/data fields, then falls into the normal epilogue. For everything else it is the original
failure path. Tested in the game (Slums opening: all 13 lines of `sl02.cnv` showed).

## Text conventions (the font)

All game text is **lower case**: the font draws every letter in the same small-caps style, and the upper-case code points
`A`-`Z` are used for accented foreign letters (German ü=`B`, ö=`O`, ä=`E`; Spanish á=`T`, é=`C`, ó=`V`, ú=`W`, ñ=`X`, ¿=`Y`
...). Write captions in lower case, and see `docs/fonts.md` for how to add the Polish letters.

## Layout (all values from the shipped tune data, observed in the log)

The manager's settings come from the `gamekeeper` tune object (`CaptionGameKeeperTune` in `Code.big`):
font name, `maxNumDraw` = 2 captions at once, left/right indent 0.075, label-to-text gap 0.05, bottom line y = -0.9 (unit
screen coordinates, +y up). The draw routine **bottom-anchors** multi-line text, but the shipped code compensated as if it
were top-anchored, lifting every extra line twice. We fix that (patches 2 and 3 below).

## Patches in the shipped patch (`tools/build_patch.py`, `patch/bo2pl.patch`)

| # | Address | Original | New | Purpose |
|---|---|---|---|---|
| 1 | 0x5205c7 | `0f 84 e8 00 00 00` | 6x `90` | draw routine: ignore the "show captions" flag |
| 2 | 0x52064f | `1c` | `38` | `fsub [rec+0x1c]` -> `fsub [rec+0x38]`: no extra upward shift of multi-line captions |
| 3 | 0x520695 | `1c` | `38` | `fld [rec+0x1c]` -> `fld [rec+0x38]`: stack the next caption by its full height |
| 4 | 0x758e76 | `0f 84 81 00 00 00` | `0f 84 <rel32>` | reader failure branch -> `patch/cave.s` |
| 5 | 0x83e780 | 288 zero bytes | `patch/cave.s` | the loose-file fallback, in the unused tail of `.text` |

## Debug flags

The "show captions" option is entry 2 of a table of 20 debug flags at 0x8f0908 (group 7, "Blood Omen Specific Flags";
others: "show camera Z lag", "dont show monster prints", "allow abort from cinematics", ...). Flags are read with
`getFlag(group, id)` (0x690200). A debug menu would list them; it is only built when a debug-enable global is set, which the
release build never does. Patch 1 bypasses the flag instead of finding a way to set it.

## Diagnostics

`tools/build_diag.py` builds an exe with logging hooks (`patch/diag/cave_diag.s`, log format in its header) for further
reverse engineering; the log is written to `C:\bo2_diag.log` (in a Wine prefix: `drive_c/bo2_diag.log`).

## Open questions

* The `\{...}` timing markup and what it does to the caption (not needed for plain captions).
* Whether the `.cnv` files are also requested for languages other than English (the shipped game has the five language
  blocks `english`, `french`, `italian`, `german`, `spanish` in its archives; only English was played).
* Steam build: not tested; the supported build is the GOG one above (the patcher refuses anything else).
