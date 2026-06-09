# Spatial Regulatory Graph baseline references

Verification date: 2026-06-07

Detailed per-baseline provenance (paper/code/SHA/gap) for this track lives in:
- `parity_assets.md` (this folder) — the curated baseline + parity asset list;
- `../MANIFEST.tsv` (consolidated paper+code+gap+status manifest for all tracks).

Brand-independence boundary: see `ALLOWED_BASELINE_CONTEXTS.md`. Baselines are used only for
provenance / parity / adapter / metric comparison — never copied into local source or used as branding.

## Primary baseline (cloned for provenance, 2026-06-07)
- SpaGRN — spatial TF-centered GRN/cascade — https://github.com/BGI-Qingdao/SpaGRN
- Local frozen clone: ../../baselines/SpaGRN-original @ 61690ca (gitignored; provenance/parity only, not copied/run).

## Gate-2 baseline_comparison provenance (2026-06-08 real rerun)

| Baseline | Gate-2 status | Evidence |
|---|---|---|
| SpaGRN | `RAN` | Frozen clone `../baselines/SpaGRN-original @ 61690ca` was run in isolated conda prefix `/tmp/nps_gate2_envs/spagrn_py38` with human hg38 cisTarget resources from `../data/resources/cistarget_hg38/`. The wrapper `experiments/gate2_real_baseline/run_reference_baseline.py` emitted generic `baseline_edges.csv` from motif-pruned regulatory-network output: 124,640 adjacency rows, 2,224 modules, 149 regulons, 40 top edges. Local control-evaluation artifact `experiments/gate2_real_baseline/parity_table.json` reports external top-edge survival `0.275` vs local validated-tier survival `1.0`. |

Gate-2 real parity artifact: `experiments/gate2_real_baseline/parity_table.json`.
Earlier local-only artifact retained for audit: `experiments/gate2_baseline_comparison/parity_table.json`.
