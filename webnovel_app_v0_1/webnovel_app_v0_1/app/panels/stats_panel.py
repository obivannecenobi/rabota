"""Stats panel with monthly metrics and software cost details."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..storage import Storage


class ChartExpander(QWidget):
    """Collapsible section containing a line chart."""

    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        self.toggle_btn = QToolButton(text=title, checkable=True, checked=False)
        self.toggle_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_btn.setArrowType(Qt.RightArrow)
        lay.addWidget(self.toggle_btn)

        self.view = QChartView(QChart(), self)
        self.view.setVisible(False)
        lay.addWidget(self.view)

        self.toggle_btn.clicked.connect(self._on_toggled)

    def _on_toggled(self, checked: bool):
        self.view.setVisible(checked)
        self.toggle_btn.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

    # ------------------------------------------------------------------
    def set_series(self, values: List[int]):
        chart = QChart()
        series = QLineSeries()
        for i, v in enumerate(values, start=1):
            series.append(QPointF(i, v))
        chart.addSeries(series)
        chart.createDefaultAxes()
        self.view.setChart(chart)


class StatsPanel(QWidget):
    """Panel showing aggregated monthly statistics for a given year."""

    METRICS = [
        "Работ",
        "Завершённых",
        "Онгоингов",
        "Глав",
        "Знаков",
        "Просмотров",
        "Профит",
        "Реклама (РК)",
        "Лайков",
        "Спасибо",
        "Комиссия",
        "Затраты на софт",
        "Чистыми",
    ]

    def __init__(self, parent: Optional[QWidget] = None, storage: Optional[Storage] = None):
        super().__init__(parent)
        self.storage = storage or Storage(Path("data"))
        self.current_year = 0
        self.current_month = 0

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Результаты / Статистика"))

        # Metrics table ------------------------------------------------
        self.metrics_table = QTableWidget(len(self.METRICS), 13, self)
        months = [
            "Янв",
            "Фев",
            "Мар",
            "Апр",
            "Май",
            "Июн",
            "Июл",
            "Авг",
            "Сен",
            "Окт",
            "Ноя",
            "Дек",
            "Итого",
        ]
        self.metrics_table.setHorizontalHeaderLabels(months)
        self.metrics_table.setVerticalHeaderLabels(self.METRICS)
        lay.addWidget(self.metrics_table)

        # Software cost subsection ------------------------------------
        self.soft_group = QGroupBox("Затраты на софт", self)
        soft_lay = QVBoxLayout(self.soft_group)
        self.software_table = QTableWidget(0, 4, self.soft_group)
        self.software_table.setHorizontalHeaderLabels(
            ["Вид", "Прайс", "Сколько взяли", "Сумма"]
        )
        soft_lay.addWidget(self.software_table)
        lay.addWidget(self.soft_group)

        # Charts -------------------------------------------------------
        self.toggle_btn = QPushButton("Показать графики", self)
        lay.addWidget(self.toggle_btn)
        self.charts_frame = QFrame(self)
        self.charts_frame.setFrameShape(QFrame.StyledPanel)
        self.charts_frame.setVisible(False)
        lay.addWidget(self.charts_frame)

        self.toggle_btn.clicked.connect(self.toggle_charts)

        charts_lay = QVBoxLayout(self.charts_frame)
        self.chart_sections: Dict[str, ChartExpander] = {}
        for name in ["Профит", "Просмотры"]:
            ce = ChartExpander(name, self.charts_frame)
            charts_lay.addWidget(ce)
            self.chart_sections[name] = ce
        charts_lay.addStretch()

    # ------------------------------------------------------------------
    def set_month(self, year: int, month: int):
        self.current_year = year
        self.current_month = month

    def _set_item(self, table: QTableWidget, row: int, col: int, text: str):
        item = table.item(row, col)
        if not item:
            item = QTableWidgetItem()
            table.setItem(row, col, item)
        item.setText(text)

    # ------------------------------------------------------------------
    def load_year(self, year: int):
        """Aggregate monthly stats from storage and populate tables."""

        monthly_data = [
            self.storage.load_json(f"{year}/stats_{m:02d}.json", {}) or {} for m in range(1, 13)
        ]

        # Metrics table values
        for row, metric in enumerate(self.METRICS):
            total = 0
            for col, data in enumerate(monthly_data):
                val = int(data.get("metrics", {}).get(metric, 0) or 0)
                self._set_item(self.metrics_table, row, col, str(val))
                total += val
            self._set_item(self.metrics_table, row, 12, str(total))

        # Software costs aggregation
        soft: Dict[str, Dict[str, float]] = {}
        for data in monthly_data:
            for entry in data.get("software", []):
                name = entry.get("name", "")
                price = float(entry.get("price", 0) or 0)
                count = int(entry.get("count", 0) or 0)
                info = soft.setdefault(name, {"price": price, "count": 0})
                info["count"] += count

        self.software_table.setRowCount(len(soft) + 1)
        total_cost = 0.0
        row = 0
        for name, info in soft.items():
            price = info["price"]
            count = info["count"]
            cost = price * count
            total_cost += cost
            self._set_item(self.software_table, row, 0, name)
            self._set_item(self.software_table, row, 1, f"{price:g}")
            self._set_item(self.software_table, row, 2, str(count))
            self._set_item(self.software_table, row, 3, f"{cost:g}")
            row += 1
        self._set_item(self.software_table, row, 0, "Итого")
        self._set_item(self.software_table, row, 3, f"{total_cost:g}")

        # Update charts
        for name, section in self.chart_sections.items():
            values = [int(d.get("metrics", {}).get(name, 0) or 0) for d in monthly_data]
            section.set_series(values)

    # ------------------------------------------------------------------
    def toggle_charts(self):
        vis = not self.charts_frame.isVisible()
        self.charts_frame.setVisible(vis)
        self.toggle_btn.setText("Скрыть графики" if vis else "Показать графики")

        if self.current_year and self.current_month:
            data = self.storage.load_json(
                f"{self.current_year}/stats_{self.current_month:02d}.json", {}
            ) or {}
            data["charts_visible"] = vis
            self.storage.save_json(
                f"{self.current_year}/stats_{self.current_month:02d}.json", data
            )

