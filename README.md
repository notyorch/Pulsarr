# Pulsarr

<p align="center">
  <img src="logo/pulsarr-wordmark.svg" alt="Pulsarr wordmark" width="520" />
</p>

Pulsarr is a real-time event relay for security teams, routing alerts from systems like Wazuh and Shuffle into human response channels.

Detect. Route. Respond.

[![Python](https://img.shields.io/badge/Python-3.8%2B-2A3047?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Event%20Relay-111420?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Telegram](https://img.shields.io/badge/Destination-Telegram-4FC9E0?style=flat-square&logo=telegram&logoColor=0A0D14)](https://core.telegram.org/bots/api)
[![Webhooks](https://img.shields.io/badge/Input-Webhook-7C6FF7?style=flat-square)](#architecture-flow)
[![Wazuh](https://img.shields.io/badge/Wazuh-Source-5548D9?style=flat-square)](https://wazuh.com/)
[![Shuffle](https://img.shields.io/badge/Shuffle-Source-3D35B0?style=flat-square)](https://shuffler.io/)
[![Status](https://img.shields.io/badge/Status-Early%20Stage-161A2C?style=flat-square)](#roadmap-direction)

## Brand Note

The attack happened. The log exists. The question is whether it reached the right human in time.

Pulsarr is not a SIEM.
Pulsarr is not a compliance platform.
Pulsarr is the relay.
The channel between your infrastructure and the humans defending it.

## What Pulsarr Is

- A webhook-driven alert routing service.
- A normalization and rendering layer for incident payloads.
- A deterministic bridge from detection systems to response channels.
- A backend-first foundation for future multi-destination event routing.

## Current Capabilities

- Receives JSON events via POST to /alert.
- Protects the endpoint with API key validation.
- Normalizes minimum and enriched payload shapes.
- Renders structured, readable Telegram messages.
- Supports HTML-safe output with escaping and truncation for long logs.
- Exposes health endpoint and production-friendly deployment paths.

Telegram is the first destination implemented, not the final one.

## Architecture Flow

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#161A2C",
    "primaryTextColor": "#E2E8F0",
    "primaryBorderColor": "#7C6FF7",
    "lineColor": "#4FC9E0",
    "secondaryColor": "#111420",
    "tertiaryColor": "#0A0D14",
    "background": "#0A0D14",
    "mainBkg": "#161A2C",
    "secondBkg": "#111420",
    "clusterBkg": "#111420",
    "clusterBorder": "#2A3047",
    "fontFamily": "Inter"
  }
}}%%

flowchart LR

    %% SOURCES
    subgraph SOURCES["Detection Sources"]
        WZ["Wazuh<br/>SIEM / EDR Events"]
        SH["Shuffle<br/>SOAR Playbooks"]
        AU["Custom Automations<br/>n8n · Scripts · APIs"]
    end

    %% INGEST
    WH["Webhook Ingress<br/>Event Intake Layer"]

    %% CORE
    subgraph PULSARR["Pulsarr Event Relay"]
        NR["Normalize<br/>Parse · Enrich · Deduplicate"]
        RD["Render<br/>Human-readable alert formatting"]
        RT["Route<br/>Priority · Escalation · Delivery"]
    end

    %% OUTPUT
    AL["/alert"]
    TG["Telegram<br/>Human Response Channel"]

    %% FLOW
    WZ --> WH
    SH --> WH
    AU --> WH

    WH --> NR
    NR --> RD
    RD --> RT

    RT --> AL
    AL --> TG

    %% STYLES
    classDef source fill:#111420,stroke:#4FC9E0,color:#E2E8F0,stroke-width:1.5px;
    classDef core fill:#161A2C,stroke:#7C6FF7,color:#E2E8F0,stroke-width:2px;
    classDef output fill:#1E2435,stroke:#A99BFF,color:#E2E8F0,stroke-width:1.5px;
    classDef accent fill:#0E2435,stroke:#17A8CC,color:#E0F7FF,stroke-width:2px;

    class WZ,SH,AU source;
    class WH,NR,RD,RT core;
    class AL accent;
    class TG output;
```

Typical deployment today:
Wazuh + Shuffle + custom automations -> Pulsarr /alert -> Telegram human response channel

## Documentation Brand Tokens

These tokens are for docs and visual consistency while the frontend does not exist yet.

- Background: #0A0D14
- Surfaces: #111420, #161A2C, #1E2435, #2A3047
- Brand violet: #7C6FF7
- Violet support: #5548D9, #3D35B0, #A99BFF, #E2DEFF
- Signal cyan: #4FC9E0
- Conceptual type pairing: Inter (UI/headings) and JetBrains Mono (metadata)

## Quick Start

### Option 1: Installer Script

```bash
./install.sh
```

### Option 2: Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then set at least these values in .env:

- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- API_KEY

Run locally:

```bash
./run.sh
```

Health check:

```bash
curl http://localhost:8000/health
```

## API Surface

### POST /alert

Headers:

- Content-Type: application/json
- X-API-Key: your API key (when API_KEY is configured)

Minimum payload:

```json
{
  "message": "SSH auth failures detected"
}
```

Enriched example:

```json
{
  "message": "Multiple SSH authentication failures detected",
  "source": "wazuh",
  "orchestrator": "shuffle",
  "severity": "high",
  "level": 9,
  "rule_id": "5716",
  "agent": "servidor-web-01",
  "agent_ip": "192.168.10.50",
  "target_user": "root",
  "source_ip": "203.0.113.78",
  "source_port": "54321",
  "decoder": "sshd",
  "log_source": "/var/log/auth.log",
  "full_log": "May 15 14:32:18 servidor-web-01 sshd[12345]: Failed password for root from 203.0.113.78 port 54321 ssh2",
  "event_type": "SSH authentication failure",
  "affected_endpoint": "/ssh",
  "workflow": "telegram-test"
}
```

## Integration Example (Wazuh + Shuffle)

```bash
curl -X POST http://localhost:8000/alert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "Multiple SSH authentication failures detected",
    "source": "wazuh",
    "orchestrator": "shuffle",
    "severity": "high",
    "rule_id": "5716",
    "agent": "servidor-web-01"
  }'
```

## Environment Variables

Required:

- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

Recommended:

- API_KEY

Operational:

- HOST (default 0.0.0.0)
- PORT (default 8000)
- LOG_LEVEL (default INFO)
- INCLUDE_RAW_JSON (default false)
- TELEGRAM_PARSE_MODE (kept for compatibility)
- GUNICORN_WORKERS (default 3)

## Deployment Notes

- Systemd unit file is currently named systemd/telegram-alert-sender.service for compatibility with existing setups.
- Docker Compose currently keeps a compatibility service key name.
- Operational names can be migrated in a dedicated deployment migration step later.

## Roadmap Direction

- Configurable sources (beyond current webhook conventions)
- Mapping engine for source-specific normalization
- Template editor for destination-specific rendering
- Multiple destinations (Telegram first, then Slack/Teams/email/webhooks)
- Frontend/admin panel for route management and observability

## Security and Operations

- Use strong API keys and rotate them.
- Keep .env out of version control.
- Restrict source IPs when possible.
- Prefer reverse-proxy TLS termination in production.

## License

MIT. See LICENSE.
