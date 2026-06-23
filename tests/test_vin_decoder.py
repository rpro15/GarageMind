from __future__ import annotations

import logging
import unittest

from app.services.vin_decoder import VinDecoderService, calculate_check_digit, decode_model_year


class VinDecoderServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = VinDecoderService(logging.getLogger("tests.vin"))

    def test_decode_marks_valid_vin(self) -> None:
        result = self.service.decode("1HGCM82633A004352")

        self.assertTrue(result.is_valid)
        self.assertEqual(result.decoded.wmi, "1HG")
        self.assertEqual(result.decoded.region, "United States")
        self.assertEqual(result.decoded.manufacturer, "Honda")
        self.assertEqual(result.decoded.model_year, 2003)
        self.assertEqual(result.decoded.plant_code, "A")
        self.assertEqual(result.decoded.serial, "004352")

    def test_decode_rejects_invalid_length(self) -> None:
        result = self.service.decode("123456789")

        self.assertFalse(result.is_valid)
        self.assertIn("VIN must be exactly 17 characters long.", result.validation_errors)

    def test_decode_rejects_forbidden_characters(self) -> None:
        result = self.service.decode("1HGCM82633A00I352")

        self.assertFalse(result.is_valid)
        self.assertIn("VIN contains forbidden characters: I.", result.validation_errors)

    def test_calculate_check_digit_supports_x(self) -> None:
        self.assertEqual(calculate_check_digit("1M8GDM9AXKP042788"), "X")

    def test_model_year_uses_latest_plausible_cycle(self) -> None:
        self.assertEqual(decode_model_year("S"), 2025)


if __name__ == "__main__":
    unittest.main()
