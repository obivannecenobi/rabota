"""Panel displaying delayed postings per day.

This panel keeps a simple table of upcoming chapter postings for works. Each
record contains a date, work title, chapter title and a priority which is
visualised by a coloured marker. Data is persisted via :class:`Storage` per
month/year similarly to other panels.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QInputDialog,
)

from ..storage import Storage


@dataclass
class Posting:
    """Single postponed posting entry."""

    date: str = ""
    work: str = ""
    chapter: str = ""
    priority: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Posting":
        return Posting(
            date=data.get("date", ""),
            work=data.get("work", ""),
            chapter=data.get("chapter", ""),
            priority=int(data.get("priority", 0)),
        )

class PostingsPanel(QWidget):
    """Table based panel with editable postings."""

    def __init__(self, parent=None, storage: Optional[Storage] = None):
        super().__init__(parent)
        self.edit_mode = False
        self.storage = storage or Storage(Path("data"))

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Постинг отложки по дням"))

        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(["Дата", "Работа", "Глава", "Приор."])
        lay.addWidget(self.table)

        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    # ------------------------------------------------------------------
    # helpers / UI
    def set_edit_mode(self, enabled: bool):
        self.edit_mode = enabled
        trigger = QTableWidget.DoubleClicked if enabled else QTableWidget.NoEditTriggers
        self.table.setEditTriggers(trigger)

    def _priority_color(self, p: int) -> str:
        return {
            3: "#ff5555",  # high
            2: "#ffaa00",  # medium
            1: "#55aa55",  # low
            0: "#888888",  # default
        }.get(p, "#888888")

    def _set_text(self, row: int, col: int, text: str):
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem()
            self.table.setItem(row, col, item)
        item.setText(text)

    def _set_priority(self, row: int, p: int):
        item = self.table.item(row, 3)
        if not item:
            item = QTableWidgetItem()
            self.table.setItem(row, 3, item)
        item.setData(Qt.UserRole, p)
        item.setText("●" if p else "")
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(QColor(self._priority_color(p)))

    def _on_cell_double_clicked(self, row: int, col: int):
        if not self.edit_mode:
            return
        if col == 3:
            item = self.table.item(row, col)
            current = item.data(Qt.UserRole) if item else 0
            p, ok = QInputDialog.getInt(self, "Приоритет", "Приоритет (0-3)", int(current), 0, 3)
            if ok:
                self._set_priority(row, p)
        else:
            self.table.editItem(self.table.item(row, col))

    # ------------------------------------------------------------------
    # persistence
    def load_month(self, year: int, month: int):
        data = self.storage.load_json(f"{year}/postings_{month:02d}.json", []) or []
        postings: List[Posting] = [Posting.from_dict(d) for d in data if isinstance(d, dict)]
        self.table.setRowCount(max(len(postings), 10))
        for row, p in enumerate(postings):
            self._set_text(row, 0, p.date)
            self._set_text(row, 1, p.work)
            self._set_text(row, 2, p.chapter)
            self._set_priority(row, p.priority)

    def save_month(self, year: int, month: int):
        data: List[dict] = []
        for r in range(self.table.rowCount()):
            date = self.table.item(r, 0).text() if self.table.item(r, 0) else ""
            work = self.table.item(r, 1).text() if self.table.item(r, 1) else ""
            chap = self.table.item(r, 2).text() if self.table.item(r, 2) else ""
            pr_item = self.table.item(r, 3)
            priority = pr_item.data(Qt.UserRole) if pr_item else 0
            if any([date, work, chap]):
                data.append(Posting(date, work, chap, priority).to_dict())
        self.storage.save_json(f"{year}/postings_{month:02d}.json", data)
