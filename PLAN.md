# Build plan — rarebox-data

A public, GitHub-hosted TCG database: daily raw+normalized snapshots of every
collection Rarebox can track, with at least 6 months of retrievable history,
maintained by a deterministic pipeline with an LLM-agent loop for the parts
that need judgment (mapping drift, absence verification, anomaly triage).

## 1. Principles

- **Static JSON over a git repo is the database.** No server, no API keys for
  consumers, CORS-free via raw.githubusercontent/jsDelivr. Matches Rarebox's
  local-first ethos and costs nothing to run.
- **Git is the history engine.** One commit per daily refresh; the repo's own
  log IS the snapshot archive. Monthly tags give stable point-in-time URLs.
  This beats hand-rolled dated files: identical days delta-compress to
  near-zero, and consumers time-travel with a ref in the URL.
- **Deterministic pipeline, judgmental agents.** Fetch/normalize/validate is
  plain Python in CI — reproducible and auditable. LLM agents only *propose*
  changes (mapping updates, allowlist additions) as PRs with cited evidence;
  validators gate, a human (or auto-merge on green checks) lands them. An
  agent never writes directly to `main`.
- **Facts in, no binaries.** Names/numbers/sets/prices/URLs only. Card images
  stay on their hosts. $0 is a valid price; unknown stays absent — never 0.
- **Every hard-won lesson becomes data or a validator.** The join maps and
  absence allowlists that fixed real Rarebox bugs live here as first-class
  published artifacts (`maps/`), each with a validator that fails the build
  when reality drifts.

## 2. What already exists (don't rebuild it)

| Asset | Where | Role here |
|---|---|---|
| Daily price ingest + per-card history since 2024-02 | `rarebox-price-history` (tcgcsv archives) | Stays the history store for *prices*; this repo links to it and mirrors only `latest` |
| tcgcsv groupId → set-id join maps | `rarebox-price-history/maps/groups.json` | Superseded here: `maps/` becomes the canonical home, price-history consumes it |
| EN price fallback builder | `rarebox/scripts/build_en_prices.py` | Port → `pipelines/pokemon_en.py` |
| EN extras (cards pokemontcg.io lacks: ME promos etc.) | `rarebox/scripts/build_en_extras.py` + `EXTRA_GROUPS` | Port; allowlist published as `maps/en-extra-groups.json` |
| JP index/prices (EN names, product ids, scans flags) | `rarebox/scripts/build_jp_*.py` | Port; `JP_EN_NAMES`, scans/padding quirks published under `maps/` |
| One Piece EN/JP, Yu-Gi-Oh!, Riftbound, sealed builders | `rarebox/scripts/build_*.py` | Port per game |
| MTG / Lorcana | live Scryfall / Lorcast in-app | New catalog snapshotters (bulk endpoints exist for both) |

Migration rule: each Rarebox builder moves here, and Rarebox's
`refresh-data.yml` shrinks to "download published artifacts" (or the app
fetches them directly at runtime). One pipeline, two consumers.

## 3. Repo layout

```
catalog/{game}/sets.json                 # all sets: id, name, series, total, releaseDate, logo URL
catalog/{game}/sets/{setId}.json         # per-set card list, normalized shape (below)
prices/{game}/latest.json                # {stamp, prices: {cardKey: usd}} — $0 valid
maps/                                    # the crown jewels — hand-verified join tables
  groups-pokemon.json                    #   tcgcsv groupId → pokemontcg set id
  en-extra-groups.json                   #   groups VERIFIED ABSENT upstream (+ evidence notes)
  jp-set-names.json                      #   tcgdex JP set id → EN community name
  quirks.md                              #   CDN padding rules, false-join cases (CL→col1), etc.
raw/{source}/…                           # phase 3: trimmed upstream responses for reproducibility
pipelines/                               # python, one module per game + shared lib
validators/                              # deterministic checks; every one encodes a past bug
agents/                                  # prompt + harness for the proposal loop (see §6)
STATUS.json                              # per-pipeline stamp, counts, last-success
.github/workflows/refresh.yml            # daily cron
.github/workflows/agent-triage.yml       # on refresh failure / drift report
```

Normalized card shape (identical to the app's):
`{ id, name, number, set: {id, name}, rarity, supertype?, image, price?, game, _lang? }`

`games`: `pokemon`, `pokemon-ja`, `mtg`, `yugioh`, `lorcana`, `one-piece`,
`one-piece-ja`, `riftbound`, `sealed` (cross-game product index).

## 4. Pipeline (daily, GitHub Actions cron)

Stages per game, all guarded, any failure leaves yesterday's data in place:

1. **Stamp check** — tcgcsv `last-updated.txt` and per-source etags; skip
   no-op days (keeps the git log meaningful).
2. **Fetch** — same etiquette as today: custom UA, ≤10 req/s, retries with
   backoff, upstream-fallbacks baked in (pokemontcg.io API → pokemon-tcg-data
   GitHub repo, which never 500s).
3. **Normalize** — to the shared shape; sorted keys, stable ordering (this is
   what makes git delta-compression do the history storage for free).
4. **Validate** (deterministic, `validators/`) — refuse to commit when:
   - any catalog shrinks >2% day-over-day (upstream truncation, bad pull)
   - a REQUIRED set drops below its known floor (the en-prices guard, generalized)
   - an absence-allowlisted group appears upstream (remove it — the real
     catalog takes over; this is the loud-failure rule from build_en_extras)
   - price sanity: >30% of a set's prices changing >5× in one day (the
     wrong-SKU / bad-join tripwire)
   - keys violate normalization (normNumber round-trip)
5. **Diff report** — machine-readable summary: new sets, new unmapped groups,
   count deltas, anomaly list. Committed to `STATUS.json` + posted as the
   run summary. This is the agent's input.
6. **Commit + tag** — one commit `refresh: YYYY-MM-DD (<counts>)`; on the
   1st of each month, tag `snapshot-YYYY-MM`.

## 5. History & retention (≥ 6 months)

- **Catalog + latest prices**: git history, forever. Working tree stays small
  (~40–60 MB: ~140k cards × ~200 B + set lists); daily commits of
  mostly-unchanged sorted JSON pack to a few KB each. Monthly tags make
  point-in-time access a URL, not an archaeology project.
- **Per-card price series**: stays in `rarebox-price-history` (change-point
  arrays, daily granularity 90d / weekly beyond, data back to 2024-02 —
  already exceeds the 6-month requirement). This repo publishes the *pointer*
  and keeps `latest.json` mirrors so most consumers never need both repos.
- **Raw upstream snapshots** (phase 3): trimmed to the fields we consume,
  same git-native retention. If working-tree size ever matters, old months
  compact into `raw/archive/YYYY-MM.jsonl` in the same commit that prunes —
  history is still reachable via tags.
- Repo-size tripwire in CI: warn at 1 GB packed, plan compaction at 2 GB
  (git history rewrite is a consumer-breaking event — avoid by compacting
  the working tree, never rewriting refs).

## 6. The agent loop (DeepSeek or similar)

The pipeline's failure modes need *judgment*, not more code — "is tcgcsv group
24722 '30th Celebration' the same thing as pokemontcg's cel25?" (no — that's
2021's Celebrations). Today that's a human with curl. The loop automates the
research while keeping humans/validators in control:

- **Trigger**: the daily diff report contains a `needs-triage` item — a new
  unmapped group, an allowlist violation, a price-anomaly cluster, a catalog
  shrink, or a pipeline failure.
- **Agent job** (`agent-triage.yml`): a cheap capable model (DeepSeek v3 /
  similar — pennies per run) gets the diff item plus tool access to fetch the
  relevant upstreams (tcgcsv group products, pokemon-tcg-data set list,
  tcgdex). Its ONLY outputs:
  1. a **PR** editing `maps/*` with the evidence quoted in the description
     (e.g. "group 24800 'XY Promos Reprint' — pokemontcg has xyp with matching
     card list, mapping to xyp; NOT an extra"), or
  2. an **issue** when evidence is ambiguous ("two plausible set matches"),
     tagging what a human must decide.
- **Gate**: validators run on the PR (an extras addition must not duplicate an
  existing catalog key; a mapping must produce ≥N key joins). Green checks +
  the evidence template → auto-merge is allowed; anything else waits for
  review. The agent has no push access to `main` — the PR + validator +
  audit-trail design means a hallucinated mapping can't silently corrupt data.
- **Second agent duty — sentinel**: weekly, re-verify a random sample of
  absence-allowlist entries against upstream (the "did pokemontcg.io finally
  add mep?" check) and spot-check 20 random prices against the live tcgcsv
  values. Drift → PR/issue as above.

Why not agents in the main fetch path: fetching is deterministic and cheap;
putting a model there adds cost and nondeterminism where none is needed. The
model earns its keep only where the pipeline currently pages a human.

## 7. Phases

**Phase 0 — seed (this commit)**
Repo, plan, schema, licensing posture, `maps/` seeded from the values already
verified in Rarebox (extra-groups allowlist with evidence notes, JP set names,
quirks doc).

**Phase 1 — Pokémon vertical slice (1–2 days)**
`pipelines/pokemon_en.py` + `pokemon_ja.py` (port of the four existing
builders), validators, daily cron, STATUS.json, first monthly tag. Rarebox
switches its `public/en-*.json`/`jp-*.json` to download from here in its own
CI (keeps the app's offline-first bundling, drops the duplicated builders).

**Phase 2 — the other games (2–3 days)**
One Piece EN/JP, Yu-Gi-Oh!, Riftbound, sealed index ports; new MTG (Scryfall
bulk-data endpoint) and Lorcana (Lorcast bulk) catalog snapshotters.
`prices/{game}/latest.json` mirrors from price-history's daily run.

**Phase 3 — raw layer + agent loop (2 days + tuning)**
Trimmed raw snapshots for reproducibility; `agent-triage.yml` with the PR
template, evidence format, and auto-merge policy; sentinel job. Start with
issues-only output for two weeks to calibrate before enabling PRs.

**Phase 4 — community surface**
SCHEMA.md examples per game, a tiny JS/TS consumer snippet package, dataset
announcement, and a CONTRIBUTING.md for mapping fixes from outside (the same
evidence template the agent uses — humans and agents follow one standard).

## 8. Risks

- **Upstream ToS/goodwill**: same fetch etiquette and volumes as today (one
  daily pull, mostly from tcgcsv's purpose-built archives). Attribution in
  README + per-file `stamp`/`source` fields; takedown contact in README.
- **Wrong data at scale**: the validator set is the real defense — every
  Rarebox data bug from this year (wrong-SKU joins, false ptcgo joins like
  CL→col1, absence-list drift, $0-vs-null) is encoded as a check before the
  agent loop ever runs.
- **GitHub limits**: raw.githubusercontent is rate-limited per-IP for
  anonymous fetches — fine for builders (they should cache), and jsDelivr
  fronts it with a real CDN for hot paths. Not a concern at this dataset size.
- **Agent cost/runaway**: triage runs only on diff items (most days: zero),
  capped tokens, no write access. Worst case is a bad PR that validators
  reject.
