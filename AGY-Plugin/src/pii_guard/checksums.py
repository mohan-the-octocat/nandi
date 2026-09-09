"""Mathematical and algorithmic checksum validators for Indian PII entities.

Includes:
- Verhoeff Algorithm (D5 Dihedral Group) for Aadhaar 12-digit UIDAI validation.
- Luhn Algorithm (Mod 10) for Payment Cards (RuPay, Visa, Mastercard).
- Mod 36 Algorithm for GSTIN 15-character verification.
- Structural algorithms for PAN, IFSC, UPI, Phone, DL, Passport, CIN, and PIN code.
"""

import re
from typing import Optional

# ==============================================================================
# Verhoeff Algorithm (Dihedral Group D5) - UIDAI Aadhaar Validation
# ==============================================================================

# Multiplication table d (10x10)
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

# Permutation table p (8x10)
_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

# Inverse table inv (10)
_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_validate(number_str: str) -> bool:
    """Validates a number string using the Verhoeff checksum algorithm.

    Used by UIDAI for 12-digit Aadhaar numbers.
    """
    cleaned = re.sub(r"[\s-]", "", str(number_str))
    if not cleaned.isdigit():
        return False
    if len(cleaned) != 12:
        return False
    # Aadhaar numbers must not start with 0 or 1
    if cleaned[0] in ("0", "1"):
        return False

    c = 0
    reversed_digits = [int(x) for x in reversed(cleaned)]
    for i, digit in enumerate(reversed_digits):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][digit]]
    return c == 0


def verhoeff_generate(number_str: str) -> Optional[str]:
    """Generates the Verhoeff checksum digit for an 11-digit number string."""
    cleaned = re.sub(r"[\s-]", "", str(number_str))
    if not cleaned.isdigit() or len(cleaned) != 11:
        return None
    c = 0
    reversed_digits = [int(x) for x in reversed(cleaned)]
    for i, digit in enumerate(reversed_digits):
        c = _VERHOEFF_D[c][_VERHOEFF_P[(i + 1) % 8][digit]]
    return str(_VERHOEFF_INV[c])


# ==============================================================================
# Luhn Algorithm (Mod 10) - Payment Card Validation
# ==============================================================================

def luhn_validate(card_number: str) -> bool:
    """Validates a payment card number using the Luhn mod-10 algorithm.

    Validates RuPay, Visa, MasterCard, Amex, and Discover cards.
    """
    cleaned = re.sub(r"[\s-]", "", str(card_number))
    if not cleaned.isdigit() or len(cleaned) < 13 or len(cleaned) > 19:
        return False

    digits = [int(d) for d in cleaned]
    checksum = 0
    reverse_digits = digits[::-1]

    for idx, d in enumerate(reverse_digits):
        if idx % 2 == 1:
            doubled = d * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += d

    return checksum % 10 == 0


# ==============================================================================
# GSTIN Mod 36 Checksum Validation
# ==============================================================================

_GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_GSTIN_CHAR_MAP = {c: i for i, c in enumerate(_GSTIN_CHARS)}

# Valid 2-digit Indian State / UT codes for GSTIN
_INDIAN_STATE_CODES = {
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
    "31", "32", "33", "34", "35", "36", "37", "38", "97", "99"
}


def gstin_validate(gstin_str: str) -> bool:
    """Validates an Indian 15-character GSTIN identifier.

    Checks:
    1. 15-character format
    2. Valid state code prefix (01-38, 97, 99)
    3. Embedded valid PAN structure in characters 3..12
    4. 14th character must be Z
    5. 15th character Mod 36 checksum
    """
    cleaned = gstin_str.strip().upper()
    if len(cleaned) != 15:
        return False

    # Regex format check
    gstin_regex = r"^(0[1-9]|[1-2]\d|3[0-8]|97|99)[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
    if not re.match(gstin_regex, cleaned):
        return False

    state_code = cleaned[:2]
    if state_code not in _INDIAN_STATE_CODES:
        return False

    # Validate embedded PAN structure
    embedded_pan = cleaned[2:12]
    if not pan_validate(embedded_pan):
        return False

    # Mod 36 Checksum calculation on first 14 chars
    factor = 1
    total = 0
    for char in cleaned[:14]:
        if char not in _GSTIN_CHAR_MAP:
            return False
        code_point = _GSTIN_CHAR_MAP[char]
        digit = factor * code_point
        factor = 2 if factor == 1 else 1
        digit = (digit // 36) + (digit % 36)
        total += digit

    remainder = total % 36
    check_code_point = (36 - remainder) % 36
    expected_check_char = _GSTIN_CHARS[check_code_point]

    return cleaned[14] == expected_check_char


# ==============================================================================
# PAN (Permanent Account Number) Structure Validation
# ==============================================================================

# Valid 4th character entity types in Indian PAN
_PAN_ENTITY_TYPES = {
    "P": "Individual / Person",
    "C": "Company",
    "H": "Hindu Undivided Family (HUF)",
    "F": "Partnership Firm / LLP",
    "A": "Association of Persons (AOP)",
    "T": "Trust",
    "B": "Body of Individuals (BOI)",
    "L": "Local Authority",
    "J": "Artificial Juridical Person",
    "G": "Government Agency"
}


def pan_validate(pan_str: str) -> bool:
    """Validates Indian Income Tax Permanent Account Number (PAN).

    Structure: 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F).
    4th character must be one of the recognized entity status types.
    """
    cleaned = pan_str.strip().upper()
    if len(cleaned) != 10:
        return False

    pan_pattern = r"^[A-Z]{3}[PCHFATBLJG][A-Z]\d{4}[A-Z]$"
    return bool(re.match(pan_pattern, cleaned))


# ==============================================================================
# IFSC (Indian Financial System Code) Validation
# ==============================================================================

def ifsc_validate(ifsc_str: str) -> bool:
    """Validates Indian Financial System Code (IFSC).

    Structure: 11 characters.
    - First 4 characters: Alphabetic bank code.
    - 5th character: Always 0 (reserved for future use).
    - Last 6 characters: Alphanumeric branch code.
    """
    cleaned = ifsc_str.strip().upper()
    if len(cleaned) != 11:
        return False

    ifsc_pattern = r"^[A-Z]{4}0[A-Z0-9]{6}$"
    return bool(re.match(ifsc_pattern, cleaned))


# ==============================================================================
# UPI VPA (Virtual Payment Address) Validation
# ==============================================================================

_KNOWN_UPI_HANDLES = {
    "okaxis", "okicici", "oksbi", "okhdfcbank", "paytm", "ybl", "ibl",
    "axl", "apl", "upi", "postbank", "barodampay", "federal", "kotak",
    "indus", "pnb", "allbank", "cnrb", "sbi", "aubank", "idbi", "boi",
    "unionbank", "equitas", "fbl", "rbl", "pingpay", "slice", "jupiteraxis",
    "cred", "freecharge", "mobikwik", "amazonpay", "airtel"
}


def upi_validate(vpa_str: str) -> bool:
    """Validates Indian UPI Virtual Payment Address (VPA)."""
    cleaned = vpa_str.strip().lower()
    if "@" not in cleaned:
        return False

    parts = cleaned.split("@")
    if len(parts) != 2:
        return False

    username, handle = parts[0], parts[1]
    if len(username) < 2 or len(username) > 64:
        return False
    if not re.match(r"^[a-z0-9.\-_]+$", username):
        return False

    if handle in _KNOWN_UPI_HANDLES:
        return True

    # Generic valid alphanumeric domain handle
    return bool(re.match(r"^[a-z]{3,30}$", handle))


# ==============================================================================
# Indian Phone Number Validation
# ==============================================================================

def phone_in_validate(phone_str: str) -> bool:
    """Validates 10-digit Indian Mobile number starting with 6, 7, 8, or 9."""
    cleaned = re.sub(r"[\s\-\(\)\+]", "", phone_str)
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]

    if len(cleaned) != 10:
        return False
    if cleaned[0] not in ("6", "7", "8", "9"):
        return False
    # Reject repeated dummy numbers (e.g. 9999999999, 8888888888)
    if len(set(cleaned)) == 1:
        return False
    return cleaned.isdigit()


# ==============================================================================
# Indian Driving Licence (DL) Validation
# ==============================================================================

_VALID_DL_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN",
    "GA", "GJ", "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD",
    "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "OR", "PB", "PY",
    "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB"
}


def dl_in_validate(dl_str: str) -> bool:
    """Validates Indian Driving Licence number."""
    cleaned = re.sub(r"[\s\-]", "", dl_str).upper()
    if len(cleaned) not in (15, 16):
        return False

    state_code = cleaned[:2]
    if state_code not in _VALID_DL_STATE_CODES:
        return False

    # Check Sarathi format: SS-RR-YYYY-NNNNNNN
    pattern = r"^[A-Z]{2}\d{2}(?:19|20)\d{2}\d{7}$"
    if re.match(pattern, cleaned):
        return True

    # Legacy or 15-digit numeric formats
    return bool(re.match(r"^[A-Z]{2}\d{13,14}$", cleaned))


# ==============================================================================
# Indian Passport Validation
# ==============================================================================

def passport_in_validate(passport_str: str) -> bool:
    """Validates Indian Passport Number (8 alphanumeric characters).

    First character is an uppercase letter (excluding Q, X, Z),
    followed by 7 digits (first digit 1-9).
    """
    cleaned = re.sub(r"\s", "", passport_str).upper()
    if len(cleaned) != 8:
        return False

    # Pattern: 1 letter (A-P, R-W, Y) + digit 1-9 + 6 digits
    pattern = r"^[A-PR-WYa-pr-wy][1-9]\d{6}$"
    return bool(re.match(pattern, cleaned))


# ==============================================================================
# Corporate Identification Number (CIN) Validation
# ==============================================================================

def cin_in_validate(cin_str: str) -> bool:
    """Validates 21-character MCA Corporate Identification Number (CIN)."""
    cleaned = cin_str.strip().upper()
    if len(cleaned) != 21:
        return False

    cin_pattern = r"^[LU]\d{5}[A-Z]{2}(?:19|20)\d{2}[A-Z]{3}\d{6}$"
    return bool(re.match(cin_pattern, cleaned))


# ==============================================================================
# Indian PIN Code Validation
# ==============================================================================

def pin_code_validate(pin_str: str) -> bool:
    """Validates 6-digit Indian Postal Index Number (PIN Code)."""
    cleaned = re.sub(r"\s", "", pin_str)
    if len(cleaned) != 6 or not cleaned.isdigit():
        return False
    # First digit must be 1 to 9 (0 is invalid)
    return cleaned[0] != "0"
