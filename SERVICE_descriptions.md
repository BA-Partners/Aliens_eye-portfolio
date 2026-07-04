# Service Descriptions

## 1. Automated Port-Forward Verification Script
I deliver a CLI tool that verifies router port forwarding for TCP and HTTP endpoints. The tool includes retry, timeout backoff, and router discovery. Safety baseline: no browser UI password storage, no persistent secrets. Typical ports in scope: 8545, 18190, 18191, 50051, 50052, 50100, 50101. I provide a runbook plus a 7-day follow-up window.

## 2. Docker Compose + Local Node Monitor
I package a reproducible node stack with a health monitor that probes HTTP and gRPC endpoints. Deliverables: docker-compose file, monitor script, threshold tuning, and validation commands. Designed for low-noise alerts and reduced false positives from transient container restarts.

## 3. Local LLM Automation Helper
I set up a scripted local-model workflow with a hardware-aware configuration. Deliverables: startup script, resource-limit tuning notes, prompt helper scripts, and a verification checklist. Safe by default: credentials and keys are never stored in the repo.
