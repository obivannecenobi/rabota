from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSettings, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QLabel,
    QStatusBar,
    QWidget,
    QToolButton,
    QStyle,
)

from .styles import base_stylesheet, light_stylesheet, apply_glass_effect
from .settings_dialog import SettingsDialog
from .version import get_version
from .central.main_panel import MainPanel
from .panels.top_month_panel import TopMonthPanel
from .panels.postings_panel import PostingsPanel
from .panels.stats_panel import StatsPanel
from .storage import Storage
from .priority_service import PriorityFilter



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Веб‑новеллы — рабочее приложение")
        self.resize(1200, 800)

        self.settings = QSettings("WebNovelApp", "Main")
        self.prefs = {
            "theme": self.settings.value("theme", "dark"),
            "accent": self.settings.value("accent", "#00E5FF"),
            "palette": self.settings.value("palette", "cyan"),
            "glass_enabled": self.settings.value("glass_enabled", False, type=bool),
            "glass_opacity": float(self.settings.value("glass_opacity", 0.9)),
            "glass_blur": int(self.settings.value("glass_blur", 6)),
            "glass_texture": int(self.settings.value("glass_texture", 2)),
            "glass_sharpness": int(self.settings.value("glass_sharpness", 5)),
            "neon_size": int(self.settings.value("neon_size", 8)),
            "neon_intensity": int(self.settings.value("neon_intensity", 60)),
            "save_dir": self.settings.value("save_dir", ""),
            "title_font": self.settings.value("title_font", ""),
            "text_font": self.settings.value("text_font", ""),
            "scale_edit_mode": self.settings.value("scale_edit_mode", False, type=bool),
            "central_scale": int(self.settings.value("central_scale", 100)),
            "left_edit_mode": self.settings.value("left_edit_mode", False, type=bool),
            "right_edit_mode": self.settings.value("right_edit_mode", False, type=bool),
            "priority_filter": int(self.settings.value("priority_filter", PriorityFilter.OneToFour)),
        }

        # Storage
        save_dir = self.prefs.get("save_dir") or "data"
        self.storage = Storage(Path(save_dir))

        # Central panel
        self.central = MainPanel(self, storage=self.storage)
        self.setCentralWidget(self.central)

        # Left dock (Top month)
        self.left_dock = QDockWidget("ТОП месяца", self)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.left_dock.setTitleBarWidget(QWidget())
        self.left_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.left_panel = TopMonthPanel(self.left_dock)
        self.left_panel.storage = self.storage
        self.left_dock.setWidget(self.left_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
        self.left_dock.visibilityChanged.connect(
            lambda vis: self.settings.setValue("left_dock_visible", vis)
        )
        if not self.settings.value("left_dock_visible", True, type=bool):
            self.left_dock.hide()

        # Right dock (Postings)
        self.right_dock = QDockWidget("Постинг отложки по дням", self)
        self.right_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.right_dock.setTitleBarWidget(QWidget())
        self.right_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.right_panel = PostingsPanel(self.right_dock, storage=self.storage)
        self.right_dock.setWidget(self.right_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)
        self.right_dock.visibilityChanged.connect(
            lambda vis: self.settings.setValue("right_dock_visible", vis)
        )
        if not self.settings.value("right_dock_visible", True, type=bool):
            self.right_dock.hide()

        # Bottom dock (Stats)
        self.bottom_dock = QDockWidget("Результаты / Статистика", self)
        self.bottom_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.bottom_dock.setTitleBarWidget(QWidget())
        self.bottom_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.stats_panel = StatsPanel(self.bottom_dock, storage=self.storage)
        self.bottom_dock.setWidget(self.stats_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
        self.bottom_dock.visibilityChanged.connect(
            lambda vis: self.settings.setValue("bottom_dock_visible", vis)
        )
        if not self.settings.value("bottom_dock_visible", True, type=bool):
            self.bottom_dock.hide()

        # Toggle buttons for docks
        icon_path = Path(__file__).resolve().parent / "icons" / "menu_vertical.svg"
        icon = QIcon(str(icon_path))

        self.left_btn = QToolButton(self)
        self.left_btn.setIcon(icon)
        self.left_btn.setAutoRaise(True)
        self.left_btn.setFixedSize(24, 24)
        self.left_btn.setIconSize(QSize(24, 24))
        self.left_btn.clicked.connect(self.toggle_left_dock)

        self.right_btn = QToolButton(self)
        self.right_btn.setIcon(icon)
        self.right_btn.setAutoRaise(True)
        self.right_btn.setFixedSize(24, 24)
        self.right_btn.setIconSize(QSize(24, 24))
        self.right_btn.clicked.connect(self.toggle_right_dock)

        self.bottom_btn = QToolButton(self)
        self.bottom_btn.setIcon(icon)
        self.bottom_btn.setAutoRaise(True)
        self.bottom_btn.setFixedSize(24, 24)
        self.bottom_btn.setIconSize(QSize(24, 24))
        self.bottom_btn.clicked.connect(self.toggle_bottom_dock)

        settings_icon = QIcon.fromTheme(
            "settings", self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        )
        self.settings_btn = QToolButton(self)
        self.settings_btn.setIcon(settings_icon)
        self.settings_btn.setAutoRaise(True)
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setIconSize(QSize(24, 24))
        self.settings_btn.clicked.connect(self.open_settings)

        self.left_dock.visibilityChanged.connect(self._place_toggle_buttons)
        self.right_dock.visibilityChanged.connect(self._place_toggle_buttons)
        self.bottom_dock.visibilityChanged.connect(self._place_toggle_buttons)

        # Load saved data for current month/year
        self.central.year.valueChanged.connect(self._load_panels)
        self.central.month.currentIndexChanged.connect(self._load_panels)
        self._load_panels()

        # Status bar: stopwatch (left) and version (right)
        sb = QStatusBar(self)
        self.setStatusBar(sb)
        self.timer_label = QLabel("00:00:00:00")
        self.version_label = QLabel(f"v{get_version()}")
        sb.addWidget(self.timer_label)
        sb.addPermanentWidget(self.version_label)

        self._secs = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

        # Menu
        self.menuBar().hide()

        # Apply initial prefs
        self.apply_prefs()

        # Restore geometry
        geo = self.settings.value("geometry")
        state = self.settings.value("windowState")
        if geo:
            self.restoreGeometry(geo)
        if state:
            self.restoreState(state)

        self._place_toggle_buttons()

    def _tick(self):
        self._secs += 1
        d = self._secs // 86400
        h = (self._secs % 86400) // 3600
        m = (self._secs % 3600) // 60
        s = self._secs % 60
        self.timer_label.setText(f"{d:02d}:{h:02d}:{m:02d}:{s:02d}")

    def toggle_left_dock(self):
        if self.left_dock.isVisible():
            self.left_dock.hide()
        else:
            self.left_dock.show()

    def toggle_right_dock(self):
        if self.right_dock.isVisible():
            self.right_dock.hide()
        else:
            self.right_dock.show()

    def toggle_bottom_dock(self):
        if self.bottom_dock.isVisible():
            self.bottom_dock.hide()
        else:
            self.bottom_dock.show()

    def _place_toggle_buttons(self, *args):
        rect = self.rect()
        margin = 5
        self.left_btn.move(rect.left() + margin, rect.top() + margin)
        self.right_btn.move(
            rect.right() - self.right_btn.width() - margin, rect.top() + margin
        )
        self.bottom_btn.move(
            rect.left() + margin,
            rect.bottom() - self.bottom_btn.height() - margin,
        )
        self.settings_btn.move(
            rect.right() - self.settings_btn.width() - margin,
            rect.top() + margin,
        )
        for btn in (self.left_btn, self.right_btn, self.bottom_btn, self.settings_btn):
            btn.raise_()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._place_toggle_buttons()

    def set_priority_filter(self, filt: PriorityFilter):
        self.prefs["priority_filter"] = int(filt)
        self.settings.setValue("priority_filter", int(filt))
        self.central.set_priority_filter(filt)

    def set_theme(self, theme: str):
        self.prefs["theme"] = theme
        self.settings.setValue("theme", theme)
        self.apply_prefs()

    def set_palette(self, palette: str):
        self.prefs["palette"] = palette
        self.settings.setValue("palette", palette)
        palette_map = {
            "cyan": "#00E5FF",
            "orange": "#FFA500",
            "purple": "#9C27B0",
        }
        if palette != "custom":
            accent = palette_map.get(palette, self.prefs.get("accent", "#00E5FF"))
            self.prefs["accent"] = accent
            self.settings.setValue("accent", accent)
        self.apply_prefs()

    def open_settings(self):
        dlg = SettingsDialog(self, self.prefs)
        def on_apply(res):
            self.prefs.update(res.__dict__)
            # Persist
            for k, v in res.__dict__.items():
                self.settings.setValue(k, int(v) if k == "priority_filter" else v)
            self.set_priority_filter(res.priority_filter)
            self.apply_prefs()
        dlg.settings_applied.connect(on_apply)
        dlg.exec()

    def apply_prefs(self):
        # Stylesheet / Theme
        if self.prefs.get("theme", "dark") == "dark":
            self.setStyleSheet(base_stylesheet(
                accent=self.prefs["accent"],
                neon_size=self.prefs["neon_size"],
                neon_intensity=self.prefs["neon_intensity"]
            ))
        else:
            self.setStyleSheet(light_stylesheet(
                accent=self.prefs["accent"],
                neon_size=self.prefs["neon_size"],
                neon_intensity=self.prefs["neon_intensity"]
            ))
            self.setPalette(self.style().standardPalette())

        # Glass
        apply_glass_effect(
            self,
            self.prefs.get("glass_enabled", False),
            self.prefs.get("glass_opacity", 0.9),
            self.prefs.get("glass_blur", 6),
            self.prefs.get("glass_texture", 2),
            self.prefs.get("glass_sharpness", 5),
        )
        # Fonts
        if self.prefs.get("title_font") or self.prefs.get("text_font"):
            f = self.font()
            if self.prefs.get("text_font"): f.setFamily(self.prefs.get("text_font"))
            self.setFont(f)
        # Central scaling
        scale = self.prefs.get("central_scale", 100)
        self.central.set_scale(scale)
        self.left_panel.set_scale(scale)
        self.right_panel.set_scale(scale)
        self.stats_panel.set_scale(scale)
        self.central.set_scale_edit_mode(self.prefs.get("scale_edit_mode", False))
        # Panel edit modes
        self.left_panel.set_edit_mode(self.prefs.get("left_edit_mode", False))
        self.right_panel.set_edit_mode(self.prefs.get("right_edit_mode", False))
        # Priority filter
        filt = PriorityFilter(self.prefs.get("priority_filter", PriorityFilter.OneToFour))
        self.central.set_priority_filter(filt)
        # Palette combo state
        if hasattr(self, "palette_combo"):
            idx = self.palette_combo.findData(self.prefs.get("palette", "cyan"))
            if idx >= 0 and self.palette_combo.currentIndex() != idx:
                self.palette_combo.blockSignals(True)
                self.palette_combo.setCurrentIndex(idx)
                self.palette_combo.blockSignals(False)

    def closeEvent(self, e):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("left_dock_visible", self.left_dock.isVisible())
        self.settings.setValue("right_dock_visible", self.right_dock.isVisible())
        self.settings.setValue("bottom_dock_visible", self.bottom_dock.isVisible())

        # Persist panel data
        y = self.central.year.value()
        m = self.central.month.currentIndex() + 1
        self.central.save_month()
        self.left_panel.save_month(y, m)
        self.right_panel.save_month(y, m)
        self.storage.save_json(
            f"{y}/stats_{m:02d}.json",
            {"charts_visible": self.stats_panel.charts_frame.isVisible()},
        )

        super().closeEvent(e)

    # ------------------------------------------------------------------
    def _load_panels(self):
        y = self.central.year.value()
        m = self.central.month.currentIndex() + 1
        self.left_panel.load_month(self.central, y, m)
        self.right_panel.load_month(y, m)
        self.stats_panel.set_month(y, m)
        self.stats_panel.load_year(y)
        stats = self.storage.load_json(f"{y}/stats_{m:02d}.json", {})
        vis = bool(stats.get("charts_visible"))
        self.stats_panel.charts_frame.setVisible(vis)
        self.stats_panel.toggle_btn.setText("Скрыть графики" if vis else "Показать графики")
