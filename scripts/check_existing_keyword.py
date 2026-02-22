#!/usr/bin/env python3
"""
Check if a city/keyword combination has already been scraped.
Returns: 0 = skip (good data), 1 = scrape needed
"""

import re
import sys
from pathlib import Path

import pandas as pd


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    sanitized = re.sub(r'[<>:"/\\|?*]', "", filename)
    sanitized = sanitized.replace(" ", "_")
    return sanitized[:100]


def check_existing_results(city: str, keyword: str) -> tuple[bool, str, int]:
    """Return (should_skip, message, row_count)."""
    leads_dir = Path("data/leads")
    if not leads_dir.exists():
        return False, "No data directory", 0

    sanitized_city = sanitize_filename(city)
    sanitized_keyword = sanitize_filename(keyword)
    pattern = f"{sanitized_city}_{sanitized_keyword}_*.csv"
    # Search recursively so country-organized folders (data/leads/<Country>/...) are included.
    matching_files = sorted(
        (path for path in leads_dir.rglob(pattern) if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not matching_files:
        return False, "No existing data", 0

    latest_file = matching_files[0]

    try:
        df = pd.read_csv(latest_file)
        row_count = len(df)
    except Exception as error:
        return False, f"Error reading file: {error}", 0

    if row_count > 1:
        return True, f"Already scraped ({row_count} results)", row_count

    return False, f"Low results ({row_count})", row_count


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: check_existing_keyword.py <city> <keyword>")
        sys.exit(2)

    city_arg = sys.argv[1]
    keyword_arg = sys.argv[2]

    should_skip, message, row_count = check_existing_results(city_arg, keyword_arg)

    if should_skip:
        print(f"SKIP:{message}:{row_count}")
        sys.exit(0)

    print(f"SCRAPE:{message}:{row_count}")
    sys.exit(1)
