# Self-Evolution Log

| Date       | Project    | Description                                        | Impact          |
|------------|------------|----------------------------------------------------|-----------------|
| 2026-05-10 | AgentBoss  | 替换 process_manager.py 中 13 处 print() 为 logging | 高：统一日志输出 |
| 2026-05-10 | AgentBoss  | 替换 terminal.py 中 3 处 print() 为 logging.warning | 中：PTY 错误处理日志化 |
| 2026-05-10 | AgentBoss  | 替换 avatar/theme/worlds_panel 中 3 处 print() 为 logging | 中：覆盖层/主题/面板调试残留清除 |
| 2026-05-10 | AgentBoss  | 修复 unassigned_agents() 逻辑：改用 main.members 而非 _agents 作为真相源 | 中：修复 room_manager 核心查找逻辑 |
