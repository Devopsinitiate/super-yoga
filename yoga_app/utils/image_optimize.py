from PIL import Image
import os
from django.conf import settings


def optimize_image(image_path, max_size=(1200, 1200), format='WEBP', quality=80):
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        base, ext = os.path.splitext(image_path)
        optimized_path = f'{base}.webp'
        img.save(optimized_path, format=format, quality=quality)
        return optimized_path


def get_media_url(file_path):
    if hasattr(settings, 'CDN_URL') and settings.CDN_URL:
        return f"{settings.CDN_URL}{file_path}"
    return f"{settings.MEDIA_URL}{file_path}"


def get_static_url(file_path):
    if hasattr(settings, 'CDN_URL') and settings.CDN_URL:
        return f"{settings.CDN_URL}static/{file_path}"
    return f"{settings.STATIC_URL}{file_path}"
