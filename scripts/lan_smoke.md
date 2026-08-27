# LAN Smoke Test Runbook

This runbook specifies operational deployment and verification across three physical hosts on a local area network:
- Desktop: `192.168.1.10` (coordinator)
- Laptop A: `192.168.1.11` (worker)
- Laptop B: `192.168.1.12` (worker)

Port `7433` is used for mTLS transport.

---

## 1. Certificate Authority and Certificate Generation

Run on Desktop (`192.168.1.10`):

```bash
mkdir -p /etc/hyge/certs
./scripts/make_ca.sh /etc/hyge/certs
```

Distribute certificates and private keys via scp:

```bash
# On Laptop A (192.168.1.11):
mkdir -p /etc/hyge/certs
scp user@192.168.1.10:/etc/hyge/certs/ca.crt /etc/hyge/certs/ca.crt
scp user@192.168.1.10:/etc/hyge/certs/laptop-a.crt /etc/hyge/certs/laptop-a.crt
scp user@192.168.1.10:/etc/hyge/certs/laptop-a.key /etc/hyge/certs/laptop-a.key
chmod 600 /etc/hyge/certs/laptop-a.key
chmod 644 /etc/hyge/certs/*.crt

# On Laptop B (192.168.1.12):
mkdir -p /etc/hyge/certs
scp user@192.168.1.10:/etc/hyge/certs/ca.crt /etc/hyge/certs/ca.crt
scp user@192.168.1.10:/etc/hyge/certs/laptop-b.crt /etc/hyge/certs/laptop-b.crt
scp user@192.168.1.10:/etc/hyge/certs/laptop-b.key /etc/hyge/certs/laptop-b.key
chmod 600 /etc/hyge/certs/laptop-b.key
chmod 644 /etc/hyge/certs/*.crt
```

The CA private key `/etc/hyge/certs/ca.key` remains offline on the desktop.

---

## 2. Node Configuration Files

### Desktop (`/etc/hyge/node_config.json` on `192.168.1.10`)

```json
{
  "name": "desktop",
  "role": "coordinator",
  "cert_path": "/etc/hyge/certs/desktop.crt",
  "key_path": "/etc/hyge/certs/desktop.key",
  "ca_path": "/etc/hyge/certs/ca.crt",
  "host": "0.0.0.0",
  "port": 7433,
  "authority_cns": ["desktop", "authority"],
  "budgets": {
    "max_fires": 500
  },
  "peers": {
    "laptop-a": {
      "host": "192.168.1.11",
      "port": 7433,
      "role": "worker"
    },
    "laptop-b": {
      "host": "192.168.1.12",
      "port": 7433,
      "role": "worker"
    }
  }
}
```

### Laptop A (`/etc/hyge/node_config.json` on `192.168.1.11`)

```json
{
  "name": "laptop-a",
  "role": "worker",
  "cert_path": "/etc/hyge/certs/laptop-a.crt",
  "key_path": "/etc/hyge/certs/laptop-a.key",
  "ca_path": "/etc/hyge/certs/ca.crt",
  "host": "192.168.1.11",
  "port": 7433,
  "budgets": {
    "max_fires": 50
  },
  "peers": {
    "desktop": {
      "host": "192.168.1.10",
      "port": 7433,
      "role": "coordinator"
    }
  }
}
```

### Laptop B (`/etc/hyge/node_config.json` on `192.168.1.12`)

```json
{
  "name": "laptop-b",
  "role": "worker",
  "cert_path": "/etc/hyge/certs/laptop-b.crt",
  "key_path": "/etc/hyge/certs/laptop-b.key",
  "ca_path": "/etc/hyge/certs/ca.crt",
  "host": "192.168.1.12",
  "port": 7433,
  "budgets": {
    "max_fires": 50
  },
  "peers": {
    "desktop": {
      "host": "192.168.1.10",
      "port": 7433,
      "role": "coordinator"
    }
  }
}
```

---

## 3. Firewall Configuration

On Desktop (`192.168.1.10`):

For Ubuntu/Debian (`ufw`):
```bash
sudo ufw allow 7433/tcp
```

For RHEL/Fedora/Rocky (`firewall-cmd`):
```bash
sudo firewall-cmd --add-port=7433/tcp --permanent && sudo firewall-cmd --reload
```

---

## 4. Execution Order

### Step 1: Start Coordinator on Desktop
```bash
python3 -m cat_theo_machine.session --net --cycles 10 --config /etc/hyge/node_config.json
```

### Step 2: Start Worker on Laptop A
```bash
python3 -m cat_theo_machine.session --net --cycles 10 --config /etc/hyge/node_config.json
```

### Step 3: Start Worker on Laptop B
```bash
python3 -m cat_theo_machine.session --net --cycles 10 --config /etc/hyge/node_config.json
```

---

## 5. Verification Criteria

- [ ] All three nodes report the same head hash after 10 cycles
- [ ] Killing a laptop mid-cycle leaves the coordinator chain valid and the laptop converges on restart
- [ ] render_curator_report shows contributions from both worker CNs
