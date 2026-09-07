import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from day1_energy_balance import coolant_rise_c, load_scenarios, required_flow_lpm  # noqa: E402


class EnergyBalanceTests(unittest.TestCase):
    def test_baseline_total_flow(self) -> None:
        self.assertAlmostEqual(required_flow_lpm(4800, 10), 6.9107, places=4)

    def test_round_trip(self) -> None:
        branch_flow = required_flow_lpm(4800, 10) / 8
        self.assertAlmostEqual(coolant_rise_c(600, branch_flow), 10.0)

    def test_half_flow_doubles_rise(self) -> None:
        branch_flow = required_flow_lpm(4800, 10) / 8
        self.assertAlmostEqual(coolant_rise_c(600, branch_flow / 2), 20.0)

    def test_scenarios(self) -> None:
        scenarios = load_scenarios()
        self.assertEqual(set(scenarios), {"uniform", "nonuniform", "restricted_branch"})
        for branches in scenarios.values():
            self.assertEqual(len(branches), 8)
            self.assertEqual(sum(float(row["power_w"]) for row in branches), 4800.0)


if __name__ == "__main__":
    unittest.main()

