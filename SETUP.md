# Setup Guide

This guide covers Google Sheets configuration, manual run triggers, alerts, and thesis generation.

## 1) Google Sheets Admin UI

Create a single Google Sheet with three tabs and make it public:

1. Create a Google Sheet.
2. Share it as "Anyone with the link can view".
3. Create the following tabs and headers:

### Tab: Substack Sources
| url |
| --- |
| https://yetanothervalueblog.substack.com |

### Tab: Alert Rules
| rule_name | condition | email | enabled |
| --- | --- | --- | --- |
| Cross Source | =dataroma_count>=2 AND substack_count>=1 | you@example.com | TRUE |

### Tab: Settings
| key | value |
| --- | --- |
| price_alert_threshold | 10 |
| default_email | you@example.com |
| thesis_password | your-password |

### GitHub Secrets for Sheets

You can configure the scraper using either a single sheet URL + gids or per-tab URLs.

Option A (single sheet + gids):
- `SHEETS_URL` = full sheet URL
- `SHEETS_SUBSTACK_GID` = Substack Sources tab gid (default 0)
- `SHEETS_ALERTS_GID` = Alert Rules tab gid (default 1)
- `SHEETS_SETTINGS_GID` = Settings tab gid (default 2)

Option B (per-tab export URLs):
- `SHEETS_SUBSTACK_URL`
- `SHEETS_ALERTS_URL`
- `SHEETS_SETTINGS_URL`

Tip: You can copy the tab gid from the URL when viewing that tab in Sheets (`gid=123456`).

## 2) "Run Now" Button via Google Apps Script

Create a button in the sheet that triggers the GitHub Actions workflow.

1. In the sheet, go to Extensions -> Apps Script.
2. Add a new script and paste:

```javascript
const OWNER = 'pduddumpudi';
const REPO = 'investment-automation';
const WORKFLOW_FILE = 'daily-scrape.yml';

function runScrape() {
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT');
  if (!token) {
    throw new Error('Missing GITHUB_PAT script property.');
  }

  const url = `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;
  const payload = {
    ref: 'main',
    inputs: {
      force_scrape: 'false',
      skip_alerts: 'false',
    },
  };

  const response = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
    },
    payload: JSON.stringify(payload),
  });

  Logger.log(response.getResponseCode());
}
```

3. In Apps Script -> Project Settings -> Script Properties, add:
   - `GITHUB_PAT` = your GitHub token
4. Insert a drawing/button in Sheets and assign the `runScrape` script.

## 3) GitHub PAT for Apps Script

Create a fine-grained token with:
- Repository access to this repo.
- Permissions: Actions (write), Contents (read).

Store the token in Apps Script as `GITHUB_PAT`.

## 4) Resend Email Alerts

1. Sign up at https://resend.com and create an API key.
2. Add GitHub Secrets:
   - `RESEND_API_KEY`
   - `ALERT_EMAIL` (default recipient)
   - Optional: `RESEND_FROM_EMAIL` (defaults to `onboarding@resend.dev`)
3. If using a custom domain, verify it in Resend and set `RESEND_FROM_EMAIL`.

## 5) Thesis Generation (Perplexity + Vercel)

1. Deploy the repo on Vercel.
2. Add Vercel environment variables:
   - `PERPLEXITY_API_KEY`
   - `THESIS_PASSWORD`
3. The dashboard calls `/api/thesis` on the same domain.

## 6) Required GitHub Secrets (Scraper)

Required for scheduled runs:
- `OPENAI_API_KEY`
- `DASHBOARD_URL` (used in alert emails)
- Sheets secrets from section 1
- Resend secrets from section 4

Optional:
- `SHEETS_SUBSTACK_URL`, `SHEETS_ALERTS_URL`, `SHEETS_SETTINGS_URL` (instead of `SHEETS_URL` + gids)

## 7) Validate Locally

```bash
python src/main.py
cd docs-src
npm install
npm run build
```

