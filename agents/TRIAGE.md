# Agent triage protocol (PLAN §6)

For any `needs-triage` issue (refresh failure, new unmapped group, allowlist
drift, price anomaly), the triage agent — human or LLM (DeepSeek v3 or
similar); both follow this exact protocol:

1. **Reproduce with evidence.** Fetch the relevant upstreams yourself and
   quote them: the tcgcsv group's products, pokemon-tcg-data's set list,
   the tcgdex response. No claim without a quoted response.
2. **Classify:**
   - *New unmapped group* → name-search pokemon-tcg-data `sets/en.json`.
     A similarly-named set near the same release date ⇒ propose a mapping in
     `maps/groups-pokemon.json`. Verified absent ⇒ propose an entry in
     `maps/en-extra-groups.json` with `evidence` + `verified` date.
     Remember the false-join lesson: an abbreviation match alone is NOT a
     mapping (SM Promos ≠ unmapped-set; CL ≠ TCG Classic's real join).
   - *Allowlisted group now exists upstream* → propose REMOVING the entry
     (the real catalog takes over).
   - *Price anomaly cluster* → check for the wrong-SKU signature (many keys
     in one set moving together to another set's values). Usually a mapping
     bug, not real market movement.
   - *Pipeline failure* → check the upstream's status; transient outages
     need no change (the pipeline keeps yesterday's data by design).
3. **Output: a PR editing `maps/` only** (never `catalog/` or `prices/`
   directly — those are pipeline outputs), with quoted evidence in the
   description, or a comment on the issue explaining why no change is safe.
4. Validators gate every PR; nothing merges red.

LLM runners: keep the whole exchange under 20k tokens; if the evidence does
not clearly decide the case, say so in an issue comment and stop — an
undecided issue is a fine outcome, a guessed mapping is not.
