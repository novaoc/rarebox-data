"""Yu-Gi-Oh! catalog + prices from YGOPRODeck's full dump (one request).
A card belongs to many sets; we emit one row per (card, set printing),
keyed by the printing's set code — set-specific prices live in
card_sets[].set_price (the rule from rarebox's AGENTS.md)."""

import re
from collections import defaultdict

from lib import card, fetch_json, now_stamp, status_update, write_json


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


def run():
    data = fetch_json("https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes", timeout=300)["data"]

    by_set = defaultdict(list)
    set_names = {}
    prices = {}
    for c in data:
        img = (c.get("card_images") or [{}])[0].get("image_url_small")
        for printing in c.get("card_sets") or []:
            sname = printing.get("set_name") or ""
            scode = (printing.get("set_code") or "").strip()
            if not sname or not scode:
                continue
            sid = slug(sname)
            set_names[sid] = sname
            by_set[sid].append(card(
                scode, c["name"], scode.split("-")[-1], sid, sname, img, "yugioh",
                rarity=printing.get("set_rarity"), supertype=c.get("type")))
            p = printing.get("set_price")
            try:
                p = round(float(p), 2)
            except (TypeError, ValueError):
                continue
            if p > 0:  # YGOPRODeck uses "0.00" as unknown, not a real $0
                prices.setdefault(scode.lower(), p)

    set_rows = []
    for sid, cards in by_set.items():
        cards.sort(key=lambda c: c["id"])
        write_json(f"catalog/yugioh/sets/{sid}.json", cards)
        set_rows.append({"id": sid, "name": set_names[sid], "series": None,
                         "total": len(cards), "printedTotal": None,
                         "releaseDate": None, "logo": None})
    set_rows.sort(key=lambda s: s["id"])
    write_json("catalog/yugioh/sets.json", set_rows)
    write_json("prices/yugioh/latest.json",
               {"stamp": now_stamp(), "source": "ygoprodeck", "prices": prices})
    n = sum(len(v) for v in by_set.values())
    status_update("yugioh", sets=len(set_rows), cards=n, priced=len(prices), source="ygoprodeck")
    print(f"yugioh: {len(set_rows)} sets, {n} printings, {len(prices)} priced")


if __name__ == "__main__":
    run()
