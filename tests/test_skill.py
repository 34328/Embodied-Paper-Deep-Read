import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import fitz


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "embodied-paper-deep-read"
SCRIPTS = SKILL / "scripts"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fetch = load_module("fetch_arxiv", SCRIPTS / "fetch_arxiv.py")
figures = load_module("extract_figures", SCRIPTS / "extract_figures.py")


class SkillMetadataTests(unittest.TestCase):
    def test_frontmatter_and_openai_metadata(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        _, frontmatter, _ = text.split("---", 2)
        self.assertIn("name: embodied-paper-deep-read", frontmatter)
        self.assertIn("Feishu", frontmatter)
        interface = (SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$embodied-paper-deep-read", interface)

    def test_personal_learning_license_is_packaged(self):
        root_license = (ROOT / "LICENSE").read_text(encoding="utf-8")
        skill_license = (SKILL / "LICENSE").read_text(encoding="utf-8")
        self.assertEqual(root_license, skill_license)
        self.assertIn("Personal Learning License 1.0", root_license)
        self.assertIn("No Commercial or Organizational Use", root_license)
        self.assertNotIn("Apache License", root_license)

    def test_no_machine_specific_or_insecure_paths(self):
        inspected = [SKILL / "SKILL.md", *SKILL.glob("references/*.md"), *SKILL.glob("scripts/*")]
        text = "\n".join(path.read_text(encoding="utf-8") for path in inspected)
        self.assertNotIn("~/.claude", text)
        self.assertNotIn("curl -k", text)
        self.assertNotIn("CURL_TLS_ARGS=(-k)", text)


class ArxivTests(unittest.TestCase):
    def test_modern_and_legacy_ids(self):
        self.assertEqual(fetch.normalize_id("https://arxiv.org/pdf/2410.06940v4.pdf"), "2410.06940v4")
        self.assertEqual(fetch.normalize_id("https://arxiv.org/abs/hep-th/9901001"), "hep-th/9901001")

    def test_page_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pdf = tmp / "paper.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "Evidence on page one")
            document.save(pdf)
            document.close()
            pages, empty = fetch.dump_page_text(pdf, tmp / "full.txt", tmp / "pages.jsonl")
            self.assertEqual((pages, empty), (1, 0))
            record = json.loads((tmp / "pages.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(record["pdf_page"], 1)
            self.assertIn("Evidence", record["text"])

    def test_local_pdf_index_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "source.pdf"
            output = tmp / "paper"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "Private local evidence")
            document.save(source)
            document.close()
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "index_pdf.py"), str(source),
                 "--dir", str(output), "--slug", "private-paper"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "private-paper.pdf").exists())
            self.assertTrue((output / "private-paper_pages.jsonl").exists())


class FigureTests(unittest.TestCase):
    def test_manifest_preserves_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pdf = tmp / "paper.pdf"
            document = fitz.open()
            page = document.new_page(width=200, height=200)
            page.insert_text((40, 40), "Figure 1")
            document.save(pdf)
            document.close()
            spec = tmp / "spec.json"
            out = tmp / "images" / "figure.png"
            manifest = tmp / "figures.manifest"
            spec.write_text(json.dumps({"figures": [{
                "page": 1,
                "rect": [20, 20, 180, 100],
                "out": str(out),
                "anchor": "after-method",
                "caption": "图 1：测试图。",
            }]}, ensure_ascii=False), encoding="utf-8")
            figures.cmd_batch(str(pdf), str(spec), str(manifest), 1.0)
            self.assertIn("images/figure.png", manifest.read_text(encoding="utf-8"))


class MineruCliTests(unittest.TestCase):
    def test_help_and_missing_token_are_offline(self):
        script = SCRIPTS / "mineru_parse_pdf.sh"
        help_result = subprocess.run(["bash", str(script), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "paper.pdf"
            document = fitz.open()
            document.new_page()
            document.save(pdf)
            document.close()
            result = subprocess.run(
                ["bash", str(script), str(pdf), str(Path(tmp) / "mineru")],
                capture_output=True,
                text=True,
                env={"PATH": "/usr/bin:/bin"},
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("MINERU_TOKEN is not set", result.stderr)


if __name__ == "__main__":
    unittest.main()
