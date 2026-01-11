# VA Benefits Navigator - Start Here

**Last Updated:** 2026-01-11

## Quick Status

| Feature | Status |
|---------|--------|
| Document Upload & AI Analysis | ✅ Working |
| C&P Exam Guides (4 guides) | ✅ Working |
| VA Glossary (46 terms) | ✅ Working |
| Rating Calculator | ✅ Working |
| Appeals System | ✅ Working |
| **Journey Dashboard** | ✅ **Working** |
| User Dashboard | ✅ Working |
| Security (CSP, Rate Limiting, Audit Logging) | ✅ Working |
| **360 Tests Passing** | ✅ **All Green** |

---

## Start the App (30 seconds)

```bash
cd /Users/zachbeaudoin/benefits-navigator
docker compose up -d
```

**Verify it's running:**
```bash
curl -I http://localhost:8000/
# Should return: HTTP/1.1 200 OK
```

---

## Key URLs

| Page | URL |
|------|-----|
| Homepage | http://localhost:8000/ |
| **My Journey** | http://localhost:8000/journey/ |
| Rating Calculator | http://localhost:8000/exam-prep/rating-calculator/ |
| C&P Exam Guides | http://localhost:8000/exam-prep/ |
| VA Glossary | http://localhost:8000/exam-prep/glossary/ |
| Document Upload | http://localhost:8000/claims/ |
| Appeals | http://localhost:8000/appeals/ |
| Dashboard | http://localhost:8000/dashboard/ |
| Admin | http://localhost:8000/admin/ |

---

## New Feature: VA Rating Calculator

The rating calculator uses official VA Math to combine disability ratings:

**Features:**
- Accurate VA Math formula (38 CFR § 4.25)
- Bilateral factor for paired limbs (38 CFR § 4.26)
- 2024 compensation rates
- Step-by-step calculation explanation
- Save calculations (logged-in users)

**Example:**
```
50% PTSD + 30% Back + 20% Knee
= 50% + (30% × 50% remaining) + (20% × 35% remaining)
= 50% + 15% + 7%
= 72% → rounds to 70%
```

**Try it:** http://localhost:8000/exam-prep/rating-calculator/

---

## Common Commands

```bash
# View logs
docker compose logs -f web

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Load sample data
docker compose exec web python manage.py loaddata examprep/fixtures/glossary_terms.json
docker compose exec web python manage.py loaddata examprep/fixtures/additional_glossary_terms.json
docker compose exec web python manage.py loaddata examprep/fixtures/exam_guides.json

# Django shell
docker compose exec web python manage.py shell_plus

# Restart after code changes
docker compose restart web

# Rebuild after requirements.txt changes
docker compose build web && docker compose up -d
```

---

## Project Structure

```
benefits-navigator/
├── benefits_navigator/     # Django project settings
├── accounts/              # User auth, profiles
├── claims/                # Document upload, AI analysis
├── examprep/              # Exam guides, glossary, rating calculator
├── appeals/               # Appeals workflow
├── core/                  # Homepage, dashboard
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── docs/                  # Documentation
├── TODO.md                # Comprehensive task list
└── docker-compose.yml     # Docker configuration
```

---

## Documentation Files

| File | Purpose |
|------|---------|
| `TODO.md` | **Comprehensive task list** (start here for next steps) |
| `docs/PROJECT_STATUS.md` | Current state, what's built |
| `docs/DEVELOPMENT_SETUP.md` | Full setup guide |
| `docs/TROUBLESHOOTING.md` | Common issues and fixes |
| `README.md` | Technical architecture |

---

## Environment Variables

Required in `.env`:
```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://postgres:postgres@db:5432/benefits_navigator
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=sk-your-openai-key
DEBUG=True
```

---

## What's Next?

See `TODO.md` for full list. High priority items:

1. **Content** - Add TBI, Sleep Apnea exam guides
2. **Notifications** - Set up email reminders
3. **PDF Export** - Export rating calculations
4. **SMC Calculator** - Special Monthly Compensation

---

## Troubleshooting

**App won't start:**
```bash
docker compose down
docker compose up --build
```

**Database issues:**
```bash
docker compose exec web python manage.py migrate
```

**500 errors:**
```bash
docker compose logs web --tail=50
```

**OpenAI not working:**
- Check `.env` has valid `OPENAI_API_KEY`
- Restart: `docker compose restart web celery`

---

## Security Notes

The app has security hardening enabled:
- Content-Security-Policy headers
- Rate limiting on login (5/min), signup (3/hr)
- File validation via magic bytes + PDF page count
- Secure cookies in production
- Audit logging middleware (tracks sensitive operations)
- Security headers middleware (X-Frame-Options, X-Content-Type-Options, etc.)

---

## Need Help?

1. Check `docs/TROUBLESHOOTING.md`
2. View logs: `docker compose logs -f web`
3. Check `TODO.md` for known issues

---

**Ready to go!** Run `docker compose up -d` and visit http://localhost:8000/
