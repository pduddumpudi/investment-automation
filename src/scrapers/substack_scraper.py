"""
Scrape Substack publications using Playwright for reading list discovery and RSS feeds for content.
"""
import feedparser
import time
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from src.processors.ticker_extractor import TickerExtractor
from src.utils.logger import setup_logger
from src.utils.config import config

logger = setup_logger(__name__)


class SubstackScraper:
    """Scrape Substack publications for investment ideas."""

    def __init__(self, reading_list_url: str = "https://substack.com/@prasadduddumpudi/reads", use_llm: bool = True):
        """
        Initialize the Substack scraper.

        Args:
            reading_list_url: URL of the Substack reading list
            use_llm: Whether to use LLM for ticker extraction
        """
        self.reading_list_url = reading_list_url
        self.ticker_extractor = TickerExtractor(use_llm=use_llm)

    def discover_publications_playwright(self) -> List[Dict[str, str]]:
        """
        Discover publications from Substack reading list using Playwright.

        Returns:
            List of publication dictionaries with name, url, and rss_feed
        """
        logger.info(f"Discovering publications from: {self.reading_list_url}")
        publications = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Navigate to reading list
                page.goto(self.reading_list_url, wait_until='networkidle', timeout=60000)

                # Wait for content to load
                time.sleep(3)

                # Scroll to load more publications (lazy loading)
                for _ in range(5):  # Scroll 5 times to load more content
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(1)

                # Extract publication links
                # Substack reading lists typically have publication links
                links = page.query_selector_all('a[href*="substack.com"]')

                seen_urls = set()
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if not href or href in seen_urls:
                            continue

                        # Filter for publication home pages
                        if 'substack.com' in href and '/p/' not in href and '/@' not in href:
                            # Extract publication name from URL
                            if href.startswith('http'):
                                publication_url = href.split('?')[0]  # Remove query params
                            else:
                                continue

                            # Get publication name from link text or URL
                            name = link.inner_text().strip() or publication_url.split('/')[-1]

                            publication = {
                                'name': name,
                                'url': publication_url,
                                'rss_feed': f"{publication_url}/feed"
                            }

                            publications.append(publication)
                            seen_urls.add(href)

                    except Exception as e:
                        logger.debug(f"Error extracting link: {e}")
                        continue

                browser.close()

            logger.info(f"Discovered {len(publications)} publications")
            return publications

        except PlaywrightTimeout:
            logger.error("Timeout while loading Substack reading list")
            return []

        except Exception as e:
            logger.error(f"Failed to discover publications: {e}")
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


def scrape_substack(reading_list_url: str = "https://substack.com/@prasadduddumpudi/reads",
                    use_cached: bool = True,
                    use_llm: bool = True) -> List[Dict]:
    """
    Convenience function to scrape Substack publications.

    Args:
        reading_list_url: URL of Substack reading list
        use_cached: Whether to use cached publications list
        use_llm: Whether to use LLM for ticker extraction

    Returns:
        List of article dictionaries
    """
    scraper = SubstackScraper(reading_list_url, use_llm=use_llm)

    # Try to load cached publications first
    publications = []
    if use_cached:
        publications = config.get_substack_publications()
        logger.info(f"Loaded {len(publications)} cached publications")

    # Discover new publications if cache is empty
    if not publications:
        logger.info("No cached publications found. Discovering from reading list...")
        publications = scraper.discover_publications_playwright()

        # Save to cache
        if publications:
            config.save_substack_publications(publications)
            logger.info("Saved publications to cache")

    if not publications:
        logger.error("No publications available to scrape")
        return []

    # Scrape articles from all publications
    articles = scraper.scrape_all_publications(publications)
    return articles
