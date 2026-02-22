"""Browser manager with stealth configuration for Playwright"""

import random
from typing import Any, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth
from src.geo_data import (
    CITY_COORDINATES,
    CITY_TIMEZONES,
    get_coordinates_for_city,
    get_timezone_for_city,
)


class BrowserManager:
    """Manages browser instances with anti-detection features"""

    LANGUAGE_DEFAULT_LOCALE: dict[str, tuple[str, list[str]]] = {
        "de": ("de-DE", ["de-DE", "de", "en-US", "en"]),
        "it": ("it-IT", ["it-IT", "it", "en-US", "en"]),
        "es": ("es-ES", ["es-ES", "es", "en-US", "en"]),
        "da": ("da-DK", ["da-DK", "da", "en-US", "en"]),
        "sv": ("sv-SE", ["sv-SE", "sv", "en-US", "en"]),
        "no": ("nb-NO", ["nb-NO", "no", "en-US", "en"]),
        "fr": ("fr-FR", ["fr-FR", "fr", "en-US", "en"]),
        "pt": ("pt-PT", ["pt-PT", "pt", "en-US", "en"]),
        "nl": ("nl-NL", ["nl-NL", "nl", "en-US", "en"]),
        "fi": ("fi-FI", ["fi-FI", "fi", "en-US", "en"]),
        "mt": ("mt-MT", ["mt-MT", "mt", "en-GB", "en"]),
        "pl": ("pl-PL", ["pl-PL", "pl", "en-US", "en"]),
        "cs": ("cs-CZ", ["cs-CZ", "cs", "en-US", "en"]),
        "sk": ("sk-SK", ["sk-SK", "sk", "en-US", "en"]),
        "hu": ("hu-HU", ["hu-HU", "hu", "en-US", "en"]),
        "sl": ("sl-SI", ["sl-SI", "sl", "en-US", "en"]),
        "hr": ("hr-HR", ["hr-HR", "hr", "en-US", "en"]),
        "sr": ("sr-RS", ["sr-RS", "sr", "en-US", "en"]),
        "sq": ("sq-AL", ["sq-AL", "sq", "en-US", "en"]),
        "mk": ("mk-MK", ["mk-MK", "mk", "en-US", "en"]),
        "bg": ("bg-BG", ["bg-BG", "bg", "en-US", "en"]),
        "ro": ("ro-RO", ["ro-RO", "ro", "en-US", "en"]),
        "el": ("el-GR", ["el-GR", "el", "en-US", "en"]),
        "en-gb": ("en-GB", ["en-GB", "en", "en-US"]),
        "en-ie": ("en-IE", ["en-IE", "en", "en-GB", "en-US"]),
        "en-mt": ("en-MT", ["en-MT", "en-GB", "en", "en-US"]),
        "en": ("en-US", ["en-US", "en"]),
    }

    LANGUAGE_DEFAULT_GEO: dict[str, tuple[tuple[float, float], str]] = {
        "de": ((52.5200, 13.4050), "Europe/Berlin"),
        "it": ((41.9028, 12.4964), "Europe/Rome"),
        "es": ((40.4168, -3.7038), "Europe/Madrid"),
        "da": ((55.6761, 12.5683), "Europe/Copenhagen"),
        "sv": ((59.3293, 18.0686), "Europe/Stockholm"),
        "no": ((59.9139, 10.7522), "Europe/Oslo"),
        "fr": ((48.8566, 2.3522), "Europe/Paris"),
        "pt": ((38.7223, -9.1393), "Europe/Lisbon"),
        "nl": ((52.3676, 4.9041), "Europe/Amsterdam"),
        "fi": ((60.1699, 24.9384), "Europe/Helsinki"),
        "mt": ((35.8989, 14.5146), "Europe/Malta"),
        "pl": ((52.2297, 21.0122), "Europe/Warsaw"),
        "cs": ((50.0755, 14.4378), "Europe/Prague"),
        "sk": ((48.1486, 17.1077), "Europe/Bratislava"),
        "hu": ((47.4979, 19.0402), "Europe/Budapest"),
        "sl": ((46.0569, 14.5058), "Europe/Ljubljana"),
        "hr": ((45.8150, 15.9819), "Europe/Zagreb"),
        "sr": ((44.7866, 20.4489), "Europe/Belgrade"),
        "sq": ((41.3275, 19.8187), "Europe/Tirane"),
        "mk": ((41.9973, 21.4280), "Europe/Skopje"),
        "bg": ((42.6977, 23.3219), "Europe/Sofia"),
        "ro": ((44.4268, 26.1025), "Europe/Bucharest"),
        "el": ((37.9838, 23.7275), "Europe/Athens"),
        "en-gb": ((51.5074, -0.1278), "Europe/London"),
        "en-ie": ((53.3498, -6.2603), "Europe/Dublin"),
        "en-mt": ((35.8989, 14.5146), "Europe/Malta"),
        "en": ((40.7128, -74.0060), "America/New_York"),
    }

    def __init__(self, config: dict[str, Any], logger: Any) -> None:
        self.config = config
        self.logger = logger
        self.playwright: Optional[Any] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.current_city: Optional[str] = None

    def start(self, city: Optional[str] = None, language: Optional[str] = None) -> Page:
        """Start browser with stealth configuration

        Args:
            city: Optional city name for setting geolocation
            language: Optional language code (e.g., 'de', 'it', 'fr') for locale/navigator.languages

        Returns:
            Playwright Page object
        """
        self.logger.info("Starting browser...")
        self.current_city = city

        browser_config = self.config.get("browser", {})
        scraper_config = self.config.get("scraper", {})

        # Start Playwright
        self.playwright = sync_playwright().start()

        # Launch browser
        self.browser = self.playwright.chromium.launch(
            headless=scraper_config.get("headless", False),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

        # Random viewport size (within reasonable desktop ranges)
        viewport_width = browser_config.get("viewport_width", 1920) + random.randint(
            -100, 100
        )
        viewport_height = browser_config.get("viewport_height", 1080) + random.randint(
            -50, 50
        )

        # Force desktop user agent (randomly choose from desktop options)
        desktop_uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        ]
        user_agent = random.choice(desktop_uas)

        self.logger.info(f"User-Agent: {user_agent[:50]}...")
        self.logger.info(f"Viewport: {viewport_width}x{viewport_height}")

        # Get geolocation based on city
        latitude, longitude = self._get_geolocation_for_city(city, language)
        timezone_id = self._get_timezone_for_city(city, language)

        # Get locale and navigator.languages based on --language parameter
        locale, nav_languages = self._get_locale_for_language(language)

        self.logger.info(
            f"Geolocation: {latitude}, {longitude} (timezone: {timezone_id})"
        )
        self.logger.info(f"Locale: {locale}, Languages: {nav_languages}")

        if not self.browser:
            raise RuntimeError("Browser failed to start")

        # Create context with anti-detection settings
        self.context = self.browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=user_agent,
            locale=locale,
            timezone_id=timezone_id,
            permissions=["geolocation"],
            geolocation={"latitude": latitude, "longitude": longitude},
            color_scheme="light",
            device_scale_factor=1.0,
        )

        # Apply playwright-stealth (covers webdriver, chrome.runtime, permissions,
        # codecs, webgl, navigator props, iframe contentWindow, and more)
        # Pass navigator.languages override to match the target language
        stealth = Stealth(
            navigator_languages_override=(
                nav_languages[0],
                nav_languages[1] if len(nav_languages) > 1 else "en",
            ),
        )
        stealth.apply_stealth_sync(self.context)

        # Create page (after stealth is applied to context)
        self.page = self.context.new_page()

        # Set default timeout
        self.page.set_default_timeout(
            scraper_config.get("page_load_timeout", 30) * 1000
        )

        self.logger.info("Browser started successfully (with playwright-stealth)")

        return self.page

    @staticmethod
    def _get_locale_for_language(language: Optional[str]) -> tuple[str, list[str]]:
        """Get browser locale and navigator.languages for a language code

        Args:
            language: Language code (e.g., 'de', 'it', 'fr')

        Returns:
            Tuple of (locale_string, languages_list)
        """
        if language:
            normalized = language.lower().strip()
            if normalized in BrowserManager.LANGUAGE_DEFAULT_LOCALE:
                return BrowserManager.LANGUAGE_DEFAULT_LOCALE[normalized]

            base_language = normalized.split("-")[0]
            if base_language in BrowserManager.LANGUAGE_DEFAULT_LOCALE:
                return BrowserManager.LANGUAGE_DEFAULT_LOCALE[base_language]

        return ("en-US", ["en-US", "en"])

    @staticmethod
    def _get_geolocation_for_city(
        city: Optional[str], language: Optional[str] = None
    ) -> tuple[float, float]:
        """Get latitude/longitude for a city, then fallback to language defaults."""
        if city:
            city_lower = city.lower().strip()
            if city_lower in CITY_COORDINATES:
                return CITY_COORDINATES[city_lower]

        if language:
            normalized = language.lower().strip()
            if normalized in BrowserManager.LANGUAGE_DEFAULT_GEO:
                return BrowserManager.LANGUAGE_DEFAULT_GEO[normalized][0]

            base_language = normalized.split("-")[0]
            if base_language in BrowserManager.LANGUAGE_DEFAULT_GEO:
                return BrowserManager.LANGUAGE_DEFAULT_GEO[base_language][0]

        return get_coordinates_for_city(city)

    @staticmethod
    def _get_timezone_for_city(
        city: Optional[str], language: Optional[str] = None
    ) -> str:
        """Get timezone for a city, then fallback to language defaults."""
        if city:
            city_lower = city.lower().strip()
            if city_lower in CITY_TIMEZONES:
                return CITY_TIMEZONES[city_lower]

        if language:
            normalized = language.lower().strip()
            if normalized in BrowserManager.LANGUAGE_DEFAULT_GEO:
                return BrowserManager.LANGUAGE_DEFAULT_GEO[normalized][1]

            base_language = normalized.split("-")[0]
            if base_language in BrowserManager.LANGUAGE_DEFAULT_GEO:
                return BrowserManager.LANGUAGE_DEFAULT_GEO[base_language][1]

        return get_timezone_for_city(city)

    def update_geolocation(self, latitude: float, longitude: float) -> None:
        """Update geolocation for the browser context"""
        if self.context:
            self.context.set_geolocation({"latitude": latitude, "longitude": longitude})
            self.logger.info(f"Updated geolocation to: {latitude}, {longitude}")

    def new_page(self) -> Optional[Page]:
        """Create a new page in the existing context"""
        if self.context:
            return self.context.new_page()
        return None

    def screenshot(self, filename: str) -> None:
        """Take a screenshot of the current page"""
        if self.page:
            try:
                self.page.screenshot(path=filename)
                self.logger.info(f"Screenshot saved: {filename}")
            except Exception as e:
                self.logger.error(f"Failed to take screenshot: {e}")

    def close(self) -> None:
        """Close browser and cleanup resources safely"""
        self.logger.info("Closing browser...")

        try:
            if self.page:
                try:
                    self.page.close()
                except Exception as e:
                    self.logger.debug(f"Error closing page: {e}")
        finally:
            try:
                if self.context:
                    try:
                        self.context.close()
                    except Exception as e:
                        self.logger.debug(f"Error closing context: {e}")
            finally:
                try:
                    if self.browser:
                        try:
                            self.browser.close()
                        except Exception as e:
                            self.logger.debug(f"Error closing browser: {e}")
                finally:
                    if self.playwright:
                        try:
                            self.playwright.stop()
                        except Exception as e:
                            self.logger.debug(f"Error stopping playwright: {e}")

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

        self.logger.info("✓ Browser closed")

    def __enter__(self) -> Page:
        """Context manager entry"""
        return self.start()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit"""
        self.close()
