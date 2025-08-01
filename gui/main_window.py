"""
Main application window - enhanced for full auto network detection and modern user experience
"""

import time
import ipaddress
import csv
import json
from typing import List, Dict, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QProgressBar, QComboBox,
    QLineEdit, QTextEdit, QTabWidget, QGroupBox, QGridLayout,
    QHeaderView, QFrame, QMessageBox, QFileDialog, QMenuBar, QToolBar
)
from PySide6.QtCore import (
    QThread, Signal, QTimer, QPropertyAnimation, QEasingCurve,
    Qt
)
from PySide6.QtGui import QColor, QFont

from core.scanner import NetworkScanner
from gui.widgets.animated_button import AnimatedButton
from gui.widgets.loading_widget import LoadingWidget
from gui.widgets.network_monitor import NetworkMonitor
from gui.widgets.advanced_settings import AdvancedSettings
from gui.styles import get_main_window_style

class ScanThread(QThread):
    """Thread for network scanning"""
    progress_updated = Signal(int, int)
    device_found = Signal(dict)
    scan_finished = Signal(list)
    scan_started = Signal()

    def __init__(self, network_range: Optional[str] = None, scan_mode: str = "fast"):
        super().__init__()
        self.scanner = NetworkScanner()
        self.network_range = network_range or self.scanner.network_range
        self.scan_mode = scan_mode

    def run(self):
        """Start scanning"""
        self.scan_started.emit()
        max_workers = 100 if self.scan_mode == "fast" else 30
        devices = self.scanner.scan_network_parallel(
            self.network_range,
            max_workers=max_workers,
            progress_callback=self.progress_updated.emit,
            result_callback=self.device_found.emit
        )
        self.scan_finished.emit(devices)

    def cancel_scan(self):
        """Cancel scanning"""
        self.scanner.cancel_scan()

class IPScannerApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.scanner = NetworkScanner()
        self.scan_thread = None
        self.devices = []
        self.init_ui()
        self.setup_animations()
        self.load_network_info()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Advanced IP Scanner - LAN Network Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.setStyleSheet(get_main_window_style())

        self.create_header(main_layout)
        self.create_control_panel(main_layout)
        self.create_main_content(main_layout)
        self.create_status_bar()

    def create_header(self, parent_layout):
        """Create header with title and loading animation"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)

        title = QLabel("Advanced IP Scanner")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #9370db;
            margin: 10px;
        """)

        self.loading_widget = LoadingWidget()

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.loading_widget)

        parent_layout.addWidget(header_frame)

    def create_control_panel(self, parent_layout):
        """Create control panel"""
        control_group = QGroupBox("Scan Settings")
        control_layout = QGridLayout(control_group)

        control_layout.addWidget(QLabel("Network Range:"), 0, 0)
        self.network_input = QLineEdit()
        self.network_input.setReadOnly(True)
        self.network_input.setPlaceholderText("Auto-detected")
        control_layout.addWidget(self.network_input, 0, 1)

        control_layout.addWidget(QLabel("Scan Mode:"), 0, 2)
        self.scan_mode = QComboBox()
        self.scan_mode.addItems(["Fast Scan", "Deep Scan"])
        control_layout.addWidget(self.scan_mode, 0, 3)

        self.scan_button = AnimatedButton("Start Scanning")
        self.scan_button.clicked.connect(self.start_scan)
        control_layout.addWidget(self.scan_button, 1, 0)

        self.stop_button = AnimatedButton("Stop")
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button, 1, 1)

        self.export_button = AnimatedButton("Export")
        self.export_button.clicked.connect(self.export_results)
        control_layout.addWidget(self.export_button, 1, 2)

        self.refresh_button = AnimatedButton("Refresh Network")
        self.refresh_button.clicked.connect(self.load_network_info)
        control_layout.addWidget(self.refresh_button, 1, 3)

        parent_layout.addWidget(control_group)

    def create_main_content(self, parent_layout):
        """Create main content with tabs"""
        self.tab_widget = QTabWidget()

        self.create_results_tab()
        self.create_network_details_tab()
        self.create_logs_tab()

        parent_layout.addWidget(self.tab_widget)

    def create_results_tab(self):
        """Create scan results tab"""
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "IP Address", "Hostname", "MAC Address", "Device Type", "Time"
        ])

        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        results_layout.addWidget(self.results_table)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        results_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to scan")
        self.status_label.setStyleSheet("color: #9370db; font-weight: bold; padding: 5px;")
        results_layout.addWidget(self.status_label)

        self.tab_widget.addTab(results_widget, "Scan Results")

    def create_network_details_tab(self):
        """Create network details tab"""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        network_info_group = QGroupBox("Network Information")
        network_info_layout = QGridLayout(network_info_group)

        self.local_ip_label = QLabel("Local IP: Loading...")
        self.network_range_label = QLabel("Network Range: Loading...")
        self.gateway_label = QLabel("Gateway: Loading...")

        network_info_layout.addWidget(self.local_ip_label, 0, 0)
        network_info_layout.addWidget(self.network_range_label, 1, 0)
        network_info_layout.addWidget(self.gateway_label, 2, 0)

        details_layout.addWidget(network_info_group)

        stats_group = QGroupBox("Scan Statistics")
        stats_layout = QGridLayout(stats_group)

        self.total_devices_label = QLabel("Total Devices: 0")
        self.active_devices_label = QLabel("Active Devices: 0")
        self.scan_time_label = QLabel("Scan Time: 0s")

        stats_layout.addWidget(self.total_devices_label, 0, 0)
        stats_layout.addWidget(self.active_devices_label, 0, 1)
        stats_layout.addWidget(self.scan_time_label, 1, 0)

        details_layout.addWidget(stats_group)
        details_layout.addStretch()

        self.tab_widget.addTab(details_widget, "Network Details")

    def create_logs_tab(self):
        """Create logs tab"""
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)

        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        logs_layout.addWidget(self.logs_text)

        clear_logs_button = AnimatedButton("Clear Logs")
        clear_logs_button.clicked.connect(self.clear_logs)
        logs_layout.addWidget(clear_logs_button)

        self.tab_widget.addTab(logs_widget, "Logs")

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: rgba(72, 61, 139, 0.3);
                color: white;
                border-top: 1px solid #483d8b;
            }
        """)
        self.status_bar.showMessage("Ready to scan")

    def setup_animations(self):
        """Setup animations"""
        self.fade_animation = QPropertyAnimation(self.results_table, b"geometry")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)

    def load_network_info(self):
        """Load network information (auto-detect only)"""
        self.log_message("Loading network information...")
        try:
            local_ip, network_range = self.scanner.local_ip, self.scanner.network_range
            self.network_input.setText(network_range)
            self.local_ip_label.setText(f"Local IP: {local_ip}")
            self.network_range_label.setText(f"Network Range: {network_range}")

            network = ipaddress.IPv4Network(network_range, strict=False)
            gateway = str(network.network_address + 1)
            self.gateway_label.setText(f"Gateway: {gateway}")

            self.log_message(f"Network info loaded: {local_ip} ({network_range})")
        except Exception as e:
            self.log_message(f"Error loading network info: {e}")

    def start_scan(self):
        """Start network scan (always uses auto-detected range)"""
        network_range = self.scanner.network_range
        self.network_input.setText(network_range)
        self.log_message(f"Starting network scan: {network_range}")
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.loading_widget.start_animation()
        self.results_table.setRowCount(0)
        self.devices = []
        scan_mode = "fast" if self.scan_mode.currentText() == "Fast Scan" else "deep"
        self.scan_thread = ScanThread(network_range, scan_mode)
        self.scan_thread.progress_updated.connect(self.update_progress)
        self.scan_thread.device_found.connect(self.add_device_to_table)
        self.scan_thread.scan_finished.connect(self.scan_completed)
        self.scan_thread.start()
        self.scan_start_time = time.time()
        self.status_label.setText("Scanning in progress...")
        self.status_bar.showMessage("Scanning network...")

    def stop_scan(self):
        """Stop scanning"""
        if self.scan_thread:
            self.scan_thread.cancel_scan()
            self.scan_thread.quit()
            self.scan_thread.wait()
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.loading_widget.stop_animation()
        self.status_label.setText("Scan stopped")
        self.status_bar.showMessage("Scan stopped")
        self.log_message("Scan stopped by user")

    def update_progress(self, completed: int, total: int):
        """Update progress bar"""
        progress = int((completed / total) * 100)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Scanning: {completed}/{total} ({progress}%)")
        self.status_bar.showMessage(f"Scanning: {completed}/{total} IP addresses")

    def add_device_to_table(self, device: Dict):
        """Add device to results table"""
        self.devices.append(device)
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(device['ip']))
        self.results_table.setItem(row, 1, QTableWidgetItem(device['hostname']))
        self.results_table.setItem(row, 2, QTableWidgetItem(device['mac']))
        self.results_table.setItem(row, 3, QTableWidgetItem(device['device_type']))
        self.results_table.setItem(row, 4, QTableWidgetItem(device['scan_time']))
        device_type = device['device_type']
        if "Router" in device_type:
            color = QColor(255, 165, 0, 50)
        elif "Mobile" in device_type:
            color = QColor(0, 255, 0, 50)
        elif "Computer" in device_type:
            color = QColor(0, 0, 255, 50)
        elif "Printer" in device_type:
            color = QColor(255, 0, 255, 50)
        elif "Raspberry" in device_type:
            color = QColor(255, 0, 0, 50)
        else:
            color = QColor(128, 128, 128, 30)
        for col in range(5):
            item = self.results_table.item(row, col)
            if item:
                item.setBackground(color)
        self.animate_new_row(row)
        self.log_message(f"Device found: {device['ip']} ({device['device_type']})")

    def animate_new_row(self, row: int):
        """Animate new table row"""
        for col in range(5):
            item = self.results_table.item(row, col)
            if item:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                QTimer.singleShot(1000, lambda: self.remove_bold_from_item(item))

    def remove_bold_from_item(self, item):
        """Remove bold formatting from item"""
        if item:
            font = item.font()
            font.setBold(False)
            item.setFont(font)

    def scan_completed(self, devices: List[Dict]):
        """Complete scanning"""
        scan_time = time.time() - self.scan_start_time
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.loading_widget.stop_animation()
        total_devices = len(devices)
        self.total_devices_label.setText(f"Total Devices: {total_devices}")
        self.active_devices_label.setText(f"Active Devices: {total_devices}")
        self.scan_time_label.setText(f"Scan Time: {scan_time:.1f}s")
        self.status_label.setText(f"Scan completed - found {total_devices} devices")
        self.status_bar.showMessage(f"Scan completed - {total_devices} active devices")
        self.log_message(f"Scan completed in {scan_time:.1f}s - found {total_devices} devices")
        self.tab_widget.setCurrentIndex(0)

    def export_results(self):
        """Export scan results"""
        if not self.devices:
            QMessageBox.information(self, "Info", "No data available for export!")
            return
        file_path, file_type = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            f"ip_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        if not file_path:
            return
        try:
            if "csv" in file_type.lower():
                self.export_to_csv(file_path)
            else:
                self.export_to_json(file_path)
            QMessageBox.information(self, "Export", f"Data successfully exported to:\n{file_path}")
            self.log_message(f"Data exported to: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export error:\n{e}")
            self.log_message(f"Export error: {e}")

    def export_to_csv(self, file_path: str):
        """Export to CSV"""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ip', 'hostname', 'mac', 'device_type', 'scan_time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for device in self.devices:
                writer.writerow(device)

    def export_to_json(self, file_path: str):
        """Export to JSON"""
        export_data = {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'network_range': self.scanner.network_range,
                'total_devices': len(self.devices),
                'scan_mode': self.scan_mode.currentText()
            },
            'devices': self.devices
        }
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)

    def log_message(self, message: str):
        """Add message to logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs_text.append(log_entry)
        cursor = self.logs_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.logs_text.setTextCursor(cursor)

    def clear_logs(self):
        """Clear logs"""
        self.logs_text.clear()
        self.log_message("Logs cleared")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.scan_thread and self.scan_thread.isRunning():
            reply = QMessageBox.question(
                self,
                'Exit Application',
                'Scan in progress. Really exit?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.stop_scan()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

class EnhancedIPScannerApp(IPScannerApp):
    """Enhanced version of main application"""

    def __init__(self):
        super().__init__()
        self.add_advanced_features()

    def add_advanced_features(self):
        """Add advanced features"""
        self.network_monitor = NetworkMonitor()
        self.tab_widget.addTab(self.network_monitor, "Network Monitor")
        self.advanced_settings = AdvancedSettings()
        self.tab_widget.addTab(self.advanced_settings, "Advanced Settings")
        self.create_menu_bar()
        self.create_toolbar()

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background: rgba(72, 61, 139, 0.3);
                color: white;
                border-bottom: 1px solid #483d8b;
            }
            QMenuBar::item {
                background: transparent;
                padding: 8px 12px;
            }
            QMenuBar::item:selected {
                background: rgba(106, 90, 205, 0.5);
            }
            QMenu {
                background: rgba(26, 26, 46, 0.95);
                color: white;
                border: 1px solid #483d8b;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background: rgba(106, 90, 205, 0.5);
            }
        """)

        file_menu = menubar.addMenu('File')
        file_menu.addAction('Export Results', self.export_results)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)

        tools_menu = menubar.addMenu('Tools')
        tools_menu.addAction('Refresh Network Info', self.load_network_info)
        tools_menu.addAction('Clear Results', self.clear_results)
        tools_menu.addAction('Clear Logs', self.clear_logs)

        help_menu = menubar.addMenu('Help')
        help_menu.addAction('About', self.show_about)

    def create_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar('Main')
        toolbar.setStyleSheet("""
            QToolBar {
                background: rgba(72, 61, 139, 0.3);
                border-bottom: 1px solid #483d8b;
                spacing: 5px;
            }
            QToolButton {
                background: rgba(106, 90, 205, 0.3);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }
            QToolButton:hover {
                background: rgba(106, 90, 205, 0.5);
            }
        """)

        toolbar.addAction('Scan', self.start_scan)
        toolbar.addAction('Stop', self.stop_scan)
        toolbar.addSeparator()
        toolbar.addAction('Export', self.export_results)
        toolbar.addAction('Refresh', self.load_network_info)

    def clear_results(self):
        """Clear scan results"""
        self.results_table.setRowCount(0)
        self.devices = []
        self.total_devices_label.setText("Total Devices: 0")
        self.active_devices_label.setText("Active Devices: 0")
        self.scan_time_label.setText("Scan Time: 0s")
        self.log_message("Scan results cleared")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", """
        <h2>Advanced IP Scanner</h2>
        <p><b>Version:</b> 0.9.0-Beta</p>
        <p><b>Author:</b> Jupik-the-dev</p>
        <p><b>Description:</b>LAN network scanner</p>
        <h3>Features:</h3>
        <ul>
        <li>Parallel IP address scanning</li>
        <li>Hostname and MAC address detection</li>
        <li>Device type identification</li>
        <li>CSV/JSON export</li>
        <li>Network monitoring</li>
        </ul>
        <p><i>Still in testing so expect bugs!</i></p>
        <p><i>Created with PySide6 and network technology passion!</i></p>
        """)