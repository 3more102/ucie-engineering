# UCIe adapter architecture review workflow

This is a completeness and design-review guide, not a normative checklist. Applicability must be decided from the selected specification revision and project configuration.

## 1. Configuration freeze

Record:
- Standard revision, ECNs, and controlled source.
- Protocol(s), operating mode(s), package topology, and die count.
- Link width, lane map, data rate, and supported configurations.
- Required and optional features.
- Power, reset, clock, manageability, and security scope.

## 2. Layer and interface contracts

Draw the Protocol Layer, Die-to-Die Adapter, and PHY boundary. For FDI and RDI independently, document:
- Signal names, directions, widths, and legal values.
- Clock and reset domains, polarity, assertion/deassertion behavior.
- Handshake and backpressure semantics.
- Packet/flit framing and ordering rules where applicable.
- Error signaling, status, and recovery ownership.
- Parameterization and configuration dependencies.

## 3. Mainband and sideband

For each channel, record purpose, traffic classes, framing, clocking, reset, arbitration, error handling, and ownership. Do not assume fixed frequencies, encoding, or sideband behavior without the selected revision and configuration.

## 4. Reliability architecture

Investigate only applicable, source-backed behavior:
- Error-detection algorithm and protected data scope.
- Error reporting and classification.
- Retry/replay trigger and cancellation conditions.
- Replay buffer ownership, depth, pointers, and wrap behavior.
- Sequence tracking and duplicate/loss prevention.
- Recovery state transitions, timeout conditions, and exit criteria.
- Fault injection points and expected observable outcomes.

Define measurable invariants for no silent corruption, no duplicate delivery, ordering, bounded storage, and eventual recovery only where the protocol contract supports them.

## 5. Flow control

Document credit unit, initialization, update events, accounting, saturation, backpressure, and interactions with buffering. Derive all numeric limits from the exact standard or project contract.

## 6. Reset, clocks, and power

Create a domain table covering clock source, frequency range if specified, reset polarity, asynchronous/synchronous behavior, reset sequencing, clock gating, power transitions, and CDC/RDC crossings. Define recovery behavior after interrupted traffic.

## 7. Review outputs

Produce:
1. Architecture block diagram.
2. Interface contract matrix.
3. Requirement-to-block allocation.
4. Buffer/credit accounting model.
5. State-machine and recovery diagrams.
6. Open-question register.
7. Risk register and verification entry criteria.

Every design decision must link to a source requirement or be labeled as a project decision/assumption.
