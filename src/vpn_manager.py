"""VPN Manager for NordVPN integration with automatic rotation"""

import subprocess
import time
import logging
from typing import Optional, Tuple


class VPNManager:
    """Manages VPN connections using NordVPN CLI"""

    # Language code to NordVPN country code mapping
    LANGUAGE_TO_COUNTRY = {
        # European countries
        "de": "DE",  # German - Germany
        "de-de": "DE",
        "pl": "PL",  # Polish - Poland
        "pl-pl": "PL",
        "fr": "FR",  # French - France
        "fr-fr": "FR",
        "it": "IT",  # Italian - Italy
        "it-it": "IT",
        "es": "ES",  # Spanish - Spain
        "es-es": "ES",
        "pt": "PT",  # Portuguese - Portugal
        "pt-pt": "PT",
        "pt-br": "BR",  # Portuguese - Brazil
        "br": "BR",
        "en": "US",  # English - USA (default)
        "en-us": "US",
        "en-gb": "GB",  # English - UK
        "en-ie": "IE",  # English - Ireland
        "en-mt": "MT",  # English - Malta
        "gb": "GB",
        "nl": "NL",  # Dutch - Netherlands
        "nl-nl": "NL",
        "se": "SE",  # Swedish - Sweden
        "sv": "SE",
        "sv-se": "SE",
        "no": "NO",  # Norwegian - Norway
        "no-no": "NO",
        "nb-no": "NO",
        "da": "DK",  # Danish - Denmark
        "da-dk": "DK",
        "fi": "FI",  # Finnish - Finland
        "fi-fi": "FI",
        "mt": "MT",  # Maltese - Malta
        "mt-mt": "MT",
        "cs": "CZ",  # Czech - Czech Republic
        "cs-cz": "CZ",
        "sk": "SK",  # Slovak - Slovakia
        "sk-sk": "SK",
        "hu": "HU",  # Hungarian - Hungary
        "hu-hu": "HU",
        "sl": "SI",  # Slovenian - Slovenia
        "sl-si": "SI",
        "ro": "RO",  # Romanian - Romania
        "ro-ro": "RO",
        "bg": "BG",  # Bulgarian - Bulgaria
        "bg-bg": "BG",
        "hr": "HR",  # Croatian - Croatia
        "hr-hr": "HR",
        "sr": "RS",  # Serbian - Serbia
        "sr-rs": "RS",
        "sq": "AL",  # Albanian - Albania
        "sq-al": "AL",
        "mk": "MK",  # Macedonian - North Macedonia
        "mk-mk": "MK",
        "uk": "UA",  # Ukrainian - Ukraine
        "uk-ua": "UA",
        "ru": "RU",  # Russian - Russia (might not be available)
        "ru-ru": "RU",
        "tr": "TR",  # Turkish - Turkey
        "tr-tr": "TR",
        "el": "GR",  # Greek - Greece
        "el-gr": "GR",
        # Additional countries
        "ja": "JP",  # Japanese - Japan
        "ja-jp": "JP",
        "zh": "CN",  # Chinese - China
        "zh-cn": "CN",
        "zh-tw": "TW",  # Chinese Traditional - Taiwan
        "ko": "KR",  # Korean - South Korea
        "ko-kr": "KR",
        "th": "TH",  # Thai - Thailand
        "vi": "VN",  # Vietnamese - Vietnam
        "vi-vn": "VN",
        "ar": "AE",  # Arabic - UAE
        "ar-ae": "AE",
    }

    # NordVPN status output country name -> ISO code
    STATUS_COUNTRY_TO_CODE = {
        "albania": "AL",
        "austria": "AT",
        "belgium": "BE",
        "bosnia and herzegovina": "BA",
        "bulgaria": "BG",
        "croatia": "HR",
        "czech republic": "CZ",
        "denmark": "DK",
        "finland": "FI",
        "france": "FR",
        "germany": "DE",
        "greece": "GR",
        "hungary": "HU",
        "italy": "IT",
        "montenegro": "ME",
        "netherlands": "NL",
        "north macedonia": "MK",
        "norway": "NO",
        "poland": "PL",
        "portugal": "PT",
        "romania": "RO",
        "serbia": "RS",
        "slovakia": "SK",
        "slovenia": "SI",
        "spain": "ES",
        "sweden": "SE",
        "switzerland": "CH",
        "united kingdom": "GB",
        "united states": "US",
    }

    def __init__(
        self,
        logger: logging.Logger,
        enabled: bool = False,
        stable_country_mode: bool = True,
        event_rotation_enabled: bool = True,
    ):
        """
        Initialize VPN Manager

        Args:
            logger: Logger instance
            enabled: Whether VPN rotation is enabled
            stable_country_mode: Keep one country connection and disable interval rotation
            event_rotation_enabled: Allow rotation on block/captcha/timeout events
        """
        self.logger = logger
        self.enabled = enabled
        self.stable_country_mode = stable_country_mode
        self.event_rotation_enabled = event_rotation_enabled
        self.current_country = None
        self.scrape_count = 0
        self.rotation_interval = 50  # Rotate every 50 scrapes
        self.vpn_connected = False

    def get_country_from_language(self, language: str) -> Optional[str]:
        """
        Convert language code to NordVPN country code

        Args:
            language: Language code (e.g., 'de', 'pl', 'en')

        Returns:
            Country code for NordVPN or None if not found
        """
        language_lower = language.lower().strip()

        # Direct mapping
        if language_lower in self.LANGUAGE_TO_COUNTRY:
            return self.LANGUAGE_TO_COUNTRY[language_lower]

        # Try to extract base language code (e.g., 'de' from 'de-DE')
        if "-" in language_lower:
            base_lang = language_lower.split("-")[0]
            if base_lang in self.LANGUAGE_TO_COUNTRY:
                return self.LANGUAGE_TO_COUNTRY[base_lang]

        self.logger.warning(f"Unknown language code '{language}', defaulting to US")
        return "US"

    def is_vpn_connected(self) -> bool:
        """
        Check if VPN is currently connected

        Returns:
            Boolean indicating VPN connection status
        """
        try:
            country_code = self._get_connected_country_code()
            connected = country_code is not None

            if connected:
                self.current_country = country_code
                self.vpn_connected = True

            return connected

        except subprocess.TimeoutExpired:
            self.logger.error("VPN status check timed out")
            return False
        except FileNotFoundError:
            self.logger.error("NordVPN CLI not found. Install it with: nordvpn")
            return False
        except Exception as e:
            self.logger.error(f"Failed to check VPN status: {e}")
            return False

    def _get_connected_country_code(self) -> Optional[str]:
        """Return current connected country code from `nordvpn status`, if connected."""
        result = subprocess.run(
            ["nordvpn", "status"], capture_output=True, text=True, timeout=8
        )

        status_output = (result.stdout or "").lower()
        if result.returncode != 0 or "status: connected" not in status_output:
            return None

        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line.lower().startswith("country:"):
                continue

            country_value = line.split(":", 1)[1].strip()
            if len(country_value) == 2 and country_value.isalpha():
                return country_value.upper()

            country_key = country_value.lower().replace("_", " ").replace("-", " ")
            return self.STATUS_COUNTRY_TO_CODE.get(country_key)

        return None

    def _wait_until_connected_to_country(
        self, country: str, timeout_seconds: int = 20, poll_seconds: float = 2.0
    ) -> bool:
        """Poll NordVPN status until connected to target country or timeout."""
        deadline = time.time() + timeout_seconds
        target = country.upper()

        while time.time() < deadline:
            try:
                connected_country = self._get_connected_country_code()
                if connected_country == target:
                    return True
            except Exception as e:
                self.logger.debug(f"Status poll failed while waiting for {target}: {e}")

            time.sleep(poll_seconds)

        return False

    def connect(self, country: str) -> bool:
        """
        Connect to VPN in specified country

        Args:
            country: Country code (e.g., 'DE', 'PL', 'US')

        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            return True

        country = country.upper()

        try:
            # Avoid unnecessary reconnects when already on the right country.
            try:
                connected_country = self._get_connected_country_code()
                if connected_country == country:
                    self.logger.info(
                        f"Already connected to {country}, skipping reconnect"
                    )
                    self.current_country = country
                    self.vpn_connected = True
                    return True
            except Exception as e:
                self.logger.debug(f"Could not verify existing VPN country: {e}")

            self.logger.info(f"Connecting to NordVPN in {country}...")

            result = subprocess.run(
                ["nordvpn", "connect", country],
                capture_output=True,
                text=True,
                timeout=45,
            )

            if result.returncode == 0 and self._wait_until_connected_to_country(
                country
            ):
                self.logger.info(f"✓ Successfully connected to {country}")
                self.current_country = country
                self.vpn_connected = True
                self.scrape_count = 0
                time.sleep(2)
                return True

            error_msg = (result.stderr or result.stdout or "").strip()
            self.logger.warning(
                f"Initial connect attempt to {country} not confirmed: {error_msg}"
            )

        except subprocess.TimeoutExpired:
            self.logger.warning(
                f"VPN connection command to {country} timed out; checking live status..."
            )

            if self._wait_until_connected_to_country(country, timeout_seconds=25):
                self.logger.info(f"✓ Connected to {country} after timeout grace period")
                self.current_country = country
                self.vpn_connected = True
                self.scrape_count = 0
                time.sleep(2)
                return True

        except FileNotFoundError:
            self.logger.error("NordVPN CLI not found. Install it with: nordvpn")
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect VPN: {e}")
            return False

        # One controlled retry with explicit reconnect to reduce transient CZ failures.
        self.logger.warning(
            f"Retrying VPN connection to {country} with disconnect/reconnect sequence"
        )
        try:
            self.disconnect()
            time.sleep(2)

            retry = subprocess.run(
                ["nordvpn", "connect", country],
                capture_output=True,
                text=True,
                timeout=50,
            )

            if retry.returncode == 0 and self._wait_until_connected_to_country(country):
                self.logger.info(f"✓ Successfully connected to {country} on retry")
                self.current_country = country
                self.vpn_connected = True
                self.scrape_count = 0
                time.sleep(2)
                return True

            if self._wait_until_connected_to_country(country, timeout_seconds=20):
                self.logger.info(f"✓ Connected to {country} after retry grace period")
                self.current_country = country
                self.vpn_connected = True
                self.scrape_count = 0
                time.sleep(2)
                return True

            error_msg = (retry.stderr or retry.stdout or "").strip()
            self.logger.error(
                f"Failed to connect to {country} after retry: {error_msg}"
            )
            return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"VPN connection to {country} timed out after retry")
            return False
        except Exception as e:
            self.logger.error(f"Failed during VPN reconnect retry: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from VPN

        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            return True

        try:
            self.logger.info("Disconnecting from VPN...")

            result = subprocess.run(
                ["nordvpn", "disconnect"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                self.logger.info("✓ Successfully disconnected from VPN")
                self.vpn_connected = False
                self.current_country = None
                return True
            else:
                error_msg = result.stderr or result.stdout
                self.logger.error(f"Failed to disconnect VPN: {error_msg}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("VPN disconnection timed out")
            return False
        except FileNotFoundError:
            self.logger.error("NordVPN CLI not found")
            return False
        except Exception as e:
            self.logger.error(f"Failed to disconnect VPN: {e}")
            return False

    def rotate(
        self,
        country: str,
        force_reconnect: bool = False,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Rotate VPN connection to different country

        Args:
            country: Country code to connect to
            force_reconnect: Reconnect even if already in the same country
            reason: Optional reason for rotation (for logs)

        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            return True

        country = country.upper()

        if reason:
            self.logger.info(f"VPN rotate requested ({reason}) -> {country}")

        # If same country and force_reconnect is disabled, skip rotation
        if country == self.current_country and not force_reconnect:
            self.logger.debug(f"Already connected to {country}, skipping rotation")
            return True

        if country == self.current_country and force_reconnect:
            self.logger.info(
                f"Reconnecting in same country ({country}) to get a new exit node"
            )

        try:
            self.disconnect()
            time.sleep(1)  # Brief pause between disconnect and reconnect
            return self.connect(country)
        except Exception as e:
            self.logger.error(f"Failed to rotate VPN: {e}")
            return False

    def increment_scrape_count(self) -> Tuple[bool, Optional[str]]:
        """
        Increment scrape counter and check if rotation is needed

        Returns:
            Tuple of (should_rotate: bool, reason: str or None)
        """
        if not self.enabled:
            return False, None

        if self.stable_country_mode:
            return False, None

        if self.rotation_interval <= 0:
            return False, None

        self.scrape_count += 1

        if self.scrape_count >= self.rotation_interval:
            return True, f"Reached {self.rotation_interval} scrapes"

        return False, None

    def reset_scrape_count(self):
        """Reset scrape counter"""
        self.scrape_count = 0

    def handle_timeout(self, country: str) -> bool:
        """
        Handle timeout by rotating VPN

        Args:
            country: Country to reconnect to

        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            return True

        if not self.event_rotation_enabled:
            self.logger.debug(
                "Event-based rotation disabled, skipping timeout-triggered rotation"
            )
            return False

        self.logger.warning(f"Timeout detected, rotating VPN to {country}...")
        return self.rotate(country, force_reconnect=True, reason="timeout")

    def handle_block_event(self, country: str, event_name: str) -> bool:
        """Handle CAPTCHA/Google block style events with forced reconnect."""
        if not self.enabled:
            return True

        if not self.event_rotation_enabled:
            self.logger.debug(
                f"Event-based rotation disabled, skipping event: {event_name}"
            )
            return False

        self.logger.warning(f"{event_name} detected, rotating VPN to {country}...")
        return self.rotate(country, force_reconnect=True, reason=event_name)

    def get_status(self) -> dict:
        """
        Get current VPN status

        Returns:
            Dictionary with status information
        """
        return {
            "enabled": self.enabled,
            "connected": self.vpn_connected,
            "current_country": self.current_country,
            "stable_country_mode": self.stable_country_mode,
            "event_rotation_enabled": self.event_rotation_enabled,
            "scrape_count": self.scrape_count,
            "rotation_interval": self.rotation_interval,
        }
