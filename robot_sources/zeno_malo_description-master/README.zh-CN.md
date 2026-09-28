# zeno_malo_description

[English](README.md) | **简体中文**

## 文件结构

Zeno Malo EDU 的 ROS 2 描述包，默认总装为搭载双 **Malo Pinch** 平行夹爪的 `zeno_malo_edu`。

```text
zeno_malo_description/
├── CMakeLists.txt                     包构建与安装规则
├── package.xml                        ROS 2 包信息与依赖
├── urdf/
│   ├── zeno_malo_edu.urdf.xacro        默认总装入口与双侧夹爪安装关系
│   ├── robots/malo_edu/
│   │   ├── malo_edu.xacro             本体装配宏
│   │   └── modules/                   底盘、躯干、左臂、右臂四模块
│   └── end_effectors/malo_pinch/      夹爪几何与手指联动
├── meshes/
│   ├── robots/malo_edu/               本体 CAD 网格
│   └── end_effectors/malo_pinch/      夹爪 CAD 网格
├── launch/display.launch.py           模型预览启动文件
├── rviz/model.rviz                    RViz 预览配置
└── test/                              模型、资源、装配及关节限制校验
```

## 使用说明

> **系统适配：** 当前支持 **ROS 2**。

### 构建与加载

将本包放入 ROS 2 工作区的 `src/` 下，在已加载 ROS 2 环境且依赖就绪的工作区根目录运行：

```bash
colcon build --symlink-install --packages-select zeno_malo_description
source install/setup.bash
```

### 模型预览

```bash
ros2 launch zeno_malo_description display.launch.py
```

默认启动 RViz 和关节滑块窗口。可追加 `gui:=false` 关闭关节滑块窗口，或追加 `rviz:=false` 关闭 RViz。

## 传感器说明

以下为传感器硬件规格及对应的 URDF 安装坐标系。

### 头部双目相机

- 安装坐标系：`stereo_camera_link`。
- 分辨率：双眼各自 **640 × 480**。
- 帧率：**30 Hz**。
- 对角线视场角（FOV）：**180°**。
- 双目基线：**6 cm**。

### 腕部单目相机

- 安装坐标系：左腕为 `left_gripper_camera_link`，右腕为 `right_gripper_camera_link`。
- 分辨率：每个相机 **640 × 480**。
- 帧率：**30 Hz**。
- 对角线视场角（FOV）：**175°**。

### 激光雷达

- 型号：**MID360**。
- 安装坐标系：`lidar_link`。
- `lidar_link` 通过固定关节连接 `base_link`，相对平移为 `(0.12, 0, 0.25505)` m，旋转为零；该 link 仅定义坐标系，无可视几何、碰撞体或惯性。
