"""
Main orchestration script for the investment automation tool.

This script:
1. Scrapes Dataroma for investor holdings
2. Scrapes Substack for investment ideas
3. Fetches fundamentals from yfinance
4. Merges all data and saves to JSON/CSV
"""
import json
import pandas as pd
from pathlib import Path
import sys
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.dataroma_scraper import scrape_dataroma
from scrapers.substack_scraper import scrape_substack
from scrapers.yfinance_scraper import fetch_fundamentals
from processors.data_merger import merge_all_data
from processors.deduplicator import deduplicate_tickers
from utils.config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


def save_results(merged_data: Dict, data_dir: Path) -> None:
    """
    Save results to JSON and CSV files.

    Args:
        merged_data: Merged dataset dictionary
        data_dir: Directory to save data files
    """
    # Save JSON
    json_path = data_dir / 'stocks.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON to {json_path}")

    # Save CSV
    if merged_data.get('stocks'):
        df = pd.json_normalize(merged_data['stocks'])
        csv_path = data_dir / 'stocks.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"Saved CSV to {csv_path}")

    # Save metadata
    metadata = {
        'last_updated': merged_data['last_updated'],
        'total_stocks': merged_data['total_stocks'],
        'dataroma_tickers': len([s for s in merged_data['stocks'] if 'Dataroma' in s.get('sources', [])]),
        'substack_tickers': len([s for s in merged_data['stocks'] if 'Substack' in s.get('sources', [])]),
    }
    metadata_path = data_dir / 'metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")


def load_previous_data(data_dir: Path) -> Dict:
    """
    Load previous data as fallback in case of errors.

    Args:
        data_dir: Directory containing data files

    Returns:
        Previous data or empty dict
    """
    json_path = data_dir / 'stocks.json'
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load previous data: {e}")

    return {'last_updated': '', 'total_stocks': 0, 'stocks': []}


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("INVESTMENT AUTOMATION TOOL - STARTING")
    logger.info("=" * 80)

    try:
        # Step 1: Scrape Dataroma
        logger.info("\n[1/5] Scraping Dataroma...")
        investors = config.get_dataroma_investors()
        logger.info(f"Tracking {len(investors)} investors: {investors}")

        dataroma_holdings = []
        try:
            dataroma_holdings = scrape_dataroma(investors)
            logger.info(f"✓ Scraped {len(dataroma_holdings)} holdings from Dataroma")
        except Exception as e:
            logger.error(f"✗ Dataroma scraping failed: {e}")

        # Step 2: Scrape Substack
        logger.info("\n[2/5] Scraping Substack...")
        substack_articles = []
        try:
            # Check if OpenAI API key is available for LLM extraction
            import os
            use_llm = bool(os.getenv('OPENAI_API_KEY'))
            if use_llm:
                logger.info("Using LLM for ticker extraction (more accurate)")
            else:
                logger.info("OPENAI_API_KEY not set. Using regex for ticker extraction.")

            substack_articles = scrape_substack(use_llm=use_llm)
            logger.info(f"✓ Scraped {len(substack_articles)} articles from Substack")
        except Exception as e:
            logger.error(f"✗ Substack scraping failed: {e}")

        # Step 3: Collect unique tickers
        logger.info("\n[3/5] Collecting unique tickers...")
        all_tickers = []

        # From Dataroma
        dataroma_tickers = [h['ticker'] for h in dataroma_holdings if h.get('ticker')]
        all_tickers.extend(dataroma_tickers)
        logger.info(f"Dataroma tickers: {len(dataroma_tickers)}")

        # From Substack
        substack_tickers = []
        for article in substack_articles:
            substack_tickers.extend(article.get('tickers', []))
        all_tickers.extend(substack_tickers)
        logger.info(f"Substack tickers: {len(substack_tickers)}")

        # Deduplicate
        unique_tickers = deduplicate_tickers(all_tickers)
        logger.info(f"✓ Total unique tickers: {len(unique_tickers)}")

        if not unique_tickers:
            logger.warning("No tickers found! Using previous data if available.")
            previous_data = load_previous_data(config.data_dir)
            save_results(previous_data, config.data_dir)
            return

        # Step 4: Fetch fundamentals
        logger.info("\n[4/5] Fetching fundamentals from yfinance...")
        fundamentals = {}
        try:
            fundamentals = fetch_fundamentals(unique_tickers)
            logger.info(f"✓ Fetched fundamentals for {len(fundamentals)} tickers")
        except Exception as e:
            logger.error(f"✗ yfinance fetching failed: {e}")

        # Step 5: Merge all data
        logger.info("\n[5/5] Merging all data...")
        merged_data = merge_all_data(
            dataroma_holdings=dataroma_holdings,
            substack_articles=substack_articles,
            fundamentals=fundamentals
        )
        logger.info(f"✓ Merged data ready: {merged_data['total_stocks']} stocks")

        # Save results
        logger.info("\nSaving results...")
        save_results(merged_data, config.data_dir)

        logger.info("\n" + "=" * 80)
        logger.info("SUCCESS! Data pipeline completed")
        logger.info(f"Output files:")
        logger.info(f"  - {config.data_dir / 'stocks.json'}")
        logger.info(f"  - {config.data_dir / 'stocks.csv'}")
        logger.info(f"  - {config.data_dir / 'metadata.json'}")
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.warning("\nProcess interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\nFATAL ERROR: {e}", exc_info=True)
        logger.warning("Attempting to use previous data...")

        previous_data = load_previous_data(config.data_dir)
        if previous_data.get('stocks'):
            save_results(previous_data, config.data_dir)
            logger.info("Using previous data as fallback")
        else:
            logger.error("No previous data available")
            sys.exit(1)


if __name__ == '__main__':
    main()
