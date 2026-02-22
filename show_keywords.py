#!/usr/bin/env python3
"""List available business types and translations."""

import argparse
import sys
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table


console = Console()


def load_keywords(file_path: Path) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(f"Missing keyword config: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file_handle:
        data = yaml.safe_load(file_handle)

    if not isinstance(data, dict):
        return {}

    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show available business types from config/search_keywords.yaml"
    )
    parser.add_argument(
        "--language",
        type=str,
        help="Optional language code to show one translation column (e.g. de, it, fr)",
    )
    args = parser.parse_args()

    config_path = Path("config/search_keywords.yaml")

    try:
        keywords = load_keywords(config_path)
    except FileNotFoundError as error:
        console.print(f"[red]{error}[/red]")
        return 1

    if not keywords:
        console.print(
            "[yellow]No keywords found in config/search_keywords.yaml[/yellow]"
        )
        return 0

    language = args.language.lower().strip() if args.language else None

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Business Type", style="cyan")

    if language:
        table.add_column(language, style="green")
    else:
        table.add_column("Languages", style="green")

    for business_type in sorted(keywords.keys()):
        translations = keywords.get(business_type, {})
        if not isinstance(translations, dict):
            continue

        if language:
            value = translations.get(language) or translations.get("en") or "-"
            table.add_row(business_type, str(value))
        else:
            available = ", ".join(sorted(translations.keys()))
            table.add_row(business_type, available)

    console.print(
        f"\n[bold cyan]Available business types: {len(keywords)}[/bold cyan]\n"
    )
    console.print(table)
    console.print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
