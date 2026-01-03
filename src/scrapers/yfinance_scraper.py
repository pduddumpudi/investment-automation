"""
Fetch comprehensive stock fundamentals using yfinance API with retry logic and rate limiting.
Includes core fields fetched upfront and extended fields for lazy loading.
"""
import yfinance as yf
import time
from typing import Dict, List, Optional, Set
try:
    from src.utils.logger import setup_logger
except ModuleNotFoundError:
    from utils.logger import setup_logger

logger = setup_logger(__name__)


# International ticker format variations to try
INTERNATIONAL_FORMATS = {
    'KS': ['.KS', '.KQ'],  # Korean (KOSPI, KOSDAQ)
    'HK': ['.HK'],  # Hong Kong
    'T': ['.T'],  # Tokyo
    'L': ['.L'],  # London
    'DE': ['.DE'],  # Germany
    'PA': ['.PA'],  # Paris
    'AS': ['.AS'],  # Amsterdam
    'SW': ['.SW'],  # Swiss
    'TO': ['.TO'],  # Toronto
    'AX': ['.AX'],  # Australia
}


class YFinanceScraper:
    """Fetch comprehensive stock fundamentals from Yahoo Finance."""

    def __init__(self, rate_limit_delay: float = 2.0):
        """
        Initialize the yfinance scraper.

        Args:
            rate_limit_delay: Delay in seconds between requests
        """
        self.rate_limit_delay = rate_limit_delay

    def _try_ticker_formats(self, ticker: str) -> Optional[yf.Ticker]:
        """
        Try different ticker formats for international stocks.

        Args:
            ticker: Original ticker symbol

        Returns:
            yf.Ticker object if found, None otherwise
        """
        # First try the ticker as-is
        stock = yf.Ticker(ticker)
        info = stock.info

        if info and 'symbol' in info and info.get('regularMarketPrice'):
            return stock

        # If it looks like an international ticker, try variations
        if any(char.isdigit() for char in ticker[:4]):
            # Likely international (e.g., 003550, 0019)
            base_ticker = ticker.split('.')[0].split('-')[0]

            for suffix_list in INTERNATIONAL_FORMATS.values():
                for suffix in suffix_list:
                    try_ticker = f"{base_ticker}{suffix}"
                    logger.debug(f"Trying format: {try_ticker}")
                    try:
                        stock = yf.Ticker(try_ticker)
                        info = stock.info
                        if info and 'symbol' in info and info.get('regularMarketPrice'):
                            logger.info(f"Found {ticker} as {try_ticker}")
                            return stock
                    except Exception:
                        continue

        return None

    def get_fundamentals(self, ticker: str, max_retries: int = 3, extended: bool = False) -> Optional[Dict]:
        """
        Get fundamental data for a stock ticker with retry logic.

        Args:
            ticker: Stock ticker symbol
            max_retries: Maximum number of retry attempts
            extended: If True, fetch all extended fields (slower)

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
                    # Try international formats
                    stock = self._try_ticker_formats(ticker)
                    if stock:
                        info = stock.info
                    else:
                        logger.warning(f"No data found for {ticker}")
                        time.sleep(self.rate_limit_delay)
                        return None

                # Core fields (always fetched)
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                week_52_high = info.get('fiftyTwoWeekHigh')
                week_52_low = info.get('fiftyTwoWeekLow')
                total_cash = info.get('totalCash')
                total_debt = info.get('totalDebt')
                long_term_debt = info.get('longTermDebt')

                # Calculate 52-week distance metrics
                pct_above_52w_low = None
                pct_below_52w_high = None
                if current_price and week_52_low and week_52_low > 0:
                    pct_above_52w_low = round(((current_price - week_52_low) / week_52_low) * 100, 2)
                if current_price and week_52_high and week_52_high > 0:
                    pct_below_52w_high = round(((week_52_high - current_price) / week_52_high) * 100, 2)

                # Calculate net debt
                net_debt = None
                if total_debt is not None and total_cash is not None:
                    net_debt = total_debt - total_cash

                fundamentals = {
                    'ticker': ticker,
                    'company_name': info.get('longName') or info.get('shortName') or ticker,
                    'pe_ratio': info.get('trailingPE'),
                    'forward_pe': info.get('forwardPE'),
                    'pb_ratio': info.get('priceToBook'),
                    'peg_ratio': info.get('pegRatio'),
                    'week_52_high': week_52_high,
                    'week_52_low': week_52_low,
                    'pct_above_52w_low': pct_above_52w_low,
                    'pct_below_52w_high': pct_below_52w_high,
                    'insider_pct': info.get('heldPercentInsiders'),
                    'institutional_pct': info.get('heldPercentInstitutions'),
                    'market_cap': info.get('marketCap'),
                    'current_price': current_price,
                    'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),
                    'total_cash': total_cash,
                    'total_debt': total_debt,
                    'long_term_debt': long_term_debt,
                    'net_debt': net_debt,
                    'sector': info.get('sector'),
                    'industry': info.get('industry'),
                    'country': info.get('country'),
                    'quote_type': info.get('quoteType', 'EQUITY'),
                    'currency': info.get('currency'),
                    'exchange': info.get('exchange'),
                }

                # Extended valuation fields
                if extended:
                    fundamentals.update({
                        # Valuation
                        'ev_to_ebitda': info.get('enterpriseToEbitda'),
                        'ev_to_revenue': info.get('enterpriseToRevenue'),
                        'price_to_sales': info.get('priceToSalesTrailing12Months'),
                        'price_to_fcf': self._calculate_price_to_fcf(info),
                        'enterprise_value': info.get('enterpriseValue'),

                        # Quality metrics
                        'roe': info.get('returnOnEquity'),
                        'roa': info.get('returnOnAssets'),
                        'gross_margin': info.get('grossMargins'),
                        'operating_margin': info.get('operatingMargins'),
                        'net_margin': info.get('profitMargins'),
                        'debt_to_equity': info.get('debtToEquity'),
                        'current_ratio': info.get('currentRatio'),
                        'quick_ratio': info.get('quickRatio'),

                        # Income metrics
                        'dividend_yield': info.get('dividendYield'),
                        'dividend_rate': info.get('dividendRate'),
                        'payout_ratio': info.get('payoutRatio'),
                        'ex_dividend_date': info.get('exDividendDate'),
                        'eps_ttm': info.get('trailingEps'),
                        'eps_forward': info.get('forwardEps'),

                        # Risk metrics
                        'beta': info.get('beta'),
                        'short_ratio': info.get('shortRatio'),
                        'short_pct_float': info.get('shortPercentOfFloat'),

                        # Additional
                        'revenue': info.get('totalRevenue'),
                        'revenue_growth': info.get('revenueGrowth'),
                        'earnings_growth': info.get('earningsGrowth'),
                        'free_cash_flow': info.get('freeCashflow'),
                        'operating_cash_flow': info.get('operatingCashflow'),
                        'total_debt': info.get('totalDebt'),
                        'total_cash': info.get('totalCash'),
                        'book_value': info.get('bookValue'),
                        'shares_outstanding': info.get('sharesOutstanding'),
                        'float_shares': info.get('floatShares'),
                        'avg_volume': info.get('averageVolume'),
                        'avg_volume_10d': info.get('averageVolume10days'),
                        'fifty_day_avg': info.get('fiftyDayAverage'),
                        'two_hundred_day_avg': info.get('twoHundredDayAverage'),
                    })

                # Convert percentages to readable format (0-100 scale)
                pct_fields = ['insider_pct', 'institutional_pct', 'roe', 'roa',
                              'gross_margin', 'operating_margin', 'net_margin',
                              'dividend_yield', 'payout_ratio', 'short_pct_float',
                              'revenue_growth', 'earnings_growth']

                for field in pct_fields:
                    if field in fundamentals and fundamentals[field] is not None:
                        # yfinance returns some as decimals (0.15) and some as percentages (15)
                        value = fundamentals[field]
                        if isinstance(value, (int, float)):
                            if abs(value) < 1:  # Likely a decimal
                                fundamentals[field] = round(value * 100, 2)
                            else:
                                fundamentals[field] = round(value, 2)

                # Flag as international if non-USD
                currency = fundamentals.get('currency', 'USD')
                fundamentals['is_international'] = currency != 'USD'

                # Log any missing core fields
                core_fields = ['pe_ratio', 'pb_ratio', 'market_cap', 'current_price']
                missing_fields = [k for k in core_fields if fundamentals.get(k) is None]
                if missing_fields:
                    logger.debug(f"{ticker} missing core fields: {missing_fields}")

                logger.info(f"Successfully fetched data for {ticker}")
                time.sleep(self.rate_limit_delay)
                return fundamentals

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {ticker}: {e}")

                if attempt < max_retries - 1:
                    wait_time = max(self.rate_limit_delay + 1.0, 3.0)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {ticker} after {max_retries} attempts")
                    return None

        return None

    def _calculate_price_to_fcf(self, info: Dict) -> Optional[float]:
        """Calculate Price to Free Cash Flow ratio."""
        market_cap = info.get('marketCap')
        fcf = info.get('freeCashflow')

        if market_cap and fcf and fcf != 0:
            return round(market_cap / fcf, 2)
        return None

    def get_fundamentals_batch(self, tickers: List[str], extended: bool = False) -> Dict[str, Dict]:
        """
        Fetch fundamentals for multiple tickers.

        Args:
            tickers: List of ticker symbols
            extended: If True, fetch all extended fields

        Returns:
            Dictionary mapping ticker to fundamentals data
        """
        results = {}
        total = len(tickers)

        logger.info(f"Fetching fundamentals for {total} tickers (extended={extended})...")

        for i, ticker in enumerate(tickers, 1):
            logger.info(f"Progress: {i}/{total} - {ticker}")

            data = self.get_fundamentals(ticker, extended=extended)
            if data:
                results[ticker] = data
            else:
                # Store failed ticker with minimal info
                results[ticker] = {
                    'ticker': ticker,
                    'company_name': ticker,
                    'error': 'Failed to fetch data'
                }

        success_count = len([r for r in results.values() if 'error' not in r])
        success_rate = (success_count / total * 100) if total > 0 else 0
        logger.info(f"Completed: {success_count}/{total} tickers ({success_rate:.1f}% success rate)")

        return results

    def get_extended_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Fetch extended fundamentals for a single ticker (for lazy loading).

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with extended fundamental data
        """
        return self.get_fundamentals(ticker, extended=True)

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
            elif isinstance(value, float):
                # Round floats to 2 decimal places
                if key in ['market_cap', 'enterprise_value', 'revenue', 'free_cash_flow',
                           'operating_cash_flow', 'total_debt', 'total_cash']:
                    # Large numbers - format with commas
                    formatted[key] = value
                else:
                    formatted[key] = round(value, 2)
            else:
                formatted[key] = value

        return formatted


def fetch_fundamentals(tickers: List[str], extended: bool = False) -> Dict[str, Dict]:
    """
    Convenience function to fetch fundamentals for multiple tickers.

    Args:
        tickers: List of ticker symbols
        extended: If True, fetch all extended fields

    Returns:
        Dictionary mapping ticker to fundamentals
    """
    scraper = YFinanceScraper(rate_limit_delay=2.0)
    return scraper.get_fundamentals_batch(tickers, extended=extended)


def fetch_single_extended(ticker: str) -> Optional[Dict]:
    """
    Fetch extended fundamentals for a single ticker (for API/lazy loading).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with extended fundamentals or None
    """
    scraper = YFinanceScraper(rate_limit_delay=2.0)
    return scraper.get_extended_fundamentals(ticker)
