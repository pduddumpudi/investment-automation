"""
Scrape Substack publications using RSS feeds for content (no login required).
Supports full article content fetching, incremental scraping, and Google Sheets config.
"""
import feedparser
import requests
from bs4 import BeautifulSoup
import time
import json
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Set
try:
    from src.processors.ticker_extractor import TickerExtractor
    from src.utils.logger import setup_logger
    from src.utils.sheets_reader import get_substack_sources_from_sheets
except ModuleNotFoundError:
    from processors.ticker_extractor import TickerExtractor
    from utils.logger import setup_logger
    try:
        from utils.sheets_reader import get_substack_sources_from_sheets
    except ModuleNotFoundError:
        def get_substack_sources_from_sheets():
            return []

logger = setup_logger(__name__)

# Persistent article store path
ARTICLES_STORE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'data', 'substack_articles.json'
)


class SubstackScraper:
    """Scrape Substack publications for investment ideas using public RSS feeds."""

    # Paywall indicators in HTML
    PAYWALL_INDICATORS = [
        'paywall', 'subscribe to read', 'paid subscriber',
        'this post is for paid subscribers', 'upgrade to paid'
    ]

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
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.articles_store = self._load_articles_store()

    def _load_articles_store(self) -> Dict:
        """Load persistent article store."""
        if os.path.exists(ARTICLES_STORE_PATH):
            try:
                with open(ARTICLES_STORE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load articles store: {e}")
        return {"articles": {}, "last_updated": None}

    def _save_articles_store(self) -> None:
        """Save persistent article store."""
        os.makedirs(os.path.dirname(ARTICLES_STORE_PATH), exist_ok=True)
        try:
            self.articles_store["last_updated"] = datetime.utcnow().isoformat() + 'Z'
            with open(ARTICLES_STORE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.articles_store, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.articles_store['articles'])} articles to store")
        except Exception as e:
            logger.error(f"Failed to save articles store: {e}")

    @staticmethod
    def _url_hash(url: str) -> str:
        """Generate hash for URL to use as key."""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def _is_article_seen(self, url: str) -> bool:
        """Check if article URL has been seen before."""
        return self._url_hash(url) in self.articles_store.get("articles", {})

    def _get_stored_article(self, url: str) -> Optional[Dict]:
        """Get stored article by URL."""
        return self.articles_store.get("articles", {}).get(self._url_hash(url))

    def _store_article(self, article: Dict) -> None:
        """Store article in persistent store."""
        url_hash = self._url_hash(article['url'])
        self.articles_store.setdefault("articles", {})[url_hash] = article

    def load_publications_from_config(self) -> List[Dict[str, str]]:
        """
        Load publications list from config file or Google Sheets.

        Returns:
            List of publication dictionaries with name, url, and rss_feed
        """
        # Try Google Sheets first
        sheets_publications = get_substack_sources_from_sheets()
        if sheets_publications:
            logger.info(f"Loaded {len(sheets_publications)} publications from Google Sheets")
            return sheets_publications

        # Fall back to config file
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    publications = data.get('publications', [])
                    logger.info(f"Loaded {len(publications)} publications from config file")
                    return publications
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return []
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return []

    def _is_paywalled(self, html_content: str) -> bool:
        """Check if article content indicates paywall."""
        content_lower = html_content.lower()
        return any(indicator in content_lower for indicator in self.PAYWALL_INDICATORS)

    def fetch_full_article_content(self, url: str) -> Optional[str]:
        """
        Fetch full article content from URL.
        Only fetches free/public posts.

        Args:
            url: Article URL

        Returns:
            Full article text content or None if paywalled/failed
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Check for paywall
            if self._is_paywalled(response.text):
                logger.debug(f"Article is paywalled: {url}")
                return None

            # Find article body - Substack uses specific classes
            article_body = soup.find('div', class_='body')
            if not article_body:
                article_body = soup.find('article')
            if not article_body:
                article_body = soup.find('div', class_='post-content')

            if article_body:
                # Extract text, preserving some structure
                text = article_body.get_text(separator='\n', strip=True)
                # Limit to reasonable size
                return text[:15000]

            return None

        except Exception as e:
            logger.warning(f"Failed to fetch full content for {url}: {e}")
            return None

    def parse_rss_feed(self, publication: Dict[str, str], max_articles: int = 10) -> List[Dict]:
        """
        Parse RSS feed for a Substack publication with incremental scraping.

        Args:
            publication: Publication dictionary with rss_feed URL
            max_articles: Maximum number of articles to parse

        Returns:
            List of article dictionaries (new + previously stored)
        """
        rss_url = publication.get('rss_feed', '')
        if not rss_url:
            logger.warning(f"No RSS feed URL for {publication.get('name', 'unknown')}")
            return []

        logger.info(f"Parsing RSS feed: {rss_url}")

        try:
            feed = feedparser.parse(rss_url)

            if not feed.entries:
                logger.warning(f"No articles found in feed: {rss_url}")
                return []

            articles = []
            new_articles_count = 0

            for entry in feed.entries[:max_articles]:
                try:
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    summary = entry.get('summary', '')
                    published = entry.get('published', '')

                    if not link:
                        continue

                    # Check if we've already processed this article
                    stored = self._get_stored_article(link)
                    if stored:
                        # Use stored article data
                        articles.append(stored)
                        continue

                    # New article - fetch full content for free posts
                    full_content = self.fetch_full_article_content(link)
                    is_paywalled = full_content is None

                    # Use full content or summary for ticker extraction
                    content_for_extraction = full_content if full_content else f"{title}\n\n{summary}"

                    # Extract tickers from content
                    tickers = self.ticker_extractor.extract_tickers(content_for_extraction)

                    if not tickers:
                        logger.debug(f"No tickers found in article: {title}")
                        # Still store it to avoid re-fetching
                        article = {
                            'publication_name': publication['name'],
                            'publication_url': publication['url'],
                            'title': title,
                            'url': link,
                            'summary': summary[:500],
                            'full_content': full_content[:5000] if full_content else None,
                            'tickers': [],
                            'is_paywalled': is_paywalled,
                            'first_seen': datetime.utcnow().isoformat() + 'Z',
                            'published_date': published
                        }
                        self._store_article(article)
                        continue

                    article = {
                        'publication_name': publication['name'],
                        'publication_url': publication['url'],
                        'title': title,
                        'url': link,
                        'summary': summary[:500],
                        'full_content': full_content[:5000] if full_content else None,
                        'tickers': tickers,
                        'is_paywalled': is_paywalled,
                        'first_seen': datetime.utcnow().isoformat() + 'Z',
                        'published_date': published
                    }

                    # Store and add to results
                    self._store_article(article)
                    articles.append(article)
                    new_articles_count += 1
                    logger.info(f"Found article with tickers {tickers}: {title}")

                    # Rate limiting for full content fetches
                    time.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error parsing RSS entry: {e}")
                    continue

            logger.info(f"Parsed {len(articles)} articles from {publication['name']} ({new_articles_count} new)")
            return articles

        except Exception as e:
            logger.error(f"Failed to parse RSS feed {rss_url}: {e}")
            return []

    def scrape_all_publications(self, publications: List[Dict[str, str]]) -> List[Dict]:
        """
        Scrape articles from all publications with incremental logic.

        Args:
            publications: List of publication dictionaries

        Returns:
            List of article dictionaries with tickers
        """
        all_articles = []

        for pub in publications:
            articles = self.parse_rss_feed(pub)
            # Only include articles with tickers
            articles_with_tickers = [a for a in articles if a.get('tickers')]
            all_articles.extend(articles_with_tickers)
            time.sleep(1)  # Rate limiting between publications

        # Save article store
        self._save_articles_store()

        logger.info(f"Total articles with tickers: {len(all_articles)}")
        return all_articles

    def get_all_stored_articles_with_tickers(self) -> List[Dict]:
        """
        Get all stored articles that have tickers.

        Returns:
            List of article dictionaries with tickers
        """
        articles = []
        for article in self.articles_store.get("articles", {}).values():
            if article.get('tickers'):
                articles.append(article)
        return articles

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
