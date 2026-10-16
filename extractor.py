"""
Extractor module for parsing contact information, B2B identifiers, and corporate data
from raw web pages, DOM trees, and microdata.
Zero-cost, regex and BeautifulSoup based parsing.
"""

import json
import re
from typing import Dict, List, Set
from urllib.parse import unquote, urlparse
from bs4 import BeautifulSoup

# Regex patterns
RE_INDIAN_MOBILE = re.compile(
    r"(?:\+91[\s\-]?)?(?:0)?[6-9]\d{4}[\s\-]?\d{5}\b"
)
RE_INDIAN_LANDLINE = re.compile(
    r"\b0\d{2,4}[\s\-]?\d{6,8}\b"
)
RE_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
RE_OBFUSCATED_EMAIL = re.compile(
    r"\b([A-Za-z0-9._%+\-]+)\s*(?:\[at\]|\(at\)|@)\s*([A-Za-z0-9.\-]+)\s*(?:\[dot\]|\(dot\)|\.)\s*([A-Za-z]{2,})\b",
    re.IGNORECASE
)
RE_GSTIN = re.compile(
    r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b"
)
RE_IEC = re.compile(
    r"(?:IEC|Import\s*Export\s*Code)[\s:.\-#]*([A-Z0-9]{10})\b",
    re.IGNORECASE
)
RE_PINCODE = re.compile(
    r"\b[1-9][0-9]{2}\s?[0-9]{3}\b"
)

IGNORED_EMAIL_DOMAINS = {
    "sentry.io",
    "wixpress.com",
    "shopify.com",
    "schema.org",
    "example.com",
    "domain.com",
    "yourdomain.com",
    "test.com",
    "cloudflare.com",
    "akamai.com",
    "tradeindia.com",
    "indiamart.com",
    "ebay.com",
    "etsy.com",
    "amazon.in",
    "amazon.com",
}

IGNORED_EMAIL_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js"
)

INDIAN_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu",
    "telangana", "tripura", "uttar pradesh", "uttarakhand", "west bengal",
    "delhi", "chandigarh", "puducherry", "moradabad", "tirupur", "jaipur",
    "kochi", "surat", "morbi", "ludhiana", "bhadohi", "panipat", "karur"
}


def clean_phone(phone_str: str) -> str:
    """Normalize extracted phone number to consistent +91 format if applicable."""
    digits = re.sub(r"\D", "", phone_str)
    if digits.startswith("91") and len(digits) == 12:
        return f"+91-{digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10 and digits[0] in "6789":
        return f"+91-{digits[:5]}-{digits[5:]}"
    elif digits.startswith("0") and len(digits) >= 10:
        return f"+91-{digits[1:6]}-{digits[6:]}"
    return phone_str.strip()


def extract_phone_numbers(text: str, soup: BeautifulSoup) -> List[str]:
    """Extract telephone and WhatsApp numbers from raw text, tel links, and WhatsApp links."""
    phones: Set[str] = set()

    # 1. From tel: links
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if href.startswith("tel:"):
            clean = clean_phone(href[4:])
            if clean:
                phones.add(clean)
        elif "wa.me/" in href or "api.whatsapp.com/send" in href:
            match = re.search(r"(?:phone=|\/)(?:91)?([6-9]\d{9})", href)
            if match:
                phones.add(f"+91-{match.group(1)[:5]}-{match.group(1)[5:]}")

    # 2. Text matches
    for match in RE_INDIAN_MOBILE.findall(text):
        cleaned = clean_phone(match)
        # Avoid zip codes or invalid sequences
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) in (10, 12):
            phones.add(cleaned)

    for match in RE_INDIAN_LANDLINE.findall(text):
        digits = re.sub(r"\D", "", match)
        if len(digits) >= 9:
            phones.add(match.strip())

    return sorted(list(phones))


def extract_emails(text: str, soup: BeautifulSoup) -> List[str]:
    """Extract clean email addresses from mailto: anchors, text, and obfuscated patterns."""
    emails: Set[str] = set()

    # 1. From mailto:
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if href.lower().startswith("mailto:"):
            target = href.split("?")[0].replace("mailto:", "").strip()
            if target and "@" in target:
                emails.add(target.lower())

    # 2. Obfuscated emails (e.g., info [at] domain.com)
    for part in RE_OBFUSCATED_EMAIL.findall(text):
        constructed = f"{part[0]}@{part[1]}.{part[2]}".lower()
        emails.add(constructed)

    # 3. Standard regex
    for email in RE_EMAIL.findall(text):
        email_clean = email.strip().lower().rstrip(".")
        emails.add(email_clean)

    # Filtering false positives & assets
    valid_emails = set()
    for email in emails:
        if any(email.endswith(ext) for ext in IGNORED_EMAIL_EXTENSIONS):
            continue
        domain = email.split("@")[-1]
        if domain in IGNORED_EMAIL_DOMAINS:
            continue
        if len(email) > 60 or len(email) < 6:
            continue
        valid_emails.add(email)

    return sorted(list(valid_emails))


def extract_gstins(text: str) -> List[str]:
    """Extract 15-character Indian GSTINs with state code validation (01-38)."""
    gstins: Set[str] = set()
    for candidate in RE_GSTIN.findall(text):
        state_code = int(candidate[:2])
        if 1 <= state_code <= 38:
            gstins.add(candidate)
    return sorted(list(gstins))


def extract_iecs(text: str) -> List[str]:
    """Extract 10-character Importer Exporter Codes (IEC)."""
    iecs: Set[str] = set()
    for match in RE_IEC.findall(text):
        val = match.strip().upper()
        if len(val) == 10 and not val.isdigit() == False and val.isalnum():
            iecs.add(val)
        elif len(val) == 10 and val.isalnum():
            iecs.add(val)
    return sorted(list(iecs))


def extract_social_links(soup: BeautifulSoup) -> List[str]:
    """Extract company social media profile links."""
    social_domains = ["linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com", "youtube.com"]
    socials: Set[str] = set()
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        for domain in social_domains:
            if domain in href and not any(share in href for share in ["sharer", "share?", "intent/tweet"]):
                socials.add(href)
    return sorted(list(socials))


def extract_address(text: str, soup: BeautifulSoup) -> str:
    """Detect and extract physical address snippets containing PIN codes or Indian locations."""
    # Check schema.org postalAddress
    postal_addr = soup.find(attrs={"itemtype": re.compile(r"PostalAddress", re.I)})
    if postal_addr:
        return re.sub(r"\s+", " ", postal_addr.get_text()).strip()

    # Search lines or blocks containing PIN code and Indian state
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for i, line in enumerate(lines):
        if RE_PINCODE.search(line):
            context = " ".join(lines[max(0, i - 1): min(len(lines), i + 2)])
            context_lower = context.lower()
            if any(state in context_lower for state in INDIAN_STATES) or "india" in context_lower:
                clean_addr = re.sub(r"\s+", " ", context).strip()
                if 15 <= len(clean_addr) <= 250:
                    return clean_addr

    return ""


def extract_json_ld(soup: BeautifulSoup) -> Dict[str, any]:
    """Extract metadata from application/ld+json blocks if present."""
    data = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            content = json.loads(script.string or "{}")
            if isinstance(content, list):
                content = content[0] if content else {}
            if isinstance(content, dict):
                data.update(content)
        except Exception:
            continue
    return data


def parse_page_data(html_content: str, source_url: str = "") -> Dict[str, any]:
    """Master extraction function: parses HTML and returns unified lead dictionary."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style tags from text representation
    for element in soup(["script", "style", "noscript", "svg", "header", "footer"]):
        element.extract()

    text = soup.get_text(separator="\n")

    # JSON-LD enrichment
    ld = extract_json_ld(soup)

    phones = extract_phone_numbers(text, soup)
    emails = extract_emails(text, soup)
    gstins = extract_gstins(text)
    iecs = extract_iecs(text)
    address = extract_address(text, soup)
    socials = extract_social_links(soup)

    # Enrich from JSON-LD
    if "telephone" in ld and ld["telephone"]:
        phones.append(clean_phone(str(ld["telephone"])))
    if "email" in ld and ld["email"]:
        emails.append(str(ld["email"]).lower())

    return {
        "phones": list(dict.fromkeys(phones)),
        "emails": list(dict.fromkeys(emails)),
        "gstins": gstins,
        "iecs": iecs,
        "address": address,
        "socials": socials,
        "title": soup.title.get_text().strip() if soup.title else "",
    }
