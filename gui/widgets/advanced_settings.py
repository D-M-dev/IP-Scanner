"""
Advanced settings widget
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
    QLabel, QSpinBox, QCheckBox
)

class AdvancedSettings(QWidget):
    """Advanced settings widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI for advanced settings"""
        layout = QVBoxLayout(self)
        
        scan_group = QGroupBox("Advanced Scan Settings")
        scan_layout = QGridLayout(scan_group)
        
        scan_layout.addWidget(QLabel("Parallel threads count:"), 0, 0)
        self.threads_spinbox = QSpinBox()
        self.threads_spinbox.setRange(1, 200)
        self.threads_spinbox.setValue(50)
        scan_layout.addWidget(self.threads_spinbox, 0, 1)
        
        scan_layout.addWidget(QLabel("Timeout (seconds):"), 1, 0)
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(1, 10)
        self.timeout_spinbox.setValue(1)
        scan_layout.addWidget(self.timeout_spinbox, 1, 1)
        
        self.port_scan_checkbox = QCheckBox("Include port scanning")
        scan_layout.addWidget(self.port_scan_checkbox, 2, 0, 1, 2)
        
        self.wol_checkbox = QCheckBox("Attempt Wake-on-LAN")
        scan_layout.addWidget(self.wol_checkbox, 3, 0, 1, 2)
        
        layout.addWidget(scan_group)
        
        export_group = QGroupBox("Export Settings")
        export_layout = QGridLayout(export_group)
        
        self.auto_export_checkbox = QCheckBox("Auto export after scan")
        export_layout.addWidget(self.auto_export_checkbox, 0, 0)
        
        self.include_timestamp_checkbox = QCheckBox("Include timestamp in filename")
        self.include_timestamp_checkbox.setChecked(True)
        export_layout.addWidget(self.include_timestamp_checkbox, 1, 0)
        
        layout.addWidget(export_group)
        layout.addStretch()