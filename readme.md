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

- **Docker** (Docker Engine)
- **Docker Compose** (the built-in `docker compose` subcommand, provided by the `docker-compose-plugin` package that ships with Docker Engine)
- **Python 3** and **pip3**
- **Ansible**
- **Python packages:** `ncclient`, `netconf-console2`, `paramiko`


**For WSL users:**
This lab runs with **Docker in rootful mode** (all `docker` commands are executed with `sudo`).
Rootful mode avoids the rootless low-port (830/831/832) binding limitations.

Install Docker directly inside your WSL distribution using Docker's official APT repository:

```bash
# Debian / Ubuntu
sudo apt update
sudo apt install -y ca-certificates curl git vim tmux python3-pip

# Add Docker's official GPG key and repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine, CLI, containerd and the Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

> On Ubuntu, replace `linux/debian` with `linux/ubuntu` in the two URLs above.

Notes:
- Docker uses a background daemon (`dockerd`). On WSL start it with `sudo service docker start` (or `sudo dockerd &`); on native Linux with systemd enable it with `sudo systemctl enable --now docker`.
- The `docker compose` subcommand is provided by the `docker-compose-plugin` package installed above (this replaces the standalone `docker-compose` binary).

### 2. Install Required Tools

Install the above tools using your distribution's package manager or download from the official websites:

- [Docker installation guide](https://docs.docker.com/engine/install/)
- [Docker Compose installation](https://docs.docker.com/compose/install/)
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


### 3. Rootful Docker

This lab uses **rootful Docker**, so container commands are prefixed with `sudo`.
Running with `sudo` avoids the rootless low-port (830/831/832) binding limitations
and keeps the commands consistent throughout the lab. If you prefer running Docker
without `sudo`, add your user to the `docker` group (`sudo usermod -aG docker $USER`)
and open a new shell — but then drop the `sudo` prefix from every command below.

### 4. Verify Installations

```bash
sudo docker --version
sudo docker compose version
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

Start the lab with Docker Compose (rootful):

```bash
sudo docker compose up
```

Check that all containers are running:
```bash
sudo docker ps
CONTAINER ID   IMAGE                                 COMMAND                  CREATED         STATUS                   PORTS                                     NAMES
9d3d35a4b8be   ghcr.io/notconf/notconf:14265929521   "/bin/sh -c /run.sh"     4 minutes ago   Up 4 minutes (healthy)   0.0.0.0:830->830/tcp, :::830->830/tcp     ran-device
e766e8a33b54   ghcr.io/notconf/notconf:14265929521   "/bin/sh -c /run.sh"     4 minutes ago   Up 4 minutes (healthy)   0.0.0.0:831->830/tcp, :::831->830/tcp     router-device
d14d68a976ca   ghcr.io/notconf/notconf:14265929521   "/bin/sh -c /run.sh"     4 minutes ago   Up 4 minutes (healthy)   0.0.0.0:832->830/tcp, :::832->830/tcp     core-device
```

Check host ports:
```bash
sudo docker port ran-device
830/tcp -> 0.0.0.0:830

sudo docker port router-device
830/tcp -> 0.0.0.0:831

sudo docker port core-device
830/tcp -> 0.0.0.0:832
```

Check the initial configuration of the devices:
N.B: It's expected that there will be errors in the network consistency check initially. These errors should be resolved as you configure the network devices correctly.
```bash
python3 network_check.py
================================================================================
🔍 Network Consistency Check - 2026-09-13 16:51:42
================================================================================
📡 Device Status:
   RAN      (localhost:830): ✅ Connected - 4 interfaces
   Router   (localhost:831): ✅ Connected - 4 interfaces
   Core     (localhost:832): ✅ Connected - 4 interfaces

🔗 Network Link Status:
   Network A (RAN-Router Backhaul)     ❌ ERROR Different networks: 10.0.1.0/30 vs 10.0.10.0/30
   Network B (Router-Core)             ❌ ERROR Different networks: 10.0.200.0/30 vs 10.0.172.0/30
   Management Network                  ❌ ERROR Different networks: 192.168.1.0/24 vs 192.168.100.0/24
   Management Network (Router-Core)    ⚠️  WARNING Unexpected network: 192.168.100.0/24 (expected 192.168.1.0/24)

📋 Interface Details:
   📱 RAN:
      backhaul0    🟢 10.0.1.1/30         (Backhaul to router)
      eth0         🟢 192.168.1.10/24     (Management interface)
      lo0          🟢 127.0.0.1/32        (Loopback interface)
      radio0       🟢 No IP               (5G NR radio interface)
   📱 Router:
      eth0         🟢 192.168.100.20/24   (Management interface)
      eth1         🟢 10.0.10.2/30        (Interface to RAN)
      eth2         🟢 10.0.200.1/30       (Interface to Core)
      lo0          🟢 127.0.0.1/32        (Loopback interface)
   📱 Core:
      eth0         🟢 192.168.100.30/24   (Management interface)
      eth1         🟢 10.0.172.2/30       (Interface to Router)
      eth2         🟢 203.0.113.1/24      (Interface to Internet/External)
      lo0          🟢 127.0.0.1/32        (Loopback interface)
```

## Exercise 1

### Check initial configuration

Once everything is up and running, check the current configuration for the *running*, *startup* and *candidate* datastores using [*netconf-console2*](https://pypi.org/project/netconf-console2/) with *--get-config*.
Check the initial configuration of the devices:
```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db running --get-config
netconf-console2 --host localhost --port 831 --user admin --password admin --db running --get-config
netconf-console2 --host localhost --port 832 --user admin --password admin --db running --get-config
```

Save the initial configuration of the devices to XML files for later reference:
```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db running --get-config > ran-device-config.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db running --get-config > router-device-config.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db running --get-config > core-device-config.xml

netconf-console2 --host localhost --port 830 --user admin --password admin --db running --get-config -x /interfaces/interface > ran-interfaces-before-change.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db running --get-config -x /interfaces/interface > router-interfaces-before-change.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db running --get-config -x /interfaces/interface > core-interfaces-before-change.xml
```

```bash
diff ran-device-config.xml router-device-config.xml -y --suppress-common-lines
      <name>backhaul0</name>                                  |       <name>eth0</name>
      <description>Backhaul to router</description>           |       <description>Management interface</description>
          <ip>10.0.1.1</ip>                                   |           <ip>192.168.100.20</ip>
                                                              >           <prefix-length>24</prefix-length>
                                                              >         </address>
                                                              >       </ipv4>
                                                              >     </interface>
                                                              >     <interface>
                                                              >       <name>eth1</name>
                                                              >       <description>Interface to RAN</description>
                                                              >       <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-i
                                                              >       <enabled>true</enabled>
                                                              >       <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
                                                              >         <enabled>true</enabled>
                                                              >         <address>
                                                              >           <ip>10.0.10.2</ip>
      <name>eth0</name>                                       |       <name>eth2</name>
      <description>Management interface</description>         |       <description>Interface to Core</description>
          <ip>192.168.100.10</ip>                             |           <ip>10.0.200.1</ip>
          <prefix-length>24</prefix-length>                   |           <prefix-length>30</prefix-length>
    </interface>                                              <
    <interface>                                               <
      <name>radio0</name>                                     <
      <description>5G NR radio interface</description>        <
      <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-i <
      <enabled>true</enabled>                                 <


diff router-device-config.xml core-device-config.xml -y --suppress-common-lines
          <ip>192.168.100.20</ip>                             |           <ip>192.168.100.30</ip>
      <description>Interface to RAN</description>             |       <description>Interface to Router</description>
          <ip>10.0.10.2</ip>                                  |           <ip>10.0.172.2</ip>
      <description>Interface to Core</description>            |       <description>Interface to Internet/External</descriptio
          <ip>10.0.200.1</ip>                                 |           <ip>203.0.113.1</ip>
          <prefix-length>30</prefix-length>                   |           <prefix-length>24</prefix-length>



diff ran-device-config.xml core-device-config.xml -y --suppress-common-lines
      <name>backhaul0</name>                                  |       <name>eth0</name>
      <description>Backhaul to router</description>           |       <description>Management interface</description>
          <ip>10.0.1.1</ip>                                   |           <ip>192.168.100.30</ip>
                                                              >           <prefix-length>24</prefix-length>
                                                              >         </address>
                                                              >       </ipv4>
                                                              >     </interface>
                                                              >     <interface>
                                                              >       <name>eth1</name>                                                                                           >       <description>Interface to Router</description>
                                                              >       <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-i
                                                              >       <enabled>true</enabled>
                                                              >       <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
                                                              >         <enabled>true</enabled>
                                                              >         <address>
                                                              >           <ip>10.0.172.2</ip>
      <name>eth0</name>                                       |       <name>eth2</name>
      <description>Management interface</description>         |       <description>Interface to Internet/External</descriptio
          <ip>192.168.100.10</ip>                             |           <ip>203.0.113.1</ip>
    </interface>                                              <
    <interface>                                               <
      <name>radio0</name>                                     <
      <description>5G NR radio interface</description>        <
      <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-i <
      <enabled>true</enabled>                                 <
```

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

```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db running --edit-config operations/exercise1-running-ran.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db running --edit-config operations/exercise1-running-router.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db running --edit-config operations/exercise1-running-core.xml
```
Check differences between the configurations:
```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db running --get-config -x /interfaces/interface > ran-interfaces-after-change.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db running --get-config -x /interfaces/interface > router-interfaces-after-change.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db running --get-config -x /interfaces/interface > core-interfaces-after-change.xml

diff ran-interfaces-before-change.xml ran-interfaces-after-change.xml
diff router-interfaces-before-change.xml router-interfaces-after-change.xml
diff core-interfaces-before-change.xml core-interfaces-after-change.xml
```

Check *running*, *startup* and *candidate* datastores for each device and save the output into the *exercise1* folder:
```bash
# RAN (port 830)
netconf-console2 --host localhost --port 830 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/ran-running.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/ran-startup.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/ran-candidate.xml

# Router (port 831)
netconf-console2 --host localhost --port 831 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/router-running.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/router-startup.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/router-candidate.xml

# Core (port 832)
netconf-console2 --host localhost --port 832 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/core-running.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/core-startup.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/core-candidate.xml
```

Compare the datastores of each device (empty output = datastores are identical):
```bash
# RAN
diff exercise1/ran-running.xml    exercise1/ran-startup.xml
diff exercise1/ran-running.xml    exercise1/ran-candidate.xml
diff exercise1/ran-startup.xml    exercise1/ran-candidate.xml

# Router
diff exercise1/router-running.xml exercise1/router-startup.xml
diff exercise1/router-running.xml exercise1/router-candidate.xml
diff exercise1/router-startup.xml exercise1/router-candidate.xml

# Core
diff exercise1/core-running.xml   exercise1/core-startup.xml
diff exercise1/core-running.xml   exercise1/core-candidate.xml
diff exercise1/core-startup.xml   exercise1/core-candidate.xml
```

Verify IP consistency across all three devices end-to-end:
```bash
python3 network_check.py
================================================================================
🔍 Network Consistency Check - 2026-09-13 17:18:21
================================================================================
📡 Device Status:
   RAN      (localhost:830): ✅ Connected - 4 interfaces
   Router   (localhost:831): ✅ Connected - 4 interfaces
   Core     (localhost:832): ✅ Connected - 4 interfaces

🔗 Network Link Status:
   Network A (RAN-Router Backhaul)     ✅ OK 10.0.1.1/30 ↔ 10.0.1.2/30
   Network B (Router-Core)             ✅ OK 10.0.2.1/30 ↔ 10.0.2.2/30
   Management Network                  ✅ OK 192.168.1.10/24 ↔ 192.168.1.20/24
   Management Network (Router-Core)    ✅ OK 192.168.1.20/24 ↔ 192.168.1.30/24

📋 Interface Details:
   📱 RAN:
      backhaul0    🟢 10.0.1.1/30         (Backhaul to router)
      eth0         🟢 192.168.1.10/24     (Management interface)
      lo0          🟢 127.0.0.1/32        (Loopback interface)
      radio0       🟢 No IP               (5G NR radio interface)
   📱 Router:
      eth0         🟢 192.168.1.20/24     (Management interface)
      eth1         🟢 10.0.1.2/30         (Interface to RAN)
      eth2         🟢 10.0.2.1/30         (Interface to Core)
      lo0          🟢 127.0.0.1/32        (Loopback interface)
   📱 Core:
      eth0         🟢 192.168.1.30/24     (Management interface)
      eth1         🟢 10.0.2.2/30         (Interface to Router)
      eth2         🟢 203.0.113.1/24      (Interface to Internet/External)
      lo0          🟢 127.0.0.1/32        (Loopback interface)
```


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

Apply the changes to the *candidate* datastore (the *running* datastore is not affected until a *commit*):
```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db candidate --edit-config operations/exercise1-candidate-ran.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db candidate --edit-config operations/exercise1-candidate-router.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db candidate --edit-config operations/exercise1-candidate-core.xml
```

Check *running*, *startup* and *candidate* datastores for each device and save the output into the *exercise1* folder:
```bash
# RAN (port 830)
netconf-console2 --host localhost --port 830 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/ran-running-candidate-ex.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/ran-startup-candidate-ex.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/ran-candidate-candidate-ex.xml

# Router (port 831)
netconf-console2 --host localhost --port 831 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/router-running-candidate-ex.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/router-startup-candidate-ex.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/router-candidate-candidate-ex.xml

# Core (port 832)
netconf-console2 --host localhost --port 832 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/core-running-candidate-ex.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/core-startup-candidate-ex.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/core-candidate-candidate-ex.xml
```

Compare running vs candidate for each device (the candidate holds the new changes, running still holds the old ones):
```bash
diff exercise1/ran-running-candidate-ex.xml    exercise1/ran-candidate-candidate-ex.xml
diff exercise1/router-running-candidate-ex.xml exercise1/router-candidate-candidate-ex.xml
diff exercise1/core-running-candidate-ex.xml   exercise1/core-candidate-candidate-ex.xml
```

Check network consistency with the provided script:
```bash
 python3 network_check.py
================================================================================
🔍 Network Consistency Check - 2026-09-13 17:31:02
================================================================================
📡 Device Status:
   RAN      (localhost:830): ✅ Connected - 4 interfaces
   Router   (localhost:831): ✅ Connected - 4 interfaces
   Core     (localhost:832): ✅ Connected - 4 interfaces

🔗 Network Link Status:
   Network A (RAN-Router Backhaul)     ✅ OK 10.0.1.1/30 ↔ 10.0.1.2/30
   Network B (Router-Core)             ✅ OK 10.0.2.1/30 ↔ 10.0.2.2/30
   Management Network                  ✅ OK 192.168.1.10/24 ↔ 192.168.1.20/24
   Management Network (Router-Core)    ✅ OK 192.168.1.20/24 ↔ 192.168.1.30/24

📋 Interface Details:
   📱 RAN:
      backhaul0    🟢 10.0.1.1/30         (Backhaul to router)
      eth0         🟢 192.168.1.10/24     (Management interface)
      lo0          🟢 127.0.0.1/32        (Loopback interface)
      radio0       🟢 No IP               (5G NR radio interface)
   📱 Router:
      eth0         🟢 192.168.1.20/24     (Management interface)
      eth1         🟢 10.0.1.2/30         (Interface to RAN)
      eth2         🟢 10.0.2.1/30         (Interface to Core)
      lo0          🟢 127.0.0.1/32        (Loopback interface)
   📱 Core:
      eth0         🟢 192.168.1.30/24     (Management interface)
      eth1         🟢 10.0.2.2/30         (Interface to Router)
      eth2         🟢 203.0.113.1/24      (Interface to Internet/External)
      lo0          🟢 127.0.0.1/32        (Loopback interface)
```

#### Answers to the activities questions

**Would the current configuration allow the system to work properly?**
Not yet. The `edit-config` operations were applied only to the *candidate* datastore. The device actually runs from the *running* datastore, which still holds the previous configuration. The new addresses (192.168.1.x/24, 10.0.100.0/30, 10.0.200.0/30) become active only after a *commit* (candidate → running).

**Are there differences between the datastores? Why?**
Yes. After editing the candidate we have `candidate ≠ running` (and `≠ startup`). This is expected: `edit-config` towards *candidate* does not touch *running* or *startup*. The candidate is a scratch/working copy that stays divergent until a *commit* copies it into *running*, and a *copy-config* copies *running* into *startup*.

**What would happen if a device gets restarted in such a case?**
On restart the device loads *startup* into *running*. Since the candidate was never committed, every edit is lost and the device comes back with the old *startup* configuration. The candidate content is discarded.

**What would happen to the network if the BBU `backhaul0` did not match Router `eth1`? Was there any check available to prevent it?**
The backhaul link would break: the two ends would sit in different subnets, so there would be no L3 connectivity between RAN and Router. NETCONF/YANG validation is *per-device* — each node only validates its own configuration against its models, so this cross-device mismatch is **not** caught automatically. This is exactly why the external `network_check.py` script exists: it verifies end-to-end consistency across all three devices.

**How does this approach scale (100 RAN + 50 Router + 1 Core)?**
It does not scale well. Configuring devices one by one with `netconf-console2` is an O(N) manual effort: 151 devices would require 151 × (edit-config + verification), which is slow and error-prone. This is the motivation for automation — Python/`ncclient` (Exercise 2) and Ansible (Exercise 3) — where the same logic loops over an inventory and applies the changes consistently to every device.

### Bonus

Before committing, verify that the datastores are **not** aligned yet (the candidate holds the new changes, running and startup still hold the old ones):
```bash
# RAN (port 830)
netconf-console2 --host localhost --port 830 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/ran-running-bonus-before.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/ran-startup-bonus-before.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/ran-candidate-bonus-before.xml

# Router (port 831)
netconf-console2 --host localhost --port 831 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/router-running-bonus-before.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/router-startup-bonus-before.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/router-candidate-bonus-before.xml

# Core (port 832)
netconf-console2 --host localhost --port 832 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/core-running-bonus-before.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/core-startup-bonus-before.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/core-candidate-bonus-before.xml

# These diffs are expected to show differences (datastores NOT aligned)
diff exercise1/ran-running-bonus-before.xml    exercise1/ran-candidate-bonus-before.xml
diff exercise1/ran-startup-bonus-before.xml    exercise1/ran-candidate-bonus-before.xml
diff exercise1/router-running-bonus-before.xml exercise1/router-candidate-bonus-before.xml
diff exercise1/router-startup-bonus-before.xml exercise1/router-candidate-bonus-before.xml
diff exercise1/core-running-bonus-before.xml   exercise1/core-candidate-bonus-before.xml
diff exercise1/core-startup-bonus-before.xml   exercise1/core-candidate-bonus-before.xml
```

1. Perform a commit operation with *netconf-console2* so that the *candidate* datastore gets committed to the *running* and perform above checks again
* Check with *netconf-console2* with *--get-config*, towards *running*, *startup* and *candidate*
    * Would the current configuration allow the system to work properly?
    * Are there differences between the datastores? Why? 
    * What would happen if a device gets restarted in such a case?

```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --commit
netconf-console2 --host localhost --port 831 --user admin --password admin --commit
netconf-console2 --host localhost --port 832 --user admin --password admin --commit
```

After the commit, verify that *running* now matches *candidate*, but *startup* is still different (it is untouched by a commit):
```bash
# RAN (port 830)
netconf-console2 --host localhost --port 830 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/ran-running-bonus-after-commit.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/ran-startup-bonus-after-commit.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/ran-candidate-bonus-after-commit.xml

# Router (port 831)
netconf-console2 --host localhost --port 831 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/router-running-bonus-after-commit.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/router-startup-bonus-after-commit.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/router-candidate-bonus-after-commit.xml

# Core (port 832)
netconf-console2 --host localhost --port 832 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/core-running-bonus-after-commit.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/core-startup-bonus-after-commit.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/core-candidate-bonus-after-commit.xml

# running == candidate (empty diff), but startup still differs
diff exercise1/ran-running-bonus-after-commit.xml    exercise1/ran-candidate-bonus-after-commit.xml
diff exercise1/ran-startup-bonus-after-commit.xml    exercise1/ran-running-bonus-after-commit.xml
diff exercise1/router-running-bonus-after-commit.xml exercise1/router-candidate-bonus-after-commit.xml
diff exercise1/router-startup-bonus-after-commit.xml exercise1/router-running-bonus-after-commit.xml
diff exercise1/core-running-bonus-after-commit.xml   exercise1/core-candidate-bonus-after-commit.xml
diff exercise1/core-startup-bonus-after-commit.xml   exercise1/core-running-bonus-after-commit.xml
```

2. Perform a copy-config operation with with *netconf-console2* so that the *running* datastore gets committed to the *startup* and perform above checks again
* Check with *netconf-console2* with *--get-config*, towards *running*, *startup* and *candidate*
    * Would the current configuration allow the system to work properly?
    * Are there differences between the datastores? Why? 
    * What would happen if a device gets restarted in such a case?

```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --copy-running-to-startup
netconf-console2 --host localhost --port 831 --user admin --password admin --copy-running-to-startup
netconf-console2 --host localhost --port 832 --user admin --password admin --copy-running-to-startup
```

After the copy-config, verify that all three datastores are now **aligned** (all diffs are empty):
```bash
# RAN (port 830)
netconf-console2 --host localhost --port 830 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/ran-running-bonus-after-copy.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/ran-startup-bonus-after-copy.xml
netconf-console2 --host localhost --port 830 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/ran-candidate-bonus-after-copy.xml

# Router (port 831)
netconf-console2 --host localhost --port 831 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/router-running-bonus-after-copy.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/router-startup-bonus-after-copy.xml
netconf-console2 --host localhost --port 831 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/router-candidate-bonus-after-copy.xml

# Core (port 832)
netconf-console2 --host localhost --port 832 --user admin --password admin --db running   --get-config -x /interfaces/interface > exercise1/core-running-bonus-after-copy.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db startup   --get-config -x /interfaces/interface > exercise1/core-startup-bonus-after-copy.xml
netconf-console2 --host localhost --port 832 --user admin --password admin --db candidate --get-config -x /interfaces/interface > exercise1/core-candidate-bonus-after-copy.xml

# All diffs are expected to be empty (running == startup == candidate)
diff exercise1/ran-running-bonus-after-copy.xml    exercise1/ran-startup-bonus-after-copy.xml
diff exercise1/ran-running-bonus-after-copy.xml    exercise1/ran-candidate-bonus-after-copy.xml
diff exercise1/ran-startup-bonus-after-copy.xml    exercise1/ran-candidate-bonus-after-copy.xml
diff exercise1/router-running-bonus-after-copy.xml exercise1/router-startup-bonus-after-copy.xml
diff exercise1/router-running-bonus-after-copy.xml exercise1/router-candidate-bonus-after-copy.xml
diff exercise1/router-startup-bonus-after-copy.xml exercise1/router-candidate-bonus-after-copy.xml
diff exercise1/core-running-bonus-after-copy.xml   exercise1/core-startup-bonus-after-copy.xml
diff exercise1/core-running-bonus-after-copy.xml   exercise1/core-candidate-bonus-after-copy.xml
diff exercise1/core-startup-bonus-after-copy.xml   exercise1/core-candidate-bonus-after-copy.xml
```


## Exercise 2 - Automate with Python

Start by restarting the system with 

```bash
sudo docker compose restart
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
sudo docker compose restart
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
sudo docker compose restart
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
