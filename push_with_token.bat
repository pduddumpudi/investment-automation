@echo off
echo ================================================
echo PUSH TO GITHUB WITH PERSONAL ACCESS TOKEN
echo ================================================
echo.
echo This script will help you push to GitHub using a Personal Access Token.
echo.
echo If you don't have a token yet:
echo 1. Go to: https://github.com/settings/tokens/new
echo 2. Note: "Investment Automation Tool"
echo 3. Check: repo (full control)
echo 4. Click: Generate token
echo 5. Copy the token
echo.
echo ================================================

set /p TOKEN="Paste your GitHub Personal Access Token here: "

if "%TOKEN%"=="" (
    echo ERROR: No token provided!
    pause
    exit /b 1
)

cd /d "%~dp0"

echo.
echo Pushing to GitHub...
echo.

git push https://%TOKEN%@github.com/prasadduddumpudi/investment-automation.git main

if errorlevel 1 (
    echo.
    echo ================================================
    echo ERROR: Push failed!
    echo ================================================
    echo.
    echo Make sure:
    echo 1. You created the repository on GitHub
    echo 2. Your token has 'repo' permissions
    echo 3. The repository name is correct
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo SUCCESS! Code pushed to GitHub!
echo ================================================
echo.
echo Next steps:
echo 1. Go to: https://github.com/prasadduddumpudi/investment-automation
echo 2. Settings -^> Pages
echo 3. Source: Deploy from branch
echo 4. Branch: main, Folder: /docs
echo 5. Save
echo.
echo Then go to Settings -^> Actions -^> General
echo Set Workflow permissions to: Read and write
echo.
echo Your dashboard will be at:
echo https://prasadduddumpudi.github.io/investment-automation/
echo.
pause
