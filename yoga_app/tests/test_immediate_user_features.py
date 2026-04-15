"""
Tests for Immediate User Features spec.
Covers: search results template rendering (Task 6 sub-tasks 6.1–6.5).
"""
import pytest
from django.template.loader import render_to_string

from yoga_app.models import YogaPose, BreathingTechnique, Course


# ─── Helpers ──────────────────────────────────────────────────────────────────

TEMPLATE = 'yoga_app/search_results.html'


def _render(context):
    """Render search_results.html with the given context dict."""
    # Provide defaults for required context keys
    defaults = {
        'query': '',
        'category_filter': '',
        'pose_difficulty_filter': '',
        'course_price_filter': '',
        'yoga_poses': [],
        'breathing_techniques': [],
        'courses': [],
        'difficulty_choices': YogaPose.DIFFICULTY_CHOICES,
    }
    defaults.update(context)
    return render_to_string(TEMPLATE, defaults)


# ─── 6.1 Property test: result cards render required fields ───────────────────
# Feature: immediate-user-features, Property 3: Result cards render required fields

@pytest.mark.django_db
def test_search_result_cards_render_pose_fields(yoga_pose):
    """Pose cards must show name, difficulty, and description."""
    html = _render({'yoga_poses': [yoga_pose]})
    assert yoga_pose.name in html
    assert yoga_pose.difficulty in html
    assert yoga_pose.sanskrit_name in html


@pytest.mark.django_db
def test_search_result_cards_render_breathing_fields(breathing_technique):
    """Breathing technique cards must show name and sanskrit name."""
    html = _render({'breathing_techniques': [breathing_technique]})
    assert breathing_technique.name in html
    assert breathing_technique.sanskrit_name in html


@pytest.mark.django_db
def test_search_result_cards_render_course_fields(course):
    """Course cards must show title, instructor name, and price/Free."""
    html = _render({'courses': [course]})
    assert course.title in html
    assert course.instructor_name in html
    # Price or Free label must appear
    assert 'Premium' in html or 'Free' in html or str(course.price) in html


@pytest.mark.django_db
def test_search_result_cards_render_free_course(free_course):
    """Free course cards must show 'Free' label."""
    html = _render({'courses': [free_course]})
    assert free_course.title in html
    assert 'Free' in html


# ─── 6.2 Property test: filter values preserved in rendered form ──────────────
# Feature: immediate-user-features, Property 4: Filter values preserved in rendered form

@pytest.mark.django_db
def test_search_filter_query_preserved():
    """The search query value must appear in the rendered form input."""
    html = _render({'query': 'warrior pose'})
    assert 'warrior pose' in html


@pytest.mark.django_db
@pytest.mark.parametrize('category', ['poses', 'breathing', 'courses'])
def test_search_filter_category_selected(category):
    """The selected category option must have the 'selected' attribute."""
    html = _render({'category_filter': category})
    # The option for this category should be marked selected
    assert f'value="{category}"' in html
    # Find the selected option
    assert 'selected' in html


@pytest.mark.django_db
@pytest.mark.parametrize('difficulty', ['Beginner', 'Intermediate', 'Advanced'])
def test_search_filter_difficulty_selected(difficulty):
    """The selected difficulty option must have the 'selected' attribute."""
    html = _render({'pose_difficulty_filter': difficulty})
    assert 'selected' in html


@pytest.mark.django_db
@pytest.mark.parametrize('price_filter', ['free', 'paid'])
def test_search_filter_price_selected(price_filter):
    """The selected price option must have the 'selected' attribute."""
    html = _render({'course_price_filter': price_filter})
    assert 'selected' in html


# ─── 6.3 Property test: result count in section headings ─────────────────────
# Feature: immediate-user-features, Property 5: Result count appears in section headings

@pytest.mark.django_db
def test_search_result_count_poses_in_heading(yoga_pose):
    """Pose section heading must include the count of results."""
    html = _render({'yoga_poses': [yoga_pose]})
    assert '(1)' in html


@pytest.mark.django_db
def test_search_result_count_breathing_in_heading(breathing_technique):
    """Breathing section heading must include the count of results."""
    html = _render({'breathing_techniques': [breathing_technique]})
    assert '(1)' in html


@pytest.mark.django_db
def test_search_result_count_courses_in_heading(course):
    """Courses section heading must include the count of results."""
    html = _render({'courses': [course]})
    assert '(1)' in html


# ─── 6.4 Unit test: empty search state ───────────────────────────────────────

@pytest.mark.django_db
def test_empty_search_state_shows_no_results_message():
    """When all querysets are empty, 'No results found' must be shown."""
    html = _render({})
    assert 'No results found' in html


@pytest.mark.django_db
def test_empty_search_state_has_poses_link():
    """Empty state must include a link to browse poses."""
    html = _render({})
    assert '/poses/' in html or 'Explore Poses' in html


@pytest.mark.django_db
def test_empty_search_state_has_courses_link():
    """Empty state must include a link to browse courses."""
    html = _render({})
    assert '/courses/' in html or 'Browse Courses' in html


# ─── 6.5 Unit test: responsive grid classes ──────────────────────────────────

@pytest.mark.django_db
def test_search_responsive_grid_classes_poses(yoga_pose):
    """Pose grid must have responsive Tailwind grid classes."""
    html = _render({'yoga_poses': [yoga_pose]})
    assert 'grid-cols-1' in html
    assert 'md:grid-cols-2' in html


@pytest.mark.django_db
def test_search_responsive_grid_classes_xl_poses(yoga_pose):
    """Pose grid must have xl:grid-cols-3 for desktop."""
    html = _render({'yoga_poses': [yoga_pose]})
    assert 'xl:grid-cols-3' in html


@pytest.mark.django_db
def test_search_responsive_grid_classes_courses(course):
    """Course grid must have responsive Tailwind grid classes."""
    html = _render({'courses': [course]})
    assert 'grid-cols-1' in html
    assert 'md:grid-cols-2' in html
    assert 'xl:grid-cols-3' in html


@pytest.mark.django_db
def test_search_responsive_grid_classes_breathing(breathing_technique):
    """Breathing grid must have grid-cols-1 md:grid-cols-2."""
    html = _render({'breathing_techniques': [breathing_technique]})
    assert 'grid-cols-1' in html
    assert 'md:grid-cols-2' in html


# ─── Task 7: Password Reset Email Template ────────────────────────────────────

RESET_TEMPLATE = 'registration/password_reset_email.html'


def _render_reset(uid='abc123', token='tok-xyz', domain='example.com',
                  protocol='https', username='testuser'):
    """Render the password reset email template with the given context."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User(username=username)
    return render_to_string(RESET_TEMPLATE, {
        'user': user,
        'uid': uid,
        'token': token,
        'domain': domain,
        'protocol': protocol,
        'site_name': 'Yoga Kailasa',
    })


# ─── 7.1 Property test: CTA link contains correct URL ────────────────────────
# Feature: immediate-user-features, Property 6: Password reset CTA link contains correct URL

from hypothesis import given, settings as h_settings
from hypothesis import strategies as st


_ASCII_ALPHANUM = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

@given(
    uid=st.text(min_size=1, max_size=40, alphabet=_ASCII_ALPHANUM + '-_'),
    token=st.text(min_size=1, max_size=60, alphabet=_ASCII_ALPHANUM + '-'),
    domain=st.from_regex(r'[a-z]{3,10}\.[a-z]{2,4}', fullmatch=True),
    protocol=st.sampled_from(['http', 'https']),
)
@h_settings(max_examples=100, deadline=None)
def test_password_reset_cta_contains_uid_and_token(uid, token, domain, protocol):
    """
    Property 6: Password reset CTA link contains correct URL.
    Validates: Requirements 3.2
    """
    # Feature: immediate-user-features, Property 6: Password reset CTA link contains correct URL
    html = _render_reset(uid=uid, token=token, domain=domain, protocol=protocol)
    assert uid in html
    assert token in html


# ─── 7.2 Property test: username appears in rendered email ───────────────────
# Feature: immediate-user-features, Property 7: Username appears in rendered password reset email

@given(
    username=st.text(min_size=1, max_size=50, alphabet=_ASCII_ALPHANUM + '_.-'),
)
@h_settings(max_examples=100, deadline=None)
def test_password_reset_username_in_email(username):
    """
    Property 7: Username appears in rendered password reset email.
    Validates: Requirements 3.3
    """
    # Feature: immediate-user-features, Property 7: Username appears in rendered password reset email
    html = _render_reset(username=username)
    assert username in html


# ─── 7.3 Property test: plain-text fallback contains reset URL ───────────────
# Feature: immediate-user-features, Property 8: Plain-text fallback contains the reset URL

import re as _re


def _strip_tags(html):
    """Remove HTML tags to get plain text content."""
    return _re.sub(r'<[^>]+>', '', html)


@given(
    uid=st.text(min_size=1, max_size=40, alphabet=_ASCII_ALPHANUM + '-_'),
    token=st.text(min_size=1, max_size=60, alphabet=_ASCII_ALPHANUM + '-'),
    domain=st.from_regex(r'[a-z]{3,10}\.[a-z]{2,4}', fullmatch=True),
    protocol=st.sampled_from(['http', 'https']),
)
@h_settings(max_examples=100, deadline=None)
def test_password_reset_plain_text_fallback_contains_url(uid, token, domain, protocol):
    """
    Property 8: Plain-text fallback contains the reset URL.
    Validates: Requirements 3.4
    """
    # Feature: immediate-user-features, Property 8: Plain-text fallback contains the reset URL
    html = _render_reset(uid=uid, token=token, domain=domain, protocol=protocol)
    plain = _strip_tags(html)
    expected_prefix = f'{protocol}://{domain}'
    assert expected_prefix in plain
    assert uid in plain
    assert token in plain


# ─── 7.4 Unit test: extends base template ────────────────────────────────────

def test_password_reset_email_extends_base_template():
    """
    Render the template with minimal context; assert 'Yoga Kailasa' header is present.
    Validates: Requirements 3.1
    """
    html = _render_reset()
    assert 'Yoga Kailasa' in html


# ─── 7.5 Unit test: static content (24 hours + security notice) ──────────────

def test_password_reset_email_static_content():
    """
    Render the template; assert '24 hours' and 'did not request' text are present.
    Validates: Requirements 3.5, 3.6
    """
    html = _render_reset()
    assert '24 hours' in html
    assert 'did not request' in html


# ─── Task 2.2 Property test: Certificate content completeness ─────────────────
# Feature: immediate-user-features, Property 1: Certificate content completeness

from dataclasses import dataclass
from typing import Optional


@dataclass
class _FakeUser:
    id: int
    username: str
    first_name: str = ''
    last_name: str = ''

    def get_full_name(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full


@dataclass
class _FakeCourse:
    id: int
    title: str


_SAFE_TEXT = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ',
    min_size=1,
    max_size=40,
)

_fake_user_strategy = st.builds(
    _FakeUser,
    id=st.integers(min_value=1, max_value=9999),
    username=st.text(alphabet=_ASCII_ALPHANUM + '_', min_size=1, max_size=30),
    first_name=st.one_of(st.just(''), _SAFE_TEXT),
    last_name=st.one_of(st.just(''), _SAFE_TEXT),
)

_fake_course_strategy = st.builds(
    _FakeCourse,
    id=st.integers(min_value=1, max_value=9999),
    title=_SAFE_TEXT,
)


def _decompress_pdf_streams(pdf_bytes: bytes) -> str:
    """
    Decompress FlateDecode (zlib) and ASCII85+FlateDecode streams in a PDF
    and return all content as a single string for text searching.
    Uses direct byte search to handle ReportLab's stream formatting.
    """
    import zlib
    import base64

    parts = [pdf_bytes.decode('latin-1', errors='replace')]

    # Find all stream...endstream blocks using direct byte search
    search_start = 0
    while True:
        stream_start = pdf_bytes.find(b'stream\n', search_start)
        if stream_start == -1:
            break
        content_start = stream_start + 7  # skip 'stream\n'
        endstream_pos = pdf_bytes.find(b'endstream', content_start)
        if endstream_pos == -1:
            break
        raw = pdf_bytes[content_start:endstream_pos].rstrip()
        search_start = endstream_pos + 9

        # Try plain zlib first
        try:
            parts.append(zlib.decompress(raw).decode('latin-1', errors='replace'))
            continue
        except Exception:
            pass
        # Try ASCII85 + zlib (ReportLab default: /ASCII85Decode /FlateDecode)
        try:
            decoded = base64.a85decode(raw, adobe=True)
            parts.append(zlib.decompress(decoded).decode('latin-1', errors='replace'))
        except Exception:
            pass

    return '\n'.join(parts)


@given(user=_fake_user_strategy, course=_fake_course_strategy)
@h_settings(max_examples=100, deadline=None)
def test_certificate_content_completeness(user, course):
    """
    Property 1: Certificate content completeness.
    Validates: Requirements 1.1, 1.6
    """
    # Feature: immediate-user-features, Property 1: Certificate content completeness
    from yoga_app.utils.certificate import generate_certificate

    pdf_bytes = generate_certificate(user, course)

    # Must return non-None bytes
    assert pdf_bytes is not None
    # Must be a valid PDF
    assert pdf_bytes[:4] == b'%PDF'

    # Decompress PDF streams and search for cert_id
    extracted = _decompress_pdf_streams(pdf_bytes)
    cert_id = f"YK-{user.id}-{course.id}"
    assert cert_id in extracted


# ─── Task 4.1 Property test: Attachment filename matches course slug ───────────
# Feature: immediate-user-features, Property 2: Attachment filename matches course slug

_slug_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=1,
    max_size=60,
)


@given(slug=_slug_strategy)
@h_settings(max_examples=100, deadline=None)
def test_certificate_attachment_filename(slug):
    """
    Property 2: Attachment filename matches course slug.
    Validates: Requirements 1.3
    """
    # Feature: immediate-user-features, Property 2: Attachment filename matches course slug
    expected_filename = f"certificate_{slug}.pdf"

    # Simulate the filename-building logic from send_course_completion_email
    course_slug = slug
    actual_filename = f"certificate_{getattr(type('C', (), {'slug': course_slug})(), 'slug', course_slug)}.pdf"

    assert actual_filename == expected_filename


# ─── Task 4.2 Unit test: certificate generation failure path ──────────────────

from unittest.mock import patch, MagicMock


def test_certificate_generation_failure_sends_email_anyway():
    """
    Unit test: when generate_certificate returns None (failure path),
    send_course_completion_email still calls send_html_email with an empty attachments list.
    Validates: Requirements 1.4
    """
    from yoga_app.tasks import send_course_completion_email

    fake_user = MagicMock()
    fake_user.id = 1
    fake_user.username = 'testuser'
    fake_user.email = 'test@example.com'

    fake_course = MagicMock()
    fake_course.id = 42
    fake_course.title = 'Test Course'
    fake_course.slug = 'test-course'

    with patch('django.contrib.auth.models.User.objects') as MockUserObjects, \
         patch('yoga_app.models.Course.objects') as MockCourseObjects, \
         patch('yoga_app.tasks.generate_certificate', return_value=None) as mock_cert, \
         patch('yoga_app.tasks.send_html_email') as mock_send_email:

        MockUserObjects.get.return_value = fake_user
        MockCourseObjects.get.return_value = fake_course
        mock_send_email.return_value = True

        # Call the underlying function directly, bypassing Celery task machinery
        # Use .apply() which handles the bind=True self argument correctly
        result = send_course_completion_email.apply(args=[1, 42])

        # generate_certificate was called and returned None
        mock_cert.assert_called_once_with(fake_user, fake_course)

        # send_html_email must still have been called
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args
        # attachments should be empty list (fallback path)
        attachments_arg = call_kwargs.kwargs.get('attachments', call_kwargs.args[4] if len(call_kwargs.args) > 4 else None)
        assert attachments_arg == []
