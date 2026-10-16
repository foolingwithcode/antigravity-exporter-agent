# =====================================================================
# ANTIGRAVITY EXPORTER & E-COMMERCE LEAD DISCOVERY AGENT (SINGLE FILE)
# =====================================================================
# Description: Autonomous local browser agent to discover Indian B2B 
# exporters & e-commerce sellers, perform multi-level sub-clicking 
# (revealing phone numbers, deep diving independent websites), and 
# export verified leads into a local CSV file.
# Cost: $100% Free (Runs locally using Python, Playwright, BeautifulSoup)
# =====================================================================

import asyncio
import csv
import random
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ---------------------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------------------
SEARCH_KEYWORDS = [
    "handicrafts exporter India",
    "cotton bedsheets manufacturer India",
    "brass hardware supplier India",
    "leather goods exporter India"
]

# Set HEADLESS_MODE = False so you can watch the browser in action 
# and manually solve any unexpected CAPTCHAs on your local IP if needed.
HEADLESS_MODE = False
TIMEOUT_MS = 30000     # 30 seconds page load timeout
MIN_DELAY = 4.0        # Min random human-like delay (seconds)
MAX_DELAY = 9.0        # Max random human-like delay (seconds)


# ---------------------------------------------------------------------
# 2. DATA EXTRACTOR (REGEX & PARSING ENGINE)
# ---------------------------------------------------------------------
def extract_lead_details(html_content, current_url):
    """
    Parses HTML content from a supplier profile or independent website 
    to extract phone numbers, email addresses, GSTINs, and company names.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text_content = soup.get_text(separator=' ')

    # 1. Extract Indian Phone Numbers (+91 or standard 10-digit mobile patterns)
    phone_pattern = r'(?:\+91[\-\s]?)?[6-9]\d{9}'
    phones = re.findall(phone_pattern, text_content)
    unique_phones = list(set(phones))
    primary_phone = unique_phones[0] if unique_phones else "Not Found"

    # 2. Extract Email Addresses (filtering out asset extensions)
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    emails = re.findall(email_pattern, text_content)
    valid_emails = [e for e in set(emails) if not any(e.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.css', '.js'])]
    primary_email = valid_emails[0] if valid_emails else "Not Found"

    # 3. Extract GSTIN (Indian Tax ID format)
    gstin_pattern = r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}'
    gstins = re.findall(gstin_pattern, text_content)
    gstin = gstins[0] if gstins else "Not Found"

    # 4. Extract Company Name from Page Title
    company_name = "Unknown Supplier"
    if soup.title and soup.title.string:
        company_name = soup.title.string.split('|')[0].strip()

    return {
        "company_name": company_name,
        "phone": primary_phone,
        "email": primary_email,
        "gstin": gstin,
        "source_url": current_url
    }


# ---------------------------------------------------------------------
# 3. BROWSER AGENT & MULTI-LEVEL SUB-CLICK ENGINE
# ---------------------------------------------------------------------
async def human_delay():
    """Adds random human-like delay to prevent bot blocks on local IP."""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    await asyncio.sleep(delay)

async def run_browser_agent(search_url):
    """
    Launches a local browser instance, navigates search results, 
    performs multi-level sub-clicks, and extracts deep contact details.
    """
    leads = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS_MODE)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"[*] Navigating to: {search_url}")
            await page.goto(search_url, timeout=TIMEOUT_MS)
            await human_delay()

            # Scroll down to load search result cards
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            await human_delay()

            # Find supplier/vendor profile links
            link_elements = await page.locator("a.clsp, .bo-name a, .prod-name a").all()
            print(f"[+] Found {len(link_elements)} potential suppliers on this search page.")

            # Limit to top 5 per run for safe local testing
            for i in range(min(5, len(link_elements))):
                try:
                    current_links = await page.locator("a.clsp, .bo-name a, .prod-name a").all()
                    if i >= len(current_links):
                        break
                    
                    target_link = current_links[i]
                    href = await target_link.get_attribute("href")
                    
                    if not href or not href.startswith("http"):
                        continue

                    print(f"[*] Sub-clicking into supplier profile {i+1}: {href}")
                    
                    sub_page = await context.new_page()
                    await sub_page.goto(href, timeout=TIMEOUT_MS)
                    await human_delay()

                    # SUB-CLICK 1: Reveal Contact / Mobile Number button if present
                    try:
                        view_btn = sub_page.locator("text='View Mobile Number', text='Contact Supplier', text='Call'")
                        if await view_btn.count() > 0:
                            await view_btn.first.click()
                            print("[*] Clicked 'View Number' button successfully.")
                            await asyncio.sleep(2)
                    except Exception:
                        pass

                    # Extract data from the profile page
                    html_data = await sub_page.content()
                    lead_info = extract_lead_details(html_data, href)

                    # SUB-CLICK 2: Check if independent website is listed for deep dive
                    website_element = sub_page.locator("a[href*='http']:not([href*='indiamart']):not([href*='tradeindia'])")
                    if await website_element.count() > 0:
                        ind_url = await website_element.first.get_attribute("href")
                        if ind_url and ind_url.startswith("http"):
                            print(f"[*] Found independent website. Diving deep into: {ind_url}")
                            ind_page = await context.new_page()
                            await ind_page.goto(ind_url, timeout=15000)
                            await human_delay()
                            
                            try:
                                contact_link = ind_page.locator("a:has-text('Contact'), a:has-text('Reach')").first
                                if await contact_link.count() > 0:
                                    await contact_link.click()
                                    await human_delay()
                            except Exception:
                                pass

                            ind_html = await ind_page.content()
                            ind_lead_info = extract_lead_details(ind_html, ind_url)
                            
                            if ind_lead_info["phone"] != "Not Found":
                                lead_info["phone"] = ind_lead_info["phone"]
                            if ind_lead_info["email"] != "Not Found":
                                lead_info["email"] = ind_lead_info["email"]
                            lead_info["source_url"] = ind_url
                            
                            await ind_page.close()

                    leads.append(lead_info)
                    print(f"[SUCCESS] Extracted: {lead_info['company_name']} | Phone: {lead_info['phone']} | Email: {lead_info['email']}")

                    await sub_page.close()
                    await human_delay()

                except Exception as inner_err:
                    print(f"[!] Error processing individual supplier: {inner_err}")
                    continue

        except Exception as e:
            print(f"[!] Browser execution error: {e}")
        finally:
            await browser.close()

    return leads


# ---------------------------------------------------------------------
# 4. MAIN ORCHESTRATOR & CSV EXPORTER
# ---------------------------------------------------------------------
async def main():
    print("==================================================")
    print(" Starting Antigravity Exporter & Lead Agent (Zero Cost)")
    print("==================================================")

    all_leads = []
    keyword = SEARCH_KEYWORDS[0]
    formatted_query = keyword.replace(" ", "%20")
    
    target_url = f"https://www.indiamart.com/proddur/search.html?ss={formatted_query}"

    print(f"[*] Target Search Keyword: {keyword}")
    leads = await run_browser_agent(target_url)
    all_leads.extend(leads)

    csv_filename = "leads.csv"
    print(f"[*] Saving {len(all_leads)} leads to local file: {csv_filename}")

    keys = ["company_name", "phone", "email", "gstin", "source_url"]
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=keys)
        writer.writeheader()
        for lead in all_leads:
            writer.writerow(lead)

    print("==================================================")
    print(f" Lead Extraction Complete! Results saved to {csv_filename}")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
