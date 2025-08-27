from dataclasses import dataclass, asdict
from pathlib import Path

from PySide6.QtCore import Qt
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
    QPushButton,
    QInputDialog,
    QMenu,
)

from ..storage import Storage
from ..priority_service import PriorityFilter, sort_tasks, filter_tasks, color_for


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


class MainPanel(QWidget):
    """Simplified central panel showing a list of works per day."""

    HEADERS = ["День", "Работа", "План", "Готово", "Приоритет", "18+", "Комментарий"]

    def __init__(self, parent=None, storage: Storage | None = None):
        super().__init__(parent)
        self.storage = storage or Storage(Path("data"))
        self.month_data: dict[int, list[Work]] = {}
        self._row_map: dict[int, tuple[int, Work]] = {}
        self.priority_filter = PriorityFilter.OneToFour
        self.scale_percent = 100

        lay = QVBoxLayout(self)
        ctrl = QHBoxLayout()
        self.year = QSpinBox(self)
        self.year.setRange(2000, 2100)
        self.month = QComboBox(self)
        self.month.addItems(["Янв","Фев","Мар","Апр","Май","Июн","Июл","Авг","Сен","Окт","Ноя","Дек"])
        ctrl.addWidget(QLabel("Год"))
        ctrl.addWidget(self.year)
        ctrl.addSpacing(12)
        ctrl.addWidget(QLabel("Месяц"))
        ctrl.addWidget(self.month)
        ctrl.addStretch(1)
        self.add_btn = QPushButton("Добавить работу", self)
        ctrl.addWidget(self.add_btn)
        lay.addLayout(ctrl)

        self.table = QTableWidget(0, len(self.HEADERS), self)
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked | QTableWidget.EditKeyPressed)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_menu)
        lay.addWidget(self.table)

        self.add_btn.clicked.connect(self.add_work)
        self.year.valueChanged.connect(self.rebuild)
        self.month.currentIndexChanged.connect(self.rebuild)

        self.year.setValue(self.year.value())  # trigger default
        self.rebuild()

    # ------------------------------------------------------------------
    def set_scale(self, percent: int):
        self.scale_percent = max(50, min(200, percent))
        f = self.font()
        f.setPointSize(int(12 * self.scale_percent / 100))
        self.setFont(f)
        for r in range(self.table.rowCount()):
            self.table.setRowHeight(r, int(24 * self.scale_percent / 100))

    def set_scale_edit_mode(self, enabled: bool):
        trigger = (QTableWidget.DoubleClicked | QTableWidget.SelectedClicked | QTableWidget.EditKeyPressed) if enabled else QTableWidget.NoEditTriggers
        self.table.setEditTriggers(trigger)

    def set_priority_filter(self, filt: PriorityFilter):
        self.priority_filter = filt
        self._refresh_table()

    # ------------------------------------------------------------------
    def rebuild(self):
        y = self.year.value()
        m = self.month.currentIndex() + 1
        self.load_month(y, m)
        self._refresh_table()

    def _refresh_table(self):
        self.table.blockSignals(True)
        rows = sum(
            len(list(filter_tasks(v, self.priority_filter)))
            for v in self.month_data.values()
        )
        self.table.setRowCount(rows)
        self._row_map.clear()
        row = 0
        for day in sorted(self.month_data.keys()):
            works = list(filter_tasks(self.month_data[day], self.priority_filter))
            for work in sort_tasks(works):
                self._row_map[row] = (day, work)
                self._set_row(row, day, work)
                row += 1
        self.table.blockSignals(False)
        self.set_scale(self.scale_percent)

    def _set_row(self, row: int, day: int, work: Work):
        def set_item(col: int, text: str, checkable: bool = False, checked: bool = False):
            item = QTableWidgetItem(text)
            if checkable:
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
                item.setText("")
            self.table.setItem(row, col, item)
        set_item(0, str(day))
        set_item(1, work.name)
        set_item(2, str(work.plan))
        set_item(3, str(work.done))
        pri_item = QTableWidgetItem(str(work.priority))
        pri_item.setForeground(QColor(color_for(work.priority)))
        self.table.setItem(row, 4, pri_item)
        set_item(5, "", checkable=True, checked=work.is_adult)
        set_item(6, work.comment)

    # ------------------------------------------------------------------
    def _on_item_changed(self, item: QTableWidgetItem):
        row = item.row()
        col = item.column()
        if row not in self._row_map:
            return
        day, work = self._row_map[row]
        try:
            if col == 0:
                new_day = int(item.text())
                if new_day != day:
                    self.month_data[day].remove(work)
                    self.month_data.setdefault(new_day, []).append(work)
                    if not self.month_data[day]:
                        del self.month_data[day]
                    self._refresh_table()
                    self.save_month()
                    return
            elif col == 1:
                work.name = item.text()
            elif col == 2:
                work.plan = int(item.text() or 0)
            elif col == 3:
                work.done = int(item.text() or 0)
            elif col == 4:
                work.priority = int(item.text() or 1)
            elif col == 5:
                work.is_adult = item.checkState() == Qt.Checked
            elif col == 6:
                work.comment = item.text()
        except ValueError:
            pass
        self.save_month()

    def _show_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0 or row not in self._row_map:
            return
        menu = QMenu(self)
        act_del = menu.addAction("Удалить")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_del:
            day, work = self._row_map[row]
            self.month_data[day].remove(work)
            if not self.month_data[day]:
                del self.month_data[day]
            self.save_month()
            self._refresh_table()

    # ------------------------------------------------------------------
    def add_work(self):
        day, ok = QInputDialog.getInt(self, "День", "День", 1, 1, 31)
        if not ok:
            return
        name, ok = QInputDialog.getText(self, "Работа", "Работа")
        if not ok or not name:
            return
        plan, ok = QInputDialog.getInt(self, "План", "План", 0, 0, 9999)
        if not ok:
            return
        done, ok = QInputDialog.getInt(self, "Готово", "Готово", 0, 0, 9999)
        if not ok:
            return
        priority, ok = QInputDialog.getInt(self, "Приоритет", "Приоритет (1-4)", 1, 1, 4)
        if not ok:
            return
        adult, ok = QInputDialog.getItem(self, "Категория", "Категория", ["0+", "18+"], 0)
        if not ok:
            return
        comment, ok = QInputDialog.getText(self, "Комментарий", "Комментарий")
        if not ok:
            return
        w = Work(name=name, plan=plan, done=done, priority=priority, is_adult=(adult == "18+"), comment=comment)
        self.month_data.setdefault(day, []).append(w)
        self.save_month()
        self._refresh_table()

    # ------------------------------------------------------------------
    def load_month(self, year: int, month: int):
        data = self.storage.load_json(f"{year}/{month:02d}.json", {}) or {}
        self.month_data = {
            int(d): [Work.from_dict(w) for w in wl]
            for d, wl in data.items()
        }

    def save_month(self):
        y = self.year.value()
        m = self.month.currentIndex() + 1
        data = {
            str(day): [w.to_dict() for w in works]
            for day, works in self.month_data.items() if works
        }
        self.storage.save_json(f"{y}/{m:02d}.json", data)
