import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from ai_platform.models import Provider, RequestContext
from ai_platform.routing import NoEligibleProvider, choose_provider


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.providers = [
            Provider("fast", frozenset({"us"}), frozenset({"chat", "json"}), 3, 250, 0.82, 0.999),
            Provider(
                "quality",
                frozenset({"us"}),
                frozenset({"chat", "json", "tools"}),
                12,
                900,
                0.97,
                0.995,
            ),
        ]

    def test_cost_ceiling_is_hard_constraint(self):
        ctx = RequestContext("t1", "us", frozenset({"chat"}), 1000, max_cost_per_million=5)
        self.assertEqual(choose_provider(self.providers, ctx).provider, "fast")

    def test_capability_filter(self):
        ctx = RequestContext("t1", "us", frozenset({"tools"}), 1000)
        self.assertEqual(choose_provider(self.providers, ctx).provider, "quality")

    def test_no_eligible_provider(self):
        ctx = RequestContext("t1", "eu", frozenset({"chat"}), 1000)
        with self.assertRaises(NoEligibleProvider):
            choose_provider(self.providers, ctx)


if __name__ == "__main__":
    unittest.main()
