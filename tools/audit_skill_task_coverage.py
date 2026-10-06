"""Audit whether each benchmark goal clause has a SkillGraph expression."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'skill_library/task_coverage.json'
GOAL_MAPPING = ROOT / 'skill_library/goal_predicates.json'


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
    action_to_skill={}
    verified={}
    for entry in skills['skills']:
        record=json.loads((ROOT/'skill_library'/entry['definition']).read_text())
        action=record['action_predicate']
        action_to_skill[action['name']]=entry['skill_id']
        verified[action['name']]=set(action['verified_by'])
    if len(action_to_skill)!=len(known):
        raise ValueError('action predicates must be unique')
    goal_map=json.loads(GOAL_MAPPING.read_text())
    if goal_map.get('schema_version')!=1 or goal_map.get('kind')!='task_goal_action_mapping':
        raise ValueError('invalid task goal/action mapping')
    reports=[]
    seen_goal_types=set()
    for path in sorted((ROOT/'tasks').glob('*/task.json')):
        task=json.loads(path.read_text())
        clauses=[]
        for clause in task['goal']['all']:
            row={'goal_clause':clause,**plan_for(clause)}
            if not set(row['skill_ids']) <= known:
                raise ValueError(f'{path}: references unknown SkillNode')
            goal_type=row['goal_type']
            seen_goal_types.add(goal_type)
            mapping=goal_map['goals'].get(goal_type)
            if mapping is None or mapping.get('task_evaluator') not in clause:
                raise ValueError(f'{path}: unmapped task goal {goal_type}')
            direct=mapping['direct_actions']
            supporting=mapping.get('supporting_actions',[])
            if not set(direct+supporting) <= set(action_to_skill):
                raise ValueError(f'{path}: unknown action predicate for {goal_type}')
            required=set(mapping['required_state_facts'])
            if any(not required <= verified[action] for action in direct):
                raise ValueError(f'{path}: unverified action facts for {goal_type}')
            if not direct and not mapping.get('terminal_invariant'):
                raise ValueError(f'{path}: no action or terminal invariant for {goal_type}')
            if direct and not {action_to_skill[action] for action in direct} & set(row['skill_ids']):
                raise ValueError(f'{path}: planned Skills do not contain a direct action for {goal_type}')
            row['action_predicates']=[action for action in direct
                                      if action_to_skill[action] in row['skill_ids']]
            row['verified_state_facts']=mapping['required_state_facts']
            row['task_evaluator_predicate']=mapping['task_evaluator']
            clauses.append(row)
        reports.append({'task':task['task'],'task_file':str(path.relative_to(ROOT)),
                        'goal_clause_count':len(clauses),'clauses':clauses,
                        'coverage':'nominal_plan_expressible',
                        'physical_success_guaranteed':False})
    if seen_goal_types != set(goal_map['goals']):
        raise ValueError(f'goal mapping differs from built tasks: {seen_goal_types ^ set(goal_map["goals"])}')
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
