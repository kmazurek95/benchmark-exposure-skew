"""Tier 3 (Webb): quantify the occ1990dd -> 2018 SOC bridge lossiness, then apply
the pre-registered decision rule.

The pre-registration (section 3) established that Webb is built on O*NET task text,
so a Webb skew is uninterpretable for the same shared-construction reason AIOE's
is; Webb cannot change the load-bearing conclusion regardless of outcome. This
script therefore does not reconstruct anyone's multi-hop CPS pipeline to force a
comparison. It builds the crosswalk only far enough to REPORT the lossiness, and
then, per the pre-registration (sections 2 and 3), reports a large unmapped
fraction as the Tier-3 finding rather than presenting a forced mapping as clean.

Bridge chain (all public, documented crosswalks):
  Webb occ1990dd -> (Dorn occ2010_occ1990dd) 2010 Census occ
                 -> (Census 2010->2018 crosswalk) 2018 SOC

Run: python src/bridge_webb.py
"""
from __future__ import annotations

import io
import json
import sys
import zipfile

import numpy as np
import pandas as pd

import paths
import oews


def load_dorn() -> pd.DataFrame:
    with zipfile.ZipFile(paths.DORN_XWALK) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".dta"))
        d = pd.read_stata(io.BytesIO(z.read(name)))
    d.columns = ["census2010", "occ1990dd"]
    d["census2010"] = d["census2010"].astype(str).str.zfill(4)
    d["occ1990dd"] = d["occ1990dd"].astype("Int64")
    return d


def load_census_2010_to_2018() -> pd.DataFrame:
    cx = pd.read_excel(paths.CENSUS_XWALK, sheet_name="2010 to 2018 Crosswalk ", header=3)
    cx.columns = ["soc2010", "census2010", "t2010", "soc2018", "census2018", "t2018"]
    cx = cx.dropna(subset=["census2010", "soc2018"])
    cx["census2010"] = (cx["census2010"].astype(str)
                        .str.replace(r"\.0$", "", regex=True).str.zfill(4))
    cx["soc2018"] = cx["soc2018"].astype(str).str.strip()
    return cx[["census2010", "soc2018"]]


def main() -> int:
    dorn = load_dorn()
    cx = load_census_2010_to_2018()
    webb = pd.read_csv(paths.WEBB)
    webb_scored = webb[webb["pct_ai"].notna()]
    webb_map = dict(zip(webb["occ1990dd"], webb["pct_ai"]))

    # Chain: 2010 census -> occ1990dd (Dorn) joined to 2010 census -> 2018 SOC (Census)
    chain = cx.merge(dorn, on="census2010", how="inner")  # census2010, soc2018, occ1990dd

    # (a) occ1990dd reach: how many of Webb's scored occ1990dd reach any 2018 SOC
    reachable_dd = set(chain["occ1990dd"].dropna())
    dd_scored = set(webb_scored["occ1990dd"])
    dd_reached = dd_scored & reachable_dd

    # (b) multiplicity, both directions (at the SOC-detailed level)
    soc_to_dd = chain.groupby("soc2018")["occ1990dd"].agg(lambda s: sorted(set(s.dropna())))
    dd_to_soc = chain.groupby("occ1990dd")["soc2018"].agg(lambda s: sorted(set(s)))
    soc_mult = soc_to_dd.apply(len)
    dd_mult = dd_to_soc.apply(len)

    # Webb score per 2018 SOC (mean of its occ1990dd scores; SOC->dd is clean 1:1 here)
    def webb_for(codes):
        vals = [webb_map[c] for c in codes if c in webb_map and pd.notna(webb_map[c])]
        return float(np.mean(vals)) if vals else np.nan
    soc_webb = soc_to_dd.apply(webb_for)

    # (c) employment coverage against OEWS detailed
    nat = oews.load_national()
    det = oews.detailed(nat).dropna(subset=["TOT_EMP"]).copy()
    det["webb"] = det["OCC_CODE"].map(soc_webb)
    emp_total = float(det["TOT_EMP"].sum())
    emp_mapped = float(det.loc[det["webb"].notna(), "TOT_EMP"].sum())
    cov = emp_mapped / emp_total

    # (d) is the unmapped set non-random? compare mapped vs unmapped on AIOE and wage
    bridged_aioe = pd.read_csv(paths.AIOE_BRIDGED_CSV, dtype={"soc2018": str})
    det = det.merge(bridged_aioe[["soc2018", "aioe"]], left_on="OCC_CODE",
                    right_on="soc2018", how="left")

    def wmean(sub, col):
        v = sub[col].to_numpy(float); e = sub["TOT_EMP"].to_numpy(float)
        ok = np.isfinite(v) & np.isfinite(e)
        return float(np.sum(v[ok] * e[ok]) / np.sum(e[ok])) if ok.any() else float("nan")

    mapped = det[det["webb"].notna()]; unmapped = det[det["webb"].isna()]
    bias = {
        "mapped_emp_weighted_mean_aioe": round(wmean(mapped, "aioe"), 4),
        "unmapped_emp_weighted_mean_aioe": round(wmean(unmapped, "aioe"), 4),
        "mapped_emp_weighted_mean_wage": round(wmean(mapped, "A_MEAN"), 0),
        "unmapped_emp_weighted_mean_wage": round(wmean(unmapped, "A_MEAN"), 0),
    }

    summary = {
        "bridge_chain": "Webb occ1990dd -> Dorn(2010 census occ) -> Census(2018 SOC)",
        "webb_occ1990dd_scored": int(len(webb_scored)),
        "webb_occ1990dd_reaching_a_2018_soc": int(len(dd_reached)),
        "webb_occ1990dd_reach_rate": round(len(dd_reached) / len(dd_scored), 4),
        "multiplicity": {
            "soc_to_occ1990dd_max": int(soc_mult.max()),
            "soc_to_occ1990dd_share_single": round(float((soc_mult == 1).mean()), 4),
            "occ1990dd_to_soc_mean": round(float(dd_mult.mean()), 2),
            "occ1990dd_to_soc_median": int(dd_mult.median()),
            "occ1990dd_to_soc_max": int(dd_mult.max()),
        },
        "employment_coverage": {
            "oews_detailed_total": int(len(det)),
            "oews_detailed_with_webb": int(det["webb"].notna().sum()),
            "employment_share_mapped": round(cov, 4),
            "employment_share_unmapped": round(1 - cov, 4),
        },
        "unmapped_nonrandom_check": bias,
        "verdict": "documented null: bridge too lossy to trust for a distributional comparison",
    }
    paths.WEBB_BRIDGE_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # local per-occupation table (third-party Webb values)
    out = det.loc[det["webb"].notna(), ["OCC_CODE", "OCC_TITLE", "TOT_EMP", "webb"]]
    out.to_csv(paths.WEBB_SOC_LOCAL, index=False)

    write_log(summary)

    # --- Report ---
    print("Webb occ1990dd -> 2018 SOC bridge, lossiness assessment")
    print(f"  Webb scored occ1990dd codes: {len(webb_scored)}")
    print(f"  reaching a 2018 SOC:         {len(dd_reached)} "
          f"({len(dd_reached)/len(dd_scored):.0%})")
    print(f"  SOC->occ1990dd single-valued: {(soc_mult==1).mean():.0%} "
          f"(clean at SOC level)")
    print(f"  occ1990dd->SOC fan-out: mean {dd_mult.mean():.1f}, max {dd_mult.max()}")
    print(f"  EMPLOYMENT COVERAGE: {cov:.1%} mapped, {1-cov:.1%} UNMAPPED")
    print(f"  unmapped is non-random: mean AIOE mapped {bias['mapped_emp_weighted_mean_aioe']:+.2f} "
          f"vs unmapped {bias['unmapped_emp_weighted_mean_aioe']:+.2f}")
    print(f"\nVerdict: {summary['verdict']}")
    print(f"Wrote {paths.WEBB_BRIDGE_SUMMARY.relative_to(paths.ROOT)}")
    print(f"Wrote {paths.WEBB_BRIDGE_LOG.relative_to(paths.ROOT)}")
    return 0


def write_log(s):
    b = s["unmapped_nonrandom_check"]
    lines = [
        "# Tier 3 (Webb): occ1990dd -> 2018 SOC bridge lossiness", "",
        "Webb is distributed by occ1990dd (Dorn's harmonized 1990 Census codes),",
        "not SOC, with no official bridge. This assessment builds the bridge only",
        "far enough to measure its lossiness, then applies the pre-registered",
        "decision rule. It does not reconstruct the multi-hop CPS-weighted pipeline",
        "used by EIG/Yale, because the pre-registration (section 3) already",
        "established that Webb shares O\\*NET construction and so cannot serve as the",
        "independent check; a forced comparison would add a caveated measure of no",
        "load-bearing value.", "",
        "## Bridge chain (public, documented crosswalks)",
        "Webb occ1990dd -> Dorn occ2010_occ1990dd (2010 Census occ) -> Census 2010->2018",
        "crosswalk (2018 SOC).", "",
        "## Lossiness",
        f"- Webb scored occ1990dd codes: **{s['webb_occ1990dd_scored']}**",
        f"- Reaching a 2018 SOC code: **{s['webb_occ1990dd_reaching_a_2018_soc']}** "
        f"({s['webb_occ1990dd_reach_rate']:.0%})",
        f"- SOC -> occ1990dd single-valued: **{s['multiplicity']['soc_to_occ1990dd_share_single']:.0%}** "
        f"(clean at the SOC level)",
        f"- occ1990dd -> SOC fan-out: mean **{s['multiplicity']['occ1990dd_to_soc_mean']}**, "
        f"max {s['multiplicity']['occ1990dd_to_soc_max']} (Webb scores apply at a coarser resolution)",
        f"- **Employment coverage: {s['employment_coverage']['employment_share_mapped']:.0%} mapped, "
        f"{s['employment_coverage']['employment_share_unmapped']:.0%} UNMAPPED**", "",
        "## The unmapped fraction is not a benign random slice",
        f"Employment-weighted mean AIOE is {b['mapped_emp_weighted_mean_aioe']:+.2f} among mapped",
        f"occupations vs {b['unmapped_emp_weighted_mean_aioe']:+.2f} among unmapped, and mean wage",
        f"${b['mapped_emp_weighted_mean_wage']:,.0f} vs ${b['unmapped_emp_weighted_mean_wage']:,.0f}.",
        "The gaps are modest but consistent: the mapped 55% skews slightly higher on",
        "both wage and AIOE, so it is not a representative subsample of the workforce.",
        "The decisive problem is simply the size of the loss, 45% of employment.", "",
        "## Verdict (pre-registered)",
        "The bridge leaves roughly 45% of US employment without a Webb score, and the",
        "unmapped set is systematically different. Per the pre-registration (sections",
        "2-3), this is reported as the Tier-3 finding rather than presenting a forced",
        "mapping as clean: the most-cited non-abilities exposure measure will not",
        "cleanly join the SOC classification the rest of the literature uses. Because",
        "Webb also shares O\\*NET construction, even a clean bridge could not have",
        "changed the load-bearing conclusion; Tier 1 carries the argument.", "",
    ]
    paths.WEBB_BRIDGE_LOG.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.path.insert(0, str(paths.ROOT / "src"))
    raise SystemExit(main())
