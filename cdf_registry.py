"""Declarative offline bundle inventory shared by packaging and evaluation."""

CORE = (
    'cdf', 'cdf-backend', 'cdf-code-review', 'cdf-codebase-research', 'cdf-debugging',
    'cdf-documentation', 'cdf-frontend', 'cdf-requirements', 'cdf-ui-design',
    'cdf-verification',
)
# Historical ownership inventory, not an installation selection. Keep these
# names frozen when CORE changes so old manifests and journals remain readable.
LEGACY_CORE_11 = (
    'cdf-backend', 'cdf-code-review', 'cdf-codebase-research', 'cdf-debugging',
    'cdf-documentation', 'cdf-frontend', 'cdf-implementation', 'cdf-orchestration',
    'cdf-planning', 'cdf-requirements', 'cdf-ui-design', 'cdf-verification',
)
EXTRAS = {
    'operator': ('cdf-model-calibration',),
    'learning': ('cdf-explain', 'cdf-teach'),
}
NATIVE_AGENTS = ('cdf_reviewer', 'cdf_diagnostician')
