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

### 1. Prerequisites

You need the following tools installed on your system (any Linux distribution, including WSL, macOS, or native):

- **Docker** 
- **Docker Compose**
- **Python 3** and **pip3**
- **Ansible**
- **Python packages:** `ncclient`, `netconf-console2`, `paramiko`


**For WSL users:**
In case Docker is not already installed, you have two options for Docker setup:

1. **Docker Desktop for Windows (Slower, but recommended for entry-level users):**
    - Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) and ensure it is running.
    - Enable WSL2 integration in Docker Desktop settings.
    - This is the most seamless experience and is required if you want to use GUI tools, volume mounts, or need full Windows integration.

2. **Native Docker inside WSL Linux (Recommended native integration in the distro, but for advanced users):**
    - You can install Docker directly in your WSL distribution using your package manager (e.g., `sudo apt install docker.io` for Ubuntu).
    - Depending on the distro you might need to manually start the Docker daemon (e.g., `sudo service docker start`) each session, and handle permissions yourself.

### 2. Install Required Tools

Install the above tools using your distribution's package manager or download from the official websites:

- [Docker installation guide](https://docs.docker.com/get-docker/)
- [Docker Compose installation](https://docs.docker.com/compose/install/)
- [Python downloads](https://www.python.org/downloads/)
- [Ansible installation guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)

**Install Python dependencies:**
```bash
pip3 install --user ncclient netconf-console2 paramiko ansible
```

### 3. (Optional) Add Your User to the Docker Group (for non-root usage)
```bash
sudo usermod -aG docker $USER
# Then restart your shell or run: exec su -l $USER
```

### 4. Verify Installations

```bash
docker --version
docker compose version   # or: docker-compose --version
python3 --version
pip3 --version
ansible --version
netconf-console2 --help  # should print help if installed
```

### 5. Start the Lab Environment

Download the repo:
```bash
git clone https://github.com/unusualfor/network-automation.git
cd network-automation/
```

Depending on your Docker Compose version, use one of the following:

```bash
# For docker-compose v1
docker-compose up

# For docker-compose v2 (recommended)
docker compose up
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
docker compose restart
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
docker compose restart
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
docker compose restart
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
