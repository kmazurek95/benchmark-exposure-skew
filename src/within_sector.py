"""Within-sector baseline (Tiers 1 and 2): the fairer test.

Restricts the comparison to occupations whose modal sector (OEWS industry data,
src/sectors.py) is one of GDPval's nine, holding the sector gate constant. This is
the pre-registration's second baseline. Occupations are assigned to sectors at the
occupation level (each occupation belongs wholly to its modal sector, as GDPval
did) and weighted by their full cross-industry employment.

Reports, for both tiers, GDPval's 44 against the within-nine-sectors population,
alongside the modal-assignment validation (42/44 of GDPval's own occupations land
in their GDPval-assigned sector).

Run: python src/within_sector.py   (needs oesm24nat.zip, oesm24in4.zip, AIOE bridge)
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

import paths
import oews
import sectors
from tier1_coverage import weighted_quantile, weighted_mean, weighted_share_below
from tier2_aioe import build_oews_aioe


def gdpval_oews_codes(oews_codes: set) -> pd.DataFrame:
    mp = pd.read_csv(paths.MAPPING_CSV, dtype=str)

    def resolve(soc):
        if soc in oews_codes:
            return soc
        broad = soc[:6] + "0"
        return broad if broad in oews_codes else None

    mp["oews_code"] = [resolve(s) for s in mp["soc_2018"]]
    return mp


def main() -> int:
    try:
        nat = oews.load_national()
    except FileNotFoundError as e:
        print("[within] OEWS cross-industry not present.\n", e); return 3
    if not paths.OEWS_IND_ZIP.exists():
        print("[within] OEWS industry file (oesm24in4.zip) not present."); return 3

    modal = sectors.assign_modal_sectors()
    val = sectors.validate_against_gdpval(modal)
    in_nine = set(modal.loc[modal["in_nine"], "OCC_CODE"])

    det = oews.detailed(nat).dropna(subset=["TOT_EMP"]).copy()
    det["all_other"] = oews.is_all_other(det["OCC_TITLE"])
    bridged = pd.read_csv(paths.AIOE_BRIDGED_CSV, dtype={"soc2018": str})
    det = build_oews_aioe(det, bridged)

    # Within-sector population S: detailed occupations modally in GDPval's nine.
    S = det[det["OCC_CODE"].isin(in_nine)].copy()

    # GDPval's 44 -> OEWS codes
    mp = gdpval_oews_codes(set(det["OCC_CODE"]))
    gd_codes = sorted(set(mp["oews_code"].dropna()))
    g = det[det["OCC_CODE"].isin(gd_codes)].copy()
    # sanity: all 44 should be inside S
    gd_not_in_S = sorted(set(gd_codes) - in_nine)

    def dist_block(pop, wcol):
        v = pop[wcol].to_numpy(float); e = pop["TOT_EMP"].to_numpy(float)
        gv = g[wcol].to_numpy(float); ge = g["TOT_EMP"].to_numpy(float)
        q = [0.10, 0.25, 0.50, 0.75, 0.90]
        return {
            "baseline_percentiles": dict(zip([f"p{int(x*100)}" for x in q],
                                             [round(float(z), 4) for z in weighted_quantile(v, q, e)])),
            "gdpval_percentiles": dict(zip([f"p{int(x*100)}" for x in q],
                                           [round(float(z), 4) for z in weighted_quantile(gv, q, ge)])),
            "baseline_weighted_median": round(float(weighted_quantile(v, [0.5], e)[0]), 4),
            "gdpval_weighted_median": round(float(weighted_quantile(gv, [0.5], ge)[0]), 4),
            "baseline_weighted_mean": round(weighted_mean(v, e), 4),
            "gdpval_weighted_mean": round(weighted_mean(gv, ge), 4),
            "gdpval_median_percentile_in_baseline": round(
                weighted_share_below(float(weighted_quantile(gv, [0.5], ge)[0]), v, e), 4),
        }

    # Tier 1 within-sector: coverage + wage
    S_emp = float(np.nansum(S["TOT_EMP"]))
    gd_emp = float(np.nansum(g["TOT_EMP"]))
    tier1 = {
        "within_sector_employment": int(S_emp),
        "gdpval44_employment": int(gd_emp),
        "coverage_share_of_nine_sectors": round(gd_emp / S_emp, 4),
        "wage": dist_block(S, "A_MEAN"),
    }

    # Tier 2 within-sector: AIOE (only scored occupations)
    S_a = S[S["aioe"].notna()]
    tier2 = {"aioe": dist_block(S_a, "aioe")}
    comp = S_a[~S_a["OCC_CODE"].isin(set(gd_codes))]["aioe"].to_numpy(float)
    gd_a = g.loc[g["aioe"].notna(), "aioe"].to_numpy(float)
    U, p = mannwhitneyu(gd_a, comp, alternative="two-sided")
    cles = U / (len(gd_a) * len(comp))
    tier2["rank_test_vs_within_sector_complement"] = {
        "test": "Mann-Whitney U (two-sided), GDPval-44 vs within-nine complement",
        "n_gdpval": int(len(gd_a)), "n_complement": int(len(comp)),
        "U": float(U), "p_value": float(p),
        "common_language_effect_gdpval_higher": round(float(cles), 4),
    }

    summary = {
        "oews_source": nat.attrs["source"],
        "sector_assignment": "OEWS May 2024 natsector modal (proxy for GDPval's 2023 NEM rule)",
        "validation_gdpval44": {
            "n": val["n"], "landed_in_gdpval_assigned_sector": val["match"],
            "mismatches": [
                {"occupation": r["gdpval_title"], "gdpval_sector": r["sector"],
                 "oews_modal_sector": r["gdpval_sector"]}
                for _, r in val["detail"][~val["detail"]["match"]].iterrows()],
        },
        "n_occupations_modal_in_nine": len(in_nine),
        "gdpval44_outside_S": gd_not_in_S,
        "tier1_within_sector": tier1,
        "tier2_within_sector": tier2,
    }
    paths.WITHIN_SECTOR_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    write_log(modal, val)
    make_figure(S, S_a, g)

    # --- Report ---
    print(f"Modal-sector validation: {val['match']}/{val['n']} of GDPval's 44 "
          f"land in their GDPval-assigned sector")
    print(f"Within-nine population: {len(in_nine)} occupations, "
          f"{S_emp:,.0f} workers")
    print(f"\nTier 1 within-sector:")
    print(f"  GDPval-44 coverage of the nine sectors: {gd_emp/S_emp:.1%}")
    print(f"  GDPval median wage percentile within nine sectors: "
          f"{tier1['wage']['gdpval_median_percentile_in_baseline']:.0%}")
    print(f"  (baseline median ${tier1['wage']['baseline_weighted_median']:,.0f} "
          f"vs GDPval ${tier1['wage']['gdpval_weighted_median']:,.0f})")
    print(f"\nTier 2 within-sector (AIOE):")
    print(f"  GDPval median AIOE percentile within nine sectors: "
          f"{tier2['aioe']['gdpval_median_percentile_in_baseline']:.0%}")
    print(f"  (baseline median {tier2['aioe']['baseline_weighted_median']:+.3f} "
          f"vs GDPval {tier2['aioe']['gdpval_weighted_median']:+.3f})")
    print(f"  rank test: U={U:.0f}, p={p:.2e}, P(GDPval higher)={cles:.3f}")
    if gd_not_in_S:
        print(f"\nWARNING: GDPval codes not in within-nine population: {gd_not_in_S}")
    print(f"\nWrote {paths.WITHIN_SECTOR_SUMMARY.relative_to(paths.ROOT)}")
    print(f"Wrote {paths.MODAL_SECTOR_LOG.relative_to(paths.ROOT)}")
    print(f"Wrote {paths.FIG_WITHIN.relative_to(paths.ROOT)}")
    return 0


def write_log(modal, val):
    d = val["detail"]
    lines = [
        "# Modal-sector assignment log (within-sector baseline)", "",
        "GDPval assigned occupations to sectors via the 2023 National Employment",
        "Matrix (\"sector with the highest employment for each occupation\"). The 2023",
        "matrix is not reachable; this uses the May 2024 OEWS national industry file",
        "(natsector), which gives occupation employment across 20 mutually-exclusive",
        "NAICS sectors. Government is NAICS 99 (OEWS designation excluding government",
        "schools and hospitals), matching how the Matrix separates Government.", "",
        f"- Occupations assigned: **{len(modal)}**",
        f"- Modal sector in GDPval's nine: **{int(modal['in_nine'].sum())}**",
        f"- Validation, GDPval's 44 landing in their GDPval-assigned sector: "
        f"**{val['match']}/{val['n']}**", "",
        "## Ownership de-duplication",
        "The natsector file gives ONE combined-ownership row per (occupation, NAICS",
        "sector), so no summation across OEWS OWN_CODEs is performed and none is",
        "needed. (The finer 3-digit files use overlapping combined codes with no full",
        "total and would double-count under naive summation; those are not used here.)",
        "As a check, each occupation's per-sector employment sums to its cross-industry",
        "total to within rounding, so the sectors partition employment cleanly.", "",
        "## Judgment call and soft-spot: Government",
        "GDPval's Government is a BEA / National Employment Matrix sector that includes",
        "public education and public hospitals. OEWS has no matching sector: its",
        "Government (NAICS 99) EXCLUDES government schools and hospitals, parking them",
        "in Educational Services (61) and Health Care (62). NAICS 99 is used as the",
        "Government sector, but it is narrower than GDPval's, and that is the main",
        "soft-spot of this baseline: government-education occupations land in Education",
        "(61, outside the nine) rather than Government, so the within-nine population",
        "may under-include some public-sector workers GDPval's framework would count.", "",
        "## Mismatches (GDPval-assigned sector vs OEWS-modal sector)", "",
        "| Occupation | GDPval sector | OEWS-modal sector | still in the nine? | why |",
        "|---|---|---|---|---|",
        "| Concierges | Real Estate and Rental and Leasing | Health Care and Social "
        "Assistance | yes | split occupation; 2024 OEWS employs more concierges in "
        "health-care settings than in real estate |",
        "| Child, Family, and School Social Workers | Government | Health Care and "
        "Social Assistance | yes | social assistance (NAICS 62) is the modal industry; "
        "the narrower NAICS-99 Government excludes such government social services |",
    ]
    lines += [
        "", "Both mismatches remain inside the nine-sector population, so the",
        "within-sector comparison is unaffected in membership; only the sector label",
        "differs. The social-worker case is a direct symptom of the Government",
        "soft-spot above.", "",
    ]
    paths.MODAL_SECTOR_LOG.write_text("\n".join(lines), encoding="utf-8")


def make_figure(S, S_a, g):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde

    def wkde(values, weights, grid, logx=False):
        values = np.asarray(values, float); weights = np.asarray(weights, float)
        ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
        x = np.log10(values[ok]) if logx else values[ok]
        return gaussian_kde(x, weights=weights[ok])(np.log10(grid) if logx else grid)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    # Tier 1 wage
    grid = np.logspace(np.log10(18000), np.log10(400000), 400)
    ax = axes[0]
    ax.plot(grid, wkde(S["A_MEAN"], S["TOT_EMP"], grid, logx=True), color="#2B8A3E", lw=2,
            label="Within GDPval's 9 sectors")
    ax.fill_between(grid, wkde(S["A_MEAN"], S["TOT_EMP"], grid, logx=True), color="#2B8A3E", alpha=0.10)
    ax.plot(grid, wkde(g["A_MEAN"], g["TOT_EMP"], grid, logx=True), color="#E8590C", lw=2,
            label="GDPval's 44")
    ax.fill_between(grid, wkde(g["A_MEAN"], g["TOT_EMP"], grid, logx=True), color="#E8590C", alpha=0.12)
    ax.set_xscale("log"); ax.set_xlabel("Mean annual wage (US$, log)")
    ax.set_ylabel("Employment-weighted density"); ax.set_title("Tier 1: wage (within-sector)")
    ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
    # Tier 2 AIOE
    ax = axes[1]
    lo = float(np.nanmin(S_a["aioe"])); hi = float(np.nanmax(S_a["aioe"]))
    ag = np.linspace(lo - 0.2, hi + 0.2, 400)
    ax.plot(ag, wkde(S_a["aioe"], S_a["TOT_EMP"], ag), color="#2B8A3E", lw=2,
            label="Within GDPval's 9 sectors")
    ax.fill_between(ag, wkde(S_a["aioe"], S_a["TOT_EMP"], ag), color="#2B8A3E", alpha=0.10)
    gg = g[g["aioe"].notna()]
    ax.plot(ag, wkde(gg["aioe"], gg["TOT_EMP"], ag), color="#E8590C", lw=2, label="GDPval's 44")
    ax.fill_between(ag, wkde(gg["aioe"], gg["TOT_EMP"], ag), color="#E8590C", alpha=0.12)
    ax.set_xlabel("AIOE (standardized)"); ax.set_title("Tier 2: AIOE (within-sector)")
    ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Within GDPval's nine sectors: GDPval's 44 vs other occupations in the same sectors",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(paths.FIG_WITHIN, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    sys.path.insert(0, str(paths.ROOT / "src"))
    raise SystemExit(main())
