import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('framework_selection', Path(__file__).resolve().parents[1]/'scripts/framework.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)

class SelectionTests(unittest.TestCase):
    def test_selection_uses_skill_and_checks_runtime(self):
        models = [{'model': 'one', 'supportedReasoningEfforts': [{'reasoningEffort':'low'}]}]
        roles = {'qa': {'policy': 'qa'}}
        selection = {'status':'researched', 'policy': {'qa': {'model':'one', 'reasoning_effort':'low'}}, 'explanation':'Provisional.', 'sources':['https://example.org/evidence'],'alternatives':['budget','quality']}
        with patch.object(f, 'run_model_routing', return_value=selection) as run:
            result = f.select_policy('codex', models, roles, {'qa':{}}, Path('/bundle'))
        self.assertEqual(result['policy'], selection['policy'])
        self.assertEqual(run.call_count, 1)

    def test_selection_rejects_missing_or_unavailable_choices(self):
        models = [{'model':'one', 'supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]
        roles = {'qa': {'policy':'qa'}}
        for selection in ({'status':'researched', 'policy':{}, 'explanation':'', 'sources':['https://example.org/evidence'],'alternatives':['budget','quality']}, {'status':'researched', 'policy':{'qa':{'model':'two','reasoning_effort':'low'}}, 'explanation':'unavailable model', 'sources':['https://example.org/evidence'],'alternatives':['budget','quality']}):
            with patch.object(f, 'run_model_routing', return_value=selection), self.assertRaises(f.FrameworkError):
                f.select_policy('codex', models, roles, {'qa':{}}, Path('/bundle'))

    def test_unavailable_research_is_rejected(self):
        result = {'status':'unavailable', 'policy':{'qa':{'model':'one','reasoning_effort':'low'}}, 'explanation':'No research available', 'sources':[]}
        models = [{'model':'one','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]
        with patch.object(f, 'run_model_routing', return_value=result), self.assertRaises(f.FrameworkError):
            f.select_policy('codex', models, {'qa':{'policy':'qa'}}, {'qa':{}}, Path('/bundle'))

    def test_install_does_not_run_model_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp).resolve()/'target'
            target.mkdir()
            roles = {'qa': {'policy':'qa', 'description':'Check evidence'}}
            policy = {'qa': {'model':'one','reasoning_effort':'low'}}
            models = [{'model':'one','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]
            with patch.object(f, 'payload', return_value=({}, b'', policy, roles)), patch.object(f, 'probe', return_value=('test', models)), patch.object(f, 'install', return_value={}) as install, patch.object(f, 'installation_availability', return_value={}), patch.object(f, 'select_policy') as research:
                self.assertEqual(f.main(['install','--target',str(target)]), 0)
                install.assert_called_once()
                research.assert_not_called()
                self.assertEqual(install.call_args.kwargs['selected_policy'], policy)
                self.assertEqual(list(target.iterdir()), [])

    def test_explicit_install_policy_is_applied_without_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp).resolve()
            supplied = target/'policy.toml'
            supplied.write_text('[qa]\nmodel="two"\nreasoning_effort="low"\n')
            roles = {'qa': {'policy':'qa', 'description':'Verify'}}
            defaults = {'qa': {'model':'one','reasoning_effort':'low'}}
            models = [{'model':'two','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]
            with patch.object(f, 'payload', return_value=({},b'',defaults,roles)), patch.object(f, 'probe', return_value=('test',models)), patch.object(f, 'read_manifest', return_value=None), patch.object(f, 'install', return_value={}) as install, patch.object(f, 'installation_availability', return_value={}), patch.object(f, 'select_policy') as research:
                self.assertEqual(f.main(['install','--target',str(target),'--model-policy',str(supplied)]), 0)
            self.assertEqual(install.call_args.kwargs['selected_policy']['qa']['model'], 'two')
            research.assert_not_called()

    def test_unavailable_install_policy_stops_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp).resolve()
            roles = {'qa': {'policy':'qa', 'description':'Verify'}}
            defaults = {'qa': {'model':'one','reasoning_effort':'low'}}
            with patch.object(f, 'payload', return_value=({},b'',defaults,roles)), patch.object(f, 'probe', return_value=('test',[])), patch.object(f, 'install') as install:
                self.assertEqual(f.main(['install','--target',str(target)]), 1)
            install.assert_not_called()
            self.assertEqual(list(target.iterdir()), [])

    def test_welcome_reports_actual_policy_and_activation(self):
        welcome = f.welcome({'qa':{'policy':'qa','description':'Check evidence'}}, {'qa':{'model':'one','reasoning_effort':'low'}})
        self.assertEqual(welcome['models']['qa'], {'model':'one','reasoning_effort':'low'})
        self.assertIn('restart', welcome['activation'].lower())

if __name__ == '__main__': unittest.main()
