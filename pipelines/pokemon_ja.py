"""Japanese Pokémon catalog: tcgdex set lists + the TCGplayer JP catalog
(category 85) appended for the secret rares tcgdex's API omits — the same
merge that fixed SV8-136 in Rarebox. Scan URLs are 3-digit zero-padded
(CDN requirement, see maps/quirks.md); scan-less sets fall back to
TCGplayer product photos."""

import json
import re
import time

from lib import ROOT, card, fetch_json, norm_number, status_update, write_json, THROTTLE

TCGDEX = "https://api.tcgdex.net/v2/ja"
TCGCSV = "https://tcgcsv.com/tcgplayer"
JP_CATEGORY = 85


def series_of(set_id: str):
    sid = set_id if set_id.startswith("neo") else set_id.upper()
    for prefix, series in [("SV", "SV"), ("SM", "SM"), ("ST", None), ("S", "S"),
                           ("M", "M"), ("XY", "XY"), ("BW", "BW"), ("DP", "DP"),
                           ("EX", "EX"), ("E", "EX"), ("neo", "NEO")]:
        if sid.startswith(prefix):
            return series
    return None


def scan_url(set_id, local_id, size="low"):
    series = series_of(set_id)
    if not series:
        return None
    return f"https://assets.tcgdex.net/ja/{series}/{set_id}/{str(local_id).zfill(3)}/{size}.webp"


def run():
    jp_names = json.loads((ROOT / "maps/jp-set-names.json").read_text())

    # TCGplayer JP: group abbreviation == tcgdex set id. English names,
    # product ids (photos), and — crucially — the full print run incl. secrets.
    tcg_by_set = {}
    for g in fetch_json(f"{TCGCSV}/{JP_CATEGORY}/groups")["results"]:
        abbr = (g.get("abbreviation") or "").strip()
        if not abbr:
            continue
        try:
            prods = fetch_json(f"{TCGCSV}/{JP_CATEGORY}/{g['groupId']}/products")["results"]
        except Exception:  # noqa: BLE001
            continue
        rows = {}
        for p in prods:
            number = next((e["value"] for e in p.get("extendedData", [])
                           if e.get("name") == "Number"), "")
            if not number:
                continue
            if re.search(r"\((?!.*/)[^)]+\)\s*$", p.get("name", "")):
                continue
            num = norm_number(number)
            rows.setdefault(num, {
                "name": re.sub(r"\s*-\s*[0-9/]+\s*$", "", p.get("name", "")).strip(),
                "pid": p["productId"],
                "raw": str(number).split("/")[0].strip(),
            })
        tcg_by_set[abbr.lower()] = rows
        time.sleep(THROTTLE)

    sets = fetch_json(f"{TCGDEX}/sets")
    set_rows, n_cards, n_secret = [], 0, 0
    for s in sets:
        sid = s["id"]
        try:
            detail = fetch_json(f"{TCGDEX}/sets/{sid}")
        except Exception:  # noqa: BLE001
            continue
        time.sleep(THROTTLE)
        tcg = tcg_by_set.get(sid.lower(), {})
        cards, seen = [], set()
        for c in detail.get("cards") or []:
            local = c.get("localId") or (c.get("id", "").split("-")[-1])
            num = norm_number(local)
            seen.add(num)
            en = tcg.get(num, {})
            img = (c.get("image") + "/low.webp") if c.get("image") else \
                (f"https://tcgplayer-cdn.tcgplayer.com/product/{en['pid']}_200w.jpg" if en.get("pid") else None)
            cards.append(card(
                f"{sid}-{local}", en.get("name") or c.get("name", ""), local,
                sid, jp_names.get(sid, s.get("name", sid)), img, "pokemon", lang="ja"))
        # secrets the tcgdex API omits but TCGplayer knows
        for num, en in sorted(tcg.items(), key=lambda kv: (len(kv[1]["raw"]), kv[1]["raw"])):
            if num in seen:
                continue
            img = scan_url(sid, en["raw"]) or \
                f"https://tcgplayer-cdn.tcgplayer.com/product/{en['pid']}_200w.jpg"
            cards.append(card(f"{sid}-{en['raw']}", en["name"], en["raw"], sid,
                              jp_names.get(sid, s.get("name", sid)), img, "pokemon", lang="ja"))
            n_secret += 1
        if not cards:
            continue
        write_json(f"catalog/pokemon-ja/sets/{sid}.json", cards)
        n_cards += len(cards)
        set_rows.append({
            "id": sid, "name": jp_names.get(sid, s.get("name", sid)),
            "nameJa": s.get("name"), "series": series_of(sid),
            "total": len(cards),
            "printedTotal": (detail.get("cardCount") or {}).get("official"),
            "releaseDate": detail.get("releaseDate"), "logo": None,
        })

    set_rows.sort(key=lambda s: (s.get("releaseDate") or "", s["id"]), reverse=True)
    write_json("catalog/pokemon-ja/sets.json", set_rows)
    status_update("pokemon-ja-catalog", sets=len(set_rows), cards=n_cards,
                  secrets_appended=n_secret, source="tcgdex+tcgcsv85")
    print(f"pokemon-ja: {len(set_rows)} sets, {n_cards} cards ({n_secret} secrets appended)")


if __name__ == "__main__":
    run()
