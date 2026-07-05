# MedAgentX Observability — Self-hosted Langfuse Integration

This document describes how to stand up and use the self-hosted [Langfuse](https://langfuse.com) observability backend for MedAgentX.  All traces, governance events, CRF decisions, and LLM generations are stored locally — **no data leaves your environment**.

---

## Architecture Overview

```
MedAgentX FastAPI Server
        │
        │  OpenTelemetry spans
        ▼
 OTel TracerProvider
  ┌─────┴──────────────────────────┐
  │                                │
  │  ConsoleSpanExporter           │  PiiMaskingSpanProcessor
  │  (always on, local debug)      │        │
  │                                │        ▼
  └────────────────────────────────┘  LangfuseSpanExporter
                                            │
                                            │  OTLP / REST
                                            ▼
                                   Langfuse Server :3000
                                   ┌──────────────────┐
                                   │  Postgres :5432  │  ← projects, users, prompts
                                   │  ClickHouse :8123│  ← traces, events, scores
                                   └──────────────────┘
```

The `PiiMaskingSpanProcessor` sits in front of the Langfuse exporter and replaces values of PII-sensitive span attributes with `[REDACTED]` before they leave the process.

---

## 1. Start the Langfuse Stack

### Prerequisites
- Docker ≥ 24 with the Compose plugin (`docker compose version`)
- Ports 3000, 5432, 8123, 9000 free locally

### Start

```bash
# From the MedAgentX repository root:
docker compose -f docker-compose.langfuse.yml up -d
```

Wait ~30 seconds for ClickHouse to be ready, then verify:

```bash
docker compose -f docker-compose.langfuse.yml ps
# All three services should show "healthy" or "running"
```

### Stop / clean up

```bash
docker compose -f docker-compose.langfuse.yml down          # stop, keep volumes
docker compose -f docker-compose.langfuse.yml down -v       # stop + delete all data
```

---

## 2. First-Run Setup

1. Open **http://localhost:3000** in your browser.
2. Log in with the bootstrap credentials:
   - Email: `admin@medagentx.local` (or `LANGFUSE_ADMIN_EMAIL` value from `.env`)
   - Password: `changeme-admin-pw` (or `LANGFUSE_ADMIN_PASSWORD`)
3. The project **MedAgentX Clinical AI** is pre-created by the bootstrap env vars.
4. Go to **Settings → API Keys → Create new key**.
5. Copy the **public key** (`pk-lf-...`) and **secret key** (`sk-lf-...`).

> **Important**: Change the bootstrap admin password immediately after first login in any shared or production deployment.

---

## 3. Configure MedAgentX to Send Traces

Add the following to your `.env` file (copy from `.env.example` if you haven't already):

```env
LANGFUSE_PUBLIC_KEY=pk-lf-<your-key>
LANGFUSE_SECRET_KEY=sk-lf-<your-key>
LANGFUSE_HOST=http://localhost:3000
```

Restart the MedAgentX server:

```bash
uvicorn medagentx.api.server:app --reload
```

You should see a log line:

```
INFO  Langfuse OTel exporter initialised (host=http://localhost:3000, project_key=pk-lf-xx...)
```

---

## 4. What Gets Traced

| Span name | Attributes | Langfuse filter |
|---|---|---|
| `http_POST_/api/agents/{id}/execute` | `http.method`, `http.url`, `http.status_code` | All HTTP requests |
| `agent_{id}_run` | `agent_id`, `task_hash`, `agent.type`, `confidence` | Per-agent execution |
| `llm.{id}.generation` | `llm.model`, `llm.usage.prompt_tokens`, `llm.usage.completion_tokens`, `llm.confidence` | LLM token usage |
| `governance.input_scan` | `governance=True`, `governance.agent_id`, `governance.pii_detected`, `governance.injection_detected`, `governance.degraded_mode` | Input guard decisions |
| `governance.output_block` | `governance=True`, `governance.blocked_phrase`, `governance.approval_required` | Blocked outputs |
| `governance.output_check` | `governance=True`, `governance.result`, `governance.approval_required` | Passed outputs |
| `governance.crf_enforcement` | `governance=True`, `crf.tag`, `crf.agent_id`, `crf.forged_tag_rejected` | CRF decisions |
| `governance.eval_scenario` | `governance=True`, `eval.scenario_id`, `eval.violation_type`, `eval.violation_detected`, `eval.latency_ms` | Evaluation run results |
| `governance_enforce` | `governance_violated`, `governance_violation_reason` | GovernanceEngine enforcement |

### Filtering governance events in Langfuse

In the Langfuse **Traces** view:
1. Click **+ Filter**
2. Add attribute filter: `governance` = `true`
3. Optionally add: `crf.forged_tag_rejected` = `true` to see only forgery attempts

---

## 5. Trace ID Correlation

Every OpenTelemetry trace ID is propagated through the full request stack.  To correlate a specific API request with its Langfuse trace:

1. Make an API call and note the HTTP response headers — look for `traceparent`.
2. Extract the trace ID (second segment of the W3C `traceparent` header).
3. Search in Langfuse: **Traces → search by trace ID**.

Alternatively, the MedAgentX structured logs (`logs/medagentx.log`) include `trace_id` in JSON log records when running under an active OTel span.

---

## 6. PII Safety

All span attributes pass through `PiiMaskingSpanProcessor` before export to Langfuse.  The following attribute keys are automatically redacted to `[REDACTED]`:

| Exact key matches | Substring patterns |
|---|---|
| `patient_id`, `mrn`, `medical_record_number` | keys containing `pii_` |
| `dob`, `date_of_birth` | keys containing `_pii` |
| `ssn`, `social_security_number`, `nhs_number` | keys containing `patient_` |
| `email`, `phone`, `phone_number` | keys containing `_ssn`, `_mrn` |
| `address`, `full_name`, `first_name`, `last_name` | |

Raw task text is **never** stored as a span attribute.  The `task_hash` attribute is a truncated SHA-256 of the task string — useful for correlation but non-reversible.

See [cybersecurity.md](cybersecurity.md) § 6 for the full PII control policy.

---

## 7. Production Hardening Checklist

- [ ] Replace all `changeme-*` secrets in `.env` with cryptographically random values
- [ ] Set `NEXTAUTH_URL` to the public hostname of your Langfuse server
- [ ] Place Langfuse behind an HTTPS reverse proxy (nginx/Caddy/Traefik)
- [ ] Restrict ClickHouse and Postgres ports to the internal Docker network (no host exposure)
- [ ] Enable Langfuse RBAC — create read-only roles for dashboard viewers
- [ ] Rotate Langfuse API keys after initial setup
- [ ] Set retention policies on ClickHouse tables to comply with your data governance requirements
- [ ] Back up the Langfuse Postgres volume per your organisation's backup schedule
