"""
Exercise 2 Baseline Script
- Connects to devices using ncclient
- Stubs for edit-config and get-config operations
- To be completed by attendees
"""

from ncclient import manager
from lxml import etree

# Example XML payload for eth0 IPv4 address (used in edit-config)
EDIT_CONFIG_TEMPLATE = '''
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
            <name>eth0</name>
            <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
                <address>
                    <ip>{ip}</ip>
                    <prefix-length>{netmask}</prefix-length>
                </address>
            </ipv4>
        </interface>
    </interfaces>
</config>
'''

# List of device connection details (to be filled by attendees)
devices = [
    # Example:
    # {"host": "127.0.0.1", "port": 830, "username": "admin", "password": "admin", "eth0": {"ip": "192.168.1.51", "prefix-length": "24"}},
    # ...
]

def connect_device(device):
    """Connect to a device using ncclient manager."""
    try:
        with manager.connect(
            host=device["host"],
            port=device.get("port", 830),
            username=device["username"],
            password=device["password"],
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            timeout=10
        ) 
        print(f"Connected to {device['host']}:{device['port']}")
        return m
    except Exception as e:
        print(f"Failed to connect to {device['host']}: {e}")
        return None

def edit_config_stub(m, eth0):
    """
    Stub for edit-config operation. To be implemented.
    eth0 is a dict with 'ip' and 'netmask'.
    Use config_xml = EDIT_CONFIG_TEMPLATE.format(ip=eth0.get('ip'), netmask=eth0.get('prefix-length')) to generate the XML payload.
    """
    pass

def get_config_stub(m):
    """Stub for get-config operation. To be implemented."""
    pass

def main():
    for device in devices:
        m = connect_device(device)
        if m:
            # TODO: Implement edit-config and get-config logic
            eth0 = device.get("eth0", {})
            edit_config_stub(m, eth0)
            get_config_stub(m)
            m.close_session()

if __name__ == "__main__":
    main()
