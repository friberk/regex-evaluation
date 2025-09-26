# Semantic Similarity (EGRET‑based)

This module computes a symmetric, example‑driven semantic similarity between two regexes by:
- Generating test strings from each regex using EGRET (native extension in this folder).
- Reporting overlap of the match sets via F1 (and weighted Fβ), Jaccard, and one‑way diagnostics.

Files
- `regex_semantic_sim.py` — public API and CLI.
- `egret_ext.cpython-3{10,11}-x86_64-linux-gnu.so` — bundled Linux CPython wheels for EGRET integration.
- `__init__.py` — package init.

Platform requirements
- Linux x86_64 with CPython 3.10 or 3.11 (to load `egret_ext.*.so`).
- On macOS/other Pythons, skip this metric (other metrics still work).

API usage
```
from metrics.semantic_similarity.regex_semantic_sim import symmetrical_semantic_similarity

m = symmetrical_semantic_similarity(r"^[a-z]+$", r"[a-z]+", beta=1.0, base_substring="evil")
print(m["f1_matchset"], m["jaccard_matchset"], m["one_way"]["accuracy_mean"])
```
Key outputs (dict):
- `f1_matchset`: 2|A∩B|/(|A|+|B|)
- `f_beta_matchset`: weighted Fβ over set‑precision/recall, `beta` controls tradeoff
- `jaccard_matchset`: |A∩B|/|A∪B|
- `coverage_r1_in_r2`, `coverage_r2_in_r1`
- `one_way`: diagnostic accuracies for r1→r2 and r2→r1 using EGRET strings from the reference
- `cardinalities`: sizes of A, B, A∩B, and union S

CLI
```
python -m metrics.semantic_similarity.regex_semantic_sim \
  "^[a-z]+$" "[a-z]+" --beta 1.0 --base-substring evil --debug
```

Integration with calculate_metrics
- `metrics/calculate_metrics.py --metric semantic_similarity` calls the symmetric API per candidate/ground‑truth pair and stores results in `candidate_regex_metrics.semantic_similarity`.
- Use `--timeout-seconds` to bound per‑item time; EGRET string generation itself is not passed a timeout.

Notes
- EGRET returns alerts followed by a `BEGIN` marker; the module strips alerts and uses subsequent strings.
- `base_substring` (default `evil`) seeds EGRET’s generation; adjust for specific domains if desired.

Troubleshooting
- ImportError on `egret_ext`: ensure Linux CPython 3.10/3.11; otherwise skip this metric.
- Mixed environments: compute this metric on a Linux host and merge results back into your SQLite DB.
