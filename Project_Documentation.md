# Yoga Kailasa — Complete Project Documentation

> Last updated: April 13, 2026. This document reflects the full current state of the codebase.

---

## 1. Project Overview

Yoga Kailasa is a full-stack Django web platform for online yoga education, wellness practice, and community engagement. It provides:

- A structured course platform with video lessons, progress tracking, and PDF certificates
- A wellness library covering yoga poses, breathing techniques (pranayama), mudras, guided meditations, chakra guide, and Kriya sessions
- A daily practice journal for authenticated users (tracks poses, breathing, mudras, meditations, and kriyas)
- A blog with categories, tags, likes, comments, and a frontend editor for authenticated users
- Paystack-powered course payments with duplicate-enrollment prevention
- A teacher/staff booking management portal
- A REST API (v1) with JWT authentication and OpenAPI documentation
- Asynchronous task processing via Celery + Redis (with synchronous fallback)
- Containerised deployment via Docker Compose

**Tech stack:**
- Backend: Django 5.2.3, Python 3.13
- Database: PostgreSQL 16
- Cache / Message broker: Redis 7
- Task queue: Celery 5.5.3
- Frontend: Tailwind CSS, Noto Serif + Manrope fonts, Font Awesome icons
- Rich text: CKEditor 5
- Payments: Paystack (inline JS + webhook)
- Static files: WhiteNoise
- API: Django REST Framework 3.15.2 + drf-spectacular (OpenAPI)
- PDF generation: ReportLab
- Testing: pytest, hypothesis (property-based), factory-boy

---

## 2. Repository Structure

```
yoga_kailasa_project/
├── yoga_kailasa/               # Django project package
│   ├── settings/               # Settings package (split by environment)
│   │   ├── __init__.py         # Auto-selects dev or production based on DJANGO_ENV
│   │   ├── base.py             # Shared settings for all environments
│   │   ├── development.py      # DEBUG=True, console email, LocMemCache
│   │   └── production.py       # DEBUG=False, Redis cache, SMTP, security headers
│   ├── urls.py                 # Root URL config
│   ├── wsgi.py
│   └── celery.py               # Celery app config
├── yoga_app/                   # Main application
│   ├── models.py               # All 28 models
│   ├── admin.py                # Admin registrations
│   ├── forms.py                # Django forms (incl. BlogPostForm)
│   ├── tasks.py                # Celery tasks
│   ├── middleware.py           # CSP + UserProfile middleware
│   ├── context_processors.py  # user_profile_processor
│   ├── validators.py           # PasswordComplexityValidator
│   ├── views/                  # Views split by domain
│   │   ├── __init__.py         # Re-export shim
│   │   ├── auth_views.py
│   │   ├── blog_views.py       # Includes frontend blog editor views
│   │   ├── booking_views.py
│   │   ├── content_views.py
│   │   ├── course_views.py
│   │   ├── discussion_views.py
│   │   ├── feedback_views.py
│   │   ├── payment_views.py
│   │   ├── search_views.py
│   │   ├── teacher_views.py    # Staff booking management portal
│   │   ├── user_views.py       # Includes certificate download view
│   │   └── wellness_views.py   # Mudras, meditations, chakras, daily practice, kriyas
│   ├── services/               # Business logic layer
│   │   ├── blog_service.py
│   │   ├── discussion_service.py
│   │   ├── enrollment_service.py
│   │   ├── notification_service.py
│   │   ├── payment_service.py
│   │   ├── progress_service.py
│   │   ├── report_service.py
│   │   ├── review_service.py
│   │   └── search_service.py   # Uses SearchVectorField + GIN index
│   ├── api/                    # REST API
│   │   ├── urls.py
│   │   ├── viewsets.py
│   │   └── serializers.py
│   ├── templatetags/
│   │   ├── app_filters.py      # Custom template filters
│   │   └── custom_filters.py
│   ├── utils/
│   │   ├── certificate.py      # ReportLab PDF certificate generator
│   │   ├── email.py            # send_html_email utility (supports attachments)
│   │   └── image_optimize.py  # Pillow image optimisation
│   ├── templates/yoga_app/     # All HTML templates
│   ├── static/                 # CSS, JS, images
│   └── tests/
│       ├── test_views.py
│       └── test_immediate_user_features.py
├── conftest.py                 # pytest fixtures
├── pytest.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── gunicorn.conf.py
└── .github/workflows/django-ci.yml
```

---

## 3. Data Models

### 3.1 User & Profile

**`UserProfile`** — extends Django's built-in `User` via OneToOne
| Field | Type | Notes |
|---|---|---|
| user | OneToOneField(User) | |
| enrolled_courses | M2M(Course) | Courses the user has paid for or enrolled in |
| last_viewed_lesson | FK(Lesson, null) | Resumes course from last position |
| profile_picture | ImageField | Auto-optimised via Celery on upload |
| bio | TextField | |
| date_of_birth | DateField | |
| phone_number | CharField | |
| address, city, country | CharField | |
| facebook/twitter/linkedin/instagram_profile | URLField | |
| receive_email_notifications | BooleanField | |
| receive_app_notifications | BooleanField | |

A `post_save` signal on `User` auto-creates a `UserProfile` on registration.

---

### 3.2 Yoga Content

**`YogaPose`**
| Field | Type |
|---|---|
| name | CharField (indexed) |
| sanskrit_name | CharField |
| difficulty | choices: Beginner / Intermediate / Advanced |
| description | CKEditor5Field |
| instructions | CKEditor5Field |
| image_url | URLField (legacy) |
| image | ImageField (upload_to='poses/') — takes priority over image_url |
| video_url | URLField |
| search_vector | SearchVectorField — auto-updated by PostgreSQL trigger |

`display_image` property returns uploaded image URL if set, else falls back to `image_url`.

**`BreathingTechnique`**
| Field | Type |
|---|---|
| name | CharField (unique, indexed) |
| sanskrit_name | CharField |
| description | CKEditor5Field |
| instructions | CKEditor5Field |
| duration | CharField |
| image_url | URLField (legacy) |
| image | ImageField (upload_to='breathing/') |
| video_url | URLField |
| search_vector | SearchVectorField — auto-updated by PostgreSQL trigger |

---

### 3.3 Courses

**`Course`**
| Field | Type | Notes |
|---|---|---|
| title | CharField | |
| description | CKEditor5Field | |
| instructor_name | CharField | |
| overview_content | CKEditor5Field | |
| price | DecimalField | `is_free` auto-set when price == 0 |
| duration | CharField | e.g. "4 weeks" |
| is_free | BooleanField | Auto-computed |
| includes | CKEditor5Field | |
| image_url | URLField (legacy) | |
| image | ImageField (upload_to='courses/') | Takes priority over image_url |
| is_popular | BooleanField | |
| start_date | DateField | |
| search_vector | SearchVectorField | Auto-updated by PostgreSQL trigger |

**`Module`** — belongs to Course, ordered
**`Lesson`** — belongs to Module, ordered; has `is_preview`, `video_url`, `resources_content`
**`UserLessonCompletion`** — tracks per-user lesson completion
**`UserCourseCompletion`** — tracks per-user course completion

---

### 3.4 Wellness Library

**`Mudra`** — sacred hand gestures
| Field | Type |
|---|---|
| name, sanskrit_name | CharField |
| difficulty | Beginner / Intermediate / Advanced |
| associated_chakra | root / sacral / solar_plexus / heart / throat / third_eye / crown / all |
| description, instructions, benefits | TextField |
| duration | CharField (e.g. "5–15 minutes") |
| image_url | URLField (legacy) |
| image | ImageField (upload_to='mudras/') |
| video_url | URLField |
| is_featured | BooleanField |

**`Meditation`** — guided meditation sessions
| Field | Type |
|---|---|
| title | CharField |
| category | morning / sleep / focus / healing / stress / gratitude / chakra / breathwork |
| difficulty | Beginner / Intermediate / Advanced |
| description, instructions, benefits | TextField |
| guided_by | CharField |
| duration_minutes | PositiveIntegerField |
| audio_url, video_url | URLField |
| image_url | URLField (legacy) |
| image | ImageField (upload_to='meditations/') |
| is_featured | BooleanField |

**`Chakra`** — the seven energy centres
| Field | Type |
|---|---|
| key | unique choice (root → crown) |
| name, sanskrit_name | CharField |
| number | 1–7 |
| color, color_hex | CharField |
| element, location, seed_mantra | CharField |
| description, signs_of_balance, signs_of_imbalance | TextField |
| image_url | URLField (legacy) |
| image | ImageField (upload_to='chakras/') |
| associated_poses | M2M(YogaPose) |
| associated_mudras | M2M(Mudra) |
| associated_breathing | M2M(BreathingTechnique) |

**`KriyaSession`** — structured practice sequences
| Field | Type |
|---|---|
| name, sanskrit_name | CharField |
| category | energising / cleansing / grounding / heart_opening / kundalini / morning / evening / healing / chakra |
| difficulty | Beginner / Intermediate / Advanced |
| description | CKEditor5Field |
| benefits | CKEditor5Field |
| duration_minutes | PositiveIntegerField |
| image_url | URLField (legacy) |
| image | ImageField (upload_to='kriyas/') |
| is_featured | BooleanField |

`step_count` property returns the number of steps in the sequence.

**`KriyaStep`** — a single ordered step within a KriyaSession
| Field | Type |
|---|---|
| kriya | FK(KriyaSession) |
| order | PositiveSmallIntegerField (unique per kriya) |
| step_type | pose / breathing / mudra / meditation |
| pose | FK(YogaPose, null) |
| breathing | FK(BreathingTechnique, null) |
| mudra | FK(Mudra, null) |
| meditation | FK(Meditation, null) |
| duration_seconds | PositiveIntegerField |
| repetitions | PositiveSmallIntegerField |
| instruction_note | CKEditor5Field |

`practice_element` property returns the actual linked object. `element_name` returns its display name. `duration_display` formats seconds as "Xm Ys".

**`DailyPractice`** — user's daily practice journal (one per user per day)
| Field | Type |
|---|---|
| user | FK(User) |
| date | DateField (unique with user) |
| mood_before, mood_after | 1–5 scale (Struggling → Radiant) |
| poses | M2M(YogaPose) |
| breathing_techniques | M2M(BreathingTechnique) |
| mudras | M2M(Mudra) |
| meditations | M2M(Meditation) |
| kriyas | M2M(KriyaSession) |
| duration_minutes | PositiveIntegerField |
| notes | TextField |

---

### 3.5 Community & Discussion

**`DiscussionTopic`** — thread within a course; supports likes (M2M), optional lesson link
**`DiscussionPost`** — reply within a topic; supports nested replies (parent_post FK) and likes
**`LessonComment`** — comment on a specific lesson
**`CourseReview`** — 1–5 star rating + comment per user per course

---

### 3.6 Blog

**`BlogPostCategory`** — name + slug
**`Tag`** — name + slug
**`BlogPost`** — title, slug, author (FK User), category, tags (M2M), excerpt, content (CKEditor5), featured_image (auto-optimised), is_published, likes (M2M User)
**`BlogComment`** — comment on a blog post

> Blog posts are created and published exclusively through the Django admin (`/admin/`). There is no frontend editor for regular users.

---

### 3.7 Transactions & Bookings

**`Payment`**
| Field | Notes |
|---|---|
| user, course | FK |
| amount | DecimalField |
| reference | unique UUID from Paystack |
| status | pending / success / failed / refunded |
| paid_at, verified_at | DateTimeField |

**`Booking`** — private session booking; linked to authenticated user (optional)

New fields added:
- `status` — pending / confirmed / cancelled / completed (default: pending)
- `teacher_notes` — private internal notes (not visible to student)
- `updated_at` — timestamp of last change

**`Consultant`** — name, specialty, bio (CKEditor5), profile_picture_url (legacy URLField), profile_picture (ImageField, upload_to='consultants/'), is_available, contact details

`display_picture` property returns uploaded image URL if set, else falls back to `profile_picture_url`.

---

### 3.8 Notifications & Feedback

**`Notification`** — types: reply, like, course_update, admin_message, blog_comment, blog_post_like, new_blog_post
**`Testimonial`** — public testimonials; requires `is_approved=True` to display
**`ContactMessage`** — contact form submissions; `is_read` flag for admin
**`NewsletterSubscription`** — email + `is_active` flag

---

## 4. URL Reference

### 4.1 Frontend Routes

| URL | View | Name |
|---|---|---|
| `/` | home_view | home |
| `/poses/` | pose_list_view | poses |
| `/poses/<id>/` | pose_detail_view | pose_detail |
| `/breathing/` | breathing_list_view | breathing |
| `/breathing/<id>/` | breathing_technique_detail_view | breathing_technique_detail |
| `/mudras/` | mudra_list_view | mudras |
| `/mudras/<id>/` | mudra_detail_view | mudra_detail |
| `/meditations/` | meditation_list_view | meditations |
| `/meditations/<id>/` | meditation_detail_view | meditation_detail |
| `/chakras/` | chakra_guide_view | chakra_guide |
| `/kriyas/` | kriya_list_view | kriyas |
| `/kriyas/<id>/` | kriya_detail_view | kriya_detail |
| `/practice/` | daily_practice_view | daily_practice |
| `/practice/log/` | log_practice_view | log_practice |
| `/courses/` | course_list_view | courses |
| `/courses/<id>/` | course_detail_view | course_detail |
| `/courses/<id>/content/` | course_content_view | course_content_base |
| `/courses/<id>/content/<lesson_id>/` | course_content_view | course_content |
| `/courses/<id>/review/submit/` | submit_course_review_view | submit_course_review |
| `/courses/complete/<id>/` | mark_course_complete_view | mark_course_complete |
| `/courses/<id>/lessons/<lesson_id>/complete/` | mark_lesson_complete_view | mark_lesson_complete |
| `/courses/<id>/discussion/` | course_discussion_list_view | course_discussion_list |
| `/courses/<id>/discussion/<topic_id>/` | discussion_topic_detail_view | course_discussion_detail |
| `/enroll/free/<id>/` | enroll_free_course_view | enroll_free_course |
| `/courses/initiate-payment/<id>/` | initiate_payment_view | initiate_payment |
| `/payments/verify/` | verify_payment_view | verify_payment |
| `/payments/webhook/paystack/` | paystack_webhook_view | paystack_webhook |
| `/blog/` | blog_list_view | blog_list |
| `/blog/new/` | create_blog_post_view | create_blog_post |
| `/blog/my-posts/` | my_blog_posts_view | my_blog_posts |
| `/blog/<slug>/` | blog_detail_view | blog_detail |
| `/blog/<slug>/edit/` | edit_blog_post_view | edit_blog_post |
| `/blog/<slug>/delete/` | delete_blog_post_view | delete_blog_post |
| `/blog/<slug>/comment/` | add_blog_comment_view | add_blog_comment |
| `/blog/<slug>/like/` | toggle_blog_post_like | toggle_blog_post_like |
| `/consultants/` | consultant_list_view | consultant_list |
| `/consultants/<id>/` | consultant_detail_view | consultant_detail |
| `/booking/` | booking_view | booking |
| `/dashboard/` | user_dashboard_view | dashboard |
| `/profile/edit/` | profile_update_view | profile_edit |
| `/notifications/` | all_notifications_view | all_notifications |
| `/notifications/api/` | get_notifications_api | get_notifications_api |
| `/search/` | global_search_view | global_search |
| `/register/` | register_view | register |
| `/login/` | CustomLoginView | login |
| `/logout/` | CustomLogoutView | logout |
| `/password_reset/` | PasswordResetView | password_reset |
| `/contact/` | contact_view | contact |
| `/about/` | about_view | about |
| `/privacy-policy/` | privacy_policy_view | privacy_policy |
| `/terms-of-service/` | terms_of_service_view | terms_of_service |
| `/certificate/<course_id>/` | download_certificate_view | download_certificate |
| `/teacher/bookings/` | teacher_dashboard_view | teacher_dashboard |
| `/teacher/bookings/<id>/` | booking_detail_view | teacher_booking_detail |
| `/teacher/bookings/<id>/status/` | update_booking_status_view | teacher_update_booking_status |
| `/request-report/` | request_report_view | request_report |
| `/health/` | health_check | health_check |
| `/admin/` | Django admin | — |

### 4.2 REST API Routes (`/api/v1/`)

| Endpoint | ViewSet | Notes |
|---|---|---|
| `courses/` | CourseViewSet | Read-only; filter by price/instructor/duration |
| `courses/<id>/enroll/` | CourseViewSet.enroll | POST, auth required |
| `courses/<id>/progress/` | CourseViewSet.progress | GET, auth required |
| `poses/` | YogaPoseViewSet | Filter by difficulty |
| `breathing/` | BreathingTechniqueViewSet | |
| `blog/` | BlogPostViewSet | Filter by category/tag; like/comment actions |
| `consultants/` | ConsultantViewSet | Contact details hidden for anonymous users |
| `notifications/` | NotificationViewSet | Auth required; mark_all_read action |
| `users/` | UserViewSet | Admin only |
| `profile/` | UserProfileViewSet | Auth required; dashboard/progress actions |
| `testimonials/` | TestimonialViewSet | Approved only |
| `bookings/` | BookingViewSet | Create requires auth |
| `contact/` | ContactMessageViewSet | Create public; list admin only |
| `search/global/` | SearchViewSet | Query param: `q`, `category` |
| `search/suggestions/` | SearchViewSet | |
| `auth/token/` | TokenObtainPairView | JWT login |
| `auth/token/refresh/` | TokenRefreshView | |
| `auth/token/verify/` | TokenVerifyView | |
| `schema/` | SpectacularAPIView | OpenAPI JSON |
| `docs/` | SpectacularSwaggerView | Swagger UI |
| `redoc/` | SpectacularRedocView | ReDoc UI |

---

## 5. Views Architecture

Views are split into domain-specific files under `yoga_app/views/`:

| File | Responsibility |
|---|---|
| `auth_views.py` | Registration, login, logout, email verification, password reset, account deletion |
| `blog_views.py` | Blog list, detail, comments, likes, frontend editor (create/edit/delete/my-posts) |
| `booking_views.py` | Session bookings, consultant list/detail |
| `content_views.py` | Pose list/detail, breathing list/detail |
| `course_views.py` | Course list/detail, content, enrollment, completion, reviews |
| `discussion_views.py` | Course discussion topics and posts (CRUD + likes) |
| `feedback_views.py` | Feedback form, newsletter, notifications, report requests |
| `payment_views.py` | Paystack payment initiation, verification, webhook |
| `search_views.py` | Global search, suggestions, about, privacy, terms |
| `teacher_views.py` | Staff-only booking management dashboard and detail view |
| `user_views.py` | User dashboard, profile editing, certificate download |
| `wellness_views.py` | Mudras, meditations, chakra guide, daily practice journal, kriya sessions |

---

## 6. Services Layer

Business logic is encapsulated in `yoga_app/services/`:

| Service | Key Responsibilities |
|---|---|
| `EnrollmentService` | Enroll free courses, check enrollment status, mark lessons/courses complete, update last viewed lesson |
| `PaymentService` | Initiate Paystack payment, verify payment, process webhook, enroll user after payment, HMAC signature verification |
| `ProgressService` | Calculate lesson/course completion percentages, get user dashboard data |
| `NotificationService` | Create and deliver in-app notifications |
| `SearchService` | Global search across poses, breathing techniques, and courses; autocomplete suggestions |
| `BlogService` | Blog post retrieval and filtering |
| `DiscussionService` | Discussion topic and post management |
| `ReviewService` | Submit/update course reviews, calculate average ratings |
| `ReportService` | Generate user activity reports |

---

## 7. Celery Tasks

All tasks use `bind=True` with retry logic. Redis is the broker and result backend.

| Task | Trigger | Retries |
|---|---|---|
| `send_enrollment_confirmation_email` | After free or paid enrollment | 3 × 60s |
| `send_course_completion_email` | After course marked complete; attaches PDF certificate | 3 × 60s |
| `send_booking_confirmation_email` | After booking created | 3 × 30s |
| `send_new_blog_post_notifications` | After blog post published | 2 × 120s |
| `send_newsletter_email` | Manual trigger | 3 × 60s |
| `generate_report_task` | User requests report | 2 × 120s |
| `optimize_profile_picture_task` | After profile picture upload | 2 × 10s |

**Fallback:** If Redis/Celery is unavailable, enrollment emails fall back to synchronous sending so enrollment is never blocked.

---

## 8. Email System

`yoga_app/utils/email.py` provides `send_html_email(subject, template, context, recipient, attachments=None)`:
- Renders an HTML template
- Strips tags for plain-text fallback
- Supports file attachments (list of `(filename, bytes, mimetype)` tuples)
- Returns `True` on success, `False` on failure (logs error)

**Email templates** (`yoga_app/templates/yoga_app/emails/`):
- `base_email.html` — branded base with gradient header, footer
- `enrollment_confirmation.html`
- `course_completion.html`
- `booking_confirmation.html`
- `new_blog_post.html`

**Password reset** uses Django's built-in flow with a custom branded HTML template at `registration/password_reset_email.html`.

---

## 9. PDF Certificate Generation

`yoga_app/utils/certificate.py` — `generate_certificate(user, course) -> bytes | None`

- A4 landscape (841 × 595 pt) PDF via ReportLab
- Brand colour `#855300`, double decorative border
- Includes: platform name, "Certificate of Completion", display name, course title, completion date, unique ID `YK-{user.id}-{course.id}`
- Returns `None` on failure (logs error); email is still sent without attachment

---

## 10. Payment Flow

1. User clicks "Enroll Now" on a paid course → POST to `initiate_payment_view`
2. View checks if user is already enrolled (blocks duplicate payment)
3. `PaymentService.initiate_payment()` creates a `Payment` record (status=pending) and returns Paystack config
4. Template renders Paystack inline popup with public key, amount (in kobo), reference
5. User completes payment in Paystack popup
6. JS callback redirects to `/payments/verify/?reference=<ref>`
7. `verify_payment_view` calls Paystack API to confirm; enrolls user; redirects to dashboard
8. Paystack also sends a webhook to `/payments/webhook/paystack/` — `process_webhook()` handles it as a backup
9. HMAC-SHA512 signature verification on all webhook requests

---

## 11. Middleware

### `ContentSecurityPolicyMiddleware`
Applied to all non-admin responses. Allows:
- Scripts: self, Paystack JS, cdnjs, YouTube, ytimg
- Styles: self, Google Fonts, cdnjs, Paystack
- Fonts: self, Google Fonts, cdnjs
- Frames: self, YouTube (www + no-www + nocookie), Paystack checkout
- Images: self, data:, https:, blob:
- Connect: self, Paystack API, YouTube, Google APIs
- Media: self, https:

Configurable via `CSP_EXTRA_SCRIPT_SRC` and `CSP_EXTRA_FRAME_SRC` settings.

### `UserProfileMiddleware`
Attaches `request.user_profile` for authenticated users — eliminates repeated DB queries in views and templates.

---

## 12. Custom Template Tags & Filters

**`app_filters`** (`{% load app_filters %}`):

| Filter | Usage |
|---|---|
| `split_lines` | `{{ text\|split_lines }}` — splits by `\n` for step-by-step lists |
| `ljust` | `{{ value\|ljust:5 }}` — pad string |
| `cut` | `{{ value\|cut:arg }}` — remove substring |
| `get_range` | `{{ rating\|get_range }}` — range for star loops |
| `multiply` | `{{ value\|multiply:arg }}` |
| `read_time` | `{{ content\|striptags\|read_time }}` — minutes to read |
| `embed_url` | `{{ video_url\|embed_url }}` — converts YouTube watch/shorts/youtu.be URLs to embed format |

**`custom_filters`** (`{% load custom_filters %}`):

| Filter | Usage |
|---|---|
| `add_class` | `{{ form.field\|add_class:"css-class" }}` |

---

## 13. Navigation Structure

The desktop navigation uses two dropdown menus to keep the bar compact:

- **Home** — direct link
- **Courses** — direct link
- **Practice ▾** — Poses, Breathing, Mudras, Meditation, Chakra Guide, Kriya Sessions, Practice Journal (auth only)
- **Explore ▾** — Consultants, Journal (Blog), Write a Post (auth only), Booking, Contact, About
- **Search bar** — live autocomplete
- **User avatar ▾** — Dashboard, My Profile, Practice Journal, Notifications, Manage Bookings (staff only), Request Report, Logout
- **Sign In / Sign Up** — for unauthenticated users

Mobile sidebar uses collapsible accordion sections for Practice and Explore.

---

## 14. Design System

The "Radiant Sanctuary" design system uses warm amber/parchment tones:

| Token | Value |
|---|---|
| `--rs-surface` | `#fff8f3` |
| `--rs-primary` | `#855300` |
| `--rs-secondary` | `#a73a00` |
| `--rs-primary-container` | `#f59e0b` |
| `--rs-on-surface` | `#1f1b14` |
| `--rs-on-surface-variant` | `#534434` |
| `--rs-outline` | `#867461` |

**Typography:** Noto Serif (headlines, `.rs-headline`) + Manrope (body)

**Key rules:**
- No 1px dividers — use tonal background shifts
- Gradient CTAs: `#855300` → `#f59e0b`
- Glassmorphism nav: 85% opacity + 20px backdrop-blur
- Ambient shadows: 32px+ blur at 6% opacity

---

## 15. Configuration & Environment Variables

All sensitive config is loaded from `.env` via `python-dotenv`.

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Raises RuntimeError if missing |
| `DEBUG` | Yes | `'true'` or `'false'` |
| `ALLOWED_HOSTS` | Yes | Comma-separated |
| `EXTRA_CSRF_TRUSTED_ORIGINS` | No | For tunnels (ngrok etc.) — must include `https://` |
| `POSTGRES_DB/USER/PASSWORD/HOST/PORT` | Yes | |
| `REDIS_URL` | No | Falls back to LocMemCache in dev |
| `PAYSTACK_SECRET_KEY` | Yes | |
| `PAYSTACK_PUBLIC_KEY` | Yes | |
| `PAYSTACK_WEBHOOK_URL` | No | |
| `SITE_URL` | No | Used in email links |
| `EMAIL_BACKEND` | No | Defaults to console |
| `EMAIL_HOST/PORT/USE_TLS/HOST_USER/HOST_PASSWORD` | No | SMTP config |
| `DEFAULT_FROM_EMAIL` | No | |
| `SECURE_SSL_REDIRECT` | No | Production only |
| `SESSION_COOKIE_SECURE` | No | Production only |
| `CSRF_COOKIE_SECURE` | No | Production only |

**Cache behaviour:**
- `DEBUG=true` → always `LocMemCache` (avoids Redis connection issues in dev)
- `DEBUG=false` + `REDIS_URL` set + Redis reachable → `RedisCache`

---

## 16. Testing

**Framework:** pytest + pytest-django

**Run tests:**
```bash
pytest --cov=yoga_app --cov-report=term-missing -x
```

**Coverage threshold:** 70% (enforced in CI)

**Test files:**
- `yoga_app/tests/test_views.py` — view tests, auth flows, payment integration
- `yoga_app/tests/test_immediate_user_features.py` — 31 tests covering:
  - Certificate content completeness (Property 1)
  - Attachment filename (Property 2)
  - Search result cards (Properties 3–5)
  - Password reset email (Properties 6–8)
  - Unit tests for edge cases

**Property-based testing:** Hypothesis with `max_examples=100`

**Fixtures:** `conftest.py` provides fixtures for User, UserProfile, Course, Module, Lesson, YogaPose, BreathingTechnique, BlogPost, Consultant, Booking, Payment, and more.

---

## 17. Deployment

### Docker Compose

```bash
docker-compose up --build
```

Services:
- `db` — PostgreSQL 16-alpine
- `redis` — Redis 7-alpine
- `web` — Django + Gunicorn (port 8000); runs `migrate` on startup
- `celery` — Celery worker (concurrency=2)

### Manual / Production

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn yoga_kailasa.wsgi:application --config gunicorn.conf.py

# In a separate process:
celery -A yoga_kailasa worker --loglevel=info
```

### CI/CD (GitHub Actions)

Triggers on push/PR to `main` and `develop`:
1. Spins up PostgreSQL 16 + Redis 7
2. Installs dependencies (Python 3.13, pip cache)
3. Runs migrations
4. Checks `collectstatic --dry-run`
5. Runs pytest with 70% coverage gate
6. Uploads coverage to Codecov
7. Emails team on failure

---

## 18. Security

- `SECRET_KEY` — raises `RuntimeError` at startup if missing
- CSRF protection on all forms; `CSRF_TRUSTED_ORIGINS` configurable via env
- `SECURE_PROXY_SSL_HEADER` enabled when `EXTRA_CSRF_TRUSTED_ORIGINS` is set (ngrok/proxy support)
- Production security headers: HSTS (1 year), `X-Frame-Options: DENY`, `Secure-Content-Type-Nosniff`, SSL redirect
- Content Security Policy via `ContentSecurityPolicyMiddleware`
- Rate limiting on login, register, and comment endpoints via `django-ratelimit`
- Paystack webhook HMAC-SHA512 signature verification
- Passwords: minimum 8 chars + `PasswordComplexityValidator`
- JWT tokens: 1-hour access, 7-day refresh with rotation

---

## 19. Blog Content Management

Any authenticated user can submit a blog post draft via `/blog/new/`. Submitted posts are saved with `is_published=False` and require staff review before going live. Staff users (`is_staff=True`) can publish posts directly from the edit form at `/blog/<slug>/edit/`.

Users manage their own posts at `/blog/my-posts/` — they can see draft/published status, edit, and delete their posts.

The Django admin at `/admin/yoga_app/blogpost/` remains available for full admin control.

---

## 20. Teacher Booking Management Portal

Staff users (`is_staff=True` or `is_superuser=True`) have access to a dedicated booking management portal:

- **`/teacher/bookings/`** — dashboard with stats (total, pending, confirmed, today, upcoming), search, status filter, date filter, and an inline status dropdown for quick updates via AJAX
- **`/teacher/bookings/<id>/`** — full booking detail with student info, session details, status selector, private teacher notes, and a mailto link to email the student directly

Booking statuses: `pending` → `confirmed` → `completed` / `cancelled`

Access is enforced via `@user_passes_test(is_staff)` — regular users are redirected to login.

---

## 21. Certificate Download

Completed courses show a gold certificate button on the user dashboard. Clicking it hits `/certificate/<course_id>/` which:
1. Verifies the user has a `UserCourseCompletion` record for that course
2. Calls `generate_certificate(user, course)` synchronously (no Celery needed)
3. Serves the PDF as a file download

The completion email also attaches the certificate. If Celery/Redis is unavailable, the email and certificate are sent synchronously as a fallback.

---

## 22. Full-Text Search Index

`YogaPose`, `BreathingTechnique`, and `Course` have a `search_vector` column (`SearchVectorField`) with a GIN index. A PostgreSQL trigger automatically updates this column on every INSERT/UPDATE — no manual maintenance required.

`SearchService` queries `search_vector=search_query` instead of building `SearchVector` on every request, making search significantly faster at scale.

---

## 23. Settings Architecture

Settings are split into a package at `yoga_kailasa/settings/`:

| File | When used |
|---|---|
| `base.py` | Shared by all environments |
| `development.py` | `DJANGO_ENV` not set or `development` — DEBUG=True, console email, LocMemCache |
| `production.py` | `DJANGO_ENV=production` — DEBUG=False, Redis cache, SMTP, full security headers |

`DJANGO_SETTINGS_MODULE` stays as `yoga_kailasa.settings` — the package `__init__.py` selects the right file automatically.

---

## 24. Known Limitations

- YouTube videos with embedding disabled (Error 153) show a fallback "Watch on YouTube" button — no code workaround exists for this restriction
- Database connection pooling (PgBouncer) not yet configured for high-traffic production


