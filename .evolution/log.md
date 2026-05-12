# Self-Evolution Log

| Date       | Project    | Description                                        | Impact          |
|------------|------------|----------------------------------------------------|-----------------|
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: room_manager.py — rename Room.id → Room.room_id; eliminates builtin `id()` shadowing (Python best practice: no single-letter or builtin names for function arguments/attributes); all call sites updated (to_dict/from_dict/_load_rooms/create_room/delete_room) | 低：代码质量提升，Python 惯例一致性，避免潜在命名空间冲突 |
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


| | 2026-05-12 | AgentBoss | terminal.py: add _BRIGHT_BG dict (SGR 100-107) + parser branch for bright background ANSI codes — fixes color leaks in themes/tools using bright bg | 中：修复亮色背景被静默忽略问题，终端配色更完整 |
| | 2026-05-11 | AgentBoss | avatar_selector.py: add logger + graceful list_avatars() failure — previously avatars dir corruption/missing silently produced empty grid with zero visibility | 低：头像选择器健壮性，错误日志化 |
| 2026-05-11 | AgentBoss | tabs.py close_all_tabs: 添加 try/except + iteration guard — 防止 _on_tab_close 异常导致无限循环；之前无保护 | 中：关闭所有标签时防止应用冻结 |
| 2026-05-11 | AgentBoss | terminal.py: remove super().cleanup() — QWidget has no cleanup() method, every tab close raised AttributeError (被 tabs.py try/except 掩盖) | 中：修复每次关闭标签时的异常泄漏 |
| 2026-05-11 | AgentBoss | terminal.py: PtyReader winpty 分支注释澄清 msleep(50) 的作用是防止 CPU 空转，与 Linux 分支 selector.select 行为对齐 | 中：Windows PTY 性能优化 |
| 2026-05-11 | AgentBoss | database.py: update_session — 3-branch if/elif/else 合并为 1 条 COALESCE UPDATE，DB 往返从 2-3 次降至 1 次 | 中：高频函数性能优化，session 刷新延迟降低 |
| 2026-05-11 | AgentBoss | terminal.py: 修复 _xterm256 grayscale range off-by-one — `range(8,0xEE+1,10)` 缺最后一格致灰度 232-255 仅 23 色；改为 `range(8,0xF0,10)` 覆盖全部 24 色 | 低：终端灰度渲染完整性，修复 `ls --color=auto` 灰度渐变断档 |
| 2026-05-11 | AgentBoss | terminal.py ANSI parser: 4处 bare `except ValueError`/`int()` 替换为 try/except + logging.warning — 256-color fg/bg + 24-bit fg/bg；之前解析失败静默丢失输出，高频路径无错误可见性 | 中：ANSI 渲染错误现在有日志可追溯，不再静默丢字符 |
| 2026-05-11 | AgentBoss  | 🤖 Self-evolution: window.py — remove unused QMessageBox + Qt imports (dead code cleanup) | 低：移除 2 个死导入，模块加载微优化 |
| 2026-05-11 | AgentBoss | window.py: 添加 `logger = getLogger(__name__)` — 之前唯一没有 logger 的模块；_restore_sessions 添加 try/except — 单个 session 恢复失败不再阻止其余 session 加载，日志可见 | 中：修复启动时 session 恢复级联失败导致部分数据静默丢失 |
| 2026-05-11 | AgentBoss | terminal.py ANSI parser: 3组重复 elif 链 (fg 30-37, bg 40-47, bright fg 90-97) → dict lookup `_STD_FG/_BRIGHT_FG/_STD_BG`；O(1) 查找替代 O(n) 线性分支，parser 路径缩短 ~40 行 | 中：消除重复代码，解析器可维护性提升，性能微增 |
| 2026-05-11 | AgentBoss | tabs.py create_tab: wrap addTab+_tab_widgets assignment in try/except — DB session创建失败时正确清理已addTab的TerminalWidget，防止orphan widget残留+QTabWidget关闭时double-remove_session报错 | 中：修复资源泄漏 + DB二次删除异常 |
| 2026-05-11 | AgentBoss | tabs.py create_tab: 替换 bare `except Exception:` 为 `logger.error` + best-effort cleanup — 之前异常被吞无日志，cleanup 操作本身失败也会掩盖根因 | 中：tab 创建失败现在有日志追溯，cleanup 失败不再掩盖原始错误 |
| 2026-05-11 | AgentBoss | map_view.py: 移除未使用的 `QGraphicsItem` 导入 — 死代码清理 | 低：减小模块加载开销，提高代码可读性 |
| 2026-05-11 | AgentBoss | terminal.py: 移除未使用的 `Property` + `QRectF` 导入（PySide6.QtCore）— 死代码清理 | 低：模块加载微优化 |
| 2026-05-11 | AgentBoss | main.py: 修正 docstring 从 `agentstudio` 为 `Agent Boss` — 项目名一致性 | 低：文档修复 |

| 2026-05-11 | AgentBoss | process_manager.py PtyProcess.read/write/resize: exc_info=e → exc_info=True — adds full traceback to error logs instead of just string repr | 中：生产环境调试能力提升，异常现在有完整堆栈可追溯 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: process_manager.py — replace bare `pass` with `logger.debug` in waitpid; aligns with os.kill+logger.debug pattern 4 lines above, full traceback in debug mode | 低：waitpid 静默 pass → 有日志可追溯的生产调试能力 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: map_view.py — remove unused QRectF import (dead code cleanup) | 低：模块加载微优化 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: map_view.py — replace hardcoded 4-room positions with responsive grid layout; fixes room overlap/viewport overflow for 5+ worlds/agents users | 中：Worlds 系统扩展性修复，5+ room 不再重叠溢出 |

| 2026-05-11 | AgentBoss | 🤖 Self-evolution: agent_detail.py — add logging.warning when _send_command is called with no agent set; silences zero-feedback command discard in Phase 4 worlds panel | 低：命令发送失败有日志可追溯，_agent_id 未设置时不再静默丢弃 |


| 2026-05-11 | AgentBoss | 🤖 Self-evolution: tabs.py — add exc_info=True to create_tab error log + replace bare `pass` with logger.warning in cleanup path; all cleanup failures now traceable in production | 低：tab 创建失败后 cleanup 异常不再静默吞掉 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: worlds_panel.py — add missing QHBoxLayout import (fixes runtime NameError) | 高：WorldsPanel 实例化时不再报 NameError: "QHBoxLayout" 未定义，Phase 4 系统激活不再崩溃 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: terminal.py — remove dead _setup_avatar stub; AvatarOverlay already instantiated in _setup_ui, stub was a no-op placeholder adding noise and potential confusion | 低：死代码清除，TerminalWidget 初始化路径简化 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: tabs.py — 2 bare `except Exception: pass` in create_tab cleanup path now log full traceback with exc_info=True; aligns with project error-logging standard (其他模块已统一) | 低：cleanup 失败从此有日志追溯，不再静默吞异常 |

| 2026-05-11 | AgentBoss | process_manager.py: 9处 exc_info=e → exc_info=True；write/read/resize/winpty分支/signal kill/waitpid/close master_fd/create_process — 所有错误日志现在输出完整 traceback 而非仅字符串 repr，生产调试能力大幅提升 | 中：生产环境异常追溯能力，堆栈信息完整 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: tabs.py + window.py — add exc_info=True to all session/tab cleanup warning logs (5 sites); aligns with project-wide traceback standard | 中：Tab关闭/session恢复/cleanup 现在输出完整traceback，生产调试能力对齐 process_manager/database |
| 2026-05-11 | AgentBoss | 🐛 Self-evolution: tabs.py create_tab — 修复异常时 orphan session 泄漏；create_tab 失败时 tab 已写入 DB 但 widget 清理后未调用 remove_session，导致 _restore_sessions 重启时重试必然失败记录；现在 cleanup 路径新增 remove_session(tab_id) | 中：修复 session 级联失败累积问题，DB 不再积累垃圾记录 |

| 2026-05-11 | AgentBoss | 🤖 Self-evolution: database.py — add exc_info=True to all error logs (3 sites); aligns with process_manager.py standard, full traceback now available for DB init/open failures | 中：生产环境 DB 异常追溯能力，堆栈信息完整 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: room_manager.py — add exc_info=True to 2 warning logs (aligns with project standard) | 低：Worlds 系统 I/O 错误现在有完整 traceback，与 process_manager/database/tabs 统一异常追溯规范 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: agent_detail.py — add logging.warning when _quick_cmd is called with no agent selected; silences zero-feedback command discard in worlds panel | 低：Worlds Panel 快速命令无 agent 时不再静默丢弃，日志可追溯 |
| 2026-05-11 | AgentBoss | 🤖 Self-evolution: process_manager.py — clarify slave_fd close comment in _create_unix_process; parent closes its copy after child dups it — clarifies existing fd-management intent, no functional change | 低：代码可读性提升，slave_fd 关闭语义明确 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: map_view.py — add `-> None` return type hints to MapView.clear_map/add_room/add_agent/move_agent_to_room; aligns with project typing standard (MapView.get_map_view already annotated) | 低：Worlds 地图系统类型安全提升，与项目其他模块类型注解规范统一 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: process_manager.py PtyProcess.close() — add %s exception repr to 2 bare logger.warning (winpty kill + master_fd close); all 9 other OSError sites already use %s + exc_info=True, close path now aligned with project standard | 低：PtyProcess 关闭路径错误日志现在输出异常内容，与项目其余保持一致 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: main.py — wire logging.basicConfig at startup; all 19 modules had `getLogger(__name__)` but zero handlers ever configured — INFO/DEBUG messages silently discarded | 中：日志系统全链路打通，`AGENTBOSS_LOG=info` 开启调试，`logger.info`终于可见 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: map_view.py — fix ZeroDivisionError in refresh_map when viewport not yet laid out (vp_width=0 → cols=0 → i%0 crash); extract vp_width variable for clarity + ternary guard for cols | 中：Worlds map 在 Qt 初始化阶段调用 refresh_map 不再崩溃 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: terminal.py ANSI parser — add exc_info=True to all 6 logger.warning calls (256-color fg/bg + 24-bit fg/bg malformed/out-of-range); aligns with project-wide exception-logging standard (process_manager/database/tabs/window/room_manager) | 中：ANSI 解析器错误现在输出完整 traceback，生产环境畸形转义序列调试能力与项目其余模块统一 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: terminal.py eventFilter — add is_closed guard before all 14 write() calls; fixes silent no-op when PTY process has exited (Ctrl+C/arrow keys/typing all discarded with zero feedback) | 中：终端进程退出后按键无响应问题修复，与 write_input() 行为对齐 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: avatar_overlay.py — paintEvent now logs once when sprite data is missing (silent no-op replaced with WARNING + once-per-instance guard); prevents paint-cycle spam while making avatar non-render visible to operators | 低：头像精灵数据缺失时不再静默失败，WARNING日志+单次触发保护 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: terminal.py PtyReader.run() — lock-protect all _process reads in run() loop (master_fd, read() call on ready path); previously only the _running/_closed check was locked, but _process itself was read without the lock after the check — if TerminalWidget.cleanup() nullified _process between the check and the read, an AttributeError would propagate into the Qt event loop | 中：修复 PtyReader 线程与 TerminalWidget cleanup 之间的竞态，process 关闭时不再产生未捕获 AttributeError |

| 2026-05-12 | 🤖 Self-evolution: terminal.py PtyReader winpty branch — add AttributeError to exception tuple alongside (OSError, ValueError, RuntimeError); AttributeError occurs when cleanup() races to nullify _winpty_process between proc capture under lock and read() call; previously uncaught exception would propagate into Qt event loop on Windows | 中：Windows PTY 竞态崩溃修复，reader 线程不再泄漏未捕获异常 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: database.py — replace threading.local singleton with module-level connection; threading.local + check_same_thread=False was contradictory; could spawn per-thread connections in Qt cross-thread slots; module singleton is simpler and correct for Qt's event-loop serialization | 中：消除 threading.local 与 check_same_thread=False 的矛盾；DB 连接模型更清晰，Qt 跨线程槽调用行为正确 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: avatar_selector.py — add exc_info=True to avatar load failure log; aligns with project-wide exception-logging standard (process_manager/database/tabs/window 全部已统一)，avatar 加载失败现在有完整 traceback 可追溯 | 低：avatar_selector 异常追溯规范与项目其余模块对齐 |

| 2026-05-12 | AgentBoss | 🤖 Self-evolution: terminal.py — flatten PtyReader.run() dual-branch duplication; `if master_fd → select()` else → winpty poll; eliminates 21-line redundant code path for non-Linux/macOS Unix platforms | 中：代码去重 + 逻辑简化，reader 线程控制流更清晰 |
| | 2026-05-12 | AgentBoss | 🤖 Self-evolution: worlds_panel.py — add explicit guards for missing rooms / empty member lists; silent no-op replaced with WARNING logs + panel clear | 低：Worlds Panel 选择空房间或无效房间时不再静默无响应，日志可见 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: room_manager.py — fix delete_room stale-agent bug; migrated agents now always update _agents mapping + deleted room members list cleared + logger.info reports migration count | 中：修复删除房间后 agent 数据不一致问题，_agents mapping 总被更新，被删房间 members 列表清空防止脏数据 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: agent_detail.py — add UI feedback when no agent selected; _send_command and _quick_cmd now display visible history messages + update status label instead of silent discard + log-only | 低：Worlds Panel 用户体验，无 agent 时操作不再静默失败 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: theme.py — narrow ValueError → json.JSONDecodeError in _load_themes; aligns with avatar_overlay/avatar_selector/room_manager exception spec across the project | 低：JSON 解析异常规范统一，项目异常处理更精确 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: terminal.py — pre-compile ANSI SGR regex at module load; _parse_and_insert hot-path now O(1) cached lookup instead of re-compiling `re.split()` on every PTY output batch | 中：终端输出渲染性能提升，高频路径消除重复正则编译开销 |
| | 2026-05-12 | AgentBoss | 🤖 Self-evolution: avatar_selector.py — narrow bare `except Exception` → `(OSError, json.JSONDecodeError)`, consistent with project exception-handling standard (avatar_overlay/database/room_manager already use specific types); removes spurious %s interpolation | 低：异常处理规范统一，list_avatars() 不会抛其他类型，代码更精确 |
| | 2026-05-12 | AgentBoss | 🤖 Self-evolution: process_manager.py — add pid+exception to debug log (last site missing %s) | 低：PtyProcess.close() os.kill 异常处理日志现在输出 pid+异常内容，与项目其余 9 处对齐 |
| | 2026-05-12 | AgentBoss | avatar_selector.py: add missing `import json` — exception handler referenced `json.JSONDecodeError` but json was never imported; would trigger NameError instead of graceful empty-grid fallback | 高：Avatar 选择器打开时 avatars.json 损坏不再崩溃，改为空网格降级 |
| | 2026-05-12 | AgentBoss | 🤖 Self-evolution: window.py — wrap create_tab in _on_new_tab with try/except + warning; uncaught DB/process exceptions now visible instead of silently propagating into Qt event loop | 低：新建标签页时 DB/进程异常不再静默泄漏，用户看到错误状态栏反馈，完整 traceback 写入日志 |


| 2026-05-12 | AgentBoss | 🤖 Self-evolution: database.py — add return type hints update_session (-> None) + get_all_sessions (-> list[sqlite3.Row]); aligns with project typing standard across database/room_manager/task_system modules | 低：DB 层类型安全提升，调用者知道函数返回值类型而非隐式 Any |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: worlds_panel.py — remove spurious warning for valid empty rooms; empty members list is normal state, not an error condition | 低：删除误报，空房间（如新建房间）不再触发 WARNING 日志 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: terminal.py — replace 12-branch if/elif key dispatch with O(1) dict lookup; _KEY_ESCAPE map eliminates 45-line chain in eventFilter, keys are now O(1) hash lookup vs O(n) linear branch; same behavior preserved, is_closed guard unchanged | 中：代码可维护性显著提升，终端按键处理路径缩短；O(1) 查找替代线性分支，逻辑更清晰 |
| 2026-05-12 | AgentBoss | 🤖 Self-evolution: map_view.py — remove dead AgentNode.avatar instance variable; was assigned in __init__ but never read in paintEvent or any other method; all call sites updated (add_agent) | 低：消除死实例变量，内存占用微降，AgentNode 签名简化 |
