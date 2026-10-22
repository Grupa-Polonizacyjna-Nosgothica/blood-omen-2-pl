# Tooling and build instructions

Everything needed to work on the patch, the font and the subtitles. For how the patch itself works see
[captions.md](captions.md), [patching.md](patching.md), [fonts.md](fonts.md) and [dialogue.md](dialogue.md).

## Prerequisites

| For | Needs |
|---|---|
| all Python tools | Python 3.10+ (standard library only, except as noted) |
| `font_tool.py` | Pillow and numpy |
| `build_patch.py`, `build_diag.py` | GNU binutils: `as`, `ld`, `objcopy`, `nm` (Linux, or WSL/MSYS2 on Windows) to assemble `patch/cave.s` |
| `Bo2Patcher` | CMake 3.16+ and a C++17 compiler (MSVC, GCC or Clang) |
| the installer | Inno Setup 6 (Windows; CI has it preinstalled) |
| running the game on Linux | Wine/Proton, e.g. through Heroic (optional) |

## Game files

Copy your own **GOG** game folder (at least `bo2.exe` and `data/`) into `GameData/`. It is gitignored; never commit
anything from it. The tools expect the *original* files there: `bo2.exe` must be the unmodified GOG build
(SHA-256 `4abee85a…9ade`), and `build_patch.py` refuses anything else. Extracted and generated files go to
`GameData/_work/` and `GameData/ogg/`, also gitignored.

## Building and testing the patcher

    cmake -S tools -B build && cmake --build build            # build/Bo2Patcher (build/Release/Bo2Patcher.exe on Windows)
    python3 -m unittest discover -s tools                     # 12 tests; synthetic game files, no game data needed
    python3 -m unittest discover -s tools -v                  # same, verbose

The tests find the patcher in `build/` or through `$BO2_PATCHER` and skip the patcher tests when it is not built. If
`GameData/bo2.exe` exists, one more test runs a patch/restore cycle on a copy of it.

## The patch (`bo2.exe`)

Regenerate `patch/bo2pl.patch` after **any** change to `patch/cave.s`, to `EXE_PATCHES` in `tools/build_patch.py`, or to the
edited font, and commit the result:

    python3 tools/build_patch.py GameData                              # writes patch/bo2pl.patch
    python3 tools/build_patch.py GameData --fonts fonts                # ... including an edited font (see below)
    python3 tools/build_patch.py GameData --write-patched GameData/_work/patched   # also write the patched files

`--write-patched` is the way to try a change in the game without the installer: copy the patched `bo2.exe` over the
game's (keep a backup). `CAVE_SIZE` in `build_patch.py` must equal the size of the assembled `cave.s`; the script says so
when it does not.

Try the patcher on a copy:

    mkdir /tmp/g && cp GameData/bo2.exe /tmp/g/
    build/Bo2Patcher check   /tmp/g patch/bo2pl.patch
    build/Bo2Patcher patch   /tmp/g patch/bo2pl.patch
    build/Bo2Patcher restore /tmp/g patch/bo2pl.patch

## Subtitles

Subtitle files are `.cnv` files, one per level archive (`sl01.big` -> `sl01.cnv`); format and rules in
[captions.md](captions.md#record-format-parser-at-0x75a2c0). To try a file, copy it to `<game>/data/texts/` and start the
patched game (the Slums opening plays at the start of a new game). Write the text in lower case (see
[fonts.md](fonts.md)). `subtitles/EN/` holds English reference text, `subtitles/PL/` the translation the installer ships.

## Voice lines

    python3 tools/rkv_extract.py GameData/data/pc.rkv GameData/ogg                   # 2,824 .ogg files + index.csv
    python3 tools/dialogue_index.py GameData/data GameData/ogg GameData/ogg/dialogue_index.csv --skeleton GameData/_work/cnv-skeleton

See [dialogue.md](dialogue.md) for what the index columns mean and how to pick the right `.cnv` for a line.

## Font

    python3 tools/font_tool.py extract GameData/data GameData/_work/font     # atlas.png, guides.png, glyphs*.tsv, font.json
    python3 tools/font_tool.py preview GameData/_work/font precode "text"    # test line from the edited atlas and table
    python3 tools/font_tool.py inject  GameData/data GameData/_work/font --out-dir /tmp/fontout
    python3 tools/font_tool.py check   GameData/data                         # round trip must be byte-identical

To ship an edited font keep the edited directory in the repo (e.g. `fonts/`) and build the manifest with `--fonts fonts`.
Details and the rules for editing: [fonts.md](fonts.md).

## Diagnostics (reverse engineering)

    python3 tools/build_diag.py GameData/bo2.exe GameData/bo2_diag.exe

builds an exe with logging hooks (`patch/diag/cave_diag.s`). Run it in the game and read the log, which is written to
`C:\bo2_diag.log`; in a Wine/Proton prefix that is `<prefix>/drive_c/bo2_diag.log` (Heroic: `~/Games/Heroic/Prefixes/<game>/drive_c/`).
The format of the lines is in the header of `cave_diag.s`; `docs/captions.md` explains what the values mean. Delete the log
before each run (it appends). The hooks do not belong in the shipped patch.

Ghidra with the REA tools was used for the static analysis; the addresses in the docs are virtual addresses of the GOG
`bo2.exe` (image base 0x400000; for the `.text` section file offset = address - 0x400000).

## The installer and releases

    ISCC.exe /DAppVersion=1.0.0 /DPatcherExe=..\dist\Bo2Patcher.exe /DPatchFile=..\patch\bo2pl.patch installer\bo2pl.iss

Run it from the repo root after building `Bo2Patcher.exe` into `dist\`; the result is `dist\BO2-PL-Setup-<version>.exe`.
CI (`.github/workflows/build.yml`) builds and tests the patcher on Windows and Linux, builds the installer on Windows and,
for a pushed tag `v*`, publishes patcher and installer as a GitHub release. The installer script has not been compiled yet
(see [patching.md](patching.md#status)).

## Tool reference

| File | What it does |
|---|---|
| `tools/build_patch.py` | applies the exe edits, optionally the edited font, and writes `patch/bo2pl.patch` |
| `tools/patcher/Bo2Patcher.cpp` | the patcher the installer runs: `check`, `patch`, `restore` |
| `tools/test_patcher.py` | tests of the manifest builder and the patcher |
| `tools/font_tool.py` | extracts/injects the font bitmap and glyph tables |
| `tools/rkv_extract.py` | unpacks the Ogg streams from `pc.rkv` |
| `tools/dialogue_index.py` | maps phrase keys to archives (`.cnv` files) and voice files |
| `tools/build_diag.py` | builds the logging exe |
| `patch/cave.s` | the code added to `bo2.exe` (loose-file fallback) |
| `patch/diag/cave_diag.s` | the logging hooks |
