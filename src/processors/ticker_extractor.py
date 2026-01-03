"""
Extract stock tickers from text using LLM (preferred) or regex (fallback).
"""
import re
import os
from typing import List, Set
try:
    from src.utils.logger import setup_logger
except ModuleNotFoundError:
    from utils.logger import setup_logger

logger = setup_logger(__name__)


class TickerExtractor:
    """Extract stock tickers from article text using LLM or regex."""

    # Common false positives to exclude
    BLACKLIST = {
        'USA', 'CEO', 'CFO', 'IPO', 'SEC', 'ETF', 'LLC', 'INC', 'LTD',
        'COO', 'CTO', 'CIO', 'VP', 'SVP', 'EVP', 'GM', 'MD', 'UK',
        'EU', 'US', 'IT', 'AI', 'API', 'GDP', 'CPI', 'ESG', 'PE',
        'VC', 'MA', 'ROI', 'ROE', 'EPS', 'EBITDA', 'GAAP', 'FAQ',
        'PDF', 'CSV', 'JSON', 'XML', 'HTML', 'HTTP', 'HTTPS', 'FTP',
        'AWS', 'IBM', 'SAP', 'ERP', 'CRM', 'SaaS', 'PaaS', 'IaaS'
    }

    def __init__(self, use_llm: bool = True):
        """
        Initialize the ticker extractor.

        Args:
            use_llm: Whether to use LLM for extraction (recommended)
        """
        self.use_llm = use_llm and self._check_llm_available()

        if self.use_llm:
            logger.info("LLM-based ticker extraction enabled")
        else:
            logger.info("Using regex-based ticker extraction (fallback)")

    def _check_llm_available(self) -> bool:
        """Check if LLM API is available."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. Falling back to regex extraction.")
            return False

        try:
            import openai
            return True
        except ImportError:
            logger.warning("openai library not installed. Install with: pip install openai")
            return False

    def extract_tickers_llm(self, text: str) -> List[str]:
        """
        Extract stock tickers using LLM (most accurate).

        Args:
            text: Article or content text

        Returns:
            List of stock tickers
        """
        try:
            import openai

            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            prompt = f"""Extract all stock tickers mentioned in the following text.
Return ONLY the ticker symbols as a comma-separated list, with no additional text or explanation.
For example: AAPL, MSFT, GOOGL

If no tickers are found, return: NONE

Text:
{text[:3000]}  # Limit to first 3000 chars to avoid token limits
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective model
                messages=[
                    {"role": "system", "content": "You are a financial analyst assistant that extracts stock ticker symbols from investment articles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0  # Deterministic output
            )

            result = response.choices[0].message.content.strip()

            if result == "NONE" or not result:
                return []

            # Parse comma-separated tickers
            tickers = [t.strip().upper() for t in result.split(',')]

            # Filter out invalid tickers
            tickers = [t for t in tickers if self._is_valid_ticker(t)]

            logger.info(f"Extracted {len(tickers)} tickers using LLM: {tickers}")
            return tickers

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}. Falling back to regex.")
            return self.extract_tickers_regex(text)

    def extract_tickers_regex(self, text: str) -> List[str]:
        """
        Extract stock tickers using regex patterns (fallback).

        Args:
            text: Article or content text

        Returns:
            List of stock tickers
        """
        tickers: Set[str] = set()

        # Pattern 1: $TICKER format
        pattern1 = r'\$([A-Z]{1,5})\b'
        matches1 = re.findall(pattern1, text)
        tickers.update(matches1)

        # Pattern 2: (TICKER) or (NASDAQ:TICKER) format
        pattern2 = r'\((?:NASDAQ:|NYSE:|NYSEARCA:)?([A-Z]{1,5})\)'
        matches2 = re.findall(pattern2, text)
        tickers.update(matches2)

        # Pattern 3: Ticker: SYMBOL format
        pattern3 = r'(?:ticker|symbol):\s*([A-Z]{1,5})\b'
        matches3 = re.findall(pattern3, text, re.IGNORECASE)
        tickers.update([t.upper() for t in matches3])

        # Filter out blacklisted and invalid tickers
        tickers = {t for t in tickers if self._is_valid_ticker(t)}

        logger.info(f"Extracted {len(tickers)} tickers using regex: {tickers}")
        return list(tickers)

    def extract_tickers(self, text: str) -> List[str]:
        """
        Extract stock tickers from text using the configured method.

        Args:
            text: Article or content text

        Returns:
            List of stock tickers
        """
        if self.use_llm:
            return self.extract_tickers_llm(text)
        else:
            return self.extract_tickers_regex(text)

    def _is_valid_ticker(self, ticker: str) -> bool:
        """
        Validate if a string is likely a valid ticker.

        Args:
            ticker: Potential ticker symbol

        Returns:
            True if valid, False otherwise
        """
        if not ticker:
            return False

        # Must be 1-5 characters
        if not (1 <= len(ticker) <= 5):
            return False

        # Must be alphabetic
        if not ticker.isalpha():
            return False

        # Must not be in blacklist
        if ticker.upper() in self.BLACKLIST:
            return False

        return True
