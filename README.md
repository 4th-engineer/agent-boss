# Agent Boss

Multi-tab terminal manager for AI agents. Run `claude`, `hermes`, or any CLI agent in separate tabs with a clean GUI.

## Install

```bash
pip install -e .
```

Windows users also need:
```bash
pip install winpty
```

## Run

```bash
boss run
```

Or directly:
```bash
python -m agent_boss
```

## Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+T | New tab |
| Ctrl+W | Close tab |

## Buttons

- **🤖 Claude** - Start `claude --acp` in current tab
- **🧙 Hermes** - Start `hermes` in current tab
- **📁 New** - Create new terminal tab
