"""
Configuration settings for Antigravity Indian Exporter & E-commerce Lead Discovery Agent.
Zero-cost, fully autonomous browser agent configuration.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_CSV = BASE_DIR / "leads.csv"

# Target Export Categories & Discovery Keywords
DEFAULT_KEYWORDS = [
    "handicrafts exporter",
    "leather goods manufacturer export",
    "organic cotton garments tirupur exporter",
    "brassware manufacturer moradabad",
    "gems and jewelry exporter jaipur",
    "spices exporter kochi",
    "ayurvedic products manufacturer export",
    "home textiles manufacturer export karur",
    "hand-knotted carpets bhadohi exporter",
    "ceramic tiles exporter morbi"
]

# Supported Platforms & Search Endpoints
PLATFORMS = {
    "indiamart": {
        "name": "IndiaMART",
        "base_url": "https://dir.indiamart.com/search.mp",
        "search_url_template": "https://dir.indiamart.com/search.mp?ss={query}",
        "enabled": True,
    },
    "tradeindia": {
        "name": "TradeIndia",
        "base_url": "https://www.tradeindia.com/search.html",
        "search_url_template": "https://www.tradeindia.com/search.html?keyword={query}",
        "enabled": True,
    },
    "etsy": {
        "name": "Etsy India Exporters",
        "base_url": "https://www.etsy.com",
        "search_url_template": "https://www.etsy.com/search?q={query}&locationQuery=India",
        "enabled": True,
    },
    "ebay": {
        "name": "eBay Indian Sellers",
        "base_url": "https://www.ebay.com",
        "search_url_template": "https://www.ebay.com/sch/i.html?_nkw={query}+india&_sop=12",
        "enabled": True,
    },
    "amazon": {
        "name": "Amazon Global Selling India",
        "base_url": "https://www.amazon.in",
        "search_url_template": "https://www.amazon.in/s?k={query}+export",
        "enabled": True,
    },
    "shopify": {
        "name": "Shopify D2C Indian Exporters",
        "base_url": "https://www.google.com",
        "search_url_template": "https://www.google.com/search?q=site%3Amyshopify.com+India+worldwide+shipping+{query}",
        "enabled": True,
    }
}

# CSV Schema
CSV_HEADERS = [
    "Company Name",
    "Platform",
    "Search Query",
    "Contact Person",
    "Phone Numbers",
    "Emails",
    "Website",
    "Address",
    "GSTIN",
    "IEC",
    "Social Links",
    "Source URL",
    "Extracted At"
]

# Human-like Navigation & Delays (Seconds)
MIN_ACTION_DELAY = 1.8
MAX_ACTION_DELAY = 4.2
PAGE_TIMEOUT_MS = 35000

# Sub-clicking & Deep Navigation Configuration
MAX_PAGES_PER_KEYWORD = 3
MAX_LEADS_PER_KEYWORD = 15
ENABLE_MULTI_LEVEL_CLICKING = True
CLICK_TIMEOUT_MS = 4000

# Selectors & Target Sub-links for Contact Details
CONTACT_LINK_TEXTS = [
    "contact us",
    "contact",
    "about us",
    "about",
    "company profile",
    "reach us",
    "get in touch",
    "seller profile",
    "business details"
]

REVEAL_NUMBER_SELECTORS = [
    "button:has-text('View Number')",
    "a:has-text('View Number')",
    "button:has-text('Show Number')",
    "span:has-text('Show Number')",
    "button:has-text('Contact Supplier')",
    "a:has-text('Contact Seller')",
    "button:has-text('View Mobile Number')",
    "[data-click='view_number']",
    ".view_number_btn"
]

# Browser Settings
DEFAULT_HEADLESS = True
VIEWPORT_WIDTH = 1366
VIEWPORT_HEIGHT = 768
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
