"""
ChronoSync: missed time pipeline (ingestion -> validation -> mapping -> output)

Generic portfolio version. Client names, real learner emails and
client-specific form headers have been removed or replaced with placeholders.
Adjust FORM_HEADER_KEYWORDS and the column names below to match your own form.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple, Optional

import pandas as pd
import numpy as np


# -----------------------------
# CONFIG
# -----------------------------
@dataclass(frozen=True)
class Config:
    # Learner emails to always ignore (lowercase). Keep real emails out of source control.
    excluded_emails: set[str] = field(default_factory=set)
    out_dt_format: str = "%m/%d/%Y %H:%M"
    required_output_cols: Tuple[str, str, str] = ("User ID", "Missed Start Time", "Missed End Time")


# Header names used to locate the header row in the corrections form
FORM_HEADER_KEYWORDS = [
    "Session ID",
    "Learner Name",
    "Learner Email Address",
    "Date (MM/DD/YYYY)",
    "Missed Time Start",
    "Missed Time End",
]


# -----------------------------
# HELPERS
# -----------------------------
EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")

def clean_email(x: object) -> Optional[str]:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip().lower()
    s = s.replace("mailto:", "")
    m = EMAIL_RE.search(s)
    return m.group(1).lower() if m else None

def split_time_cell(x: object) -> List[str]:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return []
    s = str(x).strip()
    if not s or s.lower() == "nan":
        return []
    parts = re.split(r"[\n,]+", s)
    return [p.strip() for p in parts if p.strip()]

def parse_time_24h(t: str) -> Optional[Tuple[int, int]]:
    """
    Accepts '9am', '9:15am', '13:06', '10', '10:00', etc.
    Returns (hour, minute) in 24h.
    """
    tt = re.sub(r"\s+", "", str(t).strip().lower())
    if not tt:
        return None

    # 24h HH:MM
    m = re.match(r"^(\d{1,2}):(\d{2})$", tt)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return hh, mm
        return None

    # 12h / mixed: H, H:MM, with optional am/pm
    m = re.match(r"^(\d{1,2})(?::(\d{1,2}))?(am|pm)?$", tt)
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2)) if m.group(2) is not None else 0
    ampm = m.group(3)

    if mm < 0 or mm > 59:
        return None

    if ampm:
        if hh == 12:
            hh = 0
        if ampm == "pm":
            hh += 12

    if 0 <= hh <= 23:
        return hh, mm
    return None


# -----------------------------
# INGEST
# -----------------------------
def find_header_row(df: pd.DataFrame, keywords: List[str], scan_rows: int = 300) -> int:
    for i in range(min(scan_rows, len(df))):
        row = " | ".join(str(v) for v in df.iloc[i].tolist())
        hits = sum(1 for k in keywords if k in row)
        if hits >= 3:
            return i
    raise ValueError("Header row not found")

def load_corrections(path: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=0, dtype=str, engine="openpyxl")
    hdr = find_header_row(raw, FORM_HEADER_KEYWORDS)
    headers = raw.iloc[hdr].tolist()
    headers = [("Comments" if pd.isna(h) or str(h).strip().lower() == "nan" else str(h).strip()) for h in headers]
    df = raw.iloc[hdr + 1 :].copy()
    df.columns = headers
    return df

def load_mapping(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str, engine="openpyxl")
    df.columns = [c.strip() for c in df.columns]

    email_col = next((c for c in df.columns if "email" in c.lower()), df.columns[0])
    uid_col = next((c for c in df.columns if "id" in c.lower()), df.columns[1])

    out = df[[email_col, uid_col]].copy()
    out.columns = ["Learner Email", "User ID"]
    out["Learner Email"] = out["Learner Email"].map(clean_email)
    out["User ID"] = out["User ID"].astype(str).str.strip()
    out.loc[out["User ID"].isin(["", "nan", "None", "none", "NaN"]), "User ID"] = np.nan
    return out

def load_template(path: str) -> pd.DataFrame:
    if path.lower().endswith(".csv"):
        return pd.read_csv(path, dtype=str)
    return pd.read_excel(path, dtype=str, engine="openpyxl")


# -----------------------------
# TRANSFORM
# -----------------------------
def extract_valid_instances(corr: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    needed = ["Learner Email Address", "Date (MM/DD/YYYY)", "Missed Time Start", "Missed Time End"]
    for c in needed:
        if c not in corr.columns:
            corr[c] = np.nan

    corr = corr.copy()
    if "Learner Name" not in corr.columns:
        corr["Learner Name"] = np.nan
    corr["Learner Email"] = corr["Learner Email Address"].map(clean_email)
    corr["_date"] = pd.to_datetime(corr["Date (MM/DD/YYYY)"], errors="coerce")

    rows = []
    for _, r in corr.iterrows():
        email = r.get("Learner Email")
        if not email or email in cfg.excluded_emails:
            continue

        d = r.get("_date")
        if pd.isna(d):
            continue

        starts = split_time_cell(r.get("Missed Time Start"))
        ends = split_time_cell(r.get("Missed Time End"))

        # must have both
        if not starts or not ends:
            continue

        for s, e in zip(starts, ends):
            ps = parse_time_24h(s)
            pe = parse_time_24h(e)
            if not ps or not pe:
                continue

            sd = datetime(d.year, d.month, d.day, ps[0], ps[1])
            ed = datetime(d.year, d.month, d.day, pe[0], pe[1])

            # no cross-day inference
            if ed <= sd:
                continue

            rows.append({"Learner Name": r.get("Learner Name"), "Learner Email": email,
                         "missed_start": sd, "missed_end": ed})

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    out["Missed Start Time"] = pd.to_datetime(out["missed_start"]).dt.strftime(cfg.out_dt_format)
    out["Missed End Time"] = pd.to_datetime(out["missed_end"]).dt.strftime(cfg.out_dt_format)
    return out

def apply_mapping(missed: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    if missed.empty:
        return missed
    merged = missed.merge(mapping, how="left", on="Learner Email")
    merged = merged.dropna(subset=["User ID"]).copy()
    merged["User ID"] = merged["User ID"].astype(str).str.strip()
    return merged

def write_output(template: pd.DataFrame, mapped: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    out = pd.DataFrame(columns=template.columns)
    if mapped.empty:
        return out

    out["User ID"] = mapped["User ID"].astype(str)
    out["Missed Start Time"] = mapped["Missed Start Time"]
    out["Missed End Time"] = mapped["Missed End Time"]

    for c in out.columns:
        if c not in cfg.required_output_cols:
            out[c] = ""

    return out.fillna("")


# -----------------------------
# V2: ONE ROW PER LEARNER (comma-separated times)
# -----------------------------
def group_by_learner(missed: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Group instances by learner email, in chronological order, as comma-separated values."""
    cols = ["Learner Name", "Learner Email", "Missed Start Times", "Missed End Times", "Missed Instance Count"]
    if missed.empty:
        return pd.DataFrame(columns=cols)

    m = missed.sort_values(["Learner Email", "missed_start", "missed_end"])
    fmt = cfg.out_dt_format
    rows = []
    for email, g in m.groupby("Learner Email", sort=True):
        names = g["Learner Name"].dropna()
        rows.append({
            "Learner Name": str(names.iloc[0]).strip() if len(names) else "",
            "Learner Email": email,
            "Missed Start Times": ",".join(g["missed_start"].dt.strftime(fmt)),
            "Missed End Times": ",".join(g["missed_end"].dt.strftime(fmt)),
            "Missed Instance Count": len(g),
        })
    return pd.DataFrame(rows, columns=cols)

def populate_template_v2(template: pd.DataFrame, grouped: pd.DataFrame) -> pd.DataFrame:
    """
    Fill only column C (Missed Start Time) and column D (Missed End Time).
    No User IDs or Session Learning Object IDs are created or guessed.
    If the template has an email column, existing rows are matched by email;
    learners not found in the template are appended with only email + C/D filled.
    """
    cols = list(template.columns)
    if len(cols) < 4:
        raise ValueError("Template needs at least 4 columns (C and D are populated)")
    start_col, end_col = cols[2], cols[3]
    email_col = next((c for c in cols if "email" in c.lower()), None)

    out = template.copy().fillna("")
    if grouped.empty:
        return out

    if email_col is None:
        new = pd.DataFrame("", index=range(len(grouped)), columns=cols)
        new[start_col] = grouped["Missed Start Times"].values
        new[end_col] = grouped["Missed End Times"].values
        return pd.concat([out, new], ignore_index=True)

    lookup = grouped.set_index("Learner Email")
    keys = out[email_col].map(clean_email)
    hit = keys.isin(lookup.index)
    out.loc[hit, start_col] = keys[hit].map(lookup["Missed Start Times"])
    out.loc[hit, end_col] = keys[hit].map(lookup["Missed End Times"])

    missing = grouped[~grouped["Learner Email"].isin(set(keys.dropna()))]
    if not missing.empty:
        new = pd.DataFrame("", index=range(len(missing)), columns=cols)
        new[email_col] = missing["Learner Email"].values
        new[start_col] = missing["Missed Start Times"].values
        new[end_col] = missing["Missed End Times"].values
        out = pd.concat([out, new], ignore_index=True)
    return out

def run_v2(corrections_path: str, template_path: str, output_path: str, report_path: str,
           cfg: Optional[Config] = None) -> dict:
    cfg = cfg or Config()
    corr = load_corrections(corrections_path)
    template = load_template(template_path)

    missed = extract_valid_instances(corr, cfg)
    grouped = group_by_learner(missed, cfg)
    out = populate_template_v2(template, grouped)

    out.to_csv(output_path, index=False)
    grouped.to_csv(report_path, index=False)

    summary = {
        "total_learners_processed": int(len(grouped)),
        "total_missed_instances": int(grouped["Missed Instance Count"].sum()) if len(grouped) else 0,
        "learners_with_multiple_missed": int((grouped["Missed Instance Count"] > 1).sum()) if len(grouped) else 0,
    }
    print(summary)
    return summary


# -----------------------------
# ENTRYPOINT
# -----------------------------
def run(corrections_path: str, mapping_path: str, template_path: str, output_path: str) -> None:
    cfg = Config(
        excluded_emails={
            # "learner.one@example.com",
        }
    )

    corr = load_corrections(corrections_path)
    mapping = load_mapping(mapping_path)
    template = load_template(template_path)

    missed = extract_valid_instances(corr, cfg)
    mapped = apply_mapping(missed, mapping)
    out = write_output(template, mapped, cfg)

    if output_path.lower().endswith(".csv"):
        out.to_csv(output_path, index=False)
    else:
        out.to_excel(output_path, index=False, engine="openpyxl")


if __name__ == "__main__":
    # Example:
    # run("Corrections.xlsx", "Email_to_UserID.xlsx", "MissedTimeTemplate.csv", "MissedTime_Populated.csv")
    # run_v2("Corrections.xlsx", "MissedTimeTemplate.csv", "MissedTime_Populated.csv", "Validation_Report.csv")
    pass
