"""Audit whether each benchmark goal clause has a SkillGraph expression."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'skill_library/task_coverage.json'


def plan_for(clause):
    if 'heated' in clause:
        return {'goal_type':'heated', 'skill_ids':['skill_023','skill_014','skill_024','skill_010','skill_040'],
                'terminal_check':'TaskEvaluator.heated reads measured temperatures_c',
                'conditions':'If food is preloaded, omit open/load; if it is in a fridge, open/pick first. Start only after loading and closing; wait to min_temp_c.'}
    if 'inside' in clause:
        return {'goal_type':'inside','skill_ids':['skill_004','skill_006','skill_029'],
                'terminal_check':'TaskEvaluator.inside checks all selected items in one grounded container',
                'conditions':'Select one present container alternative and repeat pick/place for each item; relocate the container first if the task also requires on(support).'}
    if 'on' in clause:
        upright=bool(clause.get('upright'))
        return {'goal_type':'on_upright' if upright else 'on',
                'skill_ids':['skill_004','skill_037','skill_039'] if upright else ['skill_004','skill_005','skill_030','skill_038'],
                'terminal_check':'TaskEvaluator.on checks support geometry'+(' and post-release tilt' if upright else ''),
                'conditions':'Ground an available object alternative and a valid support. Use edge placement when the grasp mode requires it.'}
    if 'near' in clause:
        return {'goal_type':'near','skill_ids':['skill_004','skill_038','skill_039'],
                'terminal_check':'TaskEvaluator.near checks pairwise bottom-centre distances on the support',
                'conditions':'Place each selected item within max_dist/2 of one shared hint; then run the pairwise task evaluator. Single-skill hint checks alone do not establish the group predicate.'}
    if 'upright' in clause:
        return {'goal_type':'upright','skill_ids':['skill_004','skill_036','skill_037'],
                'terminal_check':'TaskEvaluator.upright reads measured object quaternion',
                'conditions':'For a disturbed container, grasp it before orienting; floor placement recovery is not independently verified. Already-upright objects need no action.'}
    if 'closed' in clause:
        return {'goal_type':'closed','skill_ids':['skill_007','skill_024','skill_026'],
                'terminal_check':'TaskEvaluator.closed checks every requested articulated joint',
                'conditions':'Repeat the appropriate close Skill for each measured open joint; already-closed joints need no action.'}
    if 'not_dropped' in clause:
        return {'goal_type':'not_dropped','skill_ids':['skill_004','skill_020','skill_005','skill_006'],
                'terminal_check':'TaskEvaluator.not_dropped checks the global initial-to-final scene invariant',
                'conditions':'Prevent drops during each action. If a recoverable item falls, pick and replace it; this global invariant is not guaranteed by one SkillNode.'}
    raise ValueError(f'unmapped goal clause: {clause}')


def build():
    skills=json.loads((ROOT/'skill_library/catalog.json').read_text())
    known={entry['skill_id'] for entry in skills['skills']}
    reports=[]
    for path in sorted((ROOT/'tasks').glob('*/task.json')):
        task=json.loads(path.read_text())
        clauses=[]
        for clause in task['goal']['all']:
            row={'goal_clause':clause,**plan_for(clause)}
            if not set(row['skill_ids']) <= known:
                raise ValueError(f'{path}: references unknown SkillNode')
            clauses.append(row)
        reports.append({'task':task['task'],'task_file':str(path.relative_to(ROOT)),
                        'goal_clause_count':len(clauses),'clauses':clauses,
                        'coverage':'nominal_plan_expressible',
                        'physical_success_guaranteed':False})
    return {'schema_version':1,'kind':'skill_task_coverage_audit',
            'meaning':'Every declared benchmark goal clause has an action path or terminal invariant check; physical success still depends on grounding, reachability and execution.',
            'tasks':reports}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    content=json.dumps(build(),indent=2,ensure_ascii=False)+'\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text()!=content:
            raise SystemExit('stale skill_library/task_coverage.json')
        print('all task goal clauses mapped')
    else:
        OUTPUT.write_text(content)
        print(f'wrote {OUTPUT}')

if __name__=='__main__':main()
