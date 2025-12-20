from typing import Any, Dict, List


class MedicalCodingKB:
    """Lightweight ICD-10-like knowledge base (in-memory, no external data)."""

    def __init__(self) -> None:
        # Small, curated subset for demo purposes (recommendation-only).
        self._entries: List[Dict[str, Any]] = [
            {
                "code": "R50.9",
                "description": "Fever, unspecified",
                "keywords": ["fever", "pyrexia", "temperature"],
                "evidence": "Supportive coding for reported fever; confirm etiology separately.",
            },
            {
                "code": "R05",
                "description": "Cough",
                "keywords": ["cough", "dry cough", "productive cough"],
                "evidence": "Use for reported cough symptoms; no causal diagnosis implied.",
            },
            {
                "code": "R06.02",
                "description": "Shortness of breath",
                "keywords": ["dyspnea", "shortness of breath", "sob"],
                "evidence": "Applicable to documented shortness of breath; requires clinical assessment.",
            },
            {
                "code": "R07.0",
                "description": "Pain in throat",
                "keywords": ["sore throat", "throat pain", "pharyngitis"],
                "evidence": "Coding for throat pain; distinguish from infectious diagnoses separately.",
            },
            {
                "code": "R09.81",
                "description": "Nasal congestion",
                "keywords": ["congestion", "stuffy nose", "nasal obstruction"],
                "evidence": "Use for documented nasal congestion; supportive, not diagnostic.",
            },
            {
                "code": "R07.9",
                "description": "Chest pain, unspecified",
                "keywords": ["chest pain", "pressure", "tightness"],
                "evidence": "Capture reported chest pain while clinical workup determines cause.",
            },
            {
                "code": "R11.0",
                "description": "Nausea",
                "keywords": ["nausea", "queasy"],
                "evidence": "Use for nausea complaints; etiology requires clinician decision.",
            },
            {
                "code": "R19.7",
                "description": "Diarrhea, unspecified",
                "keywords": ["diarrhea", "loose stool"],
                "evidence": "Supportive code for diarrhea symptoms pending clinical review.",
            },
            {
                "code": "R51.9",
                "description": "Headache",
                "keywords": ["headache", "head pain", "migraine"],
                "evidence": "Use for reported headache; differentiate primary vs secondary causes clinically.",
            },
            {
                "code": "R68.83",
                "description": "Chills (without fever)",
                "keywords": ["chills", "shivering"],
                "evidence": "Coding for chills; ensure separate evaluation for infection risk.",
            },
            {
                "code": "R68.89",
                "description": "Other general symptoms and signs",
                "keywords": ["fatigue", "malaise", "tiredness"],
                "evidence": "General symptom coding; use when more specific code is not supported.",
            },
            {
                "code": "J02.9",
                "description": "Acute pharyngitis, unspecified",
                "keywords": ["sore throat", "pharyngitis", "throat irritation"],
                "evidence": "Use when sore throat documented and no specific pathogen identified.",
            },
            {
                "code": "J11.1",
                "description": "Influenza with other respiratory manifestations",
                "keywords": ["fever", "cough", "myalgia", "flu"],
                "evidence": "Supportive when influenza-like illness documented; confirm testing separately.",
            },
            {
                "code": "J00",
                "description": "Acute nasopharyngitis [common cold]",
                "keywords": ["runny nose", "congestion", "sneezing", "cold"],
                "evidence": "Use for common cold presentations; symptomatic care guidance applies.",
            },
        ]

    def search(self, symptoms_text: str) -> List[Dict[str, Any]]:
        """
        Recommend ICD-10-style codes based on symptom text.

        Args:
            symptoms_text: Free-text symptoms description.

        Returns:
            List of matched code dictionaries with evidence.
        """
        if not symptoms_text or not isinstance(symptoms_text, str):
            return []

        text = symptoms_text.lower()
        results: List[Dict[str, Any]] = []

        for entry in self._entries:
            matched_keywords = [kw for kw in entry["keywords"] if kw.lower() in text]
            score = len(matched_keywords)
            if score == 0:
                continue
            confidence = min(0.4 + 0.15 * score, 0.95)
            results.append(
                {
                    "code": entry["code"],
                    "description": entry["description"],
                    "evidence": entry["evidence"],
                    "matched_keywords": matched_keywords,
                    "confidence": round(confidence, 2),
                }
            )

        results.sort(key=lambda item: item["confidence"], reverse=True)
        return results

