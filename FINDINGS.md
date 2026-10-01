# Findings: Does GDPval's Sampling Frame Select High-Exposure Occupations?

This is the results document for the pre-registered analysis in
[pre_registration.md](pre_registration.md). It reports what the analysis found,
in the order the pre-registration fixed: Tier 1 (employment and wage coverage)
first, because it is the load-bearing evidence and carries no exposure-measure
artifact; then Tier 2 (AIOE exposure), with the caveat the pre-registration
attaches to it stated up front rather than in a footnote.

**Status.** Both baselines the pre-registration commits to (economy-wide and
within GDPval's nine sectors) are complete for Tiers 1 and 2. Tier 3 (Webb) ends in
a documented null, explained in section 6. Every number here is reproduced by the
pipeline in `src/`; the figures are in `figures/`; the per-occupation tables that
carry third-party values are kept local under `outputs/local/` and are not
redistributed.

---

## 1. Summary

Two findings, in the order of confidence the pre-registration assigns them.

**Tier 1, the spine.** GDPval's 44 occupations account for **19.2% of US
employment** (29.7 million of 154.2 million workers, May 2024). They also sit high
in the wage distribution: in the employment-weighted distribution of occupational
mean annual wages (the OEWS unit), the GDPval frame's median is **$98,300, against
$52,400 for the workforce as a whole**, placing the median GDPval-covered worker at
the **82nd percentile** nationally (the **73rd** even against other occupations in
GDPval's own nine sectors). This tier uses no exposure measure; it rests only on
the occupation-to-SOC mapping and public BLS data.

The two numbers do not carry equal weight. GDPval selected the predominantly
digital occupations that contribute most to total wages and compensation, a wage
bill, so the wage-position result partly reflects the selection rule rather than
being an independent finding. The **employment coverage (19.2%, and 31.1%
within-sector) is the load-bearing number.** Coverage is not the selection target,
and the wage-bill rule if anything tilts toward large-employment occupations, so the
44 reach more of the workforce than 44 occupations chosen without regard to size
would. 19.2% is a generous reading of the frame's coverage: a size-blind selection
would typically cover less, so the under-coverage is if anything understated. The wage-bill criterion also
explains why some lower-wage but high-headcount occupations (Concierges, Recreation
Workers, Customer Service Representatives) sit in a frame otherwise dominated by
high-paying work: they enter on a large wage bill built from employment, not wage.
This is what the piece leads with.

**Tier 2, the caveated extension.** GDPval's 44 also sit higher on AIOE (AI
Occupational Exposure) than the employment-weighted workforce: employment-weighted
median AIOE **+0.95 against +0.03**, with the median GDPval occupation at the 69th
percentile of the workforce AIOE distribution (64th within its own nine sectors)
and a rank test significant at p about 2e-07. Per the decision rule fixed in
advance (pre_registration.md section 4), **this skew is reported but is not claimed
to be substantive.** AIOE and GDPval's own "predominantly digital" filter are both
built from O\*NET, so a skew here cannot be separated from that shared
construction. This is the uninterpretable outcome. The pre-registration
anticipated the temptation to read it as vindication and fixed the interpretation
in advance to prevent exactly that. As a descriptive aside, the frame is somewhat
more distinctive on wages (82nd percentile) than on AIOE (69th). But Tier 1 carries
the argument for one reason: it is artifact-free. The AIOE comparison inherits the
shared-O\*NET problem whatever its magnitude, while the coverage result rests on
public wage and employment data alone.

A word on how to read this. The exposure tiers, 2 and 3, were pre-registered as
secondary to Tier 1, and both resolved exactly as the design anticipated: Tier 2 is
uninterpretable because AIOE shares O\*NET construction with GDPval's digital
filter, and Tier 3 is a documented null because the occ1990dd-to-SOC bridge is too
lossy to trust and Webb is not O\*NET-independent in any case. The design was
deliberately better powered against the hypothesis than for it (section 4), so these
are honest nulls, reported as the point rather than as a shortfall. The
load-bearing, deliberate contribution is the employment-coverage disclosure and the
reporting standard it demonstrates (section 8), not a finding about AI exposure.
Nothing here shows GDPval is biased toward exposed work; it shows what the frame
contains and how little of the workforce it speaks for.

---

## 2. Data and methods

**Occupation frame.** GDPval's 44 occupations were extracted verbatim from Table 1
of the GDPval paper (arXiv:2510.04374v1). GDPval's sampling rule (nine sectors
above 5% of US GDP by value added, then, within each, the predominantly digital
occupations that contribute most to total wages and compensation) is stated by
OpenAI in section 2.1 of the paper, with further detail in appendix A.7; this
analysis does not claim to have discovered it. The selection criterion is a wage
bill, wage times employment, not a wage rate; section 3 draws out what that implies
for the wage-position result.

**Unit and vintage.** The unit is the occupation, keyed to the 2018 SOC at the
6-digit detailed level. GDPval's frame is already 2018-SOC-native (it was built on
the May 2024 OEWS), so the mapping is close to one-to-one.

**Mapping (`src/build_mapping.py`).** Each of the 44 titles was assigned a 2018 SOC
code, and every assigned code was re-verified against the O\*NET-SOC 2019 taxonomy
on disk rather than asserted from memory. Result: 43 of 44 map cleanly to a single
detailed code; 1 is a judgment call (Buyers and Purchasing Agents, a broad group,
handled below); 0 fail. The full mapping and its judgment-call log are in
`outputs/gdpval_44_soc_mapping.csv` and `outputs/gdpval_44_soc_mapping_log.md`.

**Employment and wages.** BLS OEWS May 2024 national cross-industry estimates
(`oesm24nat.zip`). The occupation universe is the OEWS detailed set (O_GROUP =
detailed, 831 occupations); aggregate rows (major, minor, broad) are never summed
into the denominator. As a check, the detailed employment total (154,186,300)
reproduces the published "All Occupations" total (154,187,380) to within 0.001%.
OEWS suppression markers are handled explicitly and never coerced to zero: `*` and
`**` become missing, `#` (a wage at or above the $239,200 disclosure cap) is kept
at the cap for medians and percentiles and flagged. The mean annual wage is not
top-coded in this file, so it is used as the primary wage measure. As a second
check, the employment-weighted mean of the detailed occupations' mean wages
($67,909) reproduces the published national mean ($67,920) to within $11.

**AIOE (`src/bridge_aioe.py`).** AIOE (Felten, Raj and Seamans) is keyed to the
2010 SOC across 774 occupations. It was bridged to the 2018 SOC using the official
BLS 2010-to-2018 crosswalk: unchanged codes join directly; merges combine the
constituent 2010 scores by unweighted mean (2010 employment weights are not
distributed with AIOE). The bridge covers 96.8% of 2024 employment, and all 44
GDPval occupations receive a score. Reconciliations, including the one weak
imputation (Project Management Specialists, new in 2018, imputed from three 2010
"All Other" buckets), are logged in `outputs/aioe_bridge_log.md`.

**Weighting and tests.** All distributions are employment-weighted using OEWS
employment counts. Wage and exposure positions are reported as the full
distribution (overlaid employment-weighted empirical CDFs) and as summary
quantiles, not a difference in means alone. The figures are empirical CDFs rather
than smoothed densities on purpose: GDPval's side is 44 occupation-means with
heavy-tailed weights, and a kernel density would manufacture a smoothness the data
do not have. Tier 2 adds an occupation-level rank test
(Mann-Whitney U, GDPval's 44 against the complement).

**One mapping subtlety worth stating.** Buyers and Purchasing Agents is a 2018 SOC
broad group (13-1020) whose three detailed codes (13-1021/22/23) exist in the
taxonomy and in AIOE but are not published separately in OEWS May 2024, which
reports 13-1020 as its own detailed line. Tier 1 therefore uses the 13-1020
employment total (486,900), which is already the single line in the detailed
denominator, so the numerator stays consistent with the denominator. Tier 2
combines the three detailed AIOE scores by unweighted mean, since 2024 detail
employment weights are unavailable. Both choices are logged.

---

## 3. Tier 1: employment coverage and wage position (economy-wide)

**Coverage.** Two universes were fixed in advance (pre_registration.md section 6),
because they answer different questions and the choice should not be made after
seeing the result.

| Denominator | GDPval-44 coverage |
|---|---|
| All detailed occupations, including "All Other" residuals (primary) | **19.2%** |
| All detailed occupations, excluding "All Other" | 20.0% |
| Published "All Occupations" total row | 19.2% |

GDPval's 44 occupations employ 29.7 million workers. Reading the headline GDPval
score as an economy-wide signal implicitly treats these 44 occupations as
representative of the roughly 81% of employment they do not cover. Coverage is the
load-bearing number here. It is not the selection target, and because the wage-bill
rule tilts toward large-employment occupations, the 44 reach more of the workforce
than 44 occupations chosen without regard to size would. 19.2% is a generous reading
of the frame's coverage: a size-blind selection would typically cover less.

**Wage position.** The wage measure is each occupation's mean annual wage (the OEWS
unit), and the distribution is over workers, weighting each occupation's mean by its
employment; it is not a worker-level wage distribution. On that measure the 44 sit above the
workforce at every percentile shown below, from the 10th to the 90th.

| Employment-weighted distribution of occupational mean wage | Workforce | GDPval's 44 |
|---|---|---|
| 10th percentile | $35,000 | $45,400 |
| 25th percentile | $40,900 | $71,300 |
| Median | $52,400 | $98,300 |
| 75th percentile | $81,600 | $133,100 |
| 90th percentile | $121,300 | $160,000 |
| Employment-weighted mean | $67,900 | $100,800 |

The median GDPval-covered worker sits at the 82nd percentile of the national
distribution. This gap is real but, unlike coverage, it is partly mechanical:
GDPval selected on a wage bill, which rewards high wages, so a rightward wage shift
is expected from the rule itself and should not be read as an independent finding.
The figure is [figures/tier1_wage_coverage.png](figures/tier1_wage_coverage.png):
the two employment-weighted empirical CDFs, GDPval's curve well right of the
workforce across the range, with the 82nd-percentile crossing marked and a rug of
the 44 occupation-means underneath.

**Two derived checks.** Two further numbers come from `src/derived_checks.py` and
are recorded in `outputs/derived_checks.json`. The 44 occupations' wage bill,
employment times mean annual wage summed over the frame, is $2.99 trillion
($2.9917T), which reproduces the "$3T annually" GDPval reports for these
occupations; GDPval's own Table 1 figures sum to $2,991.7 billion. That is 28.6%
of the OEWS wage bill (published total employment times the published national
mean wage, so wage and salary jobs only), earned in occupations holding 19.2% of
employment. As a size-blind baseline, 200,000 draws of 44 occupations taken
uniformly from the 831 detailed occupations cover 5.3% of employment on average
(median 5.1%, 95th percentile 8.7%), and none reaches 19.2%; drawn only from the
514 occupations modally in GDPval's nine sectors, they cover 8.6% of that
population on average, against GDPval's 31.1%. These are descriptive baselines,
not hypothesis tests: GDPval's 44 were chosen by a rule, not sampled, and the
draws show only how far the wage-bill rule reaches beyond what 44 occupations
picked without regard to size would cover.

---

## 4. Tier 2: AIOE exposure (economy-wide, caveated)

**The caveat comes first.** AIOE is built from O\*NET ability ratings; GDPval's
"predominantly digital" filter is built from O\*NET task classifications. They
share the same task universe. A skew in AIOE across GDPval's frame therefore
cannot be attributed to substantive AI exposure rather than to that shared
construction, on this evidence alone. The pre-registration establishes this in
section 3 and fixes the interpretation in section 4.

**The result.** A skew is present.

| Employment-weighted AIOE (standardized) | Workforce | GDPval's 44 |
|---|---|---|
| 10th percentile | -1.29 | 0.05 |
| 25th percentile | -0.79 | 0.42 |
| Median | 0.03 | 0.95 |
| 75th percentile | 1.01 | 1.22 |
| 90th percentile | 1.29 | 1.36 |
| Employment-weighted mean | 0.03 | 0.78 |

The median GDPval occupation sits at the 69th percentile of the workforce AIOE
distribution. An occupation-level rank test (Mann-Whitney U, the 44 against the
735 other scored occupations) gives U = 23,698, p is about 2.1e-07; a randomly
chosen GDPval occupation outranks a randomly chosen other occupation on AIOE about
73% of the time. The figure is
[figures/tier2_aioe_exposure.png](figures/tier2_aioe_exposure.png): the two
employment-weighted empirical CDFs, GDPval's curve well right of the workforce,
with the 69th-percentile crossing marked and a rug of the 44 underneath.

**What this does and does not license (pre_registration.md section 4).** The
finding is that GDPval's 44 sit higher on AIOE than the employment-weighted
workforce. It is reported, and it is not claimed to be substantive, because the
measure most mechanically disposed to produce this skew (AIOE, which shares O\*NET
construction with GDPval's digital filter) is exactly the measure producing it.
The asymmetry fixed in advance is that a skew present under AIOE is uninterpretable
while a skew absent under AIOE would have been close to dispositive against the
critique. The design is better powered against the hypothesis than for it, and
that is deliberate. Tier 1 remains the load-bearing evidence.

---

## 5. Within-sector baseline (the fairer test)

The economy-wide baseline answers whether GDPval's score can be read as an
economy-wide signal. The within-sector baseline answers a different and fairer
question: holding the sector gate constant, did GDPval's occupation rule still
pick the high-wage, high-exposure occupations within the sectors it chose? It
restricts the comparison to occupations whose modal sector is one of GDPval's
nine.

**Method.** GDPval assigned occupations to sectors using the 2023 National
Employment Matrix, mapping each occupation to the sector with its highest
employment (paper section 2.1 and A.7). The 2023 matrix is not reachable, so the
assignment is reproduced from the vintage-consistent May 2024 OEWS national
industry file (`src/sectors.py`), which gives occupation employment across 20
mutually-exclusive NAICS sectors, one combined-ownership row per occupation-sector.
No summation across OEWS ownership codes is done or needed, so there is no
double-count (the finer 3-digit OEWS files, which use overlapping ownership codes
with no full total, are not used). As a check against the cross-industry totals, no
occupation's sector employment exceeds its cross-industry total (max ratio 1.0003),
which confirms there is no ownership double-count, and the employment-weighted
reconciliation is 99.7%. It is not an exact per-occupation partition (only about
half of occupations reconcile within 0.5%, because small occupations have suppressed
fine-sector cells that fall short of the total), but those suppressed cells are far
too small to be the argmax, so the modal assignment is unaffected.

The assignment is at the occupation level, the way GDPval did it: an occupation's
entire national employment is attributed to its single modal sector, not split
across the several sectors it actually works in. So the within-nine population, and
the 31.1% coverage denominator, are the employment of occupations modally assigned
to the nine sectors, not the employment physically located in those nine NAICS
industries. Those two quantities differ, and this analysis reports the first.

**The Government soft-spot.** GDPval's Government is a BEA and National Employment
Matrix sector that includes public education and public hospitals. OEWS has no
matching sector: its Government (NAICS 99) excludes government schools and hospitals,
parking them in Educational Services (NAICS 61) and Health Care (NAICS 62). NAICS 99
is used as the Government sector, but it is narrower than GDPval's, and this is the
main weakness of the secondary baseline: government-education occupations land in
Educational Services, which is not one of the nine, so the within-nine population
may under-include public-sector workers GDPval's framework would count. Government
hospitals land in Health Care, which is one of the nine, so those are retained.

**Validation.** The proxy is checked against GDPval's own 44, whose GDPval-assigned
sector is known: **42 of 44 land in the sector GDPval assigned them.** The two
exceptions both fall in Health Care rather than their GDPval sector and both remain
inside the nine, so only their label differs: Concierges (GDPval: Real Estate) is a
split occupation that 2024 OEWS employs more in health-care settings than in real
estate; Child, Family, and School Social Workers (GDPval: Government) is modally in
Social Assistance (NAICS 62), and the second case is a direct symptom of the
narrow-Government soft-spot above. The population is 514 occupations, 95.4 million
workers or about 62% of US employment, counting each occupation's full national
employment toward its modal sector (see the Method note above). The log is
`outputs/modal_sector_assignment_log.md`.

**Denominator robustness.** The 31.1% is the softest number in the piece, and its
denominator, the 95.4 million, has no external anchor the way the economy-wide side
does, so it is bounded directly (the figures are in the summary JSON). The boundary
is not brittle. A third of the 95.4 million sits on occupations whose modal sector
holds under 40% of their employment, but most of those split between two of the nine
sectors, so membership does not change. The membership-relevant fragility is 5.8% of
the denominator: 29 occupations are in the nine but have a runner-up sector outside
it within 10 points, roughly offset by 22 occupations outside the nine (6.8 million
workers) whose runner-up is inside. Flipping every one of them would move
within-sector coverage only within about 29% to 33%, so 31.1% is stable to roughly
two points.

**The finding holds, attenuated.** Even against other occupations in the same nine
sectors, GDPval's 44 sit high on both measures, though less extremely than against
the whole economy.

| Measure | Economy-wide | Within GDPval's nine sectors |
|---|---|---|
| Tier 1: employment coverage | 19.2% | 31.1% |
| Tier 1: GDPval median wage percentile | 82nd | 73rd |
| Tier 1: baseline vs GDPval median wage | $52,400 vs $98,300 | $64,100 vs $98,300 |
| Tier 2: GDPval median AIOE percentile | 69th | 64th |
| Tier 2: baseline vs GDPval median AIOE | +0.03 vs +0.95 | +0.29 vs +0.95 |
| Tier 2: rank test p (GDPval vs complement) | 2.1e-07 | 4.1e-06 |

The within-sector baseline is itself elevated (its median wage $64,100 exceeds the
economy-wide $52,400, and its median AIOE +0.29 exceeds +0.03) because GDPval's
nine sectors are higher-wage, higher-exposure than the economy as a whole. That
GDPval's 44 still sit above even that elevated baseline is consistent with the
occupation rule, which by construction selects the predominantly digital occupations
with the largest wage bill within each sector; as economy-wide, the within-sector
wage gap is partly mechanical for the same reason, and the coverage figure (31.1%)
is the cleaner of the two. One detail a careful reader will notice: the within-sector
wage and AIOE percentile baselines include the 44 themselves, mirroring the
economy-wide tier, while the rank test excludes them; keeping the 44 in the baseline
slightly understates their distinctiveness, so the 73rd and 64th percentiles are
conservative. The figure is
[figures/within_sector_baselines.png](figures/within_sector_baselines.png). The
Tier 2 within-sector skew inherits the same O\*NET caveat as its economy-wide
counterpart and is subject to the same section 4 decision rule.

---

## 6. Tier 3 (Webb): a documented null

Webb is distributed by occ1990dd (Dorn's harmonized 1990 Census codes), not SOC,
with no official bridge. The pre-registration commits in advance to reporting a
documented null if the occ1990dd-to-SOC crosswalk proves too lossy to trust, rather
than presenting a forced mapping as clean. That is the outcome here.

This does not weaken Tier 1, and the asymmetry is worth stating plainly. Tier 1
needs no crosswalk: GDPval's frame is already native to the 2018 SOC, so its
mapping only verifies codes that already exist. Webb starts two classifications
away, in 1990 Census codes, and reaches the 2018 SOC only through a multi-hop
chain, which is where the 45% loss accumulates. A bridge that frays running
backward from a 1990 vintage says nothing about a frame that was 2018-SOC-native
to begin with.

The bridge was built only far enough to measure its lossiness, using public
crosswalks (`src/bridge_webb.py`): Webb occ1990dd, through Dorn's
`occ2010_occ1990dd`, to 2010 Census occupation, through the Census 2010-to-2018
crosswalk, to 2018 SOC. Deliberately, the multi-hop CPS-weighted pipeline that EIG
and Yale build was not reconstructed to force a comparison, because section 3
already established that Webb shares O\*NET construction and so cannot serve as the
independent check the design once hoped for; a forced Webb comparison would add a
caveated measure of no load-bearing value.

The measured lossiness:

- Of Webb's 338 scored occ1990dd codes, 277 (82%) reach a 2018 SOC code.
- At the SOC level the mapping is clean (each detailed SOC inherits a single
  occ1990dd), but occ1990dd is coarser: each occ1990dd fans out to 1.5 SOC codes on
  average and up to 13, so Webb's scores apply only at that coarse resolution.
- **The bridge leaves 45% of US employment with no Webb score** (312 of 831 detailed
  occupations mapped, covering 55% of employment).
- The missing 45% is not a benign random slice: mapped occupations are modestly
  higher on both AIOE (employment-weighted mean +0.10 vs -0.01) and wage ($71,100 vs
  $64,000), so the mapped 55% is not a representative subsample.

A measure that cannot be joined to the SOC classification for nearly half the
workforce, without a materially representative sample of the rest, cannot support a
trustworthy distributional comparison. Per the pre-registration, that is the Tier-3
finding: the most-cited non-abilities exposure measure will not cleanly join the
occupational classification the rest of the literature runs on. Because Webb also
shares O\*NET construction, even a clean bridge could not have changed the
load-bearing conclusion. The assessment is logged in `outputs/webb_bridge_log.md`.

---

## 7. Limitations

- The comparison is descriptive. It shows what GDPval's frame contains; it does
  not show what a better frame would be, and it makes no causal claim about AI and
  employment.
- Occupation-level exposure says nothing about which tasks within an occupation
  GDPval sampled. A frame could select high-exposure occupations and still sample
  their least-exposed tasks; this analysis cannot observe that.
- The Tier 2 skew is caveated by construction, as section 4 explains. No exposure
  measure obtainable here is built independently of O\*NET, so none can separate a
  substantive skew from a mechanical one.
- Buyers and Purchasing Agents is handled at the 13-1020 broad-group level in
  employment (an OEWS publication choice) and by unweighted mean of three detail
  scores in AIOE. Project Management Specialists' AIOE is imputed from three 2010
  "All Other" buckets and is the least trustworthy of the 44. Dropping it from the
  Tier 2 comparison moves the employment-weighted median AIOE from +0.95 to +0.94
  and leaves the 69th-percentile position and the rank test (p about 3e-07)
  unchanged; dropping Buyers is equally negligible, so the skew rests on neither
  judgment call.
- AIOE coverage is 96.8% of employment; the 3.2% with no bridged AIOE score is
  excluded from the Tier 2 distribution. Those occupations are disproportionately
  residual and newly created codes; if they are lower-exposure on average, their
  exclusion lifts the baseline slightly and so understates the GDPval skew, which is
  the conservative direction for a result already reported as caveated.
- The within-sector baseline reproduces GDPval's 2023 National Employment Matrix
  sector assignment with the May 2024 OEWS industry file. This is a
  vintage-consistent proxy, not GDPval's exact source (the 2023 matrix bulk file
  was not reachable); it agrees with GDPval's own assignment on 42 of 44
  occupations. Its Government sector (OEWS NAICS 99) is narrower than GDPval's
  BEA/NEM Government, excluding public schools and hospitals; section 5 details the
  consequence for the nine-sector population.

---

## 8. The constructive point: a reporting standard, not a better frame

The pre-registration (section 10) commits to no canonical exposure target and to
proposing no reweighted frame. The constructive contribution is a disclosure
standard. GDPval does not report the employment coverage of its occupation set, so
a reader cannot tell from the paper what share of the labor force its 44
occupations speak for. Tier 1 is the demonstration that this is cheap to report:
the employment share and the wage-distribution position are computed here from
public data and the official crosswalk alone. An economic-value benchmark that
published these two numbers alongside its headline score would let a reader price
in the scope the number actually covers. A scoped instrument reported with its
scope is honest work; the same instrument read as an economy-wide signal because
its scope was never stated is not.
