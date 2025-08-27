from pathlib import Path
from typing import Dict, Optional, Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QPushButton,
)

from ..storage import Storage

if False:  # type checking only
    from ..central.main_panel import MainPanel

class TopMonthPanel(QWidget):
    """Panel showing monthly top works with editable statistics."""

    def __init__(self, parent=None, storage: Optional[Storage] = None):
        super().__init__(parent)
        self.edit_mode = False
        self.scale_percent = 100
        self.storage = storage or Storage(Path("data"))

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("ТОП месяца"))

        # ------------------------------------------------------------------
        # data entry form (meta information + default row values)
        form_widget = QWidget(self)
        form = QFormLayout(form_widget)
        self.year_edit = QSpinBox(form_widget)
        self.year_edit.setRange(2000, 2100)
        self.month_edit = QSpinBox(form_widget)
        self.month_edit.setRange(1, 12)
        self.work_edit = QLineEdit(form_widget)
        self.status_edit = QLineEdit(form_widget)
        self.adult_edit = QCheckBox(form_widget)
        self.total_chapters_edit = QSpinBox(form_widget)
        self.total_chapters_edit.setRange(0, 100000)
        self.symbols_edit = QLineEdit(form_widget)
        self.plan_edit = QSpinBox(form_widget)
        self.plan_edit.setRange(0, 100000)
        self.done_edit = QSpinBox(form_widget)
        self.done_edit.setRange(0, 100000)
        self.progress_edit = QSpinBox(form_widget)
        self.progress_edit.setRange(0, 100)
        self.release_edit = QLineEdit(form_widget)
        self.profit_edit = QLineEdit(form_widget)
        self.ads_edit = QLineEdit(form_widget)
        self.views_edit = QLineEdit(form_widget)
        self.likes_edit = QLineEdit(form_widget)
        self.thanks_edit = QLineEdit(form_widget)

        form.addRow("Год", self.year_edit)
        form.addRow("Месяц", self.month_edit)
        form.addRow("Работа", self.work_edit)
        form.addRow("Статус", self.status_edit)
        form.addRow("18+", self.adult_edit)
        form.addRow("Главы всего", self.total_chapters_edit)
        form.addRow("Знаки/главу", self.symbols_edit)
        form.addRow("Запланировано", self.plan_edit)
        form.addRow("Сделано", self.done_edit)
        form.addRow("Прогресс", self.progress_edit)
        form.addRow("Выпуск", self.release_edit)
        form.addRow("Профит", self.profit_edit)
        form.addRow("Реклама", self.ads_edit)
        form.addRow("Просмотры", self.views_edit)
        form.addRow("Лайки", self.likes_edit)
        form.addRow("Спасибо", self.thanks_edit)
        lay.addWidget(form_widget)
        self.add_btn = QPushButton("Добавить", self)
        lay.addWidget(self.add_btn)
        self.table = QTableWidget(0, 14, self)
        self.table.setHorizontalHeaderLabels([
            "Работа",
            "Статус",
            "18+",
            "Главы всего",
            "Знаки/главу",
            "Запланировано",
            "Сделано",
            "Прогресс",
            "Выпуск",
            "Профит",
            "Реклама",
            "Просмотры",
            "Лайки",
            "Спасибо",
        ])
        lay.addWidget(self.table)
        self.add_btn.clicked.connect(self._on_add_clicked)

    # ------------------------------------------------------------------
    # scaling / edit mode
    def set_scale(self, percent: int):
        self.scale_percent = max(50, min(200, percent))
        f = self.font()
        f.setPointSize(int(12 * self.scale_percent / 100))
        self.setFont(f)
        for r in range(self.table.rowCount()):
            self.table.setRowHeight(r, int(24 * self.scale_percent / 100))

    def set_edit_mode(self, enabled: bool):
        self.edit_mode = enabled
        trigger = QTableWidget.DoubleClicked if enabled else QTableWidget.NoEditTriggers
        self.table.setEditTriggers(trigger)
        # ensure scaling applied when toggling edit mode
        self.set_scale(self.scale_percent)

    # ------------------------------------------------------------------
    # form handling
    def _on_add_clicked(self):
        """Add a new row using form data and persist the month."""
        data = self.collect_form_data()
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._set_item(row, 0, data.get("work", ""), editable=False)
        self._set_item(row, 1, data.get("status", ""))
        adult_text = "18+" if data.get("is_adult") else "0+"
        self._set_item(row, 2, adult_text, editable=False)
        self._set_item(row, 3, str(data.get("total_chapters", "")))
        self._set_item(row, 4, str(data.get("symbols_per_chapter", "")))
        self._set_item(row, 5, str(data.get("plan", 0)), editable=False)
        self._set_item(row, 6, str(data.get("done", 0)), editable=False)
        self._set_item(row, 7, str(data.get("progress", "")))
        self._set_item(row, 8, str(data.get("release", "")))
        self._set_item(row, 9, str(data.get("profit", "")))
        self._set_item(row, 10, str(data.get("ads", "")))
        self._set_item(row, 11, str(data.get("views", "")))
        self._set_item(row, 12, str(data.get("likes", "")))
        self._set_item(row, 13, str(data.get("thanks", "")))
        self.set_scale(self.scale_percent)
        self.save_month(data.get("year", 0), data.get("month", 0))
        # clear form fields except year/month
        self.work_edit.clear()
        self.status_edit.clear()
        self.adult_edit.setChecked(False)
        self.total_chapters_edit.setValue(0)
        self.symbols_edit.clear()
        self.plan_edit.setValue(0)
        self.done_edit.setValue(0)
        self.progress_edit.setValue(0)
        self.release_edit.clear()
        self.profit_edit.clear()
        self.ads_edit.clear()
        self.views_edit.clear()
        self.likes_edit.clear()
        self.thanks_edit.clear()

    # ------------------------------------------------------------------
    # persistence helpers
    def _set_item(self, row: int, col: int, text: str, editable: bool = True):
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem()
            self.table.setItem(row, col, item)
        item.setText(text)
        flags = item.flags()
        if editable:
            item.setFlags(flags | Qt.ItemIsEditable)
        else:
            item.setFlags(flags & ~Qt.ItemIsEditable)

    def load_month(self, central: "MainPanel", year: int, month: int):
        """Load stats from MainPanel and stored data for given month."""
        # ensure central data for the month is loaded
        central.load_month(year, month)

        # aggregate works from central
        stats: Dict[str, Dict[str, Any]] = {}
        for works in central.month_data.values():
            for w in works:
                info = stats.setdefault(w.name, {"plan": 0, "done": 0, "adult": False})
                info["plan"] += w.plan
                info["done"] += w.done
                info["adult"] = info["adult"] or getattr(w, "is_adult", False)

        # load previously saved metrics
        saved = self.storage.load_json(f"{year}/top_month_{month:02d}.json", {}) or {}
        saved_form = saved.pop("__form__", {}) if isinstance(saved, dict) else {}

        # populate form from saved values or defaults
        if saved_form:
            self.year_edit.setValue(int(saved_form.get("year", year)))
            self.month_edit.setValue(int(saved_form.get("month", month)))
            self.work_edit.setText(str(saved_form.get("work", "")))
            self.status_edit.setText(str(saved_form.get("status", "")))
            self.adult_edit.setChecked(bool(saved_form.get("is_adult", False)))
            self.total_chapters_edit.setValue(int(saved_form.get("total_chapters", 0)))
            self.symbols_edit.setText(str(saved_form.get("symbols_per_chapter", "")))
            self.plan_edit.setValue(int(saved_form.get("plan", 0)))
            self.done_edit.setValue(int(saved_form.get("done", 0)))
            self.progress_edit.setValue(int(saved_form.get("progress", 0)))
            self.release_edit.setText(str(saved_form.get("release", "")))
            self.profit_edit.setText(str(saved_form.get("profit", "")))
            self.ads_edit.setText(str(saved_form.get("ads", "")))
            self.views_edit.setText(str(saved_form.get("views", "")))
            self.likes_edit.setText(str(saved_form.get("likes", "")))
            self.thanks_edit.setText(str(saved_form.get("thanks", "")))
        else:
            self.year_edit.setValue(year)
            self.month_edit.setValue(month)

        # build table
        self.table.setRowCount(len(stats))
        for row, (name, info) in enumerate(
            sorted(stats.items(), key=lambda x: x[1]["done"], reverse=True)
        ):
            self._set_item(row, 0, name, editable=False)
            saved_row = saved.get(name, {}) if isinstance(saved, dict) else {}
            self._set_item(row, 1, str(saved_row.get("status", "")))
            adult_text = "18+" if info.get("adult") else "0+"
            self._set_item(row, 2, adult_text, editable=False)
            self._set_item(row, 3, str(saved_row.get("total_chapters", "")))
            self._set_item(row, 4, str(saved_row.get("symbols_per_chapter", "")))
            self._set_item(row, 5, str(info.get("plan", 0)), editable=False)
            self._set_item(row, 6, str(info.get("done", 0)), editable=False)
            progress = saved_row.get("progress")
            if progress in (None, ""):
                plan = info.get("plan", 0)
                done = info.get("done", 0)
                progress = f"{int(done / plan * 100)}" if plan else ""
            self._set_item(row, 7, str(progress))
            self._set_item(row, 8, str(saved_row.get("release", "")))
            self._set_item(row, 9, str(saved_row.get("profit", "")))
            self._set_item(row, 10, str(saved_row.get("ads", "")))
            self._set_item(row, 11, str(saved_row.get("views", "")))
            self._set_item(row, 12, str(saved_row.get("likes", "")))
            self._set_item(row, 13, str(saved_row.get("thanks", "")))

        self.set_scale(self.scale_percent)

    def save_month(self, year: int, month: int):
        """Persist current table values for aggregation."""
        data = self.collect_month_data()
        payload = {"__form__": self.collect_form_data(), **data}
        self.storage.save_json(f"{year}/top_month_{month:02d}.json", payload)
        return payload

    def collect_form_data(self) -> Dict[str, Any]:
        """Gather current values from the input form."""
        return {
            "year": self.year_edit.value(),
            "month": self.month_edit.value(),
            "work": self.work_edit.text(),
            "status": self.status_edit.text(),
            "is_adult": self.adult_edit.isChecked(),
            "total_chapters": self.total_chapters_edit.value(),
            "symbols_per_chapter": self.symbols_edit.text(),
            "plan": self.plan_edit.value(),
            "done": self.done_edit.value(),
            "progress": self.progress_edit.value(),
            "release": self.release_edit.text(),
            "profit": self.profit_edit.text(),
            "ads": self.ads_edit.text(),
            "views": self.views_edit.text(),
            "likes": self.likes_edit.text(),
            "thanks": self.thanks_edit.text(),
        }

    def collect_month_data(self) -> Dict[str, Dict[str, str]]:
        """Return current table values as a dictionary.

        The structure mirrors what :meth:`save_month` stores and can be used
        by aggregation helpers to gather statistics without touching the
        filesystem.
        """
        data: Dict[str, Dict[str, str]] = {}
        for r in range(self.table.rowCount()):
            name_item = self.table.item(r, 0)
            if not name_item:
                continue
            name = name_item.text().strip()
            if not name:
                continue
            status = self.table.item(r, 1).text() if self.table.item(r, 1) else ""
            adult_text = self.table.item(r, 2).text() if self.table.item(r, 2) else "0+"
            is_adult = adult_text.strip().startswith("18")
            total_chapters = (
                int(self.table.item(r, 3).text() or 0) if self.table.item(r, 3) else 0
            )
            symbols_per_chapter = (
                self.table.item(r, 4).text() if self.table.item(r, 4) else ""
            )
            plan = int(self.table.item(r, 5).text() or 0) if self.table.item(r, 5) else 0
            done = int(self.table.item(r, 6).text() or 0) if self.table.item(r, 6) else 0
            progress = self.table.item(r, 7).text() if self.table.item(r, 7) else ""
            release = self.table.item(r, 8).text() if self.table.item(r, 8) else ""
            profit = self.table.item(r, 9).text() if self.table.item(r, 9) else ""
            ads = self.table.item(r, 10).text() if self.table.item(r, 10) else ""
            views = self.table.item(r, 11).text() if self.table.item(r, 11) else ""
            likes = self.table.item(r, 12).text() if self.table.item(r, 12) else ""
            thanks = self.table.item(r, 13).text() if self.table.item(r, 13) else ""
            data[name] = {
                "status": status,
                "is_adult": is_adult,
                "total_chapters": total_chapters,
                "symbols_per_chapter": symbols_per_chapter,
                "plan": plan,
                "done": done,
                "progress": progress,
                "release": release,
                "profit": profit,
                "ads": ads,
                "views": views,
                "likes": likes,
                "thanks": thanks,
            }
        return data
