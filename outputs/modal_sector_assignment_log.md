# Modal-sector assignment log (within-sector baseline)

GDPval assigned occupations to sectors via the 2023 National Employment
Matrix ("sector with the highest employment for each occupation"). The 2023
matrix is not reachable; this uses the May 2024 OEWS national industry file
(natsector), which gives occupation employment across 20 mutually-exclusive
NAICS sectors. Government is NAICS 99 (OEWS designation excluding government
schools and hospitals), matching how the Matrix separates Government.

- Occupations assigned: **830**
- Modal sector in GDPval's nine: **514**
- Validation, GDPval's 44 landing in their GDPval-assigned sector: **42/44**

## Ownership de-duplication
The natsector file gives ONE combined-ownership row per (occupation, NAICS
sector), so no summation across OEWS OWN_CODEs is performed and none is
needed. (The finer 3-digit files use overlapping combined codes with no full
total and would double-count under naive summation; those are not used here.)
As a check, each occupation's per-sector employment sums to its cross-industry
total to within rounding, so the sectors partition employment cleanly.

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
