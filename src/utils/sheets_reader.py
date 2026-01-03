"""
Read configuration from Google Sheets using public CSV export URLs.
No authentication required - sheets must be set to "Anyone with link can view".
"""
import os
import csv
import io
import requests
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, parse_qs

try:
    from src.utils.logger import setup_logger
except ModuleNotFoundError:
    from utils.logger import setup_logger

logger = setup_logger(__name__)


class SheetsReader:
    """Read configuration from Google Sheets CSV exports."""

    def __init__(self, timeout: int = 30):
        """
        Initialize the Sheets reader.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    @staticmethod
    def convert_to_csv_export_url(sheet_url: str, gid: str = "0") -> str:
        """
        Convert a Google Sheets URL to CSV export URL.

        Args:
            sheet_url: Original Google Sheets URL or spreadsheet ID
            gid: Sheet tab ID (0 for first tab)

        Returns:
            CSV export URL
        """
        # If already a CSV export URL, return as-is
        if 'export?format=csv' in sheet_url:
            return sheet_url

        # Extract spreadsheet ID from URL
        if 'docs.google.com/spreadsheets' in sheet_url:
            # Format: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/...
            parts = sheet_url.split('/d/')
            if len(parts) > 1:
                spreadsheet_id = parts[1].split('/')[0].split('?')[0]
            else:
                raise ValueError(f"Invalid Google Sheets URL: {sheet_url}")
        else:
            # Assume it's just the spreadsheet ID
            spreadsheet_id = sheet_url.strip()

        # Build CSV export URL
        csv_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
        return csv_url

    def fetch_csv(self, url: str) -> List[Dict[str, str]]:
        """
        Fetch and parse CSV from URL.

        Args:
            url: CSV URL (can be Google Sheets URL or direct CSV URL)

        Returns:
            List of dictionaries (one per row)
        """
        try:
            # Convert to CSV export URL if needed
            if 'docs.google.com/spreadsheets' in url and 'export?format=csv' not in url:
                url = self.convert_to_csv_export_url(url)

            logger.info(f"Fetching CSV from: {url[:80]}...")

            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Check if we got HTML instead of CSV (means sheet is not public)
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                logger.error("Received HTML instead of CSV. Make sure the sheet is set to 'Anyone with link can view'")
                return []

            # Parse CSV
            content = response.text
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)

            logger.info(f"Parsed {len(rows)} rows from CSV")
            return rows

        except requests.RequestException as e:
            logger.error(f"Failed to fetch CSV: {e}")
            return []
        except csv.Error as e:
            logger.error(f"Failed to parse CSV: {e}")
            return []

    def get_substack_sources(self, url: str) -> List[Dict[str, str]]:
        """
        Get Substack publication sources from Sheets.

        Expected columns: url (required)

        Args:
            url: Google Sheets URL or CSV export URL for Substack Sources tab

        Returns:
            List of publication dictionaries with url, name (auto-derived), rss_feed
        """
        rows = self.fetch_csv(url)
        publications = []

        for row in rows:
            # Get URL column (case-insensitive)
            pub_url = None
            for key in ['url', 'URL', 'Url', 'publication_url']:
                if key in row and row[key].strip():
                    pub_url = row[key].strip()
                    break

            if not pub_url:
                continue

            # Clean and validate URL
            if not pub_url.startswith('http'):
                pub_url = f"https://{pub_url}"

            # Derive publication name from URL
            # e.g., https://yetanothervalueblog.substack.com -> Yet Another Value Blog
            try:
                domain = urlparse(pub_url).netloc
                name = domain.split('.')[0]
                # Convert camelCase/lowercase to Title Case
                name = ''.join([' ' + c if c.isupper() else c for c in name]).strip()
                name = name.replace('-', ' ').replace('_', ' ').title()
            except Exception:
                name = pub_url

            # Build RSS feed URL
            if 'substack.com' in pub_url:
                # Standard Substack RSS format
                base_url = pub_url.rstrip('/')
                rss_feed = f"{base_url}/feed"
            else:
                rss_feed = f"{pub_url.rstrip('/')}/feed"

            publications.append({
                'name': name,
                'url': pub_url,
                'rss_feed': rss_feed
            })

        logger.info(f"Loaded {len(publications)} Substack sources from Sheets")
        return publications

    def get_alert_rules(self, url: str) -> List[Dict[str, Any]]:
        """
        Get alert rules from Sheets.

        Expected columns: rule_name, condition, email, enabled

        Args:
            url: Google Sheets URL or CSV export URL for Alert Rules tab

        Returns:
            List of alert rule dictionaries
        """
        rows = self.fetch_csv(url)
        rules = []

        for row in rows:
            # Get rule name
            rule_name = row.get('rule_name', row.get('Rule Name', row.get('name', ''))).strip()
            if not rule_name:
                continue

            # Get condition (formula)
            condition = row.get('condition', row.get('Condition', row.get('formula', ''))).strip()

            # Get email
            email = row.get('email', row.get('Email', row.get('recipient', ''))).strip()

            # Get enabled status
            enabled_str = row.get('enabled', row.get('Enabled', row.get('active', 'true'))).strip().lower()
            enabled = enabled_str in ('true', 'yes', '1', 'on')

            rules.append({
                'rule_name': rule_name,
                'condition': condition,
                'email': email,
                'enabled': enabled
            })

        logger.info(f"Loaded {len(rules)} alert rules from Sheets")
        return rules

    def get_settings(self, url: str) -> Dict[str, str]:
        """
        Get settings from Sheets.

        Expected columns: key, value

        Args:
            url: Google Sheets URL or CSV export URL for Settings tab

        Returns:
            Dictionary of settings
        """
        rows = self.fetch_csv(url)
        settings = {}

        for row in rows:
            key = row.get('key', row.get('Key', row.get('setting', ''))).strip()
            value = row.get('value', row.get('Value', '')).strip()

            if key:
                settings[key] = value

        logger.info(f"Loaded {len(settings)} settings from Sheets")
        return settings


def get_sheets_config() -> Dict[str, Any]:
    """
    Load all configuration from Google Sheets.

    Reads URLs from environment variables:
    - SHEETS_SUBSTACK_URL: URL for Substack Sources tab
    - SHEETS_ALERTS_URL: URL for Alert Rules tab
    - SHEETS_SETTINGS_URL: URL for Settings tab

    Or a single sheet URL with different gids:
    - SHEETS_URL: Base Google Sheets URL
    - SHEETS_SUBSTACK_GID: Tab ID for Substack Sources (default: 0)
    - SHEETS_ALERTS_GID: Tab ID for Alert Rules (default: 1)
    - SHEETS_SETTINGS_GID: Tab ID for Settings (default: 2)

    Returns:
        Dictionary with 'substack_sources', 'alert_rules', 'settings'
    """
    reader = SheetsReader()
    config = {
        'substack_sources': [],
        'alert_rules': [],
        'settings': {}
    }

    # Check for individual URLs first
    substack_url = os.getenv('SHEETS_SUBSTACK_URL')
    alerts_url = os.getenv('SHEETS_ALERTS_URL')
    settings_url = os.getenv('SHEETS_SETTINGS_URL')

    # Or use base URL with gids
    base_url = os.getenv('SHEETS_URL')

    if substack_url:
        config['substack_sources'] = reader.get_substack_sources(substack_url)
    elif base_url:
        gid = os.getenv('SHEETS_SUBSTACK_GID', '0')
        url = reader.convert_to_csv_export_url(base_url, gid)
        config['substack_sources'] = reader.get_substack_sources(url)

    if alerts_url:
        config['alert_rules'] = reader.get_alert_rules(alerts_url)
    elif base_url:
        gid = os.getenv('SHEETS_ALERTS_GID', '1')
        url = reader.convert_to_csv_export_url(base_url, gid)
        config['alert_rules'] = reader.get_alert_rules(url)

    if settings_url:
        config['settings'] = reader.get_settings(settings_url)
    elif base_url:
        gid = os.getenv('SHEETS_SETTINGS_GID', '2')
        url = reader.convert_to_csv_export_url(base_url, gid)
        config['settings'] = reader.get_settings(url)

    return config


def get_substack_sources_from_sheets() -> List[Dict[str, str]]:
    """
    Convenience function to get just Substack sources from Sheets.

    Returns:
        List of Substack publication dictionaries
    """
    substack_url = os.getenv('SHEETS_SUBSTACK_URL')
    base_url = os.getenv('SHEETS_URL')

    if not substack_url and not base_url:
        logger.info("No Sheets URL configured. Using local config file.")
        return []

    reader = SheetsReader()

    if substack_url:
        return reader.get_substack_sources(substack_url)
    elif base_url:
        gid = os.getenv('SHEETS_SUBSTACK_GID', '0')
        url = reader.convert_to_csv_export_url(base_url, gid)
        return reader.get_substack_sources(url)

    return []
