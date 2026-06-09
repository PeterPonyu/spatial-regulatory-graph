from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"test_brand_independence.py", "check_independence.sh", "results_contract.py"}
ZONES = ("src", "tests", "scripts", "configs")


def _term(*parts: str) -> str:
    return "".join(parts).casefold()


FORBIDDEN = {
    _term('3d', '-o', 't'),
    _term('aeth', 'er-3', 'd'),
    _term('aeth', 'er3d'),
    _term('be', 'nt', 'o'),
    _term('cell', 'nich', 'e'),
    _term('conta', 'mguar', 'd'),
    _term('deeps', 'patia', 'l'),
    _term('factorg', 'raph-st'),
    _term('factor', 'graphs', 't'),
    _term('foundation', '-st-parity'),
    _term('foundatio', 'nstparity'),
    _term('gps', 'fis', 'h'),
    _term('har', 'ves', 't'),
    _term('ins', 'pir', 'e'),
    _term('lumi', 'na-s', 't'),
    _term('lumi', 'nast'),
    _term('molecu', 'lepoin', 't'),
    _term('niche', '-lens'),
    _term('nich', 'eflo', 'w'),
    _term('niche', 'forme', 'r'),
    _term('nich', 'elen', 's'),
    _term('panel', 'oracl', 'e'),
    _term('path2', 'space'),
    _term('path', 'scop', 'e'),
    _term('pertur', 'bcausa', 'l'),
    _term('scc', 'omm'),
    _term('sce', 'ptr', 'e'),
    _term('sc', 'gp', 'd'),
    _term('sc', 'om', 'm'),
    _term('smo', 'ppi', 'x'),
    _term('spa', 'grn'),
    _term('sp', 'ai', 'm'),
    _term('spatialp', 'erturbse', 'q'),
    _term('spatiotemp', 'oral-niche'),
    _term('spatiotem', 'poralnich', 'e'),
    _term('spat', 'race'),
    _term('sti', 'mag', 'e'),
    _term('sto', 'rie', 's'),
    _term('stpa', 'inte', 'r'),
    _term('vi', 'st', 'a'),
    _term('xenium_analy', 'sis_pipeline')
}


def test_no_reference_or_sibling_brand_in_executable_zones():
    hits: list[str] = []
    for zone in ZONES:
        zone_path = ROOT / zone
        if not zone_path.exists():
            continue
        for path in zone_path.rglob("*"):
            if not path.is_file() or path.name in EXCLUDED or "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8").casefold()
            except UnicodeDecodeError:
                continue
            for term in FORBIDDEN:
                if term and term in text:
                    hits.append(f"{path.relative_to(ROOT)}:{term}")
    assert hits == []
