# Quirks — lessons that cost real debugging time

Each entry is a rule the pipelines and validators must respect. Dates are
when the behavior was live-verified.

## pokemontcg.io / pokemon-tcg-data (EN Pokémon)

- **Whole sets can be missing.** No set exists for TCGplayer's "ME: Mega
  Evolution Promo" group (2026-08-08: `/v2/sets/mep` → 404; pokemon-tcg-data
  has no such set) — likewise McDonald's 2023+, Trick or Trade bundles, Prize
  Pack Series, and the rest of `en-extra-groups.json`. "Unmapped by
  abbreviation" is NOT proof of absence: SM Promos is unmapped (tcgcsv `SMP`
  vs ptcgoCode `PR-SM`) yet exists upstream as `smp`. Absence must be
  verified by name search against the set list, then allowlisted.
- **ptcgoCode joins can be FALSE-positive.** TCG Classic's tcgcsv abbreviation
  `CL` equals Call of Legends' ptcgoCode → joins to `col1` and silently
  vanishes. Known cases are pinned in the maps; new joins with implausible
  release-date gaps deserve suspicion.
- **New sets ship URL-only prices.** Since me2pt5 (2026-01), cards carry a
  `tcgplayer.url` but no `prices` — price coverage must come from tcgcsv.
- **The API 500s routinely** (sometimes hours). The canonical data repo
  `PokemonTCG/pokemon-tcg-data` on GitHub is the reliable fallback and is
  current.
- **Set card-count sorting is unstable across pages** — page by `orderBy=id`,
  never `number`, or >250-card sets silently drop cards.

## tcgdex (JP Pokémon)

- **The API stops at each set's official count.** SV8 lists 106 cards;
  Pikachu ex 136/106 (`SV8-136`) is a 404 — every JP secret rare is invisible
  to the API. But TCGplayer's JP catalog knows the full run, and…
- **…the tcgdex CDN HAS the secret-rare scans its API omits.**
  `assets.tcgdex.net/ja/SV/SV8/136/low.webp` serves a real scan.
- **CDN paths require 3-digit zero-padding**: `/SV8/006` → 200, `/SV8/6` →
  404. Every scan URL must pad. (The API's `localId` is unpadded — trap.)
- **The Mega era has no scans at all** (`scans: false` in set meta) — image
  URLs must fall back to TCGplayer product photos
  (`tcgplayer-cdn.tcgplayer.com/product/{pid}_200w.jpg`).
- **`_lang: 'ja'` must survive every normalization** — JP set ids collide
  with EN ids case-insensitively (EN `sv3` ≠ JP `SV3`), and One Piece JP set
  ids overlap the EN catalog outright (`PRB-01`, `EB-04`).

## TCGplayer / tcgcsv (prices, all games)

- **$0 is a real market price.** Only absent/None is unknown. Collapsing with
  `||` instead of `??` has caused real bugs twice.
- **Ambiguous names must never take the first search result.** "Collector
  Booster Box" matches every Magic set's collector box; the first result was
  a $1,800 Final Fantasy box for a $380 Spider-Man product (2026-08-08).
  Match by token overlap against name+set, and qualify sealed queries with
  the set name.
- **Variant printings share the base card's Number** ("Erika's Oddish
  (Poke Ball)") — skip `(...)`-suffixed products or keys collide.
- **Promo product names embed the number** ("Mega Charizard X ex - 029") —
  strip ` - NNN` suffixes for display names.
- Etiquette: ≤10 req/s, custom UA, check `last-updated.txt` before pulling.

## Number normalization (shared, MUST round-trip everywhere)

`"001/217"` → `1` · `"TG07"` → `tg7` · `"SWSH001"` → `swsh1` · `"0"` → `0`
(lowercase; strip leading zeros; letter-prefixed numbers keep the prefix and
strip the zeros after it). One implementation per language, mirrored tests.
