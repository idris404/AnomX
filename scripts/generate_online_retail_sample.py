"""Generate a small Online Retail II-like sample CSV for demos."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl

OUTPUT = Path("data/online_retail/sample.csv")


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2011, 1, 1, tzinfo=UTC)
    rows: list[dict[str, object]] = []

    for day in range(120):
        day_start = start + timedelta(days=day)
        lines = 20 + (day % 7) * 3
        for line in range(lines):
            quantity = 1 + ((day + line) % 5)
            unit_price = 2.5 + ((day + line) % 10) * 0.35
            if day == 90 and line < 3:
                quantity *= 25
            rows.append(
                {
                    "InvoiceDate": day_start + timedelta(minutes=line * 7),
                    "Quantity": float(quantity),
                    "UnitPrice": round(unit_price, 2),
                    "StockCode": f"S{1000 + line}",
                }
            )

    frame = pl.DataFrame(rows)
    frame.write_csv(OUTPUT)
    print(f"Wrote {len(rows)} invoice lines to {OUTPUT}")


if __name__ == "__main__":
    main()
