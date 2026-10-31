"""Static guidance contracts. These checks do not execute model task evaluations."""
import json
from pathlib import Path
import re
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GuidanceContracts(unittest.TestCase):
    def test_entrypoint_word_budgets(self):
        limits = {ROOT / 'templates/AGENTS.md': 300}
        for entry in (ROOT / 'skills').rglob('SKILL.md'):
            if entry.parent.name == 'model-routing':
                continue  # Explicit model research has a separate, on-demand entrypoint.
            limits[entry] = 700 if entry.parent.name == 'delivery' else 250
        for path, limit in limits.items():
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertLessEqual(len(path.read_text().split()), limit)

    def test_external_inventory_contains_only_retained_integration(self):
        inventory = json.loads((ROOT / 'subskills.json').read_text())
        self.assertEqual(inventory['schema'], 2)
        self.assertEqual(set(inventory['subskills']), {'codebase-memory'})
        self.assertEqual(inventory['subskills']['codebase-memory']['kind'], 'mcp-integration')

    def test_helpers_are_bounded_local_resources(self):
        inventory = json.loads((ROOT / 'subskills.json').read_text())
        self.assertTrue(inventory['helpers'])
        paths = []
        for name, helper in inventory['helpers'].items():
            with self.subTest(helper=name):
                path = (ROOT / helper['path']).resolve()
                self.assertTrue(path.is_relative_to(ROOT / 'skills'))
                self.assertEqual(path.suffix, '.md')
                self.assertNotEqual(path.name, 'SKILL.md')
                self.assertTrue(helper['activation'].strip())
                self.assertTrue(path.is_file())
                text = path.read_text()
                self.assertLessEqual(len(text.split()), 400)
                self.assertNotRegex(text, r'(?m)^name:')
                paths.append(path)
        self.assertEqual(len(paths), len(set(paths)))

    def test_role_references_resolve(self):
        inventory = json.loads((ROOT / 'subskills.json').read_text())
        registry = json.loads((ROOT / 'roles.json').read_text())['roles']
        policy = tomllib.loads((ROOT / 'model-policy.toml').read_text())
        available = set(inventory['helpers']) | set(inventory['subskills'])
        self.assertEqual(set(inventory['roles']), set(registry))
        for name, role in registry.items():
            with self.subTest(role=name):
                self.assertIn(role['policy'], policy)
                self.assertTrue(set(inventory['roles'][name]) <= available)
                for skill in role['skills']:
                    self.assertTrue((ROOT / 'skills' / skill / 'SKILL.md').is_file())

    def test_specialist_candidates_have_provenance_routes_and_fallbacks(self):
        inventory = json.loads((ROOT / 'subskills.json').read_text())
        roles = json.loads((ROOT / 'roles.json').read_text())['roles']
        sources = {entry['id'] for entry in json.loads((ROOT / 'sources.json').read_text())['sources']}
        candidates = inventory['specialist_skills']
        self.assertTrue(candidates)
        for name, candidate in candidates.items():
            with self.subTest(candidate=name):
                self.assertTrue(candidate['activation'].strip())
                self.assertTrue(candidate['availability'].strip())
                self.assertTrue(candidate['roles'])
                self.assertTrue(set(candidate['roles']) <= set(roles))
                self.assertIn(candidate['source'], sources)
                fallback = ROOT / 'skills' / candidate['fallback']
                self.assertTrue(fallback.is_file() or (fallback / 'SKILL.md').is_file())
        self.assertIn('diagnosis', candidates['systematic-debugging']['roles'])
        self.assertIn('planner', candidates['grilling']['roles'])
        self.assertIn('reviewer', candidates['react-best-practices']['roles'])

    def test_specialist_routing_is_explicit(self):
        delivery = (ROOT / 'skills/delivery/SKILL.md').read_text()
        routing = (ROOT / 'skills/helpers/specialist-routing.md').read_text()
        self.assertIn('../helpers/specialist-routing.md', delivery)
        self.assertIn('check the runtime skill catalog', routing.lower())
        self.assertIn('Do not install skills automatically', routing)
        self.assertIn('use its listed framework fallback', routing)
        self.assertIn('specialist candidates', delivery)

    def test_local_markdown_references_resolve(self):
        for source in (ROOT / 'skills').rglob('*.md'):
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', source.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                target = target.split('#', 1)[0]
                with self.subTest(source=source.relative_to(ROOT), target=target):
                    self.assertFalse(Path(target).is_absolute())
                    self.assertTrue((source.parent / target).is_file())

    def test_advertised_skill_names_are_unique(self):
        names = []
        for source in (ROOT / 'skills').rglob('SKILL.md'):
            match = re.search(r'(?m)^name:\s*(.+)', source.read_text())
            self.assertIsNotNone(match, str(source))
            names.append(match.group(1).strip())
        self.assertEqual(len(names), len(set(names)))

    def test_task_scenarios_have_conditional_resource_routes(self):
        """Check authored routes; this does not prove a model follows them."""
        cases = {
            'small edit': ('implementation', ('regression-testing',)),
            'bug investigation': ('debugging', ('diagnosis', 'regression-testing')),
            'substantial frontend design': ('interface-design', ('design', 'accessibility')),
            'React interaction': ('frontend-development', ('react', 'accessibility')),
            'independent review': ('code-review', ('verification',)),
        }
        for scenario, (skill, helpers) in cases.items():
            text = (ROOT / 'skills' / skill / 'SKILL.md').read_text()
            with self.subTest(scenario=scenario):
                for helper in helpers:
                    self.assertIn(f'../helpers/{helper}.md', text)
                self.assertIn('only for:', text)

    def test_review_and_escalation_scenarios_are_explicit(self):
        """Protect review conditions in policy text, not simulated execution."""
        delivery = (ROOT / 'skills/delivery/SKILL.md').read_text()
        cases = {
            'small edit stays local': 'Work directly by default',
            'medium and high risk': 'independent review for medium/high risk',
            'four code files': 'more than three changed code files',
            '51 changed lines': 'more than 50 added/deleted code lines',
            'generated and documentation exclusions': 'Exclude generated files and documentation',
            'risk takes precedence': 'Behavioral risk overrides size',
            'review unavailable': 'mark shipping blocked',
            'repeated failure': 'After two failed repairs, obtain independent diagnosis',
            'updated patch review': 'Substantive repairs require updated review',
            'task decomposition': 'Before work, decompose the task',
            'mixed ownership': 'a sequence of role-assigned subagents, or a mix',
            'no nested launch': 'Only the master agent launches agents',
            'continue after partial work': 'A failed approach or partial milestone is not a reason to stop',
            'integrate delegated results': 'Integrate subagent findings',
            'questions and pending work': 'keep dependent work pending',
            'completion or concrete blocker': 'a concrete blocker prevents meaningful authorized progress',
            'compare both active settings': 'compare its runtime-advertised model and reasoning effort with both policy values',
            'record launch evidence': 'distinguish a request from a confirmed active setting',
            'unavailable matching launch': 'treat that delegation as unavailable',
            'substantial interview': 'conduct a short requirements interview',
            'reuse answers': 'use existing user answers and repository evidence',
            'delegation cost': 'expected benefit exceeds coordination and token costs',
        }
        for scenario, contract in cases.items():
            with self.subTest(scenario=scenario):
                self.assertIn(contract, delivery)


if __name__ == '__main__':
    unittest.main()
