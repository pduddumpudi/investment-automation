#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verification script to check if the project is set up correctly.
Run this before deploying to catch any issues early.
"""
import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(path).exists():
        print(f"[OK] {description}: {path}")
        return True
    else:
        print(f"[MISSING] {description}: {path}")
        return False


def check_directory_exists(path: str, description: str) -> bool:
    """Check if a directory exists."""
    if Path(path).is_dir():
        print(f"[OK] {description}: {path}")
        return True
    else:
        print(f"[MISSING] {description}: {path}")
        return False


def verify_project_structure():
    """Verify all required files and directories exist."""
    print("=" * 80)
    print("INVESTMENT AUTOMATION TOOL - SETUP VERIFICATION")
    print("=" * 80)
    print()

    issues = []

    # Core directories
    print("[1/6] Checking core directories...")
    checks = [
        ("src", "Source code directory"),
        ("src/scrapers", "Scrapers directory"),
        ("src/processors", "Processors directory"),
        ("src/utils", "Utils directory"),
        ("docs", "Frontend directory"),
        ("docs/css", "CSS directory"),
        ("docs/js", "JavaScript directory"),
        ("config", "Config directory"),
        ("data", "Data directory"),
        ("tests", "Tests directory"),
        (".github/workflows", "GitHub workflows directory"),
    ]

    for path, desc in checks:
        if not check_directory_exists(path, desc):
            issues.append(f"Missing directory: {path}")
    print()

    # Python source files
    print("[2/6] Checking Python source files...")
    py_files = [
        ("src/main.py", "Main orchestration script"),
        ("src/scrapers/dataroma_scraper.py", "Dataroma scraper"),
        ("src/scrapers/substack_scraper.py", "Substack scraper"),
        ("src/scrapers/yfinance_scraper.py", "YFinance scraper"),
        ("src/processors/ticker_extractor.py", "Ticker extractor"),
        ("src/processors/data_merger.py", "Data merger"),
        ("src/processors/deduplicator.py", "Deduplicator"),
        ("src/utils/logger.py", "Logger utility"),
        ("src/utils/config.py", "Config utility"),
    ]

    for path, desc in py_files:
        if not check_file_exists(path, desc):
            issues.append(f"Missing Python file: {path}")
    print()

    # Frontend files
    print("[3/6] Checking frontend files...")
    frontend_files = [
        ("docs/index.html", "Dashboard HTML"),
        ("docs/css/style.css", "Custom CSS"),
        ("docs/js/app.js", "Dashboard JavaScript"),
    ]

    for path, desc in frontend_files:
        if not check_file_exists(path, desc):
            issues.append(f"Missing frontend file: {path}")
    print()

    # Configuration files
    print("[4/6] Checking configuration files...")
    config_files = [
        ("config/dataroma_investors.json", "Investors config"),
        ("requirements.txt", "Python dependencies"),
        (".github/workflows/daily-scrape.yml", "GitHub Actions workflow"),
        (".gitignore", "Git ignore file"),
    ]

    for path, desc in config_files:
        if not check_file_exists(path, desc):
            issues.append(f"Missing config file: {path}")
    print()

    # Documentation files
    print("[5/6] Checking documentation files...")
    doc_files = [
        ("README.md", "Main README"),
        ("QUICKSTART.md", "Quick start guide"),
        ("DEPLOYMENT.md", "Deployment guide"),
        ("PROJECT_SUMMARY.md", "Project summary"),
        ("LICENSE", "License file"),
    ]

    for path, desc in doc_files:
        if not check_file_exists(path, desc):
            issues.append(f"Missing documentation: {path}")
    print()

    # Python imports test
    print("[6/6] Testing Python imports...")
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src'))

        from scrapers import dataroma_scraper
        from scrapers import substack_scraper
        from scrapers import yfinance_scraper
        from processors import ticker_extractor
        from processors import data_merger
        from processors import deduplicator
        from utils import logger
        from utils import config

        print("[OK] All Python modules can be imported")
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        issues.append(f"Import error: {e}")
    print()

    # Summary
    print("=" * 80)
    if not issues:
        print("[SUCCESS] ALL CHECKS PASSED!")
        print()
        print("Your project is ready to deploy. Next steps:")
        print("1. Follow QUICKSTART.md for 10-minute setup")
        print("2. Or follow DEPLOYMENT.md for detailed deployment guide")
        print()
        print("Optional: Set up OpenAI API key in .env for better ticker extraction")
        print("  cp .env.example .env")
        print("  # Then edit .env and add your OPENAI_API_KEY")
        return True
    else:
        print(f"[ERROR] FOUND {len(issues)} ISSUE(S):")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("Please fix the issues above before deploying.")
        return False


if __name__ == '__main__':
    success = verify_project_structure()
    sys.exit(0 if success else 1)
