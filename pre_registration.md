# Pre-Registration: Does GDPval's Sampling Frame Select High-Exposure Occupations?

**Written before any data was acquired or examined.** The point of writing it first is that the interpretation of each possible outcome is fixed in advance, so the analysis cannot be steered toward the result that makes the better story.

**Date:** Original pre-registration 2026-07-08; the §3 correction and the three-tier rescope were entered 2026-07-09, after the feasibility check and before any exposure data was analyzed. The git history preserves the pre-correction text.

---

## 1. The question

GDPval samples occupations according to a specific rule: sectors contributing more than 5% of US GDP by value added (Q2 2024), yielding nine; then, within each sector, the five highest-wage occupations that are "predominantly digital," defined as having at least 60% of their O\*NET component tasks classified as digital. Government is among the nine sectors. Retail Trade contributes four occupations rather than five, so the total is 44.

That rule is documented by OpenAI in appendix A.7 of the GDPval paper, where the wage-weighted selection procedure and the digital-task filter are described as deliberate design choices. I am not claiming to have discovered the sampling rule. The rule was chosen for measurement reasons, and the untested question is whether it carries an economic consequence: do GDPval's 44 occupations sit systematically higher on AI-exposure measures than the US workforce does, once the workforce is weighted by how workers are actually distributed across occupations? OpenAI weights by wages and compensation, not by employment, and never compares the resulting occupation set to an exposure distribution or an employment-weighted baseline. That comparison is what this analysis performs.

If the answer is yes, the occupations GDPval scores are not representative of where American labor sits on AI exposure, and reading its headline figure as an economy-wide signal is unwarranted.

## 2. What I am measuring

The analysis proceeds in three tiers, ordered by the degree of confidence each warrants. The first tier is the spine and incorporates no exposure measure; the second and third introduce exposure comparisons that inherit the caveats §3 establishes. I am fixing this ordering now, so that the load-bearing claim is the one least vulnerable to the crosswalk problems the feasibility check identified.

**Unit throughout:** occupation, keyed to 2018 SOC at the 6-digit level. GDPval's frame is already 2018-SOC-native, making this the natural key.

**Tier 1, the spine: employment and wage coverage of GDPval's frame.** This is the primary analysis and the piece's load-bearing evidence. The treatment set is GDPval's 44 occupations; the data are BLS OEWS May 2024 national employment and wage estimates. The outcome is what share of US employment the 44 occupations cover, and where they sit in the employment-weighted wage distribution. No exposure measure enters, so no artifact problem enters; the only crosswalk this tier can require is the official BLS 2010↔2018 bridge, and only if a source forces it. On mapping grounds this tier is close to unimpeachable, which is why it carries the argument. Coverage is reported against two baselines, because they answer different questions and I do not want to choose after seeing the result. The economy-wide baseline is all US occupations, with the universe declared in §6, and it is the comparison relevant to reading GDPval as an economy-wide signal. The within-sector baseline restricts to occupations in GDPval's nine sectors, and it is the fairer test of the occupation-selection rule itself, since it holds the sector gate constant.

**Tier 2, the extension: AIOE exposure, caveated.** AIOE is keyed to 2010 SOC across 774 occupations, bridged to 2018 SOC with the official BLS crosswalk. I will compare the AIOE distribution of GDPval's 44 against the same two baselines and report a skew if one appears. The caveat belongs up front rather than in a footnote: AIOE and GDPval's digital filter share O\*NET structure, so a skew here cannot be attributed to substantive exposure rather than to shared construction on this evidence alone. Section 4 specifies what I will and will not conclude from each outcome.

**Tier 3, the conditional: Webb, which may end in a null.** Webb ships as occ1990dd rather than SOC, with no official bridge to the classification the rest of this analysis uses. I will attempt the occ1990dd→SOC crosswalk; Yale's Budget Lab has done it, so it is possible. I commit in advance to the following: if the bridge proves too lossy to trust, I will report that as the finding rather than present a forced mapping as clean. That the field's most-cited non-abilities exposure measure cannot be cleanly joined to the occupational classification the rest of the literature runs on is itself a result worth publishing.

## 3. The measures, and what they can and cannot separate

- **AIOE** (Felten, Raj & Seamans). Built on O\*NET ability ratings, mapped from a catalog of AI applications.
- **Webb.** Built on textual overlap between O\*NET job-task descriptions and the text of AI patents.

**Correction, entered after the feasibility check and before any exposure data was analyzed.** An earlier version of this section claimed that Webb "does not share that plumbing" with GDPval's O\*NET digital filter, treating Webb as an independent, non-O\*NET check capable of separating a substantive skew from a mechanical one. That claim was false; the feasibility work is what caught it. Webb's scores are constructed from O\*NET task text; AIOE's are constructed from O\*NET ability ratings. Both take their occupational task universe from O\*NET, the same source on which GDPval's ≥60%-digital filter is built. The two measures differ in signal source, not in task universe. Webb reads the overlap between task descriptions and patent text where AIOE reads ability ratings, and that distinction is real; it does not buy independence from the O\*NET structure that the artifact worry is about.

Webb is therefore a weaker check than this design first assumed. A skew appearing under both AIOE and Webb is suggestive, but it is not clean evidence that the skew is substantive rather than a property of shared O\*NET construction, because both measures inherit that construction. I am leaving the mistake visible rather than overwriting it silently: the reason to write a pre-registration first is to keep the reasoning auditable, and that must include the places where it required correction.

Eloundou et al. carries the same limitation and partially shares O\*NET task structure, so it cannot serve as the independent check either. None of the exposure measures I can actually obtain is constructed independently of O\*NET. That constraint now shapes the tiered structure in §2 and the decision rule in §4, rather than being assumed away.

## 4. The decision rule, committed in advance

The primary finding does not depend on any exposure measure. Tier 1 in §2 reports how much of US employment GDPval's 44 occupations cover and where they sit in the employment-weighted wage distribution; that result stands on the occupation-to-SOC mapping alone, and it is what the piece leads with. The exposure comparison is an extension, and its decision rule is narrower than the earlier draft claimed.

The earlier draft made the rule "the finding counts as substantive only if the skew appears under both AIOE and Webb." That rule is withdrawn. It assumed Webb was independent of O\*NET, and §3 explains why it is not, so agreement between the two measures can no longer certify a skew as substantive. What remains is a rule about AIOE alone, stated with the artifact ambiguity attached to it rather than resolved by a second measure.

| Outcome (Tier 2, AIOE) | What I will conclude and publish |
|---|---|
| Skew present under AIOE | GDPval's 44 occupations sit higher on AIOE than the employment-weighted workforce. I will report the skew, and I will not claim it is substantive, because AIOE and GDPval's digital filter share O\*NET construction and this evidence cannot separate substantive exposure from that shared structure. |
| Skew absent under AIOE | GDPval's frame does not sit higher on AIOE than the employment-weighted workforce. This is the strong outcome, not the weak one. AIOE shares O\*NET construction with GDPval's digital filter, which makes it the measure mechanically disposed to score these occupations high, and therefore the measure most likely to return a false positive. A skew that fails to appear even under the measure most biased toward producing one is close to dispositive against the exposure-axis critique, and I will report it as such. |
| Under either outcome | The artifact ambiguity persists for a positive result, and only for a positive result. No Tier 2 skew can be attributed to AI's economic reach rather than to shared O\*NET inputs; a Tier 2 null faces no such ambiguity, and Tier 1 remains the load-bearing evidence regardless of which way AIOE falls. |

This produces an asymmetry I want stated plainly rather than left as an aside. A skew present under AIOE is uninterpretable: the shared O\*NET construction could produce it with or without any real exposure difference. A skew absent under AIOE is powerful, because it is a null from the measure most predisposed to find one. The design is therefore better powered against my own hypothesis than for it. The outcome that would flatter the critique is the one I cannot cleanly claim; the outcome that would refute it is the one I could state without hedging. I am keeping that design rather than quietly rebuilding it into one that can only confirm me.

A null result is publishable, and so is a caveated one. I am recording this explicitly because the temptation, following the crosswalk work, will be to read a Tier 2 skew as vindication. The structure above is here to prevent that reading.

## 5. What I am not claiming

- **No claim to have discovered GDPval's sampling rule.** OpenAI documents it in appendix A.7 and presents it as a feature. What remains untested is what the rule produces relative to the employment-weighted occupational structure, and that is the only thing this analysis claims to show.
- **No canonical exposure target.** Exposure measures operationalize distinct constructs, correlate imperfectly with one another, and predict labor outcomes poorly in isolation (Frank et al. 2025). Platform-derived exposure measures carry their own selection bias (Yin et al. 2026). The deliverable is therefore a **sensitivity analysis across measures**, never a single corrected number, and never a claim that some reweighted frame is the correct one.
- **No causal claim about AI's labor-market effect.** This analysis concerns what a benchmark's frame contains, not what AI will do to employment.
- **No claim about RLI unless the mapping is clean.** RLI is organized by Upwork category, not SOC. I will attempt a crosswalk. Where categories prove incommensurable with occupation-based exposure measures, I will report that incommensurability as the finding rather than forcing a mapping. That is a real result: the frame cannot be evaluated against the standard exposure measures at all.

## 6. Analytic choices fixed in advance

- Exposure distributions are compared via the full distribution (overlaid densities) and a rank-based test, not a difference in means alone, since exposure scores are not obviously interval-scaled across measures.
- Employment weighting uses BLS OES employment counts by SOC.
- **The occupation universe is declared in advance, because three defensible universes exist and they are not interchangeable.** OpenAI filtered OEWS May 2024 down to 761 detailed occupations after dropping "All Other" residual categories, from a starting set of roughly 831. Parshall & Lopez-Luzuriaga (2026) work over 923 O\*NET occupations. "All Other" categories are residual buckets that can carry substantial employment; including or excluding them changes the baseline distribution against which GDPval's 44 occupations are compared.

  **Committed choice:** the primary baseline uses the full OEWS detailed-occupation set *including* "All Other" categories, because the economy-wide-signal critique concerns the actual distribution of employment, and excluding residual buckets would silently remove workers from the denominator. A secondary baseline excluding "All Other" will be reported for comparability with OpenAI's own filtering. If the two baselines disagree about whether a skew exists, that disagreement is itself the finding and will be reported as such, not resolved by preference.
- **SOC level is fixed before mapping.** Exposure measures are keyed at the detailed (SOC-6) level. If GDPval's appendix supplies only broad (SOC-4) groups, aggregating exposure scores up to SOC-4 is a modeling choice with its own defensibility problem; the analysis will either map to SOC-6 directly or disclose the aggregation and its consequences. The level will not be chosen after seeing which one produces a skew.
- **Every occupation-to-SOC judgment call will be logged in a mapping file, with ambiguous cases flagged.** The crosswalk hit rate (how many of the 44 map cleanly, how many required judgment) will be reported as a limitation, not buried.
- **Buyers and Purchasing Agents is the one occupation with no single detailed code.** It is a 2018 SOC broad group (13-1020); I will aggregate it across its three detailed codes (13-1021, 13-1022, 13-1023) using employment weights, and I will log that aggregation as a judgment call in the mapping file.
- Where SOC vintages differ across sources (2010 vs. 2018), the crosswalk between vintages is itself a source of error and will be disclosed as such.
- No measure will be dropped after seeing its result. If AIOE and Webb disagree, both get reported.

## 7. Known limitations, stated before the fact

- GDPval's ≥60%-digital filter and AIOE share O\*NET inputs; this shared construction motivates §3 and §4.
- Because AIOE shares O\*NET construction with GDPval's filter, the Tier 2 design is better powered against my own hypothesis than for it: a null result under AIOE is the clean, near-dispositive finding, while a detected skew is the caveated one. That asymmetry is a property of the design I am retaining rather than a flaw I am working around; §4 states it in full.
- Exposure measures disagree with one another, and the analysis inherits their construct-level problems.
- Occupation-level exposure indicates nothing about which tasks *within* an occupation GDPval sampled; a frame could select high-exposure occupations while sampling their least-exposed tasks. This analysis cannot observe that.
- The comparison is descriptive. It shows what the frame contains; it does not show what a better frame would be.

## 8. Related work, and how this differs

**Parshall, D., & Lopez-Luzuriaga, A. (2026). "Measuring AI's Economic Reach: A Multi-Dimensional Task Taxonomy." GWU Center for Economic Research Working Paper 2026-005, March 2026.** This is the nearest adjacent work. The authors propose a three-axis taxonomy (Cognitive complexity, Deployment difficulty, Regulatory restrictions), classify the full O\*NET task universe (23,850 DWA-task pairs across 923 occupations) by multi-model LLM consensus, and employment-weight the result by labor time to characterize where in the economy AI-reachable tasks sit.

Confirmed by text search of a browser-decoded PDF (not read in full by hand): GDPval appears once, as a passing score citation (GPT-5.4, 83%, March 2026); RLI does not appear; AIOE and Webb are not used as instruments. Felten, Raj & Seamans is cited as a comparison whose abilities-based approach maps onto their C-axis while ignoring the D and R axes; Eloundou is used to validate CDR. The paper thus proposes and validates a new exposure construct rather than applying established ones, and it never treats a benchmark's occupation list as a unit of analysis.

**The differentiation, stated once so a reviewer need not ask:** this analysis uses AIOE (Felten, Raj & Seamans) and Webb because they are the established, externally-validated *occupation-level* exposure measures the field benchmarks against, and because the unit of analysis here must be the occupation, the occupation being the unit on which GDPval sampled. Parshall and Lopez-Luzuriaga instead propose a new *task-level* taxonomy and employment-weight the full O\*NET universe to characterize economy-wide AI reach. The question here is narrower and distinct: whether GDPval's and RLI's sampling frames pre-select high-exposure occupations relative to the labor-weighted distribution. That is a representativeness test of an existing instrument, not a proposal for a superior exposure metric, and their paper does not perform it.

**Also reviewed; none preempting:** Epoch AI, "What do 'economic value' benchmarks tell us?" (13 Feb 2026), which raises the representativeness question qualitatively (noting "far more remote labor than represented in RLI, and many more sources of GDP than captured by GDPval") without quantifying it against any exposure measure or employment baseline; Tolan et al. (2020), the nearest methodological template, which maps O\*NET tasks to cognitive abilities across 328 AI benchmarks but not to these benchmarks' sampling frames; Yale Budget Lab, "Labor Market AI Exposure: What Do We Know?" (19 Feb 2026), which compares exposure metrics without reference to GDPval.

## 9. A note on benchmark scores

Benchmark scores on GDPval shift rapidly. The reported top score was 74% (win-or-tie, GPT-5.2 Pro) in Epoch's February 2026 comparison, rising to 83% (GPT-5.4) as cited in March 2026. Every score quoted in this write-up carries a model, a date, and a source. No score is stated as a standing fact.

## 10. Beyond critique: a reporting standard, not a better frame

Section 5 commits me to no canonical exposure target, and I intend to honor that commitment rather than introduce a correction through the back door. Exposure measures disagree with one another; in isolation, they predict labor outcomes poorly; and the platform-derived measures carry their own selection bias on top of that. To propose a reweighted or "corrected" sampling frame would be to assert exactly the canonical target I have just argued does not exist. The constructive contribution here is therefore not a better frame. It is a disclosure standard.

The gap is straightforward to state. GDPval does not report the employment coverage of its occupation set; a reader cannot determine from the paper what share of the US labor force its 44 occupations represent. RLI does not report it either. I am not aware of an economic-value benchmark that does. The headline numbers these benchmarks produce are read as statements about work in general, while the frame over which they are computed is left undescribed.

The proposal is that economic-value benchmarks should publish the employment share of their task frame and its position in the employment-weighted wage distribution, so that a reader can see what fraction of the labor force the headline number actually speaks for. This costs benchmark authors close to nothing; the employment and wage data are public, and the mapping is the same one this project constructs. It is the discipline survey researchers already take for granted when they report sampling weights and design effects alongside an estimate, rather than reporting the estimate alone.

Tier 1 is the demonstration. I am not asking benchmark authors to do something I have only asserted is cheap; the coverage analysis anchoring this piece is that same computation, run on GDPval, using nothing but public data and the official crosswalk.

Be clear about the limits of the claim. This does not suggest GDPval's frame is wrong, or that some alternative set of occupations would be preferable. It suggests that the frame's coverage should be visible, so that a downstream reader can price it into whatever they infer from the score. A scoped instrument reported with its scope is honest work; the same instrument, read as an economy-wide signal because its scope was never stated, is not.

The move is the one I made with DICES: audit an annotation scheme's reliability before trusting the scores built on top of it, and make the instrument's properties visible rather than rebuilding the instrument itself.
