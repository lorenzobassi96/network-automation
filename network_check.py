#!/usr/bin/env python3
"""
Network Consistency Checker for Telco Lab
Continuously monitors network link consistency between devices
"""

import time
import ipaddress
from datetime import datetime
from ncclient import manager
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import sys

@dataclass
class Interface:
    """Represents a network interface"""
    name: str
    ip_address: Optional[str] = None
    prefix_length: Optional[int] = None
    enabled: bool = False
    description: str = ""
    
    @property
    def network(self) -> Optional[ipaddress.IPv4Network]:
        """Get the network this interface belongs to"""
        if self.ip_address and self.prefix_length:
            try:
                return ipaddress.IPv4Network(f"{self.ip_address}/{self.prefix_length}", strict=False)
            except:
                return None
        return None
    
    @property
    def ip_with_prefix(self) -> str:
        """Get IP address with prefix length"""
        if self.ip_address and self.prefix_length:
            return f"{self.ip_address}/{self.prefix_length}"
        return "No IP"

@dataclass
class Device:
    """Represents a network device"""
    name: str
    host: str
    port: int
    interfaces: Dict[str, Interface]
    
    def __post_init__(self):
        if not hasattr(self, 'interfaces'):
            self.interfaces = {}

@dataclass
class NetworkLink:
    """Represents a network link between two devices"""
    name: str
    device1: str
    interface1: str
    device2: str
    interface2: str
    expected_networks: List[str]
    description: str

class NetworkConsistencyChecker:
    def __init__(self):
        self.devices = {
            'RAN': Device('RAN', 'localhost', 830, {}),
            'Router': Device('Router', 'localhost', 831, {}),
            'Core': Device('Core', 'localhost', 832, {})
        }
        
        # Define expected network links. The second backhaul/transport network is the one
        # used in the "Work with candidate" exercise.
        self.network_links = [
            NetworkLink(
                name="Network A (RAN-Router Backhaul)",
                device1="RAN", interface1="backhaul0",
                device2="Router", interface2="eth1", 
                expected_networks=["10.0.1.0/30", "10.0.100.0/30"],
                description="RAN backhaul to Router"
            ),
            NetworkLink(
                name="Network B (Router-Core)",
                device1="Router", interface1="eth2",
                device2="Core", interface2="eth1",
                expected_networks=["10.0.2.0/30", "10.0.200.0/30"], 
                description="Router to Core network"
            ),
            NetworkLink(
                name="Management Network",
                device1="RAN", interface1="eth0",
                device2="Router", interface2="eth0",
                expected_networks=["192.168.1.0/24"],
                description="Management network"
            ),
            NetworkLink(
                name="Management Network (Router-Core)",
                device1="Router", interface1="eth0", 
                device2="Core", interface2="eth0",
                expected_networks=["192.168.1.0/24"],
                description="Management network"
            )
        ]
    
    def connect_device(self, device: Device) -> Optional[manager.Manager]:
        """Connect to a NETCONF device"""
        try:
            conn = manager.connect(
                host=device.host,
                port=device.port,
                username='admin',
                password='admin',
                hostkey_verify=False,
                timeout=10
            )
            return conn
        except Exception as e:
            print(f"❌ Failed to connect to {device.name}: {e}")
            return None
    
    def parse_interface_config(self, xml_data: str) -> Dict[str, Interface]:
        """Parse interface configuration from NETCONF XML"""
        interfaces = {}
        
        try:
            root = ET.fromstring(xml_data)
            
            # Find all interfaces
            for interface_elem in root.findall('.//{urn:ietf:params:xml:ns:yang:ietf-interfaces}interface'):
                name_elem = interface_elem.find('.//{urn:ietf:params:xml:ns:yang:ietf-interfaces}name')
                if name_elem is None:
                    continue
                    
                name = name_elem.text
                
                # Get description
                desc_elem = interface_elem.find('.//{urn:ietf:params:xml:ns:yang:ietf-interfaces}description')
                description = desc_elem.text if desc_elem is not None else ""
                
                # Get enabled status
                enabled_elem = interface_elem.find('.//{urn:ietf:params:xml:ns:yang:ietf-interfaces}enabled')
                enabled = enabled_elem.text.lower() == 'true' if enabled_elem is not None else False
                
                # Get IP address
                ip_elem = interface_elem.find('.//{urn:ietf:params:xml:ns:yang:ietf-ip}ip')
                prefix_elem = interface_elem.find('.//{urn:ietf:params:xml:ns:yang:ietf-ip}prefix-length')
                
                ip_address = ip_elem.text if ip_elem is not None else None
                prefix_length = int(prefix_elem.text) if prefix_elem is not None else None
                
                interfaces[name] = Interface(
                    name=name,
                    ip_address=ip_address,
                    prefix_length=prefix_length,
                    enabled=enabled,
                    description=description
                )
                
        except Exception as e:
            print(f"Error parsing XML: {e}")
            
        return interfaces
    
    def get_device_interfaces(self, device: Device) -> bool:
        """Get interface configuration from a device"""
        conn = self.connect_device(device)
        if not conn:
            return False
            
        try:
            config = conn.get_config(source='running')
            device.interfaces = self.parse_interface_config(config.data_xml)
            conn.close_session()
            return True
        except Exception as e:
            print(f"❌ Failed to get interfaces from {device.name}: {e}")
            if conn:
                conn.close_session()
            return False
    
    def check_link_consistency(self, link: NetworkLink) -> Tuple[str, str]:
        """Check if a network link is consistent"""
        device1 = self.devices.get(link.device1)
        device2 = self.devices.get(link.device2)
        
        if not device1 or not device2:
            return "❌ ERROR", "Device not found"
        
        interface1 = device1.interfaces.get(link.interface1)
        interface2 = device2.interfaces.get(link.interface2)
        
        if not interface1:
            return "❌ ERROR", f"{link.device1}:{link.interface1} not found"
        if not interface2:
            return "❌ ERROR", f"{link.device2}:{link.interface2} not found"
        
        # Check if both interfaces are enabled
        if not interface1.enabled:
            return "⚠️  WARNING", f"{link.device1}:{link.interface1} disabled"
        if not interface2.enabled:
            return "⚠️  WARNING", f"{link.device2}:{link.interface2} disabled"
        
        # Check if both have IP addresses
        if not interface1.ip_address:
            return "⚠️  WARNING", f"{link.device1}:{link.interface1} has no IP"
        if not interface2.ip_address:
            return "⚠️  WARNING", f"{link.device2}:{link.interface2} has no IP"
        
        # Check if they're in the same network
        network1 = interface1.network
        network2 = interface2.network
        expected_networks = [ipaddress.IPv4Network(n) for n in link.expected_networks]
        
        if not network1 or not network2:
            return "❌ ERROR", "Cannot determine network"
        
        if network1 != network2:
            return "❌ ERROR", f"Different networks: {network1} vs {network2}"
        
        if network1 not in expected_networks:
            expected = " or ".join(str(n) for n in expected_networks)
            return "⚠️  WARNING", f"Unexpected network: {network1} (expected {expected})"
        
        # Check IP addresses are different (not the same IP)
        if interface1.ip_address == interface2.ip_address:
            return "❌ ERROR", f"Same IP address: {interface1.ip_address}"
        
        return "✅ OK", f"{interface1.ip_with_prefix} ↔ {interface2.ip_with_prefix}"
    
    def print_status_header(self):
        """Print status header"""
        print("=" * 80)
        print(f"🔍 Network Consistency Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def print_device_status(self):
        """Print device connection status"""
        print("📡 Device Status:")
        for name, device in self.devices.items():
            status = "✅ Connected" if device.interfaces else "❌ Disconnected"
            interface_count = len(device.interfaces)
            print(f"   {name:8} ({device.host}:{device.port}): {status} - {interface_count} interfaces")
        print()
    
    def print_link_status(self):
        """Print network link status"""
        print("🔗 Network Link Status:")
        
        for link in self.network_links:
            status, details = self.check_link_consistency(link)
            print(f"   {link.name:35} {status} {details}")
        
        print()
    
    def print_interface_details(self):
        """Print detailed interface information"""
        print("📋 Interface Details:")
        
        for device_name, device in self.devices.items():
            if not device.interfaces:
                continue
                
            print(f"   📱 {device_name}:")
            for interface_name, interface in sorted(device.interfaces.items()):
                enabled_str = "🟢" if interface.enabled else "🔴"
                ip_str = interface.ip_with_prefix if interface.ip_address else "No IP"
                desc_str = f" ({interface.description})" if interface.description else ""
                print(f"      {interface_name:12} {enabled_str} {ip_str:18} {desc_str}")
        print()
    
    def run_single_check(self) -> bool:
        """Run a single consistency check"""
        self.print_status_header()
        
        # Get interface data from all devices
        all_connected = True
        for device in self.devices.values():
            if not self.get_device_interfaces(device):
                all_connected = False
        
        # Print status
        self.print_device_status()
        
        if all_connected:
            self.print_link_status()
            self.print_interface_details()
        else:
            print("⚠️  Cannot perform full consistency check - some devices disconnected")
        
        return all_connected
    
    def run_continuous_monitoring(self, interval: int = 30):
        """Run continuous network monitoring"""
        print("🚀 Starting Network Consistency Monitor")
        print(f"📊 Checking every {interval} seconds (Press Ctrl+C to stop)")
        print()
        
        try:
            while True:
                self.run_single_check()
                print(f"⏰ Next check in {interval} seconds...")
                print("─" * 80)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Error during monitoring: {e}")

def main():
    checker = NetworkConsistencyChecker()
    
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
            checker.run_continuous_monitoring(interval)
        except ValueError:
            print("Invalid interval. Using default 30 seconds.")
            checker.run_continuous_monitoring()
    else:
        # Single check mode
        checker.run_single_check()

if __name__ == "__main__":
    main()