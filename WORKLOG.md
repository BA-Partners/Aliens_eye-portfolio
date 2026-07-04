# Worklog

## router_port_verify.py
CLI port-forward verifier.
- TCP + HTTP probes with retries and backoff.
- UPnP/NAT-PMP best-effort discovery/mapping.
- No secrets required.
- Verified against TRON port set: 18190, 18191, 8545, 8060, 50051, 50052.

## tron_grpc_compat_preflight.py
Offline compatibility preflight.
- TLV encode/decode path verified.
- Deterministic pass/fail reporting.
- Result: 12/12 cases pass offline.

## tron_seednode_handshake.py
Seed node handshake probing.
- Live probe for 50100/50101.
- Used to validate routing and firewall behavior.

## tron_watchdog.js
Lightweight node monitor.
- HTTP/TCP checks with timeout/reconnect handling.
- Container reset tolerance to reduce false positives.

## tplink_portforward_guide.md
Non-UPnP router workflow.
- Keyboard-driven port-forward entry for TP-Link EC225-G5.
- Usable without storing credentials.

## Portfolio page
`portfolio_automation_services.html`
- Single-page service portfolio.
- Safe for public sharing: no secrets embedded.
- Covers Type A (script delivery) and Type B (integration/hourly) engagements.
