"""Render physical verification status for every active SkillNode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'skill_library/verification/node_contract_smoke.json'
OUTPUT = ROOT / 'skill_library/verification/STATUS.md'


def build() -> str:
    catalog = json.loads((ROOT / 'skill_library/catalog.json').read_text())
    evidence = json.loads(REPORT.read_text())
    observed: dict[str, list[tuple[str, dict]]] = {}
    blocked: dict[str, str] = {}
    for run in evidence['runs']:
        for cid in run.get('unreached_contracts', []):
            blocked[cid] = run['source_report']
        for contract in run['contracts']:
            observed.setdefault(contract['contract_id'], []).append(
                (run['source_report'], contract))
    lines = ['# SkillNode physical verification status', '',
             f'All {len(catalog["skills"])} SkillNode/Contract definitions pass the static pairing and schema checks. '
             'A physical pass means at least one Contract invocation finished with its measured '
             'postconditions true in Isaac Sim; it does not guarantee success for every noun or scene.', '',
             '| SkillNode | Contract | Status | Successful path(s) | Evidence |',
             '| --- | --- | --- | --- | --- |']
    passed = 0
    for entry in catalog['skills']:
        sid = entry['skill_id']
        spec = json.loads((ROOT / 'skill_library' / entry['definition']).read_text())
        cid = spec['contract_id']
        records = observed.get(cid, [])
        successes = [(source, row) for source, row in records if row['success']]
        if successes:
            status = 'physical pass'
            passed += 1
        elif records:
            status = 'attempted; no pass'
        elif cid in blocked:
            status = 'blocked by preparation'
        else:
            status = 'not yet run'
        paths = ', '.join(f'`{name}`' for name in sorted({
            row.get('selected_policy_path') or 'fixed' for _, row in successes})) or '—'
        evidence_sources = ([source for source, _ in successes[:2]]
                            if successes else [records[-1][0]] if records else
                            [blocked[cid]] if cid in blocked else [])
        sources = ', '.join(f'[{Path(source).parent.name}](../../{source})'
                            for source in evidence_sources) or '—'
        lines.append(f'| `{sid}` | `{cid}` | {status} | {paths} | {sources} |')
    lines += ['', f'**Physical passes: {passed}/{len(catalog["skills"])}.** Remaining: {len(catalog["skills"])-passed}.', '',
              'Full observations, failures, and scene paths are in '
              '[node_contract_smoke.json](node_contract_smoke.json). Remaining blockers are in '
              '[FINDINGS.md](FINDINGS.md).', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = build()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != content:
            raise SystemExit('stale SkillNode physical status')
        print('SkillNode physical status current')
    else:
        OUTPUT.write_text(content)
        print(next(line for line in content.splitlines() if line.startswith('**Physical passes:')))


if __name__ == '__main__':
    main()
