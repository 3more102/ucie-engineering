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
