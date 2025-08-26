from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem

class TopMonthPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit_mode = False
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("ТОП месяца"))
        self.table = QTableWidget(5, 6, self)
        self.table.setHorizontalHeaderLabels(["Работа","Главы всего","Сделано","Профит","Просмотры","Лайки"])
        lay.addWidget(self.table)

    def set_edit_mode(self, enabled: bool):
        self.edit_mode = enabled
        self.table.setEditTriggers(QTableWidget.DoubleClicked if enabled else QTableWidget.NoEditTriggers)
