"""
Great Expectations setup for Assignment 2.

This script:
  1. Initializes (or re-uses) a file-backed GE context in ./gx
  2. Registers a pandas filesystem data source pointing at ./data
  3. Creates / overwrites the `customer_data_expectations` suite with the
     eight expectations required by the assignment
  4. Builds a checkpoint that runs the suite against customer_data.csv
  5. Executes the checkpoint and builds HTML Data Docs into ./gx/uncommitted/data_docs

Run:  python setup_ge.py
"""

import os
import shutil
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
import great_expectations.expectations as gxe


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
GX_DIR       = os.path.join(PROJECT_ROOT, "gx")
DATA_DIR     = os.path.join(PROJECT_ROOT, "data")
CSV_NAME     = "customer_data.csv"

DATA_SOURCE_NAME = "customer_data_source"
DATA_ASSET_NAME  = "customer_data_asset"
BATCH_DEF_NAME   = "customer_data_batch"
SUITE_NAME       = "customer_data_expectations"
CHECKPOINT_NAME  = "customer_data_checkpoint"

EMAIL_REGEX = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"


def get_context():
    """Return a file-backed GE context, creating one if needed."""
    if os.path.isdir(GX_DIR):
        return gx.get_context(mode="file", project_root_dir=PROJECT_ROOT)
    return gx.get_context(mode="file", project_root_dir=PROJECT_ROOT)


def register_data_source(context):
    """Idempotently register a pandas filesystem data source + CSV asset."""
    try:
        ds = context.data_sources.get(DATA_SOURCE_NAME)
    except (KeyError, LookupError, ValueError):
        ds = context.data_sources.add_pandas_filesystem(
            name=DATA_SOURCE_NAME, base_directory=DATA_DIR
        )

    try:
        asset = ds.get_asset(DATA_ASSET_NAME)
    except (KeyError, LookupError, ValueError):
        asset = ds.add_csv_asset(name=DATA_ASSET_NAME)

    try:
        batch_def = asset.get_batch_definition(BATCH_DEF_NAME)
    except (KeyError, LookupError, ValueError):
        batch_def = asset.add_batch_definition_path(
            name=BATCH_DEF_NAME, path=CSV_NAME
        )

    return batch_def


def build_suite(context) -> ExpectationSuite:
    """Create (or overwrite) the customer_data_expectations suite."""
    # Drop existing suite so re-runs are clean
    try:
        context.suites.delete(name=SUITE_NAME)
    except Exception:
        pass

    suite = context.suites.add(ExpectationSuite(name=SUITE_NAME))

    # 1. customer_id must be unique
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeUnique(column="customer_id")
    )
    # 2. customer_id must not be null
    suite.add_expectation(
        gxe.ExpectColumnValuesToNotBeNull(column="customer_id")
    )
    # 3. age must be between 0 and 120
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="age", min_value=0, max_value=120)
    )
    # 4. email must match a valid format
    suite.add_expectation(
        gxe.ExpectColumnValuesToMatchRegex(column="email", regex=EMAIL_REGEX)
    )
    # 5. salary present in >= 95% of rows
    suite.add_expectation(
        gxe.ExpectColumnValuesToNotBeNull(column="salary", mostly=0.95)
    )
    # 6. country must be one of the allowed values
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeInSet(
            column="country",
            value_set=["USA", "Canada", "UK", "Australia"],
        )
    )
    # 7. signup_date must parse as datetime
    suite.add_expectation(
        gxe.ExpectColumnValuesToMatchStrftimeFormat(
            column="signup_date", strftime_format="%m/%d/%Y"
        )
    )
    # 8. Table row count must be between 500 and 1000
    suite.add_expectation(
        gxe.ExpectTableRowCountToBeBetween(min_value=500, max_value=1000)
    )

    suite.save()
    return suite


def build_and_run_checkpoint(context, batch_def, suite):
    """Wire a Validation Definition + Checkpoint and run it."""
    from great_expectations.core.validation_definition import ValidationDefinition
    from great_expectations.checkpoint.checkpoint import Checkpoint
    from great_expectations.checkpoint.actions import UpdateDataDocsAction

    vd_name = "customer_data_validation"
    try:
        context.validation_definitions.delete(name=vd_name)
    except Exception:
        pass

    vd = context.validation_definitions.add(
        ValidationDefinition(name=vd_name, data=batch_def, suite=suite)
    )

    try:
        context.checkpoints.delete(name=CHECKPOINT_NAME)
    except Exception:
        pass

    checkpoint = context.checkpoints.add(
        Checkpoint(
            name=CHECKPOINT_NAME,
            validation_definitions=[vd],
            actions=[UpdateDataDocsAction(name="update_docs")],
            result_format={"result_format": "SUMMARY"},
        )
    )

    return checkpoint.run()


def main():
    print(f"GE version: {gx.__version__}")
    print(f"Project root: {PROJECT_ROOT}")

    context = get_context()
    print(f"Context initialised at: {GX_DIR}")

    batch_def = register_data_source(context)
    print(f"Registered data source '{DATA_SOURCE_NAME}' -> asset '{DATA_ASSET_NAME}' -> batch '{BATCH_DEF_NAME}'")

    suite = build_suite(context)
    print(f"Created suite '{SUITE_NAME}' with {len(suite.expectations)} expectations")

    result = build_and_run_checkpoint(context, batch_def, suite)
    print("\n=== Checkpoint result ===")
    print(f"Success: {result.success}")

    # Build Data Docs explicitly so the HTML site is regenerated.
    context.build_data_docs()
    docs_sites = context.get_docs_sites_urls()
    print("\nData Docs:")
    for s in docs_sites:
        print(f"  - {s.get('site_name')}: {s.get('site_url')}")

    # Persist a JSON copy of the run result for the report.
    out_json = os.path.join(PROJECT_ROOT, "docs", "validation_result.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    import json
    with open(out_json, "w") as f:
        json.dump(result.describe_dict(), f, indent=2, default=str)
    print(f"\nWrote summary: {out_json}")


if __name__ == "__main__":
    main()
