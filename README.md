# Aliens_eye — Automation Services + Tooling

I ship portable automation, verification, and deployment artifacts for engineering workflows.

## Services

### Scoped automation script
One concrete script, README, and runbook. Typical scope: port-forward verifier, node health monitor, local LLM startup/tuning script, or router diagnostics.

### Integration + support
Ongoing tuning, monitoring, or Docker/PM2 packaging for an existing artifact.

## Pricing

- Type A: fixed $80-$220, 1 scoped script, 24-72h
- Type B: $40-$90/hr, integration, tuning, and support

## Deliverables

- CLI or service artifact
- README with install and run steps
- retry/timeout defaults and runbook
- 7-day follow-up window

## Proof

- `router_port_verify.py` — TCP/HTTP verifier with retries
- `tron_grpc_compat_preflight.py` — offline gRPC/TLV readiness tests
- `tron_watchdog.js` — lightweight node monitor
- `tplink_portforward_guide.md` — router port-forward flow guide

## Portfolio links

- GitHub repo: https://github.com/BA-Partners/Aliens_eye-portfolio
- Netlify Drop: http://tourmaline-pie-a6e32b.netlify.app
- GitHub Pages: https://ba-partners.github.io/Aliens_eye-portfolio/

## Outreach assets

- `fiverr_gig_type_a.md` — fixed-price gig copy
- `fiverr_gig_type_b.md` — hourly gig copy
- `fiverr_buyer_request_variants.md` — buyer-request replies
- `first_month_funnel.md` — month-1 traffic, conversion, orders target

## Contact

- Email: info@hsjpatners.com
- Telegram: @atao66666666
- GitHub: https://github.com/arxhr007

## Policy

- No secrets or credentials stored in repos
- No browser UI scraping or password entry
- Credentials are referenced by placeholders only

---

# Aliens Eye (OSINT tooling)

This repo also contains the Aliens Eye username scanner under a separate track.

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
