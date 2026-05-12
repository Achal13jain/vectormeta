# Changelog

All notable changes to this project will be documented in this file.

## 0.1.0 - 2026-05-12

- Initial MVP package structure.
- Added metadata byte sizing with compact UTF-8 JSON.
- Added scan analysis for oversized metadata records.
- Added JSON and JSONL input support.
- Added fixer that moves heavy metadata fields into JSON sidecars.
- Added hydration from `content_ref` sidecars.
- Added Typer CLI with Rich table output and stable JSON scan output.
- Added tests, examples, docs, and GitHub Actions CI.
