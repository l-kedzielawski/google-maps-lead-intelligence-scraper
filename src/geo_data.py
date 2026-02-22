"""Centralized city/country/timezone/coordinate mappings"""

# City to (latitude, longitude) mapping for browser geolocation
CITY_COORDINATES: dict[str, tuple[float, float]] = {
    # Poland
    'warsaw': (52.2297, 21.0122),
    'warszawa': (52.2297, 21.0122),
    'krakow': (50.0647, 19.9450),
    'kraków': (50.0647, 19.9450),
    'wroclaw': (51.1079, 17.0385),
    'wrocław': (51.1079, 17.0385),
    'poznan': (52.4064, 16.9252),
    'poznań': (52.4064, 16.9252),
    'gdansk': (54.3520, 18.6466),
    'gdańsk': (54.3520, 18.6466),
    'lublin': (51.2465, 22.5684),
    'szczecin': (53.4285, 14.5528),
    'bydgoszcz': (53.1235, 18.0084),
    # France
    'paris': (48.8566, 2.3522),
    'lyon': (45.7640, 4.8357),
    'marseille': (43.2965, 5.3698),
    'nice': (43.7102, 7.2620),
    'toulouse': (43.6047, 1.4442),
    'bordeaux': (44.8378, -0.5792),
    # Italy
    'rome': (41.9028, 12.4964),
    'roma': (41.9028, 12.4964),
    'milan': (45.4642, 9.1900),
    'milano': (45.4642, 9.1900),
    'venice': (45.4408, 12.3155),
    'venezia': (45.4408, 12.3155),
    'florence': (43.7696, 11.2558),
    'firenze': (43.7696, 11.2558),
    'naples': (40.8518, 14.2681),
    'napoli': (40.8518, 14.2681),
    'turin': (45.0703, 7.6869),
    'torino': (45.0703, 7.6869),
    # Spain
    'madrid': (40.4168, -3.7038),
    'barcelona': (41.3851, 2.1734),
    'valencia': (39.4699, -0.3763),
    'seville': (37.3891, -5.9845),
    'sevilla': (37.3891, -5.9845),
    'bilbao': (43.2630, -2.9350),
    'malaga': (36.7213, -4.4214),
    'málaga': (36.7213, -4.4214),
    # Germany
    'berlin': (52.5200, 13.4050),
    'munich': (48.1351, 11.5820),
    'münchen': (48.1351, 11.5820),
    'hamburg': (53.5511, 9.9937),
    'frankfurt': (50.1109, 8.6821),
    'cologne': (50.9375, 6.9603),
    'köln': (50.9375, 6.9603),
    'düsseldorf': (51.2277, 6.7735),
    # UK
    'london': (51.5074, -0.1278),
    'manchester': (53.4808, -2.2426),
    'birmingham': (52.4862, -1.8904),
    'liverpool': (53.4084, -2.9916),
    'edinburgh': (55.9533, -3.1883),
    'glasgow': (55.8642, -4.2518),
    # Portugal
    'lisbon': (38.7223, -9.1393),
    'lisboa': (38.7223, -9.1393),
    'porto': (41.1579, -8.6291),
    # Netherlands
    'amsterdam': (52.3676, 4.9041),
    'rotterdam': (51.9225, 4.4792),
    # Belgium
    'brussels': (50.8503, 4.3517),
    'bruxelles': (50.8503, 4.3517),
    'antwerp': (51.2194, 4.4025),
    'antwerpen': (51.2194, 4.4025),
    # Switzerland
    'zurich': (47.3769, 8.5417),
    'zürich': (47.3769, 8.5417),
    'geneva': (46.2044, 6.1432),
    'genève': (46.2044, 6.1432),
    'bern': (46.9480, 7.4474),
    # USA
    'new york': (40.7128, -74.0060),
    'los angeles': (34.0522, -118.2437),
    'chicago': (41.8781, -87.6298),
    'houston': (29.7604, -95.3698),
    'miami': (25.7617, -80.1918),
    'san francisco': (37.7749, -122.4194),
    'boston': (42.3601, -71.0589),
    'seattle': (47.6062, -122.3321),
    'las vegas': (36.1699, -115.1398),
    'denver': (39.7392, -104.9903),
    'austin': (30.2672, -97.7431),
}

# City to timezone mapping
CITY_TIMEZONES: dict[str, str] = {
    # Poland
    'warsaw': 'Europe/Warsaw', 'warszawa': 'Europe/Warsaw',
    'krakow': 'Europe/Warsaw', 'kraków': 'Europe/Warsaw',
    'wroclaw': 'Europe/Warsaw', 'wrocław': 'Europe/Warsaw',
    'poznan': 'Europe/Warsaw', 'poznań': 'Europe/Warsaw',
    'gdansk': 'Europe/Warsaw', 'gdańsk': 'Europe/Warsaw',
    'lublin': 'Europe/Warsaw', 'szczecin': 'Europe/Warsaw',
    'bydgoszcz': 'Europe/Warsaw',
    # France
    'paris': 'Europe/Paris', 'lyon': 'Europe/Paris', 'marseille': 'Europe/Paris',
    'nice': 'Europe/Paris', 'toulouse': 'Europe/Paris', 'bordeaux': 'Europe/Paris',
    # Italy
    'rome': 'Europe/Rome', 'roma': 'Europe/Rome',
    'milan': 'Europe/Rome', 'milano': 'Europe/Rome',
    'venice': 'Europe/Rome', 'venezia': 'Europe/Rome',
    'florence': 'Europe/Rome', 'firenze': 'Europe/Rome',
    'naples': 'Europe/Rome', 'napoli': 'Europe/Rome',
    'turin': 'Europe/Rome', 'torino': 'Europe/Rome',
    # Spain
    'madrid': 'Europe/Madrid', 'barcelona': 'Europe/Madrid',
    'valencia': 'Europe/Madrid', 'seville': 'Europe/Madrid', 'sevilla': 'Europe/Madrid',
    'bilbao': 'Europe/Madrid', 'malaga': 'Europe/Madrid', 'málaga': 'Europe/Madrid',
    # Germany
    'berlin': 'Europe/Berlin', 'munich': 'Europe/Berlin', 'münchen': 'Europe/Berlin',
    'hamburg': 'Europe/Berlin', 'frankfurt': 'Europe/Berlin',
    'cologne': 'Europe/Berlin', 'köln': 'Europe/Berlin', 'düsseldorf': 'Europe/Berlin',
    # UK
    'london': 'Europe/London', 'manchester': 'Europe/London',
    'birmingham': 'Europe/London', 'liverpool': 'Europe/London',
    'edinburgh': 'Europe/London', 'glasgow': 'Europe/London',
    # Portugal
    'lisbon': 'Europe/Lisbon', 'lisboa': 'Europe/Lisbon', 'porto': 'Europe/Lisbon',
    # Netherlands
    'amsterdam': 'Europe/Amsterdam', 'rotterdam': 'Europe/Amsterdam',
    # Belgium
    'brussels': 'Europe/Brussels', 'bruxelles': 'Europe/Brussels',
    'antwerp': 'Europe/Brussels', 'antwerpen': 'Europe/Brussels',
    # Switzerland
    'zurich': 'Europe/Zurich', 'zürich': 'Europe/Zurich',
    'geneva': 'Europe/Zurich', 'genève': 'Europe/Zurich', 'bern': 'Europe/Zurich',
    # USA
    'new york': 'America/New_York', 'los angeles': 'America/Los_Angeles',
    'chicago': 'America/Chicago', 'houston': 'America/Chicago',
    'miami': 'America/New_York', 'san francisco': 'America/Los_Angeles',
    'boston': 'America/New_York', 'seattle': 'America/Los_Angeles',
    'las vegas': 'America/Los_Angeles', 'denver': 'America/Denver',
    'austin': 'America/Chicago',
}

# City to ISO country code mapping (for phone number parsing)
CITY_COUNTRY_CODES: dict[str, str] = {
    # Poland
    'warsaw': 'PL', 'warszawa': 'PL', 'krakow': 'PL', 'kraków': 'PL',
    'wroclaw': 'PL', 'wrocław': 'PL', 'poznan': 'PL', 'poznań': 'PL',
    'gdansk': 'PL', 'gdańsk': 'PL', 'lublin': 'PL', 'szczecin': 'PL',
    'bydgoszcz': 'PL', 'warsaw metropolitan': 'PL',
    # France
    'paris': 'FR', 'lyon': 'FR', 'marseille': 'FR', 'nice': 'FR',
    'toulouse': 'FR', 'bordeaux': 'FR',
    # Italy
    'rome': 'IT', 'roma': 'IT', 'milan': 'IT', 'milano': 'IT',
    'venice': 'IT', 'venezia': 'IT', 'florence': 'IT', 'firenze': 'IT',
    'naples': 'IT', 'napoli': 'IT', 'turin': 'IT', 'torino': 'IT',
    # Spain
    'madrid': 'ES', 'barcelona': 'ES', 'valencia': 'ES',
    'seville': 'ES', 'sevilla': 'ES', 'bilbao': 'ES',
    'malaga': 'ES', 'málaga': 'ES',
    # Germany
    'berlin': 'DE', 'munich': 'DE', 'münchen': 'DE',
    'hamburg': 'DE', 'frankfurt': 'DE', 'cologne': 'DE',
    'köln': 'DE', 'düsseldorf': 'DE',
    # UK
    'london': 'GB', 'manchester': 'GB', 'birmingham': 'GB',
    'liverpool': 'GB', 'edinburgh': 'GB', 'glasgow': 'GB',
    # Portugal
    'lisbon': 'PT', 'lisboa': 'PT', 'porto': 'PT',
    # Netherlands
    'amsterdam': 'NL', 'rotterdam': 'NL',
    # Belgium
    'brussels': 'BE', 'bruxelles': 'BE', 'antwerp': 'BE', 'antwerpen': 'BE',
    # Switzerland
    'zurich': 'CH', 'zürich': 'CH', 'geneva': 'CH', 'genève': 'CH', 'bern': 'CH',
    # USA
    'new york': 'US', 'los angeles': 'US', 'chicago': 'US', 'houston': 'US',
    'miami': 'US', 'san francisco': 'US', 'boston': 'US', 'seattle': 'US',
    'las vegas': 'US', 'denver': 'US', 'austin': 'US',
}


def get_coordinates_for_city(city: str | None) -> tuple[float, float]:
    """Get latitude/longitude for a city
    
    Args:
        city: City name
        
    Returns:
        Tuple of (latitude, longitude)
    """
    if city:
        city_lower = city.lower().strip()
        if city_lower in CITY_COORDINATES:
            return CITY_COORDINATES[city_lower]
    return (40.7128, -74.0060)  # Default to NYC


def get_timezone_for_city(city: str | None) -> str:
    """Get timezone for a city
    
    Args:
        city: City name
        
    Returns:
        Timezone string
    """
    if city:
        city_lower = city.lower().strip()
        if city_lower in CITY_TIMEZONES:
            return CITY_TIMEZONES[city_lower]
    return 'America/New_York'


def get_country_code_for_city(city: str) -> str:
    """Get ISO country code for a city (for phone parsing)
    
    Args:
        city: City name
        
    Returns:
        ISO country code string (e.g., 'DE', 'IT')
    """
    city_lower = city.lower().strip()
    return CITY_COUNTRY_CODES.get(city_lower, 'US')
