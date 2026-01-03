# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Investment automation tool that aggregates stock ideas from superinvestor portfolios (Dataroma) and Substack publications, enriched with fundamental data from Yahoo Finance. Deployed on GitHub Pages with daily automated updates.

## Common Commands

### Development
```bash
# Run the full data pipeline
python src/main.py

# Force full scrape (ignore incremental updates)
python src/main.py --force

# Run tests
pytest tests/test_scrapers.py -v

# Verify setup
python verify_setup.py
```

### Local Testing
```bash
# Test dashboard locally
cd docs
python -m http.server 8000
# Visit http://localhost:8000

# Test with virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
playwright install chromium
```

### Deployment
```bash
# Manual workflow trigger
# Go to GitHub Actions → "Daily Investment Data Update" → Run workflow

# Build frontend (if using React version in docs-src/)
cd docs-src
npm ci
npm run build
```

## Architecture

### Data Pipeline Flow

```
DataromaScraper → Holdings →
SubstackScraper → Tickers → Deduplicator → yfinance → DataMerger → stocks.json
                                                                         ↓
                                                                   GitHub Pages
```

**Key orchestration:** `src/main.py` coordinates the entire pipeline in 5 steps:
1. Scrape Dataroma with dynamic investor discovery
2. Scrape Substack using Playwright + RSS
3. Deduplicate tickers from both sources
4. Fetch fundamentals from yfinance API
5. Merge and save to JSON/CSV

### Dynamic Investor Discovery

`DataromaScraper` (src/scrapers/dataroma_scraper.py) automatically discovers all investors on Dataroma instead of using hardcoded lists:
- Scrapes the managers page to find all available investors
- Implements incremental scraping: only fetches investors whose portfolios changed since last run
- Stores metadata in `data/investor_metadata.json` to track last updated dates
- Use `--force` flag to override incremental logic and scrape all investors

### Ticker Extraction Strategy

`TickerExtractor` (src/processors/ticker_extractor.py) uses a two-tier approach:
1. **Primary:** OpenAI GPT-4-mini for accurate extraction from article text
2. **Fallback:** Regex-based extraction if OPENAI_API_KEY not set
3. Maintains blacklist of false positives (USA, CEO, IPO, etc.)

### Ticker Normalization

Handles Dataroma edge cases where tickers use different formats:
- `.WS` (warrants) → `-WT` for Yahoo Finance compatibility
- `.A`, `.B` (share classes) → `-A`, `-B`
- Located in `dataroma_scraper.py:normalize_ticker()`

### Configuration Management

`Config` class (src/utils/config.py) provides centralized configuration:
- Paths: `base_dir`, `config_dir`, `data_dir`, `docs_dir`
- API keys: Loads from `.env` file via `python-dotenv`
- JSON configs: `dataroma_investors.json`, `substack_publications.json`

### Error Recovery

The pipeline includes multiple fallback mechanisms:
- If scraping fails, uses previous day's data from `data/stocks.json`
- Playwright timeout: Falls back to cached `config/substack_publications.json`
- yfinance rate limiting: Exponential backoff with 0.5s delays
- Missing fundamentals: Shows 'N/A' instead of breaking

## GitHub Actions Workflow

Located in `.github/workflows/daily-scrape.yml`:

**Schedule:**
- Daily at 10 AM UTC
- Additional run at 6 PM UTC during 13F filing periods (Feb, May, Aug, Nov 1-20)

**Steps:**
1. Install Python 3.11 and dependencies
2. Install Node.js 20 (for React frontend build if applicable)
3. Run scraper with optional `--force` flag
4. Copy data to `docs/data/`
5. Build frontend (if using docs-src React version)
6. Commit changes if data updated
7. Deploy to GitHub Pages
8. Create GitHub Issue on failure

**Environment Variables:**
- `OPENAI_API_KEY`: Optional secret for LLM-based ticker extraction

## Critical Files

- `src/main.py`: Main orchestration script (entry point)
- `src/scrapers/dataroma_scraper.py`: Dynamic investor discovery + incremental scraping
- `src/scrapers/substack_scraper.py`: Playwright automation + RSS parsing
- `src/scrapers/yfinance_scraper.py`: Fetch PE, PB, PEG ratios, 52-week ranges
- `src/processors/ticker_extractor.py`: LLM/regex ticker extraction
- `src/processors/data_merger.py`: Combines all sources into unified format
- `src/processors/deduplicator.py`: Remove duplicate tickers
- `data/stocks.json`: Main output consumed by dashboard
- `docs/index.html`: Dashboard UI (if static HTML) or build output (if React)

## Testing Approach

When modifying scrapers:
1. Test individual scraper in isolation first
2. Run full pipeline with `python src/main.py`
3. Verify `data/stocks.json` structure matches expected format
4. Test dashboard locally before deploying

Expected JSON structure:
```json
{
  "last_updated": "2026-01-03T10:00:00Z",
  "total_stocks": 150,
  "stocks": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "sources": ["dataroma", "substack"],
      "investor_count": 3,
      "aggregate_activity": "Buy",
      "fundamentals": {
        "pe_ratio": 28.5,
        "pb_ratio": 45.2,
        "peg_ratio": 2.1,
        ...
      },
      "dataroma_data": {
        "investors": [
          {
            "name": "Warren Buffett",
            "activity": "Buy",
            "portfolio_weight": 45.2
          }
        ]
      },
      "substack_data": {
        "articles": [...]
      }
    }
  ],
  "stats": {
    "dataroma_stocks": 120,
    "substack_stocks": 50,
    "both_sources": 20
  }
}
```

## Deployment Notes

**GitHub Pages Setup:**
- Source: `/docs` folder from `main` branch
- Requires public repository for free tier
- Workflow permissions must be set to "Read and write permissions"

**Cost Optimization:**
- GitHub Actions runs ~2-5 min per execution
- Free tier: 2000 min/month
- Current usage: ~60-150 min/month (daily runs)
- OpenAI costs: ~$0.01-0.10/month with GPT-4-mini

## Common Issues

**"No tickers found" error:**
- Check if `config/substack_publications.json` exists and has valid RSS feeds
- Verify OPENAI_API_KEY is set if using LLM extraction
- Check logs for scraping failures

**Playwright timeout:**
- Substack reading list may require authentication
- Manually create `config/substack_publications.json` with publication URLs

**yfinance rate limiting:**
- Pipeline includes exponential backoff
- If persistent, increase delay in `yfinance_scraper.py`

**Incremental scraping not working:**
- Check `data/investor_metadata.json` exists
- Use `--force` flag to override and scrape all investors

## When Modifying Code

**Adding new data source:**
1. Create new scraper in `src/scrapers/`
2. Return list of dicts with at minimum: `ticker`, `company_name`, `source`
3. Update `src/main.py` to call new scraper
4. Update `data_merger.py` to handle new source

**Adding new fundamental metric:**
1. Modify `yfinance_scraper.py:fetch_fundamentals()` to extract new field
2. Update dashboard frontend to display new metric
3. Update tests to verify new field

**Changing scraping schedule:**
- Edit `.github/workflows/daily-scrape.yml` cron expression
- Format: `minute hour day month weekday` (UTC timezone)

**Windows-specific considerations:**
- Use `venv\Scripts\activate` instead of `source venv/bin/activate`
- Playwright may require additional setup on Windows
- File paths use backslashes in Windows but code uses pathlib for cross-platform compatibility
