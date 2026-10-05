"""Copy concise, reviewable evidence from Isaac Sim Contract result files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'skill_library/verification/node_contract_smoke.json'


def summarize(source: Path) -> dict:
    result = json.loads(source.read_text())
    if not isinstance(result.get('contracts'), list) or not result.get('scene'):
        raise ValueError(f'{source}: not a Contract runner result')
    rows = []
    for contract in result['contracts']:
        observation = contract.get('observations', {})
        rows.append({
            'contract_id': contract['contract_id'],
            'success': contract['success'],
            'error': contract.get('error'),
            'selected_policy_path': observation.get('selected_policy_path'),
            'bound_nouns': {slot: noun['instance'] for slot, noun in
                            observation.get('bound_nouns', {}).items()},
            'verified_predicates': observation.get('verified_predicates', []),
            'policy_steps': [step['policy_id'] for step in observation.get('policy_steps', [])],
            'completed_policy_steps': [step['policy_id'] for step in
                                       observation.get('completed_policy_steps', [])],
            'failed_policy_step': (observation.get('failed_policy_step') or {}).get('policy_id'),
            'temperature_c': observation.get('temperature_c'),
            'object_tilt_deg': observation.get('object_tilt_deg'),
            'hint_error_m': observation.get('hint_error_m'),
        })
    return {
        'scene': result['scene'],
        'source_report': str(source.relative_to(ROOT)),
        'success': result['success'],
        'failure': result.get('failure'),
        'start_base': result.get('start_base'),
        'preparation_policies': result.get('preparation_policies', []),
        'unreached_contracts': result.get('unreached_contracts', []),
        'contracts': rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', nargs='+', type=Path)
    args = parser.parse_args()
    report = json.loads(REPORT.read_text())
    for path in args.results:
        source = path.resolve()
        if not source.is_relative_to(ROOT):
            raise ValueError(f'{source}: result must be inside the repository')
        item = summarize(source)
        report['runs'] = [row for row in report['runs']
                          if row['source_report'] != item['source_report']]
        report['runs'].append(item)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f"recorded {len(args.results)} run(s) in {REPORT.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
