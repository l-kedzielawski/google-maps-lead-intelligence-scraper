#!/bin/bash

# ============================================
# CZECH + SLOVAKIA + NORDIC ICE CREAM SCRAPER
# ============================================
# Scrapes Czech Republic, Slovakia, Denmark, Sweden, and Norway
# for ice cream makers, artisans, and manufacturers using local languages.
#
# Features:
#   - 5 countries with localized keywords
#   - 500 max results per search
#   - 20km radius
#   - Checks existing results and skips if > 1 result found
#   - Re-scrapes if <= 1 result or no data exists
#   - Progress tracking with resume capability
#   - Resume from specific scrape number with --start-from
#
# Usage:
#   ./scripts/czech_slovakia_nordic_ice_cream_scraper.sh
#   ./scripts/czech_slovakia_nordic_ice_cream_scraper.sh --start-from 150
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

MAX_RESULTS=500
RADIUS_KM=20
FIND_EMAILS="--find-emails"
START_FROM=1

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
            echo "  $0 --start-from 150    # Resume from scrape #150"
            echo "  $0 -s 150              # Short form"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if ! [[ "$START_FROM" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}Error: --start-from must be a positive number${NC}"
    exit 1
fi

declare -A SEARCH_TERMS=(
    # Czech Republic - Czech
    ["ice_cream_manufacturer_cs"]="výrobce zmrzliny|cs"
    ["artisanal_ice_cream_cs"]="řemeslná zmrzlina|cs"
    ["ice_cream_maker_cs"]="zmrzlinář|cs"
    ["ice_cream_manufactory_cs"]="manufaktura zmrzliny|cs"

    # Slovakia - Slovak
    ["ice_cream_manufacturer_sk"]="výrobca zmrzliny|sk"
    ["artisanal_ice_cream_sk"]="remeselná zmrzlina|sk"
    ["ice_cream_maker_sk"]="zmrzlinár|sk"
    ["ice_cream_manufactory_sk"]="manufaktúra zmrzliny|sk"

    # Denmark - Danish + English fallback
    ["ice_cream_manufacturer_da"]="isproducent|da"
    ["artisanal_ice_cream_da"]="håndlavet is|da"
    ["ice_cream_factory_da"]="isbutik|da"
    ["ice_cream_maker_da"]="ice cream shop|en"

    # Sweden - Swedish + English fallback
    ["ice_cream_manufacturer_sv"]="glassproducent|sv"
    ["artisanal_ice_cream_sv"]="glassbar|sv"
    ["ice_cream_factory_sv"]="konditori|sv"
    ["ice_cream_maker_sv"]="ice cream shop|en"

    # Norway - Norwegian + English fallback
    ["ice_cream_manufacturer_no"]="iskremprodusent|no"
    ["artisanal_ice_cream_no"]="iskrembar|no"
    ["ice_cream_factory_no"]="konditori|no"
    ["ice_cream_maker_no"]="ice cream shop|en"
)

# CZECH REPUBLIC (27 cities, 40K+)
CZECH_CITIES=(
    "Praha|cs" "Brno|cs" "Ostrava|cs" "Plzeň|cs" "Liberec|cs" "Olomouc|cs" "České Budějovice|cs" "Hradec Králové|cs" "Pardubice|cs" "Ústí nad Labem|cs" "Zlín|cs" "Havířov|cs" "Kladno|cs" "Most|cs" "Karlovy Vary|cs" "Opava|cs" "Frýdek-Místek|cs" "Jihlava|cs" "Teplice|cs" "Děčín|cs" "Chomutov|cs" "Přerov|cs" "Prostějov|cs" "Třinec|cs" "Jablonec nad Nisou|cs" "Mladá Boleslav|cs" "Karviná|cs"
)

# SLOVAKIA (9 cities, 40K+)
SLOVAKIA_CITIES=(
    "Bratislava|sk" "Košice|sk" "Prešov|sk" "Žilina|sk" "Nitra|sk" "Banská Bystrica|sk" "Trnava|sk" "Trenčín|sk" "Martin|sk"
)

# DENMARK (12 cities)
DENMARK_CITIES=(
    "København|da" "Aarhus|da" "Odense|da" "Aalborg|da" "Esbjerg|da" "Randers|da" "Kolding|da" "Horsens|da" "Vejle|da" "Roskilde|da" "Herning|da" "Silkeborg|da"
)

# SWEDEN (15 cities)
SWEDEN_CITIES=(
    "Stockholm|sv" "Göteborg|sv" "Malmö|sv" "Uppsala|sv" "Västerås|sv" "Örebro|sv" "Linköping|sv" "Helsingborg|sv" "Jönköping|sv" "Norrköping|sv" "Lund|sv" "Umeå|sv" "Gävle|sv" "Borås|sv" "Södertälje|sv"
)

# NORWAY (12 cities)
NORWAY_CITIES=(
    "Oslo|no" "Bergen|no" "Trondheim|no" "Stavanger|no" "Drammen|no" "Fredrikstad|no" "Kristiansand|no" "Sandnes|no" "Tromsø|no" "Sarpsborg|no" "Skien|no" "Ålesund|no"
)

ALL_CITIES=(
    "${CZECH_CITIES[@]}"
    "${SLOVAKIA_CITIES[@]}"
    "${DENMARK_CITIES[@]}"
    "${SWEDEN_CITIES[@]}"
    "${NORWAY_CITIES[@]}"
)

if [ ! -f "../main.py" ] && [ ! -f "main.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/czech_slovakia_nordic_ice_cream_scraper.sh${NC}"
    exit 1
fi

if [ -f "../main.py" ]; then
    cd ..
fi

get_search_terms_for_country() {
    local country_code="$1"
    local terms=()

    case "$country_code" in
        cs)
            terms=("ice_cream_manufacturer_cs" "artisanal_ice_cream_cs" "ice_cream_maker_cs" "ice_cream_manufactory_cs")
            ;;
        sk)
            terms=("ice_cream_manufacturer_sk" "artisanal_ice_cream_sk" "ice_cream_maker_sk" "ice_cream_manufactory_sk")
            ;;
        da)
            terms=("ice_cream_manufacturer_da" "artisanal_ice_cream_da" "ice_cream_factory_da" "ice_cream_maker_da")
            ;;
        sv)
            terms=("ice_cream_manufacturer_sv" "artisanal_ice_cream_sv" "ice_cream_factory_sv" "ice_cream_maker_sv")
            ;;
        no)
            terms=("ice_cream_manufacturer_no" "artisanal_ice_cream_no" "ice_cream_factory_no" "ice_cream_maker_no")
            ;;
    esac

    echo "${terms[@]}"
}

get_phone_country_code() {
    local country_code="$1"

    case "$country_code" in
        cs) echo "CZ" ;;
        sk) echo "SK" ;;
        da) echo "DK" ;;
        sv) echo "SE" ;;
        no) echo "NO" ;;
        *) echo "$(echo "$country_code" | tr '[:lower:]' '[:upper:]')" ;;
    esac
}

check_existing_results() {
    local city="$1"
    local keyword="$2"

    local result
    result=$(python scripts/check_existing_keyword.py "$city" "$keyword" 2>/dev/null)

    local action
    action=$(echo "$result" | cut -d: -f1)

    if [ "$action" = "SKIP" ]; then
        echo -e "${GREEN}✓${NC} Existing data found - ${GREEN}SKIPPING${NC}"
        return 0
    fi

    echo -e "${BLUE}○${NC} No usable data - ${BLUE}SCRAPING${NC}"
    return 1
}

total_combinations=$((${#ALL_CITIES[@]} * 4))
current=0
skipped=0
scraped=0
failed=0
zero_results=0
skipped_before_start=0

if [ "$START_FROM" -gt "$total_combinations" ]; then
    echo -e "${RED}Error: --start-from ($START_FROM) exceeds total searches ($total_combinations)${NC}"
    exit 1
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}     CZECH + SLOVAKIA + NORDIC ICE CREAM SCRAPER         ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Countries:${NC} Czech Republic (${#CZECH_CITIES[@]}), Slovakia (${#SLOVAKIA_CITIES[@]}), Denmark (${#DENMARK_CITIES[@]}), Sweden (${#SWEDEN_CITIES[@]}), Norway (${#NORWAY_CITIES[@]})"
echo -e "${YELLOW}Total Cities:${NC} ${#ALL_CITIES[@]} cities"
echo -e "${YELLOW}Search Terms per City:${NC} 4 variations"
echo -e "${YELLOW}Total Searches:${NC} $total_combinations"
echo -e "${YELLOW}Max Results per Search:${NC} $MAX_RESULTS"
echo -e "${YELLOW}Search Radius:${NC} ${RADIUS_KM}km"
echo -e "${YELLOW}Email Extraction:${NC} ENABLED"
if [ "$START_FROM" -gt 1 ]; then
    echo -e "${MAGENTA}Starting From:${NC} Scrape #$START_FROM (skipping first $((START_FROM - 1)) scrapes)"
fi
echo ""
echo -e "${YELLOW}Working directory:${NC} $(pwd)"
echo ""

echo -e "${CYAN}Starting batch scraping...${NC}"
if [ "$START_FROM" -gt 1 ]; then
    echo -e "${CYAN}Resuming from scrape #$START_FROM (skipping $((START_FROM - 1)) scrapes)${NC}"
fi
echo -e "${CYAN}Total searches to perform: $((total_combinations - START_FROM + 1)) of $total_combinations${NC}"
echo ""

PROGRESS_LOG="data/czech_slovakia_nordic_ice_cream_progress.log"
mkdir -p data
touch "$PROGRESS_LOG"

city_header_printed=false
for city_entry in "${ALL_CITIES[@]}"; do
    IFS='|' read -r city country_code <<< "$city_entry"

    city_header_printed=false
    search_term_keys=$(get_search_terms_for_country "$country_code")

    for term_key in $search_term_keys; do
        ((current++))

        if [ "$current" -lt "$START_FROM" ]; then
            ((skipped_before_start++))
            continue
        fi

        if [ "$city_header_printed" = false ]; then
            echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${MAGENTA}City: $city ($country_code)${NC}"
            echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            city_header_printed=true
        fi

        term_data="${SEARCH_TERMS[$term_key]}"
        if [ -z "$term_data" ]; then
            echo -e "${RED}Warning: No search term found for $term_key${NC}"
            continue
        fi

        IFS='|' read -r keyword language <<< "$term_data"
        echo -e "${YELLOW}[$current/$total_combinations]${NC} $city - \"$keyword\" ($language)"

        if check_existing_results "$city" "$keyword"; then
            ((skipped++))
            echo "$city|$keyword|$language|SKIPPED" >> "$PROGRESS_LOG"
            echo ""
            continue
        fi

        echo -e "${BLUE}→${NC} Scraping $city for \"$keyword\"..."
        country_code_upper=$(get_phone_country_code "$country_code")

        scrape_log=$(mktemp)
        python -u main.py --city "$city" --keyword "$keyword" --language "$language" --country-code "$country_code_upper" $FIND_EMAILS --max-results "$MAX_RESULTS" --radius "$RADIUS_KM" 2>&1 | tee "$scrape_log"
        exit_code=${PIPESTATUS[0]}

        scraped_count=0
        if [ $exit_code -eq 0 ]; then
            while IFS= read -r line; do
                case "$line" in
                    SCRAPED_COUNT:*)
                        scraped_count="${line#SCRAPED_COUNT:}"
                        ;;
                esac
            done < "$scrape_log"
        fi

        rm -f "$scrape_log"

        if [ $exit_code -eq 0 ] && [ "${scraped_count:-0}" -gt 0 ]; then
            echo -e "${GREEN}✓${NC} Completed: $city - $keyword"
            ((scraped++))
            echo "$city|$keyword|$language|SUCCESS" >> "$PROGRESS_LOG"
        elif [ $exit_code -eq 0 ]; then
            echo -e "${YELLOW}○${NC} Completed with 0 results: $city - $keyword"
            ((zero_results++))
            echo "$city|$keyword|$language|ZERO_RESULTS" >> "$PROGRESS_LOG"
        else
            echo -e "${RED}✗${NC} Failed: $city - $keyword (exit code: $exit_code)"
            ((failed++))
            echo "$city|$keyword|$language|FAILED" >> "$PROGRESS_LOG"
        fi

        echo ""
        sleep 3
    done

    echo ""
done

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}                    FINAL SUMMARY                          ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Total Searches:${NC} $total_combinations"
if [ "$skipped_before_start" -gt 0 ]; then
    echo -e "${BLUE}Skipped (before start):${NC} $skipped_before_start"
fi
echo -e "${GREEN}Successfully Scraped:${NC} $scraped"
echo -e "${YELLOW}Zero Results:${NC} $zero_results"
echo -e "${GREEN}Skipped (existing):${NC} $skipped"
echo -e "${RED}Failed:${NC} $failed"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}All results saved to:${NC} data/leads/"
echo -e "${YELLOW}Progress log:${NC} $PROGRESS_LOG"
echo ""
echo -e "${GREEN}✓ Czech + Slovakia + Nordic scraper completed!${NC}"
echo ""
echo -e "${YELLOW}Tip:${NC} To resume from a specific point, use: $0 --start-from <number>"
echo ""
