"""
Assignment - Automate NETCONF configuration with ncclient (candidate + commit)

Workflow implemented (see the "Assignment" section of the project README):
  1. Connect to each device (RAN, Router, Core).
  2. edit-config towards the *candidate* datastore -> eth0 IPv4 in 192.168.1.0/24.
  3. edit-config towards the *candidate* datastore -> backhaul interfaces:
       - RAN:    backhaul0                  (BBU-Router network 10.0.1.0/30)
       - Router: eth1 (to RAN) + eth2 (Core) (10.0.1.0/30 and 10.0.2.0/30)
       - Core:   eth1                       (Router-Core network 10.0.2.0/30)
  4. get-config towards the *candidate* datastore to verify the changes.
  5. If everything is as expected -> commit (candidate -> running) and re-read running.

Reference: equivalent netconf-console2 commands are listed in the README
"Reference Commands" section.
"""

from ncclient import manager
from lxml import etree


# --------------------------------------------------------------------------- #
# Device inventory
# --------------------------------------------------------------------------- #
# Each device carries the list of interfaces to (re)configure. Addresses follow
# the topology validated by network_check.py:
#   - Management (eth0):            192.168.1.0/24
#   - BBU-Router backhaul:          10.0.1.0/30  (RAN backhaul0 <-> Router eth1)
#   - Router-Core network:          10.0.2.0/30  (Router eth2  <-> Core   eth1)
DEVICES = [
    {
        "name": "RAN",
        "host": "127.0.0.1",
        "port": 830,
        "username": "admin",
        "password": "admin",
        "interfaces": [
            {"name": "eth0", "ip": "192.168.1.10", "prefix": "24"},
            {"name": "backhaul0", "ip": "10.0.1.1", "prefix": "30"},
        ],
    },
    {
        "name": "Router",
        "host": "127.0.0.1",
        "port": 831,
        "username": "admin",
        "password": "admin",
        "interfaces": [
            {"name": "eth0", "ip": "192.168.1.20", "prefix": "24"},
            {"name": "eth1", "ip": "10.0.1.2", "prefix": "30"},
            {"name": "eth2", "ip": "10.0.2.1", "prefix": "30"},
        ],
    },
    {
        "name": "Core",
        "host": "127.0.0.1",
        "port": 832,
        "username": "admin",
        "password": "admin",
        "interfaces": [
            {"name": "eth0", "ip": "192.168.1.30", "prefix": "24"},
            {"name": "eth1", "ip": "10.0.2.2", "prefix": "30"},
        ],
    },
]


# --------------------------------------------------------------------------- #
# XML templates
# --------------------------------------------------------------------------- #
# One <interface> block. nc:operation="replace" makes the edit idempotent: it
# overwrites the ipv4 container instead of merging/failing on existing data.
INTERFACE_TEMPLATE = """
    <interface>
        <name>{name}</name>
        <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip"
              xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
              nc:operation="replace">
            <enabled>true</enabled>
            <address>
                <ip>{ip}</ip>
                <prefix-length>{prefix}</prefix-length>
            </address>
        </ipv4>
    </interface>"""

CONFIG_TEMPLATE = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">{interfaces}
    </interfaces>
</config>"""

# Filter used by get-config to fetch only the interface list.
INTERFACES_FILTER = """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"/>
</filter>"""


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def connect_device(device):
    """Open a NETCONF session to a single device and return the manager."""
    conn = manager.connect(
        host=device["host"],
        port=device["port"],
        username=device["username"],
        password=device["password"],
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        timeout=10,
    )
    print(f"[{device['name']}] connected to {device['host']}:{device['port']}")
    return conn


def build_config(device):
    """Assemble the <config> payload for every interface of a device."""
    blocks = "".join(
        INTERFACE_TEMPLATE.format(name=i["name"], ip=i["ip"], prefix=i["prefix"])
        for i in device["interfaces"]
    )
    return CONFIG_TEMPLATE.format(interfaces=blocks)


def edit_candidate(conn, device):
    """Push the interface configuration to the *candidate* datastore."""
    config_xml = build_config(device)
    conn.edit_config(target="candidate", config=config_xml)
    names = ", ".join(i["name"] for i in device["interfaces"])
    print(f"[{device['name']}] edit-config -> candidate OK ({names})")


def get_config(conn, device, source):
    """Read back the interface configuration from the given datastore."""
    reply = conn.get_config(source=source, filter=INTERFACES_FILTER)
    xml = etree.tostring(reply.data_ele, pretty_print=True).decode()
    print(f"[{device['name']}] get-config <{source}>:\n{xml}")


def commit(conn, device):
    """Commit the candidate datastore into running."""
    conn.commit()
    print(f"[{device['name']}] commit OK (candidate -> running)")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    for device in DEVICES:
        conn = connect_device(device)
        try:
            # Step 2 + 3: stage eth0 and backhaul interfaces into candidate.
            edit_candidate(conn, device)

            # Step 4: verify the candidate before committing.
            get_config(conn, device, source="candidate")

            # Step 5: commit and re-read running to confirm it took effect.
            commit(conn, device)
            get_config(conn, device, source="running")
        finally:
            conn.close_session()
        print("-" * 72)


if __name__ == "__main__":
    main()
