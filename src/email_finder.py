"""Find email addresses by crawling business websites"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Any, Optional
from src.utils import extract_emails
import time


class EmailFinder:
    """Crawls websites to find email addresses"""

    def __init__(self, config: dict[str, Any], logger: Any) -> None:
        self.config = config
        self.logger = logger

        email_config = config.get("email_extraction", {})
        self.timeout = email_config.get("timeout", 10)
        self.secondary_timeout = max(
            1, email_config.get("secondary_page_timeout", min(8, self.timeout))
        )
        self.max_pages = email_config.get("max_pages_per_site", 3)
        self.max_retries = email_config.get("max_retries", 3)
        self.retry_connect_errors = email_config.get("retry_connect_errors", 0)
        self.retry_read_errors = email_config.get("retry_read_errors", 0)
        self.retry_backoff_factor = email_config.get("retry_backoff_factor", 0.2)
        self.status_forcelist = email_config.get(
            "status_forcelist", [429, 500, 502, 503, 504]
        )
        self.common_paths = email_config.get(
            "common_paths",
            ["", "/contact", "/about", "/kontakt", "/mentions-legales", "/impressum"],
        )

        # Setup session with retry logic
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            connect=self.retry_connect_errors,
            read=self.retry_read_errors,
            status=self.max_retries,
            other=0,
            backoff_factor=self.retry_backoff_factor,
            status_forcelist=self.status_forcelist,
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def _is_unrecoverable_ssl_error(self, error: Exception) -> bool:
        """Return True for TLS/SSL failures that are unlikely to succeed on retries."""
        error_text = str(error).lower()
        unrecoverable_markers = (
            "unexpected eof while reading",
            "eof occurred in violation of protocol",
            "certificate verify failed",
            "wrong version number",
            "sslv3 alert",
            "tlsv1 alert",
            "handshake failure",
            "remote end closed connection without response",
            "remotedisconnected",
        )
        return any(marker in error_text for marker in unrecoverable_markers)

    def find_emails_from_website(self, website_url: str) -> list[str]:
        """
        Find email addresses from a business website

        Args:
            website_url: The website URL to crawl

        Returns:
            list: List of found email addresses
        """
        if not website_url:
            return []

        all_emails: set[str] = set()

        try:
            # Parse base URL
            parsed_url = urlparse(website_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # Pages to check
            pages_to_check = []
            for path in self.common_paths:
                if path:
                    full_url = urljoin(base_url, path)
                else:
                    full_url = base_url
                pages_to_check.append(full_url)

            # Limit number of pages
            pages_to_check = pages_to_check[: self.max_pages]

            # Crawl each page
            for page_url in pages_to_check:
                try:
                    self.logger.debug(f"Checking: {page_url}")

                    request_timeout = (
                        self.timeout if page_url == base_url else self.secondary_timeout
                    )

                    response = self.session.get(
                        page_url, timeout=request_timeout, allow_redirects=True
                    )

                    # Only process successful responses
                    if response.status_code == 200:
                        # Parse HTML
                        soup = BeautifulSoup(response.text, "html.parser")

                        # Extract emails from page text
                        page_text = soup.get_text()
                        emails = extract_emails(page_text)
                        all_emails.update(emails)

                        # Also check mailto links
                        mailto_links = soup.find_all(
                            "a", href=lambda x: bool(x and x.startswith("mailto:"))
                        )
                        for link in mailto_links:
                            href = link.get("href")
                            if not isinstance(href, str):
                                continue
                            email = href.replace("mailto:", "").split("?")[0]
                            email = email.strip()
                            if email and "@" in email:
                                all_emails.add(email)

                        # Small delay between requests
                        time.sleep(0.5)

                except requests.Timeout:
                    self.logger.debug(f"Timeout accessing: {page_url}")
                except requests.RequestException as e:
                    if self._is_unrecoverable_ssl_error(e):
                        self.logger.debug(
                            f"Unrecoverable SSL/TLS error for {base_url}, skipping remaining paths"
                        )
                        break
                    self.logger.debug(f"Error accessing {page_url}: {str(e)[:50]}")
                except Exception as e:
                    self.logger.debug(f"Error parsing {page_url}: {str(e)[:50]}")

            if all_emails:
                self.logger.info(f"✓ Found {len(all_emails)} email(s) from {base_url}")

        except Exception as e:
            self.logger.debug(f"Error crawling {website_url}: {str(e)[:100]}")

        return list(all_emails)

    def find_emails_with_playwright(self, page: Any, website_url: str) -> list[str]:
        """
        Alternative method: Use existing Playwright page to find emails.
        This is slower but can handle JavaScript-heavy sites.

        Note: This method is available for use with JS-heavy sites but
        the default find_emails_from_website() uses requests which is faster.

        Args:
            page: Playwright page object
            website_url: Website URL to crawl

        Returns:
            list: List of found email addresses
        """
        if not website_url:
            return []

        all_emails: set[str] = set()

        try:
            # Navigate to website
            page.goto(
                website_url, wait_until="domcontentloaded", timeout=self.timeout * 1000
            )
            time.sleep(2)  # Let JS load

            # Extract emails from page content
            page_content = page.content()
            emails = extract_emails(page_content)
            all_emails.update(emails)

            # Also get visible text
            try:
                body_text = page.inner_text("body")
                emails_from_text = extract_emails(body_text)
                all_emails.update(emails_from_text)
            except Exception:
                pass

            if all_emails:
                self.logger.info(
                    f"✓ Found {len(all_emails)} email(s) from {website_url}"
                )

        except Exception as e:
            self.logger.debug(f"Error with Playwright email search: {str(e)[:100]}")

        return list(all_emails)
