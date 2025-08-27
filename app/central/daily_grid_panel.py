from dataclasses import dataclass, asdict
from pathlib import Path
import calendar

from PySide6.QtCore import Qt, Signal
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
from ..priority_service import PriorityFilter, filter_tasks


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

    HEADERS = ["Работа", "План", "Готово"]

    def __init__(self, rows: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.rows_per_day = rows
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self.caption = QLabel("", self)
        self.caption.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.caption)

        self.table = QTableWidget(rows, len(self.HEADERS), self)
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        # Center and bold headers
        for c in range(self.table.columnCount()):
            h = self.table.horizontalHeaderItem(c)
            h.setTextAlignment(Qt.AlignCenter)
            f = h.font()
            f.setBold(True)
            h.setFont(f)
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
        def set_item(col: int, text: str, align_left: bool = False):
            item = QTableWidgetItem(text)
            if align_left:
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            else:
                item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col, item)

        set_item(0, work.name, align_left=True)
        set_item(1, str(work.plan))
        set_item(2, str(work.done))

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
        except ValueError:
            pass
        self.changed.emit()

    # --------------------------------------------------------------
    def set_scale(self, percent: int):
        f = self.font()
        f.setPointSize(int(12 * percent / 100))
        self.caption.setFont(f)
        self.table.setFont(f)
        self.caption.setFixedHeight(int(24 * percent / 100))
        for r in range(self.table.rowCount()):
            self.table.setRowHeight(r, int(24 * percent / 100))

    def set_caption(self, text: str):
        self.caption.setText(text)

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
    """Panel showing month data in grid form with week numbers and day headers."""

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
        title = QLabel("План график")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

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
        # 7 rows (header + 6 weeks) x 8 columns (week + 7 days)
        self.grid = QTableWidget(7, 8, self)
        self.grid.verticalHeader().setVisible(False)
        self.grid.setEditTriggers(QTableWidget.NoEditTriggers)
        self.grid.setHorizontalHeaderLabels([
            "Неделя", "ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"
        ])
        self.grid.setRowHidden(0, True)

        for week in range(1, 7):
            item = QTableWidgetItem(str(week))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsEnabled)
            self.grid.setItem(week, 0, item)

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
            base = 0 if r == 0 else self.rows_per_day * 24
            self.grid.setRowHeight(r, int(base * self.scale_percent / 100))

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

        weeks = calendar.monthcalendar(y, m)
        day_names = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]

        # Clear previous day widgets
        for r in range(1, 7):
            for c in range(1, 8):
                w = self.grid.cellWidget(r, c)
                if w:
                    w.deleteLater()
                self.grid.setCellWidget(r, c, None)
        self.day_widgets.clear()

        # Hide unused week rows
        for r in range(1, 7):
            self.grid.setRowHidden(r, r > len(weeks))

        for w_index, week in enumerate(weeks):
            for d_index, day in enumerate(week):
                if day == 0:
                    continue
                cell = DayCell(self.rows_per_day, self.grid)
                cell.changed.connect(self.save_month)
                cell.set_caption(f"{day_names[d_index]} {day}")
                works = self.month_data.get(day, [])
                cell.set_works(works, self.priority_filter)
                self.grid.setCellWidget(w_index + 1, d_index + 1, cell)
                self.day_widgets[day] = cell

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

