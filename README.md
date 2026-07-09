# benchmark-exposure-skew

Does GDPval's sampling frame select high-exposure occupations?

GDPval evaluates AI models on tasks drawn from 44 occupations, chosen by a documented rule: sectors
above a 5% share of US GDP by value added, then the highest-wage predominantly-digital occupations
within them. The rule was chosen for measurement reasons. This project asks what it produces: how
much of US employment those 44 occupations cover, and where they sit in the employment-weighted wage
distribution. A second question, harder to answer cleanly, is whether they sit higher on AI-exposure
measures than the workforce does.

## Status

Pre-registration only. No exposure data has been analyzed.

[pre_registration.md](pre_registration.md) fixes the claim, the measures, the decision rule, and the
interpretation of every possible outcome, including the null and the measurement-artifact result. It
is committed before the analysis so the reasoning stays auditable, and so the analysis cannot be
steered toward whichever result makes the better story.

An earlier draft treated Webb's exposure measure as an independent, non-O\*NET check on AIOE. Webb's
scores are built from O\*NET task text, so that was false, and Section 3 records the correction
instead of overwriting it. The error was caught by a feasibility check on data availability, before
any exposure data was examined.

## What this is not

This project does not claim to have discovered GDPval's sampling rule; OpenAI documents it in their
own appendix and presents it as a design choice. Nor does it propose a corrected sampling frame,
since exposure measures disagree with one another and none is a canonical target. The analysis is
descriptive: it shows what a frame contains, and says nothing causal about what AI will do to jobs.

## Data

Third-party data is not redistributed here. The manifests under `data/raw/` and `sources/` record
every file, its origin, its classification vintage, and what could not be obtained, so anything used
can be re-fetched from the primary source.
