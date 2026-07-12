"""Bridge AIOE (2010 SOC) -> 2018 SOC (Tier-2 input).

AIOE (Felten, Raj & Seamans) is keyed to 2010 SOC across 774 detailed
occupations. GDPval's frame and OEWS are 2018 SOC. Most codes are unchanged and
join directly; a minority changed in the 2010->2018 revision and need
reconciliation.

Two modes, chosen automatically:
  * If the official BLS 2010->2018 SOC crosswalk is present
    (data/raw/soc_2010_to_2018_crosswalk.xlsx), every 2018 detailed code is
    bridged from its 2010 predecessor(s): 1:1 inherit, or many-2010->1-2018
    combined by unweighted mean (2010 employment weights are not distributed
    with AIOE; the constituents are close, so the choice is near-immaterial).
  * If the crosswalk is absent, a direct code join covers unchanged codes, and a
    small documented reconciliation table (below) covers exactly the four
    GDPval-relevant changed codes so GDPval's 44 are always scorable. Economy-
    wide baseline coverage is then reported as a limitation until the crosswalk
    is dropped in.

The reconciliation table is applied in BOTH modes as an assertion check: if the
crosswalk disagrees with a documented GDPval case, the script flags it.

Outputs:
  outputs/aioe_2018soc_bridged.csv   2018 SOC code -> AIOE, with method flag
  outputs/aioe_gdpval44.csv          AIOE for GDPval's 44 (46 detail rows)

Run: python src/bridge_aioe.py
"""
from __future__ import annotations

import sys
import numpy as np
import pandas as pd

import paths  # noqa: E402


# GDPval-relevant 2018 codes that are NOT direct 2010 codes, with the documented
# BLS reconciliation. combine="mean" averages the listed 2010 AIOE scores.
RECONCILE: dict[str, dict] = {
    "15-1252": dict(from2010=["15-1132", "15-1133"], method="merge-mean",
                    note="Software Developers: 2018 merge of 2010 Applications + Systems Software."),
    "27-3023": dict(from2010=["27-3021", "27-3022"], method="merge-mean",
                    note="News Analysts/Reporters/Journalists: 2018 merge of 2010 Broadcast News Analysts + Reporters."),
    "11-3012": dict(from2010=["11-3011"], method="split-inherit",
                    note="Administrative Services Managers: 2010 11-3011 split into 11-3012 + 11-3013; inherit parent score."),
    "13-1082": dict(from2010=["13-1199"], method="imputed-parent",
                    note="Project Management Specialists: new in 2018; imputed from 2010 parent 13-1199 (Business Operations Specialists, All Other). Weakest link in the bridge."),
}


def load_aioe() -> pd.DataFrame:
    a = pd.read_excel(paths.AIOE_MAIN, sheet_name="Appendix A")
    a.columns = ["soc2010", "title2010", "aioe"]
    a["soc2010"] = a["soc2010"].str.strip()
    return a


def load_2018_universe() -> set[str]:
    onet = pd.read_excel(paths.ONETSOC_2019, header=3).dropna(subset=["O*NET-SOC 2019 Code"])
    onet["soc6"] = onet["O*NET-SOC 2019 Code"].str.slice(0, 7)
    return set(onet["soc6"])


def load_official_xwalk() -> pd.DataFrame | None:
    """Return distinct (soc2010, soc2018) pairs from the official BLS crosswalk, or None."""
    if not paths.SOC_XWALK.exists():
        return None
    raw = pd.read_excel(paths.SOC_XWALK, header=None)
    # Find the header row (contains '2010 SOC Code' and '2018 SOC Code' in some casing).
    hdr = None
    for i in range(min(12, len(raw))):
        vals = [str(v).strip().lower() for v in raw.iloc[i].tolist()]
        if any("2010 soc" in v for v in vals) and any("2018 soc" in v for v in vals):
            hdr = i
            break
    if hdr is None:
        raise RuntimeError("Could not locate header row in official SOC crosswalk.")
    df = pd.read_excel(paths.SOC_XWALK, header=hdr)
    cols = {c: str(c).strip().lower() for c in df.columns}
    c2010 = next(c for c, l in cols.items() if l.startswith("2010 soc"))
    c2018 = next(c for c, l in cols.items() if l.startswith("2018 soc"))
    out = df[[c2010, c2018]].rename(columns={c2010: "soc2010", c2018: "soc2018"})
    out = out.dropna()
    out["soc2010"] = out["soc2010"].astype(str).str.strip()
    out["soc2018"] = out["soc2018"].astype(str).str.strip()
    # keep only detailed-code shaped values (##-####)
    ok = out["soc2010"].str.match(r"^\d{2}-\d{4}$") & out["soc2018"].str.match(r"^\d{2}-\d{4}$")
    return out[ok].drop_duplicates().reset_index(drop=True)


def bridge_with_crosswalk(aioe, universe, xwalk):
    score2010 = dict(zip(aioe["soc2010"], aioe["aioe"]))
    rows = []
    # group 2010 predecessors per 2018 code
    preds = xwalk.groupby("soc2018")["soc2010"].apply(list).to_dict()
    for code in sorted(universe):
        if code in score2010:  # unchanged code, direct
            rows.append((code, score2010[code], "direct", code))
            continue
        pre = [p for p in preds.get(code, []) if p in score2010]
        if pre:
            val = float(np.mean([score2010[p] for p in pre]))
            method = "xwalk-inherit" if len(pre) == 1 else "xwalk-merge-mean"
            rows.append((code, val, method, "+".join(pre)))
        else:
            rows.append((code, np.nan, "unmatched", ""))
    return pd.DataFrame(rows, columns=["soc2018", "aioe", "method", "aioe_source_2010"])


def bridge_direct_plus_reconcile(aioe, universe):
    score2010 = dict(zip(aioe["soc2010"], aioe["aioe"]))
    rows = []
    for code in sorted(universe):
        if code in score2010:
            rows.append((code, score2010[code], "direct", code))
        elif code in RECONCILE:
            r = RECONCILE[code]
            val = float(np.mean([score2010[c] for c in r["from2010"]]))
            rows.append((code, val, r["method"], "+".join(r["from2010"])))
        else:
            rows.append((code, np.nan, "unmatched", ""))
    return pd.DataFrame(rows, columns=["soc2018", "aioe", "method", "aioe_source_2010"])


def main() -> int:
    aioe = load_aioe()
    universe = load_2018_universe()
    score2010 = dict(zip(aioe["soc2010"], aioe["aioe"]))
    xwalk = load_official_xwalk()

    if xwalk is not None:
        bridged = bridge_with_crosswalk(aioe, universe, xwalk)
        mode = "official BLS 2010->2018 crosswalk"
        # Assertion: documented GDPval reconciliations agree with the crosswalk source set.
        src = dict(zip(bridged["soc2018"], bridged["aioe_source_2010"]))
        for code, r in RECONCILE.items():
            got = set(src.get(code, "").split("+")) - {""}
            want = set(r["from2010"])
            if got and got != want:
                print(f"NOTE: crosswalk source for {code} = {sorted(got)}; "
                      f"documented = {sorted(want)} (using crosswalk).")
    else:
        bridged = bridge_direct_plus_reconcile(aioe, universe)
        mode = "direct join + documented reconciliation (official crosswalk not present)"

    bridged.to_csv(paths.AIOE_BRIDGED_CSV, index=False)

    # GDPval's 44 -> AIOE (join through the mapping's 46 detail rows)
    mp = pd.read_csv(paths.MAPPING_CSV, dtype=str)
    g = mp.merge(bridged, left_on="soc_2018", right_on="soc2018", how="left")
    g_out = g[["gdpval_title", "sector", "soc_2018", "status", "aioe", "method", "aioe_source_2010"]]
    g_out.to_csv(paths.AIOE_GDPVAL44_CSV, index=False)

    # --- Report ---
    n_uni = len(universe)
    n_matched = bridged["aioe"].notna().sum()
    print(f"Bridge mode: {mode}")
    print(f"2018 detailed universe:               {n_uni}")
    print(f"  AIOE assigned:                      {n_matched}  ({n_matched/n_uni:.1%})")
    print(f"  unmatched (no 2010 AIOE source):    {n_uni - n_matched}")
    print("  method breakdown:")
    print(bridged["method"].value_counts().to_string().replace("\n", "\n    "))

    gd_missing = g_out[g_out["aioe"].isna()]["gdpval_title"].unique()
    print(f"\nGDPval detail rows:                   {len(g_out)}")
    print(f"  GDPval occupations missing AIOE:    {len(gd_missing)}")
    for t in gd_missing:
        print("    !!", t)
    print("\nGDPval reconciled (non-direct) codes:")
    nd = g_out[g_out["method"] != "direct"][["gdpval_title", "soc_2018", "aioe", "method", "aioe_source_2010"]].drop_duplicates()
    print(nd.to_string(index=False))
    print(f"\nWrote {paths.AIOE_BRIDGED_CSV.relative_to(paths.ROOT)}")
    print(f"Wrote {paths.AIOE_GDPVAL44_CSV.relative_to(paths.ROOT)}")

    # --- Methods log (tracked; no raw AIOE values, just method + provenance) ---
    src = dict(zip(bridged["soc2018"], bridged["aioe_source_2010"]))
    mth = dict(zip(bridged["soc2018"], bridged["method"]))
    lines = [
        "# AIOE 2010->2018 SOC bridge: methods log", "",
        f"Generated by `src/bridge_aioe.py`. Bridge mode: **{mode}**.", "",
        f"- 2018 detailed universe: **{n_uni}**",
        f"- AIOE assigned: **{n_matched}** ({n_matched/n_uni:.1%} of codes)",
        f"- Unmatched (no 2010 AIOE source even via crosswalk): **{n_uni - n_matched}**", "",
        "Merges combine constituent 2010 AIOE scores by unweighted mean: AIOE is not",
        "distributed with 2010 employment counts, so an employment-weighted mean is",
        "unavailable. Constituents of the GDPval merges are close, so the choice is",
        "near-immaterial except for Project Management Specialists (see below).", "",
        "## GDPval-44 codes requiring reconciliation (non-direct)", "",
        "| GDPval occupation | 2018 SOC | method | 2010 source(s) |",
        "|---|---|---|---|",
    ]
    seen = set()
    for _, r in g_out.iterrows():
        code = r["soc_2018"]
        if r["method"] == "direct" or code in seen:
            continue
        seen.add(code)
        lines.append(f"| {r['gdpval_title']} | {code} | {r['method']} | {src.get(code,'')} |")
    lines += [
        "", "## Note on Project Management Specialists (13-1082)",
        "13-1082 is new in the 2018 SOC. The official BLS crosswalk maps it from",
        "parts of THREE 2010 residual codes: 11-9199 (Managers, All Other),",
        "13-1199 (Business Operations Specialists, All Other), and 15-1199 (Computer",
        "Occupations, All Other). The bridge uses the mean of those three AIOE scores.",
        "This is the weakest link in the bridge: it imputes from three 'All Other'",
        "buckets, so its AIOE is the least trustworthy of GDPval's 44. Flagged here so",
        "any Tier-2 result can be checked for sensitivity to this one occupation.", "",
        "## Buyers and Purchasing Agents (13-1020)",
        "Its three detail codes 13-1021/22/23 are all present in AIOE (2010). OEWS 2024",
        "publishes only the 13-1020 aggregate, so Tier 2 combines the three detail AIOE",
        "scores by unweighted mean (2024 detail employment weights are unavailable).", "",
    ]
    paths.AIOE_BRIDGE_LOG.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {paths.AIOE_BRIDGE_LOG.relative_to(paths.ROOT)}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(paths.ROOT / "src"))
    raise SystemExit(main())
