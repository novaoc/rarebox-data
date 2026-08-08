# Schema

All files are UTF-8 JSON with sorted keys and stable array ordering — the
stability is load-bearing (git delta-compression is the history engine).

## Card (normalized, shared across games)

```json
{
  "id": "me2-13",
  "name": "Mega Charizard X ex",
  "number": "13",
  "set": { "id": "me2", "name": "Phantasmal Flames" },
  "rarity": "Double Rare",
  "supertype": "Pokémon",
  "image": "https://images.pokemontcg.io/me2/13.png",
  "game": "pokemon",
  "_lang": null
}
```

- `image` is a URL to the upstream host — never a stored binary.
- `_lang`: `"ja"` for Japanese printings, otherwise null/absent. Japanese
  cards keep their language-qualified identity everywhere (EN sv3 ≠ JP SV3).
- Synthetic sets (cards no primary catalog has, sourced from TCGplayer) use
  `x-` prefixed set ids (`x-mep`) — guaranteed never to collide with a real
  upstream id.

## catalog/{game}/sets.json

Array of `{ id, name, series, total, printedTotal, releaseDate, logo }`,
newest first. `total` counts secret rares; `printedTotal` is the official
count printed on cards ("136/106" ⇒ number 136, printedTotal 106).

## prices/{game}/latest.json

```json
{ "stamp": "2026-08-07T20:05:32+0000", "source": "tcgcsv", "prices": { "me2-13": 4.79 } }
```

- Key: `{setId}-{normalizedNumber}` (lowercase, no leading zeros:
  `"001/217"` → `1`, `"TG07"` → `tg7`, `"SWSH001"` → `swsh1`).
- **$0 is a real market price.** Unknown prices are ABSENT, never 0 or null.
- One price per card: the best variant by the priority
  holofoil → 1st-ed holo → unlimited holo → reverse holo → normal → 1st-ed
  normal, market else mid.

## maps/

- `groups-pokemon.json` — `{ tcgcsvGroupId: pokemontcgSetId | null }`. `null`
  means verified: no upstream counterpart exists.
- `en-extra-groups.json` — the absence allowlist: groups whose cards exist on
  TCGplayer but in NO primary catalog, each entry carrying its verification
  evidence and date. These become the `x-` synthetic sets.
- `jp-set-names.json` — tcgdex JP set id → English community name.
- `quirks.md` — prose rules that took real debugging to learn (CDN padding,
  false ptcgo joins, secret-rare API gaps). Read it before touching pipelines.

## History access

- Latest: `https://raw.githubusercontent.com/novaoc/rarebox-data/main/<path>`
- Point-in-time: replace `main` with a monthly tag `snapshot-YYYY-MM` (or any
  commit SHA).
- Per-card price time series:
  [rarebox-price-history](https://github.com/novaoc/rarebox-price-history)
  `data/{game}/{setKey}.json` — change-point `[epochDay, usd]` arrays.
