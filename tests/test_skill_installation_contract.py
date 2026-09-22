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


if __name__ == "__main__":
    unittest.main()
