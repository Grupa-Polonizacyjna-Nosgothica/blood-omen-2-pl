#!/usr/bin/env python3
"""Builds an index of the game's voice lines: which phrase key lives in which level archive.

Usage:
    dialogue_index.py <data_dir> <ogg_dir> <out.csv> [--skeleton DIR]

<data_dir> holds the *.big archives, <ogg_dir> is the output of rkv_extract.py (needs index.csv).

How the game finds subtitles (docs/captions.md): when a level or UI screen loads, the engine
asks for "<root>/resources/levels/<area>/<name>.cnv" where <name> is the archive's name without
".big" (sl01.big -> sl01.cnv). The patched game reads data/texts/<name>.cnv for each. The records
of those files go into one global phrase table, keyed by the phrase key (lower-case sound name,
e.g. sl02_umah_01), so a record only has to be present in *some* .cnv that is loaded before the
line is spoken. The safest place is the .cnv of every archive that references the line, which is
what this index lists.

The archives reference voice lines as "vo/SND/<name>" symbols; the same name in lower case is
the phrase key. Output columns:
    phrase_key, speaker, seconds, ogg (relative to <ogg_dir>), cnv_files (';'-separated)

--skeleton DIR writes one <name>.cnv per archive with a placeholder record for every line it
references (the text is "TODO <key>"), a starting point for translators.
"""
import argparse
import csv
import mmap
import os
import re
import sys

PATTERN = re.compile(rb"vo/SND/([A-Za-z0-9_]+)\x00")


def speaker(key):
    parts = key.split("_")
    return parts[-2] if len(parts) >= 3 else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data_dir")
    ap.add_argument("ogg_dir")
    ap.add_argument("out_csv")
    ap.add_argument("--skeleton", metavar="DIR")
    args = ap.parse_args()

    ogg = {}
    with open(os.path.join(args.ogg_dir, "index.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["phrase_key"]:
                ogg[row["phrase_key"]] = (row["file"], row["seconds"])

    used = {}      # phrase key -> set of cnv names
    per_cnv = {}   # cnv name -> ordered list of keys
    for name in sorted(os.listdir(args.data_dir)):
        if not name.lower().endswith(".big"):
            continue
        cnv = name[:-4]
        keys = []
        with open(os.path.join(args.data_dir, name), "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                for match in PATTERN.finditer(m):
                    key = match.group(1).decode("ascii").lower()
                    if key not in keys:
                        keys.append(key)
        if keys:
            per_cnv[cnv] = keys
            for key in keys:
                used.setdefault(key, set()).add(cnv)

    keys = sorted(set(ogg) | set(used))
    with open(args.out_csv, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["phrase_key", "speaker", "seconds", "ogg", "cnv_files"])
        for key in keys:
            f, secs = ogg.get(key, ("", ""))
            w.writerow([key, speaker(key), secs, f, ";".join(sorted(used.get(key, ())))])
    unused = [k for k in ogg if k not in used]
    missing = [k for k in used if k not in ogg]
    print("%d phrase keys; %d voice streams not referenced by any archive; %d references without a stream"
          % (len(keys), len(unused), len(missing)), file=sys.stderr)

    if args.skeleton:
        os.makedirs(args.skeleton, exist_ok=True)
        for cnv, ks in per_cnv.items():
            with open(os.path.join(args.skeleton, cnv + ".cnv"), "w", newline="", encoding="ascii") as out:
                for key in ks:
                    out.write('%s "%s"\r\nTODO %s\r\n\r\n' % (key, speaker(key), key))
        print("wrote %d skeleton files to %s" % (len(per_cnv), args.skeleton), file=sys.stderr)


if __name__ == "__main__":
    main()
