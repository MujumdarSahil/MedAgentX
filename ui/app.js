// MedAgentX Frontend JavaScript

const API_BASE = '/api';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadAgents();
    
    // Set up symptom analysis form
    const symptomForm = document.getElementById('symptomForm');
    symptomForm.addEventListener('submit', handleSymptomAnalysis);
    
    // Set up refresh agents button
    document.getElementById('refreshAgents').addEventListener('click', loadAgents);
});

// Handle symptom analysis form submission
async function handleSymptomAnalysis(e) {
    e.preventDefault();
    
    const symptoms = document.getElementById('symptoms').value;
    const age = document.getElementById('age').value;
    const gender = document.getElementById('gender').value;
    
    const patientContext = {};
    if (age) patientContext.age = parseInt(age);
    if (gender) patientContext.gender = gender;
    
    // Show loading
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('recommendationsSection').style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/analyze-symptoms`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symptoms: symptoms,
                patient_context: patientContext,
            }),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayRecommendations(data.recommendations);
        
    } catch (error) {
        console.error('Error analyzing symptoms:', error);
        showError('Error analyzing symptoms. Please try again.');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
}

// Display recommendations
function displayRecommendations(recommendations) {
    const resultsDiv = document.getElementById('results');
    const recommendationsDiv = document.getElementById('recommendations');
    
    if (!recommendations || recommendations.length === 0) {
        resultsDiv.innerHTML = '<p>No recommendations generated.</p>';
        resultsDiv.classList.remove('hidden');
        return;
    }
    
    // Build recommendations HTML
    let html = '';
    
    recommendations.forEach((rec, index) => {
        const confidenceClass = getConfidenceClass(rec.confidence);
        
        html += `
            <div class="recommendation-card">
                <div class="recommendation-header">
                    <span class="recommendation-type">${formatRecommendationType(rec.type)}</span>
                    <span class="confidence-badge ${confidenceClass}">
                        ${rec.confidence.replace('_', ' ').toUpperCase()} (${(rec.confidence_score * 100).toFixed(0)}%)
                    </span>
                </div>
                
                <div class="recommendation-content">
                    ${escapeHtml(rec.content)}
                </div>
                
                ${rec.supporting_evidence && rec.supporting_evidence.length > 0 ? `
                    <div class="evidence-section">
                        <h4>Supporting Evidence</h4>
                        <ul class="evidence-list">
                            ${rec.supporting_evidence.map(evidence => `
                                <li>${escapeHtml(evidence)}</li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${rec.risks_and_warnings && rec.risks_and_warnings.length > 0 ? `
                    <div class="warnings-section">
                        <h4>Warnings</h4>
                        <ul class="warnings-list">
                            ${rec.risks_and_warnings.map(warning => `
                                <li>${escapeHtml(warning)}</li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${rec.requires_approval ? `
                    <div class="approval-banner">
                        ⚠️ This recommendation requires human (doctor) approval before use
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    recommendationsDiv.innerHTML = html;
    resultsDiv.classList.remove('hidden');
    document.getElementById('recommendationsSection').style.display = 'block';
}

// Load agents list
async function loadAgents() {
    try {
        const response = await fetch(`${API_BASE}/agents`);
        const data = await response.json();
        
        const agentsListDiv = document.getElementById('agentsList');
        
        if (data.agents.length === 0) {
            agentsListDiv.innerHTML = '<p>No agents registered yet.</p>';
            return;
        }
        
        agentsListDiv.innerHTML = data.agents.map(agent => `
            <div class="agent-item">
                <div class="agent-info">
                    <h3>${escapeHtml(agent.agent_name)}</h3>
                    <p>${escapeHtml(agent.description || 'No description')}</p>
                </div>
                <span class="agent-id">ID: ${escapeHtml(agent.agent_id)}</span>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading agents:', error);
        document.getElementById('agentsList').innerHTML = '<p>Error loading agents.</p>';
    }
}

// Utility functions
function getConfidenceClass(confidence) {
    if (confidence.includes('HIGH')) {
        return 'confidence-high';
    } else if (confidence.includes('MODERATE')) {
        return 'confidence-moderate';
    } else {
        return 'confidence-low';
    }
}

function formatRecommendationType(type) {
    return type.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `<div class="error-message" style="color: var(--danger-color); padding: 1rem; background: #fee2e2; border-radius: 4px;">${escapeHtml(message)}</div>`;
    resultsDiv.classList.remove('hidden');
}

