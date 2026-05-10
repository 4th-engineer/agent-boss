# Self-Evolution Log

| Date       | Project    | Description                                        | Impact          |
|------------|------------|----------------------------------------------------|-----------------|
| 2026-05-10 | AgentBoss  | process_manager.py: shrink 2x bare Exception → (OSError, ValueError) in create_process/_create_windows_process | 中：统一项目异常处理规范，防静默吞掉非预期错误 |
| 2026-05-10 | AgentBoss  | avatar_overlay.py: narrow _load_avatar bare Exception → (OSError, json.JSONDecodeError) | 低：缩小异常范围，防止意外被吞 |
| 2026-05-10 | AgentBoss  | room_manager.py wraps _load_rooms and _save_rooms with try/except + logging.warning — handles corrupted rooms.json gracefully | 中：防止 worlds 系统崩溃 |
| 2026-05-10 | AgentBoss  | 替换 terminal.py 中 3 处 print() 为 logging.warning | 中：PTY 错误处理日志化 |
| 2026-05-10 | AgentBoss  | 统一 terminal.py 两处 logging.warning 为 %-format 风格（与项目其余保持一致） | 低：代码风格一致性 |
| 2026-05-10 | AgentBoss  | 替换 avatar/theme/worlds_panel 中 3 处 print() 为 logging | 中：覆盖层/主题/面板调试残留清除 |
| 2026-05-10 | AgentBoss  | terminal.py: PtyReader.stop() now acquires lock before writing _running flag — eliminates stop/run data race; was a latent race in cleanup path | 中：修复线程安全竞态，防止 cleanup 时标志位不一致 |
| 2026-05-10 | AgentBoss  | 修复 list_avatars() 静默失败：添加 logging.warning 记录 JSON/OSError | 低：调试可追溯性提升 |
| 2026-05-10 | AgentBoss  | 移除 theme.py 中未使用的 `import os` | 低：清理死代码 |
| 2026-05-10 | AgentBoss  | 缩小 PtyProcess.write/resize 中的 bare Exception 为具体类型 (OSError, ValueError, TypeError) | 中：防止编程错误被静默吞掉 |
| 2026-05-10 | AgentBoss  | avatar_overlay.py adopts logger = getLogger(__name__) pattern (fixes bare logging.warning in list_avatars) | 中：统一项目日志规范 |
| 2026-05-10 | AgentBoss  | PtyReader winpty branch now wrapped with try/except + logging.warning — aligns with Linux path's error coverage | 中：PTY 跨平台健壮性 |
| 2026-05-10 | AgentBoss  | theme.py _load_themes: narrow except Exception → (OSError, ValueError) — 与 avatar_overlay/room_manager 一致的异常处理规范 | 低：缩小异常范围，防止误吞非JSON错误 |
| 2026-05-10 | AgentBoss  | terminal.py ANSI parser: add SGR 2-9 (dim/italic/underline/blink/reverse/conceal/strike) + 38/48 extended color (256-color + 24-bit true-color) | 高：ls --color/git diff/htop 等主流命令不再泄漏裸转义序列 |
| 2026-05-10 | AgentBoss  | database.py: add logging + error handling to init_db and get_connection — previously zero visibility on DB failures | 中：磁盘满/权限错误/损坏 DB 现在有日志可追溯，启动失败不再静默吞异常 |
| 2026-05-10 | AgentBoss  | worlds/map_view.py: MapView.mousePressEvent now calls event.accept() after RoomItem/AgentNode click — fixes double-fire bug where child item click propagated to parent, emitting signals twice | 中：修复 world map 点击时信号重复触发的竞态/传播问题 |
