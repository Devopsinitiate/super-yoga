# Design Document — Immediate User Features

## Overview

Three self-contained improvements to the Yoga Kailasa Django platform:

1. **Certificate Generation** — a `generate_certificate` utility that produces a branded ReportLab PDF and attaches it to the existing `send_course_completion_email` Celery task.
2. **Search Page UI** — the `search_results.html` template already has a solid skeleton; this feature completes the results display, filter visibility logic, empty state, and responsive grid.
3. **Password Reset Email Styling** — a new `registration/password_reset_email.html` template that extends `base_email.html` and a matching plain-text file, wired into Django's built-in password reset flow.

All three features are additive: no existing models, URLs, or views need to change.

---

## Architecture

### Feature 1 — Certificate Generation

```
send_course_completion_email (Celery task)
  └─ generate_certificate(user, course) → bytes | None
       └─ ReportLab canvas API
  └─ send_html_email() + attach PDF bytes
```

The certificate generator is a pure function in `yoga_app/utils/certificate.py`. It takes a `User` and `Course` instance and returns raw PDF bytes (or `None` on error). The Celery task calls it, attaches the bytes to the `EmailMultiAlternatives` message, and falls back gracefully if generation fails.

`send_html_email` in `yoga_app/utils/email.py` currently builds and sends the message internally. To support an attachment we will add an optional `attachments` parameter — a list of `(filename, data, mimetype)` tuples — that gets passed to `EmailMultiAlternatives.attach()`.

### Feature 2 — Search Page UI

The view (`global_search_view`) and service (`SearchService.global_search`) are already complete and pass the correct context variables. The template already has the correct structure. The remaining work is:

- Ensure all result card fields are rendered (instructor name, price, duration for courses; difficulty badge and Sanskrit name for poses; Sanskrit name for breathing techniques).
- Ensure the "No results found" empty state with browse links is present.
- Ensure filter visibility JS correctly hides/shows difficulty and price selects based on category.
- Ensure the form preserves submitted filter values via `selected` attributes.
- Ensure result count appears in section headings.
- Ensure the grid is responsive (1 col mobile → multi-col desktop via Tailwind).

The template already satisfies most of these. The design confirms the current implementation is correct and documents what the template must contain.

### Feature 3 — Password Reset Email Styling

Django's built-in `PasswordResetView` renders `registration/password_reset_email.html` for the HTML body and `registration/password_reset_email.txt` (or the same template) for the plain-text body. We override both by placing templates in the project's template directory.

```
templates/
  registration/
    password_reset_email.html   ← extends base_email.html, HTML body
    password_reset_subject.txt  ← one-line subject (optional override)
```

Django's `PasswordResetForm.send_mail()` uses `EmailMultiAlternatives` when an HTML template is provided. We configure `PasswordResetView` in `urls.py` with `html_email_template_name='registration/password_reset_email.html'`.

---

## Components and Interfaces

### `yoga_app/utils/certificate.py` (new)

```python
def generate_certificate(user: User, course: Course) -> bytes | None:
    """
    Generate a branded PDF certificate using ReportLab.
    Returns raw PDF bytes on success, None on failure (logs error).
    """
```

Internal steps:
1. Resolve display name: `user.get_full_name() or user.username`
2. Build a unique identifier: `f"YK-{user.id}-{course.id}"`
3. Draw the PDF using `reportlab.pdfgen.canvas.Canvas` writing to a `BytesIO` buffer
4. Return `buffer.getvalue()`

### `yoga_app/utils/email.py` (modified)

Add optional `attachments: list[tuple[str, bytes, str]] | None = None` parameter to `send_html_email`. After `msg.attach_alternative(...)`, iterate attachments and call `msg.attach(filename, data, mimetype)`.

### `yoga_app/tasks.py` — `send_course_completion_email` (modified)

```python
from yoga_app.utils.certificate import generate_certificate

# inside the task, after building context:
pdf_bytes = generate_certificate(user, course)
attachments = [(f"certificate_{course.slug}.pdf", pdf_bytes, "application/pdf")] if pdf_bytes else []

send_html_email(
    ...,
    attachments=attachments,
)
```

### `yoga_app/templates/yoga_app/emails/course_completion.html` (no change needed)

The existing template already renders the completion details correctly.

### `yoga_app/templates/yoga_app/search_results.html` (confirmed complete)

The template already implements all required sections. The design confirms the JS `toggleFilters()` function and the Tailwind grid classes satisfy the requirements.

### `templates/registration/password_reset_email.html` (new)

Extends `yoga_app/emails/base_email.html`. Blocks:
- `subject` — "Reset Your Password"
- `header_subtitle` — "Account Security"
- `body` — greeting with `{{ user.username }}`, explanation, 24-hour validity note, security notice
- `cta` — button linking to `{{ protocol }}://{{ domain }}{% url 'password_reset_confirm' uidb64=uid token=token %}`

### `yoga_kailasa/urls.py` (modified)

Wire `PasswordResetView` with `html_email_template_name`:

```python
from django.contrib.auth import views as auth_views

path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
    html_email_template_name='registration/password_reset_email.html'
), name='password_reset'),
```

---

## Data Models

No new models are required.

Existing models used:

| Model | Fields accessed |
|---|---|
| `User` | `id`, `username`, `get_full_name()`, `email` |
| `Course` | `id`, `title`, `slug`, `instructor_name`, `price`, `is_free`, `duration`, `description`, `image_url` |
| `UserCourseCompletion` | `completed_at` (for certificate date) |
| `YogaPose` | `name`, `sanskrit_name`, `difficulty`, `description`, `image_url` |
| `BreathingTechnique` | `name`, `sanskrit_name`, `description`, `image_url` |

### Certificate PDF layout (ReportLab)

The PDF is generated entirely in memory using `BytesIO`. No files are written to disk.

```
Page size: A4 landscape (841 × 595 pt)
Background: white with a #855300 border rectangle (inset 20pt)
Header:     "Yoga Kailasa" in Georgia 36pt, colour #855300
Subtitle:   "Certificate of Completion" in Georgia 24pt, colour #534434
Body:       "This certifies that" (Helvetica 14pt)
            <display_name> (Georgia Bold 28pt, #855300)
            "has successfully completed" (Helvetica 14pt)
            <course_title> (Georgia Bold 22pt, #1f1b14)
            <completion_date> (Helvetica 12pt, #867461)
Footer:     Certificate ID: YK-<user_id>-<course_id> (Helvetica 9pt, #b0a090)
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Certificate content completeness

*For any* `User` (with or without a full name set) and any `Course`, calling `generate_certificate(user, course)` should return non-`None` bytes whose extracted text contains: the user's display name (`get_full_name()` or `username`), the course title, a date string matching the format "Month DD, YYYY", and the unique identifier string `YK-<user.id>-<course.id>`.

**Validates: Requirements 1.1, 1.6**

---

### Property 2: Attachment filename matches course slug

*For any* `Course` with any slug value, when `generate_certificate` succeeds the attachment tuple passed to `send_html_email` should have filename `certificate_<course.slug>.pdf`.

**Validates: Requirements 1.3**

---

### Property 3: Result cards render required fields

*For any* non-empty list of `YogaPose` objects, `BreathingTechnique` objects, or `Course` objects passed as template context, the rendered `search_results.html` HTML should contain each item's primary display field (pose name / technique name / course title), and for courses should also contain the instructor name and either the price value or the string "Free".

**Validates: Requirements 2.1, 2.2, 2.3**

---

### Property 4: Filter values are preserved in the rendered form

*For any* combination of `query`, `category_filter`, `pose_difficulty_filter`, and `course_price_filter` strings passed as template context, the rendered `search_results.html` HTML should contain those values as the `value` attribute of the search input and as `selected` attributes on the corresponding `<option>` elements.

**Validates: Requirements 2.8**

---

### Property 5: Result count appears in section headings

*For any* non-empty result list of length N passed as template context, the rendered `search_results.html` HTML should contain a heading that includes the string `(N)` where N is the length of that result list.

**Validates: Requirements 2.9**

---

### Property 6: Password reset CTA link contains correct URL

*For any* `uid`, `token`, `domain`, and `protocol` values passed as template context, the rendered `registration/password_reset_email.html` HTML should contain an `<a>` tag whose `href` includes both `uid` and `token` as substrings.

**Validates: Requirements 3.2**

---

### Property 7: Username appears in rendered password reset email

*For any* `User` with any username, the rendered `registration/password_reset_email.html` HTML should contain that username as a substring.

**Validates: Requirements 3.3**

---

### Property 8: Plain-text fallback contains the reset URL

*For any* `uid`, `token`, `domain`, and `protocol` values, the plain-text rendering of the password reset email (stripped of HTML tags) should contain the full reset URL as a substring.

**Validates: Requirements 3.4**

---

## Error Handling

### Certificate generation failure (Requirement 1.4)

`generate_certificate` wraps all ReportLab operations in a `try/except Exception`. On failure it calls `logger.error(...)` and returns `None`. The Celery task checks for `None` and sends the email with an empty attachments list. The task's own retry logic is unaffected — a PDF failure does not cause a task retry.

```python
# yoga_app/utils/certificate.py
try:
    # ... ReportLab drawing ...
    return buffer.getvalue()
except Exception as exc:
    logger.error("Certificate generation failed for user %s course %s: %s", user.id, course.id, exc)
    return None
```

### Missing course slug

`Course.slug` is not currently a model field. The attachment filename will use `course.id` as a fallback: `certificate_{course.id}.pdf` if no slug attribute exists. If a `slug` field is added later, the utility will use it automatically via `getattr(course, 'slug', course.id)`.

### Password reset template context

Django's `PasswordResetForm` always provides `uid`, `token`, `domain`, `protocol`, `user`, and `site_name` in the template context. No additional error handling is needed in the template.

---

## Testing Strategy

### Dual approach

Both unit tests and property-based tests are required. Unit tests cover specific examples and edge cases; property tests verify universal correctness across generated inputs.

### Property-based testing library

**Hypothesis** (`hypothesis` + `hypothesis[django]`) — the standard PBT library for Python. Add to `requirements.txt`:

```
hypothesis==6.x
```

Each property test runs a minimum of **100 iterations** (Hypothesis default `max_examples=100`).

Each test is tagged with a comment in the format:
`# Feature: immediate-user-features, Property N: <property_text>`

### Unit tests

Location: `yoga_app/tests/test_immediate_user_features.py`

| Test | What it covers |
|---|---|
| `test_certificate_generation_failure_sends_email_anyway` | Edge case: mock `generate_certificate` to raise, assert email is still sent with no attachment (Req 1.4) |
| `test_empty_search_state` | Example: render template with empty querysets, assert "No results found" text and browse links present (Req 2.4) |
| `test_search_responsive_grid_classes` | Example: render template with one pose, assert `grid-cols-1 md:grid-cols-2` classes present (Req 2.10) |
| `test_password_reset_email_extends_base` | Example: render template, assert "Yoga Kailasa" header text present (Req 3.1) |
| `test_password_reset_email_static_content` | Example: render template, assert "24 hours" and "did not request" text present (Req 3.5, 3.6) |

### Property-based tests

Location: `yoga_app/tests/test_immediate_user_features.py`

Each property maps 1-to-1 to a design property:

| Test function | Design property | Hypothesis strategy |
|---|---|---|
| `test_certificate_content_completeness` | Property 1 | `st.builds(User, ...)`, `st.builds(Course, ...)` with optional full name |
| `test_certificate_attachment_filename` | Property 2 | `st.text(alphabet=st.characters(whitelist_categories=('Ll','Nd')), min_size=1)` for slug |
| `test_search_result_cards_render_fields` | Property 3 | `st.lists(st.builds(...), min_size=1)` for each model type |
| `test_search_filter_values_preserved` | Property 4 | `st.text()` for query, `st.sampled_from(['', 'poses', 'breathing', 'courses'])` for category |
| `test_search_result_count_in_heading` | Property 5 | `st.lists(st.builds(YogaPose, ...), min_size=1, max_size=50)` |
| `test_password_reset_cta_link` | Property 6 | `st.text()` for uid/token, `st.from_regex(r'[a-z0-9.-]+')` for domain |
| `test_password_reset_username_in_body` | Property 7 | `st.text(min_size=1, max_size=150)` for username |
| `test_password_reset_plaintext_url` | Property 8 | same as Property 6 |
