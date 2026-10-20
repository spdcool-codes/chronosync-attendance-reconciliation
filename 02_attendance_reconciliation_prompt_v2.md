# Attendance Reconciliation Prompt (v2: one row per learner)

**Purpose:** Read an attendance corrections workbook, group each learner's missed attendance periods, and populate a Missed Time file with comma-separated start and end times per learner, plus a validation report.

**Inputs:** Attendance Corrections workbook, Missed Time template
**Output:** Populated Missed Time CSV, validation report, and a short output summary

> Generic version for portfolio use. The client's program name has been removed from the first line. This is the updated prompt. See [v1](01_attendance_reconciliation_prompt_v1.md) for the earlier version.

---

## Prompt

Create a populated MissedTime file from the attached Attendance Corrections Form.

**Instructions:**

1. Read the Attendance Corrections workbook.
2. Identify all learners and their missed attendance records.
3. Group records by Learner Email Address.
4. Collect all missed attendance periods for each learner across all session days.
5. Merge all missed start times into a comma-separated value.
6. Merge all missed end times into a comma-separated value.
7. Maintain chronological order of missed times.
8. Populate only:
   - Column C = Missed Start Time
   - Column D = Missed End Time
9. Do not modify any other columns in the template.
10. Do not create or guess User IDs or Session Learning Object IDs.
11. Generate:
    - A populated MissedTime CSV file
    - A validation report showing:
        - Learner Name
        - Learner Email
        - Missed Start Times
        - Missed End Times
        - Missed Instance Count

**Output Summary:**
- Total learners processed
- Total missed attendance instances identified
- Number of learners with multiple missed attendance occurrences

---

## Design notes

| Design choice | Why it matters |
|---|---|
| Group by learner email | One template row per learner, matching templates that expect all of a learner's periods in a single row |
| Comma-separated start and end values, kept in chronological order | Start and end values stay aligned pair by pair |
| "Populate only" columns C and D, leave other columns untouched | Protects pre-filled template data |
| "Do not create or guess" IDs | IDs must come from the template or source system, never from the model |
| Separate validation report | Gives a per-learner audit trail for every run |
| Output summary counts | Quick sanity check on each run |
