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
            limits[entry] = 600 if entry.parent.name == 'delivery' else 250
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
            'no nested launch': 'Only the main agent launches agents',
        }
        for scenario, contract in cases.items():
            with self.subTest(scenario=scenario):
                self.assertIn(contract, delivery)


if __name__ == '__main__':
    unittest.main()
