"""Magic catalog + prices from Scryfall's bulk-data endpoint (purpose-built
for exactly this; one download, no per-card requests). default_cards covers
every printing; we trim to the shared shape and emit per-set files plus
prices/mtg/latest.json keyed {setCode}-{collectorNumber}."""

import gzip
import json
from collections import defaultdict

from lib import card, fetch, fetch_json, norm_number, now_stamp, status_update, write_json


def run():
    bulk = fetch_json("https://api.scryfall.com/bulk-data")
    entry = next(b for b in bulk["data"] if b["type"] == "default_cards")
    # Scryfall serves bulk as gzipped JSONL now (jsonl_download_uri); the old
    # plain download_uri is gone
    blob = fetch(entry["jsonl_download_uri"], timeout=600)
    raw = [json.loads(line) for line in gzip.decompress(blob).splitlines() if line.strip()]

    sets_meta = {s["code"]: s for s in fetch_json("https://api.scryfall.com/sets")["data"]}

    by_set = defaultdict(list)
    prices = {}
    for c in raw:
        if c.get("digital"):
            continue
        code = c.get("set")
        img = ((c.get("image_uris") or {}).get("small")
               or ((c.get("card_faces") or [{}])[0].get("image_uris") or {}).get("small"))
        by_set[code].append(card(
            c["id"], c["name"], c.get("collector_number", ""), code,
            c.get("set_name", code), img, "mtg", rarity=c.get("rarity")))
        usd = c.get("prices", {}).get("usd") or c.get("prices", {}).get("usd_foil")
        if usd is not None:
            key = f"{code}-{norm_number(c.get('collector_number'))}"
            prices.setdefault(key, round(float(usd), 2))

    set_rows = []
    for code, cards in by_set.items():
        cards.sort(key=lambda c: (len(c["number"]), c["number"]))
        write_json(f"catalog/mtg/sets/{code}.json", cards)
        m = sets_meta.get(code, {})
        set_rows.append({
            "id": code, "name": m.get("name", code), "series": m.get("set_type"),
            "total": len(cards), "printedTotal": m.get("card_count"),
            "releaseDate": m.get("released_at"), "logo": None,
        })
    set_rows.sort(key=lambda s: (s.get("releaseDate") or "", s["id"]), reverse=True)
    write_json("catalog/mtg/sets.json", set_rows)
    write_json("prices/mtg/latest.json",
               {"stamp": now_stamp(), "source": "scryfall", "prices": prices})
    n = sum(len(v) for v in by_set.values())
    status_update("mtg", sets=len(set_rows), cards=n, priced=len(prices), source="scryfall-bulk")
    print(f"mtg: {len(set_rows)} sets, {n} cards, {len(prices)} priced")


if __name__ == "__main__":
    run()
