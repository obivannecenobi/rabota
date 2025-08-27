from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QColorDialog, QSlider, QFileDialog, QCheckBox, QSpinBox, QTabWidget, QWidget, QFormLayout, QLineEdit, QRadioButton
)

from .priority_service import PriorityFilter

class SettingsResult:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class SettingsDialog(QDialog):
    settings_applied = Signal(object)

    def __init__(self, parent, current):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.resize(680, 520)

        tabs = QTabWidget(self)

        # Theme tab
        theme_tab = QWidget()
        fl = QFormLayout(theme_tab)
        theme_box = QWidget()
        thl = QHBoxLayout(theme_box)
        thl.setContentsMargins(0, 0, 0, 0)
        self.dark_radio = QRadioButton("Тёмная")
        self.light_radio = QRadioButton("Светлая")
        if current.get("theme", "dark") == "dark":
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)
        thl.addWidget(self.dark_radio)
        thl.addWidget(self.light_radio)
        fl.addRow("Тема", theme_box)

        # Palette / accent
        self.palette_combo = QComboBox()
        self.palette_combo.addItem("Циан", "cyan")
        self.palette_combo.addItem("Оранж", "orange")
        self.palette_combo.addItem("Фиолет", "purple")
        self.palette_combo.addItem("Свой цвет", "custom")
        self.palette_combo.currentIndexChanged.connect(self._palette_changed)

        self.accent_btn = QPushButton("Выбрать цвет акцента")
        self.accent_btn.clicked.connect(self.pick_accent)

        self.glass_chk = QCheckBox("Прозрачное \"стекло\"")
        self.glass_chk.setChecked(current.get("glass_enabled", False))
        self.opacity_slider = QSlider(Qt.Horizontal); self.opacity_slider.setRange(50, 100); self.opacity_slider.setValue(int(current.get("glass_opacity", 0.9)*100))
        self.blur_slider = QSlider(Qt.Horizontal); self.blur_slider.setRange(0, 20); self.blur_slider.setValue(current.get("glass_blur", 6))
        self.texture_slider = QSlider(Qt.Horizontal); self.texture_slider.setRange(0, 10); self.texture_slider.setValue(current.get("glass_texture", 2))
        self.sharp_slider = QSlider(Qt.Horizontal); self.sharp_slider.setRange(0, 10); self.sharp_slider.setValue(current.get("glass_sharpness", 5))

        self.glass_chk.toggled.connect(self._glass_toggled)
        self._glass_toggled(self.glass_chk.isChecked())

        fl.addRow("Палитра", self.palette_combo)
        fl.addRow("Акцент", self.accent_btn)
        fl.addRow(self.glass_chk)
        fl.addRow("Прозрачность", self.opacity_slider)
        fl.addRow("Размытость", self.blur_slider)
        fl.addRow("Текстура", self.texture_slider)
        fl.addRow("Чёткость", self.sharp_slider)

        # Priority filter preset
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("1-4", PriorityFilter.OneToFour)
        self.priority_combo.addItem("1-2", PriorityFilter.OneToTwo)
        fl.addRow("Фильтр приоритетов", self.priority_combo)

        self.log_btn = QPushButton("Открыть журнал приоритетов")
        self.log_btn.clicked.connect(parent.open_priority_log)
        fl.addRow(self.log_btn)

        # Fonts tab
        fonts_tab = QWidget()
        ffl = QFormLayout(fonts_tab)
        self.title_font = QLineEdit(current.get("title_font",""))
        self.text_font = QLineEdit(current.get("text_font",""))
        ffl.addRow("Шрифт заголовков (системное имя)", self.title_font)
        ffl.addRow("Шрифт текста (системное имя)", self.text_font)

        # Storage tab
        storage_tab = QWidget()
        sfl = QFormLayout(storage_tab)
        self.save_dir_edit = QLineEdit(current.get("save_dir",""))
        pick = QPushButton("Выбрать папку...")
        def pick_dir():
            d = QFileDialog.getExistingDirectory(self, "Папка сохранения")
            if d:
                self.save_dir_edit.setText(d)
        pick.clicked.connect(pick_dir)
        sfl.addRow("Папка сохранения", self.save_dir_edit)
        sfl.addRow(pick)

        # Neon tab
        neon_tab = QWidget()
        nfl = QFormLayout(neon_tab)
        self.neon_size = QSpinBox(); self.neon_size.setRange(0, 32); self.neon_size.setValue(current.get("neon_size", 8))
        self.neon_intensity = QSpinBox(); self.neon_intensity.setRange(0, 100); self.neon_intensity.setValue(current.get("neon_intensity", 60))
        nfl.addRow("Размер неона", self.neon_size)
        nfl.addRow("Интенсивность неона (%)", self.neon_intensity)

        # Scaling tab (central + panels)
        scale_tab = QWidget()
        scl = QFormLayout(scale_tab)
        self.scale_edit_mode = QCheckBox("Редактирование масштаба центральной области")
        self.scale_edit_mode.setChecked(current.get("scale_edit_mode", False))
        self.central_scale = QSpinBox(); self.central_scale.setRange(50, 200); self.central_scale.setValue(current.get("central_scale", 100))
        self.left_panel_edit = QCheckBox("Редактирование левой панели (ТОП месяца)")
        self.left_panel_edit.setChecked(current.get("left_edit_mode", False))
        self.right_panel_edit = QCheckBox("Редактирование правой панели (постинг)")
        self.right_panel_edit.setChecked(current.get("right_edit_mode", False))
        scl.addRow(self.scale_edit_mode)
        scl.addRow("Масштаб центральной области (%)", self.central_scale)
        scl.addRow(self.left_panel_edit)
        scl.addRow(self.right_panel_edit)

        tabs.addTab(theme_tab, "Тема/Палитра")
        tabs.addTab(fonts_tab, "Шрифты")
        tabs.addTab(storage_tab, "Сохранение")
        tabs.addTab(neon_tab, "Неон")
        tabs.addTab(scale_tab, "Масштаб")

        btns = QHBoxLayout()
        ok = QPushButton("Применить")
        cancel = QPushButton("Отмена")
        ok.clicked.connect(self.apply)
        cancel.clicked.connect(self.reject)
        btns.addStretch(1); btns.addWidget(ok); btns.addWidget(cancel)

        lay = QVBoxLayout(self)
        lay.addWidget(tabs)
        lay.addLayout(btns)

        self._accent = current.get("accent", "#00E5FF")
        self._palette_map = {
            "cyan": "#00E5FF",
            "orange": "#FFA500",
            "purple": "#9C27B0",
        }
        palette_name = current.get("palette", "cyan")
        idx = self.palette_combo.findData(palette_name)
        if idx >= 0:
            self.palette_combo.setCurrentIndex(idx)
        # Disable accent button for predefined palettes
        if palette_name != "custom":
            self._accent = self._palette_map.get(palette_name, self._accent)
            self.accent_btn.setEnabled(False)
        # Priority filter
        pf_idx = self.priority_combo.findData(PriorityFilter(current.get("priority_filter", PriorityFilter.OneToFour)))
        if pf_idx >= 0:
            self.priority_combo.setCurrentIndex(pf_idx)

    def pick_accent(self):
        from PySide6.QtGui import QColor
        col = QColorDialog.getColor()
        if col.isValid():
            self._accent = col.name()
            idx = self.palette_combo.findData("custom")
            if idx >= 0:
                self.palette_combo.setCurrentIndex(idx)
            self.accent_btn.setEnabled(True)

    def _palette_changed(self, index):
        key = self.palette_combo.itemData(index)
        if key == "custom":
            self.accent_btn.setEnabled(True)
        else:
            self.accent_btn.setEnabled(False)
            self._accent = self._palette_map.get(key, self._accent)

    def _glass_toggled(self, checked: bool):
        for w in (self.opacity_slider, self.blur_slider, self.texture_slider, self.sharp_slider):
            w.setEnabled(checked)

    def apply(self):
        res = SettingsResult(
            theme = "dark" if self.dark_radio.isChecked() else "light",
            accent = self._accent,
            palette = self.palette_combo.currentData(),
            glass_enabled = self.glass_chk.isChecked(),
            glass_opacity = self.opacity_slider.value()/100.0,
            glass_blur = self.blur_slider.value(),
            glass_texture = self.texture_slider.value(),
            glass_sharpness = self.sharp_slider.value(),
            title_font = self.title_font.text().strip(),
            text_font = self.text_font.text().strip(),
            save_dir = self.save_dir_edit.text().strip(),
            neon_size = self.neon_size.value(),
            neon_intensity = self.neon_intensity.value(),
            scale_edit_mode = self.scale_edit_mode.isChecked(),
            central_scale = self.central_scale.value(),
            left_edit_mode = self.left_panel_edit.isChecked(),
            right_edit_mode = self.right_panel_edit.isChecked(),
            priority_filter = self.priority_combo.currentData(),
        )
        self.settings_applied.emit(res)
        self.accept()
