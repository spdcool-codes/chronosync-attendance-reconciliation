# ChronoSync | AI-Powered Attendance Reconciliation Engine

Built at Tata Consultancy Services to automate a client's L&D attendance correction process.

## The problem
Learners submitted attendance corrections in an Excel form with messy entries: mixed time formats, several missed periods in one cell, and partial or comment-only rows. Turning these into an upload-ready missed time file was manual and repetitive.

## What it does
1. Reads the attendance corrections form
2. Validates each entry
3. Maps learners to User IDs
4. Normalizes times to MM/DD/YYYY HH:MM
5. Fills the missed time template, ready for upload

It also produces a per-learner validation report and summary counts.

## Impact
Processing time cut from about 30 minutes of manual work to about 30 seconds per run.

## Sample data
The sample workbook covers 40 learners across four program formats (1, 2, 4 and 5 days), with up to three missed periods per learner per day.

- 59 form rows received, 59 missed-time instances extracted
- 23 learners with missed time, 14 with multiple missed occurrences

## Files
- `ChronoSync_Project_Sample_with_Cover.pdf`: quick-view version of the full workbook
- `ChronoSync_Sample_Workbook.xlsx`: the full workbook with formulas, dashboard and analysis

## Tech
Prompt Engineering, Microsoft Copilot, Claude, Python (pandas)

> All names, emails and IDs are fictional sample data. No client data is included.
