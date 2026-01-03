"""
Deduplicate stock tickers and merge duplicate entries.
"""
from typing import List, Dict
try:
    from src.utils.logger import setup_logger
except ModuleNotFoundError:
    from utils.logger import setup_logger

logger = setup_logger(__name__)


def deduplicate_tickers(tickers: List[str]) -> List[str]:
    """
    Remove duplicate tickers from a list.

    Args:
        tickers: List of ticker symbols (may contain duplicates)

    Returns:
        List of unique ticker symbols (sorted)
    """
    unique_tickers = sorted(list(set(t.upper() for t in tickers if t)))
    logger.info(f"Deduplicated {len(tickers)} tickers to {len(unique_tickers)} unique tickers")
    return unique_tickers


def merge_duplicate_entries(entries: List[Dict], key: str = 'ticker') -> List[Dict]:
    """
    Merge entries with the same ticker/key.

    For duplicate entries, this function:
    - Combines sources
    - Keeps the first occurrence's data as primary
    - Merges additional context

    Args:
        entries: List of entry dictionaries
        key: Key to use for deduplication (default: 'ticker')

    Returns:
        List of deduplicated entries
    """
    merged = {}

    for entry in entries:
        ticker = entry.get(key)
        if not ticker:
            continue

        ticker = ticker.upper()

        if ticker in merged:
            # Merge with existing entry
            existing = merged[ticker]

            # Combine sources
            if 'sources' in existing and 'sources' in entry:
                existing['sources'] = list(set(existing['sources'] + entry['sources']))

            # Merge dataroma data
            if 'dataroma_data' in entry:
                if 'dataroma_data' not in existing:
                    existing['dataroma_data'] = entry['dataroma_data']
                else:
                    # Combine investors
                    existing_investors = existing['dataroma_data'].get('investors', [])
                    new_investors = entry['dataroma_data'].get('investors', [])
                    existing['dataroma_data']['investors'] = list(set(existing_investors + new_investors))

            # Merge substack data
            if 'substack_data' in entry:
                if 'substack_data' not in existing:
                    existing['substack_data'] = entry['substack_data']
                else:
                    # Combine publications and articles
                    existing_pubs = existing['substack_data'].get('publications', [])
                    new_pubs = entry['substack_data'].get('publications', [])
                    existing['substack_data']['publications'] = list(set(existing_pubs + new_pubs))

                    existing_urls = existing['substack_data'].get('article_urls', [])
                    new_urls = entry['substack_data'].get('article_urls', [])
                    existing['substack_data']['article_urls'] = list(set(existing_urls + new_urls))

                    # Keep the longer thesis
                    existing_thesis = existing['substack_data'].get('thesis', '')
                    new_thesis = entry['substack_data'].get('thesis', '')
                    if len(new_thesis) > len(existing_thesis):
                        existing['substack_data']['thesis'] = new_thesis

        else:
            # First occurrence
            merged[ticker] = entry.copy()

    logger.info(f"Merged {len(entries)} entries to {len(merged)} unique entries")
    return list(merged.values())
