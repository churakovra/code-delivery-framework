import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('framework', Path(__file__).resolve().parents[1]/'scripts/framework.py')
f = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(f)

class RootSkillTests(unittest.TestCase):
    def test_root_skill_copies_supporting_files_and_license(self):
        import subprocess
        revision = 'a' * 40
        def run(args, **kwargs):
            if 'rev-parse' in args:
                return subprocess.CompletedProcess(args, 0, stdout=revision + '\n')
            if 'ls-tree' in args:
                if '--full-tree' in args:
                    return subprocess.CompletedProcess(args, 0, stdout=b'100644 blob one\tSKILL.md\0' + b'100644 blob two\treferences/rules.md\0' + b'100644 blob three\tLICENSE\0')
                return subprocess.CompletedProcess(args, 0, stdout=b'100644 blob three\tLICENSE\0')
            if 'cat-file' in args:
                return subprocess.CompletedProcess(args, 0, stdout=args[-1].encode())
            return subprocess.CompletedProcess(args, 0, stdout=b'')
        with patch.object(f.subprocess, 'run', side_effect=run):
            files = f.git_package({'path': '.', 'repository': 'https://github.com/example/skill', 'revision': revision}, '.agents/skills/example', Path('/tmp/example'))
        self.assertEqual(files['.agents/skills/example/SKILL.md'], b'one')
        self.assertEqual(files['.agents/skills/example/references/rules.md'], b'two')
        self.assertEqual(files['.agents/skills/example/UPSTREAM_LICENSE'], b'three')

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()/'bundle'
        self.target = Path(self.tmp.name).resolve()/'project'
        self.target.mkdir()
        (self.root/'skills/test').mkdir(parents=True)
        (self.root/'skills/test/SKILL.md').write_text('---\nname: test\ndescription: test\n---\n')
        (self.root/'skills/model-routing').mkdir()
        (self.root/'skills/model-routing/SKILL.md').write_text('---\nname: model-routing\ndescription: routing\n---\n')
        (self.root/'templates').mkdir()
        (self.root/'templates/AGENTS.md').write_text('Managed instructions\n')
        (self.root/'model-policy.toml').write_text('[qa]\nmodel="test-model"\nreasoning_effort="low"\n')
        (self.root/'roles.json').write_text(json.dumps({'defaults':{'instructions':['Preserve other work.']},'roles':{'qa':{'policy':'qa','skills':['test'],'read_only':True,'description':'Inspect evidence.'}}}))
    def install(self, dry=False):
        return f.install(self.target,dry,self.root)
    def test_install_exposes_role_guidance_for_runtime_policy_routing(self):
        self.install()
        role_path = self.target/'.codex/delivery-framework/roles.json'
        roles = json.loads(role_path.read_text())
        self.assertEqual(roles['qa']['policy'], 'qa')
        self.assertEqual(roles['qa']['skills'], ['test'])
        self.assertEqual(roles['qa']['instructions'], 'Inspect evidence.\nPreserve other work.')
        agent = __import__('tomllib').loads((self.target/'.codex/agents/delivery-qa.toml').read_text())
        self.assertIn('Inspect evidence.\nPreserve other work.', agent['developer_instructions'])
        self.assertTrue(roles['qa']['read_only'])
        self.assertEqual(set(f.status(self.target)['files'].values()), {'clean'})

    def test_framework_skill_is_grouped_and_role_can_find_it(self):
        self.install()
        skill = self.target/'.agents/skills/code-delivery-framework/test/SKILL.md'
        self.assertTrue(skill.is_file())
        self.assertFalse((self.target/'.agents/skills/test/SKILL.md').exists())
        role = __import__('tomllib').loads((self.target/'.codex/agents/delivery-qa.toml').read_text())
        self.assertIn('.agents/skills/code-delivery-framework/test/SKILL.md', role['developer_instructions'])
    def test_round_trip_restores_exact_original(self):
        original = b'User instructions without newline'
        (self.target/'AGENTS.md').write_bytes(original)
        self.install()
        self.assertEqual(set(f.status(self.target)['files'].values()),{'clean'})
        self.assertEqual(f.uninstall(self.target)['state'],'absent')
        self.assertEqual((self.target/'AGENTS.md').read_bytes(),original)
    def test_global_agents_location(self):
        f.install(self.target,root=self.root,global_mode=True)
        self.assertTrue((self.target/'.codex/AGENTS.md').exists())
        self.assertFalse((self.target/'AGENTS.md').exists())
        role=__import__('tomllib').loads((self.target/'.codex/agents/delivery-qa.toml').read_text())
        self.assertIn(str(self.target/'.agents/skills/code-delivery-framework/test/SKILL.md'),role['developer_instructions'])
        f.uninstall(self.target)
        self.assertFalse((self.target/'.codex/AGENTS.md').exists())
    def test_existing_pipeline_requires_migration(self):
        (self.target/'AGENTS.md').write_text('# Delegated delivery workflow\nold rules')
        with self.assertRaises(f.FrameworkError): self.install()
        self.assertFalse((self.target/f.STATE).exists())
    def test_dry_run_no_writes(self):
        self.install(True)
        self.assertEqual(list(self.target.iterdir()),[])
    def test_conflict_preflight_no_partial_writes(self):
        path=self.target/'.codex/agents/delivery-qa.toml'
        path.parent.mkdir(parents=True)
        path.write_text('user config')
        with self.assertRaises(f.FrameworkError): self.install()
        self.assertEqual(path.read_text(),'user config')
        self.assertFalse((self.target/f.STATE).exists())
    def test_dirty_skills_preserved(self):
        self.install()
        skill=self.target/'.agents/skills/code-delivery-framework/test/SKILL.md'
        skill.write_text('user edit')
        self.assertEqual(f.uninstall(self.target)['preserved'],['.agents/skills/code-delivery-framework/test/SKILL.md'])
        self.assertEqual(skill.read_text(),'user edit')
        self.assertEqual(f.status(self.target)['state'],'preserved')
    def test_agents_surrounding_edits_preserved(self):
        self.install()
        agents=self.target/'AGENTS.md'
        agents.write_bytes(b'new prefix\n'+agents.read_bytes()+b'new suffix\n')
        f.uninstall(self.target)
        self.assertEqual(agents.read_bytes(),b'new prefix\nnew suffix\n')
    def test_agents_managed_edits_preserved(self):
        self.install()
        agents=self.target/'AGENTS.md'
        agents.write_text(agents.read_text().replace('Managed','Custom'))
        self.assertIn('AGENTS.md',f.uninstall(self.target)['preserved'])
    def test_partial_install_recoverable(self):
        real=f.atomic
        count=0
        def fail(path,data):
            nonlocal count
            count+=1
            if count==3: raise OSError('injected disk failure')
            return real(path,data)
        with patch.object(f,'atomic',side_effect=fail):
            with self.assertRaises(OSError): self.install()
        self.assertEqual(f.status(self.target)['state'],'installing')
        f.uninstall(self.target)
        self.assertEqual(f.status(self.target)['state'],'absent')
    def test_failed_install_before_agents_write_drops_restored_ownership(self):
        agents=self.target/'AGENTS.md'
        original=b'User original\n'
        agents.write_bytes(original)
        real=f.atomic
        count=0
        def fail(path,data):
            nonlocal count
            count+=1
            if count==2: raise OSError('injected before payload')
            return real(path,data)
        with patch.object(f,'atomic',side_effect=fail):
            with self.assertRaises(OSError): self.install()
        self.assertEqual(f.uninstall(self.target)['state'],'absent')
        self.assertEqual(agents.read_bytes(),original)
        self.install()
    def test_interrupted_uninstall_retry_recognizes_restored_backup(self):
        agents=self.target/'AGENTS.md'
        original=b'User original\n'
        agents.write_bytes(original)
        self.install()
        real=Path.unlink
        def fail(path,*args,**kwargs):
            if path==self.target/f.STATE: raise OSError('injected manifest cleanup failure')
            return real(path,*args,**kwargs)
        with patch.object(Path,'unlink',fail):
            with self.assertRaises(OSError): f.uninstall(self.target)
        self.assertEqual(agents.read_bytes(),original)
        self.assertEqual(f.uninstall(self.target)['state'],'absent')
        self.assertEqual(agents.read_bytes(),original)
    def test_global_path_serialization_special_characters(self):
        target=self.target/'quote"and\\backslash'
        target.mkdir()
        f.install(target,root=self.root,global_mode=True)
        role=__import__('tomllib').loads((target/'.codex/agents/delivery-qa.toml').read_text())
        self.assertIn(str(target/'.agents/skills/code-delivery-framework/test/SKILL.md'),role['developer_instructions'])
    def test_symlink_and_traversal_refused(self):
        (self.target/'.agents').symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(f.FrameworkError): self.install()
        with self.assertRaises(f.FrameworkError): f.safe(self.target,'../outside')
    def test_manifest_traversal_refused(self):
        self.install()
        path=self.target/f.STATE
        data=json.loads(path.read_text()); data['files']['../outside']='x'; path.write_text(json.dumps(data))
        with self.assertRaises(f.FrameworkError): f.uninstall(self.target)
    def test_duplicate_skill_name_different_folder(self):
        path=self.target/'.agents/skills/other/SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_text('---\nname: test\ndescription: duplicate\n---\n')
        with self.assertRaises(f.FrameworkError): self.install()
        self.assertFalse((self.target/f.STATE).exists())
    def test_missing_runtime_explicit(self):
        with self.assertRaises(f.FrameworkError): f.probe('/nonexistent/codex')
    def test_live_probe_protocol_and_model_list(self):
        runtime=Path(self.tmp.name)/'fake-codex'
        runtime.write_text("#!/usr/bin/env python3\nimport sys,json\nif '--version' in sys.argv:\n print('codex-cli 0.163.0');sys.exit()\nif 'exec' in sys.argv:\n sys.stdin.read(); open(sys.argv[sys.argv.index('-o')+1], 'w').write(json.dumps({'status':'researched', 'policy':{'qa':{'model':'test-model','reasoning_effort':'low'}},'explanation':'test selection','sources':['https://example.org/evidence'],'alternatives':['budget','quality']})); sys.exit()\nfor line in sys.stdin:\n request=json.loads(line)\n if 'id' not in request: continue\n result={} if request['method']=='initialize' else {'data':[{'model':'test-model','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}],'nextCursor':None}\n print(json.dumps({'id':request['id'],'result':result}),flush=True)\n")
        runtime.chmod(0o755)
        version,models=f.probe(str(runtime))
        self.assertEqual(version,'codex-cli 0.163.0')
        _,_,policy,roles=f.payload(self.root)
        f.compatibility(policy,roles,models)
        original_payload=f.payload
        with patch.object(f,'payload',side_effect=lambda root=self.root, selected_policy=None: original_payload(self.root, selected_policy)), patch.object(f,'dependency_inventory',return_value=None):
            self.assertEqual(f.main(['validate','--target',str(self.target),'--codex',str(runtime)]),0)
            self.assertEqual(f.main(['install','--dry-run','--target',str(self.target),'--codex',str(runtime)]),0)
            self.assertFalse((self.target/f.STATE).exists())
            self.assertEqual(f.main(['install','--target',str(self.target),'--codex',str(runtime)]),0)
            agent = __import__('tomllib').loads((self.target/'.codex/agents/delivery-qa.toml').read_text())
            self.assertEqual((agent['model'], agent['model_reasoning_effort']), ('test-model', 'low'))
            self.assertEqual(f.main(['status','--target',str(self.target)]),0)
            self.assertEqual(f.main(['uninstall','--dry-run','--target',str(self.target)]),0)
            self.assertTrue((self.target/f.STATE).exists())
            self.assertEqual(f.main(['uninstall','--target',str(self.target)]),0)
            self.assertFalse((self.target/f.STATE).exists())
    def test_missing_models_and_effort_explicit(self):
        _,_,policy,roles=f.payload(self.root)
        with self.assertRaises(f.FrameworkError): f.compatibility(policy,roles,[])
        with self.assertRaises(f.FrameworkError): f.compatibility(policy,roles,[{'model':'test-model','supportedReasoningEfforts':[{'reasoningEffort':'high'}]}])
    def test_global_boundary(self):
        self.assertEqual(f.main(['install','--target',str(self.target),'--home',str(self.target)]),1)
        self.assertEqual(f.main(['install','--global','--target',str(self.target),'--home',str(self.root)]),1)
    def test_offline_cannot_install(self):
        self.assertEqual(f.main(['install','--offline','--target',str(self.target)]),1)
    def test_missing_skill_blocked(self):
        (self.root/'skills/test/SKILL.md').unlink()
        with self.assertRaises(f.FrameworkError): self.install()

class DependencyInstallerTests(InstallerTests):
    def setUp(self):
        super().setUp()
        self.inventory = {'schema':1, 'subskills': {
            'codebase-memory': {'kind':'mcp-integration','repository':'https://github.com/test/cbm','revision':'a'*40,'activation':'when tracing'},
            'demo': {'kind':'skill','repository':'https://github.com/test/skills','revision':'b'*40,'path':'skills/demo','activation':'when relevant'}},
            'roles': {'qa':['codebase-memory','demo']}}
        self.skill = b'---\nname: demo\ndescription: demo\n---\n'
        self.cbm_skill = b'---\nname: codebase-memory\ndescription: graph\n---\n'
        self.binary_name = 'codebase-memory-mcp.exe' if __import__('platform').system().lower() == 'windows' else 'codebase-memory-mcp'
        self.binary = b'#!/bin/sh\necho test\n'
        self.package = {'.agents/skills/demo/SKILL.md':self.skill,
                        '.agents/skills/demo/support.txt':b'support',
                        '.agents/skills/codebase-memory/SKILL.md':self.cbm_skill,
                        '.codex/delivery-framework/bin/'+self.binary_name:self.binary}
        self.versions = {name:{'kind': spec['kind'], 'revision':spec['revision']} for name,spec in self.inventory['subskills'].items()}
    def enable(self):
        (self.root/'subskills.json').write_text(json.dumps(self.inventory))
        return patch.object(f,'fetch_dependencies',return_value=(dict(self.package),dict(self.versions)))
    @unittest.skipIf(__import__('os').name == 'nt', 'Unix executable permissions')
    def test_install_refuses_nonexecutable_identical_user_binary(self):
        binary = self.target/'.codex/delivery-framework/bin'/self.binary_name
        binary.parent.mkdir(parents=True)
        binary.write_bytes(self.binary)
        binary.chmod(0o644)
        with self.enable(), self.assertRaisesRegex(f.FrameworkError, 'not executable'):
            self.install()
        self.assertEqual(binary.read_bytes(), self.binary)
        self.assertFalse((self.target/f.STATE).exists())

    @unittest.skipIf(__import__('os').name == 'nt', 'Unix executable permissions')
    def test_status_detects_reused_binary_losing_executable_permission(self):
        binary = self.target/'.codex/delivery-framework/bin'/self.binary_name
        binary.parent.mkdir(parents=True)
        binary.write_bytes(self.binary)
        binary.chmod(0o755)
        with self.enable(): self.install()
        binary.chmod(0o644)
        name = str(binary.relative_to(self.target))
        self.assertEqual(f.status(self.target)['reused'][name], 'not-executable')

    def test_upgrade_moves_legacy_framework_skill_and_keeps_subskills(self):
        real_payload = f.payload
        def legacy_payload(root):
            files, block, policy, roles = real_payload(root)
            files = {name.replace('.agents/skills/code-delivery-framework/', '.agents/skills/'):
                     content.replace(b'.agents/skills/code-delivery-framework/', b'.agents/skills/')
                     for name, content in files.items()}
            return files, block, policy, roles
        with self.enable(), patch.object(f, 'payload', side_effect=legacy_payload):
            self.install()
        self.assertTrue((self.target/'.agents/skills/test/SKILL.md').is_file())
        with self.enable():
            f.install_with_dependencies(self.target, root=self.root, upgrade=True)
        self.assertFalse((self.target/'.agents/skills/test/SKILL.md').exists())
        self.assertTrue((self.target/'.agents/skills/code-delivery-framework/test/SKILL.md').is_file())
        self.assertEqual((self.target/'.agents/skills/demo/SKILL.md').read_bytes(), self.skill)
        self.assertEqual(set(f.status(self.target)['files'].values()), {'clean'})
        self.assertEqual(f.uninstall(self.target)['state'], 'absent')
    def test_sync_models_applies_edited_policy_and_preserves_role_instructions(self):
        import tomllib
        with self.enable(): self.install()
        policy = self.target/'.codex/delivery-framework/model-policy.toml'
        agent = self.target/'.codex/agents/delivery-qa.toml'
        before = tomllib.loads(agent.read_text())
        policy.write_text('[qa]\nmodel="new-model"\nreasoning_effort="medium"\n')
        models = [{'model':'new-model','supportedReasoningEfforts':[{'reasoningEffort':'medium'}]}]
        f.sync_models(self.target, {'qa': {'policy':'qa'}}, models)
        after = tomllib.loads(agent.read_text())
        self.assertEqual(after['model'], 'new-model')
        self.assertEqual(after['model_reasoning_effort'], 'medium')
        self.assertEqual(after['developer_instructions'], before['developer_instructions'])
        self.assertEqual(set(f.status(self.target)['files'].values()), {'clean'})

    def test_sync_models_refuses_invalid_policy_and_modified_agent(self):
        with self.enable(): self.install()
        policy = self.target/'.codex/delivery-framework/model-policy.toml'
        agent = self.target/'.codex/agents/delivery-qa.toml'
        original = agent.read_bytes()
        roles = {'qa': {'policy':'qa'}}
        models = [{'model':'test-model','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]
        policy.write_text('[qa]\nmodel="missing"\nreasoning_effort="low"\n')
        with self.assertRaisesRegex(f.FrameworkError, 'Unavailable model'):
            f.sync_models(self.target, roles, models)
        self.assertEqual(agent.read_bytes(), original)
        policy.write_text('[qa]\nmodel="test-model"\nreasoning_effort="low"\n')
        agent.write_bytes(original+b'# user edit\n')
        with self.assertRaisesRegex(f.FrameworkError, 'Modified managed file'):
            f.sync_models(self.target, roles, models)
        self.assertEqual(agent.read_bytes(), original+b'# user edit\n')

    def test_sync_models_recovers_interrupted_transaction(self):
        with self.enable(): self.install()
        policy = self.target/'.codex/delivery-framework/model-policy.toml'
        policy.write_text('[qa]\nmodel="new-model"\nreasoning_effort="medium"\n')
        original = policy.read_bytes()
        agent = self.target/'.codex/agents/delivery-qa.toml'
        agent_before = agent.read_bytes()
        atomic = f.atomic
        def interrupt(path, data):
            if path == agent: raise KeyboardInterrupt()
            return atomic(path, data)
        with patch.object(f, 'atomic', side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            f.sync_models(self.target, {'qa': {'policy':'qa'}}, [{'model':'new-model','supportedReasoningEfforts':[{'reasoningEffort':'medium'}]}])
        self.assertEqual(f.status(self.target)['state'], 'recovery-required')
        f.recover(self.target)
        self.assertEqual(policy.read_bytes(), original)
        self.assertEqual(agent.read_bytes(), agent_before)

    def test_sync_models_detects_concurrent_policy_edit_and_allows_upgrade(self):
        with self.enable(): self.install()
        policy = self.target/'.codex/delivery-framework/model-policy.toml'
        policy.write_text('[qa]\nmodel="test-model"\nreasoning_effort="low"\n[demanding_implementation]\nmodel="old"\nreasoning_effort="low"\n')
        roles = {'qa': {'policy':'qa'}}
        models = [{'model':'test-model','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]
        original = policy.read_bytes()
        transaction = f.transaction
        def concurrent(target, operations, expected):
            policy.write_bytes(original+b'# concurrent\n')
            return transaction(target, operations, expected)
        with patch.object(f, 'transaction', side_effect=concurrent), self.assertRaisesRegex(f.FrameworkError, 'File changed during installation'):
            f.sync_models(self.target, roles, models)
        self.assertEqual(policy.read_bytes(), original+b'# concurrent\n')
        policy.write_bytes(original)
        f.sync_models(self.target, roles, models)
        with self.enable():
            f.install_with_dependencies(self.target, root=self.root, upgrade=True, selected_policy=__import__('tomllib').loads(policy.read_text()))
        self.assertEqual(set(f.status(self.target)['files'].values()), {'clean'})

    def test_apply_proposal_is_transactional_and_preserves_instructions(self):
        import tomllib
        with self.enable(): self.install()
        policy_path = self.target/'.codex/delivery-framework/model-policy.toml'
        agent_path = self.target/'.codex/agents/delivery-qa.toml'
        current = tomllib.loads(policy_path.read_text())
        before = tomllib.loads(agent_path.read_text())
        selected = {'qa': {'model':'new-model','reasoning_effort':'medium'}}
        report = {'selection':selected, 'explanation':'evidence'}
        proposal = f.model_proposal(current,selected,report,self.target,f.digest((self.target/f.STATE).read_bytes()))
        models = [{'model':'new-model','supportedReasoningEfforts':[{'reasoningEffort':'medium'}]}]
        roles = {'qa': {'policy':'qa','description':'QA'}}
        f.apply_model_proposal(self.target,roles,models,proposal)
        after = tomllib.loads(agent_path.read_text())
        self.assertEqual(after['model'],'new-model')
        self.assertEqual(after['developer_instructions'],before['developer_instructions'])
        self.assertEqual(json.loads((self.target/'.codex/delivery-framework/model-selection.json').read_text()),report)
        self.assertEqual(set(f.status(self.target)['files'].values()),{'clean'})
        with self.enable(): f.install_with_dependencies(self.target,root=self.root,upgrade=True,selected_policy=selected)
        self.assertEqual(json.loads((self.target/'.codex/delivery-framework/model-selection.json').read_text()),report)
        agent_path.write_text(agent_path.read_text()+'# user edit\n')
        next_proposal = f.model_proposal(selected,selected,report,self.target,f.digest((self.target/f.STATE).read_bytes()))
        with self.assertRaisesRegex(f.FrameworkError,'Modified managed file'):
            f.apply_model_proposal(self.target,roles,models,next_proposal)
        self.assertIn('# user edit',agent_path.read_text())

    def test_apply_proposal_refuses_concurrent_agent_and_manifest_edits(self):
        import tomllib
        with self.enable(): self.install()
        roles={'qa':{'policy':'qa','description':'QA'}}
        models=[{'model':'test-model','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]
        policy=tomllib.loads((self.target/'.codex/delivery-framework/model-policy.toml').read_text())
        proposal=f.model_proposal(policy,policy,{'selection':policy},self.target,f.digest((self.target/f.STATE).read_bytes()))
        real_transaction=f.transaction
        for name in ('.codex/agents/delivery-qa.toml', f.STATE):
            path=self.target/name
            original=path.read_bytes()
            def concurrent(target,operations,expected=None):
                path.write_bytes(original+b' ')
                return real_transaction(target,operations,expected)
            with patch.object(f,'transaction',side_effect=concurrent), self.assertRaisesRegex(f.FrameworkError,'File changed during installation'):
                f.apply_model_proposal(self.target,roles,models,proposal)
            self.assertEqual(path.read_bytes(),original+b' ')
            path.write_bytes(original)

    def test_apply_proposal_rejects_stale_target_and_recovers_interruption(self):
        import tomllib
        with self.enable(): self.install()
        roles={'qa':{'policy':'qa','description':'QA'}}
        models=[{'model':'test-model','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]
        policy=tomllib.loads((self.target/'.codex/delivery-framework/model-policy.toml').read_text())
        proposal=f.model_proposal(policy,policy,{'selection':policy},self.target,f.digest((self.target/f.STATE).read_bytes()))
        stale=dict(proposal, target=str(self.target/'other'))
        with self.assertRaisesRegex(f.FrameworkError,'stale or belongs'):
            f.apply_model_proposal(self.target,roles,models,stale)
        original_manifest=(self.target/f.STATE).read_bytes()
        original_atomic=f.atomic
        def interrupt(path,data):
            if path == self.target/'.codex/agents/delivery-qa.toml': raise KeyboardInterrupt()
            return original_atomic(path,data)
        with patch.object(f,'atomic',side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            f.apply_model_proposal(self.target,roles,models,proposal)
        self.assertEqual(f.status(self.target)['state'],'recovery-required')
        self.assertEqual(f.recover(self.target)['state'],'recovered')
        self.assertEqual((self.target/f.STATE).read_bytes(),original_manifest)
        self.assertEqual(set(f.status(self.target)['files'].values()),{'clean'})

    def test_apply_proposal_rejects_extra_policy_fields(self):
        import tomllib
        with self.enable(): self.install()
        policy=tomllib.loads((self.target/'.codex/delivery-framework/model-policy.toml').read_text())
        selected={'qa':dict(policy['qa'], extra='ignored')}
        with self.assertRaisesRegex(f.FrameworkError,'Invalid proposed role policy'):
            f.apply_model_proposal(self.target,{'qa':{'policy':'qa','description':'QA'}},[{'model':'test-model','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}],f.model_proposal(policy,selected,{'selection':selected},self.target,f.digest((self.target/f.STATE).read_bytes())))

    def test_upgrade_retains_selected_policy_and_blocks_edits(self):
        selected = {'qa': {'model': 'selected-model', 'reasoning_effort': 'low'}}
        with self.enable():
            f.install_with_dependencies(self.target, root=self.root, selected_policy=selected)
        with self.enable():
            f.install_with_dependencies(self.target, root=self.root, upgrade=True, selected_policy=selected)
        agent = __import__('tomllib').loads((self.target/'.codex/agents/delivery-qa.toml').read_text())
        self.assertEqual(agent['model'], 'selected-model')
        policy_path = self.target/'.codex/delivery-framework/model-policy.toml'
        policy_path.write_text(policy_path.read_text() + '# user edit\n')
        with self.enable(), self.assertRaisesRegex(f.FrameworkError, 'Modified managed file'):
            f.install_with_dependencies(self.target, root=self.root, upgrade=True, selected_policy=selected)
        self.assertIn('# user edit', policy_path.read_text())

    def test_project_install_status_uninstall_and_config_preservation(self):
        config=self.target/'.codex/config.toml'
        config.parent.mkdir(parents=True)
        original=b'model = "user-model"\n'
        config.write_bytes(original)
        with self.enable():
            result=self.install()
        self.assertEqual(result['state'],'installed')
        role=__import__('tomllib').loads((self.target/'.codex/agents/delivery-qa.toml').read_text())
        self.assertIn('when relevant',role['developer_instructions'])
        self.assertIn('.agents/skills/demo/SKILL.md',role['developer_instructions'])
        self.assertEqual((self.target/'.agents/skills/demo/support.txt').read_bytes(),b'support')
        self.assertTrue(__import__('os').access(self.target/'.codex/delivery-framework/bin'/self.binary_name,__import__('os').X_OK))
        self.assertEqual(set(f.status(self.target)['files'].values()),{'clean'})
        self.assertEqual(f.uninstall(self.target)['state'],'absent')
        self.assertEqual(config.read_bytes(),original)
    def test_schema_one_upgrade_restores_existing_config(self):
        config=self.target/'.codex/config.toml'; config.parent.mkdir(parents=True)
        original=b'[desktop]\nappearance = "dark"\n'; config.write_bytes(original)
        self.install()
        with self.enable():
            f.install_with_dependencies(self.target,root=self.root,upgrade=True)
        self.assertEqual(f.status(self.target)['state'],'installed')
        f.uninstall(self.target)
        self.assertEqual(config.read_bytes(),original)
    def test_interrupted_upgrade_recovery_restores_prior_files(self):
        self.install()
        old=(self.target/f.STATE).read_bytes()
        original_atomic=f.atomic
        def interrupt(path,data):
            if path == self.target/'.codex/config.toml': raise KeyboardInterrupt()
            return original_atomic(path,data)
        with self.enable(), patch.object(f,'atomic',side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                f.install_with_dependencies(self.target,root=self.root,upgrade=True)
        self.assertEqual(f.status(self.target)['state'],'recovery-required')
        self.assertEqual(f.recover(self.target)['state'],'recovered')
        self.assertEqual((self.target/f.STATE).read_bytes(),old)
        self.assertEqual(set(f.status(self.target)['files'].values()),{'clean'})
    def test_prejournal_interruption_recover(self):
        directory=self.target/'.codex/delivery-framework/transaction'; directory.mkdir(parents=True)
        (directory/'0.bak').write_bytes(b'not applied')
        (directory/'.delivery-partial').write_bytes(b'partial')
        self.assertEqual(f.recover(self.target)['state'],'recovered')
        self.assertFalse(directory.exists())

    def test_transaction_preserves_edit_during_snapshot_read(self):
        path = self.target/'user.txt'
        path.write_bytes(b'original')
        original_read = Path.read_bytes
        changed = False
        def read_and_edit(current):
            nonlocal changed
            data = original_read(current)
            if current == path and not changed:
                changed = True
                path.write_bytes(b'concurrent edit')
            return data
        with patch.object(Path, 'read_bytes', read_and_edit), self.assertRaises(f.FrameworkError):
            f.transaction(self.target, {'user.txt': b'replacement'}, {'user.txt': f.digest(b'original')})
        self.assertEqual(path.read_bytes(), b'concurrent edit')

    def test_concurrent_edit_between_preflight_and_transaction_is_preserved(self):
        agents=self.target/'AGENTS.md'; agents.write_text('original instructions\n')
        real_transaction=f.transaction
        def concurrent_edit(target, operations, expected=None):
            agents.write_text('concurrent user instructions\n')
            return real_transaction(target, operations, expected)
        with self.enable(), patch.object(f,'transaction',side_effect=concurrent_edit):
            with self.assertRaisesRegex(f.FrameworkError,'File changed during installation'):
                self.install()
        self.assertEqual(agents.read_text(),'concurrent user instructions\n')
        self.assertFalse((self.target/f.STATE).exists())
    def test_fetch_failure_leaves_existing_installation_unchanged(self):
        self.install(); before=(self.target/f.STATE).read_bytes()
        (self.root/'subskills.json').write_text(json.dumps(self.inventory))
        with patch.object(f,'fetch_dependencies',side_effect=f.FrameworkError('network')):
            with self.assertRaises(f.FrameworkError): f.install_with_dependencies(self.target,root=self.root,upgrade=True)
        self.assertEqual((self.target/f.STATE).read_bytes(),before)
        self.assertEqual(set(f.status(self.target)['files'].values()),{'clean'})
    def test_reuse_compatible_user_owned_mcp_and_skill(self):
        command=self.target/'existing-cbm'; command.write_bytes(self.binary); command.chmod(0o755)
        config=self.target/'.codex/config.toml'; config.parent.mkdir(parents=True)
        original=('[mcp_servers.codebase-memory-mcp]\ncommand = '+json.dumps(str(command))+'\nargs = []\n').encode()
        config.write_bytes(original)
        folder=self.target/'.codex/skills/demo'; folder.mkdir(parents=True)
        (folder/'SKILL.md').write_bytes(self.skill); (folder/'support.txt').write_bytes(b'support')
        with self.enable(): self.install()
        self.assertEqual(config.read_bytes(),original)
        role=__import__('tomllib').loads((self.target/'.codex/agents/delivery-qa.toml').read_text())
        self.assertIn(str(folder/'SKILL.md'),role['developer_instructions'])
        self.assertEqual(f.status(self.target)['external_mcp'],'clean')
        f.uninstall(self.target)
        self.assertEqual(config.read_bytes(),original)
        self.assertTrue(command.exists()); self.assertTrue((folder/'SKILL.md').exists())
    def test_incompatible_user_mcp_blocks_before_target_changes(self):
        command=self.target/'existing-cbm'; command.write_bytes(b'different')
        config=self.target/'.codex/config.toml'; config.parent.mkdir(parents=True)
        config.write_text('[mcp_servers.codebase-memory-mcp]\ncommand = '+json.dumps(str(command))+'\n')
        with self.enable(), self.assertRaises(f.FrameworkError): self.install()
        self.assertFalse((self.target/f.STATE).exists())
        self.assertEqual(command.read_bytes(),b'different')
    def test_disabled_or_nonexecutable_user_mcp_blocks(self):
        command=self.target/'existing-cbm'; command.write_bytes(self.binary); command.chmod(0o755)
        config=self.target/'.codex/config.toml'; config.parent.mkdir(parents=True)
        config.write_text('[mcp_servers.codebase-memory-mcp]\ncommand = '+json.dumps(str(command))+'\nenabled = false\n')
        with self.enable(), self.assertRaises(f.FrameworkError): self.install()
        config.write_text('[mcp_servers.codebase-memory-mcp]\ncommand = '+json.dumps(str(command))+'\n')
        command.chmod(0o600)
        with self.enable(), self.assertRaises(f.FrameworkError): self.install()
        self.assertFalse((self.target/f.STATE).exists())
    def test_dry_run_does_not_fetch_or_write(self):
        (self.root/'subskills.json').write_text(json.dumps(self.inventory))
        with patch.object(f,'fetch_dependencies',side_effect=AssertionError('must not fetch')):
            result=self.install(True)
        self.assertTrue(result['dry_run'])
        self.assertEqual(list(self.target.iterdir()),[])
    def test_bad_pinned_archive_is_rejected(self):
        from io import BytesIO
        spec={'release':'v0.12.1'}
        with patch.object(f.urllib.request,'urlopen',return_value=BytesIO(b'bad')):
            with self.assertRaisesRegex(f.FrameworkError,'checksum'): f.fetch_codebase_memory(spec,self.target/'scratch')
        self.assertFalse((self.target/'scratch').exists())
    def test_recovery_does_not_overwrite_user_change(self):
        self.install()
        original_atomic=f.atomic
        def interrupt(path,data):
            if path == self.target/'.codex/config.toml': raise KeyboardInterrupt()
            return original_atomic(path,data)
        with self.enable(), patch.object(f,'atomic',side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt): f.install_with_dependencies(self.target,root=self.root,upgrade=True)
        agents=self.target/'AGENTS.md'; agents.write_text('user edit after interruption')
        with self.assertRaisesRegex(f.FrameworkError,'File changed during recovery'): f.recover(self.target)
        self.assertEqual(agents.read_text(),'user edit after interruption')
        self.assertEqual(f.status(self.target)['state'],'recovery-required')
    def test_modified_config_surrounding_owned_block_preserved(self):
        with self.enable(): self.install()
        config=self.target/'.codex/config.toml'
        config.write_bytes(b'# user prefix\n'+config.read_bytes()+b'\n# user suffix\n')
        f.uninstall(self.target)
        self.assertEqual(config.read_bytes(),b'# user prefix\n\n# user suffix\n')

    def test_user_edits_after_install_survive_upgrade_and_uninstall(self):
        with self.enable(): self.install()
        agents=self.target/'AGENTS.md'
        config=self.target/'.codex/config.toml'
        agents.write_bytes(b'# user instructions\n'+agents.read_bytes())
        config.write_bytes(b'# user config\n'+config.read_bytes())
        with self.enable(): f.install_with_dependencies(self.target,root=self.root,upgrade=True)
        f.uninstall(self.target)
        self.assertEqual(agents.read_bytes(),b'# user instructions\n')
        self.assertEqual(config.read_bytes(),b'# user config\n')

    def test_uninstall_restores_exact_no_newline_originals(self):
        agents=self.target/'AGENTS.md'; agents.write_bytes(b'User original without newline')
        config=self.target/'.codex/config.toml'; config.parent.mkdir(parents=True)
        config.write_bytes(b'model = "x"')
        with self.enable(): self.install()
        f.uninstall(self.target)
        self.assertEqual(agents.read_bytes(),b'User original without newline')
        self.assertEqual(config.read_bytes(),b'model = "x"')

    def test_concurrent_edits_before_uninstall_transaction_are_preserved(self):
        with self.enable(): self.install()
        agents=self.target/'AGENTS.md'; config=self.target/'.codex/config.toml'
        real_transaction=f.transaction
        def concurrent_edit(target, operations, expected=None):
            agents.write_bytes(agents.read_bytes()+b'concurrent user guidance\n')
            config.write_bytes(config.read_bytes()+b'# concurrent user setting\n')
            return real_transaction(target,operations,expected)
        with patch.object(f,'transaction',side_effect=concurrent_edit):
            with self.assertRaisesRegex(f.FrameworkError,'File changed during installation'):
                f.uninstall(self.target)
        self.assertIn(b'concurrent user guidance',agents.read_bytes())
        self.assertIn(b'# concurrent user setting',config.read_bytes())
        self.assertTrue((self.target/f.STATE).exists())

    def test_upgrade_uninstall_restores_exact_no_newline_originals(self):
        agents=self.target/'AGENTS.md'; agents.write_bytes(b'User original without newline')
        config=self.target/'.codex/config.toml'; config.parent.mkdir(parents=True)
        config.write_bytes(b'model = "x"')
        with self.enable(): self.install()
        with self.enable(): f.install_with_dependencies(self.target,root=self.root,upgrade=True)
        f.uninstall(self.target)
        self.assertEqual(agents.read_bytes(),b'User original without newline')
        self.assertEqual(config.read_bytes(),b'model = "x"')
    def test_installed_binary_missing_execute_bit_is_unhealthy(self):
        with self.enable(): self.install()
        name='.codex/delivery-framework/bin/'+self.binary_name
        (self.target/name).chmod(0o600)
        self.assertEqual(f.status(self.target)['files'][name],'not-executable')

if __name__=='__main__': unittest.main()
