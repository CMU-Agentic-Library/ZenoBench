"""Validate the deployed robot tree, mesh resources and mechanical limits."""
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

import pytest
import xacro


PACKAGE = Path(__file__).resolve().parents[1]
ASSEMBLY_ENTRY = PACKAGE / 'urdf/zeno_malo_edu.urdf.xacro'
BODY_MODULES = PACKAGE / 'urdf/robots/malo_edu/modules'


@pytest.fixture(scope='module')
def robot():
    return ET.fromstring(xacro.process_file(str(ASSEMBLY_ENTRY)).toxml())


def joint(robot, name):
    result = robot.find(f'joint[@name="{name}"]')
    assert result is not None, f'Missing joint {name}'
    return result


def test_complete_assembly_is_a_single_connected_tree(robot):
    assert robot.get('name') == 'zeno_malo_edu'
    links = [element.get('name') for element in robot.findall('link')]
    joints = [element.get('name') for element in robot.findall('joint')]
    assert len(links) == len(set(links)) == 37
    assert len(joints) == len(set(joints)) == 36
    parents = {}
    for element in robot.findall('joint'):
        parent = element.find('parent').get('link')
        child = element.find('child').get('link')
        assert parent in links and child in links
        assert child not in parents, f'Multiple parents for {child}'
        parents[child] = parent
    assert set(links) - parents.keys() == {'base_link'}
    for link in links:
        seen = set()
        current = link
        while current in parents:
            assert current not in seen, f'Cycle from {link} through {current}'
            seen.add(current)
            current = parents[current]
        assert current == 'base_link'
    # 26 independent body joints and one independent joint per gripper.
    assert sum(j.get('type') != 'fixed' and j.find('mimic') is None
               for j in robot.findall('joint')) == 28
    assert not robot.findall('gazebo')
    assert not robot.findall('transmission')
    assert not robot.findall('ros2_control')


def test_mesh_resources_resolve_within_the_package(robot):
    meshes = robot.findall('.//mesh')
    assert meshes
    used = set()
    for mesh in meshes:
        uri = mesh.get('filename')
        prefix = 'package://zeno_malo_description/'
        assert uri.startswith(prefix), f'Non-portable mesh URI: {uri}'
        relative = PurePosixPath(uri.removeprefix(prefix))
        assert not relative.is_absolute() and '..' not in relative.parts
        target = PACKAGE.joinpath(*relative.parts)
        assert target.is_file(), f'Missing mesh: {uri}'
        assert target.resolve().is_relative_to(PACKAGE.resolve())
        used.add(target)
    # All CAD assets are used by this assembly; the bilateral tools share meshes.
    assert used == set((PACKAGE / 'meshes').rglob('*.STL'))
    assert len(used) == 32


def test_four_body_modules_are_complete_and_disjoint(robot):
    elements = []
    for name in ('chassis', 'torso', 'left_arm', 'right_arm'):
        module = ET.parse(BODY_MODULES / f'{name}.xacro').getroot()
        elements.extend(module.findall('.//link'))
        elements.extend(module.findall('.//joint'))
    names = [(e.tag, e.get('name')) for e in elements]
    assert len(names) == len(set(names)) == 57
    assert sum(tag == 'link' for tag, _ in names) == 29
    assert sum(tag == 'joint' for tag, _ in names) == 28
    assembled_body = {(e.tag, e.get('name'))
                      for e in robot.findall('link') + robot.findall('joint')
                      if '_gripper_' not in e.get('name')}
    assert set(names) == assembled_body
    for element in elements:
        deployed = robot.find(f'{element.tag}[@name="{element.get("name")}"]')
        assert deployed is not None
        # Xacro expansion must leave body geometry and joint properties intact.
        assert [(e.tag, e.attrib) for e in element.iter()] == [
            (e.tag, e.attrib) for e in deployed.iter()]


@pytest.mark.parametrize('side,expected_y', [('left', -0.019), ('right', 0.019)])
def test_mounts_fit_mirrored_cad_faces_below_the_wrist(robot, side, expected_y):
    mount = joint(robot, side + '_gripper_mount_joint')
    assert mount.get('type') == 'fixed'
    assert mount.find('parent').get('link') == side + '_arm_link_7'
    assert mount.find('child').get('link') == side + '_gripper_link'
    origin = mount.find('origin')
    xyz = [float(value) for value in origin.get('xyz').split()]
    rpy = [float(value) for value in origin.get('rpy').split()]
    assert xyz == pytest.approx([0, expected_y, -0.0384])
    assert rpy == pytest.approx([0, 0, 0])
    # CAD mounting faces: left tool +24 mm meets wrist +5 mm; right mirrored.
    sign = 1 if side == 'left' else -1
    assert xyz[1] + sign * 0.024 == pytest.approx(sign * 0.005)


@pytest.mark.parametrize('side', ['left', 'right'])
@pytest.mark.parametrize('q', [0.0, 0.02, 0.04])
def test_single_gripper_coordinate_moves_fingers_equally(robot, side, q):
    leader_name = side + '_gripper_left_finger_axis'
    leader = joint(robot, leader_name)
    follower = joint(robot, side + '_gripper_right_finger_axis')
    assert leader.get('type') == follower.get('type') == 'prismatic'
    assert leader.find('mimic') is None
    mimic = follower.find('mimic')
    assert mimic.get('joint') == leader_name
    follower_q = q * float(mimic.get('multiplier')) + float(mimic.get('offset'))
    assert follower_q == pytest.approx(q)
    axes = [[float(v) for v in j.find('axis').get('xyz').split()]
            for j in (leader, follower)]
    assert axes == [[0, 1, 0], [0, -1, 0]]
    origins = [[float(v) for v in j.find('origin').get('xyz').split()]
               for j in (leader, follower)]
    assert origins[0] == origins[1]
    positions = [[origin + axis * state for origin, axis in zip(o, a)]
                 for o, a, state in zip(origins, axes, (q, follower_q))]
    assert [(a+b)/2 for a, b in zip(*positions)] == pytest.approx(origins[0])
    assert positions[0][1] - positions[1][1] == pytest.approx(2*q)
    for finger_joint in (leader, follower):
        limits = finger_joint.find('limit')
        assert float(limits.get('lower')) == 0
        assert float(limits.get('upper')) == 0.04
        assert float(limits.get('effort')) == 80
        assert float(limits.get('velocity')) == 0.0785


def test_lift_speed_uses_metres_per_second(robot):
    lift = joint(robot, 'torso_lift_joint')
    assert lift.get('type') == 'prismatic'
    assert float(lift.find('limit').get('velocity')) == 0.1166666666
