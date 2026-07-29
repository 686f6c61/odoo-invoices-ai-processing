# Independence audit

Date: 2026-07-29

## Scope

The automated comparison covered 25 implementation files in `ai_processing`
and 35 Python, XML, CSV, HTML or JavaScript files from both the original
third-party addon and the previously adapted addon.

Generated documentation, dependency metadata and generic Odoo framework source
were excluded from the implementation comparison.

## Results

| Check | Result |
|---|---:|
| Identical runs of 30 or more nonblank lines | 0 |
| Longest identical nonblank-line run | 8 lines |
| Longest identical Python token run | 54 tokens |
| Identical Python functions with at least 20 AST nodes | 0 |
| Highest whole-file line ratio, files with at least 10 lines | 0.5882 |

The highest whole-file ratio belongs to `__manifest__.py`, whose structure and
keys are prescribed by Odoo. The longest remaining exact run is schema
boilerplate in `core/contracts.py`; it is below the release threshold and does
not form an identical function.

## Method

- whitespace-only lines were removed before exact-line comparison;
- every new file was compared with every same-extension reference file;
- Python token streams excluded comments, indentation and line separators;
- AST function dumps excluded source locations and only functions of at least
  20 nodes were eligible;
- the exact-run release threshold was 30 nonblank lines.

## Interpretation

The automated evidence found no copied implementation block at the selected
threshold and no identical nontrivial Python function. This supports independent
implementation; it is not a legal opinion or a substitute for provenance and
license review.
