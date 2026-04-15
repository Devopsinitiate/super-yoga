# Implementation Plan: Immediate User Features

## Overview

Three additive improvements to the Yoga Kailasa Django platform: PDF certificate generation wired into the course completion email, a confirmed-complete search results UI, and a branded HTML password reset email. No new models or URL patterns are required beyond wiring `PasswordResetView`.

## Tasks

- [x] 1. Add dependencies to requirements.txt
  - Add `reportlab` (PDF generation) and `hypothesis` (property-based testing) to `requirements.txt`
  - _Requirements: 1.5_

- [x] 2. Implement certificate generation utility
  - [x] 2.1 Create `yoga_app/utils/certificate.py` with `generate_certificate(user, course) -> bytes | None`
    - Resolve display name via `user.get_full_name() or user.username`
    - Build unique ID `f"YK-{user.id}-{course.id}"`
    - Draw A4-landscape PDF using `reportlab.pdfgen.canvas.Canvas` writing to `BytesIO`
    - Apply brand colour `#855300`, decorative border, Georgia serif fonts per the PDF layout spec in the design
    - Include platform name, "Certificate of Completion" subtitle, display name, course title, completion date formatted as "Month DD, YYYY", and certificate ID in footer
    - Wrap all ReportLab operations in `try/except`; on failure call `logger.error(...)` and return `None`
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6_

  - [ ]* 2.2 Write property test for certificate content completeness
    - **Property 1: Certificate content completeness**
    - **Validates: Requirements 1.1, 1.6**
    - Use `hypothesis` strategies to generate `User` objects with and without full names and `Course` objects with arbitrary titles
    - Assert returned bytes are non-`None` and that extracted text contains display name, course title, a date matching "Month DD, YYYY" format, and `YK-<user.id>-<course.id>`
    - Tag: `# Feature: immediate-user-features, Property 1: Certificate content completeness`

- [x] 3. Update `send_html_email` to support attachments
  - Modify `yoga_app/utils/email.py`: add optional `attachments: list[tuple[str, bytes, str]] | None = None` parameter
  - After `msg.attach_alternative(...)`, iterate `attachments` and call `msg.attach(filename, data, mimetype)` for each tuple
  - _Requirements: 1.3_

- [x] 4. Wire certificate into `send_course_completion_email` task
  - Modify `yoga_app/tasks.py` `send_course_completion_email`:
    - Import `generate_certificate` from `yoga_app.utils.certificate`
    - Call `generate_certificate(user, course)` after fetching models
    - Build `attachments` list: `[(f"certificate_{getattr(course, 'slug', course.id)}.pdf", pdf_bytes, "application/pdf")]` if `pdf_bytes` else `[]`
    - Pass `attachments=attachments` to `send_html_email`
  - _Requirements: 1.3, 1.4_

  - [ ]* 4.1 Write property test for attachment filename matches course slug
    - **Property 2: Attachment filename matches course slug**
    - **Validates: Requirements 1.3**
    - Generate arbitrary slug strings; assert the attachment tuple filename equals `certificate_<slug>.pdf`
    - Tag: `# Feature: immediate-user-features, Property 2: Attachment filename matches course slug`

  - [ ]* 4.2 Write unit test for certificate generation failure path
    - Mock `generate_certificate` to raise an exception
    - Assert `send_course_completion_email` still calls `send_html_email` with an empty `attachments` list (email is sent without attachment)
    - _Requirements: 1.4_

- [x] 5. Checkpoint — Ensure all certificate-related tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Verify search results template is complete
  - Confirm `yoga_app/templates/yoga_app/search_results.html` contains all required elements per the design:
    - Result cards for poses (name, difficulty badge, Sanskrit name, truncated description)
    - Result cards for breathing techniques (name, Sanskrit name, truncated description)
    - Result cards for courses (title, instructor name, price/Free, duration, truncated description)
    - "No results found" empty state with links to poses and courses
    - Result count in each section heading e.g. `({{ yoga_poses|length }})`
    - Filter values preserved via `selected` attributes on `<option>` elements and `value` on search input
    - `toggleFilters()` JS function hiding/showing difficulty and price selects based on category
    - Responsive grid classes `grid-cols-1 md:grid-cols-2` (and `xl:grid-cols-3` for poses/courses)
  - If any element is missing, add it to the template
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [ ]* 6.1 Write property test for result cards render required fields
    - **Property 3: Result cards render required fields**
    - **Validates: Requirements 2.1, 2.2, 2.3**
    - Generate non-empty lists of `YogaPose`, `BreathingTechnique`, and `Course` objects; render the template; assert each item's primary display field is present in the HTML, and for courses assert instructor name and price/Free are present
    - Tag: `# Feature: immediate-user-features, Property 3: Result cards render required fields`

  - [ ]* 6.2 Write property test for filter values preserved in rendered form
    - **Property 4: Filter values are preserved in the rendered form**
    - **Validates: Requirements 2.8**
    - Generate arbitrary query, category, difficulty, and price filter strings; render the template; assert each value appears as a `value` attribute or `selected` attribute in the output HTML
    - Tag: `# Feature: immediate-user-features, Property 4: Filter values preserved in rendered form`

  - [ ]* 6.3 Write property test for result count in section headings
    - **Property 5: Result count appears in section headings**
    - **Validates: Requirements 2.9**
    - Generate non-empty lists of length N; render the template; assert a heading containing `(N)` is present
    - Tag: `# Feature: immediate-user-features, Property 5: Result count appears in section headings`

  - [ ]* 6.4 Write unit test for empty search state
    - Render template with all three querysets empty; assert "No results found" text is present and links to poses and courses are present
    - _Requirements: 2.4_

  - [ ]* 6.5 Write unit test for responsive grid classes
    - Render template with one pose result; assert `grid-cols-1` and `md:grid-cols-2` classes are present in the HTML
    - _Requirements: 2.10_

- [x] 7. Create branded password reset email template
  - Create `yoga_app/templates/registration/password_reset_email.html` extending `yoga_app/emails/base_email.html`
  - Override blocks: `subject` ("Reset Your Password"), `header_subtitle` ("Account Security"), `body` (greeting with `{{ user.username }}`, explanation, 24-hour validity note, security notice), `cta` (button linking to `{{ protocol }}://{{ domain }}{% url 'password_reset_confirm' uidb64=uid token=token %}`)
  - Include plain-text reset URL as visible text inside the body block as fallback
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 7.1 Write property test for password reset CTA link contains correct URL
    - **Property 6: Password reset CTA link contains correct URL**
    - **Validates: Requirements 3.2**
    - Generate arbitrary `uid`, `token`, `domain`, `protocol` values; render the template; assert the rendered HTML contains an `<a>` tag whose `href` includes both `uid` and `token` as substrings
    - Tag: `# Feature: immediate-user-features, Property 6: Password reset CTA link contains correct URL`

  - [ ]* 7.2 Write property test for username appears in rendered email
    - **Property 7: Username appears in rendered password reset email**
    - **Validates: Requirements 3.3**
    - Generate arbitrary username strings; render the template; assert the username is present as a substring in the HTML output
    - Tag: `# Feature: immediate-user-features, Property 7: Username appears in rendered password reset email`

  - [ ]* 7.3 Write property test for plain-text fallback contains reset URL
    - **Property 8: Plain-text fallback contains the reset URL**
    - **Validates: Requirements 3.4**
    - Generate arbitrary `uid`, `token`, `domain`, `protocol`; strip HTML tags from rendered output; assert the full reset URL is present as a substring
    - Tag: `# Feature: immediate-user-features, Property 8: Plain-text fallback contains the reset URL`

  - [ ]* 7.4 Write unit test for password reset email extends base template
    - Render the template with minimal context; assert "Yoga Kailasa" header text is present
    - _Requirements: 3.1_

  - [ ]* 7.5 Write unit test for password reset email static content
    - Render the template; assert "24 hours" and "did not request" text are present
    - _Requirements: 3.5, 3.6_

- [x] 8. Wire `PasswordResetView` with HTML template in urls.py
  - In `yoga_kailasa/urls.py`, configure the `accounts/password_reset/` path to use `auth_views.PasswordResetView.as_view(html_email_template_name='registration/password_reset_email.html')`
  - Ensure the existing `password_reset_confirm`, `password_reset_done`, and `password_reset_complete` paths are preserved
  - _Requirements: 3.7_

- [x] 9. Create test file with all unit and property-based tests
  - Create `yoga_app/tests/test_immediate_user_features.py` containing all unit tests and property-based tests defined in tasks 2.2, 4.1, 4.2, 6.1–6.5, 7.1–7.5
  - Import `hypothesis` strategies and `@given` decorator; set `max_examples=100` per the testing strategy
  - Each property test tagged with `# Feature: immediate-user-features, Property N: <text>` comment
  - _Requirements: 1.1, 1.3, 1.4, 1.6, 2.1–2.4, 2.8–2.10, 3.1–3.6_

- [x] 10. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The search results template (`search_results.html`) is already substantially complete per the design; task 6 is a verification + gap-fill step
- `Course.slug` may not exist as a model field; use `getattr(course, 'slug', course.id)` as the fallback per the design's error handling section
- Property tests use `hypothesis` with Django test client for template rendering; add `hypothesis[django]` if needed
- Each property maps 1-to-1 to a design document property (Properties 1–8)
