# Research and publication methodology

## Before implementation

Define the research question, hypothesis, novelty claim, baselines, competing approaches, measurable contributions, and falsifiable success criteria. Conduct a literature comparison before claiming novelty.

## Experimental integrity

For each experiment, preserve:
- Source commit and source hashes.
- Specification revision and configuration.
- Tool and library versions.
- Constraints, parameters, and environment.
- Random seeds and run scripts.
- Raw logs and machine-readable results.
- Failed and incomplete runs.
- Analysis scripts and figure-generation code.

## Results

Separate measured results, simulation results, analytical estimates, and projections. Include uncertainty, sample counts, corner coverage, negative results, limitations, and threats to validity. Do not convert synthetic or simulated speedups into measured silicon claims.

## Paper structure

1. Abstract.
2. Introduction and contributions.
3. Background and related work.
4. Proposed architecture.
5. Formal model, invariants, or algorithms.
6. Verification and implementation methodology.
7. Experimental setup and results.
8. Discussion and limitations.
9. Conclusion and future work.

All figures and tables should be reproducible from scripts and traceable to raw data. Avoid unsupported compliance or novelty statements.
