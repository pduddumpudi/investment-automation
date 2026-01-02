"""
Merge data from Dataroma, Substack, and yfinance into a unified format.
"""
from typing import List, Dict, Optional
from datetime import datetime
from src.utils.logger import setup_logger
from src.processors.deduplicator import deduplicate_tickers, merge_duplicate_entries

logger = setup_logger(__name__)


class DataMerger:
    """Merge investment data from multiple sources."""

    # Known ETFs that superinvestors hold
    KNOWN_ETFS = {
        'SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI', 'VEA', 'VWO', 'EFA', 'EEM',
        'GLD', 'SLV', 'TLT', 'IEF', 'LQD', 'HYG', 'XLF', 'XLK', 'XLE', 'XLV',
        'XLI', 'XLY', 'XLP', 'XLB', 'XLU', 'XLRE', 'XLC', 'VIG', 'VYM', 'SCHD',
        'ARKK', 'ARKG', 'ARKF', 'ARKW', 'ARKQ', 'IVV', 'IEFA', 'AGG', 'BND',
        'VNQ', 'VNQI', 'VGT', 'VHT', 'VFH', 'VDC', 'VIS', 'VAW', 'VDE', 'VPU'
    }

    def __init__(self):
        self.stocks = {}

    def _get_known_etfs(self):
        """Return set of known ETF tickers."""
        return self.KNOWN_ETFS

    def add_dataroma_data(self, holdings: List[Dict]) -> None:
        """
        Add Dataroma holdings data.

        Args:
            holdings: List of holdings from Dataroma
        """
        logger.info(f"Adding {len(holdings)} Dataroma holdings")

        for holding in holdings:
            ticker = holding.get('ticker')
            if not ticker:
                continue

            ticker = ticker.upper()

            if ticker not in self.stocks:
                self.stocks[ticker] = {
                    'ticker': ticker,
                    'company_name': holding.get('company_name', ticker),
                    'sources': [],
                    'dataroma_data': {},
                    'substack_data': {}
                }

            # Add Dataroma source
            if 'Dataroma' not in self.stocks[ticker]['sources']:
                self.stocks[ticker]['sources'].append('Dataroma')

            # Add or update Dataroma data
            if 'investors' not in self.stocks[ticker]['dataroma_data']:
                self.stocks[ticker]['dataroma_data']['investors'] = []

            investor = holding.get('investor')
            if investor and investor not in self.stocks[ticker]['dataroma_data']['investors']:
                self.stocks[ticker]['dataroma_data']['investors'].append(investor)

            # Keep track of activity
            activity = holding.get('activity', 'Hold')
            if 'activity' not in self.stocks[ticker]['dataroma_data']:
                self.stocks[ticker]['dataroma_data']['activity'] = activity
            elif activity != 'Hold':
                # Prioritize Buy/Sell over Hold
                self.stocks[ticker]['dataroma_data']['activity'] = activity

            # Store source URL
            if 'source_url' in holding:
                self.stocks[ticker]['dataroma_data']['source_url'] = holding['source_url']

    def add_substack_data(self, articles: List[Dict]) -> None:
        """
        Add Substack articles data.

        Args:
            articles: List of articles from Substack
        """
        logger.info(f"Adding {len(articles)} Substack articles")

        for article in articles:
            tickers = article.get('tickers', [])
            if not tickers:
                continue

            for ticker in tickers:
                ticker = ticker.upper()

                if ticker not in self.stocks:
                    self.stocks[ticker] = {
                        'ticker': ticker,
                        'company_name': ticker,  # Will be updated with yfinance data
                        'sources': [],
                        'dataroma_data': {},
                        'substack_data': {}
                    }

                # Add Substack source
                if 'Substack' not in self.stocks[ticker]['sources']:
                    self.stocks[ticker]['sources'].append('Substack')

                # Add or update Substack data
                if 'publications' not in self.stocks[ticker]['substack_data']:
                    self.stocks[ticker]['substack_data']['publications'] = []
                    self.stocks[ticker]['substack_data']['article_urls'] = []

                pub_name = article.get('publication_name')
                if pub_name and pub_name not in self.stocks[ticker]['substack_data']['publications']:
                    self.stocks[ticker]['substack_data']['publications'].append(pub_name)

                article_url = article.get('url')
                if article_url and article_url not in self.stocks[ticker]['substack_data']['article_urls']:
                    self.stocks[ticker]['substack_data']['article_urls'].append(article_url)

                # Use article summary as thesis (keep the longest one)
                summary = article.get('summary', '')
                existing_thesis = self.stocks[ticker]['substack_data'].get('thesis', '')
                if len(summary) > len(existing_thesis):
                    self.stocks[ticker]['substack_data']['thesis'] = summary

    def add_fundamentals(self, fundamentals: Dict[str, Dict]) -> None:
        """
        Add fundamental data from yfinance.

        Args:
            fundamentals: Dictionary mapping ticker to fundamentals
        """
        logger.info(f"Adding fundamentals for {len(fundamentals)} tickers")

        for ticker, data in fundamentals.items():
            ticker = ticker.upper()

            if ticker not in self.stocks:
                # Stock only found in fundamentals (shouldn't happen but handle it)
                logger.warning(f"Ticker {ticker} found in fundamentals but not in sources")
                continue

            # Update with fundamental data
            self.stocks[ticker].update({
                'company_name': data.get('company_name', self.stocks[ticker].get('company_name', ticker)),
                'pe_ratio': data.get('pe_ratio'),
                'forward_pe': data.get('forward_pe'),
                'pb_ratio': data.get('pb_ratio'),
                'peg_ratio': data.get('peg_ratio'),
                'week_52_high': data.get('week_52_high'),
                'week_52_low': data.get('week_52_low'),
                'insider_pct': data.get('insider_pct'),
                'institutional_pct': data.get('institutional_pct'),
                'market_cap': data.get('market_cap'),
                'current_price': data.get('current_price'),
                'sector': data.get('sector'),
                'industry': data.get('industry'),
                'country': data.get('country'),
            })

            # Add StockAnalysis link (ETFs use /etf/, stocks use /stocks/)
            # Check if it's an ETF based on certain indicators
            sector = data.get('sector', '')
            quote_type = data.get('quote_type', 'stock')

            if quote_type == 'ETF' or sector == '' or ticker in self._get_known_etfs():
                # Try ETF path first for securities without sector
                self.stocks[ticker]['stockanalysis_link'] = f"https://stockanalysis.com/etf/{ticker.lower()}/"
                self.stocks[ticker]['is_etf'] = True
            else:
                self.stocks[ticker]['stockanalysis_link'] = f"https://stockanalysis.com/stocks/{ticker.lower()}/"
                self.stocks[ticker]['is_etf'] = False

    def get_merged_data(self) -> Dict:
        """
        Get the final merged dataset.

        Returns:
            Dictionary with merged stock data
        """
        stocks_list = list(self.stocks.values())

        # Replace None values with 'N/A' for display
        for stock in stocks_list:
            for key, value in stock.items():
                if value is None and key not in ['dataroma_data', 'substack_data', 'sources']:
                    stock[key] = 'N/A'

        result = {
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'total_stocks': len(stocks_list),
            'stocks': sorted(stocks_list, key=lambda x: x['ticker'])
        }

        logger.info(f"Merged data ready: {result['total_stocks']} stocks")
        return result


def merge_all_data(dataroma_holdings: List[Dict],
                   substack_articles: List[Dict],
                   fundamentals: Dict[str, Dict]) -> Dict:
    """
    Convenience function to merge all data sources.

    Args:
        dataroma_holdings: Holdings from Dataroma
        substack_articles: Articles from Substack
        fundamentals: Fundamentals from yfinance

    Returns:
        Merged dataset dictionary
    """
    merger = DataMerger()

    if dataroma_holdings:
        merger.add_dataroma_data(dataroma_holdings)

    if substack_articles:
        merger.add_substack_data(substack_articles)

    if fundamentals:
        merger.add_fundamentals(fundamentals)

    return merger.get_merged_data()
