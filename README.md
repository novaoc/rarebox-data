# rarebox-data

Public, CC0 TCG dataset: normalized card catalogs and market prices for
**Pokémon (EN + JP), Magic, Yu-Gi-Oh!, Lorcana, One Piece (EN + JP), and
Riftbound** — ~195,000 cards, refreshed daily, versioned in git, served as
plain JSON over raw.githubusercontent / jsDelivr (CORS `*`, no keys, no SDK).

**Full documentation — architecture and how to use it in any application:**
**[docs.rarebox.io/data/rarebox-data](https://docs.rarebox.io/data/rarebox-data)**

## What's in it

```
catalog/{game}/sets.json           set lists (id, name, totals, releaseDate, logo URL)
catalog/{game}/sets/{setId}.json   per-set card lists, one shared shape across all games
prices/{game}/latest.json          {stamp, prices: {"me2-13": 4.79}} — $0 valid, unknown absent
prices/history.json                pointer to per-card daily series back to 2024-02
maps/                              hand-verified upstream join tables + absence allowlists
raw/                               full upstream responses for at-risk hobby APIs
STATUS.json                        per-pipeline counts and last-success stamps
```

Games: `pokemon` · `pokemon-ja` · `mtg` · `yugioh` · `lorcana` · `one-piece` · `riftbound`.

Coverage goes beyond the primary catalogs: `x-` prefixed sets carry
TCGplayer-only cards pokemontcg.io doesn't have (ME Black Star Promos,
McDonald's 2023/24, Prize Pack Series, …), and the Japanese Pokémon catalog
includes the 6,450 secret rares the tcgdex API omits.

## Quick start

```js
// a set's cards — same shape for every game
const cards = await fetch(
  'https://raw.githubusercontent.com/novaoc/rarebox-data/main/catalog/pokemon-ja/sets/SV8.json'
).then(r => r.json())
// { id: 'SV8-136', name: 'Pikachu ex', number: '136',
//   set: {id, name}, rarity, image, game: 'pokemon', _lang: 'ja' }

// latest prices — keys are `${setId}-${normalizedNumber}`
const { prices } = await fetch(
  'https://raw.githubusercontent.com/novaoc/rarebox-data/main/prices/pokemon/latest.json'
).then(r => r.json())
```

## History

- **Point-in-time snapshots**: every day is one commit; monthly tags give
  stable refs — swap `main` for `snapshot-2026-08` in any URL.
- **Per-card price series** (change-point `[epochDay, usd]` arrays, daily
  since **2024-02-07**): sibling repo
  [rarebox-price-history](https://github.com/novaoc/rarebox-price-history),
  indexed by [prices/history.json](prices/history.json).

## How it's maintained

A daily pipeline (07:30 UTC, [refresh.yml](.github/workflows/refresh.yml))
fetches each source at ≤10 req/s, normalizes to the shared shape, and commits
only if validators pass: catalogs may not shrink >2%, prices may not
mass-move >5×, `$0` stays valid, and absence claims carry dated evidence.
One flaky upstream never blocks the rest — a failed pipeline keeps
yesterday's data. Mapping drift is triaged per
[agents/TRIAGE.md](agents/TRIAGE.md); roadmap in [PLAN.md](PLAN.md).

## Licensing

Dataset: **CC0 1.0** — public-domain dedication, use it for anything.
Code: MIT. Card **images are never stored**; image URLs point to their
original hosts. Provenance per file: pokemon-tcg-data / pokemontcg.io,
tcgdex, Scryfall, YGOPRODeck, Lorcast, optcgapi, riftcodex, and TCGplayer
market data via [tcgcsv.com](https://tcgcsv.com).
