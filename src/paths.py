"""Shared paths for the benchmark-exposure-skew pipeline.

Every path is resolved relative to the repo root so scripts run from anywhere.
Raw third-party data lives under data/raw/ (gitignored); derived outputs the
project authors go to outputs/ and figures/.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW = ROOT / "data" / "raw"
OUTPUTS = ROOT / "outputs"
# Per-occupation tables that carry third-party (AIOE / OEWS / Webb) values live
# here and are gitignored; only aggregate results and our own mapping are tracked.
OUTPUTS_LOCAL = OUTPUTS / "local"
FIGURES = ROOT / "figures"

# Raw inputs
GDPVAL_44 = RAW / "gdpval_44_occupations_verbatim.csv"
ONETSOC_2019 = RAW / "onetsoc2019.xlsx"
CENSUS_XWALK = RAW / "census2018_occ_crosswalk.xlsx"
AIOE_MAIN = RAW / "aioe_felten2021_dataappendix.xlsx"
AIOE_LM = RAW / "aioe_language_modeling_aioe_aiie.xlsx"
WEBB = RAW / "webb_exposure_by_occ1990dd_lswt2010.csv"
# OEWS May 2024 national (oesm24nat.zip -> national_M2024_dl.xlsx); acquired manually.
OEWS_DIR = RAW / "oesm24nat"
# Official BLS 2010->2018 SOC crosswalk (soc_2010_to_2018_crosswalk.xlsx); acquired manually.
SOC_XWALK = RAW / "soc_2010_to_2018_crosswalk.xlsx"
# OEWS May 2024 national industry-specific (oesm24in4.zip); natsector member gives
# occupation employment by 20 NAICS sectors (Government = NAICS 99).
OEWS_IND_ZIP = RAW / "oesm24in4.zip"
OEWS_IND_SECTOR_MEMBER = "oesm24in4/natsector_M2024_dl.xlsx"

# Derived outputs -- TRACKED (our own work, no third-party per-occupation values)
MAPPING_CSV = OUTPUTS / "gdpval_44_soc_mapping.csv"
MAPPING_LOG = OUTPUTS / "gdpval_44_soc_mapping_log.md"
AIOE_BRIDGE_LOG = OUTPUTS / "aioe_bridge_log.md"

# Derived outputs -- LOCAL (carry third-party per-occupation values; gitignored)
AIOE_BRIDGED_CSV = OUTPUTS_LOCAL / "aioe_2018soc_bridged.csv"
AIOE_GDPVAL44_CSV = OUTPUTS_LOCAL / "aioe_gdpval44.csv"
TIER1_OCC_LOCAL = OUTPUTS_LOCAL / "tier1_gdpval44_employment_wage.csv"

TIER2_OCC_LOCAL = OUTPUTS_LOCAL / "tier2_gdpval44_aioe.csv"

# Aggregate results -- TRACKED (no per-occupation third-party values)
TIER1_SUMMARY = OUTPUTS / "tier1_coverage_summary.json"
FIG_TIER1 = FIGURES / "tier1_wage_coverage.png"
TIER2_SUMMARY = OUTPUTS / "tier2_aioe_summary.json"
FIG_TIER2 = FIGURES / "tier2_aioe_exposure.png"
WITHIN_SECTOR_SUMMARY = OUTPUTS / "within_sector_summary.json"
MODAL_SECTOR_LOG = OUTPUTS / "modal_sector_assignment_log.md"
FIG_WITHIN = FIGURES / "within_sector_baselines.png"
WEBB_BRIDGE_SUMMARY = OUTPUTS / "webb_bridge_lossiness.json"
DERIVED_CHECKS = OUTPUTS / "derived_checks.json"
WEBB_BRIDGE_LOG = OUTPUTS / "webb_bridge_log.md"
WEBB_SOC_LOCAL = OUTPUTS_LOCAL / "webb_2018soc_bridged.csv"
# Dorn 2010-Census-occ -> occ1990dd crosswalk (occ2010_occ1990dd.zip), for Webb.
DORN_XWALK = RAW / "occ2010_occ1990dd.zip"

for _d in (OUTPUTS, OUTPUTS_LOCAL, FIGURES):
    _d.mkdir(parents=True, exist_ok=True)
