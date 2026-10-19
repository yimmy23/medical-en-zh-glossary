---
name: medical-en-zh-glossary
description: English-Chinese medical terminology glossary for academic translation in thoracic oncology, lung cancer, clinical research methodology and biostatistics (target trial emulation, causal inference, survival analysis). Look up the standard Chinese for an English term or the reverse, check a translation for forbidden or inconsistent terms, and add verified terms. Use when translating or reviewing medical manuscripts, abstracts, reviewer comments or response letters between English and Chinese, or when the user asks 查术语、这个词怎么译、术语对不对、补术语、检查译文术语、医学翻译术语表.
license: CC0-1.0
metadata:
  version: "1.0.0"
---

# Medical English-Chinese Glossary

Goal: every term in a translation matches the main glossary; terms outside it are verified against an authoritative source or marked 待核; no forbidden translation remains.

Run commands from this skill's directory. They need only Python 3.9+.

## Before translating: look up terms

```bash
python3 scripts/glossary.py lookup "confounding by indication"   # English or Chinese query
```

- `[主表]` hit: use `target` as written. First mention uses the full form; later mentions follow `notes` (for example 后续用 ITT).
- Only an `[外部表·未核]` hit, or no hit: the external list is a lead, not a standard. Verify against an authoritative source first (ICH guideline Chinese editions, 全国科学技术名词审定委员会, 人卫版 textbooks, 中华医学会 journals, CSCO guidelines). If nothing authoritative is found, mark the term 待核 in the translation and tell the user.

## After translating: check

```bash
python3 scripts/glossary.py check translation.md                    # bilingual file
python3 scripts/glossary.py check translation.md --source source.md # Chinese-only output
```

Two kinds of finding, each with a line number:

1. 禁用: a translation listed as `NOT ...` in the glossary notes appears.
2. 译文未见: an English glossary term appears in the source, but its Chinese is missing from the translation, which usually means a different rendering was used.

Exit 0 means clean. Exit 1 means review each finding: fix real errors; keep wording that fits the context (for example an abbreviation already introduced) and say why.

## Adding terms

Add only verified terms or terms the user has chosen:

```bash
python3 scripts/glossary.py add "estimand" "估计目标（estimand）" "ICH E9(R1) 中文版用语"
python3 scripts/glossary.py lint
```

`add` inserts in sorted order and refuses duplicates. Edit an existing row by hand and give the reason in `notes`. In `notes`, cite the source or write 常用译法，未核规范来源, and record known wrong renderings as `NOT a/b`.

## Files

- `references/glossary.tsv`: main glossary, the standard. Columns `source`, `target` (first-mention form, full-width brackets), `notes`.
- `references/external-medical-translator.tsv`: about 4,000 unverified terms imported from an external list; lookup leads only.
- `scripts/glossary.py`: lookup, check, lint, add.
