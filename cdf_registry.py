"""Declarative offline bundle inventory shared by packaging and evaluation."""

CORE = (
    'cdf', 'cdf-architecture', 'cdf-backend', 'cdf-code-review', 'cdf-codebase-research', 'cdf-debugging',
    'cdf-documentation', 'cdf-frontend', 'cdf-requirements', 'cdf-ui-design',
    'cdf-verification', 'cdf-testing', 'cdf-explain', 'cdf-teach',
)
# Frozen 2.0.x ownership, before learning/testing became standard.
LEGACY_CORE_20 = (
    'cdf', 'cdf-architecture', 'cdf-backend', 'cdf-code-review', 'cdf-codebase-research', 'cdf-debugging',
    'cdf-documentation', 'cdf-frontend', 'cdf-requirements', 'cdf-ui-design', 'cdf-verification',
)
LEGACY_EXTRAS = {'operator': ('cdf-model-calibration',), 'learning': ('cdf-explain', 'cdf-teach')}
# Frozen 1.2–1.5 inventory, shared by flat and compact historical installs.
LEGACY_CORE_15 = (
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
    'learning': (),  # Deprecated compatibility alias; learning is now standard.
}
NATIVE_AGENTS = ('cdf_reviewer', 'cdf_diagnostician')

# Explicit profile setup; legacy installation retains the original two roles.
PROFILE_AGENTS = ('cdf_explorer', *NATIVE_AGENTS)
