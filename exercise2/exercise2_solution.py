"""
Exercise 2 Solution Script
- Connects to devices using ncclient
- Uses edit-config to set eth0 IPv4 address and netmask
- Uses get-config to verify configuration
- Reference: See 'Reference Commands' section in the project README for equivalent netconf-console2 usage.
"""

from ncclient import manager  # NETCONF client library: opens sessions and sends RPCs
from lxml import etree        # XML library: used here to pretty-print XML replies

# Example XML payload for eth0 IPv4 address (used in edit-config)
# {ip} and {netmask} are placeholders filled in later with str.format()
# <config>: mandatory wrapper of every edit-config payload
# <interfaces>: ietf-interfaces YANG module; <name> is the list key (selects eth0)
# <ipv4>: ietf-ip YANG module; nc:operation="replace" deletes the old ipv4 content
#         and writes the new one (the default, merge, would add to the old address)
EDIT_CONFIG_TEMPLATE = '''
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
            <name>eth0</name>
            <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip"
                  xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
                  nc:operation="replace">
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
# Each device is a dictionary: key -> value
devices = [
    {"host": "127.0.0.1", "port": 830, "username": "admin", "password": "admin", "eth0": {"ip": "192.168.1.51", "prefix-length": "24"}},
    {"host": "127.0.0.1", "port": 831, "username": "admin", "password": "admin", "eth0": {"ip": "192.168.1.21", "prefix-length": "24"}},
    {"host": "127.0.0.1", "port": 832, "username": "admin", "password": "admin", "eth0": {"ip": "192.168.1.31", "prefix-length": "24"}}
    # Add more devices as needed
]

def connect_device(device):
    """Connect to a device using ncclient manager."""
    try:
        # Open the NETCONF session (over SSH); returns a session object
        m = manager.connect(
            host=device["host"],
            port=device.get("port", 830),  # 830 if the key "port" is missing
            username=device["username"],
            password=device["password"],
            hostkey_verify=False,  # do not check the SSH host key (ok for the lab)
            allow_agent=False,     # do not use an SSH agent
            look_for_keys=False,   # do not look for SSH key files: use user/password only
            timeout=10             # seconds to wait before giving up
        )
        print(f"Connected to {device['host']}:{device['port']}")
        return m
    except Exception as e:
        # Any error (device down, wrong port, bad credentials) ends up here
        print(f"Failed to connect to {device['host']}: {e}")
        return None  # the caller checks this value

def edit_config_eth0(m, eth0):
    """
    Edit eth0 IPv4 address and netmask using edit-config.
    Reference command:
      netconf-console2 --host <host> --port <port> --edit-config <xml-file> --db running
    """
    # Read the values from the dictionary and put them in the XML placeholders
    config_xml = EDIT_CONFIG_TEMPLATE.format(ip=eth0.get('ip'), netmask=eth0.get('prefix-length'))
    try:
        # Send <edit-config> to the running datastore: the change is immediate
        response = m.edit_config(target='running', config=config_xml)
        print("edit-config response:", response)  # <ok/> means success
    except Exception as e:
        print(f"edit-config failed: {e}")

def get_config_eth0(m):
    # Subtree filter: ask only for the eth0 interface instead of the whole config
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
        # Send <get-config> on the running datastore, applying the filter
        response = m.get_config(source='running', filter=filter_xml)
        print("get-config response:")
        # data_ele is the <data> XML element; tostring() turns it into indented text
        print(etree.tostring(response.data_ele, pretty_print=True).decode())
    except Exception as e:
        print(f"get-config failed: {e}")

def main():
    # Repeat the same steps for every device in the list
    for device in devices:
        m = connect_device(device)
        if m:  # None means the connection failed: skip this device
            eth0 = device.get("eth0", {})  # {} if the key is missing
            edit_config_eth0(m, eth0)      # write the new address
            get_config_eth0(m)             # read it back to verify
            m.close_session()              # close the NETCONF session

# Run main() only when the file is executed directly (not when imported)
if __name__ == "__main__":
    main()
