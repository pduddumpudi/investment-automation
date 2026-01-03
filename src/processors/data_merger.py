"""
Merge data from Dataroma, Substack, and yfinance into a unified format
with per-investor details and structured activity data.
"""
from typing import List, Dict, Optional
from datetime import datetime
try:
    from src.utils.logger import setup_logger
except ModuleNotFoundError:
    from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataMerger:
    """Merge investment data from multiple sources with rich per-investor details."""

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
        Add Dataroma holdings data with per-investor details.

        Args:
            holdings: List of holdings from Dataroma with structured activity
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
                    'dataroma_data': {
                        'investors': []
                    },
                    'substack_data': {
                        'mentions': []
                    }
                }

            # Add Dataroma source
            if 'Dataroma' not in self.stocks[ticker]['sources']:
                self.stocks[ticker]['sources'].append('Dataroma')

            # Create investor entry with full details
            investor_entry = {
                'name': holding.get('investor'),
                'fund_id': holding.get('fund_id'),
                'portfolio_pct': holding.get('portfolio_pct'),
                'shares': holding.get('shares'),
                'activity': holding.get('activity', {'action': 'Hold', 'percentage': None}),
                'activity_raw': holding.get('activity_raw', ''),
                'source_url': holding.get('source_url')
            }

            # Check if this investor is already in the list (avoid duplicates)
            existing_investors = self.stocks[ticker]['dataroma_data']['investors']
            if not any(inv['name'] == investor_entry['name'] for inv in existing_investors):
                existing_investors.append(investor_entry)

    def add_substack_data(self, articles: List[Dict]) -> None:
        """
        Add Substack articles data with publication details.

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
                        'company_name': ticker,
                        'sources': [],
                        'dataroma_data': {
                            'investors': []
                        },
                        'substack_data': {
                            'mentions': []
                        }
                    }

                # Add Substack source
                if 'Substack' not in self.stocks[ticker]['sources']:
                    self.stocks[ticker]['sources'].append('Substack')

                # Create mention entry
                mention_entry = {
                    'publication': article.get('publication_name'),
                    'article_title': article.get('title'),
                    'article_url': article.get('url'),
                    'thesis': article.get('summary', '')[:500],  # Limit thesis length
                    'published_date': article.get('published_date')
                }

                # Check for duplicates (same article URL)
                existing_mentions = self.stocks[ticker]['substack_data']['mentions']
                if not any(m['article_url'] == mention_entry['article_url'] for m in existing_mentions):
                    existing_mentions.append(mention_entry)

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
                logger.warning(f"Ticker {ticker} found in fundamentals but not in sources")
                continue

            # Build fundamentals object
            fundamentals_obj = {
                'pe_ratio': data.get('pe_ratio'),
                'forward_pe': data.get('forward_pe'),
                'pb_ratio': data.get('pb_ratio'),
                'peg_ratio': data.get('peg_ratio'),
                'week_52_high': data.get('week_52_high'),
                'week_52_low': data.get('week_52_low'),
                'current_price': data.get('current_price'),
                'previous_close': data.get('previous_close'),
                'market_cap': data.get('market_cap'),
                'insider_pct': data.get('insider_pct'),
                'institutional_pct': data.get('institutional_pct'),
                'sector': data.get('sector'),
                'industry': data.get('industry'),
                'country': data.get('country'),
                'currency': data.get('currency'),
                'exchange': data.get('exchange'),
                'is_international': data.get('is_international', False),
            }

            # Update stock entry
            self.stocks[ticker]['company_name'] = data.get('company_name', self.stocks[ticker].get('company_name', ticker))
            self.stocks[ticker]['fundamentals'] = fundamentals_obj

            # Determine if ETF
            quote_type = data.get('quote_type', 'EQUITY')
            sector = data.get('sector', '')

            if quote_type == 'ETF' or sector == '' or ticker in self._get_known_etfs():
                self.stocks[ticker]['stockanalysis_link'] = f"https://stockanalysis.com/etf/{ticker.lower()}/"
                self.stocks[ticker]['is_etf'] = True
            else:
                self.stocks[ticker]['stockanalysis_link'] = f"https://stockanalysis.com/stocks/{ticker.lower()}/"
                self.stocks[ticker]['is_etf'] = False

    def _get_aggregate_activity(self, investors: List[Dict]) -> str:
        """
        Determine aggregate activity across all investors.

        Priority: New > Buy > Add > Sell > Reduce > Hold
        """
        if not investors:
            return 'Hold'

        activity_priority = {
            'New': 6,
            'Buy': 5,
            'Add': 4,
            'Sell': 3,
            'Reduce': 2,
            'Hold': 1
        }

        highest_priority = 0
        highest_action = 'Hold'

        for inv in investors:
            activity = inv.get('activity', {})
            action = activity.get('action', 'Hold')
            priority = activity_priority.get(action, 1)

            if priority > highest_priority:
                highest_priority = priority
                highest_action = action

        return highest_action

    def get_merged_data(self) -> Dict:
        """
        Get the final merged dataset with new structure.

        Returns:
            Dictionary with merged stock data
        """
        stocks_list = []

        for ticker, stock in self.stocks.items():
            # Create clean stock entry
            stock_entry = {
                'ticker': stock['ticker'],
                'company_name': stock.get('company_name', ticker),
                'sources': stock['sources'],
                'dataroma_data': stock['dataroma_data'],
                'substack_data': stock['substack_data'],
                'fundamentals': stock.get('fundamentals', {}),
                'stockanalysis_link': stock.get('stockanalysis_link', f"https://stockanalysis.com/stocks/{ticker.lower()}/"),
                'is_etf': stock.get('is_etf', False),
                'thesis': None  # Populated on-demand via Perplexity
            }

            # Add aggregate activity for easy filtering
            investors = stock['dataroma_data'].get('investors', [])
            stock_entry['aggregate_activity'] = self._get_aggregate_activity(investors)
            stock_entry['investor_count'] = len(investors)

            # Add mention count
            mentions = stock['substack_data'].get('mentions', [])
            stock_entry['mention_count'] = len(mentions)

            # Replace None values with 'N/A' in fundamentals
            if stock_entry['fundamentals']:
                for key, value in stock_entry['fundamentals'].items():
                    if value is None:
                        stock_entry['fundamentals'][key] = 'N/A'

            stocks_list.append(stock_entry)

        # Calculate statistics
        dataroma_count = sum(1 for s in stocks_list if 'Dataroma' in s['sources'])
        substack_count = sum(1 for s in stocks_list if 'Substack' in s['sources'])
        both_count = sum(1 for s in stocks_list if 'Dataroma' in s['sources'] and 'Substack' in s['sources'])

        result = {
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'total_stocks': len(stocks_list),
            'stats': {
                'dataroma_stocks': dataroma_count,
                'substack_stocks': substack_count,
                'both_sources': both_count,
                'dataroma_only': dataroma_count - both_count,
                'substack_only': substack_count - both_count
            },
            'stocks': sorted(stocks_list, key=lambda x: x['ticker'])
        }

        logger.info(f"Merged data ready: {result['total_stocks']} stocks")
        logger.info(f"Stats: Dataroma={dataroma_count}, Substack={substack_count}, Both={both_count}")

        return result


def merge_all_data(dataroma_holdings: List[Dict],
                   substack_articles: List[Dict],
                   fundamentals: Dict[str, Dict]) -> Dict:
    """
    Convenience function to merge all data sources.

    Args:
        dataroma_holdings: Holdings from Dataroma (with structured activity)
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
