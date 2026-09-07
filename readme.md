# NETCONF & Network Automation

# Table of Contents
- [Architecture](#architecture)
- [Setup](#setup)
- [Exercise 1](#exercise-1)
- [Exercise 2 - Automate with Python](#exercise-2---automate-with-python)
- [Exercise 3 - Automate with Ansible](#exercise-3---automate-with-ansible)
- [Assignment](#assignment)
- [Troubleshooting](#troubleshooting)
- [Reference Commands](#reference-commands)


## Architecture 

![Architecture](arch.png)


## Setup


### WSL Setup on Windows (PowerShell)

Run the following commands from **PowerShell** on Windows.

1. List available Linux distributions:

```powershell
wsl --list --online
```

Example output:

```text
The following is a list of valid distributions that can be installed.
Install using 'wsl.exe --install <Distro>'.

NAME                            FRIENDLY NAME
Ubuntu                          Ubuntu
Debian                          Debian GNU/Linux
FedoraLinux-44                  Fedora Linux 44
...
```

2. Install WSL and Debian:

```powershell
wsl --install -d Debian
```

If WSL is already installed, ensure WSL2 is the default:

```powershell
wsl --set-default-version 2
```

3. Update the WSL kernel (recommended):

```powershell
wsl --update
```

4. Verify installation status:

```powershell
wsl --status
wsl -l -v
```

Example output:

```text
Default Distribution: Debian
Default Version: 2

NAME      STATE    VERSION
* Debian  Stopped  2
```

5. Start Debian:

```powershell
wsl -d Debian
```

At first startup, Debian will ask you to create a Linux username and password.

Quick checks inside Debian:
Suggestion: install [Windows Terminal](https://aka.ms/terminal) for a better WSL experience.

```bash
cat /etc/os-release
python3 --version
```

6. Stop WSL when needed:

```powershell
wsl --shutdown
```

7. Check whether Debian is stopped or running:

```powershell
wsl -l -v
```

Example output when running:

```text
NAME      STATE    VERSION
* Debian  Running  2
```


### 1. Prerequisites

You need the following tools installed on your system (any Linux distribution, including WSL, macOS, or native):

- **Podman**
- **Podman Compose** (`podman-compose`; some Podman versions also support the built-in `podman compose` subcommand, but not all — if `podman compose` gives `unrecognized command`, just use `podman-compose` instead)
- **Python 3** and **pip3**
- **Ansible**
- **Python packages:** `ncclient`, `netconf-console2`, `paramiko`


**For WSL users:**
This lab runs with **Podman in rootful mode** (all `podman` commands are executed with `sudo`).
Rootful mode avoids the rootless low-port (830/831/832) binding limitations.

Install Podman directly inside your WSL distribution using its package manager:

```bash
# Debian / Ubuntu
sudo apt update
sudo apt install -y podman podman-compose python3-pip git vim tmux
```

Notes:
- Podman is daemonless, so there is no service to start.
- `podman-compose` provides `docker-compose`-like behavior; alternatively the native `podman compose` command can be used if the compose provider is available on your system (requires a recent Podman with the compose plugin installed). If you get `Error: unrecognized command "podman compose"`, your Podman install doesn't have it — just use `podman-compose` instead.

### 2. Install Required Tools

Install the above tools using your distribution's package manager or download from the official websites:

- [Podman installation guide](https://podman.io/docs/installation)
- [podman-compose installation](https://github.com/containers/podman-compose)
- [Python downloads](https://www.python.org/downloads/)
- [Ansible installation guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)

**Install Python dependencies:**

On Debian/Ubuntu, `pip3 install --user` may fail with `externally-managed-environment` (PEP 668).
To install system-wide anyway (skip the virtual environment), pass `--break-system-packages`:

```bash
pip3 install --user --break-system-packages ncclient netconf-console2 paramiko ansible six
```

`--user` installs executables (like `ansible`, `netconf-console2`) into `~/.local/bin`, which may not be in your `PATH` yet. If running `ansible` (or similar) gives `command not found`, add it to your `PATH`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```


### 3. Rootful Podman

This lab uses **rootful Podman**, so container commands are prefixed with `sudo`.
No user/group setup is required (unlike Docker's `docker` group).

### 4. Verify Installations

```bash
sudo podman --version
podman-compose --version   # or, if available: sudo podman compose version
python3 --version
pip3 --version
ansible --version
netconf-console2 --help  # should print help if installed
```

### 5. Start the Lab Environment
################################################### To Be changed later when repo is ready
Download the repo:
```bash
git clone https://github.com/unusualfor/network-automation.git
cd network-automation/
```

Start the lab with Podman (rootful) using one of the following:

```bash
# Using podman-compose (works on all Podman installs)
sudo podman-compose up

# Or, if your Podman install has the compose plugin, the native subcommand also works
sudo podman compose up
```

## Exercise 1

### Check initial configuration

Once everything is up and running, check the current configuration for the *running*, *startup* and *candidate* datastores using [*netconf-console2*](https://pypi.org/project/netconf-console2/) with *--get-config*.

1. Are there differences between the datastores? Why?

### Modify running datastore

Copy and modify the file in *operations/change-eth0.xml* and use it to perform the following changes:

1. For each device, update eth0 IPv4 address values to be consistently in 192.168.1.0/24. Use *netconf-console2* to perform *edit-config* towards the *running* datastore.
2. Update the BBU-Router network to be in 10.0.1.0/30. Use *netconf-console2* to perform *edit-config* towards the *running* datastore. Make sure to configure the right interfaces of the devices.
3. Update the Router-Core network to be in 10.0.2.0/30. Use *netconf-console2* to perform *edit-config* towards the *running* datastore. Make sure to configure the right interfaces of the devices.

Activities:
* Check with *netconf-console2* with *--get-config*, towards *running*, *startup* and *candidate*
    * Would the current configuration allow the system to work properly?
    * Are there differences between the datastores? Why? 
    * What would happen if a device gets restarted in such a case?
    * What would happen to the network if the configuration applied to BBU backhaul0 was not matching the network configuration applied to Router eth1? Was there any check available to prevent this?
* Further checks: check that the three devices have consistent IP addresses with the *network-check.py* script and, in case not, modify IP addresses again

### Work with candidate

Copy and modify the file in *operations/change-eth0.xml* and use it to perform the following changes:

1. For each device, update eth0 IPv4 address values to be consistently in 192.168.1.0/24 (use different addresses with respect to the previous exercise). Use *netconf-console2* to perform *edit-config* towards the *candidate* datastore.
2. Update the BBU-Router network to be in 10.0.100.0/30. Use *netconf-console2* to perform *edit-config* towards the *candidate* datastore. Make sure to configure the right interfaces of the devices.
3. Update the Router-Core network to be in 10.0.200.0/30. Use *netconf-console2* to perform *edit-config* towards the *candidate* datastore. Make sure to configure the right interfaces of the devices.

Activities:
* Check with *netconf-console2* with *--get-config*, towards *running*, *startup* and *candidate*
    * Would the current configuration allow the system to work properly?
    * Are there differences between the datastores? Why? 
    * What would happen if a device gets restarted in such a case?
    * What would happen to the network if the configuration applied to BBU backhaul0 was not matching the network configuration applied to Router eth1? Was there any check available to prevent this?
* How does this approach scale? What is the impact in terms of time spent if we have to manage 100 RAN devices, 50 router devices and 1 core network device?
* Further checks: check that the three devices have consistent IP addresses with the *network-check.py* script and, in case not, modify IP addresses again

### Bonus

1. Perform a commit operation with *netconf-console2* so that the *candidate* datastore gets committed to the *running* and perform above checks again
* Check with *netconf-console2* with *--get-config*, towards *running*, *startup* and *candidate*
    * Would the current configuration allow the system to work properly?
    * Are there differences between the datastores? Why? 
    * What would happen if a device gets restarted in such a case?
2. Perform a copy-config operation with with *netconf-console2* so that the *running* datastore gets committed to the *startup* and perform above checks again
* Check with *netconf-console2* with *--get-config*, towards *running*, *startup* and *candidate*
    * Would the current configuration allow the system to work properly?
    * Are there differences between the datastores? Why? 
    * What would happen if a device gets restarted in such a case?


## Exercise 2 - Automate with Python

Start by restarting the system with 

```bash
sudo podman-compose restart   # or: sudo podman compose restart (if available)
```

Create a python script that makes use of [ncclient](https://pypi.org/project/ncclient/) to perform the following: 
1. Connect to each device
2. Use *edit-config* towards the *running* datastore and modify eth0 IPv4 address values to be consistently in 192.168.1.0/24
3. Check the devices with *get-config* and ensure all eth0 interfaces are correctly configured to be in 192.168.1.0/24

**Tip:** See `exercise2_baseline.py` for a starting point and `exercise2_solution.py` for a complete example.

#### Success Criteria
- All eth0 interfaces on all devices have an IP in 192.168.1.0/24.
- `network-check.py` reports no inconsistencies.

Activities:
* How does this approach scale? What is the impact in terms of time spent if we have to manage 100 RAN devices, 50 router devices and 1 core network device?


## Exercise 3 - Automate with Ansible

Start by restarting the system with 

```bash
sudo podman-compose restart   # or: sudo podman compose restart (if available)
```

1. Look at the files inside *ansible* folder
    * inventory.yml -> The inventory
    * network_automation.yml -> The playbook
    * README.md, COMPARISON.md, TROUBLESHOOTING.md for general knowledge
2. Run the playbook with
```bash
ansible-playbook -i inventory.yml network_automation.yml --tags=auto
```
3. Check with *netconf-console2* (or python or directly from ansible) the *--get-config* operation, towards *running*, *startup* and *candidate*

Activities:
* What is the playbook doing?
* Is the playbook working with candidate, running, startup or all of them?
* How does this approach scale? What is the impact in terms of time spent if we have to manage 100 RAN devices, 50 router devices and 1 core network device?
* What is the time spent compared to the other solutions?


## Assignment 

Start by restarting the system with 

```bash
sudo podman-compose restart   # or: sudo podman compose restart (if available)
```

Create a python script that makes use of [ncclient](https://pypi.org/project/ncclient/) to perform the following tasks. Feel free to reuse any code already available while making sure to comment the different functions. 
1. Connect to each device
2. Use *edit-config* towards the *candidate* datastore and modify eth0 IPv4 address values to be consistently in 192.168.1.0/24
3. Use *edit-config* towards the *candidate* datastore and modify **backhaul IPv4 address values** as follows:
    - **RAN:** configure `backhaul0`
    - **Router:** configure `eth1` and `eth2`
    - **Core:** configure `eth1`
   
    Assign the interfaces to be consistently in the related networks:
    - **BBU-Router network:** `10.0.1.0/30`
    - **Router-Core network:** `10.0.2.0/30`
4. Check the devices with *get-config* towards the *candidate* datastore and ensure all interfaces are correctly configured as expected.
If confirmed, perform a *commit* operation and check the *running* datastore.

Activities:
* Check with *netconf-console2* with *--get-config*, towards *running*, *startup* and *candidate*
    * Would the current configuration allow the system to work properly?
    * Are there differences between the datastores? Why? 
    * What would happen if a device gets restarted in such a case?
* How does this approach scale? What is the impact in terms of time spent if we have to manage 100 RAN devices, 50 router devices and 1 core network device?
* Further checks: check that the three devices have consistent IP addresses with the *network-check.py* script and, in case not, modify IP addresses again


## Troubleshooting

**Common Issues:**

- **Cannot connect to device:**
    - Check device IP, port, username, and password.
    - Ensure the device is running and reachable from your host.
- **ncclient not installed:**
    - Run `pip3 install ncclient`.
- **`externally-managed-environment` error when running `pip3 install`:**
    - Debian/Ubuntu blocks system-wide pip installs (PEP 668). Add `--break-system-packages` to the `pip3 install` command.
- **`command not found` for `ansible`, `netconf-console2`, etc. after `pip3 install --user`:**
    - `~/.local/bin` is not in your `PATH`. Run `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc`.
- **`ModuleNotFoundError: No module named 'six'` when running `netconf-console2`:**
    - `netconf-console2` depends on `six` but it is not always pulled in automatically. Run `pip3 install --user --break-system-packages six`.
- **netconf-console2 not found:**
    - Run `pip3 install netconf-console2` or check your PATH.
- **Ansible errors:**
    - Check your inventory and playbook syntax.
- **IP address not updated:**
    - Verify your XML payload and device YANG model compatibility.

If you encounter other issues, check the logs or ask your instructor for help.

## Reference commands

Retrieve current configuration of *running* datastore with *netconf-console2*:
```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db running --get-config 
```

Modify current configuration of *candidate* datastore with the content of *operations/change-eth0.xml*:
```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db candidate --edit-config operations/change-eth0.xml 
```

Retrieve current configuration of *startup* datastore with *netconf-console2*, by filtering per the *interfaces* xpath:
```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db startup --get-config -x /interfaces
```

Retrieve current configuration of *startup* datastore with *netconf-console2*, by filtering per the *eth0 interface* xpath:
```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db startup --get-config -x '/interfaces/interface[name="eth0"]'
```
