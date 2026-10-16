"""
Main Orchestrator & CLI execution loop for Antigravity Indian Exporter & E-commerce Lead Discovery Agent.
Discovers Indian international e-commerce sellers and B2B exporters, extracts deep contacts via multi-level clicking,
and writes live results to CSV with zero external API costs.
"""

import argparse
import asyncio
import csv
from datetime import datetime
import logging
import os
from pathlib import Path
from typing import Dict, List, Set

import config
from browser_agent import ExporterBrowserAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("MainOrchestrator")


class LeadStorage:
    """Manages thread-safe, deduplicated, streaming CSV lead output."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.seen_signatures: Set[str] = set()
        self._initialize_csv()

    def _initialize_csv(self):
        """Create CSV file with headers if not present, and load existing signatures to deduplicate."""
        file_exists = self.filepath.exists() and os.path.getsize(self.filepath) > 0

        if not file_exists:
            with open(self.filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(config.CSV_HEADERS)
            logger.info(f"Initialized new CSV file: {self.filepath}")
        else:
            try:
                with open(self.filepath, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        sig = self._generate_signature(
                            row.get("Company Name", ""),
                            row.get("Website", "") or row.get("Source URL", "")
                        )
                        self.seen_signatures.add(sig)
                logger.info(f"Loaded {len(self.seen_signatures)} existing leads for deduplication.")
            except Exception as e:
                logger.warning(f"Could not read existing CSV for deduplication: {e}")

    def _generate_signature(self, name: str, url: str) -> str:
        clean_name = "".join(c for c in name.lower() if c.isalnum())
        clean_url = url.split("?")[0].rstrip("/").lower()
        return f"{clean_name}|{clean_url}"

    def save_lead(self, lead: Dict[str, any]) -> bool:
        """Append a newly discovered lead to CSV if not already stored."""
        name = lead.get("company_name", "Unknown")
        url = lead.get("website", "") or lead.get("source_url", "")
        sig = self._generate_signature(name, url)

        if sig in self.seen_signatures:
            logger.debug(f"Skipping duplicate lead: {name}")
            return False

        self.seen_signatures.add(sig)

        row = [
            name,
            lead.get("platform", ""),
            lead.get("query", ""),
            lead.get("contact_person", ""),
            "; ".join(lead.get("phones", [])),
            "; ".join(lead.get("emails", [])),
            lead.get("website", ""),
            lead.get("address", ""),
            "; ".join(lead.get("gstins", [])),
            "; ".join(lead.get("iecs", [])),
            "; ".join(lead.get("socials", [])),
            lead.get("source_url", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        with open(self.filepath, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        return True


async def run_orchestrator(
    keywords: List[str],
    platforms: List[str],
    output_path: Path,
    headless: bool,
    max_leads: int,
    enable_deep_crawl: bool,
):
    """Main discovery loop iterating over keywords and platforms."""
    config.MAX_LEADS_PER_KEYWORD = max_leads
    config.ENABLE_MULTI_LEVEL_CLICKING = enable_deep_crawl

    storage = LeadStorage(output_path)
    agent = ExporterBrowserAgent(headless=headless)

    total_extracted = 0
    total_emails = 0
    total_phones = 0

    print("=" * 70)
    print("🚀 Antigravity Indian Exporter & E-commerce Lead Discovery Agent")
    print(f"📦 Platforms: {', '.join(platforms)}")
    print(f"🔍 Keywords: {len(keywords)} queries")
    print(f"💾 Output File: {output_path}")
    print(f"🕵️  Headless Mode: {headless} | Multi-level Clicking: {enable_deep_crawl}")
    print("=" * 70)

    try:
        await agent.start()

        for kw_idx, keyword in enumerate(keywords, 1):
            print(f"\n[{kw_idx}/{len(keywords)}] 🔎 Starting Discovery: '{keyword}'")

            for platform in platforms:
                if platform not in config.PLATFORMS:
                    logger.warning(f"Skipping unsupported platform: {platform}")
                    continue

                leads = await agent.search_and_discover(platform, keyword)

                saved_count = 0
                for lead in leads:
                    is_new = storage.save_lead(lead)
                    if is_new:
                        saved_count += 1
                        total_extracted += 1
                        total_emails += len(lead.get("emails", []))
                        total_phones += len(lead.get("phones", []))

                print(
                    f"   └─ {config.PLATFORMS[platform]['name']}: "
                    f"Discovered {len(leads)} raw leads -> Saved {saved_count} unique leads."
                )

                # Randomized breath between platforms
                await asyncio.sleep(2.0)

    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Saved leads are safely preserved.")
    except Exception as e:
        logger.error(f"Unexpected orchestrator error: {e}", exc_info=True)
    finally:
        await agent.close()

    print("\n" + "=" * 70)
    print("🏁 Discovery Run Completed Successfully!")
    print(f"✅ Total Unique Leads Saved: {total_extracted}")
    print(f"📧 Total Direct Emails Discovered: {total_emails}")
    print(f"📞 Total Phone / WhatsApp Numbers: {total_phones}")
    print(f"📁 Output File: {output_path}")
    print("=" * 70)


def parse_arguments():
    """Command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Antigravity Indian Exporter & E-commerce Lead Discovery Agent"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        default="",
        help="Comma-separated custom search queries/keywords (e.g., 'brassware exporter,leather goods export')"
    )
    parser.add_argument(
        "--platforms",
        type=str,
        default="all",
        help="Comma-separated platforms: indiamart, tradeindia, etsy, ebay, amazon, shopify (default: all)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="leads.csv",
        help="Target output CSV file path (default: leads.csv)"
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run browser in headful mode (visible window) for debugging"
    )
    parser.add_argument(
        "--max-leads",
        type=int,
        default=config.MAX_LEADS_PER_KEYWORD,
        help="Maximum leads to extract per keyword/platform combination"
    )
    parser.add_argument(
        "--disable-deep-crawl",
        action="store_true",
        help="Disable multi-level sub-clicking into Contact Us / About Us pages"
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Determine keywords
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    else:
        keywords = config.DEFAULT_KEYWORDS

    # Determine platforms
    if args.platforms.lower() == "all":
        platforms = list(config.PLATFORMS.keys())
    else:
        platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]

    output_path = Path(args.output).resolve()
    headless = not args.headful
    enable_deep_crawl = not args.disable_deep_crawl

    asyncio.run(
        run_orchestrator(
            keywords=keywords,
            platforms=platforms,
            output_path=output_path,
            headless=headless,
            max_leads=args.max_leads,
            enable_deep_crawl=enable_deep_crawl,
        )
    )


if __name__ == "__main__":
    main()
