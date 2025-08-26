from enum import IntEnum
from typing import Iterable, Dict, Tuple
from PySide6.QtCore import QTimer

class PriorityLevel(IntEnum):
    One = 1
    Two = 2
    Three = 3
    Four = 4

PRIORITY_COLORS = {
    PriorityLevel.One: "#00FF00",  # Bright Green
    PriorityLevel.Two: "#008000",  # Dark Green
    PriorityLevel.Three: "#FFFF00",  # Yellow
    PriorityLevel.Four: "#FFA500",  # Orange
}

# Human readable descriptions for tooltips/legends
PRIORITY_DESCRIPTIONS = {
    PriorityLevel.One: "Низкий",
    PriorityLevel.Two: "Средний",
    PriorityLevel.Three: "Высокий",
    PriorityLevel.Four: "Срочный",
}

class PriorityFilter(IntEnum):
    OneToFour = 0
    OneToTwo = 1

def color_for(priority: int) -> str:
    try:
        return PRIORITY_COLORS[PriorityLevel(priority)]
    except Exception:
        return "#ffffff"

def sort_tasks(tasks: Iterable) -> Iterable:
    return sorted(tasks, key=lambda t: getattr(t, "priority", 0), reverse=True)

def filter_tasks(tasks: Iterable, filt: PriorityFilter) -> Iterable:
    if filt == PriorityFilter.OneToTwo:
        return [t for t in tasks if getattr(t, "priority", 4) <= 2]
    return tasks

_overrides: Dict[object, Tuple[QTimer, int]] = {}


def override_priority(task: object, new_priority: int, duration_sec: int = 86400) -> None:
    original = getattr(task, "priority", new_priority)
    if task in _overrides:
        cancel_override(task)
    setattr(task, "priority", new_priority)
    timer = QTimer()
    timer.setSingleShot(True)

    def _reset():
        setattr(task, "priority", original)
        _overrides.pop(task, None)

    timer.timeout.connect(_reset)
    _overrides[task] = (timer, original)
    timer.start(duration_sec * 1000)


def cancel_override(task: object) -> None:
    data = _overrides.pop(task, None)
    if data:
        timer, original = data
        timer.stop()
        setattr(task, "priority", original)
