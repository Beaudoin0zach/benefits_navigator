#!/bin/bash
# M21 Scraper Installation Script
# Installs and configures the M21-1 web scraper

set -e  # Exit on error

echo "========================================="
echo "M21-1 Scraper Installation"
echo "========================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "   Please run: source venv/bin/activate"
    echo "   Then run this script again."
    exit 1
fi

echo "✓ Virtual environment detected: $VIRTUAL_ENV"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install playwright beautifulsoup4 lxml
echo "✓ Python packages installed"
echo ""

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium
echo "✓ Playwright chromium browser installed"
echo ""

# Run migrations
echo "🗄️  Creating database migrations..."
python manage.py makemigrations agents
echo ""

echo "🗄️  Applying migrations..."
python manage.py migrate
echo "✓ Database migrations complete"
echo ""

# Optional: Test scrape
echo "🧪 Would you like to test the scraper with one article? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Testing scraper with article 554400000181474..."
    python manage.py scrape_m21 --article-id 554400000181474
    echo ""
    echo "✓ Test scrape complete!"
fi

echo ""
echo "========================================="
echo "✓ Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Scrape starter articles:"
echo "   python manage.py scrape_m21 --import-from-file agents/data/starter_article_ids.json"
echo ""
echo "2. View scraped content in Django admin:"
echo "   python manage.py runserver"
echo "   Visit: http://localhost:8000/admin"
echo ""
echo "3. Read the full documentation:"
echo "   cat agents/M21_SCRAPER_README.md"
echo ""
echo "4. Discover more articles:"
echo "   python agents/discover_article_ids.py"
echo ""
echo "For help, see: agents/SETUP_GUIDE.md"
echo ""
