"""Extract business data from Google Maps pages"""

import re
import time
from typing import Any, Optional, Union
from src.utils import extract_emails, extract_phone_numbers, clean_text, random_delay


class DataExtractor:
    """Extracts business information from Google Maps"""

    def __init__(self, page: Any, config: dict[str, Any], logger: Any) -> None:
        self.page = page
        self.config = config
        self.logger = logger

    def extract_business_data(self, country_code: str = "US") -> dict[str, Any]:
        """
        Extract all available data from a business listing

        Args:
            country_code: ISO country code for phone parsing

        Returns:
            dict: Business data with phone, email, address, etc.
        """
        data: dict[str, Any] = {
            "business_name": None,
            "phone": None,
            "email": None,
            "address": None,
            "city": None,
            "postal_code": None,
            "country": country_code,
            "website": None,
            "rating": None,
            "review_count": None,
            "category": None,
            "google_maps_url": None,
            "hours": None,
            "price_range": None,
        }

        try:
            # Wait for business panel to load
            self.page.wait_for_selector("h1", timeout=5000)
            time.sleep(1)  # Let content settle

            # Extract business name
            try:
                name_element = self.page.query_selector("h1")
                if name_element:
                    data["business_name"] = clean_text(name_element.inner_text())
            except Exception as e:
                self.logger.debug(f"Failed to extract business name: {e}")

            # Extract phone number (multiple possible locations)
            phone = self._extract_phone(country_code)
            data["phone"] = phone

            # Extract address
            address_info = self._extract_address()
            data.update(address_info)

            # Extract website
            data["website"] = self._extract_website()

            # Extract rating and reviews
            rating_info = self._extract_rating()
            data.update(rating_info)

            # Extract category
            data["category"] = self._extract_category()

            # Extract Google Maps URL
            data["google_maps_url"] = self._extract_google_maps_url()

            # Extract hours (optional)
            data["hours"] = self._extract_hours()

            # Extract price range (optional)
            data["price_range"] = self._extract_price_range()

            self.logger.debug(f"Extracted data for: {data['business_name']}")

        except Exception as e:
            self.logger.error(f"Error extracting business data: {e}")

        return data

    def _extract_phone(self, country_code: str = "US") -> Optional[str]:
        """Extract phone number from various possible locations

        Args:
            country_code: ISO country code for phone parsing

        Returns:
            Normalized phone number or None
        """
        # Get phone exclusion patterns from config
        phone_config = self.config.get("phone_extraction", {})
        exclude_patterns = phone_config.get("exclude_patterns", ["800", "888", "877"])

        phone_selectors = [
            'button[data-item-id^="phone:tel:"]',
            'a[data-item-id^="phone:tel:"]',
            '[data-section-id="pn0"] button',
            'button[aria-label*="Phone"]',
            'button[aria-label*="Call"]',
            'a[href^="tel:"]',
        ]

        for selector in phone_selectors:
            try:
                elements = self.page.query_selector_all(selector)
                for element in elements:
                    # Try to get phone from various attributes
                    phone_text = None

                    # Check data-item-id
                    item_id = element.get_attribute("data-item-id")
                    if item_id and "tel:" in item_id:
                        phone_text = item_id.split("tel:")[-1]

                    # Check href
                    if not phone_text:
                        href = element.get_attribute("href")
                        if href and "tel:" in href:
                            phone_text = href.split("tel:")[-1]

                    # Check inner text
                    if not phone_text:
                        phone_text = element.inner_text()

                    # Check aria-label
                    if not phone_text:
                        aria_label = element.get_attribute("aria-label")
                        if aria_label:
                            phone_text = aria_label

                    if phone_text:
                        # Extract phone numbers from text with exclusion patterns
                        phones = extract_phone_numbers(
                            phone_text, country_code, exclude_patterns
                        )
                        if phones:
                            return phones[0]  # Return first valid phone
            except Exception:
                continue

        # Fallback: search contact-related sections only (not entire body)
        # This avoids false positives from zip codes, fax numbers, etc.
        contact_selectors = [
            '[data-section-id="pn0"]',  # Google Maps phone section
            '[aria-label*="Phone"]',
            '[aria-label*="phone"]',
            '[aria-label*="Telefon"]',
            '[aria-label*="Téléphone"]',
            '[aria-label*="Telefono"]',
            '[aria-label*="Teléfono"]',
        ]
        for selector in contact_selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    text = element.inner_text()
                    phones = extract_phone_numbers(text, country_code, exclude_patterns)
                    if phones:
                        return phones[0]
            except Exception:
                continue

        return None

    def _extract_address(self) -> dict[str, Optional[str]]:
        """Extract address components"""
        address_data: dict[str, Optional[str]] = {
            "address": None,
            "city": None,
            "postal_code": None,
            "country": None,
        }

        # Selectors for address
        address_selectors = [
            'button[data-item-id="address"]',
            '[data-section-id="ad"] button',
            'button[aria-label*="Address"]',
        ]

        for selector in address_selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    full_address = clean_text(element.inner_text())
                    if full_address:
                        address_data["address"] = full_address

                        # Try to parse city and postal code
                        # This is basic - can be improved with geopy or address parsing libraries
                        parts = full_address.split(",")
                        if len(parts) >= 2:
                            # Last part often contains city and postal code
                            last_part = parts[-1].strip()
                            # Look for postal code pattern
                            postal_match = re.search(r"\b\d{4,5}\b", last_part)
                            if postal_match:
                                address_data["postal_code"] = postal_match.group()

                            # City is usually second to last or in last part
                            if len(parts) >= 2:
                                city_part = (
                                    parts[-2].strip()
                                    if len(parts) > 2
                                    else parts[-1].strip()
                                )
                                # Remove postal code from city if present
                                city_part = re.sub(
                                    r"\b\d{4,5}\b", "", city_part
                                ).strip()
                                if city_part:
                                    address_data["city"] = city_part

                        break
            except Exception:
                continue

        return address_data

    def _extract_website(self):
        """Extract website URL"""
        website_selectors = [
            'a[data-item-id="authority"]',
            'a[aria-label*="Website"]',
            '[data-section-id="ws"] a',
        ]

        for selector in website_selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    href = element.get_attribute("href")
                    if href and not href.startswith("mailto:"):
                        # Clean Google redirect URLs
                        if "google.com/url?q=" in href:
                            # Extract actual URL from Google redirect
                            match = re.search(r"[?&]q=([^&]+)", href)
                            if match:
                                from urllib.parse import unquote

                                return unquote(match.group(1))
                        return href
            except Exception:
                continue

        return None

    def _extract_rating(self) -> dict[str, Any]:
        """Extract rating and review count using multiple methods"""
        rating_data: dict[str, Any] = {
            "rating": None,
            "review_count": None,
        }

        try:
            # Method 1: Look for the rating span with aria-hidden (most reliable)
            # Google shows rating like "4.5" in a span near stars
            rating_selectors = [
                'div.F7nice span[aria-hidden="true"]',  # Main rating display
                'span.ceNzKf[role="img"]',  # Rating with aria-label
                '[role="img"][aria-label*="stars"]',  # Fallback stars
                'span.ZkP5Je[aria-hidden="true"]',  # Alternative rating span
                "div.fontDisplayLarge",  # Large display rating
            ]

            for selector in rating_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    for element in elements:
                        # Try aria-label first
                        aria_label = element.get_attribute("aria-label")
                        if aria_label:
                            # Match patterns like "4.5 stars" or "4,5 Sterne" (German)
                            rating_match = re.search(
                                r"([\d,\.]+)\s*(?:stars?|Sterne|stelle|estrellas|étoiles|sterren)",
                                aria_label,
                                re.IGNORECASE,
                            )
                            if rating_match:
                                rating_str = rating_match.group(1).replace(",", ".")
                                rating_data["rating"] = float(rating_str)
                                break

                        # Try inner text
                        text = element.inner_text().strip()
                        if text:
                            # Match rating like "4.5" or "4,5"
                            rating_match = re.match(r"^([\d,\.]+)$", text)
                            if rating_match:
                                rating_str = rating_match.group(1).replace(",", ".")
                                try:
                                    rating_val = float(rating_str)
                                    if 1.0 <= rating_val <= 5.0:  # Valid rating range
                                        rating_data["rating"] = rating_val
                                        break
                                except ValueError:
                                    pass

                    if rating_data["rating"]:
                        break
                except Exception:
                    continue

            # Method 2: Extract review count
            review_selectors = [
                'button[aria-label*="review"]',  # English
                'button[aria-label*="Rezension"]',  # German
                'button[aria-label*="recens"]',  # Italian/Spanish
                'button[aria-label*="avis"]',  # French
                'div.F7nice span[aria-label*="review"]',
                'span[aria-label*="review"]',
            ]

            for selector in review_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        aria_label = element.get_attribute("aria-label") or ""
                        text = element.inner_text() or ""
                        combined = f"{aria_label} {text}"

                        # Match patterns like "1,234 reviews" or "(1.234)"
                        review_match = re.search(
                            r"([\d,.]+)\s*(?:review|Rezension|recens|avis|beoordelingen)",
                            combined,
                            re.IGNORECASE,
                        )
                        if review_match:
                            count_str = (
                                review_match.group(1).replace(".", "").replace(",", "")
                            )
                            rating_data["review_count"] = int(count_str)
                            break

                        # Also try to find just a number in parentheses like "(234)"
                        paren_match = re.search(r"\(([\d,.]+)\)", combined)
                        if paren_match:
                            count_str = (
                                paren_match.group(1).replace(".", "").replace(",", "")
                            )
                            try:
                                rating_data["review_count"] = int(count_str)
                                break
                            except ValueError:
                                pass
                except Exception:
                    continue

            # Method 3: JavaScript extraction as fallback
            if not rating_data["rating"] or not rating_data["review_count"]:
                try:
                    js_result = self.page.evaluate("""
                        () => {
                            const result = { rating: null, review_count: null };
                            
                            // Find rating - look for text matching X.X pattern near stars
                            const allSpans = document.querySelectorAll('span');
                            for (const span of allSpans) {
                                const text = span.innerText?.trim();
                                if (text && /^[1-5][.,][0-9]$/.test(text)) {
                                    result.rating = parseFloat(text.replace(',', '.'));
                                    break;
                                }
                            }
                            
                            // Find review count - look for number followed by review text
                            const bodyText = document.body.innerText;
                            const reviewMatch = bodyText.match(/([\\d,.]+)\\s*(?:reviews?|Rezensionen?|recensioni|reseñas|avis)/i);
                            if (reviewMatch) {
                                result.review_count = parseInt(reviewMatch[1].replace(/[.,]/g, ''));
                            }
                            
                            return result;
                        }
                    """)
                    if js_result:
                        if not rating_data["rating"] and js_result.get("rating"):
                            rating_data["rating"] = js_result["rating"]
                        if not rating_data["review_count"] and js_result.get(
                            "review_count"
                        ):
                            rating_data["review_count"] = js_result["review_count"]
                except Exception:
                    pass

        except Exception as e:
            self.logger.debug(f"Failed to extract rating: {e}")

        return rating_data

    def _extract_category(self):
        """Extract business category/type"""
        try:
            # Category is often under the business name
            category_element = self.page.query_selector('button[jsaction*="category"]')
            if category_element:
                return clean_text(category_element.inner_text())

            # Alternative location
            category_element = self.page.query_selector(".DkEaL")
            if category_element:
                return clean_text(category_element.inner_text())
        except Exception as e:
            self.logger.debug(f"Failed to extract category: {e}")

        return None

    def _extract_google_maps_url(self) -> Optional[str]:
        """Extract Google Maps URL from address bar"""
        try:
            return self.page.url
        except Exception as e:
            self.logger.debug(f"Failed to extract Google Maps URL: {e}")
        return None

    def _extract_hours(self) -> Optional[str]:
        """Extract opening hours using multiple methods"""
        try:
            # Multiple selectors for hours in different languages
            hours_selectors = [
                # English
                'button[aria-label*="Hours"]',
                'button[data-item-id*="oh"]',  # oh = opening hours
                '[aria-label*="hours"]',
                # German
                'button[aria-label*="Öffnungszeiten"]',
                'button[aria-label*="ffnungszeiten"]',
                # Italian
                'button[aria-label*="Orari"]',
                'button[aria-label*="orario"]',
                # Spanish
                'button[aria-label*="Horario"]',
                # French
                'button[aria-label*="Horaires"]',
                # Dutch
                'button[aria-label*="Openingstijden"]',
                # Generic clock icon or time-related
                '[data-tooltip*="hours"]',
                '[data-tooltip*="Hours"]',
            ]

            for selector in hours_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        # Get aria-label which often has the full hours info
                        aria_label = element.get_attribute("aria-label")
                        if aria_label:
                            return clean_text(aria_label)

                        # Otherwise get inner text
                        text = element.inner_text()
                        if text:
                            return clean_text(text)
                except Exception:
                    continue

            # Method 2: Look for hours section by content pattern
            try:
                js_result = self.page.evaluate("""
                    () => {
                        // Look for elements containing time patterns like "9:00" or "09:00"
                        const timePattern = /\\d{1,2}[:.][0-9]{2}\\s*[-–]\\s*\\d{1,2}[:.][0-9]{2}/;
                        const elements = document.querySelectorAll('div, span, button');
                        
                        for (const el of elements) {
                            const text = el.innerText?.trim();
                            if (text && timePattern.test(text) && text.length < 200) {
                                // Check if it looks like hours (contains days or time ranges)
                                if (/Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun|Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag|Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato|Domenica|Open|Closed|Geöffnet|Geschlossen|Aperto|Chiuso/i.test(text)) {
                                    return text;
                                }
                            }
                        }
                        return null;
                    }
                """)
                if js_result:
                    return clean_text(js_result)
            except Exception:
                pass

        except Exception as e:
            self.logger.debug(f"Failed to extract hours: {e}")

        return None

    def _extract_price_range(self) -> Optional[str]:
        """Extract price range if available using multiple methods"""
        try:
            # Price range selectors for different languages
            price_selectors = [
                '[aria-label*="Price"]',
                '[aria-label*="price"]',
                '[aria-label*="Preis"]',  # German
                '[aria-label*="Prezzo"]',  # Italian
                '[aria-label*="Precio"]',  # Spanish
                '[aria-label*="Prix"]',  # French
                'span[aria-label*="€"]',
                'span[aria-label*="$"]',
            ]

            for selector in price_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        aria_label = element.get_attribute("aria-label")
                        if aria_label:
                            return clean_text(aria_label)
                        text = element.inner_text()
                        if text:
                            return clean_text(text)
                except Exception:
                    continue

            # Method 2: Look for price indicators (€, $, ££) in the page
            try:
                js_result = self.page.evaluate("""
                    () => {
                        // Look for price level indicators like €€, $$, £££
                        const pricePattern = /^[€$£]{1,4}$/;
                        const expensivePattern = /(?:€|\\$|£){1,4}\\s*[-–]\\s*(?:€|\\$|£){1,4}/;
                        
                        const elements = document.querySelectorAll('span, div');
                        for (const el of elements) {
                            const text = el.innerText?.trim();
                            if (text) {
                                // Match €€ or $$ style
                                if (pricePattern.test(text)) {
                                    return text;
                                }
                                // Match "€€ - €€€" style
                                if (expensivePattern.test(text)) {
                                    return text;
                                }
                                // Match "Moderate" or "Expensive" text
                                if (/^(Cheap|Moderate|Expensive|Inexpensive|Very Expensive|Günstig|Moderat|Teuer|Economico|Moderato|Costoso)$/i.test(text)) {
                                    return text;
                                }
                            }
                        }
                        return null;
                    }
                """)
                if js_result:
                    return clean_text(js_result)
            except Exception:
                pass

        except Exception as e:
            self.logger.debug(f"Failed to extract price range: {e}")

        return None
