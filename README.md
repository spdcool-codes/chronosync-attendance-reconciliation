# ChronoSync | AI-Powered Attendance Reconciliation Engine

Built at Tata Consultancy Services to automate a client's L&D attendance correction process.

## The problem
Learners submitted attendance corrections in an Excel form with messy entries: mixed time formats, several missed periods in one cell, and partial or comment-only rows. Turning these into an upload-ready missed time file was manual and repetitive.

## What it does
1. Reads the attendance corrections form
2. Validates each entry (start and end both present, end not earlier than start)
3. Maps learners to User IDs using the cleaned email
4. Normalizes times to `MM/DD/YYYY HH:MM`
5. Fills the missed time template, one row per missed-time instance

It also produces a per-learner validation report and summary counts.

## Impact
Processing time cut from about 30 minutes of manual work to about 30 seconds per run.

## How it works
The tool is driven by a structured prompt that asks for three inputs in order (corrections form, User ID mapping file, missed time template), then applies explicit rules for filtering, ID mapping, datetime normalization and template population. Two generic prompt versions are included in [`prompts/`](prompts/):

| Version | Output shape | Notes |
|---|---|---|
| [v1](prompts/01_attendance_reconciliation_prompt_v1.md) | One row per missed-time instance | Maps learners to User IDs using a mapping file |
| [v2](prompts/02_attendance_reconciliation_prompt_v2.md) | One row per learner, with comma-separated start and end times | Groups by learner email, leaves IDs untouched, adds a validation report and summary counts |

Both versions are also implemented as a Python (pandas) pipeline in [`src/missed_time_pipeline.py`](src/missed_time_pipeline.py): `run()` for v1 and `run_v2()` for v2.

## Run it
```bash
pip install -r requirements.txt
```
```python
from src.missed_time_pipeline import run
# v1: one row per missed-time instance, with User ID mapping
run("Corrections.xlsx", "Email_to_UserID.xlsx", "MissedTimeTemplate.csv", "MissedTime_Populated.csv")

# v2: one row per learner (comma-separated times) plus a validation report
run_v2("Corrections.xlsx", "MissedTimeTemplate.csv", "MissedTime_Populated.csv", "Validation_Report.csv")
```
Adjust the header names in `FORM_HEADER_KEYWORDS` to match your own corrections form, and add any learner emails to skip in `Config.excluded_emails`.

## Sample data
The sample workbook covers 40 learners across four program formats (1, 2, 4 and 5 days), with up to three missed periods per learner per day.

- 59 missed-time instances extracted
- 23 learners with missed time, 14 with multiple missed occurrences

## Repository contents
| Path | Description |
|---|---|
| [`docs/ChronoSync_Project_Sample_with_Cover.pdf`](docs/ChronoSync_Project_Sample_with_Cover.pdf) | Quick-view PDF of the full workbook |
| [`data/ChronoSync_Sample_Workbook.xlsx`](data/ChronoSync_Sample_Workbook.xlsx) | Full workbook with formulas, dashboard and analysis |
| [`prompts/`](prompts/) | Generic versions of both prompts (v1 and v2) |
| [`src/missed_time_pipeline.py`](src/missed_time_pipeline.py) | Python (pandas) pipeline: ingest, validate, map, output |
| [`requirements.txt`](requirements.txt) | Python dependencies |

## Tech
Prompt Engineering, Microsoft Copilot, Claude, Python (pandas)

> All names, emails and IDs are fictional sample data. No client data is included.
