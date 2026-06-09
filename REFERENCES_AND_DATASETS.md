# Spatial Regulatory Graph — references (with code) & datasets

Consolidated reference + dataset index. Verified via the GitHub API / Crossref on
2026-06-09. See `BASELINE_REFERENCES.md` and `parity_assets.md` for the full provenance.

## Reference papers & method baselines (with public code)

| Role | Method | Venue / year | DOI | Code |
|------|--------|--------------|-----|------|
| Primary | SpaGRN — spatial TF-centered gene-regulatory-network / cascade inference | — | — | https://github.com/BGI-Qingdao/SpaGRN |

SpaGRN is the gate-2 `RAN` reference baseline (run in an isolated conda prefix with
human hg38 cisTarget resources). No standalone paper DOI is recorded in the repo.

## Datasets

Runs on user-supplied spatial expression + regulatory priors (no shipped catalog):
- Spatial-omics expression matrices (for candidate regulatory-edge construction).
- cisTarget hg38 motif resources (used by the SpaGRN baseline).

> Verification: SpaGRN repo confirmed live via GitHub API (2026-06-09).
