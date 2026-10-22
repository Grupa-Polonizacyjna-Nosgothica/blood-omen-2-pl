#!/usr/bin/env python3
"""Builds patch/bo2pl.patch, the manifest the installer's patcher applies to the user's own game files.

Usage:
    build_patch.py <game_dir> [-o patch/bo2pl.patch] [--fonts fonts_dir] [--write-patched DIR]

<game_dir> is the directory with the ORIGINAL bo2.exe and data/ (a GOG or Steam install).
The tool
  1. applies the exe edits listed in EXE_PATCHES (below) to bo2.exe, with the assembled
     patch/cave.s placed in the unused tail of .text;
  2. if --fonts is given (a directory made by `font_tool.py extract` and edited), injects
     the edited font into copies of data/PreCode.big and data/Code.big;
  3. diffs every original/modified pair into range patches and writes the manifest.

The manifest never contains game data: each range stores the offset, the length, the CRC-32 of
the ORIGINAL bytes (so the patcher can recognise the right game build and a half-patched file) and
the NEW bytes, which are ours. Format (text, one record per line):

    BO2PL-PATCH 1
    file <path relative to the game dir> size <n> crc32 <hex of the whole original file>
    range <offset hex> <length> <crc32 of the original bytes hex> <new bytes hex>

--write-patched DIR also writes the patched files (for testing in the game without the installer).
"""
import argparse
import os
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

IMAGE_BASE = 0x400000
TEXT_RAW = 0x1000          # .text: virtual 0x401000 -> file offset 0x1000, so file offset = VA - 0x400000
CAVE_VA = 0x83E780         # unused zero tail of .text (file offset 0x43e780)
CAVE_SIZE = 288            # size of the assembled cave.s; checked below
FALLBACK_BRANCH_VA = 0x758E76


def file_offset(va):
    return va - IMAGE_BASE


# (virtual address, expected original bytes, new bytes, why). The cave itself is added separately.
EXE_PATCHES = [
    (0x5205C7, "0f84e8000000", "909090909090",
     "caption draw routine: ignore the 'show captions' debug flag (7,2) so captions are drawn"),
    (0x52064F, "1c", "38",
     "caption layout: fsub [rec+0x1c] -> fsub [rec+0x38], i.e. no extra upward shift for multi-line captions"),
    (0x520695, "1c", "38",
     "caption layout: fld [rec+0x1c] -> fld [rec+0x38], stack the next caption by its full height"),
]


def assemble_cave():
    src = os.path.join(ROOT, "patch", "cave.s")
    with tempfile.TemporaryDirectory() as tmp:
        obj, elf, binf = (os.path.join(tmp, n) for n in ("c.o", "c.elf", "c.bin"))
        try:
            subprocess.check_call(["as", "--32", "-o", obj, src])
            subprocess.check_call(["ld", "-m", "elf_i386", "-Ttext=0x%x" % CAVE_VA, "-o", elf, obj])
            subprocess.check_call(["objcopy", "-O", "binary", "-j", ".text", elf, binf])
        except (OSError, subprocess.CalledProcessError) as e:
            raise SystemExit("cannot assemble patch/cave.s (needs GNU as, ld, objcopy): %s" % e)
        with open(binf, "rb") as f:
            cave = f.read()
    if len(cave) != CAVE_SIZE:
        raise SystemExit("cave is %d bytes, expected %d (update CAVE_SIZE after changing cave.s)" % (len(cave), CAVE_SIZE))
    return cave


def patch_exe(orig):
    out = bytearray(orig)

    def put(va, old, new, what):
        o = file_offset(va)
        if bytes(out[o:o + len(old)]) != old:
            raise SystemExit("bo2.exe differs from the supported build at 0x%x (%s): found %s"
                             % (va, what, bytes(out[o:o + len(old)]).hex()))
        out[o:o + len(new)] = new

    for va, old, new, what in EXE_PATCHES:
        put(va, bytes.fromhex(old), bytes.fromhex(new), what)
    cave = assemble_cave()
    put(CAVE_VA, bytes(len(cave)), cave, "cave space must be empty")
    rel = CAVE_VA - (FALLBACK_BRANCH_VA + 6)
    put(FALLBACK_BRANCH_VA, bytes.fromhex("0f8481000000"), b"\x0f\x84" + struct.pack("<i", rel),
        "reader: failure branch -> cave")
    return bytes(out)


def crc32(b):
    return zlib.crc32(b) & 0xFFFFFFFF


def ranges(orig, new, gap=24):
    """Differing byte ranges; ranges closer than `gap` identical bytes are merged."""
    if len(orig) != len(new):
        raise SystemExit("patched file has a different size; only in-place edits are supported")
    out = []
    i = 0
    n = len(orig)
    while i < n:
        if orig[i] == new[i]:
            i += 1
            continue
        start = i
        last = i
        while i < n and i - last <= gap:
            if orig[i] != new[i]:
                last = i
            i += 1
        out.append((start, last + 1))
        i = last + 1
    return out


def manifest(entries):
    lines = ["BO2PL-PATCH 1"]
    for rel, orig, new in entries:
        lines.append("file %s size %d crc32 %08x" % (rel, len(orig), crc32(orig)))
        for a, b in ranges(orig, new):
            lines.append("range %x %d %08x %s" % (a, b - a, crc32(orig[a:b]), new[a:b].hex()))
    return "\n".join(lines) + "\n"


def find(base, rel):
    """Case-insensitive path lookup (the shipped files are mixed case)."""
    cur = base
    for part in rel.split("/"):
        for e in os.listdir(cur):
            if e.lower() == part.lower():
                cur = os.path.join(cur, e)
                break
        else:
            raise SystemExit("%s not found under %s" % (rel, base))
    return cur


def read(path):
    with open(path, "rb") as f:
        return f.read()


def build(game_dir, fonts_dir=None):
    entries = []          # (relative path in the manifest, original bytes, new bytes)
    exe = read(find(game_dir, "bo2.exe"))
    entries.append(("bo2.exe", exe, patch_exe(exe)))
    if fonts_dir:
        import font_tool
        with tempfile.TemporaryDirectory() as tmp:
            font_tool.inject(find(game_dir, "data"), fonts_dir, tmp)
            for _, name in font_tool.ARCHIVES:
                src = find(game_dir, "data/" + name)
                rel = "data/" + os.path.basename(src)
                entries.append((rel, read(src), read(os.path.join(tmp, os.path.basename(src)))))
    return entries


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("game_dir")
    ap.add_argument("-o", "--output", default=os.path.join(ROOT, "patch", "bo2pl.patch"))
    ap.add_argument("--fonts")
    ap.add_argument("--write-patched", metavar="DIR")
    a = ap.parse_args()

    entries = build(a.game_dir, a.fonts)
    text = manifest(entries)
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with open(a.output, "w", newline="\n") as f:
        f.write(text)
    total = sum(1 for l in text.splitlines() if l.startswith("range"))
    print("wrote %s: %d files, %d ranges, %d bytes" % (a.output, len(entries), total, len(text)))
    if a.write_patched:
        for rel, orig, new in entries:
            dst = os.path.join(a.write_patched, *rel.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(new)
            print("patched file: %s" % dst)


if __name__ == "__main__":
    main()
