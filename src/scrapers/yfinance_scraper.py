"""
Fetch stock fundamentals using yfinance API with retry logic and rate limiting.
"""
import yfinance as yf
import time
from typing import Dict, List, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class YFinanceScraper:
    """Fetch stock fundamentals from Yahoo Finance."""

    def __init__(self, rate_limit_delay: float = 0.5):
        """
        Initialize the yfinance scraper.

        Args:
            rate_limit_delay: Delay in seconds between requests
        """
        self.rate_limit_delay = rate_limit_delay

    def get_fundamentals(self, ticker: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Get fundamental data for a stock ticker with retry logic.

        Args:
            ticker: Stock ticker symbol
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary with fundamental data or None if failed
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"Fetching fundamentals for {ticker} (attempt {attempt + 1}/{max_retries})")

                stock = yf.Ticker(ticker)
                info = stock.info

                # Check if we got valid data
                if not info or 'symbol' not in info:
                    logger.warning(f"No data found for {ticker}")
                    return None

                fundamentals = {
                    'ticker': ticker,
                    'company_name': info.get('longName') or info.get('shortName') or ticker,
                    'pe_ratio': info.get('trailingPE'),
                    'forward_pe': info.get('forwardPE'),
                    'pb_ratio': info.get('priceToBook'),
                    'peg_ratio': info.get('pegRatio'),
                    'week_52_high': info.get('fiftyTwoWeekHigh'),
                    'week_52_low': info.get('fiftyTwoWeekLow'),
                    'insider_pct': info.get('heldPercentInsiders'),
                    'institutional_pct': info.get('heldPercentInstitutions'),
                    'market_cap': info.get('marketCap'),
                    'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
                    'sector': info.get('sector'),
                    'industry': info.get('industry'),
                    'country': info.get('country'),
                    'quote_type': info.get('quoteType', 'EQUITY'),  # EQUITY, ETF, MUTUALFUND, etc.
                }

                # Convert percentages to readable format
                if fundamentals['insider_pct']:
                    fundamentals['insider_pct'] = round(fundamentals['insider_pct'] * 100, 2)
                if fundamentals['institutional_pct']:
                    fundamentals['institutional_pct'] = round(fundamentals['institutional_pct'] * 100, 2)

                # Log any missing fields
                missing_fields = [k for k, v in fundamentals.items() if v is None]
                if missing_fields:
                    logger.debug(f"{ticker} missing fields: {missing_fields}")

                logger.info(f"Successfully fetched data for {ticker}")
                time.sleep(self.rate_limit_delay)
                return fundamentals

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {ticker}: {e}")

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * self.rate_limit_delay
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {ticker} after {max_retries} attempts")
                    return None

        return None

    def get_fundamentals_batch(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch fundamentals for multiple tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping ticker to fundamentals data
        """
        results = {}
        total = len(tickers)

        logger.info(f"Fetching fundamentals for {total} tickers...")

        for i, ticker in enumerate(tickers, 1):
            logger.info(f"Progress: {i}/{total} - {ticker}")

            data = self.get_fundamentals(ticker)
            if data:
                results[ticker] = data
            else:
                # Store failed ticker with minimal info
                results[ticker] = {
                    'ticker': ticker,
                    'company_name': ticker,
                    'error': 'Failed to fetch data'
                }

        success_rate = (len([r for r in results.values() if 'error' not in r]) / total * 100) if total > 0 else 0
        logger.info(f"Completed: {len(results)}/{total} tickers ({success_rate:.1f}% success rate)")

        return results

    def format_for_display(self, fundamentals: Dict) -> Dict:
        """
        Format fundamentals data for display (replace None with 'N/A').

        Args:
            fundamentals: Raw fundamentals dictionary

        Returns:
            Formatted dictionary
        """
        formatted = {}
        for key, value in fundamentals.items():
            if value is None:
                formatted[key] = 'N/A'
            elif isinstance(value, float) and key != 'insider_pct' and key != 'institutional_pct':
                # Round floats to 2 decimal places
                formatted[key] = round(value, 2)
            else:
                formatted[key] = value

        return formatted


def fetch_fundamentals(tickers: List[str]) -> Dict[str, Dict]:
    """
    Convenience function to fetch fundamentals for multiple tickers.

    Args:
        tickers: List of ticker symbols

    Returns:
        Dictionary mapping ticker to fundamentals
    """
    scraper = YFinanceScraper(rate_limit_delay=0.5)
    return scraper.get_fundamentals_batch(tickers)
