# Voice lines and phrase keys

`tools/rkv_extract.py` unpacks the game's audio so you can listen to a line and know its phrase key.

    python3 tools/rkv_extract.py <game>/data/pc.rkv GameData/ogg
    python3 tools/dialogue_index.py <game>/data GameData/ogg GameData/ogg/dialogue_index.csv [--skeleton DIR]

* `pc.rkv` holds 2,824 Ogg Vorbis streams: voice lines `vo/<LEVEL>_<SPEAKER>_<NN>` (e.g. `vo/SL02_UMAH_01`), music and
  ambience (`streams/wav/...`, `music/wav/...`). Format notes are in the header of `rkv_extract.py`. The last stream
  (`vo/WHAM_VORA_02`) is cut short in the shipped file (59,392 of 61,009 bytes).
* The **phrase key** of a voice line is its lower-case name, `sl02_umah_01`; it is the first token of a record in a `.cnv`
  subtitle file (`docs/captions.md`). `GameData/ogg/index.csv` lists name, file, phrase key, offset, size and duration;
  `dialogue_index.csv` adds the speaker and the **archives that reference the line** (`cnv_files`, i.e. the `.cnv` files
  to put the record in; an empty list means no archive mentions the line, probably cut content).
* A record only has to be in one `.cnv` that is loaded before the line is spoken, but the archive that references the
  line is the safe choice. Example: the Slums opening (`sl02_umah_01` ...) is referenced by `sl01.big`, so its record
  belongs in `sl01.cnv` (it also works from `sl02.cnv`, which loads earlier in the same level).
* `--skeleton DIR` writes one `<archive>.cnv` per archive with a placeholder record for every line it references
  (`TODO <key>` as the text), a starting point for translators.

Numbers from this game build: 2,592 phrase keys; 1,427 are referenced by an archive (one or more), 1,165 voice streams are not
referenced by any archive; 162 archives reference at least one line.
