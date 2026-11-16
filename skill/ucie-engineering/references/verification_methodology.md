# Verification methodology

## Requirement-driven verification

Each atomic requirement should have:
- Requirement ID and exact source reference.
- Configuration and applicability.
- Design element and observable behavior.
- One or more tests/assertions.
- Expected result and pass/fail criteria.
- Evidence location and status.

Do not mark a requirement PASS when evidence is absent or not reviewed.

## UVM environment

Choose components based on interface complexity:
- Transaction item with only contract-defined fields.
- Sequencer and driver for stimulus.
- Monitor for observed protocol behavior.
- Scoreboard/reference model for ordering, data integrity, and accounting.
- Coverage collector for requirement-driven coverage.
- Virtual sequences for cross-agent scenarios where needed.

Keep the reference model independent enough to detect design errors. Document any shared assumptions or reused code.

## Test classes

- Directed nominal tests.
- Boundary and parameter tests derived from specified limits.
- Backpressure and sustained-throughput tests.
- Reset and power-transition tests.
- Negative/error injection tests.
- Retry/replay and recovery tests where applicable.
- Randomized stress and long-duration tests.
- Regression and reproducibility tests.

## SVA candidates

Consider properties for:
- Valid/data stability while stalled.
- No FIFO overflow or underflow.
- Credit conservation and legal credit updates.
- Ordering and no duplicate/lost delivery.
- Legal FSM transitions.
- Reset-state and reset-release behavior.
- Mutual exclusion and one-hot conditions.
- Bounded response only when a bound is specified.

Use the correct clocking event, disable condition, sampled signals, and implication semantics from the design contract. Generated skeletons require review.

## Coverage

Keep these distinct:
- Code coverage.
- Functional coverage.
- Assertion coverage.
- Fault-injection/mutation coverage.
- Requirement/specification coverage.

Cross only meaningful dimensions. Record exclusions and justify them.

## Regression record

Capture source commit, specification baseline, simulator/version, compile options, test list, seed, timeout, coverage database, logs, and exit status. Preserve failing seeds and failure waveforms. A passing regression is evidence for the tested scope, not automatic standards certification.
