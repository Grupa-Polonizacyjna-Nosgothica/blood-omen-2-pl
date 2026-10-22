# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

An unofficial subtitles patch (and, in time, Polish translation) for *Legacy of Kain: Blood Omen 2* (PC, GOG build) by Grupa Polonizacyjna Nosgothica. The PC game ships a complete caption system in its engine but no caption text and with drawing switched off. We patch the user's own `bo2.exe` (a few bytes plus a small routine that reads `.cnv` subtitle files from `data\texts`), ship our own subtitle files, and install it all with an Inno Setup installer built around a small C++ patcher. Nothing from the game is ever stored or shipped here. The README is bilingual (Polish, then English) and written for end users; developer docs are in `docs/` (English).

## Layout

- `docs/TOOLING.md`: prerequisites, build and tool commands, workflows (start here for "how do I run X").
- `docs/captions.md`: how the engine's caption pipeline works, the `.cnv` record format, every address we patch. The main reverse-engineering notes.
- `docs/patching.md`: the manifest format, the patcher and its exit codes, the installer, tests/CI, what is not yet run.
- `docs/fonts.md`: font format (bitmap + glyph tables), the lower-case/foreign-letter convention, the plan for the Polish letters.
- `docs/dialogue.md`: `pc.rkv` extraction, phrase keys, the dialogue index.
- `patch/cave.s`: code added to `bo2.exe`. `patch/bo2pl.patch`: the **generated** manifest the patcher applies (commit it after regenerating). `patch/diag/cave_diag.s`: logging hooks for reverse engineering, not shipped.
- `tools/`: Python tools (`build_patch.py`, `font_tool.py`, `rkv_extract.py`, `dialogue_index.py`, `build_diag.py`), `patcher/Bo2Patcher.cpp` (C++17, CMake in `tools/CMakeLists.txt`), `test_patcher.py`.
- `installer/`: `bo2pl.iss`, `INSTALL.txt`, `reapply.cmd`. `.github/workflows/build.yml`: CI.
- `subtitles/EN`, `subtitles/PL`: `.cnv` files (`PL/` is what the installer ships; so far only an English test file exists, in `EN/`).
- `GameData/` is **gitignored**: the developer's own copy of the game plus extracted files (`GameData/ogg/`, `GameData/_work/`). Never commit anything from it.

## Commands

Details and more in `docs/TOOLING.md`.

```
cmake -S tools -B build && cmake --build build           # build/Bo2Patcher
python3 -m unittest discover -s tools                    # 12 tests, no game data needed (real files used if GameData/bo2.exe exists)
python3 tools/build_patch.py GameData                    # regenerate patch/bo2pl.patch from the ORIGINAL GameData/bo2.exe
python3 tools/build_patch.py GameData --write-patched GameData/_work/patched   # also write the patched exe to try in the game
python3 tools/rkv_extract.py GameData/data/pc.rkv GameData/ogg
python3 tools/dialogue_index.py GameData/data GameData/ogg GameData/ogg/dialogue_index.csv
python3 tools/font_tool.py extract|inject|preview|check ...
python3 tools/build_diag.py GameData/bo2.exe GameData/bo2_diag.exe   # logging build, log: <wine prefix>/drive_c/bo2_diag.log
```

No linter. Python tools use the standard library (the font tool also needs Pillow and numpy); the cave needs GNU `as`/`ld`/`objcopy`/`nm`.

## How it works (short; see `docs/captions.md`)

- Every spoken line calls `SpeechHandler::PhraseStart` (0x4b6420) with a *phrase key* (lower-case voice name, e.g. `sl02_umah_01`). The key is looked up in a global phrase table; on a miss the caption section is skipped (this is why the shipped game shows nothing).
- The table is filled per level/UI group from `/gogames/bo2/resources/levels/<area>/<name>.cnv` through the engine's virtual file system, which only knows the archives and finds none. `patch/cave.s` hooks the whole-file reader's failure branch (0x758e76) and reads `.\data\texts\<basename>` from disk instead.
- `.cnv` record: `<key> "<label>"`, then text lines (joined with spaces), ended by a blank line; lines shorter than 3 characters end a record. Text is **lower case**; upper-case code points are accented foreign letters in the game's font.
- Other patches: the draw routine ignores the hidden "show captions" debug flag (0x5205c7) and two one-byte layout fixes (0x52064f, 0x520695) so multi-line captions are not lifted twice.
- Addresses are virtual addresses of the GOG `bo2.exe` (SHA-256 `4abee85a1da1b2c2ae9764a53cc34a8f6ec3f496e5ce6fd8a918af79bf0f9ade`, image base 0x400000; for `.text`, file offset = address - 0x400000). The patcher and `build_patch.py` refuse any other build.

## Conventions and gotchas

- **Shipped data**: the manifest stores only CRC-32 of original bytes plus our new bytes. Keep it that way: no original game bytes, no game files, no extracted audio or textures in the repo.
- After any change to `patch/cave.s`, `EXE_PATCHES` in `build_patch.py` or an edited font, regenerate **and commit** `patch/bo2pl.patch`. `CAVE_SIZE` in `build_patch.py` must match the assembled cave.
- The patcher writes ranges in place and keeps a full `<file>.plbackup`; `restore` refuses without a valid backup. Keep the exit codes (docs/patching.md) in sync with the strings in `installer/bo2pl.iss`.
- The font exists in **both** `PreCode.big` and `Code.big` (the `Code.big` bitmap is stored upside down; `font_tool.py` handles that). Which copy the game draws is unknown. Glyph records are `u8 code + 3 bytes 0xFF` (keep the padding), tables must keep 87 rows.
- File names in the game folder are mixed case (`precode.big` on disk, `PreCode.big` in docs); the tools look names up case-insensitively.
- Games run under Wine/Proton are a normal way to test here (Heroic). The game's own debug output goes nowhere in the release build; use `build_diag.py` for runtime information.
- `installer/bo2pl.iss` and `INSTALL.txt` are UTF-8 with BOM and CRLF (Inno Setup needs that for the Polish texts); keep that when editing.

## Status (keep this section current)

Verified in the game: captions show and are laid out correctly in the Slums opening (English test text). Written but **not yet run**: the Windows build of `Bo2Patcher`, the Inno Setup installer (never compiled; no Inno Setup on the development machine). Not done: the Polish glyphs and the Unicode-to-glyph-code step, the Polish subtitles, centring/smaller text/no labels/a separate caption font (all judged feasible, untested), Steam build support. Open questions are listed at the end of `docs/captions.md`.

## Commit rules

Keep the commit message brief and to the point. ***Use `Assisted-By` instead of `Co-Authored-By` when marking AI-assisted commits***, (e.g. `Assisted-By: Claude Sonnet 5.5 <noreply@anthropic.com>`). This applies to pull request descriptions written by the assistant as well; do not add `Co-Authored-By` lines.
