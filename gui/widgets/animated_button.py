"""
Animated button widget
"""
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class AnimatedButton(QPushButton):
    """Animated button with hover effects"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a5acd, stop:1 #483d8b);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7b68ee, stop:1 #6a5acd);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #483d8b, stop:1 #2f2f4f);
            }
            QPushButton:disabled {
                background: #696969;
                color: #a0a0a0;
            }
        """)