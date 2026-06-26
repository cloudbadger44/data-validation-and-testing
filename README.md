#  — Data Validation & Testing

Great Expectations + pytest pipeline for validating a messy customer dataset.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Initialize GE, create the suite, run the checkpoint, build HTML docs
python setup_ge.py

# 2. Run unit tests
pytest -v

# 3. Open the Data Docs in a browser
open gx/uncommitted/data_docs/local_site/index.html
```

## Layout

```
.
├── data/customer_data.csv          # the messy dataset under test
├── src/data_utils.py               # load_csv, clean_phone, validate_email
├── tests/test_data_utils.py        # pytest suite (50 tests)
├── setup_ge.py                     # GE bootstrap + run
├── dq_report.py                    # standalone DQ counter
├── gx/                             # GE config + generated Data Docs
├── docs/                           # validation JSON + HTML copy
├── screenshots/                    # report screenshots
├── assignment2_report.md           # submission report
└── requirements.txt
```

## Expectations

The `customer_data_expectations` suite checks:

1. `customer_id` is unique
2. `customer_id` is not null
3. `age` is between 0 and 120
4. `email` matches a valid format
5. `salary` is present in at least 95% of rows
6. `country` ∈ {USA, Canada, UK, Australia}
7. `signup_date` parses as `%m/%d/%Y`
8. Table row count is between 500 and 1000
