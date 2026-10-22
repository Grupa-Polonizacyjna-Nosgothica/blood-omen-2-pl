#!/usr/bin/env python3
"""Unpacks the Ogg Vorbis streams from Blood Omen 2's data/pc.rkv.

Usage:
    rkv_extract.py <pc.rkv> <out_dir> [--list] [--prefix vo/]

Writes <out_dir>/<entry name>.ogg (entry names look like "vo/SL02_UMAH_01" or
"streams/wav/STR_canyonswind") and <out_dir>/index.csv with one row per stream:
name, ogg file, phrase key, byte offset in pc.rkv, size, duration in seconds.

The phrase key is the lower-cased last path component of a "vo/" entry. It is exactly the
name the engine hands to the speech code (see docs/captions.md), i.e. the first token of a
record in a .cnv subtitle file.

Format of pc.rkv (little-endian), reverse-engineered:
    u32 version (1)
    u32 index size
    u32 language count (1)
      u32 name length, name ("english")
      u32 section count (1)
        u32 name length, name ("strstrem")
        u32 entry count, u32 0
        entries: u32 name length, name, u32 1, u32 sector, u32 size, u32 0
    ...padding...
    data area at DATA_START; an entry's bytes are at DATA_START + sector * 2048.
"""
import argparse
import csv
import os
import struct
import sys

SECTOR = 2048


def parse_index(f):
    f.seek(0)
    head = f.read(12)
    version, index_size, languages = struct.unpack("<III", head)
    if version != 1 or languages != 1:
        raise SystemExit("unexpected pc.rkv header: version=%d languages=%d" % (version, languages))
    f.seek(12)
    data = f.read(index_size + 64)
    o = 0

    def u32():
        nonlocal o
        v = struct.unpack_from("<I", data, o)[0]
        o += 4
        return v

    def string():
        nonlocal o
        n = u32()
        s = data[o:o + n].decode("latin-1")
        o += n
        return s

    string()                      # language name
    sections = u32()
    entries = []
    for _ in range(sections):
        section = string()
        count = u32()
        u32()                     # always 0
        for _ in range(count):
            name = string()
            u32()                 # always 1
            sector = u32()
            size = u32()
            u32()                 # always 0
            entries.append((section, name, sector, size))
    return index_size, entries


def find_data_start(f, entries, index_size):
    """The data area follows the index; check the guess against the first entry's Ogg signature."""
    first = entries[0]
    for start in (index_size + 8 + 0x800, ((index_size + 0x7FF) & ~0x7FF), ((index_size + 0x7FF) & ~0x7FF) + 0x800):
        f.seek(start + first[2] * SECTOR)
        if f.read(4) == b"OggS":
            return start
    raise SystemExit("could not locate the data area (no OggS at the first entry)")


def ogg_duration(blob):
    """Duration in seconds of a Vorbis-in-Ogg stream (sample rate from the identification header,
    length from the granule position of the last page). Returns 0.0 if it cannot be read."""
    try:
        i = blob.index(b"\x01vorbis")
        rate = struct.unpack_from("<I", blob, i + 12)[0]
        j = blob.rindex(b"OggS")
        granule = struct.unpack_from("<q", blob, j + 6)[0]
        return granule / rate if rate and granule > 0 else 0.0
    except (ValueError, struct.error):
        return 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rkv")
    ap.add_argument("out_dir")
    ap.add_argument("--list", action="store_true", help="only print the entries, write nothing")
    ap.add_argument("--prefix", default="", help="only entries whose name starts with this (e.g. vo/)")
    args = ap.parse_args()

    with open(args.rkv, "rb") as f:
        index_size, entries = parse_index(f)
        start = find_data_start(f, entries, index_size)
        entries = [e for e in entries if e[1].startswith(args.prefix)]
        print("%d entries, data area at 0x%x" % (len(entries), start), file=sys.stderr)
        if args.list:
            for section, name, sector, size in entries:
                print("%s\t%d\t%d" % (name, start + sector * SECTOR, size))
            return

        os.makedirs(args.out_dir, exist_ok=True)
        rows = []
        for section, name, sector, size in entries:
            offset = start + sector * SECTOR
            f.seek(offset)
            blob = f.read(size)
            if blob[:4] != b"OggS":
                print("warning: %s does not start with an Ogg page, skipped" % name, file=sys.stderr)
                continue
            if len(blob) != size:
                # The last stream of the shipped pc.rkv runs past the end of the file.
                print("warning: %s is truncated in pc.rkv (%d of %d bytes), written as is"
                      % (name, len(blob), size), file=sys.stderr)
            rel = name + ".ogg"
            path = os.path.join(args.out_dir, *rel.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as out:
                out.write(blob)
            key = name.split("/")[-1].lower() if name.startswith("vo/") else ""
            rows.append((name, rel, key, offset, size, "%.2f" % ogg_duration(blob)))

    with open(os.path.join(args.out_dir, "index.csv"), "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["name", "file", "phrase_key", "offset", "size", "seconds"])
        w.writerows(rows)
    print("wrote %d files to %s" % (len(rows), args.out_dir), file=sys.stderr)


if __name__ == "__main__":
    main()
