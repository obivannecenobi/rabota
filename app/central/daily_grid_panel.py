from dataclasses import dataclass, asdict
from pathlib import Path
import calendar

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QComboBox,
)

from ..storage import Storage
from ..priority_service import PriorityFilter, filter_tasks, color_for


@dataclass
class Work:
    name: str
    plan: int = 0
    done: int = 0
    priority: int = 1
    is_adult: bool = False
    comment: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Work":
        return Work(
            name=data.get("name", ""),
            plan=int(data.get("plan", 0)),
            done=int(data.get("done", 0)),
            priority=int(data.get("priority", 1)),
            is_adult=bool(data.get("is_adult", False)),
            comment=data.get("comment", ""),
        )


class DayCell(QWidget):
    """Widget representing a single day's list of works."""

    changed = Signal()

    HEADERS = ["Работа", "План", "Готово", "Приоритет", "18+", "Комментарий"]

    def __init__(self, rows: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.rows_per_day = rows
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(rows, len(self.HEADERS), self)
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setEditTriggers(
            QTableWidget.DoubleClicked
            | QTableWidget.SelectedClicked
            | QTableWidget.EditKeyPressed
        )
        lay.addWidget(self.table)
        self._works: list[Work] = [Work("") for _ in range(rows)]
        self.table.itemChanged.connect(self._on_item_changed)

    # --------------------------------------------------------------
    def set_works(self, works: list[Work], priority_filter: PriorityFilter):
        filtered = list(filter_tasks(works, priority_filter))
        self._works = filtered + [Work("") for _ in range(self.rows_per_day - len(filtered))]
        self.table.blockSignals(True)
        for row, work in enumerate(self._works):
            self._set_row(row, work)
        self.table.blockSignals(False)

    def get_works(self) -> list[Work]:
        return [w for w in self._works if w.name]

    def _set_row(self, row: int, work: Work):
        def set_item(col: int, text: str, checkable: bool = False, checked: bool = False):
            item = QTableWidgetItem(text)
            if checkable:
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
                item.setText("")
            self.table.setItem(row, col, item)

        set_item(0, work.name)
        set_item(1, str(work.plan))
        set_item(2, str(work.done))
        pri_item = QTableWidgetItem(str(work.priority))
        pri_item.setForeground(QColor(color_for(work.priority)))
        self.table.setItem(row, 3, pri_item)
        set_item(4, "", checkable=True, checked=work.is_adult)
        set_item(5, work.comment)

    def _on_item_changed(self, item: QTableWidgetItem):
        row = item.row()
        col = item.column()
        if row >= len(self._works):
            return
        work = self._works[row]
        try:
            if col == 0:
                work.name = item.text()
            elif col == 1:
                work.plan = int(item.text() or 0)
            elif col == 2:
                work.done = int(item.text() or 0)
            elif col == 3:
                work.priority = int(item.text() or 1)
            elif col == 4:
                work.is_adult = item.checkState() == Qt.Checked
            elif col == 5:
                work.comment = item.text()
        except ValueError:
            pass
        self.changed.emit()

    # --------------------------------------------------------------
    def set_scale(self, percent: int):
        f = self.font()
        f.setPointSize(int(12 * percent / 100))
        self.table.setFont(f)
        for r in range(self.table.rowCount()):
            self.table.setRowHeight(r, int(24 * percent / 100))

    def set_edit_mode(self, enabled: bool):
        trigger = (
            QTableWidget.DoubleClicked
            | QTableWidget.SelectedClicked
            | QTableWidget.EditKeyPressed
            if enabled
            else QTableWidget.NoEditTriggers
        )
        self.table.setEditTriggers(trigger)


class DailyGridPanel(QWidget):
    """Panel showing month data in grid form: columns are days (1-31), rows are weeks."""

    def __init__(
        self,
        parent: QWidget | None = None,
        storage: Storage | None = None,
        rows_per_day: int = 6,
    ):
        super().__init__(parent)
        self.storage = storage or Storage(Path("data"))
        self.rows_per_day = rows_per_day
        self.month_data: dict[int, list[Work]] = {}
        self.priority_filter = PriorityFilter.OneToFour
        self.scale_percent = 100
        self.day_widgets: dict[int, DayCell] = {}

        lay = QVBoxLayout(self)
        ctrl = QHBoxLayout()
        self.year = QSpinBox(self)
        self.year.setRange(2000, 2100)
        self.month = QComboBox(self)
        self.month.addItems([
            "Янв","Фев","Мар","Апр","Май","Июн",
            "Июл","Авг","Сен","Окт","Ноя","Дек"
        ])
        ctrl.addWidget(QLabel("Год"))
        ctrl.addWidget(self.year)
        ctrl.addSpacing(12)
        ctrl.addWidget(QLabel("Месяц"))
        ctrl.addWidget(self.month)
        ctrl.addStretch(1)
        lay.addLayout(ctrl)

        self.grid = None
        self._build_grid()
        lay.addWidget(self.grid)

        self.year.valueChanged.connect(self.rebuild)
        self.month.currentIndexChanged.connect(self.rebuild)
        self.rebuild()

    # --------------------------------------------------------------
    def _build_grid(self):
        if self.grid is not None:
            self.grid.deleteLater()
            self.day_widgets.clear()
        self.grid = QTableWidget(6, 31, self)
        self.grid.setHorizontalHeaderLabels([str(i) for i in range(1, 32)])
        self.grid.setVerticalHeaderLabels([str(i) for i in range(1, 7)])
        for day in range(1, 32):
            row = (day - 1) // 7
            col = day - 1
            cell = DayCell(self.rows_per_day, self.grid)
            cell.changed.connect(self.save_month)
            self.grid.setCellWidget(row, col, cell)
            self.day_widgets[day] = cell

    # --------------------------------------------------------------
    def set_rows_per_day(self, rows: int):
        if rows == self.rows_per_day:
            return
        self.rows_per_day = rows
        self._build_grid()
        self.rebuild()

    def set_scale(self, percent: int):
        self.scale_percent = max(50, min(200, percent))
        f = self.font()
        f.setPointSize(int(12 * self.scale_percent / 100))
        self.setFont(f)
        for cell in self.day_widgets.values():
            cell.set_scale(self.scale_percent)
        for r in range(self.grid.rowCount()):
            self.grid.setRowHeight(r, int(self.rows_per_day * 24 * self.scale_percent / 100))

    def set_scale_edit_mode(self, enabled: bool):
        for cell in self.day_widgets.values():
            cell.set_edit_mode(enabled)

    def set_priority_filter(self, filt: PriorityFilter):
        self.priority_filter = filt
        self.rebuild()

    # --------------------------------------------------------------
    def rebuild(self):
        y = self.year.value()
        m = self.month.currentIndex() + 1
        self.load_month(y, m)
        days_in_month = calendar.monthrange(y, m)[1]
        for day in range(1, 32):
            w = self.day_widgets.get(day)
            if not w:
                continue
            self.grid.setColumnHidden(day - 1, day > days_in_month)
            works = self.month_data.get(day, []) if day <= days_in_month else []
            w.set_works(works, self.priority_filter)
        self.set_scale(self.scale_percent)

    # --------------------------------------------------------------
    def load_month(self, year: int, month: int):
        data = self.storage.load_json(f"{year}/{month:02d}.json", {}) or {}
        self.month_data = {
            int(d): [Work.from_dict(w) for w in wl]
            for d, wl in data.items()
        }

    def save_month(self):
        y = self.year.value()
        m = self.month.currentIndex() + 1
        data = {}
        for day, widget in self.day_widgets.items():
            works = widget.get_works()
            if works:
                data[str(day)] = [w.to_dict() for w in works]
        self.storage.save_json(f"{y}/{m:02d}.json", data)

