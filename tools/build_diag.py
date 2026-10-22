#!/usr/bin/env python3
"""Builds a diagnostic bo2.exe: the shipped patch's caption gate and loose-file fallback plus the logging
hooks of patch/diag/cave_diag.s (see the header of that file for the log format).

    build_diag.py <original bo2.exe> <output exe>

Needs GNU as/ld/objcopy/nm. Not part of the installer; for reverse engineering only. The output logs to
C:\\bo2_diag.log (drive_c/bo2_diag.log in the Wine prefix).
"""
import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CAVE_VA = 0x83E780
# (virtual address, original bytes, symbol of the cave routine that replaces them)
HOOKS = [
    (0x4B6420, "64a100000000", "hook0"),            # SpeechHandler::PhraseStart entry
    (0x4B6756, "8b4d00833900", "hookP"),            # before the caption section of PhraseStart
    (0x5205B0, "83ec145355", "hookD"),              # caption draw entry
    (0x520470, "6aff685b1e8100", "hookA"),          # AddCaption entry
    (0x75AAA6, "8b0da03ca800", "hookL"),            # PhraseTable::Load, after the path is built
]


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, dst = sys.argv[1:]
    with open(src, "rb") as f:
        exe = bytearray(f.read())

    def put(va, old, new):
        o = va - 0x400000
        if bytes(exe[o:o + len(old)]) != old:
            raise SystemExit("unexpected bytes at 0x%x: %s" % (va, bytes(exe[o:o + len(old)]).hex()))
        exe[o:o + len(new)] = new

    with tempfile.TemporaryDirectory() as tmp:
        obj, elf, binf = (os.path.join(tmp, n) for n in ("d.o", "d.elf", "d.bin"))
        asm = os.path.join(ROOT, "patch", "diag", "cave_diag.s")
        subprocess.check_call(["as", "--32", "-o", obj, asm])
        subprocess.check_call(["ld", "-m", "elf_i386", "-Ttext=0x%x" % CAVE_VA, "-o", elf, obj])
        subprocess.check_call(["objcopy", "-O", "binary", "-j", ".text", elf, binf])
        syms = {}
        for line in subprocess.check_output(["nm", elf], text=True).splitlines():
            parts = line.split()
            if len(parts) == 3:
                syms[parts[2]] = int(parts[0], 16)
        with open(binf, "rb") as f:
            cave = f.read()
    if CAVE_VA + len(cave) > 0x83F000:
        raise SystemExit("cave does not fit in the unused tail of .text")

    put(0x5205C7, bytes.fromhex("0f84e8000000"), b"\x90" * 6)                      # show captions gate
    put(CAVE_VA, bytes(len(cave)), cave)
    for va, old, sym in HOOKS:
        put(va, bytes.fromhex(old), b"\xe9" + struct.pack("<i", syms[sym] - (va + 5)) + b"\x90" * (len(old) // 2 - 5))
    put(0x758E76, bytes.fromhex("0f8481000000"), b"\x0f\x84" + struct.pack("<i", syms["hookC"] - (0x758E76 + 6)))
    with open(dst, "wb") as f:
        f.write(exe)
    print("wrote %s (cave %d bytes at 0x%x)" % (dst, len(cave), CAVE_VA))


if __name__ == "__main__":
    main()
