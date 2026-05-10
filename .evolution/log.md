# Self-Evolution Log

| Date       | Project    | Description                                        | Impact          |
|------------|------------|----------------------------------------------------|-----------------|
| 2026-05-10 | AgentBoss  | 修复 PtyProcess.read() 静默吞异常：winpty 分支从 bare Exception 缩小到 (OSError, ValueError, TypeError) | 中：防止编程错误被静默吞掉 |
| 2026-05-10 | AgentBoss  | room_manager.py wraps _load_rooms and _save_rooms with try/except + logging.warning — handles corrupted rooms.json gracefully | 中：防止 worlds 系统崩溃 |
| 2026-05-10 | AgentBoss  | 替换 terminal.py 中 3 处 print() 为 logging.warning | 中：PTY 错误处理日志化 |
| 2026-05-10 | AgentBoss  | 统一 terminal.py 两处 logging.warning 为 %-format 风格（与项目其余保持一致） | 低：代码风格一致性 |
| 2026-05-10 | AgentBoss  | 替换 avatar/theme/worlds_panel 中 3 处 print() 为 logging | 中：覆盖层/主题/面板调试残留清除 |
| 2026-05-10 | AgentBoss  | 修复 unassigned_agents() 逻辑：改用 main.members 而非 _agents 作为真相源 | 中：修复 room_manager 核心查找逻辑 |
| 2026-05-10 | AgentBoss  | 修复 list_avatars() 静默失败：添加 logging.warning 记录 JSON/OSError | 低：调试可追溯性提升 |
| 2026-05-10 | AgentBoss  | 移除 theme.py 中未使用的 `import os` | 低：清理死代码 |
| 2026-05-10 | AgentBoss  | 缩小 PtyProcess.write/resize 中的 bare Exception 为具体类型 (OSError, ValueError, TypeError) | 中：防止编程错误被静默吞掉 |
| 2026-05-10 | AgentBoss  | avatar_overlay.py adopts logger = getLogger(__name__) pattern (fixes bare logging.warning in list_avatars) | 中：统一项目日志规范 |
