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


# OPTIONAL: 🐳 Run with an Execution Environment (ansible-builder + ansible-navigator)

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
>
> **⚠️ Rootful (`sudo`) vs rootless:** the examples below use `sudo` to avoid
> permission issues. If you go this route you **must be consistent**: build the
> EE, start the devices, and run the playbook **all with `sudo`**. An image built
> with `sudo` lives in root's container storage (`/var/lib/containers`) and would
> **not** be found by a rootless `ansible-navigator`. Never mix rootful and
> rootless commands, or you'll hit *"image not found"* errors.

### 1. Install the tooling (once):
```bash
sudo pip3 install ansible-builder ansible-navigator
```

> **`error: externally-managed-environment` (PEP 668)?** On recent
> Debian/Ubuntu, `pip` refuses to install system-wide. Since these are CLI
> applications, install them with **pipx** instead:
> ```bash
> sudo apt install pipx
> pipx install ansible-builder
> pipx install ansible-navigator
> pipx ensurepath   # adds ~/.local/bin to PATH (open a new shell afterwards)
> ```
> Alternatively, use a virtual environment
> (`python3 -m venv venv && source venv/bin/activate && pip install ansible-builder ansible-navigator`)
> or override the check with `pip install --break-system-packages ...` (not recommended).

### 2. Start the devices (from the repository root):
```bash
sudo podman compose up -d
```

### 3. Build the execution environment (from this `ansible/` folder):
```bash
sudo ~/.local/bin/ansible-builder build -t netconf-ee -f execution-environment.yml --container-runtime podman -vvv
```
NB: WSL may crash during the build process due OOM (Out Of Memory) errors. Consider increasing the available memory for WSL.
In case you are not able to complete the build, you can skip the build and access the image at:  docker.io/lorenzobassi/network-automation:netconf-ee-1.0.0
In case the build is successful:
```bash
sudo podman images
REPOSITORY                                      TAG          IMAGE ID      CREATED        SIZE
localhost/netconf-ee                            latest       da9b18f56f99  2 minutes ago  553 MB
```

### 4. Run the playbook with ansible-navigator:
`ansible-navigator.yml` selects the `netconf-ee` image automatically, so you only
pass the playbook and its arguments. `--mode stdout` prints plain output (drop it
to use the interactive TUI).
```bash
# Show current configuration on all devices
sudo ~/.local/bin/ansible-navigator run network_automation.yml -i inventory.yml --tags show --mode stdout

# Apply the automatic IP configuration on all devices
sudo ~/.local/bin/ansible-navigator run network_automation.yml -i inventory.yml --tags auto --mode stdout

# Target a single device
sudo ~/.local/bin/ansible-navigator run network_automation.yml -i inventory.yml --tags show --limit RAN --mode stdout

# Override parameters (change a specific interface)
sudo ~/.local/bin/ansible-navigator run network_automation.yml -i inventory.yml --tags change --mode stdout \
  -e "target_device=RAN target_interface=backhaul0 target_ip=10.2.1.1 target_prefix=30"
```

### EE vs local execution: what actually changed?

Compare this run with the "local" flow from the [🚀 Usage & Examples](#-usage--examples) section
above (`ansible-playbook -i inventory.yml ...`), and try to answer these questions:

- Before running step 4, did you have to `pip install ncclient jxmlease` or run
  `ansible-galaxy collection install` on your host, like you did for the local flow? Why not?
- If a teammate with a brand-new laptop (no Python, no Ansible, no collections installed)
  received only this repo, could they run `ansible-navigator run ...` and get the exact same
  result you did? Would they be able to run `ansible-playbook` directly, without any setup?
- `requirements.txt` and `requirements.yml` still exist in this folder — are they used when you
  run through `ansible-navigator`? Where did their contents actually end up?
- What happens if your host's globally installed `ncclient` is a different (older/newer)
  version than the one the playbook was tested with? Does that risk exist when running through
  the EE?
- Two people build the same `execution-environment.yml` on two different machines (different
  OS, different Python already installed). Do you expect their `ansible-playbook` version, their
  `ansible.netcommon` version, and their `ncclient` version to match? Why?

The point: `execution-environment.yml` pins **every** dependency (ansible-core, collections,
Python libraries) into a single container image. You build it **once**, then `ansible-navigator`
runs the playbook *inside* that container — the host only needs `podman`/`docker` and
`ansible-navigator` itself, nothing NETCONF-specific. This removes the classic "works on my
machine" problem caused by missing or mismatched dependencies, at the cost of an extra build step
and a (much) heavier artifact than a handful of `pip install` commands.


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
