from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QLabel,
    QStatusBar,
    QFileDialog,
    QWidget,
    QHBoxLayout,
)

from .styles import base_stylesheet, apply_glass_effect
from .settings_dialog import SettingsDialog
from .version import get_version
from .central.calendar_panel import CalendarPanel
from .panels.top_month_panel import TopMonthPanel
from .panels.postings_panel import PostingsPanel
from .panels.stats_panel import StatsPanel
from .storage import Storage
from .priority_service import PriorityFilter, PRIORITY_COLORS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Веб‑новеллы — рабочее приложение")
        self.resize(1200, 800)

        self.settings = QSettings("WebNovelApp", "Main")
        self.prefs = {
            "theme": self.settings.value("theme", "dark"),
            "accent": self.settings.value("accent", "#00E5FF"),
            "glass_enabled": self.settings.value("glass_enabled", False, type=bool),
            "glass_opacity": float(self.settings.value("glass_opacity", 0.9)),
            "neon_size": int(self.settings.value("neon_size", 8)),
            "neon_intensity": int(self.settings.value("neon_intensity", 60)),
            "save_dir": self.settings.value("save_dir", ""),
            "title_font": self.settings.value("title_font", ""),
            "text_font": self.settings.value("text_font", ""),
            "scale_edit_mode": self.settings.value("scale_edit_mode", False, type=bool),
            "central_scale": int(self.settings.value("central_scale", 100)),
            "left_edit_mode": self.settings.value("left_edit_mode", False, type=bool),
            "right_edit_mode": self.settings.value("right_edit_mode", False, type=bool),
        }

        # Storage
        save_dir = self.prefs.get("save_dir") or "data"
        self.storage = Storage(Path(save_dir))

        # Central panel
        self.central = CalendarPanel(self)
        self.central.storage = self.storage
        self.central.rebuild()
        self.setCentralWidget(self.central)

        # Left dock (Top month)
        self.left_dock = QDockWidget("ТОП месяца", self)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.left_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.left_panel = TopMonthPanel(self.left_dock)
        self.left_panel.storage = self.storage
        self.left_dock.setWidget(self.left_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)

        # Right dock (Postings)
        self.right_dock = QDockWidget("Постинг отложки по дням", self)
        self.right_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.right_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.right_panel = PostingsPanel(self.right_dock, storage=self.storage)
        self.right_dock.setWidget(self.right_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)

        # Bottom dock (Stats)
        self.bottom_dock = QDockWidget("Результаты / Статистика", self)
        self.bottom_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.bottom_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.stats_panel = StatsPanel(self.bottom_dock, storage=self.storage)
        self.bottom_dock.setWidget(self.stats_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)

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

        # Toolbar/Actions
        self._build_toolbar()

        # Apply initial prefs
        self.apply_prefs()

        # Restore geometry
        geo = self.settings.value("geometry")
        state = self.settings.value("windowState")
        if geo:
            self.restoreGeometry(geo)
        if state:
            self.restoreState(state)

    def _tick(self):
        self._secs += 1
        d = self._secs // 86400
        h = (self._secs % 86400) // 3600
        m = (self._secs % 3600) // 60
        s = self._secs % 60
        self.timer_label.setText(f"{d:02d}:{h:02d}:{m:02d}:{s:02d}")

    def _build_toolbar(self):
        tb = self.addToolBar("Главное")
        tb.setMovable(False)

        act_settings = QAction("Настройки", self)
        act_settings.triggered.connect(self.open_settings)
        tb.addAction(act_settings)

        act_save_dir = QAction("Папка сохранения", self)
        act_save_dir.triggered.connect(self.pick_save_dir)
        tb.addAction(act_save_dir)

        tb.addSeparator()

        group = QActionGroup(self)
        act_all = QAction("1-4", self, checkable=True)
        act_all.setChecked(True)
        act_all.triggered.connect(lambda: self.set_priority_filter(PriorityFilter.OneToFour))
        group.addAction(act_all)
        tb.addAction(act_all)

        act_low = QAction("1-2", self, checkable=True)
        act_low.triggered.connect(lambda: self.set_priority_filter(PriorityFilter.OneToTwo))
        group.addAction(act_low)
        tb.addAction(act_low)

        legend = QWidget()
        lay = QHBoxLayout(legend)
        lay.setContentsMargins(4, 0, 4, 0)
        for p, color in PRIORITY_COLORS.items():
            lbl = QLabel(str(int(p)))
            lbl.setStyleSheet(f"background:{color}; padding:2px; border-radius:3px; color:#000;")
            lay.addWidget(lbl)
        tb.addWidget(legend)

    def pick_save_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Выбрать папку сохранения")
        if d:
            self.prefs["save_dir"] = d
            self.settings.setValue("save_dir", d)

    def set_priority_filter(self, filt: PriorityFilter):
        self.central.set_priority_filter(filt)

    def open_settings(self):
        dlg = SettingsDialog(self, self.prefs)
        def on_apply(res):
            self.prefs.update(res.__dict__)
            # Persist
            for k, v in res.__dict__.items():
                self.settings.setValue(k, v)
            self.apply_prefs()
        dlg.settings_applied.connect(on_apply)
        dlg.exec()

    def apply_prefs(self):
        # Stylesheet
        self.setStyleSheet(base_stylesheet(
            accent=self.prefs["accent"],
            neon_size=self.prefs["neon_size"],
            neon_intensity=self.prefs["neon_intensity"]
        ))
        # Glass
        apply_glass_effect(self, self.prefs.get("glass_enabled", False), self.prefs.get("glass_opacity", 0.9))
        # Fonts
        if self.prefs.get("title_font") or self.prefs.get("text_font"):
            f = self.font()
            if self.prefs.get("text_font"): f.setFamily(self.prefs.get("text_font"))
            self.setFont(f)
        # Central scaling
        scale = self.prefs.get("central_scale", 100)
        self.central.set_scale(scale)
        self.left_panel.set_scale(scale)
        self.central.set_scale_edit_mode(self.prefs.get("scale_edit_mode", False))
        # Panel edit modes
        self.left_panel.set_edit_mode(self.prefs.get("left_edit_mode", False))
        self.right_panel.set_edit_mode(self.prefs.get("right_edit_mode", False))

    def closeEvent(self, e):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

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
