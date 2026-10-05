"""Render per-node Agent Skill guides from the static Skill/Contract catalogs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'skill_library'


def build() -> dict[Path, str]:
    catalog = json.loads((LIB / 'catalog.json').read_text())
    contracts = {row['skill_id']: row for row in
                 json.loads((ROOT / 'zeno_skills/node_contracts.json').read_text())['contracts']}
    relations = json.loads((LIB / 'relations.json').read_text())['relations']
    files = {}
    for entry in catalog['skills']:
        path = LIB / entry['definition']
        spec = json.loads(path.read_text())
        sid = spec['skill_id']
        contract = contracts[sid]
        lines = ['---', f'name: {sid}', f'description: {spec["description"]}', '---', '',
                 f'# {sid} — {spec["name"]}', '', '## When to use', '',
                 spec['description'], '', '## Inputs', '']
        if spec['args']:
            for name, meta in spec['args'].items():
                lines.append(f'- `{name}` (`{meta["type"]}`): {meta["description"]}')
        else:
            lines.append('- None.')
        lines += ['', '## Preconditions', '']
        lines += [f'- `{row["predicate"]}` — `{row["enforcement"]}`'
                  for row in spec['requires']]
        lines += ['', '## Expected state change', '']
        lines += [f'- `{row["predicate"]}` — measured by `{row["verification"]}`'
                  for row in spec['achieves']]
        lines += ['', '## Invocation and policy plan', '',
                  f'Use `skill_id: {sid}` with typed `args` in a `skill_subgraph`. '
                  f'The Graph Manager grounds refs, then calls '
                  f'`ContractRunner.run("{spec["contract_id"]}", "compose", ...)`.', '']
        lines += ['Grounded noun slots (Contract validates the scene instance before execution):', '']
        for name, binding in contract['noun_bindings'].items():
            constraints = {key: value for key, value in binding.items()
                           if key not in ('argument', 'kind')}
            lines.append(f'- `{name}`: `{binding["kind"]}`; constraints `{constraints}`')
        lines.append('')
        plan = contract['policy_plan']
        paths = plan.get('paths') or [{'path_id': 'fixed', 'when': [], 'steps': plan['steps']}]
        for route_path in paths:
            lines += [f'### Policy path: {route_path["path_id"]}', '',
                      f'Match before execution: `{route_path["when"]}`.', '']
            for index, step in enumerate(route_path['steps'], 1):
                args = ', '.join(row['arg'] for row in step['args'])
                kwargs = ', '.join(f'{name}={value["arg"] if isinstance(value, dict) else value}'
                                   for name, value in step.get('kwargs', {}).items())
                signature = ', '.join(part for part in (args, kwargs) if part)
                lines.append(f'{index}. `{step["policy_id"]}({signature})`')
            lines.append('')
        verifier = contract['verifier']
        primary = (f'{verifier["legacy_family_contract"]} / {verifier["route"]}'
                   if verifier.get('legacy_family_contract') else verifier['custom'])
        extras = ', '.join(verifier.get('extra_checks', []))
        lines += ['', f'Verifier: `{primary}`' + (f' plus `{extras}`.' if extras else '.'),
                  '', '## Related Skills', '']
        outgoing = [row for row in relations if row['from'] == sid]
        incoming = [row for row in relations if row['to'] == sid]
        if outgoing:
            lines += [f'- `{row["to"]}` (`{row["kind"]}`) when {row["when"]} '
                      f'— {row["reason"]}' for row in outgoing]
        if incoming:
            lines += [f'- May follow `{row["from"]}` (`{row["kind"]}`) when {row["when"]}.'
                      for row in incoming]
        if not outgoing and not incoming:
            lines.append('- No fixed relation; select the next node from the task goal and observation.')
        lines += ['', '## Failure', '',
                  'Stop and observe the live scene again. The upper layer decides whether to retry, '
                  'choose a related Skill, or revise the subgraph. Relations never execute automatically.']
        for hint in spec.get('fallback_hints', []):
            lines.append(f'- Conditional fallback `{hint["skill_id"]}` when {hint["when"]}: {hint["reason"]}')
        lines += ['', '## Scope and evidence', '', spec['scope']['unit'], '',
                  f'Availability: `{spec["availability"]}`. A callable or previously verified '
                  'policy does not guarantee success in a new scene.']
        lines += [f'- Outside scope: {item}' for item in spec['scope']['excludes']]
        lines.append('')
        files[path.with_name('SKILL.md')] = '\n'.join(lines)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = build()
    stale = [str(path) for path, content in files.items()
             if not path.exists() or path.read_text() != content]
    if args.check and stale:
        raise SystemExit(f'stale Agent Skill guides: {stale[:5]} ({len(stale)})')
    if not args.check:
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print(f'{len(files)} Agent Skill guides current' if args.check
          else f'wrote {len(files)} Agent Skill guides')


if __name__ == '__main__':
    main()
