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
from tier1_coverage import (weighted_quantile, weighted_mean,
                            weighted_share_below, weighted_ecdf)
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


def denominator_robustness(det, gd_emp):
    """Audit the within-nine denominator: partition reconciliation (natsector sums
    vs cross-industry totals) and boundary-flip fragility (occupations whose modal
    argmax sits near the in-nine / out-of-nine line)."""
    se = sectors.load_sector_employment().dropna(subset=["TOT_EMP"])
    xind = det.set_index("OCC_CODE")["TOT_EMP"]
    nine = set(sectors.GDPVAL_SECTOR_BY_NAICS)

    # Partition reconciliation: does natsector sum to the cross-industry total?
    sec_sum = se.groupby("OCC_CODE")["TOT_EMP"].sum()
    rr = pd.DataFrame({"sec": sec_sum, "x": xind}).dropna()
    ratio = rr["sec"] / rr["x"]
    recon = {
        "n_occupations": int(len(rr)),
        "max_ratio": round(float(ratio.max()), 4),                 # >1 would be a double-count
        "n_exceeding_101pct": int((ratio > 1.01).sum()),
        "employment_weighted_ratio": round(float(np.average(ratio, weights=rr["x"])), 4),
        "share_reconciling_within_half_pct": round(float(((ratio >= 0.995) & (ratio <= 1.005)).mean()), 3),
    }

    # Boundary-flip fragility: modal vs runner-up sector per occupation.
    def top2(g):
        s = g.sort_values("TOT_EMP", ascending=False)
        tot = s["TOT_EMP"].sum()
        run = s.iloc[1] if len(s) >= 2 else None
        return pd.Series({
            "modal_naics": s.iloc[0]["NAICS"], "modal_share": s.iloc[0]["TOT_EMP"] / tot,
            "runner_naics": (run["NAICS"] if run is not None else None),
            "runner_share": ((run["TOT_EMP"] / tot) if run is not None else 0.0)})
    t2 = se.groupby("OCC_CODE").apply(top2, include_groups=False)
    t2["emp"] = xind
    t2 = t2.dropna(subset=["emp"])
    t2["modal_in"] = t2["modal_naics"].isin(nine)
    t2["runner_in"] = t2["runner_naics"].isin(nine)
    t2["gap"] = t2["modal_share"] - t2["runner_share"]
    Semp = float(t2.loc[t2["modal_in"], "emp"].sum())

    low = t2[t2["modal_in"] & (t2["modal_share"] < 0.40)]
    flip_out = t2[t2["modal_in"] & ~t2["runner_in"] & (t2["gap"] < 0.10)]   # could leave the nine
    flip_in = t2[~t2["modal_in"] & t2["runner_in"] & (t2["gap"] < 0.10)]    # could enter the nine
    frag = {
        "within_nine_employment": int(Semp),
        "low_modal_share_under_0_40": {
            "n": int(len(low)), "employment": int(low["emp"].sum()),
            "share_of_denominator": round(float(low["emp"].sum() / Semp), 3),
            "note": "most split between two in-nine sectors, so membership is unchanged"},
        "membership_flip_out": {
            "n": int(len(flip_out)), "employment": int(flip_out["emp"].sum()),
            "share_of_denominator": round(float(flip_out["emp"].sum() / Semp), 3)},
        "membership_flip_in": {
            "n": int(len(flip_in)), "employment": int(flip_in["emp"].sum())},
        "coverage_band": {
            "point": round(gd_emp / Semp, 4),
            "if_flip_out_leave": round(gd_emp / (Semp - float(flip_out["emp"].sum())), 4),
            "if_flip_in_enter": round(gd_emp / (Semp + float(flip_in["emp"].sum())), 4)},
    }
    return {"partition_reconciliation": recon, "boundary_fragility": frag}


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

    robust = denominator_robustness(det, gd_emp)

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
        "denominator_robustness": robust,
    }
    paths.WITHIN_SECTOR_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    write_log(modal, val, robust)
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


def write_log(modal, val, robust):
    d = val["detail"]
    rec = robust["partition_reconciliation"]
    fr = robust["boundary_fragility"]
    lines = [
        "# Modal-sector assignment log (within-sector baseline)", "",
        "GDPval assigned occupations to sectors via the 2023 National Employment",
        "Matrix (\"sector with the highest employment for each occupation\"). The 2023",
        "matrix is not reachable; this uses the May 2024 OEWS national industry file",
        "(natsector), which gives occupation employment across 20 mutually-exclusive",
        "NAICS sectors. Government is NAICS 99 (OEWS designation excluding government",
        "schools and hospitals); this is narrower than GDPval's BEA/NEM Government,",
        "a documented soft-spot detailed below.", "",
        f"- Occupations assigned: **{len(modal)}**",
        f"- Modal sector in GDPval's nine: **{int(modal['in_nine'].sum())}**",
        f"- Validation, GDPval's 44 landing in their GDPval-assigned sector: "
        f"**{val['match']}/{val['n']}**", "",
        "## Ownership de-duplication and partition reconciliation",
        "The natsector file gives ONE combined-ownership row per (occupation, NAICS",
        "sector), so no summation across OEWS OWN_CODEs is performed and none is",
        "needed. (The finer 3-digit files use overlapping combined codes with no full",
        "total and would double-count under naive summation; those are not used here.)",
        f"Checked against the cross-industry totals: no occupation's sector employment",
        f"exceeds its cross-industry total (max ratio {rec['max_ratio']}), so there is no",
        f"ownership double-count, and the employment-weighted reconciliation is",
        f"{rec['employment_weighted_ratio']:.1%}. It is NOT an exact partition per",
        f"occupation: only {rec['share_reconciling_within_half_pct']:.0%} reconcile within 0.5%, because small",
        "occupations have suppressed fine-sector cells that fall short of the total.",
        "Those cells are too small to be the argmax, so the modal assignment is",
        "unaffected; the earlier 'sums to within rounding' phrasing was too strong.", "",
        "## Denominator boundary fragility",
        f"A third of the within-nine employment ({fr['low_modal_share_under_0_40']['share_of_denominator']:.0%}) sits on occupations whose",
        "modal sector holds under 40% of their employment, but most of those split",
        "between two IN-nine sectors, which does not change membership. The",
        f"membership-relevant fragility is smaller: {fr['membership_flip_out']['n']} occupations "
        f"({fr['membership_flip_out']['share_of_denominator']:.1%} of the",
        "denominator) are in the nine with an out-of-nine runner-up within 10 points,",
        f"and {fr['membership_flip_in']['n']} occupations outside the nine "
        f"({fr['membership_flip_in']['employment']:,} workers) have an in-nine",
        f"runner-up equally close. Flipping these moves within-sector coverage within",
        f"about {fr['coverage_band']['if_flip_in_enter']:.1%} to {fr['coverage_band']['if_flip_out_leave']:.1%}, "
        f"so 31.1% is stable to roughly two points.", "",
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

    def panel(ax, bv, bw, gv, gw, logx, xlabel, title):
        # Employment-weighted empirical CDFs (step), baseline vs GDPval's 44, with
        # the GDPval median's baseline percentile marked. No smoothing over small n.
        xb, yb = weighted_ecdf(bv, bw)
        xg, yg = weighted_ecdf(gv, gw)
        gd_med = float(weighted_quantile(np.asarray(gv, float), [0.5],
                                         np.asarray(gw, float))[0])
        pct = weighted_share_below(gd_med, bv, bw)
        ax.step(xb, yb, where="post", color="#2B8A3E", lw=2,
                label="Within GDPval's 9 sectors")
        ax.step(xg, yg, where="post", color="#E8590C", lw=2, label="GDPval's 44")
        ax.plot(np.asarray(gv, float), np.full(len(gv), -0.03), "|", color="#E8590C",
                ms=7, alpha=0.5, clip_on=False)
        ax.vlines(gd_med, 0, pct, color="#868e96", ls="--", lw=1)
        ax.hlines(pct, np.asarray(xb).min(), gd_med, color="#868e96", ls="--", lw=1)
        ax.plot([gd_med], [pct], "o", color="#2B8A3E", zorder=5)
        ax.annotate(f"{pct:.0%} pctile", xy=(gd_med, pct),
                    xytext=(gd_med, pct - 0.16), fontsize=9, color="#333")
        if logx:
            ax.set_xscale("log")
        ax.set_ylim(-0.05, 1.02)
        ax.set_xlabel(xlabel)
        ax.set_title(title)
        ax.legend(frameon=False, loc="upper left")
        ax.spines[["top", "right"]].set_visible(False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    panel(axes[0], S["A_MEAN"], S["TOT_EMP"], g["A_MEAN"], g["TOT_EMP"],
          True, "Mean annual wage (US$, log)", "Tier 1: wage (within-sector)")
    axes[0].set_ylabel("Cumulative share of employment")
    gg = g[g["aioe"].notna()]
    panel(axes[1], S_a["aioe"], S_a["TOT_EMP"], gg["aioe"], gg["TOT_EMP"],
          False, "AIOE (standardized)", "Tier 2: AIOE (within-sector)")
    fig.suptitle("Within GDPval's nine sectors: GDPval's 44 vs other occupations in the same sectors",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(paths.FIG_WITHIN, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    sys.path.insert(0, str(paths.ROOT / "src"))
    raise SystemExit(main())
