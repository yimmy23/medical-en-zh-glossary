"""Tests for scripts/glossary.py. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("glossary", ROOT / "scripts" / "glossary.py")
glossary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(glossary)

SAMPLE = (
    "source\ttarget\tnotes\n"
    "confounding by indication\t适应证混杂（confounding by indication）\tNOT 指征混杂/指示混杂\n"
    "immortal-time bias\t永生时间偏倚（immortal-time bias）\t❗NOT 不朽时间偏倚\n"
    "standardised mean difference\t标准化均数差（standardised mean difference，SMD）\t\n"
)


class GlossaryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.main = self.dir / "glossary.tsv"
        self.main.write_text(SAMPLE, encoding="utf-8")
        self._saved = (glossary.MAIN, glossary.EXTERNAL)
        glossary.MAIN, glossary.EXTERNAL = self.main, self.dir / "missing.tsv"

    def tearDown(self):
        glossary.MAIN, glossary.EXTERNAL = self._saved
        self.tmp.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = glossary.main(list(args))
        return code, out.getvalue()

    def write(self, name: str, text: str) -> str:
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_check_flags_forbidden_translation(self):
        code, out = self.run_cli("check", self.write("t.md", "本文核心难题是指示混杂。\n"))
        self.assertEqual(code, 1)
        self.assertIn("禁用「指示混杂」", out)

    def test_check_flags_missing_translation_in_bilingual_file(self):
        doc = "Confounding by indication is central.\n\n> 本文核心难题是治疗选择混杂。\n"
        code, out = self.run_cli("check", self.write("t.md", doc))
        self.assertEqual(code, 1)
        self.assertIn("译文未见「适应证混杂」", out)

    def test_check_matches_hyphen_and_ize_variants(self):
        src = self.write("en.md", "Immortal time bias and the standardized mean difference.\n")
        code, out = self.run_cli("check", self.write("zh.md", "无关译文。\n"), "--source", src)
        self.assertEqual(code, 1)
        self.assertIn("永生时间偏倚", out)
        self.assertIn("标准化均数差", out)

    def test_check_passes_clean_translation(self):
        doc = "Confounding by indication.\n\n> 适应证混杂。\n"
        code, _ = self.run_cli("check", self.write("t.md", doc))
        self.assertEqual(code, 0)

    def test_lookup_english_and_chinese(self):
        self.assertIn("适应证混杂", self.run_cli("lookup", "CONFOUNDING BY INDICATION")[1])
        self.assertIn("immortal-time bias", self.run_cli("lookup", "永生时间偏倚")[1])
        self.assertEqual(self.run_cli("lookup", "nonexistent-term")[0], 1)

    def test_lookup_by_abbreviation_matches_whole_words_only(self):
        out = self.run_cli("lookup", "smd")[1]
        self.assertIn("standardised mean difference", out)
        self.assertEqual(self.run_cli("lookup", "ind")[0], 1)  # not a substring of "indication"

    def test_add_inserts_sorted_and_rejects_duplicates(self):
        code, _ = self.run_cli("add", "estimand", "估计目标（estimand）", "ICH E9(R1) 中文版")
        self.assertEqual(code, 0)
        sources = [r[0] for r in glossary.read_rows(self.main)]
        self.assertEqual(sources, sorted(sources, key=str.lower))
        self.assertEqual(self.run_cli("add", "Estimand", "估计目标")[0], 2)
        self.assertEqual(self.run_cli("lint")[0], 0)

    def test_lint_reports_unsorted_and_halfwidth_brackets(self):
        self.main.write_text(
            "source\ttarget\tnotes\nzeta\t泽塔\t\nalpha\t阿尔法(alpha)\t\n", encoding="utf-8"
        )
        code, out = self.run_cli("lint")
        self.assertEqual(code, 1)
        self.assertIn("not sorted", out)
        self.assertIn("full-width", out)

    def test_bundled_glossary_is_clean(self):
        glossary.MAIN = self._saved[0]
        self.assertEqual(self.run_cli("lint")[0], 0)


if __name__ == "__main__":
    unittest.main()
