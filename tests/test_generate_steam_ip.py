import unittest

from scripts.generate_steam_ip import generate_rule_set


class GenerateRuleSetTest(unittest.TestCase):
    def test_generates_and_collapses_networks(self) -> None:
        config = {
            "success": True,
            "pops": {
                "regular-a": {
                    "partners": 1,
                    "relays": [{"ipv4": "10.0.0.10"}, {"ipv4": "10.0.0.11"}],
                },
                "regular-b": {
                    "partners": 3,
                    "relays": [{"ipv4": "192.0.2.7", "ipv6": "2001:db8::1"}],
                },
                "partner": {
                    "partners": 2,
                    "relays": [
                        {"ipv4": "203.0.113.129"},
                        {"ipv4": "203.0.113.134"},
                    ],
                },
            },
        }

        self.assertEqual(
            generate_rule_set(config),
            {
                "version": 4,
                "rules": [
                    {
                        "ip_cidr": [
                            "10.0.0.10/31",
                            "192.0.2.7/32",
                            "203.0.113.129/32",
                            "203.0.113.134/32",
                            "2001:db8::1/128",
                        ]
                    }
                ],
            },
        )

    def test_rejects_unsuccessful_response(self) -> None:
        with self.assertRaisesRegex(ValueError, "success=true"):
            generate_rule_set({"success": False, "pops": {"x": {}}})

    def test_rejects_empty_relay_list(self) -> None:
        with self.assertRaisesRegex(ValueError, "relay addresses"):
            generate_rule_set({"success": True, "pops": {"x": {"relays": []}}})

    def test_rejects_invalid_address(self) -> None:
        config = {
            "success": True,
            "pops": {"x": {"relays": [{"ipv4": "not-an-address"}]}},
        }
        with self.assertRaisesRegex(ValueError, "invalid ipv4"):
            generate_rule_set(config)


if __name__ == "__main__":
    unittest.main()
