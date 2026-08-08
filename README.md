# rarebox-data

The open TCG dataset behind [Rarebox](https://github.com/novaoc/rarebox):
normalized catalogs and market prices for every collection Rarebox tracks —
**Pokémon (EN + JP), Magic, Yu-Gi-Oh!, Lorcana, One Piece (EN + JP), Riftbound,
plus sealed products** — refreshed daily, versioned in git, and served as
static JSON to any builder over raw.githubusercontent / jsDelivr (CORS `*`).

Why this exists: every collection app builds on the same upstream APIs, and
those APIs have holes and outages — pokemontcg.io has **no set at all** for the
Mega-era promos (the Phantasmal Flames tin Mega Charizard ex is invisible to
every app built on it), tcgdex omits Japanese secret rares its own CDN has
scans for, and both 500 routinely. This repo publishes the merged, corrected
picture — including the hand-verified join tables and absence lists that fix
those holes — so nobody has to rediscover them.

## Consuming

Everything is plain JSON at stable paths (see [SCHEMA.md](SCHEMA.md)):

```
https://raw.githubusercontent.com/novaoc/rarebox-data/main/catalog/pokemon/sets.json
https://raw.githubusercontent.com/novaoc/rarebox-data/main/catalog/pokemon/sets/me2.json
https://raw.githubusercontent.com/novaoc/rarebox-data/main/prices/pokemon/latest.json
https://raw.githubusercontent.com/novaoc/rarebox-data/main/maps/en-extra-groups.json
```

**History is git-native.** Every daily refresh is one commit; monthly tags
(`snapshot-YYYY-MM`) give stable point-in-time refs. Any past state is a URL:

```
https://raw.githubusercontent.com/novaoc/rarebox-data/snapshot-2026-08/prices/pokemon/latest.json
```

Per-card **price history** (change-point series, daily since 2024-02) lives in
the sibling repo [rarebox-price-history](https://github.com/novaoc/rarebox-price-history).

## Status

Being built — see [PLAN.md](PLAN.md) for the pipeline design and phases.
The `maps/` directory (the hand-verified upstream join tables) is seeded first
because it is the part nobody else publishes.

## Sources & licensing

Card names, numbers, and set structures are facts. Prices are point-in-time
market data © TCGplayer, obtained via [tcgcsv.com](https://tcgcsv.com)'s daily
archives, republished here for interoperability with attribution — same
posture as tcgcsv itself. Card **images are never stored** in this repo; only
URLs to their existing hosts, for identification purposes. Catalog sources:
pokemontcg.io / pokemon-tcg-data, tcgdex, Scryfall, YGOPRODeck, Lorcast,
optcgapi, riftcodex, TCGplayer (via tcgcsv). If you own any of this data and
want something changed, open an issue.

Code: MIT. Dataset: CC BY 4.0 with the upstream attributions above.
