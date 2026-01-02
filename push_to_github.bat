@echo off

echo ================================================
echo PUSHING TO GITHUB
echo ================================================
echo.

cd /d "%~dp0"

echo [1/3] Adding remote repository...
git remote add origin https://github.com/prasadduddumpudi/investment-automation.git 2>nul
if errorlevel 1 (
    echo Remote already exists, updating URL...
    git remote set-url origin https://github.com/prasadduddumpudi/investment-automation.git
)

echo.
echo [2/3] Renaming branch to main...
git branch -M main

echo.
echo [3/3] Pushing code to GitHub...
git push -u origin main

if errorlevel 1 (
    echo.
    echo ================================================
    echo ERROR: Push failed!
    echo ================================================
    echo.
    echo Make sure you:
    echo 1. Created the repository on GitHub first
    echo 2. Are logged in to GitHub
    echo.
    echo If you need to log in, run: git config --global credential.helper wincred
    pause
    exit /b 1
)

echo.
echo ================================================
echo SUCCESS! Code pushed to GitHub
echo ================================================
echo.
echo Next steps:
echo 1. Go to https://github.com/prasadduddumpudi/investment-automation
echo 2. Follow DEPLOY_NOW.md to enable GitHub Pages
echo.
pause
