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
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
)

from .styles import base_stylesheet, light_stylesheet, apply_glass_effect
from .settings_dialog import SettingsDialog
from .version import get_version
from .central.daily_grid_panel import DailyGridPanel
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
            "rows_per_day": int(self.settings.value("rows_per_day", 6)),
        }

        # Storage
        save_dir = self.prefs.get("save_dir") or "data"
        self.storage = Storage(Path(save_dir))

        # Central panel
        self.central = DailyGridPanel(
            self,
            storage=self.storage,
            rows_per_day=self.prefs.get("rows_per_day", 6),
        )
        self.setCentralWidget(self.central)

        # Left dock (Top month)
        self.left_dock = QDockWidget("ТОП месяца", self)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
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
        self.bottom_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.stats_panel = StatsPanel(self.bottom_dock, storage=self.storage)
        self.bottom_dock.setWidget(self.stats_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
        self.bottom_dock.visibilityChanged.connect(
            lambda vis: self.settings.setValue("bottom_dock_visible", vis)
        )
        if not self.settings.value("bottom_dock_visible", True, type=bool):
            self.bottom_dock.hide()

        # Headers and placeholders for docks
        icon_path = Path(__file__).resolve().parent / "icons" / "menu_vertical.svg"
        icon = QIcon(str(icon_path))

        # Left dock header
        self.left_header = QFrame()
        lh_layout = QHBoxLayout(self.left_header)
        lh_layout.setContentsMargins(5, 0, 5, 0)
        lh_layout.addWidget(QLabel("ТОП месяца"))
        lh_layout.addStretch()
        lh_btn = QToolButton(self.left_header)
        lh_btn.setIcon(icon)
        lh_btn.setAutoRaise(True)
        lh_btn.setFixedSize(20, 20)
        lh_btn.setIconSize(QSize(20, 20))
        lh_btn.clicked.connect(self.toggle_left_dock)
        lh_layout.addWidget(lh_btn)
        self.left_dock.setTitleBarWidget(self.left_header)

        # Right dock header
        self.right_header = QFrame()
        rh_layout = QHBoxLayout(self.right_header)
        rh_layout.setContentsMargins(5, 0, 5, 0)
        rh_layout.addWidget(QLabel("Постинг отложки по дням"))
        rh_layout.addStretch()
        rh_btn = QToolButton(self.right_header)
        rh_btn.setIcon(icon)
        rh_btn.setAutoRaise(True)
        rh_btn.setFixedSize(20, 20)
        rh_btn.setIconSize(QSize(20, 20))
        rh_btn.clicked.connect(self.toggle_right_dock)
        rh_layout.addWidget(rh_btn)
        self.right_dock.setTitleBarWidget(self.right_header)

        # Bottom dock header
        self.bottom_header = QFrame()
        bh_layout = QHBoxLayout(self.bottom_header)
        bh_layout.setContentsMargins(5, 0, 5, 0)
        bh_layout.addWidget(QLabel("Результаты / Статистика"))
        bh_layout.addStretch()
        bh_btn = QToolButton(self.bottom_header)
        bh_btn.setIcon(icon)
        bh_btn.setAutoRaise(True)
        bh_btn.setFixedSize(20, 20)
        bh_btn.setIconSize(QSize(20, 20))
        bh_btn.clicked.connect(self.toggle_bottom_dock)
        bh_layout.addWidget(bh_btn)
        self.bottom_dock.setTitleBarWidget(self.bottom_header)

        # Placeholders shown when docks are hidden
        self.left_placeholder = QFrame(self)
        self.left_placeholder.setFrameShape(QFrame.StyledPanel)
        self.left_placeholder.setFixedWidth(20)
        lp_layout = QVBoxLayout(self.left_placeholder)
        lp_layout.setContentsMargins(0, 0, 0, 0)
        lp_layout.addStretch()
        lp_btn = QToolButton(self.left_placeholder)
        lp_btn.setIcon(icon)
        lp_btn.setAutoRaise(True)
        lp_btn.setFixedSize(20, 20)
        lp_btn.setIconSize(QSize(20, 20))
        lp_btn.clicked.connect(self.toggle_left_dock)
        lp_layout.addWidget(lp_btn)
        lp_layout.addStretch()
        self.left_placeholder.hide()
        self.left_placeholder.mousePressEvent = lambda e: self.toggle_left_dock()

        self.right_placeholder = QFrame(self)
        self.right_placeholder.setFrameShape(QFrame.StyledPanel)
        self.right_placeholder.setFixedWidth(20)
        rp_layout = QVBoxLayout(self.right_placeholder)
        rp_layout.setContentsMargins(0, 0, 0, 0)
        rp_layout.addStretch()
        rp_btn = QToolButton(self.right_placeholder)
        rp_btn.setIcon(icon)
        rp_btn.setAutoRaise(True)
        rp_btn.setFixedSize(20, 20)
        rp_btn.setIconSize(QSize(20, 20))
        rp_btn.clicked.connect(self.toggle_right_dock)
        rp_layout.addWidget(rp_btn)
        rp_layout.addStretch()
        self.right_placeholder.hide()
        self.right_placeholder.mousePressEvent = lambda e: self.toggle_right_dock()

        self.bottom_placeholder = QFrame(self)
        self.bottom_placeholder.setFrameShape(QFrame.StyledPanel)
        self.bottom_placeholder.setFixedHeight(20)
        bp_layout = QHBoxLayout(self.bottom_placeholder)
        bp_layout.setContentsMargins(0, 0, 0, 0)
        bp_layout.addStretch()
        bp_btn = QToolButton(self.bottom_placeholder)
        bp_btn.setIcon(icon)
        bp_btn.setAutoRaise(True)
        bp_btn.setFixedSize(20, 20)
        bp_btn.setIconSize(QSize(20, 20))
        bp_btn.clicked.connect(self.toggle_bottom_dock)
        bp_layout.addWidget(bp_btn)
        bp_layout.addStretch()
        self.bottom_placeholder.hide()
        self.bottom_placeholder.mousePressEvent = lambda e: self.toggle_bottom_dock()

        settings_icon_path = (
            Path(__file__).resolve().parent / "icons" / "settings.svg"
        )
        settings_icon = QIcon(str(settings_icon_path))
        self.settings_btn = QToolButton(self)
        self.settings_btn.setIcon(settings_icon)
        self.settings_btn.setAutoRaise(True)
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setIconSize(QSize(24, 24))
        self.settings_btn.setToolTip("Настройки")
        self.settings_btn.clicked.connect(self.open_settings)

        self.left_dock.visibilityChanged.connect(self._place_controls)
        self.right_dock.visibilityChanged.connect(self._place_controls)
        self.bottom_dock.visibilityChanged.connect(self._place_controls)

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

        self._place_controls()

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

    def _place_controls(self, *args):
        rect = self.rect()
        margin = 5
        self.settings_btn.move(
            rect.right() - self.settings_btn.width() - margin,
            rect.top() + margin,
        )

        if not self.left_dock.isVisible():
            self.left_placeholder.setGeometry(
                rect.left(), rect.top(), self.left_placeholder.width(), rect.height()
            )
            self.left_placeholder.show()
        else:
            self.left_placeholder.hide()

        if not self.right_dock.isVisible():
            self.right_placeholder.setGeometry(
                rect.right() - self.right_placeholder.width(),
                rect.top(),
                self.right_placeholder.width(),
                rect.height(),
            )
            self.right_placeholder.show()
        else:
            self.right_placeholder.hide()

        if not self.bottom_dock.isVisible():
            self.bottom_placeholder.setGeometry(
                rect.left(),
                rect.bottom() - self.bottom_placeholder.height(),
                rect.width(),
                self.bottom_placeholder.height(),
            )
            self.bottom_placeholder.show()
        else:
            self.bottom_placeholder.hide()

        for w in (
            self.left_placeholder,
            self.right_placeholder,
            self.bottom_placeholder,
            self.settings_btn,
        ):
            w.raise_()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._place_controls()

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
            sheet = base_stylesheet(
                accent=self.prefs["accent"],
                neon_size=self.prefs["neon_size"],
                neon_intensity=self.prefs["neon_intensity"],
            )
        else:
            sheet = light_stylesheet(
                accent=self.prefs["accent"],
                neon_size=self.prefs["neon_size"],
                neon_intensity=self.prefs["neon_intensity"],
            )
            self.setPalette(self.style().standardPalette())
        self.setStyleSheet(sheet)
        # Re-polish panels so dock contents pick up the accent focus/hover styles
        for w in (
            self.central,
            self.left_panel,
            self.right_panel,
            self.stats_panel,
            self.left_dock,
            self.right_dock,
            self.bottom_dock,
        ):
            w.setStyleSheet("")

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
        self.central.set_rows_per_day(self.prefs.get("rows_per_day", 6))
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
