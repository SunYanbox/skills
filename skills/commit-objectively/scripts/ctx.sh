#!/bin/bash

echo ""
echo "=== LAST 5 COMMITS (FORMAT REFERENCE ONLY) ==="
echo "Use these solely as a style/format reference for the commit message."
echo "Do NOT copy, quote, or include any of this content in the generated commit message."
git log -5 --pretty=format:"%h %s%n%n%b%n---" 2>&1

echo ""
echo "=== CURRENT BRANCH ==="
git branch --show-current
