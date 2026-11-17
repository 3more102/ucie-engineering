# RTL-to-GDSII and FPGA implementation planning

## Shared RTL discipline

- Maintain a synthesizable source of truth.
- Separate simulation-only code and technology-specific wrappers.
- Define parameter ranges and elaboration-time assertions.
- Document clocks, resets, CDC/RDC crossings, IO timing, and reset sequencing.
- Keep constraints version-controlled and tied to a specific target.

## ASIC flow

1. RTL review and coding-rule checks.
2. Elaboration and lint.
3. CDC/RDC analysis.
4. Synthesis and constraint validation.
5. Formal equivalence where available.
6. Floorplanning and power planning.
7. Placement and optimization.
8. Clock-tree synthesis.
9. Routing and parasitic extraction.
10. Static timing analysis across required corners/modes.
11. DRC/LVS and physical verification.
12. Power analysis and sign-off review.

## FPGA flow

1. RTL elaboration and lint.
2. FPGA synthesis and resource mapping.
3. Pin/clock constraints and IO planning.
4. Placement and routing.
5. Timing analysis.
6. Bitstream generation.
7. Board bring-up and functional validation where hardware exists.

## Reporting

Report target FPGA/device or ASIC library/process, PVT corners, voltage, clock periods, uncertainty, IO delays, tool versions, constraints, area/resource use, timing/slack, power method, throughput, latency, and buffer utilization.

Do not compare FPGA timing or LUT counts directly with ASIC PPA. Clearly distinguish estimates, synthesis results, post-route results, and measured hardware results.
