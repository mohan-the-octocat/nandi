"""Unit tests for mathematical and algorithmic checksum validators."""

import os
import sys
import unittest

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plugin_root = os.path.join(repo_root, "AGY-Plugin")
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from src.pii_guard.checksums import (
    verhoeff_generate,
    verhoeff_validate,
    luhn_validate,
    gstin_validate,
    pan_validate,
    ifsc_validate,
    upi_validate,
    phone_in_validate,
    dl_in_validate,
    passport_in_validate,
    cin_in_validate,
    pin_code_validate,
)


class TestChecksums(unittest.TestCase):

    def test_verhoeff_aadhaar_validation(self):
        # Generate valid 12th digit
        prefix = "23456789012"
        check_digit = verhoeff_generate(prefix)
        self.assertIsNotNone(check_digit)
        valid_aadhaar = f"{prefix}{check_digit}"
        self.assertTrue(verhoeff_validate(valid_aadhaar))
        self.assertTrue(verhoeff_validate(f"{prefix[:4]} {prefix[4:8]} {prefix[8:]}{check_digit}"))

        # Corrupt last digit
        wrong_digit = str((int(check_digit) + 1) % 10)
        invalid_aadhaar = f"{prefix}{wrong_digit}"
        self.assertFalse(verhoeff_validate(invalid_aadhaar))

        # Aadhaar starting with 0 or 1 is invalid per UIDAI
        self.assertFalse(verhoeff_validate("012345678901"))
        self.assertFalse(verhoeff_validate("112345678901"))

    def test_luhn_card_validation(self):
        # Valid test Visa card
        self.assertTrue(luhn_validate("4532015112830366"))
        # Valid test RuPay card (5081 prefix)
        self.assertTrue(luhn_validate("5081234567890120"))
        # Invalid card number (tampered checksum)
        self.assertFalse(luhn_validate("4532015112830367"))

    def test_gstin_mod36_validation(self):
        # 27 = Maharashtra, AADCS1234F = PAN, 1 = entity, Z = default, checksum
        # Let's test a valid formatted GSTIN structure
        # State 27 + valid PAN AADCS1234F + 1 + Z + check
        # We verify invalid state code is rejected
        self.assertFalse(gstin_validate("999999999999999"))
        self.assertFalse(gstin_validate("00AADCS1234F1Z5")) # State 00 invalid

    def test_pan_validation(self):
        # Valid PANs
        self.assertTrue(pan_validate("ABCPE1234F")) # P = Person
        self.assertTrue(pan_validate("XYZCA5678G")) # C = Company
        self.assertTrue(pan_validate("MNOFA9876H")) # F = Firm
        self.assertTrue(pan_validate("PQRHA1111J")) # H = HUF
        self.assertTrue(pan_validate("STUTA2222K")) # T = Trust

        # Invalid PANs
        self.assertFalse(pan_validate("ABCDE1234F")) # 'D' is not a valid 4th char
        self.assertFalse(pan_validate("ABC1234F"))   # Wrong length
        self.assertFalse(pan_validate("ABCPE12345")) # Last char must be letter

    def test_ifsc_validation(self):
        self.assertTrue(ifsc_validate("HDFC0001234"))
        self.assertTrue(ifsc_validate("SBIN0000123"))
        self.assertTrue(ifsc_validate("ICIC0000001"))
        self.assertFalse(ifsc_validate("HDFC1001234")) # 5th char must be 0
        self.assertFalse(ifsc_validate("HDFC000123"))  # Length must be 11

    def test_upi_validation(self):
        self.assertTrue(upi_validate("merchant@okaxis"))
        self.assertTrue(upi_validate("john.doe@okhdfcbank"))
        self.assertTrue(upi_validate("user_123@paytm"))
        self.assertTrue(upi_validate("support@upi"))
        self.assertFalse(upi_validate("not_a_upi_vpa"))
        self.assertFalse(upi_validate("a@b"))

    def test_phone_in_validation(self):
        self.assertTrue(phone_in_validate("+91 9876543210"))
        self.assertTrue(phone_in_validate("09876543210"))
        self.assertTrue(phone_in_validate("9876543210"))
        self.assertTrue(phone_in_validate("7000012345"))
        self.assertFalse(phone_in_validate("1234567890")) # Starts with 1
        self.assertFalse(phone_in_validate("9999999999")) # Repeated dummy digits

    def test_passport_and_dl(self):
        self.assertTrue(passport_in_validate("A1234567"))
        self.assertTrue(passport_in_validate("K9876543"))
        self.assertFalse(passport_in_validate("Z9876543")) # Z is excluded in Indian passports
        self.assertFalse(passport_in_validate("12345678"))

        self.assertTrue(dl_in_validate("MH-12-2018-0001234"))
        self.assertTrue(dl_in_validate("DL0420110012345"))
        self.assertFalse(dl_in_validate("XX9999999999999")) # Invalid state code

    def test_cin_and_pin(self):
        self.assertTrue(cin_in_validate("L17110MH1973PLC019786"))
        self.assertTrue(cin_in_validate("U74999DL2016PTC308432"))
        self.assertFalse(cin_in_validate("A17110MH1973PLC019786")) # Must start with L or U

        self.assertTrue(pin_code_validate("400001"))
        self.assertTrue(pin_code_validate("110001"))
        self.assertFalse(pin_code_validate("012345")) # Starts with 0


if __name__ == "__main__":
    unittest.main()
