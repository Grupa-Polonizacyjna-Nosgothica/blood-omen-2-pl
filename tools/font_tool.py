#!/usr/bin/env python3
"""Extracts and re-inserts Blood Omen 2's main font (bitmap + glyph tables).

Usage:
    font_tool.py extract <data_dir> <out_dir>
    font_tool.py inject  <data_dir> <edit_dir> [--out-dir DIR]
    font_tool.py check   <data_dir>            # extract + inject must give byte-identical archives
    font_tool.py preview <edit_dir> <archive> "text" [--table N] [-o out.png]

<data_dir> holds PreCode.big and Code.big. `extract` writes, per archive (precode/, code/):
    atlas.png      the font bitmap, upright, RGBA. EDIT THIS. Keep it 256x256.
    guides.png     the same on a dark background with the glyph boxes and codes (reference only)
    glyphs0.tsv    glyph table of the first font chunk   (code, char, x, y, w, h)  EDIT THIS
    glyphs1.tsv    glyph table of the second font chunk (identical in the shipped game)
    font.json      where everything sits in the archive (do not edit)

`inject` writes the edited atlas and tables back *in place* (the output archives have the
same size), to <data_dir> itself or to --out-dir. Rules: 256x256 PNG, and every glyph table must
keep its 87 rows (change codes/boxes freely, do not add or remove rows; the archive has a
fixed amount of room). A glyph "code" is a character code: ASCII slots are reused for foreign
letters, see docs/fonts.md. The two tables of an archive are separate; edit both (or copy
glyphs0.tsv over glyphs1.tsv) so that they stay consistent.

Format (reverse-engineered), inside the .big archives:
  * the atlas is an uncompressed A8R8G8B8 DDS (128 byte header + 256*256*4 bytes), in a "texture" chunk.
    In Code.big the pixels are stored with the rows in the opposite order; font.json records this
    and the tool flips them, so atlas.png is always upright.
  * a font is a chunk "texfont\\0" holding a table: 24 byte header
        u16 0, u16 0xffff, f32 20.0 (line height), f32 2.0, f32 5.0, f32 8.0, u8 0, u8 0xff, u16 record count
    then <count> records of 20 bytes: u8 character code + 3 bytes 0xFF (padding),
    f32 x, y, w, h (pixels in the 256x256 atlas, y from the top).
"""
import argparse
import json
import os
import re
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ARCHIVES = (("precode", "PreCode.big"), ("code", "Code.big"))
ATLAS = 256
PIXELS = ATLAS * ATLAS * 4
DDS_HEADER = 128
TABLE_HEADER = 24
RECORD = 20
TABLE_SIZE = 0x6F4          # size field of the inner "texfont" chunk of the shipped game
CHUNK_BODY = 16             # tag (8) + size (4) + zero (4)


def read(path):
    with open(path, "rb") as f:
        return bytearray(f.read())


def find_archive(data_dir, name):
    for entry in os.listdir(data_dir):
        if entry.lower() == name.lower():
            return os.path.join(data_dir, entry)
    raise SystemExit("%s not found in %s" % (name, data_dir))


def find_atlas(data):
    """Offset of the DDS header of the font atlas: the only 256x256 uncompressed ARGB DDS."""
    found = []
    for m in re.finditer(rb"DDS \x7c\x00\x00\x00", data):
        o = m.start()
        height, width = struct.unpack_from("<II", data, o + 12)
        bits, rmask, gmask, bmask, amask = struct.unpack_from("<IIIII", data, o + 88)
        if (width, height, bits) == (ATLAS, ATLAS, 32) and (rmask, gmask, bmask, amask) == (0xFF0000, 0xFF00, 0xFF, 0xFF000000):
            found.append(o)
    if len(found) != 1:
        raise SystemExit("expected exactly one 256x256 ARGB atlas, found %d" % len(found))
    return found[0]


def find_tables(data):
    """Offsets of the glyph tables (the body after the 16-byte chunk header of each inner texfont chunk)."""
    out = []
    for m in re.finditer(rb"texfont\x00", data):
        o = m.start()
        if struct.unpack_from("<I", data, o + 8)[0] == TABLE_SIZE:
            out.append(o + CHUNK_BODY)
    return out


def parse_table(data, offset):
    count = struct.unpack_from("<H", data, offset + 22)[0]
    header = bytes(data[offset:offset + TABLE_HEADER])
    rows = []
    for i in range(count):
        code = data[offset + TABLE_HEADER + i * RECORD]
        x, y, w, h = struct.unpack_from("<ffff", data, offset + TABLE_HEADER + i * RECORD + 4)
        rows.append((code, x, y, w, h))
    return header, rows


def fmt(v):
    return ("%g" % v)


def glyph_char(code):
    c = code & 0xFF
    return chr(c) if 33 <= c < 127 else ""


def upright_score(pixels, rows, flip):
    """Fraction of the visible pixels that fall inside glyph boxes (right orientation scores high)."""
    rgb = pixels[:, :, :3].astype(int)
    grey = (rgb.max(axis=2) - rgb.min(axis=2)) < 40
    a = (pixels[:, :, 3] > 40) & grey & (rgb.max(axis=2) > 90)
    if flip:
        a = a[::-1]
    inside = np.zeros_like(a)
    for _, x, y, w, h in rows:
        inside[int(y):int(y + h) + 1, int(x):int(x + w) + 1] = True
    total = a.sum()
    return float((a & inside).sum()) / total if total else 0.0


def load_pixels(data, atlas):
    raw = np.frombuffer(bytes(data[atlas + DDS_HEADER:atlas + DDS_HEADER + PIXELS]), dtype=np.uint8)
    bgra = raw.reshape(ATLAS, ATLAS, 4)
    return bgra[:, :, [2, 1, 0, 3]]          # RGBA


def store_pixels(data, atlas, rgba, flip):
    arr = np.ascontiguousarray(rgba[::-1] if flip else rgba)
    bgra = arr[:, :, [2, 1, 0, 3]]
    data[atlas + DDS_HEADER:atlas + DDS_HEADER + PIXELS] = bgra.tobytes()


def extract(data_dir, out_dir):
    for key, name in ARCHIVES:
        data = read(find_archive(data_dir, name))
        atlas = find_atlas(data)
        tables = find_tables(data)
        if not tables:
            raise SystemExit("no glyph tables found in %s" % name)
        rgba = load_pixels(data, atlas)
        _, rows = parse_table(data, tables[0])
        flip = upright_score(rgba, rows, True) > upright_score(rgba, rows, False)
        upright = rgba[::-1] if flip else rgba
        d = os.path.join(out_dir, key)
        os.makedirs(d, exist_ok=True)
        Image.fromarray(np.ascontiguousarray(upright), "RGBA").save(os.path.join(d, "atlas.png"))
        for n, t in enumerate(tables):
            _, trows = parse_table(data, t)
            with open(os.path.join(d, "glyphs%d.tsv" % n), "w", newline="\n") as f:
                f.write("code\tchar\tx\ty\tw\th\n")
                for code, x, y, w, h in trows:
                    f.write("%d\t%s\t%s\t%s\t%s\t%s\n" % (code, glyph_char(code), fmt(x), fmt(y), fmt(w), fmt(h)))
        meta = {"archive": name, "atlas_offset": atlas, "table_offsets": tables, "flipped": bool(flip),
                "rows": [len(parse_table(data, t)[1]) for t in tables]}
        with open(os.path.join(d, "font.json"), "w") as f:
            json.dump(meta, f, indent=2)
        guides(upright, parse_table(data, tables[0])[1], os.path.join(d, "guides.png"))
        print("%s: atlas at 0x%x (%s), %d tables, %d glyphs each" %
              (name, atlas, "stored upside down" if flip else "upright", len(tables), len(rows)))


def guides(upright, rows, path):
    img = Image.fromarray(np.ascontiguousarray(upright), "RGBA")
    bg = Image.new("RGBA", img.size, (40, 40, 60, 255))
    bg.alpha_composite(img)
    big = bg.resize((ATLAS * 4, ATLAS * 4), Image.NEAREST)
    dr = ImageDraw.Draw(big)
    for code, x, y, w, h in rows:
        dr.rectangle([x * 4, y * 4, (x + w) * 4, (y + h) * 4], outline=(255, 0, 0, 255))
        c = code & 0xFF
        dr.text((x * 4 + 2, y * 4 + 2), chr(c) if 33 <= c < 127 else "%02x" % c, fill=(255, 255, 0, 255))
    big.save(path)


def read_tsv(path, expected):
    rows = []
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            line = line.rstrip("\r\n")
            if not line:
                continue
            p = line.split("\t")
            rows.append((int(p[0]), float(p[2]), float(p[3]), float(p[4]), float(p[5])))
    if len(rows) != expected:
        raise SystemExit("%s has %d rows, must keep exactly %d (the archive has no room for more)"
                         % (path, len(rows), expected))
    return rows


def inject(data_dir, edit_dir, out_dir=None):
    for key, name in ARCHIVES:
        d = os.path.join(edit_dir, key)
        src = find_archive(data_dir, name)
        data = read(src)
        with open(os.path.join(d, "font.json")) as f:
            meta = json.load(f)
        if find_atlas(data) != meta["atlas_offset"] or find_tables(data) != meta["table_offsets"]:
            raise SystemExit("%s does not match the extracted layout; extract again" % name)
        img = Image.open(os.path.join(d, "atlas.png")).convert("RGBA")
        if img.size != (ATLAS, ATLAS):
            raise SystemExit("atlas.png must be %dx%d, is %dx%d" % (ATLAS, ATLAS, img.size[0], img.size[1]))
        store_pixels(data, meta["atlas_offset"], np.array(img), meta["flipped"])
        for n, t in enumerate(meta["table_offsets"]):
            rows = read_tsv(os.path.join(d, "glyphs%d.tsv" % n), meta["rows"][n])
            for i, (code, x, y, w, h) in enumerate(rows):
                at = t + TABLE_HEADER + i * RECORD
                data[at] = code & 0xFF            # the three padding bytes stay as they are
                struct.pack_into("<ffff", data, at + 4, x, y, w, h)
        dst = os.path.join(out_dir, os.path.basename(src)) if out_dir else src
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(data)
        print("wrote %s" % dst)


def check(data_dir):
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        extract(data_dir, os.path.join(tmp, "e"))
        inject(data_dir, os.path.join(tmp, "e"), os.path.join(tmp, "o"))
        ok = True
        for _, name in ARCHIVES:
            same = read(find_archive(data_dir, name)) == read(os.path.join(tmp, "o", os.path.basename(find_archive(data_dir, name))))
            print("%s round trip: %s" % (name, "identical" if same else "DIFFERENT"))
            ok &= same
    if not ok:
        raise SystemExit(1)


def preview(edit_dir, archive, text, table, out):
    d = os.path.join(edit_dir, archive)
    img = Image.open(os.path.join(d, "atlas.png")).convert("RGBA")
    rows = {}
    with open(os.path.join(d, "glyphs%d.tsv" % table), encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\r\n").split("\t")
            if len(p) >= 6:
                rows[int(p[0])] = tuple(float(v) for v in p[2:6])
    height = 24
    surface = Image.new("RGBA", (max(60, int(len(text) * 24)), height * 2), (30, 30, 40, 255))
    x = 8
    for ch in text:
        if ch == " ":
            x += 8
            continue
        r = rows.get(ord(ch))
        if not r:
            x += 8
            continue
        gx, gy, gw, gh = (int(round(v)) for v in r)
        glyph = img.crop((gx, gy, gx + gw, gy + gh))
        surface.alpha_composite(glyph, (x, 8))
        x += gw + 1
    surface.crop((0, 0, x + 8, height * 2)).resize(((x + 8) * 3, height * 6), Image.NEAREST).save(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract"); p.add_argument("data_dir"); p.add_argument("out_dir")
    p = sub.add_parser("inject"); p.add_argument("data_dir"); p.add_argument("edit_dir"); p.add_argument("--out-dir")
    p = sub.add_parser("check"); p.add_argument("data_dir")
    p = sub.add_parser("preview"); p.add_argument("edit_dir"); p.add_argument("archive"); p.add_argument("text")
    p.add_argument("--table", type=int, default=0); p.add_argument("-o", "--output", default="preview.png")
    a = ap.parse_args()
    if a.cmd == "extract":
        extract(a.data_dir, a.out_dir)
    elif a.cmd == "inject":
        inject(a.data_dir, a.edit_dir, a.out_dir)
    elif a.cmd == "check":
        check(a.data_dir)
    else:
        preview(a.edit_dir, a.archive, a.text, a.table, a.output)


if __name__ == "__main__":
    main()
