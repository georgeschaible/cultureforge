"""Download BacDive records only for strains that appear in MediaDive links.

Strategy: scan data/mediadive/medium_strains/*.json, collect unique bacdive_id
values, then GET https://api.bacdive.dsmz.de/fetch/{id} for each (resumable).
"""

import glob
import json
import os
import time
import requests

BASE = "https://api.bacdive.dsmz.de"
SRC_DIR = "data/mediadive/medium_strains"
OUT_DIR = "data/bacdive/strains"
SLEEP = 0.3
TIMEOUT = 30


def collect_ids():
    ids = set()
    for p in glob.glob(os.path.join(SRC_DIR, "*.json")):
        with open(p) as f:
            for row in json.load(f):
                bid = row.get("bacdive_id")
                if bid:
                    ids.add(int(bid))
    return sorted(ids)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ids = collect_ids()
    print(f"{len(ids)} unique BacDive IDs to fetch")

    for i, bid in enumerate(ids, 1):
        path = os.path.join(OUT_DIR, f"{bid}.json")
        if os.path.exists(path):
            continue
        try:
            r = requests.get(f"{BASE}/fetch/{bid}", timeout=TIMEOUT)
            if r.status_code == 200:
                payload = r.json()
                # results is a dict keyed by the id
                rec = payload.get("results", {}).get(str(bid)) or next(
                    iter(payload.get("results", {}).values()), None
                )
                with open(path, "w") as f:
                    json.dump(rec, f)
            else:
                print(f"  {bid}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  {bid}: {e}")
        if i % 200 == 0 or i == len(ids):
            print(f"  [{i}/{len(ids)}]")
        time.sleep(SLEEP)

    print(f"Done. Files in {OUT_DIR}")


if __name__ == "__main__":
    main()
