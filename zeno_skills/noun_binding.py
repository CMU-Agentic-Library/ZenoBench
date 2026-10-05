"""Bind Contract noun slots to live annotated scene entities and select a path."""

from __future__ import annotations

from .rig import SkillFailure


def _handle_collider(rig, obj):
    stage = getattr(rig, 'stage', None)
    if stage is None:
        return False
    try:
        prim = stage.GetPrimAtPath(obj['body'] + '/handle_collider')
        return bool(prim.IsValid()) if hasattr(prim, 'IsValid') else bool(prim)
    except Exception:
        return False


def _object_location(rig, name):
    try:
        pos, _ = rig.obj_pose(name)
        art = rig.ann.art('kitchen_microwave')
        bounds = art.get('cavity_aabb')
        if bounds and all(bounds[i] < pos[i] < bounds[i+3] for i in range(3)):
            return 'microwave_cavity'
    except Exception:
        pass
    return None


def bind_contract_nouns(contract: dict, values: dict, rig) -> dict[str, dict]:
    """Validate grounded IDs and return measured attributes used by path rules."""
    context = {}
    ann = getattr(rig, 'ann', None)
    if ann is None:
        raise SkillFailure('Contract noun binding requires live scene annotations')
    for slot, binding in contract.get('noun_bindings', {}).items():
        name = values[slot]
        if not isinstance(name, str) or not name.strip():
            raise SkillFailure(f'{slot}: noun must be a grounded scene instance ID')
        kind = binding['kind']
        try:
            if kind in ('scene_object', 'container'):
                obj = ann.objects[name]
                asset = ann.asset_of(obj)
                grasp_types = [item['type'] for item in asset.get('grasps', [])]
                held = getattr(rig, 'held', None)
                item = {'instance': name, 'kind': 'scene_object', 'asset': obj['asset'],
                        'grasp_types': grasp_types,
                        'held_kind': held.get('kind') if held and held.get('name') == name else None,
                        'handle_collider': _handle_collider(rig, obj),
                        'location': _object_location(rig, name)}
                try:
                    item['on_floor'] = float(rig.geo.bottom(name, rig.state())[2]) < 0.05
                except Exception:
                    item['on_floor'] = None
                if kind == 'container' and not asset.get('container'):
                    raise SkillFailure(f'{slot}: {name} is not an annotated container')
                if binding.get('requires_grasp_type') not in (None, *grasp_types):
                    raise SkillFailure(f'{slot}: {name} lacks {binding["requires_grasp_type"]} grasp')
                if binding.get('requires_right_held') and (not held or held.get('name') != name):
                    raise SkillFailure(f'{slot}: {name} is not right-held')
                if binding.get('requires_held_kind') and item['held_kind'] != binding['requires_held_kind']:
                    raise SkillFailure(f'{slot}: {name} is not {binding["requires_held_kind"]}-held')
            elif kind == 'support':
                support = ann.support(name)
                item = {'instance': name, 'kind': 'support',
                        'furniture': support.get('furniture'),
                        'category': support.get('category')}
                if binding.get('furniture_equals') and item['furniture'] != binding['furniture_equals']:
                    raise SkillFailure(f'{slot}: {name} is not a {binding["furniture_equals"]} support')
            elif kind == 'articulated':
                art = ann.art(name)
                item = {'instance': name, 'kind': 'articulated',
                        'category': art.get('category'), 'type': art.get('type'),
                        'has_handle': bool(art.get('handle')),
                        'powered_microwave': art.get('category') == 'microwave' and 'door_button' in art}
                if binding.get('category_equals') and item['category'] != binding['category_equals']:
                    raise SkillFailure(f'{slot}: {name} has wrong appliance category')
                if binding.get('required_annotation') and binding['required_annotation'] not in art:
                    raise SkillFailure(f'{slot}: {name} lacks {binding["required_annotation"]} annotation')
                if binding.get('forbid_annotation') and binding['forbid_annotation'] in art:
                    raise SkillFailure(f'{slot}: {name} is not a manual handle target')
            else:
                raise ValueError(f'{slot}: unknown noun kind {kind}')
        except (KeyError, IndexError) as exc:
            raise SkillFailure(f'{slot}: {name} is absent from scene annotation') from exc
        context[slot] = item
    return context


def select_policy_path(plan: dict, nouns: dict[str, dict]) -> tuple[str, list[dict]]:
    if plan['kind'] == 'sequence':
        return 'fixed', plan['steps']
    if plan['kind'] != 'choice':
        raise ValueError(f'unknown policy plan kind {plan["kind"]}')
    for path in plan['paths']:
        if all((condition.get('equals') == nouns[condition['noun']].get(condition['field'])
                if 'equals' in condition else
                condition['contains'] in nouns[condition['noun']].get(condition['field'], []))
               for condition in path['when']):
            return path['path_id'], path['steps']
    raise SkillFailure('no safe policy path matches the bound nouns and current state')
