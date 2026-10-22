# Subtitle files

`<name>.cnv` files, one per level archive (`sl01.big` -> `sl01.cnv`). The installer copies everything in
`PL/` to `<game>/data/texts/`; the patched game reads `data/texts/<name>.cnv` whenever it loads that
level. Format and details: `docs/captions.md`.

- `EN/`: English reference text (so far only a test file for the Slums opening).
- `PL/`: the Polish translation. Empty for now.

To find out which phrase keys belong in which file, generate the index (see `docs/dialogue.md`).
