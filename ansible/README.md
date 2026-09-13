# Network Automation - Ansible Playbook

This directory contains an Ansible playbook that configures 3 network devices with NETCONF.

## 📁 Files

- `inventory.yml` - Inventory file defining the NETCONF devices
- `network_automation.yml` - Main playbook with all operations
- `README.md` - This file
- `ansible.cfg` - Ansible configuration (optional)
- `execution-environment.yml` - Execution Environment definition for `ansible-builder`
- `ansible-navigator.yml` - `ansible-navigator` config (EE image, podman, host network)
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
```bash
pip install ansible ansible-netcommon
ansible-galaxy collection install ansible.netcommon

# Python libraries used by the NETCONF modules:
#   ncclient  -> NETCONF transport
#   jxmlease  -> required by `display: json` to parse device output into a dict
pip install ncclient jxmlease
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

## 🐳 Run with an Execution Environment (ansible-builder + ansible-navigator)

Instead of installing Ansible and its dependencies locally, the playbook can run
inside a self-contained **Execution Environment (EE)**. The EE is defined by
`execution-environment.yml`, built with **ansible-builder**, and run with
**ansible-navigator** (configured in `ansible-navigator.yml`).

The EE bundles everything: ansible-core, the `ansible.netcommon` / `ansible.posix`
collections, and the Python NETCONF libraries (`ncclient`, `jxmlease`, ...).

> The NETCONF devices are started by the root `docker-compose.yml` and expose
> ports `830/831/832` on the host. `ansible-navigator.yml` already runs the EE
> with `--net=host` so the inventory targets (`localhost:830-832`) are reachable.
>
> These examples use **podman** (set in `ansible-navigator.yml`).

### 1. Install the tooling (once):
```bash
pip install ansible-builder ansible-navigator
```

### 2. Start the devices (from the repository root):
```bash
podman compose up -d
```

### 3. Build the execution environment (from this `ansible/` folder):
```bash
ansible-builder build -t netconf-ee -f execution-environment.yml --container-runtime podman
```

### 4. Run the playbook with ansible-navigator:
`ansible-navigator.yml` selects the `netconf-ee` image automatically, so you only
pass the playbook and its arguments. `--mode stdout` prints plain output (drop it
to use the interactive TUI).
```bash
# Show current configuration on all devices
ansible-navigator run network_automation.yml -i inventory.yml --tags show --mode stdout

# Apply the automatic IP configuration on all devices
ansible-navigator run network_automation.yml -i inventory.yml --tags auto --mode stdout

# Target a single device
ansible-navigator run network_automation.yml -i inventory.yml --tags show --limit RAN --mode stdout

# Override parameters (change a specific interface)
ansible-navigator run network_automation.yml -i inventory.yml --tags change --mode stdout \
  -e "target_device=RAN target_interface=backhaul0 target_ip=10.2.1.1 target_prefix=30"
```

> **Docker Desktop (macOS/Windows):** `--net=host` is not supported. Set
> `container-engine: docker` in `ansible-navigator.yml`, remove the `--net=host`
> container option, attach the EE to the compose network instead
> (`--net=telco-net`), and target the device container names.

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
