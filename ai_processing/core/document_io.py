import io
from dataclasses import dataclass

from PIL import Image, ImageDraw, UnidentifiedImageError


class DocumentError(ValueError):
    pass


@dataclass(frozen=True)
class DocumentInfo:
    mimetype: str | None
    width: int = 0
    height: int = 0
    page_count: int = 0
    eligible: bool = False
    reason: str = ""


def inspect_document(raw, *, max_bytes, min_image_edge=300, max_pdf_pages=50):
    if not raw:
        return DocumentInfo(None, reason="empty file")
    if len(raw) > max_bytes:
        return DocumentInfo(None, reason="file exceeds the configured size limit")
    if raw.startswith((b"GIF87a", b"GIF89a")):
        return DocumentInfo("image/gif", reason="GIF is preserved but not processed")
    if raw.startswith(b"%PDF-"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw))
            page_count = len(reader.pages)
            if reader.is_encrypted and reader.decrypt("") == 0:
                return DocumentInfo(
                    "application/pdf",
                    page_count=page_count,
                    reason="password-protected PDF",
                )
            if page_count > max_pdf_pages:
                return DocumentInfo(
                    "application/pdf",
                    page_count=page_count,
                    reason="PDF exceeds the configured page limit",
                )
        except Exception:
            return DocumentInfo("application/pdf", reason="unreadable PDF")
        return DocumentInfo(
            "application/pdf",
            page_count=page_count,
            eligible=True,
            reason="valid PDF",
        )
    signatures = {
        "image/jpeg": raw.startswith(b"\xff\xd8\xff"),
        "image/png": raw.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": (
            len(raw) >= 12 and raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"
        ),
    }
    mimetype = next((kind for kind, matches in signatures.items() if matches), None)
    if not mimetype:
        return DocumentInfo(None, reason="unsupported content signature")
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError):
        return DocumentInfo(mimetype, reason="damaged image")
    if width < min_image_edge or height < min_image_edge:
        return DocumentInfo(
            mimetype,
            width=width,
            height=height,
            reason="image is too small and is likely a signature or logo",
        )
    return DocumentInfo(
        mimetype,
        width=width,
        height=height,
        eligible=True,
        reason="valid image",
    )


def render_pdf(
    raw, *, max_pages, max_page_bytes=3 * 1024 * 1024, max_total_bytes=12 * 1024 * 1024
):
    import pypdfium2 as pdfium

    try:
        document = pdfium.PdfDocument(raw)
    except Exception as error:
        raise DocumentError("PDF could not be rendered safely") from error
    try:
        if len(document) > max_pages:
            raise DocumentError("PDF exceeds the visual page limit")
        rendered = []
        total = 0
        for index in range(len(document)):
            page = document.get_page(index)
            try:
                bitmap = page.render(scale=2)
                try:
                    image = bitmap.to_pil().convert("RGB")
                    buffer = io.BytesIO()
                    image.save(buffer, "JPEG", quality=88, optimize=True)
                finally:
                    bitmap.close()
            finally:
                page.close()
            page_bytes = buffer.getvalue()
            if len(page_bytes) > max_page_bytes:
                raise DocumentError(f"rendered page {index + 1} is too large")
            total += len(page_bytes)
            if total > max_total_bytes:
                raise DocumentError("rendered PDF exceeds the visual byte limit")
            rendered.append(page_bytes)
        return rendered
    finally:
        document.close()


def capability_probe_image():
    image = Image.new("RGB", (720, 360), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 700, 340), outline="black", width=4)
    draw.text((70, 110), "AI PROCESSING", fill="black")
    draw.text((70, 190), "VISION CODE: AIP-7429", fill="black")
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()
