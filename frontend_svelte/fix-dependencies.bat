@echo off
REM Reinstall node_modules from scratch. Run this if module resolution breaks
REM after switching branches or editing dependencies.
REM
REM package-lock.json is deliberately NOT deleted. The lockfile is what makes a
REM local install match the one Netlify performs; throwing it away silently
REM upgrades every transitive dependency and turns "works on my machine" into a
REM build that cannot be reproduced. If you genuinely need to re-resolve the
REM tree, delete it yourself and commit the new lockfile as its own change.

echo Removing node_modules ...
if exist node_modules rmdir /s /q node_modules

echo Clearing npm cache ...
call npm cache clean --force

echo Reinstalling from package-lock.json ...
call npm ci
if errorlevel 1 goto failed

echo Done. Try "npm run dev" again.
goto end

:failed
echo.
echo npm ci failed. If package.json and package-lock.json are out of sync,
echo run "npm install" once and commit the updated lockfile.

:end
pause
