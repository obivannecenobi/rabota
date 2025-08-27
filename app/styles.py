from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsBlurEffect


class GlassBlurEffect(QGraphicsBlurEffect):
    """Blur effect with optional texture and sharpness overlays."""

    def __init__(self, texture: int = 0, sharpness: int = 0, parent=None):
        super().__init__(parent)
        self._texture = max(0, texture)
        self._sharpness = max(0, sharpness)

    def setTexture(self, value: int) -> None:
        self._texture = max(0, value)

    def setSharpness(self, value: int) -> None:
        self._sharpness = max(0, value)

    def draw(self, painter):  # type: ignore[override]
        # First let the base class draw the blurred source
        super().draw(painter)

        rect = self.boundingRect()

        if self._texture:
            # Overlay a translucent white to emulate frosted texture
            alpha = max(0, min(255, self._texture))
            painter.fillRect(rect, QColor(255, 255, 255, alpha))

        if self._sharpness:
            # Draw a subtle border to give an impression of sharpness
            pen = painter.pen()
            pen.setColor(QColor(255, 255, 255, max(0, min(255, self._sharpness))))
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

# Styles used across the application
MARK_STYLESHEET_TEMPLATE = "background:{}; border-radius:4px;"
DAY_PLACEHOLDER_STYLESHEET = "color: gray;"
ADULT_LABEL_STYLESHEET = "color: red;"

def base_stylesheet(accent: str = "#00E5FF", neon_size: int = 8, neon_intensity: int = 60):
    '''Return a base dark stylesheet with rounded controls and a pseudo-neon focus.'''
    # Neon via shadow-like glow using box-shadow is not native in Qt stylesheets.
    # We emulate with focus ring and accent borders.
    col = QColor(accent)
    shadow = f"rgba({col.red()}, {col.green()}, {col.blue()}, {neon_intensity/100})"
    return f"""
    * {{
        font-size: 13px;
    }}
    QWidget {{
        background-color: #151718;
        color: #EAEAEA;
    }}
    QMainWindow {{
        background-color: #151718;
    }}
    QDockWidget, QFrame, QGroupBox, QTableView, QTableWidget, QListView, QTreeView {{
        background-color: #1B1D1E;
        border: 1px solid #2A2D2E;
        border-radius: 10px;
    }}
    QDockWidget::title {{
        padding: 2px;
        margin: 0;
    }}

    QHeaderView::section {{
        background-color: #2A2D2E;
        color: #D0D0D0;
        border: none;
        padding: 6px;
        font-weight: bold;
    }}
    QPushButton {{
        background-color: #202325;
        border: 1px solid #2E3235;
        border-radius: 10px;
        padding: 8px 12px;
    }}
    QPushButton:hover {{
        border-color: {accent};
    }}
    QPushButton:pressed {{
        background-color: #191B1C;
    }}
    QToolBar, QMenuBar {{
        background-color: #141617;
        border: none;
    }}
    QStatusBar {{
        background-color: #141617;
        border-top: 1px solid #2A2D2E;
    }}
    QLineEdit, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit {{
        background-color: #202325;
        border: 1px solid #2E3235;
        border-radius: 8px;
        padding: 6px 8px;
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {accent};
        box-shadow: 0 0 {neon_size}px {shadow};
    }}
    QDockWidget:focus, QFrame:focus, QGroupBox:focus, QTableView:focus,
    QTableWidget:focus, QListView:focus, QTreeView:focus {{
        border: 1px solid {accent};
        box-shadow: 0 0 {neon_size}px {shadow};
    }}
    QDockWidget:hover, QFrame:hover, QGroupBox:hover, QTableView:hover,
    QTableWidget:hover, QListView:hover, QTreeView:hover {{
        border-color: {accent};
    }}
    """


def light_stylesheet(accent: str = "#000000", neon_size: int = 8, neon_intensity: int = 60):
    """Return a simple light stylesheet with white backgrounds and black text."""
    col = QColor(accent)
    shadow = f"rgba({col.red()}, {col.green()}, {col.blue()}, {neon_intensity/100})"
    return f"""
    * {{
        font-size: 13px;
    }}
    QWidget {{
        background-color: #FFFFFF;
        color: #000000;
    }}
    QMainWindow {{
        background-color: #FFFFFF;
    }}
    QDockWidget, QFrame, QGroupBox, QTableView, QTableWidget, QListView, QTreeView {{
        background-color: #F5F5F5;
        border: 1px solid #C0C0C0;
        border-radius: 10px;
    }}
    QDockWidget::title {{
        padding: 2px;
        margin: 0;
    }}

    QHeaderView::section {{
        background-color: #E0E0E0;
        color: #202020;
        border: none;
        padding: 6px;
        font-weight: bold;
    }}
    QPushButton {{
        background-color: #E8E8E8;
        border: 1px solid #C0C0C0;
        border-radius: 10px;
        padding: 8px 12px;
    }}
    QPushButton:hover {{
        border-color: {accent};
    }}
    QPushButton:pressed {{
        background-color: #D0D0D0;
    }}
    QToolBar, QMenuBar {{
        background-color: #F0F0F0;
        border: none;
    }}
    QStatusBar {{
        background-color: #F0F0F0;
        border-top: 1px solid #C0C0C0;
    }}
    QLineEdit, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit {{
        background-color: #FFFFFF;
        border: 1px solid #C0C0C0;
        border-radius: 8px;
        padding: 6px 8px;
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {accent};
        box-shadow: 0 0 {neon_size}px {shadow};
    }}
    QDockWidget:focus, QFrame:focus, QGroupBox:focus, QTableView:focus,
    QTableWidget:focus, QListView:focus, QTreeView:focus {{
        border: 1px solid {accent};
        box-shadow: 0 0 {neon_size}px {shadow};
    }}
    QDockWidget:hover, QFrame:hover, QGroupBox:hover, QTableView:hover,
    QTableWidget:hover, QListView:hover, QTreeView:hover {{
        border-color: {accent};
    }}
    """
    
def apply_glass_effect(window, enabled: bool, opacity: float = 0.9,
                       blur: int | None = None, texture: int | None = None,
                       sharpness: int | None = None):
    """Apply a simple glass-like effect.

    Besides adjusting window opacity, this helper stores the desired blur,
    texture and sharpness values and applies a ``GlassBlurEffect`` to the
    window.  Parameters are optional; if omitted the values are read from the
    window's ``prefs`` dictionary when available.  When the underlying Qt
    features are unavailable, the effect is safely disabled.
    """

    prefs = getattr(window, "prefs", {})
    if blur is None:
        blur = prefs.get("glass_blur", 6)
    if texture is None:
        texture = prefs.get("glass_texture", 2)
    if sharpness is None:
        sharpness = prefs.get("glass_sharpness", 5)

    if enabled:
        window.setWindowOpacity(opacity)
        try:
            effect = GlassBlurEffect(texture=texture, sharpness=sharpness)
            effect.setBlurRadius(blur)
            window.setGraphicsEffect(effect)
        except Exception:
            # If the effect cannot be created (e.g. missing Qt features),
            # disable it gracefully
            window.setWindowOpacity(1.0)
            window.setGraphicsEffect(None)
    else:
        window.setWindowOpacity(1.0)
        window.setGraphicsEffect(None)

    # Persist values on the window for future calls
    prefs["glass_blur"] = blur
    prefs["glass_texture"] = texture
    prefs["glass_sharpness"] = sharpness
