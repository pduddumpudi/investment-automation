# Quick Start Guide

Get your investment automation tool up and running in 10 minutes!

## Step 1: Setup Locally (5 minutes)

```bash
# Clone and navigate
cd "C:\Users\Prasad Duddumpudi\Desktop\AI Projects\investment-automation"

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# (Optional) Set up OpenAI API for better ticker extraction
# Copy .env.example to .env and add your API key
copy .env.example .env
# Then edit .env and add your OPENAI_API_KEY
```

## Step 2: Test Locally (2 minutes)

```bash
# Run the scraper
python src/main.py

# This will:
# - Scrape Dataroma (Warren Buffett, Bill Ackman, etc.)
# - Auto-discover your Substack publications
# - Fetch stock fundamentals
# - Generate data/stocks.json

# View the dashboard
cd docs
python -m http.server 8000
# Open http://localhost:8000 in your browser
```

## Step 3: Deploy to GitHub (3 minutes)

### 3.1 Create GitHub Repository

Go to https://github.com/new and create a new repository:
- Name: `investment-automation`
- Public (required for free GitHub Pages)
- Don't initialize with README

### 3.2 Push Code

```bash
# In your project directory
git init
git add .
git commit -m "Initial commit: Investment automation tool"
git branch -M main
git remote add origin https://github.com/prasadduddumpudi/investment-automation.git
git push -u origin main
```

### 3.3 Configure GitHub

1. **Enable GitHub Pages**
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main`, Folder: `/docs`
   - Save

2. **Enable Actions Write Permission**
   - Settings → Actions → General
   - Workflow permissions → **Read and write permissions**
   - Save

3. **(Optional) Add OpenAI API Key**
   - Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `OPENAI_API_KEY`
   - Value: Your API key
   - Save

### 3.4 Trigger First Run

- Go to Actions tab
- Click "Daily Investment Data Update"
- Click "Run workflow" → "Run workflow"
- Wait 3-5 minutes

### 3.5 Access Dashboard

Visit: `https://prasadduddumpudi.github.io/investment-automation/`

## Done! 🎉

Your dashboard is now live and will update automatically every day at 10 AM UTC.

## Next Steps

- **Customize investors**: Edit `config/dataroma_investors.json`
- **Add more Substack feeds**: Will auto-update from your reading list
- **Change schedule**: Edit `.github/workflows/daily-scrape.yml`
- **View logs**: GitHub → Actions → Recent workflow runs

## Troubleshooting

### No data showing?
- Check GitHub Actions logs for errors
- Verify workflow completed successfully
- Wait 2-3 minutes after workflow completes

### OpenAI API costs too much?
- Remove the API key - regex extraction will be used (free)
- Less accurate but works for most cases

### Want to track different investors?
- Edit `config/dataroma_investors.json`
- Available: Warren Buffett, Bill Ackman, Seth Klarman, David Einhorn, Mohnish Pabrai, Li Lu, Guy Spier, etc.
- See `src/scrapers/dataroma_scraper.py` for full list

## Support

Questions? Open an issue on GitHub or check the full README.md
