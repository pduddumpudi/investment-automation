"""
Main orchestration script for the investment automation tool.

This script:
1. Scrapes Dataroma for investor holdings (dynamic discovery)
2. Scrapes Substack for investment ideas
3. Fetches fundamentals from yfinance
4. Merges all data and saves to JSON/CSV
"""
import json
import pandas as pd
from pathlib import Path
import sys
import argparse
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.dataroma_scraper import scrape_dataroma, DataromaScraper
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
    # Ensure directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = data_dir / 'stocks.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON to {json_path}")

    # Save CSV (flattened)
    if merged_data.get('stocks'):
        # Flatten for CSV export
        flat_stocks = []
        for stock in merged_data['stocks']:
            flat_entry = {
                'ticker': stock['ticker'],
                'company_name': stock['company_name'],
                'sources': ', '.join(stock.get('sources', [])),
                'investor_count': stock.get('investor_count', 0),
                'aggregate_activity': stock.get('aggregate_activity', 'Hold'),
            }

            # Add fundamentals
            fundamentals = stock.get('fundamentals', {})
            for key, value in fundamentals.items():
                flat_entry[f'fundamentals_{key}'] = value

            # Add investors as comma-separated
            investors = stock.get('dataroma_data', {}).get('investors', [])
            flat_entry['investors'] = ', '.join([inv['name'] for inv in investors])

            flat_stocks.append(flat_entry)

        df = pd.DataFrame(flat_stocks)
        csv_path = data_dir / 'stocks.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"Saved CSV to {csv_path}")

    # Save metadata
    stats = merged_data.get('stats', {})
    metadata = {
        'last_updated': merged_data['last_updated'],
        'total_stocks': merged_data['total_stocks'],
        'dataroma_stocks': stats.get('dataroma_stocks', 0),
        'substack_stocks': stats.get('substack_stocks', 0),
        'both_sources': stats.get('both_sources', 0),
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

    return {'last_updated': '', 'total_stocks': 0, 'stocks': [], 'stats': {}}


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Investment Automation Tool')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force full scrape of all investors (ignore incremental)')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("INVESTMENT AUTOMATION TOOL - STARTING")
    logger.info("=" * 80)

    try:
        # Step 1: Scrape Dataroma (dynamic discovery)
        logger.info("\n[1/5] Scraping Dataroma (dynamic investor discovery)...")
        dataroma_holdings = []
        discovered_investors = []
        try:
            scraper = DataromaScraper(force_full_scrape=args.force)
            dataroma_holdings = scraper.scrape_all_investors()
            discovered_investors = scraper.get_discovered_investors()
            logger.info(f"Discovered {len(discovered_investors)} investors on Dataroma")
            logger.info(f"Scraped {len(dataroma_holdings)} holdings from Dataroma")
        except Exception as e:
            logger.error(f"Dataroma scraping failed: {e}")

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
            logger.info(f"Scraped {len(substack_articles)} articles from Substack")
        except Exception as e:
            logger.error(f"Substack scraping failed: {e}")

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
        logger.info(f"Total unique tickers: {len(unique_tickers)}")

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
            success_count = len([f for f in fundamentals.values() if 'error' not in f])
            logger.info(f"Fetched fundamentals for {success_count}/{len(unique_tickers)} tickers")
        except Exception as e:
            logger.error(f"yfinance fetching failed: {e}")

        # Step 5: Merge all data
        logger.info("\n[5/5] Merging all data...")
        merged_data = merge_all_data(
            dataroma_holdings=dataroma_holdings,
            substack_articles=substack_articles,
            fundamentals=fundamentals
        )
        logger.info(f"Merged data ready: {merged_data['total_stocks']} stocks")

        # Log statistics
        stats = merged_data.get('stats', {})
        logger.info(f"  - From Dataroma: {stats.get('dataroma_stocks', 0)}")
        logger.info(f"  - From Substack: {stats.get('substack_stocks', 0)}")
        logger.info(f"  - From Both: {stats.get('both_sources', 0)}")

        # Save results
        logger.info("\nSaving results...")
        save_results(merged_data, config.data_dir)

        # Copy to docs folder for GitHub Pages
        docs_data_dir = config.docs_dir / 'data'
        docs_data_dir.mkdir(parents=True, exist_ok=True)

        # Copy JSON to docs
        import shutil
        shutil.copy(config.data_dir / 'stocks.json', docs_data_dir / 'stocks.json')
        logger.info(f"Copied stocks.json to {docs_data_dir}")

        logger.info("\n" + "=" * 80)
        logger.info("SUCCESS! Data pipeline completed")
        logger.info(f"Output files:")
        logger.info(f"  - {config.data_dir / 'stocks.json'}")
        logger.info(f"  - {config.data_dir / 'stocks.csv'}")
        logger.info(f"  - {config.data_dir / 'metadata.json'}")
        logger.info(f"  - {docs_data_dir / 'stocks.json'}")
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
