from dataclasses import dataclass, asdict
from pathlib import Path

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QTableWidget,
    QSpinBox, QFrame, QInputDialog, QMenu
)

from ..storage import Storage
from ..priority_service import (
    PriorityFilter,
    color_for,
    sort_tasks,
    filter_tasks,
    override_priority,
    PriorityLevel,
    PRIORITY_DESCRIPTIONS,
)
from ..styles import (
    ADULT_LABEL_STYLESHEET,
    DAY_PLACEHOLDER_STYLESHEET,
    MARK_STYLESHEET_TEMPLATE,
)


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


class PriorityMark(QFrame):
    def __init__(self, panel: "CalendarPanel", day: int, work: Work):
        super().__init__()
        self.panel = panel
        self.day = day
        self.work = work
        self.setFixedSize(8, 8)
        self.setCursor(Qt.PointingHandCursor)
        self._update()

    def _update(self):
        self.setStyleSheet(
            MARK_STYLESHEET_TEMPLATE.format(color_for(self.work.priority))
        )
        desc = PRIORITY_DESCRIPTIONS.get(PriorityLevel(self.work.priority), "")
        tip = f"Приоритет: {self.work.priority}"
        if desc:
            tip += f" — {desc}"
        tip += "\nЛКМ: изменить\nПКМ: выбрать"
        self.setToolTip(tip)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            p = self.work.priority + 1
            if p > int(PriorityLevel.Four):
                p = int(PriorityLevel.One)
            override_priority(self.work, p)
            self.panel.save_month()
            self.panel.refresh_day(self.day)
        elif event.button() == Qt.RightButton:
            menu = QMenu(self)
            actions = []
            for lvl in PriorityLevel:
                act = menu.addAction(f"{int(lvl)}")
                act.setData(int(lvl))
                actions.append(act)
            chosen = menu.exec(self.mapToGlobal(event.pos()))
            if chosen:
                p = int(chosen.data())
                if p != self.work.priority:
                    override_priority(self.work, p)
                    self.panel.save_month()
                    self.panel.refresh_day(self.day)
        else:
            super().mousePressEvent(event)


class WorkLabel(QLabel):
    def __init__(self, panel: "CalendarPanel", day: int, work: Work):
        super().__init__()
        self.panel = panel
        self.day = day
        self.work = work
        self._update_text()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

    def _update_text(self):
        txt = f"{self.work.name} {self.work.plan}/{self.work.done}"
        self.setText(txt)
        desc = PRIORITY_DESCRIPTIONS.get(PriorityLevel(self.work.priority), "")
        tip = f"Приоритет: {self.work.priority} — {desc}" if desc else f"Приоритет: {self.work.priority}"
        if self.work.comment:
            tip += f"\n{self.work.comment}"
        self.setToolTip(tip)
        # Set border color according to priority
        color = color_for(self.work.priority)
        self.setStyleSheet(f"border: 1px solid {color};")

    def _show_menu(self, pos):
        menu = QMenu(self)
        actions = []
        for lvl in PriorityLevel:
            act = menu.addAction(f"{int(lvl)}")
            act.setData(int(lvl))
            actions.append(act)
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen:
            p = int(chosen.data())
            if p != self.work.priority:
                override_priority(self.work, p)
                self.panel.save_month()
                self.panel.refresh_day(self.day)
                self._update_text()

    def mouseDoubleClickEvent(self, event):
        self.panel.edit_work(self.day, self.work)
        self._update_text()
        super().mouseDoubleClickEvent(event)

class CalendarPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_percent = 100
        self.scale_edit_mode = False
        self.storage = Storage(Path("data"))
        self.month_data: dict[int, list[Work]] = {}
        self._day_pos: dict[int, tuple[int, int]] = {}
        self.priority_filter = PriorityFilter.OneToFour

        lay = QVBoxLayout(self)
        ctrl = QHBoxLayout()
        self.year = QSpinBox(); self.year.setRange(2000, 2100); self.year.setValue(QDate.currentDate().year())
        self.month = QComboBox(); self.month.addItems(["Янв","Фев","Мар","Апр","Май","Июн","Июл","Авг","Сен","Окт","Ноя","Дек"])
        self.month.setCurrentIndex(QDate.currentDate().month()-1)

        ctrl.addWidget(QLabel("Год")); ctrl.addWidget(self.year)
        ctrl.addSpacing(12)
        ctrl.addWidget(QLabel("Месяц")); ctrl.addWidget(self.month)
        ctrl.addStretch(1)
        lay.addLayout(ctrl)

        self.table = QTableWidget(6, 7, self)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        lay.addWidget(self.table)

        self.rebuild()

        self.year.valueChanged.connect(self.rebuild)
        self.month.currentIndexChanged.connect(self.rebuild)

    def set_scale(self, percent: int):
        self.scale_percent = max(50, min(200, percent))
        f = self.font()
        f.setPointSize(int(12 * self.scale_percent/100))
        self.setFont(f)
        # Adjust row heights
        for r in range(self.table.rowCount()):
            self.table.setRowHeight(r, int(80 * self.scale_percent/100))

    def set_scale_edit_mode(self, enabled: bool):
        self.scale_edit_mode = enabled
        self.table.setEditTriggers(QTableWidget.DoubleClicked if enabled else QTableWidget.NoEditTriggers)

    def rebuild(self):
        # Fill calendar grid with day numbers and works for selected month/year
        y = self.year.value()
        m = self.month.currentIndex() + 1
        self.load_month(y, m)
        first = QDate(y, m, 1)
        start_col = first.dayOfWeek() - 1  # 0..6 (Mon..Sun)
        days_in_month = first.daysInMonth()
        self.table.horizontalHeader().setVisible(True)
        self.table.setHorizontalHeaderLabels(["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"])
        # Clear
        self._day_pos.clear()
        for r in range(6):
            for c in range(7):
                self.table.setCellWidget(r, c, QWidget())

        # Previous month days
        prev = first.addMonths(-1)
        prev_days = prev.daysInMonth()
        for c in range(start_col):
            day_num = prev_days - start_col + c + 1
            self.table.setCellWidget(0, c, self.build_day_placeholder(day_num))

        # Current month days
        day = 1
        r = 0
        c = start_col
        while day <= days_in_month and r < 6:
            self.table.setCellWidget(r, c, self.build_day_widget(day))
            self._day_pos[day] = (r, c)
            day += 1
            c += 1
            if c >= 7:
                c = 0
                r += 1

        # Next month days
        next_day = 1
        while r < 6:
            self.table.setCellWidget(r, c, self.build_day_placeholder(next_day))
            next_day += 1
            c += 1
            if c >= 7:
                c = 0
                r += 1

    def build_day_placeholder(self, day: int) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(2)
        day_lbl = QLabel(str(day))
        day_lbl.setStyleSheet(DAY_PLACEHOLDER_STYLESHEET)
        lay.addWidget(day_lbl)
        lay.addStretch(1)
        w.setEnabled(False)
        return w

    def build_day_widget(self, day: int) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(2)
        day_lbl = QLabel(str(day))
        lay.addWidget(day_lbl)
        w.setContextMenuPolicy(Qt.CustomContextMenu)
        w.customContextMenuRequested.connect(lambda pos, d=day, wid=w: self.show_day_menu(d, wid, pos))
        works = self.month_data.get(day, [])
        works = filter_tasks(works, self.priority_filter)
        for work in sort_tasks(works):
            hl = QHBoxLayout()
            mark = PriorityMark(self, day, work)
            hl.addWidget(mark, alignment=Qt.AlignTop)
            lbl = WorkLabel(self, day, work)
            hl.addWidget(lbl, alignment=Qt.AlignTop)
            hl.addStretch(1)
            if work.is_adult:
                adult_lbl = QLabel("18+")
                adult_lbl.setStyleSheet(ADULT_LABEL_STYLESHEET)
                hl.addWidget(adult_lbl, alignment=Qt.AlignRight | Qt.AlignTop)
            lay.addLayout(hl)
        lay.addStretch(1)
        return w

    def set_priority_filter(self, filt: PriorityFilter):
        self.priority_filter = filt
        for day in list(self.month_data.keys()):
            self.refresh_day(day)

    def edit_work(self, day: int, work: Work):
        name, ok = QInputDialog.getText(self, "Имя", "Имя", text=work.name)
        if ok and name:
            work.name = name
        adult, ok = QInputDialog.getItem(
            self, "Категория", "Категория", ["0+", "18+"], 1 if work.is_adult else 0
        )
        if ok:
            work.is_adult = adult == "18+"
        comment, ok = QInputDialog.getText(self, "Комментарий", "Комментарий", text=work.comment)
        if ok:
            work.comment = comment
        plan, ok = QInputDialog.getInt(self, "Plan", "Plan", work.plan, 0, 9999)
        if ok:
            work.plan = plan
        done, ok = QInputDialog.getInt(self, "Done", "Done", work.done, 0, 9999)
        if ok:
            work.done = done
        p, ok = QInputDialog.getInt(self, "Приоритет", "Приоритет (1-4)", work.priority, 1, 4)
        if ok and p != work.priority:
            override_priority(work, p)
        self.save_month()
        self.refresh_day(day)

    def add_work(self, day: int):
        name, ok = QInputDialog.getText(self, "Имя", "Имя")
        if not ok or not name:
            return
        adult, ok = QInputDialog.getItem(
            self, "Категория", "Категория", ["0+", "18+"], 0
        )
        if not ok:
            return
        comment, ok = QInputDialog.getText(self, "Комментарий", "Комментарий")
        if not ok:
            return
        plan, ok = QInputDialog.getInt(self, "Plan", "Plan", 0, 0, 9999)
        if not ok:
            return
        done, ok = QInputDialog.getInt(self, "Done", "Done", 0, 0, 9999)
        if not ok:
            return
        priority, ok = QInputDialog.getInt(self, "Приоритет", "Приоритет (1-4)", 1, 1, 4)
        if not ok:
            return
        w = Work(
            name=name,
            plan=plan,
            done=done,
            priority=priority,
            is_adult=(adult == "18+"),
            comment=comment,
        )
        self.month_data.setdefault(day, []).append(w)
        self.save_month()
        self.refresh_day(day)

    def show_day_menu(self, day: int, widget: QWidget, pos):
        menu = QMenu(widget)
        act_add = menu.addAction("Добавить работу")
        action = menu.exec(widget.mapToGlobal(pos))
        if action == act_add:
            self.add_work(day)

    def refresh_day(self, day: int):
        pos = self._day_pos.get(day)
        if pos:
            r, c = pos
            self.table.setCellWidget(r, c, self.build_day_widget(day))

    def load_month(self, year: int, month: int):
        data = self.storage.load_json(f"{year}/{month:02d}.json", default={}) or {}
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
