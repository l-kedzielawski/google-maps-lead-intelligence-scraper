#!/usr/bin/env python3
"""
Check if a city/business-type combination has already been scraped
Returns: 0 = skip (good data), 1 = scrape needed
"""

import sys
import pandas as pd
from pathlib import Path
import yaml
import re


def load_keywords():
    """Load keywords from YAML file"""
    keywords_path = Path("config/search_keywords.yaml")
    with open(keywords_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_translated_keyword(business_type, language):
    """Get translated keyword for business type and language"""
    keywords = load_keywords()

    if business_type in keywords:
        translations = keywords[business_type]
        if language in translations:
            return translations[language]
        # Fall back to English
        return translations.get("en", business_type)

    return business_type


def sanitize_filename(filename):
    """Sanitize filename by removing invalid characters (same as src.utils)"""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")
    # Limit length
    return sanitized[:100]


def check_existing_results(city, business_type, language):
    """
    Check if results exist and have more than 1 entry

    Args:
        city: City name
        business_type: Business type (e.g., pastry_shop)
        language: Language code (e.g., de)

    Returns:
        Tuple of (should_skip: bool, message: str, row_count: int)
    """
    # Get the actual keyword that would be used
    keyword = get_translated_keyword(business_type, language)

    # Sanitize city name for file matching (use same function as csv_handler)
    sanitized_city = sanitize_filename(city)

    # Check if data/leads directory exists
    leads_dir = Path("data/leads")
    if not leads_dir.exists():
        return False, "No data directory", 0

    # Find any CSV file for this city + keyword combination
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

    # Use the most recent file
    latest_file = matching_files[0]

    # Try to read the CSV and count rows
    try:
        df = pd.read_csv(latest_file)
        row_count = len(df)
    except Exception as e:
        return False, f"Error reading file: {e}", 0

    if row_count > 1:
        return True, f"Already scraped ({row_count} results)", row_count
    else:
        return False, f"Low results ({row_count})", row_count


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: check_existing.py <city> <business_type> <language>")
        sys.exit(2)

    city = sys.argv[1]
    business_type = sys.argv[2]
    language = sys.argv[3]

    should_skip, message, row_count = check_existing_results(
        city, business_type, language
    )

    if should_skip:
        print(f"SKIP:{message}:{row_count}")
        sys.exit(0)
    else:
        print(f"SCRAPE:{message}:{row_count}")
        sys.exit(1)
