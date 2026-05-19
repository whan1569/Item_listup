"""
Aggregate.py

Purpose:
- Read data/raw_search_phrases.csv from Crawler.py
- Aggregate raw phrases into simple search-term volume table
- No product filtering
- No scoring
- No keyword splitting
- Output only search_term + search_volume first

Input:
    data/raw_search_phrases.csv

Output:
    data/search_volume.csv

Run:
    python Aggregate.py
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional


DATA_DIR = Path("data")
INPUT_CSV = DATA_DIR / "raw_search_phrases.csv"
OUTPUT_CSV = DATA_DIR / "search_volume.csv"


def normalize_search_term(value: Optional[str]) -> str:
    """
    Minimal aggregation normalization.

    Allowed:
    - lowercase
    - whitespace normalization
    - strip edges

    Not allowed:
    - word splitting
    - product filtering
    - stopword removal
    - price/unit removal
    - phrase recombination
    """
    if not value:
        return ""

    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def read_raw_phrases(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def aggregate(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(lambda: {
        "search_volume": 0,
        "sources": set(),
        "example_raw_phrase": "",
    })

    for row in rows:
        raw_phrase = row.get("raw_phrase", "")
        search_term = normalize_search_term(raw_phrase)

        if not search_term:
            continue

        g = grouped[search_term]
        g["search_volume"] += 1

        source = row.get("source", "")
        if source:
            g["sources"].add(source)

        if not g["example_raw_phrase"]:
            g["example_raw_phrase"] = raw_phrase

    output_rows: list[dict] = []

    for search_term, data in grouped.items():
        output_rows.append({
            "search_term": search_term,
            "search_volume": data["search_volume"],
            "source_count": len(data["sources"]),
            "sources": ",".join(sorted(data["sources"])),
            "example_raw_phrase": data["example_raw_phrase"],
        })

    output_rows.sort(
        key=lambda x: (x["search_volume"], x["source_count"], x["search_term"]),
        reverse=True,
    )

    return output_rows


def write_csv(rows: list[dict], path: Path) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "search_term",
            "search_volume",
            "source_count",
            "sources",
            "example_raw_phrase",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = read_raw_phrases(INPUT_CSV)
    result = aggregate(rows)
    write_csv(result, OUTPUT_CSV)

    print(f"input rows: {len(rows)}")
    print(f"unique search terms: {len(result)}")
    print(f"saved: {OUTPUT_CSV}")
    print()
    print("TOP 50 SEARCH TERMS")

    for row in result[:50]:
        print(
            f"{row['search_term']} | volume={row['search_volume']} | "
            f"sources={row['source_count']}"
        )


if __name__ == "__main__":
    main()
