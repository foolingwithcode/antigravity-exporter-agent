"""
Playwright-based Browser Agent for autonomous navigation, stealth discovery,
and multi-level sub-clicking into seller portals, contact pages, and B2B directories.
"""

import asyncio
import logging
import random
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

import config
from extractor import parse_page_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BrowserAgent")


class ExporterBrowserAgent:
    """Autonomous Playwright agent with stealth and multi-level sub-clicking capabilities."""

    def __init__(self, headless: bool = config.DEFAULT_HEADLESS):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def start(self):
        """Initialize browser with stealth parameters to prevent bot detection."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
                "--ignore-certifcate-errors",
                "--ignore-certifcate-errors-spki-list",
            ],
        )
        self.context = await self.browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT},
            locale="en-US,en;q=0.9",
            timezone_id="Asia/Kolkata",
        )

        # Remove navigator.webdriver detection
        await self.context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        )
        logger.info("Browser agent launched in stealth mode.")

    async def close(self):
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser agent stopped.")

    async def random_delay(self, min_s: float = config.MIN_ACTION_DELAY, max_s: float = config.MAX_ACTION_DELAY):
        """Human-like jitter delay between operations."""
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def smooth_scroll(self, page: Page, max_scrolls: int = 3):
        """Simulate human reading scroll to trigger lazy loading elements."""
        for _ in range(max_scrolls):
            scroll_by = random.randint(350, 750)
            await page.evaluate(f"window.scrollBy({{top: {scroll_by}, behavior: 'smooth'}})")
            await asyncio.sleep(random.uniform(0.6, 1.4))

    async def dismiss_popups(self, page: Page):
        """Attempt to close newsletter overlays, modal popups, or cookie banners."""
        close_selectors = [
            "button[aria-label='Close']",
            "button.close",
            ".modal-close",
            "#close-button",
            "span.close",
            "[data-dismiss='modal']",
            "button:has-text('Accept All')",
            "button:has-text('I agree')",
            "button:has-text('Got it')",
            "button:has-text('Skip')",
        ]
        for sel in close_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=500):
                    await btn.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

    async def reveal_hidden_numbers(self, page: Page):
        """Click 'View Number' or 'Show Contact' buttons to unmask phone details."""
        for selector in config.REVEAL_NUMBER_SELECTORS:
            try:
                elements = await page.locator(selector).all()
                for el in elements[:3]:  # Click up to 3 buttons per page to avoid spamming
                    if await el.is_visible():
                        await el.click(timeout=config.CLICK_TIMEOUT_MS)
                        await asyncio.sleep(random.uniform(1.0, 1.8))
            except Exception:
                continue

    async def find_contact_sublinks(self, page: Page, current_url: str) -> List[str]:
        """Discover sub-navigation links for Contact, About, and Company details."""
        sublinks = set()
        base_domain = urlparse(current_url).netloc

        try:
            links = await page.locator("a[href]").all()
            for link in links:
                try:
                    text = (await link.inner_text()).strip().lower()
                    href = await link.get_attribute("href")
                    if not href:
                        continue

                    full_url = urljoin(current_url, href)
                    target_domain = urlparse(full_url).netloc

                    # Only follow links on same domain
                    if target_domain and target_domain != base_domain:
                        continue

                    # Match keyword text, URL slug, or seller profile pattern
                    is_contact_pattern = any(target in text for target in config.CONTACT_LINK_TEXTS) or any(
                        target in href.lower() for target in ["contact", "about-us", "about", "reach-us", "profile", "at-a-glance"]
                    )
                    is_seller_profile = bool(re.search(r"tradeindia\.com/[a-z0-9\-]+-\d+/?", full_url))

                    if is_contact_pattern or is_seller_profile:
                        # Filter out mailto/tel links from page navigation
                        if not full_url.startswith("mailto:") and not full_url.startswith("tel:"):
                            sublinks.add(full_url)
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Error finding sublinks: {e}")

        return list(sublinks)[:3]  # Return top 3 most relevant sublinks

    async def deep_crawl_entity(self, page: Page, initial_url: str) -> Dict[str, any]:
        """
        Deep multi-level crawler:
        1. Opens the entity's main page.
        2. Clicks 'View Number' / reveals.
        3. Parses primary contact data.
        4. Navigates to 'Contact Us' / 'About Us' sub-pages.
        5. Aggregates and returns complete lead profile.
        """
        aggregated_data = {
            "phones": [],
            "emails": [],
            "gstins": [],
            "iecs": [],
            "address": "",
            "socials": [],
            "title": "",
            "website": initial_url,
        }

        try:
            logger.info(f"Navigating to entity profile: {initial_url}")
            await page.goto(initial_url, wait_until="domcontentloaded", timeout=config.PAGE_TIMEOUT_MS)
            await self.random_delay(1.5, 2.5)
            await self.dismiss_popups(page)
            await self.smooth_scroll(page, max_scrolls=2)
            await self.reveal_hidden_numbers(page)

            # Step 1: Extract from landing page
            html = await page.content()
            data = parse_page_data(html, initial_url)
            self._merge_lead_data(aggregated_data, data)

            # Step 2: Multi-level sub-clicking
            if config.ENABLE_MULTI_LEVEL_CLICKING:
                sublinks = await self.find_contact_sublinks(page, initial_url)
                for sublink in sublinks:
                    if sublink == initial_url:
                        continue
                    try:
                        logger.info(f"Sub-clicking into contact page: {sublink}")
                        await page.goto(sublink, wait_until="domcontentloaded", timeout=config.PAGE_TIMEOUT_MS)
                        await self.random_delay(1.0, 2.0)
                        await self.dismiss_popups(page)
                        await self.reveal_hidden_numbers(page)

                        sub_html = await page.content()
                        sub_data = parse_page_data(sub_html, sublink)
                        self._merge_lead_data(aggregated_data, sub_data)
                    except Exception as e:
                        logger.debug(f"Failed sub-page crawl {sublink}: {e}")

        except Exception as e:
            logger.warning(f"Error deep-crawling {initial_url}: {e}")

        return aggregated_data

    def _merge_lead_data(self, target: Dict[str, any], source: Dict[str, any]):
        """Merge newly discovered data into the existing lead profile."""
        target["phones"] = list(dict.fromkeys(target["phones"] + source.get("phones", [])))
        target["emails"] = list(dict.fromkeys(target["emails"] + source.get("emails", [])))
        target["gstins"] = list(dict.fromkeys(target["gstins"] + source.get("gstins", [])))
        target["iecs"] = list(dict.fromkeys(target["iecs"] + source.get("iecs", [])))
        target["socials"] = list(dict.fromkeys(target["socials"] + source.get("socials", [])))
        if not target["address"] and source.get("address"):
            target["address"] = source["address"]
        if not target["title"] and source.get("title"):
            target["title"] = source["title"]

    async def search_and_discover(self, platform_key: str, query: str) -> List[Dict[str, any]]:
        """Run platform-specific discovery and deep lead extraction."""
        platform = config.PLATFORMS.get(platform_key)
        if not platform or not platform.get("enabled"):
            logger.warning(f"Platform {platform_key} is disabled or unknown.")
            return []

        search_url = platform["search_url_template"].format(query=query.replace(" ", "+"))
        logger.info(f"Searching on {platform['name']} for query '{query}': {search_url}")

        page = await self.context.new_page()
        discovered_leads: List[Dict[str, any]] = []

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=config.PAGE_TIMEOUT_MS)
            await self.random_delay(2.0, 3.5)
            await self.dismiss_popups(page)
            await self.smooth_scroll(page, max_scrolls=3)

            # Discover candidate entity links depending on platform
            candidate_links = await self._extract_platform_listing_links(page, platform_key)
            logger.info(f"Found {len(candidate_links)} candidates on {platform['name']}.")

            for item in candidate_links[:config.MAX_LEADS_PER_KEYWORD]:
                entity_url = item.get("url")
                company_name = item.get("name", "")

                if not entity_url:
                    continue

                lead_data = await self.deep_crawl_entity(page, entity_url)
                title = lead_data.get("title", "")
                resolved_name = company_name
                if (not resolved_name or resolved_name in ["TradeIndia Exporter", "IndiaMART Supplier", "Unknown Company"]) and title:
                    if "|" in title:
                        resolved_name = title.split("|")[-1].strip()
                    elif " - " in title:
                        resolved_name = title.split(" - ")[0].strip()
                    else:
                        resolved_name = title

                lead_data["company_name"] = resolved_name or "Unknown Company"
                lead_data["platform"] = platform["name"]
                lead_data["query"] = query
                lead_data["source_url"] = entity_url

                # Keep leads with either phone, email, gstin, address, or verified company name
                if lead_data["phones"] or lead_data["emails"] or lead_data["gstins"] or lead_data["address"]:
                    discovered_leads.append(lead_data)
                    logger.info(
                        f"Extracted lead: {lead_data['company_name']} | "
                        f"Phones: {len(lead_data['phones'])} | Emails: {len(lead_data['emails'])}"
                    )

        except Exception as e:
            logger.error(f"Error during search on {platform_key}: {e}")
        finally:
            await page.close()

        return discovered_leads

    async def _extract_platform_listing_links(self, page: Page, platform_key: str) -> List[Dict[str, str]]:
        """Extract candidate exporter listing links and names from search results."""
        results = []

        try:
            if platform_key == "tradeindia":
                # Primary: TradeIndia product and catalog cards
                links = await page.locator("a[href*='/products/'], a[href*='-c'], a.listing-title, .co-name a").all()
                seen = set()
                for link in links:
                    try:
                        href = await link.get_attribute("href")
                        if not href or href in seen:
                            continue
                        name = (await link.inner_text()).strip()
                        if "/products/" in href or "-c" in href:
                            seen.add(href)
                            full_url = urljoin("https://www.tradeindia.com", href)
                            clean_name = name.split("-")[0].strip() if name else "TradeIndia Exporter"
                            results.append({"name": clean_name, "url": full_url})
                            if len(results) >= config.MAX_LEADS_PER_KEYWORD:
                                break
                    except Exception:
                        continue

                # Fallback: if search page had 0, try category page
                if not results:
                    current_url = page.url
                    query_term = current_url.split("keyword=")[-1].split("&")[0].split("+")[0]
                    cat_url = f"https://www.tradeindia.com/manufacturers/{query_term}.html"
                    try:
                        await page.goto(cat_url, wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(2)
                        cat_links = await page.locator("a[href*='/products/']").all()
                        for link in cat_links:
                            href = await link.get_attribute("href")
                            if href and href not in seen:
                                seen.add(href)
                                full_url = urljoin("https://www.tradeindia.com", href)
                                name = (await link.inner_text()).strip()
                                results.append({"name": name or "TradeIndia Exporter", "url": full_url})
                                if len(results) >= config.MAX_LEADS_PER_KEYWORD:
                                    break
                    except Exception:
                        pass

            elif platform_key == "indiamart":
                # IndiaMART supplier cards and product links
                selectors = [
                    "a.clsp", ".bo-name a", ".prod-name a",
                    "a[href*='indiamart.com/proddtl/']", "a[href*='indiamart.com/company/']",
                    ".gpcls a", ".card a", "a.to-fnt", "a.bold"
                ]
                seen = set()
                for sel in selectors:
                    cards = await page.locator(sel).all()
                    for card in cards:
                        try:
                            href = await card.get_attribute("href")
                            if not href or href in seen:
                                continue
                            if any(skip in href for skip in ["help.", "seller.", "corporate.", "blog.", "terms"]):
                                continue
                            seen.add(href)
                            name = (await card.inner_text()).strip() or "IndiaMART Supplier"
                            results.append({"name": name, "url": href})
                            if len(results) >= config.MAX_LEADS_PER_KEYWORD:
                                break
                        except Exception:
                            continue
                    if len(results) >= config.MAX_LEADS_PER_KEYWORD:
                        break

            elif platform_key == "shopify":
                # Bing search results for Shopify Indian exporter stores
                search_results = await page.locator("li.b_algo h2 a, a[href^='http']").all()
                seen = set()
                for link in search_results:
                    try:
                        href = await link.get_attribute("href")
                        if not href:
                            continue
                        parsed = urlparse(href)
                        domain = parsed.netloc.lower()
                        if any(skip in domain for skip in ["bing.", "microsoft.", "google.", "wikipedia.", "gov.in", "ndtv."]):
                            continue
                        if domain not in seen:
                            seen.add(domain)
                            store_url = f"{parsed.scheme}://{domain}"
                            name = domain.split(".")[0].replace("-", " ").title()
                            results.append({"name": name, "url": store_url})
                            if len(results) >= config.MAX_LEADS_PER_KEYWORD:
                                break
                    except Exception:
                        continue

            elif platform_key == "amazon":
                # Amazon India search results
                prod_links = await page.locator("a.a-link-normal.s-no-outline, .s-result-item h2 a").all()
                seen = set()
                for link in prod_links:
                    try:
                        href = await link.get_attribute("href")
                        if not href or href in seen:
                            continue
                        if "/dp/" in href:
                            seen.add(href)
                            full_url = urljoin("https://www.amazon.in", href)
                            name = (await link.inner_text()).strip() or "Amazon Exporter"
                            results.append({"name": name, "url": full_url})
                            if len(results) >= config.MAX_LEADS_PER_KEYWORD:
                                break
                    except Exception:
                        continue

            elif platform_key == "etsy":
                # Etsy shops & listing cards
                shop_links = await page.locator("a[href*='/shop/'], a.listing-link, a[href*='/listing/']").all()
                seen = set()
                for link in shop_links:
                    try:
                        href = await link.get_attribute("href")
                        if not href or href in seen:
                            continue
                        seen.add(href)
                        clean_url = href.split("?")[0]
                        name = (await link.inner_text()).strip() or "Etsy Artisan"
                        results.append({"name": name, "url": clean_url})
                        if len(results) >= config.MAX_LEADS_PER_KEYWORD:
                            break
                    except Exception:
                        continue

            elif platform_key == "ebay":
                # eBay items and sellers
                items = await page.locator(".s-item__link, a[href*='/itm/'], a[href*='/str/']").all()
                seen = set()
                for item in items:
                    try:
                        href = await item.get_attribute("href")
                        if not href or href in seen:
                            continue
                        seen.add(href)
                        clean_url = href.split("?")[0]
                        name = (await item.inner_text()).strip() or "eBay Seller"
                        results.append({"name": name, "url": clean_url})
                        if len(results) >= config.MAX_LEADS_PER_KEYWORD:
                            break
                    except Exception:
                        continue

        except Exception as e:
            logger.warning(f"Error parsing listing links for {platform_key}: {e}")

        return results
