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

## Validation marker

`python -m spatial_regulatory_graph.cli claim-status` reads the committed package marker in `src/spatial_regulatory_graph/validation.py` and prints `validated`. It does not require private governance documents to be present.

## Citations and references

See `BASELINE_REFERENCES.md` for papers, code references, and citation context.
