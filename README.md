# Aliens_eye — Automation Services + Tooling

## Available for hire: automation scripts and local node tooling

I ship portable automation, verification, and deployment artifacts for engineering workflows.

- **Type A:** $80-$220 fixed — scoped script + README + runbook
- **Type B:** $40-$90/hr — integration, tuning, and support

Response time: usually within hours. Typical delivery: 24-72h for scoped scripts.

---

## What I deliver

### 1. Port-forward verifier
TCP + HTTP probes with retries, backoff, UPnP/NAT-PMP checks, and router discovery.

### 2. Node health monitor
Lightweight monitor with container-reset tolerance, timeout tuning, and cleanup logic.

### 3. Local LLM deploy helper
Startup scripts and Metal tuning for `llama.cpp` on Apple Silicon.

### 4. Router diagnostics
Keyboard-driven router port-forward flow, router audits, and manual mapping checklists.

## Working deliverables

- `router_port_verify.py` — TCP/HTTP verifier with retries
- `tron_grpc_compat_preflight.py` — offline gRPC/TLV tests
- `tron_watchdog.js` — node monitor with timeout/reconnect logic
- `tplink_portforward_guide.md` — router port-forward flow guide

## Portfolio and proof

Live portfolio: http://tourmaline-pie-a6e32b.netlify.app  
Password: `My-Drop-Site`

## Safety and policy

- No secrets stored in repos
- No browser UI scraping or password entry
- Credentials are referenced by placeholders only

## Contact

- Email: info@hsjpatners.com
- Telegram: @atao66666666
- GitHub: https://github.com/arxhr007

---

# Aliens Eye (OSINT tooling)

This repo also contains the Aliens Eye username scanner.

## Highlights

- **840+ platforms** scanned asynchronously in seconds
- **ML + heuristic detection**
- **Modern terminal UI**
- **Proxy & Tor support**
- **Reports** in JSON, CSV, HTML, and Markdown

## Install

```bash
pip install aliens-eye
```

## Usage

```bash
aliens_eye username
aliens_eye username1 username2 --site github,reddit --no-nsfw --format all
```
