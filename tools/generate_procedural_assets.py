"""Generate deterministic, graspable Zeno props as URDF meshes.

Run with the IsaacLab Python (`trimesh` required), then use the IsaacLab Python:
`OMNI_KIT_ACCEPT_EULA=YES python tools/prepare_assets.py --only ... --convert`.
The mesh is generated at real size; the standard converter adds annotation and USD.
"""
from __future__ import annotations

import json
from pathlib import Path
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    'foam_cube': {'size': 0.06, 'mass': 0.035, 'tags': ['toy','block','floor_pick'], 'collider': 'solid'},
    'soda_can': {'size': 0.12, 'mass': 0.15, 'tags': ['can','recyclable'], 'collider': 'solid'},
    'snack_carton': {'size': 0.17, 'mass': 0.18, 'tags': ['food','box'], 'collider': 'solid'},
    'small_storage_bin': {'size': 0.22, 'mass': 0.30, 'tags': ['container','storage'], 'collider': 'rect_container'},
    'wide_storage_bin': {'size': 0.34, 'mass': 1.20, 'tags': ['container','storage','recycling'], 'collider': 'rect_container'},
    'juice_bottle': {'size': 0.18, 'mass': 0.20, 'tags': ['bottle','recyclable'], 'collider': 'solid'},
    'plastic_cup': {'size': 0.095, 'mass': 0.08, 'tags': ['cup','container'], 'collider': 'round_container'},
    'paperback_book': {'size': 0.18, 'mass': 0.25, 'tags': ['book','flat'], 'collider': 'solid'},
    'tissue_box': {'size': 0.14, 'mass': 0.17, 'tags': ['box','flat'], 'collider': 'solid'},
    'rolling_pin': {'size': 0.22, 'mass': 0.26, 'tags': ['utensil','cylinder'], 'collider': 'solid'},
    'shallow_sorting_tray': {'size': 0.27, 'mass': 0.32, 'tags': ['container','tray','storage'], 'collider': 'rect_container'},
}


def box(extents, center):
    mesh = trimesh.creation.box(extents=extents)
    mesh.apply_translation(center)
    return mesh


def open_rect_container(width, depth, height, wall=0.007):
    """Open-top floor and four walls; no solid hull closing the cavity."""
    parts = [box((width, depth, wall), (0, 0, wall / 2)),
             box((wall, depth, height), (-(width - wall) / 2, 0, height / 2)),
             box((wall, depth, height), ((width - wall) / 2, 0, height / 2)),
             box((width - 2 * wall, wall, height), (0, -(depth - wall) / 2, height / 2)),
             box((width - 2 * wall, wall, height), (0, (depth - wall) / 2, height / 2))]
    return trimesh.util.concatenate(parts)


def geometry(name):
    if name == 'foam_cube':
        return box((0.06,0.06,0.06),(0,0,0.03))
    if name == 'soda_can':
        mesh = trimesh.creation.cylinder(radius=0.033, height=0.12, sections=32)
        mesh.apply_translation((0,0,0.06))
        return mesh
    if name == 'snack_carton':
        return box((0.06,0.11,0.17),(0,0,0.085))
    if name in ('small_storage_bin', 'wide_storage_bin', 'shallow_sorting_tray'):
        dims = {'small_storage_bin': (0.22, 0.17, 0.09),
                'wide_storage_bin': (0.34, 0.30, 0.14),
                'shallow_sorting_tray': (0.27, 0.20, 0.055)}
        return open_rect_container(*dims[name])
    if name == 'juice_bottle':
        mesh = trimesh.creation.cylinder(radius=0.029, height=0.18, sections=40)
        mesh.apply_translation((0, 0, 0.09))
        return mesh
    if name == 'plastic_cup':
        wall = trimesh.creation.annulus(r_min=0.033, r_max=0.040,
                                        height=0.095, sections=48)
        wall.apply_translation((0, 0, 0.0475))
        floor = trimesh.creation.cylinder(radius=0.040, height=0.006, sections=48)
        floor.apply_translation((0, 0, 0.003))
        return trimesh.util.concatenate([floor, wall])
    if name == 'paperback_book':
        return box((0.18, 0.12, 0.025), (0, 0, 0.0125))
    if name == 'tissue_box':
        return box((0.14, 0.09, 0.06), (0, 0, 0.03))
    if name == 'rolling_pin':
        mesh = trimesh.creation.cylinder(radius=0.022, height=0.22, sections=40)
        mesh.apply_transform(trimesh.transformations.rotation_matrix(1.5707963268, (0, 1, 0)))
        mesh.apply_translation((0, 0, 0.022))
        return mesh
    raise KeyError(name)


def main():
    registry = ROOT/'assets/custom_assets.json'
    records = json.loads(registry.read_text()) if registry.exists() else {}
    for name, spec in SPECS.items():
        folder = ROOT/'assets/asset3d'/name/'result'
        mesh_dir = folder/'mesh'
        mesh_dir.mkdir(parents=True,exist_ok=True)
        model = geometry(name)
        if name in ("foam_cube", "snack_carton", "paperback_book", "tissue_box"):
            # Dense planar vertices let the shared pinch profiler sample side slabs.
            model = model.subdivide().subdivide().subdivide()
        if name == "rolling_pin":
            model = model.subdivide().subdivide()
        for suffix in ['', '_collision']:
            model.export(mesh_dir/f'{name}{suffix}.obj')
        urdf = f'''<?xml version="1.0"?>
<robot name="{name}"><link name="{name}">
<visual><origin xyz="0 0 0" rpy="0 0 0"/><geometry><mesh filename="mesh/{name}.obj" scale="1 1 1"/></geometry></visual>
<collision><origin xyz="0 0 0" rpy="0 0 0"/><geometry><mesh filename="mesh/{name}_collision.obj" scale="1 1 1"/></geometry></collision>
<inertial><mass value="{spec['mass']}"/><origin xyz="0 0 0"/><inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" iyz="0" izz="0.001"/></inertial>
</link></robot>'''
        (folder/f'{name}.urdf').write_text(urdf)
        records[name] = {**spec,'lay_flat':False,'urdf':f'assets/asset3d/{name}/result/{name}.urdf','generator':'procedural_mesh_v1'}
        print(name,tuple(round(v,4) for v in model.extents))
    registry.write_text(json.dumps(records,indent=2)+'\n')


if __name__ == '__main__':main()
