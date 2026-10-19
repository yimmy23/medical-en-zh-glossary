#!/usr/bin/env python3
"""English-Chinese medical glossary tool (stdlib only).

Commands:
  lookup QUERY [--all]           Find a term in the main glossary, then the external list.
                                 QUERY may be English or Chinese; matching is case-insensitive.
  check FILE [--source SRC]      Check a translation: forbidden translations ("NOT ..." in notes)
                                 and glossary terms whose English appears in SRC (default: FILE
                                 itself, for bilingual files) but whose Chinese is missing.
  lint                           Validate the main glossary (columns, duplicates, order, brackets).
  add SOURCE TARGET [NOTES]      Insert a verified term into the main glossary in sorted order.

Exit codes: 0 ok, 1 findings (check/lint) or not found (lookup), 2 bad input.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REFS = Path(__file__).resolve().parent.parent / "references"
MAIN = REFS / "glossary.tsv"
EXTERNAL = REFS / "external-medical-translator.tsv"
HEADER = "source\ttarget\tnotes"
CJK = re.compile(r"[一-鿿]")


def read_rows(path: Path) -> list[list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.split("\t") for ln in lines[1:] if ln.strip()]


def sort_key(row: list[str]) -> str:
    return row[0].lower()


def head_term(target: str) -> str:
    """Chinese part of a target, e.g. 适应证混杂（confounding by indication） -> 适应证混杂."""
    return re.split(r"[（(]", target, maxsplit=1)[0].strip()


def abbreviations(row: list[str]) -> set[str]:
    """Abbreviations from the target (…，ITT）) or the external list's notes (缩写 ITT/KM)."""
    found = set(re.findall(r"，\s*([A-Za-z][\w\-–/]*)）", row[1]))
    if len(row) > 2:
        for m in re.finditer(r"缩写 ([^；]+)", row[2]):
            found.update(m.group(1).split("/"))
    return {a.strip().lower() for a in found if a.strip()}


def source_pattern(source: str) -> re.Pattern[str]:
    """Match an English term case-insensitively, tolerating hyphen/space and -ise/-ize variants."""
    pat = re.escape(source)
    pat = re.sub(r"(\\-|\\ |-| )", r"[-\\s]", pat)
    pat = re.sub(r"is(?=e|a)", "i[sz]", pat)
    return re.compile(rf"(?<![A-Za-z]){pat}(?![A-Za-z])", re.IGNORECASE)


def forbidden(rows: list[list[str]]) -> list[tuple[str, str]]:
    out = []
    for row in rows:
        if len(row) < 3:
            continue
        for m in re.finditer(r"NOT\s+([^；;（(]+)", row[2]):
            for word in re.split(r"[/、]", m.group(1)):
                if word.strip():
                    out.append((word.strip(), row[1]))
    return out


def cmd_lookup(args: argparse.Namespace) -> int:
    q = args.query.strip().lower()
    found = False
    for label, path in (("主表", MAIN), ("外部表·未核", EXTERNAL)):
        if not path.exists():
            continue
        rows = read_rows(path)
        exact = [r for r in rows if q in (r[0].lower(), head_term(r[1]).lower()) or q in abbreviations(r)]
        if CJK.search(q):
            partial = [r for r in rows if r not in exact and q in r[1].lower()]
        else:  # whole-word match, so "ITT" does not hit "Committee"
            word = re.compile(rf"(?<![a-z0-9]){re.escape(q)}(?![a-z0-9])")
            partial = [r for r in rows if r not in exact and (word.search(r[0].lower()) or word.search(r[1].lower()))]
        hits = exact + partial
        if not args.all:
            hits = hits[:10]
        for r in hits:
            found = True
            print(f"[{label}] {r[0]}\t{r[1]}" + (f"\t{r[2]}" if len(r) > 2 and r[2] else ""))
        if exact and label == "主表" and not args.all:
            break  # main glossary is authoritative; skip the external list
    if not found:
        print(f"未找到：{args.query}（需核权威来源后再用，查不到标“待核”）", file=sys.stderr)
    return 0 if found else 1


def cmd_check(args: argparse.Namespace) -> int:
    path = Path(args.file)
    src_path = Path(args.source) if args.source else path
    for p in (path, src_path):
        if not p.is_file():
            print(f"not a file: {p}", file=sys.stderr)
            return 2
    text = path.read_text(encoding="utf-8")
    source_text = src_path.read_text(encoding="utf-8")
    rows = read_rows(MAIN)
    findings = 0

    banned = forbidden(rows)
    for lineno, line in enumerate(text.splitlines(), 1):
        for word, target in banned:
            if word in line:
                findings += 1
                print(f"{path}:{lineno}: 禁用「{word}」→ 应为 {target}")

    for row in rows:
        head = head_term(row[1])
        if not CJK.search(head) or head in text:
            continue
        m = source_pattern(row[0]).search(source_text)
        if m:
            findings += 1
            lineno = source_text.count("\n", 0, m.start()) + 1
            print(f"{src_path}:{lineno}: 原文有「{m.group(0)}」，译文未见「{head}」→ 核对是否改用了别的译法")

    sys.stdout.flush()
    print(f"{findings} finding(s)", file=sys.stderr)
    return 1 if findings else 0


def lint_rows(rows: list[list[str]], header: str) -> list[str]:
    problems = []
    if header != HEADER:
        problems.append(f"header should be: {HEADER!r}")
    seen: dict[str, int] = {}
    for i, row in enumerate(rows, 2):
        if len(row) != 3:
            problems.append(f"line {i}: expected 3 tab-separated columns, got {len(row)}")
            continue
        source, target, _ = row
        if not source.strip() or not target.strip():
            problems.append(f"line {i}: empty source or target")
        if "(" in target or ")" in target:
            problems.append(f"line {i}: use full-width （） in target: {target}")
        key = source.lower()
        if key in seen:
            problems.append(f"line {i}: duplicate source {source!r} (first at line {seen[key]})")
        seen.setdefault(key, i)
    keys = [sort_key(r) for r in rows]
    if keys != sorted(keys):
        problems.append("rows are not sorted by source (case-insensitive)")
    return problems


def cmd_lint(_: argparse.Namespace) -> int:
    header = MAIN.read_text(encoding="utf-8").splitlines()[0]
    problems = lint_rows(read_rows(MAIN), header)
    for p in problems:
        print(p)
    sys.stdout.flush()
    print(f"{len(problems)} problem(s) in {MAIN.name}", file=sys.stderr)
    return 1 if problems else 0


def cmd_add(args: argparse.Namespace) -> int:
    rows = read_rows(MAIN)
    if any(r[0].lower() == args.source.lower() for r in rows):
        print(f"already in glossary: {args.source}（修改已有条目请直接编辑并在 notes 说明原因）", file=sys.stderr)
        return 2
    new = [args.source.strip(), args.target.strip(), args.notes.strip()]
    problems = lint_rows([new], HEADER)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    rows = sorted(rows + [new], key=sort_key)
    MAIN.write_text("\n".join([HEADER] + ["\t".join(r) for r in rows]) + "\n", encoding="utf-8")
    line = "\t".join(new)
    print(f"added: {line}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("lookup")
    p.add_argument("query")
    p.add_argument("--all", action="store_true", help="show every match, including the external list")
    p.set_defaults(func=cmd_lookup)
    p = sub.add_parser("check")
    p.add_argument("file")
    p.add_argument("--source", help="English source file, if FILE is not bilingual")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("lint")
    p.set_defaults(func=cmd_lint)
    p = sub.add_parser("add")
    p.add_argument("source")
    p.add_argument("target")
    p.add_argument("notes", nargs="?", default="")
    p.set_defaults(func=cmd_add)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
