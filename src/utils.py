"""Utility functions for the scraper"""

import random
import sys
import time
import logging
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
import phonenumbers
from rich.console import Console
from rich.logging import RichHandler

console = Console()


def load_config(config_path: str = "config/settings.yaml") -> dict[str, Any]:
    """Load configuration from YAML file

    Args:
        config_path: Path to the YAML config file

    Returns:
        Configuration dictionary
    """
    path = Path(config_path)
    if not path.exists():
        console.print(f"[red]Error: {config_path} not found![/red]")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def setup_logging(log_dir="data/logs"):
    """Setup logging with rich handler"""
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    log_file = Path(log_dir) / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(console=console, rich_tracebacks=True),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )

    return logging.getLogger("scraper")


def random_delay(min_seconds=3, max_seconds=8):
    """Sleep for a random duration to mimic human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay


def extract_emails(text):
    """Extract email addresses from text using regex"""
    if not text:
        return []

    # Email regex pattern
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    emails = re.findall(email_pattern, text)

    # Filter out common fake/invalid emails
    invalid_patterns = [
        "example.com",
        "test.com",
        "noreply",
        "no-reply",
        "donotreply",
        "mailer-daemon",
        "postmaster",
        "abuse",
        "spam",
        "privacy@",
        "legal@",
        "copyright@",
        "dmca@",
        "wix.com",
        "squarespace.com",
        "wordpress.com",
        "placeholder",
        "youremail",
        "yourname",
        "example@",
        "user@",
        "email@",
        "info.info",  # Obviously fake
        "contact.contact",  # Obviously fake
    ]

    valid_emails = []
    for email in emails:
        email_lower = email.lower()
        if not any(pattern in email_lower for pattern in invalid_patterns):
            valid_emails.append(email)

    # Return unique emails
    return list(set(valid_emails))


def normalize_phone_number(
    phone_str: str,
    country_code: str = "US",
    exclude_patterns: Optional[list[str]] = None,
) -> Optional[str]:
    """
    Normalize phone number to E.164 format

    Args:
        phone_str: Raw phone number string
        country_code: ISO country code (US, FR, IT, etc.)
        exclude_patterns: List of patterns to exclude (e.g., toll-free prefixes)

    Returns:
        Normalized phone number in E.164 format (+33142654321) or None
    """
    if not phone_str:
        return None

    # Default exclude patterns (toll-free numbers)
    if exclude_patterns is None:
        exclude_patterns = ["800", "888", "877", "866", "855", "844", "833"]

    try:
        # Parse phone number
        phone_obj = phonenumbers.parse(phone_str, country_code)

        # Validate
        if phonenumbers.is_valid_number(phone_obj):
            # Format to E.164
            formatted = phonenumbers.format_number(
                phone_obj, phonenumbers.PhoneNumberFormat.E164
            )

            # Check exclusion patterns
            if exclude_patterns:
                for pattern in exclude_patterns:
                    # Check if the number contains the pattern after country code
                    # E.164 format: +1800..., +1888..., etc.
                    if pattern in formatted:
                        return None

            return formatted
        else:
            return None
    except Exception:
        # If parsing fails, return None
        return None


def extract_phone_numbers(
    text: str, country_code: str = "US", exclude_patterns: Optional[list[str]] = None
) -> list[str]:
    """
    Extract and normalize phone numbers from text

    Args:
        text: Text to search for phone numbers
        country_code: ISO country code for parsing
        exclude_patterns: List of patterns to exclude (e.g., toll-free prefixes)

    Returns:
        List of normalized phone numbers
    """
    if not text:
        return []

    # Common phone number patterns
    phone_patterns = [
        r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
        r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",  # US format
        r"\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}",  # European format
    ]

    potential_phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        potential_phones.extend(matches)

    # Normalize all found numbers
    normalized = []
    for phone in potential_phones:
        normalized_phone = normalize_phone_number(phone, country_code, exclude_patterns)
        if normalized_phone:
            normalized.append(normalized_phone)

    # Return unique phone numbers
    return list(set(normalized))


def sanitize_filename(filename):
    """Sanitize filename by removing invalid characters"""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")
    # Limit length
    return sanitized[:100]


def get_country_code_from_city(city):
    """
    Get ISO country code from city name.
    Delegates to the centralized geo_data module.
    """
    from src.geo_data import get_country_code_for_city

    return get_country_code_for_city(city)


def clean_text(text):
    """Clean text by removing extra whitespace and special characters"""
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


# Consent and popup language coverage mirrors all scraper scripts:
# de, it, es, pt, nl, fr, da, sv, no, fi, mt, pl, cs, sk, hu, sl, hr, sr, sq, mk, bg, ro, el.
CONSENT_DETECTION_PHRASES = [
    # "Before you continue to Google"
    "before you continue to google",
    "zanim przejdziesz do google",
    "bevor sie zu google weitergehen",
    "avant de continuer vers google",
    "prima di continuare su google",
    "antes de continuar en google",
    "antes de continuar para o google",
    "voordat je doorgaat naar google",
    "for du fortsaetter til google",
    "for du fortsetter til google",
    "innan du fortsatter till google",
    "ennen kuin jatkat googleen",
    "qabel tkompli fuq google",
    "než přejdete na google",
    "predtým, než prejdete na google",
    "mielőtt továbblépne a google-ra",
    "preden nadaljujete v google",
    "prije nego što nastavite na google",
    "пре него што наставите на google",
    "para se të vazhdoni në google",
    "пред да продолжите на google",
    "преди да продължите към google",
    "înainte de a continua pe google",
    "προτού συνεχίσετε στην google",
    # Cookie/consent wording
    "we use cookies",
    "używamy plików cookie",
    "nous utilisons des cookies",
    "utilizziamo i cookie",
    "usamos cookies",
    "utilizamos cookies",
    "wij gebruiken cookies",
    "vi bruger cookies",
    "vi anvander cookies",
    "vi bruker cookies",
    "vi bruker informasjonskapsler",
    "kaytamme evasteita",
    "käytämme evästeitä",
    "nuzaw cookies",
    "nużaw cookies",
    "nużaw il-cookies",
    "používáme soubory cookie",
    "používame súbory cookie",
    "cookie-kat használunk",
    "uporabljamo piškotke",
    "koristimo kolačiće",
    "користимо колачиће",
    "përdorim cookie",
    "користиме колачиња",
    "използваме бисквитки",
    "folosim cookie-uri",
    "χρησιμοποιούμε cookies",
]

CONSENT_ACCEPT_TEXTS = [
    "Accept all",
    "Zaakceptuj wszystko",
    "Alle akzeptieren",
    "Tout accepter",
    "Accetta tutto",
    "Aceptar todo",
    "Aceitar tudo",
    "Alles accepteren",
    "Accepter alle",
    "Acceptera alla",
    "Godta alle",
    "Hyväksy kaikki",
    "Aċċetta kollox",
    "Přijmout vše",
    "Prijať všetko",
    "Az összes elfogadása",
    "Összes elfogadása",
    "Sprejmi vse",
    "Prihvati sve",
    "Прихвати све",
    "Prano të gjitha",
    "Прифати сè",
    "Приемам всички",
    "Acceptă tot",
    "Acceptați tot",
    "Αποδοχή όλων",
    # Alternate one-button confirmation wording
    "I agree",
    "Souhlasím",
    "Súhlasím",
    "Egyetértek",
    "Strinjam se",
    "Slažem se",
    "Слажем се",
    "Pajtohem",
    "Се согласувам",
    "Съгласен съм",
    "Sunt de acord",
    "Συμφωνώ",
]

CONSENT_REJECT_TEXTS = [
    "Reject all",
    "Odrzuć wszystko",
    "Alle ablehnen",
    "Tout refuser",
    "Rifiuta tutto",
    "Rechazar todo",
    "Rejeitar tudo",
    "Alles weigeren",
    "Afvis alle",
    "Avvisa alla",
    "Avvis alle",
    "Hylkää kaikki",
    "Irrifjuta kollox",
    "Odmítnout vše",
    "Odmietnuť všetko",
    "Összes elutasítása",
    "Zavrni vse",
    "Odbij sve",
    "Одбиј све",
    "Refuzo të gjitha",
    "Одбиј сè",
    "Отхвърляне на всички",
    "Respinge tot",
    "Απόρριψη όλων",
]

POPUP_DETECTION_PHRASES = [
    "uaktualnij aplikację",
    "update the app",
    "upgrade to a smarter",
    "open the google maps app",
    "auf das noch smartere",
    "smartere google maps",
    "umsteigen",
    "echtzeit",
    "get real-time",
    "turn-by-turn navigation",
    "get real-time navigation",
    "keep using web",
    "go back to web",
    "stay in browser",
    "mettre à jour",
    "actualizar",
    "aggiorna",
    "aktualisieren",
    "atualizar",
    "bijwerken",
    "opdater appen",
    "uppdatera appen",
    "oppdater appen",
    "paivita sovellus",
    "päivitä sovellus",
    "aggorna l-app",
    "aktualizujte aplikaci",
    "aktualizovať aplikáciu",
    "frissítse az alkalmazást",
    "posodobite aplikacijo",
    "ažurirajte aplikaciju",
    "ажурирајте апликацију",
    "përditëso aplikacionin",
    "ажурирај ја апликацијата",
    "актуализирайте приложението",
    "actualizați aplicația",
    "ενημερώστε την εφαρμογή",
    "wróć do przeglądarki",
    "zurück zur webversion",
    "retour au web",
    "volver a la web",
    "torna alla versione web",
    "voltar à versão web",
    "tilbage til webversionen",
    "tillbaka till webben",
    "tilbake til nettet",
    "palaa verkkoversioon",
    "lura għall-web",
]

POPUP_DISMISS_TEXTS = [
    "Keep using web",
    "Go back to web",
    "Stay in browser",
    "No thanks",
    "Wróć do przeglądarki",
    "Zurück zur Webversion",
    "Im Browser bleiben",
    "Nein danke",
    "Retour au web",
    "Rester dans le navigateur",
    "Non merci",
    "Volver a la web",
    "Seguir en el navegador",
    "No, gracias",
    "Torna alla versione web",
    "Resta nel browser",
    "No, grazie",
    "Voltar à versão web",
    "Continuar no navegador",
    "Não, obrigado",
    "Terug naar webversie",
    "Blijf in browser",
    "Nee bedankt",
    "Tilbage til webversionen",
    "Bliv i browseren",
    "Nej tak",
    "Tillbaka till webben",
    "Stanna i webblasaren",
    "Nej tack",
    "Tilbake til nettet",
    "Fortsett i nettleseren",
    "Nei takk",
    "Palaa verkkoversioon",
    "Pysy selaimessa",
    "Ei kiitos",
    "Lura għall-web",
    "Ibqa' fil-browser",
    "Le grazzi",
    "Zůstat v prohlížeči",
    "Zpět na web",
    "Zostať v prehliadači",
    "Maradás a böngészőben",
    "Sprejmi in nadaljuj v brskalniku",
    "Nastavi u pregledniku",
    "Остани у прегледачу",
    "Qëndro në shfletues",
    "Остани во прелистувач",
    "Останете в браузъра",
    "Rămâi în browser",
    "Μείνετε στο πρόγραμμα περιήγησης",
]

POPUP_CLOSE_ARIA_TERMS = [
    "dismiss",
    "close",
    "zamknij",
    "fermer",
    "cerrar",
    "chiudi",
    "fechar",
    "sluiten",
    "luk",
    "lukk",
    "stang",
    "sulje",
    "aghlaq",
    "agħlaq",
    "zavřít",
    "zavrieť",
    "bezárás",
    "zapri",
    "zatvori",
    "mbyll",
    "затвори",
    "închide",
    "κλείσιμο",
]


def is_cookie_consent_present(page):
    """
    Check if Google's cookie consent page is present

    Args:
        page: Playwright page object

    Returns:
        Boolean indicating if cookie consent page is detected
    """
    try:
        # Also check URL for consent page
        if "consent.google" in page.url.lower():
            return True

        page_text = page.inner_text("body").lower()
        return any(phrase in page_text for phrase in CONSENT_DETECTION_PHRASES)

    except Exception:
        return False


def handle_cookie_consent(page, logger):
    """
    Automatically handle Google's cookie consent page

    Args:
        page: Playwright page object
        logger: Logger instance

    Returns:
        Boolean indicating if consent was handled
    """
    try:
        if not is_cookie_consent_present(page):
            return False

        logger.info("Cookie consent page detected, attempting to accept...")

        accept_button_selectors = []
        for text in CONSENT_ACCEPT_TEXTS:
            accept_button_selectors.append(f'button:has-text("{text}")')
            accept_button_selectors.append(f'[role="button"]:has-text("{text}")')

        accept_button_selectors.extend(
            [
                'button[aria-label*="Accept"]',
                'button[aria-label*="Zaakceptuj"]',
                'button[aria-label*="Akzept"]',
                'button[aria-label*="Accepter"]',
                'button[aria-label*="Accetta"]',
                'button[aria-label*="Aceptar"]',
                'button[aria-label*="Aceitar"]',
                'button[aria-label*="Accepteren"]',
                'button[aria-label*="Přijmout"]',
                'button[aria-label*="Prijať"]',
                'button[aria-label*="Elfogad"]',
                'button[aria-label*="Sprejmi"]',
                'button[aria-label*="Prihvati"]',
                'button[aria-label*="Prano"]',
                'button[aria-label*="Прифати"]',
                'button[aria-label*="Прием"]',
                'button[aria-label*="Acceptă"]',
                'button[aria-label*="Αποδοχή"]',
            ]
        )

        # Try translated selectors first, then generic consent form selectors.
        for selector in accept_button_selectors:
            try:
                button = page.query_selector(selector)
                if button and button.is_visible():
                    logger.info(f"Clicking consent button: {selector}")
                    button.click(timeout=2000)
                    time.sleep(2)
                    logger.info("✓ Cookie consent accepted")
                    return True
            except Exception as e:
                logger.debug(f"Failed with selector {selector}: {e}")
                continue

        # Fallback 1: score visible consent buttons by translated accept/reject texts.
        try:
            clicked = page.evaluate(
                """({acceptTexts, rejectTexts}) => {
                    const selectors = [
                        'form[action*="consent"] button',
                        'form[action*="consent"] [role="button"]',
                        'form[action*="consent"] input[type="submit"]'
                    ];
                    const elements = [];
                    for (const selector of selectors) {
                        for (const el of document.querySelectorAll(selector)) {
                            if (!elements.includes(el)) {
                                elements.push(el);
                            }
                        }
                    }

                    let bestElement = null;
                    let bestScore = 0;

                    for (const el of elements) {
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden') {
                            continue;
                        }

                        const text = ((el.textContent || '') + ' ' + (el.getAttribute('aria-label') || '')).toLowerCase();
                        if (!text.trim()) {
                            continue;
                        }

                        let score = 0;
                        for (const acceptText of acceptTexts) {
                            if (text.includes(acceptText)) score += 5;
                        }
                        for (const rejectText of rejectTexts) {
                            if (text.includes(rejectText)) score -= 8;
                        }

                        if (el.closest('form[action*="consent"]')) {
                            score += 1;
                        }

                        if (score > bestScore) {
                            bestScore = score;
                            bestElement = el;
                        }
                    }

                    if (bestElement && bestScore > 0) {
                        bestElement.click();
                        return true;
                    }

                    return false;
                }""",
                {
                    "acceptTexts": [text.lower() for text in CONSENT_ACCEPT_TEXTS],
                    "rejectTexts": [text.lower() for text in CONSENT_REJECT_TEXTS],
                },
            )

            if clicked:
                logger.info("✓ Cookie consent accepted via scored fallback")
                time.sleep(2)
                return True
        except Exception as e:
            logger.debug(f"Scored fallback consent click failed: {e}")

        # Fallback 2: last visible consent submit button.
        try:
            consent_buttons = page.query_selector_all(
                'form[action*="consent"] button[type="submit"]'
            )
            for button in reversed(consent_buttons):
                if button and button.is_visible():
                    logger.info("Clicking fallback consent submit button")
                    button.click(timeout=2000)
                    time.sleep(2)
                    logger.info("✓ Cookie consent accepted via fallback")
                    return True
        except Exception as e:
            logger.debug(f"Fallback consent click failed: {e}")

        # If we couldn't click, try to navigate directly to Maps
        logger.warning("Could not click consent button, trying direct navigation...")
        return False

    except Exception as e:
        logger.error(f"Error handling cookie consent: {e}")
        return False


def handle_google_popups(page, logger):
    """
    Handle various Google Maps popups (update app, notifications, etc.)

    Args:
        page: Playwright page object
        logger: Logger instance

    Returns:
        Boolean indicating if any popup was handled
    """
    try:
        handled = False

        popup_modal_selectors = [
            'div[role="dialog"]',
            'div[role="alertdialog"]',
            ".modal",
            '[aria-modal="true"]',
            ".VfPpkd-fmcmS-eyIwS-AxUoEf",
        ]

        visible_popup = None
        for selector in popup_modal_selectors:
            try:
                popup = page.wait_for_selector(selector, timeout=500)
                if popup and popup.is_visible():
                    visible_popup = popup
                    break
            except Exception:
                continue

        if not visible_popup:
            return False

        popup_text = visible_popup.inner_text().lower() if visible_popup else ""
        popup_detected = any(phrase in popup_text for phrase in POPUP_DETECTION_PHRASES)

        if not popup_detected:
            return False

        logger.info("Google Maps popup detected, attempting to dismiss...")

        dismiss_selectors = []
        for text in POPUP_DISMISS_TEXTS:
            dismiss_selectors.append(f'button:has-text("{text}")')
            dismiss_selectors.append(f'[role="button"]:has-text("{text}")')

        for aria_term in POPUP_CLOSE_ARIA_TERMS:
            dismiss_selectors.append(f'button[aria-label*="{aria_term}"]')

        dismiss_selectors.extend(
            [
                '[aria-label*="close"]',
                '[aria-label*="Close"]',
                '[aria-label*="dismiss"]',
                '[aria-label*="Dismiss"]',
            ]
        )

        for selector in dismiss_selectors:
            try:
                button = visible_popup.query_selector(selector)
                if button and button.is_visible():
                    logger.info(f"Clicking popup dismiss button: {selector}")
                    button.click()
                    time.sleep(1)
                    handled = True
                    logger.info("✓ Popup dismissed")
                    return True
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {str(e)[:50]}")
                continue

        try:
            logger.info("No dismiss button found in popup, trying Escape key...")
            page.press("Escape")
            time.sleep(1)
            logger.info("✓ Popup closed with Escape")
            handled = True
            return True
        except Exception:
            pass

        return handled

    except Exception as e:
        logger.debug(f"Error handling Google popups: {e}")
        return False


def is_captcha_present(page):
    """
    Check if CAPTCHA is present on the page (with improved accuracy)

    Args:
        page: Playwright page object

    Returns:
        Boolean indicating if CAPTCHA is detected
    """
    try:
        # First check if it's just a cookie consent page (NOT a CAPTCHA)
        if is_cookie_consent_present(page):
            return False  # This is not a CAPTCHA, it's a consent page

        # Method 1: Check for visible CAPTCHA elements (most accurate)
        captcha_selectors = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="google.com/recaptcha"]',
            'iframe[title*="reCAPTCHA"]',
            'div[class*="g-recaptcha"]',
            'div[id*="captcha"]',
            ".captcha-container",
            "#captcha",
        ]

        for selector in captcha_selectors:
            element = page.query_selector(selector)
            if element:
                # Check if element is visible
                if element.is_visible():
                    return True

        # Method 2: Check for CAPTCHA blocking messages (Google's actual CAPTCHA page)
        blocking_phrases = [
            "unusual traffic from your computer network",
            "our systems have detected unusual traffic",
            "we have detected unusual traffic",
            "please show you're not a robot",
        ]

        page_text = page.inner_text("body").lower()

        for phrase in blocking_phrases:
            if phrase in page_text:
                return True

        # Method 3: Check page title and URL for actual CAPTCHA (not consent)
        title = page.title().lower()
        url = page.url.lower()

        # Google's actual CAPTCHA page has "sorry" in URL and robot in title
        if "sorry" in url and ("captcha" in title or "robot" in title):
            return True

        return False

    except Exception as e:
        # If we can't check, assume no CAPTCHA (avoid false positives)
        return False


# NOTE: play_alert_sound() and wait_for_user_captcha_solve() have been moved
# to src/notifications.py. Use captcha_alert_popup() from there instead.
