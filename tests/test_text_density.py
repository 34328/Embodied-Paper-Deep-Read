import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).parents[1] / "embodied-paper-deep-read" / "scripts" / "check_text_density.py"
SPEC = importlib.util.spec_from_file_location("check_text_density", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def cn(length):
    return "段" * length


class RhythmCheckTests(unittest.TestCase):
    def html_runs(self, body):
        return CHECKER.prose_wall_runs(CHECKER.html_layout_items(body, "sample.xml"))

    def markdown_runs(self, body):
        return CHECKER.prose_wall_runs(CHECKER.markdown_layout_items(body, "sample.md"))

    def test_three_dense_html_paragraphs_are_flagged(self):
        runs = self.html_runs(
            f"<h2>数据治理</h2><p>{cn(110)}</p><p>{cn(110)}</p><p>{cn(110)}</p>"
        )
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["section"], "数据治理")
        self.assertIn("dense prose", runs[0]["reasons"])

    def test_short_html_paragraphs_are_not_flagged(self):
        runs = self.html_runs(
            f"<h2>短说明</h2><p>{cn(40)}</p><p>{cn(40)}</p><p>{cn(40)}</p>"
        )
        self.assertEqual(runs, [])

    def test_three_normal_length_paragraphs_are_reviewed_by_layout_not_density(self):
        runs = self.html_runs(
            f"<h2>正常正文</h2><p>{cn(80)}</p><p>{cn(80)}</p><p>{cn(80)}</p>"
        )
        self.assertEqual(runs, [])

    def test_sliding_window_catches_one_short_and_two_dense_paragraphs(self):
        runs = self.html_runs(
            f"<h2>混合长度</h2><p>{cn(70)}</p><p>{cn(130)}</p><p>{cn(130)}</p>"
        )
        self.assertEqual(len(runs), 1)

    def test_two_tiny_paragraphs_do_not_turn_one_long_block_into_a_wall(self):
        runs = self.html_runs(
            f"<h2>非连续墙</h2><p>{cn(20)}</p><p>{cn(20)}</p><p>{cn(200)}</p>"
        )
        self.assertEqual(runs, [])

    def test_bold_lead_run_is_flagged_without_density(self):
        runs = self.html_runs(
            "<h2>并列项</h2>"
            "<p><b>条件一：</b>短说明。</p>"
            "<p><strong>条件二：</strong>短说明。</p>"
            "<p><b>条件三：</b>短说明。</p>"
        )
        self.assertEqual(len(runs), 1)
        self.assertIn("bold-lead rhythm", runs[0]["reasons"])

    def test_heading_and_structural_components_break_html_runs(self):
        body = (
            f"<h2>方法</h2><p>{cn(100)}</p><p>{cn(100)}</p>"
            f"<table><tr><td><p>{cn(150)}</p></td></tr></table>"
            f"<p>{cn(100)}</p><p>{cn(100)}</p>"
            f"<h3>下一节</h3><p>{cn(100)}</p><p>{cn(100)}</p>"
        )
        self.assertEqual(self.html_runs(body), [])

    def test_lists_callouts_figures_and_whiteboards_break_html_runs(self):
        breakers = (
            f"<ul><li>{cn(120)}</li></ul>"
            f"<callout><p>{cn(120)}</p></callout>"
            "<img src=\"x\"/>"
            "<whiteboard>flowchart LR</whiteboard>"
        )
        body = f"<h2>方法</h2><p>{cn(100)}</p><p>{cn(100)}</p>{breakers}<p>{cn(100)}</p>"
        self.assertEqual(self.html_runs(body), [])

    def test_generic_figure_diagram_svg_and_formula_tags_break_html_runs(self):
        components = (
            "<diagram>flowchart LR</diagram>",
            "<svg><text>图</text></svg>",
            "<fig><figcaption>图注</figcaption></fig>",
            "<figure><figcaption>图注</figcaption></figure>",
            "<math>x_t</math>",
        )
        for component in components:
            with self.subTest(component=component):
                body = (
                    f"<h2>方法</h2><p>{cn(100)}</p><p>{cn(100)}</p>"
                    f"{component}<p>{cn(100)}</p>"
                )
                self.assertEqual(self.html_runs(body), [])

    def test_display_formula_breaks_but_inline_formula_keeps_prose(self):
        display = (
            f"<h2>公式</h2><p>{cn(100)}</p><p>{cn(100)}</p>"
            "<p align=\"center\"><latex>\\text{中文公式}</latex></p>"
            f"<p>{cn(100)}</p>"
        )
        self.assertEqual(self.html_runs(display), [])

        inline = (
            f"<h2>机制</h2><p>{cn(110)}<latex>x_t</latex></p>"
            f"<p>{cn(110)}<math>y_t</math></p><p>{cn(110)}</p>"
        )
        self.assertEqual(len(self.html_runs(inline)), 1)

    def test_overlapping_windows_merge_into_one_span(self):
        body = "<h2>长节</h2>" + "".join(f"<p>{cn(110)}</p>" for _ in range(5))
        runs = self.html_runs(body)
        self.assertEqual(len(runs), 1)
        self.assertEqual(len(runs[0]["items"]), 5)

    def test_markdown_heading_list_table_and_figure_break_runs(self):
        body = (
            f"## 方法\n\n{cn(100)}\n\n{cn(100)}\n\n- {cn(100)}\n\n"
            f"{cn(100)}\n\n| 字段 | 内容 |\n|---|---|\n| A | {cn(100)} |\n\n"
            f"{cn(100)}\n\n![图](fig.png)\n\n{cn(100)}\n"
        )
        self.assertEqual(self.markdown_runs(body), [])

    def test_gfm_table_without_outer_pipes_breaks_markdown_runs(self):
        body = (
            f"## 方法\n\n{cn(100)}\n\n{cn(100)}\n\n"
            f"字段 | 内容\n--- | ---\nA | {cn(100)}\n\n{cn(100)}\n"
        )
        self.assertEqual(self.markdown_runs(body), [])
        blocks = CHECKER.markdown_blocks(body, "sample.md")
        self.assertTrue(all(CHECKER.cjk_count(block[3]) <= 220 for block in blocks))

    def test_centered_html_figure_and_caption_break_markdown_runs(self):
        body = (
            f"## 图示\n\n{cn(100)}\n\n{cn(100)}\n\n"
            '<p align="center"><img src="fig.png" /></p>\n\n'
            f'<p align="center"><sub>图 1：{cn(80)}</sub></p>\n\n'
            f"{cn(100)}\n\n{cn(100)}\n"
        )
        self.assertEqual(self.markdown_runs(body), [])

    def test_markdown_display_math_breaks_runs(self):
        body = (
            f"## 公式\n\n{cn(100)}\n\n{cn(100)}\n\n"
            "$$\n\\text{中文公式}\n$$\n\n"
            f"{cn(100)}\n"
        )
        self.assertEqual(self.markdown_runs(body), [])

    def test_markdown_dense_and_bold_runs_are_flagged(self):
        dense = f"## 结果\n\n{cn(110)}\n\n{cn(110)}\n\n{cn(110)}\n"
        self.assertEqual(len(self.markdown_runs(dense)), 1)

        bold = (
            "## 局限\n\n**信号：** 短说明。\n\n"
            "**几何：** 短说明。\n\n**迁移：** 短说明。\n"
        )
        self.assertEqual(len(self.markdown_runs(bold)), 1)

    def test_fetch_json_uses_the_same_rhythm_check(self):
        content = f"<h2>数据</h2><p>{cn(110)}</p><p>{cn(110)}</p><p>{cn(110)}</p>"
        payload = json.dumps({"data": {"document": {"content": content}}})
        _, layout = CHECKER.scan_with_layout(payload, "fetch.json", "json")
        self.assertEqual(len(CHECKER.prose_wall_runs(layout)), 1)

    def test_existing_single_block_threshold_still_works(self):
        blocks = CHECKER.html_blocks(f"<p>{cn(221)}</p>", "sample.xml")
        self.assertEqual(len(blocks), 1)
        self.assertGreater(CHECKER.cjk_count(blocks[0][3]), CHECKER.THRESHOLD)

    def test_html_long_block_line_number_survives_multiline_code(self):
        body = f"<pre>\ncode\nmore code\n</pre>\n<p>{cn(221)}</p>"
        blocks = CHECKER.html_blocks(body, "sample.xml")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][1], 5)

    def test_cli_exit_codes_distinguish_clean_review_and_parse_error(self):
        def run_cli(content, mode):
            return subprocess.run(
                [sys.executable, str(SCRIPT), "--format", mode, "-"],
                input=content,
                text=True,
                capture_output=True,
                check=False,
            )

        clean_result = run_cli(f"<p>{cn(20)}</p>", "html")
        wall_result = run_cli(
            f"<p>{cn(110)}</p><p>{cn(110)}</p><p>{cn(110)}</p>", "html"
        )
        error_result = run_cli("{not json", "json")
        self.assertEqual(clean_result.returncode, 0)
        self.assertEqual(wall_result.returncode, 1)
        self.assertEqual(error_result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
