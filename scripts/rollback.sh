#!/bin/bash

# Rollback Helper Script
# Usage: ./scripts/rollback.sh <BAD_COMMIT_HASH>

if [ -z "$1" ]; then
  echo "Usage: $0 <BAD_COMMIT_HASH>"
  exit 1
fi

COMMIT_HASH=$1

echo "WARNING: This will revert commit $COMMIT_HASH on main and push immediately."
read -p "Are you sure? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "Switching to main..."
git checkout main
git pull origin main

echo "Reverting $COMMIT_HASH..."
git revert $COMMIT_HASH -m 1

echo "Pushing to origin..."
git push origin main

echo "Rollback pushed. Railway should redeploy shortly."
