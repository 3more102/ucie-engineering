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

### Contract-driven ready/valid scaffolding

A generic source/sink ready-valid agent may be generated only from an explicit contract that supplies the interface name, agent name, clock, distinct drive/sample edges, role, valid/ready signal names, and payload field names/widths. The source role drives valid and payload and observes ready; the sink role drives ready and observes valid/payload. The monitor records a transfer only when valid and ready are sampled high together. The generator also emits an SVA include fragment for valid persistence and per-field payload stability on the next configured sample edge after a stall. The sink driver should explicitly drive ready low when no sequence item is available; the generated template polls `try_next_item` on the drive edge to avoid retaining stale backpressure control. The generated templates do not implement reset, timeout, packet framing, CRC, retry/replay, credits, or UCIe-specific behavior. They are scaffolding, not normative FDI/RDI models; verify them against the controlled interface specification. Repository CI uses Slang for front-end syntax/elaboration checks, but the package must still be compiled against the target UVM library and simulated in the target UVM environment.

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
