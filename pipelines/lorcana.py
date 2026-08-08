"""Lorcana catalog + prices from Lorcast (sets list + per-set search)."""

import time

from lib import card, fetch_json, norm_number, now_stamp, status_update, write_json, THROTTLE


def run():
    sets = fetch_json("https://api.lorcast.com/v0/sets")["results"]
    set_rows, prices, n = [], {}, 0
    for s in sets:
        code = s.get("code")
        cards = []
        page = 1
        while True:
            r = fetch_json(f"https://api.lorcast.com/v0/cards/search?q=set:{code}&page={page}")
            batch = r.get("results") or []
            cards.extend(batch)
            if not batch or len(cards) >= (r.get("total_cards") or 0):
                break
            page += 1
            time.sleep(THROTTLE)
        rows = []
        for c in cards:
            num = str(c.get("collector_number", ""))
            rows.append(card(
                c.get("id") or f"{code}-{num}", c.get("name", ""), num, code,
                s.get("name", code), (c.get("image_uris") or {}).get("digital", {}).get("small")
                if isinstance(c.get("image_uris"), dict) else None,
                "lorcana", rarity=c.get("rarity")))
            usd = (c.get("prices") or {}).get("usd") or (c.get("prices") or {}).get("usd_foil")
            if usd is not None:
                try:
                    prices.setdefault(f"{code}-{norm_number(num)}", round(float(usd), 2))
                except (TypeError, ValueError):
                    pass
        rows.sort(key=lambda c: (len(c["number"]), c["number"]))
        write_json(f"catalog/lorcana/sets/{code}.json", rows)
        n += len(rows)
        set_rows.append({"id": code, "name": s.get("name"), "series": None,
                         "total": len(rows), "printedTotal": None,
                         "releaseDate": (s.get("released_at") or "")[:10] or None, "logo": None})
        time.sleep(THROTTLE)
    set_rows.sort(key=lambda s: (s.get("releaseDate") or "", s["id"]), reverse=True)
    write_json("catalog/lorcana/sets.json", set_rows)
    write_json("prices/lorcana/latest.json",
               {"stamp": now_stamp(), "source": "lorcast", "prices": prices})
    status_update("lorcana", sets=len(set_rows), cards=n, priced=len(prices), source="lorcast")
    print(f"lorcana: {len(set_rows)} sets, {n} cards, {len(prices)} priced")


if __name__ == "__main__":
    run()
