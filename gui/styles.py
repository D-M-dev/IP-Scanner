"""
Application styles
"""

def get_main_window_style():
    """Return main window stylesheet"""
    return """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a1a2e, stop:1 #16213e);
        }
        QWidget {
            background: transparent;
            color: #e0e0e0;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QGroupBox {
            font-size: 14px;
            font-weight: bold;
            color: #a0a0ff;
            border: 2px solid #483d8b;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QTableWidget {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid #483d8b;
            border-radius: 8px;
            gridline-color: #483d8b;
            selection-background-color: rgba(106, 90, 205, 0.3);
        }
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid rgba(72, 61, 139, 0.3);
        }
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #6a5acd, stop:1 #483d8b);
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        QLineEdit, QComboBox, QSpinBox {
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid #483d8b;
            border-radius: 6px;
            padding: 8px;
            color: white;
            font-size: 12px;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
            border-color: #6a5acd;
        }
        QProgressBar {
            border: 2px solid #483d8b;
            border-radius: 8px;
            text-align: center;
            color: white;
            font-weight: bold;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #6a5acd, stop:1 #9370db);
            border-radius: 6px;
        }
        QTabWidget::pane {
            border: 2px solid #483d8b;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
        }
        QTabBar::tab {
            background: rgba(72, 61, 139, 0.3);
            color: #e0e0e0;
            padding: 12px 20px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        QTabBar::tab:selected {
            background: #6a5acd;
            color: white;
        }
        QTextEdit {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid #483d8b;
            border-radius: 6px;
            color: #e0e0e0;
            font-family: 'Consolas', monospace;
        }
    """