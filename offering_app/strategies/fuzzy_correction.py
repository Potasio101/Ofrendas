import re
from difflib import get_close_matches
from typing import Tuple

from offering_app.interfaces.i_correction_strategy import ICorrectionStrategy


class FuzzyCorrection(ICorrectionStrategy):
    AMOUNT_FIELDS = {
        "diezmo",
        "ofrenda",
        "primicias",
        "pro_templo",
        "ofrenda_misionera",
        "ofrenda_pastoral",
        "total",
    }

    def correct(self, text: str, field: str, members: list[str]) -> Tuple[str, float]:
        value = (text or "").strip()
        if field in self.AMOUNT_FIELDS:
            spaced = re.sub(r"[^0-9.\s]", "", value)
            spaced = re.sub(r"\s+", " ", spaced).strip()
            if "." not in spaced:
                decimal_match = re.search(r"(\d+)\s+(\d{1,2})$", spaced)
                if decimal_match:
                    whole = decimal_match.group(1)
                    cents = decimal_match.group(2)
                    return f"{whole}.{cents}", 0.85

            cleaned = re.sub(r"[^0-9.]", "", spaced)
            if cleaned.count(".") > 1:
                first = cleaned.find(".")
                cleaned = cleaned[: first + 1] + cleaned[first + 1 :].replace(".", "")
            if cleaned == "" or cleaned == ".":
                return "0", 0.6
            return cleaned, 0.9

        if field == "member_name" and members:
            try:
                from rapidfuzz import process

                match = process.extractOne(value, members)
                if match:
                    return str(match[0]), min(float(match[1]) / 100.0, 1.0)
            except Exception:
                pass

            fallback = get_close_matches(value, members, n=1, cutoff=0.0)
            if fallback:
                return fallback[0], 0.75

        return value, 0.7 if value else 0.5
