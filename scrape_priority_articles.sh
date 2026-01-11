#!/bin/bash
# Scrape high-priority M21 articles one at a time
# These are the most valuable sections for veterans claims assistance

set -e

echo "================================================"
echo "Scraping High-Priority M21 Articles"
echo "================================================"
echo ""

source venv/bin/activate

# High-priority article IDs
articles=(
    "554400000014119"  # III.ii.2.B - Service Treatment Records
    "554400000180494"  # IV.i.1.A - Medical Examinations
    "554400000180492"  # V.ii.4.A - Effective Dates
    "554400000177422"  # VIII.i.1.A - Herbicide Exposure
)

titles=(
    "Service Treatment Records (STRs)"
    "C&P Medical Examinations"
    "Effective Dates for Benefits"
    "Herbicide Exposure (Agent Orange)"
)

total=${#articles[@]}
success=0
failed=0

for i in "${!articles[@]}"; do
    article_id="${articles[$i]}"
    title="${titles[$i]}"
    num=$((i + 1))

    echo "[$num/$total] Scraping: $title"
    echo "  Article ID: $article_id"

    if python manage.py scrape_m21 --article-id "$article_id" 2>&1 | grep -q "Successful: 1"; then
        ((success++))
        echo "  ✓ Success"
    else
        ((failed++))
        echo "  ✗ Failed"
    fi

    echo ""

    # Delay between articles to avoid rate limiting
    if [ $i -lt $((total - 1)) ]; then
        echo "  Waiting 3 seconds before next article..."
        sleep 3
    fi
done

echo "================================================"
echo "Scraping Complete!"
echo "================================================"
echo "Success: $success"
echo "Failed: $failed"
echo "Total sections in database: $((7 + success))"
echo ""
echo "Check status: python check_m21_status.py"
echo "View in admin: python manage.py runserver"
