"""Download all media recipes from MediaDive (DSMZ).

API: https://mediadive.dsmz.de/rest
Licence: CC BY 4.0.

Response shape (confirmed 2026-04-14):
  GET /media           -> {status, count, data: [ {id, name, ...}, ... ]}
  GET /medium/<id>     -> {status, count, data: {medium: {...}, solutions: [...]}}

Saves:
  data/mediadive/index.json        — the list response
  data/mediadive/media/<id>.json   — one file per medium (resumable)
  data/mediadive/all_media.json    — combined array of every detail payload
"""

import json
import os
import time
import requests

BASE = "https://mediadive.dsmz.de/rest"
OUT_DIR = "data/mediadive"
PER_MEDIUM_DIR = os.path.join(OUT_DIR, "media")
SLEEP = 0.4          # be polite
TIMEOUT = 30


def fetch_json(url):
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def main():
    os.makedirs(PER_MEDIUM_DIR, exist_ok=True)

    print("Fetching index of all media…")
    index = fetch_json(f"{BASE}/media")
    media_list = index["data"]
    with open(os.path.join(OUT_DIR, "index.json"), "w") as f:
        json.dump(index, f, indent=2)
    print(f"  {len(media_list)} media listed.")

    details = []
    total = len(media_list)
    for i, entry in enumerate(media_list, 1):
        mid = entry["id"]
        path = os.path.join(PER_MEDIUM_DIR, f"{mid}.json")

        if os.path.exists(path):
            # Resume: reuse cached detail
            with open(path) as f:
                details.append(json.load(f))
            continue

        try:
            payload = fetch_json(f"{BASE}/medium/{mid}")
            detail = payload.get("data", payload)
            with open(path, "w") as f:
                json.dump(detail, f, indent=2)
            details.append(detail)
        except Exception as e:
            print(f"  [{i}/{total}] medium {mid}: FAILED ({e})")
            time.sleep(SLEEP)
            continue

        if i % 50 == 0 or i == total:
            print(f"  [{i}/{total}] downloaded (latest id={mid})")
        time.sleep(SLEEP)

    combined = os.path.join(OUT_DIR, "all_media.json")
    with open(combined, "w") as f:
        json.dump(details, f, indent=2)
    print(f"\nDone. {len(details)} media -> {combined}")


if __name__ == "__main__":
    main()
