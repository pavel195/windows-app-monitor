"""
Модуль определения типов изображений
Это замена стандартного модуля imghdr, который был удален в Python 3.13
"""

def what(file, h=None):
    """
    Определяет тип изображения по заголовку файла
    Возвращает строку с типом или None, если тип не определен
    """
    if h is None:
        if isinstance(file, str):
            try:
                with open(file, 'rb') as f:
                    h = f.read(32)
            except OSError:
                return None
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
            if not h:
                return None

    # JPEG
    if h[0:2] == b'\xff\xd8':
        return 'jpeg'

    # PNG
    if h[0:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'

    # GIF ('87 и '89 варианты)
    if h[0:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'

    # BMP
    if h[0:2] == b'BM':
        return 'bmp'

    # WebP
    if h[0:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'

    # TIFF
    if h[0:4] in (b'MM\x00*', b'II*\x00'):
        return 'tiff'

    return None

tests = [
    ("jpeg", b'\xff\xd8\xff'),
    ("png", b'\x89PNG\r\n\x1a\n'),
    ("gif", b'GIF87a'),
    ("gif", b'GIF89a'),
    ("bmp", b'BM'),
    ("webp", b'RIFF\x00\x00\x00\x00WEBP'),
    ("tiff", b'MM\x00*'),
    ("tiff", b'II*\x00'),
] 