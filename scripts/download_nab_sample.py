"""Download a small NAB sample dataset for local demos."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

NAB_BASE = "https://raw.githubusercontent.com/numenta/NAB/master"
DATASET = "realKnownCause/cpu_utilization_asg_misconfiguration.csv"
OUTPUT_DIR = Path("data/nab")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data_url = f"{NAB_BASE}/data/{DATASET}"
    labels_url = f"{NAB_BASE}/labels/combined_windows.json"

    data_path = OUTPUT_DIR / Path(DATASET).name
    labels_path = OUTPUT_DIR / "combined_windows.json"

    _download(data_url, data_path)
    _download(labels_url, labels_path)

    # Sanity check labels file
    payload = json.loads(labels_path.read_text(encoding="utf-8"))
    key = f"realKnownCause/{data_path.name}"
    windows = payload.get(key, [])
    print(f"Wrote {data_path} ({data_path.stat().st_size} bytes)")
    print(f"Wrote {labels_path} ({len(windows)} anomaly windows for {key})")


def _download(url: str, destination: Path) -> None:
    print(f"Downloading {url} -> {destination}")
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310
        destination.write_bytes(response.read())


if __name__ == "__main__":
    main()
