# mark_spots（在支撑面上标出可放的位置）

给 VLM 用的 visual prompting：拿着东西时，把一整张桌面放进头部相机的一帧画面，在图上用编号圆点标出几个可以放的空位。VLM 看图选一个号，再用原来的 place 放过去：

```
mark_spots(object, support)                       → outputs.spots = [[x, y], ...]，图上第 n 号 = spots[n-1]
place(object, receptacle=support, hint_xy=spots[k-1])   原来的 place，一行没改
```

这是两个 skill，不是一个 skill 调两次：`mark_spots` 只看、只标，不放（`skill_072` / `contract_080`，policy `policy_117` + `policy_118`，2026-11-15）。

## 步骤

**看全桌面**（`perceive.ViewSupportPolicy`，`policy_117`）

1. 拿着东西时先摆好搬运姿态（和 navigate 拿着东西开车一样，`carry_posture`，底部高过这张桌面）。
2. **现在站的位置**离桌面不超过 `base_near` 的 1.3 m、并且整张桌面都看得见，就不动。
3. 否则在 navigate 用的那组停车点里找（`base_motion.standoff_poses`：桌面周围一圈，都在 1.3 m 以内，整机在行驶姿态下不碰），只留底盘开得到的（`skills.base_reachable`，一次可达场），按 navigate 的顺序（离现在近的先）挨个算：头按 look 的瞄法对准桌面中心，或者沿视线往近处、远处挪桌面半对角线的 0.4 倍（`AIM_FRACS`：头最多往下低 18°，近的桌面要瞄得更近），看桌面 5×5 个采样点（四个角都在里面，比板面高 1 cm）有几个在画面里（视野四边各缩 8%，`VIEW_MARGIN`）、视线不被家具框挡（`_segment_blocked`）。第一个全看得见的胜出；都看不全就选看到最多的。
4. 开过去（`skills.navigate`），到了以后按实际停的位置重新瞄，头转过去，停在那里不摆正：下一次 observation 的普通 head 图和打点图是同一个视角。
5. 输出 `coverage`：桌面看见了几成（1 = 全部）。

几何上（benchmark 相机，水平 92°、垂直 76°；躯干升到顶时相机离地 1.32 m）：垂直方向不是问题（0.71 m 高的餐桌站在 0.41 m 外就看得到近边），限制在水平方向——1.65 m 的书桌要站到近边 0.8 m 外，2 m 长的餐桌从长边看要 0.96 m，2.5 m 长的靠墙台面要 1.2 m，可能被别的家具挡住，这时 `coverage < 1`，只在看得见的部分打点。

**打点**（`perceive.MarkSpotsPolicy`，`policy_118`，`visual_prompt.mark_spots`）

6. **空位**：`free_spots` 的同一套判据（物体任意朝向都放得下，离其他物体先留 7 cm、没有再 4.5 cm、2 cm；台面离开放的边 4 cm），全部取出来，再按 6 cm 的网格每格留排名最前的一个（`thin`）：`free_spots` 按离机器人远近排，只取前 400 个时 2.46 m 长的餐桌远的一半一个点都没有（11-15 T20）。
7. 只留 place 会**照原样**接受的点：`skills.hint_spot_free`，就是 `free_spots` 判断 hint 的那段（从 `free_spots` 里抽出来的，行为不变）——VLM 选了 3 号，place 的第一个空位就是 3 号本身。坐标取到毫米再判断，输出的就是判断过的值。
8. 只留**看得见**的：从头部相机的镜头（`stereo_camera_link` 前方 4 cm）到点的视线不被家具框、别的物体（按物体的占地和高度围的框）挡住；投到画面里，离四边不到画面宽度的 4%（`EDGE_FRAC`）的不要。机器人自己的手臂和手里的物体**不查**：点画在手里的物体上也没关系（用户 11-15；11-15 T20 有两个点画在了手里的瓶子上）。
9. **拉开**：最远点采样，第一个是 `free_spots` 排的第一个（离机器人最近），之后每次加离已选的最远的，间距不小于 12 cm 和物体的长边，最多 6 个（`MAX_SPOTS`）。
10. **画**：投影用渲染这张图的 Isaac 相机自己的内参（`CameraData.intrinsic_matrices`），位姿按仿真里实测的底盘、躯干、腰、头的关节角走 URDF 头部链到 `stereo_camera_link`，再加相机挂在它前方的 4 cm（`visual_prompt.head_camera_ros`）。不用 Isaac 相机自己的位姿：`CameraCfg.update_latest_camera_pose` 关着，它不随图更新；手动读到的是 USD 里机器人出生时的位姿，在 6 m 外（11-15 T20 / T24：两个 episode 读出同一个相机位姿，6 个点挤在一处）。每个点一个红底白边的编号圆（640 宽的图半径 11 px，随宽度缩放），外面一圈白线是物体长边一半为半径的占地。
11. 没有一个点留下就失败。

**图怎么到 VLM**

画好的图放在 `rig.memory["visual_prompt"]`，下一次 observation（`episode.Episode._images`）取出来追加在普通图片后面，只给一次：

```json
{"camera": "head", "png_base64": "..."},
{"camera": "head", "overlay": "place_spots", "png_base64": "..."}
```

`encode="path"` 时存成 `obs<NNN>_<tag>_head_place_spots.png`。profile 不开 head 相机时没有图，`spots` 照样返回（可见性按 `project_to_head_camera` 判）。

## 已知问题

- **benchmark 的空位用的是 GT**：桌上没被看见过的物体也会被避开。站到看全桌面的位置以后桌上的东西基本都在视野里，影响很小。
- **place 不保证放在选的那个点上**：`hint_xy` 是 place 空位列表的第一个，这个点做不出放置计划时 place 会用附近的其他空位（`place.md` 第 1 步），结果检查是离目标 10 cm 以内。
- **选点不看任务**：6 个点在整个支撑面上用最远点采样拉开，"放在某个东西旁边 15 cm 以内"这类要求常常没有点落在那里。11-15 仿真检查（`/data/zenobench/vp_1115/choose`，v6 sticky/gt 种子 10，只跑到 mark_spots）：T01 `reader_seat__mug_2` 6 个点里只有 1 个满足要求，T21 `the_kids_side__kid_north` 一个都没有（最近的离孩子的杯子 22 cm）。打算改成每个物体旁边各标空位。
- **视角**：现在站的位置看得全就不动，判据只看桌面在不在画面里，不看清不清楚。两个 episode 都停在长桌一端，相机 1.07 m 高（躯干没升），远处的点挤在一起、互相重叠。打算先升躯干，再按画面里的分辨率选停车点（偏向长边）。
- 11-15 早先的检查（`vp_1115/run4`，这次去掉的机器人自身遮挡检查之前）：T20、T24 选 2 号点，place 成功，落点离所选点 2.9 / 3.3 cm（T20 很可能放在了旁边 3 cm 的网格点上：hint 只是 place 目标集合里代价最低的那个）。
