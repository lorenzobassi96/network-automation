"""
Exercise 2 Solution Script
- Connects to devices using ncclient
- Uses edit-config to set eth0 IPv4 address and netmask
- Uses get-config to verify configuration
- Reference: See 'Reference Commands' section in the project README for equivalent netconf-console2 usage.
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

# List of device connection details and eth0 config
devices = [
    {"host": "127.0.0.1", "port": 830, "username": "admin", "password": "admin", "eth0": {"ip": "192.168.1.51", "prefix-length": "24"}},
    {"host": "127.0.0.1", "port": 831, "username": "admin", "password": "admin", "eth0": {"ip": "192.168.1.21", "prefix-length": "24"}},
    {"host": "127.0.0.1", "port": 832, "username": "admin", "password": "admin", "eth0": {"ip": "192.168.1.31", "prefix-length": "24"}}
    # Add more devices as needed
]

def connect_device(device):
    """Connect to a device using ncclient manager."""
    try:
        m = manager.connect(
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

def edit_config_eth0(m, eth0):
    """
    Edit eth0 IPv4 address and netmask using edit-config.
    Reference command:
      netconf-console2 --host <host> --port <port> --edit-config <xml-file> --db running
    """
    config_xml = EDIT_CONFIG_TEMPLATE.format(ip=eth0.get('ip'), netmask=eth0.get('prefix-length'))
    try:
        response = m.edit_config(target='running', config=config_xml, operation='replace')
        print("edit-config response:", response)
    except Exception as e:
        print(f"edit-config failed: {e}")

def get_config_eth0(m):
    filter_xml = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
            <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                <interface>
                    <name>eth0</name>
                </interface>
            </interfaces>
        </filter>
    '''
    try:
        response = m.get_config(source='running', filter=filter_xml)
        print("get-config response:")
        print(etree.tostring(response.data_ele, pretty_print=True).decode())
    except Exception as e:
        print(f"get-config failed: {e}")

def main():
    for device in devices:
        m = connect_device(device)
        if m:
            eth0 = device.get("eth0", {})
            edit_config_eth0(m, eth0)
            get_config_eth0(m)
            m.close_session()

if __name__ == "__main__":
    main()
