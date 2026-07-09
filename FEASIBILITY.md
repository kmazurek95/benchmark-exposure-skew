# FEASIBILITY.md — Benchmark Exposure Skew

**Scope:** a bounded feasibility check answering three questions. This is **not** the analysis.
No distributions were computed; no measure was reweighted; the pre-registration and foundation
sheet were not modified.

**Date run:** 2026-07-08.
**Environment caveat that shaped the work:** `www.bls.gov` returns an Akamai **HTTP 403 "Access
Denied"** to this sandbox (both `curl` with many header variants and the hosted WebFetch). So BLS
files could not be pulled directly here; BLS *facts* were confirmed from BLS-authored text surfaced
in search results, and BLS *code lists* were verified via reachable primary mirrors (O*NET Resource
Center, U.S. Census Bureau). Every such substitution is flagged inline. Full provenance for every
file: [`data/raw/SOURCES.md`](data/raw/SOURCES.md), plus [`sources/aioe/SOURCES.md`](sources/aioe/SOURCES.md)
and [`sources/webb-ai/SOURCES.md`](sources/webb-ai/SOURCES.md).

---

## TL;DR — the three answers

| # | Question | Answer |
|---|---|---|
| **1** | Crosswalk hit rate (GDPval 44 → SOC) | **43 clean / 1 judgment call / 0 fail** at GDPval's native 2018-SOC vintage. The one judgment call is *Buyers and Purchasing Agents* (an aggregate of 3 detailed codes). The rate degrades to **~4 judgment calls** once you crosswalk to a 2010-SOC exposure measure — all resolvable via the official BLS 2010↔2018 crosswalk. |
| **2** | Webb data usable, SOC-keyed, public? | **Public: yes. SOC-keyed: NO.** A real, un-gated CSV exists (341 occupations, separate `pct_ai`/`pct_software`/`pct_robot`) but it is keyed to **`occ1990dd`** (1990 Census harmonized codes), not SOC. Using it requires a self-built occ1990dd→SOC crosswalk for which **no official BLS bridge exists**. |
| **3** | SOC vintage alignment | **AIOE = 2010 SOC. BLS OES = 2018 SOC. Webb = neither** (distributed as occ1990dd; *constructed* on O*NET-SOC 2010). GDPval's own frame = 2018 SOC. Official **BLS 2010↔2018 SOC crosswalk exists**; **no official occ1990dd↔SOC crosswalk exists.** |

**Verdict (one line):** The analysis is practical as specified **except that Webb — which the
pre-registration makes load-bearing — is not SOC-keyed**, and bridging it to SOC is the single
component that most threatens the timeline and the clean-comparison credibility. Details in §Verdict.

---

## Q1 — CROSSWALK HIT RATE

**Source of the 44 occupations:** GDPval paper, arXiv:2510.04374v1, **Table 1** ("Top Occupations and
Total Compensation"). Extracted verbatim; saved to
[`data/raw/gdpval_44_occupations_verbatim.csv`](data/raw/gdpval_44_occupations_verbatim.csv). Paper HTML+PDF
archived under [`data/raw/gdpval_paper/`](data/raw/gdpval_paper/). (9 sectors × 5, minus one in Retail Trade = 44.)

**Why the mapping is easy at first and hard later — the key structural fact.** GDPval did *not*
invent occupation labels. Per the paper's appendix, it used the **May 2024 OEWS** (which is on the
**2018 SOC**) for the occupation universe and O*NET SOC-6 for tasks. So the 44 titles are already
2018-SOC-native — abbreviated display forms of standard SOC titles. Mapping the *name* to a *2018 SOC
code* is therefore nearly 1:1. The difficulty the pre-registration worries about is real but lives one
step later: the **exposure measures are older vintages**, so the operative crosswalk is
GDPval(2018 SOC) → AIOE(2010 SOC) / Webb(occ1990dd).

**Verification method (no codes asserted from memory).** Each of the 44 titles was matched
programmatically against the **O*NET-SOC 2019 taxonomy** (867 codes; the 2018-SOC-based authoritative
list, used because `bls.gov/soc/2018` was blocked). 39 matched exactly; 3 matched modulo display
abbreviation; 2 were inspected by hand against the taxonomy and the Census 2010→2018 crosswalk.

### Result at GDPval's native vintage (2018 SOC): 43 clean / 1 judgment / 0 fail

- **43 of 44** map cleanly and unambiguously to a single 2018 SOC 6-digit code.
- **1 requires a judgment call.**
- **0 fail to map.**

**The 1 judgment call (native vintage):**
- **Buyers and Purchasing Agents** — has **no single detailed 2018 SOC code**. It is a broad group
  (13-1020) spanning three detailed occupations: **13-1021** (Farm Products), **13-1022** (Wholesale
  and Retail Buyers, Except Farm Products), **13-1023** (Purchasing Agents). GDPval reports it as one
  line ($39.79B). Any exposure measure scores the three detailed codes separately, so the analyst must
  decide how to combine them (e.g. employment-weighted mean). *Not resolved here, per instructions.*

### Result at the operative vintage (crosswalk to AIOE's 2010 SOC): ~4 judgment calls

These 2018-SOC occupations were **created or merged in the 2010→2018 revision** and are therefore
**absent from AIOE** (verified: the four codes below are not in AIOE's file; their 2010 predecessors
are). Each needs a documented reconciliation via the official BLS 2010↔2018 crosswalk:

| GDPval occupation | 2018 SOC | Why it's a judgment call vs a 2010-SOC measure |
|---|---|---|
| **Software Developers** | 15-1252 | 2018 **merge** of 2010 `15-1132` (Applications) + `15-1133` (Systems Software). Must combine two AIOE scores. |
| **Project Management Specialists** | 13-1082 | **New in 2018**; no 2010 detailed code. In 2010 these sat inside `13-1199` "Business Operations Specialists, All Other". Requires assignment/imputation — the closest thing to a genuine miss. |
| **News Analysts, Reporters, and Journalists** | 27-3023 | 2018 **merge** of 2010 `27-3021` (Broadcast News Analysts) + `27-3022` (Reporters and Correspondents). Must combine two AIOE scores. |
| **Administrative Services Managers** | 11-3012 | 2010 `11-3011` **split** into 11-3012 + 11-3013 (Facilities Managers). Near-clean: inherit `11-3011`'s score (many-to-one). |

(One more, **Financial and Investment Analysts** 13-2051, had a minor scope change — 2010 "Financial
Analysts" shed `13-2054` Financial Risk Specialists — but the code is stable and maps cleanly.)
*Buyers and Purchasing Agents' three detail codes (13-1021/22/23) are all present in AIOE, so that one
is combinable within AIOE.*

**Ambiguous cases, listed by name (not resolved):** Buyers and Purchasing Agents; Software Developers;
Project Management Specialists; News Analysts, Reporters, and Journalists; (borderline) Administrative
Services Managers, Financial and Investment Analysts.
**Failed mappings:** none.

The full 44-row verified mapping table is in [Appendix A](#appendix-a--full-44-occupation-soc-mapping-verified).

---

## Q2 — WEBB DATA AVAILABILITY

**Question:** does Michael Webb's AI-exposure score exist in a practically usable, **SOC-keyed**,
publicly downloadable form? **Answer: publicly downloadable YES; SOC-keyed NO.**

- **A usable public file exists and was downloaded and verified.** `exposure_by_occ1990dd_lswt2010.csv`
  (21 KB, **341 occupations**, 338 with a non-blank AI score). It carries three separate 1–100 measures:
  `pct_ai`, `pct_software`, `pct_robot`. Saved to
  [`data/raw/webb_exposure_by_occ1990dd_lswt2010.csv`](data/raw/webb_exposure_by_occ1990dd_lswt2010.csv).
- **It is NOT SOC-keyed.** The file's key is **`occ1990dd`** — Dorn (2009) / Deming (2017) harmonized
  1990 Census occupation codes (integers like 4, 7, 8). There is no SOC column. Header verified by
  direct parse: `occ1990dd, occ1990dd_title, lswt2010, pct_software, pct_robot, pct_ai`.
- **Where it lives.** Webb's *own* copy is **email-gated** (michaelwebb.co → Mailchimp signup → a Notion
  data page). An **identical, un-gated** copy is redistributed by the Economic Innovation Group at
  **https://github.com/EIG-Research/AI-unemployment** (its README cites "Webb (2022) … FILE NAME:
  exposure_by_occ1990dd_lswt2010.csv"). The public copy is what was retrieved; contents confirmed
  genuine (columns/keying match the paper).
- **No SOC-keyed public copy was found.** NOT CONFIRMED that Webb posts any O*NET-SOC- or SOC-keyed
  file: his Notion page is a JS redirect the agent could not fetch, and no ICPSR, Harvard Dataverse, or
  journal replication package for the measure was located. What tried and failed is logged in
  [`sources/webb-ai/SOURCES.md`](sources/webb-ai/SOURCES.md).
- **Underlying vintage.** Scores were *constructed* on **O*NET v22.0 (= O*NET-SOC 2010)** — paper: "I use
  the replication code provided for Acemoglu and Autor (2011) … for O*NET v22.0"; "O*NET describes 964
  occupations." But Webb *distributes* only the occ1990dd aggregation.

**Practical consequence:** to use Webb in this SOC-keyed study you must build an **occ1990dd → SOC**
crosswalk yourself. Yale's Budget Lab did exactly this ("we crosswalk … to eventually arrive at the SOC
2018 occupational codes," https://budgetlab.yale.edu/research/labor-market-ai-exposure-what-do-we-know),
so there is a precedent — but it is a many-to-many bridge between two *different classification systems*,
not a same-system vintage update, and it has no official BLS backing (see Q3).

---

## Q3 — SOC VINTAGE ALIGNMENT

| Source | Classification / vintage | Level | Coverage | How confirmed |
|---|---|---|---|---|
| **GDPval frame** (the 44) | **2018 SOC** | 6-digit (via May 2024 OEWS) | 44 | Paper appendix: "May 2024 OEWS", O*NET SOC-6 |
| **AIOE** (Felten, Raj & Seamans) | **2010 SOC** (O*NET-SOC 2010) | 6-digit detailed | **774** occupations | Parsed the file: contains 2010-only 15-1132/15-1133/27-3021/27-3022; lacks 2018-only 15-1252/15-1211/27-3023 |
| **Webb** | **Not SOC** — distributed as **occ1990dd** (1990 Census harmonized); *constructed* on O*NET-SOC 2010 | occ1990dd (~341 cats) | 341 (338 scored) | Parsed the file (no SOC column); paper quotes O*NET v22.0 |
| **BLS OES / OEWS employment** | **2018 SOC** (since May 2021) | 6-digit detailed | **~830** occupational categories | BLS `methods_24.pdf` + OEWS FAQ via search (BLS site Akamai-blocked from sandbox) |

**Vintages actually present:** 2018 SOC (GDPval frame, BLS OES) and 2010 SOC (AIOE), plus the
non-SOC **occ1990dd** system (Webb).

**Official BLS crosswalks:**
- **2010 SOC ↔ 2018 SOC — EXISTS (official).** BLS crosswalk page
  https://www.bls.gov/soc/2018/crosswalks.htm and explanatory note
  https://www.bls.gov/soc/2018/soc_note_2010_to_2018_crosswalk.pdf . (Confirmed via BLS-authored search
  results; the XLSX itself was Akamai-blocked here. A reachable equivalent — the Census 2010→2018
  occupation crosswalk with SOC columns — was downloaded to
  [`data/raw/census2018_occ_crosswalk.xlsx`](data/raw/census2018_occ_crosswalk.xlsx) and used for the Q1
  vintage analysis.) **This cleanly bridges AIOE (2010) ↔ BLS OES / GDPval (2018).**
- **occ1990dd ↔ SOC — NO official BLS crosswalk.** `occ1990dd` is an academic harmonization
  (Dorn 2009; Deming 2017), not a BLS product; BLS/Census publish Census-occ↔SOC bridges but not an
  occ1990dd↔SOC one. Reaching SOC from Webb means chaining academic/Census mappings (as Yale did) —
  the largest and least official crosswalk in the pipeline.

---

## Datasets — links & vintages (one place)

| Dataset | Saved as | Link | Vintage / key | Status |
|---|---|---|---|---|
| GDPval paper | `data/raw/gdpval_paper/gdpval_2510.04374v1.{html,pdf}` | https://arxiv.org/abs/2510.04374 | frame = 2018 SOC | ✅ acquired |
| GDPval 44 occupations (extract) | `data/raw/gdpval_44_occupations_verbatim.csv` | (from Table 1) | 2018 SOC titles | ✅ extracted verbatim |
| O*NET-SOC 2019 taxonomy | `data/raw/onetsoc2019.xlsx` | https://www.onetcenter.org/taxonomy/2019/list/?fmt=xlsx | 2018-SOC basis | ✅ acquired (BLS-SOC substitute) |
| Census 2018 occ list + 2010→2018 crosswalk | `data/raw/census2018_occ_crosswalk.xlsx` | https://www2.census.gov/programs-surveys/demo/guidance/industry-occupation/2018-occupation-code-list-and-crosswalk.xlsx | 2010↔2018 | ✅ acquired |
| **AIOE** (occupation/industry/geo) | `data/raw/aioe_felten2021_dataappendix.xlsx` (+ 2 generative-AI files) | https://github.com/AIOE-Data/AIOE | **2010 SOC**, 6-digit, 774 occ | ✅ acquired & verified |
| **Webb** exposure | `data/raw/webb_exposure_by_occ1990dd_lswt2010.csv` | https://github.com/EIG-Research/AI-unemployment (un-gated mirror) | **occ1990dd**, 341 occ | ✅ acquired & verified — **not SOC** |
| BLS OEWS May 2024 national | — | https://www.bls.gov/oes/special-requests/oesm24nat.zip | 2018 SOC, ~830 occ | ⚠️ **NOT acquired** — Akamai 403 from sandbox (see below) |
| BLS 2010→2018 SOC crosswalk (official) | — | https://www.bls.gov/soc/2018/crosswalks.htm | 2010↔2018 | ⚠️ confirmed to exist; not downloaded (Akamai); Census equivalent used |

---

## Attempt log / dead ends (the deliverable too)

1. **GDPval occupation list** — first pull (WebFetch summary) abbreviated the titles; re-pulled the raw
   HTML and extracted all 44 verbatim from Table 1. The paper's appendix "Detail about O*NET Data Source"
   was the key find (SOC-6 vs SOC-4 handling; the 12 O*NET-29.0 splits). ✅
2. **BLS OEWS May 2024 national ZIP** — `curl` (multiple UA/header variants) and WebFetch both got a
   1,325-byte Akamai "Access Denied" (HTTP 403). Environment/bot block, not a bad link; retrievable from a
   normal browser. Not decisive for feasibility (microdata is an analysis-phase input). ❌ from sandbox.
3. **BLS SOC 2018 definitions / crosswalk XLSX** — same Akamai 403. Worked around with the O*NET-SOC 2019
   taxonomy and the Census 2010→2018 crosswalk (both reachable, both primary). ↪️ substituted.
4. **BLS OEWS SOC vintage** — could not fetch the page; confirmed "2018 SOC since May 2021, ~830 categories"
   from BLS-authored search snippets (`methods_24.pdf`, OEWS FAQ). ✅ via search.
5. **AIOE** — found and downloaded from GitHub AIOE-Data/AIOE (repo confirmed to exist). SOC vintage not
   stated in the README; established as 2010 SOC by parsing the code set. Journal PDF paywalled (Wiley 402);
   HTML free. ✅ data acquired.
6. **Webb** — official data page is email-gated (Mailchimp→Notion); the Notion page itself was an
   unfetchable JS redirect. Found an un-gated identical copy in EIG's public repo and verified it. No
   SOC-keyed copy, no ICPSR/Dataverse/journal replication package found. ✅ data acquired, ❌ SOC-keyed copy.
7. **occ1990dd→SOC official crosswalk** — none exists (occ1990dd is academic, not BLS). ❌.

---

## Verdict — is the pre_registration analysis practical as specified?

**Mostly yes, but with one component that is the binding constraint: Webb.** Three of the four data
pillars are ready or trivially so — GDPval's 44 occupations are 2018-SOC-native (43/44 map cleanly, 0
failures), AIOE is a clean, downloadable, 6-digit-SOC file (2010 vintage, 774 occupations), and BLS OES
is standard 2018-SOC data (blocked only by this sandbox's Akamai filter, not by any real unavailability),
with an **official BLS 2010↔2018 crosswalk** that cleanly reconciles AIOE↔OES↔GDPval — so the AIOE arm of
the pre-registered "skew under both measures" rule is fully executable. The blocking issue is **Webb**:
the pre-registration makes Webb load-bearing (the finding is "substantive" *only* if the skew appears
under **both** AIOE **and** Webb, because Webb is the non-O*NET check against a mechanical artifact), yet
Webb is **not published in SOC-keyed form** — only as `occ1990dd`, a different 1990-Census-based
classification with **no official BLS crosswalk to SOC**. This does not make the analysis impossible
(the file is public and usable, and Yale's Budget Lab has demonstrated an occ1990dd→SOC-2018 mapping),
but it converts Webb from "download and merge" into "build and defend a many-to-many, cross-system,
unofficially-bridged crosswalk" — which is exactly the step most likely to (a) consume the bulk of the
Phase-2 timeline and (b) inject enough mapping error to weaken the credibility of any Webb-based skew,
the very robustness the pre-registration relies on. **Recommendation for the decision you're about to
make:** the project is worth proceeding with, but treat the **occ1990dd→SOC crosswalk for Webb** as the
gating task and its error as a first-class limitation; if that bridge proves too lossy to trust, the
pre-registration's own §3 fallback (Eloundou et al., with the explicit caveat that it shares O*NET
structure and thus *weakens* the check) is the specified contingency, and it should be invoked openly
rather than presenting a forced occ1990dd→SOC mapping as clean.

---

## Appendix A — full 44-occupation SOC mapping (verified)

SOC codes verified against the O*NET-SOC 2019 taxonomy (2018-SOC basis). Status is at GDPval's native
2018 vintage; the "2010-xwalk note" column flags what changes when mapping to AIOE (2010 SOC).

| # | Sector | GDPval title (verbatim) | 2018 SOC | Status | 2010-xwalk note |
|---|---|---|---|---|---|
| 1 | Real Estate | Property/RE/Community Association Managers | 11-9141 | clean | — |
| 2 | Real Estate | Counter and Rental Clerks | 41-2021 | clean | — |
| 3 | Real Estate | Real Estate Sales Agents | 41-9022 | clean | — |
| 4 | Real Estate | Real Estate Brokers | 41-9021 | clean | — |
| 5 | Real Estate | Concierges | 39-6012 | clean | — |
| 6 | Manufacturing | First-Line Supervisors of Production and Operating Workers | 51-1011 | clean | — |
| 7 | Manufacturing | **Buyers and Purchasing Agents** | 13-1020 (broad) | **judgment** | aggregate of 13-1021/22/23 (all in AIOE) |
| 8 | Manufacturing | Shipping, Receiving, and Inventory Clerks | 43-5071 | clean | same code; 2010 title "…Traffic Clerks" |
| 9 | Manufacturing | Industrial Engineers | 17-2112 | clean | — |
| 10 | Manufacturing | Mechanical Engineers | 17-2141 | clean | — |
| 11 | Prof/Sci/Tech | **Software Developers** | 15-1252 | clean (2018) | **judgment** vs 2010: = 15-1132 + 15-1133 |
| 12 | Prof/Sci/Tech | Lawyers | 23-1011 | clean | — |
| 13 | Prof/Sci/Tech | Accountants and Auditors | 13-2011 | clean | — |
| 14 | Prof/Sci/Tech | Computer and Information Systems Managers | 11-3021 | clean | — |
| 15 | Prof/Sci/Tech | **Project Management Specialists** | 13-1082 | clean (2018) | **judgment** vs 2010: new; sits in 13-1199 |
| 16 | Government | Compliance Officers | 13-1041 | clean | — |
| 17 | Government | Administrative Services Managers | 11-3012 | clean (2018) | near-clean vs 2010: from 11-3011 |
| 18 | Government | Child, Family, and School Social Workers | 21-1021 | clean | — |
| 19 | Government | First-Line Supervisors of Police and Detectives | 33-1012 | clean | — |
| 20 | Government | Recreation Workers | 39-9032 | clean | — |
| 21 | Health Care | Registered Nurses | 29-1141 | clean | — |
| 22 | Health Care | First-Line Supervisors of Office/Admin Support | 43-1011 | clean | — |
| 23 | Health Care | Medical & Health Services Managers | 11-9111 | clean | — |
| 24 | Health Care | Nurse Practitioners | 29-1171 | clean | — |
| 25 | Health Care | Medical Secretaries & Admin Assistants | 43-6013 | clean | — |
| 26 | Finance | Financial Managers | 11-3031 | clean | — |
| 27 | Finance | Customer Service Representatives | 43-4051 | clean | — |
| 28 | Finance | Securities, Commodities, and Financial Services Sales Agents | 41-3031 | clean | — |
| 29 | Finance | Personal Financial Advisors | 13-2052 | clean | — |
| 30 | Finance | Financial and Investment Analysts | 13-2051 | clean | minor scope shift vs 2010 (13-2054 split off) |
| 31 | Retail | General & Operations Managers | 11-1021 | clean | — |
| 32 | Retail | 1st-Line Supervisors of Retail Sales Workers | 41-1011 | clean | — |
| 33 | Retail | Pharmacists | 29-1051 | clean | — |
| 34 | Retail | Private Detectives & Investigators | 33-9021 | clean | — |
| 35 | Wholesale | Sales Reps, Wholesale & Mfg (Except Tech/Scientific) | 41-4012 | clean | — |
| 36 | Wholesale | Sales Managers | 11-2022 | clean | — |
| 37 | Wholesale | Sales Reps, Wholesale & Mfg (Tech/Scientific) | 41-4011 | clean | — |
| 38 | Wholesale | 1st-Line Supervisors of Non-Retail Sales Workers | 41-1012 | clean | — |
| 39 | Wholesale | Order Clerks | 43-4151 | clean | — |
| 40 | Information | Producers & Directors | 27-2012 | clean | — |
| 41 | Information | Editors | 27-3041 | clean | — |
| 42 | Information | **News Analysts, Reporters, and Journalists** | 27-3023 | clean (2018) | **judgment** vs 2010: = 27-3021 + 27-3022 |
| 43 | Information | Audio & Video Technicians | 27-4011 | clean | — |
| 44 | Information | Film & Video Editors | 27-4032 | clean | — |

*Codes are provisional feasibility output, verified against the O*NET-SOC 2019 taxonomy; the analysis
phase should re-verify against the authoritative BLS 2018 SOC definitions file and OEWS titles once
`bls.gov` is reachable.*
