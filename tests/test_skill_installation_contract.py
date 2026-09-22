from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillInstallationContractTest(unittest.TestCase):
    def test_skill_makes_source_and_runtime_setup_agent_owned(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("User experience contract", skill)
        self.assertIn("containing this `SKILL.md`", skill)
        self.assertIn("Do not ask the user to clone", skill)
        self.assertIn("Do not ask the user to install or configure Python", skill)

    def test_readme_starts_users_from_ai_skill_installation(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "请安装这个 Skill：https://github.com/qihaokaigong/qh-voice-skill",
            readme,
        )
        self.assertIn("用户不需要克隆本仓库", readme)
        self.assertLess(readme.index("## User installation"), readme.index("## Development setup"))

    def test_intel_macos_uses_the_existing_local_web_configuration_flow(self) -> None:
        environments = (ROOT / "references" / "supported-environments.md").read_text(
            encoding="utf-8"
        )
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("macOS | x64", environments)
        self.assertIn("Intel", environments)
        self.assertIn("temporary Chinese local configuration page", skill)
        self.assertIn("127.0.0.1", skill)

    def test_configuration_success_ends_install_without_mandatory_health_check(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("Run layered health checks", skill)
        self.assertIn("Do not run post-configuration health checks", skill)

    def test_skill_has_complete_reference_wiring(self) -> None:
        wiring = (ROOT / "references" / "hardware-wiring.md").read_text(
            encoding="utf-8"
        )

        required_connections = (
            "`VDD` | `3V3`",
            "`L/R` | `GND`",
            "`OUT` | `GPIO8`",
            "`BLK` | `3V3`",
            "`SDA` | `GPIO10`",
            "`DIN` | `GPIO18`",
            "`SPK+` | 喇叭正端",
            "`SPK-` | 喇叭负端",
        )
        for connection in required_connections:
            self.assertIn(connection, wiring)


if __name__ == "__main__":
    unittest.main()
