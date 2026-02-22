#!/bin/bash

# ============================================
# DUTCH + SPAIN ICE CREAM BATCH SCRAPER
# ============================================
# Scrapes Netherlands and Spain cities for artisanal ice cream
# makers and manufacturers using Dutch and Spanish keywords.
#
# Features:
#   - Netherlands (nl) + Spain (es)
#   - 500 max results per search
#   - 20km radius
#   - Checks existing results and skips if > 1 result found
#   - Re-scrapes if <= 1 result or no data exists
#   - Progress tracking with resume capability
#   - Resume from specific scrape number with --start-from
#
# Usage:
#   ./scripts/dutch_spain_ice_cream_scraper.sh
#   ./scripts/dutch_spain_ice_cream_scraper.sh --start-from 200
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
            echo "  $0 --start-from 200    # Resume from scrape #200"
            echo "  $0 -s 200              # Short form"
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
    ["artisanal_ice_cream_es"]="heladería artesanal|es"
    ["gelato_producer_es"]="productor de helado artesanal|es"
    ["ice_cream_manufacturer_es"]="fabricante de helados|es"
    ["craft_ice_cream_es"]="helado artesanal|es"

    ["artisanal_ice_cream_nl"]="ambachtelijke ijssalon|nl"
    ["gelato_producer_nl"]="ambachtelijke ijsmaker|nl"
    ["ice_cream_manufacturer_nl"]="ijsproducent|nl"
    ["craft_ice_cream_nl"]="artisanale ijsmaker|nl"
)

SPAIN_CITIES=(
    "Madrid|es" "Barcelona|es" "Valencia|es" "Sevilla|es" "Zaragoza|es"
    "Málaga|es" "Murcia|es" "Palma|es" "Las Palmas de Gran Canaria|es" "Bilbao|es"
    "Alicante|es" "Córdoba|es" "Valladolid|es" "Vigo|es" "Gijón|es"
    "L'Hospitalet de Llobregat|es" "Vitoria-Gasteiz|es" "A Coruña|es" "Elche|es" "Granada|es"
    "Terrassa|es" "Badalona|es" "Oviedo|es" "Sabadell|es" "Cartagena|es"
    "Jerez de la Frontera|es" "Móstoles|es" "Santa Cruz de Tenerife|es" "Pamplona|es" "Almería|es"
    "Alcalá de Henares|es" "Leganés|es" "Getafe|es" "Fuenlabrada|es" "San Sebastián|es"
    "Castellón de la Plana|es" "Burgos|es" "Alcorcón|es" "Santander|es" "Albacete|es"
    "San Cristóbal de La Laguna|es" "Marbella|es" "Logroño|es" "Badajoz|es" "Lleida|es"
    "Salamanca|es" "Tarragona|es" "Torrejón de Ardoz|es" "Huelva|es" "Dos Hermanas|es"
    "Parla|es" "Mataró|es" "Algeciras|es" "Santa Coloma de Gramenet|es" "León|es"
    "Alcobendas|es" "Jaén|es" "Reus|es" "Roquetas de Mar|es" "Cádiz|es"
    "Girona|es" "Ourense|es" "Telde|es" "Rivas-Vaciamadrid|es" "Barakaldo|es"
    "Santiago de Compostela|es" "Lugo|es" "Las Rozas de Madrid|es" "Lorca|es" "Torrevieja|es"
    "San Fernando|es" "Cáceres|es" "San Sebastián de los Reyes|es" "Cornellà de Llobregat|es" "Sant Cugat del Vallès|es"
    "El Puerto de Santa María|es" "Guadalajara|es" "Pozuelo de Alarcón|es" "Melilla|es" "Toledo|es"
    "Mijas|es" "Chiclana de la Frontera|es" "Sant Boi de Llobregat|es" "Ceuta|es" "Torrent|es"
    "El Ejido|es" "Talavera de la Reina|es" "Pontevedra|es" "Fuengirola|es" "Arona|es"
    "Vélez-Málaga|es" "Coslada|es" "Rubí|es" "Manresa|es" "Palencia|es"
    "Orihuela|es" "Getxo|es" "Avilés|es" "Valdemoro|es" "Gandia|es"
    "Alcalá de Guadaíra|es" "Ciudad Real|es" "Santa Lucía de Tirajana|es" "Molina de Segura|es" "Majadahonda|es"
    "Paterna|es" "Benidorm|es" "Estepona|es" "Sanlúcar de Barrameda|es" "Torremolinos|es"
    "Benalmádena|es" "Vilanova i la Geltrú|es" "Castelldefels|es" "Viladecans|es" "Sagunto|es"
    "Ferrol|es" "El Prat de Llobregat|es" "Arrecife|es" "Ponferrada|es" "Collado Villalba|es"
)

NETHERLANDS_CITIES=(
    "Amsterdam|nl" "Rotterdam|nl" "'s-Gravenhage|nl" "Utrecht|nl" "Eindhoven|nl"
    "Tilburg|nl" "Groningen|nl" "Almere|nl" "Breda|nl" "Nijmegen|nl"
    "Enschede|nl" "Haarlem|nl" "Arnhem|nl" "Zaanstad|nl" "Amersfoort|nl"
    "Apeldoorn|nl" "'s-Hertogenbosch|nl" "Hoofddorp|nl" "Maastricht|nl" "Leiden|nl"
    "Dordrecht|nl" "Zoetermeer|nl" "Zwolle|nl" "Deventer|nl" "Delft|nl"
    "Alkmaar|nl" "Heerlen|nl" "Venlo|nl" "Leeuwarden|nl" "Hilversum|nl"
    "Hengelo|nl" "Amstelveen|nl" "Roosendaal|nl" "Purmerend|nl" "Oss|nl"
    "Schiedam|nl" "Spijkenisse|nl" "Helmond|nl" "Vlaardingen|nl" "Almelo|nl"
    "Gouda|nl" "Zaandam|nl" "Lelystad|nl" "Alphen aan den Rijn|nl" "Hoorn|nl"
    "Velsen|nl" "Ede|nl" "Bergen op Zoom|nl" "Capelle aan den IJssel|nl" "Assen|nl"
    "Nieuwegein|nl" "Veenendaal|nl" "Zeist|nl" "Den Helder|nl" "Hardenberg|nl"
    "Emmen|nl" "Oosterhout|nl"
)

ALL_CITIES=(
    "${SPAIN_CITIES[@]}"
    "${NETHERLANDS_CITIES[@]}"
)

if [ ! -f "../main.py" ] && [ ! -f "main.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/dutch_spain_ice_cream_scraper.sh${NC}"
    exit 1
fi

if [ -f "../main.py" ]; then
    cd ..
fi

get_search_terms_for_country() {
    local country_code="$1"
    local terms=()

    case "$country_code" in
        es)
            terms=("artisanal_ice_cream_es" "gelato_producer_es" "ice_cream_manufacturer_es" "craft_ice_cream_es")
            ;;
        nl)
            terms=("artisanal_ice_cream_nl" "gelato_producer_nl" "ice_cream_manufacturer_nl" "craft_ice_cream_nl")
            ;;
    esac

    echo "${terms[@]}"
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
skipped_before_start=0

if [ "$START_FROM" -gt "$total_combinations" ]; then
    echo -e "${RED}Error: --start-from ($START_FROM) exceeds total searches ($total_combinations)${NC}"
    exit 1
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}       DUTCH + SPAIN ICE CREAM BATCH SCRAPER             ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Countries:${NC} Spain (${#SPAIN_CITIES[@]}), Netherlands (${#NETHERLANDS_CITIES[@]})"
echo -e "${YELLOW}Total Cities:${NC} ${#ALL_CITIES[@]} cities"
echo -e "${YELLOW}Search Terms per City:${NC} 4 variations"
echo -e "${YELLOW}Total Searches:${NC} $total_combinations"
echo -e "${YELLOW}Max Results per Search:${NC} $MAX_RESULTS"
echo -e "${YELLOW}Search Radius:${NC} ${RADIUS_KM}km"
echo -e "${YELLOW}Email Extraction:${NC} DISABLED"
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

PROGRESS_LOG="data/dutch_spain_ice_cream_progress.log"
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
        country_code_upper=$(echo "$country_code" | tr '[:lower:]' '[:upper:]')

        python main.py --city "$city" --keyword "$keyword" --language "$language" --country-code "$country_code_upper" --no-find-emails --max-results "$MAX_RESULTS" --radius "$RADIUS_KM" 2>&1
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
echo -e "${GREEN}Skipped (existing):${NC} $skipped"
echo -e "${RED}Failed:${NC} $failed"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}All results saved to:${NC} data/leads/"
echo -e "${YELLOW}Progress log:${NC} $PROGRESS_LOG"
echo ""
echo -e "${GREEN}✓ Dutch + Spain ice cream scraper completed!${NC}"
echo ""
echo -e "${YELLOW}Tip:${NC} To resume from a specific point, use: $0 --start-from <number>"
echo ""
