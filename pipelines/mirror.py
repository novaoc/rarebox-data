"""Mirror step — republishes the price/index assets Rarebox's own daily CI
already builds with guards (en/jp prices, extras, One Piece EN+JP, Yu-Gi-Oh!,
Riftbound). One fetch pipeline upstream, one publisher here; the builders
migrate into this repo in a later phase (PLAN §2) without consumers noticing.

Each mirror keeps the source stamp and refuses to overwrite good data with a
shrunken pull (>2% fewer keys than what's already committed)."""

import json

from lib import ROOT, fetch_json, now_stamp, status_update, write_json

RAREBOX_RAW = "https://raw.githubusercontent.com/novaoc/rarebox/main/public"

MIRRORS = [
    # (source asset, destination, count key path)
    ("en-prices.json", "prices/pokemon/latest.json", "prices"),
    ("en-extras.json", "prices/pokemon/extras.json", "cards"),
    ("jp-prices.json", "prices/pokemon-ja/latest.json", "prices"),
    ("jp-index.json", "prices/pokemon-ja/index.json", "cards"),
    ("op-prices.json", "prices/one-piece/tcgplayer.json", "prices"),
    ("op-jp-index.json", "catalog/one-piece-ja/index.json", "cards"),
    ("op-jp-prices.json", "prices/one-piece-ja/latest.json", "prices"),
    ("ygo-prices.json", "prices/yugioh/tcgplayer.json", "prices"),
    ("riftbound-prices.json", "prices/riftbound/latest.json", "prices"),
]


def count_of(data, key):
    v = data.get(key)
    if isinstance(v, dict):
        return len(v)
    if isinstance(v, list):
        return len(v)
    return 0


def run():
    results = {}
    for src, dest, key in MIRRORS:
        try:
            data = fetch_json(f"{RAREBOX_RAW}/{src}", timeout=120)
        except Exception as e:  # noqa: BLE001
            print(f"  {src}: fetch failed ({e}) — keeping committed copy")
            continue
        n = count_of(data, key)
        prev_path = ROOT / dest
        if prev_path.exists():
            try:
                prev_n = count_of(json.loads(prev_path.read_text()), key)
                if prev_n and n < prev_n * 0.98:
                    print(f"  {src}: shrank {prev_n}→{n} — refusing to overwrite")
                    continue
            except (ValueError, OSError):
                pass
        data.setdefault("mirrored", now_stamp())
        data.setdefault("source", f"rarebox/{src}")
        write_json(dest, data)
        results[src] = n
    status_update("mirror", assets=results, source="rarebox-ci")
    print("mirrored:", ", ".join(f"{k}={v}" for k, v in results.items()))


if __name__ == "__main__":
    run()
