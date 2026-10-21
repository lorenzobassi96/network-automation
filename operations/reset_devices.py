#!/usr/bin/env python3
"""
Reset all lab devices to clean state
"""

NETWORK_CONFIG = {
    'RAN': {
        'eth0', 
        'backhaul0'
    },
    'Router': {
        'eth0',
        'eth1',
        'eth2'
    },
    'Core': {
        'eth0',
        'eth1'
    }
}

from ncclient import manager

def reset_device(host, port, device_name):
    """Reset a device to clean state"""
        
    # Connect to device
    conn = manager.connect(
        username='admin',
        password='admin',
        hostkey_verify=False,
        timeout=10,
        device_params={'name': 'default'}
    )
        
    # Configure each interface
    for iface in NETWORK_CONFIG[device_name]:
        
        cleanup_config = f'''
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>{iface}</name>
      <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace">
      </ipv4>
    </interface>
  </interfaces>
</config>'''
    
        try:
            with manager.connect(
                host=host,
                port=port,
                username='admin',
                password='admin',
                hostkey_verify=False
            ) as m:
                print(f"Resetting {device_name}, {iface}...")
            
                # Remove all interfaces
                result = m.edit_config(target='running', config=cleanup_config)
            
        except Exception as e:
            print(f"❌ Failed to reset {device_name}: {e}")
            return False
    
    print(f"✅ {device_name} reset successfully")
    return True

def main():
    devices = [
        ('localhost', 830, 'RAN'),
        ('localhost', 831, 'Router'), 
        ('localhost', 832, 'Core')
    ]
    
    print("🧹 Resetting all lab devices...")
    print("=" * 40)
    
    success_count = 0
    for host, port, name in devices:
        if reset_device(host, port, name):
            success_count += 1
    
    print("=" * 40)
    print(f"✅ {success_count}/{len(devices)} devices reset successfully")
    
    if success_count == len(devices):
        print("All devices are now clean!")
    
    print("\nTo fully restore original configurations:")
    print("docker-compose restart")

if __name__ == '__main__':
    main()