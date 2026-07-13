"""Tier 1 (the spine): employment coverage and wage-distribution position of
GDPval's 44 occupations, economy-wide baseline.

No exposure measure enters here, so no artifact problem enters. Outputs the two
numbers the pre-registration (section 10) argues economic-value benchmarks should
publish: the share of US employment the frame covers, and where that frame sits
in the employment-weighted wage distribution.

Baselines for the denominator (section 6):
  * PRIMARY   -- all detailed occupations INCLUDING 'All Other' residual buckets
  * secondary -- excluding 'All Other', for comparability with OpenAI's filtering
Total-employment share (vs the 00-0000 total row) is reported alongside.

Run: python src/tier1_coverage.py   (needs data/raw/oesm24nat.zip)
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import paths
import oews


def weighted_quantile(values, quantiles, weights):
    """Employment-weighted quantiles (values need not be sorted)."""
    values = np.asarray(values, float)
    weights = np.asarray(weights, float)
    ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values, weights = values[ok], weights[ok]
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    cw = np.cumsum(weights) - 0.5 * weights
    cw /= np.sum(weights)
    return np.interp(quantiles, cw, values)


def weighted_mean(values, weights):
    """Employment-weighted mean over cells that have BOTH a value and a weight
    (so suppressed-wage occupations don't sit in the denominator)."""
    values = np.asarray(values, float)
    weights = np.asarray(weights, float)
    ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    return float(np.sum(values[ok] * weights[ok]) / np.sum(weights[ok]))


def weighted_share_below(threshold, values, weights):
    """Employment-weighted share of workers whose occ mean wage < threshold."""
    values = np.asarray(values, float)
    weights = np.asarray(weights, float)
    ok = np.isfinite(values) & np.isfinite(weights)
    values, weights = values[ok], weights[ok]
    return float(np.sum(weights[values < threshold]) / np.sum(weights))


def main() -> int:
    try:
        nat = oews.load_national()
    except FileNotFoundError as e:
        print("[tier1] OEWS not present yet -- pipeline ready, waiting on data.\n")
        print(e)
        return 3

    # Detailed occupations only (never the major/minor/broad aggregate rows).
    det = oews.detailed(nat)
    det["all_other"] = oews.is_all_other(det["OCC_TITLE"])
    total_emp = oews.total_employment(nat)

    mp = pd.read_csv(paths.MAPPING_CSV, dtype=str)
    gd_codes = mp["soc_2018"].unique().tolist()
    oews_detailed_codes = set(det["OCC_CODE"])

    # Resolve each SOC-correct GDPval detail code to the code OEWS actually
    # PUBLISHES. OEWS sometimes publishes a broad group as its own detailed line
    # instead of the sub-details: Buyers and Purchasing Agents 13-1021/22/23 are
    # not in OEWS May 2024; 13-1020 is published as detailed (486,900), and it is
    # already the single line in the detailed denominator, so using it in the
    # numerator is consistent (no double count, no missing employment).
    def resolve(soc: str):
        if soc in oews_detailed_codes:
            return soc, "direct"
        broad = soc[:6] + "0"                       # 13-1021 -> 13-1020
        if broad in oews_detailed_codes:
            return broad, "broad-as-detailed"
        return None, "absent"

    resolved, via_broad, absent = {}, [], []
    for soc in gd_codes:
        code, how = resolve(soc)
        if code is None:
            absent.append(soc)
        else:
            resolved[soc] = code
            if how == "broad-as-detailed":
                via_broad.append(f"{soc}->{code}")
    gd_oews_codes = sorted(set(resolved.values()))  # deduped OEWS codes (Buyers -> one)

    g = det[det["OCC_CODE"].isin(gd_oews_codes)].copy()
    emp_suppressed = sorted(g.loc[g["TOT_EMP"].isna(), "OCC_CODE"])
    wage_suppressed = sorted(g.loc[g["A_MEAN"].isna(), "OCC_CODE"])
    wage_capped = sorted(g.loc[g.get("A_MEAN_CAPPED", False) == True, "OCC_CODE"])

    flags = []
    if via_broad:
        flags.append(f"resolved detail->broad (OEWS publishes broad as detailed): {via_broad}")
    if absent:
        flags.append(f"ABSENT from OEWS entirely: {absent}")
    if emp_suppressed:
        flags.append(f"employment suppressed (TOT_EMP blank): {emp_suppressed}")
    if wage_suppressed:
        flags.append(f"annual mean wage suppressed (A_MEAN blank): {wage_suppressed}")
    if wage_capped:
        flags.append(f"annual mean wage at disclosure cap '#': {wage_capped}")

    # nansum: suppressed cells contribute 0 to the sum and are reported above,
    # not coerced to a real zero.
    gd_emp = float(np.nansum(g["TOT_EMP"]))
    emp_incl = float(np.nansum(det["TOT_EMP"]))
    emp_excl = float(np.nansum(det.loc[~det["all_other"], "TOT_EMP"]))

    # --- Coverage ---
    cov = {
        "share_of_total_employment_row": gd_emp / total_emp,
        "share_of_detailed_incl_all_other": gd_emp / emp_incl,   # PRIMARY
        "share_of_detailed_excl_all_other": gd_emp / emp_excl,   # secondary
    }

    # --- Wage-distribution position (economy-wide, employment-weighted) ---
    w = det["A_MEAN"].to_numpy(float)
    we = det["TOT_EMP"].to_numpy(float)
    gw = g["A_MEAN"].to_numpy(float)
    gwe = g["TOT_EMP"].to_numpy(float)

    q = [0.10, 0.25, 0.50, 0.75, 0.90]
    base_q = weighted_quantile(w, q, we)
    gd_q = weighted_quantile(gw, q, gwe)

    base_median = float(weighted_quantile(w, [0.5], we)[0])
    gd_median = float(weighted_quantile(gw, [0.5], gwe)[0])
    gd_mean_wt = weighted_mean(gw, gwe)
    base_mean_wt = weighted_mean(w, we)
    # Where does the GDPval-covered median worker sit in the economy-wide dist?
    gd_median_pctile = weighted_share_below(gd_median, w, we)

    wage = {
        "economywide_weighted_wage_percentiles": dict(zip(
            [f"p{int(x*100)}" for x in q], [round(v, 1) for v in base_q])),
        "gdpval44_weighted_wage_percentiles": dict(zip(
            [f"p{int(x*100)}" for x in q], [round(v, 1) for v in gd_q])),
        "economywide_weighted_median_wage": round(base_median, 1),
        "gdpval44_weighted_median_wage": round(gd_median, 1),
        "economywide_weighted_mean_wage": round(base_mean_wt, 1),
        "gdpval44_weighted_mean_wage": round(gd_mean_wt, 1),
        "gdpval44_median_worker_percentile_economywide": round(gd_median_pctile, 4),
    }

    summary = {
        "oews_source": nat.attrs["source"],
        "n_gdpval_detail_codes": len(gd_codes),
        "n_gdpval_codes_matched": int(g["OCC_CODE"].nunique()),
        "n_gdpval_occupations": 44,
        "n_gdpval_oews_codes": len(gd_oews_codes),
        "data_flags": {
            "resolved_detail_to_broad": via_broad,
            "absent_from_oews": absent,
            "employment_suppressed": emp_suppressed,
            "wage_mean_suppressed": wage_suppressed,
            "wage_mean_at_cap": wage_capped,
        },
        "gdpval44_employment": int(gd_emp),
        "total_employment_row": int(total_emp),
        "detailed_employment_incl_all_other": int(emp_incl),
        "detailed_employment_excl_all_other": int(emp_excl),
        "n_detailed_occupations": int(len(det)),
        "n_all_other_occupations": int(det["all_other"].sum()),
        "coverage": {k: round(v, 4) for k, v in cov.items()},
        "wage": wage,
    }
    paths.TIER1_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Per-occupation table (third-party OEWS values) -> local. Join through the
    # resolved OEWS code so Buyers (13-1020) picks up its GDPval title.
    mp = mp.copy()
    mp["oews_code"] = [resolve(s)[0] for s in mp["soc_2018"]]
    occ_lookup = (mp.dropna(subset=["oews_code"])
                    .drop_duplicates("oews_code")[["oews_code", "gdpval_title", "sector"]])
    g_out = g[["OCC_CODE", "OCC_TITLE", "TOT_EMP", "A_MEAN", "A_MEDIAN"]].merge(
        occ_lookup, left_on="OCC_CODE", right_on="oews_code", how="left")
    g_out.to_csv(paths.TIER1_OCC_LOCAL, index=False)

    # --- Report ---
    print(f"OEWS source: {nat.attrs['source']}")
    print(f"\nGDPval detail codes: {len(gd_codes)} | matched in OEWS: {g['OCC_CODE'].nunique()}")
    if flags:
        print("DATA FLAGS (reported, not dropped):")
        for f in flags:
            print("  -", f)
    else:
        print("Data flags: none -- all 44 resolve to a present OEWS detailed row "
              "with released employment and wages.")
    print(f"\nGDPval-44 employment:            {gd_emp:>14,.0f}")
    print(f"Total US employment (00-0000):   {total_emp:>14,.0f}")
    print(f"Detailed emp incl 'All Other':   {emp_incl:>14,.0f}")
    print(f"Detailed emp excl 'All Other':   {emp_excl:>14,.0f}")
    print("\nCoverage (share of US employment):")
    print(f"  vs total row:                  {cov['share_of_total_employment_row']:.2%}")
    print(f"  vs detailed incl All Other  *  {cov['share_of_detailed_incl_all_other']:.2%}   (PRIMARY)")
    print(f"  vs detailed excl All Other:    {cov['share_of_detailed_excl_all_other']:.2%}")
    print("\nEmployment-weighted mean annual wage:")
    print(f"  economy-wide:                  ${base_mean_wt:>12,.0f}")
    print(f"  GDPval-44 covered workers:     ${gd_mean_wt:>12,.0f}")
    print(f"\nGDPval-covered median worker sits at the "
          f"{gd_median_pctile:.0%} percentile of the economy-wide wage distribution.")
    print(f"\nWrote {paths.TIER1_SUMMARY.relative_to(paths.ROOT)}")
    print(f"Wrote {paths.TIER1_OCC_LOCAL.relative_to(paths.ROOT)}")

    make_figure(w, we, gw, gwe, cov, base_median, gd_median)
    print(f"Wrote {paths.FIG_TIER1.relative_to(paths.ROOT)}")
    return 0


def weighted_ecdf(values, weights):
    """Employment-weighted empirical CDF: sorted values and cumulative share.
    Returns (x, y) suitable for a steps-post plot (no smoothing over small n)."""
    values = np.asarray(values, float)
    weights = np.asarray(weights, float)
    ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values, weights = values[ok], weights[ok]
    order = np.argsort(values)
    x = values[order]
    y = np.cumsum(weights[order]) / np.sum(weights)
    return x, y


def make_figure(w, we, gw, gwe, cov, base_median, gd_median):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Employment-weighted empirical CDFs. The GDPval side is 44 occupation-means
    # with heavy-tailed weights, so a step ECDF (not a smoothed density) is used:
    # it shows the true step structure and reads the percentile positions directly.
    xw, yw = weighted_ecdf(w, we)
    xg, yg = weighted_ecdf(gw, gwe)
    pct = weighted_share_below(gd_median, w, we)   # GDPval median's workforce percentile

    fig, ax = plt.subplots(figsize=(9, 5.4))
    ax.step(xw, yw, where="post", color="#4C6EF5", lw=2,
            label="US workforce (employment-weighted)")
    ax.step(xg, yg, where="post", color="#E8590C", lw=2,
            label="GDPval's 44 occupations")
    # rug of the 44 occupation-means so their small-n lumpiness is visible
    ax.plot(gw, np.full_like(np.asarray(gw, float), -0.03), "|", color="#E8590C",
            ms=8, alpha=0.5, clip_on=False)
    # mark the load-bearing stat: GDPval median wage -> its percentile on the workforce
    ax.vlines(gd_median, 0, pct, color="#868e96", ls="--", lw=1)
    ax.hlines(pct, xw.min(), gd_median, color="#868e96", ls="--", lw=1)
    ax.plot([gd_median], [pct], "o", color="#4C6EF5", zorder=5)
    ax.annotate(f"GDPval median ${gd_median:,.0f}\nsits at the {pct:.0%} percentile\n"
                f"of the workforce",
                xy=(gd_median, pct), xytext=(gd_median * 1.08, pct - 0.30),
                fontsize=9, color="#333",
                arrowprops=dict(arrowstyle="->", color="#868e96"))
    ax.set_xscale("log")
    ax.set_ylim(-0.05, 1.02)
    ax.set_xlabel("Occupational mean annual wage (US$, log scale)")
    ax.set_ylabel("Cumulative share of employment")
    ax.set_title("GDPval's frame vs the employment-weighted US workforce\n"
                 f"Coverage: {cov['share_of_detailed_incl_all_other']:.1%} of US employment",
                 fontsize=12)
    ax.legend(frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(paths.FIG_TIER1, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    sys.path.insert(0, str(paths.ROOT / "src"))
    raise SystemExit(main())
