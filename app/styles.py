from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsBlurEffect

def base_stylesheet(accent: str = "#00E5FF", neon_size: int = 8, neon_intensity: int = 60):
    '''Return a base dark stylesheet with rounded controls and a pseudo-neon focus.'''
    # Neon via shadow-like glow using box-shadow is not native in Qt stylesheets.
    # We emulate with focus ring and accent borders.
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
    QDockWidget::title {
        padding: 2px;
        margin: 0;
    }

    QHeaderView::section {{
        background-color: #2A2D2E;
        color: #D0D0D0;
        border: none;
        padding: 6px;
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
    }}
    """


def light_stylesheet(accent: str = "#000000", neon_size: int = 8, neon_intensity: int = 60):
    """Return a simple light stylesheet with white backgrounds and black text."""
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
    QDockWidget::title {
        padding: 2px;
        margin: 0;
    }

    QHeaderView::section {{
        background-color: #E0E0E0;
        color: #202020;
        border: none;
        padding: 6px;
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
    }}
    """
    
def apply_glass_effect(window, enabled: bool, opacity: float = 0.9,
                       blur: int | None = None, texture: int | None = None,
                       sharpness: int | None = None):
    """Apply a simple glass-like effect.

    Besides adjusting window opacity, this helper stores the desired blur,
    texture and sharpness values and applies a ``QGraphicsBlurEffect`` to the
    window.  Parameters are optional; if omitted the values are read from the
    window's ``prefs`` dictionary when available.
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
        effect = QGraphicsBlurEffect()
        effect.setBlurRadius(blur)
        window.setGraphicsEffect(effect)
    else:
        window.setWindowOpacity(1.0)
        window.setGraphicsEffect(None)

    # Persist values on the window for future calls
    prefs["glass_blur"] = blur
    prefs["glass_texture"] = texture
    prefs["glass_sharpness"] = sharpness
