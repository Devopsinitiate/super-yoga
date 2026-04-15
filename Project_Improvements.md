# Yoga Kailasa — Project Improvement Notes

> **Status:** All items from the original audit have been addressed.
> This document is kept for reference. See git history for implementation details.

---

## Completed Improvements

### Security
- [x] `DEBUG` fixed to proper boolean — production security headers now apply
- [x] `SECRET_KEY = None` raises `RuntimeError` at startup
- [x] Hardcoded ngrok URL removed — `EXTRA_CSRF_TRUSTED_ORIGINS` env var used instead
- [x] All `print()` debug statements replaced with `logging` across all files
- [x] `hmac.new()` webhook signature bug fixed in `payment_service.py`
- [x] Email backend is environment-driven — console in dev, SMTP in production
- [x] `ContentSecurityPolicyMiddleware` added — covers script, style, font, frame, img, connect sources
- [x] Rate limiting already applied to login, register, and comment endpoints via `django-ratelimit`

### Configuration
- [x] `STATICFILES_STORAGE` set to WhiteNoise `CompressedManifestStaticFilesStorage`
- [x] `drf-spectacular` wired up — OpenAPI docs at `/api/v1/docs/` and `/api/v1/redoc/`
- [x] `LOGGING` config added — structured log levels per environment
- [x] `.env.example` fully synced with all settings variables

### Models
- [x] `UserProfile.save()` double-save eliminated — uses `QuerySet.update()` for picture name
- [x] Recursive `post_save` signal fixed — no longer calls `profile.save()` on every `User.save()`
- [x] Image optimization moved to Celery task (`optimize_profile_picture_task`)
- [x] `Course.lessons` upgraded to `@cached_property` — DB hit once per instance
- [x] `Booking.user` FK added — bookings now linked to authenticated users (migration 0032)
- [x] `slugify` unused import removed from `models.py`

### Views & Business Logic
- [x] `enroll_free_course_view` now has `@login_required`
- [x] `initiate_payment_view` now has `@login_required`
- [x] Prev/next lesson uses ORM queries instead of loading all lessons into memory
- [x] `submit_course_review_view` form-error context now includes `modules` key
- [x] `booking_view` links booking to `request.user` when authenticated

### Templates
- [x] `yoga_app/static/css/design_tokens.css` — all design tokens extracted, loaded once in `base.html`
- [x] `yoga_app/static/yoga_app/js/kailasa.js` — shared CSRF, AJAX, like buttons, toasts, comment forms
- [x] `base_detail.html` intermediate template created
- [x] `padding: 0 !important` overrides removed from all detail page templates
- [x] Back buttons added/fixed across all detail pages
- [x] `read_time` template filter added — fixes broken `divisibleby` read time in `blog_detail.html`

### API
- [x] API versioned at `/api/v1/`
- [x] `ConsultantSerializer` split — contact details hidden from unauthenticated users
- [x] `BookingViewSet` and `ContactMessageViewSet` permissions tightened
- [x] `DEFAULT_SCHEMA_CLASS` set to `drf_spectacular.openapi.AutoSchema`

### Testing
- [x] `test_review_rating_validation` fixed — uses `full_clean()` and asserts `ValidationError`
- [x] `yoga_app/tests/test_views.py` created — view tests, auth flows, payment integration tests
- [x] `pytest.ini` — `--cov-fail-under=70` added, `view` marker registered
- [x] Legacy `tests.py` replaced with redirect comment
- [x] Celery task tests added with `unittest.mock.patch`

### Performance
- [x] `@cache_page` on `pose_list_view` (5 min), `breathing_list_view` (8 min), `course_list_view` (5 min, `vary_on_cookie`)
- [x] `UserProfileMiddleware` — attaches `request.user_profile` once per request
- [x] `context_processors.py` — uses `request.user_profile` from middleware, avoids second DB hit
- [x] `select_related` and `prefetch_related` added throughout views and services

### Code Quality
- [x] `yoga_app/tests.py` legacy file cleaned up
- [x] `yoga_app/views.py` is a thin re-export shim (legacy compatibility)
- [x] Type hints added to `enrollment_service.py` and `progress_service.py`
- [x] `tasks.py` — real retry logic, `DEFAULT_FROM_EMAIL`, no `time.sleep()` placeholders

### Admin
- [x] `ConsultantAdmin` — removed non-existent `icon_class` field reference
- [x] `BookingAdmin` — `user` field added to list display and fieldsets
- [x] `ContactMessageAdmin` — `is_read` in list display with `list_editable`
- [x] `TestimonialAdmin` — `is_approved` in `list_editable` for quick moderation

### DevOps
- [x] `Dockerfile` — multi-stage build, non-root user, `collectstatic` at build time
- [x] `docker-compose.yml` — web + db + redis + celery with health checks
- [x] `gunicorn.conf.py` — worker count, timeouts, logging, graceful restart
- [x] `.github/workflows/django-ci.yml` — Python 3.13, Redis service, pytest, Codecov
- [x] `/health/` endpoint added

---

## Remaining Considerations (Future Work)

These are architectural decisions that go beyond bug-fixing and require product decisions:

- **Settings split** — `settings/base.py` + `settings/development.py` + `settings/production.py` for cleaner environment separation
- **`Consultant.profile_picture_url`** — still a `URLField`; migrating to `ImageField` requires a data migration and storage decision
- **`image_url` fields on `YogaPose`/`BreathingTechnique`/`Course`** — same as above; URLField vs ImageField is a content management decision
- **Database connection pooling** — PgBouncer or `django-db-geventpool` for high-traffic production
- **Full-text search index** — PostgreSQL `SearchVectorField` with a trigger for automatic updates would replace the per-query `SearchVector` annotation
- **Certificate/completion emails** — `UserCourseCompletion` signal could trigger a congratulations email via Celery
