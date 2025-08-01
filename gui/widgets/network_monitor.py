"""
Network monitoring widget with live statistics and professional stylized history graph.
Graphs now show axis values, dynamic scaling, and grid lines for better readability.
"""

import platform
import re
import subprocess
import socket
import time
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel
)
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush

class NetworkMonitor(QWidget):
    """Network monitoring widget with live stats and stylized graphs"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize histories BEFORE setup_ui!
        self.ping_history = deque(maxlen=60)       # last 60 pings (2min if update every 2s)
        self.bandwidth_history = deque(maxlen=60)  # last 60 bandwidth samples
        self.last_rx = None
        self.last_tx = None
        self.last_time = None

        self.setup_ui()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(2000)  # Update every 2 seconds

    def setup_ui(self):
        """Setup UI for monitoring and graphs"""
        layout = QVBoxLayout(self)
        stats_group = QGroupBox("Network Statistics")
        stats_layout = QGridLayout(stats_group)

        self.ping_label = QLabel("Ping to gateway: Measuring...")
        self.dns_label = QLabel("DNS test: Testing...")
        self.bandwidth_label = QLabel("Bandwidth: Measuring...")

        self.ping_stats_label = QLabel("Ping stats: N/A")
        self.bandwidth_stats_label = QLabel("Bandwidth stats: N/A")

        stats_layout.addWidget(self.ping_label, 0, 0)
        stats_layout.addWidget(self.ping_stats_label, 0, 1)
        stats_layout.addWidget(self.dns_label, 1, 0)
        stats_layout.addWidget(self.bandwidth_label, 2, 0)
        stats_layout.addWidget(self.bandwidth_stats_label, 2, 1)

        layout.addWidget(stats_group)

        self.graph_group = QGroupBox("Live Graphs")
        graph_layout = QVBoxLayout(self.graph_group)

        self.ping_graph = PingGraphWidget(self.ping_history)
        self.bandwidth_graph = BandwidthGraphWidget(self.bandwidth_history)
        graph_layout.addWidget(QLabel("Ping (ms) History:"))
        graph_layout.addWidget(self.ping_graph)
        graph_layout.addWidget(QLabel("Bandwidth (KB/s) History:"))
        graph_layout.addWidget(self.bandwidth_graph)

        layout.addWidget(self.graph_group)

    def update_stats(self):
        """Update network statistics and graphs"""

        # Ping test to gateway (8.8.8.8)
        ping_value = None
        try:
            if platform.system().lower() == "windows":
                result = subprocess.run(
                    ["ping", "-n", "1", "8.8.8.8"],
                    capture_output=True, text=True, timeout=3
                )
            else:
                result = subprocess.run(
                    ["ping", "-c", "1", "8.8.8.8"],
                    capture_output=True, text=True, timeout=3
                )

            if result.returncode == 0:
                output = result.stdout
                ping_time = re.search(r'time[=<]?(\d+\.?\d*)', output)
                if ping_time:
                    ping_value = float(ping_time.group(1))
                    self.ping_label.setText(f"Internet ping: {ping_value:.1f} ms")
                else:
                    self.ping_label.setText("Internet ping: OK")
            else:
                self.ping_label.setText("Internet ping: Unavailable")
        except Exception:
            self.ping_label.setText("Internet ping: Error")

        # Update ping stats and graph
        if ping_value is not None:
            self.ping_history.append(ping_value)
        else:
            self.ping_history.append(0)
        if self.ping_history:
            min_ping = min(self.ping_history)
            max_ping = max(self.ping_history)
            avg_ping = sum(self.ping_history) / len(self.ping_history)
            self.ping_stats_label.setText(
                f"min: {min_ping:.1f} ms | max: {max_ping:.1f} ms | avg: {avg_ping:.1f} ms"
            )
        else:
            self.ping_stats_label.setText("Ping stats: N/A")
        self.ping_graph.update()

        # DNS test
        try:
            socket.gethostbyname("google.com")
            self.dns_label.setText("DNS test: Functional")
        except Exception:
            self.dns_label.setText("DNS test: Not functional")

        # Bandwidth test (rx/tx delta, Linux/Mac only)
        bandwidth_val = None
        if platform.system().lower() != "windows":
            try:
                rx, tx = self.get_bytes_linux()
                now = time.time()
                if self.last_rx is not None and self.last_tx is not None and self.last_time is not None:
                    delta_rx = rx - self.last_rx
                    delta_tx = tx - self.last_tx
                    delta_t = now - self.last_time
                    total_kb_s = (delta_rx + delta_tx) / delta_t / 1024 if delta_t > 0 else 0
                    self.bandwidth_label.setText(f"Bandwidth: {total_kb_s:.1f} KB/s")
                    bandwidth_val = total_kb_s
                self.last_rx = rx
                self.last_tx = tx
                self.last_time = now
            except Exception:
                self.bandwidth_label.setText("Bandwidth: N/A")
        else:
            self.bandwidth_label.setText("Bandwidth: N/A (Windows)")

        # Update bandwidth stats and graph
        if bandwidth_val is not None:
            self.bandwidth_history.append(bandwidth_val)
        else:
            self.bandwidth_history.append(0)
        if self.bandwidth_history:
            min_bw = min(self.bandwidth_history)
            max_bw = max(self.bandwidth_history)
            avg_bw = sum(self.bandwidth_history) / len(self.bandwidth_history)
            self.bandwidth_stats_label.setText(
                f"min: {min_bw:.1f} | max: {max_bw:.1f} | avg: {avg_bw:.1f} KB/s"
            )
        else:
            self.bandwidth_stats_label.setText("Bandwidth stats: N/A")
        self.bandwidth_graph.update()

    def get_bytes_linux(self):
        """Get rx/tx bytes from active interface (Linux/Mac)"""
        default_iface = "eth0"
        try:
            result = subprocess.run(["ip", "route"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if line.startswith("default"):
                    default_iface = line.split()[4]
                    break
        except Exception:
            pass
        # Read /sys/class/net/<iface>/statistics/rx_bytes
        try:
            with open(f"/sys/class/net/{default_iface}/statistics/rx_bytes") as f:
                rx = int(f.read())
            with open(f"/sys/class/net/{default_iface}/statistics/tx_bytes") as f:
                tx = int(f.read())
            return rx, tx
        except Exception:
            # fallback: try all interfaces
            for iface in ["eth0", "wlan0", "en0"]:
                try:
                    with open(f"/sys/class/net/{iface}/statistics/rx_bytes") as f:
                        rx = int(f.read())
                    with open(f"/sys/class/net/{iface}/statistics/tx_bytes") as f:
                        tx = int(f.read())
                    return rx, tx
                except Exception:
                    continue
            raise RuntimeError("Could not read rx/tx bytes")

class PingGraphWidget(QWidget):
    """Professional live ping graph widget"""

    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.history = history
        self.setMinimumHeight(150)
        self.setMaximumHeight(200)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        # Gradient background
        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0.0, QColor(237, 246, 255))
        gradient.setColorAt(1.0, QColor(189, 222, 255))
        qp.fillRect(0, 0, w, h, QBrush(gradient))

        # Calculate data bounds
        count = len(self.history)
        if count < 2:
            qp.end()
            return

        max_val = max(self.history)
        min_val = min(self.history)
        if max_val == min_val:
            max_val += 1

        # Margins
        left_margin = 50
        right_margin = 20
        top_margin = 30
        bottom_margin = 40
        graph_w = w - left_margin - right_margin
        graph_h = h - top_margin - bottom_margin

        # Draw grid lines and axis labels
        qp.setPen(QPen(QColor(200, 200, 220), 1, Qt.DashLine))
        steps = 5
        for i in range(steps + 1):
            y = top_margin + graph_h - int(graph_h * i / steps)
            qp.drawLine(left_margin, y, w - right_margin, y)
            value = min_val + (max_val - min_val) * i / steps
            qp.setFont(QFont("Segoe UI", 9))
            qp.setPen(QPen(QColor(60, 60, 110), 1))
            qp.drawText(10, y + 5, f"{value:.1f}")

        # Draw X axis timeline
        qp.setPen(QPen(QColor(120, 120, 180), 2))
        qp.drawLine(left_margin, h - bottom_margin, w - right_margin, h - bottom_margin)
        qp.drawLine(left_margin, top_margin, left_margin, h - bottom_margin)

        # Time labels
        qp.setFont(QFont("Segoe UI", 9))
        qp.setPen(QPen(QColor(80, 80, 80), 1))
        qp.drawText(left_margin, h - 10, "Nejstarší")
        qp.drawText(w - right_margin - 60, h - 10, "Nejnovější")

        # Prepare data points
        points = []
        for i, val in enumerate(self.history):
            x = left_margin + int(graph_w * i / (count - 1))
            y = top_margin + graph_h - int(graph_h * (val - min_val) / (max_val - min_val))
            points.append((x, y))

        # Draw curve
        qp.setPen(QPen(QColor(30, 80, 200), 2, Qt.SolidLine))
        for i in range(len(points) - 1):
            qp.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

        # Draw points
        qp.setPen(QPen(QColor(70, 130, 180), 7, Qt.SolidLine))
        for x, y in points:
            qp.drawPoint(x, y)

        # Fill under curve
        qp.setPen(Qt.NoPen)
        qp.setBrush(QBrush(QColor(150, 200, 255, 80)))
        poly = [QPoint(x, y) for x, y in points] + [QPoint(points[-1][0], h - bottom_margin), QPoint(points[0][0], h - bottom_margin)]
        qp.drawPolygon(poly)

        # Draw current value
        qp.setFont(QFont("Segoe UI", 10, QFont.Bold))
        qp.setPen(QPen(QColor(40, 120, 200), 1))
        qp.drawText(w - right_margin - 95, top_margin + 10, f"Aktuální: {self.history[-1]:.1f} ms")
        qp.end()

class BandwidthGraphWidget(QWidget):
    """Professional live bandwidth graph widget"""

    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.history = history
        self.setMinimumHeight(150)
        self.setMaximumHeight(200)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        # Gradient background
        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0.0, QColor(220, 255, 237))
        gradient.setColorAt(1.0, QColor(190, 255, 189))
        qp.fillRect(0, 0, w, h, QBrush(gradient))

        # Calculate data bounds
        count = len(self.history)
        if count < 2:
            qp.end()
            return

        max_val = max(self.history)
        min_val = min(self.history)
        if max_val == min_val:
            max_val += 1

        # Margins
        left_margin = 50
        right_margin = 20
        top_margin = 30
        bottom_margin = 40
        graph_w = w - left_margin - right_margin
        graph_h = h - top_margin - bottom_margin

        # Draw grid lines and axis labels
        qp.setPen(QPen(QColor(200, 220, 200), 1, Qt.DashLine))
        steps = 5
        for i in range(steps + 1):
            y = top_margin + graph_h - int(graph_h * i / steps)
            qp.drawLine(left_margin, y, w - right_margin, y)
            value = min_val + (max_val - min_val) * i / steps
            qp.setFont(QFont("Segoe UI", 9))
            qp.setPen(QPen(QColor(60, 110, 60), 1))
            qp.drawText(10, y + 5, f"{value:.1f}")

        # Draw X axis timeline
        qp.setPen(QPen(QColor(120, 180, 120), 2))
        qp.drawLine(left_margin, h - bottom_margin, w - right_margin, h - bottom_margin)
        qp.drawLine(left_margin, top_margin, left_margin, h - bottom_margin)

        # Time labels
        qp.setFont(QFont("Segoe UI", 9))
        qp.setPen(QPen(QColor(80, 80, 80), 1))
        qp.drawText(left_margin, h - 10, "Nejstarší")
        qp.drawText(w - right_margin - 60, h - 10, "Nejnovější")

        # Prepare data points
        points = []
        for i, val in enumerate(self.history):
            x = left_margin + int(graph_w * i / (count - 1))
            y = top_margin + graph_h - int(graph_h * (val - min_val) / (max_val - min_val))
            points.append((x, y))

        # Draw curve
        qp.setPen(QPen(QColor(60, 150, 60), 2, Qt.SolidLine))
        for i in range(len(points) - 1):
            qp.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

        # Draw points
        qp.setPen(QPen(QColor(60, 180, 60), 7, Qt.SolidLine))
        for x, y in points:
            qp.drawPoint(x, y)

        # Fill under curve
        qp.setPen(Qt.NoPen)
        qp.setBrush(QBrush(QColor(120, 220, 120, 80)))
        poly = [QPoint(x, y) for x, y in points] + [QPoint(points[-1][0], h - bottom_margin), QPoint(points[0][0], h - bottom_margin)]
        qp.drawPolygon(poly)

        # Draw current value
        qp.setFont(QFont("Segoe UI", 10, QFont.Bold))
        qp.setPen(QPen(QColor(40, 200, 120), 1))
        qp.drawText(w - right_margin - 120, top_margin + 10, f"Aktuální: {self.history[-1]:.1f} KB/s")
        qp.end()