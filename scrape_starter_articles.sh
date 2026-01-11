#!/bin/bash
# Scrape starter M21 articles one at a time
# This is more reliable than bulk import

set -e

echo "================================================"
echo "Scraping M21 Starter Articles (One at a Time)"
echo "================================================"
echo ""

source venv/bin/activate

# Article IDs from starter_article_ids.json
articles=(
    "554400000181474"  # I.i.1.A - Duty to Notify
    "554400000181476"  # I.i.1.B - Due Process
    "554400000181477"  # I.i.2.A - Power of Attorney
    "554400000174869"  # II.iii.1.A - Applications
    "554400000174870"  # II.iii.1.B - Screening Applications
    "554400000174871"  # II.iii.1.C - Substantial Completeness
    "554400000174872"  # II.iii.2.A - Intent to File
    "554400000174873"  # II.iii.2.B - Supplemental Claims
)

total=${#articles[@]}
success=0
failed=0

for i in "${!articles[@]}"; do
    article_id="${articles[$i]}"
    num=$((i + 1))

    echo "[$num/$total] Scraping article $article_id..."

    if python manage.py scrape_m21 --article-id "$article_id" 2>&1 | grep -q "Successful: 1"; then
        ((success++))
        echo "  ✓ Success"
    else
        ((failed++))
        echo "  ✗ Failed"
    fi

    echo ""

    # Small delay between articles
    sleep 2
done

echo "================================================"
echo "Scraping Complete!"
echo "================================================"
echo "Success: $success"
echo "Failed: $failed"
echo ""
echo "Check status: python check_m21_status.py"
echo "View in admin: python manage.py runserver"
