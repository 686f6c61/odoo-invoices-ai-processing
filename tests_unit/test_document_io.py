import io
import unittest

from PIL import Image

from ai_processing.core.document_io import capability_probe_image, inspect_document


def image_bytes(kind, size=(600, 800)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "white").save(buffer, kind)
    return buffer.getvalue()


class DocumentIOTests(unittest.TestCase):
    def test_valid_image(self):
        info = inspect_document(
            image_bytes("PNG"),
            max_bytes=2 * 1024 * 1024,
        )
        self.assertTrue(info.eligible)
        self.assertEqual(info.mimetype, "image/png")

    def test_small_image_is_preserved_but_not_processed(self):
        info = inspect_document(
            image_bytes("JPEG", (100, 100)),
            max_bytes=2 * 1024 * 1024,
        )
        self.assertFalse(info.eligible)
        self.assertIn("too small", info.reason)

    def test_gif_is_not_processed(self):
        info = inspect_document(b"GIF89a" + b"x" * 100, max_bytes=1024)
        self.assertFalse(info.eligible)
        self.assertEqual(info.mimetype, "image/gif")

    def test_extension_cannot_override_signature(self):
        info = inspect_document(b"MZ" + b"x" * 1000, max_bytes=2048)
        self.assertFalse(info.eligible)
        self.assertIsNone(info.mimetype)

    def test_oversized_input(self):
        info = inspect_document(b"x" * 2049, max_bytes=2048)
        self.assertFalse(info.eligible)
        self.assertIn("size", info.reason)

    def test_probe_image_is_valid_and_large_enough(self):
        info = inspect_document(capability_probe_image(), max_bytes=1024 * 1024)
        self.assertTrue(info.eligible)
        self.assertEqual(info.mimetype, "image/png")


if __name__ == "__main__":
    unittest.main()
