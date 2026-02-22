#!/bin/bash

# =====================================================================
# EU TOP-TIER ICE CREAM + CONFECTIONERY SCRAPER
# =====================================================================
# Top-tier EU English-friendly markets with native language targeting,
# plus Poland confectionery-only targeting.
#
# Countries:
#   - Sweden (SE)
#   - Netherlands (NL)
#   - Denmark (DK)
#   - Finland (FI)
#   - Ireland (IE)
#   - Malta (MT)
#   - Poland (PL) -> cukiernia only
#
# Features:
#   - Native-language + artisanal variants
#   - Confectionery intent (konditori / banketbakkerij / confectionery, etc.)
#   - Email extraction enabled
#   - Output to per-country folders in data/leads/<Country>/
#   - Smart skip threshold (re-scrapes thin existing files)
#   - Tracks ZERO_RESULTS separately from SUCCESS
#   - Resume support via --start-from
#
# Usage:
#   ./scripts/eu_top_tier_ice_cream_confectionery_scraper.sh
#   ./scripts/eu_top_tier_ice_cream_confectionery_scraper.sh --country se
#   ./scripts/eu_top_tier_ice_cream_confectionery_scraper.sh --start-from 250
# =====================================================================

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
MIN_EXISTING_RESULTS_TO_SKIP=20
START_FROM=1
COUNTRY_FILTER="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--start-from)
            START_FROM="$2"
            shift 2
            ;;
        -c|--country)
            COUNTRY_FILTER="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -s, --start-from NUM   Start from scrape number NUM (default: 1)"
            echo "  -c, --country CODE     Run only one country: se|nl|dk|fi|ie|mt|pl|all"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                     # Run all target countries"
            echo "  $0 --country se        # Sweden only"
            echo "  $0 --country pl        # Poland cukiernia only"
            echo "  $0 --start-from 250    # Resume from scrape #250"
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

COUNTRY_FILTER=$(echo "$COUNTRY_FILTER" | tr '[:upper:]' '[:lower:]')
if [[ "$COUNTRY_FILTER" != "all" && "$COUNTRY_FILTER" != "se" && "$COUNTRY_FILTER" != "nl" && "$COUNTRY_FILTER" != "dk" && "$COUNTRY_FILTER" != "fi" && "$COUNTRY_FILTER" != "ie" && "$COUNTRY_FILTER" != "mt" && "$COUNTRY_FILTER" != "pl" ]]; then
    echo -e "${RED}Error: --country must be one of: se|nl|dk|fi|ie|mt|pl|all${NC}"
    exit 1
fi

declare -A SEARCH_TERMS=(
    # Sweden (Swedish + artisanal English variant)
    ["artisan_ice_cream_sv"]="hantverksglass|sv"
    ["artisan_ice_cream_en_se"]="artisan ice cream|en-gb"
    ["ice_cream_bar_sv"]="glassbar|sv"
    ["ice_cream_producer_sv"]="glassproducent|sv"
    ["confectionery_sv"]="konditori|sv"
    ["gelato_shop_en_se"]="gelato shop|en-gb"

    # Netherlands (Dutch)
    ["artisan_ice_cream_nl"]="ambachtelijke ijssalon|nl"
    ["artisan_ice_cream_variant_nl"]="ambachtelijk ijs|nl"
    ["ice_cream_maker_nl"]="ijsmakerij|nl"
    ["ice_cream_producer_nl"]="ijsproducent|nl"
    ["confectionery_nl"]="banketbakkerij|nl"
    ["chocolatier_nl"]="chocolaterie|nl"

    # Denmark (Danish + artisanal English variant)
    ["artisan_ice_cream_da"]="håndlavet is|da"
    ["artisan_ice_cream_en_da"]="artisan ice cream|en-gb"
    ["ice_cream_shop_da"]="isbutik|da"
    ["ice_cream_producer_da"]="isproducent|da"
    ["confectionery_da"]="konditori|da"
    ["dessert_shop_da"]="dessertbutik|da"

    # Finland (Finnish + artisanal English variant)
    ["artisan_ice_cream_fi"]="artesaanijäätelö|fi"
    ["artisan_ice_cream_en_fi"]="artisan ice cream|en-gb"
    ["ice_cream_bar_fi"]="jäätelöbaari|fi"
    ["ice_cream_producer_fi"]="jäätelön valmistaja|fi"
    ["ice_cream_shop_fi"]="jäätelökauppa|fi"
    ["confectionery_fi"]="konditoria|fi"

    # Ireland (English Ireland locale)
    ["artisan_ice_cream_ie"]="artisan ice cream shop|en-ie"
    ["artisan_gelato_ie"]="artisan gelato|en-ie"
    ["ice_cream_manufacturer_ie"]="ice cream manufacturer|en-ie"
    ["ice_cream_producer_ie"]="ice cream producer|en-ie"
    ["confectionery_ie"]="confectionery|en-ie"
    ["dessert_shop_ie"]="dessert shop|en-ie"

    # Malta (English Malta locale)
    ["artisan_ice_cream_mt"]="artisan ice cream shop|en-mt"
    ["gelato_shop_mt"]="gelato shop|en-mt"
    ["ice_cream_manufacturer_mt"]="ice cream manufacturer|en-mt"
    ["confectionery_mt"]="confectionery|en-mt"
    ["dessert_shop_mt"]="dessert shop|en-mt"
    ["cake_shop_mt"]="cake shop|en-mt"

    # Poland (confectionery only, singular requested)
    ["confectionery_pl"]="cukiernia|pl"
)

# Format: "City|PhoneCountryISO|term_group"
SWEDEN_CITIES=(
    "Stockholm|SE|se" "Göteborg|SE|se" "Malmö|SE|se" "Uppsala|SE|se" "Västerås|SE|se"
    "Örebro|SE|se" "Linköping|SE|se" "Helsingborg|SE|se" "Jönköping|SE|se" "Norrköping|SE|se"
    "Lund|SE|se" "Umeå|SE|se" "Gävle|SE|se" "Borås|SE|se" "Södertälje|SE|se"
    "Halmstad|SE|se" "Växjö|SE|se" "Karlstad|SE|se" "Sundsvall|SE|se" "Luleå|SE|se"
)

NETHERLANDS_CITIES=(
    "Amsterdam|NL|nl" "Rotterdam|NL|nl" "Utrecht|NL|nl" "Eindhoven|NL|nl" "Tilburg|NL|nl"
    "Groningen|NL|nl" "Almere|NL|nl" "Breda|NL|nl" "Nijmegen|NL|nl" "Enschede|NL|nl"
    "Haarlem|NL|nl" "Arnhem|NL|nl" "Amersfoort|NL|nl" "Apeldoorn|NL|nl" "Leiden|NL|nl"
    "Dordrecht|NL|nl" "Zwolle|NL|nl" "Delft|NL|nl" "Maastricht|NL|nl" "Den Bosch|NL|nl"
)

DENMARK_CITIES=(
    "København|DK|dk" "Aarhus|DK|dk" "Odense|DK|dk" "Aalborg|DK|dk" "Esbjerg|DK|dk"
    "Randers|DK|dk" "Kolding|DK|dk" "Horsens|DK|dk" "Vejle|DK|dk" "Roskilde|DK|dk"
    "Herning|DK|dk" "Silkeborg|DK|dk"
)

FINLAND_CITIES=(
    "Helsinki|FI|fi" "Espoo|FI|fi" "Tampere|FI|fi" "Vantaa|FI|fi" "Oulu|FI|fi"
    "Turku|FI|fi" "Jyväskylä|FI|fi" "Kuopio|FI|fi" "Lahti|FI|fi" "Pori|FI|fi"
    "Kouvola|FI|fi" "Joensuu|FI|fi"
)

IRELAND_CITIES=(
    "Dublin|IE|ie" "Cork|IE|ie" "Limerick|IE|ie" "Galway|IE|ie"
    "Waterford|IE|ie" "Drogheda|IE|ie" "Dundalk|IE|ie" "Sligo|IE|ie"
)

MALTA_CITIES=(
    "Valletta|MT|mt" "Birkirkara|MT|mt" "Sliema|MT|mt" "Mosta|MT|mt"
    "Qormi|MT|mt" "St Julians|MT|mt" "Żabbar|MT|mt" "Rabat|MT|mt"
)

POLAND_CITIES=(
    "Warszawa|PL|pl" "Kraków|PL|pl" "Łódź|PL|pl" "Wrocław|PL|pl" "Poznań|PL|pl"
    "Gdańsk|PL|pl" "Szczecin|PL|pl" "Bydgoszcz|PL|pl" "Lublin|PL|pl" "Białystok|PL|pl"
    "Katowice|PL|pl" "Gdynia|PL|pl" "Częstochowa|PL|pl" "Radom|PL|pl" "Sosnowiec|PL|pl"
    "Toruń|PL|pl" "Kielce|PL|pl" "Rzeszów|PL|pl" "Gliwice|PL|pl" "Zabrze|PL|pl"
)

ALL_CITIES=(
    "${SWEDEN_CITIES[@]}"
    "${NETHERLANDS_CITIES[@]}"
    "${DENMARK_CITIES[@]}"
    "${FINLAND_CITIES[@]}"
    "${IRELAND_CITIES[@]}"
    "${MALTA_CITIES[@]}"
    "${POLAND_CITIES[@]}"
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
    echo -e "${YELLOW}Usage: ./scripts/eu_top_tier_ice_cream_confectionery_scraper.sh${NC}"
    exit 1
fi

if [ -f "../main.py" ]; then
    cd ..
fi

get_search_terms_for_country_group() {
    local country_group="$1"
    local terms=()

    case "$country_group" in
        se)
            terms=("artisan_ice_cream_sv" "artisan_ice_cream_en_se" "ice_cream_bar_sv" "ice_cream_producer_sv" "confectionery_sv" "gelato_shop_en_se")
            ;;
        nl)
            terms=("artisan_ice_cream_nl" "artisan_ice_cream_variant_nl" "ice_cream_maker_nl" "ice_cream_producer_nl" "confectionery_nl" "chocolatier_nl")
            ;;
        dk)
            terms=("artisan_ice_cream_da" "artisan_ice_cream_en_da" "ice_cream_shop_da" "ice_cream_producer_da" "confectionery_da" "dessert_shop_da")
            ;;
        fi)
            terms=("artisan_ice_cream_fi" "artisan_ice_cream_en_fi" "ice_cream_bar_fi" "ice_cream_producer_fi" "ice_cream_shop_fi" "confectionery_fi")
            ;;
        ie)
            terms=("artisan_ice_cream_ie" "artisan_gelato_ie" "ice_cream_manufacturer_ie" "ice_cream_producer_ie" "confectionery_ie" "dessert_shop_ie")
            ;;
        mt)
            terms=("artisan_ice_cream_mt" "gelato_shop_mt" "ice_cream_manufacturer_mt" "confectionery_mt" "dessert_shop_mt" "cake_shop_mt")
            ;;
        pl)
            terms=("confectionery_pl")
            ;;
    esac

    echo "${terms[@]}"
}

get_country_folder_name() {
    local country_iso="$1"

    case "$country_iso" in
        SE) echo "Sweden" ;;
        NL) echo "Netherlands" ;;
        DK) echo "Denmark" ;;
        FI) echo "Finland" ;;
        IE) echo "Ireland" ;;
        MT) echo "Malta" ;;
        PL) echo "Poland" ;;
        *) echo "$country_iso" ;;
    esac
}

check_existing_results() {
    local city="$1"
    local keyword="$2"

    local result
    result=$(python scripts/check_existing_keyword.py "$city" "$keyword" 2>/dev/null)

    if [ -z "$result" ]; then
        echo -e "${BLUE}○${NC} No usable data - ${BLUE}SCRAPING${NC}"
        return 1
    fi

    local action
    action=$(echo "$result" | cut -d: -f1)

    local row_count
    row_count=$(echo "$result" | awk -F: '{print $NF}')
    if ! [[ "$row_count" =~ ^[0-9]+$ ]]; then
        row_count=0
    fi

    if [ "$action" = "SKIP" ] && [ "$row_count" -ge "$MIN_EXISTING_RESULTS_TO_SKIP" ]; then
        echo -e "${GREEN}✓${NC} Existing data found (${row_count}) - ${GREEN}SKIPPING${NC}"
        return 0
    fi

    if [ "$action" = "SKIP" ] && [ "$row_count" -lt "$MIN_EXISTING_RESULTS_TO_SKIP" ]; then
        echo -e "${YELLOW}○${NC} Existing data too low (${row_count} < ${MIN_EXISTING_RESULTS_TO_SKIP}) - ${BLUE}RE-SCRAPING${NC}"
    else
        echo -e "${BLUE}○${NC} No usable data - ${BLUE}SCRAPING${NC}"
    fi

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
echo -e "${CYAN}      EU TOP-TIER ICE CREAM + CONFECTIONERY SCRAPER      ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
if [ "$COUNTRY_FILTER" = "all" ]; then
    echo -e "${YELLOW}Countries:${NC} Sweden, Netherlands, Denmark, Finland, Ireland, Malta, Poland(cukiernia)"
else
    echo -e "${YELLOW}Country Filter:${NC} $COUNTRY_FILTER"
fi
echo -e "${YELLOW}Total Cities:${NC} ${#SELECTED_CITIES[@]} cities"
echo -e "${YELLOW}Total Searches:${NC} $total_combinations"
echo -e "${YELLOW}Max Results per Search:${NC} $MAX_RESULTS"
echo -e "${YELLOW}Search Radius:${NC} ${RADIUS_KM}km"
echo -e "${YELLOW}Email Extraction:${NC} ENABLED"
echo -e "${YELLOW}Skip Threshold:${NC} Existing files with >= ${MIN_EXISTING_RESULTS_TO_SKIP} rows"
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

PROGRESS_LOG="data/eu_top_tier_ice_cream_confectionery_progress.log"
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
echo -e "${GREEN}✓ EU top-tier ice cream + confectionery scraper completed!${NC}"
echo ""
echo -e "${YELLOW}Tip:${NC} To resume from a specific point, use: $0 --start-from <number>"
echo ""
