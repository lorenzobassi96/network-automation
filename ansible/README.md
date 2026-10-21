# Network Automation - Ansible Playbook

This directory contains an Ansible playbook that configures 3 network devices with NETCONF.

## 📁 Files

- `inventory.yml` - Inventory file defining the NETCONF devices
- `network_automation.yml` - Main playbook with all operations
- `README.md` - This file
- `ansible.cfg` - Ansible configuration (optional)

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
```bash
pip install ansible ansible-netcommon
ansible-galaxy collection install ansible.netcommon
```

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

## 🚀 Advanced Usage

### Run on subset of devices:
```bash
ansible-playbook -i inventory.yml network_automation.yml --tags=auto --limit=RAN,Router
```

### Dry run (check mode):
```bash
ansible-playbook -i inventory.yml network_automation.yml --tags=auto --check
```

### Verbose output:
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
