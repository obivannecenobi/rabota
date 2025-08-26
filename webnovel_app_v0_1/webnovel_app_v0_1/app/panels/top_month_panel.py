from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem

from ..storage import Storage

if False:  # type checking only
    from ..central.calendar_panel import CalendarPanel

class TopMonthPanel(QWidget):
    """Panel showing monthly top works with editable statistics."""

    def __init__(self, parent=None, storage: Optional[Storage] = None):
        super().__init__(parent)
        self.edit_mode = False
        self.scale_percent = 100
        self.storage = storage or Storage(Path("data"))

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("ТОП месяца"))
        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels([
            "Работа",
            "Главы всего",
            "Сделано",
            "Профит",
            "Просмотры",
            "Лайки",
        ])
        lay.addWidget(self.table)

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

    def load_month(self, calendar: "CalendarPanel", year: int, month: int):
        """Load stats from CalendarPanel and stored data for given month."""
        # ensure calendar data for the month is loaded
        calendar.load_month(year, month)

        # aggregate works from calendar
        stats: Dict[str, Dict[str, int]] = {}
        for works in calendar.month_data.values():
            for w in works:
                info = stats.setdefault(w.name, {"plan": 0, "done": 0})
                info["plan"] += w.plan
                info["done"] += w.done

        # load previously saved metrics
        saved = self.storage.load_json(f"{year}/top_month_{month:02d}.json", {}) or {}

        # build table
        self.table.setRowCount(len(stats))
        for row, (name, info) in enumerate(sorted(stats.items(), key=lambda x: x[1]["done"], reverse=True)):
            self._set_item(row, 0, name, editable=False)
            self._set_item(row, 1, str(info.get("plan", 0)), editable=False)
            self._set_item(row, 2, str(info.get("done", 0)), editable=False)
            saved_row = saved.get(name, {}) if isinstance(saved, dict) else {}
            self._set_item(row, 3, str(saved_row.get("profit", "")))
            self._set_item(row, 4, str(saved_row.get("views", "")))
            self._set_item(row, 5, str(saved_row.get("likes", "")))

        self.set_scale(self.scale_percent)

    def save_month(self, year: int, month: int):
        """Persist current table values for aggregation."""
        data = self.collect_month_data()
        self.storage.save_json(f"{year}/top_month_{month:02d}.json", data)
        return data

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
            plan = int(self.table.item(r, 1).text() or 0) if self.table.item(r, 1) else 0
            done = int(self.table.item(r, 2).text() or 0) if self.table.item(r, 2) else 0
            profit = self.table.item(r, 3).text() if self.table.item(r, 3) else ""
            views = self.table.item(r, 4).text() if self.table.item(r, 4) else ""
            likes = self.table.item(r, 5).text() if self.table.item(r, 5) else ""
            data[name] = {
                "plan": plan,
                "done": done,
                "profit": profit,
                "views": views,
                "likes": likes,
            }
        return data
