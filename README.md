# IP Scanner

Advanced desktop application for scanning and analyzing local networks.

## Features

- Automatic detection of local IP address and network range (CIDR)
- Parallel network scanning with configurable thread count
- Detection of IP, hostname, MAC address, and device type
- Real-time monitoring with progress bar and loading animation
- Export scan results to CSV or JSON with metadata
- Network monitoring with live statistics and history graphs
- Advanced scan and export settings
- Modern GUI built with PySide6
- Cross-platform: Windows, Linux, macOS

## Project Structure
core/ models.py scanner.py utils.py 
gui/ main_window.py styles.py 
widgets/ advanced_settings.py animated_button.py loading_widget.py network_monitor.py

## Main Components

- **core/scanner.py**: Implements automatic network detection and parallel scanning. See `NetworkScanner`.
- **core/models.py**: Data models for devices and scan results. See `DeviceInfo`, `ScanResult`.
- **core/utils.py**: Utility functions for exporting scan results. See `export_to_csv`, `export_to_json`.
- **gui/main_window.py**: Main application window and logic. See `EnhancedIPScannerApp`.
- **gui/widgets/**: Custom widgets for advanced settings, animated buttons, loading animation, and network monitoring.

## Usage

1. Install Python 3.8+ and PySide6.
2. Run the application:

    ```sh
    python main.py
    ```

3. The application will auto-detect your network and display the main window.
4. Start scanning to discover devices on your local network.
5. Export results as CSV or JSON.

## Requirements

- Python 3.8+
- PySide6
- mayi forgot for smt just install...

## Package Info

```python
# [__init__.py](http://_vscodecontentref_/2)
__version__ = "0.9.0"
__author__ = "Jupik-the-dev"

