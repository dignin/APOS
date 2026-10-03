"""Convert uploaded/camera photos to small, metadata-free JPEG avatars."""
import io
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PHOTO_BYTES = 3 * 1024 * 1024


def read_photo(files):
    chosen = [files.get(key) for key in ("photo", "camera") if files.get(key) and files.get(key).filename]
    if len(chosen) > 1:
        raise ValueError("Choose one photo: upload or camera.")
    if not chosen:
        return None
    with chosen[0].stream as stream:
        data = stream.read(MAX_PHOTO_BYTES + 1)
    if len(data) > MAX_PHOTO_BYTES:
        raise ValueError("Photo must be no larger than 3 MiB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in ("JPEG", "PNG", "WEBP") or image.width * image.height > 20_000_000:
                    raise ValueError("Use a JPEG, PNG or WebP photo up to 20 megapixels.")
                image = ImageOps.exif_transpose(image)
                image = ImageOps.fit(image.convert("RGB"), (256, 256), method=Image.Resampling.LANCZOS)
                output = io.BytesIO()
                image.save(output, format="JPEG", quality=85)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError("Use a valid JPEG, PNG or WebP photo.") from None
