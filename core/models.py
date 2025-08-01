"""
Data models for the application
"""
from typing import Dict, List

class DeviceInfo:
    """Class representing a network device"""
    def __init__(self, ip: str, hostname: str, mac: str, device_type: str, scan_time: str):
        self.ip = ip
        self.hostname = hostname
        self.mac = mac
        self.device_type = device_type
        self.scan_time = scan_time

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'ip': self.ip,
            'hostname': self.hostname,
            'mac': self.mac,
            'device_type': self.device_type,
            'scan_time': self.scan_time
        }

class ScanResult:
    """Class representing scan results"""
    def __init__(self, network_range: str, scan_mode: str, devices: List[DeviceInfo]):
        self.network_range = network_range
        self.scan_mode = scan_mode
        self.devices = devices