"""Download Microsoft's SEC submissions and companyfacts XBRL JSON."""
import json
import os
from pathlib import Path

import requests

CIK = "0000789019"
BASE = "https://data.sec.gov"
USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "MA-Synergy-Analyzer research contact@users.noreply.github.com",
)
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "microsoft"


def download(endpoint, filename):
    OUT.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        BASE + endpoint, headers={"User-Agent": USER_AGENT}, timeout=30
    )
    response.raise_for_status()
    (OUT / filename).write_text(
        json.dumps(response.json(), indent=2), encoding="utf-8"
    )


def main():
    try:
        download(f"/submissions/CIK{CIK}.json", "submissions.json")
        download(f"/api/xbrl/companyfacts/CIK{CIK}.json", "companyfacts.json")
    except requests.RequestException as error:
        print(f"SEC XBRL retrieval unavailable; continuing without supplement: {error}")


if __name__ == "__main__":
    main()
