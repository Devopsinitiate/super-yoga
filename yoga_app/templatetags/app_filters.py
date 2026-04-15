# yoga_app/templatetags/app_filters.py

from django import template

register = template.Library()

@register.filter
def split_lines(value):
    """
    Splits a string by newline characters and returns a list of lines.
    Useful for displaying multi-line instructions in templates.
    """
    if not isinstance(value, str):
        return []
    return [line.strip() for line in value.split('\n') if line.strip()]

@register.filter
def ljust(value, arg):
    """
    Pads a string with spaces on the right to a specified width.
    Used for creating a sequence for stars (e.g., "|ljust:5").
    """
    return str(value).ljust(arg)

@register.filter
def cut(value, arg):
    """
    Removes all occurrences of arg from the given string.
    Used to calculate remaining stars for testimonials (e.g., "|cut:testimonial.rating").
    """
    if not isinstance(value, str):
        return value
    return value.replace(str(arg), "")

@register.filter
def get_range(value):
    """
    Filter to generate a range of numbers up to a given value (for star ratings).
    Example: {{ course.avg_rating|get_range }} will produce [1, 2, 3, ...] up to avg_rating.
    It handles float values by converting to int for the range.
    """
    try:
        # Convert to float first, then int to handle cases like 3.5 -> 3
        # We only need the integer part for the number of full stars
        return range(int(float(value)))
    except (ValueError, TypeError):
        return range(0) # Return an empty range if value is not a valid number


@register.filter
def multiply(value, arg):
    """
    Multiplies the value with the arg.
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return '' # Return empty string or handle error as preferred

@register.filter
def read_time(value):
    """
    Estimates reading time in minutes for a given HTML/text string.
    Based on an average reading speed of 200 words per minute.
    """
    import re
    if not value:
        return 1
    text = re.sub(r'<[^>]+>', '', str(value))
    word_count = len(text.split())
    minutes = max(1, round(word_count / 200))
    return minutes


@register.filter
def embed_url(value):
    """
    Converts a YouTube URL to an embed URL.
    Handles watch, short (youtu.be), Shorts, and existing embed URLs.
    """
    import re
    import html as _html

    if not value:
        return ''

    value = _html.unescape(str(value).strip())

    # Already an embed URL (regular or nocookie) — return clean version
    match = re.search(r'(?:youtube\.com|youtube-nocookie\.com)/embed/([a-zA-Z0-9_-]+)', value)
    if match:
        return f'https://www.youtube-nocookie.com/embed/{match.group(1)}'

    # YouTube Shorts: youtube.com/shorts/VIDEO_ID
    match = re.search(r'youtube\.com/shorts/([a-zA-Z0-9_-]+)', value)
    if match:
        return f'https://www.youtube-nocookie.com/embed/{match.group(1)}'

    # Standard watch URL: ?v=VIDEO_ID
    match = re.search(r'[?&]v=([a-zA-Z0-9_-]+)', value)
    if match:
        return f'https://www.youtube-nocookie.com/embed/{match.group(1)}'

    # Short URL: youtu.be/VIDEO_ID
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', value)
    if match:
        return f'https://www.youtube-nocookie.com/embed/{match.group(1)}'

    return value
