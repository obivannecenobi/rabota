from pathlib import Path
from typing import Dict, Optional, Any

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
        stats: Dict[str, Dict[str, Any]] = {}
        for works in calendar.month_data.values():
            for w in works:
                info = stats.setdefault(w.name, {"plan": 0, "done": 0, "adult": False})
                info["plan"] += w.plan
                info["done"] += w.done
                info["adult"] = info["adult"] or getattr(w, "is_adult", False)

        # load previously saved metrics
        saved = self.storage.load_json(f"{year}/top_month_{month:02d}.json", {}) or {}

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
