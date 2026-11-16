# UCIe Interface Contract Intake — FDI First

## Purpose

Use this intake before generating a project-specific UVM agent. It separates facts extracted from the controlled specification from project decisions and testbench scheduling choices. This document is an intake template, not a UCIe requirements summary.

## Baseline and scope gate

Record the exact UCIe specification title, revision, publication date, applicable ECNs, controlled source identifier, and source hash if available. The project profile currently targets UCIe 3.0 and the Die-to-Die Adapter, with FDI as the first interface study target and the 2D package as the baseline. Confirm that baseline against the team's controlled copy before treating it as frozen.

Do not import signal definitions, timing, fields, reset behavior, or requirements from another UCIe revision.

## Contract records to complete

Create separate records for each interface direction and each independent clock/reset domain. Do not assume FDI TX and FDI RX share identical signals or behavior. Record RDI separately even if it is outside the first implementation phase.

| Field | Required entry |
|---|---|
| Contract ID | Unique project ID, e.g. FDI-TX-CONTRACT-001 |
| Layer boundary | Exact blocks on each side of the interface |
| Direction | Which block produces and which consumes each signal |
| Signal name | Exact name from controlled interface definition |
| Width | Exact width and any parameter dependency |
| Legal values | Enumerations, reserved values, and constraints |
| Clock | Exact clock signal/domain and sampling edge |
| Reset | Signal, polarity, synchronous/asynchronous behavior, assertion/deassertion rules |
| Handshake | Exact valid/ready or other control semantics; acceptance condition |
| Payload | Field map, widths, packing/order, and stability rules |
| Backpressure | Producer behavior while consumer is not ready |
| Reset during transfer | Abort/retry/retain behavior, only if source-defined or explicitly decided |
| Error/status | Signals, ownership, and response behavior |
| Source reference | Revision, section/clause, table/figure, page, and controlled file/hash |
| Evidence status | VERIFIED / PROJECT DECISION / ASSUMPTION / OPEN / NOT VERIFIED |

## Generator mapping

The current generic generator supports only a single-clock ready/valid contract:

- `interface_name`, `agent_name`: legal SystemVerilog identifiers.
- `clock`: the supplied interface clock identifier.
- `drive_edge`: testbench scheduling edge. This is a simulation scheduling choice, not automatically a normative protocol requirement.
- `sample_edge`: the edge on which the monitor samples the contract.
- `role = source`: the UVM driver drives valid and payload and observes ready.
- `role = sink`: the UVM driver drives ready and observes valid/payload.
- `valid`, `ready`: exact signal identifiers from the verified contract.
- `payload`: exact payload field names, widths, and signedness.
- `source_ref`: exact controlled source location.

The generator requires drive_edge and sample_edge to differ. Choose the drive edge only after reviewing the target simulator/testbench timing convention; do not reinterpret it as a UCIe-specified edge.

## JSON intake skeleton

This is intentionally incomplete and must not be sent to the generator until every TBD is replaced by verified project values.

~~~json
{
  "schema_version": "1.0",
  "interface_name": "TBD_INTERFACE",
  "agent_name": "TBD_AGENT",
  "clock": "TBD_CLOCK",
  "drive_edge": "TBD_TESTBENCH_DRIVE_EDGE",
  "sample_edge": "TBD_PROTOCOL_SAMPLE_EDGE",
  "role": "TBD_SOURCE_OR_SINK",
  "valid": "TBD_VALID_SIGNAL",
  "ready": "TBD_READY_SIGNAL",
  "payload": [
    {
      "name": "TBD_PAYLOAD_FIELD",
      "width": 0,
      "signed": false
    }
  ],
  "source_ref": "TBD: exact UCIe revision, clause/table, page, controlled source"
}
~~~

## Mandatory review questions before generation

1. Is the specification revision and all applicable ECNs frozen?
2. Are all signal names, directions, widths, and parameter dependencies copied from the controlled interface definition?
3. Is the agent's source/sink role correct relative to the DUT boundary?
4. Is the protocol sample edge known, and is the separate testbench drive edge race-safe in the selected simulator?
5. Are reset and reset-during-transfer semantics documented? The generic generator does not implement reset and rejects a non-empty reset declaration.
6. Are payload packing, valid/ready acceptance, and stability rules fully understood?
7. Are there additional sideband, flush, error, ordering, or credit signals that make the simple ready/valid abstraction incomplete?
8. Does each field have an exact source reference and evidence status?

## Exit criteria

Do not call a generated agent project-ready until:
- The contract is reviewed by the RTL/interface owner.
- Every normative field has an exact source reference.
- Project decisions and assumptions are explicitly marked.
- Reset behavior is implemented and reviewed separately.
- Generated interface, UVM package, and SVA include are compiled in the target UVM simulator.
- Directed transfer, stall, backpressure, and reset tests pass.
- Simulator version, compile options, seed, logs, and source commit are archived.

The generic agent is a starting scaffold only. It does not model UCIe CRC, retry/replay, credits, training, power states, sideband, or FDI/RDI-specific semantics.
