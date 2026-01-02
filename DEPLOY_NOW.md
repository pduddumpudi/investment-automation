# 🚀 Deploy Now - Step by Step

Your code is ready! Follow these exact steps to deploy:

## ✅ Pre-Deployment Status

- [x] Git repository initialized
- [x] All files committed
- [x] Code is ready to push

## 📋 Deployment Steps (5 minutes)

### Step 1: Create GitHub Repository (2 minutes)

1. **Open your browser** and go to: https://github.com/new

2. **Fill in the form:**
   - Repository name: `investment-automation`
   - Description: `Automated investment research tool - Tracks superinvestor portfolios and Substack ideas with LLM-powered analysis`
   - **IMPORTANT**: Select **Public** (required for free GitHub Pages)
   - **IMPORTANT**: Do NOT check any boxes (no README, no .gitignore, no license)

3. **Click** "Create repository"

### Step 2: Push Your Code (1 minute)

GitHub will show you commands. **Use these instead:**

```bash
cd "C:\Users\Prasad Duddumpudi\Desktop\AI Projects\investment-automation"

# Add your GitHub repository as remote
git remote add origin https://github.com/prasadduddumpudi/investment-automation.git

# Rename branch to main
git branch -M main

# Push your code
git push -u origin main
```

**Note**: You may be prompted to log in to GitHub. Use your credentials.

### Step 3: Enable GitHub Pages (1 minute)

1. On your GitHub repository page, click **Settings** (top right)

2. In the left sidebar, scroll down and click **Pages**

3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: Select **main**
   - Folder: Select **/docs**

4. Click **Save**

5. You'll see: "Your site is ready to be published at https://prasadduddumpudi.github.io/investment-automation/"

### Step 4: Configure GitHub Actions (1 minute)

1. Still in Settings, click **Actions** → **General** (left sidebar)

2. Scroll to "Workflow permissions"

3. Select: **"Read and write permissions"**

4. Check: **"Allow GitHub Actions to create and approve pull requests"**

5. Click **Save**

### Step 5: (Optional) Add OpenAI API Key

For better ticker extraction (recommended but optional):

1. In Settings, go to **Secrets and variables** → **Actions**

2. Click **"New repository secret"**

3. Add:
   - Name: `OPENAI_API_KEY`
   - Secret: Your OpenAI API key from https://platform.openai.com/api-keys

4. Click **"Add secret"**

**Skip this step** if you want to use free regex extraction instead (less accurate but $0 cost).

### Step 6: Run First Workflow (Free - takes 3-4 minutes)

1. Go to the **Actions** tab in your repository

2. Click **"Daily Investment Data Update"** (left sidebar)

3. Click **"Run workflow"** (right side)

4. Click the green **"Run workflow"** button

5. **Wait 3-4 minutes** - Watch the workflow run:
   - ✅ Install Python and dependencies
   - ✅ Install Playwright
   - ✅ Scrape Dataroma
   - ✅ Scrape Substack
   - ✅ Fetch fundamentals
   - ✅ Commit data
   - ✅ Deploy to GitHub Pages

### Step 7: Access Your Dashboard! 🎉

After the workflow completes:

**Visit:** https://prasadduddumpudi.github.io/investment-automation/

You should see your investment dashboard with live data!

**Note**: First deployment may take 1-2 additional minutes for GitHub Pages to go live.

---

## 🔄 What Happens Next?

### Automatic Daily Updates

Your dashboard will now **update automatically every day at 10 AM UTC** (3:30 PM IST).

No manual intervention needed! GitHub Actions will:
1. Run the scraper
2. Fetch new data
3. Update the dashboard
4. Email you if anything fails

### How to Check Status

- Go to **Actions** tab to see daily runs
- Green checkmark = success
- Red X = failure (click to see logs)

---

## 📊 Expected Results

After first run, you should see:
- **~50-100 stocks** from Dataroma investors
- **~20-50 stocks** from Substack articles
- **All fundamental ratios** populated
- **Interactive table** with sorting/filtering
- **Export buttons** working

---

## ⚙️ Customization (Optional)

### Change Tracked Investors

1. Edit `config/dataroma_investors.json` on GitHub
2. Add or remove investor names
3. Commit changes
4. Next run will use new list

### Change Update Schedule

1. Edit `.github/workflows/daily-scrape.yml`
2. Change the cron schedule line
3. Examples:
   - `0 */6 * * *` = Every 6 hours
   - `0 0 * * 1` = Every Monday
   - `0 14 * * *` = Daily at 2 PM UTC

---

## 🆘 Troubleshooting

### Issue: No data showing

**Solution:**
1. Check Actions tab for successful run
2. Wait 2-3 minutes after workflow completes
3. Hard refresh browser (Ctrl + Shift + R)

### Issue: Workflow failed

**Solution:**
1. Click on the failed workflow
2. Check error logs
3. Most common: Playwright timeout (just run again)

### Issue: "Permission denied" error

**Solution:**
1. Settings → Actions → General
2. Workflow permissions → "Read and write"
3. Save and run workflow again

---

## 🎯 Success Checklist

After completing all steps, verify:

- [ ] Repository created on GitHub
- [ ] Code pushed successfully
- [ ] GitHub Pages enabled (Settings → Pages)
- [ ] Workflow permissions set (Read/Write)
- [ ] First workflow run completed successfully
- [ ] Dashboard accessible at GitHub Pages URL
- [ ] Data is showing in the table
- [ ] Table is sortable and filterable
- [ ] Export buttons work

---

## 🎊 You're Done!

**Congratulations!** Your investment automation tool is now live at:

**https://prasadduddumpudi.github.io/investment-automation/**

It will update automatically every day with fresh data from:
- Warren Buffett, Bill Ackman, and other superinvestors (Dataroma)
- Your Substack publications
- Yahoo Finance fundamentals

**Total cost: $0/month** (or ~$0.01-0.10/month if using OpenAI API)

---

## 💡 Pro Tips

1. **Bookmark your dashboard** for easy access
2. **Star the repository** to find it easily later
3. **Check Actions tab weekly** to ensure daily runs are working
4. **Add more investors** in config to get more ideas

---

## 📞 Need Help?

- Check full documentation: `README.md`
- Review logs: Actions tab → Click on any run
- Test locally: `python src/main.py`

---

**Ready? Start with Step 1 above! 🚀**
