# 🧠 MedAgentX (E-Doctor OS)

**A Programmable Agentic AI + GenAI Platform for Clinical Decision Support**

MedAgentX enables doctors, clinics, healthcare startups, and researchers to build custom AI-powered medical recommendation engines using agents, tools, MCP servers, and governance policies.

## ⚠️ CLINICAL SAFETY DISCLAIMER

**IMPORTANT:** This system provides **clinical decision support**, NOT autonomous diagnosis.

- All outputs are **recommendations**, not final decisions
- Human (doctor) approval is **mandatory** before any diagnosis or treatment suggestion
- The system enforces this at the architecture level

## 🏗️ Architecture Overview

MedAgentX is built with 7 core layers:

1. **Agentic Orchestration Layer** - ReAct, MRKL, multi-agent collaboration
2. **Clinical Intelligence & Recommendation Layer** - E-Doctor workflows
3. **Knowledge, Retrieval & Medical Memory Layer** - Advanced RAG techniques
4. **Model & Training Layer** - GenAI models, fine-tuning, optimization
5. **Safety, Governance & Clinical Compliance Layer** - Safety guardrails
6. **Tool / MCP Builder Layer** - User-creatable tools
7. **API, UI & Developer Platform Layer** - APIs and interfaces

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize configuration (optional)
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings

# Run the web server with UI
python run_server.py

# Then open your browser to:
# - UI: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## 🖥️ Web UI

MedAgentX includes a modern web interface for:
- Symptom analysis
- Viewing recommendations
- Agent management
- Real-time clinical decision support

Access the UI at `http://localhost:8000` when the server is running.

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [Agent Development Guide](docs/agents.md)
- [MCP Tool Development](docs/mcp_tools.md)
- [Safety & Compliance](docs/safety.md)

## 📄 License

Proprietary - MedAgentX Platform

