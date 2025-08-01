
import socket
import ipaddress
import subprocess
import re
import platform
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class NetworkScanner:
    """Network scanning with total auto-detection (IP, netmask, range)."""

    def __init__(self):
        self.active_devices = []
        self.scan_cancelled = threading.Event()
        self.lock = threading.Lock()
        self.local_ip, self.network_range = self._detect_network_range()

    def _detect_network_range(self) -> Tuple[str, str]:
        """Detect local IP and network CIDR automatically for any OS."""
        try:
            plat = platform.system().lower()
            if plat == "windows":
                local_ip, cidr = self._windows_network_cidr()
            else:
                local_ip, cidr = self._unix_network_cidr()
            return local_ip, cidr
        except Exception as e:
            print(f"Error auto-detecting network: {e}")
            # Fallback to outbound connection, /24
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
                return local_ip, f"{network.network_address}/24"
            except Exception:
                return "0.0.0.0", "0.0.0.0/24"

    def _windows_network_cidr(self) -> Tuple[str, str]:
        """Windows: parse ipconfig for IP and netmask, convert to CIDR."""
        result = subprocess.run(["ipconfig"], capture_output=True, text=True)
        ip, netmask = None, None
        for line in result.stdout.splitlines():
            match_ip = re.search(r"IPv4.*?:\s*([\d\.]+)", line)
            match_mask = re.search(r"(Subnet Mask|Maska podsítě).*?:\s*([\d\.]+)", line)
            if match_ip:
                ip = match_ip.group(1)
            if match_mask:
                netmask = match_mask.group(2)
            if ip and netmask:
                break
        if not (ip and netmask):
            raise RuntimeError("IP or netmask not found")
        prefix = sum(bin(int(x)).count('1') for x in netmask.split('.'))
        network = ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
        return ip, f"{network.network_address}/{prefix}"

    def _unix_network_cidr(self) -> Tuple[str, str]:
        """Linux/Mac: use 'ip' or 'ifconfig' for IP and netmask, convert to CIDR."""
        # Try 'ip addr'
        try:
            result = subprocess.run(["ip", "-4", "addr"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                match = re.search(r'inet ([\d\.]+)/(\d+)', line)
                if match:
                    ip = match.group(1)
                    prefix = int(match.group(2))
                    network = ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
                    return ip, f"{network.network_address}/{prefix}"
        except Exception:
            pass
        # Fallback: try 'ifconfig'
        result = subprocess.run(["ifconfig"], capture_output=True, text=True)
        ip, netmask = None, None
        for line in result.stdout.splitlines():
            match_ip = re.search(r'inet (?:addr:)?([\d\.]+)', line)
            match_mask = re.search(r'(?:Mask:|netmask )([\d\.]+)', line)
            if match_ip and not ip and not match_ip.group(1).startswith("127."):
                ip = match_ip.group(1)
            if match_mask and not netmask:
                netmask = match_mask.group(1)
            if ip and netmask:
                break
        if not (ip and netmask):
            raise RuntimeError("IP or netmask not found")
        prefix = sum(bin(int(x)).count('1') for x in netmask.split('.'))
        network = ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
        return ip, f"{network.network_address}/{prefix}"

    def ping_host(self, ip: str, timeout: int = 1) -> bool:
        """Ping test for given IP address."""
        try:
            plat = platform.system().lower()
            if plat == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
            if "ttl" in result.stdout.lower():
                return True
            return result.returncode == 0
        except Exception:
            return False

    def get_hostname(self, ip: str) -> str:
        """Get hostname for IP address, fallback to IP if not found."""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except Exception:
            return ip

    def get_mac_address(self, ip: str) -> str:
        """Get MAC address using ARP table, cross-platform and robust parsing."""
        try:
            plat = platform.system().lower()
            if plat == "windows":
                result = subprocess.run(["arp", "-a", ip], capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if ip in line:
                        mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                        if mac_match:
                            return mac_match.group(0).upper()
            else:
                result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if ip in line:
                        mac_match = re.search(r'([0-9a-f]{2}(:|-)){5}[0-9a-f]{2}', line, re.IGNORECASE)
                        if mac_match:
                            return mac_match.group(0).upper()
                        parts = line.split()
                        for part in parts:
                            if ':' in part and len(part) == 17:
                                return part.upper()
        except Exception:
            pass
        return "Unknown"

    def identify_device_type(self, hostname: str, mac: str) -> str:
        """Identify device type by hostname and MAC, with extended vendor detection."""
        hostname_lower = hostname.lower() if hostname else ""
        mac_prefix = mac.replace(":", "").replace("-", "").upper()[:6]
        mac_vendors = {
            '005056': 'VMware',
            '080027': 'VirtualBox',
            '000C29': 'VMware',
            '001B21': 'Intel',
            '00E04C': 'Realtek',
            'B827EB': 'Raspberry Pi',
            'DCA632': 'Raspberry Pi',
            '00163E': 'Xen Virtual',
            '525400': 'QEMU/KVM',
            'FCFBFB': 'Ubiquiti',
            '001A11': 'Apple',
            'F0D1A9': 'Samsung',
        }
        device_types = [
            (["router", "gateway", "fritzbox", "dlink", "asus", "tp-link"], "Router"),
            (["printer", "canon", "hp", "epson", "brother"], "Printer"),
            (["phone", "android", "iphone", "samsung", "huawei", "xiaomi"], "Mobile Device"),
            (["laptop", "notebook", "pc", "desktop", "macbook", "imac"], "Computer"),
            (["tv", "smart", "lg", "samsung-tv", "chromecast", "firetv"], "Smart TV"),
            (["raspberry", "pi"], "Raspberry Pi"),
            (["camera", "webcam", "cctv"], "Camera"),
            (["ap", "access point", "wifi"], "Wireless AP"),
        ]
        for keywords, dtype in device_types:
            if any(x in hostname_lower for x in keywords):
                return dtype
        if mac_prefix in mac_vendors:
            vendor = mac_vendors[mac_prefix]
            if "vmware" in vendor.lower() or "virtual" in vendor.lower():
                return "Virtual Machine"
            return vendor
        if mac_prefix in ['B827EB', 'DCA632'] or "raspberry" in hostname_lower:
            return "Raspberry Pi"
        return "Unknown Device"

    def scan_network_parallel(
        self,
        network_range: Optional[str] = None,
        max_workers: int = 100,
        progress_callback=None,
        result_callback=None
    ) -> List[Dict]:
        """
        Parallel network scanning with auto-detected network range.
        If network_range is None, uses the automatically detected range.
        """
        self.active_devices = []
        self.scan_cancelled.clear()
        network_range = network_range or self.network_range

        try:
            network = ipaddress.IPv4Network(network_range, strict=False)
            ip_list = [str(ip) for ip in network.hosts()]
            total_ips = len(ip_list)
            completed = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_ip = {
                    executor.submit(self._scan_single_ip, ip): ip for ip in ip_list
                }
                for future in as_completed(future_to_ip):
                    if self.scan_cancelled.is_set():
                        break
                    ip = future_to_ip[future]
                    completed += 1
                    try:
                        device_info = future.result()
                        if device_info:
                            with self.lock:
                                self.active_devices.append(device_info)
                            if result_callback:
                                result_callback(device_info)
                    except Exception as e:
                        print(f"Error scanning {ip}: {e}")
                    if progress_callback:
                        progress_callback(completed, total_ips)
            return self.active_devices
        except Exception as e:
            print(f"Network scanning error: {e}")
            return []

    def _scan_single_ip(self, ip: str) -> Optional[Dict]:
        """Scan single IP address with all details."""
        if self.scan_cancelled.is_set():
            return None
        if self.ping_host(ip):
            hostname = self.get_hostname(ip)
            mac = self.get_mac_address(ip)
            device_type = self.identify_device_type(hostname, mac)
            return {
                'ip': ip,
                'hostname': hostname,
                'mac': mac,
                'device_type': device_type,
                'scan_time': datetime.now().strftime("%H:%M:%S"),
            }
        return None

    def cancel_scan(self):
        """Cancel ongoing scan in a thread-safe way."""

        self.scan_cancelled.set()
