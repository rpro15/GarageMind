from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.domain.models import VinDecodeResult, VinDecoded


TRANSLITERATION = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 6,
    "G": 7,
    "H": 8,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "P": 7,
    "R": 9,
    "S": 2,
    "T": 3,
    "U": 4,
    "V": 5,
    "W": 6,
    "X": 7,
    "Y": 8,
    "Z": 9,
}

VIN_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)
MODEL_YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"
MODEL_YEAR_BASE = {code: 1980 + index for index, code in enumerate(MODEL_YEAR_CODES)}
REGION_BY_WMI_PREFIX = {
    "1": "United States",
    "2": "Canada",
    "3": "Mexico",
    "4": "United States",
    "5": "United States",
    "6": "Australia",
    "7": "New Zealand",
    "8": "South America",
    "9": "South America",
    "J": "Japan",
    "K": "Korea",
    "L": "China",
    "M": "India",
    "N": "Turkey",
    "P": "Philippines",
    "R": "Taiwan",
    "S": "United Kingdom",
    "T": "Switzerland",
    "V": "France/Spain",
    "W": "Germany",
    "X": "Russia",
    "Y": "Sweden/Finland",
    "Z": "Italy",
}
MANUFACTURERS_BY_WMI = {
    "1C4": "Jeep",
    "1FA": "Ford",
    "1FT": "Ford",
    "1G1": "Chevrolet",
    "1HG": "Honda",
    "1M8": "MCI",
    "2HG": "Honda",
    "3VW": "Volkswagen",
    "5YJ": "Tesla",
    "JHM": "Honda",
    "JTD": "Toyota",
    "KMH": "Hyundai",
    "KNM": "Renault Samsung",
    "WAU": "Audi",
    "WBA": "BMW",
    "WDB": "Mercedes-Benz",
    "ZFA": "Fiat",
}
FORBIDDEN_CHARS = {"I", "O", "Q"}


class VinDecoderService:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def decode(self, raw_vin: str) -> VinDecodeResult:
        vin = (raw_vin or "").strip().upper()
        validation_errors: list[str] = []

        if len(vin) != 17:
            validation_errors.append("VIN must be exactly 17 characters long.")

        forbidden = sorted(set(vin) & FORBIDDEN_CHARS)
        if forbidden:
            validation_errors.append(
                f"VIN contains forbidden characters: {', '.join(forbidden)}."
            )

        invalid_characters = sorted({char for char in vin if not (char.isdigit() or "A" <= char <= "Z")})
        if invalid_characters:
            validation_errors.append(
                f"VIN contains invalid characters: {', '.join(invalid_characters)}."
            )

        if len(vin) == 17 and not forbidden and not invalid_characters:
            expected_check_digit = calculate_check_digit(vin)
            if expected_check_digit != vin[8]:
                validation_errors.append(
                    f"VIN check digit mismatch: expected {expected_check_digit}, got {vin[8]}."
                )

        decoded = VinDecoded(
            wmi=vin[:3] if len(vin) >= 3 else None,
            region=REGION_BY_WMI_PREFIX.get(vin[0]) if len(vin) >= 1 else None,
            manufacturer=MANUFACTURERS_BY_WMI.get(vin[:3]) if len(vin) >= 3 else None,
            model_year=decode_model_year(vin[9]) if len(vin) >= 10 else None,
            plant_code=vin[10] if len(vin) >= 11 else None,
            serial=vin[11:] if len(vin) >= 12 else None,
        )

        self._logger.debug(
            "Decoded VIN vin=%s valid=%s errors=%s",
            vin,
            not validation_errors,
            len(validation_errors),
        )

        return VinDecodeResult(
            vin=vin,
            is_valid=not validation_errors,
            validation_errors=validation_errors,
            decoded=decoded,
        )


def calculate_check_digit(vin: str) -> str:
    total = 0
    for index, char in enumerate(vin):
        value = int(char) if char.isdigit() else TRANSLITERATION[char]
        total += value * VIN_WEIGHTS[index]

    remainder = total % 11
    return "X" if remainder == 10 else str(remainder)


def decode_model_year(code: str, *, current_year: int | None = None) -> int | None:
    if code not in MODEL_YEAR_BASE:
        return None

    resolved_current_year = current_year or datetime.now(timezone.utc).year
    base_year = MODEL_YEAR_BASE[code]
    # VIN year codes repeat every 30 years, so project one cycle beyond the
    # current year and choose the latest candidate that is still plausible.
    candidate_years = list(range(base_year, resolved_current_year + 31, 30))
    valid_years = [year for year in candidate_years if year <= resolved_current_year + 1]
    if valid_years:
        return max(valid_years)
    return min(candidate_years)
