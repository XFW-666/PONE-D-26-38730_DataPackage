# Data and code deposit
Manuscript: "Anthropomorphic AI customer service and consumer avoidance intentions: a cross-sectional survey study of serial mediation through uncanny-valley perception and psychological reactance" (PLOS ONE, PONE-D-26-38730 revision).

## Contents
- `public_data.csv` — the analyzed sample (397 rows × 38 columns). All 37 question responses are retained verbatim in their original Chinese response categories so the file can support future secondary research; quasi-identifiers (user IDs, submission timestamps, completion durations, source and source-detail fields, IP addresses) were removed. `case_id` preserves the original export numbering; gaps correspond to the ten records excluded during cleaning (nine with inconsistent self-reported 'under 18' age entries despite adult-only administration, and one fully identical double submission), which are not deposited.
- `data_dictionary.csv` — column descriptions and value codes (Chinese options with English glosses; numeric recoding rule for the 1–7 scales)
- `questionnaire_zh.docx` / `questionnaire_en.docx` — survey instrument (Chinese original; English translation), including the consent page and scenario
- `scenario.docx` — scenario/vignette text (Chinese and English)
- `analysis_from_raw_wjx_export.py` — full analysis pipeline as run on the private master copy (descriptives, CFA, SEM, bootstrap mediation, robustness)
- `model_comparison.py` — serial vs parallel mediation model comparison
- `make_figures.py` — regenerates all manuscript figures (600 dpi PNG)
- `run_from_public_data.py` — self-contained reproduction script (see below)
- `results.json`, `model_comparison.json` — stored outputs reproducing every number in the manuscript
- `figures/` — the 9 multi-panel figure files (consolidated from 12 diagnostics; see `combine_panels.py`)

## Requirements
Python 3.12 with pandas, numpy, scipy, openpyxl, matplotlib, semopy==2.3.11.

## Reproduction
Run `python run_from_public_data.py` in this folder. It recodes the response categories per `data_dictionary.csv` and recomputes every statistic reported in the manuscript (CFA/SEM fit and path coefficients, 5,000-resample bootstrap mediation, Harman single-factor test, single-factor baseline, stimulus checks), writes `results_republished.json`, and prints a consistency check against `results.json` (all checks passed at deposit time). `analysis_from_raw_wjx_export.py` and `model_comparison.py` document the full pipeline as run on the private master export.

## Notes
- Data collected via the Wenjuanxing (WJX) online survey platform, distributed through WeChat links; no monetary compensation.
- Ethics: Science and Technology Ethics Committee of the School of Public Health, Shandong University, approval STEC-SPH-SDU-20251120 (26 Nov 2025).
- Electronic informed consent on the questionnaire's first page.
- License: CC-BY 4.0 (data and code).
