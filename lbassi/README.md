# Assignment - NETCONF automation with ncclient

Python solution for the **Assignment** section of the main project README.
The script [`assignment.py`](assignment.py) configures the three lab devices
(RAN, Router, Core) using [`ncclient`](https://pypi.org/project/ncclient/):
it stages the changes into the **candidate** datastore, verifies them, and then
**commits** them into **running**.

## What the script does

For every device it:

1. Opens a NETCONF session.
2. `edit-config` towards **candidate** to set `eth0` in `192.168.1.0/24`.
3. `edit-config` towards **candidate** to set the backhaul interfaces:
   | Device | Interface(s) | Network |
   | ------ | ------------ | ------- |
   | RAN    | `backhaul0`  | `10.0.1.0/30` (BBU-Router) |
   | Router | `eth1`, `eth2` | `10.0.1.0/30` + `10.0.2.0/30` |
   | Core   | `eth1`       | `10.0.2.0/30` (Router-Core) |
4. `get-config` on **candidate** to check the staged configuration.
5. `commit` (candidate → running) and re-reads **running** to confirm.

Assigned addresses:

| Device | eth0 | backhaul |
| ------ | ---- | -------- |
| RAN    | `192.168.1.10/24` | `backhaul0` `10.0.1.1/30` |
| Router | `192.168.1.20/24` | `eth1` `10.0.1.2/30`, `eth2` `10.0.2.1/30` |
| Core   | `192.168.1.30/24` | `eth1` `10.0.2.2/30` |

## Prerequisites

- The lab environment is up (see the main README "Setup" section):
  ```bash
  sudo docker compose up -d
  sudo docker ps
  ```
- Python dependencies installed:
  ```bash
  pip3 install --user --break-system-packages ncclient lxml
  ```

## How to run

The assignment asks to restart the environment first, so the devices start from
a clean state:

```bash
sudo docker compose restart
```

Then run the script from the repository root:

```bash
python3 lbassi/assignment.py
```

You will see, per device: the connection log, the `edit-config` confirmation,
the `get-config` on candidate, the `commit`, and the `get-config` on running.

## Verify the result

Check end-to-end IP consistency with the provided checker:

```bash
python3 network_check.py
```

Expected output — all links `✅ OK`:

```text
🔗 Network Link Status:
   Network A (RAN-Router Backhaul)     ✅ OK 10.0.1.1/30 ↔ 10.0.1.2/30
   Network B (Router-Core)             ✅ OK 10.0.2.1/30 ↔ 10.0.2.2/30
   Management Network                  ✅ OK 192.168.1.10/24 ↔ 192.168.1.20/24
   Management Network (Router-Core)    ✅ OK 192.168.1.20/24 ↔ 192.168.1.30/24
```

You can also inspect a single datastore with `netconf-console2`:

```bash
netconf-console2 --host localhost --port 830 --user admin --password admin --db running --get-config -x /interfaces
```

## Notes

- The script is **idempotent**: the edits use `nc:operation="replace"` on the
  `ipv4` container, so it can be re-run safely.
- `commit` aligns **running** with **candidate**, but **startup** stays
  unchanged. On a device restart the device reloads **startup**, so to make the
  configuration persistent you would additionally run a `copy-config`
  running → startup (see the Exercise 1 "Bonus" section in the main README).
- Running from Windows/WSL: the devices listen on `localhost` ports
  `830/831/832`; run the script inside the same WSL distro where the containers
  are running.
