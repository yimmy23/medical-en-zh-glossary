# medical-en-zh-glossary

医学中英学术翻译术语表，附查询与译文检查工具，可作为 [Agent Skill](https://agentskills.io/specification) 在 Claude Code、Codex 等工具中使用。

An English-Chinese glossary for medical academic translation, focused on thoracic oncology, lung cancer, clinical research methodology and biostatistics, with a small stdlib-only tool to look up terms and check translations. Packaged as an [Agent Skill](https://agentskills.io/specification).

## 为什么需要它

逐词直译容易把专业术语译错，而且整段读起来通顺时不容易发现。例如 confounding by indication 被直译成“指示混杂”，规范写法是“适应证混杂”。本仓库把核实过的译法集中在一张表里：翻译前查表，翻译后自动检查。

## 内容

| 文件 | 说明 |
|---|---|
| `references/glossary.tsv` | 主表，约 60 条核心术语，是标准。每条注明来源或“未核规范来源”，已知错误译法记为 `NOT ×××` |
| `references/external-medical-translator.tsv` | 外部词表 3,983 条，覆盖心血管、泌尿、统计等多个学科，全部标“未核”，只作查询线索 |
| `scripts/glossary.py` | 查询、检查、校验、补录工具，只依赖 Python 3.9+ 标准库 |
| `SKILL.md` | Agent Skill 入口 |
| `tests/` | 单元测试 |

## 安装为 Skill

```bash
git clone https://github.com/yimmy23/medical-en-zh-glossary.git
ln -s "$PWD/medical-en-zh-glossary" ~/.claude/skills/medical-en-zh-glossary   # Claude Code
ln -s "$PWD/medical-en-zh-glossary" ~/.codex/skills/medical-en-zh-glossary    # Codex
```

## 用法

```bash
# 查询：英文或中文都可以，不区分大小写；主表精确命中时不再显示外部表
python3 scripts/glossary.py lookup "confounding by indication"
python3 scripts/glossary.py lookup 永生时间 --all

# 检查译文：双语对照文件直接检查；只有中文的译文用 --source 指定英文原文
python3 scripts/glossary.py check translation.md
python3 scripts/glossary.py check translation.md --source source.md

# 补录核实过的术语（按字母顺序插入，拒绝重复），然后校验整表
python3 scripts/glossary.py add "estimand" "估计目标（estimand）" "ICH E9(R1) 中文版用语"
python3 scripts/glossary.py lint
```

`check` 报告两类问题：

- **禁用**：译文里出现了表中标为 `NOT` 的译法。
- **译文未见**：原文出现了表中的英文术语，译文里却没有对应中文，通常说明用了别的译法。英文匹配不区分大小写，并兼容连字符与空格、英式与美式拼写（-ise/-ize）。

检查只做字符串匹配，结果需要人工判断。退出码：0 无问题，1 有发现，2 输入错误。

## 录入规则

1. 先查表；表外术语先核权威来源：ICH 指导原则中文版、全国科学技术名词审定委员会、人卫版教材、中华医学会系列期刊、CSCO 指南。
2. `notes` 写明来源；查不到权威来源的常用译法写“常用译法，未核规范来源”。
3. 已知错误译法写 `NOT a/b`，`check` 会据此报警。
4. `target` 用首次出现格式：中文全称（英文全称，缩写），全角括号与逗号。
5. 同一英文只保留一行；修改已有条目时在 `notes` 说明原因。外部表不改，核实后的词写进主表。
6. 提交前运行 `python3 scripts/glossary.py lint` 和 `python3 -m unittest discover -s tests`。

## 来源

- 主表：维护者在翻译实践中逐条核对整理，来源写在各条 `notes` 中。
- 外部表：整表导入自 [nian1147/medical-translator](https://github.com/nian1147/medical-translator)（提交 `5aa12f22e305c813068ab2b85b24da7bf1a507be`，`terms.csv` 与 `vocabulary.csv`），去重并统一格式；与主表冲突处以主表为准。
- 检查禁用译法的思路参考 [mylc2010/sci-translation-skill](https://github.com/mylc2010/sci-translation-skill)，代码为本仓库自写。
- Skill 结构遵循 [Agent Skills 规范](https://agentskills.io/specification) 与 [anthropics/skills](https://github.com/anthropics/skills)。

## 许可

[CC0 1.0](LICENSE)：放弃全部权利，可自由使用、修改、再发布，无需署名。

术语表仅供翻译参考，不构成医学建议；正式发表前请按目标期刊与权威规范核对。
