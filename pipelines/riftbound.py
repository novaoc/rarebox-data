"""Riftbound catalog from riftcodex (small hobby API — preservation
priority: raw responses are kept too). Prices mirror Rarebox's daily
PriceCharting-built asset until that builder migrates here."""

import time

from lib import card, fetch_json, status_update, write_json, THROTTLE

RIFTCODEX = "https://api.riftcodex.com"


def run():
    sets = fetch_json(f"{RIFTCODEX}/sets")
    listing = sets.get("items") if isinstance(sets, dict) else sets
    write_json("raw/riftcodex/sets.json", listing)
    set_rows, n = [], 0
    for s in listing or []:
        sid = s.get("set_id") or s.get("id")
        if not sid:
            continue
        cards_raw, page = [], 1
        while True:
            d = fetch_json(f"{RIFTCODEX}/cards?set_id={sid}&limit=100&page={page}")
            batch = d.get("items") if isinstance(d, dict) else d
            if not batch:
                break
            cards_raw.extend(batch)
            if page >= (d.get("pages") or 1):
                break
            page += 1
            time.sleep(THROTTLE)
        write_json(f"raw/riftcodex/cards-{sid}.json", cards_raw)
        rows = [card(c.get("riftbound_id") or str(c.get("id")), c.get("name", ""),
                     str(c.get("collector_number") or ""),
                     str(sid), s.get("name", str(sid)),
                     (c.get("media") or {}).get("image_url"), "riftbound",
                     rarity=(c.get("classification") or {}).get("rarity"),
                     supertype=(c.get("classification") or {}).get("type")) for c in cards_raw]
        rows.sort(key=lambda c: (len(c["number"]), c["number"]))
        write_json(f"catalog/riftbound/sets/{sid}.json", rows)
        n += len(rows)
        set_rows.append({"id": str(sid), "name": s.get("name", str(sid)), "series": None,
                         "total": len(rows), "printedTotal": None,
                         "releaseDate": (s.get("release_date") or "")[:10] or None,
                         "logo": None})
        time.sleep(THROTTLE)
    set_rows.sort(key=lambda s: (s.get("releaseDate") or "", s["id"]), reverse=True)
    write_json("catalog/riftbound/sets.json", set_rows)
    status_update("riftbound-catalog", sets=len(set_rows), cards=n, source="riftcodex")
    print(f"riftbound: {len(set_rows)} sets, {n} cards")


if __name__ == "__main__":
    run()
