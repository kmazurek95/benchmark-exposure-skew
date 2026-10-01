"""Derived checks: two descriptive numbers the write-up uses that no other script
emits.

  1. Wage bill. The sum of employment times mean annual wage over GDPval's 44
     occupations, against the national wage bill (the published All Occupations
     employment times the published national mean wage). The 44's wage bill is
     what GDPval's "$3T annually" refers to, so it doubles as a reproduction
     check; GDPval's own Table 1 figures (carried in the mapping CSV) are summed
     alongside for comparison.
  2. Random-draw baseline. How much employment 44 occupations cover when drawn
     uniformly, without replacement and without regard to size: economy-wide
     (the 831 detailed OEWS occupations) and within GDPval's nine sectors (the
     same modal-sector population within_sector.py uses).

Both are descriptive baselines, not hypothesis tests. GDPval's 44 were chosen by
a documented rule, not sampled, so the draws show what size-blind selection would
cover; they do not test whether GDPval's coverage arose by chance.

Run: python src/derived_checks.py   (needs oesm24nat.zip, oesm24in4.zip, and the
     outputs of tier1_coverage.py and within_sector.py)
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import paths
import oews
import sectors

SEED = 20261001
N_DRAWS = 200_000
K = 44


def draw_shares(emp: np.ndarray, denom: float, rng: np.random.Generator) -> np.ndarray:
    """Employment share covered by K occupations drawn uniformly without
    replacement, repeated N_DRAWS times."""
    n = len(emp)
    return np.array([emp[rng.choice(n, K, replace=False)].sum()
                     for _ in range(N_DRAWS)]) / denom


def draw_block(shares: np.ndarray, pool: str, n_pool: int, denom: float,
               denom_label: str, gdpval_share: float) -> dict:
    return {
        "pool": pool,
        "n_pool": int(n_pool),
        "k": K,
        "n_draws": N_DRAWS,
        "seed": SEED,
        "denominator": denom_label,
        "denominator_employment": int(denom),
        "mean_share": round(float(shares.mean()), 4),
        "median_share": round(float(np.median(shares)), 4),
        "p95_share": round(float(np.percentile(shares, 95)), 4),
        "max_share": round(float(shares.max()), 4),
        "gdpval44_share": gdpval_share,
        "n_draws_at_or_above_gdpval44": int((shares >= gdpval_share).sum()),
    }


def main() -> int:
    try:
        nat = oews.load_national()
    except FileNotFoundError as e:
        print("[derived] OEWS cross-industry not present.\n", e); return 3
    if not paths.OEWS_IND_ZIP.exists():
        print("[derived] OEWS industry file (oesm24in4.zip) not present."); return 3
    if not (paths.TIER1_SUMMARY.exists() and paths.WITHIN_SECTOR_SUMMARY.exists()):
        print("[derived] run tier1_coverage.py and within_sector.py first."); return 3

    t1 = json.loads(paths.TIER1_SUMMARY.read_text(encoding="utf-8"))
    ws = json.loads(paths.WITHIN_SECTOR_SUMMARY.read_text(encoding="utf-8"))

    det = oews.detailed(nat)
    total = nat[nat["OCC_CODE"].astype(str).str.strip() == "00-0000"].iloc[0]
    total_emp = float(total["TOT_EMP"])
    total_mean_wage = float(total["A_MEAN"])

    # GDPval's 44 -> the codes OEWS publishes (Buyers 13-1021/22/23 -> 13-1020).
    mp = pd.read_csv(paths.MAPPING_CSV, dtype=str)
    oews_codes = set(det["OCC_CODE"])

    def resolve(soc):
        if soc in oews_codes:
            return soc
        broad = soc[:6] + "0"
        return broad if broad in oews_codes else None

    mp["oews_code"] = [resolve(s) for s in mp["soc_2018"]]
    gd_codes = sorted(set(mp["oews_code"].dropna()))
    g = det[det["OCC_CODE"].isin(gd_codes)]
    gd_emp = float(g["TOT_EMP"].sum())

    # --- 1. Wage bill ---
    gd_wage_bill = float((g["TOT_EMP"] * g["A_MEAN"]).sum())
    nat_wage_bill = total_emp * total_mean_wage
    table1 = (mp.drop_duplicates("gdpval_title")["total_compensation_usd_billions"]
                .astype(float).sum())

    # --- 2. Random-draw baselines ---
    # Economy-wide: the 831 detailed occupations, against the primary Tier 1
    # denominator (detailed employment including "All Other").
    det_emp = det["TOT_EMP"].to_numpy(float)
    det_total = float(det_emp.sum())
    econ = draw_shares(det_emp, det_total, np.random.default_rng(SEED))

    # Within nine: same population as within_sector.py (detailed occupations
    # whose modal OEWS sector is one of GDPval's nine).
    modal = sectors.assign_modal_sectors()
    in_nine = set(modal.loc[modal["in_nine"], "OCC_CODE"])
    S = det.dropna(subset=["TOT_EMP"])
    S = S[S["OCC_CODE"].isin(in_nine)]
    S_emp = S["TOT_EMP"].to_numpy(float)
    S_total = float(S_emp.sum())
    nine = draw_shares(S_emp, S_total, np.random.default_rng(SEED))

    gd_share_econ = t1["coverage"]["share_of_detailed_incl_all_other"]
    gd_share_nine = ws["tier1_within_sector"]["coverage_share_of_nine_sectors"]

    summary = {
        "oews_source": nat.attrs["source"],
        "inputs": [
            "data/raw/oesm24nat.zip (OEWS May 2024 national, national_M2024_dl.xlsx)",
            "data/raw/oesm24in4.zip (OEWS May 2024 national industry, natsector member; "
            "modal-sector assignment via src/sectors.py, as in within_sector.py)",
            "outputs/gdpval_44_soc_mapping.csv",
            "outputs/tier1_coverage_summary.json",
            "outputs/within_sector_summary.json",
        ],
        "note": ("Descriptive baselines, not hypothesis tests. GDPval's 44 occupations "
                 "were chosen by a documented rule, not sampled; the random draws show "
                 "what 44 occupations chosen without regard to size would cover. The "
                 "national wage bill covers OEWS wage and salary jobs only (the OEWS "
                 "universe excludes the self-employed)."),
        "consistency": {
            "gdpval44_employment": int(gd_emp),
            "matches_tier1_summary": int(gd_emp) == t1["gdpval44_employment"],
            "within_nine_employment": int(S_total),
            "matches_within_sector_summary":
                int(S_total) == ws["tier1_within_sector"]["within_sector_employment"],
        },
        "gdpval44_wage_bill": {
            "definition": "sum over GDPval's 44 OEWS occupations of TOT_EMP x A_MEAN",
            "usd": int(round(gd_wage_bill)),
            "usd_trillions": round(gd_wage_bill / 1e12, 4),
            "gdpval_table1_sum_usd_billions": round(float(table1), 1),
        },
        "national_wage_bill": {
            "definition": "published All Occupations (00-0000) TOT_EMP x published A_MEAN",
            "total_employment": int(total_emp),
            "mean_annual_wage": total_mean_wage,
            "usd": int(round(nat_wage_bill)),
            "usd_trillions": round(nat_wage_bill / 1e12, 4),
        },
        "gdpval44_share_of_national_wage_bill": round(gd_wage_bill / nat_wage_bill, 4),
        "random_draw_baseline": draw_block(
            econ, "OEWS detailed occupations (including 'All Other')", len(det_emp),
            det_total, "detailed employment including 'All Other' (Tier 1 primary)",
            gd_share_econ),
        "random_draw_within_nine": draw_block(
            nine, "detailed occupations whose modal sector is one of GDPval's nine",
            len(S_emp), S_total, "within-nine employment (within_sector.py)",
            gd_share_nine),
    }
    paths.DERIVED_CHECKS.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # --- Report ---
    print(f"OEWS source: {nat.attrs['source']}")
    print(f"\nGDPval-44 wage bill:   ${gd_wage_bill / 1e12:.4f}T "
          f"(GDPval Table 1 sums to ${table1:,.1f}B)")
    print(f"National wage bill:    ${nat_wage_bill / 1e12:.4f}T "
          f"({total_emp:,.0f} x ${total_mean_wage:,.0f})")
    print(f"Share:                 {gd_wage_bill / nat_wage_bill:.1%}")
    for label, block in (("Economy-wide", summary["random_draw_baseline"]),
                         ("Within nine", summary["random_draw_within_nine"])):
        print(f"\n{label}: {K} of {block['n_pool']} occupations, {N_DRAWS:,} draws, "
              f"seed {SEED}")
        print(f"  mean {block['mean_share']:.1%} | median {block['median_share']:.1%} | "
              f"95th pct {block['p95_share']:.1%} | max {block['max_share']:.1%}")
        print(f"  draws at or above GDPval's {block['gdpval44_share']:.1%}: "
              f"{block['n_draws_at_or_above_gdpval44']}")
    c = summary["consistency"]
    if not (c["matches_tier1_summary"] and c["matches_within_sector_summary"]):
        print("\nWARNING: employment totals do not match the committed summaries:", c)
    print(f"\nWrote {paths.DERIVED_CHECKS.relative_to(paths.ROOT)}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(paths.ROOT / "src"))
    raise SystemExit(main())
