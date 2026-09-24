import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

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
render = load_module("render_figures", SCRIPTS / "render_figures.py")
punct = load_module("normalize_cjk_punct", SCRIPTS / "normalize_cjk_punct.py")


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
        candidates = [SKILL / "SKILL.md", *SKILL.glob("references/*.md"), *SKILL.glob("scripts/*")]
        # scripts/ picks up __pycache__ once anything imports these modules.
        inspected = [path for path in candidates if path.is_file()]
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

    def test_local_pdf_can_be_staged_without_text_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "source.pdf"
            output = tmp / "paper"
            document = fitz.open()
            document.new_page().insert_text((72, 72), "Use MinerU for the content")
            document.save(source)
            document.close()
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "index_pdf.py"), str(source),
                 "--dir", str(output), "--slug", "private-paper", "--no-text"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "private-paper.pdf").exists())
            self.assertFalse((output / "private-paper_pages.jsonl").exists())
            self.assertIn("skipped (--no-text", result.stdout)


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
            self.assertGreaterEqual(fitz.Pixmap(str(out)).width, 1440)


class MineruCliTests(unittest.TestCase):
    @staticmethod
    def blank_pdf(directory):
        pdf = Path(directory) / "paper.pdf"
        document = fitz.open()
        document.new_page()
        document.save(pdf)
        document.close()
        return pdf

    def test_help_and_missing_token_are_offline(self):
        script = SCRIPTS / "mineru_parse_pdf.sh"
        help_result = subprocess.run(["bash", str(script), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            pdf = self.blank_pdf(tmp)
            home = Path(tmp) / "home"
            home.mkdir()
            result = subprocess.run(
                ["bash", str(script), str(pdf), str(Path(tmp) / "mineru")],
                capture_output=True,
                text=True,
                env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("MINERU_TOKEN is not set", result.stderr)

    def test_token_file_is_read_from_home(self):
        """A ~/.mineru_token is picked up. An invalid token proves it offline:
        the charset check runs after the file is read, so we never reach the network."""
        script = SCRIPTS / "mineru_parse_pdf.sh"
        with tempfile.TemporaryDirectory() as tmp:
            pdf = self.blank_pdf(tmp)
            home = Path(tmp) / "home"
            home.mkdir()
            (home / ".mineru_token").write_text("not a valid token!\n", encoding="utf-8")
            result = subprocess.run(
                ["bash", str(script), str(pdf), str(Path(tmp) / "mineru")],
                capture_output=True,
                text=True,
                env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("unsupported characters", result.stderr)
            self.assertNotIn("MINERU_TOKEN is not set", result.stderr)

    def test_overlong_pdf_is_rejected_before_upload(self):
        script = SCRIPTS / "mineru_parse_pdf.sh"
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "long-report.pdf"
            document = fitz.open()
            for _ in range(201):
                document.new_page()
            document.save(pdf)
            document.close()
            result = subprocess.run(
                ["bash", str(script), str(pdf), str(Path(tmp) / "mineru")],
                capture_output=True, text=True,
                env={**os.environ, "MINERU_TOKEN": "dummy-token"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("limit of 200 pages", result.stderr)
            self.assertIn("No partial extraction was uploaded", result.stderr)


class RenderFiguresTests(unittest.TestCase):
    """render_figures.py re-rasterizes MinerU's own bboxes instead of guessing boundaries.

    MinerU caps its images near ~1100px and exposes no DPI knob, so publishing its JPEGs at
    2x display width reads blurry. These tests pin the two properties that make the fix safe:
    the output is genuinely higher resolution, and a wrong bbox is reported, not written silently.
    """

    BBOX = [72.0, 120.0, 522.0, 420.0]  # 450x300 -> ratio 1.5
    IMAGE = "bcedd339aa11.jpg"

    def build_fixture(self, tmp, bbox=None):
        tmp = Path(tmp)
        (tmp / "mineru/images").mkdir(parents=True)
        document = fitz.open()
        for _ in range(3):
            document.new_page(width=595, height=842)
        document[1].insert_text((90, 160), "Figure 1")
        pdf = tmp / "paper.pdf"
        document.save(pdf)
        document.close()

        # MinerU's own raster for that region, at its usual ~1100px cap.
        original = fitz.open()
        page = original.new_page(width=450, height=300)
        page.get_pixmap(matrix=fitz.Matrix(2.4, 2.4)).save(tmp / "mineru/images" / self.IMAGE)
        original.close()

        body = {"type": "image_body", "bbox": bbox or self.BBOX,
                "lines": [{"spans": [{"image_path": self.IMAGE}]}]}
        layout = {"pdf_info": [
            {"page_idx": 0, "para_blocks": []},
            {"page_idx": 1, "para_blocks": [
                {"type": "image", "bbox": bbox or self.BBOX, "blocks": [body]}]},
            {"page_idx": 2, "para_blocks": []},
        ]}
        (tmp / "mineru/layout.json").write_text(json.dumps(layout), encoding="utf-8")
        return pdf, tmp / "mineru"

    def render(self, pdf, mineru_dir, out):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "render_figures.py"), str(pdf), str(mineru_dir),
             "--out", str(out), "--pick", "bcedd339=Fig1:760"],
            capture_output=True, text=True,
        )

    def test_bbox_map_reads_mineru_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, mineru_dir = self.build_fixture(tmp)
            mapping = render.load_bbox_map(str(mineru_dir))
            self.assertEqual(list(mapping), [self.IMAGE])
            self.assertEqual(mapping[self.IMAGE]["page"], 2)
            self.assertEqual(mapping[self.IMAGE]["bbox"], self.BBOX)

    def test_render_upscales_and_preserves_the_region(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf, mineru_dir = self.build_fixture(tmp)
            out = Path(tmp) / "figs_hires"
            result = self.render(pdf, mineru_dir, out)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ok ", result.stdout)
            self.assertNotIn("MISMATCH", result.stdout)

            # Pixmap reports real pixels; opening the PNG as a document would report
            # points at 72dpi and silently understate the resolution.
            rendered = fitz.Pixmap(str(out / "Fig1.png"))
            width, height = rendered.width, rendered.height
            # 760 CSS px at dpr 2 -> ~1520 physical px, well above MinerU's 1080.
            self.assertGreater(width, 1400)
            self.assertAlmostEqual(width / height, 1.5, places=1)

    def test_wrong_bbox_is_reported_not_silently_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            # A bbox that swallows body text below the figure: the classic mis-frame.
            pdf, mineru_dir = self.build_fixture(tmp, bbox=[72.0, 120.0, 522.0, 700.0])
            result = self.render(pdf, mineru_dir, Path(tmp) / "figs")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MISMATCH", result.stdout)
            self.assertIn("Inspect before publishing", result.stdout)

    def test_verified_render_rewrites_manifest_to_high_resolution_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf, mineru_dir = self.build_fixture(tmp)
            manifest = Path(tmp) / "figures.manifest"
            manifest.write_text(
                f"<!-- FIG mineru/images/{self.IMAGE} | anchor:after-method | w=760 | cap:图 1：架构。 -->\n",
                encoding="utf-8",
            )
            out = Path(tmp) / "figs_hires"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "render_figures.py"), str(pdf), str(mineru_dir),
                 "--out", str(out), "--pick", "bcedd339=Fig1:760",
                 "--manifest", str(manifest)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("figs_hires/Fig1.png", manifest.read_text(encoding="utf-8"))
            self.assertNotIn(self.IMAGE, manifest.read_text(encoding="utf-8"))

    def test_failed_ratio_check_keeps_provisional_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf, mineru_dir = self.build_fixture(tmp, bbox=[72.0, 120.0, 522.0, 700.0])
            manifest = Path(tmp) / "figures.manifest"
            original = f"<!-- FIG mineru/images/{self.IMAGE} | anchor:after-method | w=760 | cap:图 1：架构。 -->\n"
            manifest.write_text(original, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "render_figures.py"), str(pdf), str(mineru_dir),
                 "--out", str(Path(tmp) / "figs_hires"),
                 "--pick", "bcedd339=Fig1:760", "--manifest", str(manifest)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(manifest.read_text(encoding="utf-8"), original)

    def test_missing_layout_json_explains_the_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf, mineru_dir = self.build_fixture(tmp)
            (mineru_dir / "layout.json").unlink()
            result = self.render(pdf, mineru_dir, Path(tmp) / "figs")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MINERU_REFRESH", result.stdout + result.stderr)


class MineruOutputTests(unittest.TestCase):
    """The installer block inside mineru_parse_pdf.sh must keep layout.json,
    which is what render_figures.py reads its bboxes from."""

    @staticmethod
    def install_block():
        text = (SCRIPTS / "mineru_parse_pdf.sh").read_text(encoding="utf-8")
        blocks = re.findall(r"<<'PY'\n(.*?)\nPY", text, re.S)
        return blocks[-1]

    def run_install(self, tmp, with_layout):
        tmp = Path(tmp)
        source = tmp / "src"
        (source / "images").mkdir(parents=True)
        (source / "full.md").write_text("# Paper\n", encoding="utf-8")
        (source / "images/a.jpg").write_bytes(b"fake")
        (source / "middle.json").write_text("{}", encoding="utf-8")
        if with_layout:
            (source / "layout.json").write_text('{"pdf_info": []}', encoding="utf-8")
        archive = tmp / "result.zip"
        with zipfile.ZipFile(archive, "w") as handle:
            for path in source.rglob("*"):
                if path.is_file():
                    handle.write(path, path.relative_to(source))

        script = tmp / "install.py"
        script.write_text(self.install_block(), encoding="utf-8")
        out = tmp / "out"
        result = subprocess.run(
            [sys.executable, str(script), str(archive), str(tmp / "extract"), str(out)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return out

    def test_layout_json_is_kept_and_scratch_files_are_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.run_install(tmp, with_layout=True)
            self.assertTrue((out / "full.md").is_file())
            self.assertTrue((out / "images").is_dir())
            self.assertTrue((out / "layout.json").is_file(), "render_figures.py needs this")
            self.assertFalse((out / "middle.json").exists())

    def test_missing_layout_json_is_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.run_install(tmp, with_layout=False)
            self.assertTrue((out / "full.md").is_file())
            self.assertFalse((out / "layout.json").exists())


class PunctuationTests(unittest.TestCase):
    def test_converts_chinese_context_only(self):
        got = punct.process(
            '<p>方法(简称 VLA),准确率 92.5%,共 1,200 条,比例 1:15;见 '
            '<latex>a, b: c</latex> 与 <b>要点</b>:结束!</p>'
        )
        self.assertIn("（简称 VLA）", got)
        self.assertIn("1,200", got)      # thousands separator stays half-width
        self.assertIn("1:15", got)       # ratio stays half-width
        self.assertIn("<latex>a, b: c</latex>", got)  # math is never touched
        self.assertIn("：结束！", got)

    def test_ascii_only_text_is_untouched(self):
        source = "<p>Pure ASCII sentence, with commas: unchanged (really)!</p>"
        self.assertEqual(punct.process(source), source)

    def test_attribute_values_are_untouched(self):
        source = '<p>见 <bookmark href="https://arxiv.org/abs/2503.20020?a=1,2">论文</bookmark>。</p>'
        self.assertIn('href="https://arxiv.org/abs/2503.20020?a=1,2"', punct.process(source))


class InstallerTests(unittest.TestCase):
    INSTALLER = ROOT / "install.sh"

    def test_syntax_is_valid(self):
        result = subprocess.run(["bash", "-n", str(self.INSTALLER)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_install_is_scoped_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "skills"
            for _ in range(2):
                result = subprocess.run(
                    ["bash", str(self.INSTALLER), "--dest", str(dest), "--skip-deps"],
                    capture_output=True,
                    text=True,
                    cwd=str(ROOT),
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            installed = dest / "embodied-paper-deep-read"
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "scripts/fetch_arxiv.py").is_file())
            self.assertTrue((installed / "scripts/_pymupdf.py").is_file())
            self.assertTrue((installed / "references/writing-style.md").is_file())
            # Maintainer-only material must never ship into a user's skills directory.
            self.assertFalse((installed / "tests").exists())
            self.assertFalse(list(installed.rglob("__pycache__")))

    def test_install_preserves_a_private_venv(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "skills"
            args = ["bash", str(self.INSTALLER), "--dest", str(dest), "--skip-deps"]
            subprocess.run(args, capture_output=True, text=True, cwd=str(ROOT), check=True)
            marker = dest / "embodied-paper-deep-read" / ".venv" / "marker"
            marker.parent.mkdir(parents=True)
            marker.write_text("keep me", encoding="utf-8")
            subprocess.run(args, capture_output=True, text=True, cwd=str(ROOT), check=True)
            self.assertTrue(marker.is_file(), "reinstall must not delete the dependency venv")

    def test_install_can_create_both_official_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)
            env.pop("CLAUDE_CONFIG_DIR", None)
            result = subprocess.run(
                ["bash", str(self.INSTALLER), "--agent", "both", "--skip-deps"],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for root in (home / ".claude/skills", home / ".codex/skills", home / ".agents/skills"):
                self.assertTrue((root / "embodied-paper-deep-read/SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
