#!/usr/bin/env python3
"""
Deduplicate and merge multiple CSV files from lead scraping
"""

import argparse
import glob
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.csv_handler import CSVHandler
from src.utils import setup_logging, load_config
from rich.console import Console

console = Console()

def main():
    parser = argparse.ArgumentParser(
        description='Merge and deduplicate CSV files from lead scraping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge all CSV files in data/leads/
  python scripts/deduplicate.py --input "data/leads/*.csv" --output merged_leads.csv
  
  # Merge specific files
  python scripts/deduplicate.py --input file1.csv file2.csv file3.csv --output combined.csv
  
  # Use glob pattern
  python scripts/deduplicate.py --input "data/leads/Paris_*.csv" --output paris_all.csv
        """
    )
    
    parser.add_argument('--input', nargs='+', required=True, help='Input CSV files or glob pattern')
    parser.add_argument('--output', default='merged_leads.csv', help='Output filename')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    logger = setup_logging()
    
    # Expand glob patterns
    csv_files = []
    for pattern in args.input:
        matched_files = glob.glob(pattern)
        if matched_files:
            csv_files.extend(matched_files)
        else:
            # If not a pattern, treat as direct file path
            csv_files.append(pattern)
    
    # Remove duplicates in file list
    csv_files = list(set(csv_files))
    
    if not csv_files:
        console.print("[red]Error: No CSV files found matching the pattern[/red]")
        sys.exit(1)
    
    console.print(f"\n[cyan]Found {len(csv_files)} CSV file(s) to merge:[/cyan]")
    for f in csv_files:
        console.print(f"  - {f}")
    console.print()
    
    # Merge and deduplicate
    csv_handler = CSVHandler(config, logger)
    
    try:
        output_file = csv_handler.merge_csv_files(csv_files, args.output)
        
        if output_file:
            # Show statistics
            stats = csv_handler.get_statistics(output_file)
            
            console.print("\n[bold green]╔═══════════════════════════════════════════╗[/bold green]")
            console.print("[bold green]║       Merge & Deduplication Complete!    ║[/bold green]")
            console.print("[bold green]╚═══════════════════════════════════════════╝[/bold green]\n")
            
            console.print(f"[yellow]Total Businesses:[/yellow] {stats.get('total_businesses', 0)}")
            console.print(f"[yellow]With Phone:[/yellow] {stats.get('with_phone', 0)} ({stats.get('phone_percentage', 0)}%)")
            console.print(f"[yellow]With Email:[/yellow] {stats.get('with_email', 0)} ({stats.get('email_percentage', 0)}%)")
            console.print(f"[yellow]With Website:[/yellow] {stats.get('with_website', 0)} ({stats.get('website_percentage', 0)}%)")
            console.print(f"\n[bold cyan]Output File:[/bold cyan] {output_file}\n")
    
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}\n")
        logger.error(f"Error during merge: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
