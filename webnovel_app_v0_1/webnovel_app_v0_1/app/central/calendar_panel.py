from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QTableWidget, QTableWidgetItem, QSpinBox

class CalendarPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_percent = 100
        self.scale_edit_mode = False

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
        self.table.horizontalHeader().setVisible(False)
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
        # Fill calendar grid with day numbers for selected month/year
        y = self.year.value()
        m = self.month.currentIndex()+1
        first = QDate(y, m, 1)
        # Qt: 1=Mon..7=Sun
        start_col = first.dayOfWeek() - 1  # 0..6 (Mon..Sun)
        day = 1
        days_in_month = first.daysInMonth()
        # Clear
        for r in range(6):
            for c in range(7):
                self.table.setItem(r, c, QTableWidgetItem(""))
        r = 0; c = start_col
        while day <= days_in_month and r < 6:
            it = QTableWidgetItem(str(day))
            self.table.setItem(r, c, it)
            day += 1
            c += 1
            if c>=7:
                c = 0; r += 1
