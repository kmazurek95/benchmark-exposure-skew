"""Loader for BLS OEWS May 2024 national cross-industry estimates.

Consumes either the raw download (data/raw/oesm24nat.zip) or an already-extracted
copy under data/raw/oesm24nat/. The national cross-industry workbook is
`national_M2024_dl.xlsx`; its schema is stable across recent OEWS vintages.

OEWS special value conventions handled here:
  TOT_EMP  '**'  -> employment not released (NaN)
  wages    '*'   -> wage not available (NaN)
  wages    '#'   -> at/above the disclosure cap ($115.00/hr, $239,200/yr).
                    Kept as the cap value, with a boolean *_capped flag, because
                    dropping the highest-wage cells would bias the wage
                    distribution downward exactly where GDPval's frame sits.

Exposes:
  load_national()   -> DataFrame of all rows (cleaned numeric columns)
  detailed(df)      -> O_GROUP == 'detailed' rows (the occupation universe)
  total_employment(df) -> scalar TOT_EMP for OCC_CODE 00-0000
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

import paths

WAGE_ANNUAL_CAP = 239_200.0   # BLS '#' disclosure cap, annual
WAGE_HOURLY_CAP = 115.0       # BLS '#' disclosure cap, hourly

_NUM_COLS = ["TOT_EMP", "H_MEAN", "A_MEAN", "H_PCT10", "H_PCT25", "H_MEDIAN",
             "H_PCT75", "H_PCT90", "A_PCT10", "A_PCT25", "A_MEDIAN", "A_PCT75",
             "A_PCT90", "JOBS_1000", "LOC_QUOTIENT", "PCT_TOTAL", "EMP_PRSE",
             "MEAN_PRSE"]
_WAGE_COLS = ["H_MEAN", "A_MEAN", "H_PCT10", "H_PCT25", "H_MEDIAN", "H_PCT75",
              "H_PCT90", "A_PCT10", "A_PCT25", "A_MEDIAN", "A_PCT75", "A_PCT90"]


def _find_workbook() -> tuple[str, bytes]:
    """Return (source_label, xlsx_bytes) from the extracted dir or the zip."""
    if paths.OEWS_DIR.exists():
        xlsx = sorted(paths.OEWS_DIR.rglob("*national_M2024_dl.xlsx")) or \
               sorted(paths.OEWS_DIR.rglob("*.xlsx"))
        if xlsx:
            return str(xlsx[0].relative_to(paths.ROOT)), xlsx[0].read_bytes()
    zip_path = paths.RAW / "oesm24nat.zip"
    if zip_path.exists() and zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
            pick = next((n for n in names if "national_m2024_dl" in n.lower()), None) \
                or (names[0] if names else None)
            if pick is None:
                raise FileNotFoundError("No .xlsx inside oesm24nat.zip")
            return f"oesm24nat.zip::{pick}", z.read(pick)
    # A present-but-invalid oesm24nat.zip (e.g. a leftover HTML error page) is
    # treated as not-yet-acquired, not a crash.
    raise FileNotFoundError(
        "OEWS May 2024 national file not found. Download "
        "https://www.bls.gov/oes/special-requests/oesm24nat.zip and place it at "
        f"{(paths.RAW / 'oesm24nat.zip')} (or extract to {paths.OEWS_DIR}).")


def _coerce_numeric(s: pd.Series, is_wage: bool) -> tuple[pd.Series, pd.Series]:
    """Return (values, capped_flag). '#' -> cap (wages only); '*','**' -> NaN."""
    raw = s.astype(str).str.strip()
    capped = raw.eq("#") & is_wage
    # OEWS suppression / flag markers -> NaN (never zero). '#' handled via cap below.
    cleaned = raw.replace({"*": np.nan, "**": np.nan, "***": np.nan, "#": np.nan,
                           "~": np.nan, "": np.nan, "nan": np.nan, "None": np.nan})
    cleaned = cleaned.str.replace(",", "", regex=False)
    vals = pd.to_numeric(cleaned, errors="coerce")
    if is_wage:
        cap = WAGE_ANNUAL_CAP if s.name.startswith("A_") else WAGE_HOURLY_CAP
        vals = vals.where(~capped, cap)
    return vals, capped


def load_national() -> pd.DataFrame:
    label, data = _find_workbook()
    df = pd.read_excel(io.BytesIO(data))
    df.columns = [str(c).strip().upper() for c in df.columns]
    for col in _NUM_COLS:
        if col in df.columns:
            vals, capped = _coerce_numeric(df[col], is_wage=col in _WAGE_COLS)
            df[col] = vals
            if col in _WAGE_COLS:
                df[col + "_CAPPED"] = capped
    df.attrs["source"] = label
    return df


def detailed(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["O_GROUP"].astype(str).str.lower() == "detailed"].copy()
    d["OCC_CODE"] = d["OCC_CODE"].astype(str).str.strip()
    return d


def total_employment(df: pd.DataFrame) -> float:
    row = df[df["OCC_CODE"].astype(str).str.strip() == "00-0000"]
    if len(row):
        return float(row["TOT_EMP"].iloc[0])
    return float(detailed(df)["TOT_EMP"].sum())


def is_all_other(occ_title: pd.Series) -> pd.Series:
    return occ_title.astype(str).str.strip().str.endswith("All Other")


if __name__ == "__main__":
    df = load_national()
    d = detailed(df)
    print("source:", df.attrs["source"])
    print("rows:", len(df), "| detailed occupations:", len(d))
    print("total employment (00-0000):", f"{total_employment(df):,.0f}")
    print("sum of detailed TOT_EMP:    ", f"{d['TOT_EMP'].sum():,.0f}")
    print("detailed 'All Other' occs:  ", int(is_all_other(d['OCC_TITLE']).sum()))
    print("wage cells at disclosure cap (#):",
          int(d.get("A_MEAN_CAPPED", pd.Series(dtype=bool)).sum()))
