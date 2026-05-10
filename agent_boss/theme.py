"""Theme system for Agent Boss.

Themes are JSON files with color definitions. Users can add custom themes
by placing JSON files in ~/.agentboss/themes/ or the bundled themes/ directory.
"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


DEFAULT_THEME = "default"


class ThemeManager:
    """Manages themes and applies them to the UI."""

    def __init__(self, app=None):
        self._app = app
        self._current_theme = None
        self._themes_dir = self._get_themes_dir()
        self._themes: dict[str, dict] = {}
        self._load_themes()

    def _get_themes_dir(self) -> Path:
        """Get themes directory, prioritizing user config over bundled."""
        # User themes: ~/.agentboss/themes/
        user_dir = Path.home() / ".agentboss" / "themes"
        # Bundled themes: <package>/themes/
        bundled_dir = Path(__file__).parent / "themes"
        return user_dir if user_dir.exists() else bundled_dir

    def _load_themes(self):
        """Load all theme JSON files from themes directory."""
        themes_dir = self._themes_dir
        if themes_dir.exists():
            for file in themes_dir.glob("*.json"):
                try:
                    with open(file) as f:
                        theme = json.load(f)
                        name = file.stem
                        self._themes[name] = theme
                except (OSError, ValueError) as e:
                    logger.warning("Failed to load theme %s: %s", file, e)

    def list_themes(self) -> list[str]:
        """Return list of available theme names."""
        return list(self._themes.keys())

    def get_theme(self, name: Optional[str] = None) -> dict:
        """Get theme by name, or current theme if None."""
        if name is None:
            name = self._current_theme or DEFAULT_THEME
        return self._themes.get(name, self._themes.get(DEFAULT_THEME, {}))

    def apply_theme(self, window, name: Optional[str] = None):
        """Apply theme to the main window."""
        theme = self.get_theme(name)
        if not theme:
            return

        self._current_theme = name if name else DEFAULT_THEME
        colors = theme.get("colors", {})

        # Build stylesheet
        styles = f"""
            QMainWindow {{ background: {colors.get("bg", "#1E1E1E")}; }}
            QWidget {{ background: {colors.get("bg", "#1E1E1E")}; color: {colors.get("fg", "#D4D4D4")}; }}
            QTextEdit {{ background-color: {colors.get("bg", "#1E1E1E")}; color: {colors.get("fg", "#D4D4D4")}; border: none; }}
            QTabWidget::pane {{ border: 1px solid {colors.get("border", "#3C3C3C")}; background: {colors.get("bg", "#1E1E1E")}; }}
            QTabBar::tab {{ background: {colors.get("tab_inactive", "#2D2D2D")}; color: {colors.get("fg", "#D4D4D4")}; padding: 6px 12px; border: 1px solid {colors.get("border", "#3C3C3C")}; border-bottom: none; }}
            QTabBar::tab:selected {{ background: {colors.get("tab_active", "#1E1E1E")}; }}
            QTabBar::tab:hover:!selected {{ background: {colors.get("button_hover", "#3C3C3C")}; }}
            QTabBar::close-button:hover {{ background: #C42B1C; border-radius: 2px; }}
            QToolBar {{ background: {colors.get("toolbar", "#252526")}; border: none; spacing: 4px; padding: 4px; }}
            QPushButton {{ background: {colors.get("toolbar", "#3C3C3C")}; color: {colors.get("fg", "#D4D4D4")}; border: none; border-radius: 4px; padding: 6px 12px; font-size: 12px; }}
            QPushButton:hover {{ background: {colors.get("button_hover", "#505050")}; }}
            QStatusBar {{ background: {colors.get("statusbar", "#007ACC")}; color: #FFFFFF; }}
            QInputDialog {{ background: {colors.get("bg", "#1E1E1E")}; }}
        """

        window.setStyleSheet(styles)

        # Store colors for components that need direct access
        window._theme_colors = colors
        window._theme_name = self._current_theme

    def get_colors(self) -> dict:
        """Get current theme colors."""
        return self.get_theme().get("colors", {})
