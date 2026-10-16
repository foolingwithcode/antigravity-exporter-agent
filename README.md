# 🚀 Antigravity Indian Exporter & E-commerce Lead Discovery Agent

An autonomous, **zero-cost AI browser agent** built with **Playwright**, **BeautifulSoup**, and Python's built-in libraries to discover Indian international e-commerce sellers, manufacturers, and B2B exporters across **Amazon**, **Etsy**, **eBay**, **Shopify**, **IndiaMART**, and **TradeIndia**.

It navigates deep into website hierarchies via **multi-level sub-clicking** (locating *"Contact Us"*, *"About Us"*, and revealing hidden B2B numbers) and saves structured lead profiles directly into a local CSV file with zero cash cost.

---

## 📂 Project Architecture & Directory Structure

```text
antigravity-exporter-agent/
├── main.py              # Core execution loop & orchestrator CLI
├── browser_agent.py     # Playwright navigation & multi-level sub-clicking logic
├── extractor.py         # Parsing logic for phones, emails, addresses, GSTINs & IECs
├── config.py            # Search keywords, target platforms, and human-like delays
├── requirements.txt     # Python dependencies (playwright, beautifulsoup4, etc.)
├── README.md            # Setup and execution guide
├── leads.csv            # Output storage file with extracted leads
└── .gitignore           # Git ignore configurations
```

---

## ✨ Key Features

- **Zero API Costs**: No costly third-party data APIs or paid scraper subscriptions required.
- **Multi-Platform Exporter Discovery**:
  - **IndiaMART**: B2B manufacturer directories and supplier profiles.
  - **TradeIndia**: Verified Indian exporters across industrial and consumer sectors.
  - **Etsy**: Indian artisans and international craft exporters.
  - **eBay**: High-volume Indian export stores and registered businesses.
  - **Amazon Global Selling**: Indian manufacturers retailing internationally.
  - **Shopify**: Independent Indian D2C export brands discovered via search dorking.
- **Deep Multi-Level Sub-Clicking**:
  - Automatically identifies and clicks internal *"Contact Us"*, *"About Us"*, and *"Company Profile"* links.
  - Unmasks dynamic or hidden numbers (clicks *"View Number"*, *"Show Contact"* triggers).
  - Merges multi-page entity data into a consolidated lead profile.
- **High-Precision B2B Extractor**:
  - **Phones & WhatsApp**: Normalizes Indian mobile (`+91 9XXXX XXXXX`), landlines, and WhatsApp API click-to-chat links.
  - **Emails**: Extracts direct mailto anchors, regex matches, and decodes obfuscated patterns (`info [at] domain.com`).
  - **GSTIN & IEC**: Validates 15-character Indian GSTINs with state codes (01–38) and 10-character Importer Exporter Codes (IEC).
  - **Physical Addresses**: Extracts Indian PIN codes (6 digits) and state/city designations.
- **Stealth & Anti-Detection**:
  - Bypasses basic bot fingerprints (`navigator.webdriver` removal).
  - Humanized smooth scrolling to trigger lazy-loaded DOM elements.
  - Configurable randomized jitter delays between requests.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.9+ installed on your system.
- Git.

### 2. Clone Repository & Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/foolingwithcode/antigravity-exporter-agent.git
cd antigravity-exporter-agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies & Playwright Browser Binaries
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 🚦 Usage & Examples

### Default Run (All Platforms & Default Export Categories)
```bash
python main.py
```

### Custom Queries & Targeted Platforms
Target specific manufacturing hubs and export categories:
```bash
python main.py --keywords "brassware moradabad export,organic cotton tirupur" --platforms "indiamart,tradeindia"
```

### Visual Debugging (Headful Browser Window)
Watch the browser agent navigate and perform sub-clicks in real time:
```bash
python main.py --headful --platforms "shopify,etsy" --keywords "handmade jewelry jaipur"
```

### Command Line Options

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--keywords` | *(Preconfigured list)* | Comma-separated search queries/categories |
| `--platforms` | `all` | Specific platforms: `indiamart`, `tradeindia`, `etsy`, `ebay`, `amazon`, `shopify` |
| `--output` | `leads.csv` | Destination CSV file path |
| `--headful` | `False` | Run with visible browser window for debugging |
| `--max-leads` | `15` | Maximum leads per keyword/platform pair |
| `--disable-deep-crawl` | `False` | Turn off multi-level clicking into Contact/About pages |

---

## 📊 Extracted Lead Data Schema (`leads.csv`)

| Field | Description | Example |
| :--- | :--- | :--- |
| **Company Name** | Registered entity or storefront title | *Moradabad Artisan Handicrafts Ltd.* |
| **Platform** | Source directory or marketplace | *IndiaMART* |
| **Search Query** | Category keyword matched | *brassware manufacturer export* |
| **Contact Person** | Name of owner or export manager | *Rajesh Sharma* |
| **Phone Numbers** | Semicolon-separated verified numbers | *+91-98123-45678; +91-99887-76655* |
| **Emails** | Semicolon-separated clean email addresses | *export@moradabadartisans.com* |
| **Website** | Direct website or storefront link | *https://moradabadartisans.com* |
| **Address** | Physical location with PIN code | *Civil Lines, Moradabad, Uttar Pradesh 244001* |
| **GSTIN** | 15-digit validated GST number | *09AAACH7409R1ZZ* |
| **IEC** | 10-character Importer Exporter Code | *0508012345* |
| **Social Links** | Company LinkedIn, Facebook, Instagram links | *https://linkedin.com/company/...* |
| **Source URL** | Direct URL where lead was discovered | *https://dir.indiamart.com/...* |
| **Extracted At** | Timestamp of extraction | *2026-10-16 15:30:00* |

---

## 🛡️ Best Practices & Responsible Usage

1. **Human-like Delays**: Always maintain the default delay intervals in [`config.py`](config.py) to prevent rate limiting or IP throttling.
2. **Respect `robots.txt`**: Ensure your discovery runs abide by each platform's published terms of service and acceptable use policies.
3. **Data Privacy**: Extracted contacts are strictly for public B2B outreach and legitimate commercial export-import communication.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
