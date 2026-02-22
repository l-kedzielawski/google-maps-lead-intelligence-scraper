#!/bin/bash

# ============================================
# EASTERN EUROPE ICE CREAM ARTISAN BATCH SCRAPER
# ============================================
# Scrapes 254 cities (40K+ population) across Czech Republic, Slovakia, Hungary,
# Slovenia, Croatia, Bosnia and Herzegovina, Kosovo, Montenegro, Albania, Serbia,
# North Macedonia, Bulgaria, Romania, and Greece for ice cream manufacturers and artisans
#
# Search Terms:
#   - Ice cream manufacturer
#   - Artisanal ice cream
#   - Ice cream maker/producer
#   - Ice cream workshop/manufactory
#
# Features:
#   - 254 cities with 40K+ population
#   - 500 max results per search
#   - 20km radius per city
#   - Checks existing results and skips if > 1 result found
#   - Re-scrapes if <= 1 result or no data exists
#   - Multi-language support (14 languages across 14 countries)
#   - Progress tracking with resume capability
#   - Resume from specific scrape number with --start-from
#
# Total Searches: 1,016 (254 cities × 4 keywords)
# Expected Time: 32-45 hours with email extraction disabled
#
# Coverage:
#   - Czech Republic (27 cities)
#   - Slovakia (9 cities)
#   - Hungary (27 cities)
#   - Slovenia (2 cities)
#   - Croatia (8 cities)
#   - Bosnia and Herzegovina (4 cities)
#   - Kosovo (7 cities)
#   - Montenegro (1 city)
#   - Albania (5 cities)
#   - Serbia (29 cities)
#   - North Macedonia (8 cities)
#   - Bulgaria (39 cities)
#   - Romania (50 cities)
#   - Greece (38 cities)
#
# Usage:
#   ./scripts/eastern_europe_ice_cream_scraper.sh                    # Start from beginning
#   ./scripts/eastern_europe_ice_cream_scraper.sh --start-from 300   # Resume from scrape #300
#   ./scripts/eastern_europe_ice_cream_scraper.sh -s 300             # Short form
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
START_FROM=1  # Default: start from the beginning

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
            echo "  $0 --start-from 300    # Resume from scrape #300"
            echo "  $0 -s 300              # Short form"
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

# Search keywords by country language
# Format: "keyword|language"
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
    
    # Hungary - Hungarian
    ["ice_cream_manufacturer_hu"]="fagylalt gyártó|hu"
    ["artisanal_ice_cream_hu"]="kézműves fagylalt|hu"
    ["ice_cream_maker_hu"]="fagylaltkészítő|hu"
    ["ice_cream_manufactory_hu"]="fagylalt manufaktúra|hu"
    
    # Slovenia - Slovenian
    ["ice_cream_manufacturer_sl"]="proizvajalec sladoleda|sl"
    ["artisanal_ice_cream_sl"]="obrtniška sladoled|sl"
    ["ice_cream_maker_sl"]="sladoledničar|sl"
    ["ice_cream_manufactory_sl"]="sladoled manufaktura|sl"
    
    # Croatia - Croatian
    ["ice_cream_manufacturer_hr"]="proizvođač sladoleda|hr"
    ["artisanal_ice_cream_hr"]="obrtni sladoled|hr"
    ["ice_cream_maker_hr"]="sladoledžinica|hr"
    ["ice_cream_manufactory_hr"]="sladoled manufaktura|hr"
    
    # Bosnia and Herzegovina / Serbia / Montenegro - Serbian/Bosnian
    ["ice_cream_manufacturer_sr"]="proizvođač sladoleda|sr"
    ["artisanal_ice_cream_sr"]="zanatski sladoled|sr"
    ["ice_cream_production_sr"]="proizvodnja sladoleda|sr"
    ["ice_cream_manufactory_sr"]="sladoled manufaktura|sr"
    
    # Kosovo / Albania - Albanian
    ["ice_cream_manufacturer_sq"]="prodhues akullore|sq"
    ["artisanal_ice_cream_sq"]="akullore artizanale|sq"
    ["ice_cream_factory_sq"]="fabrikë akullore|sq"
    ["ice_cream_workshop_sq"]="punishte akullore|sq"
    
    # North Macedonia - Macedonian
    ["ice_cream_manufacturer_mk"]="производител на сладолед|mk"
    ["artisanal_ice_cream_mk"]="занаетчиски сладолед|mk"
    ["ice_cream_manufactory_mk"]="мануфактура сладолед|mk"
    ["ice_cream_workshop_mk"]="артисански сладолед|mk"
    
    # Bulgaria - Bulgarian
    ["ice_cream_manufacturer_bg"]="производител на сладолед|bg"
    ["artisanal_ice_cream_bg"]="занаятчийски сладолед|bg"
    ["ice_cream_factory_bg"]="сладоледна фабрика|bg"
    ["ice_cream_workshop_bg"]="артисански сладолед|bg"
    
    # Romania - Romanian
    ["ice_cream_manufacturer_ro"]="producător înghețată|ro"
    ["artisanal_ice_cream_ro"]="înghețată artizanală|ro"
    ["ice_cream_factory_ro"]="fabrică înghețată|ro"
    ["ice_cream_manufactory_ro"]="manufactura înghețată|ro"
    
    # Greece - Greek
    ["ice_cream_manufacturer_el"]="παραγωγός παγωτού|el"
    ["artisanal_ice_cream_el"]="χειροποίητο παγωτό|el"
    ["ice_cream_workshop_el"]="βιοτεχνία παγωτού|el"
    ["ice_cream_maker_el"]="παγωτατζής|el"
)

# Cities by country with language mapping
# Format: "City|CountryCode"

# CZECH REPUBLIC (27 cities 40K+) - Czech
CZECH_CITIES=(
"Praha|cs" "Brno|cs" "Ostrava|cs" "Plzeň|cs" "Liberec|cs" "Olomouc|cs" "České Budějovice|cs" "Hradec Králové|cs" "Pardubice|cs" "Ústí nad Labem|cs" "Zlín|cs" "Havířov|cs" "Kladno|cs" "Most|cs" "Karlovy Vary|cs" "Opava|cs" "Frýdek-Místek|cs" "Jihlava|cs" "Teplice|cs" "Děčín|cs" "Chomutov|cs" "Přerov|cs" "Prostějov|cs" "Třinec|cs" "Jablonec nad Nisou|cs" "Mladá Boleslav|cs" "Karviná|cs"
)

# SLOVAKIA (9 cities 40K+) - Slovak
SLOVAKIA_CITIES=(
"Bratislava|sk" "Košice|sk" "Prešov|sk" "Žilina|sk" "Nitra|sk" "Banská Bystrica|sk" "Trnava|sk" "Trenčín|sk" "Martin|sk"
)

# HUNGARY (27 cities 40K+) - Hungarian
HUNGARY_CITIES=(
"Budapest|hu" "Debrecen|hu" "Szeged|hu" "Miskolc|hu" "Pécs|hu" "Győr|hu" "Nyíregyháza|hu" "Kecskemét|hu" "Székesfehérvár|hu" "Szombathely|hu" "Érd|hu" "Sopron|hu" "Veszprém|hu" "Szolnok|hu" "Nagykanizsa|hu" "Kaposvár|hu" "Eger|hu" "Zalaegerszeg|hu" "Hódmezővásárhely|hu" "Békéscsaba|hu" "Dunaújváros|hu" "Tatabánya|hu" "Szekszárd|hu" "Cegléd|hu" "Szigetszentmiklós|hu" "Törökbálint|hu" "Hajdúböszörmény|hu"
)

# SLOVENIA (2 cities 40K+) - Slovenian
SLOVENIA_CITIES=(
"Ljubljana|sl" "Maribor|sl"
)

# CROATIA (8 cities 40K+) - Croatian
CROATIA_CITIES=(
"Zagreb|hr" "Split|hr" "Rijeka|hr" "Osijek|hr" "Zadar|hr" "Pula|hr" "Slavonski Brod|hr" "Karlovac|hr"
)

# BOSNIA AND HERZEGOVINA (4 cities 40K+) - Serbian/Bosnian
BOSNIA_CITIES=(
"Sarajevo|sr" "Banja Luka|sr" "Tuzla|sr" "Zenica|sr"
)

# KOSOVO (7 cities 40K+) - Albanian
KOSOVO_CITIES=(
"Prishtinë|sq" "Prizren|sq" "Gjilan|sq" "Ferizaj|sq" "Gjakovë|sq" "Pejë|sq" "Fushë Kosovë|sq"
)

# MONTENEGRO (1 city 40K+) - Serbian
MONTENEGRO_CITIES=(
"Podgorica|sr"
)

# ALBANIA (5 cities 40K+) - Albanian
ALBANIA_CITIES=(
"Tiranë|sq" "Durrës|sq" "Vlorë|sq" "Elbasan|sq" "Shkodër|sq"
)

# SERBIA (29 cities 40K+) - Serbian
SERBIA_CITIES=(
"Beograd|sr" "Novi Sad|sr" "Niš|sr" "Kragujevac|sr" "Subotica|sr" "Pančevo|sr" "Novi Pazar|sr" "Čačak|sr" "Zrenjanin|sr" "Leskovac|sr" "Kraljevo|sr" "Kruševac|sr" "Šabac|sr" "Smederevo|sr" "Sombor|sr" "Vranje|sr" "Užice|sr" "Valjevo|sr" "Jagodina|sr" "Pirot|sr" "Zaječar|sr" "Sremska Mitrovica|sr" "Kikinda|sr" "Senta|sr" "Vršac|sr" "Smederevska Palanka|sr" "Bor|sr" "Požarevac|sr" "Prokuplje|sr"
)

# NORTH MACEDONIA (8 cities 40K+) - Macedonian
NORTH_MACEDONIA_CITIES=(
"Skopje|mk" "Kumanovo|mk" "Bitola|mk" "Prilep|mk" "Tetovo|mk" "Štip|mk" "Veles|mk" "Ohrid|mk"
)

# BULGARIA (39 cities 40K+) - Bulgarian
BULGARIA_CITIES=(
"Sofia|bg" "Plovdiv|bg" "Varna|bg" "Burgas|bg" "Ruse|bg" "Stara Zagora|bg" "Pleven|bg" "Sliven|bg" "Dobrich|bg" "Shumen|bg" "Pernik|bg" "Haskovo|bg" "Yambol|bg" "Pazardzhik|bg" "Blagoevgrad|bg" "Veliko Tarnovo|bg" "Vratsa|bg" "Gabrovo|bg" "Asenovgrad|bg" "Vidin|bg" "Kazanlak|bg" "Kardzhali|bg" "Montana|bg" "Dimitrovgrad|bg" "Targovishte|bg" "Lovech|bg" "Silistra|bg" "Dupnitsa|bg" "Svishtov|bg" "Razgrad|bg" "Gorna Oryahovitsa|bg" "Smolyan|bg" "Petrich|bg" "Kyustendil|bg" "Sevlievo|bg" "Sandanski|bg" "Lom|bg" "Karlovo|bg" "Velingrad|bg"
)

# ROMANIA (50 cities 40K+) - Romanian
ROMANIA_CITIES=(
"București|ro" "Cluj-Napoca|ro" "Iași|ro" "Constanța|ro" "Timișoara|ro" "Brașov|ro" "Craiova|ro" "Galați|ro" "Oradea|ro" "Ploiești|ro" "Brăila|ro" "Arad|ro" "Pitești|ro" "Bacău|ro" "Sibiu|ro" "Târgu Mureș|ro" "Baia Mare|ro" "Buzău|ro" "Satu Mare|ro" "Botoșani|ro" "Râmnicu Vâlcea|ro" "Suceava|ro" "Piatra Neamț|ro" "Drobeta-Turnu Severin|ro" "Focșani|ro" "Târgoviște|ro" "Tulcea|ro" "Târgu Jiu|ro" "Reșița|ro" "Bistrița|ro" "Slatina|ro" "Călărași|ro" "Giurgiu|ro" "Vaslui|ro" "Roman|ro" "Mediaș|ro" "Hunedoara|ro" "Deva|ro" "Zalău|ro" "Sfântu Gheorghe|ro" "Slobozia|ro" "Petroșani|ro" "Lupeni|ro" "Turda|ro" "Voluntari|ro" "Popești-Leordeni|ro" "Alexandria|ro" "Alba Iulia|ro" "Bârlad|ro" "Câmpina|ro"
)

# GREECE (38 cities 40K+) - Greek
GREECE_CITIES=(
"Athínai|el" "Thessaloníki|el" "Pátrai|el" "Irákleion|el" "Lárisa|el" "Vólos|el" "Acharnaí|el" "Chanía|el" "Ioánnina|el" "Chalkís|el" "Agrínion|el" "Kateríni|el" "Kalamáta|el" "Sérrai|el" "Xánthi|el" "Tríkala|el" "Lamía|el" "Alexándroupolis|el" "Véroia|el" "Ródos|el" "Komotiní|el" "Chíos|el" "Réthymnon|el" "Salamís|el" "Dráma|el" "Ptolemaḯs|el" "Kozání|el" "Kavála|el" "Kérkyra|el" "Kórinthos|el" "Giannitsá|el" "Kardítsa|el" "Préveza|el" "Náfplio|el" "Trípolís|el" "Spárti|el" "Árgos|el" "Édessa|el"
)

# Combine all cities
ALL_CITIES=(
    "${CZECH_CITIES[@]}"
    "${SLOVAKIA_CITIES[@]}"
    "${HUNGARY_CITIES[@]}"
    "${SLOVENIA_CITIES[@]}"
    "${CROATIA_CITIES[@]}"
    "${BOSNIA_CITIES[@]}"
    "${KOSOVO_CITIES[@]}"
    "${MONTENEGRO_CITIES[@]}"
    "${ALBANIA_CITIES[@]}"
    "${SERBIA_CITIES[@]}"
    "${NORTH_MACEDONIA_CITIES[@]}"
    "${BULGARIA_CITIES[@]}"
    "${ROMANIA_CITIES[@]}"
    "${GREECE_CITIES[@]}"
)

# Check if running from scripts directory
if [ ! -f "../main.py" ] && [ ! -f "main.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/eastern_europe_ice_cream_scraper.sh${NC}"
    exit 1
fi

# If running from scripts directory, go to parent
if [ -f "../main.py" ]; then
    cd ..
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  EASTERN EUROPE ICE CREAM ARTISAN BATCH SCRAPER        ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Countries:${NC} Czech Republic (27), Slovakia (9), Hungary (27),"
echo -e "           Slovenia (2), Croatia (8), Bosnia and Herzegovina (4),"
echo -e "           Kosovo (7), Montenegro (1), Albania (5), Serbia (29),"
echo -e "           North Macedonia (8), Bulgaria (39), Romania (50), Greece (38)"
echo -e "${YELLOW}Total Cities:${NC} ${#ALL_CITIES[@]} cities (40K+ population)"
echo -e "${YELLOW}Search Terms per City:${NC} 4 variations"
echo -e "${YELLOW}Total Searches:${NC} $((${#ALL_CITIES[@]} * 4))"
echo -e "${YELLOW}Max Results per Search:${NC} $MAX_RESULTS"
echo -e "${YELLOW}Search Radius:${NC} 20km"
echo -e "${YELLOW}Email Extraction:${NC} DISABLED"
if [ "$START_FROM" -gt 1 ]; then
    echo -e "${MAGENTA}Starting From:${NC} Scrape #$START_FROM (skipping first $((START_FROM - 1)) scrapes)"
fi
echo ""
echo -e "${YELLOW}Working directory:${NC} $(pwd)"
echo ""

# Function to get country-specific search terms
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
        hu)
            terms=("ice_cream_manufacturer_hu" "artisanal_ice_cream_hu" "ice_cream_maker_hu" "ice_cream_manufactory_hu")
            ;;
        sl)
            terms=("ice_cream_manufacturer_sl" "artisanal_ice_cream_sl" "ice_cream_maker_sl" "ice_cream_manufactory_sl")
            ;;
        hr)
            terms=("ice_cream_manufacturer_hr" "artisanal_ice_cream_hr" "ice_cream_maker_hr" "ice_cream_manufactory_hr")
            ;;
        sr)
            terms=("ice_cream_manufacturer_sr" "artisanal_ice_cream_sr" "ice_cream_production_sr" "ice_cream_manufactory_sr")
            ;;
        sq)
            terms=("ice_cream_manufacturer_sq" "artisanal_ice_cream_sq" "ice_cream_factory_sq" "ice_cream_workshop_sq")
            ;;
        mk)
            terms=("ice_cream_manufacturer_mk" "artisanal_ice_cream_mk" "ice_cream_manufactory_mk" "ice_cream_workshop_mk")
            ;;
        bg)
            terms=("ice_cream_manufacturer_bg" "artisanal_ice_cream_bg" "ice_cream_factory_bg" "ice_cream_workshop_bg")
            ;;
        ro)
            terms=("ice_cream_manufacturer_ro" "artisanal_ice_cream_ro" "ice_cream_factory_ro" "ice_cream_manufactory_ro")
            ;;
        el)
            terms=("ice_cream_manufacturer_el" "artisanal_ice_cream_el" "ice_cream_workshop_el" "ice_cream_maker_el")
            ;;
    esac
    
    echo "${terms[@]}"
}

# Function to map language code to ISO country code for phone parsing
get_phone_country_code() {
    local language_code="$1"

    case "$language_code" in
        cs) echo "CZ" ;;
        sk) echo "SK" ;;
        hu) echo "HU" ;;
        sl) echo "SI" ;;
        hr) echo "HR" ;;
        sr) echo "RS" ;;
        sq) echo "AL" ;;
        mk) echo "MK" ;;
        bg) echo "BG" ;;
        ro) echo "RO" ;;
        el) echo "GR" ;;
        *) echo "$(echo "$language_code" | tr '[:lower:]' '[:upper:]')" ;;
    esac
}

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
total_combinations=$((${#ALL_CITIES[@]} * 4))  # 4 search terms per city
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
PROGRESS_LOG="data/eastern_europe_ice_cream_progress.log"
mkdir -p data
touch "$PROGRESS_LOG"

# Main scraping loop
city_header_printed=false
for city_entry in "${ALL_CITIES[@]}"; do
    # Parse city and country code
    IFS='|' read -r city country_code <<< "$city_entry"
    
    city_header_printed=false
    
    # Get search terms for this country
    search_term_keys=$(get_search_terms_for_country "$country_code")
    
    for term_key in $search_term_keys; do
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
        
        # Convert language code to ISO country code for phone parsing
        country_code_upper=$(get_phone_country_code "$language")
        
        # Run python and capture output
        python main.py --city "$city" --keyword "$keyword" --language "$language" --country-code "$country_code_upper" --no-find-emails --max-results $MAX_RESULTS --radius 20 2>&1
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
echo -e "${CYAN}                    FINAL SUMMARY                           ${NC}"
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
echo -e "${GREEN}✓ Eastern Europe ice cream scraper completed!${NC}"
echo ""
echo -e "${YELLOW}Tip:${NC} To resume from a specific point, use: $0 --start-from <number>"
echo ""
