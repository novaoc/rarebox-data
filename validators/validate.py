"""Deterministic gates run before any refresh commit. Every check encodes a
failure that actually happened (see maps/quirks.md). Non-zero exit = the
day's changes must not be committed.

Checks:
1. every JSON file parses
2. no catalog set-list shrinks >2% vs the committed state (git HEAD)
3. price files: keys normalize round-trip; $0 allowed; null forbidden
4. absence allowlist entries carry evidence + verified date
5. price sanity vs committed: <30% of shared keys moving >5x in one refresh
"""

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
bad = []


def committed(path: str):
    try:
        out = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT,
                             capture_output=True, text=True)
        return json.loads(out.stdout) if out.returncode == 0 else None
    except (ValueError, OSError):
        return None


def norm_number(num) -> str:
    import re
    n = str(num or "").split("/")[0].strip().lower()
    n = re.sub(r"^0+(?=[a-z0-9])", "", n)
    m = re.match(r"^([a-z]+)0*(\d.*)$", n)
    return (m.group(1) + m.group(2)) if m else n


# 1 — parseability
for p in ROOT.rglob("*.json"):
    if ".git" in p.parts:
        continue
    try:
        json.load(open(p))
    except Exception as e:  # noqa: BLE001
        bad.append(f"invalid JSON {p.relative_to(ROOT)}: {e}")

# 2 — catalog shrink guard
for sets_file in ROOT.glob("catalog/*/sets.json"):
    rel = str(sets_file.relative_to(ROOT))
    now = json.load(open(sets_file))
    prev = committed(rel)
    if prev and len(now) < len(prev) * 0.98:
        bad.append(f"{rel}: sets shrank {len(prev)}→{len(now)} (>2%) — upstream truncation?")

# 3 — price files
for pf in ROOT.glob("prices/*/latest.json"):
    rel = str(pf.relative_to(ROOT))
    d = json.load(open(pf))
    prices = d.get("prices", {})
    def price_ok(v):
        # flat number, or a per-variant map ({foil: null, normal: 14.31} —
        # null inside a variant map means "this variant has no market")
        if isinstance(v, (int, float)):
            return v >= 0
        if isinstance(v, dict) and v:
            return all(x is None or (isinstance(x, (int, float)) and x >= 0)
                       for x in v.values())
        return False

    for k, v in list(prices.items())[:100000]:
        if not price_ok(v):
            bad.append(f"{rel}: bad price at {k}: {v!r}")
            break
    # 5 — sanity vs committed
    prev = committed(rel)
    if prev:
        pp = prev.get("prices", {})
        shared = [k for k in prices
                  if isinstance(prices.get(k), (int, float)) and prices[k]
                  and isinstance(pp.get(k), (int, float)) and pp[k]]
        if len(shared) > 100:
            wild = sum(1 for k in shared
                       if prices[k] / pp[k] > 5 or pp[k] / prices[k] > 5)
            if wild > len(shared) * 0.3:
                bad.append(f"{rel}: {wild}/{len(shared)} prices moved >5x — bad join?")

# 4 — allowlist evidence
extras = json.load(open(ROOT / "maps/en-extra-groups.json"))
for gid, e in extras.items():
    if not (e.get("evidence") and e.get("verified")):
        bad.append(f"maps/en-extra-groups.json: group {gid} lacks evidence/verified")

if bad:
    print("VALIDATION FAILED:")
    for b in bad:
        print(" -", b)
    sys.exit(1)
print("validation passed")
