import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('cdf_selection', Path(__file__).resolve().parents[1]/'scripts/framework.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)

class SelectionLifecycleTests(unittest.TestCase):
    def test_routing_receives_profile_without_bundled_model_assignments(self):
        roles={'qa':{'policy':'qa','description':'Verify'}}
        profile={'environment':{'plan':'Plus'},'preferences':{'qa':'luna low'}}
        models=[{'model':'one','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]
        response={'status':'researched','policy':{'qa':{'model':'one','reasoning_effort':'low'}},'explanation':'Fit','sources':['https://example.com'],'alternatives':['Budget','Quality']}
        with patch.object(f,'run_model_routing',return_value=response) as run:
            f.select_policy('codex',models,roles,profile,Path('/bundle'))
        self.assertEqual(run.call_args.args[3], profile)
        self.assertNotIn('model',run.call_args.args[3])

    def test_codex_prompt_contains_profile_and_no_default_policy(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'skills/model-routing').mkdir(parents=True)
            (root/'skills/model-routing/SKILL.md').write_text('routing instructions')
            seen=[]
            def run(args, **kwargs):
                seen.append(kwargs['input'])
                Path(args[args.index('-o')+1]).write_text(json.dumps({'status':'researched','policy':{'qa':{'model':'one','reasoning_effort':'low'}},'explanation':'Fit','sources':['https://example.com'],'alternatives':['Budget']}))
            with patch.object(f.subprocess,'run',side_effect=run):
                f.select_policy('codex',[{'model':'one','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}],{'qa':{'policy':'qa'}},{'environment':{'plan':'Plus'}},root)
            self.assertIn('"plan": "Plus"',seen[0])
            self.assertNotIn('POLICY KEYS AND PRIOR CHOICES',seen[0])
            self.assertNotIn('USER CURRENT POLICY',seen[0])

    def test_selection_report_is_in_installed_payload(self):
        roles={'qa':{'policy':'qa'}}
        selection={'policy':{'qa':{'model':'one','reasoning_effort':'low'}},'explanation':'Fit','sources':['https://example.com'],'alternatives':['Budget','Quality']}
        report=f.selection_report(selection, {'environment':{'plan':'Plus'}})
        self.assertEqual(report['context']['environment']['plan'], 'Plus')
        self.assertEqual(report['alternatives'], ['Budget','Quality'])
        self.assertEqual(report['selection'], selection['policy'])

    def test_proposal_does_not_apply_implicitly(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)
            result=f.model_proposal({'qa':{'model':'one','reasoning_effort':'low'}},{'qa':{'model':'two','reasoning_effort':'low'}},{'reason':'test'}, target, 'hash')
            self.assertEqual(result['current']['qa']['model'],'one')
            self.assertEqual(result['proposed']['qa']['model'],'two')
            self.assertEqual(list(target.iterdir()),[])
