"""Run every pipeline; any single failure leaves that game's committed data
in place and the rest continue. Exit non-zero only when NOTHING succeeded
(total outage) so a flaky upstream never blocks the day's other captures."""

import sys
import traceback

import lorcana
import mirror
import mtg
import one_piece
import pokemon_en
import pokemon_ja
import riftbound
import yugioh

PIPELINES = [
    ("pokemon-en", pokemon_en.run),
    ("pokemon-ja", pokemon_ja.run),
    ("mtg", mtg.run),
    ("yugioh", yugioh.run),
    ("lorcana", lorcana.run),
    ("one-piece", one_piece.run),
    ("riftbound", riftbound.run),
    ("mirror", mirror.run),
]


def main() -> int:
    ok, failed = [], []
    for name, fn in PIPELINES:
        print(f"=== {name} ===", flush=True)
        try:
            fn()
            ok.append(name)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            failed.append(name)
    print(f"\ndone: {len(ok)} ok ({', '.join(ok)})"
          + (f" · {len(failed)} FAILED ({', '.join(failed)})" if failed else ""))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
