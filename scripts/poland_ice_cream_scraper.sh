#!/bin/bash

# ============================================
# POLAND ICE CREAM BATCH SCRAPER
# ============================================
# Scrapes major Polish cities for artisanal ice cream businesses
# using Polish keywords.
#
# Search Terms:
#   - Artisanal ice cream shop
#   - Ice cream producer
#   - Ice cream manufacturer
#   - Craft ice cream
#
# Features:
#   - Poland only (Polish keywords)
#   - Checks existing results and skips if > 1 result found
#   - Re-scrapes if <= 1 result or no data exists
#   - Progress tracking with resume capability
#   - Resume from specific scrape number with --start-from
#
# Usage:
#   ./scripts/poland_ice_cream_scraper.sh                  # Start from beginning
#   ./scripts/poland_ice_cream_scraper.sh --start-from 80  # Resume from scrape #80
# ============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
MAX_RESULTS=500
FIND_EMAILS="--find-emails"
START_FROM=1

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--start-from)
            START_FROM="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -s, --start-from NUM   Start from scrape number NUM (default: 1)"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                     # Start from beginning"
            echo "  $0 --start-from 80     # Resume from scrape #80"
            echo "  $0 -s 80               # Short form"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate START_FROM is a number
if ! [[ "$START_FROM" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}Error: --start-from must be a positive number${NC}"
    exit 1
fi

# Search keywords in Polish
# Format: "keyword|language"
declare -A SEARCH_TERMS=(
    ["artisanal_ice_cream_pl"]="lodziarnia rzemieślnicza|pl"
    ["ice_cream_producer_pl"]="producent lodów|pl"
    ["ice_cream_manufacturer_pl"]="wytwórnia lodów|pl"
    ["craft_ice_cream_pl"]="lody rzemieślnicze|pl"
)

SEARCH_TERM_KEYS=(
    "artisanal_ice_cream_pl"
    "ice_cream_producer_pl"
    "ice_cream_manufacturer_pl"
    "craft_ice_cream_pl"
)

# Poland cities (50K+ population)
# Format: "City|CountryCode"
POLAND_CITIES=(
    "Warszawa|pl" "Kraków|pl" "Łódź|pl" "Wrocław|pl" "Poznań|pl" "Gdańsk|pl" "Szczecin|pl" "Bydgoszcz|pl" "Lublin|pl" "Białystok|pl"
    "Katowice|pl" "Gdynia|pl" "Częstochowa|pl" "Radom|pl" "Sosnowiec|pl" "Toruń|pl" "Kielce|pl" "Rzeszów|pl" "Gliwice|pl" "Zabrze|pl"
    "Olsztyn|pl" "Bielsko-Biała|pl" "Bytom|pl" "Zielona Góra|pl" "Rybnik|pl" "Ruda Śląska|pl" "Tychy|pl" "Dąbrowa Górnicza|pl" "Płock|pl" "Elbląg|pl"
    "Opole|pl" "Gorzów Wielkopolski|pl" "Wałbrzych|pl" "Włocławek|pl" "Tarnów|pl" "Chorzów|pl" "Koszalin|pl" "Kalisz|pl" "Legnica|pl" "Grudziądz|pl"
    "Słupsk|pl" "Jaworzno|pl" "Jastrzębie-Zdrój|pl" "Nowy Sącz|pl" "Jelenia Góra|pl" "Siedlce|pl" "Mysłowice|pl" "Piła|pl" "Konin|pl" "Piotrków Trybunalski|pl"
    "Inowrocław|pl" "Lubin|pl" "Ostrów Wielkopolski|pl" "Suwałki|pl" "Stargard|pl" "Gniezno|pl" "Ostrołęka|pl" "Przemyśl|pl" "Pabianice|pl" "Tomaszów Mazowiecki|pl"
    "Chełm|pl" "Ełk|pl" "Leszno|pl" "Świdnica|pl" "Zamość|pl" "Bełchatów|pl" "Biała Podlaska|pl" "Zgierz|pl" "Tarnobrzeg|pl" "Puławy|pl"
    "Starachowice|pl" "Skierniewice|pl" "Nysa|pl" "Racibórz|pl" "Świnoujście|pl" "Kędzierzyn-Koźle|pl" "Mielec|pl" "Wejherowo|pl" "Siemianowice Śląskie|pl" "Piekary Śląskie|pl"
    "Żory|pl" "Pruszków|pl" "Ostrowiec Świętokrzyski|pl" "Głogów|pl"
)

ALL_CITIES=("${POLAND_CITIES[@]}")

# Check if running from scripts directory
if [ ! -f "../main.py" ] && [ ! -f "main.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/poland_ice_cream_scraper.sh${NC}"
    exit 1
fi

# If running from scripts directory, go to parent
if [ -f "../main.py" ]; then
    cd ..
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}            POLAND ICE CREAM BATCH SCRAPER               ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Country:${NC} Poland"
echo -e "${YELLOW}Language:${NC} Polish (pl)"
echo -e "${YELLOW}Cities:${NC} ${#ALL_CITIES[@]} cities"
echo -e "${YELLOW}Search Terms per City:${NC} ${#SEARCH_TERM_KEYS[@]} variations"
echo -e "${YELLOW}Total Searches:${NC} $((${#ALL_CITIES[@]} * ${#SEARCH_TERM_KEYS[@]}))"
echo -e "${YELLOW}Max Results per Search:${NC} $MAX_RESULTS"
echo -e "${YELLOW}Email Extraction:${NC} ENABLED"
if [ "$START_FROM" -gt 1 ]; then
    echo -e "${MAGENTA}Starting From:${NC} Scrape #$START_FROM (skipping first $((START_FROM - 1)) scrapes)"
fi
echo ""
echo -e "${YELLOW}Working directory:${NC} $(pwd)"
echo ""

# Function to check if results exist
check_existing_results() {
    local city="$1"
    local keyword="$2"
    local language="$3"

    # Use Python helper to match filename sanitization exactly with main scraper
    local result
    result=$(python scripts/check_existing_keyword.py "$city" "$keyword" 2>/dev/null)

    local action
    action=$(echo "$result" | cut -d: -f1)

    if [ "$action" = "SKIP" ]; then
        echo -e "${GREEN}✓${NC} Existing data found - ${GREEN}SKIPPING${NC}"
        return 0  # Skip
    fi

    echo -e "${BLUE}○${NC} No usable data - ${BLUE}SCRAPING${NC}"
    return 1  # Scrape
}

# Track statistics
total_combinations=$((${#ALL_CITIES[@]} * ${#SEARCH_TERM_KEYS[@]}))
current=0
skipped=0
scraped=0
failed=0
skipped_before_start=0

# Validate START_FROM is within range
if [ "$START_FROM" -gt "$total_combinations" ]; then
    echo -e "${RED}Error: --start-from ($START_FROM) exceeds total searches ($total_combinations)${NC}"
    exit 1
fi

echo -e "${CYAN}Starting batch scraping...${NC}"
if [ "$START_FROM" -gt 1 ]; then
    echo -e "${CYAN}Resuming from scrape #$START_FROM (skipping $((START_FROM - 1)) scrapes)${NC}"
fi
echo -e "${CYAN}Total searches to perform: $((total_combinations - START_FROM + 1)) of $total_combinations${NC}"
echo ""

# Progress log file
PROGRESS_LOG="data/poland_ice_cream_progress.log"
mkdir -p data
touch "$PROGRESS_LOG"

# Main scraping loop
city_header_printed=false
for city_entry in "${ALL_CITIES[@]}"; do
    IFS='|' read -r city country_code <<< "$city_entry"

    city_header_printed=false

    for term_key in "${SEARCH_TERM_KEYS[@]}"; do
        ((current++))

        # Skip if before START_FROM
        if [ "$current" -lt "$START_FROM" ]; then
            ((skipped_before_start++))
            continue
        fi

        # Print city header only once per city (and only if we have work to do)
        if [ "$city_header_printed" = false ]; then
            echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${MAGENTA}City: $city ($country_code)${NC}"
            echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            city_header_printed=true
        fi

        # Get keyword and language from the search term
        term_data="${SEARCH_TERMS[$term_key]}"
        if [ -z "$term_data" ]; then
            echo -e "${RED}Warning: No search term found for $term_key${NC}"
            continue
        fi

        IFS='|' read -r keyword language <<< "$term_data"

        echo -e "${YELLOW}[$current/$total_combinations]${NC} $city - \"$keyword\" ($language)"

        # Check if already scraped
        if check_existing_results "$city" "$keyword" "$language"; then
            ((skipped++))
            echo "$city|$keyword|$language|SKIPPED" >> "$PROGRESS_LOG"
            echo ""
            continue
        fi

        # Run scraper
        echo -e "${BLUE}→${NC} Scraping $city for \"$keyword\"..."

        # Convert country code to uppercase for phone parsing (pl -> PL)
        country_code_upper=$(echo "$country_code" | tr '[:lower:]' '[:upper:]')

        # Run python and capture output
        python main.py --city "$city" --keyword "$keyword" --language "$language" --country-code "$country_code_upper" $FIND_EMAILS --max-results $MAX_RESULTS 2>&1
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Completed: $city - $keyword"
            ((scraped++))
            echo "$city|$keyword|$language|SUCCESS" >> "$PROGRESS_LOG"
        else
            echo -e "${RED}✗${NC} Failed: $city - $keyword (exit code: $exit_code)"
            ((failed++))
            echo "$city|$keyword|$language|FAILED" >> "$PROGRESS_LOG"
        fi

        echo ""
        sleep 3  # Delay between scrapes to avoid detection
    done

    echo ""
done

# Final summary
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}                    FINAL SUMMARY                          ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Total Searches:${NC} $total_combinations"
if [ "$skipped_before_start" -gt 0 ]; then
    echo -e "${BLUE}Skipped (before start):${NC} $skipped_before_start"
fi
echo -e "${GREEN}Successfully Scraped:${NC} $scraped"
echo -e "${GREEN}Skipped (existing):${NC} $skipped"
echo -e "${RED}Failed:${NC} $failed"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}All results saved to:${NC} data/leads/"
echo -e "${YELLOW}Progress log:${NC} $PROGRESS_LOG"
echo ""
echo -e "${GREEN}✓ Poland ice cream scraper completed!${NC}"
echo ""
echo -e "${YELLOW}Tip:${NC} To resume from a specific point, use: $0 --start-from <number>"
echo ""
