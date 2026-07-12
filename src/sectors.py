"""Modal-sector assignment, replicating GDPval's rule with OEWS industry data.

GDPval assigned each occupation to "the sector with the highest employment for
each occupation" using the 2023 National Employment Matrix (paper section 2.1 /
A.7). The 2023 matrix is not reachable, so this uses the vintage-consistent
May 2024 OEWS national industry-specific file (natsector member): occupation
employment across 20 mutually-exclusive NAICS sectors, one row per
occupation-sector (so no summation across OEWS combined-ownership OWN_CODEs is
needed and none is done; the per-sector rows already partition each occupation's
employment, and their sum reproduces the cross-industry total to within rounding).

Government is NAICS 99, the OEWS designation "Federal, State, and Local Government,
excluding State and Local Government Schools and Hospitals and the U.S. Postal
Service." This is a documented soft-spot, not a clean match: GDPval's Government is
a BEA / National-Employment-Matrix sector that INCLUDES public education and public
hospitals, so this OEWS Government is narrower. Government schools land in
Educational Services (NAICS 61, not one of GDPval's nine) and government hospitals
in Health Care (NAICS 62, which is one of the nine). The consequence is logged and
surfaced in the write-up; the validation below bounds its effect.

The assignment is validated against GDPval's own 44 (whose GDPval-assigned sector
is known) in validate_against_gdpval(): 42 of 44 land in their GDPval-assigned
sector.
"""
from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd

import paths

# GDPval's nine sectors <-> OEWS natsector NAICS codes.
GDPVAL_SECTOR_BY_NAICS = {
    "53": "Real Estate and Rental and Leasing",
    "31-33": "Manufacturing",
    "54": "Professional, Scientific, and Technical Services",
    "99": "Government",
    "62": "Health Care and Social Assistance",
    "52": "Finance and Insurance",
    "44-45": "Retail Trade",
    "42": "Wholesale Trade",
    "51": "Information",
}


def _clean_emp(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.strip().str.replace(",", "", regex=False)
         .replace({"*": np.nan, "**": np.nan, "***": np.nan, "~": np.nan,
                   "#": np.nan, "": np.nan, "nan": np.nan}),
        errors="coerce")


def load_sector_employment() -> pd.DataFrame:
    """Occupation x NAICS-sector employment (detailed occupations only)."""
    with zipfile.ZipFile(paths.OEWS_IND_ZIP) as z:
        df = pd.read_excel(io.BytesIO(z.read(paths.OEWS_IND_SECTOR_MEMBER)))
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df[df["O_GROUP"].astype(str).str.lower() == "detailed"].copy()
    df["OCC_CODE"] = df["OCC_CODE"].astype(str).str.strip()
    df["NAICS"] = df["NAICS"].astype(str).str.strip()
    df["TOT_EMP"] = _clean_emp(df["TOT_EMP"])
    return df[["OCC_CODE", "OCC_TITLE", "NAICS", "NAICS_TITLE", "TOT_EMP"]]


def assign_modal_sectors() -> pd.DataFrame:
    """One row per occupation: its modal NAICS sector and GDPval-sector label."""
    se = load_sector_employment().dropna(subset=["TOT_EMP"])
    # argmax sector by employment per occupation
    idx = se.groupby("OCC_CODE")["TOT_EMP"].idxmax()
    modal = se.loc[idx, ["OCC_CODE", "OCC_TITLE", "NAICS", "NAICS_TITLE", "TOT_EMP"]]
    modal = modal.rename(columns={"NAICS": "modal_naics",
                                  "NAICS_TITLE": "modal_naics_title",
                                  "TOT_EMP": "modal_sector_emp"})
    modal["gdpval_sector"] = modal["modal_naics"].map(GDPVAL_SECTOR_BY_NAICS)
    modal["in_nine"] = modal["gdpval_sector"].notna()
    # share of the occupation's (sector-summed) employment in its modal sector
    tot = se.groupby("OCC_CODE")["TOT_EMP"].sum()
    modal = modal.merge(tot.rename("sector_summed_emp"), on="OCC_CODE")
    modal["modal_share"] = modal["modal_sector_emp"] / modal["sector_summed_emp"]
    return modal.reset_index(drop=True)


def validate_against_gdpval(modal: pd.DataFrame) -> dict:
    """Do GDPval's 44 land in the sector GDPval assigned them?"""
    mp = pd.read_csv(paths.MAPPING_CSV, dtype=str)
    # Buyers 13-1021/22/23 -> OEWS publishes 13-1020; align to what natsector uses.
    modal_codes = set(modal["OCC_CODE"])

    def resolve(soc):
        if soc in modal_codes:
            return soc
        broad = soc[:6] + "0"
        return broad if broad in modal_codes else None

    mp["oews_code"] = [resolve(s) for s in mp["soc_2018"]]
    occ = (mp.dropna(subset=["oews_code"]).drop_duplicates("oews_code")
             [["oews_code", "gdpval_title", "sector"]])
    j = occ.merge(modal[["OCC_CODE", "gdpval_sector", "modal_naics_title", "modal_share"]],
                  left_on="oews_code", right_on="OCC_CODE", how="left")
    j["match"] = j["gdpval_sector"] == j["sector"]
    return {"n": len(j), "match": int(j["match"].sum()), "detail": j}


if __name__ == "__main__":
    m = assign_modal_sectors()
    print("occupations assigned:", len(m))
    print("in GDPval's 9 sectors:", int(m["in_nine"].sum()))
    print("\nby GDPval sector (modal):")
    print(m[m["in_nine"]]["gdpval_sector"].value_counts().to_string())
    v = validate_against_gdpval(m)
    print(f"\nValidation vs GDPval's own 44: {v['match']}/{v['n']} land in "
          f"GDPval's assigned sector")
    mism = v["detail"][~v["detail"]["match"]]
    if len(mism):
        print("\nMismatches (GDPval sector -> OEWS-modal sector):")
        for _, r in mism.iterrows():
            print(f"  {r['gdpval_title'][:40]:40} GDPval={r['sector'][:22]:22} "
                  f"OEWS-modal={str(r['gdpval_sector'])}")
