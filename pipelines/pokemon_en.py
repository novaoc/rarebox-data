"""Pokémon EN catalog from PokemonTCG/pokemon-tcg-data (the canonical repo
behind pokemontcg.io — current, and it never 500s), plus the x- synthetic
extras sets from TCGplayer for card groups the upstream lacks entirely
(maps/en-extra-groups.json — ME promos etc.)."""

import io
import json
import re
import tarfile
import time

from lib import ROOT, card, fetch, fetch_json, norm_number, status_update, write_json, THROTTLE

TARBALL = "https://codeload.github.com/PokemonTCG/pokemon-tcg-data/tar.gz/refs/heads/master"
TCGCSV = "https://tcgcsv.com/tcgplayer"
EN_CATEGORY = 3


def run():
    raw = fetch(TARBALL, timeout=180)
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    sets_member = next(m for m in tf.getmembers() if m.name.endswith("sets/en.json"))
    sets = json.loads(tf.extractfile(sets_member).read().decode())

    set_rows = []
    n_cards = 0
    for s in sets:
        member = next((m for m in tf.getmembers()
                       if m.name.endswith(f"cards/en/{s['id']}.json")), None)
        cards_raw = json.loads(tf.extractfile(member).read().decode()) if member else []
        cards = [
            card(c["id"], c["name"], c.get("number", ""), s["id"], s["name"],
                 (c.get("images") or {}).get("small"), "pokemon",
                 rarity=c.get("rarity"), supertype=c.get("supertype"))
            for c in cards_raw
        ]
        write_json(f"catalog/pokemon/sets/{s['id']}.json", cards)
        n_cards += len(cards)
        set_rows.append({
            "id": s["id"], "name": s["name"], "series": s.get("series"),
            "total": s.get("total"), "printedTotal": s.get("printedTotal"),
            "releaseDate": s.get("releaseDate"),
            "logo": (s.get("images") or {}).get("logo"),
        })

    # ── x- extras: cards no upstream catalog has (see maps/quirks.md) ──
    extras = json.loads((ROOT / "maps/en-extra-groups.json").read_text())
    groups = {str(g["groupId"]): g
              for g in fetch_json(f"{TCGCSV}/{EN_CATEGORY}/groups")["results"]}
    n_extra = 0
    for gid in sorted(extras):
        g = groups.get(gid)
        if not g:
            continue
        ab = (g.get("abbreviation") or "").strip().lower()
        sid = f"x-{ab}" if re.fullmatch(r"[a-z0-9]{2,10}", ab) else f"x-g{gid}"
        prods = fetch_json(f"{TCGCSV}/{EN_CATEGORY}/{gid}/products")["results"]
        time.sleep(THROTTLE)
        cards, seen = [], set()
        for p in prods:
            number = next((e["value"] for e in p.get("extendedData", [])
                           if e.get("name") == "Number"), "")
            if not number or number.lower() in seen:
                continue
            name = re.sub(r"\s*-\s*[0-9/]+\s*$", "", p.get("name", "")).strip()
            if re.search(r"\((?!.*/)[^)]+\)\s*$", name):
                continue
            seen.add(number.lower())
            cards.append(card(
                f"{sid}-{norm_number(number)}", name, number, sid, g["name"],
                f"https://tcgplayer-cdn.tcgplayer.com/product/{p['productId']}_200w.jpg",
                "pokemon"))
        if cards:
            write_json(f"catalog/pokemon/sets/{sid}.json", cards)
            n_extra += len(cards)
            set_rows.append({
                "id": sid, "name": g["name"], "series": "TCGplayer-only",
                "total": len(cards), "printedTotal": None,
                "releaseDate": (g.get("publishedOn") or "")[:10] or None,
                "logo": None,
            })
        time.sleep(THROTTLE)

    set_rows.sort(key=lambda s: (s.get("releaseDate") or "", s["id"]), reverse=True)
    write_json("catalog/pokemon/sets.json", set_rows)
    status_update("pokemon-catalog", sets=len(set_rows), cards=n_cards + n_extra,
                  extras=n_extra, source="pokemon-tcg-data+tcgcsv")
    print(f"pokemon: {len(set_rows)} sets, {n_cards} cards + {n_extra} extras")


if __name__ == "__main__":
    run()
