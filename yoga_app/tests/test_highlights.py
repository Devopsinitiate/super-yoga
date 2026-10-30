"""Tests for the homepage Highlighted Sessions feature."""
import pytest
from django.urls import reverse

from yoga_app.models import HighlightSession


@pytest.mark.model
class TestHighlightSessionModel:
    def test_str_and_defaults(self):
        session = HighlightSession.objects.create(title='Morning Flow', video_url='')
        assert str(session) == 'Morning Flow'
        assert session.session_type == 'yoga_class'
        assert session.is_active is True
        assert session.order == 0

    def _session(self, url):
        return HighlightSession(title='t', video_url=url)

    def test_youtube_watch_url(self):
        assert self._session('https://www.youtube.com/watch?v=dQw4w9WgXcQ').embed_url \
            == 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ'

    def test_youtube_short_url(self):
        assert self._session('https://youtu.be/dQw4w9WgXcQ').embed_url \
            == 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ'

    def test_youtube_shorts_url(self):
        assert self._session('https://www.youtube.com/shorts/dQw4w9WgXcQ').embed_url \
            == 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ'

    def test_youtube_thumbnail_fallback(self):
        session = self._session('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        assert session.thumbnail_url == 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'

    def test_vimeo_url(self):
        assert self._session('https://vimeo.com/123456789').embed_url \
            == 'https://player.vimeo.com/video/123456789'

    def test_instagram_reel_url(self):
        assert self._session('https://www.instagram.com/reel/Cxyz123/').embed_url \
            == 'https://www.instagram.com/p/Cxyz123/embed'

    def test_tiktok_url(self):
        assert self._session('https://www.tiktok.com/@creator/video/7301234567890123456').embed_url \
            == 'https://www.tiktok.com/embed/v2/7301234567890123456'

    def test_facebook_video_url(self):
        url = 'https://www.facebook.com/somepage/videos/1234567890/'
        assert self._session(url).embed_url == \
            f'https://www.facebook.com/plugins/video.php?href={url}'

    def test_unsupported_url_returns_empty(self):
        assert self._session('https://example.com/video.mp4').embed_url == ''
        assert self._session('https://example.com/video.mp4').thumbnail_url == ''

    def test_empty_url(self):
        assert HighlightSession(title='t', video_url='').embed_url == ''


@pytest.mark.view
class TestHighlightSessionHomepage:
    def test_home_page_shows_only_active_sessions(self, client):
        HighlightSession.objects.create(
            title='Active Yoga Flow',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            session_type='yoga_class', order=1, is_active=True,
        )
        HighlightSession.objects.create(
            title='Hidden Massage Session',
            video_url='https://vimeo.com/123456789',
            session_type='massage_therapy', order=2, is_active=False,
        )
        response = client.get(reverse('home'))
        assert response.status_code == 200
        content = response.content.decode()
        # Active session renders with a playable embed
        assert 'Active Yoga Flow' in content
        assert 'highlight-sessions' in content
        assert 'youtube-nocookie.com/embed/dQw4w9WgXcQ' in content
        # Inactive session never renders
        assert 'Hidden Massage Session' not in content

    def test_home_page_without_sessions_has_no_section(self, db, client):
        response = client.get(reverse('home'))
        assert response.status_code == 200
        assert 'Sessions In Motion' not in response.content.decode()
