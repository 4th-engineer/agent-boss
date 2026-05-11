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
| 2026-05-10 | AgentBoss  | 移除 theme.py 中未使用的 self._app = app（ThemeManager 构造函数中的死代码） | 低：清理无用实例变量，减小对象内存占用 |
| 2026-05-10 | AgentBoss  | tabs.py: _on_tab_close 三个操作全部包 try/except — remove_process/remove_session/cleanup 任意失败不再导致部分清理 + 静默资源泄漏 | 中：关闭标签页时的进程/DB/Widget 资源泄漏问题修复 |
| 2026-05-11 | AgentBoss  | terminal.py: ANSI 256-color parser — add ValueError guard + bounds check for color index before _xterm256 lookup; prevents IndexError from malformed escape sequences (e.g. \x1b[38;5;999m) | 中：防终端输出非法颜色代码导致 Qt 事件循环崩溃 |


| 2026-05-11 | AgentBoss | avatar_selector.py: add logger + graceful list_avatars() failure — previously avatars dir corruption/missing silently produced empty grid with zero visibility | 低：头像选择器健壮性，错误日志化 |
| 2026-05-11 | AgentBoss | tabs.py close_all_tabs: 添加 try/except + iteration guard — 防止 _on_tab_close 异常导致无限循环；之前无保护 | 中：关闭所有标签时防止应用冻结 |
| 2026-05-11 | AgentBoss | terminal.py: remove super().cleanup() — QWidget has no cleanup() method, every tab close raised AttributeError (被 tabs.py try/except 掩盖) | 中：修复每次关闭标签时的异常泄漏 |
| 2026-05-11 | AgentBoss | terminal.py: PtyReader winpty 分支注释澄清 msleep(50) 的作用是防止 CPU 空转，与 Linux 分支 selector.select 行为对齐 | 中：Windows PTY 性能优化 |
| 2026-05-11 | AgentBoss | database.py: update_session — 3-branch if/elif/else 合并为 1 条 COALESCE UPDATE，DB 往返从 2-3 次降至 1 次 | 中：高频函数性能优化，session 刷新延迟降低 |
| 2026-05-11 | AgentBoss | terminal.py: 修复 _xterm256 grayscale range off-by-one — `range(8,0xEE+1,10)` 缺最后一格致灰度 232-255 仅 23 色；改为 `range(8,0xF0,10)` 覆盖全部 24 色 | 低：终端灰度渲染完整性，修复 `ls --color=auto` 灰度渐变断档 |
| 2026-05-11 | AgentBoss | terminal.py ANSI parser: 4处 bare `except ValueError`/`int()` 替换为 try/except + logging.warning — 256-color fg/bg + 24-bit fg/bg；之前解析失败静默丢失输出，高频路径无错误可见性 | 中：ANSI 渲染错误现在有日志可追溯，不再静默丢字符 |
| 2026-05-11 | AgentBoss | task_system.py + agent_detail.py: add logger + structured logging — task creation/status transitions logged; agent commands logged at info level; update_status missing task returns warning | 低：TaskManager 和 AgentDetailPanel 从此有日志可追溯 |
| 2026-05-11 | AgentBoss | window.py: 添加 `logger = getLogger(__name__)` — 之前唯一没有 logger 的模块；_restore_sessions 添加 try/except — 单个 session 恢复失败不再阻止其余 session 加载，日志可见 | 中：修复启动时 session 恢复级联失败导致部分数据静默丢失 |
| 2026-05-11 | AgentBoss | terminal.py ANSI parser: 3组重复 elif 链 (fg 30-37, bg 40-47, bright fg 90-97) → dict lookup `_STD_FG/_BRIGHT_FG/_STD_BG`；O(1) 查找替代 O(n) 线性分支，parser 路径缩短 ~40 行 | 中：消除重复代码，解析器可维护性提升，性能微增 |
| 2026-05-11 | AgentBoss | tabs.py create_tab: wrap addTab+_tab_widgets assignment in try/except — DB session创建失败时正确清理已addTab的TerminalWidget，防止orphan widget残留+QTabWidget关闭时double-remove_session报错 | 中：修复资源泄漏 + DB二次删除异常 |
| 2026-05-11 | AgentBoss | tabs.py create_tab: 替换 bare `except Exception:` 为 `logger.error` + best-effort cleanup — 之前异常被吞无日志，cleanup 操作本身失败也会掩盖根因 | 中：tab 创建失败现在有日志追溯，cleanup 失败不再掩盖原始错误 |
| 2026-05-11 | AgentBoss | map_view.py: 移除未使用的 `QGraphicsItem` 导入 — 死代码清理 | 低：减小模块加载开销，提高代码可读性 |
| 2026-05-11 | AgentBoss | terminal.py: 移除未使用的 `Property` + `QRectF` 导入（PySide6.QtCore）— 死代码清理 | 低：模块加载微优化 |
| 2026-05-11 | AgentBoss | main.py: 修正 docstring 从 `agentstudio` 为 `Agent Boss` — 项目名一致性 | 低：文档修复 |

| 2026-05-11 | AgentBoss | process_manager.py PtyProcess.read/write/resize: exc_info=e → exc_info=True — adds full traceback to error logs instead of just string repr | 中：生产环境调试能力提升，异常现在有完整堆栈可追溯 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: room_manager.py — add structured logging to create_room/delete_room/assign_agent; zero observability on world state changes | 中：Worlds 系统所有状态变更操作现在有日志可追溯，调试/审计不再黑盒 |

| 2026-05-11 | AgentBoss | 🤖 Self-evolution: process_manager.py — fix exc_info=e → exc_info=True in PtyProcess.close() winpty branch; aligns with write/read/resize which already use exc_info=True; ensures full traceback in production error logs | 中：生产环境调试能力提升，winpty kill 异常现在有完整堆栈可追溯 |
| 2026-05-11 | AgentBoss | main.py + __main__.py: add top-level Exception handler + logger; catches Qt event loop crashes that would otherwise silently terminate — logs critical with full traceback before exit | 高：启动/运行时异常不再静默消失；新增优雅关闭日志（exit_code 可追溯）|

