from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .contracts import ClaimGateEvidence, ClaimStatus, evaluate_claim_gate
from .data_paths import processed_data_path

REGULATOR_SEEDS = (
    "FOS", "JUN", "JUNB", "JUND", "STAT1", "STAT3", "RELA", "NFKB1",
    "SOX2", "SOX4", "TBR1", "NEUROD1", "NEUROD2", "EGR1", "EGR2", "MYC",
    "ETS1", "SPI1", "GATA3", "FOXA1", "FOXP2", "PAX6", "BCL11B", "SATB2",
    "RORB", "TCF4", "CUX1", "CUX2",
)


def default_st_path() -> Path:
    return processed_data_path("dlpfc_maynard_2021_visium", "anndata.h5ad")


@dataclass(frozen=True)
class RealSmokeConfig:
    st_path: Path = field(default_factory=default_st_path)
    label_key: str = "ground_truth"
    max_spots: int = 1500
    max_regulators: int = 12
    max_targets: int = 32
    max_gene_scan: int = 4096
    neighbor_count: int = 8
    seed: int = 31

    def validate(self) -> None:
        if self.max_spots < 30:
            raise ValueError("max_spots must be at least 30")
        if self.max_regulators < 1:
            raise ValueError("max_regulators must be positive")
        if self.max_targets < 2:
            raise ValueError("max_targets must be at least two")
        if self.max_gene_scan < self.max_targets:
            raise ValueError("max_gene_scan must be at least max_targets")
        if self.neighbor_count < 2:
            raise ValueError("neighbor_count must be at least two")


@dataclass(frozen=True)
class RealSmokeResult:
    metrics: dict[str, float]
    tier_counts: dict[str, int]
    evidence: ClaimGateEvidence
    edge_rows: tuple[dict[str, object], ...] = ()

    @property
    def claim_status(self) -> ClaimStatus:
        return evaluate_claim_gate(self.evidence)

    def to_jsonable(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "metrics": self.metrics,
            "tier_counts": self.tier_counts,
            "claim_status": self.claim_status.value,
            "missing_claim_evidence": list(self.evidence.missing()),
        }
        if self.edge_rows:
            payload["edge_rows"] = list(self.edge_rows)
        return payload


def _resolve_h5ad(path: str | Path) -> Path:
    resolved = Path(path).expanduser()
    if not resolved.exists():
        raise FileNotFoundError(f"AnnData file does not exist: {resolved}")
    if resolved.suffix != ".h5ad":
        raise ValueError(f"expected a .h5ad file, got: {resolved}")
    return resolved


def _read_h5ad(path: str | Path) -> Any:
    try:
        import anndata as ad  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - depends on optional real-data env
        raise RuntimeError("real-data smoke requires the optional anndata package") from exc
    return ad.read_h5ad(_resolve_h5ad(path), backed="r")


def _close(adata: Any) -> None:
    close = getattr(getattr(adata, "file", None), "close", None)
    if close is not None:
        close()


def _as_numpy(matrix: Any) -> Any:
    import numpy as np

    if hasattr(matrix, "toarray"):
        matrix = matrix.toarray()
    return np.asarray(matrix, dtype=np.float32)


def _sample_indices(total: int, limit: int, seed: int) -> Any:
    import numpy as np

    if total <= limit:
        return np.arange(total, dtype=int)
    rng = np.random.default_rng(seed)
    idx = rng.choice(total, size=limit, replace=False)
    idx.sort()
    return idx


def _safe_corr(left: Any, right: Any) -> float:
    import numpy as np

    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left = left - left.mean()
    right = right - right.mean()
    denom = float(np.sqrt(np.sum(left * left) * np.sum(right * right)))
    return float(np.sum(left * right) / denom) if denom else 0.0


def _smooth_by_coords(values: Any, coords: Any, k: int) -> Any:
    import numpy as np

    coords = np.asarray(coords, dtype=np.float64)
    values = np.asarray(values, dtype=np.float64)
    k = min(max(2, k), len(values))
    try:
        from scipy.spatial import cKDTree  # type: ignore[import-untyped]

        _, idx = cKDTree(coords).query(coords, k=k)
    except Exception:  # pragma: no cover - fallback for minimal envs
        dist = ((coords[:, None, :] - coords[None, :, :]) ** 2).sum(axis=2)
        idx = np.argsort(dist, axis=1)[:, :k]
    return values[idx].mean(axis=1)


def _label_similarity(left: Any, right: Any, labels: Any) -> float:
    import numpy as np

    labels = np.asarray([str(x) for x in labels], dtype=object)
    left_means = []
    right_means = []
    for label in sorted(set(labels)):
        if label.lower() == "nan":
            continue
        mask = labels == label
        if int(mask.sum()) < 2:
            continue
        left_means.append(float(np.mean(left[mask])))
        right_means.append(float(np.mean(right[mask])))
    if len(left_means) < 2:
        return 0.0
    return abs(_safe_corr(left_means, right_means))


def _prior_support(regulator: str, target: str) -> float:
    token = f"{regulator}:{target}"
    return 1.0 if sum(ord(ch) for ch in token) % 5 in {0, 1} else 0.0


def _edge_score(reg: Any, target: Any, coords: Any, labels: Any, prior: float, k: int) -> float:
    expr = abs(_safe_corr(reg, target))
    spatial = abs(_safe_corr(reg, _smooth_by_coords(target, coords, k)))
    label = _label_similarity(reg, target, labels)
    return float(0.50 * expr + 0.30 * spatial + 0.15 * label + 0.05 * prior)


def _select_regulators(var_names: list[str], regulator_matrix: Any, regulator_idx: list[int], max_regulators: int) -> list[int]:
    import numpy as np

    if not regulator_idx:
        raise ValueError("no regulator seed genes found in AnnData var_names")
    variances = regulator_matrix.var(axis=0)
    order = np.argsort(-variances)
    return [int(regulator_idx[int(i)]) for i in order[:max_regulators]]


def _select_targets(adata: Any, rows: Any, regulator_idx: set[int], max_targets: int, max_scan: int) -> list[int]:
    import numpy as np

    scan_count = min(int(adata.n_vars), max_scan)
    scan_idx = np.unique(np.linspace(0, int(adata.n_vars) - 1, scan_count, dtype=int))
    scan_matrix = np.log1p(_as_numpy(adata[rows, scan_idx].X))
    variance = scan_matrix.var(axis=0)
    mean = scan_matrix.mean(axis=0)
    scores = np.where(mean > 0.0, variance, -1.0)
    ranked = np.lexsort((scan_idx, -scores))
    targets: list[int] = []
    for pos in ranked:
        gene_idx = int(scan_idx[int(pos)])
        if gene_idx in regulator_idx or scores[int(pos)] < 0.0:
            continue
        targets.append(gene_idx)
        if len(targets) >= max_targets:
            break
    if len(targets) < 2:
        raise ValueError("not enough target genes selected from expression matrix")
    return targets


def _tier(score: float, survives: bool) -> str:
    if survives and score >= 0.25:
        return "validated"
    if survives or score >= 0.18:
        return "supported"
    return "candidate"


def _control_score_values(
    *,
    reg_vec: Any,
    target_vec: Any,
    coords: Any,
    labels: Any,
    shuffled_coords: Any,
    shuffled_labels: Any,
    shuffled_prior: float,
    prior: float,
    rng: Any,
    k: int,
) -> dict[str, float | bool | str]:
    real = _edge_score(reg_vec, target_vec, coords, labels, prior, k)
    coord_score = _edge_score(reg_vec, target_vec, shuffled_coords, labels, prior, k)
    label_score = _edge_score(reg_vec, target_vec, coords, shuffled_labels, prior, k)
    prior_score = _edge_score(reg_vec, target_vec, coords, labels, shuffled_prior, k)
    cross_target = target_vec.copy()
    rng.shuffle(cross_target)
    cross_score = _edge_score(reg_vec, cross_target, coords, labels, prior, k)
    survives = real > max(coord_score, label_score, prior_score, cross_score)
    return {
        "score": float(real),
        "coordinate_control_score": float(coord_score),
        "label_control_score": float(label_score),
        "prior_control_score": float(prior_score),
        "cross_reference_control_score": float(cross_score),
        "survives_controls": bool(survives),
        "tier": _tier(real, survives),
    }


def _rounded_control_scores(values: dict[str, float | bool | str]) -> dict[str, float | bool | str]:
    return {
        "score": round(float(values["score"]), 6),
        "coordinate_control_score": round(float(values["coordinate_control_score"]), 6),
        "label_control_score": round(float(values["label_control_score"]), 6),
        "prior_control_score": round(float(values["prior_control_score"]), 6),
        "cross_reference_control_score": round(float(values["cross_reference_control_score"]), 6),
        "survives_controls": bool(values["survives_controls"]),
        "tier": str(values["tier"]),
    }


def _control_scores(**kwargs: Any) -> dict[str, float | bool | str]:
    return _rounded_control_scores(_control_score_values(**kwargs))


def evaluate_external_edges(
    edge_rows: list[dict[str, object]] | tuple[dict[str, object], ...],
    config: RealSmokeConfig,
) -> tuple[dict[str, object], ...]:
    """Score externally supplied regulator-target rows under the local controls.

    The input rows are generic edge files from an isolated reference run. This
    function deliberately evaluates only the pair identities against the same
    public-data smoke controls used for local tiers; source scores are preserved
    as provenance fields and never treated as local control-survival evidence.
    """
    import numpy as np

    config.validate()
    adata = _read_h5ad(config.st_path)
    try:
        if "spatial" not in adata.obsm:
            raise KeyError("external-edge evaluation requires obsm['spatial']")
        if config.label_key not in adata.obs:
            raise KeyError(f"external-edge evaluation requires obs[{config.label_key!r}]")
        rows = _sample_indices(int(adata.n_obs), config.max_spots, config.seed)
        labels = adata.obs[config.label_key].iloc[rows].astype(str).to_numpy()
        coords = np.asarray(adata.obsm["spatial"][rows], dtype=np.float64)
        var_names = [str(v) for v in adata.var_names]
        name_to_idx = {name: idx for idx, name in enumerate(var_names)}

        requested_genes = []
        for row in edge_rows:
            requested_genes.extend([str(row.get("regulator", "")), str(row.get("target", ""))])
        selected_idx = sorted({name_to_idx[name] for name in requested_genes if name in name_to_idx})
        matrix = np.log1p(_as_numpy(adata[rows, selected_idx].X)) if selected_idx else np.empty((len(rows), 0))
        pos_by_idx = {idx: pos for pos, idx in enumerate(selected_idx)}

        rng = np.random.default_rng(config.seed)
        shuffled_coords = coords.copy()
        rng.shuffle(shuffled_coords, axis=0)
        shuffled_labels = labels.copy()
        rng.shuffle(shuffled_labels)
        priors = [_prior_support(str(row.get("regulator", "")), str(row.get("target", ""))) for row in edge_rows]
        shuffled_priors = [float(prior) for prior in priors]
        rng.shuffle(shuffled_priors)

        evaluated: list[dict[str, object]] = []
        for idx, row in enumerate(edge_rows):
            reg_name = str(row.get("regulator", ""))
            target_name = str(row.get("target", ""))
            source_rank = row.get("rank", idx + 1)
            source_score = row.get("score", "")
            base = {
                "rank": idx + 1,
                "source_rank": source_rank,
                "regulator": reg_name,
                "target": target_name,
                "reference_score": source_score,
            }
            reg_idx = name_to_idx.get(reg_name)
            target_idx = name_to_idx.get(target_name)
            if reg_idx is None or target_idx is None:
                missing = []
                if reg_idx is None:
                    missing.append("regulator")
                if target_idx is None:
                    missing.append("target")
                evaluated.append(
                    {
                        **base,
                        "score": "",
                        "coordinate_control_score": "",
                        "label_control_score": "",
                        "prior_control_score": "",
                        "cross_reference_control_score": "",
                        "survives_controls": False,
                        "tier": "unmatched",
                        "evaluated": False,
                        "missing_reason": "+".join(missing),
                    }
                )
                continue
            scores = _control_scores(
                reg_vec=matrix[:, pos_by_idx[reg_idx]],
                target_vec=matrix[:, pos_by_idx[target_idx]],
                coords=coords,
                labels=labels,
                shuffled_coords=shuffled_coords,
                shuffled_labels=shuffled_labels,
                shuffled_prior=float(shuffled_priors[idx]),
                prior=float(priors[idx]),
                rng=rng,
                k=config.neighbor_count,
            )
            evaluated.append({**base, **scores, "evaluated": True, "missing_reason": ""})
        return tuple(evaluated)
    finally:
        _close(adata)


def run_real_data_smoke(config: RealSmokeConfig) -> RealSmokeResult:
    import numpy as np

    config.validate()
    adata = _read_h5ad(config.st_path)
    try:
        if "spatial" not in adata.obsm:
            raise KeyError("real-data smoke requires obsm['spatial']")
        if config.label_key not in adata.obs:
            raise KeyError(f"real-data smoke requires obs[{config.label_key!r}]")
        rows = _sample_indices(int(adata.n_obs), config.max_spots, config.seed)
        labels = adata.obs[config.label_key].iloc[rows].astype(str).to_numpy()
        coords = np.asarray(adata.obsm["spatial"][rows], dtype=np.float64)
        var_names = [str(v) for v in adata.var_names]
        name_to_idx = {name: idx for idx, name in enumerate(var_names)}
        regulator_pool = [name_to_idx[name] for name in REGULATOR_SEEDS if name in name_to_idx]
        regulator_matrix = np.log1p(_as_numpy(adata[rows, regulator_pool].X))
        regulator_idx = _select_regulators(var_names, regulator_matrix, regulator_pool, config.max_regulators)
        target_idx = _select_targets(adata, rows, set(regulator_idx), config.max_targets, config.max_gene_scan)
        selected_idx = regulator_idx + target_idx
        matrix = np.log1p(_as_numpy(adata[rows, selected_idx].X))
        reg_pos = {idx: pos for pos, idx in enumerate(selected_idx)}
        target_pos = {idx: pos for pos, idx in enumerate(selected_idx)}

        candidates = []
        for reg_idx in regulator_idx:
            reg_name = var_names[reg_idx]
            reg_vec = matrix[:, reg_pos[reg_idx]]
            for target_idx_item in target_idx:
                target_name = var_names[target_idx_item]
                target_vec = matrix[:, target_pos[target_idx_item]]
                prior = _prior_support(reg_name, target_name)
                real = _edge_score(reg_vec, target_vec, coords, labels, prior, config.neighbor_count)
                candidates.append((real, reg_name, target_name, reg_vec, target_vec, prior))
        candidates.sort(key=lambda item: item[0], reverse=True)
        candidates = candidates[: min(40, len(candidates))]
        if not candidates:
            raise ValueError("no candidate edges were produced")

        rng = np.random.default_rng(config.seed)
        shuffled_coords = coords.copy()
        rng.shuffle(shuffled_coords, axis=0)
        shuffled_labels = labels.copy()
        rng.shuffle(shuffled_labels)
        shuffled_priors = [item[5] for item in candidates]
        rng.shuffle(shuffled_priors)

        coord_deltas: list[float] = []
        label_deltas: list[float] = []
        prior_deltas: list[float] = []
        cross_deltas: list[float] = []
        tier_counts: dict[str, int] = {"candidate": 0, "supported": 0, "validated": 0}
        edge_rows: list[dict[str, object]] = []
        surviving = 0
        for idx, (real, reg_name, target_name, reg_vec, target_vec, prior) in enumerate(candidates):
            scored_raw = _control_score_values(
                reg_vec=reg_vec,
                target_vec=target_vec,
                coords=coords,
                labels=labels,
                shuffled_coords=shuffled_coords,
                shuffled_labels=shuffled_labels,
                shuffled_prior=float(shuffled_priors[idx]),
                prior=prior,
                rng=rng,
                k=config.neighbor_count,
            )
            scored = _rounded_control_scores(scored_raw)
            coord_score = float(scored_raw["coordinate_control_score"])
            label_score = float(scored_raw["label_control_score"])
            prior_score = float(scored_raw["prior_control_score"])
            cross_score = float(scored_raw["cross_reference_control_score"])
            coord_deltas.append(real - coord_score)
            label_deltas.append(real - label_score)
            prior_deltas.append(abs(real - prior_score))
            cross_deltas.append(real - cross_score)
            survives = bool(scored["survives_controls"])
            surviving += int(survives)
            tier = str(scored["tier"])
            tier_counts[tier] += 1
            edge_rows.append(
                {
                    "rank": idx + 1,
                    "regulator": reg_name,
                    "target": target_name,
                    **scored,
                }
            )

        metrics = {
            "sampled_spot_count": float(len(rows)),
            "regulator_count": float(len(regulator_idx)),
            "target_count": float(len(target_idx)),
            "candidate_edge_count": float(len(candidates)),
            "surviving_edge_count": float(surviving),
            "coordinate_shuffle_delta": round(float(np.mean(coord_deltas)), 6),
            "label_shuffle_delta": round(float(np.mean(label_deltas)), 6),
            "prior_shuffle_delta": round(float(np.mean(prior_deltas)), 6),
            "cross_reference_shuffle_delta": round(float(np.mean(cross_deltas)), 6),
            "validated_tier_fraction": round(float(tier_counts["validated"] / len(candidates)), 6),
        }
        return RealSmokeResult(metrics, tier_counts, ClaimGateEvidence(public_data_smoke=True), tuple(edge_rows))
    finally:
        _close(adata)
