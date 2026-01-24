# VM No Network Connection Fix

## Problem
VM has no network connectivity after installation or reboot.

## Solution

### 1. Check network interface
```bash
ip link show
```
Look for your interface name (commonly `ens33`, `eth0`, or similar). **Ignore `lo` (loopback interface)**.

### 2. Enable NetworkManager and configure interface
```bash
# Enable and start NetworkManager
systemctl enable --now NetworkManager

# Add ethernet connection (replace ens33 with your interface name)
nmcli connection add type ethernet ifname ens33 con-name ens33 ipv4.method auto

# Enable autoconnect on boot
nmcli connection modify ens33 connection.autoconnect yes

# Bring connection up
nmcli connection up ens33
```

### 3. Verify connectivity
```bash
ip addr show ens33
ping -c 4 8.8.8.8
```
