"""
Main orchestration script for the investment automation tool.

This script:
1. Scrapes Dataroma for investor holdings (dynamic discovery)
2. Scrapes Substack for investment ideas
3. Fetches fundamentals from yfinance
4. Merges all data and saves to JSON/CSV
5. Evaluates alerts and sends email notifications
"""
import json
import pandas as pd
from pathlib import Path
import sys
import argparse
import os
from typing import Dict, List, Set
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.dataroma_scraper import scrape_dataroma, DataromaScraper
from scrapers.substack_scraper import scrape_substack
from scrapers.yfinance_scraper import fetch_fundamentals
from processors.data_merger import merge_all_data
from processors.deduplicator import deduplicate_tickers
from utils.config import config
from utils.logger import setup_logger

# Import alerts (optional - may not be installed)
try:
    from alerts.alert_engine import evaluate_alerts
    from alerts.email_sender import send_alert_email
    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False

# Import sheets reader (optional)
try:
    from utils.sheets_reader import get_sheets_config
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

logger = setup_logger(__name__)

# Failed tickers retry file
FAILED_TICKERS_PATH = config.data_dir / 'failed_tickers.json'


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


def load_failed_tickers() -> Dict:
    """Load failed tickers for retry."""
    if FAILED_TICKERS_PATH.exists():
        try:
            with open(FAILED_TICKERS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load failed tickers: {e}")
    return {'tickers': {}}


def save_failed_tickers(failed: Dict) -> None:
    """Save failed tickers for next run."""
    try:
        FAILED_TICKERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(FAILED_TICKERS_PATH, 'w', encoding='utf-8') as f:
            json.dump(failed, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save failed tickers: {e}")


def track_failed_ticker(failed_data: Dict, ticker: str) -> None:
    """Track a failed ticker with failure count."""
    if ticker not in failed_data['tickers']:
        failed_data['tickers'][ticker] = {
            'first_failed': datetime.utcnow().isoformat(),
            'fail_count': 0
        }
    failed_data['tickers'][ticker]['fail_count'] += 1
    failed_data['tickers'][ticker]['last_failed'] = datetime.utcnow().isoformat()


def get_stale_tickers(failed_data: Dict, max_failures: int = 3) -> Set[str]:
    """Get tickers that have failed too many times."""
    stale = set()
    for ticker, info in failed_data.get('tickers', {}).items():
        if info.get('fail_count', 0) >= max_failures:
            stale.add(ticker)
    return stale


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Investment Automation Tool')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force full scrape of all investors (ignore incremental)')
    parser.add_argument('--no-alerts', action='store_true',
                        help='Skip alert evaluation and email sending')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("INVESTMENT AUTOMATION TOOL - STARTING")
    logger.info("=" * 80)

    # Load configuration from Google Sheets if available
    sheets_config = {}
    if SHEETS_AVAILABLE and (os.getenv('SHEETS_URL') or os.getenv('SHEETS_SUBSTACK_URL')):
        logger.info("\nLoading configuration from Google Sheets...")
        try:
            sheets_config = get_sheets_config()
            logger.info(f"Loaded: {len(sheets_config.get('substack_sources', []))} Substack sources, "
                       f"{len(sheets_config.get('alert_rules', []))} alert rules")
        except Exception as e:
            logger.warning(f"Failed to load Sheets config: {e}")

    # Load failed tickers for retry
    failed_tickers_data = load_failed_tickers()
    stale_tickers = get_stale_tickers(failed_tickers_data)
    if stale_tickers:
        logger.info(f"Found {len(stale_tickers)} stale tickers (failed 3+ times)")

    try:
        # Step 1: Scrape Dataroma (dynamic discovery)
        logger.info("\n[1/6] Scraping Dataroma (dynamic investor discovery)...")
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
        logger.info("\n[2/6] Scraping Substack...")
        substack_articles = []
        try:
            # Check if OpenAI API key is available for LLM extraction
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
        logger.info("\n[3/6] Collecting unique tickers...")
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
        logger.info("\n[4/6] Fetching fundamentals from yfinance...")
        fundamentals = {}
        current_failed = set()
        try:
            fundamentals = fetch_fundamentals(unique_tickers)

            # Track successes and failures
            for ticker, data in fundamentals.items():
                if 'error' in data:
                    track_failed_ticker(failed_tickers_data, ticker)
                    current_failed.add(ticker)
                elif ticker in failed_tickers_data.get('tickers', {}):
                    # Remove from failed list if successful
                    del failed_tickers_data['tickers'][ticker]

            success_count = len([f for f in fundamentals.values() if 'error' not in f])
            logger.info(f"Fetched fundamentals for {success_count}/{len(unique_tickers)} tickers")
            if current_failed:
                logger.warning(f"Failed to fetch {len(current_failed)} tickers")

            # Save failed tickers for next run
            save_failed_tickers(failed_tickers_data)

        except Exception as e:
            logger.error(f"yfinance fetching failed: {e}")

        # Step 5: Merge all data
        logger.info("\n[5/6] Merging all data...")
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

        # Step 6: Evaluate alerts and send emails
        if ALERTS_AVAILABLE and not args.no_alerts:
            logger.info("\n[6/6] Evaluating alerts...")
            try:
                stocks = merged_data.get('stocks', [])
                alert_rules = sheets_config.get('alert_rules', [])
                settings = sheets_config.get('settings', {})

                all_alerts = evaluate_alerts(stocks, alert_rules, settings)

                total_alerts = sum(len(a) for a in all_alerts.values())
                if total_alerts > 0:
                    logger.info(f"Generated {total_alerts} alerts")

                    # Send alert emails
                    default_email = settings.get('default_email', os.getenv('ALERT_EMAIL'))
                    if default_email:
                        sent = send_alert_email(all_alerts, default_email)
                        logger.info(f"Sent {sent} alert email(s)")
                    else:
                        logger.warning("No alert email configured (set ALERT_EMAIL or default_email in Sheets)")
                else:
                    logger.info("No alerts triggered")

            except Exception as e:
                logger.error(f"Alert evaluation failed: {e}")
        else:
            logger.info("\n[6/6] Alerts skipped (disabled or not available)")

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
