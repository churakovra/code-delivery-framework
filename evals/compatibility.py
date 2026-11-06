"""Read-only prerequisite checks; availability is not live runtime evidence."""
import os
import shutil


CASE_PREREQUISITES = {
    'G07': ('node',),
    'G08': ('node',),
}


def inspect_case(case, kind, *, platform_name=None, find_executable=None):
    platform_name = os.name if platform_name is None else platform_name
    find_executable = find_executable or shutil.which
    missing = []
    if platform_name != 'posix':
        missing.append('POSIX process and filesystem APIs')
    required = ('git',) + CASE_PREREQUISITES.get(case['id'], ())
    missing.extend(name for name in required if find_executable(name) is None)
    controls = sorted(case.get('runtime_controls', {}))
    return {
        'status': 'UNAVAILABLE' if missing else 'AVAILABLE',
        'missing_prerequisites': missing,
        'required_executables': list(required),
        'required_runtime_controls': controls,
        'native_resume_required': kind == 'codex' and bool(case.get('scripted_answers')),
        'runtime_protocol': 'Codex JSON events and resume' if kind == 'codex' else 'external adapter protocol',
        'runtime_version_validation': 'UNVERIFIED',
        'note': 'Executable presence does not verify version compatibility or actual controls. '
                'No live-supported Codex version is recorded yet; inspect real traces before grading.',
    }
