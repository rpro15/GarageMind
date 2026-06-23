from __future__ import annotations

import base64
import io
import unittest

from app.config.settings import Settings
from app.main import create_app


SAMPLE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5+G94AAAAASUVORK5CYII="
)


class ApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app = create_app(
            Settings(
                max_image_bytes=1024 * 1024,
                allowed_image_mime_types=("image/png", "image/jpeg", "image/webp"),
                recognition_provider="stub",
                log_level="DEBUG",
            )
        )
        app.testing = True
        self.client = app.test_client()

    def test_recognize_part_accepts_multipart_upload(self) -> None:
        response = self.client.post(
            "/api/recognize-part",
            data={"image": (io.BytesIO(SAMPLE_PNG), "brake-pad.png", "image/png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["source"], "stub")
        self.assertIn("part_name", payload)
        self.assertEqual(len(payload["possible_matches"]), 3)
        self.assertEqual(response.headers.get("X-Request-Id") is not None, True)

    def test_recognize_part_accepts_json_base64_payload(self) -> None:
        response = self.client.post(
            "/api/recognize-part",
            json={
                "image_base64": base64.b64encode(SAMPLE_PNG).decode("ascii"),
                "content_type": "image/png",
                "filename": "test.png",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["source"], "stub")
        self.assertIn("category", payload)

    def test_recognize_part_rejects_unsupported_media(self) -> None:
        response = self.client.post(
            "/api/recognize-part",
            data={"image": (io.BytesIO(b"not-an-image"), "notes.txt", "text/plain")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 415)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "unsupported_media_type")

    def test_recognize_part_rejects_malformed_base64(self) -> None:
        response = self.client.post(
            "/api/recognize-part",
            json={"image_base64": "%%notbase64%%", "content_type": "image/png"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "invalid_base64_image")

    def test_decode_vin_returns_decoded_payload(self) -> None:
        response = self.client.post("/api/decode-vin", json={"vin": "1HGCM82633A004352"})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["vin"], "1HGCM82633A004352")
        self.assertTrue(payload["is_valid"])
        self.assertEqual(payload["decoded"]["manufacturer"], "Honda")
        self.assertEqual(payload["decoded"]["model_year"], 2003)

    def test_decode_vin_returns_422_for_invalid_vin(self) -> None:
        response = self.client.get("/api/decode-vin?vin=1HGCM82633A004353")

        self.assertEqual(response.status_code, 422)
        payload = response.get_json()
        self.assertFalse(payload["is_valid"])
        self.assertGreater(len(payload["validation_errors"]), 0)

    def test_decode_vin_requires_value(self) -> None:
        response = self.client.post("/api/decode-vin", json={})

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "missing_vin")


if __name__ == "__main__":
    unittest.main()
