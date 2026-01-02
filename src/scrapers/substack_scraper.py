"""
Scrape Substack publications using RSS feeds for content (no login required).
"""
import feedparser
import time
import json
import os
from typing import List, Dict, Optional
from src.processors.ticker_extractor import TickerExtractor
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SubstackScraper:
    """Scrape Substack publications for investment ideas using public RSS feeds."""

    def __init__(self, use_llm: bool = True):
        """
        Initialize the Substack scraper.

        Args:
            use_llm: Whether to use LLM for ticker extraction
        """
        self.ticker_extractor = TickerExtractor(use_llm=use_llm)
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config', 'substack_sources.json'
        )

    def load_publications_from_config(self) -> List[Dict[str, str]]:
        """
        Load publications list from config file.

        Returns:
            List of publication dictionaries with name, url, and rss_feed
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    publications = data.get('publications', [])
                    logger.info(f"Loaded {len(publications)} publications from config")
                    return publications
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return []
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return []

    def parse_rss_feed(self, publication: Dict[str, str], max_articles: int = 10) -> List[Dict]:
        """
        Parse RSS feed for a Substack publication.

        Args:
            publication: Publication dictionary with rss_feed URL
            max_articles: Maximum number of articles to parse

        Returns:
            List of article dictionaries
        """
        rss_url = publication['rss_feed']
        logger.info(f"Parsing RSS feed: {rss_url}")

        try:
            feed = feedparser.parse(rss_url)

            if not feed.entries:
                logger.warning(f"No articles found in feed: {rss_url}")
                return []

            articles = []
            for entry in feed.entries[:max_articles]:
                try:
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    summary = entry.get('summary', '')

                    # Combine title and summary for ticker extraction
                    content = f"{title}\n\n{summary}"

                    # Extract tickers from content
                    tickers = self.ticker_extractor.extract_tickers(content)

                    if not tickers:
                        logger.debug(f"No tickers found in article: {title}")
                        continue

                    article = {
                        'publication_name': publication['name'],
                        'publication_url': publication['url'],
                        'title': title,
                        'url': link,
                        'summary': summary[:300],  # First 300 chars for thesis
                        'tickers': tickers
                    }

                    articles.append(article)
                    logger.info(f"Found article with tickers {tickers}: {title}")

                except Exception as e:
                    logger.error(f"Error parsing RSS entry: {e}")
                    continue

            logger.info(f"Parsed {len(articles)} articles from {publication['name']}")
            return articles

        except Exception as e:
            logger.error(f"Failed to parse RSS feed {rss_url}: {e}")
            return []

    def scrape_all_publications(self, publications: List[Dict[str, str]]) -> List[Dict]:
        """
        Scrape articles from all publications.

        Args:
            publications: List of publication dictionaries

        Returns:
            List of article dictionaries with tickers
        """
        all_articles = []

        for pub in publications:
            articles = self.parse_rss_feed(pub)
            all_articles.extend(articles)
            time.sleep(1)  # Rate limiting

        logger.info(f"Total articles with tickers: {len(all_articles)}")
        return all_articles

    def get_unique_tickers(self, articles: List[Dict]) -> List[str]:
        """
        Extract unique tickers from all articles.

        Args:
            articles: List of article dictionaries

        Returns:
            List of unique ticker symbols
        """
        tickers = set()
        for article in articles:
            tickers.update(article.get('tickers', []))

        return sorted(list(tickers))


def scrape_substack(use_llm: bool = True) -> List[Dict]:
    """
    Convenience function to scrape Substack publications using public RSS feeds.

    Args:
        use_llm: Whether to use LLM for ticker extraction

    Returns:
        List of article dictionaries
    """
    scraper = SubstackScraper(use_llm=use_llm)

    # Load publications from config file
    publications = scraper.load_publications_from_config()

    if not publications:
        logger.error("No publications configured. Add publications to config/substack_sources.json")
        return []

    # Scrape articles from all publications
    articles = scraper.scrape_all_publications(publications)
    return articles
