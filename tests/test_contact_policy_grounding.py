"""Rear push and top drag must use the same live support guard as normal push."""
from types import SimpleNamespace
import numpy as np
import pytest

from zeno_skills.policies.manipulation import PushFromBehindPolicy, TopDragPolicy
from zeno_skills.rig import SkillFailure


@pytest.mark.parametrize('policy_type', [PushFromBehindPolicy, TopDragPolicy])
def test_contact_policy_resolves_support_and_checks_live_occupancy(monkeypatch, policy_type):
    calls = []
    support = {'name': 'table'}
    rig = SimpleNamespace(
        held=None,
        ann=SimpleNamespace(objects={'cube': {}}, support=lambda name: support),
        geo=SimpleNamespace(support_under=lambda name, state: support),
        state=lambda: {},
    )
    monkeypatch.setattr('zeno_skills.policies.manipulation.skills.push',
                        lambda *args, **kwargs: calls.append((args, kwargs)))
    policy_type(rig).execute('cube', 'table', [1.0, 0.0], 0.10)
    assert calls[0][0][2] is support
    assert np.allclose(calls[0][0][3], [1.0, 0.0])
    rig.geo.support_under = lambda name, state: {'name': 'shelf'}
    with pytest.raises(SkillFailure, match='not on table'):
        policy_type(rig).execute('cube', 'table', [1.0, 0.0], 0.10)
