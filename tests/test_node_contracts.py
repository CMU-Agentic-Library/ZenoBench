"""One-to-one SkillNode contracts and their composed execution boundary."""

from types import SimpleNamespace

import pytest

from skill_library.graph import load_skills
from zeno_skills.contract_runtime import ContractRunner
from zeno_skills.node_contracts import NODE_CONTRACTS


def test_public_skill_nodes_pair_bijectively_with_measured_contracts():
    skills = load_skills()
    assert len(skills) == len(NODE_CONTRACTS) == 42
    assert {row['contract_id'] for row in skills.values()} == set(NODE_CONTRACTS)
    for skill in skills.values():
        contract = NODE_CONTRACTS[skill['contract_id']]
        assert contract['skill_id'] == skill['skill_id']
        assert contract['requires'] == skill['requires']
        assert contract['achieves'] == skill['achieves']
        plan = contract['policy_plan']
        assert (plan['steps'] if plan['kind'] == 'sequence' else plan['paths'])


def _rig():
    rig = SimpleNamespace(
        held={'name': 'apple'}, left_held=None, events=[],
        geo=SimpleNamespace(on=lambda obj, support, state: (True, {'on': True})),
        state=lambda: {'objects': {'apple': {}}},
        base_pose=lambda: (0.0, 0.0, 0.0),
        ann=SimpleNamespace(
            objects={'apple': {'name': 'apple', 'asset': 'apple', 'body': '/apple'}},
            asset_of=lambda obj: {'grasps': [{'type': 'top_pinch'}]},
            support=lambda name: {'name': name, 'furniture':
                                  'kitchen_microwave' if name == 'cavity_floor' else 'table'},
        ),
    )
    return rig


def test_three_policy_place_sequence_and_final_verifier(monkeypatch):
    rig = _rig()
    calls = []

    class Policy:
        def __init__(self, name):
            self.name = name

        def execute(self, *args):
            calls.append((self.name, args))
            if self.name == 'policy_019':
                rig.held = None

    monkeypatch.setattr('zeno_skills.policies.PolicySuite',
                        lambda live: SimpleNamespace(**{
                            pid: Policy(pid) for pid in ('policy_018', 'policy_019', 'policy_020')
                        }))
    result = ContractRunner(rig).run('contract_022', 'compose', 'apple', 'cavity_floor')
    assert [name for name, _ in calls] == ['policy_018', 'policy_019', 'policy_020']
    assert result.observations['verified_predicates'] == ['on', 'right_hand_empty']
    assert len(result.observations['policy_steps']) == 3


def test_policy_failure_stops_sequence_and_reports_partial_effects(monkeypatch):
    rig = _rig()
    calls = []

    class Policy:
        def __init__(self, name):
            self.name = name

        def execute(self, *args):
            calls.append(self.name)
            if self.name == 'policy_019':
                rig.held = None
                raise RuntimeError('release failed after contact')

    monkeypatch.setattr('zeno_skills.policies.PolicySuite',
                        lambda live: SimpleNamespace(**{
                            pid: Policy(pid) for pid in ('policy_018', 'policy_019', 'policy_020')
                        }))
    runner = ContractRunner(rig)
    with pytest.raises(RuntimeError, match='release failed'):
        runner.run('contract_022', 'compose', 'apple', 'cavity_floor')
    assert calls == ['policy_018', 'policy_019']
    trace = runner.trace[-1]
    assert not trace.success
    assert trace.observations['completed_policy_steps'] == [
        {'index': 1, 'policy_id': 'policy_018'}
    ]
    assert trace.observations['failed_policy_step'] == {'index': 2, 'policy_id': 'policy_019'}
    assert trace.observations['held_right'] is None


def test_wrong_route_and_arity_are_rejected_before_policy_execution():
    runner = ContractRunner(_rig())
    with pytest.raises(ValueError, match='compose route'):
        runner.run('contract_022', 'microwave', 'apple', 'cavity_floor')
    with pytest.raises(ValueError, match='expected 2 arguments'):
        runner.run('contract_022', 'compose', 'apple')


def test_temperature_contract_waits_for_measured_threshold():
    thermal = SimpleNamespace(temperatures_c={'oatmeal': 56.0}, active=True)
    events = []
    def step(count):
        assert count == 120
        thermal.temperatures_c['oatmeal'] += 4.0
    rig = SimpleNamespace(
        held=None, left_held=None, events=events, thermal=thermal,
        base_pose=lambda: (0.0, 0.0, 0.0),
        step=step,
        log=lambda label, **data: events.append({'label': label, **data}),
        ann=SimpleNamespace(
            objects={'oatmeal': {'name': 'oatmeal', 'asset': 'oatmeal', 'body': '/oatmeal'}},
            asset_of=lambda obj: {'grasps': []},
        ),
    )
    result = ContractRunner(rig).run('contract_048', 'compose', 'oatmeal', 60.0)
    assert result.observations['temperature_c'] >= 60.0
    assert result.observations['verified_predicates'] == ['temperature_at_least']
    assert not thermal.active


def test_near_hint_contract_passes_dynamic_keyword_and_checks_final_offset(monkeypatch):
    rig = _rig()
    rig.bottom = [1.1, 2.1, 0.75]
    rig.geo = SimpleNamespace(
        on=lambda obj, support, state: (True, {'on': True}),
        bottom=lambda obj, state: __import__('numpy').asarray(rig.bottom),
    )
    calls = []
    class Place:
        def execute(self, obj, support, *, hint):
            calls.append((obj, support, hint))
            rig.held = None
    monkeypatch.setattr('zeno_skills.policies.PolicySuite',
                        lambda live: SimpleNamespace(policy_015=Place()))
    result = ContractRunner(rig).run(
        'contract_046', 'compose', 'apple', 'table', [1.0, 2.0], 0.2)
    assert calls == [('apple', 'table', [1.0, 2.0])]
    assert result.observations['hint_error_m'] < 0.2
    assert 'within_hint_radius' in result.observations['verified_predicates']


def test_near_hint_rejects_policy_success_outside_allowed_radius(monkeypatch):
    rig = _rig()
    rig.geo = SimpleNamespace(
        on=lambda obj, support, state: (True, {'on': True}),
        bottom=lambda obj, state: __import__('numpy').asarray([1.5, 2.0, 0.75]),
    )
    class Place:
        def execute(self, obj, support, *, hint):
            rig.held = None
    monkeypatch.setattr('zeno_skills.policies.PolicySuite',
                        lambda live: SimpleNamespace(policy_015=Place()))
    runner = ContractRunner(rig)
    with pytest.raises(Exception, match='from hint'):
        runner.run('contract_046', 'compose', 'apple', 'table', [1.0, 2.0], 0.2)
    assert runner.trace[-1].observations['completed_policy_steps'] == [
        {'index': 1, 'policy_id': 'policy_015'}]


def test_relations_and_task_clause_audit_are_complete():
    from skill_library.relations import load_relations
    from tools.audit_skill_task_coverage import build
    skills = load_skills()
    relations = load_relations(skills)
    assert len(relations) >= 30
    audit = build()
    assert len(audit['tasks']) == 8
    assert sum(task['goal_clause_count'] for task in audit['tasks']) == 32
    types = {row['goal_type'] for task in audit['tasks'] for row in task['clauses']}
    assert types == {'heated','inside','on','on_upright','near','upright','closed','not_dropped'}
    assert all(not task['physical_success_guaranteed'] for task in audit['tasks'])


def _annotated_rig(annotation='tasks/collect_fruits/annotation.json', *, floor=False):
    from zeno_skills.annotations import SceneAnnotations
    import numpy as np

    rig = _rig()
    rig.held = None
    rig.ann = SceneAnnotations(annotation)
    rig.geo = SimpleNamespace(bottom=lambda name, state: np.array([0.0, 0.0, 0.0 if floor else 0.75]))
    rig.obj_pose = lambda name: (np.array([0.0, 0.0, 0.75]), np.array([1.0, 0.0, 0.0, 0.0]))
    return rig


@pytest.mark.parametrize(('name', 'expected_path', 'expected_policy'), [
    ('apple', 'top_pinch', 'policy_010'),
    ('bowl_side_table', 'round_rim', 'policy_011'),
    ('serving_tray', 'rectangular_rim', 'policy_012'),
    ('plate_counter_a', 'flat_edge', 'policy_013'),
])
def test_one_pick_contract_selects_policy_from_bound_object(
        monkeypatch, name, expected_path, expected_policy):
    rig = _annotated_rig()
    called = []

    class ProbePolicy:
        def __init__(self, pid):
            self.pid = pid

        def execute(self, *args):
            called.append((self.pid, args))
            raise RuntimeError('probe stops before motion')

    monkeypatch.setattr('zeno_skills.policies.PolicySuite',
                        lambda live: SimpleNamespace(**{
                            pid: ProbePolicy(pid) for pid in
                            ('policy_010', 'policy_011', 'policy_012', 'policy_013')
                        }))
    runner = ContractRunner(rig)
    with pytest.raises(RuntimeError, match='probe stops'):
        runner.run_bound('contract_012', object=name)
    assert called == [(expected_policy, (name,))]
    assert runner.trace[-1].observations['selected_policy_path'] == expected_path
    assert runner.trace[-1].observations['bound_nouns']['object']['instance'] == name


def test_floor_object_selects_floor_corner_path():
    from zeno_skills.noun_binding import bind_contract_nouns, select_policy_path
    contract = NODE_CONTRACTS['contract_012']
    nouns = bind_contract_nouns(contract, {'object': 'plate_counter_a'},
                                _annotated_rig(floor=True))
    path, steps = select_policy_path(contract['policy_plan'], nouns)
    assert path == 'floor_corner'
    assert [step['policy_id'] for step in steps] == ['policy_014']


def test_open_contract_uses_articulated_noun_and_button_annotation():
    from zeno_skills.noun_binding import bind_contract_nouns, select_policy_path
    contract = NODE_CONTRACTS['contract_011']
    cases = [
        ('tasks/collect_fruits/annotation.json',
         'KitchenCabinetFactory_6689129_spawn_asset_9539479', 'manual_drawer', 'policy_050'),
        ('tasks/collect_fruits/annotation.json',
         'KitchenCabinetFactory_3699907_spawn_asset_505866', 'manual_hinged_door', 'policy_049'),
        ('tasks/heat_breakfast/annotation.json',
         'kitchen_microwave', 'powered_microwave', 'policy_024'),
    ]
    for ann, noun, expected_path, expected_policy in cases:
        nouns = bind_contract_nouns(contract, {'articulated': noun}, _annotated_rig(ann))
        path, steps = select_policy_path(contract['policy_plan'], nouns)
        assert path == expected_path
        assert [step['policy_id'] for step in steps] == [expected_policy]


def test_unknown_or_unhandled_noun_stops_before_policy(monkeypatch):
    rig = _annotated_rig()
    calls = []
    monkeypatch.setattr('zeno_skills.policies.PolicySuite', lambda live: calls.append(live))
    runner = ContractRunner(rig)
    with pytest.raises(Exception, match='absent from scene annotation'):
        runner.run_bound('contract_012', object='nonexistent_item')
    assert calls == []
    with pytest.raises(Exception, match='no safe policy path'):
        runner.run_bound('contract_012', object='clutter_cereal_a')
    assert calls == []
    assert runner.trace[-1].observations['selected_policy_path'] is None


def test_place_contract_routes_by_target_and_current_grasp():
    from zeno_skills.noun_binding import bind_contract_nouns, select_policy_path
    contract = NODE_CONTRACTS['contract_013']
    cases = [
        ('tasks/heat_breakfast/annotation.json', 'oatmeal',
         'kitchen_microwave/inside_floor', 'rim_pinch', 'microwave_support', ['policy_018', 'policy_019', 'policy_020']),
        ('tasks/collect_fruits/annotation.json', 'plate_counter_a',
         'TableDiningFactory_1437886_spawn_asset_2104395/surface_2',
         'edge', 'edge_held', ['policy_017']),
        ('tasks/collect_fruits/annotation.json', 'apple',
         'TableDiningFactory_1437886_spawn_asset_2104395/surface_2',
         'top_pinch', 'ordinary_surface', ['policy_015']),
    ]
    for ann, obj, support, grasp, expected_path, expected_policies in cases:
        rig = _annotated_rig(ann)
        rig.held = {'name': obj, 'kind': grasp}
        nouns = bind_contract_nouns(contract, {'object': obj, 'support': support}, rig)
        path, steps = select_policy_path(contract['policy_plan'], nouns)
        assert path == expected_path
        assert [step['policy_id'] for step in steps] == expected_policies


def test_push_policy_resolves_contract_support_and_direction(monkeypatch):
    import numpy as np
    from zeno_skills.policies.manipulation import PushPolicy

    rig = SimpleNamespace(held=None, ann=SimpleNamespace(
        support=lambda name: {'name': name, 'z': 0.7}),
        geo=SimpleNamespace(support_under=lambda obj, state: {'name': 'desk'}),
        state=lambda: {})
    calls = []
    monkeypatch.setattr('zeno_skills.policies.manipulation.skills.push',
                        lambda *args, **kwargs: calls.append((args, kwargs)) or 0.06)
    assert PushPolicy(rig).execute('book_red', 'desk', [0.0, -1.0], 0.06) == 0.06
    args, kwargs = calls[0]
    assert args[2] == {'name': 'desk', 'z': 0.7}
    np.testing.assert_allclose(args[3], [0.0, -1.0])
    assert kwargs['label'] == 'PUSH'
    with pytest.raises(ValueError, match='unit vector'):
        PushPolicy(rig).execute('book_red', 'desk', [0.0, -2.0], 0.06)
