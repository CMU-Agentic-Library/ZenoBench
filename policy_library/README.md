# Low-level Policy Library

这里为现有 64 个公开控制入口提供 `policy_001` 到 `policy_064`
的稳定公开 ID。每个 `policies/<id>/` 目录包含 `policy.json`
和 `POLICY.md`，记录控制器范围、实际 `execute()` 参数、绑定类、
验证状态以及关联 Contract。[catalog.json](catalog.json) 是索引。

运行时用 `PolicySuite(rig).policy_010.execute(...)` 调用，也可继续用
旧名 `PolicySuite(rig).pick_top.execute(...)`。现有 Python 类名保留，
避免破坏仿真控制代码；公开目录和手动 CLI 接受新的 policy ID。
[ID 对照](../docs/INTERFACE_IDS.md) 列出新旧名称。

`effect_summary` 是原能力目录的摘要，不自动成为上层 Contract 保证。
各 policy 的具体适用条件仍在控制器内部检查；记录中的
`policy_specific_preconditions` 明确表示这部分尚未全部规范化。
`callable` 表示代码入口存在，但当前没有该路线的独立成功实跑。

记录由 `python tools/export_interface_libraries.py` 生成；
用 `--check` 检查是否与可执行注册表一致。
