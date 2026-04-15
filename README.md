# Yoga Kailasa

A full-stack Django platform for online yoga education, wellness practice, and community engagement.

## Features

- **Course Platform** — structured video lessons, progress tracking, PDF certificates on completion
- **Wellness Library** — yoga poses, breathing techniques (pranayama), mudras, guided meditations, chakra guide
- **Daily Practice Journal** — authenticated users log daily sessions with mood tracking, streak counter, and session history
- **Blog** — categories, tags, likes, comments; managed via admin
- **Payments** — Paystack inline checkout with webhook verification and duplicate-enrollment prevention
- **Community** — course discussion forums, lesson comments, course reviews
- **Notifications** — real-time in-app notification bell with unread count
- **Global Search** — live autocomplete across poses, breathing techniques, and courses
- **REST API** — versioned at `/api/v1/` with JWT auth and OpenAPI docs at `/api/v1/docs/`
- **Async Tasks** — Celery + Redis for emails, certificate generation, image optimisation
- **Branded Emails** — HTML enrollment confirmation, course completion (with PDF), booking confirmation, password reset

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2.3, Python 3.13 |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Task Queue | Celery 5.5.3 |
| Frontend | Tailwind CSS, Noto Serif + Manrope, Font Awesome |
| Rich Text | CKEditor 5 |
| Payments | Paystack |
| Static Files | WhiteNoise |
| API | Django REST Framework + drf-spectacular |
| PDF | ReportLab |
| Testing | pytest, hypothesis, factory-boy |

## Quick Start

```bash
# 1. Clone and set up environment
git clone <repo>
cd yoga_kailasa_project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your database credentials, SECRET_KEY, Paystack keys

# 4. Set up database
python manage.py migrate
python manage.py createsuperuser

# 5. Run development server
python manage.py runserver

# 6. Start Celery worker (separate terminal)
celery -A yoga_kailasa worker --loglevel=info
```

## Docker

```bash
docker-compose up --build
```

Starts PostgreSQL, Redis, Django (Gunicorn), and Celery worker with health checks.

## Testing

```bash
pytest --cov=yoga_app --cov-report=term-missing -x
```

Coverage threshold: 70% (enforced in CI).

## API Documentation

- Swagger UI: `/api/v1/docs/`
- ReDoc: `/api/v1/redoc/`
- OpenAPI schema: `/api/v1/schema/`

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Notes |
|---|---|
| `SECRET_KEY` | Required — raises RuntimeError if missing |
| `DEBUG` | `'true'` for dev, `'false'` for production |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `POSTGRES_*` | Database connection |
| `REDIS_URL` | Optional in dev (falls back to LocMemCache) |
| `PAYSTACK_SECRET_KEY` / `PAYSTACK_PUBLIC_KEY` | Payment processing |
| `SITE_URL` | Used in email links |
| `EXTRA_CSRF_TRUSTED_ORIGINS` | For tunnels like ngrok (include `https://`) |

## Project Documentation

See `Project_Documentation.md` for the complete technical reference including all models, URL patterns, services, tasks, and deployment details.

## License

MIT — see `LICENSE`.
