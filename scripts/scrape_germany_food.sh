#!/bin/bash

# ============================================
# GERMAN WHOLESALER & SUPPLIER BATCH SCRAPER
# ============================================
# Scrapes German cities for spice wholesalers, baking wholesalers,
# ingredient suppliers, and HoReCa suppliers
#
# Features:
#   - Checks existing results and skips if > 1 result found
#   - Re-scrapes if <= 1 result or no data exists
#   - Language: German (de)
#
# Usage:
#   ./scripts/scrape_germany_food.sh
# ============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Business types to scrape
BUSINESS_TYPES=("spice_wholesaler" "baking_wholesaler" "ingredient_supplier" "horeca_supplier")

# Cities to scrape
CITIES=(
    "Berlin"
    "Hamburg"
    "München"
    "Köln"
    "Frankfurt am Main"
    "Stuttgart"
    "Düsseldorf"
    "Leipzig"
    "Dortmund"
    "Essen"
    "Bremen"
    "Dresden"
    "Hannover"
    "Nürnberg"
    "Duisburg"
    "Bochum"
    "Wuppertal"
    "Bielefeld"
    "Bonn"
    "Münster"
    "Karlsruhe"
    "Mannheim"
    "Augsburg"
    "Wiesbaden"
    "Gelsenkirchen"
    "Mönchengladbach"
    "Braunschweig"
    "Chemnitz"
    "Kiel"
    "Aachen"
    "Halle (Saale)"
    "Magdeburg"
    "Freiburg im Breisgau"
    "Krefeld"
    "Lübeck"
    "Oberhausen"
    "Erfurt"
    "Mainz"
    "Rostock"
    "Kassel"
    "Hagen"
    "Saarbrücken"
    "Hamm"
    "Mülheim an der Ruhr"
    "Ludwigshafen am Rhein"
    "Leverkusen"
    "Oldenburg"
    "Osnabrück"
    "Solingen"
    "Heidelberg"
    "Herne"
    "Neuss"
    "Darmstadt"
    "Paderborn"
    "Regensburg"
    "Ingolstadt"
    "Würzburg"
    "Ulm"
    "Heilbronn"
    "Reutlingen"
    "Tübingen"
    "Konstanz"
    "Villingen-Schwenningen"
    "Offenburg"
    "Baden-Baden"
    "Landshut"
    "Passau"
    "Rosenheim"
    "Kempten (Allgäu)"
    "Garmisch-Partenkirchen"
    "Flensburg"
    "Husum"
    "Itzehoe"
    "Cuxhaven"
    "Bremerhaven"
    "Wilhelmshaven"
    "Emden"
    "Leer"
    "Lüneburg"
    "Celle"
    "Wolfsburg"
    "Salzgitter"
    "Göttingen"
    "Fulda"
    "Gießen"
    "Marburg"
    "Siegen"
    "Coblenz (Koblenz)"
    "Trier"
    "Bitburg"
    "Pforzheim"
    "Schwäbisch Hall"
    "Aalen"
    "Weiden in der Oberpfalz"
    "Bayreuth"
    "Hof"
    "Zwickau"
    "Plauen"
    "Görlitz"
    "Bautzen"
)

# Configuration
LANGUAGE="de"
FIND_EMAILS="--find-emails"
MAX_RESULTS=100

# Check if running from scripts directory
if [ ! -f "../main.py" ] && [ ! -f "main.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/scrape_germany_food.sh${NC}"
    exit 1
fi

# If running from scripts directory, go to parent
if [ -f "../main.py" ]; then
    cd ..
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}       GERMAN FOOD BUSINESS BATCH SCRAPER              ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Language:${NC} $LANGUAGE"
echo -e "${YELLOW}Business Types:${NC} ${BUSINESS_TYPES[*]}"
echo -e "${YELLOW}Cities:${NC} ${#CITIES[@]} cities"
echo -e "${YELLOW}Max Results per Search:${NC} $MAX_RESULTS"
echo -e "${YELLOW}Email Extraction:${NC} ENABLED"
echo ""
echo -e "${YELLOW}Working directory:${NC} $(pwd)"
echo ""

# Function to check if results exist and have more than 3 entries
check_existing_results() {
    local city="$1"
    local business_type="$2"
    local language="$3"

    # Use Python script to check (handles translations correctly)
    local result=$(python scripts/check_existing.py "$city" "$business_type" "$language" 2>/dev/null)

    # Parse result: "SKIP:message:count" or "SCRAPE:message:count"
    local action=$(echo "$result" | cut -d: -f1)
    local message=$(echo "$result" | cut -d: -f2)
    local count=$(echo "$result" | cut -d: -f3)

    if [ "$action" = "SKIP" ]; then
        echo -e "${GREEN}✓${NC} $city - $business_type: $message - ${GREEN}SKIPPING${NC}"
        return 0  # Skip
    else
        echo -e "${BLUE}○${NC} $city - $business_type: $message - ${BLUE}SCRAPING${NC}"
        return 1  # Scrape
    fi
}

# Track statistics
total_combinations=$((${#CITIES[@]} * ${#BUSINESS_TYPES[@]}))
current=0
skipped=0
scraped=0

echo -e "${CYAN}Starting batch scraping...${NC}"
echo ""

# Main scraping loop
for business_type in "${BUSINESS_TYPES[@]}"; do
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Business Type: $business_type${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    for city in "${CITIES[@]}"; do
        ((current++))
        echo -e "${YELLOW}[$current/$total_combinations]${NC} Checking: $city"

        # Check if we should skip this combination
        if check_existing_results "$city" "$business_type" "$LANGUAGE"; then
            ((skipped++))
            continue
        fi

        # Run scraper
        echo -e "${BLUE}→${NC} Scraping $city ($business_type)..."

        # Run python and capture exit code
        python main.py --city "$city" --business-type "$business_type" --language "$LANGUAGE" $FIND_EMAILS --max-results $MAX_RESULTS
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Completed: $city - $business_type"
            ((scraped++))
        else
            echo -e "${RED}✗${NC} Failed: $city - $business_type (exit code: $exit_code)"
        fi

        echo ""
        sleep 2  # Short delay between scrapes
    done

    echo ""
done

# Final summary
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}                    SUMMARY                                 ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Total Combinations:${NC} $total_combinations"
echo -e "${GREEN}Successfully Scraped:${NC} $scraped"
echo -e "${GREEN}Skipped (existing > 1):${NC} $skipped"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}All results saved to:${NC} data/leads/"
echo ""
