"""One Piece EN catalog + prices from optcgapi (per-set; the API sends no
CORS headers so browsers can't use it directly — one more reason a static
mirror helps every builder). JP sets ride the mirror step (op-jp assets)."""

import time

from lib import card, fetch_json, now_stamp, status_update, write_json, THROTTLE

BASE = "https://optcgapi.com/api"


def run():
    sets = fetch_json(f"{BASE}/allSets/")
    rows_by_set, set_rows, prices, n = {}, [], {}, 0
    for s in sets:
        sid = s.get("set_id") or s.get("id")
        if not sid:
            continue
        try:
            cards_raw = fetch_json(f"{BASE}/sets/{sid}/")
        except Exception:  # noqa: BLE001
            continue
        time.sleep(THROTTLE)
        # preservation: optcgapi is a hobby API with no CORS and no archive —
        # keep the full upstream response, not just our trimmed shape
        write_json(f"raw/optcgapi/{sid}.json", cards_raw)
        rows = []
        for c in cards_raw if isinstance(cards_raw, list) else []:
            cid = c.get("card_set_id")
            if not cid:
                continue
            rows.append(card(
                cid, c.get("card_name", ""), cid.split("-")[-1], sid,
                s.get("set_name", sid), c.get("card_image") or c.get("image"),
                "one-piece", rarity=c.get("rarity")))
            mp = c.get("market_price")
            try:
                mp = round(float(mp), 2)
            except (TypeError, ValueError):
                continue
            prices.setdefault(cid, mp)
        if not rows:
            continue
        write_json(f"catalog/one-piece/sets/{sid}.json", rows)
        n += len(rows)
        set_rows.append({"id": sid, "name": s.get("set_name", sid), "series": None,
                         "total": len(rows), "printedTotal": None,
                         "releaseDate": None, "logo": None})
    set_rows.sort(key=lambda s: s["id"])
    write_json("catalog/one-piece/sets.json", set_rows)
    write_json("prices/one-piece/latest.json",
               {"stamp": now_stamp(), "source": "optcgapi", "prices": prices})
    status_update("one-piece", sets=len(set_rows), cards=n, priced=len(prices), source="optcgapi")
    print(f"one-piece: {len(set_rows)} sets, {n} cards, {len(prices)} priced")


if __name__ == "__main__":
    run()
