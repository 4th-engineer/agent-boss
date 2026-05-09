# Agent Boss - Phase 1 规格文档

## 概述

**项目目标：** Windows 本地终端管理器，为 PowerShell 套上外壳，提供多标签页、快捷启动 agent、可视化增强。

**技术栈：**
- Python 3.11+
- PySide6 (Qt6) — 跨平台 GUI 框架
- pywinpty — Windows PTY 绑定（Windows only）
- pty module — Linux/macOS 内置
- SQLite — 会话持久化

**定位：** Phase 1 只做终端管理器，后续叠加像素角色系统。

---

## 界面设计

### 窗口布局

```
┌────────────────────────────────────────────────────────┐
│  agentstudio                           [─] [□] [×]    │
├────────────────────────────────────────────────────────┤
│  [🤖 Claude] [🧙 Hermes] [📁 新建] [⚙ 设置]             │
├────────────────────────────────────────────────────────┤
│  [标签1 PowerShell] [标签2 PowerShell] [+]             │
├────────────────────────────────────────────────────────┤
│                                                        │
│  PS C:\Users\YeLei> _                                  │
│                                                        │
│                                                        │
│                                                        │
│                                                        │
│                                                        │
├────────────────────────────────────────────────────────┤
│  就绪                                                  │
└────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 描述 |
|------|------|
| 标题栏 | 原生窗口控件（最小化/最大化/关闭） |
| 工具栏 | 快捷按钮：启动 Claude / 启动 Hermes / 新建标签 / 设置 |
| 标签栏 | 多标签页，支持关闭和新建 |
| 终端区域 | 每个标签页内的 PowerShell 会话（pywinpty 驱动） |
| 状态栏 | 当前终端状态、快捷命令提示 |

---

## 功能列表

### 核心功能

1. **多标签终端**
   - 新建标签 → 启动独立 PowerShell 进程
   - 关闭标签 → 确认后终止进程
   - 切换标签 → 独立会话状态

2. **快捷启动 Agent**
   - 点击「🤖 Claude」→ 在当前标签执行 `claude --acp`
   - 点击「🧙 Hermes」→ 在当前标签执行 `hermes`
   - 前提：claude / hermes 已安装并在 PATH 中

3. **终端交互**
   - 实时输入/输出（pty 流式）
   - 支持 Ctrl+C 中断
   - 支持复制粘贴

4. **会话持久化**
   - SQLite 记录标签页状态
   - 重启后恢复上次的标签页数量
   - 每次标签页的 cwd 记忆

### Phase 1 暂不包含

- 像素角色系统（Phase 2）
- 世界地图视图（Phase 2）
- agent 任务/TODO 同步（Phase 2）

---

## 数据模型

### SQLite Schema

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tab_id TEXT UNIQUE NOT NULL,      -- 标签页唯一 ID (UUID)
    tab_title TEXT NOT NULL,          -- 标签显示名称
    working_dir TEXT,                 -- 上次工作目录
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active_at DATETIME
);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

---

## 项目结构

```
agentstudio/
├── SPEC.md
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py              # 入口
│   ├── window.py            # 主窗口
│   ├── terminal.py         # 终端组件
│   ├── tabs.py             # 标签页管理
│   ├── toolbar.py          # 工具栏
│   ├── process_manager.py  # 进程管理
│   └── database.py         # SQLite 封装
├── assets/
│   └── icon.ico
└── build/                   # 打包输出
```

---

## 依赖

```
PySide6>=6.6.0
pywinpty>=2.0.0
```

---

## 验收标准

- [ ] 新建标签页可以启动独立 PowerShell 会话
- [ ] 多个标签页之间切换保持独立状态
- [ ] 点击「Claude」按钮在当前标签执行 `claude --acp`
- [ ] 点击「Hermes」按钮在当前标签执行 `hermes`
- [ ] 程序重启后恢复上次标签页
- [ ] 原生窗口控件正常工作（最小化/最大化/关闭）

---

## 后续计划（Phase 2）

- 像素角色 avatar 叠加在终端上
- agent 任务状态实时显示
- 地图视图展示所有 agent
