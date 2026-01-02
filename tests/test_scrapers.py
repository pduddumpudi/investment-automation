"""
Basic tests for the scraper modules.
"""
import pytest
from src.processors.ticker_extractor import TickerExtractor
from src.scrapers.dataroma_scraper import DataromaScraper


class TestTickerExtractor:
    """Test ticker extraction functionality."""

    def test_regex_extraction_basic(self):
        """Test basic ticker extraction with regex."""
        extractor = TickerExtractor(use_llm=False)

        text = "I'm bullish on $AAPL and think MSFT (NASDAQ:MSFT) is undervalued"
        tickers = extractor.extract_tickers_regex(text)

        assert 'AAPL' in tickers
        assert 'MSFT' in tickers

    def test_blacklist_filtering(self):
        """Test that blacklisted words are filtered out."""
        extractor = TickerExtractor(use_llm=False)

        text = "The USA CEO discussed the IPO at the SEC"
        tickers = extractor.extract_tickers_regex(text)

        assert len(tickers) == 0

    def test_ticker_validation(self):
        """Test ticker validation logic."""
        extractor = TickerExtractor(use_llm=False)

        assert extractor._is_valid_ticker('AAPL') == True
        assert extractor._is_valid_ticker('USA') == False  # Blacklisted
        assert extractor._is_valid_ticker('ABCDEF') == False  # Too long
        assert extractor._is_valid_ticker('') == False  # Empty
        assert extractor._is_valid_ticker('123') == False  # Not alphabetic


class TestDataromaScraper:
    """Test Dataroma scraper functionality."""

    def test_ticker_normalization(self):
        """Test ticker normalization for edge cases."""
        assert DataromaScraper.normalize_ticker('BRK.WS') == 'BRK-WT'
        assert DataromaScraper.normalize_ticker('BRK.A') == 'BRK-A'
        assert DataromaScraper.normalize_ticker('BRK.B') == 'BRK-B'
        assert DataromaScraper.normalize_ticker('AAPL') == 'AAPL'

    def test_investor_id_lookup(self):
        """Test investor ID mapping."""
        scraper = DataromaScraper(['Warren Buffett'])

        assert scraper.get_investor_id('Warren Buffett') == 'BRK'
        assert scraper.get_investor_id('Bill Ackman') == 'pershing'
        assert scraper.get_investor_id('Unknown Investor') is None


def test_imports():
    """Test that all modules can be imported without errors."""
    from src.scrapers import dataroma_scraper
    from src.scrapers import substack_scraper
    from src.scrapers import yfinance_scraper
    from src.processors import ticker_extractor
    from src.processors import data_merger
    from src.processors import deduplicator
    from src.utils import logger
    from src.utils import config

    assert True  # If we get here, all imports succeeded


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
