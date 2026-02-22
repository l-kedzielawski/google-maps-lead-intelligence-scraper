"""Main Google Maps scraper"""

import time
from typing import Any, Optional
from urllib.parse import quote
from tqdm import tqdm
from src.browser_manager import BrowserManager
from src.data_extractor import DataExtractor
from src.email_finder import EmailFinder
from src.csv_handler import CSVHandler
from src.vpn_manager import VPNManager
from src.utils import (
    random_delay,
    is_captcha_present,
    get_country_code_from_city,
    handle_cookie_consent,
    handle_google_popups,
)
from src.geo_data import get_coordinates_for_city
from rich.console import Console

console = Console()


class GoogleMapsScraper:
    """Scrapes business listings from Google Maps"""

    def __init__(self, config: dict[str, Any], logger: Any) -> None:
        self.config = config
        self.logger = logger
        self.browser_manager: Optional[BrowserManager] = None
        self.page: Optional[Any] = None
        self.data_extractor: Optional[DataExtractor] = None
        self.email_finder = EmailFinder(config, logger)
        self.csv_handler = CSVHandler(config, logger)
        self.businesses: list[dict[str, Any]] = []
        self._current_keyword: Optional[str] = None
        self._current_city: Optional[str] = None

        # VPN management
        vpn_config = config.get("vpn", {})
        self.vpn_manager = VPNManager(
            logger,
            enabled=vpn_config.get("enabled", False),
            stable_country_mode=vpn_config.get("stable_country_mode", True),
            event_rotation_enabled=vpn_config.get("event_rotation_enabled", True),
        )
        self.vpn_manager.rotation_interval = vpn_config.get("rotation_interval", 50)
        self.rotate_on_navigation_errors = vpn_config.get(
            "rotate_on_navigation_errors", True
        )
        self.rotate_on_google_block = vpn_config.get("rotate_on_google_block", True)
        self.rotate_on_captcha = vpn_config.get("rotate_on_captcha", True)

    def scrape(
        self,
        city: str,
        keyword: str,
        language: str = "en",
        country_code: Optional[str] = None,
        radius: Optional[int] = None,
        max_results: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Scrape businesses from Google Maps

        Args:
            city: City to search in
            keyword: Search keyword
            language: Language code (en, de, fr, etc.)
            country_code: ISO country code for phone parsing
            radius: Search radius in km (optional)
            max_results: Maximum results to scrape

        Returns:
            List of business data dictionaries
        """
        self.businesses = []
        self._current_keyword = keyword
        self._current_city = city

        # Get scraper config
        scraper_config = self.config.get("scraper", {})

        # Get country code for phone number parsing
        # Priority: 1) Explicit parameter, 2) Derive from language, 3) Derive from city, 4) Default to US
        if not country_code:
            normalized_language = language.lower().strip()
            base_language = normalized_language.split("-")[0]

            # Try to derive from language code first
            language_to_country = {
                "de": "DE",
                "it": "IT",
                "es": "ES",
                "pt": "PT",
                "nl": "NL",
                "da": "DK",
                "sv": "SE",
                "no": "NO",
                "fi": "FI",
                "mt": "MT",
                "en-gb": "GB",
                "en-ie": "IE",
                "en-mt": "MT",
                "fr": "FR",
                "pl": "PL",
                "cs": "CZ",
                "sk": "SK",
                "hu": "HU",
                "sl": "SI",
                "hr": "HR",
                "sr": "RS",
                "sq": "AL",
                "mk": "MK",
                "bg": "BG",
                "ro": "RO",
                "el": "GR",
            }
            country_code = language_to_country.get(normalized_language)
            if not country_code:
                country_code = language_to_country.get(base_language)

            # Fall back to city-based detection if language doesn't help
            if not country_code:
                country_code = get_country_code_from_city(city)

            if not country_code:
                country_code = "US"

        self.logger.info(f"Using country code: {country_code} for phone parsing")

        # Setup VPN if enabled
        if self.vpn_manager.enabled:
            vpn_country = self.vpn_manager.get_country_from_language(language)
            vpn_mode = (
                "stable-country" if self.vpn_manager.stable_country_mode else "interval"
            )
            console.print(
                f"\n[cyan]VPN:[/cyan] Enabled ({vpn_mode} mode) - Connecting to {vpn_country}...\n"
            )
            if vpn_country and self.vpn_manager.connect(vpn_country):
                console.print(f"[green]✓ VPN connected to {vpn_country}[/green]\n")
            else:
                console.print(
                    "[yellow]⚠ VPN connection failed, continuing without VPN[/yellow]\n"
                )
                self.logger.warning(
                    "VPN not confirmed; waiting briefly before continuing to avoid transient network state"
                )
                time.sleep(5)

        # Setup browser with city-based geolocation and matching locale
        self.logger.info(f"Starting scrape: {keyword} in {city}")
        self.browser_manager = BrowserManager(self.config, self.logger)
        self.page = self.browser_manager.start(city=city, language=language)
        if not self.page:
            raise RuntimeError("Browser page failed to initialize")
        self.data_extractor = DataExtractor(self.page, self.config, self.logger)

        try:
            # Build search URL
            search_url = self._build_search_url(city, keyword, language, radius)
            self.logger.info(f"Search URL: {search_url}")

            # Navigate to Google Maps
            console.print("\n[cyan]Navigating to Google Maps...[/cyan]")
            nav_timeout = scraper_config.get("navigation_timeout", 30000)
            self.page.goto(
                search_url, wait_until="domcontentloaded", timeout=nav_timeout
            )
            time.sleep(2)

            # Handle cookie consent if present
            if handle_cookie_consent(self.page, self.logger):
                time.sleep(2)
                console.print("[green]✓ Cookie consent accepted[/green]")

            # Handle Google Maps popups
            if handle_google_popups(self.page, self.logger):
                time.sleep(2)
                console.print("[green]✓ Google popup dismissed[/green]")

            # Rotate on Google anti-bot page and retry search once
            if self._is_google_block_page():
                self.logger.warning("Google anti-bot page detected on initial search")
                if self.rotate_on_google_block and self._rotate_vpn_for_event(
                    language, "google_block_on_search"
                ):
                    self.page.goto(
                        search_url, wait_until="domcontentloaded", timeout=nav_timeout
                    )
                    time.sleep(2)
                    handle_cookie_consent(self.page, self.logger)
                    handle_google_popups(self.page, self.logger)

            # Wait for results to load - look for feed container AND result indicators
            max_wait_time = scraper_config.get("results_wait_timeout", 20)
            waited = 0
            found_results = False
            found_feed = False

            while waited < max_wait_time and not found_results:
                # First check for feed container
                try:
                    feed = self.page.query_selector('div[role="feed"]')
                    if feed:
                        found_feed = True
                        # Then check for actual business links inside the feed
                        for selector in [
                            'a.hfpxzc[href*="/maps/place/"]',
                            'a[href*="/maps/place/"]',
                        ]:
                            try:
                                elements = self.page.query_selector_all(selector)
                                if elements and len(elements) > 0:
                                    found_results = True
                                    self.logger.debug(
                                        f"Found {len(elements)} result links using selector: {selector}"
                                    )
                                    break
                            except Exception:
                                pass
                except Exception:
                    pass

                if not found_results:
                    time.sleep(1)
                    waited += 1

            if not found_feed:
                self.logger.error(
                    f"❌ FAIL: Results feed container not found after {max_wait_time} seconds"
                )
                self.logger.error(f"   Page URL: {self.page.url}")
                self.logger.error(
                    f"   This may indicate popup interference or wrong page state"
                )
                return []
            elif not found_results:
                self.logger.error(
                    f"❌ FAIL: Feed container found but no business links after {max_wait_time} seconds"
                )
                self.logger.error(f"   Page URL: {self.page.url}")
                self.logger.error(f"   This may indicate results haven't loaded yet")
                return []
            else:
                self.logger.info(f"✓ SUCCESS: Results loaded after {waited} seconds")

            # Check for CAPTCHA
            if is_captcha_present(self.page):
                if self.rotate_on_captcha and self._rotate_vpn_for_event(
                    language, "captcha_before_results"
                ):
                    self.page.goto(
                        search_url, wait_until="domcontentloaded", timeout=nav_timeout
                    )
                    time.sleep(2)
                    handle_cookie_consent(self.page, self.logger)
                    handle_google_popups(self.page, self.logger)

                if is_captcha_present(self.page):
                    from src.notifications import captcha_alert_popup

                    headless_mode = self.config.get("scraper", {}).get(
                        "headless", False
                    )
                    if not captcha_alert_popup(
                        self.logger, headless_mode=headless_mode
                    ):
                        return []

            # Scroll results panel
            console.print("[cyan]Loading business listings...[/cyan]")
            self._scroll_results_panel()

            # Extract business URLs from page source
            business_urls = self._extract_business_links()

            if not business_urls:
                self.logger.warning("No businesses found!")
                return []

            # Limit results
            max_results = max_results or self.config.get("scraper", {}).get(
                "max_results_per_search", 100
            )
            business_urls = business_urls[:max_results]

            console.print(
                f"[green]Found {len(business_urls)} businesses to scrape[/green]\n"
            )

            # Scrape each business
            find_emails = self.config.get("scraper", {}).get("find_emails", False)

            if find_emails:
                console.print(
                    "[cyan]✓ Email extraction ENABLED - Will crawl websites for emails[/cyan]"
                )
                console.print(
                    "[yellow]  (This will be slower but find more emails)[/yellow]\n"
                )
            else:
                console.print(
                    "[yellow]⚠ Email extraction DISABLED - Only using Google Maps data[/yellow]"
                )
                console.print(
                    "[dim]  (Use --find-emails flag for better email coverage)[/dim]\n"
                )

            with tqdm(
                total=len(business_urls), desc="Scraping businesses", unit="business"
            ) as pbar:
                for idx, business_url in enumerate(business_urls, 1):
                    try:
                        # Check if periodic VPN rotation is needed (interval mode only)
                        should_rotate, rotate_reason = (
                            self.vpn_manager.increment_scrape_count()
                        )
                        if should_rotate:
                            vpn_country = self.vpn_manager.get_country_from_language(
                                language
                            )
                            if vpn_country:
                                console.print(
                                    f"\n[yellow]⚠ {rotate_reason} - Rotating VPN to {vpn_country}[/yellow]"
                                )
                                if self.vpn_manager.rotate(
                                    vpn_country,
                                    force_reconnect=True,
                                    reason=rotate_reason,
                                ):
                                    console.print(
                                        "[green]✓ VPN rotated successfully[/green]\n"
                                    )
                                    # Reset counter after rotation to avoid repeated messages
                                    self.vpn_manager.reset_scrape_count()
                                else:
                                    console.print(
                                        "[yellow]⚠ VPN rotation failed, continuing[/yellow]\n"
                                    )

                        # Navigate to business page with timeout handling
                        business_timeout = scraper_config.get(
                            "business_page_timeout", 20000
                        )
                        try:
                            self.page.goto(
                                business_url,
                                wait_until="domcontentloaded",
                                timeout=business_timeout,
                            )
                            time.sleep(2)

                            if self._is_google_block_page():
                                self.logger.warning(
                                    f"Google anti-bot page while opening {business_url}"
                                )
                                if (
                                    self.rotate_on_google_block
                                    and self._rotate_vpn_for_event(
                                        language, "google_block_on_business_page"
                                    )
                                ):
                                    self.page.goto(
                                        business_url,
                                        wait_until="domcontentloaded",
                                        timeout=business_timeout,
                                    )
                                    time.sleep(2)

                                if self._is_google_block_page():
                                    self.logger.error(
                                        f"Google block persisted after rotation, skipping {business_url}"
                                    )
                                    pbar.update(1)
                                    continue

                        except Exception as navigation_error:
                            # Handle navigation/network errors by rotating VPN
                            if (
                                self.rotate_on_navigation_errors
                                and self._is_rotation_worthy_navigation_error(
                                    navigation_error
                                )
                            ):
                                console.print(
                                    "\n[yellow]⚠ Navigation error - Rotating VPN[/yellow]"
                                )
                                if self._rotate_vpn_for_event(
                                    language, "navigation_error"
                                ):
                                    console.print(
                                        "[green]✓ VPN rotated after navigation error[/green]\n"
                                    )
                                    # Retry the navigation
                                    try:
                                        self.page.goto(
                                            business_url,
                                            wait_until="domcontentloaded",
                                            timeout=business_timeout,
                                        )
                                        time.sleep(2)

                                        if self._is_google_block_page():
                                            self.logger.error(
                                                f"Google block still present after retry, skipping {business_url}"
                                            )
                                            pbar.update(1)
                                            continue
                                    except Exception:
                                        self.logger.error(
                                            f"Failed to navigate to {business_url} even after VPN rotation"
                                        )
                                        pbar.update(1)
                                        continue
                                else:
                                    self.logger.error(
                                        f"VPN rotation failed, skipping {business_url}"
                                    )
                                    pbar.update(1)
                                    continue
                            else:
                                raise

                        business_data = self.data_extractor.extract_business_data(
                            country_code
                        )

                        if find_emails and business_data.get("website"):
                            if not business_data.get("email"):
                                self.logger.debug(
                                    f"Searching for email on {business_data.get('website')}"
                                )
                                emails = self.email_finder.find_emails_from_website(
                                    business_data["website"]
                                )
                                if emails:
                                    business_data["email"] = emails[0]
                                    self.logger.debug(f"Found email: {emails[0]}")

                        self.businesses.append(business_data)

                        pbar.update(1)
                        pbar.set_postfix(
                            {
                                "name": business_data.get("business_name", "Unknown")[
                                    :30
                                ],
                                "phone": "✓" if business_data.get("phone") else "✗",
                                "email": "✓" if business_data.get("email") else "✗",
                            }
                        )

                        # Periodic save to prevent memory issues and data loss
                        periodic_save_interval = scraper_config.get(
                            "periodic_save_interval", 0
                        )
                        if (
                            periodic_save_interval > 0
                            and idx % periodic_save_interval == 0
                        ):
                            self._periodic_save(keyword, city)

                        if idx < len(business_urls):
                            delay_min = scraper_config.get("delay_min", 3)
                            delay_max = scraper_config.get("delay_max", 8)
                            random_delay(delay_min, delay_max)

                        if idx % scraper_config.get("captcha_check_interval", 5) == 0:
                            if is_captcha_present(self.page):
                                if (
                                    self.rotate_on_captcha
                                    and self._rotate_vpn_for_event(
                                        language, "captcha_during_business_loop"
                                    )
                                ):
                                    continue

                                from src.notifications import captcha_alert_popup

                                headless_mode = scraper_config.get("headless", False)
                                if not captcha_alert_popup(
                                    self.logger, headless_mode=headless_mode
                                ):
                                    break

                    except Exception as e:
                        self.logger.error(
                            f"Error scraping business {idx}: {str(e)[:100]}"
                        )
                        pbar.update(1)
                        continue

            console.print(
                f"\n[green]✓ Successfully scraped {len(self.businesses)} businesses[/green]\n"
            )

        except Exception as e:
            self.logger.error(f"Scraping error: {e}")

        finally:
            if self.browser_manager:
                self.browser_manager.close()
            # Keep VPN connected - don't disconnect automatically
            # User can manually disconnect if needed

        return self.businesses

    @staticmethod
    def _radius_to_zoom(radius_km: int) -> int:
        """Approximate map zoom level from radius in km."""
        if radius_km <= 1:
            return 16
        if radius_km <= 2:
            return 15
        if radius_km <= 5:
            return 14
        if radius_km <= 10:
            return 13
        if radius_km <= 20:
            return 12
        if radius_km <= 40:
            return 11
        if radius_km <= 80:
            return 10
        return 9

    def _build_search_url(
        self,
        city: str,
        keyword: str,
        language: str = "en",
        radius: Optional[int] = None,
    ) -> str:
        """Build Google Maps search URL (optionally centered by radius)."""
        search_query = f"{keyword} {city}"
        encoded_query = quote(search_query)

        if radius and radius > 0:
            latitude, longitude = get_coordinates_for_city(city)
            zoom = self._radius_to_zoom(radius)
            return (
                f"https://www.google.com/maps/search/{encoded_query}/"
                f"@{latitude},{longitude},{zoom}z?hl={language}"
            )

        url = f"https://www.google.com/maps/search/{encoded_query}?hl={language}"
        return url

    def _is_google_block_page(self) -> bool:
        """Detect Google anti-bot / blocked pages."""
        if not self.page:
            return False

        try:
            url = self.page.url.lower()
            if "sorry/index" in url or "/sorry" in url:
                return True

            body = self.page.inner_text("body").lower()
            block_markers = (
                "unusual traffic",
                "detected unusual traffic",
                "automated queries",
                "not a robot",
                "please show you're not a robot",
            )
            return any(marker in body for marker in block_markers)
        except Exception:
            return False

    @staticmethod
    def _is_rotation_worthy_navigation_error(error: Exception) -> bool:
        """Return True for navigation errors where a VPN reconnect can help."""
        error_text = str(error).lower()
        markers = (
            "timeout",
            "net::err",
            "unexpected eof while reading",
            "remote end closed connection",
            "eof occurred in violation of protocol",
            "connection reset",
            "connection aborted",
            "connection refused",
            "ssl",
            "tls",
        )
        return any(marker in error_text for marker in markers)

    def _rotate_vpn_for_event(self, language: str, event_name: str) -> bool:
        """Rotate VPN for an event if VPN and event rotation are enabled."""
        if not self.vpn_manager.enabled:
            return False

        vpn_country = self.vpn_manager.get_country_from_language(language)
        if not vpn_country:
            self.logger.warning("Could not determine VPN country for event rotation")
            return False

        return self.vpn_manager.handle_block_event(vpn_country, event_name)

    def _periodic_save(self, keyword: str, city: str) -> None:
        """Periodically save businesses to CSV to prevent data loss.

        Uses a fixed filename (overwriting each time) to avoid creating
        multiple partial files. The final save_to_csv() creates the
        properly timestamped file.

        Args:
            keyword: Search keyword
            city: Search city
        """
        if not self.businesses:
            return

        try:
            from src.utils import sanitize_filename
            import pandas as pd

            sanitized_city = sanitize_filename(city)
            sanitized_keyword = sanitize_filename(keyword)
            output_dir = self.csv_handler.output_dir

            # Fixed filename — overwritten on each periodic save
            filename = f"{sanitized_city}_{sanitized_keyword}_partial.csv"
            filepath = output_dir / filename

            df = pd.DataFrame(self.businesses.copy())
            df.to_csv(filepath, index=False, encoding="utf-8")

            self.logger.info(
                f"Periodic save: {len(self.businesses)} businesses saved to {filepath}"
            )
        except Exception as e:
            self.logger.error(f"Periodic save failed: {e}")

    def _scroll_results_panel(self) -> None:
        """Scroll the results panel to load all businesses"""
        scraper_config = self.config.get("scraper", {})

        if not self.page:
            self.logger.error("Cannot scroll results: page is not initialized")
            return

        assert self.page is not None

        try:
            time.sleep(2)
            handle_google_popups(self.page, self.logger)

            scroll_container_selectors = [
                'div[role="feed"]',
                "div.m6QErb",
                '[aria-label*="Results"]',
                '[aria-label*="Wyniki"]',
            ]

            scroll_container = None
            for selector in scroll_container_selectors:
                try:
                    scroll_container = self.page.wait_for_selector(
                        selector, timeout=5000
                    )
                    if scroll_container:
                        self.logger.debug(f"Found scroll container: {selector}")
                        break
                except Exception as e:
                    self.logger.debug(f"Selector {selector} not found: {e}")
                    continue

            if not scroll_container:
                self.logger.warning(
                    "❌ FAIL: Could not find results container to scroll"
                )
                self.logger.warning(f"   Tried selectors: {scroll_container_selectors}")
                self.logger.warning(
                    f"   Page URL: {self.page.url if self.page else 'N/A'}"
                )
                return

            last_height = 0
            scroll_attempts = 0
            max_scrolls = scraper_config.get("max_scroll_attempts", 20)

            while scroll_attempts < max_scrolls:
                try:
                    scroll_container.evaluate(
                        "(element) => element.scrollTo(0, element.scrollHeight)"
                    )
                    scroll_delay = self.config.get("scraper", {}).get("scroll_delay", 2)
                    time.sleep(scroll_delay)

                    try:
                        new_height = scroll_container.evaluate(
                            "(element) => element.scrollHeight"
                        )
                    except Exception as eval_error:
                        self.logger.debug(
                            f"Scroll context lost: {eval_error}, re-finding container..."
                        )
                        scroll_container = self.page.wait_for_selector(
                            scroll_container_selectors[0], timeout=3000
                        )
                        if not scroll_container:
                            break
                        new_height = scroll_container.evaluate(
                            "(element) => element.scrollHeight"
                        )

                    if new_height == last_height:
                        break

                    last_height = new_height
                    scroll_attempts += 1
                    self.logger.debug(
                        f"Scroll {scroll_attempts}: height = {new_height}"
                    )

                except Exception as scroll_error:
                    self.logger.debug(f"Error during scroll: {scroll_error}")
                    break

            self.logger.info(f"Completed scrolling after {scroll_attempts} attempts")

        except Exception as e:
            self.logger.error(f"Error scrolling results: {e}")

    def _extract_business_links(self):
        """Extract business URLs from Google Maps results using multiple methods"""
        business_links = []

        if not self.page:
            self.logger.error("Cannot extract business links: page is not initialized")
            return business_links

        assert self.page is not None

        try:
            # Wait for the results feed to be fully loaded
            self.logger.info("⏳ Waiting for business listings to load...")
            try:
                self.page.wait_for_selector('div[role="feed"]', timeout=10000)
                time.sleep(2)  # Extra wait for JavaScript to populate links
            except Exception:
                self.logger.warning("Feed container not found, continuing anyway...")
                time.sleep(3)

            # Debug: Log what's actually on the page
            try:
                page_html = self.page.content()
                has_hfpxzc = 'class="hfpxzc"' in page_html
                has_maps_place = "/maps/place/" in page_html
                self.logger.info(
                    f"Page analysis: has 'hfpxzc' class: {has_hfpxzc}, has '/maps/place/': {has_maps_place}"
                )
            except Exception:
                pass

            # Method 1: Use JavaScript to extract all URLs from the page at once (FASTEST)
            try:
                self.logger.info("Attempting to extract URLs using JavaScript...")

                # Run JavaScript to find all business links
                js_code = """
                () => {
                    const urls = new Set();
                    
                    // Try method 1: Find a.hfpxzc links (the actual business links)
                    const hfpxzcLinks = document.querySelectorAll('a.hfpxzc[href*="/maps/place/"]');
                    for (let link of hfpxzcLinks) {
                        const href = link.getAttribute('href');
                        if (href && href.includes('/maps/place/')) {
                            urls.add(href.split('?')[0]);
                        }
                    }
                    
                    // Try method 2: Find all anchor links with /maps/place/
                    const links = document.querySelectorAll('a[href*="/maps/place/"]');
                    for (let link of links) {
                        const href = link.getAttribute('href');
                        if (href && href.includes('/maps/place/')) {
                            urls.add(href.split('?')[0]);
                        }
                    }
                    
                    // Try method 3: Find all divs with data attributes pointing to places
                    const divs = document.querySelectorAll('div[data-cid], div[data-placeid]');
                    for (let div of divs) {
                        const link = div.querySelector('a[href*="/maps/place/"]');
                        if (link) {
                            const href = link.getAttribute('href');
                            if (href) urls.add(href.split('?')[0]);
                        }
                    }
                    
                    // Return as array with count info
                    return {
                        urls: Array.from(urls),
                        hfpxzcCount: hfpxzcLinks.length,
                        allLinksCount: links.length
                    };
                }
                """

                result = self.page.evaluate(js_code)
                if result and isinstance(result, dict):
                    urls_from_js = result.get("urls", [])
                    hfpxzc_count = result.get("hfpxzcCount", 0)
                    all_links_count = result.get("allLinksCount", 0)

                    self.logger.info(
                        f"📊 Found {hfpxzc_count} a.hfpxzc links, {all_links_count} total /maps/place/ links"
                    )

                    if urls_from_js and len(urls_from_js) > 0:
                        business_links = list(set(urls_from_js))  # Deduplicate
                        self.logger.info(
                            f"✓ SUCCESS: Found {len(business_links)} business URLs via JavaScript extraction (METHOD 1)"
                        )
                        return business_links
                    else:
                        self.logger.warning(
                            f"❌ Method 1 (JavaScript extraction) returned no URLs (despite finding {hfpxzc_count} a.hfpxzc links)"
                        )
                else:
                    self.logger.warning(
                        f"❌ Method 1 (JavaScript extraction) returned unexpected format: {type(result)}"
                    )

            except Exception as e:
                self.logger.warning(f"❌ Method 1 (JavaScript extraction) failed: {e}")

            # Method 2: Extract href from anchor links with /maps/place/ URLs
            try:
                # First try a.hfpxzc specifically
                hfpxzc_links = self.page.query_selector_all(
                    'a.hfpxzc[href*="/maps/place/"]'
                )
                all_links = self.page.query_selector_all('a[href*="/maps/place/"]')

                links = hfpxzc_links if hfpxzc_links else all_links

                if links:
                    self.logger.info(
                        f"📊 Found {len(hfpxzc_links)} a.hfpxzc links, {len(all_links)} total /maps/place/ links via DOM selector"
                    )
                    seen_urls = set()

                    for link in links:
                        try:
                            href = link.get_attribute("href")
                            if href and "/maps/place/" in href:
                                base_url = href.split("?")[0] if "?" in href else href

                                if base_url not in seen_urls:
                                    business_links.append(href)
                                    seen_urls.add(base_url)
                                    self.logger.debug(f"Extracted URL: {href[:100]}...")
                        except Exception as e:
                            self.logger.debug(f"Error extracting link: {e}")
                            continue

                    if business_links:
                        self.logger.info(
                            f"✓ SUCCESS: Found {len(business_links)} business URLs via DOM selector (METHOD 2)"
                        )
                        return business_links
                    else:
                        self.logger.warning(
                            f"❌ Method 2 (DOM selector) found links but extracted no URLs"
                        )

            except Exception as e:
                self.logger.warning(f"❌ Method 2 (DOM selector) failed: {e}")

            # Method 3: Click buttons as fallback (slower but reliable)
            try:
                buttons = self.page.query_selector_all("button.hfpxzc")
                if buttons:
                    self.logger.info(
                        f"Found {len(buttons)} hfpxzc buttons, trying button click method (METHOD 3)..."
                    )
                    seen_urls = set()
                    max_buttons = self.config.get("scraper", {}).get(
                        "max_buttons_to_click", 50
                    )

                    for i in range(
                        min(len(buttons), max_buttons)
                    ):  # Limit to avoid timeout
                        try:
                            # Re-query to avoid stale references
                            button_list = self.page.query_selector_all("button.hfpxzc")
                            if i < len(button_list):
                                button_list[i].click()
                                time.sleep(0.5)  # Reduced from 1 second
                                current_url = self.page.url

                                if (
                                    "/maps/place/" in current_url
                                    and current_url not in seen_urls
                                ):
                                    business_links.append(current_url)
                                    seen_urls.add(current_url)
                                    self.logger.debug(
                                        f"Extracted URL from button {i}: {current_url[:100]}..."
                                    )
                        except Exception as e:
                            self.logger.debug(f"Error with button {i}: {e}")
                            continue

                    if business_links:
                        self.logger.info(
                            f"✓ SUCCESS: Found {len(business_links)} business URLs via button clicks (METHOD 3)"
                        )
                        return business_links
                    else:
                        self.logger.warning(
                            f"❌ Method 3 (button clicks) - clicked {len(buttons)} buttons but found no valid URLs"
                        )
                else:
                    self.logger.warning(
                        f"❌ Method 3 (button clicks) - no hfpxzc buttons found"
                    )

            except Exception as e:
                self.logger.warning(f"❌ Method 3 (button clicks) failed: {e}")

            if not business_links:
                self.logger.error(
                    "❌ TOTAL FAILURE: Could not find any business URLs using any method"
                )
                self.logger.error(
                    f"   Page URL: {self.page.url if self.page else 'N/A'}"
                )
                self.logger.error(f"   All 3 extraction methods failed")

        except Exception as e:
            self.logger.error(f"Error extracting business links: {e}")

        return business_links

    def save_to_csv(self, keyword, city, output_subdir: Optional[str] = None):
        """Save scraped businesses to CSV"""
        if not self.businesses:
            self.logger.warning("No businesses to save")
            return None

        result = self.csv_handler.export_to_csv(
            self.businesses, keyword, city, output_subdir=output_subdir
        )

        # Clean up partial file from periodic saves (if it exists)
        if result:
            try:
                from src.utils import sanitize_filename

                sanitized_city = sanitize_filename(city)
                sanitized_keyword = sanitize_filename(keyword)
                partial_filename = f"{sanitized_city}_{sanitized_keyword}_partial.csv"
                candidate_dirs = [self.csv_handler.output_dir]
                if output_subdir:
                    candidate_dirs.append(
                        self.csv_handler.output_dir / sanitize_filename(output_subdir)
                    )

                for candidate_dir in candidate_dirs:
                    partial_file = candidate_dir / partial_filename
                    if partial_file.exists():
                        partial_file.unlink()
                        self.logger.debug(f"Cleaned up partial file: {partial_file}")
            except Exception:
                pass

        return result
