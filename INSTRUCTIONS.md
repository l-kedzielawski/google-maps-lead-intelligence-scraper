# Google Maps Lead Scraper - Detailed Instructions

## Table of Contents

1. [Installation Guide](#installation-guide)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Batch Processing](#batch-processing)
5. [VPN Rotation](#vpn-rotation)
6. [Domain Scraper](#domain-scraper)
7. [Troubleshooting](#troubleshooting)
8. [Performance Optimization](#performance-optimization)
9. [Best Practices](#best-practices)

---

## Installation Guide

### Step 1: System Requirements

Ensure you have:
- Python 3.9 or higher installed
- pip (Python package manager)
- Git (to clone the repository)
- 500MB free disk space for Playwright

### Step 2: Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd google-maps-lead-scraper

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright Chromium browser
playwright install chromium
```

### Step 4: Verify Installation

```bash
# Test that everything works
python show_keywords.py
```

You should see a list of available business types and their translations.

---

## Basic Usage

### Single Search - Quick Examples

#### Example 1: Find pastry shops in Warsaw
```bash
python main.py --city "Warsaw" --business-type "pastry_shop" --language "pl"
```

**What this does:**
- Searches for "cukiernia" (Polish for pastry shop) in Warsaw
- Extracts phone numbers, emails, addresses
- Saves results to `data/leads/Warsaw_pastry_shop_YYYYMMDD_HHMMSS.csv`

#### Example 2: Find chocolate makers in Paris
```bash
python main.py --city "Paris" --business-type "chocolate_maker" --language "fr" --find-emails
```

**What this does:**
- Searches for "chocolatier" in Paris
- Extracts phone numbers, emails, addresses
- **Visits each business website** to find emails (slower but better coverage)

#### Example 3: Custom keyword search
```bash
python main.py --city "Rome" --keyword "pizza" --language "it" --max-results 20
```

**What this does:**
- Searches for "pizza" in Rome using Italian Google Maps
- Limits to 20 results
- Does not use predefined business type translations

### Understanding the Output

After scraping completes, you'll see:

```
╔═══════════════════════════════════════════╗
║          Scraping Complete!              ║
╚═══════════════════════════════════════════╝

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Metric           ┃ Value              ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Total Businesses │ 54                 │
│ With Phone       │ 54 (100.0%)        │
│ With Email       │ 11 (20.4%)         │
│ With Website     │ 52 (96.3%)         │
└──────────────────┴────────────────────┘

CSV File: data/leads/Warsaw_pastry_shop_20231215_120000.csv

SCRAPED_COUNT:54
```

### Viewing Statistics for Existing CSV

```bash
python main.py --stats data/leads/Warsaw_pastry_shop_20231215_120000.csv
```

This shows statistics for previously scraped data without re-scraping.

---

## Advanced Features

### Headless Mode

Run the scraper in the background without a visible browser:

```bash
python main.py --city "Berlin" --keyword "bakery" --headless
```

**Benefits:**
- Faster execution
- Uses less system resources
- Can run on servers without GUI

**Important:** If CAPTCHA is detected in headless mode, the browser will automatically open for you to solve it.

### Email Extraction from Websites

There are two modes:

#### Mode 1: Google Maps Only (Default)
```bash
python main.py --city "Madrid" --keyword "cafe"
```
- **Speed:** Fast (~2 seconds per business)
- **Email coverage:** 5-10% (only emails visible on Google Maps)
- **Best for:** Quick searches, large volumes

#### Mode 2: Website Crawling (Recommended)
```bash
python main.py --city "Madrid" --keyword "cafe" --find-emails
```
- **Speed:** Slower (~10-30 seconds per business)
- **Email coverage:** 50-70% (visits business websites)
- **Best for:** Quality leads, B2B outreach

### Custom Delays

Adjust delays between requests to avoid detection:

```bash
# Edit config/settings.yaml
scraper:
  delay_min: 3  # Slower, less likely to be detected
  delay_max: 7
```

### Selective Data Export

Customize what data to export:

```bash
# Edit config/settings.yaml
export:
  include_coordinates: false  # Don't save GPS coordinates
  deduplicate: true          # Remove duplicates
```

---

## Batch Processing

### Using the Batch Script

The `scripts/ice_cream_scraper.sh` script automates large multi-city scraping with resume support.

#### Basic Usage

```bash
# Scrape Poland (5 cities, 5 business types each)
./scripts/ice_cream_scraper.sh

# Scrape France with 100 results per search
./scripts/ice_cream_scraper.sh --start-from 300

# Scrape all supported countries
./scripts/scrape_germany_food.sh
```

#### What the Script Does

1. **Scrapes multiple business types** in each city:
   - Pastry shops
   - Spice wholesalers
   - Baking wholesalers
   - HORECA suppliers
   - Ice cream shops

2. **Automatically deduplicates** results across all searches

3. **Merges all results** into a single CSV file

#### Expected Results

- **Poland (5 cities × 5 types × 50 results):** ~900-1,100 unique leads
- **France (5 cities × 4 types × 50 results):** ~700-900 unique leads
- **All countries:** ~4,000-5,000 unique leads

### Creating Custom Batch Scripts

Create your own batch script for specific needs:

```bash
#!/bin/bash

# Your custom batch script
CITIES=("London" "Manchester" "Birmingham")
MAX_RESULTS=50

for city in "${CITIES[@]}"; do
    echo "Scraping $city..."
    python main.py --city "$city" --keyword "restaurant" --language "en" --max-results $MAX_RESULTS
done

echo "Done!"
```

Save as `my_batch_script.sh` and make executable:
```bash
chmod +x my_batch_script.sh
./my_batch_script.sh
```

---

## VPN Rotation

### Why Use VPN Rotation?

When scraping large volumes of data (1000+ businesses), Google may temporarily block your IP. VPN rotation changes your IP address automatically to avoid this.

### Setting Up NordVPN

#### 1. Install NordVPN CLI

**Linux (Ubuntu/Debian):**
```bash
sh <(curl -sSf https://downloads.nordcdn.com/apps/linux/install.sh)
```

**macOS:**
```bash
brew install nordvpn
```

**Windows (WSL):**
```bash
apt-get install nordvpn
```

#### 2. Login to NordVPN

```bash
nordvpn login
```

#### 3. Test Connection

```bash
nordvpn connect
nordvpn status
nordvpn disconnect
```

### Using VPN Rotation with the Scraper

#### Method 1: Command Line

```bash
python main.py --city "Paris" --keyword "cafe" --vpn-rotation --vpn-interval 50
```

This will:
1. Connect to a random NordVPN server
2. Scrape 50 businesses
3. Rotate to a new server
4. Continue scraping

#### Method 2: Configuration File

Edit `config/settings.yaml`:

```yaml
vpn:
  enabled: true
  rotation_interval: 50  # Rotate every 50 scrapes
```

Now just run:
```bash
python main.py --city "Paris" --keyword "cafe"
```

### VPN Rotation Tips

- **Start with 50-100 scrapes per rotation** - Adjust based on your needs
- **Use batch script with VPN:** The batch script already has VPN enabled by default
- **Monitor for blocks:** If you see timeouts or CAPTCHAs frequently, reduce the rotation interval

---

## Domain Scraper

### Overview

The domain scraper (`scrape_domains.py`) extracts contact information from a list of websites, without using Google Maps.

### When to Use Domain Scraper

- You already have a list of competitor websites
- You want to supplement Google Maps results
- You're scraping from sources other than Google Maps

### Basic Usage

#### Step 1: Create Input File

Create `domains.txt`:

```text
example.com
https://bakery.fr
www.chocolatier.it
shop.example.de
```

#### Step 2: Run Scraper

```bash
# Basic usage
python scrape_domains.py domains.txt

# Custom output file
python scrape_domains.py domains.txt --output my_contacts.csv

# With delay between requests
python scrape_domains.py domains.txt --delay 3
```

### Domain Scraper Output

The domain scraper provides:
- Company name
- Website URL
- Email addresses (up to 5 per site)
- Phone numbers
- Address (if available)
- Social media links (Facebook, Instagram, LinkedIn, Twitter)
- Website description

### Example Output

```text
╔═══════════════════════════════════════════╗
║          Scraping Complete!              ║
╚═══════════════════════════════════════════╝

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Metric           ┃ Value              ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Total Domains    │ 10                 │
│ With Email       │ 7 (70.0%)          │
│ With Phone       │ 6 (60.0%)          │
│ With Company Name│ 9 (90.0%)          │
└──────────────────┴────────────────────┘
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "No results found"

**Symptoms:**
```
❌ FAIL: Could not find result elements
No businesses found or scraped.
```

**Possible Causes:**
1. City name is misspelled
2. Business type doesn't exist in that city
3. Google Maps changed their selectors

**Solutions:**
- Verify city spelling: Try `"Warsaw"` instead of `"Warsaw "`
- Check business type: `python show_keywords.py`
- Try with `--keyword` instead of `--business-type`
- Example: `python main.py --city "Warsaw" --keyword "test"`

#### Issue 2: CAPTCHA detected frequently

**Symptoms:**
```
⚠️  CAPTCHA DETECTED!
Please solve the CAPTCHA in the browser...
```

**Solutions:**
1. **Use VPN rotation:**
   ```bash
   python main.py --city "Paris" --keyword "cafe" --vpn-rotation
   ```

2. **Increase delays** (edit `config/settings.yaml`):
   ```yaml
   scraper:
     delay_min: 5
     delay_max: 10
   ```

3. **Reduce scraping volume:**
   - Don't scrape more than 500-1000 businesses per session
   - Take breaks between sessions

#### Issue 3: Phone numbers not extracting

**Symptoms:**
```
With Phone: 5 (10.0%)  # Very low percentage
```

**Possible Causes:**
1. Wrong language/country combination
2. Phone numbers not visible on Google Maps
3. Phone number format not recognized

**Solutions:**
- Verify language code: `--language "pl"` for Poland
- Check if phone numbers are visible on Google Maps manually
- Use `--find-emails` to get emails from websites instead

#### Issue 4: Low email extraction rate

**Symptoms:**
```
With Email: 3 (5.6%)  # Without --find-emails
With Email: 27 (50.0%)  # With --find-emails
```

**Solutions:**
- Add `--find-emails` flag to crawl websites
- Understand this is a trade-off: Speed vs completeness
- Email extraction from websites is never 100%

#### Issue 5: Playwright browser not found

**Symptoms:**
```
Error: Executable doesn't exist at /path/to/chromium
```

**Solution:**
```bash
playwright install chromium
```

#### Issue 6: Import errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'playwright'
```

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Issue 7: VPN not connecting

**Symptoms:**
```
Error: Could not connect to VPN
```

**Solutions:**
1. Check NordVPN CLI installation: `nordvpn --version`
2. Login to NordVPN: `nordvpn login`
3. Test manually: `nordvpn connect && nordvpn status`
4. Check NordVPN subscription is active

### Getting Debug Information

The scraper has built-in logging. Check the console output for:

- `✓ SUCCESS:` - Operations that worked
- `❌ FAIL:` - Operations that failed
- `⚠️ WARNING:` - Potential issues

If you encounter issues, check:
1. Which extraction method worked (JavaScript, DOM selector, button clicks)
2. How many results were found
3. Any error messages

---

## Performance Optimization

### Speed Comparison

| Configuration | Speed | Email Coverage | Best For |
|--------------|-------|----------------|----------|
| **Fastest** | ~1-2s per business | 5-10% | Large volumes, quick searches |
| **Balanced** | ~3-5s per business | 20-30% | General use |
| **Quality** | ~10-30s per business | 50-70% | B2B outreach, quality leads |

### Optimization Tips

#### 1. Use Headless Mode
```bash
python main.py --city "Paris" --keyword "cafe" --headless
```
Saves ~20-30% time by not rendering graphics.

#### 2. Adjust Batch Size
For large volumes:
```bash
# Smaller batches, more sessions
./scripts/ice_cream_scraper.sh

# VS larger batches, fewer sessions (slower per business but less overhead)
./scripts/ice_cream_scraper.sh --start-from 300
```

#### 3. Skip Email Extraction for Testing
```bash
# Quick test run
python main.py --city "Paris" --keyword "cafe" --max-results 10

# Full run with emails
python main.py --city "Paris" --keyword "cafe" --find-emails --max-results 100
```

#### 4. Use VPN Rotation Wisely
```bash
# Optimal: Rotate every 50-100 scrapes
python main.py --city "Paris" --keyword "cafe" --vpn-rotation --vpn-interval 50

# Avoid: Rotate too frequently (adds overhead)
python main.py --city "Paris" --keyword "cafe" --vpn-rotation --vpn-interval 5
```

#### 5. Parallel Processing (Advanced)

You can run multiple scrapers in parallel on different machines or containers. Each scraper will have its own data files.

### Expected Time Estimates

- **20 results:** 30-40 seconds (without emails), 3-5 minutes (with emails)
- **50 results:** 1-2 minutes (without emails), 8-12 minutes (with emails)
- **100 results:** 2-3 minutes (without emails), 15-25 minutes (with emails)
- **500 results:** 10-15 minutes (without emails), 1-2 hours (with emails)

---

## Best Practices

### 1. Start Small

Always test with a small batch first:
```bash
# Test with 10 results
python main.py --city "Warsaw" --business-type "pastry_shop" --language "pl" --max-results 10

# If successful, scale up
python main.py --city "Warsaw" --business-type "pastry_shop" --language "pl" --max-results 100
```

### 2. Use Appropriate Delays

For safety:
```yaml
# Production settings
scraper:
  delay_min: 3
  delay_max: 7
```

For speed (use with caution):
```yaml
# Fast settings
scraper:
  delay_min: 1
  delay_max: 3
```

### 3. Respect Google's Terms of Service

- Don't scrape more than 5,000 businesses per day
- Use delays between requests
- Don't use for spam or harassment
- Comply with GDPR and other privacy laws

### 4. Verify Data Quality

After scraping:
```bash
# View statistics
python main.py --stats data/leads/Warsaw_pastry_shop_20231215.csv

# Open CSV to check quality
# Look for:
# - Valid phone numbers (start with +48, +33, etc.)
# - Valid email formats
# - Complete addresses
```

### 5. Regular Data Cleanup

Use the deduplication script:
```bash
python scripts/deduplicate.py --input "data/leads/*.csv" --output "cleaned_leads.csv"
```

### 6. Backup Your Results

```bash
# Create backups of important results
cp data/leads/Warsaw_pastry_shop_20231215.csv backups/
```

### 7. Monitor for Issues

Watch for these signs:
- Frequent CAPTCHAs → Reduce scraping volume or use VPN
- Zero results → Check city name and business type
- Low phone/email coverage → Add `--find-emails` flag
- Timeouts → Increase delays or check internet connection

### 8. Combine Data Sources

For best results:
1. Use Google Maps scraper to find businesses
2. Use domain scraper to supplement with competitor lists
3. Merge and deduplicate results

---

## Appendix: Quick Reference

### Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--city` | City to search in | `--city "Warsaw"` |
| `--keyword` | Custom search keyword | `--keyword "bakery"` |
| `--business-type` | Predefined business type | `--business-type "pastry_shop"` |
| `language` | Language code | `--language "pl"` |
| `--max-results` | Max businesses to scrape | `--max-results 50` |
| `--find-emails` | Extract emails from websites | `--find-emails` |
| `--headless` | Run in background | `--headless` |
| `--vpn-rotation` | Enable VPN rotation | `--vpn-rotation` |
| `--vpn-interval` | VPN rotation interval | `--vpn-interval 50` |
| `--stats` | Show statistics for CSV | `--stats file.csv` |

### Language Codes

| Code | Language |
|------|----------|
| `pl` | Polish |
| `fr` | French |
| `de` | German |
| `it` | Italian |
| `es` | Spanish |
| `pt` | Portuguese |
| `en` | English |

### Example Commands

```bash
# Quick test (10 results, no emails)
python main.py --city "Paris" --keyword "cafe" --max-results 10

# Quality leads (100 results, with emails)
python main.py --city "Warsaw" --business-type "pastry_shop" --language "pl" --find-emails --max-results 100

# Large batch (with VPN)
python main.py --city "Rome" --business-type "chocolate_maker" --language "it" --find-emails --vpn-rotation --max-results 200

# Background processing
python main.py --city "Berlin" --keyword "bakery" --headless

# View statistics
python main.py --stats data/leads/Berlin_bakery_20231215.csv

# Batch processing
./scripts/scrape_germany_food.sh

# Domain scraping
python scrape_domains.py domains.txt --output contacts.csv
```

---

For additional help or issues, please refer to the main [README.md](README.md) or create an issue on GitHub.
