#!/bin/bash

echo "=== GITHUB LABELS ==="
gh label list 2>&1

echo ""
echo "=== PR TEMPLATE ==="
if [ -f .github/pull_request_template.md ]; then
    echo "Template found - will use 3 merged PRs for style reference"
    cat .github/pull_request_template.md
    echo ""
    echo "=== RECENT MERGED PRS (last 3) ==="
    gh pr list -L 3 --state merged --json number,title,body,labels,baseRefName 2>&1
else
    echo "No template found - will use 5 merged PRs for style reference"
    echo ""
    echo "=== RECENT MERGED PRS (last 5) ==="
    gh pr list -L 5 --state merged --json number,title,body,labels,baseRefName 2>&1
    echo ""
    echo "=== OPEN PRS (last 2) ==="
    gh pr list -L 2 --state open --json number,title,body,labels,baseRefName 2>&1
    echo ""
    echo "=== CLOSED PRS (last 2) ==="
    gh pr list -L 2 --state closed --json number,title,body,labels,baseRefName 2>&1
fi

echo ""
echo "=== CURRENT BRANCH ==="
git branch --show-current
