@echo off
echo ==============================================
echo  GitHub Authentication Reset Utility
echo ==============================================
echo.

echo Step 1: Removing old GitHub credentials...
cmdkey /delete:git:https://github.com >nul 2>&1
cmdkey /delete:github.com >nul 2>&1
echo ✅ Old credentials cleared.
echo.

echo Step 2: Enter your new GitHub credentials.
set /p GITUSER="GitHub Username: "
set /p GITPASS="Personal Access Token (PAT): "

echo.
echo Saving new credentials...
cmdkey /add:git:https://github.com /user:%GITUSER% /pass:%GITPASS%
echo ✅ Credentials saved securely to Windows Credential Manager.
echo.

echo Step 3: Testing authentication...
git ls-remote https://github.com/%GITUSER%/ai-log-analyzer.git >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Authentication successful!
) else (
    echo ❌ Authentication test failed.
    echo Please verify your username and token.
)
echo.
pause
