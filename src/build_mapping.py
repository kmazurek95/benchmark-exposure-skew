"""Build and verify the GDPval-44 -> 2018 SOC mapping (Tier-1 spine input).

GDPval's occupation titles are abbreviated display forms of standard 2018-SOC
titles (the frame is 2018-SOC-native via the May 2024 OEWS). This script assigns
each of the 44 a 2018 SOC 6-digit code, then re-verifies every assigned code
against the O*NET-SOC 2019 taxonomy on disk -- codes are checked, not asserted
from memory. Judgment calls are flagged and written to a log.

Outputs:
  outputs/gdpval_44_soc_mapping.csv   one row per (gdpval title, 2018 SOC code)
  outputs/gdpval_44_soc_mapping_log.md  human-readable judgment-call log

Run: python src/build_mapping.py
"""
from __future__ import annotations

import sys
import pandas as pd

import paths  # noqa: E402  (src/ is on sys.path when run as a script)


# --- The assignment. Keyed by the EXACT verbatim GDPval display title so the
# --- join to the source CSV is exact. Codes from FEASIBILITY.md Appendix A,
# --- re-verified below against the O*NET-SOC 2019 taxonomy.
# status: "clean"  = single detailed 2018-SOC code, unambiguous
#         "broad"  = a 2018-SOC broad group; expanded to its detail codes here
MAPPING: dict[str, dict] = {
    # Real Estate and Rental and Leasing
    "Property/RE/Community Association Managers": dict(soc="11-9141", status="clean"),
    "Counter and Rental Clerks":                  dict(soc="41-2021", status="clean"),
    "Real Estate Sales Agents":                   dict(soc="41-9022", status="clean"),
    "Real Estate Brokers":                        dict(soc="41-9021", status="clean"),
    "Concierges":                                 dict(soc="39-6012", status="clean"),
    # Manufacturing
    "First-Line Supervisors of Production and Operating Workers": dict(soc="51-1011", status="clean"),
    "Buyers and Purchasing Agents": dict(
        soc="13-1020", status="broad",
        detail=["13-1021", "13-1022", "13-1023"],
        note="2018 SOC broad group (no single detailed code). Aggregate the three "
             "detail codes by OEWS employment weight for any per-occupation measure.",
    ),
    "Shipping, Receiving, and Inventory Clerks":  dict(soc="43-5071", status="clean",
        note="2010 SOC title was 'Shipping, Receiving, and Traffic Clerks'; same code."),
    "Industrial Engineers":                       dict(soc="17-2112", status="clean"),
    "Mechanical Engineers":                       dict(soc="17-2141", status="clean"),
    # Professional, Scientific, and Technical Services
    "Software Developers": dict(soc="15-1252", status="clean",
        note="2018 code. Bridging to 2010 AIOE = merge of 15-1132 + 15-1133."),
    "Lawyers":                                    dict(soc="23-1011", status="clean"),
    "Accountants and Auditors":                   dict(soc="13-2011", status="clean"),
    "Computer and Information Systems Managers":  dict(soc="11-3021", status="clean"),
    "Project Management Specialists": dict(soc="13-1082", status="clean",
        note="New in 2018 SOC; in 2010 these sat inside 13-1199 (Business Operations "
             "Specialists, All Other). Bridging to 2010 AIOE requires imputation."),
    # Government
    "Compliance Officers":                        dict(soc="13-1041", status="clean"),
    "Administrative Services Managers": dict(soc="11-3012", status="clean",
        note="2010 11-3011 split into 11-3012 + 11-3013; inherit 11-3011's 2010 score."),
    "Child, Family, and School Social Workers":   dict(soc="21-1021", status="clean"),
    "First-Line Supervisors of Police and Detectives": dict(soc="33-1012", status="clean"),
    "Recreation Workers":                         dict(soc="39-9032", status="clean"),
    # Health Care and Social Assistance
    "Registered Nurses":                          dict(soc="29-1141", status="clean"),
    "First-Line Supervisors of Office/Admin Support": dict(soc="43-1011", status="clean"),
    "Medical & Health Services Managers":         dict(soc="11-9111", status="clean"),
    "Nurse Practitioners":                        dict(soc="29-1171", status="clean"),
    "Medical Secretaries & Admin Assistants":     dict(soc="43-6013", status="clean"),
    # Finance and Insurance
    "Financial Managers":                         dict(soc="11-3031", status="clean"),
    "Customer Service Representatives":           dict(soc="43-4051", status="clean"),
    "Securities, Commodities, and Financial Services Sales Agents": dict(soc="41-3031", status="clean"),
    "Personal Financial Advisors":                dict(soc="13-2052", status="clean"),
    "Financial and Investment Analysts": dict(soc="13-2051", status="clean",
        note="Minor 2010->2018 scope change (13-2054 Financial Risk Specialists split off); code stable."),
    # Retail Trade
    "General & Operations Managers":              dict(soc="11-1021", status="clean"),
    "1st-Line Supervisors of Retail Sales Workers": dict(soc="41-1011", status="clean"),
    "Pharmacists":                                dict(soc="29-1051", status="clean"),
    "Private Detectives & Investigators":         dict(soc="33-9021", status="clean"),
    # Wholesale Trade
    "Sales Reps, Wholesale & Mfg (Except Tech/Scientific)": dict(soc="41-4012", status="clean"),
    "Sales Managers":                             dict(soc="11-2022", status="clean"),
    "Sales Reps, Wholesale & Mfg (Tech/Scientific)": dict(soc="41-4011", status="clean"),
    "1st-Line Supervisors of Non-Retail Sales Workers": dict(soc="41-1012", status="clean"),
    "Order Clerks":                               dict(soc="43-4151", status="clean"),
    # Information
    "Producers & Directors":                      dict(soc="27-2012", status="clean"),
    "Editors":                                    dict(soc="27-3041", status="clean"),
    "News Analysts, Reporters, and Journalists": dict(soc="27-3023", status="clean",
        note="2018 merge of 2010 27-3021 (Broadcast News Analysts) + 27-3022 (Reporters)."),
    "Audio & Video Technicians":                  dict(soc="27-4011", status="clean"),
    "Film & Video Editors":                       dict(soc="27-4032", status="clean"),
}


def load_onet_stems() -> pd.DataFrame:
    """O*NET-SOC 2019 taxonomy -> unique 6-digit SOC stems with a display title."""
    raw = pd.read_excel(paths.ONETSOC_2019, header=3)
    raw = raw.rename(columns={
        "O*NET-SOC 2019 Code": "onet_code",
        "O*NET-SOC 2019 Title": "onet_title",
    })
    raw = raw.dropna(subset=["onet_code"])
    raw["soc6"] = raw["onet_code"].str.slice(0, 7)  # "11-1011.00" -> "11-1011"
    # Prefer the base-level (.00) title as the canonical stem title where present.
    raw["is_base"] = raw["onet_code"].str.endswith(".00")
    raw = raw.sort_values("is_base", ascending=False)
    stems = raw.drop_duplicates("soc6")[["soc6", "onet_title"]].reset_index(drop=True)
    return stems


def main() -> int:
    gd = pd.read_csv(paths.GDPVAL_44)
    stems = load_onet_stems()
    stem_set = set(stems["soc6"])
    title_by_stem = dict(zip(stems["soc6"], stems["onet_title"]))

    # Sanity: every GDPval title in the source CSV must be in MAPPING.
    src_titles = list(gd["gdpval_display_title"])
    missing = [t for t in src_titles if t not in MAPPING]
    if missing:
        print("ERROR: source titles with no mapping entry:")
        for t in missing:
            print("   ", repr(t))
        return 1
    if len(MAPPING) != len(src_titles):
        print(f"WARN: MAPPING has {len(MAPPING)} entries, source CSV has {len(src_titles)}.")

    rows = []
    judgment = []  # (gdpval_title, kind, detail)
    unverified = []

    for _, r in gd.iterrows():
        title = r["gdpval_display_title"]
        m = MAPPING[title]
        # GDPval Table 1 compensation and sector GDP shares are OpenAI's own
        # published figures (the object of the critique), not redistributed
        # third-party data, so they stay in the tracked mapping.
        base = dict(
            sector=r["sector"],
            sector_pct_gdp=r["sector_pct_gdp"],
            gdpval_title=title,
            total_compensation_usd_billions=r["total_compensation_usd_billions"],
        )
        if m["status"] == "broad":
            judgment.append((title, "broad-group aggregation",
                             f"{m['soc']} -> {', '.join(m['detail'])} (employment-weighted)"))
            for i, dc in enumerate(m["detail"]):
                if dc not in stem_set:
                    unverified.append((title, dc))
                rows.append({**base,
                    "soc_2018": dc,
                    "soc_2018_title_onet": title_by_stem.get(dc, "<<NOT IN O*NET-SOC 2019>>"),
                    "status": "broad-detail",
                    "broad_group": m["soc"],
                    "is_primary_row": (i == 0),
                    "note": m.get("note", "")})
        else:
            soc = m["soc"]
            if soc not in stem_set:
                unverified.append((title, soc))
            if m.get("note"):
                judgment.append((title, "documented note", m["note"]))
            rows.append({**base,
                "soc_2018": soc,
                "soc_2018_title_onet": title_by_stem.get(soc, "<<NOT IN O*NET-SOC 2019>>"),
                "status": m["status"],
                "broad_group": "",
                "is_primary_row": True,
                "note": m.get("note", "")})

    out = pd.DataFrame(rows)
    out.to_csv(paths.MAPPING_CSV, index=False)

    # --- Report ---
    n_titles = len(src_titles)
    n_broad = sum(1 for m in MAPPING.values() if m["status"] == "broad")
    n_clean = n_titles - n_broad
    print(f"GDPval occupations mapped:            {n_titles}")
    print(f"  clean single-code (2018 SOC):       {n_clean}")
    print(f"  broad-group judgment calls:         {n_broad}")
    print(f"SOC rows written (broad expanded):    {len(out)}")
    print(f"Codes NOT found in O*NET-SOC 2019:    {len(unverified)}")
    for t, c in unverified:
        print(f"    !! {c}  ({t})")
    print(f"\nWrote {paths.MAPPING_CSV.relative_to(paths.ROOT)}")

    # --- Log ---
    lines = ["# GDPval-44 -> 2018 SOC mapping: judgment-call log", "",
             "Generated by `src/build_mapping.py`. Every 2018 SOC code below is "
             "verified to exist in the O\\*NET-SOC 2019 taxonomy "
             "(`data/raw/onetsoc2019.xlsx`, 2018-SOC basis).", "",
             f"- GDPval occupations: **{n_titles}**",
             f"- Clean single-code mappings: **{n_clean}**",
             f"- Broad-group judgment calls: **{n_broad}**",
             f"- Failed mappings (code absent from taxonomy): **{len(unverified)}**", "",
             "## Judgment calls and documented notes", ""]
    for title, kind, detail in judgment:
        lines.append(f"- **{title}** ({kind}): {detail}")
    lines += ["", "## Note on vintage",
              "All codes are at GDPval's native 2018-SOC vintage. Bridging to the "
              "2010-SOC exposure measures (AIOE) introduces additional reconciliations "
              "handled in `src/bridge_aioe.py`; see that log.", ""]
    paths.MAPPING_LOG.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {paths.MAPPING_LOG.relative_to(paths.ROOT)}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(paths.ROOT / "src"))
    raise SystemExit(main())
