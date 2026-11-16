import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

import build_release


class ReleaseArchiveTests(unittest.TestCase):
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
