#!/bin/bash
# Reinstall node_modules from scratch. Run this if module resolution breaks
# after switching branches or editing dependencies.
#
# package-lock.json is deliberately NOT deleted. The lockfile is what makes a
# local install match the one Netlify performs; throwing it away silently
# upgrades every transitive dependency and turns "works on my machine" into a
# build that cannot be reproduced. If you genuinely need to re-resolve the
# tree, delete it yourself and commit the new lockfile as its own change.
set -e

echo "Removing node_modules ..."
rm -rf node_modules

echo "Clearing npm cache ..."
npm cache clean --force

echo "Reinstalling from package-lock.json ..."
npm ci

echo "Done. Try 'npm run dev' again."
