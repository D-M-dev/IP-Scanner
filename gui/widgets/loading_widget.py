"""
Loading animation widget
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QBrush, QPen

class LoadingWidget(QWidget):
    """Loading animation widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        
    def start_animation(self):
        """Start animation"""
        self.timer.start(50)
        self.show()
    
    def stop_animation(self):
        """Stop animation"""
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        """Rotate loading indicator"""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Draw loading indicator"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        
        for i in range(8):
            painter.save()
            painter.translate(center)
            painter.rotate(self.angle + i * 45)
            
            opacity = 1.0 - (i * 0.1)
            color = QColor(106, 90, 205, int(255 * opacity))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            painter.drawEllipse(15, -3, 6, 6)
            painter.restore()