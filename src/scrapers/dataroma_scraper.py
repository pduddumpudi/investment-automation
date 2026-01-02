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

    # Complete investor name to Dataroma ID mapping (ALL 81 investors)
    INVESTOR_IDS = {
        "AKO Capital": "AKO",
        "Alex Roepers": "AIM",
        "AltaRock Partners": "AP",
        "Bill & Melinda Gates Foundation": "GFT",
        "Bill Ackman": "psc",
        "Bill Miller": "LMM",
        "Bill Nygren": "oaklx",
        "Bruce Berkowitz": "fairx",
        "Bryan Lawrence": "OCL",
        "Carl Icahn": "ic",
        "Charles Bobrinskoy": "ARFFX",
        "Chase Coleman": "TGM",
        "Chris Hohn": "tci",
        "Christopher Bloomstran": "SA",
        "Christopher Davis": "DAV",
        "Chuck Akre": "AC",
        "Clifford Sosin": "CAS",
        "Daniel Loeb": "tp",
        "David Abrams": "abc",
        "David Einhorn": "GLRE",
        "David Katz": "MAVFX",
        "David Rolfe": "WP",
        "David Tepper": "AM",
        "Dennis Hong": "SP",
        "Dodge & Cox": "DODGX",
        "Duan Yongping": "HH",
        "First Eagle": "FE",
        "FPA Queens Road": "FPPTX",
        "Francis Chou": "ca",
        "Francois Rochon": "GC",
        "Glenn Greenberg": "CCM",
        "Glenn Welling": "ENG",
        "Greenhaven Associates": "GA",
        "Greg Alexander": "CM",
        "Guy Spier": "aq",
        "Harry Burn": "SSHFX",
        "Hillman Value Fund": "hcmax",
        "Howard Marks": "oc",
        "Jensen Investment": "JIM",
        "John Armitage": "EC",
        "John Rogers": "CAAPX",
        "Josh Tarasoff": "GLC",
        "Kahn Brothers": "KB",
        "Lee Ainslie": "mc",
        "Leon Cooperman": "oa",
        "Li Lu": "HC",
        "Lindsell Train": "LT",
        "Mairs & Power": "MPGFX",
        "Mason Hawkins": "LLPFX",
        "Meridian Contrarian": "MVALX",
        "Michael Burry": "SAM",
        "Mohnish Pabrai": "PI",
        "Nelson Peltz": "TF",
        "Norbert Lou": "PC",
        "Pat Dorsey": "DA",
        "Polen Capital": "pcm",
        "Prem Watsa": "FFH",
        "Richard Pzena": "pzfvx",
        "Robert Olstein": "OFALX",
        "Robert Vinall": "RVC",
        "Ruane Cunniff": "SEQUX",
        "Samantha McLemore": "PTNT",
        "Sarah Ketterer": "CAU",
        "Seth Klarman": "BAUPOST",
        "Stephen Mandel": "LPC",
        "Steven Romick": "FPACX",
        "Terry Smith": "FS",
        "Third Avenue": "TA",
        "Thomas Gayner": "MKL",
        "Thomas Russo": "GR",
        "Tom Bancroft": "MP",
        "Torray Funds": "T",
        "Triple Frond Partners": "TFP",
        "Tweedy Browne": "TWEBX",
        "Valley Forge Capital": "VFC",
        "ValueAct Capital": "VA",
        "Viking Global": "vg",
        "Wallace Weitz": "WVALX",
        "Warren Buffett": "BRK",
        "William Von Mueffling": "cc",
        "Yacktman Asset": "YAM"
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
                    # Column structure:
                    # 0: History link (hamburger icon)
                    # 1: Stock link with "TICKER- Company Name" and href /m/stock.php?sym=TICKER
                    # 2: Portfolio percentage
                    # 3: Recent activity
                    # 4: Shares

                    # Get the stock link from column 1 (not column 0 which is history)
                    stock_link = cols[1].find('a')
                    if not stock_link:
                        continue

                    # The ticker is in the URL parameter: /m/stock.php?sym=AAPL
                    href = stock_link.get('href', '')
                    if 'sym=' in href:
                        ticker_raw = href.split('sym=')[-1].split('&')[0]
                    else:
                        # Fallback: try to extract from link text (e.g., "AAPL- Apple Inc.")
                        link_text = stock_link.get_text(strip=True)
                        if '- ' in link_text:
                            ticker_raw = link_text.split('- ')[0].strip()
                        else:
                            ticker_raw = link_text

                    ticker = self.normalize_ticker(ticker_raw)

                    # Company name is after the dash in the link text
                    link_text = stock_link.get_text(strip=True)
                    if '- ' in link_text:
                        company_name = link_text.split('- ', 1)[1].strip()
                    else:
                        company_name = ticker

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
