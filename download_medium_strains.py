"""Download the organism↔medium links from MediaDive.

Endpoint: GET /medium-strains/{medium_id}
Returns: {status, count, data: [{id, species, ccno, growth, bacdive_id, domain}, ...]}

Saves one JSON per medium under data/mediadive/medium_strains/. Resumable.
"""

import json
import os
import time
import requests

BASE = "https://mediadive.dsmz.de/rest"
OUT = "data/mediadive/medium_strains"
INDEX = "data/mediadive/index.json"
SLEEP = 0.3
TIMEOUT = 30


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(INDEX) as f:
        media_list = json.load(f)["data"]

    total = len(media_list)
    for i, entry in enumerate(media_list, 1):
        mid = entry["id"]
        path = os.path.join(OUT, f"{mid}.json")
        if os.path.exists(path):
            continue
        try:
            r = requests.get(f"{BASE}/medium-strains/{mid}", timeout=TIMEOUT)
            r.raise_for_status()
            payload = r.json()
            with open(path, "w") as f:
                json.dump(payload.get("data", []), f)
        except Exception as e:
            print(f"  [{i}/{total}] medium {mid}: {e}")
        if i % 100 == 0 or i == total:
            print(f"  [{i}/{total}] done")
        time.sleep(SLEEP)

    print(f"Done. Files in {OUT}")


if __name__ == "__main__":
    main()
