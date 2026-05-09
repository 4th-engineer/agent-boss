# Agent Boss

Windows 终端管理器，为 PowerShell 套上外壳，提供多标签页、快捷启动 agent。

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python -m src.main
```

## 功能

- 多标签 PowerShell 终端
- 快捷启动 Claude / Hermes
- 会话持久化（SQLite）
- 键盘快捷键

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+T | 新建标签 |
| Ctrl+W | 关闭标签 |

## 依赖

- PySide6 >= 6.6.0
- pywinpty >= 2.0.0

## Phase 2 计划

- 像素角色 avatar 系统
- 地图视图
- agent 任务状态可视化
