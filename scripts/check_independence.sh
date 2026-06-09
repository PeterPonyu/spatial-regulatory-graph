#!/usr/bin/env bash
# Track-local brand-independence gate. Run from this track root.
# It scans executable zones only; docs/manifests may mention reference papers and adapters.
set -euo pipefail

ZONES=""
for z in src tests scripts configs; do [ -d "$z" ] && ZONES="$ZONES $z"; done
if [ -z "$ZONES" ]; then
  echo "PASS: no executable zones yet (skeleton stage)."
  exit 0
fi

PATTERN='3d-?ot|aether-?3d|aether3d|bento|cellniche|contamguard|deepspatial|factorgraph-?st|factorgraphst|foundation-?st-?parity|foundationstparity|gpsfish|harvest|inspire|lumina-?st|luminast|moleculepoint|niche-?lens|nicheflow|nicheformer|nichelens|paneloracle|path2space|pathscope|perturbcausal|sccomm|sceptre|scgpd|scomm|smoppix|spagrn|spaim|spatialperturbseq|spatiotemporal-?niche|spatiotemporalniche|spatrace|stimage|stories|stpainter|vista|xenium_analysis_pipeline'
HITS=$(grep -rilE "$PATTERN" $ZONES   --exclude-dir=__pycache__   --exclude-dir='*.egg-info'   --exclude='check_independence.sh'   --exclude='test_brand_independence.py'   --exclude='results_contract.py' 2>/dev/null || true)

if [ -n "$HITS" ]; then
  echo "FAIL: reference or sibling brand in executable zones ($ZONES):" >&2
  echo "$HITS" >&2
  exit 1
fi
echo "PASS: executable zones are brand-independent ($ZONES)."
