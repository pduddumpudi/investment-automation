"""
Scrape investor portfolio data from Dataroma.com with dynamic investor discovery
and incremental scraping based on last updated dates.
"""
import requests
from bs4 import BeautifulSoup
import time
import json
import os
import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
try:
    from src.utils.logger import setup_logger
except ModuleNotFoundError:
    from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataromaScraper:
    """Scrape investor holdings from Dataroma with dynamic discovery."""

    BASE_URL = "https://www.dataroma.com/m"
    HOME_URL = f"{BASE_URL}/home.php"
    MANAGERS_URL = f"{BASE_URL}/managers.php"

    # Metadata file for tracking last-scraped dates
    METADATA_FILE = "data/investor_metadata.json"

    def __init__(self, force_full_scrape: bool = False):
        """
        Initialize the Dataroma scraper.

        Args:
            force_full_scrape: If True, scrape all investors regardless of last updated date
        """
        self.force_full_scrape = force_full_scrape
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.investor_metadata = self._load_metadata()
        self.discovered_investors = []

    def _load_metadata(self) -> Dict:
        """Load investor metadata from file."""
        if os.path.exists(self.METADATA_FILE):
            try:
                with open(self.METADATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
        return {"investors": {}, "last_full_scrape": None}

    def _save_metadata(self) -> None:
        """Save investor metadata to file."""
        os.makedirs(os.path.dirname(self.METADATA_FILE), exist_ok=True)
        try:
            with open(self.METADATA_FILE, 'w') as f:
                json.dump(self.investor_metadata, f, indent=2)
            logger.info("Saved investor metadata")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    @staticmethod
    def normalize_ticker(ticker: str) -> str:
        """
        Normalize ticker symbols to handle edge cases.

        Handles:
        - .WS (warrants) → -WT
        - .A, .B (share classes) → -A, -B
        - International tickers (Korean, HK, etc.)
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

        # Handle other period-based formats (but preserve international tickers)
        # International formats like 003550.KS, 0019.HK should stay as-is for yfinance
        if '.' in ticker:
            parts = ticker.split('.')
            suffix = parts[-1]
            # Known international suffixes - keep these
            international_suffixes = {'KS', 'KQ', 'HK', 'T', 'L', 'DE', 'PA', 'AS', 'MI', 'SW', 'TO', 'V', 'AX', 'SI', 'BO', 'NS'}
            if suffix in international_suffixes:
                return ticker  # Keep as-is for yfinance
            elif not any(char.isdigit() for char in suffix):
                return ticker.replace('.', '-')

        return ticker

    @staticmethod
    def parse_activity(activity_text: str) -> Dict:
        """
        Parse activity text into structured format.

        Args:
            activity_text: Raw activity text like "Add 15%", "Sell", "Buy", "Reduce 8%"

        Returns:
            Dict with 'action' and 'percentage' keys
        """
        activity_text = activity_text.strip().lower() if activity_text else ""

        result = {
            "action": "Hold",
            "percentage": None
        }

        if not activity_text:
            return result

        # Extract percentage if present
        pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%?', activity_text)
        if pct_match:
            result["percentage"] = float(pct_match.group(1))

        # Determine action
        if 'buy' in activity_text or activity_text.startswith('add'):
            result["action"] = "Add" if 'add' in activity_text else "Buy"
        elif 'sell' in activity_text:
            result["action"] = "Sell"
        elif 'reduce' in activity_text:
            result["action"] = "Reduce"
        elif 'new' in activity_text:
            result["action"] = "New"

        return result

    def discover_investors(self) -> List[Dict]:
        """
        Discover all investors from Dataroma homepage dynamically.

        Returns:
            List of investor dicts with name, fund_id, last_updated
        """
        logger.info(f"Discovering investors from {self.HOME_URL}")

        try:
            response = self.session.get(self.HOME_URL, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            investors = []

            # Find all portfolio update links
            # Format: <a href="/m/holdings.php?m=SEQUX">Ruane Cunniff - Sequoia Fund Updated 26 Nov 2025</a>
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')

                if 'holdings.php' in href and 'm=' in href:
                    # Extract fund ID from URL
                    fund_id = href.split('m=')[-1].split('&')[0].strip()

                    if not fund_id:
                        continue

                    # Parse the link text
                    text = link.get_text(strip=True)

                    if not text or 'Updated' not in text:
                        continue

                    # Extract investor name and last updated date
                    # Format: "Investor Name - Fund Name Updated DD Mon YYYY"
                    updated_match = re.search(r'(.+?)\s+Updated\s+(\d{1,2}\s+\w{3}\s+\d{4})', text)

                    if updated_match:
                        full_name = updated_match.group(1).strip()
                        date_str = updated_match.group(2).strip()

                        # Parse investor name (before the dash if present)
                        if ' - ' in full_name:
                            investor_name = full_name.split(' - ')[0].strip()
                        else:
                            investor_name = full_name

                        # Parse date
                        try:
                            last_updated = datetime.strptime(date_str, '%d %b %Y')
                            last_updated_str = last_updated.strftime('%Y-%m-%d')
                        except ValueError:
                            last_updated_str = None
                            logger.warning(f"Could not parse date: {date_str}")

                        investor_info = {
                            "name": investor_name,
                            "full_name": full_name,
                            "fund_id": fund_id,
                            "last_updated": last_updated_str,
                            "source_url": f"{self.BASE_URL}/holdings.php?m={fund_id}"
                        }

                        # Avoid duplicates
                        if not any(i["fund_id"] == fund_id for i in investors):
                            investors.append(investor_info)
                            logger.debug(f"Discovered: {investor_name} ({fund_id}) - Updated {last_updated_str}")
                    else:
                        # Try alternative pattern without date (just grab the investor)
                        if ' - ' in text:
                            investor_name = text.split(' - ')[0].strip()
                            investor_info = {
                                "name": investor_name,
                                "full_name": text.replace('Updated', '').strip(),
                                "fund_id": fund_id,
                                "last_updated": None,
                                "source_url": f"{self.BASE_URL}/holdings.php?m={fund_id}"
                            }
                            if not any(i["fund_id"] == fund_id for i in investors):
                                investors.append(investor_info)
                                logger.debug(f"Discovered (no date): {investor_name} ({fund_id})")

            logger.info(f"Discovered {len(investors)} investors from Dataroma")
            self.discovered_investors = investors
            return investors

        except requests.RequestException as e:
            logger.error(f"Failed to discover investors: {e}")
            return []

    def should_scrape_investor(self, investor: Dict) -> bool:
        """
        Determine if an investor needs to be scraped based on last updated date.

        Args:
            investor: Investor info dict with name, fund_id, last_updated

        Returns:
            True if investor should be scraped
        """
        if self.force_full_scrape:
            return True

        fund_id = investor.get("fund_id")
        last_updated = investor.get("last_updated")

        if not fund_id or not last_updated:
            return True  # Scrape if we don't have data

        # Check our metadata for when we last scraped this investor
        stored_info = self.investor_metadata.get("investors", {}).get(fund_id, {})
        last_scraped = stored_info.get("last_updated_on_site")

        if not last_scraped:
            return True  # Never scraped before

        # If Dataroma's last_updated is newer than our last_scraped, scrape again
        return last_updated > last_scraped

    def scrape_investor_holdings(self, investor: Dict) -> List[Dict]:
        """
        Scrape holdings for a specific investor with full position details.

        Args:
            investor: Investor info dict

        Returns:
            List of holding dictionaries with structured data
        """
        fund_id = investor.get("fund_id")
        investor_name = investor.get("name")
        source_url = investor.get("source_url")

        if not fund_id or not source_url:
            logger.warning(f"Missing fund_id or source_url for {investor_name}")
            return []

        logger.info(f"Scraping {investor_name} ({fund_id}): {source_url}")

        try:
            response = self.session.get(source_url, timeout=30)
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
                    # 1: Stock link with "TICKER- Company Name"
                    # 2: Portfolio percentage
                    # 3: Recent activity
                    # 4: Shares

                    # Get the stock link from column 1
                    stock_link = cols[1].find('a')
                    if not stock_link:
                        continue

                    # Extract ticker from URL parameter
                    href = stock_link.get('href', '')
                    if 'sym=' in href:
                        ticker_raw = href.split('sym=')[-1].split('&')[0]
                    else:
                        # Fallback: extract from link text
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

                    # Portfolio percentage
                    portfolio_pct_text = cols[2].get_text(strip=True).replace('%', '').replace(',', '')
                    try:
                        portfolio_pct = float(portfolio_pct_text) if portfolio_pct_text else None
                    except ValueError:
                        portfolio_pct = None

                    # Shares held
                    shares_text = cols[4].get_text(strip=True).replace(',', '') if len(cols) > 4 else ''
                    try:
                        shares = int(shares_text) if shares_text and shares_text.isdigit() else None
                    except ValueError:
                        shares = None

                    # Activity (structured)
                    activity_text = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                    activity = self.parse_activity(activity_text)

                    holding = {
                        'ticker': ticker,
                        'ticker_raw': ticker_raw,
                        'company_name': company_name,
                        'investor': investor_name,
                        'fund_id': fund_id,
                        'portfolio_pct': portfolio_pct,
                        'shares': shares,
                        'activity': activity,
                        'activity_raw': activity_text,
                        'source_url': source_url
                    }

                    holdings.append(holding)
                    logger.debug(f"Extracted: {ticker} ({company_name}) - {activity['action']} {activity['percentage'] or ''}")

                except Exception as e:
                    logger.error(f"Error parsing row for {investor_name}: {e}")
                    continue

            logger.info(f"Scraped {len(holdings)} holdings for {investor_name}")

            # Update metadata
            self.investor_metadata.setdefault("investors", {})[fund_id] = {
                "name": investor_name,
                "last_updated_on_site": investor.get("last_updated"),
                "last_scraped": datetime.utcnow().isoformat()
            }

            return holdings

        except requests.RequestException as e:
            logger.error(f"Failed to scrape {investor_name}: {e}")
            return []

        except Exception as e:
            logger.error(f"Unexpected error scraping {investor_name}: {e}")
            return []

        finally:
            time.sleep(2)  # Rate limiting

    def scrape_all_investors(self) -> List[Dict]:
        """
        Discover and scrape all investors with incremental logic.

        Returns:
            List of all holdings across all investors
        """
        # Step 1: Discover all investors dynamically
        investors = self.discover_investors()

        if not investors:
            logger.error("No investors discovered. Aborting scrape.")
            return []

        # Step 2: Filter to only investors needing update
        investors_to_scrape = []
        for inv in investors:
            if self.should_scrape_investor(inv):
                investors_to_scrape.append(inv)
            else:
                logger.info(f"Skipping {inv['name']} - no updates since last scrape")

        logger.info(f"Scraping {len(investors_to_scrape)}/{len(investors)} investors (incremental)")

        # Step 3: Scrape each investor
        all_holdings = []
        for i, investor in enumerate(investors_to_scrape, 1):
            logger.info(f"Progress: {i}/{len(investors_to_scrape)} - {investor['name']}")
            holdings = self.scrape_investor_holdings(investor)
            all_holdings.extend(holdings)
            time.sleep(2)  # Be respectful to the server

        # Step 4: Save metadata
        self.investor_metadata["last_full_scrape"] = datetime.utcnow().isoformat()
        self._save_metadata()

        logger.info(f"Total holdings scraped: {len(all_holdings)}")
        return all_holdings

    def get_discovered_investors(self) -> List[Dict]:
        """Return list of all discovered investors (for reporting)."""
        return self.discovered_investors

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


def scrape_dataroma(force_full_scrape: bool = False) -> List[Dict]:
    """
    Convenience function to scrape Dataroma holdings with dynamic discovery.

    Args:
        force_full_scrape: If True, scrape all investors regardless of last updated date

    Returns:
        List of holdings dictionaries
    """
    scraper = DataromaScraper(force_full_scrape=force_full_scrape)
    return scraper.scrape_all_investors()
