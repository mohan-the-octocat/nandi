"""PII Redaction and Format-Preserving Masking Engine."""

import re
from typing import Dict, List, Tuple
from src.pii_guard.entities import PIIMatch, PIICategory


class PIIRedactor:
    """Utility class to mask or redact sensitive PII spans from text."""

    @staticmethod
    def mask_match(match: PIIMatch) -> str:
        """Produces a format-preserving or standard masked string for an entity."""
        val = match.raw_value.strip()
        e_type = match.entity_type

        if e_type == "AADHAAR":
            cleaned = re.sub(r"[\s-]", "", val)
            last4 = cleaned[-4:] if len(cleaned) >= 4 else "XXXX"
            return f"XXXX-XXXX-{last4}"

        elif e_type == "PAN":
            if len(val) == 10:
                return f"{val[:2]}XXXXX{val[-3:]}"
            return "[REDACTED_PAN]"

        elif e_type == "CREDIT_DEBIT_CARD":
            cleaned = re.sub(r"[\s-]", "", val)
            if len(cleaned) >= 8:
                return f"{cleaned[:4]}-XXXX-XXXX-{cleaned[-4:]}"
            return "[REDACTED_CARD]"

        elif e_type == "CARD_CVV":
            return "[REDACTED_CVV]"

        elif e_type == "BANK_ACCOUNT_IN":
            cleaned = re.sub(r"[\s-]", "", val)
            if len(cleaned) >= 4:
                return f"XXXXXXXXXXXX{cleaned[-4:]}"
            return "[REDACTED_ACCOUNT]"

        elif e_type == "IFSC":
            if len(val) == 11:
                return f"{val[:4]}0XX{val[-3:]}"
            return "[REDACTED_IFSC]"

        elif e_type == "MICR":
            if len(val) == 9:
                return f"{val[:3]}XXX{val[-3:]}"
            return "[REDACTED_MICR]"

        elif e_type == "UPI_VPA":
            if "@" in val:
                user, handle = val.split("@", 1)
                masked_user = f"{user[:2]}***" if len(user) > 2 else "***"
                return f"{masked_user}@{handle}"
            return "[REDACTED_UPI]"

        elif e_type == "PHONE_IN":
            cleaned = re.sub(r"[\s\-\(\)\+]", "", val)
            if len(cleaned) >= 4:
                return f"+91-XXXXX-{cleaned[-4:]}"
            return "[REDACTED_PHONE]"

        elif e_type == "GSTIN":
            if len(val) == 15:
                return f"{val[:2]}XXXXXXXXX{val[-4:]}"
            return "[REDACTED_GSTIN]"

        elif e_type == "PASSPORT_IN":
            if len(val) >= 2:
                return f"{val[0]}XXXXXX{val[-1]}"
            return "[REDACTED_PASSPORT]"

        elif e_type == "DRIVING_LICENSE_IN":
            if len(val) >= 6:
                return f"{val[:2]}XXXX{val[-4:]}"
            return "[REDACTED_DL]"

        elif e_type == "VOTER_ID_IN":
            if len(val) == 10:
                return f"{val[:3]}XXXX{val[-3:]}"
            return "[REDACTED_VOTER_ID]"

        elif e_type == "CIN_IN":
            if len(val) == 21:
                return f"{val[:6]}XXXXXXXX{val[-7:]}"
            return "[REDACTED_CIN]"

        elif e_type == "PIN_CODE_IN":
            cleaned = re.sub(r"\s", "", val)
            if len(cleaned) == 6:
                return f"{cleaned[:3]}XXX"
            return "[REDACTED_PIN]"

        return f"[REDACTED_{e_type}]"

    @classmethod
    def redact_text(cls, text: str, matches: List[PIIMatch]) -> str:
        """Redacts all matched spans in the text in reverse order to preserve offsets."""
        if not matches or not text:
            return text

        sorted_matches = sorted(matches, key=lambda m: m.start_index, reverse=True)
        result = list(text)

        for match in sorted_matches:
            start = match.start_index
            end = match.end_index
            if 0 <= start <= end <= len(result):
                replacement = cls.mask_match(match)
                result[start:end] = list(replacement)

        return "".join(result)
