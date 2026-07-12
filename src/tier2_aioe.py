"""Tier 2 (extension, caveated): AIOE exposure of GDPval's frame vs the
employment-weighted workforce.

AIOE (Felten, Raj & Seamans) bridged to 2018 SOC by src/bridge_aioe.py. This
compares the AIOE distribution of GDPval's 44 occupations against the
employment-weighted economy-wide workforce.

The caveat is load-bearing and stated up front (pre_registration.md sections 3-4):
AIOE and GDPval's >=60%-digital filter both derive from O*NET, so a skew here
cannot be read as substantive exposure rather than shared construction. The
asymmetry is fixed in advance -- a skew present under AIOE is uninterpretable; a
skew ABSENT under AIOE is the strong result, because AIOE is the measure most
disposed to find one. This script reports the comparison; it does not decide the
conclusion, which section 4 fixes per outcome.

Baseline here: economy-wide only (within-sector is a separate fast-follow).

Run: python src/tier2_aioe.py   (needs OEWS + outputs/local/aioe_2018soc_bridged.csv)
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

import paths
import oews
from tier1_coverage import weighted_quantile, weighted_mean, weighted_share_below


def build_oews_aioe(det: pd.DataFrame, bridged: pd.DataFrame) -> pd.DataFrame:
    """Attach an AIOE score to each OEWS detailed occupation.

    Direct join on 2018 SOC code; for OEWS codes that are broad groups published
    as detailed (e.g. Buyers 13-1020), use the employment-unweighted mean of the
    AIOE of the detail codes sharing the stem (13-1021/22/23). 2010-vintage detail
    employment is not distributed with AIOE, so an employment-weighted mean is not
    available; the unweighted mean is logged as the choice.
    """
    aioe_map = {c: v for c, v in zip(bridged["soc2018"], bridged["aioe"])
                if pd.notna(v)}
    methods = {}

    def get(code: str):
        if code in aioe_map:
            return aioe_map[code], "direct"
        if code.endswith("0"):  # possible broad group
            stem = code[:6]
            details = [aioe_map[c] for c in aioe_map if c[:6] == stem and c != code]
            if details:
                return float(np.mean(details)), "broad-mean"
        return np.nan, "unmatched"

    vals, ms = [], []
    for code in det["OCC_CODE"]:
        v, m = get(code)
        vals.append(v)
        ms.append(m)
    out = det.copy()
    out["aioe"] = vals
    out["aioe_method"] = ms
    return out


def main() -> int:
    try:
        nat = oews.load_national()
    except FileNotFoundError as e:
        print("[tier2] OEWS not present yet -- pipeline ready, waiting on data.\n", e)
        return 3
    if not paths.AIOE_BRIDGED_CSV.exists():
        print("[tier2] AIOE bridge missing; run src/bridge_aioe.py first.")
        return 3

    det = oews.detailed(nat).dropna(subset=["TOT_EMP"]).copy()
    det["all_other"] = oews.is_all_other(det["OCC_TITLE"])
    bridged = pd.read_csv(paths.AIOE_BRIDGED_CSV, dtype={"soc2018": str})
    det = build_oews_aioe(det, bridged)

    # GDPval's 44 -> OEWS code (Buyers 13-1021/22/23 -> 13-1020, whose AIOE the
    # broad-mean rule already set to the mean of the three details).
    mp = pd.read_csv(paths.MAPPING_CSV, dtype=str)
    oews_codes = set(det["OCC_CODE"])

    def resolve(soc):
        if soc in oews_codes:
            return soc
        broad = soc[:6] + "0"
        return broad if broad in oews_codes else None

    mp["oews_code"] = [resolve(s) for s in mp["soc_2018"]]
    gd_codes = sorted(set(mp["oews_code"].dropna()))
    g = det[det["OCC_CODE"].isin(gd_codes)].copy()

    # --- AIOE coverage of the economy-wide baseline ---
    scored = det["aioe"].notna()
    emp_total = float(np.nansum(det["TOT_EMP"]))
    emp_scored = float(np.nansum(det.loc[scored, "TOT_EMP"]))
    aioe_missing_gd = sorted(g.loc[g["aioe"].isna(), "OCC_CODE"])

    # --- Employment-weighted AIOE distributions ---
    w = det["aioe"].to_numpy(float);  we = det["TOT_EMP"].to_numpy(float)
    gw = g["aioe"].to_numpy(float);    gwe = g["TOT_EMP"].to_numpy(float)

    q = [0.10, 0.25, 0.50, 0.75, 0.90]
    base_q = weighted_quantile(w, q, we)
    gd_q = weighted_quantile(gw, q, gwe)
    base_med = float(weighted_quantile(w, [0.5], we)[0])
    gd_med = float(weighted_quantile(gw, [0.5], gwe)[0])
    gd_med_pctile = weighted_share_below(gd_med, w, we)  # where GDPval median sits

    # --- Rank-based test, occupation-level (unweighted), GDPval vs complement ---
    gd_set = set(gd_codes)
    comp = det[~det["OCC_CODE"].isin(gd_set) & det["aioe"].notna()]["aioe"].to_numpy(float)
    gd_scores = g.loc[g["aioe"].notna(), "aioe"].to_numpy(float)
    U, p = mannwhitneyu(gd_scores, comp, alternative="two-sided")
    # Effect sizes, signed so positive = GDPval-44 ranks HIGHER on AIOE.
    cles = U / (len(gd_scores) * len(comp))   # P(random GDPval occ > random other)
    rb = 2 * cles - 1                          # rank-biserial correlation

    summary = {
        "oews_source": nat.attrs["source"],
        "aioe_bridge_mode": "official crosswalk" if paths.SOC_XWALK.exists()
                            else "direct+reconcile",
        "economywide_aioe_coverage": {
            "n_detailed": int(len(det)),
            "n_detailed_scored": int(scored.sum()),
            "employment_share_scored": round(emp_scored / emp_total, 4),
        },
        "gdpval44_aioe_missing": aioe_missing_gd,
        "distribution_employment_weighted": {
            "economywide_aioe_percentiles": dict(zip(
                [f"p{int(x*100)}" for x in q], [round(float(v), 4) for v in base_q])),
            "gdpval44_aioe_percentiles": dict(zip(
                [f"p{int(x*100)}" for x in q], [round(float(v), 4) for v in gd_q])),
            "economywide_weighted_median_aioe": round(base_med, 4),
            "gdpval44_weighted_median_aioe": round(gd_med, 4),
            "economywide_weighted_mean_aioe": round(weighted_mean(w, we), 4),
            "gdpval44_weighted_mean_aioe": round(weighted_mean(gw, gwe), 4),
            "gdpval44_median_percentile_in_economywide": round(gd_med_pctile, 4),
        },
        "rank_test_occupation_level_unweighted": {
            "test": "Mann-Whitney U (two-sided), GDPval-44 vs complement",
            "n_gdpval": int(len(gd_scores)),
            "n_complement": int(len(comp)),
            "U": float(U),
            "p_value": float(p),
            "common_language_effect_gdpval_higher": round(float(cles), 4),
            "rank_biserial_pos_means_gdpval_higher": round(float(rb), 4),
        },
    }
    paths.TIER2_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    g_out = g[["OCC_CODE", "OCC_TITLE", "TOT_EMP", "aioe", "aioe_method"]].merge(
        mp.dropna(subset=["oews_code"]).drop_duplicates("oews_code")[
            ["oews_code", "gdpval_title", "sector"]],
        left_on="OCC_CODE", right_on="oews_code", how="left")
    g_out.to_csv(paths.TIER2_OCC_LOCAL, index=False)

    # --- Report ---
    print(f"OEWS source: {nat.attrs['source']}")
    print(f"AIOE economy-wide coverage: {int(scored.sum())}/{len(det)} occupations, "
          f"{emp_scored/emp_total:.1%} of employment")
    if aioe_missing_gd:
        print("  GDPval occupations missing AIOE:", aioe_missing_gd)
    print("\nEmployment-weighted AIOE:")
    print(f"  economy-wide median:  {base_med:+.3f}   mean: {weighted_mean(w, we):+.3f}")
    print(f"  GDPval-44   median:  {gd_med:+.3f}   mean: {weighted_mean(gw, gwe):+.3f}")
    print(f"  GDPval median sits at the {gd_med_pctile:.0%} percentile of the "
          f"employment-weighted workforce AIOE distribution.")
    print(f"\nRank test (occupation-level, unweighted), GDPval-44 vs complement:")
    print(f"  Mann-Whitney U={U:.0f}, p={p:.2e}")
    print(f"  P(random GDPval occ ranks higher on AIOE) = {cles:.3f}; rank-biserial={rb:+.3f}")
    print(f"\nWrote {paths.TIER2_SUMMARY.relative_to(paths.ROOT)}")
    print(f"Wrote {paths.TIER2_OCC_LOCAL.relative_to(paths.ROOT)}")

    make_figure(w, we, gw, gwe, base_med, gd_med)
    print(f"Wrote {paths.FIG_TIER2.relative_to(paths.ROOT)}")
    return 0


def make_figure(w, we, gw, gwe, base_med, gd_med):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde

    def wkde(values, weights, grid):
        values = np.asarray(values, float); weights = np.asarray(weights, float)
        ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
        return gaussian_kde(values[ok], weights=weights[ok])(grid)

    lo = float(np.nanmin(w)); hi = float(np.nanmax(w))
    grid = np.linspace(lo - 0.2, hi + 0.2, 400)
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(grid, wkde(w, we, grid), color="#4C6EF5", lw=2,
            label="US workforce (employment-weighted)")
    ax.fill_between(grid, wkde(w, we, grid), color="#4C6EF5", alpha=0.10)
    ax.plot(grid, wkde(gw, gwe, grid), color="#E8590C", lw=2,
            label="GDPval's 44 occupations")
    ax.fill_between(grid, wkde(gw, gwe, grid), color="#E8590C", alpha=0.12)
    ax.axvline(base_med, color="#4C6EF5", ls="--", lw=1)
    ax.axvline(gd_med, color="#E8590C", ls="--", lw=1)
    ax.set_xlabel("AIOE (AI Occupational Exposure), standardized")
    ax.set_ylabel("Employment-weighted density")
    ax.set_title("AIOE exposure: GDPval's frame vs the employment-weighted workforce\n"
                 "Caveat: AIOE shares O*NET construction with GDPval's digital filter "
                 "(see pre-registration sections 3-4)", fontsize=11)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(paths.FIG_TIER2, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    sys.path.insert(0, str(paths.ROOT / "src"))
    raise SystemExit(main())
