# Investment Automation Tool

Automate your investment research by aggregating stock ideas from Dataroma (superinvestor portfolios) and Substack publications, enriched with fundamental ratios from Yahoo Finance.

## Features

- **Dataroma Scraping**: Track holdings from superinvestors (Warren Buffett, Bill Ackman, Seth Klarman, etc.)
- **Substack Integration**: Automatically discover and parse investment ideas from your Substack reading list
- **LLM-Powered Ticker Extraction**: Uses OpenAI GPT to accurately extract stock tickers from articles (with regex fallback)
- **Fundamental Data**: Fetch PE, PB, PEG ratios, 52-week ranges, insider holdings, and more from Yahoo Finance
- **Interactive Dashboard**: Beautiful, filterable table with export capabilities
- **Fully Automated**: Daily updates via GitHub Actions with $0/month hosting cost

## Live Demo

Once deployed, your dashboard will be available at:
```
https://<your-username>.github.io/investment-automation/
```

## Tech Stack

- **Backend**: Python 3.11 + BeautifulSoup4 + Playwright + yfinance
- **Ticker Extraction**: OpenAI GPT-4-mini (optional but recommended)
- **Frontend**: HTML/CSS/JavaScript + DataTables.js + Bootstrap 5
- **Deployment**: GitHub Actions (scheduling) + GitHub Pages (hosting)
- **Cost**: $0/month (100% free)

## Installation

### Prerequisites

- Python 3.11 or higher
- Git
- GitHub account
- (Optional) OpenAI API key for better ticker extraction

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/investment-automation.git
   cd investment-automation
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **(Optional) Set up OpenAI API key**
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

   Without this, the tool will use regex-based ticker extraction (less accurate but free).

6. **Run the scraper**
   ```bash
   python src/main.py
   ```

   This will:
   - Scrape Dataroma for investor holdings
   - Discover your Substack publications (requires browser automation)
   - Extract tickers from articles
   - Fetch fundamentals from Yahoo Finance
   - Generate `data/stocks.json` and `data/stocks.csv`

7. **View the dashboard locally**
   ```bash
   cd docs
   python -m http.server 8000
   ```

   Open http://localhost:8000 in your browser.

## GitHub Pages Deployment

### Setup

1. **Create a new GitHub repository**
   - Name it `investment-automation` (or any name you prefer)
   - Make it public (required for free GitHub Pages)

2. **Push your code**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Investment automation tool"
   git branch -M main
   git remote add origin https://github.com/<your-username>/investment-automation.git
   git push -u origin main
   ```

3. **Configure GitHub Pages**
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main`, Folder: `/docs`
   - Click Save

4. **Enable GitHub Actions**
   - Go to Settings → Actions → General
   - Workflow permissions: **Read and write permissions**
   - Click Save

5. **(Optional) Add OpenAI API key**
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key
   - Click "Add secret"

6. **Trigger first workflow run**
   - Go to Actions tab
   - Select "Daily Investment Data Update"
   - Click "Run workflow"
   - Wait 3-5 minutes for completion

7. **Access your dashboard**
   - Visit `https://<your-username>.github.io/investment-automation/`

## Configuration

### Dataroma Investors

Edit `config/dataroma_investors.json` to customize which investors to track:

```json
{
  "investors": [
    "Warren Buffett",
    "Bill Ackman",
    "Seth Klarman",
    "David Einhorn",
    "Mohnish Pabrai"
  ]
}
```

Available investors are defined in `src/scrapers/dataroma_scraper.py` (see `INVESTOR_IDS` mapping).

### Substack Publications

On first run, the tool will automatically discover your Substack reading list and cache it to `config/substack_publications.json`.

To manually configure:
```json
{
  "publications": [
    {
      "name": "Liberty's Highlights",
      "url": "https://libertyrpf.substack.com",
      "rss_feed": "https://libertyrpf.substack.com/feed"
    }
  ]
}
```

### Update Schedule

By default, the workflow runs daily at 10 AM UTC. To change:

Edit `.github/workflows/daily-scrape.yml`:
```yaml
on:
  schedule:
    - cron: '0 10 * * *'  # Change this cron expression
```

Cron format: `minute hour day month weekday`
- `0 10 * * *` = 10:00 AM UTC daily
- `0 */6 * * *` = Every 6 hours
- `0 0 * * 1` = Every Monday at midnight

## Project Structure

```
investment-automation/
├── .github/workflows/
│   └── daily-scrape.yml        # GitHub Actions workflow
├── src/
│   ├── main.py                 # Main orchestration script
│   ├── scrapers/
│   │   ├── dataroma_scraper.py # Dataroma scraping
│   │   ├── substack_scraper.py # Substack + Playwright
│   │   └── yfinance_scraper.py # Yahoo Finance API
│   ├── processors/
│   │   ├── ticker_extractor.py # LLM/regex ticker extraction
│   │   ├── data_merger.py      # Merge all sources
│   │   └── deduplicator.py     # Remove duplicates
│   └── utils/
│       ├── logger.py           # Logging setup
│       └── config.py           # Configuration management
├── data/
│   ├── stocks.json             # Output data (dashboard loads this)
│   ├── stocks.csv              # CSV export
│   └── metadata.json           # Update stats
├── docs/                       # GitHub Pages frontend
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── config/
│   ├── dataroma_investors.json
│   └── substack_publications.json
├── requirements.txt
└── README.md
```

## How It Works

### Data Pipeline

1. **Dataroma Scraper**
   - Fetches investor portfolio pages
   - Extracts tickers, buy/sell activity, portfolio weights
   - Handles edge cases like `.WS` warrants and share classes

2. **Substack Scraper**
   - Uses Playwright to discover publications from your reading list
   - Parses RSS feeds for each publication
   - Extracts tickers using LLM (OpenAI) or regex fallback
   - Captures investment thesis from article summaries

3. **Ticker Deduplication**
   - Combines tickers from both sources
   - Removes duplicates
   - Normalizes formats (e.g., `BRK.A` → `BRK-A`)

4. **Fundamental Data**
   - Fetches data from Yahoo Finance for all tickers
   - Includes: PE, PB, PEG ratios, 52-week high/low, insider holdings
   - Handles rate limiting with exponential backoff

5. **Data Merging**
   - Combines all sources into unified JSON format
   - Generates StockAnalysis.com links
   - Saves to `data/stocks.json`

6. **Frontend Display**
   - DataTables.js loads and displays the data
   - Color-coded PE ratios (green = low, red = high)
   - Sortable, filterable, exportable table
   - Responsive design for mobile

## Edge Cases Handled

- **Invalid Tickers**: Blacklist of false positives (USA, CEO, IPO, etc.)
- **Ticker Formats**: Normalizes `.WS`, `.A`, `.B` to Yahoo Finance format
- **Rate Limiting**: 0.5s delay + exponential backoff for yfinance
- **Missing Data**: Shows 'N/A' instead of breaking
- **Scraping Failures**: Falls back to previous day's data
- **No Tickers Found**: Skips articles without stock mentions
- **Playwright Failures**: Uses cached publication list as fallback

## Costs

| Component | Cost |
|-----------|------|
| GitHub Actions | $0 (2000 min/month free) |
| GitHub Pages | $0 (100GB bandwidth) |
| Yahoo Finance API | $0 (free, no key needed) |
| OpenAI API (optional) | ~$0.01-0.10/month |
| **Total** | **$0-0.10/month** |

## Troubleshooting

### "No tickers found"
- Check if OPENAI_API_KEY is set (for better extraction)
- Verify Substack publications exist in config
- Check logs in GitHub Actions for errors

### "Playwright timeout"
- Reading list may require login (currently not supported)
- Manually create `config/substack_publications.json` instead

### "Rate limiting from yfinance"
- Workflow will retry with exponential backoff
- If persistent, reduce number of tickers or increase delay

### "GitHub Actions quota exceeded"
- Free tier allows 2000 min/month
- Reduce scraping frequency or optimize code
- Consider upgrading to Pro ($4/month for 3000 min)

## Future Enhancements

- [ ] Twitter/X integration (requires $200/month API or risky scraping)
- [ ] Historical data tracking with database
- [ ] Email alerts for new high-conviction ideas
- [ ] Portfolio tracking (mark favorites)
- [ ] Sentiment analysis on thesis text
- [ ] Price alerts based on fundamentals
- [ ] Mobile app (Capacitor wrapper)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

**This tool is for informational purposes only and does not constitute financial advice.** Always do your own research before making investment decisions. The data provided may be incomplete, inaccurate, or outdated. Use at your own risk.

## Acknowledgments

- Data sources: [Dataroma](https://www.dataroma.com/), Substack publishers, [Yahoo Finance](https://finance.yahoo.com/)
- Built with: [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/), [Playwright](https://playwright.dev/), [yfinance](https://github.com/ranaroussi/yfinance), [DataTables](https://datatables.net/)

## Support

If you find this tool useful, please:
- ⭐ Star the repository
- 🐛 Report bugs via [Issues](https://github.com/<your-username>/investment-automation/issues)
- 💡 Suggest features via [Discussions](https://github.com/<your-username>/investment-automation/discussions)

---

**Happy Investing! 📈**
