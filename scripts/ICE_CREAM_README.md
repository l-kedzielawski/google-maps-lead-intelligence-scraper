# European Artisan Ice Cream Scraper - COMPREHENSIVE EDITION

## Overview

This script scrapes artisanal ice cream businesses, gelato producers, ice cream manufacturers, and craft ice cream shops across **639 cities (50K+ population)** in **8 European countries**.

**🎯 SCALE: 2,556 total searches (639 cities × 4 keywords each)**

## Countries Covered

- 🇩🇪 **Germany** (191 cities - 50K+ population)
- 🇮🇹 **Italy** (140 cities - 50K+ population)
- 🇪🇸 **Spain** (120 cities - 50K+ population)
- 🇳🇱 **Netherlands** (58 cities - 50K+ population)
- 🇵🇹 **Portugal** (57 cities - 50K+ population)
- 🇧🇪 **Belgium** (37 cities - 50K+ population)
- 🇨🇭 **Switzerland** (26 cities - 50K+ population)
- 🇦🇹 **Austria** (10 cities - 50K+ population)

**Total: 639 cities (all with 50,000+ population)**

## Configuration

**MAX_RESULTS: 500 businesses per search** (increased from 100)

This means:
- Up to **500 ice cream businesses per city per keyword**
- Maximum potential: **1.278 million business records** (2,556 searches × 500 results)
- Realistic expectation: **200,000-400,000 unique ice cream businesses**

## Search Terms by Language

Each city is searched with 4 different keywords in the local language:

### German (DE, AT, CH-German)
- `handwerkliche eisdiele` (artisanal ice cream shop)
- `gelato hersteller` (gelato producer)
- `eishersteller` (ice cream manufacturer)
- `manufaktur eis` / `eismanufaktur` (craft ice cream)

### Italian (IT)
- `gelateria artigianale` (artisanal gelato shop)
- `produttore gelato artigianale` (artisan gelato producer)
- `produttore di gelato` (ice cream producer)
- `laboratorio gelato` (gelato laboratory/workshop)

### Spanish (ES)
- `heladería artesanal` (artisanal ice cream shop)
- `productor de helado artesanal` (artisan ice cream producer)
- `fabricante de helados` (ice cream manufacturer)
- `helado artesanal` (artisan ice cream)

### Portuguese (PT)
- `gelado artesanal` (artisan ice cream)
- `produtor de gelado artesanal` (artisan ice cream producer)
- `fabricante de gelados` (ice cream manufacturer)
- `gelados artesanais` (artisan ice creams)

### Dutch (NL, BE-Flemish)
- `ambachtelijke ijssalon` (artisan ice cream parlor)
- `ambachtelijke ijsmaker` (artisan ice cream maker)
- `ijsproducent` (ice cream producer)
- `artisanale ijsmaker` (artisanal ice cream maker)

### French (CH-French, BE-French)
- `glacier artisanal` (artisan ice cream shop)
- `producteur de glace` (ice cream producer)
- `producteur de glace artisanale` (artisan ice cream producer)

## Usage

### Run Full Scrape (All 150 Cities × 4 Keywords = 600 Searches)

```bash
./scripts/ice_cream_scraper.sh
```

### Configuration

Edit the script to modify these settings:

```bash
MAX_RESULTS=100              # Max results per search
FIND_EMAILS="--find-emails"  # Enable/disable email extraction
```

## Features

✅ **Smart Skip Logic** - Automatically skips cities/keywords that already have results (>1 entry)  
✅ **Progress Tracking** - Saves progress log to `data/ice_cream_progress.log`  
✅ **Resume Capability** - Can safely restart if interrupted  
✅ **Multi-language** - Searches in 6 languages (DE, IT, ES, PT, NL, FR)  
✅ **Email Extraction** - Crawls business websites for emails  
✅ **Color-coded Output** - Easy to read progress and status  

## Output

Results are saved to `data/leads/` as CSV files:

```
data/leads/Berlin_handwerkliche_eisdiele_20260203_140532.csv
data/leads/Roma_gelateria_artigianale_20260203_141205.csv
data/leads/Madrid_heladería_artesanal_20260203_142030.csv
...
```

Each CSV contains:
- Business name
- Phone number (E.164 format)
- Email address
- Full address
- Website
- Google Maps rating
- Review count
- GPS coordinates
- Google Maps URL

## Expected Results

**Estimated Total Searches:** 600 (150 cities × 4 keywords)

**Time Estimate:**
- Without email extraction: ~5-8 hours
- With email extraction: ~12-20 hours (recommended for better data quality)

**Expected Leads:**
- Conservative: 5,000-10,000 businesses
- Realistic: 10,000-20,000 businesses
- Optimistic: 20,000-30,000 businesses

*Note: Actual results depend on business density in each city*

## Progress Monitoring

Monitor progress in real-time:

```bash
tail -f data/ice_cream_progress.log
```

Check statistics:

```bash
# Count total entries
wc -l data/ice_cream_progress.log

# Count successes
grep SUCCESS data/ice_cream_progress.log | wc -l

# Count skipped
grep SKIPPED data/ice_cream_progress.log | wc -l

# Count failures
grep FAILED data/ice_cream_progress.log | wc -l
```

## Cities List

<details>
<summary><b>Germany (30 cities)</b></summary>

Berlin, Hamburg, München, Köln, Frankfurt am Main, Stuttgart, Düsseldorf, Leipzig, Dortmund, Essen, Bremen, Dresden, Hannover, Nürnberg, Duisburg, Bochum, Wuppertal, Bielefeld, Bonn, Münster, Karlsruhe, Mannheim, Augsburg, Wiesbaden, Mönchengladbach, Gelsenkirchen, Braunschweig, Chemnitz, Kiel, Aachen
</details>

<details>
<summary><b>Austria (10 cities)</b></summary>

Wien, Graz, Linz, Salzburg, Innsbruck, Klagenfurt, Villach, Wels, St. Pölten, Dornbirn
</details>

<details>
<summary><b>Italy (30 cities)</b></summary>

Roma, Milano, Napoli, Torino, Palermo, Genova, Bologna, Firenze, Bari, Catania, Venezia, Verona, Messina, Padova, Trieste, Brescia, Taranto, Prato, Parma, Modena, Reggio Calabria, Reggio Emilia, Perugia, Livorno, Ravenna, Cagliari, Foggia, Rimini, Salerno, Ferrara
</details>

<details>
<summary><b>Spain (25 cities)</b></summary>

Madrid, Barcelona, Valencia, Sevilla, Zaragoza, Málaga, Murcia, Palma de Mallorca, Las Palmas de Gran Canaria, Bilbao, Alicante, Córdoba, Valladolid, Vigo, Gijón, Hospitalet de Llobregat, A Coruña, Vitoria-Gasteiz, Granada, Elche, Oviedo, Badalona, Cartagena, Terrassa, Jerez de la Frontera
</details>

<details>
<summary><b>Switzerland (15 cities)</b></summary>

Zürich, Genève, Basel, Bern, Lausanne, Winterthur, Luzern, St. Gallen, Lugano, Biel/Bienne, Thun, Köniz, La Chaux-de-Fonds, Fribourg, Schaffhausen
</details>

<details>
<summary><b>Portugal (15 cities)</b></summary>

Lisboa, Porto, Vila Nova de Gaia, Amadora, Braga, Setúbal, Coimbra, Queluz, Funchal, Cacém, Vila Franca de Xira, Loures, Évora, Rio de Mouro, Odivelas
</details>

<details>
<summary><b>Netherlands (15 cities)</b></summary>

Amsterdam, Rotterdam, Den Haag, Utrecht, Eindhoven, Groningen, Tilburg, Almere, Breda, Nijmegen, Enschede, Haarlem, Arnhem, Zaanstad, Amersfoort
</details>

<details>
<summary><b>Belgium (10 cities)</b></summary>

Bruxelles, Antwerpen, Gent, Charleroi, Liège, Brugge, Namur, Leuven, Mons, Aalst
</details>

## Troubleshooting

### Script won't run
```bash
chmod +x scripts/ice_cream_scraper.sh
```

### CAPTCHA issues
The script will pause automatically if Google detects scraping. Solve the CAPTCHA manually when the browser opens.

### Too slow
Disable email extraction by editing the script:
```bash
FIND_EMAILS=""  # Remove --find-emails flag
```

### Resume after interruption
Just run the script again. It will automatically skip cities that have already been scraped.

## Legal Notice

This tool is for educational and B2B lead generation purposes only. Please:
- Respect Google's Terms of Service
- Don't scrape more than 5,000 businesses per day
- Use appropriate delays between requests
- Comply with GDPR and local data protection laws
- Don't use data for spam or automated contact

## Support

For issues or questions, check the main README or INSTRUCTIONS.md in the project root.
