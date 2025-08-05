#!/usr/bin/env python3
"""
Advanced IP Scanner - LAN Network Scanner Application
Modern GUI network scanner for local network analysis
"""

import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import EnhancedIPScannerApp

def main():
    """Main application function"""
    app = QApplication(sys.argv)
    
    app.setApplicationName("IP Scanner")
    app.setApplicationVersion("0.9.0")
    app.setOrganizationName("Jupik the dev")
    
    window = EnhancedIPScannerApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()