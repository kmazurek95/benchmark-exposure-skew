# Modal-sector assignment log (within-sector baseline)

GDPval assigned occupations to sectors via the 2023 National Employment
Matrix ("sector with the highest employment for each occupation"). The 2023
matrix is not reachable; this uses the May 2024 OEWS national industry file
(natsector), which gives occupation employment across 20 mutually-exclusive
NAICS sectors. Government is NAICS 99 (OEWS designation excluding government
schools and hospitals); this is narrower than GDPval's BEA/NEM Government,
a documented soft-spot detailed below.

- Occupations assigned: **830**
- Modal sector in GDPval's nine: **514**
- Validation, GDPval's 44 landing in their GDPval-assigned sector: **42/44**

## Ownership de-duplication and partition reconciliation
The natsector file gives ONE combined-ownership row per (occupation, NAICS
sector), so no summation across OEWS OWN_CODEs is performed and none is
needed. (The finer 3-digit files use overlapping combined codes with no full
total and would double-count under naive summation; those are not used here.)
Checked against the cross-industry totals: no occupation's sector employment
exceeds its cross-industry total (max ratio 1.0003), so there is no
ownership double-count, and the employment-weighted reconciliation is
99.7%. It is NOT an exact partition per
occupation: only 53% reconcile within 0.5%, because small
occupations have suppressed fine-sector cells that fall short of the total.
Those cells are too small to be the argmax, so the modal assignment is
unaffected; the earlier 'sums to within rounding' phrasing was too strong.

## Denominator boundary fragility
A third of the within-nine employment (34%) sits on occupations whose
modal sector holds under 40% of their employment, but most of those split
between two IN-nine sectors, which does not change membership. The
membership-relevant fragility is smaller: 29 occupations (5.8% of the
denominator) are in the nine with an out-of-nine runner-up within 10 points,
and 22 occupations outside the nine (6,840,850 workers) have an in-nine
runner-up equally close. Flipping these moves within-sector coverage within
about 29.0% to 33.0%, so 31.1% is stable to roughly two points.

## Judgment call and soft-spot: Government
GDPval's Government is a BEA / National Employment Matrix sector that includes
public education and public hospitals. OEWS has no matching sector: its
Government (NAICS 99) EXCLUDES government schools and hospitals, parking them
in Educational Services (61) and Health Care (62). NAICS 99 is used as the
Government sector, but it is narrower than GDPval's, and that is the main
soft-spot of this baseline: government-education occupations land in Education
(61, outside the nine) rather than Government, so the within-nine population
may under-include some public-sector workers GDPval's framework would count.

## Mismatches (GDPval-assigned sector vs OEWS-modal sector)

| Occupation | GDPval sector | OEWS-modal sector | still in the nine? | why |
|---|---|---|---|---|
| Concierges | Real Estate and Rental and Leasing | Health Care and Social Assistance | yes | split occupation; 2024 OEWS employs more concierges in health-care settings than in real estate |
| Child, Family, and School Social Workers | Government | Health Care and Social Assistance | yes | social assistance (NAICS 62) is the modal industry; the narrower NAICS-99 Government excludes such government social services |

Both mismatches remain inside the nine-sector population, so the
within-sector comparison is unaffected in membership; only the sector label
differs. The social-worker case is a direct symptom of the Government
soft-spot above.
