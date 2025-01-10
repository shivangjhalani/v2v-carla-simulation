from PySide6.QtWidgets import QWidget

def apply_styles(widget: QWidget):
    """Apply common styles to widgets"""
    widget.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
        }
        QLabel {
            color: #e0e0e0;
            font-size: 14px;
        }
        QFrame {
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 8px;
            background-color: #333333;
        }
    """)
