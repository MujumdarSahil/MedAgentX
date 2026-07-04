# MedAgentX

**The governance runtime for clinical AI (E-Doctor OS).**

> MedAgentX is a deterministic, governed, multi-agent clinical intelligence platform. It is not a diagnostic tool. It is the architectural layer that ensures every clinical AI recommendation has an enforced responsibility trail, a replayable audit log, and a non-bypassable human approval gate.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Paper: JMIR](https://img.shields.io/badge/Paper-JMIR%20Medical%20Informatics-orange)](https://jmir.org)
[![Status: Research](https://img.shields.io/badge/Status-Research-yellow)](EVALUATION.md)

---

## Clinical Safety

This system provides **clinical decision support only**. It does not diagnose, prescribe, or treat. All outputs carry a `requires_human_approval: true` flag enforced at the governance layer. The system is designed as CDS (Clinical Decision Support) software under FDA guidance — not as a medical device.

**Every output produced by MedAgentX is tagged with a Responsibility State (`AI_SUGGESTED → DOCTOR_VALIDATED → DOCTOR_OVERRIDDEN`) that is immutable, auditable, and enforced architecturally — not just by policy.**

---

## What MedAgentX Solves

Three problems that block clinical AI adoption in regulated environments:

### 1. Who is responsible when the AI is wrong?

The **Clinical Responsibility Firewall (CRF)** makes responsibility attribution a first-class architectural primitive — not a UI label. Every output carries a state tag that is:

- **Immutable**: Responsibility metadata cannot be silently rewritten after creation
- **Auditable**: State transitions are logged to an append-only Event Store
- **Enforced at the governance layer**: `requires_human_approval: true` is mandatory on agent outputs

### 2. Can you reconstruct what the AI recommended after an adverse event?

The **append-only Event Store** and **Replay Engine** enable reconstruction of prior workflow executions — including which agent produced what, which evidence was retrieved, and what responsibility state each output carried.

### 3. How do you enforce the same governance policy across all your clinical AI tools?

MedAgentX functions as a **governance runtime**. Domain agents (symptom structuring, diagnosis support, coding, risk scoring) plug into a shared workflow with one audit trail, one responsibility firewall, and one compliance interface.

---

## Architecture

MedAgentX is organized into layered packages. Core governance and orchestration live under `medagentx/core/`; domain agents, tools, and APIs wrap that runtime.

| Layer | Location | Description |
|-------|----------|-------------|
| **Governance** | `medagentx/governance/` | Governance Engine, safety rules, phrase-level output filtering |
| **Core runtime** | `medagentx/core/` | CRF, Event Store, Replay Engine, workflows, bounded persistence, CHIL, MCP registry |
| **Agents** | `medagentx/agents/` | Domain-specific ReAct agents (symptom, diagnosis support, coding, risk, guidelines, prescription review) |
| **Knowledge** | `medagentx/knowledge/` | Knowledge base, hybrid retrieval (FAISS + ChromaDB + BM25), medical coding |
| **Tools & MCP** | `medagentx/tools/` | Tool registry, MCP server integration, ICD-10 coding tools |
| **LLM** | `medagentx/models/llm_engine.py` | Multi-provider LLM abstraction (OpenAI, Anthropic, Groq, Gemini, Mistral, Cohere, Ollama, Perplexity) |
| **API** | `medagentx/api/server.py` | FastAPI REST server and static web UI |
| **UI** | `medagentx/ui/streamlit_app.py`, `ui/` | Streamlit dashboard and lightweight HTML/JS frontend |

The **Clinical Responsibility Firewall** sits between every agent output and clinical use. No output can reach clinical action without passing governance validation and carrying human-approval metadata.

For the full architectural specification, see [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/architecture.md](docs/architecture.md).

---

## Agents

| Agent | Module | Role |
|-------|--------|------|
| Symptom Analyzer | `symptom_analyzer.py` | Structures symptoms; does not diagnose |
| Diagnosis Support | `diagnosis_support.py` | Supportive reasoning only; no definitive diagnosis |
| Medical Coder | `medical_coder.py` | Maps findings to ICD-10/CPT suggestions |
| Risk Scorer | `risk_assessor.py` | Numeric risk scoring support; no treatment advice |
| Clinical Guideline | `clinical_guideline.py` | Retrieves and summarizes guideline context |
| Prescription Reviewer | `prescription_reviewer.py` | Reviews prescriptions under governance constraints |

The default API server registers Symptom Analyzer, Diagnosis Support, Medical Coder, and Risk Scorer out of the box.

---

## Evaluation

MedAgentX is evaluated on **governance enforcement, determinism, replay capability, human-approval enforcement, and audit completeness** — not diagnostic accuracy.

The current scenario suite contains **13 scenarios** across governance, adversarial, determinism, and evidence test categories under `evaluation/scenarios/`. Runners and statistical analysis live in `evaluation/runners/` and `evaluation/analysis/`.

| Property | What it measures |
|----------|-----------------|
| Governance enforcement | Refuses diagnostic/prescriptive outputs under adversarial prompts |
| Determinism | Non-LLM agents produce identical outputs for identical inputs |
| Replay capability | Event store replay reproduces CRF state sequences |
| Human approval | `requires_human_approval` present on every output |
| Audit completeness | Execution steps logged to the event store |

See [EVALUATION.md](EVALUATION.md) for methodology, reproduction instructions, and known limitations.

---

## Quick Start

### Prerequisites

- Python 3.10+
- API key(s) for at least one LLM provider (optional for deterministic paths; required for LLM-backed agents)

### Installation

```bash
git clone https://github.com/MujumdarSahil/MedAgentX.git
cd MedAgentX

# Create a virtual environment (do NOT commit this)
python -m venv venv
source venv/bin/activate     # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Install runtime dependencies
pip install -r requirements.txt

# Install dev + evaluation dependencies (optional)
pip install -r requirements-dev.txt
```

### Configuration

```bash
# Copy the example config
cp config/config.example.yaml config/config.yaml   # Linux/macOS
copy config\config.example.yaml config\config.yaml # Windows

# Set LLM API keys via environment variables (recommended)
# OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, etc.
```

Edit `config/config.yaml` for platform settings (default provider, temperature, governance flags, knowledge paths).

### Run the API Server

```bash
python run_server.py
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:8000/ |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/health |

### Run the Full Stack (API + Streamlit)

```bash
python run_streamlit.py
```

This starts the FastAPI backend (port 8000) and Streamlit UI (port 8501) together. Override ports with `MEDAGENTX_API_PORT` and `MEDAGENTX_UI_PORT`.

| Service | URL |
|---------|-----|
| Streamlit dashboard | http://localhost:8501 |
| API backend | http://localhost:8000 |

### Run the CLI Demo Workflow

```bash
python -m medagentx.main
```

Runs the recommendation workflow locally (symptom analysis → diagnosis support → coding) with trace output, deterministic replay, and evaluation logging.

### Verify Installation

```bash
curl http://localhost:8000/api/health
# {"status": "healthy", "platform": "MedAgentX"}
```

---

## API Overview

Key REST endpoints exposed by `medagentx/api/server.py`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/agents` | List registered agents |
| `POST` | `/api/agents` | Create a new agent |
| `POST` | `/api/agents/{agent_id}/execute` | Execute a task with an agent |
| `POST` | `/api/analyze-symptoms` | Run symptom analysis |
| `POST` | `/api/recommend` | Run the full recommendation workflow |
| `GET` | `/api/tools` | List registered tools |
| `GET` | `/api/workflows` | List available workflows |

Interactive documentation is available at `/docs` when the server is running.

---

## Running Evaluations

```bash
# Start the server first
python run_server.py

# Governance test runner (runs against local API)
python -m evaluation.runners.governance_test_runner \
  --api-url http://localhost:8000 \
  --scenarios-file evaluation/scenarios/governance_tests/scenarios.json \
  --output-dir evaluation/results/

# Determinism verification
python -m evaluation.runners.determinism_verifier \
  --workflow crf_transition \
  --input '{"current_state": "AI_SUGGESTED", "event": "DOCTOR_REVIEW_COMPLETE"}' \
  --runs 20

# Baseline comparison — GPT-4 vs MedAgentX (requires OPENAI_API_KEY)
python -m evaluation.runners.baseline_comparison \
  --scenarios-file evaluation/scenarios/governance_tests/scenarios.json \
  --reps 5
```

See [EVALUATION.md](EVALUATION.md) for complete reproduction instructions.

---

## Running Tests

```bash
# Unit tests (no server required)
pytest tests/unit/ -v

# CRF state machine tests
pytest tests/unit/test_crf.py -v

# Integration tests (placeholders; require live server — see EVALUATION.md)
pytest tests/integration/ -v -m integration
```

---

## Project Structure

```
MedAgentX/
├── medagentx/                  Core Python package
│   ├── agents/                 Domain-specific clinical agents
│   ├── core/                   CRF, event store, replay, workflows, CHIL, bounded store
│   ├── governance/             Governance engine and safety rules
│   ├── knowledge/              Knowledge base, retrieval, medical coding
│   ├── models/                 LLM engine abstraction
│   ├── tools/                  Tool registry, MCP server, example tools
│   ├── api/                    FastAPI server
│   ├── ui/                     Streamlit application
│   ├── main.py                 CLI demo entry point
│   └── utils/                  Config and logging helpers
├── evaluation/                 Evaluation framework (Phase 2)
│   ├── runners/                Governance, determinism, baseline runners
│   ├── scenarios/              JSON test scenarios (governance, adversarial, etc.)
│   ├── analysis/               Statistical analysis and reporting
│   └── results/                Output directory (gitignored)
├── tests/                      Unit and integration tests
├── docs/                       Documentation
├── paper/                      LaTeX paper and figures
├── ui/                         Static web frontend (HTML/CSS/JS)
├── config/                     Configuration files
├── examples/                   Usage examples
├── scripts/                    Utility scripts
├── ARCHITECTURE.md             Platform architecture (v2.0)
├── EVALUATION.md               Evaluation reproduction guide
├── CITATION.cff                Academic citation metadata
├── run_server.py               FastAPI launcher
├── run_streamlit.py            Unified API + Streamlit launcher
└── requirements.txt            Runtime dependencies
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [EVALUATION.md](EVALUATION.md) | Complete evaluation framework and reproduction guide |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Platform architecture (v2.0) |
| [docs/architecture.md](docs/architecture.md) | Detailed architecture documentation |
| [docs/QUICK_START.md](docs/QUICK_START.md) | Quick start guide |
| [docs/UI_GUIDE.md](docs/UI_GUIDE.md) | UI usage guide |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version history |
| [docs/agents.md](docs/agents.md) | Agent documentation |
| [docs/safety.md](docs/safety.md) | Safety and governance documentation |
| [docs/mcp_tools.md](docs/mcp_tools.md) | MCP tool registry documentation |
| [docs/evaluation.md](docs/evaluation.md) | Evaluation overview |

---

## Research

**Paper:** *"Designing Deterministic and Governed Multi-Agent Systems for Clinical Intelligence Without Autonomous Diagnosis: The MedAgentX Architecture"*  
**Journal:** JMIR Medical Informatics (under review)  
**Author:** Sahil Mujumdar, Tobox Ventures

**Citation:**

```bibtex
@software{mujumdar2025medagentx,
  author    = {Mujumdar, Sahil},
  title     = {MedAgentX: A Governance-First Deterministic Multi-Agent Clinical Intelligence Platform},
  year      = {2025},
  url       = {https://github.com/MujumdarSahil/MedAgentX},
  license   = {MIT}
}
```

For a citation format compatible with GitHub, Zenodo, and academic software citation standards, see [CITATION.cff](CITATION.cff).

**Reproduce the evaluation:** See [EVALUATION.md](EVALUATION.md)

---

## Contributing

This repository is maintained for academic research and patent documentation purposes. Issue reports and evaluation discrepancies should be filed as GitHub Issues.

- Governance violations discovered during evaluation: label `governance-finding`
- Evaluation result discrepancies: label `evaluation-discrepancy`
- General bugs: label `bug`

---

## License

MIT License. See [LICENSE](LICENSE).

**Note on clinical deployment:** The clinical decision support capabilities of MedAgentX are subject to applicable medical device and software regulations in your jurisdiction. This software is provided for research and evaluation purposes. Deployment in clinical settings requires appropriate regulatory review under applicable frameworks (FDA Software as a Medical Device guidance, EU MDR, or equivalent).

MedAgentX is designed as Clinical Decision Support (CDS) software — a category that provides information to clinicians to support their decisions, not to make decisions autonomously. All outputs require clinician review and approval before clinical use. The `requires_human_approval: true` flag enforced in the governance layer reflects this design intent.

---

*MedAgentX v2.0.0 | Research | Tobox Ventures, Mumbai, India*
