#!/usr/bin/env python3
"""
Domain Scraper - Extract contact information from a list of domains/websites

Usage:
    python scrape_domains.py domains.txt
    python scrape_domains.py domains.txt --output contacts.csv
    
Input file format (domains.txt):
    example.com
    https://bakery.fr
    www.chocolatier.it
    shop.example.de
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from src.email_finder import EmailFinder
from src.utils import setup_logging, load_config, extract_emails, extract_phone_numbers
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

console = Console()

def normalize_url(domain):
    """Normalize domain to full URL"""
    domain = domain.strip()
    
    # Remove any trailing slashes
    domain = domain.rstrip('/')
    
    # Add https:// if no protocol
    if not domain.startswith(('http://', 'https://')):
        domain = 'https://' + domain
    
    return domain

def load_domains(filepath):
    """Load domains from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Normalize all domains
    domains = [normalize_url(d) for d in domains]
    
    return domains

def extract_company_info(url, soup, logger):
    """Extract company name and other info from webpage"""
    info = {
        'company_name': None,
        'description': None,
    }
    
    try:
        # Try to get company name from various sources
        # 1. Page title
        if soup.title and soup.title.string:
            info['company_name'] = soup.title.string.strip()
        
        # 2. og:site_name meta tag
        og_site_name = soup.find('meta', property='og:site_name')
        if og_site_name and og_site_name.get('content'):
            info['company_name'] = og_site_name['content'].strip()
        
        # 3. h1 tag
        if not info['company_name']:
            h1 = soup.find('h1')
            if h1:
                info['company_name'] = h1.get_text().strip()
        
        # Get description
        description_meta = soup.find('meta', attrs={'name': 'description'})
        if description_meta and description_meta.get('content'):
            info['description'] = description_meta['content'].strip()[:200]
        
    except Exception as e:
        logger.debug(f"Error extracting company info: {e}")
    
    return info

def scrape_domain(url, email_finder, logger):
    """Scrape contact information from a single domain
    
    Args:
        url: Website URL to scrape
        email_finder: Shared EmailFinder instance (reuses session)
        logger: Logger instance
    """
    result = {
        'website': url,
        'company_name': None,
        'emails': [],
        'phones': [],
        'address': None,
        'social_media': {},
        'description': None,
        'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    try:
        # Get domain for logging
        domain = urlparse(url).netloc
        logger.info(f"Scraping {domain}...")
        
        # Use email finder (checks multiple pages including homepage)
        # EmailFinder already fetches the homepage, so we reuse its session
        # to also get company info and phone numbers
        emails = email_finder.find_emails_from_website(url)
        result['emails'] = emails
        
        # Fetch homepage for company info, phones, address, social links
        # Use the email_finder's session (already has retry logic + proper UA)
        try:
            response = email_finder.session.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract company info
                company_info = extract_company_info(url, soup, logger)
                result['company_name'] = company_info['company_name']
                result['description'] = company_info['description']
                
                # Extract phone numbers
                page_text = soup.get_text()
                
                # Detect country from domain TLD
                country_code = 'US'
                tld = urlparse(url).netloc.split('.')[-1].upper()
                country_map = {
                    'PL': 'PL', 'FR': 'FR', 'DE': 'DE', 'IT': 'IT', 
                    'ES': 'ES', 'UK': 'GB', 'PT': 'PT', 'NL': 'NL',
                    'BE': 'BE', 'CH': 'CH', 'AT': 'AT',
                }
                country_code = country_map.get(tld, 'US')
                
                phones = extract_phone_numbers(page_text, country_code)
                result['phones'] = phones
                
                # Look for address (common patterns)
                address_keywords = ['address:', 'adres:', 'adresse:', 'indirizzo:', 'dirección:']
                for keyword in address_keywords:
                    if keyword.lower() in page_text.lower():
                        idx = page_text.lower().find(keyword.lower())
                        if idx != -1:
                            address_snippet = page_text[idx:idx+200].split('\n')[0]
                            result['address'] = address_snippet.strip()
                            break
                
                # Extract social media links
                social_platforms = {
                    'facebook': ['facebook.com', 'fb.com'],
                    'instagram': ['instagram.com'],
                    'linkedin': ['linkedin.com'],
                    'twitter': ['twitter.com', 'x.com'],
                }
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    for platform, domains in social_platforms.items():
                        if any(d in href for d in domains):
                            result['social_media'][platform] = href
                            break
        
        except requests.RequestException as e:
            logger.warning(f"Could not fetch {url}: {str(e)[:50]}")
        
        # Log results
        if result['emails'] or result['phones']:
            logger.info(f"Found {domain}: {len(result['emails'])} email(s), {len(result['phones'])} phone(s)")
        else:
            logger.warning(f"No contact info for {domain}")
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)[:100]}")
    
    return result

def export_results(results, output_file):
    """Export results to CSV"""
    # Prepare data for CSV
    rows = []
    for result in results:
        row = {
            'company_name': result['company_name'],
            'website': result['website'],
            'email': result['emails'][0] if result['emails'] else None,
            'all_emails': ', '.join(result['emails']) if result['emails'] else None,
            'phone': result['phones'][0] if result['phones'] else None,
            'all_phones': ', '.join(result['phones']) if result['phones'] else None,
            'address': result['address'],
            'description': result['description'],
            'facebook': result['social_media'].get('facebook'),
            'instagram': result['social_media'].get('instagram'),
            'linkedin': result['social_media'].get('linkedin'),
            'twitter': result['social_media'].get('twitter'),
            'scraped_date': result['scraped_date'],
        }
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Export to CSV
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    return output_path

def main():
    parser = argparse.ArgumentParser(
        description='Scrape contact information from a list of domains',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python scrape_domains.py domains.txt
  
  # Custom output file
  python scrape_domains.py domains.txt --output my_contacts.csv
  
  # With delay between requests
  python scrape_domains.py domains.txt --delay 3

Input file format (domains.txt):
  example.com
  https://bakery.fr
  www.chocolatier.it
        """
    )
    
    parser.add_argument('domains_file', help='Text file with domains (one per line)')
    parser.add_argument('--output', '-o', default='domain_contacts.csv', help='Output CSV file')
    parser.add_argument('--delay', '-d', type=int, default=2, help='Delay between requests (seconds)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.domains_file).exists():
        console.print(f"[red]Error: File '{args.domains_file}' not found![/red]")
        sys.exit(1)
    
    # Load configuration and logger
    config = load_config()
    logger = setup_logging()
    
    # Load domains
    console.print(f"\n[cyan]Loading domains from {args.domains_file}...[/cyan]")
    domains = load_domains(args.domains_file)
    
    console.print(f"[green]Found {len(domains)} domain(s) to scrape[/green]\n")
    
    # Create a single shared EmailFinder (reuses HTTP session across all domains)
    email_finder = EmailFinder(config, logger)
    
    # Scrape each domain
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Scraping domains...", total=len(domains))
        
        for domain in domains:
            result = scrape_domain(domain, email_finder, logger)
            results.append(result)
            
            progress.update(task, advance=1)
            
            # Delay between requests
            if args.delay > 0:
                time.sleep(args.delay)
    
    # Export results
    console.print(f"\n[yellow]Exporting results...[/yellow]")
    output_path = export_results(results, args.output)
    
    # Show statistics
    total = len(results)
    with_email = sum(1 for r in results if r['emails'])
    with_phone = sum(1 for r in results if r['phones'])
    with_company = sum(1 for r in results if r['company_name'])
    
    console.print("\n[bold green]╔═══════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║          Scraping Complete!              ║[/bold green]")
    console.print("[bold green]╚═══════════════════════════════════════════╝[/bold green]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Domains", str(total))
    table.add_row("With Email", f"{with_email} ({round(with_email/total*100, 1) if total else 0}%)")
    table.add_row("With Phone", f"{with_phone} ({round(with_phone/total*100, 1) if total else 0}%)")
    table.add_row("With Company Name", f"{with_company} ({round(with_company/total*100, 1) if total else 0}%)")
    
    console.print(table)
    console.print(f"\n[bold cyan]Output File:[/bold cyan] {output_path}\n")

if __name__ == '__main__':
    main()
