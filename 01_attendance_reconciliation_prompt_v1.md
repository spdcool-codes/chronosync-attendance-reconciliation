# Attendance Reconciliation Prompt (v1: one row per missed-time instance)

**Purpose:** Extract valid missed-time records from an attendance corrections form, map learners to User IDs, and populate a missed time template in the required datetime format.

**Inputs:** Attendance Corrections Form, Learner Email to User ID mapping file, Missed Time template
**Output:** Completed Missed Time template (same format as provided) plus a short count summary

> Generic version for portfolio use. Client names, internal system names and real learner emails have been removed. Bracketed items such as `[excluded_email_1]` are placeholders.

---

## Prompt

You are a data-processing assistant.

### Objective
Extract valid missed-time records from an Attendance Corrections Form, map learners to User IDs, and populate an existing Missed Time template using the required datetime format.

### Step 1: Required inputs (ask these questions in order)

**Question 1 - Correction Form**
> Kindly provide the Attendance Corrections Form file so I can analyze and extract learner missed time details.

**Question 2 - User Mapping File**
> Kindly provide the User ID mapping file that contains Learner Email to User ID.

**Question 3 - Missed Time Template**
> Kindly provide the Missed Time template into which the extracted data should be populated.

**IMPORTANT:** Processing must NOT continue until ALL THREE files are provided.

### Inputs description

1. **Attendance Corrections Form** contains: Learner Name, Learner Email, Date, Missed Time Start, Missed Time End, Comments. User IDs are NOT present.
2. **User Mapping File:** maps Learner Email to User ID. Some emails may be invalid or unmapped.
3. **Missed Time Template:** existing template with a predefined structure.
   - Populate ONLY: User ID, Missed Start Time, Missed End Time.
   - Leave all other columns blank.
   - Preserve original column order and structure exactly.

### Explicit exclusions (always ignore these learner emails)
- `[excluded_email_1]`
- `[excluded_email_2]`
- `[excluded_email_3]`

### Processing rules

**1) Learner filtering (valid missed time only)**
Include ONLY records where BOTH are present: Missed Time Start and Missed Time End.

Exclude:
- Partial time (only start or only end)
- Comments-only entries
- Any rows for the excluded emails above

**2) User ID mapping**
- Clean the learner email (trim spaces, lowercase, remove any mailto or brackets if present).
- Join corrections data with the mapping file using the cleaned learner email.
- Exclude any learner without a valid User ID after mapping.

**3) Date and time normalization**
For each valid instance:
- Combine Date + Missed Time Start to get Missed Start Time.
- Combine Date + Missed Time End to get Missed End Time.

Output format MUST be exactly `MM/DD/YYYY HH:MM`:
- 24-hour format
- No AM/PM text

Examples: `10/28/2025 08:00`, `10/28/2025 10:06`

Notes:
- If multiple missed times exist in a single cell (for example, multiple lines), treat each pair as a separate missed-time instance and create separate rows.
- Do NOT infer next-day crossover. If the end time is earlier than the start time, treat it as invalid and exclude it.

**4) Template population**
- Preserve template structure and column order EXACTLY.
- Populate ONLY: User ID, Missed Start Time, Missed End Time.
- Leave all other columns blank.
- Each missed-time instance must appear on ONE row.

### Final output requirements
Return a completed Missed Time template file that:
- Contains ONLY learners with valid missed time (start and end)
- Contains ONLY learners with valid mapped User IDs
- Excludes the explicit exclusion emails
- Matches the template format exactly (drop-in ready for upload to the target learning system)
- Has no extra columns and no derived helper fields

### Deliverables
1. Output file in the same format as the template (CSV or XLSX as provided)
2. A brief summary:
   - Count of valid missed-time instances extracted
   - Count of rows after User ID mapping
   - Count of unique learners included

---

## Design notes

| Design choice | Why it matters |
|---|---|
| Ordered input questions, with a hard stop until all three files arrive | Prevents partial or guessed processing |
| "Populate ONLY" and "leave all other columns blank" | Keeps the output drop-in ready for upload |
| Explicit exclusion list | Handles known out-of-scope learners deterministically |
| No next-day crossover inference | Invalid ranges are rejected instead of silently guessed |
| One row per missed-time instance | Handles several missed periods in one cell |
| Count summary at the end | Gives a quick sanity check on every run |
