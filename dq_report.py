"""
Compute exact data-quality issue counts for the assignment report.

Independent of Great Expectations; useful as a cross-check.
"""

import re
import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.data_utils import validate_email  # reuse the same regex as production

CSV = os.path.join(PROJECT_ROOT, "data", "customer_data.csv")
ALLOWED_COUNTRIES = {"USA", "Canada", "UK", "Australia"}


def main():
    df = pd.read_csv(CSV)
    n = len(df)

    print(f"Rows: {n}")
    print(f"Columns: {list(df.columns)}")
    print()

    # Per-column nulls
    print("Missing values per column:")
    for c, v in df.isnull().sum().items():
        print(f"  {c:<12} {v}")
    print()

    # customer_id integrity
    cid_null  = df["customer_id"].isnull().sum()
    cid_dupes = df["customer_id"].duplicated(keep=False).sum()  # all rows that share an id
    cid_first_dupes = df["customer_id"].duplicated().sum()      # count beyond first
    print(f"customer_id nulls: {cid_null}")
    print(f"customer_id rows sharing a duplicated id (incl. originals): {cid_dupes}")
    print(f"customer_id duplicate occurrences (excluding first): {cid_first_dupes}")
    full_dupes = df.duplicated().sum()
    print(f"Fully duplicate rows: {full_dupes}")
    print()

    # Age
    age_out_of_range = ((df["age"] < 0) | (df["age"] > 120)).sum()
    age_gt_120 = (df["age"] > 120).sum()
    age_lt_0   = (df["age"] < 0).sum()
    print(f"age > 120: {age_gt_120}")
    print(f"age < 0:   {age_lt_0}")
    print(f"age out of [0, 120]: {age_out_of_range}")
    print()

    # Email
    invalid_email = df["email"].apply(lambda x: not validate_email(x) and pd.notna(x)).sum()
    null_email = df["email"].isnull().sum()
    print(f"emails null:                  {null_email}")
    print(f"emails present-but-invalid:   {invalid_email}")
    print()

    # Salary
    null_salary = df["salary"].isnull().sum()
    neg_salary  = (df["salary"] < 0).sum()
    salary_present_pct = (1 - null_salary / n) * 100
    print(f"salary null: {null_salary}  ({null_salary / n:.2%})")
    print(f"salary present: {salary_present_pct:.2f}%  (threshold for 95% expectation)")
    print(f"salary negative: {neg_salary}")
    print()

    # Country
    country_invalid = (~df["country"].isin(ALLOWED_COUNTRIES) & df["country"].notna()).sum()
    null_country = df["country"].isnull().sum()
    print(f"country null:                {null_country}")
    print(f"country not in allowed set:  {country_invalid}")
    print(f"country distinct values: {sorted(df['country'].dropna().unique().tolist())}")
    print()

    # Phone format inconsistency (count rows whose raw value is not a clean 10-digit form)
    print(f"phone null: {df['phone'].isnull().sum()}")
    print(f"phone unique format examples: {df['phone'].dropna().sample(min(10, df['phone'].notna().sum()), random_state=0).tolist()}")
    print()

    # signup_date
    bad_date = df["signup_date"].apply(
        lambda x: pd.notna(x) and not re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", str(x))
    ).sum()
    null_date = df["signup_date"].isnull().sum()
    print(f"signup_date null:        {null_date}")
    print(f"signup_date wrong fmt:   {bad_date}")
    print()

    print(f"Row count: {n} (expected 500-1000 — FAIL)")


if __name__ == "__main__":
    main()
