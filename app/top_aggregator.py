"""Utilities for aggregating monthly top statistics.

The :class:`TopAggregator` reads monthly files produced by
:class:`~app.panels.top_month_panel.TopMonthPanel` via :meth:`save_month`
and combines them over arbitrary periods.  The resulting data structure is
suitable for displaying in future reporting windows.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .storage import Storage


@dataclass
class Stats:
    """Container holding numeric statistics for a work."""

    plan: int = 0
    done: int = 0
    profit: int = 0
    views: int = 0
    likes: int = 0

    def add(self, other: "Stats") -> None:
        self.plan += other.plan
        self.done += other.done
        self.profit += other.profit
        self.views += other.views
        self.likes += other.likes


def _to_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class TopAggregator:
    """Aggregate monthly top results stored in :class:`Storage`."""

    def __init__(self, storage: Optional[Storage] = None, base_dir: Optional[Path] = None):
        self.storage = storage or Storage(base_dir or Path("data"))

    # ------------------------------------------------------------------
    # loading helpers
    def load_month(self, year: int, month: int) -> Dict[str, Stats]:
        """Load statistics for a specific month."""
        raw = self.storage.load_json(f"{year}/top_month_{month:02d}.json", {}) or {}
        result: Dict[str, Stats] = {}
        if isinstance(raw, dict):
            # new format may store meta information under special key
            if "__form__" in raw:
                raw = {k: v for k, v in raw.items() if k != "__form__"}
            for name, info in raw.items():
                result[name] = Stats(
                    plan=_to_int(info.get("plan")),
                    done=_to_int(info.get("done")),
                    profit=_to_int(info.get("profit")),
                    views=_to_int(info.get("views")),
                    likes=_to_int(info.get("likes")),
                )
        return result

    # ------------------------------------------------------------------
    # aggregation
    def aggregate_months(self, months: Iterable[Tuple[int, int]]) -> List[Tuple[str, Stats]]:
        """Aggregate over provided ``(year, month)`` pairs."""
        aggregated: Dict[str, Stats] = {}
        for year, month in months:
            month_data = self.load_month(year, month)
            for name, stats in month_data.items():
                aggregated.setdefault(name, Stats()).add(stats)
        # sort by completed chapters descending
        return sorted(aggregated.items(), key=lambda x: x[1].done, reverse=True)

    def aggregate_year(self, year: int) -> List[Tuple[str, Stats]]:
        """Aggregate statistics for the whole year."""
        return self.aggregate_months((year, m) for m in range(1, 13))

    def aggregate_quarter(self, year: int, quarter: int) -> List[Tuple[str, Stats]]:
        """Aggregate statistics for a specific quarter (1-4)."""
        if quarter not in {1, 2, 3, 4}:
            raise ValueError("quarter must be in 1..4")
        start_month = (quarter - 1) * 3 + 1
        return self.aggregate_months((year, m) for m in range(start_month, start_month + 3))

    def aggregate_period(self, start: date, end: date) -> List[Tuple[str, Stats]]:
        """Aggregate statistics between two dates (inclusive)."""
        months: List[Tuple[int, int]] = []
        y, m = start.year, start.month
        while (y < end.year) or (y == end.year and m <= end.month):
            months.append((y, m))
            m += 1
            if m > 12:
                m = 1
                y += 1
        return self.aggregate_months(months)


__all__ = ["Stats", "TopAggregator"]
