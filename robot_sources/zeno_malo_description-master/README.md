# zeno_malo_description

**English** | [简体中文](README.zh-CN.md)

## File Structure

ROS 2 description package for Zeno Malo EDU. The default assembly, `zeno_malo_edu`, includes two **Malo Pinch** parallel grippers.

```text
zeno_malo_description/
├── CMakeLists.txt                     Package build and install rules
├── package.xml                        ROS 2 package metadata and dependencies
├── urdf/
│   ├── zeno_malo_edu.urdf.xacro        Default assembly and mounts for both grippers
│   ├── robots/malo_edu/
│   │   ├── malo_edu.xacro             Robot body assembly macro
│   │   └── modules/                   Chassis, torso, left arm and right arm modules
│   └── end_effectors/malo_pinch/      Gripper geometry and coupled finger motion
├── meshes/
│   ├── robots/malo_edu/               Robot body CAD meshes
│   └── end_effectors/malo_pinch/      Gripper CAD meshes
├── launch/display.launch.py           Model preview launch file
├── rviz/model.rviz                    RViz preview configuration
└── test/                              Model, asset, assembly and joint limit checks
```

## Usage

> **Compatibility:** This package currently supports **ROS 2**.

### Build and Source

Place this package in the `src/` directory of a ROS 2 workspace. After sourcing the ROS 2 environment and installing the dependencies, run the following commands from the workspace root:

```bash
colcon build --symlink-install --packages-select zeno_malo_description
source install/setup.bash
```

### Model Preview

```bash
ros2 launch zeno_malo_description display.launch.py
```

RViz and the joint slider window open by default. Append `gui:=false` to disable the joint slider window, or `rviz:=false` to disable RViz.

## Sensors

The following hardware specifications are listed with their corresponding URDF mounting frames.

### Head Stereo Camera

- Mounting frame: `stereo_camera_link`.
- Resolution: **640 × 480** per eye.
- Frame rate: **30 Hz**.
- Diagonal field of view (FOV): **180°**.
- Stereo baseline: **6 cm**.

### Wrist Monocular Cameras

- Mounting frames: `left_gripper_camera_link` for the left wrist and `right_gripper_camera_link` for the right wrist.
- Resolution: **640 × 480** per camera.
- Frame rate: **30 Hz**.
- Diagonal field of view (FOV): **175°**.

### LiDAR

- Model: **MID360**.
- Mounting frame: `lidar_link`.
- `lidar_link` is attached to `base_link` by a fixed joint, with a translation of `(0.12, 0, 0.25505)` m and zero rotation. It defines a coordinate frame only, with no visual geometry, collision geometry or inertia.
