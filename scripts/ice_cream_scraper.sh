#!/bin/bash

# ============================================
# EUROPEAN ICE CREAM ARTISAN BATCH SCRAPER
# ============================================
# Scrapes 639 cities (50K+ population) across Germany, Austria, Spain, Italy,
# Switzerland, Portugal, Netherlands, and Belgium for artisanal ice cream businesses
#
# Search Terms:
#   - Artisanal ice cream / craft ice cream
#   - Gelato producer
#   - Ice cream manufacturer
#   - Ice cream producer
#
# Features:
#   - 639 cities with 50K+ population
#   - 500 max results per search
#   - Checks existing results and skips if > 1 result found
#   - Re-scrapes if <= 1 result or no data exists
#   - Multi-language support (DE, IT, ES, PT, NL, FR)
#   - Progress tracking with resume capability
#   - Resume from specific scrape number with --start-from
#
# Total Searches: 2,556 (639 cities × 4 keywords)
# Expected Time: 80-110 hours with email extraction
#
# Usage:
#   ./scripts/ice_cream_scraper.sh                    # Start from beginning
#   ./scripts/ice_cream_scraper.sh --start-from 300   # Resume from scrape #300
#   ./scripts/ice_cream_scraper.sh -s 300             # Short form
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
MAX_RESULTS=500  # Increased from 100 to 500
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
    # Germany - German
    ["artisanal_ice_cream_de"]="handwerkliche eisdiele|de"
    ["gelato_producer_de"]="gelato hersteller|de"
    ["ice_cream_manufacturer_de"]="eishersteller|de"
    ["craft_ice_cream_de"]="eismanufaktur|de"
    
    # Austria - German
    ["artisanal_ice_cream_at"]="handwerkliche eisdiele|de"
    ["gelato_producer_at"]="gelato produzent|de"
    ["ice_cream_manufacturer_at"]="eisproduzent|de"
    ["craft_ice_cream_at"]="eismanufaktur|de"
    
    # Switzerland - German/French/Italian
    ["artisanal_ice_cream_ch_de"]="handwerkliche eisdiele|de"
    ["gelato_producer_ch_de"]="gelato hersteller|de"
    ["artisanal_ice_cream_ch_fr"]="glacier artisanal|fr"
    ["ice_cream_producer_ch_fr"]="producteur de glace artisanale|fr"
    
    # Italy - Italian
    ["artisanal_gelato_it"]="gelateria artigianale|it"
    ["gelato_producer_it"]="produttore gelato artigianale|it"
    ["ice_cream_manufacturer_it"]="produttore di gelato|it"
    ["craft_gelato_it"]="laboratorio gelato|it"
    
    # Spain - Spanish
    ["artisanal_ice_cream_es"]="heladería artesanal|es"
    ["gelato_producer_es"]="productor de helado artesanal|es"
    ["ice_cream_manufacturer_es"]="fabricante de helados|es"
    ["craft_ice_cream_es"]="helado artesanal|es"
    
    # Portugal - Portuguese
    ["artisanal_ice_cream_pt"]="gelado artesanal|pt"
    ["gelato_producer_pt"]="produtor de gelado artesanal|pt"
    ["ice_cream_manufacturer_pt"]="fabricante de gelados|pt"
    ["craft_ice_cream_pt"]="gelados artesanais|pt"
    
    # Netherlands - Dutch
    ["artisanal_ice_cream_nl"]="ambachtelijke ijssalon|nl"
    ["gelato_producer_nl"]="ambachtelijke ijsmaker|nl"
    ["ice_cream_manufacturer_nl"]="ijsproducent|nl"
    ["craft_ice_cream_nl"]="artisanale ijsmaker|nl"
    
    # Belgium - Dutch/French
    ["artisanal_ice_cream_be_nl"]="ambachtelijke ijssalon|nl"
    ["gelato_producer_be_nl"]="ambachtelijke ijsmaker|nl"
    ["artisanal_ice_cream_be_fr"]="glacier artisanal|fr"
    ["ice_cream_producer_be_fr"]="producteur de glace artisanale|fr"
)

# Cities by country with language mapping
# Format: "City|CountryCode"

# GERMANY (191 cities) - German
GERMANY_CITIES=(
"Berlin|de" "Hamburg|de" "München|de" "Köln|de" "Frankfurt am Main|de" "Düsseldorf|de" "Stuttgart|de" "Leipzig|de" "Dortmund|de" "Bremen|de" "Essen|de" "Dresden|de" "Hannover|de" "Nürnberg|de" "Duisburg|de" "Bonn|de" "Bochum|de" "Mannheim|de" "Wuppertal|de" "Bielefeld|de" "Karlsruhe|de" "Münster|de" "Mönchengladbach|de" "Augsburg|de" "Chemnitz|de" "Braunschweig|de" "Aachen|de" "Magdeburg|de" "Kiel|de" "Krefeld|de" "Mainz|de" "Freiburg im Breisgau|de" "Lübeck|de" "Oberhausen|de" "Erfurt|de" "Rostock|de" "Kassel|de" "Hagen|de" "Halle (Saale)|de" "Hamm|de" "Saarbrücken|de" "Mülheim an der Ruhr|de" "Ludwigshafen am Rhein|de" "Oldenburg (Oldb)|de" "Leverkusen|de" "Darmstadt|de" "Osnabrück|de" "Solingen|de" "Herne|de" "Neuss|de" "Paderborn|de" "Heidelberg|de" "Regensburg|de" "Ingolstadt|de" "Würzburg|de" "Fürth|de" "Offenbach am Main|de" "Ulm|de" "Wolfsburg|de" "Heilbronn|de" "Göttingen|de" "Bottrop|de" "Reutlingen|de" "Bremerhaven|de" "Remscheid|de" "Koblenz|de" "Erlangen|de" "Recklinghausen|de" "Bergisch Gladbach|de" "Jena|de" "Trier|de" "Salzgitter|de" "Siegen|de" "Gütersloh|de" "Hildesheim|de" "Cottbus (Chóśebuz)|de" "Kaiserslautern|de" "Witten|de" "Hanau|de" "Esslingen am Neckar|de" "Ludwigsburg|de" "Iserlohn|de" "Flensburg|de" "Schwerin|de" "Tübingen|de" "Düren|de" "Gera|de" "Ratingen|de" "Moers|de" "Gießen|de" "Lünen|de" "Konstanz|de" "Worms|de" "Marl|de" "Velbert|de" "Delmenhorst|de" "Norderstedt|de" "Neumünster|de" "Viersen|de" "Rheine|de" "Bamberg|de" "Troisdorf|de" "Minden|de" "Dessau-Roßlau|de" "Brandenburg an der Havel|de" "Gladbeck|de" "Arnsberg|de" "Detmold|de" "Lüneburg|de" "Lüdenscheid|de" "Bayreuth|de" "Castrop-Rauxel|de" "Aschaffenburg|de" "Dorsten|de" "Landshut|de" "Kempten (Allgäu)|de" "Neuwied|de" "Celle|de" "Dinslaken|de" "Plauen|de" "Kerpen|de" "Grevenbroich|de" "Villingen-Schwenningen|de" "Rüsselsheim am Main|de" "Fulda|de" "Rosenheim|de" "Schwäbisch Gmünd|de" "Dormagen|de" "Friedrichshafen|de" "Bocholt|de" "Offenburg|de" "Euskirchen|de" "Rastatt|de" "Sindelfingen|de" "Langenfeld (Rheinland)|de" "Meerbusch|de" "Herten|de" "Greifswald|de" "Lingen (Ems)|de" "Baden-Baden|de" "Bad Homburg vor der Höhe|de" "Neubrandenburg|de" "Hürth|de" "Stolberg (Rhld.)|de" "Hilden|de" "Waiblingen|de" "Eschweiler|de" "Frankfurt (Oder)|de" "Göppingen|de" "Wetzlar|de" "Garbsen|de" "Langenhagen|de" "Hameln|de" "Görlitz|de" "Stralsund|de" "Schweinfurt|de" "Neustadt an der Weinstraße|de" "Menden (Sauerland)|de" "Marburg|de" "Hattingen|de" "Kleve|de" "Unna|de" "Lörrach|de" "Lippstadt|de" "Passau|de" "Ibbenbüren|de" "Ravensburg|de" "Böblingen|de" "Gummersbach|de" "Sankt Augustin|de" "Pulheim|de" "Bad Salzuflen|de" "Bad Oeynhausen|de" "Gronau (Westf.)|de" "Ahlen|de" "Frechen|de" "Heidenheim an der Brenz|de" "Lahr/Schwarzwald|de" "Peine|de" "Bergheim|de" "Bad Kreuznach|de" "Herford|de" "Nordhorn|de" "Wilhelmshaven|de" "Aalen|de" "Neu-Ulm|de" "Zwickau|de" "Weimar|de" "Wesel|de"
)

# AUSTRIA (10 cities) - German
AUSTRIA_CITIES=(
"Wien|de" "Graz|de" "Linz|de" "Salzburg|de" "Innsbruck|de" "Klagenfurt|de" "Villach|de" "Wels|de" "Sankt Pölten|de" "Dornbirn|de"
)

# ITALY (140 cities) - Italian
ITALY_CITIES=(
"Roma|it" "Milano|it" "Napoli|it" "Torino|it" "Palermo|it" "Genova|it" "Bologna|it" "Firenze|it" "Bari|it" "Catania|it" "Verona|it" "Venezia|it" "Messina|it" "Padova|it" "Trieste|it" "Brescia|it" "Parma|it" "Taranto|it" "Prato|it" "Modena|it" "Reggio Calabria|it" "Reggio Emilia|it" "Perugia|it" "Livorno|it" "Ravenna|it" "Cagliari|it" "Foggia|it" "Rimini|it" "Salerno|it" "Ferrara|it" "Sassari|it" "Latina|it" "Giugliano in Campania|it" "Monza|it" "Siracusa|it" "Pescara|it" "Bergamo|it" "Bolzano|it" "Forlì|it" "Trento|it" "Vicenza|it" "Terni|it" "Novara|it" "Piacenza|it" "Ancona|it" "Andria|it" "Arezzo|it" "Udine|it" "Cesena|it" "Lecce|it" "Pesaro|it" "Alessandria|it" "Barletta|it" "La Spezia|it" "Pisa|it" "Pistoia|it" "Guidonia Montecelio|it" "Lucca|it" "Brindisi|it" "Como|it" "Busto Arsizio|it" "Catanzaro|it" "Varese|it" "Treviso|it" "Marsala|it" "Grosseto|it" "Pozzuoli|it" "Asti|it" "Sesto San Giovanni|it" "Casoria|it" "Carpi|it" "Cinisello Balsamo|it" "Aprilia|it" "Caserta|it" "Altamura|it" "Cremona|it" "Ragusa|it" "Gela|it" "Vigevano|it" "Trapani|it" "Pavia|it" "Matera|it" "Lido di Ostia|it" "Fiumicino|it" "Molfetta|it" "Carrara|it" "Velletri|it" "Imola|it" "Viterbo|it" "Anzio|it" "Benevento|it" "Castellammare di Stabia|it" "Acerra|it" "Crotone|it" "Caltanissetta|it" "Cuneo|it" "Afragola|it" "Agrigento|it" "Savona|it" "Faenza|it" "Trani|it" "Cerignola|it" "Civitavecchia|it" "Fano|it" "Avellino|it" "Battipaglia|it" "Vittoria|it" "Marano di Napoli|it" "Torre del Greco|it" "Portici|it" "Cosenza|it" "Potenza|it" "Ercolano|it" "Bitonto|it" "Bagheria|it" "Acireale|it" "Sanremo|it" "Pomezia|it" "Bisceglie|it" "Aversa|it" "Viareggio|it" "Legnano|it" "Scafati|it" "Rho|it" "Cologno Monzese|it" "Collegno|it" "Manfredonia|it" "Mazara del Vallo|it" "Quartu Sant'Elena|it" "Sesto Fiorentino|it" "Montesilvano|it" "Rovigo|it" "Corigliano-Rossano|it" "Ardea|it" "Scandicci|it" "Olbia|it" "Casalnuovo di Napoli|it" "San Severo|it" "Moncalieri|it" "Rozzano|it" "Cerveteri|it"
)

# SPAIN (120 cities) - Spanish
SPAIN_CITIES=(
"Madrid|es" "Barcelona|es" "Valencia|es" "Sevilla|es" "Zaragoza|es" "Málaga|es" "Murcia|es" "Palma|es" "Las Palmas de Gran Canaria|es" "Bilbao|es" "Alicante|es" "Córdoba|es" "Valladolid|es" "Vigo|es" "Gijón|es" "L'Hospitalet de Llobregat|es" "Vitoria-Gasteiz|es" "A Coruña|es" "Elche|es" "Granada|es" "Terrassa|es" "Badalona|es" "Oviedo|es" "Sabadell|es" "Cartagena|es" "Jerez de la Frontera|es" "Móstoles|es" "Santa Cruz de Tenerife|es" "Pamplona|es" "Almería|es" "Alcalá de Henares|es" "Leganés|es" "Getafe|es" "Fuenlabrada|es" "San Sebastián|es" "Castellón de la Plana|es" "Burgos|es" "Alcorcón|es" "Santander|es" "Albacete|es" "San Cristóbal de La Laguna|es" "Marbella|es" "Logroño|es" "Badajoz|es" "Lleida|es" "Salamanca|es" "Tarragona|es" "Torrejón de Ardoz|es" "Huelva|es" "Dos Hermanas|es" "Parla|es" "Mataró|es" "Algeciras|es" "Santa Coloma de Gramenet|es" "León|es" "Alcobendas|es" "Jaén|es" "Reus|es" "Roquetas de Mar|es" "Cádiz|es" "Girona|es" "Ourense|es" "Telde|es" "Rivas-Vaciamadrid|es" "Barakaldo|es" "Santiago de Compostela|es" "Lugo|es" "Las Rozas de Madrid|es" "Lorca|es" "Torrevieja|es" "San Fernando|es" "Cáceres|es" "San Sebastián de los Reyes|es" "Cornellà de Llobregat|es" "Sant Cugat del Vallès|es" "El Puerto de Santa María|es" "Guadalajara|es" "Pozuelo de Alarcón|es" "Melilla|es" "Toledo|es" "Mijas|es" "Chiclana de la Frontera|es" "Sant Boi de Llobregat|es" "Ceuta|es" "Torrent|es" "El Ejido|es" "Talavera de la Reina|es" "Pontevedra|es" "Fuengirola|es" "Arona|es" "Vélez-Málaga|es" "Coslada|es" "Rubí|es" "Manresa|es" "Palencia|es" "Orihuela|es" "Getxo|es" "Avilés|es" "Valdemoro|es" "Gandia|es" "Alcalá de Guadaíra|es" "Ciudad Real|es" "Santa Lucía de Tirajana|es" "Molina de Segura|es" "Majadahonda|es" "Paterna|es" "Benidorm|es" "Estepona|es" "Sanlúcar de Barrameda|es" "Torremolinos|es" "Benalmádena|es" "Vilanova i la Geltrú|es" "Castelldefels|es" "Viladecans|es" "Sagunto|es" "Ferrol|es" "El Prat de Llobregat|es" "Arrecife|es" "Ponferrada|es" "Collado Villalba|es"
)

# SWITZERLAND (26 cities) - German/French/Italian
SWITZERLAND_CITIES=(
"Zürich|de" "Genève|fr" "Basel|de" "Lausanne|fr" "Bern|de" "Winterthur|de" "Luzern|de" "St. Gallen|de" "Lugano|it" "Biel|de" "Thun|de" "Köniz|de" "La Chaux-de-Fonds|fr" "Schaffhausen|de" "Fribourg|fr" "Chur|de" "Vernier|fr" "Neuchâtel|fr" "Uster|de" "Sion|fr" "Emmen|de" "Kriens|de" "Rapperswil-Jona|de" "Yverdon-les-Bains|fr" "Dübendorf|de" "Dietikon|de"
)

# PORTUGAL (57 cities) - Portuguese
PORTUGAL_CITIES=(
"Lisboa|pt" "Sintra|pt" "Vila Nova de Gaia|pt" "Porto|pt" "Cascais|pt" "Loures|pt" "Braga|pt" "Almada|pt" "Amadora|pt" "Matosinhos|pt" "Oeiras|pt" "Seixal|pt" "Gondomar|pt" "Guimarães|pt" "Odivelas|pt" "Coimbra|pt" "Maia|pt" "Vila Franca de Xira|pt" "Santa Maria da Feira|pt" "Vila Nova de Famalicão|pt" "Leiria|pt" "Setúbal|pt" "Barcelos|pt" "Funchal|pt" "Viseu|pt" "Valongo|pt" "Mafra|pt" "Torres Vedras|pt" "Aveiro|pt" "Viana do Castelo|pt" "Paredes|pt" "Vila do Conde|pt" "Barreiro|pt" "Loulé|pt" "Palmela|pt" "Penafiel|pt" "Moita|pt" "Faro|pt" "Ponta Delgada|pt" "Póvoa de Varzim|pt" "Santo Tirso|pt" "Oliveira de Azeméis|pt" "Portimão|pt" "Santarém|pt" "Figueira da Foz|pt" "Montijo|pt" "Alcobaça|pt" "Ovar|pt" "Sesimbra|pt" "Paços de Ferreira|pt" "Felgueiras|pt" "Caldas da Rainha|pt" "Évora|pt" "Castelo Branco|pt" "Pombal|pt" "Amarante|pt" "Vila Real|pt"
)

# NETHERLANDS (58 cities) - Dutch
NETHERLANDS_CITIES=(
"Amsterdam|nl" "Rotterdam|nl" "'s-Gravenhage|nl" "Utrecht|nl" "Eindhoven|nl" "Tilburg|nl" "Groningen|nl" "Almere|nl" "Breda|nl" "Nijmegen|nl" "Enschede|nl" "Haarlem|nl" "Arnhem|nl" "Zaanstad|nl" "Amersfoort|nl" "Apeldoorn|nl" "'s-Hertogenbosch|nl" "Hoofddorp|nl" "Maastricht|nl" "Leiden|nl" "Dordrecht|nl" "Zoetermeer|nl" "Zwolle|nl" "Deventer|nl" "Delft|nl" "Alkmaar|nl" "Heerlen|nl" "Venlo|nl" "Leeuwarden|nl" "Hilversum|nl" "Hengelo|nl" "Amstelveen|nl" "Roosendaal|nl" "Purmerend|nl" "Oss|nl" "Schiedam|nl" "Spijkenisse|nl" "Helmond|nl" "Vlaardingen|nl" "Almelo|nl" "Gouda|nl" "Zaandam|nl" "Lelystad|nl" "Alphen aan den Rijn|nl" "Hoorn|nl" "Velsen|nl" "Ede|nl" "Bergen op Zoom|nl" "Capelle aan den IJssel|nl" "Assen|nl" "Nieuwegein|nl" "Veenendaal|nl" "Zeist|nl" "Den Helder|nl" "Hardenberg|nl" "Emmen|nl" "Oosterhout|nl"
)

# BELGIUM (37 cities) - Dutch/French
BELGIUM_CITIES=(
"Antwerpen|nl" "Gent|nl" "Charleroi|fr" "Bruxelles|fr" "Liège|fr" "Schaerbeek|fr" "Anderlecht|fr" "Brugge|nl" "Namur|fr" "Leuven|nl" "Molenbeek-Saint-Jean|fr" "Mons|fr" "Aalst|nl" "Hasselt|nl" "Ixelles|fr" "Mechelen|nl" "Beveren|nl" "Uccle|fr" "Sint-Niklaas|nl" "La Louvière|fr" "Kortrijk|nl" "Oostende|nl" "Tournai|fr" "Genk|nl" "Roeselare|nl" "Seraing|fr" "Woluwe-Saint-Lambert|fr" "Mouscron|fr" "Forest|fr" "Verviers|fr" "Jette|fr" "Lokeren|nl" "Etterbeek|fr" "Saint-Gilles|fr" "Dendermonde|nl" "Vilvoorde|nl" "Turnhout|nl"
)

# Combine all cities
ALL_CITIES=(
    "${GERMANY_CITIES[@]}"
    "${AUSTRIA_CITIES[@]}"
    "${ITALY_CITIES[@]}"
    "${SPAIN_CITIES[@]}"
    "${SWITZERLAND_CITIES[@]}"
    "${PORTUGAL_CITIES[@]}"
    "${NETHERLANDS_CITIES[@]}"
    "${BELGIUM_CITIES[@]}"
)

# Check if running from scripts directory
if [ ! -f "../main.py" ] && [ ! -f "main.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}Usage: ./scripts/ice_cream_scraper.sh${NC}"
    exit 1
fi

# If running from scripts directory, go to parent
if [ -f "../main.py" ]; then
    cd ..
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}     EUROPEAN ARTISAN ICE CREAM BATCH SCRAPER           ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Countries:${NC} Germany (191), Austria (10), Italy (140), Spain (120),"
echo -e "           Switzerland (26), Portugal (57), Netherlands (58), Belgium (37)"
echo -e "${YELLOW}Total Cities:${NC} ${#ALL_CITIES[@]} cities (50K+ population)"
echo -e "${YELLOW}Search Terms per City:${NC} 4 variations"
echo -e "${YELLOW}Total Searches:${NC} $((${#ALL_CITIES[@]} * 4))"
echo -e "${YELLOW}Max Results per Search:${NC} $MAX_RESULTS"
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
        de)
            terms=("artisanal_ice_cream_de" "gelato_producer_de" "ice_cream_manufacturer_de" "craft_ice_cream_de")
            ;;
        it)
            terms=("artisanal_gelato_it" "gelato_producer_it" "ice_cream_manufacturer_it" "craft_gelato_it")
            ;;
        es)
            terms=("artisanal_ice_cream_es" "gelato_producer_es" "ice_cream_manufacturer_es" "craft_ice_cream_es")
            ;;
        pt)
            terms=("artisanal_ice_cream_pt" "gelato_producer_pt" "ice_cream_manufacturer_pt" "craft_ice_cream_pt")
            ;;
        nl)
            terms=("artisanal_ice_cream_nl" "gelato_producer_nl" "ice_cream_manufacturer_nl" "craft_ice_cream_nl")
            ;;
        fr)
            terms=("artisanal_ice_cream_ch_fr" "ice_cream_producer_ch_fr" "artisanal_ice_cream_be_fr" "ice_cream_producer_be_fr")
            ;;
    esac
    
    echo "${terms[@]}"
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
PROGRESS_LOG="data/ice_cream_progress.log"
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
        
        # Convert country code to uppercase for phone parsing (de -> DE, it -> IT, etc.)
        country_code_upper=$(echo "$country_code" | tr '[:lower:]' '[:upper:]')
        
        # Run python and capture output
        python main.py --city "$city" --keyword "$keyword" --language "$language" --country-code "$country_code_upper" --no-find-emails --max-results $MAX_RESULTS 2>&1
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
echo -e "${GREEN}✓ Ice cream scraper completed!${NC}"
echo ""
echo -e "${YELLOW}Tip:${NC} To resume from a specific point, use: $0 --start-from <number>"
echo ""
