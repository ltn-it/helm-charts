from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / "charts" / "openshift-ingressoperatorpatch"


def render(values: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "values.yaml"
        path.write_text(yaml.safe_dump(values), encoding="utf-8")
        return subprocess.run(
            ["helm", "template", "placement-test", str(CHART), "-f", str(path)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )


class IngressPlacementTests(unittest.TestCase):
    def ingress(self, values: dict) -> dict:
        result = render(values)
        self.assertEqual(result.returncode, 0, result.stderr)
        return next(
            item
            for item in yaml.safe_load_all(result.stdout)
            if item and item.get("kind") == "IngressController"
        )

    def test_default_does_not_override_operator_placement(self):
        self.assertEqual(
            self.ingress({})["spec"],
            {"routeAdmission": {"wildcardPolicy": "WildcardsAllowed"}},
        )

    def test_placement_preserves_certificate_and_wildcard_configuration(self):
        placement = {
            "nodeSelector": {"matchLabels": {"node-role.kubernetes.io/infra": ""}},
            "tolerations": [
                {
                    "key": "infra",
                    "operator": "Equal",
                    "value": "reserved",
                    "effect": "NoSchedule",
                }
            ],
        }
        self.assertEqual(
            self.ingress(
                {
                    "nodePlacement": placement,
                    "allowWildcards": False,
                    "ingress": {
                        "enabled": True,
                        "certificateSecret": "router-tls",
                        "dnsNames": ["router.example.invalid"],
                    },
                }
            )["spec"],
            {
                "nodePlacement": placement,
                "routeAdmission": {"wildcardPolicy": "WildcardsDisallowed"},
                "defaultCertificate": {"name": "router-tls"},
            },
        )

    def test_non_object_placement_is_rejected(self):
        result = render({"nodePlacement": "invalid"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("nodePlacement", result.stderr)


if __name__ == "__main__":
    unittest.main()
