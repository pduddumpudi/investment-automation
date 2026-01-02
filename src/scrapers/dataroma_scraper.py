"""
Scrape investor portfolio data from Dataroma.com with edge case handling.
"""
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from typing import List, Dict, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataromaScraper:
    """Scrape investor holdings from Dataroma."""

    BASE_URL = "https://www.dataroma.com/m"
    MANAGERS_URL = f"{BASE_URL}/managers.php"

    # Investor name to Dataroma ID mapping (expand as needed)
    INVESTOR_IDS = {
        "Warren Buffett": "BRK",
        "Bill Ackman": "pershing",
        "Seth Klarman": "baupost",
        "David Einhorn": "greenlight",
        "Mohnish Pabrai": "pabrai",
        "Li Lu": "himalaya",
        "Guy Spier": "aquamarine",
        "Mason Hawkins": "longleaf",
        "Chuck Akre": "akre"
    }

    def __init__(self, investors: List[str]):
        """
        Initialize the Dataroma scraper.

        Args:
            investors: List of investor names to track
        """
        self.investors = investors
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    @staticmethod
    def normalize_ticker(ticker: str) -> str:
        """
        Normalize ticker symbols to handle edge cases.

        This function handles special ticker formats:
        - .WS (warrants) → -WT
        - .A, .B (share classes) → -A, -B
        - Other edge cases

        Args:
            ticker: Raw ticker from Dataroma

        Returns:
            Normalized ticker symbol
        """
        if not ticker:
            return ticker

        ticker = ticker.strip().upper()

        # Handle warrants (.WS → -WT)
        if ticker.endswith('.WS'):
            return ticker.replace('.WS', '-WT')

        # Handle share classes (.A, .B → -A, -B) but not numbered classes
        if not any(char.isdigit() for char in ticker):
            if ticker.endswith('.A') or ticker.endswith('.B'):
                return ticker.replace('.', '-')

        # Handle other period-based formats
        if '.' in ticker and not any(char.isdigit() for char in ticker.split('.')[-1]):
            return ticker.replace('.', '-')

        return ticker

    def get_investor_id(self, investor_name: str) -> Optional[str]:
        """
        Get Dataroma ID for an investor.

        Args:
            investor_name: Name of the investor

        Returns:
            Dataroma ID or None if not found
        """
        return self.INVESTOR_IDS.get(investor_name)

    def scrape_investor_holdings(self, investor_name: str) -> List[Dict]:
        """
        Scrape holdings for a specific investor.

        Args:
            investor_name: Name of the investor

        Returns:
            List of holding dictionaries
        """
        investor_id = self.get_investor_id(investor_name)
        if not investor_id:
            logger.warning(f"Investor ID not found for: {investor_name}")
            return []

        url = f"{self.BASE_URL}/holdings.php?m={investor_id}"
        logger.info(f"Scraping {investor_name} ({investor_id}): {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            holdings = []

            # Find the holdings table
            table = soup.find('table', {'id': 'grid'})
            if not table:
                logger.warning(f"No holdings table found for {investor_name}")
                return []

            rows = table.find_all('tr')[1:]  # Skip header row

            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue

                try:
                    # Extract data from columns
                    stock_link = cols[0].find('a')
                    if not stock_link:
                        continue

                    ticker_raw = stock_link.get_text(strip=True)
                    ticker = self.normalize_ticker(ticker_raw)

                    company_name = cols[1].get_text(strip=True)
                    portfolio_pct = cols[2].get_text(strip=True).replace('%', '')

                    # Get activity (buy/sell/hold)
                    activity = "Hold"
                    activity_col = cols[3] if len(cols) > 3 else None
                    if activity_col:
                        activity_text = activity_col.get_text(strip=True).lower()
                        if 'buy' in activity_text or 'add' in activity_text:
                            activity = "Increased position"
                        elif 'sell' in activity_text or 'reduce' in activity_text:
                            activity = "Decreased position"
                        elif 'new' in activity_text:
                            activity = "New position"

                    holding = {
                        'ticker': ticker,
                        'ticker_raw': ticker_raw,  # Keep original for debugging
                        'company_name': company_name,
                        'investor': investor_name,
                        'portfolio_percentage': portfolio_pct,
                        'activity': activity,
                        'source_url': url
                    }

                    holdings.append(holding)
                    logger.debug(f"Extracted: {ticker} ({company_name}) - {activity}")

                except Exception as e:
                    logger.error(f"Error parsing row for {investor_name}: {e}")
                    continue

            logger.info(f"Scraped {len(holdings)} holdings for {investor_name}")
            return holdings

        except requests.RequestException as e:
            logger.error(f"Failed to scrape {investor_name}: {e}")
            return []

        except Exception as e:
            logger.error(f"Unexpected error scraping {investor_name}: {e}")
            return []

        finally:
            # Rate limiting to be respectful
            time.sleep(2)

    def scrape_all_investors(self) -> List[Dict]:
        """
        Scrape holdings for all configured investors.

        Returns:
            List of all holdings across all investors
        """
        all_holdings = []

        for investor in self.investors:
            logger.info(f"Processing investor: {investor}")
            holdings = self.scrape_investor_holdings(investor)
            all_holdings.extend(holdings)
            time.sleep(2)  # Be respectful to the server

        logger.info(f"Total holdings scraped: {len(all_holdings)}")
        return all_holdings

    def get_unique_tickers(self, holdings: List[Dict]) -> List[str]:
        """
        Extract unique tickers from holdings.

        Args:
            holdings: List of holding dictionaries

        Returns:
            List of unique ticker symbols
        """
        tickers = {h['ticker'] for h in holdings if h.get('ticker')}
        return sorted(list(tickers))

    def export_to_dataframe(self, holdings: List[Dict]) -> pd.DataFrame:
        """
        Convert holdings to pandas DataFrame.

        Args:
            holdings: List of holding dictionaries

        Returns:
            DataFrame with holdings data
        """
        if not holdings:
            return pd.DataFrame()

        df = pd.DataFrame(holdings)
        return df


def scrape_dataroma(investors: List[str]) -> List[Dict]:
    """
    Convenience function to scrape Dataroma holdings.

    Args:
        investors: List of investor names

    Returns:
        List of holdings dictionaries
    """
    scraper = DataromaScraper(investors)
    return scraper.scrape_all_investors()
