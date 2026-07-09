# Pre-Registration: Does GDPval's Sampling Frame Select High-Exposure Occupations?

**Written before any data was acquired or examined.** The point of writing it first is that the interpretation of each possible outcome is fixed in advance, so the analysis cannot be steered toward the result that makes the better story.

**Date:** 2026-07-08

---

## 1. The question

GDPval samples occupations by a specific rule: sectors contributing over 5% of US GDP by value added (Q2 2024), yielding nine; then, within each sector, the five highest-wage occupations that are "predominantly digital," meaning at least 60% of their O*NET component tasks are classified as digital. Government is among the nine sectors. Retail Trade contributes four occupations rather than five, so the total is 44.

That rule is documented by OpenAI themselves, in appendix A.7 of the GDPval paper, where the wage-weighted selection and the digital-task filter are described as deliberate design choices. I am not claiming to have discovered the sampling rule. The rule was chosen for measurement reasons, and the untested question is whether it has an economic consequence: **do GDPval's 44 occupations sit systematically higher on AI-exposure measures than the US workforce does, once the workforce is weighted by how people are actually distributed across occupations?** OpenAI weights by wages and compensation, not by employment, and never compares the resulting occupation set to an exposure distribution or an employment-weighted baseline. That comparison is what this analysis performs.

If yes, the occupations GDPval scores are not representative of where American labor sits on AI exposure, and reading its headline number as an economy-wide signal is unwarranted.

## 2. What I am measuring

- **Unit:** occupation, keyed to SOC code.
- **Treatment set:** GDPval's 44 sampled occupations.
- **Baseline:** all US occupations (universe declared in §6), weighted by BLS OES employment counts. I will report two baselines, because they answer different questions and I do not want to choose after seeing the result:
  - *Economy-wide baseline*: all occupations. This is the comparison relevant to reading GDPval as an economy-wide signal.
  - *Within-sector baseline*: occupations restricted to GDPval's nine sectors. This is the fairer test of the occupation-selection rule itself, holding the sector gate constant.
- **Outcome:** the distribution of exposure scores in the treatment set versus each baseline.

## 3. The measures, and why two of them

- **AIOE** (Felten, Raj & Seamans). Built on O*NET abilities.
- **Webb.** Built on overlap between job-task text and patent text.

These are not interchangeable, and the difference is the entire reason the second one is here. **AIOE and GDPval's occupation filter both derive from O*NET's task and ability structure.** An exposure skew visible only under AIOE could therefore be mechanical: a filter that selects occupations by digital O*NET tasks would be expected to select occupations that an O*NET-ability-based exposure measure scores highly, without that telling us anything about AI's actual economic reach. Webb's patent-overlap construction does not share that plumbing, so it functions as a check on whether the skew is substantive or an artifact of shared inputs.

Eloundou et al. is an optional third measure. It partially shares O*NET task structure, so if it substitutes for Webb (because Webb's data proves impractical), the robustness check is **weakened**, and I will say so explicitly in the write-up rather than presenting it as equivalent.

## 4. The decision rule, committed in advance

**The finding counts as substantive only if the skew appears under both AIOE and Webb.**

I commit now to the following interpretations:

| Outcome | What I will conclude and publish |
|---|---|
| Skew under **both** AIOE and Webb | The sampling frame selects high-exposure occupations, and the result is not an artifact of shared O*NET structure. GDPval's score is partly a property of its frame. |
| Skew under **AIOE only** | The apparent skew is plausibly mechanical, produced by the shared O*NET task-and-ability structure between GDPval's digital filter and AIOE's construction. This is a finding about measurement, not about AI's economic reach, and I will report it as such. |
| Skew under **Webb only** | Unexpected. I will not have a clean story; I will report it, investigate whether it reflects Webb's high-skill directionality (Webb finds AI is directed at high-skilled tasks, and GDPval selects high-wage occupations), and decline to make a strong claim. |
| **No skew** under either | GDPval's frame does not select high-exposure occupations relative to the workforce. The selection-bias critique, as I formulated it, is wrong on this axis, and I will publish that. |

A null result is publishable. So is the mechanical-artifact result. I am writing this down because the temptation, after two days of crosswalk work, will be to find something.

## 5. What I am not claiming

- **No claim to have discovered GDPval's sampling rule.** OpenAI documents it in appendix A.7 and presents it as a feature. What is untested is what the rule produces relative to the employment-weighted occupational structure, and that is the only thing this analysis claims to show.
- **No canonical exposure target.** Exposure measures operationalize different constructs, correlate imperfectly, and predict labor outcomes poorly in isolation (Frank et al. 2025). Platform-derived exposure measures carry their own selection bias (Yin et al. 2026). So the deliverable is a **sensitivity analysis across measures**, never a single corrected number and never a claim that some reweighted frame is the right one.
- **No causal claim about AI's labor-market effect.** This is a statement about what a benchmark's frame contains, not about what AI will do to jobs.
- **No claim about RLI unless the mapping is clean.** RLI is organized by Upwork category, not SOC. I will attempt a crosswalk. If the categories are genuinely incommensurable with occupation-based exposure, I will report that incommensurability as the finding rather than forcing a mapping. That is a real result: the frame cannot be evaluated against the standard exposure measures at all.

## 6. Analytic choices fixed in advance

- Exposure distributions compared via the full distribution (overlaid densities) and a rank-based test, not a difference in means alone, since exposure scores are not obviously interval-scaled across measures.
- Employment weighting uses BLS OES employment counts by SOC.
- **The occupation universe is declared in advance, because three defensible universes exist and they are not interchangeable.** OpenAI filtered OEWS May 2024 down to 761 detailed occupations after dropping "All Other" residual categories, from a starting set of roughly 831. Parshall & Lopez-Luzuriaga (2026) work over 923 O*NET occupations. "All Other" categories are residual buckets that can carry substantial employment, so including or excluding them changes the baseline distribution against which GDPval's 44 are compared.

  **Committed choice:** the primary baseline uses the full OEWS detailed-occupation set *including* "All Other" categories, because the economy-wide-signal critique concerns the actual distribution of employment, and excluding residual buckets would silently remove workers from the denominator. A secondary baseline excluding "All Other" will be reported for comparability with OpenAI's own filtering. If the two baselines disagree about whether a skew exists, that disagreement is itself the finding and will be reported as such rather than resolved by preference.
- **SOC level is fixed before mapping.** Exposure measures are keyed at the detailed (SOC-6) level. If GDPval's appendix supplies only broad (SOC-4) groups, aggregating exposure scores up to SOC-4 is a modeling choice with its own defensibility problem, and the analysis will either map to SOC-6 directly or disclose the aggregation and its consequences. The level will not be chosen after seeing which one produces a skew.
- **Every occupation-to-SOC judgment call will be logged in a mapping file, with the ambiguous cases flagged.** The crosswalk hit rate (how many of the 44 map cleanly, how many required judgment) will be reported as a limitation, not buried.
- If SOC vintages differ across sources (2010 vs 2018), the crosswalk between vintages is itself a source of error and will be disclosed.
- No measure will be dropped after seeing its result. If AIOE and Webb disagree, both get reported.

## 7. Known limitations, stated before the fact

- GDPval's ≥60%-digital filter and AIOE share O*NET inputs (this motivates §3 and §4).
- Exposure measures disagree with each other; the analysis inherits their construct problems.
- Occupation-level exposure says nothing about which *tasks within* an occupation GDPval sampled, so a frame could select high-exposure occupations while sampling their least-exposed tasks. This analysis cannot see that.
- The comparison is descriptive. It shows what the frame contains; it does not show what a better frame would be.

## 8. Related work, and how this differs

**Parshall, D., & Lopez-Luzuriaga, A. (2026). "Measuring AI's Economic Reach: A Multi-Dimensional Task Taxonomy." GWU Center for Economic Research Working Paper 2026-005, March 2026.** The nearest adjacent work. They propose a new three-axis taxonomy (Cognitive complexity, Deployment difficulty, Regulatory restrictions), classify the full O*NET task universe (23,850 DWA-task pairs across 923 occupations) by multi-model LLM consensus, and employment-weight the result by labor time to characterize where in the economy AI-reachable tasks sit.

Confirmed by text search of a browser-decoded PDF (not read in full by hand): GDPval appears once, as a passing score citation (GPT-5.4, 83%, March 2026); RLI does not appear; AIOE and Webb are not used as instruments. Felten, Raj & Seamans is cited as a comparison whose abilities-based approach maps onto their C-axis while ignoring their D and R axes; Eloundou is used to validate CDR. So the paper proposes and validates a new exposure construct rather than applying established ones, and it never treats a benchmark's occupation list as a unit of analysis.

**The differentiation, stated once so a reviewer never has to ask:** this analysis uses AIOE (Felten, Raj & Seamans) and Webb because they are the established, externally-validated *occupation-level* exposure measures the field benchmarks against, and because the unit of analysis here must be the occupation, since the occupation is the unit GDPval sampled on. Parshall and Lopez-Luzuriaga instead propose a new *task-level* taxonomy and employment-weight the full O*NET universe to describe economy-wide AI reach. The question here is narrower and different: whether GDPval's and RLI's sampling frames pre-select high-exposure occupations relative to the labor-weighted distribution. That is a representativeness test of an existing instrument, not a proposal for a better exposure metric, and their paper does not perform it.

**Also reviewed, none preempting:** Epoch AI, "What do 'economic value' benchmarks tell us?" (13 Feb 2026), which raises the representativeness question qualitatively ("far more remote labor than represented in RLI, and many more sources of GDP than captured by GDPval") without quantifying it against any exposure measure or employment baseline; Tolan et al. (2020), the nearest methodological template, which maps O*NET tasks to cognitive abilities to 328 AI benchmarks but not to these benchmarks' sampling frames; Yale Budget Lab, "Labor Market AI Exposure: What Do We Know?" (19 Feb 2026), which compares exposure metrics without reference to GDPval.

## 9. A note on benchmark scores

Scores on these benchmarks move fast. GDPval's reported top score was 74% (win-or-tie, GPT-5.2 Pro) in Epoch's February 2026 comparison and 83% (GPT-5.4) as cited in March 2026. Every score quoted in the write-up carries a model, a date, and a source. No score is stated as a standing fact.
