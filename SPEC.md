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

## 主题系统

### 概述
可选的主题系统，用户可通过 JSON 文件自定义界面颜色。内置 3 个主题，支持用户扩展。

### 内置主题
| 主题 | 描述 | 风格 |
|------|------|------|
| `default` | VSCode 深色 | 经典暗色 |
| `hacker` | 黑客绿 | 终端复古 |
| `ocean` | 海洋蓝 | 冷静蓝调 |

### 主题 JSON 格式
```json
{
  "name": "Theme Name",
  "description": "Description",
  "colors": {
    "bg": "#HEXCODE",
    "fg": "#HEXCODE",
    "tab_active": "#HEXCODE",
    "tab_inactive": "#HEXCODE",
    "toolbar": "#HEXCODE",
    "button_hover": "#HEXCODE",
    "statusbar": "#HEXCODE",
    "accent": "#HEXCODE",
    "border": "#HEXCODE"
  }
}
```

### 主题安装
- 内置主题：`agent_boss/themes/*.json`
- 用户主题：`~/.agentboss/themes/*.json`

### 切换主题
点击 ⚙️ 设置 → 选择主题

---

## 后续计划（Phase 2-4）

### Phase 2: 角色系统
- [x] 每个终端绑定一个 pixel avatar（默认 beaver）
- [x] 点击 👾 Avatar 按钮显示/隐藏 avatar
- [x] avatar 显示在终端右下角
- [x] 支持切换不同 avatar（beaver/robot/wizard/cat/dragon）
- [ ] avatar 与终端一一绑定，可独立选择
- [ ] 右键 avatar 弹出选择菜单

### Phase 3: 世界/房间
- [x] 房间管理（main/backend/frontend/devops）
- [x] RoomManager 管理房间 CRUD
- [x] MapView 图形化展示房间和成员
- [x] session 表增加 room_id / avatar_id 字段
- [ ] 拖拽分配 agent 到房间
- [ ] 房间视图与终端视图切换

### Phase 4: 交互系统
- [x] AgentDetailPanel 点击查看详情
- [x] 快速命令按钮（Status/Tasks/Ping）
- [x] 命令发送到 agent
- [x] TaskManager 任务系统
- [ ] 任务状态实时同步
- [ ] 多人协作/广播指令

---

## 验收标准

- [x] 主题系统支持切换（Phase 1 可选功能）
- [ ] 新建标签页可以启动独立 PowerShell 会话
- [ ] 多个标签页之间切换保持独立状态
- [ ] 点击「Claude」按钮在当前标签执行 `claude --acp`
- [ ] 点击「Hermes」按钮在当前标签执行 `hermes`
- [ ] 程序重启后恢复上次标签页
- [ ] 原生窗口控件正常工作（最小化/最大化/关闭）
