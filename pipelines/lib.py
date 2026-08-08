"""Shared plumbing for every pipeline: polite fetching, the one true number
normalization, stable JSON writing (sorted keys — git delta-compression is
the history engine), and STATUS bookkeeping."""

import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADERS = {
    "User-Agent": "rarebox-data/1.0 (+https://github.com/novaoc/rarebox-data)",
    "Accept": "application/json",
}
THROTTLE = 0.1  # ≤10 req/s everywhere


def fetch(url: str, timeout: int = 60, retries: int = 3) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception:  # noqa: BLE001
            if attempt >= retries:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("unreachable")


def fetch_json(url: str, timeout: int = 60, retries: int = 3):
    return json.loads(fetch(url, timeout, retries).decode())


def norm_number(num) -> str:
    """MUST mirror rarebox normEnNumber: '001/217'→'1', 'TG07'→'tg7',
    'SWSH001'→'swsh1', '0'→'0'."""
    n = str(num or "").split("/")[0].strip().lower()
    n = re.sub(r"^0+(?=[a-z0-9])", "", n)
    m = re.match(r"^([a-z]+)0*(\d.*)$", n)
    if m:
        n = m.group(1) + m.group(2)
    return n


def write_json(rel_path: str, data) -> Path:
    """Sorted keys, tight separators, trailing newline — byte-stable output."""
    p = ROOT / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=False) + "\n")
    return p


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def status_update(pipeline: str, **fields):
    p = ROOT / "STATUS.json"
    try:
        status = json.loads(p.read_text())
    except (ValueError, OSError):
        status = {}
    status.setdefault("pipelines", {})[pipeline] = {"updated": now_stamp(), **fields}
    status["phase"] = 1
    status.pop("note", None)
    p.write_text(json.dumps(status, indent=1, sort_keys=True) + "\n")


def card(id_, name, number, set_id, set_name, image, game,
         rarity=None, supertype=None, lang=None):
    """The shared normalized card shape (see SCHEMA.md)."""
    c = {
        "id": id_, "name": name, "number": str(number),
        "set": {"id": set_id, "name": set_name},
        "image": image or None, "game": game,
    }
    if rarity:
        c["rarity"] = rarity
    if supertype:
        c["supertype"] = supertype
    if lang:
        c["_lang"] = lang
    return c
