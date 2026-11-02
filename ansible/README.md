# Network Automation - Ansible Playbook

This directory contains an Ansible playbook that configures 3 network devices with NETCONF.

## 📁 Files

- `inventory.yml` - Inventory file defining the NETCONF devices
- `network_automation.yml` - Main playbook with all operations
- `README.md` - This file
- `ansible.cfg` - Ansible configuration (optional)
- `requirements.txt` - Python dependencies (ncclient, jxmlease, lxml, paramiko)
- `requirements.yml` - Ansible collection dependencies (ansible.netcommon, ansible.posix)

## 🔑 Key Differences between Python and Ansible

### 1. **Connection Management**
- **Python**: Manual connection handling with try/except blocks
- **Ansible**: Automatic connection management via `ansible_connection: netconf`

### 2. **Configuration Storage**
- **Python**: Hardcoded in class dictionaries
- **Ansible**: Stored in inventory and playbook variables

### 3. **Error Handling**
- **Python**: Explicit try/except blocks with custom error messages
- **Ansible**: Built-in error handling with `ignore_errors` and `failed_when`

### 4. **Execution Model**
- **Python**: Procedural, executes device-by-device in sequence
- **Ansible**: Declarative, can execute in parallel across devices

### 5. **XML Generation**
- **Python**: f-strings to build XML
- **Ansible**: Jinja2 templates in playbook content

## 📦 Prerequisites

### For Python Script:
```bash
pip install ncclient
```

### For Ansible Playbook:
Install everything **before** running the playbook. Run these commands from the `ansible/` directory (the one containing `ansible.cfg`, `requirements.txt` and `requirements.yml`):
```bash
cd ansible

# 1. Ansible itself
pip install ansible

# 2. Python libraries used by the NETCONF modules
#    ncclient  -> NETCONF transport
#    jxmlease  -> required by `display: json` to parse device output into a dict
#    lxml, paramiko -> XML handling and SSH
pip install -r requirements.txt

# 3. Ansible collections (ansible.netcommon provides netconf_get / netconf_config)
ansible-galaxy collection install -r requirements.yml
```

Check that the tools are available:
```bash
ansible --version
python3 -c "import ncclient, jxmlease, lxml, paramiko; print('Python libraries OK')"
ansible-galaxy collection list | grep -E "ansible.netcommon|ansible.posix"
```

> If you use a virtual environment (for example `.venv` in the repository root), activate it first
> (`source ../.venv/bin/activate`) so that `ansible-playbook` and the libraries use the same Python.

> Always run `ansible-playbook` from the `ansible/` directory: `ansible.cfg` is read only from the
> current directory. Otherwise the NETCONF connection fails with `Unknown host key`.

## 🎯 Educational Highlights

### 1. **Idempotency**
Ansible playbooks are idempotent by default - running the same playbook multiple times produces the same result without side effects. The Python script doesn't guarantee this.

### 2. **Inventory as Source of Truth**
Ansible uses inventory files as the single source of truth for device information, making it easier to manage at scale.

### 3. **Tagging System**
Ansible's tagging system (`--tags`) allows selective execution of tasks, similar to the Python script's command-line arguments but more flexible.

### 4. **Built-in NETCONF Support**
Ansible has native NETCONF modules (`ansible.netcommon.netconf_config`, `netconf_get`) that handle connection management and XML formatting.

### 5. **Declarative vs Imperative**
- **Python (Imperative)**: "Connect to device, then change this IP, then close connection"
- **Ansible (Declarative)**: "Ensure this interface has this IP address"

## 🚀 Usage & Examples

### Run on ALL devices (RAN, Router, Core):
The play targets `hosts: devices`, so a single command runs on all three devices in the group.
```bash
# Apply the pre-defined IP configuration to every device
ansible-playbook -i inventory.yml network_automation.yml --tags=auto

# Show the current configuration of every device
ansible-playbook -i inventory.yml network_automation.yml --tags=show
```

### List which hosts would run (without changing anything):
Useful to confirm the playbook targets all three devices before executing.
```bash
ansible-playbook -i inventory.yml network_automation.yml --tags=auto --list-hosts
```
Example output:
```text
playbook: network_automation.yml

  play #1 (devices): Network Automation TAGS: []
    pattern: ['devices']
    hosts (3):
      Router
      Core
      RAN

  play #2 (devices): 📊 Configuration Summary   TAGS: [never,auto]
    pattern: ['devices']
    hosts (3):
      Router
      Core
      RAN
```

### Target a single device:
Use `--limit` to restrict execution to one host.
```bash
# Only RAN
ansible-playbook -i inventory.yml network_automation.yml --tags=auto --limit RAN

# Only Core
ansible-playbook -i inventory.yml network_automation.yml --tags=show --limit Core
```

### Target a subset of devices:
```bash
ansible-playbook -i inventory.yml network_automation.yml --tags=auto --limit "RAN,Router"
```

### Override parameters (change a specific interface):
The `change` tag takes parameters via `-e` (extra vars) to configure a single interface on a single device.
```bash
ansible-playbook -i inventory.yml network_automation.yml --tags=change \
  -e "target_device=RAN target_interface=backhaul0 target_ip=10.2.1.1 target_prefix=30"
```
- `target_device`   → host to configure (must match an inventory hostname)
- `target_interface`→ interface name to change
- `target_ip`       → new IPv4 address
- `target_prefix`   → prefix length (optional, defaults to 30)

### Dry run (check mode):
Simulates changes without applying them.
```bash
ansible-playbook -i inventory.yml network_automation.yml --tags=auto --check
```

### Verbose output:
Add `-v`, `-vv`, or `-vvv` for increasing levels of detail (NETCONF debugging).
```bash
ansible-playbook -i inventory.yml network_automation.yml --tags=show -vvv
```


## 🔍 What's the Same?

1. Both use NETCONF protocol for device management
2. Same XML structure for configuration changes
3. Same IP address assignments and network topology
4. Same interface names and device organization
5. Similar error reporting and status messages

## 📝 Notes

- The `never` tag ensures tasks only run when explicitly called with `--tags`
- `gather_facts: false` speeds up execution by skipping fact collection
- The playbook uses the same YANG models as the Python script (ietf-interfaces, ietf-ip)
- Connection parameters (credentials, ports) are centralized in inventory

## 🎓 Learning Outcomes

By comparing these two implementations, you'll understand:
- How automation tools abstract low-level connection handling
- The benefits of declarative configuration management
- How inventory systems scale better than hardcoded device lists
- The trade-offs between flexibility (Python) and standardization (Ansible)
- When to use scripting vs configuration management tools
