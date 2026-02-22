#!/usr/bin/env python3
"""
Google Maps Lead Scraper
Scrapes business information (phone, email, address) from Google Maps
"""

import argparse
import signal
import yaml
import sys
from pathlib import Path
from typing import Optional
from src.scraper import GoogleMapsScraper
from src.utils import setup_logging, load_config
from src.csv_handler import CSVHandler
from rich.console import Console
from rich.table import Table

console = Console()


def display_statistics_table(stats: dict, title: Optional[str] = None) -> None:
    """
    Display statistics in a formatted table

    Args:
        stats: Dictionary containing statistics
        title: Optional title to display before the table
    """
    if title:
        console.print(f"\n[bold cyan]{title}[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Businesses", str(stats.get("total_businesses", 0)))
    table.add_row(
        "With Phone",
        f"{stats.get('with_phone', 0)} ({stats.get('phone_percentage', 0)}%)",
    )
    table.add_row(
        "With Email",
        f"{stats.get('with_email', 0)} ({stats.get('email_percentage', 0)}%)",
    )
    table.add_row(
        "With Website",
        f"{stats.get('with_website', 0)} ({stats.get('website_percentage', 0)}%)",
    )

    # Only show these if they exist in stats
    if "with_rating" in stats:
        table.add_row("With Rating", str(stats.get("with_rating", 0)))
    if "unique_cities" in stats:
        table.add_row("Unique Cities", str(stats.get("unique_cities", 0)))

    console.print(table)


def load_keywords() -> dict:
    """Load business keywords from YAML file"""
    keywords_path = Path("config/search_keywords.yaml")
    if keywords_path.exists():
        with open(keywords_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_keyword_from_type(business_type, language, keywords_dict):
    """Get translated keyword for business type and language"""
    if business_type in keywords_dict:
        translations = keywords_dict[business_type]
        if language in translations:
            return translations[language]
        # Fall back to English
        return translations.get("en", business_type)
    # If not in predefined keywords, use as-is
    return business_type


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Google Maps Lead Scraper - Extract business contact information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python main.py --city "Paris" --keyword "boulangerie" --language "fr"
  
  # Using predefined business type
  python main.py --city "Rome" --business-type "ice_cream" --language "it"
  
  # With email extraction from websites (slower)
  python main.py --city "Barcelona" --keyword "bakery" --find-emails
  
  # Limit results
  python main.py --city "London" --keyword "cafe" --max-results 50
  
  # Show statistics for a CSV file
  python main.py --stats data/leads/Paris_bakery_20231215_120000.csv
        """,
    )

    parser.add_argument(
        "--city", type=str, help='City to search in (e.g., "Paris", "New York")'
    )
    parser.add_argument(
        "--keyword", type=str, help='Search keyword (e.g., "bakery", "ice cream shop")'
    )
    parser.add_argument(
        "--business-type",
        type=str,
        help='Predefined business type from config (e.g., "bakery", "ice_cream")',
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help="Language code (en, fr, it, es, de, etc.)",
    )
    parser.add_argument(
        "--country-code",
        type=str,
        help="ISO country code for phone parsing (DE, IT, ES, etc.)",
    )
    parser.add_argument(
        "--output-subdir",
        type=str,
        help="Optional output subdirectory under data/leads (e.g., Spain, Netherlands)",
    )
    parser.add_argument("--radius", type=int, help="Search radius in km (optional)")
    parser.add_argument(
        "--max-results", type=int, help="Maximum number of results to scrape"
    )
    parser.add_argument(
        "--find-emails",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable email extraction from websites (slower when enabled)",
    )
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable headless browser mode",
    )
    parser.add_argument(
        "--vpn-rotation",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable VPN usage and rotation logic (requires NordVPN CLI)",
    )
    parser.add_argument(
        "--vpn-interval", type=int, help="VPN rotation interval in number of scrapes"
    )
    parser.add_argument("--stats", type=str, help="Show statistics for a CSV file")

    args = parser.parse_args()

    # Load configuration
    config = load_config()
    logger = setup_logging()

    # Show statistics mode
    if args.stats:
        csv_handler = CSVHandler(config, logger)
        stats = csv_handler.get_statistics(args.stats)

        if stats:
            display_statistics_table(stats, title=f"Statistics for: {args.stats}")
            console.print()

        return

    # Validate required arguments for scraping
    if not args.city:
        console.print("[red]Error: --city is required for scraping[/red]")
        parser.print_help()
        sys.exit(1)

    if not args.keyword and not args.business_type:
        console.print(
            "[red]Error: Either --keyword or --business-type is required[/red]"
        )
        parser.print_help()
        sys.exit(1)

    # Determine keyword
    keyword = args.keyword
    if args.business_type:
        keywords_dict = load_keywords()
        keyword = get_keyword_from_type(
            args.business_type, args.language, keywords_dict
        )
        logger.info(
            f"Using keyword '{keyword}' for business type '{args.business_type}'"
        )

    # Override config with command line arguments
    if args.find_emails is not None:
        config["scraper"]["find_emails"] = args.find_emails

    if args.headless is not None:
        config["scraper"]["headless"] = args.headless

    if args.vpn_rotation is not None:
        config["vpn"]["enabled"] = args.vpn_rotation

    if args.vpn_interval:
        config["vpn"]["rotation_interval"] = args.vpn_interval

    effective_find_emails = config.get("scraper", {}).get("find_emails", False)
    effective_headless = config.get("scraper", {}).get("headless", False)
    effective_vpn = config.get("vpn", {}).get("enabled", False)
    effective_vpn_interval = config.get("vpn", {}).get("rotation_interval", 50)
    stable_country_mode = config.get("vpn", {}).get("stable_country_mode", True)
    event_rotation_enabled = config.get("vpn", {}).get("event_rotation_enabled", True)
    vpn_mode = (
        "Stable Country + Event Rotation"
        if stable_country_mode
        else "Interval Rotation"
    )

    # Print configuration
    console.print(
        "\n[bold cyan]╔═══════════════════════════════════════════╗[/bold cyan]"
    )
    console.print("[bold cyan]║   Google Maps Lead Scraper v1.0         ║[/bold cyan]")
    console.print(
        "[bold cyan]╚═══════════════════════════════════════════╝[/bold cyan]\n"
    )

    console.print(f"[yellow]City:[/yellow] {args.city}")
    console.print(f"[yellow]Keyword:[/yellow] {keyword}")
    console.print(f"[yellow]Language:[/yellow] {args.language}")
    console.print(
        f"[yellow]Find Emails:[/yellow] {'Yes (slower)' if effective_find_emails else 'No'}"
    )
    console.print(f"[yellow]Headless:[/yellow] {'Yes' if effective_headless else 'No'}")
    console.print(
        f"[yellow]Max Results:[/yellow] {args.max_results or config.get('scraper', {}).get('max_results_per_search', 100)}"
    )
    console.print(f"[yellow]VPN:[/yellow] {'Enabled' if effective_vpn else 'Disabled'}")
    if args.output_subdir:
        console.print(
            f"[yellow]Output Folder:[/yellow] data/leads/{args.output_subdir}"
        )
    if effective_vpn:
        console.print(f"[yellow]VPN Mode:[/yellow] {vpn_mode}")
        if not stable_country_mode:
            console.print(
                f"[yellow]VPN Interval:[/yellow] Every {effective_vpn_interval} scrapes"
            )
        console.print(
            f"[yellow]Event Rotation:[/yellow] {'Enabled' if event_rotation_enabled else 'Disabled'}"
        )
    console.print()

    # Initialize scraper
    scraper = GoogleMapsScraper(config, logger)

    # Handle SIGTERM (kill during batch runs) — save partial results
    def _sigterm_handler(signum, frame):
        console.print(
            "\n[yellow]Received SIGTERM signal, saving partial results...[/yellow]"
        )
        logger.warning("SIGTERM received, saving partial results")
        if scraper.businesses:
            csv_file = scraper.save_to_csv(
                keyword, args.city, output_subdir=args.output_subdir
            )
            console.print(f"[cyan]Partial results saved to:[/cyan] {csv_file}")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _sigterm_handler)

    try:
        # Run scraping
        businesses = scraper.scrape(
            city=args.city,
            keyword=keyword,
            language=args.language,
            country_code=args.country_code,
            radius=args.radius,
            max_results=args.max_results,
        )

        if businesses:
            # Save to CSV
            csv_file = scraper.save_to_csv(
                keyword, args.city, output_subdir=args.output_subdir
            )

            if csv_file:
                # Show statistics
                csv_handler = CSVHandler(config, logger)
                stats = csv_handler.get_statistics(csv_file)

                console.print(
                    "\n[bold green]╔═══════════════════════════════════════════╗[/bold green]"
                )
                console.print(
                    "[bold green]║          Scraping Complete!              ║[/bold green]"
                )
                console.print(
                    "[bold green]╚═══════════════════════════════════════════╝[/bold green]"
                )

                display_statistics_table(stats)
                console.print(f"\n[bold cyan]CSV File:[/bold cyan] {csv_file}\n")

                # Output simple count for batch script parsing
                print(f"SCRAPED_COUNT:{stats.get('total_businesses', 0)}")
        else:
            console.print("\n[yellow]No businesses found or scraped.[/yellow]\n")
            print("SCRAPED_COUNT:0")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Scraping interrupted by user[/yellow]")
        logger.info("Scraping interrupted by user")

        # Save partial results if any
        if scraper.businesses:
            csv_file = scraper.save_to_csv(
                keyword, args.city, output_subdir=args.output_subdir
            )
            console.print(f"\n[cyan]Partial results saved to:[/cyan] {csv_file}\n")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}\n")
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
