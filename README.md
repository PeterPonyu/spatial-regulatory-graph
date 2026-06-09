# Spatial Regulatory Graph

Spatial Regulatory Graph builds candidate regulatory edges and assigns evidence tiers from expression, prior support, and spatial negative-control survival.

This repository is a conservative public code surface: method implementation, command-line entry points, tests, and the byte-locked results schema. Background citations are listed in `BASELINE_REFERENCES.md`.

## Install

```bash
python -m pip install -e .
```

The lightweight unit tests run without bundled datasets. Real-data commands expect local spatial-omics inputs and expose `--help` for path overrides.

## Command-line usage

```bash
python -m spatial_regulatory_graph.cli smoke-synthetic
python -m spatial_regulatory_graph.cli smoke-real --help
python -m spatial_regulatory_graph.cli gate2-parity --help
python -m spatial_regulatory_graph.cli gate3-analysis --help
python -m spatial_regulatory_graph.cli claim-status
```

Commands emit JSON to stdout. Gate commands also write uniform contract outputs under `results/<project>/` via the vendored `results_contract.py`.

## Evidence-derived status

`python -m spatial_regulatory_graph.cli claim-status` reads `evidence/summary.json`, derives the public claim label from the visible evidence and stated validation bar, and currently prints `preliminary` plus the missing-evidence list. It does not rely on private governance documents or a hardcoded validation constant.

The current public-safe scope is preliminary: the repository includes real gate metrics, but a non-self-referential independent regulon ground truth and a null that collapses the asserted validated set are still required before any public `validated` label.

## Citations and references

See `BASELINE_REFERENCES.md` for papers, code references, and citation context.
