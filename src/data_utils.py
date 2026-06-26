"""
Data utility functions for customer data validation.

Three small, testable functions used by the data pipeline and exercised by
pytest in tests/test_data_utils.py.
"""

import os
import re
import pandas as pd


# --- Regex patterns -----------------------------------------------------------

# Practical email pattern: local@domain.tld
# - local part: letters, digits, dot, underscore, percent, plus, hyphen
# - must contain a single '@'
# - domain: letters, digits, dot, hyphen
# - TLD: 2+ letters
EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
)


# --- Functions ----------------------------------------------------------------

def load_csv(filepath: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.

    Parameters
    ----------
    filepath : str
        Path to the CSV file.

    Returns
    -------
    pandas.DataFrame

    Raises
    ------
    FileNotFoundError
        If the file does not exist at `filepath`.
    ValueError
        If the file is empty (zero bytes or no rows / no columns).
    """
    if not isinstance(filepath, str) or not filepath:
        raise FileNotFoundError(f"Invalid filepath: {filepath!r}")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    if os.path.getsize(filepath) == 0:
        raise ValueError(f"File is empty: {filepath}")

    try:
        df = pd.read_csv(filepath)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"File has no parseable data: {filepath}") from exc

    if df.shape[0] == 0 or df.shape[1] == 0:
        raise ValueError(f"File loaded but contains no rows/columns: {filepath}")

    return df


def clean_phone(phone) -> str | None:
    """
    Normalise a phone number to a canonical format.

    Strips all non-digit characters and returns the digits in the form
    ``XXX-XXX-XXXX`` when there are exactly 10 digits, or ``+1-XXX-XXX-XXXX``
    when there are 11 digits starting with '1'. Returns ``None`` for inputs
    that cannot be normalised (None/NaN, empty, or wrong digit count).

    Parameters
    ----------
    phone : Any
        Raw phone value. Strings, ints, None, and pandas NaN are accepted.

    Returns
    -------
    str or None
        Canonicalised phone number, or None if input is invalid.
    """
    # None / NaN handling
    if phone is None:
        return None
    # pandas NaN is a float; cheap check
    try:
        if isinstance(phone, float) and pd.isna(phone):
            return None
    except Exception:
        pass

    # Coerce to string
    s = str(phone).strip()
    if not s:
        return None

    # Extract digits only
    digits = re.sub(r"\D", "", s)

    if len(digits) == 10:
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"

    # Anything else (too few digits, too many, negative-looking junk) is invalid
    return None


def validate_email(email) -> bool:
    """
    Return True iff `email` is a syntactically valid email address.

    Validation rules (intentionally pragmatic, not full RFC 5322):
      - must be a non-empty string
      - must contain exactly one '@'
      - local and domain parts must be non-empty
      - domain must contain at least one '.'
      - must match :data:`EMAIL_REGEX`

    Returns False for None, NaN, non-strings, and any malformed value.
    """
    if email is None:
        return False
    try:
        if isinstance(email, float) and pd.isna(email):
            return False
    except Exception:
        pass
    if not isinstance(email, str):
        return False

    s = email.strip()
    if not s:
        return False
    if s.count("@") != 1:
        return False

    local, _, domain = s.partition("@")
    if not local or not domain:
        return False
    if "." not in domain:
        return False

    return EMAIL_REGEX.match(s) is not None
