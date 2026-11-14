"""Pure advisory child-model resolution; this module never launches a model."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import tomllib


def _candidates(policy):
    candidates = policy.get('candidates', {})
    allowed = {'t0', 't1', 't2', 't3', 'explorer', 'reviewer', 'diagnostician'}
    if not isinstance(candidates, dict) or set(candidates) - allowed:
        raise ValueError('Invalid candidate table or unsupported candidate fields')
    for value in candidates.values():
        if not isinstance(value, str) or (value != 'inherit' and (
                len(value.split(':')) != 2 or
                any(not part or any(c.isspace() for c in part) for part in value.split(':')))):
            raise ValueError('Candidates must be inherit or explicit model:effort strings')
    return candidates


def _fallback_rules(policy):
    defaults = {'when_model_unavailable': 'inherit_with_disclosure',
                'when_effort_unavailable': 'runtime_default_with_disclosure',
                'when_review_agent_unavailable': 'block_required_review_and_offer_human_review'}
    rules = policy.get('fallback', {})
    if not isinstance(rules, dict) or set(rules) - defaults.keys():
        raise ValueError('Unsupported fallback policy fields')
    result = defaults | rules
    for key, value in result.items():
        allowed = {defaults[key]} | ({'block'} if key != 'when_review_agent_unavailable' else set())
        if not isinstance(value, str) or value not in allowed:
            raise ValueError(f'Unsupported fallback rule: {key}')
    return result


def load_policy(path):
    """Read an operator-selected policy without changing session configuration."""
    policy = tomllib.loads(Path(path).read_text())
    allowed = {'schema', 'selection_mode', 'selected_profile', 'checked_on',
               'budget', 'balanced', 'quality', 'candidates', 'fallback'}
    if set(policy) - allowed or type(policy.get('schema')) is not int or policy['schema'] != 1 or policy.get('selection_mode') != 'advisory':
        raise ValueError('Unsupported advisory policy')
    if 'checked_on' in policy and not isinstance(policy['checked_on'], str):
        raise ValueError('checked_on must be a string')
    for name in ('budget', 'balanced', 'quality'):
        entry = policy.get(name, {})
        if not isinstance(entry, dict):
            raise ValueError('Invalid operator profile table')
        if set(entry) - {'parallel_agents_max', 'review_medium_by_default', 'allow_unverified_fallback'}:
            raise ValueError('Unsupported operator profile fields')
        if type(entry.get('parallel_agents_max')) is not int or not 1 <= entry['parallel_agents_max'] <= 2:
            raise ValueError('Profile worker limit must be between one and two')
        if any(type(entry.get(k)) is not bool for k in ('review_medium_by_default', 'allow_unverified_fallback')):
            raise ValueError('Invalid profile review/fallback flags')
    if policy.get('selected_profile') not in ('budget', 'balanced', 'quality'):
        raise ValueError('Invalid selected profile')
    _fallback_rules(policy)
    _candidates(policy)
    return policy


def delegation_decision(policy=None, *, risk, active_workers=0, material_questions=False,
                        benefit=False, shared_contract_changed=False, weak_failure_evidence=False,
                        uncertain_rollback=False, reviewer_available=True, authorized_worker_limit=None,
                        patch_ready=False):
    """Pure gate used by operator tools; installed guidance applies the same rules.

    No session, agent, model, or user configuration is mutated.
    """
    if risk not in ('LOW', 'MEDIUM', 'HIGH') or type(active_workers) is not int or active_workers < 0:
        raise ValueError('Invalid risk or active worker count')
    profile = policy[policy['selected_profile']] if policy else {}
    limit = profile.get('parallel_agents_max', 2)
    if type(limit) is not int or not 1 <= limit <= 2:
        raise ValueError('Invalid worker limit')
    if authorized_worker_limit is not None:
        if type(authorized_worker_limit) is not int or authorized_worker_limit < 1:
            raise ValueError('Invalid explicitly authorized worker limit')
        limit = authorized_worker_limit
    review = risk == 'HIGH' or (risk == 'MEDIUM' and (
        profile.get('review_medium_by_default', False) or shared_contract_changed
        or weak_failure_evidence or uncertain_rollback))
    mode = ('WAITING_FOR_USER' if material_questions else
            'BLOCKED_REVIEW' if patch_ready and review and not reviewer_available else
            'DELEGATE' if benefit and active_workers < limit else 'DIRECT')
    return {'mode': mode, 'parallel_agents_max': limit, 'review_required': review,
            'review_gate': ('BLOCKED_REVIEW' if review and not reviewer_available else
                            'PENDING' if review else 'NOT_REQUIRED'),
            'worker_launch_allowed': mode == 'DELEGATE'}


@dataclass(frozen=True)
class ModelResolution:
    role: str
    tier: str
    candidate_model: str | None
    candidate_effort: str | None
    requested_model: str | None
    requested_effort: str | None
    observed_model: str | None
    observed_effort: str | None
    state: str
    reason: str

    def to_dict(self):
        return asdict(self)


def _pair(value):
    if not isinstance(value, (tuple, list)) or len(value) != 2 or not all(isinstance(x, str) and x for x in value):
        raise ValueError('Model evidence must be an explicit model/effort pair')
    return tuple(value)


def resolve_child(policy, *, role, tier, catalog=None, override_supported=False,
                  inherited=None, observed=None, required_pair=None,
                  reviewer_available=True, review_required=False):
    """Return a request or disclosed fallback from actual runtime capabilities.

    catalog is an observed collection of (model, effort) pairs, or None when
    unavailable. observed is independent runtime evidence, never disk policy.
    Explicit required_pair forbids substitution. Direct work retains root settings.
    """
    if role not in {'worker', 'explorer', 'cdf_reviewer', 'cdf_diagnostician'} or tier not in {'t0', 't1', 't2', 't3'}:
        raise ValueError('Unsupported role or task tier')
    profile = policy.get('selected_profile', 'balanced')
    if profile not in {'budget', 'balanced', 'quality'} or profile not in policy:
        raise ValueError('Invalid operator profile')
    key = {'worker': tier, 'cdf_reviewer': 'reviewer', 'cdf_diagnostician': 'diagnostician', 'explorer': 'explorer'}[role]
    spec = _candidates(policy).get(key, 'inherit')
    if required_pair is not None:
        pair = _pair(required_pair)
    elif spec == 'inherit':
        pair = None
    else:
        if not isinstance(spec, str) or len(spec.split(':')) != 2 or not all(spec.split(':')):
            raise ValueError('Invalid candidate model:effort')
        pair = tuple(spec.split(':'))
    if pair is not None and (len(pair) != 2 or not all(isinstance(x, str) and x for x in pair)):
        raise ValueError('Invalid required model/effort')
    request = None
    fallback = _fallback_rules(policy)
    obs = _pair(observed) if observed is not None else (None, None)
    inherited = _pair(inherited) if inherited is not None else None
    if catalog is not None:
        if not isinstance(catalog, (list, tuple, set, frozenset)):
            raise ValueError('Catalog must contain observed model/effort pairs')
        catalog = {_pair(entry) for entry in catalog}
    missing_pair_rule = (None if pair is None or (catalog is not None and pair in catalog) else
                         'when_effort_unavailable' if catalog is not None and any(x[0] == pair[0] for x in catalog)
                         else 'when_model_unavailable')
    if not reviewer_available and role == 'cdf_reviewer':
        state = 'unavailable'
        reason = ('Mandatory independent reviewer unavailable: BLOCKED_REVIEW' if review_required
                  else 'Optional reviewer unavailable; no independent review can be claimed')
    elif pair is not None and inherited == pair and obs == pair:
        state, reason = 'confirmed', 'Desired pair confirmed through inherited runtime settings'
    elif pair and override_supported and catalog is not None and pair in catalog:
        request = pair
        if observed is not None and obs != pair:
            state, reason = 'unavailable', 'Observed runtime model differs from the requested pair'
        else:
            state = 'confirmed' if obs == pair else 'requested_unconfirmed'
            reason = 'Runtime confirms request' if state == 'confirmed' else 'Request only; effective model unconfirmed'
    elif required_pair is not None:
        if inherited and tuple(inherited) == pair and obs == pair:
            state, reason = 'confirmed', 'Required pair confirmed through inherited runtime settings'
        else:
            state, reason = 'unavailable', 'Explicit model requirement cannot be verified; substitution forbidden'
    elif missing_pair_rule is not None and fallback[missing_pair_rule] == 'block':
        state, reason = 'unavailable', 'Selected fallback policy blocks unavailable model/effort'
    elif policy[profile].get('allow_unverified_fallback', False):
        state, reason = 'fallback', 'Retain runtime settings; candidate or per-spawn override unavailable/unverified'
    else:
        state, reason = 'unavailable', 'Policy forbids unverified fallback'
    return ModelResolution(role, tier, *(pair or (None, None)), *(request or (None, None)), *obs, state, reason)


def native_profile_plan(path, *, profile=None, capabilities=None, root=None):
    """Render explicit native role candidates; catalog checks are not execution proof."""
    import hashlib
    import json
    from cdf_registry import PROFILE_AGENTS
    source = Path(path).read_bytes()
    data = tomllib.loads(source.decode('utf-8'))
    if (set(data) != {'schema', 'selected_profile', 'fallback', 'profiles'}
            or type(data['schema']) is not int or data['schema'] != 1 or data['fallback'] != 'block'
            or not isinstance(data['profiles'], dict) or set(data['profiles']) != {'budget', 'balanced', 'quality'}):
        raise ValueError('Unsupported native profile policy')
    selected = profile or data['selected_profile']
    if not isinstance(selected, str) or selected not in data['profiles']:
        raise ValueError('Unknown native profile')
    for entry in data['profiles'].values():
        if not isinstance(entry, dict) or set(entry) != set(PROFILE_AGENTS):
            raise ValueError('Native profiles must define exactly the supported CDF roles')
        for candidate in entry.values():
            if not isinstance(candidate, str) or len(candidate.split(':')) != 2 or any(
                    not part or any(char.isspace() for char in part) for part in candidate.split(':')):
                raise ValueError('Native profiles require explicit model:effort pairs')
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    catalog = {tuple(pair) for pair in capabilities['pairs']} if capabilities is not None else None
    roles = {}
    for role, candidate in data['profiles'][selected].items():
        model, effort = candidate.split(':')
        fields = tomllib.loads((root / 'templates' / f'{role}.toml').read_text())
        if (set(fields) != {'name', 'description', 'developer_instructions'} or fields['name'] != role
                or not all(isinstance(value, str) and value for value in fields.values())):
            raise ValueError('Invalid native role template')
        fields.update(model=model, model_reasoning_effort=effort)
        text = '\n'.join(key + ' = ' + json.dumps(value, ensure_ascii=False) for key, value in fields.items()) + '\n'
        state = ('NOT_CHECKED' if catalog is None else
                 'AVAILABLE_ADVERTISED' if (model, effort) in catalog and capabilities['agents_enabled']
                 else 'UNAVAILABLE')
        roles[role] = {'path': f'.codex/agents/{role}.toml', 'content': text,
                       'model_requested': model, 'effort_requested': effort,
                       'model_observed': None, 'effort_observed': None, 'state': state}
    return {'schema': 1, 'profile': selected, 'policy_sha256': hashlib.sha256(source).hexdigest(),
            'roles': roles, 'fallback': 'block', 'native_config_applied': False,
            'runtime_routing': 'NOT_OBSERVED'}
