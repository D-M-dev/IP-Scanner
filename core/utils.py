"""
Utility functions for the application
"""
import csv
import json
from datetime import datetime
from typing import List, Dict

def export_to_csv(file_path: str, devices: List[Dict]):
    """Export to CSV"""
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ip', 'hostname', 'mac', 'device_type', 'scan_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for device in devices:
            writer.writerow(device)

def export_to_json(file_path: str, network_range: str, scan_mode: str, devices: List[Dict]):
    """Export to JSON"""
    export_data = {
        'scan_info': {
            'timestamp': datetime.now().isoformat(),
            'network_range': network_range,
            'total_devices': len(devices),
            'scan_mode': scan_mode
        },
        'devices': devices
    }
    
    with open(file_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)