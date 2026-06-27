# MedAgentX Web UI Guide

## Overview

MedAgentX includes a modern, responsive web interface built with:
- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Design**: Modern, clean UI with medical safety emphasis

## Features

### 🏠 Main Dashboard
- Clean, professional interface
- Prominent safety disclaimer
- Easy navigation

### 🔍 Symptom Analysis
- Input form for patient symptoms
- Patient context fields (age, gender)
- Real-time analysis
- Visual loading indicators

### 📋 Recommendations Display
- Structured recommendation cards
- Confidence badges (color-coded)
- Supporting evidence list
- Warnings and disclaimers
- Mandatory approval banners

### 🤖 Agent Management
- View all registered agents
- Agent information display
- Refresh functionality

## Running the UI

### Start the Server

```bash
python run_server.py
```

### Access the UI

- **Main UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health

## UI Components

### Symptom Analysis Form
Located at the top of the main page:
- **Symptoms Textarea**: Enter patient symptoms (free text)
- **Age Field**: Patient age (optional)
- **Gender Dropdown**: Patient gender (optional)
- **Analyze Button**: Triggers symptom analysis

### Recommendations Section
Appears after analysis:
- **Recommendation Cards**: Each recommendation displayed in a card
- **Type Badge**: Shows recommendation type
- **Confidence Badge**: Color-coded confidence level
  - 🟢 Green: High confidence (>70%)
  - 🟡 Yellow: Moderate confidence (50-70%)
  - 🔴 Red: Low confidence (<50%)
- **Content**: Full recommendation text
- **Evidence**: Supporting evidence list
- **Warnings**: Risk warnings and disclaimers
- **Approval Banner**: Mandatory human approval notice

### Agents List
Shows all registered agents:
- Agent name and description
- Agent ID
- Refresh button to reload list

## API Endpoints

The UI communicates with these API endpoints:

- `POST /api/analyze-symptoms` - Analyze patient symptoms
- `GET /api/agents` - List all agents
- `POST /api/agents` - Create new agent
- `POST /api/agents/{agent_id}/execute` - Execute agent task

## Safety Features in UI

1. **Prominent Disclaimer**: Always visible at the top
2. **Approval Banners**: Every recommendation shows approval requirement
3. **Warning Sections**: Highlighted warnings in recommendations
4. **Confidence Indicators**: Clear confidence visualization

## Customization

### Styling
Edit `ui/styles.css` to customize:
- Colors (CSS variables in `:root`)
- Layout and spacing
- Typography
- Responsive breakpoints

### Functionality
Edit `ui/app.js` to customize:
- API endpoints
- Data formatting
- Error handling
- Additional features

## Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (responsive design)

## Future Enhancements

Planned UI features:
- Agent builder interface
- MCP tool builder
- Workflow visualizer
- Patient case viewer
- Audit log dashboard
- Advanced filtering and search

