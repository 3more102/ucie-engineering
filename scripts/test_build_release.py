import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

import build_release


class ReleaseArchiveTests(unittest.TestCase):
    def test_release_metadata_versions_are_consistent(self):
        root = build_release.ROOT
        manifest_version = __import__("json").loads(
            (root / "mcp-server" / "manifest.json").read_text(encoding="utf-8")
        )["version"]
        pyproject = (root / "mcp-server" / "pyproject.toml").read_text(encoding="utf-8")
        package_init = (root / "mcp-server" / "ucie_mcp" / "__init__.py").read_text(encoding="utf-8")
        server = (root / "mcp-server" / "ucie_mcp" / "server.py").read_text(encoding="utf-8")
        readme = (root / "mcp-server" / "README.md").read_text(encoding="utf-8")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        version = manifest_version
        self.assertIn(f'version = "{version}"', pyproject)
        self.assertIn(f'__version__ = "{version}"', package_init)
        self.assertIn(f'version="{version}"', server)
        self.assertIn(f"Version {version}", readme)
        self.assertIn(f"name: ucie-engineering-v{version}", workflow)

    def test_source_archive_contains_only_committed_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "ci@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "CI Test"], check=True)

            (root / "README.md").write_text("tracked readme\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "architecture.md").write_text("tracked architecture\n", encoding="utf-8")
            (root / ".gitignore").write_text(".env\n", encoding="utf-8")
            (root / "local-notes.txt").write_text("untracked workspace note\n", encoding="utf-8")

            subprocess.run(
                ["git", "-C", str(root), "add", "README.md", ".gitignore", "docs/architecture.md"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "--quiet", "-m", "fixture"],
                check=True,
            )

            (root / ".env").write_text("API_TOKEN=must-not-ship\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-f", ".env"], check=True)

            archive_path = build_release.build_source(root=root, dist=root / "dist")
            with zipfile.ZipFile(archive_path) as archive:
                names = set(archive.namelist())
                self.assertIn("README.md", names)
                self.assertIn("docs/architecture.md", names)
                self.assertNotIn(".env", names)
                self.assertNotIn("local-notes.txt", names)
                self.assertFalse(any(name.startswith("dist/") for name in names))


if __name__ == "__main__":
    unittest.main()
