# Deployment Guide

Complete guide to deploy your investment automation tool to GitHub Pages with daily automation.

## Prerequisites Checklist

- [ ] GitHub account
- [ ] Git installed locally
- [ ] Python 3.11+ installed
- [ ] Project tested locally (ran `python src/main.py` successfully)
- [ ] (Optional) OpenAI API key from https://platform.openai.com/api-keys

## Deployment Steps

### 1. Prepare Your Repository

```bash
# Navigate to project directory
cd "C:\Users\Prasad Duddumpudi\Desktop\AI Projects\investment-automation"

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: Investment automation tool"
```

### 2. Create GitHub Repository

1. Go to https://github.com/new
2. Fill in:
   - Repository name: `investment-automation`
   - Description: "Automated investment research tool"
   - **Public** (required for free GitHub Pages)
   - **Do NOT** initialize with README/license/gitignore
3. Click "Create repository"

### 3. Push Code to GitHub

```bash
# Add remote (replace with your username)
git remote add origin https://github.com/prasadduddumpudi/investment-automation.git

# Push code
git branch -M main
git push -u origin main
```

### 4. Configure GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** (top right)
3. In left sidebar, click **Pages**
4. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/docs**
5. Click **Save**
6. GitHub will show: "Your site is ready to be published at https://<username>.github.io/investment-automation/"

### 5. Configure GitHub Actions

1. Still in Settings, go to **Actions** → **General** (left sidebar)
2. Scroll to "Workflow permissions"
3. Select **"Read and write permissions"**
4. Check **"Allow GitHub Actions to create and approve pull requests"**
5. Click **Save**

### 6. Add Secrets (Optional but Recommended)

For LLM-powered ticker extraction:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Add secret:
   - Name: `OPENAI_API_KEY`
   - Secret: Your OpenAI API key from https://platform.openai.com/api-keys
4. Click **"Add secret"**

**Note**: Without this, the tool will use regex extraction (less accurate but free).

### 7. Test the Workflow

1. Go to the **Actions** tab
2. Click on **"Daily Investment Data Update"** workflow (left sidebar)
3. Click **"Run workflow"** button (right side)
4. Select branch: **main**
5. Click **"Run workflow"** (green button)

Wait 3-5 minutes. The workflow will:
- Install Python and dependencies
- Install Playwright browser
- Run the scraper
- Commit data files
- Deploy to GitHub Pages

### 8. Monitor Workflow

1. Click on the running workflow to see real-time logs
2. Check each step:
   - ✅ Checkout repository
   - ✅ Set up Python
   - ✅ Install dependencies
   - ✅ Install Playwright browsers
   - ✅ Run scraper
   - ✅ Commit and push changes
   - ✅ Deploy to GitHub Pages

3. If any step fails:
   - Click on the failed step to see error logs
   - Common issues:
     - **Playwright timeout**: Try running manually again
     - **Permission denied**: Check workflow permissions in Settings
     - **No tickers found**: Check Dataroma/Substack configuration

### 9. Access Your Dashboard

After the workflow completes successfully:

1. Visit: `https://prasadduddumpudi.github.io/investment-automation/`
2. You should see your investment dashboard with data!

**Note**: First deployment may take 1-2 minutes for GitHub Pages to go live.

### 10. Verify Automation

The workflow will now run automatically **every day at 10 AM UTC**.

To verify:
1. Go to **Actions** tab
2. You should see the workflow listed under "workflows"
3. Next scheduled run will be shown

## Post-Deployment Configuration

### Change Update Schedule

Edit `.github/workflows/daily-scrape.yml`:

```yaml
on:
  schedule:
    - cron: '0 10 * * *'  # Current: 10 AM UTC daily
```

Examples:
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 1` - Every Monday at midnight
- `0 14 * * *` - Every day at 2 PM UTC

After editing, commit and push:
```bash
git add .github/workflows/daily-scrape.yml
git commit -m "Update workflow schedule"
git push
```

### Update Tracked Investors

Edit `config/dataroma_investors.json`:

```json
{
  "investors": [
    "Warren Buffett",
    "Bill Ackman",
    "Your custom investor"
  ]
}
```

Commit and push changes.

### Refresh Substack Publications

Delete `config/substack_publications.json` and the next run will auto-discover fresh publications.

## Monitoring & Maintenance

### Check Workflow Status

- Go to **Actions** tab to see recent runs
- Green checkmark = success
- Red X = failure (click to see logs)

### View Logs

1. Click on any workflow run
2. Click on "scrape-and-update" job
3. Expand steps to see detailed logs

### Email Notifications

GitHub will email you if a workflow fails (check spam folder).

### Manual Trigger

Anytime: Actions → Daily Investment Data Update → Run workflow

## Troubleshooting

### Issue: "Workflow not running"

**Solution**:
- Check Settings → Actions → Allow all actions
- Verify workflow permissions are set to "Read and write"
- Check `.github/workflows/daily-scrape.yml` exists

### Issue: "No data showing on dashboard"

**Solution**:
1. Check Actions tab for successful workflow run
2. Verify `data/stocks.json` exists in repository
3. Clear browser cache and reload
4. Check browser console for errors (F12)

### Issue: "Playwright browser not found"

**Solution**:
- The workflow should auto-install browsers
- Check logs for "Install Playwright browsers" step
- If fails, may need to upgrade Playwright version

### Issue: "OpenAI API errors"

**Solution**:
- Check API key is correct in Secrets
- Verify you have credits on OpenAI account
- Alternative: Remove the key to use free regex extraction

### Issue: "Rate limited by yfinance"

**Solution**:
- Workflow includes automatic retry logic
- If persistent, reduce number of tracked investors
- Or increase delay in `src/scrapers/yfinance_scraper.py`

## Cost Management

### Free Tier Limits

- **GitHub Actions**: 2,000 minutes/month
- **GitHub Pages**: 100GB bandwidth/month
- **Typical usage**: ~50 minutes/month (daily runs @ ~2 min each)

### If You Exceed Limits

1. **Reduce frequency**: Change cron to weekly instead of daily
2. **Optimize scraper**: Remove less important investors
3. **Upgrade**: GitHub Pro ($4/month) for 3,000 minutes

### OpenAI API Costs

- **Typical usage**: $0.01-0.10/month
- **To reduce costs**:
  - Remove API key (use regex instead)
  - Reduce number of Substack publications tracked
  - Use GPT-4-mini instead of GPT-4 (already configured)

## Updating Your Tool

```bash
# Pull latest changes
git pull origin main

# Make your changes
# ... edit files ...

# Commit and push
git add .
git commit -m "Update: description of changes"
git push

# Workflow will run automatically with new code
```

## Advanced: Custom Domain

1. Buy a domain (e.g., myinvestments.com)
2. In GitHub repo: Settings → Pages → Custom domain
3. Enter your domain: `myinvestments.com`
4. Update DNS settings with your domain registrar:
   - Add CNAME record pointing to `<username>.github.io`
5. Wait 24-48 hours for DNS propagation
6. Enable "Enforce HTTPS" in Pages settings

## Support

- **Documentation**: README.md and QUICKSTART.md
- **Issues**: https://github.com/prasadduddumpudi/investment-automation/issues
- **Logs**: Check GitHub Actions tab for detailed error messages

---

## Success Checklist

After deployment, verify:

- [ ] GitHub repository is public
- [ ] GitHub Pages is enabled (/docs folder)
- [ ] Workflow permissions set to "Read and write"
- [ ] First workflow run completed successfully
- [ ] Dashboard accessible at GitHub Pages URL
- [ ] Data is showing in the table
- [ ] Export buttons work (CSV/Excel)
- [ ] Table is sortable and filterable
- [ ] Next workflow is scheduled
- [ ] (Optional) OpenAI secret added
- [ ] (Optional) Custom domain configured

**Congratulations! Your investment automation tool is live! 🎉**
