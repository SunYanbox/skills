#!/bin/bash

echo ""
echo "=== LAST 5 COMMITS ==="
git log -5 --pretty=format:"%h %s%n%n%b%n---" 2>&1

echo ""
echo "=== CURRENT BRANCH ==="
git branch --show-current
