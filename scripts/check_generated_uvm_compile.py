#!/usr/bin/env python3
"""Compile generated source/sink UVM packages against pinned Accellera UVM using Slang.

This is a front-end compile/type-check, not a dynamic simulation or sign-off run.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp-server"))

from ucie_mcp import core  # noqa: E402
from pyslang.driver import CommandLineOptions, Driver  # noqa: E402


def contract(role: str) -> dict:
    return {
        "schema_version": "1.0",
        "interface_name": f"uvm_ci_{role}_if",
        "agent_name": f"uvm_ci_{role}",
        "clock": "link_clk",
        "drive_edge": "negedge",
        "sample_edge": "posedge",
        "role": role,
        "valid": f"{role}_valid",
        "ready": f"{role}_ready",
        "payload": [
            {"name": f"{role}_flit", "width": 128},
            {"name": f"{role}_opcode", "width": 4},
            {"name": f"{role}_signed_meta", "width": 7, "signed": True},
        ],
        "source_ref": "CI fixture only; not a UCIe specification claim",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uvm-src", type=Path, required=True)
    args = parser.parse_args()
    uvm_src = args.uvm_src.resolve()
    uvm_pkg = uvm_src / "uvm_pkg.sv"
    if not uvm_pkg.is_file() or not (uvm_src / "uvm_macros.svh").is_file():
        raise FileNotFoundError(f"Accellera UVM source tree not found: {uvm_src}")

    with tempfile.TemporaryDirectory(prefix="ucie-uvm-compile-") as temporary:
        work = Path(temporary)
        sources = [uvm_pkg]
        for role in ("source", "sink"):
            generated = core.generate_ready_valid_uvm_agent(json.dumps(contract(role)))
            interface = generated["interface_sv"]
            marker = f"endinterface : {generated['interface_name']}"
            if marker not in interface:
                raise RuntimeError(f"{role}: generated interface terminator missing")
            interface = interface.replace(
                marker, generated["assertions_sv"] + "\n" + marker
            )
            interface_path = work / generated["interface_file"]
            package_path = work / generated["package_file"]
            interface_path.write_text(interface, encoding="utf-8")
            package_path.write_text(generated["package_sv"], encoding="utf-8")
            sources.extend([interface_path, package_path])

        command = [
            "slang",
            f"-I{uvm_src}",
            "-DUVM_NO_DPI",
            *[str(path) for path in sources],
        ]
        driver = Driver()
        driver.addStandardArgs()
        if not driver.parseCommandLine(shlex.join(command), CommandLineOptions()):
            raise RuntimeError("Slang rejected the generated compile command")
        if not driver.processOptions():
            raise RuntimeError("Slang failed while processing compile options")
        if not driver.parseAllSources():
            raise RuntimeError("Slang failed while parsing the UVM and generated sources")
        compilation = driver.createCompilation()
        driver.reportCompilation(compilation, True)
        if compilation.hasIssuedErrors:
            raise RuntimeError("Slang reported semantic or elaboration errors")

    print(
        "Accellera UVM 2020.3.1 compile/type-check passed for both generated "
        "source and sink agents. This is not a simulation."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"generated UVM compile check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
