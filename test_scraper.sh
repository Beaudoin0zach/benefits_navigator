#!/bin/bash
# Quick test script for M21 scraper

set -e

echo "Testing M21 Scraper..."
echo ""

# Activate virtual environment
source venv/bin/activate

echo "1. Testing with one article (should take ~10 seconds)..."
python manage.py scrape_m21 --article-id 554400000181474

echo ""
echo "2. Checking if it worked..."
python manage.py shell << 'EOF'
from agents.models import M21ManualSection
count = M21ManualSection.objects.count()
if count > 0:
    section = M21ManualSection.objects.first()
    print(f"\n✓ Success! Found {count} section(s)")
    print(f"  Reference: {section.reference}")
    print(f"  Title: {section.title[:60]}...")
    print(f"  Content length: {len(section.content)} characters")
else:
    print("\n✗ No sections found - something went wrong")
EOF

echo ""
echo "Done! Check Django admin to view the scraped content:"
echo "  python manage.py runserver"
echo "  Visit: http://localhost:8000/admin"
