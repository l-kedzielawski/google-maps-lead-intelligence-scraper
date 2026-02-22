#!/bin/bash

# ==============================================================
# ENGLISH-FRIENDLY ICE CREAM + CONFECTIONERY BATCH SCRAPER
# ==============================================================
# Targets countries where English works well for business outreach,
# while still using local-language keywords for better coverage.
#
# Countries:
#   - United Kingdom (GB)
#   - Ireland (IE)
#   - Netherlands (NL)
#   - Sweden (SE)
#   - Norway (NO)
#   - Denmark (DK)
#
# Business intent keywords include:
#   - Ice cream makers / gelato shops
#   - Ice cream manufacturers / producers
#   - Confectionery / pastry / dessert businesses
#
# Usage:
#   ./scripts/english_friendly_ice_cream_confectionery_scraper.sh
#   ./scripts/english_friendly_ice_cream_confectionery_scraper.sh --start-from 300
# ==============================================================

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
COUNTRY_FILTER="all"

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
            echo "  -c, --country CODE     Run only one country: uk|ie|nl|se|no|dk|all"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                     # Start from beginning"
            echo "  $0 --start-from 300    # Resume from scrape #300"
            echo "  $0 --country se        # Sweden only"
            echo "  $0 -s 300              # Short form"
            exit 0
            ;;
        -c|--country)
            COUNTRY_FILTER="$2"
            shift 2
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

COUNTRY_FILTER=$(echo "$COUNTRY_FILTER" | tr '[:upper:]' '[:lower:]')
if [[ "$COUNTRY_FILTER" != "all" && "$COUNTRY_FILTER" != "uk" && "$COUNTRY_FILTER" != "ie" && "$COUNTRY_FILTER" != "nl" && "$COUNTRY_FILTER" != "se" && "$COUNTRY_FILTER" != "no" && "$COUNTRY_FILTER" != "dk" ]]; then
    echo -e "${RED}Error: --country must be one of: uk|ie|nl|se|no|dk|all${NC}"
    exit 1
fi

declare -A SEARCH_TERMS=(
    # UK (English - UK locale)
    ["artisan_ice_cream_en_gb"]="artisan ice cream shop|en-gb"
    ["gelato_shop_en_gb"]="gelato shop|en-gb"
    ["ice_cream_manufacturer_en_gb"]="ice cream manufacturer|en-gb"
    ["ice_cream_producer_en_gb"]="ice cream producer|en-gb"
    ["confectionery_en_gb"]="confectionery|en-gb"
    ["dessert_shop_en_gb"]="dessert shop|en-gb"

    # Ireland (English - Ireland locale)
    ["artisan_ice_cream_en_ie"]="artisan ice cream shop|en-ie"
    ["gelato_shop_en_ie"]="gelato shop|en-ie"
    ["ice_cream_manufacturer_en_ie"]="ice cream manufacturer|en-ie"
    ["ice_cream_producer_en_ie"]="ice cream producer|en-ie"
    ["confectionery_en_ie"]="confectionery|en-ie"
    ["dessert_shop_en_ie"]="dessert shop|en-ie"

    # Netherlands (Dutch + English fallback)
    ["artisan_ice_cream_nl"]="ambachtelijke ijssalon|nl"
    ["ice_cream_maker_nl"]="ijsmakerij|nl"
    ["ice_cream_producer_nl"]="ijsproducent|nl"
    ["confectionery_nl"]="banketbakkerij|nl"
    ["chocolatier_nl"]="chocolaterie|nl"
    ["ice_cream_shop_en_nl"]="ice cream shop|en"

    # Sweden (Swedish + English fallback)
    ["artisan_ice_cream_sv"]="glassbar|sv"
    ["ice_cream_producer_sv"]="glassproducent|sv"
    ["ice_cream_factory_sv"]="glassfabrik|sv"
    ["confectionery_sv"]="konditori|sv"
    ["dessert_sv"]="dessertbutik|sv"
    ["ice_cream_shop_en_sv"]="ice cream shop|en"

    # Norway (Norwegian + English fallback)
    ["artisan_ice_cream_no"]="iskrembar|no"
    ["ice_cream_producer_no"]="iskremprodusent|no"
    ["ice_cream_factory_no"]="iskremfabrikk|no"
    ["confectionery_no"]="konditori|no"
    ["dessert_no"]="dessertbutikk|no"
    ["ice_cream_shop_en_no"]="ice cream shop|en"

    # Denmark (Danish + English fallback)
    ["artisan_ice_cream_da"]="isbutik|da"
    ["ice_cream_producer_da"]="isproducent|da"
    ["ice_cream_factory_da"]="isfabrik|da"
    ["confectionery_da"]="konditori|da"
    ["dessert_da"]="dessertbutik|da"
    ["ice_cream_shop_en_da"]="ice cream shop|en"
)

# Format: "City|PhoneCountryISO|term_group"
UK_CITIES=(
    "London|GB|uk" "Manchester|GB|uk" "Birmingham|GB|uk" "Liverpool|GB|uk" "Leeds|GB|uk"
    "Sheffield|GB|uk" "Bristol|GB|uk" "Newcastle upon Tyne|GB|uk" "Nottingham|GB|uk" "Leicester|GB|uk"
    "Coventry|GB|uk" "Belfast|GB|uk" "Edinburgh|GB|uk" "Glasgow|GB|uk" "Cardiff|GB|uk"
    "Southampton|GB|uk" "Portsmouth|GB|uk" "Brighton|GB|uk" "Reading|GB|uk" "Milton Keynes|GB|uk"
    "Aberdeen|GB|uk" "Dundee|GB|uk" "Cambridge|GB|uk" "Oxford|GB|uk" "York|GB|uk"
)

IRELAND_CITIES=(
    "Dublin|IE|ie" "Cork|IE|ie" "Limerick|IE|ie" "Galway|IE|ie"
    "Waterford|IE|ie" "Drogheda|IE|ie" "Dundalk|IE|ie" "Sligo|IE|ie"
)

NETHERLANDS_CITIES=(
    "Amsterdam|NL|nl" "Rotterdam|NL|nl" "Utrecht|NL|nl" "Eindhoven|NL|nl" "Tilburg|NL|nl"
    "Groningen|NL|nl" "Almere|NL|nl" "Breda|NL|nl" "Nijmegen|NL|nl" "Enschede|NL|nl"
    "Haarlem|NL|nl" "Arnhem|NL|nl" "Amersfoort|NL|nl" "Apeldoorn|NL|nl" "Leiden|NL|nl"
    "Dordrecht|NL|nl" "Zwolle|NL|nl" "Delft|NL|nl" "Maastricht|NL|nl" "Den Bosch|NL|nl"
)

SWEDEN_CITIES=(
    "Stockholm|SE|se" "Göteborg|SE|se" "Malmö|SE|se" "Uppsala|SE|se" "Västerås|SE|se"
    "Örebro|SE|se" "Linköping|SE|se" "Helsingborg|SE|se" "Jönköping|SE|se" "Norrköping|SE|se"
    "Lund|SE|se" "Umeå|SE|se" "Gävle|SE|se" "Borås|SE|se" "Södertälje|SE|se"
)

NORWAY_CITIES=(
    "Oslo|NO|no" "Bergen|NO|no" "Trondheim|NO|no" "Stavanger|NO|no" "Drammen|NO|no"
    "Fredrikstad|NO|no" "Kristiansand|NO|no" "Sandnes|NO|no" "Tromsø|NO|no" "Sarpsborg|NO|no"
    "Skien|NO|no" "Ålesund|NO|no"
)

DENMARK_CITIES=(
    "København|DK|dk" "Aarhus|DK|dk" "Odense|DK|dk" "Aalborg|DK|dk" "Esbjerg|DK|dk"
    "Randers|DK|dk" "Kolding|DK|dk" "Horsens|DK|dk" "Vejle|DK|dk" "Roskilde|DK|dk"
)

ALL_CITIES=(
    "${UK_CITIES[@]}"
    "${IRELAND_CITIES[@]}"
    "${NETHERLANDS_CITIES[@]}"
    "${SWEDEN_CITIES[@]}"
    "${NORWAY_CITIES[@]}"
    "${DENMARK_CITIES[@]}"
)

SELECTED_CITIES=()
for city_entry in "${ALL_CITIES[@]}"; do
    IFS='|' read -r _ _ country_group <<< "$city_entry"
    if [ "$COUNTRY_FILTER" = "all" ] || [ "$COUNTRY_FILTER" = "$country_group" ]; then
        SELECTED_CITIES+=("$city_entry")
    fi
done

if [ ${#SELECTED_CITIES[@]} -eq 0 ]; then
    echo -e "${RED}Error: No cities selected for country filter '$COUNTRY_FILTER'${NC}"
    exit 1
fi

if [ ! -f "../main.py" ] && [ ! -f "main.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/english_friendly_ice_cream_confectionery_scraper.sh${NC}"
    exit 1
fi

if [ -f "../main.py" ]; then
    cd ..
fi

get_search_terms_for_country_group() {
    local country_group="$1"
    local terms=()

    case "$country_group" in
        uk)
            terms=("artisan_ice_cream_en_gb" "gelato_shop_en_gb" "ice_cream_manufacturer_en_gb" "ice_cream_producer_en_gb" "confectionery_en_gb" "dessert_shop_en_gb")
            ;;
        ie)
            terms=("artisan_ice_cream_en_ie" "gelato_shop_en_ie" "ice_cream_manufacturer_en_ie" "ice_cream_producer_en_ie" "confectionery_en_ie" "dessert_shop_en_ie")
            ;;
        nl)
            terms=("artisan_ice_cream_nl" "ice_cream_maker_nl" "ice_cream_producer_nl" "confectionery_nl" "chocolatier_nl" "ice_cream_shop_en_nl")
            ;;
        se)
            terms=("artisan_ice_cream_sv" "ice_cream_producer_sv" "ice_cream_factory_sv" "confectionery_sv" "dessert_sv" "ice_cream_shop_en_sv")
            ;;
        no)
            terms=("artisan_ice_cream_no" "ice_cream_producer_no" "ice_cream_factory_no" "confectionery_no" "dessert_no" "ice_cream_shop_en_no")
            ;;
        dk)
            terms=("artisan_ice_cream_da" "ice_cream_producer_da" "ice_cream_factory_da" "confectionery_da" "dessert_da" "ice_cream_shop_en_da")
            ;;
    esac

    echo "${terms[@]}"
}

get_country_folder_name() {
    local country_iso="$1"

    case "$country_iso" in
        GB) echo "United_Kingdom" ;;
        IE) echo "Ireland" ;;
        NL) echo "Netherlands" ;;
        SE) echo "Sweden" ;;
        NO) echo "Norway" ;;
        DK) echo "Denmark" ;;
        *) echo "$country_iso" ;;
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

total_combinations=0
for city_entry in "${SELECTED_CITIES[@]}"; do
    IFS='|' read -r _ _ country_group <<< "$city_entry"
    search_term_keys=$(get_search_terms_for_country_group "$country_group")
    for _ in $search_term_keys; do
        ((total_combinations++))
    done
done

current=0
skipped=0
scraped=0
zero_results=0
failed=0
skipped_before_start=0

if [ "$START_FROM" -gt "$total_combinations" ]; then
    echo -e "${RED}Error: --start-from ($START_FROM) exceeds total searches ($total_combinations)${NC}"
    exit 1
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ENGLISH-FRIENDLY ICE CREAM + CONFECTIONERY SCRAPER     ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
if [ "$COUNTRY_FILTER" = "all" ]; then
    echo -e "${YELLOW}Countries:${NC} UK (${#UK_CITIES[@]}), IE (${#IRELAND_CITIES[@]}), NL (${#NETHERLANDS_CITIES[@]}), SE (${#SWEDEN_CITIES[@]}), NO (${#NORWAY_CITIES[@]}), DK (${#DENMARK_CITIES[@]})"
else
    echo -e "${YELLOW}Country Filter:${NC} $COUNTRY_FILTER"
fi
echo -e "${YELLOW}Total Cities:${NC} ${#SELECTED_CITIES[@]} cities"
echo -e "${YELLOW}Search Terms per City:${NC} 6 variations"
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

PROGRESS_LOG="data/english_friendly_ice_cream_confectionery_progress.log"
mkdir -p data
touch "$PROGRESS_LOG"

city_header_printed=false
for city_entry in "${SELECTED_CITIES[@]}"; do
    IFS='|' read -r city country_iso country_group <<< "$city_entry"

    city_header_printed=false
    country_folder=$(get_country_folder_name "$country_iso")
    search_term_keys=$(get_search_terms_for_country_group "$country_group")

    for term_key in $search_term_keys; do
        ((current++))

        if [ "$current" -lt "$START_FROM" ]; then
            ((skipped_before_start++))
            continue
        fi

        if [ "$city_header_printed" = false ]; then
            echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${MAGENTA}City: $city ($country_iso)${NC}"
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

        scrape_log=$(mktemp)
        python -u main.py --city "$city" --keyword "$keyword" --language "$language" --country-code "$country_iso" --output-subdir "$country_folder" $FIND_EMAILS --max-results "$MAX_RESULTS" --radius "$RADIUS_KM" 2>&1 | tee "$scrape_log"
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
            echo -e "${GREEN}✓${NC} Completed: $city - $keyword (${scraped_count} results)"
            ((scraped++))
            echo "$city|$keyword|$language|SUCCESS|$scraped_count" >> "$PROGRESS_LOG"
        elif [ $exit_code -eq 0 ]; then
            echo -e "${YELLOW}○${NC} Completed with 0 results: $city - $keyword"
            ((zero_results++))
            echo "$city|$keyword|$language|ZERO_RESULTS|0" >> "$PROGRESS_LOG"
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
echo -e "${YELLOW}All results saved to:${NC} data/leads/<Country>/"
echo -e "${YELLOW}Progress log:${NC} $PROGRESS_LOG"
echo ""
echo -e "${GREEN}✓ English-friendly scraper completed!${NC}"
echo ""
echo -e "${YELLOW}Tip:${NC} To resume from a specific point, use: $0 --start-from <number>"
echo ""
