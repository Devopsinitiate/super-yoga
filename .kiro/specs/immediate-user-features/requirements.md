# Requirements Document

## Introduction

Three immediate user-facing features for the Yoga Kailasa Django platform:

1. **Certificate Generation** — Generate a branded PDF certificate when a user completes a course and attach it to the existing course completion email sent via the `send_course_completion_email` Celery task.
2. **Search Page UI** — Improve the `search_results.html` template to display a proper results UI for poses, courses, and breathing techniques with working category/difficulty/price filtering.
3. **Password Reset Email Styling** — Replace the plain-text Django password reset email with a branded HTML email that matches the existing `base_email.html` template style.

## Glossary

- **Certificate_Generator**: The component responsible for producing a PDF certificate from a template and user/course data.
- **PDF_Attachment**: A PDF file attached to an outgoing email via Django's `EmailMultiAlternatives`.
- **Completion_Email**: The email sent by the `send_course_completion_email` Celery task in `yoga_app/tasks.py`.
- **UserCourseCompletion**: The Django model that records when a user finishes a course, including `completed_at` timestamp.
- **Search_UI**: The `search_results.html` template rendered by `global_search_view`.
- **SearchService**: The existing service in `yoga_app/services/search_service.py` that returns `yoga_poses`, `breathing_techniques`, and `courses` querysets.
- **Filter_Panel**: The form section of the Search_UI containing category, difficulty, and price filter controls.
- **Password_Reset_Email**: The email Django sends during the built-in password reset flow, rendered from `registration/password_reset_email.html`.
- **Base_Email_Template**: The existing branded HTML email layout at `yoga_app/templates/yoga_app/emails/base_email.html`.
- **SITE_URL**: The `settings.SITE_URL` value used to construct absolute URLs in emails.

---

## Requirements

### Requirement 1: PDF Certificate Generation

**User Story:** As a student, I want to receive a PDF certificate when I complete a course, so that I have a tangible record of my achievement.

#### Acceptance Criteria

1. WHEN a user completes a course, THE Certificate_Generator SHALL produce a PDF containing the user's full name (or username if no full name is set), the course title, and the completion date formatted as "Month DD, YYYY".
2. THE Certificate_Generator SHALL apply Yoga Kailasa branding: the platform name, the brand colour `#855300`, and a decorative border or header consistent with the platform's visual identity.
3. WHEN the PDF is generated, THE Completion_Email SHALL include the certificate as an attachment named `certificate_<course_slug>.pdf`.
4. IF PDF generation raises an exception, THEN THE Completion_Email SHALL still be sent without an attachment, and THE Certificate_Generator SHALL log the error at ERROR level.
5. THE Certificate_Generator SHALL generate the PDF using a library already available or easily added to `requirements.txt` without requiring a headless browser (e.g., ReportLab or WeasyPrint).
6. WHEN the certificate is generated, THE Certificate_Generator SHALL include a unique identifier derived from the user ID and course ID so that each certificate is distinguishable.

---

### Requirement 2: Search Page Results UI

**User Story:** As a visitor, I want to see clearly organised search results for poses, courses, and breathing techniques, so that I can quickly find what I am looking for.

#### Acceptance Criteria

1. WHEN `global_search_view` renders `search_results.html` with a non-empty `yoga_poses` queryset, THE Search_UI SHALL display each pose's name, difficulty badge, Sanskrit name (if present), and a truncated description.
2. WHEN `global_search_view` renders `search_results.html` with a non-empty `breathing_techniques` queryset, THE Search_UI SHALL display each technique's name, Sanskrit name (if present), and a truncated description.
3. WHEN `global_search_view` renders `search_results.html` with a non-empty `courses` queryset, THE Search_UI SHALL display each course's title, instructor name, price (or "Free"), duration, and a truncated description.
4. WHEN all three result sets are empty, THE Search_UI SHALL display a "No results found" message and links to browse poses and courses.
5. WHEN the Filter_Panel `category` select is set to "poses", THE Search_UI SHALL hide the price filter and show the difficulty filter.
6. WHEN the Filter_Panel `category` select is set to "courses", THE Search_UI SHALL hide the difficulty filter and show the price filter.
7. WHEN the Filter_Panel `category` select is set to "" (all), THE Search_UI SHALL show both the difficulty filter and the price filter.
8. WHEN a search query is submitted, THE Search_UI SHALL preserve the submitted `q`, `category`, `pose_difficulty`, and `course_price` values in the filter form inputs.
9. WHEN results are present, THE Search_UI SHALL display a result count per category section heading (e.g., "Sacred Poses (12)").
10. THE Search_UI SHALL be responsive, displaying results in a single column on mobile and a multi-column grid on tablet and desktop viewports.

---

### Requirement 3: Branded Password Reset Email

**User Story:** As a user who has forgotten their password, I want to receive a branded HTML password reset email, so that the experience feels consistent with the rest of the Yoga Kailasa platform.

#### Acceptance Criteria

1. WHEN Django's password reset flow sends an email, THE Password_Reset_Email SHALL render as an HTML email that extends `base_email.html`.
2. THE Password_Reset_Email SHALL display a clear call-to-action button linking to `{{ protocol }}://{{ domain }}{% url 'password_reset_confirm' uidb64=uid token=token %}`.
3. THE Password_Reset_Email SHALL include the user's username in the email body.
4. THE Password_Reset_Email SHALL include a plain-text fallback that contains the reset URL.
5. IF the password reset link has expired or is invalid, THE Password_Reset_Email content SHALL note that the link is valid for a limited time (24 hours).
6. THE Password_Reset_Email SHALL include a security notice informing the user that if they did not request a password reset, they can safely ignore the email.
7. WHEN Django renders the password reset email, THE Password_Reset_Email SHALL use the `EMAIL_BACKEND` configured in `settings.py`, consistent with all other platform emails.
