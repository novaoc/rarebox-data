# rarebox-data

The open TCG dataset behind [Rarebox](https://github.com/novaoc/rarebox):
normalized catalogs and market prices for every collection Rarebox tracks —
**Pokémon (EN + JP), Magic, Yu-Gi-Oh!, Lorcana, One Piece (EN + JP), Riftbound,
plus sealed products** — refreshed daily, versioned in git, and served as
static JSON to any builder over raw.githubusercontent / jsDelivr (CORS `*`).

**Why this exists.** Public data sources are shutting down or decaying, and
the ones still up have holes and outages — pokemontcg.io has **no set at all**
for the Mega-era promos (the Phantasmal Flames tin Mega Charizard ex is
invisible to every app built on it), tcgdex omits Japanese secret rares its
own CDN has scans for, and both 500 routinely. This repo is a preservation
effort: capture the public record of the entire TCG market — including the
special cases, obscure releases, and rare promos the big catalogs skip — and
keep it permanently free and publicly available, with the hand-verified join
tables and absence lists that fix the holes, so nobody has to rediscover them
and nothing disappears when an upstream does. At-risk hobby APIs additionally
get their raw responses preserved under `raw/`.

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

**Live.** Daily refresh at 07:30 UTC ([refresh.yml](.github/workflows/refresh.yml)),
validators gating every commit, monthly `snapshot-YYYY-MM` tags. Seeded
2026-08-08 with ~195,000 cards across 7 games — including 919 TCGplayer-only
cards no primary catalog has (`x-` sets) and 6,450 Japanese secret rares the
tcgdex API omits. Per-card price history reaches back to **2024-02-07** via
[rarebox-price-history](https://github.com/novaoc/rarebox-price-history)
(see [prices/history.json](prices/history.json)). Roadmap: [PLAN.md](PLAN.md);
triage protocol for humans and agents: [agents/TRIAGE.md](agents/TRIAGE.md).

## Sources & licensing

Card names, collector numbers, set structures, and market prices are **facts —
public information that belongs to no one**. This dataset compiles those facts
and dedicates the compilation to the public domain (**CC0 1.0**): use it for
anything, no permission needed, forever. Card **images are never stored** in
this repo; only URLs to their existing hosts, for identification purposes.

Provenance (kept for data lineage, not permission): pokemon-tcg-data /
pokemontcg.io, tcgdex, Scryfall, YGOPRODeck, Lorcast, optcgapi, riftcodex,
and TCGplayer market data via [tcgcsv.com](https://tcgcsv.com)'s daily
archives. Code: MIT.
