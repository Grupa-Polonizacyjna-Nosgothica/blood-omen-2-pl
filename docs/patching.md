# Patching and the installer

The game is changed on the player's own machine; nothing from the game is shipped. What ships:

* `Bo2Patcher.exe` (built from `tools/patcher/Bo2Patcher.cpp`, C++17, static runtime),
* `bo2pl.patch`, the patch manifest (`patch/bo2pl.patch`, ~1 KB for the exe patch),
* our subtitle files `subtitles/PL/*.cnv`, copied as plain files to `<game>/data/texts/`,
* an Inno Setup installer (`installer/bo2pl.iss`) that finds the game and runs the patcher.

## The manifest

`tools/build_patch.py <original game dir>` applies the exe edits (`EXE_PATCHES` in the script plus the assembled
`patch/cave.s`, see `docs/captions.md`), optionally injects an edited font (`--fonts`, see `docs/fonts.md`) and diffs
every original/modified file pair into *range patches*:

    BO2PL-PATCH 1
    file bo2.exe size 5378116 crc32 321ed88f
    range 1205c7 6 17396cf3 909090909090      # offset (hex), length, CRC-32 of the ORIGINAL bytes, NEW bytes (hex)

The manifest never holds original game bytes, only a checksum of them, so it can be published freely. Rebuild it with
`python3 tools/build_patch.py GameData` (GNU `as`, `ld`, `objcopy` needed for the cave) and commit the result.
`--write-patched DIR` also writes the patched files, to try them in the game without the installer.

## The patcher

    Bo2Patcher check   <game dir> [bo2pl.patch]
    Bo2Patcher patch   <game dir> [bo2pl.patch] [--force]
    Bo2Patcher restore <game dir> [bo2pl.patch]

A file is **original** when its size and CRC-32 match and every range still has its original CRC, **patched** when every
range holds the new bytes, otherwise unsupported (wrong build) or changed (something else modified it). `patch`
refuses anything but original/patched, copies the file to `<file>.plbackup`, writes the ranges in place and re-reads the
file to verify. It is idempotent. `restore` copies the backup back (after checking that it is the original) and removes it.
Without a valid backup it refuses and tells the user to verify the game files in GOG/Steam.

| Exit code | Meaning |
|---|---|
| 0 | ok |
| 1 | usage |
| 2 | other error |
| 3 | unsupported game build (size/CRC mismatch) |
| 4 | the game is running (a process named `bo2.exe`; on Linux: process name or argv[0]) |
| 5 | not enough disk space |
| 6 | a file was changed by something else, or the backup is missing/invalid |
| 7 | no write access |

## The installer

`installer/bo2pl.iss` (Inno Setup 6) builds `BO2-PL-Setup-<version>.exe`:

* **Finding the game:** GOG (registry key `SOFTWARE\GOG.com\Games\1207659101`, `path`), then a best-effort Steam search
  (`steamapps\common\Legacy of Kain Blood Omen 2` in each library); otherwise the user picks the folder, which must contain
  `bo2.exe` and `data\pc.rkv`.
* On the folder page `Bo2Patcher check` runs and its exit code becomes a message, before anything is copied.
* After copying it runs `Bo2Patcher patch` (log: `<game>\Bo2PL\patch.log`); on failure it explains and points to the Start
  menu shortcut "Zastosuj spolszczenie ponownie" (`reapply.cmd`, runs elevated).
* Uninstall runs `restore` first and removes the copied subtitle files.
* Needs administrator rights (games are often in protected folders). Texts: Polish and English.
* Local build: `ISCC.exe /DAppVersion=1.0.0 /DPatcherExe=..\dist\Bo2Patcher.exe /DPatchFile=..\patch\bo2pl.patch installer\bo2pl.iss`.
  No wizard images or icon are set (Inno defaults); add `SetupIconFile`, `WizardImageFile` and `WizardSmallImageFile` if wanted.

## Tests and CI

* `python3 -m unittest discover -s tools` (after `cmake -S tools -B build && cmake --build build`): manifest builder
  and the patcher on synthetic game files (patch, idempotence, byte-identical restore, wrong build, tampering, lost backup,
  read-only file, running game, usage), plus a patch/restore cycle on a copy of the real `bo2.exe` when `GameData/` has one.
* `.github/workflows/build.yml` builds and tests on Windows and Linux, builds the installer on Windows and publishes the
  artifacts on a `v*` tag.

## Status

* The patch itself (the exe edits) was tried in the game: captions appear and are laid out correctly.
* **Not yet run:** the C++ patcher on Windows, and the installer script. Inno Setup was not available when it was written, so
  neither the script nor the wizard flow has been compiled or clicked through; the first CI run is the first compile.
* The font patch is not part of the manifest yet (no edited font).
