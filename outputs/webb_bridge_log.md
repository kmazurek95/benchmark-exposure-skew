# Tier 3 (Webb): occ1990dd -> 2018 SOC bridge lossiness

Webb is distributed by occ1990dd (Dorn's harmonized 1990 Census codes),
not SOC, with no official bridge. This assessment builds the bridge only
far enough to measure its lossiness, then applies the pre-registered
decision rule. It does not reconstruct the multi-hop CPS-weighted pipeline
used by EIG/Yale, because the pre-registration (section 3) already
established that Webb shares O\*NET construction and so cannot serve as the
independent check; a forced comparison would add a caveated measure of no
load-bearing value.

## Bridge chain (public, documented crosswalks)
Webb occ1990dd -> Dorn occ2010_occ1990dd (2010 Census occ) -> Census 2010->2018
crosswalk (2018 SOC).

## Lossiness
- Webb scored occ1990dd codes: **338**
- Reaching a 2018 SOC code: **277** (82%)
- SOC -> occ1990dd single-valued: **100%** (clean at the SOC level)
- occ1990dd -> SOC fan-out: mean **1.47**, max 13 (Webb scores apply at a coarser resolution)
- **Employment coverage: 55% mapped, 45% UNMAPPED**

## The unmapped fraction is not a benign random slice
Employment-weighted mean AIOE is +0.10 among mapped
occupations vs -0.01 among unmapped, and mean wage
$71,123 vs $63,980.
The gaps are modest but consistent: the mapped 55% skews slightly higher on
both wage and AIOE, so it is not a representative subsample of the workforce.
The decisive problem is simply the size of the loss, 45% of employment.

## Verdict (pre-registered)
The bridge leaves roughly 45% of US employment without a Webb score, and the
unmapped set is systematically different. Per the pre-registration (sections
2-3), this is reported as the Tier-3 finding rather than presenting a forced
mapping as clean: the most-cited non-abilities exposure measure will not
cleanly join the SOC classification the rest of the literature uses. Because
Webb also shares O\*NET construction, even a clean bridge could not have
changed the load-bearing conclusion; Tier 1 carries the argument.
