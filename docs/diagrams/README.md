# MedAgentX Publication Diagrams

This directory contains publication-quality diagrams, charts, and visualizations for journal and paper submissions.

## Generated Diagrams

### 1. Architecture Diagram (`01_architecture_diagram`)
Shows the complete 7-layer system architecture of MedAgentX v1.7:
- Layer 7: API, UI & Developer Platform
- Layer 6: Tool / MCP Builder
- Layer 5: Safety, Governance & Clinical Compliance
- Layer 4: Knowledge, Retrieval & Medical Memory
- Layer 3: Clinical Intelligence & Recommendation
- Layer 2: Agentic Orchestration
- Layer 1: Model & Training

**Use Case**: System architecture overview, technical documentation, system design papers

### 2. Radar Comparison Chart (`02_radar_comparison`)
Multi-dimensional feature comparison showing MedAgentX vs competitors:
- IBM Watson Health
- Epic DxPlain
- Isabel Healthcare
- WebMD Symptom Checker

**Features Compared**:
- Multi-Agent Architecture
- Adaptive Memory
- Evidence-Based Reasoning
- Human Approval
- Deterministic Traces
- Medical Coding
- Risk Scoring
- Open Source
- Customizability
- Embeddings Support

**Use Case**: Feature comparison papers, competitive analysis, system evaluation

### 3. Performance Comparison Charts (`03_performance_comparison`)
Four-panel comparison showing MedAgentX performance metrics:

**Panel 1: Accuracy Metrics**
- Symptom Matching Accuracy
- ICD-10 Code Accuracy
- Risk Score Correlation
- Evidence Relevance

**Panel 2: Speed Performance**
- Symptom Analysis time
- Full Workflow time
- Similarity Search time
- Trace Replay time

**Panel 3: Safety & Governance Metrics**
- Human Approval Rate
- Governance Blocks
- Audit Log Coverage
- Trace Completeness

**Panel 4: Improvement Percentage**
- Overall improvement over industry average

**Use Case**: Performance evaluation papers, benchmarking studies, system validation

### 4. Feature Comparison Matrix (`04_feature_matrix`)
Heatmap showing detailed feature support across all systems:
- Green = Full Support
- Yellow = Partial/Limited Support
- Red = Not Available

**Use Case**: Quick reference comparison, feature analysis, system selection guides

### 5. Workflow Diagram (`05_workflow_diagram`)
Complete data flow and agent interaction workflow:
- User Input → Symptom Analyzer, Diagnosis Support, Risk Scorer
- Knowledge Base & Adaptive Memory integration
- Medical Coder aggregation
- Governance Engine safety checks
- Human Approval Gate (mandatory)
- Final Output with evidence and trace

**Use Case**: Process documentation, workflow papers, system operation guides

## File Formats

Each diagram is available in two formats:
- **PNG**: High-resolution (300 DPI) for digital viewing and presentations
- **PDF**: Vector format for publication-quality printing and journal submission

## Usage in Publications

### For Journal Papers:
- Use PDF versions for submission (vector graphics preferred)
- Include captions describing each diagram
- Reference in text: "Figure 1: System Architecture" etc.

### For Presentations:
- Use PNG versions for slides
- Ensure sufficient resolution (300 DPI minimum)
- Consider color accessibility (diagrams use colorblind-friendly palettes)

### For Documentation:
- Both formats available for flexibility
- PNG for web/online documentation
- PDF for printable documentation

## Regenerating Diagrams

To regenerate all diagrams:

```bash
python scripts/generate_diagrams.py
```

**Requirements**:
- Python 3.10+
- matplotlib
- seaborn
- numpy

## Customization

The diagram generation script (`scripts/generate_diagrams.py`) can be customized to:
- Adjust colors and styles
- Modify data values
- Add/remove systems or features
- Change diagram layouts

## Citation

When using these diagrams in publications, please cite:

```
MedAgentX v1.7: A Multi-Agent Clinical Decision Support System
[Your Paper Title]
[Your Authors]
[Publication Venue]
```

## Notes

- All diagrams use publication-quality settings (300 DPI, serif fonts)
- Color schemes are designed to be colorblind-friendly
- Diagrams follow academic paper formatting standards
- Text sizes optimized for readability in both digital and print formats

