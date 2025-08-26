from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame

class StatsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Результаты / Статистика"))
        self.toggle_btn = QPushButton("Показать графики")
        lay.addWidget(self.toggle_btn)
        self.charts_frame = QFrame(self)
        self.charts_frame.setFrameShape(QFrame.StyledPanel)
        self.charts_frame.setVisible(False)
        lay.addWidget(self.charts_frame)

        self.toggle_btn.clicked.connect(self.toggle_charts)

    def toggle_charts(self):
        vis = not self.charts_frame.isVisible()
        self.charts_frame.setVisible(vis)
        self.toggle_btn.setText("Скрыть графики" if vis else "Показать графики")
