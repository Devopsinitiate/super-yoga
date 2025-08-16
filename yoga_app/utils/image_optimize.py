from PIL import Image
import os

def optimize_image(image_path, max_size=(1200, 1200), format='WEBP', quality=80):
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        base, ext = os.path.splitext(image_path)
        optimized_path = f'{base}.webp'
        img.save(optimized_path, format=format, quality=quality)
        return optimized_path