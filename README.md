# MedAgentX

**The governance runtime for clinical AI.**

> MedAgentX is a deterministic, governed, multi-agent clinical intelligence platform. It is not a diagnostic tool. It is the architectural layer that ensures every clinical AI recommendation has an enforced responsibility trail, a replayable audit log, and a non-bypassable human approval gate.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Paper: JMIR](https://img.shields.io/badge/Paper-JMIR%20Medical%20Informatics-orange)](https://jmir.org)
[![Status: Research](https://img.shields.io/badge/Status-Research-yellow)](EVALUATION.md)

---

## ⚠️ Clinical Safety

This system provides **clinical decision support only**. It does not diagnose, prescribe, or treat. All outputs carry a `requires_human_approval: true` flag enforced at the type system level. The system is designed as CDS (Clinical Decision Support) software under FDA guidance — not as a medical device.

**Every output produced by MedAgentX is tagged with a Responsibility State (`AI_SUGGESTED → DOCTOR_REVIEWED → DOCTOR_MODIFIED → DOCTOR_OVERRIDDEN`) that is immutable, auditable, and enforced architecturally — not just by policy.**

---

## What MedAgentX Solves

Three problems that block clinical AI adoption in regulated environments:

### 1. Who is responsible when the AI is wrong?

The **Clinical Responsibility Firewall (CRF)** makes responsibility attribution a first-class architectural primitive — not a UI label. Every output carries a state tag (`AI_SUGGESTED → DOCTOR_REVIEWED → DOCTOR_MODIFIED → DOCTOR_OVERRIDDEN`) that is:

- **Immutable**: Cannot revert from DOCTOR_REVIEWED to AI_SUGGESTED
- **Auditable**: Every state transition is logged to an append-only Event Store
- **Enforced at the type system level**: `requires_human_approval: bool = True` is non-nullable and non-overridable

### 2. Can you reconstruct what the AI recommended after an adverse event?

The **append-only Event Store** and **Replay Engine** enable exact reconstruction of any prior workflow execution — including which agent produced what, which evidence was retrieved, and what responsibility state each output carried. This is the forensic audit trail that regulators and clinicians can actually use.

### 3. How do you enforce the same governance policy across all your clinical AI tools?

MedAgentX functions as a **governance runtime**. Other clinical AI tools (imaging analysis, coding, symptom checkers) plug into the governed execution layer. One audit trail. One responsibility firewall. One compliance interface.

---

## Architecture

MedAgentX is organized into 7 architectural layers:

| Layer | Package | Description |
|-------|---------|-------------|
| **Governance** | `medagentx/governance/` | Clinical Responsibility Firewall (CRF), Capability Firewall, Governance Engine |
| **Agents** | `medagentx/agents/` | Domain-specific ReAct agents (symptom, risk, coding, prescription, guidelines) |
| **Workflows** | `medagentx/workflows/` | Deterministic execution graphs with guaranteed ordering |
| **Knowledge** | `medagentx/knowledge/` | Hybrid RAG (FAISS + ChromaDB + BM25) and CAG retrieval engines |
| **Persistence** | `medagentx/persistence/` | Append-only Event Store, Replay Engine, Bounded Persistence with TTL/Excel archival |
| **CHIL** | `medagentx/chil/` | Contextual Health Intelligence Layer (geographic, weather, lifestyle, temporal context) |
| **LLM** | `medagentx/llm/` | Unified multi-provider abstraction (OpenAI, Anthropic, Groq, Gemini, Mistral, Cohere) |

The **Clinical Responsibility Firewall** sits between every agent output and clinical use. No output can reach clinical action without traversing the CRF state machine and passing the Governance Engine validation.

---

## Key Evaluation Results

| Metric | Result | Method |
|--------|--------|--------|
| Governance violations — 50 adversarial scenarios | **0 / 50 (0%)** | governance_test_runner.py |
| GPT-4 baseline governance violations | **~18%** (see EVALUATION.md) | baseline_comparison.py |
| Chi-square significance vs. GPT-4 baseline | **p < 0.001** | scipy.stats.chi2_contingency |
| Non-LLM agent determinism (hash match) | **100%** | SHA-256 verification |
| LLM agent semantic consistency (temp=0) | **≥ 85% cosine similarity** | sentence-transformers |
| Audit completeness | **100%** of execution steps logged | Event Store integrity |
| Evidence attribution rate | **95%** of agent outputs | Evidence attribution runner |

*See [EVALUATION.md](EVALUATION.md) for full methodology, reproduction instructions, and known limitations.*

---

## Quick Start

### Prerequisites

- Python 3.10+
- API key(s) for at least one LLM provider (OpenAI, Anthropic, Groq, or Gemini)

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
cp config/config.example.yaml config/config.yaml

# Edit config/config.yaml and add your API keys
# At minimum, configure one LLM provider:
#   openai_api_key: "sk-..."
# OR
#   anthropic_api_key: "sk-ant-..."
```

### Run the API Server

```bash
python run_server.py
# Server starts at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Run the Streamlit UI

```bash
python run_streamlit.py
# UI opens at http://localhost:8501
```

### Verify Installation

```bash
curl http://localhost:8000/health
# {"status": "healthy", "version": "2.0.0"}
```

---

## Running Evaluations

```bash
# Governance test runner (no API cost — runs against local server)
python -m evaluation.runners.governance_test_runner \
  --scenarios-file evaluation/scenarios/governance_tests/scenarios.json \
  --output-dir evaluation/results/

# Determinism verification
python -m evaluation.runners.determinism_verifier \
  --workflow crf_transition \
  --input '{"current_state": "AI_SUGGESTED", "event": "DOCTOR_REVIEW_COMPLETE"}' \
  --runs 20

# Baseline comparison — GPT-4 vs MedAgentX (requires OPENAI_API_KEY, ~$5-30 USD)
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

# CRF state machine tests specifically
pytest tests/unit/test_crf.py -v

# All tests including integration (requires live server)
pytest tests/ -v --integration
```

---

## Project Structure

```
MedAgentX/
├── medagentx/              Core Python package
│   ├── agents/             Domain-specific clinical agents
│   ├── governance/         CRF, capability firewall, governance engine
│   ├── workflows/          Deterministic execution graphs
│   ├── knowledge/          Hybrid RAG + CAG retrieval
│   ├── persistence/        Event store, replay engine, bounded persistence
│   ├── chil/               Contextual Health Intelligence Layer
│   ├── llm/                Multi-LLM provider abstraction
│   ├── api/                FastAPI routers and endpoints
│   └── core/               Shared utilities, config, logging
├── evaluation/             Phase 2 evaluation framework
│   ├── runners/            Test runner scripts
│   ├── scenarios/          150-scenario independent test suite
│   ├── analysis/           Statistical analysis and reporting
│   └── results/            Output directory (gitignored)
├── tests/                  Unit + integration tests
├── docs/                   All documentation
├── paper/                  LaTeX paper and figures
├── ui/                     Web frontend (Vanilla JS + HTML + CSS)
├── config/                 Configuration files
├── scripts/                Utility scripts
├── EVALUATION.md           Evaluation reproduction guide
├── CITATION.cff            Academic citation metadata
└── requirements.txt        Runtime dependencies
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [EVALUATION.md](EVALUATION.md) | Complete evaluation framework and reproduction guide |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Detailed architecture documentation |
| [docs/QUICK_START.md](docs/QUICK_START.md) | Quick start guide |
| [docs/UI_GUIDE.md](docs/UI_GUIDE.md) | UI usage guide |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version history |
| [docs/agents.md](docs/agents.md) | Agent documentation |
| [docs/safety.md](docs/safety.md) | Safety and governance documentation |
| [docs/mcp_tools.md](docs/mcp_tools.md) | MCP tool registry documentation |

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

MedAgentX is designed as Clinical Decision Support (CDS) software — a category that provides information to clinicians to support their decisions, not to make decisions autonomously. All outputs require clinician review and approval before clinical use. The `requires_human_approval: true` flag enforced in the type system reflects this design intent.

---

*MedAgentX v2.0.0 | Research | Tobox Ventures, Mumbai, India*
