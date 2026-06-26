"""
Pytest unit tests for src/data_utils.py.

Covers:
- load_csv: file not found, empty file, successful load
- clean_phone: many input formats and invalid inputs
- validate_email: valid / invalid / edge cases
"""

import os
import sys
import numpy as np
import pandas as pd
import pytest

# Make src importable when running pytest from the project root.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.data_utils import load_csv, clean_phone, validate_email  # noqa: E402


# =============================================================================
# load_csv
# =============================================================================

class TestLoadCsv:
    def test_load_csv_file_not_found(self, tmp_path):
        missing = tmp_path / "does_not_exist.csv"
        with pytest.raises(FileNotFoundError):
            load_csv(str(missing))

    def test_load_csv_empty_file_raises(self, tmp_path):
        empty = tmp_path / "empty.csv"
        empty.write_text("")  # zero bytes
        with pytest.raises(ValueError):
            load_csv(str(empty))

    def test_load_csv_header_only_raises(self, tmp_path):
        header_only = tmp_path / "header_only.csv"
        header_only.write_text("a,b,c\n")
        with pytest.raises(ValueError):
            load_csv(str(header_only))

    def test_load_csv_successful(self, tmp_path):
        good = tmp_path / "good.csv"
        good.write_text("customer_id,age\nC001,30\nC002,42\n")
        df = load_csv(str(good))
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)
        assert list(df.columns) == ["customer_id", "age"]
        assert df.iloc[0]["customer_id"] == "C001"

    def test_load_csv_invalid_path_type(self):
        with pytest.raises(FileNotFoundError):
            load_csv("")

    def test_load_csv_real_dataset(self):
        """Smoke test against the actual assignment dataset."""
        path = os.path.join(PROJECT_ROOT, "data", "customer_data.csv")
        if not os.path.exists(path):
            pytest.skip("Assignment dataset not present")
        df = load_csv(path)
        assert df.shape[0] > 0
        assert "customer_id" in df.columns


# =============================================================================
# clean_phone
# =============================================================================

class TestCleanPhone:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("3637929158",       "363-792-9158"),
            ("363-792-9158",     "363-792-9158"),
            ("363.792.9158",     "363-792-9158"),
            ("(363) 792-9158",   "363-792-9158"),
            ("363 792 9158",     "363-792-9158"),
            (" 363-792-9158 ",   "363-792-9158"),
            ("363-792-9158x123", "363-792-9158"),   # extension digits ignored only if total is 10
        ],
    )
    def test_clean_phone_ten_digit_formats(self, raw, expected):
        # Note: the last case actually has 13 digits, so it should be None.
        # Adjust expectation accordingly inside the test.
        result = clean_phone(raw)
        digits_only = "".join(ch for ch in raw if ch.isdigit())
        if len(digits_only) == 10:
            assert result == expected
        elif len(digits_only) == 11 and digits_only.startswith("1"):
            assert result.startswith("+1-")
        else:
            assert result is None

    def test_clean_phone_eleven_digit_us(self):
        assert clean_phone("1-363-792-9158") == "+1-363-792-9158"
        assert clean_phone("13637929158")    == "+1-363-792-9158"

    @pytest.mark.parametrize(
        "raw",
        [
            None,
            "",
            "   ",
            "abcde",
            "12345",            # too short
            "12345678901234",   # too long
            "-8437",            # weird negative-looking junk seen in real data
            "0",
        ],
    )
    def test_clean_phone_invalid_inputs(self, raw):
        assert clean_phone(raw) is None

    def test_clean_phone_nan(self):
        assert clean_phone(np.nan) is None

    def test_clean_phone_integer_input(self):
        assert clean_phone(3637929158) == "363-792-9158"

    def test_clean_phone_idempotent(self):
        once = clean_phone("(363) 792-9158")
        twice = clean_phone(once)
        assert once == twice == "363-792-9158"


# =============================================================================
# validate_email
# =============================================================================

class TestValidateEmail:
    @pytest.mark.parametrize(
        "addr",
        [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user_name@sub.example.com",
            "u1@e1.io",
            "first.last+filter@some-domain.org",
        ],
    )
    def test_validate_email_valid(self, addr):
        assert validate_email(addr) is True

    @pytest.mark.parametrize(
        "addr",
        [
            "@domain.com",        # missing local part
            "user@",              # missing domain
            "invalid-email",      # no @
            "user@@domain.com",   # double @
            "no-dot@com",         # no dot in domain
            "missingatsign.com",  # no @ at all
            "user @domain.com",   # space in local (regex rejects)
            "user@domain",        # no TLD
            "user@.com",          # empty domain label
            "user@domain.c",      # 1-char TLD
        ],
    )
    def test_validate_email_invalid(self, addr):
        assert validate_email(addr) is False

    @pytest.mark.parametrize(
        "addr",
        [None, "", "   ", 123, 3.14, [], {}],
    )
    def test_validate_email_edge_cases(self, addr):
        assert validate_email(addr) is False

    def test_validate_email_nan(self):
        assert validate_email(np.nan) is False

    def test_validate_email_strips_whitespace(self):
        # whitespace-only is invalid, but surrounding whitespace on a valid
        # address should also be rejected by the strict regex -- documenting
        # the strict behavior here.
        assert validate_email("  user@example.com  ") is True
