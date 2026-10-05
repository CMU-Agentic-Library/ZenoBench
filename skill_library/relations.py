"""Validate conditional Agent Skill relationship hints."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
KINDS = {'enables', 'preparation', 'follows', 'alternative', 'recovery'}


def load_relations(skills: dict[str, dict], path: Path = HERE / 'relations.json') -> list[dict]:
    data = json.loads(path.read_text())
    if data.get('schema_version') != 1 or data.get('kind') != 'skill_relations':
        raise ValueError('invalid Skill relation catalog')
    rows = data.get('relations')
    if not isinstance(rows, list):
        raise ValueError('Skill relations must be a list')
    ids = set()
    for row in rows:
        if row.get('id') in ids or not row.get('id'):
            raise ValueError('duplicate or missing Skill relation ID')
        ids.add(row['id'])
        if row.get('from') not in skills or row.get('to') not in skills:
            raise ValueError(f"{row['id']}: unknown SkillNode")
        if row['from'] == row['to'] or row.get('kind') not in KINDS:
            raise ValueError(f"{row['id']}: invalid relation type or self link")
        if not row.get('when') or not row.get('reason') or row.get('automatic') is not False:
            raise ValueError(f"{row['id']}: relation must be conditional and nonautomatic")
    for sid, spec in skills.items():
        index = spec.get('relations', {})
        outgoing = [row['id'] for row in rows if row['from'] == sid]
        incoming = [row['id'] for row in rows if row['to'] == sid]
        if index.get('outgoing') != outgoing or index.get('incoming') != incoming:
            raise ValueError(f'{sid}: relation index differs')
    return rows
