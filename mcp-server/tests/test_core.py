import json
import unittest

from ucie_mcp import core


class CoreTests(unittest.TestCase):
    def test_crc_check_vector(self):
        self.assertEqual(core.crc16_ccitt_false("313233343536373839")["crc"], "0x29B1")

    def test_crc_separators_and_prefix(self):
        self.assertEqual(core.crc16_ccitt_false("0x31 32:33-34_35 36 37 38 39")["crc"], "0x29B1")

    def test_crc_rejects_odd_hex(self):
        with self.assertRaises(ValueError):
            core.crc16_ccitt_false("ABC")

    def test_manifest_valid(self):
        manifest = {
            "schema_version": "1.0",
            "project": {"name": "test", "objective": "verify adapter"},
            "baseline": {"standard": "UCIe", "revision": "3.0", "specification_source": "controlled copy", "source_status": "verified"},
            "scope": {"in_scope": ["adapter"], "out_of_scope": ["analog PHY"]},
            "interfaces": [{"name": "FDI"}],
            "verification": {"methodology": "UVM"},
        }
        result = core.validate_project_manifest(json.dumps(manifest))
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["errors"], [])

    def test_manifest_missing_fields(self):
        self.assertEqual(core.validate_project_manifest('{"schema_version":"1.0"}')["status"], "invalid")

    def test_manifest_wrong_type(self):
        manifest = {"schema_version": "1.0", "project": [], "baseline": {}, "scope": {}, "interfaces": [], "verification": {}}
        self.assertEqual(core.validate_project_manifest(json.dumps(manifest))["status"], "invalid")

    def test_sv_shell(self):
        ports = [{"name": "clk", "direction": "input"}, {"name": "data", "direction": "input", "width": 64}, {"name": "ready", "direction": "output"}]
        rtl = core.generate_sv_module_shell("adapter_if", json.dumps(ports))
        self.assertIn("module adapter_if", rtl)
        self.assertIn("logic [63:0] data", rtl)
        self.assertIn("endmodule", rtl)

    def test_sv_rejects_duplicate_ports(self):
        ports = [{"name": "clk", "direction": "input"}, {"name": "clk", "direction": "output"}]
        with self.assertRaises(ValueError):
            core.generate_sv_module_shell("m", json.dumps(ports))

    def test_sva_skeleton_defaults_to_overlapped_implication(self):
        result = core.generate_sva_skeleton("p_stable", "clk", "valid && !ready", "$stable(data)", "!rst_n")
        self.assertIn("disable iff (!rst_n)", result)
        self.assertIn("(valid && !ready) |-> ($stable(data))", result)

    def test_sva_skeleton_supports_non_overlapped_implication(self):
        result = core.generate_sva_skeleton(
            "p_stable", "clk", "valid && !ready", "$stable(data)", "!rst_n", "|=>"
        )
        self.assertIn("(valid && !ready) |=> ($stable(data))", result)

    def test_sva_skeleton_rejects_unknown_implication(self):
        with self.assertRaises(ValueError):
            core.generate_sva_skeleton("p_bad", "clk", "a", "b", implication="|>>")

    def test_ready_valid_sva_checks_next_cycle_hold(self):
        result = core.generate_ready_valid_sva(
            "fdi_tx", "clk", "valid", "ready", "payload", "!rst_n"
        )
        self.assertIn("(valid && !ready) |=> valid;", result)
        self.assertIn("(valid && !ready) |=> $stable(payload);", result)
        self.assertEqual(result.count("disable iff (!rst_n)"), 2)

    def test_ready_valid_sva_rejects_expression_in_signal_name(self):
        with self.assertRaises(ValueError):
            core.generate_ready_valid_sva("tx", "clk", "valid", "ready", "payload[7:0]")

    def test_uvm_agent_skeleton_contains_standard_components(self):
        fields = [
            {"name": "valid"},
            {"name": "payload", "width": 128},
            {"name": "opcode", "width": 4, "signed": False},
        ]
        result = core.generate_uvm_agent_skeleton("fdi_tx", "fdi_if", json.dumps(fields))
        self.assertIn("class fdi_tx_item extends uvm_sequence_item", result)
        self.assertIn("class fdi_tx_sequencer extends uvm_sequencer", result)
        self.assertIn("class fdi_tx_driver extends uvm_driver", result)
        self.assertIn("class fdi_tx_monitor extends uvm_monitor", result)
        self.assertIn("class fdi_tx_agent extends uvm_agent", result)
        self.assertIn("uvm_field_int(payload, UVM_DEFAULT)", result)
        self.assertIn("virtual fdi_if vif", result)
        self.assertIn("TODO: implement run_phase", result)

    def test_uvm_agent_skeleton_rejects_duplicate_fields(self):
        fields = [{"name": "data", "width": 8}, {"name": "data", "width": 16}]
        with self.assertRaises(ValueError):
            core.generate_uvm_agent_skeleton("tx", "link_if", json.dumps(fields))

    def _ready_valid_contract(self, role="source"):
        return {
            "schema_version": "1.0", "interface_name": "fdi_tx_if", "agent_name": "fdi_tx",
            "clock": "clk", "drive_edge": "negedge", "sample_edge": "posedge", "role": role,
            "valid": "valid", "ready": "ready",
            "payload": [{"name": "flit", "width": 128}, {"name": "opcode", "width": 4}],
            "source_ref": "Project interface contract Rev A, Section 2.1"
        }

    def test_ready_valid_contract_accepts_explicit_source_contract(self):
        result = core.validate_ready_valid_contract(json.dumps(self._ready_valid_contract()))
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["role"], "source")
        self.assertEqual(result["payload_fields"], 2)
        self.assertEqual(result["warnings"], [])

    def test_ready_valid_contract_rejects_same_drive_and_sample_edge(self):
        contract = self._ready_valid_contract()
        contract["sample_edge"] = "negedge"
        result = core.validate_ready_valid_contract(json.dumps(contract))
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("must differ" in error for error in result["errors"]))

    def test_ready_valid_contract_rejects_duplicate_signal_names(self):
        contract = self._ready_valid_contract()
        contract["payload"][0]["name"] = "valid"
        result = core.validate_ready_valid_contract(json.dumps(contract))
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("must all be unique" in error for error in result["errors"]))

    def test_ready_valid_contract_rejects_reset_declaration(self):
        contract = self._ready_valid_contract()
        contract["reset"] = {"signal": "rst_n", "active_level": 0}
        result = core.validate_ready_valid_contract(json.dumps(contract))
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("Reset handling is not generated" in error for error in result["errors"]))

    def test_ready_valid_contract_warns_without_source_reference(self):
        contract = self._ready_valid_contract()
        del contract["source_ref"]
        result = core.validate_ready_valid_contract(json.dumps(contract))
        self.assertEqual(result["status"], "valid")
        self.assertTrue(any("No source_ref supplied" in warning for warning in result["warnings"]))

    def test_ready_valid_uvm_source_agent_generation(self):
        result = core.generate_ready_valid_uvm_agent(json.dumps(self._ready_valid_contract("source")))
        self.assertEqual(result["status"], "generated")
        self.assertIn("output valid, flit, opcode;", result["interface_sv"])
        self.assertIn("input ready;", result["interface_sv"])
        self.assertIn("input clk, valid, flit, opcode", result["interface_sv"])
        self.assertIn("output ready", result["interface_sv"])
        self.assertIn("vif.drv_cb.valid <= 1'b1;", result["package_sv"])
        self.assertIn("vif.drv_cb.flit <= req_item.flit;", result["package_sv"])
        self.assertIn("while (vif.mon_cb.ready !== 1'b1)", result["package_sv"])
        self.assertIn("analysis_port.write(observed);", result["package_sv"])

    def test_ready_valid_uvm_generation_includes_stall_assertions(self):
        result = core.generate_ready_valid_uvm_agent(json.dumps(self._ready_valid_contract("source")))
        self.assertIn("p_fdi_tx_valid_held_while_stalled", result["assertions_sv"])
        self.assertIn("(valid && !ready) |=> valid;", result["assertions_sv"])
        self.assertIn("$stable(flit)", result["assertions_sv"])
        self.assertIn("$stable(opcode)", result["assertions_sv"])
        self.assertEqual(result["assertions_file"], "fdi_tx_contract_assertions.svh")

    def test_ready_valid_uvm_sink_agent_generation(self):
        result = core.generate_ready_valid_uvm_agent(json.dumps(self._ready_valid_contract("sink")))
        self.assertIn("output ready;", result["interface_sv"])
        self.assertIn("input valid, flit, opcode;", result["interface_sv"])
        self.assertIn("output valid, flit, opcode", result["interface_sv"])
        self.assertIn("input clk, ready", result["interface_sv"])
        self.assertIn("rand bit ready;", result["package_sv"])
        self.assertIn("vif.drv_cb.ready <= req_item.ready;", result["package_sv"])
        self.assertIn("observed.ready = vif.mon_cb.ready;", result["package_sv"])

    def test_ready_valid_uvm_generator_uses_custom_signal_names(self):
        contract = self._ready_valid_contract("source")
        contract["clock"] = "link_clk"
        contract["valid"] = "tx_valid"
        contract["ready"] = "tx_ready"
        contract["payload"][0]["name"] = "tx_flit"
        result = core.generate_ready_valid_uvm_agent(json.dumps(contract))
        self.assertIn("vif.drv_cb.tx_valid <= 1'b1;", result["package_sv"])
        self.assertIn("vif.mon_cb.tx_ready !== 1'b1", result["package_sv"])
        self.assertIn("vif.mon_cb.tx_valid === 1'b1", result["package_sv"])
        self.assertIn("vif.drv_cb.tx_flit <= req_item.tx_flit;", result["package_sv"])
        self.assertIn("@(negedge link_clk)", result["interface_sv"])

    def test_ready_valid_sink_uses_custom_handshake_names(self):
        contract = self._ready_valid_contract("sink")
        contract["valid"] = "rx_valid"
        contract["ready"] = "sink_ready"
        result = core.generate_ready_valid_uvm_agent(json.dumps(contract))
        self.assertIn("vif.drv_cb.sink_ready <= req_item.ready;", result["package_sv"])
        self.assertIn("vif.mon_cb.rx_valid === 1'b1", result["package_sv"])
        self.assertIn("vif.mon_cb.sink_ready === 1'b1", result["package_sv"])
        self.assertIn("observed.ready = vif.mon_cb.sink_ready;", result["package_sv"])

    def test_ready_valid_uvm_generator_rejects_reset(self):
        contract = self._ready_valid_contract()
        contract["reset"] = {"signal": "rst_n", "active_level": 0}
        with self.assertRaises(ValueError):
            core.generate_ready_valid_uvm_agent(json.dumps(contract))

    def test_uvm_plan_keeps_todos(self):
        plan = core.generate_uvm_testplan(json.dumps([{"id": "F1", "name": "Retry", "source_refs": ["UCIe clause TBD"]}]))
        self.assertIn("F1_NOMINAL", plan)
        self.assertIn("TODO", plan)

    def test_traceability_gap(self):
        result = core.audit_traceability_matrix('[{"requirement_id":"R1","result":"PASS"}]')
        self.assertEqual(result["status"], "gaps_found")
        self.assertGreater(result["rows_with_gaps"], 0)

    def test_architecture_review_is_not_compliance(self):
        result = core.review_architecture_inputs('{"baseline":{"standard":"UCIe","revision":"3.0"}}')
        self.assertEqual(result["status"], "review_inputs_incomplete")
        self.assertIn("not a normative", result["disclaimer"])

    def test_json_size_limit(self):
        with self.assertRaises(ValueError):
            core.review_architecture_inputs('"' + ("x" * (core.MAX_JSON_CHARS + 1)) + '"')


if __name__ == "__main__":
    unittest.main()
