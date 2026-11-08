"""Record every downloaded file in data_log.csv.

2026 mortality data is provisional and will be revised, so each result must be
traceable to the exact file version it was built from.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from heatrisk.config import PROJECT_ROOT, load_settings

FIELDS = ["file", "source", "dataset_id", "version", "downloaded_utc", "url", "notes"]


def log_download(
    file: str | Path,
    source: str,
    dataset_id: str,
    version: str = "",
    url: str = "",
    notes: str = "",
    log_path: str | Path | None = None,
) -> dict[str, str]:
    log_path = Path(log_path or PROJECT_ROOT / load_settings()["paths"]["data_log"])
    row = {
        "file": str(file),
        "source": source,
        "dataset_id": dataset_id,
        "version": version,
        "downloaded_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "url": url,
        "notes": notes,
    }
    new_file = not log_path.exists() or log_path.stat().st_size == 0
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    return row
