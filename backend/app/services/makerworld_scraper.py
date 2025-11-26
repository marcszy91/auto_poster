"""MakerWorld scraper service using Playwright for web scraping."""

import asyncio
import re
from typing import Optional

from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

from app.config import settings
from app.logging_config import get_logger
from app.schemas.post import MakerWorldData

logger = get_logger(__name__)


class MakerWorldScraperError(Exception):
    """Custom exception for MakerWorld scraper errors."""

    pass


class MakerWorldScraper:
    """
    Service for scraping MakerWorld print model information.

    Attributes:
        browser: Playwright browser instance
        headless: Whether to run browser in headless mode
    """

    def __init__(self, headless: bool = True) -> None:
        """
        Initialize MakerWorld scraper.

        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None

    async def __aenter__(self) -> "MakerWorldScraper":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()

    def _parse_makerworld_input(self, input_str: str) -> tuple[str, str | None]:
        """
        Parse MakerWorld input (model ID or full URL).

        Args:
            input_str: Either a model ID (e.g., "938881") or full URL

        Returns:
            tuple: (full_url, profile_id or None)
        """
        input_str = input_str.strip()

        # Check if input is a full URL
        if input_str.startswith("http://") or input_str.startswith("https://"):
            # Extract profile ID from URL hash if present
            profile_id = None
            if "#profileId-" in input_str:
                # Split by # and extract profile ID
                parts = input_str.split("#profileId-")
                url = parts[0]
                profile_id = parts[1] if len(parts) > 1 else None
                logger.debug(f"Detected profile ID from URL: {profile_id}")
                return url, profile_id
            return input_str, None
        else:
            # Assume it's just a model ID
            url = f"{settings.makerworld_base_url}/models/{input_str}"
            return url, None

    async def scrape_model_data(self, makerworld_id_or_url: str) -> MakerWorldData:
        """
        Scrape model data from MakerWorld.

        Args:
            makerworld_id_or_url: MakerWorld model ID or full URL (with optional #profileId)

        Returns:
            MakerWorldData: Scraped model information

        Raises:
            MakerWorldScraperError: If scraping fails
        """
        # Parse input to extract model ID and optional profile ID
        url, profile_id = self._parse_makerworld_input(makerworld_id_or_url)

        try:
            async with async_playwright() as playwright:
                # Launch browser
                self.browser = await playwright.chromium.launch(headless=self.headless)
                context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    timezone_id="America/New_York",
                )
                page = await context.new_page()

                # Block unnecessary resources to speed up loading (except stylesheets for debugging)
                # Images, media, and fonts are blocked for faster loading
                await page.route(
                    "**/*",
                    lambda route: (
                        route.abort()
                        if route.request.resource_type in ["image", "media", "font"]
                        else route.continue_()
                    ),
                )

                # Set extra headers to look more like a real browser
                await page.set_extra_http_headers(
                    {
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    }
                )

                # Navigate to model page
                # If profile_id is provided, add it to URL fragment
                full_url = url
                if profile_id:
                    full_url = f"{url}#profileId-{profile_id}"
                    logger.info(f"Loading URL with profile ID: {full_url}")
                else:
                    logger.info(f"Loading URL: {full_url}")

                try:
                    # Try with domcontentloaded first (fastest, most reliable)
                    response = await page.goto(
                        full_url,
                        wait_until="domcontentloaded",
                        timeout=settings.scraper_timeout * 1000,
                    )
                    logger.debug(
                        f"Page loaded with status: {response.status if response else 'No response'}"
                    )
                except Exception as e:
                    logger.error(f"Error during page load: {str(e)}")
                    raise

                # Wait for dynamic content to load (SPA needs time to render)
                await asyncio.sleep(3)
                logger.debug("Waiting for JavaScript to render content...")

                # Wait for key elements to be present (optional)
                try:
                    logger.debug("Waiting for h1 element...")
                    await page.wait_for_selector("h1", timeout=10000)
                    logger.debug("h1 element found!")
                except Exception as e:
                    logger.warning(f"h1 element not found, continuing anyway: {str(e)}")

                # Take screenshot for debugging (optional, only if not headless)
                if not self.headless:
                    try:
                        screenshot_path = (
                            f"/tmp/makerworld_debug_{makerworld_id_or_url.split('/')[-1][:20]}.png"
                        )
                        await page.screenshot(path=screenshot_path)
                        logger.debug(f"Debug screenshot saved to: {screenshot_path}")
                    except Exception as e:
                        logger.warning(f"Could not save screenshot: {e}")

                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")

                # Extract model information (from main page)
                logger.info("Extracting model information...")
                title = await self._extract_title(page, soup)
                logger.info(f"Title: {title}")

                designer_name = await self._extract_designer(page, soup)
                logger.info(f"Designer: {designer_name}")

                # If no specific profile ID was provided, select P1S printer model
                if not profile_id:
                    logger.info("No profile ID specified, selecting P1S printer...")
                    await self._select_printer_model(page, "P1S")
                    # Wait for profile list to update
                    await asyncio.sleep(2)
                else:
                    logger.info(
                        f"Profile ID {profile_id} was provided via URL, waiting for page to load..."
                    )
                    # The URL already includes the profileId, wait a bit more for it to activate
                    await asyncio.sleep(3)

                # Get updated page content
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")

                # Extract profile information from active profile (with hover for details)
                logger.info("Extracting active profile information...")
                profile_data = await self._extract_active_profile_data_with_hover(
                    page, soup, designer_name
                )
                logger.debug(f"Profile title: {profile_data['profile_title']}")
                logger.debug(f"Profile designer: {profile_data['profile_designer']}")
                logger.debug(f"Print duration: {profile_data['print_duration']}")
                logger.debug(f"Materials: {profile_data['materials']}")
                logger.debug(f"Material amount: {profile_data['material_amount']}")

                await self.browser.close()

                return MakerWorldData(
                    title=title,
                    designer_name=designer_name,
                    profile_title=profile_data["profile_title"],
                    profile_designer=profile_data["profile_designer"],
                    print_duration=profile_data["print_duration"],
                    materials=profile_data["materials"],
                    material_amount=profile_data["material_amount"],
                )

        except PlaywrightTimeout:
            raise MakerWorldScraperError(f"Timeout while loading MakerWorld page: {url}")
        except Exception as e:
            raise MakerWorldScraperError(f"Failed to scrape MakerWorld data: {str(e)}")

    async def _extract_title(self, page: Page, soup: BeautifulSoup) -> str:
        """
        Extract model title.

        Args:
            page: Playwright page
            soup: BeautifulSoup parsed HTML

        Returns:
            str: Model title
        """
        # Try different selectors for title
        selectors = [
            'h1[data-testid="model-title"]',
            "h1.model-title",
            "h1",
            '[class*="title"]',
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    title = await element.inner_text()
                    if title and title.strip():
                        return title.strip()
            except Exception:
                continue

        # Fallback to BeautifulSoup
        title_elem = soup.find("h1")
        if title_elem:
            return title_elem.get_text(strip=True)

        return "Unknown Title"

    async def _extract_designer(self, page: Page, soup: BeautifulSoup) -> str:
        """
        Extract designer name from the main page.

        Args:
            page: Playwright page
            soup: BeautifulSoup parsed HTML

        Returns:
            str: Designer name
        """
        logger.debug("Looking for designer name...")

        try:
            # Strategy 1: Look in the main model info container (mw-css-1omp05f)
            # Designer is in: .mw-css-1omp05f > .mw-css-wn1ugj > .person-wrap > a.user_link > span.user_name
            logger.debug("Trying to find designer in main model info container...")

            designer_elem = await page.query_selector("div.mw-css-1omp05f span.user_name")
            if designer_elem:
                designer = (await designer_elem.inner_text()).strip()
                logger.info(f"Found designer in main container: {designer}")
                return designer

            # Alternative: try the link directly
            designer_link = await page.query_selector("div.mw-css-1omp05f a.user_link")
            if designer_link:
                designer = (await designer_link.inner_text()).strip()
                logger.info(f"Found designer via user_link: {designer}")
                return designer

        except Exception as e:
            logger.debug(f"Error with main container search: {e}")

        try:
            # Strategy 2: Look for "By [Name]" pattern in page text
            page_text = await page.inner_text("body")
            by_pattern = r"[Bb]y\s+([A-Z][a-zA-Z0-9_-]{2,})"
            matches = re.findall(by_pattern, page_text)
            if matches:
                designer = matches[0].strip()
                logger.info(f"Found designer via 'By [Name]' pattern: {designer}")
                return designer

        except Exception as e:
            logger.debug(f"Error with pattern matching: {e}")

        try:
            # Strategy 3: Look for profile links (fallback)
            profile_links = await page.query_selector_all('a[href*="/@"]')
            logger.debug(f"Found {len(profile_links)} user profile links")

            for i, link in enumerate(profile_links[:5]):
                href = await link.get_attribute("href")
                text = await link.inner_text()
                text = text.strip()

                # Skip empty, short names, or common UI text
                skip_texts = ["Profile", "View", "More", "Follow", "Designer", "User", ""]
                if text and len(text) > 2 and text not in skip_texts:
                    logger.debug(f"Designer candidate #{i+1}: '{text}' (href: {href})")
                    logger.debug(f"Selected as designer: {text}")
                    return text

        except Exception as e:
            logger.debug(f"Error finding designer by profile link: {e}")

        logger.debug("Designer not found, returning Unknown Designer")
        return "Unknown Designer"

    async def _select_printer_model(self, page: Page, printer_model: str) -> None:
        """
        Select printer model (e.g., P1S).

        Args:
            page: Playwright page
            printer_model: Printer model to select
        """
        try:
            # Look for the printer button with specific structure
            # <div class="mw-css-111wug5"><div class="mw-css-107wca0">P1S</div></div>

            # Try to find div containing the printer model text
            logger.debug(f"Looking for printer button with text: {printer_model}")

            # Try multiple strategies
            selectors = [
                f'div.mw-css-107wca0:has-text("{printer_model}")',
                f'div:has-text("{printer_model}")',
                f'button:has-text("{printer_model}")',
            ]

            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    logger.debug(f"Found {len(elements)} elements with selector: {selector}")

                    for element in elements:
                        text = await element.inner_text()
                        text = text.strip()
                        logger.debug(f"Element text: '{text}'")

                        # Check if this is exactly the printer model we want
                        if text == printer_model:
                            logger.debug(f"Found exact match for {printer_model}, clicking...")
                            await element.click()
                            await asyncio.sleep(2)  # Wait for update
                            logger.debug("Printer selected successfully")
                            return
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {str(e)}")
                    continue

            logger.debug(f"Could not find {printer_model} button, using default printer")

        except Exception as e:
            logger.debug(f"Error selecting printer: {str(e)}")
            # If selection fails, continue with default settings
            pass

    async def _extract_active_profile_data_with_hover(
        self, page: Page, soup: BeautifulSoup, main_designer: str = "Unknown Designer"
    ) -> dict:
        """
        Extract data from the active print profile by hovering over it to see details.

        Args:
            page: Playwright page
            soup: BeautifulSoup parsed HTML
            main_designer: Main designer name (fallback if profile designer not found)

        Returns:
            dict: Profile data including title, designer, duration, materials, amount
        """
        profile_data = {
            "profile_title": "Unknown Profile",
            "profile_designer": main_designer,
            "print_duration": "Unknown",
            "materials": [],
            "material_amount": "Unknown",
        }

        try:
            # Find the active profile (has class 'active' on mw-css-bxlu7r element)
            logger.debug("Looking for active profile...")

            active_profile = await page.query_selector("div.mw-css-bxlu7r.active")

            if not active_profile:
                logger.debug("No active profile found, using first profile")
                active_profile = await page.query_selector("div.mw-css-bxlu7r")

            if active_profile:
                logger.debug("Found active profile element, hovering to see details...")

                # Hover over the profile to trigger tooltip/popup
                await active_profile.hover()
                await asyncio.sleep(1.5)  # Wait for hover popup to appear

                # Save HTML during hover (for debugging)
                if not self.headless:
                    try:
                        hover_html = await page.content()
                        hover_file = "/tmp/makerworld_hover_debug.html"
                        with open(hover_file, "w", encoding="utf-8") as f:
                            f.write(hover_html)
                        logger.debug(f"✓ Saved hover HTML to: {hover_file}")

                        # Also take a screenshot during hover
                        hover_screenshot = "/tmp/makerworld_hover_debug.png"
                        await page.screenshot(path=hover_screenshot)
                        logger.debug(f"✓ Saved hover screenshot to: {hover_screenshot}")
                    except Exception as e:
                        logger.debug(f"Could not save hover debug files: {e}")

                # Extract profile title
                title_elem = await active_profile.query_selector("span.config_title")
                if title_elem:
                    profile_data["profile_title"] = (await title_elem.inner_text()).strip()
                    logger.debug(f"Profile title: {profile_data['profile_title']}")

                # Extract print duration (span.time) - has clock icon before it
                time_elem = await active_profile.query_selector("span.time")
                if time_elem:
                    profile_data["print_duration"] = (await time_elem.inner_text()).strip()
                    logger.debug(f"Print duration: {profile_data['print_duration']}")

                # Extract materials from profile title and full page content
                profile_data["materials"] = self._parse_materials_from_text(
                    profile_data["profile_title"]
                )

                # Also check the full profile element for material mentions
                profile_html = await active_profile.inner_html()
                additional_materials = self._parse_materials_from_text(profile_html)
                for mat in additional_materials:
                    if mat not in profile_data["materials"]:
                        profile_data["materials"].append(mat)

                logger.debug(f"Parsed materials: {profile_data['materials']}")

                # Extract profile designer
                try:
                    profile_link = await active_profile.query_selector('a[href*="/profile/"]')
                    if profile_link:
                        designer_text = (await profile_link.inner_text()).strip()
                        if (
                            designer_text
                            and len(designer_text) > 2
                            and designer_text not in ["Designer", "Profile"]
                        ):
                            logger.debug(f"Found specific profile designer: '{designer_text}'")
                            profile_data["profile_designer"] = designer_text
                        else:
                            logger.debug(f"Profile uses main designer: {main_designer}")
                    else:
                        logger.debug(
                            f"No specific profile designer found, using main designer: {main_designer}"
                        )
                except Exception as e:
                    logger.debug(f"Error extracting profile designer: {e}")

            # Extract total material amount
            profile_data["material_amount"] = await self._extract_total_material_amount(page, soup)

        except Exception as e:
            logger.debug(f"Error extracting active profile data: {str(e)}")
            import traceback

            traceback.print_exc()

        return profile_data

    async def _extract_active_profile_data(
        self, page: Page, soup: BeautifulSoup, main_designer: str = "Unknown Designer"
    ) -> dict:
        """
        Extract data from the active print profile.

        Args:
            page: Playwright page
            soup: BeautifulSoup parsed HTML
            main_designer: Main designer name (fallback if profile designer not found)

        Returns:
            dict: Profile data including title, designer, duration, materials, amount
        """
        profile_data = {
            "profile_title": "Unknown Profile",
            "profile_designer": main_designer,  # Default to main designer
            "print_duration": "Unknown",
            "materials": [],
            "material_amount": "Unknown",
        }

        try:
            # Find the active profile (has class 'active' on mw-css-bxlu7r element)
            logger.debug("Looking for active profile...")

            # Try to find active profile element
            active_profile = await page.query_selector("div.mw-css-bxlu7r.active")

            if not active_profile:
                logger.debug("No active profile found, using first profile")
                # Fallback: use first profile
                active_profile = await page.query_selector("div.mw-css-bxlu7r")

            if active_profile:
                logger.debug("Found active profile element")

                # Extract profile title
                title_elem = await active_profile.query_selector("span.config_title")
                if title_elem:
                    profile_data["profile_title"] = (await title_elem.inner_text()).strip()
                    logger.debug(f"Profile title: {profile_data['profile_title']}")

                # Extract print duration (span.time)
                time_elem = await active_profile.query_selector("span.time")
                if time_elem:
                    profile_data["print_duration"] = (await time_elem.inner_text()).strip()
                    logger.debug(f"Print duration: {profile_data['print_duration']}")

                # Extract materials from profile title
                profile_data["materials"] = self._parse_materials_from_text(
                    profile_data["profile_title"]
                )
                logger.debug(f"Parsed materials from profile title: {profile_data['materials']}")

                # Extract profile designer from the profile list item
                # The designer div usually just says "Designer", so we keep the main designer
                # Unless we can find a specific designer link within the profile
                try:
                    # Try to find a profile link within the active profile element
                    profile_link = await active_profile.query_selector('a[href*="/profile/"]')
                    if profile_link:
                        designer_text = (await profile_link.inner_text()).strip()
                        if designer_text and len(designer_text) > 2:
                            logger.debug(f"Found specific profile designer: '{designer_text}'")
                            profile_data["profile_designer"] = designer_text
                        else:
                            logger.debug(f"Profile uses main designer: {main_designer}")
                    else:
                        logger.debug(
                            f"No specific profile designer found, using main designer: {main_designer}"
                        )
                except Exception as e:
                    logger.debug(f"Error extracting profile designer: {e}")
                    logger.debug(f"Using main designer as fallback: {main_designer}")

            # Extract total material amount - look for weight information
            profile_data["material_amount"] = await self._extract_total_material_amount(page, soup)

        except Exception as e:
            logger.debug(f"Error extracting active profile data: {str(e)}")
            import traceback

            traceback.print_exc()

        return profile_data

    def _parse_materials_from_text(self, text: str) -> list:
        """
        Parse material types from text (e.g., profile title or description).

        Args:
            text: Text to parse

        Returns:
            list: List of material types found
        """
        materials = []
        common_materials = ["PLA", "PETG", "ABS", "TPU", "ASA", "NYLON", "PC", "PVA", "PVB"]

        text_upper = text.upper()

        # Find all materials mentioned in the text
        for material in common_materials:
            if material in text_upper:
                materials.append(material)

        # Remove duplicates while preserving order
        seen = set()
        materials = [m for m in materials if not (m in seen or seen.add(m))]

        logger.debug(f"Materials found in '{text}': {materials}")
        return materials if materials else ["PLA"]  # Default to PLA

    async def _extract_print_duration(self, page: Page, soup: BeautifulSoup) -> str:
        """
        Extract print duration.

        Args:
            page: Playwright page
            soup: BeautifulSoup parsed HTML

        Returns:
            str: Print duration
        """
        # Get all text from page
        content = await page.content()

        # Try to find duration patterns like "1h 30m", "2h30m", "45m", "1.5h"
        duration_patterns = [
            r"(\d+h\s*\d+m)",  # Matches "1h 30m" or "1h30m"
            r"(\d+\s*hours?\s*\d+\s*min)",  # Matches "1 hour 30 min"
            r"(\d+h)",  # Matches "2h"
            r"(\d+\s*min)",  # Matches "45 min" or "45min"
            r"(\d+\.?\d*\s*hours?)",  # Matches "1.5 hours"
        ]

        for pattern in duration_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                result = matches[0].strip()
                logger.debug(f"Found print duration: {result}")
                return result

        logger.debug("Print duration not found, returning 'Unknown'")
        return "Unknown"

    async def _extract_material(self, page: Page, soup: BeautifulSoup) -> str:
        """
        Extract material type.

        Args:
            page: Playwright page
            soup: BeautifulSoup parsed HTML

        Returns:
            str: Material type
        """
        # Common materials
        materials = ["PLA", "PETG", "ABS", "TPU", "ASA"]

        content = await page.content()
        for material in materials:
            if material in content:
                return material

        return "PLA"  # Default

    async def _extract_total_material_amount(self, page: Page, soup: BeautifulSoup) -> str:
        """
        Extract total material amount across all parts.

        Args:
            page: Playwright page
            soup: BeautifulSoup parsed HTML

        Returns:
            str: Total material amount
        """
        logger.debug("Extracting total material amount...")

        try:
            # Get page content
            content = await page.content()

            # Strategy 1: Look for explicit total/gesamt weight
            total_patterns = [
                r"(?:total|gesamt|sum)[:\s]*(\d+\.?\d*)\s*g",
                r"(\d+\.?\d*)\s*g\s*(?:total|gesamt)",
            ]

            for pattern in total_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    try:
                        value = float(matches[0])
                        if 1 <= value <= 10000:
                            result = f"{int(value)}g" if value == int(value) else f"{value}g"
                            logger.debug(f"Found total weight: {result}")
                            return result
                    except ValueError:
                        continue

            # Strategy 2: Find all weights and use the largest (likely the total)
            weight_patterns = [
                r"(\d+\.?\d*)\s*g(?!\w)",
                r"(\d+\.?\d*)\s*grams?",
            ]

            all_weights = []
            for pattern in weight_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        value = float(match)
                        if 1 <= value <= 10000:
                            all_weights.append(value)
                    except ValueError:
                        continue

            if all_weights:
                # Take the largest weight (likely the total)
                max_weight = max(all_weights)
                result = (
                    f"{int(max_weight)}g" if max_weight == int(max_weight) else f"{max_weight}g"
                )
                logger.debug(
                    f"Found largest weight (likely total): {result} from {len(all_weights)} weights"
                )
                logger.debug(
                    f"All weights found: {sorted(all_weights, reverse=True)[:10]}"
                )  # Show top 10
                return result

        except Exception as e:
            logger.debug(f"Error extracting material amount: {e}")

        logger.debug("Material amount not found, returning 'Unknown'")
        return "Unknown"

    async def _extract_material_amount(self, page: Page, soup: BeautifulSoup) -> str:
        """
        Extract material amount (deprecated, use _extract_total_material_amount).

        Args:
            page: Playwright page
            soup: BeautifulSoup parsed HTML

        Returns:
            str: Material amount
        """
        return await self._extract_total_material_amount(page, soup)
