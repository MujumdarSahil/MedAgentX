from typing import Any, Dict, List


class MedicalCodingKB:
    """Lightweight ICD-10-like knowledge base (in-memory, no external data)."""

    def __init__(self) -> None:
        # Expanded curated subset for demo purposes (recommendation-only).
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
            # Additional ICD-10 entries (30-50 total)
            {
                "code": "R50.81",
                "description": "Fever presenting with conditions classified elsewhere",
                "keywords": ["fever", "elevated temperature", "hyperthermia"],
                "evidence": "Fever as presenting symptom; underlying condition requires separate coding.",
            },
            {
                "code": "R06.00",
                "description": "Dyspnea, unspecified",
                "keywords": ["dyspnea", "breathing difficulty", "respiratory distress"],
                "evidence": "General dyspnea coding; assess for underlying respiratory or cardiac causes.",
            },
            {
                "code": "R06.09",
                "description": "Other forms of dyspnea",
                "keywords": ["orthopnea", "exertional dyspnea", "paroxysmal dyspnea"],
                "evidence": "Specific dyspnea patterns; clinical correlation needed for etiology.",
            },
            {
                "code": "R10.9",
                "description": "Unspecified abdominal pain",
                "keywords": ["abdominal pain", "stomach pain", "belly ache"],
                "evidence": "Non-specific abdominal pain; requires clinical evaluation for cause.",
            },
            {
                "code": "R10.10",
                "description": "Upper abdominal pain",
                "keywords": ["epigastric pain", "upper abdomen", "stomach pain"],
                "evidence": "Upper abdominal pain; consider GI, cardiac, or other etiologies.",
            },
            {
                "code": "R10.30",
                "description": "Lower abdominal pain, unspecified",
                "keywords": ["lower abdominal pain", "pelvic pain"],
                "evidence": "Lower abdominal pain; assess for GI, GU, or gynecological causes.",
            },
            {
                "code": "R11.2",
                "description": "Nausea with vomiting",
                "keywords": ["nausea", "vomiting", "emesis"],
                "evidence": "Nausea with vomiting; evaluate for GI, CNS, or metabolic causes.",
            },
            {
                "code": "R12",
                "description": "Heartburn",
                "keywords": ["heartburn", "pyrosis", "acid reflux"],
                "evidence": "Heartburn symptoms; consider GERD, dietary factors, or medication effects.",
            },
            {
                "code": "R13.10",
                "description": "Dysphagia, unspecified",
                "keywords": ["difficulty swallowing", "dysphagia", "swallowing problem"],
                "evidence": "Swallowing difficulty; assess for structural, neurological, or functional causes.",
            },
            {
                "code": "R19.00",
                "description": "Intra-abdominal and pelvic swelling, mass and lump, unspecified site",
                "keywords": ["abdominal mass", "swelling", "lump"],
                "evidence": "Abdominal mass or swelling; requires imaging and clinical evaluation.",
            },
            {
                "code": "R20.0",
                "description": "Anesthesia of skin",
                "keywords": ["numbness", "anesthesia", "loss of sensation"],
                "evidence": "Skin anesthesia; evaluate for neurological or vascular causes.",
            },
            {
                "code": "R20.2",
                "description": "Paresthesia of skin",
                "keywords": ["tingling", "paresthesia", "pins and needles"],
                "evidence": "Paresthesia; consider peripheral neuropathy, compression, or metabolic causes.",
            },
            {
                "code": "R21",
                "description": "Rash and other nonspecific skin eruption",
                "keywords": ["rash", "skin eruption", "dermatitis"],
                "evidence": "Non-specific rash; requires clinical examination for pattern and cause.",
            },
            {
                "code": "R22.9",
                "description": "Localized swelling, mass and lump, unspecified",
                "keywords": ["swelling", "mass", "lump", "localized"],
                "evidence": "Localized swelling or mass; assess for infection, neoplasm, or other causes.",
            },
            {
                "code": "R25.0",
                "description": "Abnormal involuntary movements",
                "keywords": ["tremor", "involuntary movement", "twitching"],
                "evidence": "Abnormal movements; evaluate for neurological, metabolic, or medication causes.",
            },
            {
                "code": "R25.2",
                "description": "Cramp and spasm",
                "keywords": ["cramp", "spasm", "muscle cramp"],
                "evidence": "Muscle cramps or spasms; consider electrolyte imbalance, overuse, or neurological causes.",
            },
            {
                "code": "R29.818",
                "description": "Other symptoms and signs involving the nervous and musculoskeletal systems",
                "keywords": ["neurological symptoms", "musculoskeletal symptoms"],
                "evidence": "Non-specific neuro-musculoskeletal symptoms; requires detailed clinical assessment.",
            },
            {
                "code": "R30.0",
                "description": "Dysuria",
                "keywords": ["dysuria", "painful urination", "burning urination"],
                "evidence": "Dysuria; evaluate for UTI, STI, or other genitourinary causes.",
            },
            {
                "code": "R31.9",
                "description": "Hematuria, unspecified",
                "keywords": ["hematuria", "blood in urine"],
                "evidence": "Hematuria; requires urological evaluation for cause.",
            },
            {
                "code": "R32",
                "description": "Unspecified urinary incontinence",
                "keywords": ["incontinence", "urinary incontinence", "leakage"],
                "evidence": "Urinary incontinence; assess for stress, urge, overflow, or functional causes.",
            },
            {
                "code": "R33.9",
                "description": "Retention of urine, unspecified",
                "keywords": ["urinary retention", "inability to void"],
                "evidence": "Urinary retention; evaluate for obstruction, neurological, or medication causes.",
            },
            {
                "code": "R40.0",
                "description": "Somnolence",
                "keywords": ["somnolence", "drowsiness", "sleepiness"],
                "evidence": "Excessive sleepiness; consider sleep disorders, medications, or CNS causes.",
            },
            {
                "code": "R40.1",
                "description": "Stupor",
                "keywords": ["stupor", "decreased consciousness"],
                "evidence": "Stupor; urgent evaluation for CNS, metabolic, or toxic causes.",
            },
            {
                "code": "R41.0",
                "description": "Disorientation, unspecified",
                "keywords": ["disorientation", "confusion", "altered mental status"],
                "evidence": "Disorientation; assess for delirium, dementia, or acute CNS causes.",
            },
            {
                "code": "R42",
                "description": "Dizziness and giddiness",
                "keywords": ["dizziness", "vertigo", "giddiness", "lightheadedness"],
                "evidence": "Dizziness; differentiate vertigo from presyncope; evaluate for vestibular, cardiac, or neurological causes.",
            },
            {
                "code": "R50.9",
                "description": "Fever, unspecified",
                "keywords": ["fever", "pyrexia", "temperature"],
                "evidence": "Supportive coding for reported fever; confirm etiology separately.",
            },
            {
                "code": "R53.1",
                "description": "Weakness",
                "keywords": ["weakness", "muscle weakness", "generalized weakness"],
                "evidence": "Weakness; assess for neurological, muscular, metabolic, or systemic causes.",
            },
            {
                "code": "R53.81",
                "description": "Other malaise",
                "keywords": ["malaise", "feeling unwell", "generalized illness"],
                "evidence": "General malaise; non-specific symptom requiring clinical correlation.",
            },
            {
                "code": "R53.83",
                "description": "Other fatigue",
                "keywords": ["fatigue", "tiredness", "exhaustion"],
                "evidence": "Fatigue; evaluate for sleep, metabolic, psychiatric, or systemic causes.",
            },
            {
                "code": "R55",
                "description": "Syncope and collapse",
                "keywords": ["syncope", "fainting", "collapse", "passing out"],
                "evidence": "Syncope; urgent evaluation for cardiac, neurological, or vasovagal causes.",
            },
            {
                "code": "R56.9",
                "description": "Unspecified convulsions",
                "keywords": ["seizure", "convulsion", "fit"],
                "evidence": "Seizure activity; requires neurological evaluation and EEG if indicated.",
            },
            {
                "code": "R59.0",
                "description": "Localized enlarged lymph nodes",
                "keywords": ["lymphadenopathy", "swollen lymph nodes", "enlarged nodes"],
                "evidence": "Localized lymphadenopathy; assess for infection, malignancy, or inflammatory causes.",
            },
            {
                "code": "R59.9",
                "description": "Enlarged lymph nodes, unspecified",
                "keywords": ["generalized lymphadenopathy", "swollen nodes"],
                "evidence": "Generalized lymphadenopathy; evaluate for systemic infection, malignancy, or autoimmune causes.",
            },
            {
                "code": "R63.0",
                "description": "Anorexia",
                "keywords": ["anorexia", "loss of appetite", "decreased appetite"],
                "evidence": "Anorexia; consider GI, psychiatric, metabolic, or medication causes.",
            },
            {
                "code": "R63.3",
                "description": "Feeding difficulties",
                "keywords": ["feeding difficulty", "difficulty eating"],
                "evidence": "Feeding difficulties; assess for swallowing, GI, or neurological causes.",
            },
            {
                "code": "R63.4",
                "description": "Abnormal weight loss",
                "keywords": ["weight loss", "unintended weight loss"],
                "evidence": "Unintended weight loss; evaluate for malignancy, GI, endocrine, or psychiatric causes.",
            },
            {
                "code": "R63.5",
                "description": "Abnormal weight gain",
                "keywords": ["weight gain", "unintended weight gain"],
                "evidence": "Weight gain; assess for endocrine, medication, or lifestyle causes.",
            },
            {
                "code": "R64",
                "description": "Cachexia",
                "keywords": ["cachexia", "wasting", "muscle wasting"],
                "evidence": "Cachexia; severe wasting syndrome; evaluate for malignancy, chronic disease, or malnutrition.",
            },
            {
                "code": "R73.09",
                "description": "Other abnormal glucose",
                "keywords": ["abnormal glucose", "hyperglycemia", "hypoglycemia"],
                "evidence": "Abnormal glucose; assess for diabetes, medication effects, or metabolic causes.",
            },
            {
                "code": "R79.9",
                "description": "Abnormal finding of blood chemistry, unspecified",
                "keywords": ["abnormal labs", "abnormal blood work"],
                "evidence": "Abnormal blood chemistry; requires clinical correlation with specific values.",
            },
            {
                "code": "I10",
                "description": "Essential (primary) hypertension",
                "keywords": ["hypertension", "high blood pressure", "HTN"],
                "evidence": "Essential hypertension; requires blood pressure monitoring and cardiovascular risk assessment.",
            },
            {
                "code": "E11.9",
                "description": "Type 2 diabetes mellitus without complications",
                "keywords": ["diabetes", "type 2 diabetes", "DM2"],
                "evidence": "Type 2 diabetes; requires glucose monitoring and complication screening.",
            },
            {
                "code": "M79.3",
                "description": "Panniculitis, unspecified",
                "keywords": ["muscle pain", "myalgia", "muscle ache"],
                "evidence": "Muscle pain; assess for inflammatory, infectious, or overuse causes.",
            },
            {
                "code": "K21.9",
                "description": "Gastro-esophageal reflux disease without esophagitis",
                "keywords": ["GERD", "acid reflux", "heartburn"],
                "evidence": "GERD; lifestyle modifications and medication management may be indicated.",
            },
            {
                "code": "J44.9",
                "description": "Chronic obstructive pulmonary disease, unspecified",
                "keywords": ["COPD", "chronic bronchitis", "emphysema"],
                "evidence": "COPD; requires pulmonary function testing and management optimization.",
            },
            {
                "code": "I25.10",
                "description": "Atherosclerotic heart disease of native coronary artery without angina pectoris",
                "keywords": ["coronary artery disease", "CAD", "heart disease"],
                "evidence": "Coronary artery disease; requires cardiovascular risk management and monitoring.",
            },
            {
                "code": "M54.5",
                "description": "Low back pain",
                "keywords": ["back pain", "low back pain", "lumbar pain"],
                "evidence": "Low back pain; assess for mechanical, discogenic, or other causes.",
            },
            {
                "code": "G43.909",
                "description": "Migraine, unspecified, not intractable, without status migrainosus",
                "keywords": ["migraine", "headache", "migraine headache"],
                "evidence": "Migraine; assess frequency, triggers, and response to treatment.",
            },
        ]
        
        # CPT/HCPCS procedural codes (minimal placeholder set)
        self._cpt_hcpcs_entries: List[Dict[str, Any]] = [
            {
                "code": "99213",
                "description": "Office or other outpatient visit for the evaluation and management of an established patient",
                "code_type": "CPT",
                "procedure_type": "evaluation",
                "keywords": ["office visit", "outpatient visit", "established patient", "evaluation"],
                "evidence": "Standard office visit code for established patient evaluation; requires appropriate documentation.",
            },
            {
                "code": "99214",
                "description": "Office or other outpatient visit for the evaluation and management of an established patient, detailed",
                "code_type": "CPT",
                "procedure_type": "evaluation",
                "keywords": ["office visit", "detailed visit", "established patient", "comprehensive"],
                "evidence": "Detailed office visit for established patient; requires detailed history, examination, and medical decision making.",
            },
            {
                "code": "85025",
                "description": "Complete blood count (CBC)",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["cbc", "complete blood count", "blood test", "lab work"],
                "evidence": "Complete blood count for evaluation of infection, anemia, or other hematologic conditions.",
            },
            {
                "code": "80053",
                "description": "Comprehensive metabolic panel",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["cmp", "metabolic panel", "chemistry panel", "blood work"],
                "evidence": "Comprehensive metabolic panel for evaluation of electrolytes, kidney function, and liver function.",
            },
            {
                "code": "71020",
                "description": "Radiologic examination, chest, 2 views, frontal and lateral",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["chest xray", "chest x-ray", "cxr", "chest imaging"],
                "evidence": "Chest X-ray for evaluation of respiratory symptoms, infection, or cardiac conditions.",
            },
            {
                "code": "93000",
                "description": "Electrocardiogram, routine ECG with at least 12 leads",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["ekg", "ecg", "electrocardiogram", "heart rhythm"],
                "evidence": "ECG for evaluation of cardiac rhythm, ischemia, or other cardiac conditions.",
            },
            {
                "code": "81001",
                "description": "Urinalysis, automated, with microscopy",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["urinalysis", "urine test", "ua", "urine analysis"],
                "evidence": "Urinalysis for evaluation of urinary tract infection, kidney function, or other genitourinary conditions.",
            },
            {
                "code": "87804",
                "description": "Infectious agent detection by nucleic acid (DNA or RNA); influenza virus",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["flu test", "influenza test", "rapid flu", "flu swab"],
                "evidence": "Influenza testing for evaluation of flu-like symptoms; requires appropriate clinical indication.",
            },
            {
                "code": "87880",
                "description": "Infectious agent detection by nucleic acid (DNA or RNA); Streptococcus, group A",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["strep test", "strep throat", "group a strep", "rapid strep"],
                "evidence": "Group A Streptococcus testing for evaluation of pharyngitis; requires appropriate clinical indication.",
            },
            {
                "code": "99281",
                "description": "Emergency department visit for the evaluation and management of a patient",
                "code_type": "CPT",
                "procedure_type": "evaluation",
                "keywords": ["emergency", "ed visit", "er visit", "emergency department"],
                "evidence": "Emergency department visit code; requires appropriate documentation and medical necessity.",
            },
            {
                "code": "36415",
                "description": "Routine venipuncture for collection of specimen(s)",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["blood draw", "venipuncture", "phlebotomy", "lab draw"],
                "evidence": "Routine venipuncture for blood specimen collection; typically included in lab test codes.",
            },
            {
                "code": "94010",
                "description": "Spirometry, including graphic record, total and timed vital capacity",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["spirometry", "pulmonary function", "breathing test", "lung function"],
                "evidence": "Spirometry for evaluation of pulmonary function, asthma, or COPD; requires appropriate clinical indication.",
            },
            {
                "code": "76700",
                "description": "Ultrasound, abdominal, real time with image documentation",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["abdominal ultrasound", "abdominal us", "ultrasound abdomen"],
                "evidence": "Abdominal ultrasound for evaluation of abdominal pain, organ abnormalities, or other abdominal conditions.",
            },
            {
                "code": "70450",
                "description": "Computed tomography, head or brain; without contrast material",
                "code_type": "CPT",
                "procedure_type": "diagnostic",
                "keywords": ["head ct", "brain ct", "ct head", "head imaging"],
                "evidence": "Head CT for evaluation of headache, trauma, or neurological symptoms; requires appropriate clinical indication.",
            },
            {
                "code": "J0696",
                "description": "Injection, ceftriaxone sodium, per 250 mg",
                "code_type": "HCPCS",
                "procedure_type": "therapeutic",
                "keywords": ["ceftriaxone", "antibiotic injection", "rocephin"],
                "evidence": "Ceftriaxone injection for treatment of bacterial infections; requires appropriate diagnosis and clinical indication.",
            },
            {
                "code": "J0690",
                "description": "Injection, cefazolin sodium, 500 mg",
                "code_type": "HCPCS",
                "procedure_type": "therapeutic",
                "keywords": ["cefazolin", "antibiotic injection", "ancef"],
                "evidence": "Cefazolin injection for treatment of bacterial infections; requires appropriate diagnosis and clinical indication.",
            },
            {
                "code": "J2720",
                "description": "Injection, promethazine HCl, up to 50 mg",
                "code_type": "HCPCS",
                "procedure_type": "therapeutic",
                "keywords": ["promethazine", "phenergan", "nausea injection", "antiemetic"],
                "evidence": "Promethazine injection for treatment of nausea and vomiting; requires appropriate clinical indication.",
            },
            {
                "code": "J7030",
                "description": "Infusion, normal saline solution, 1000 cc",
                "code_type": "HCPCS",
                "procedure_type": "therapeutic",
                "keywords": ["normal saline", "iv fluids", "saline infusion", "hydration"],
                "evidence": "Normal saline infusion for hydration or medication administration; requires appropriate clinical indication.",
            },
            {
                "code": "J7042",
                "description": "Injection, normal saline solution, 1000 cc",
                "code_type": "HCPCS",
                "procedure_type": "therapeutic",
                "keywords": ["normal saline", "saline injection", "hydration"],
                "evidence": "Normal saline injection for hydration; requires appropriate clinical indication.",
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

    def search_cpt_hcpcs(self, symptoms_text: str, procedure_type: str = "general") -> List[Dict[str, Any]]:
        """
        Recommend CPT/HCPCS-style procedural codes based on symptom text.

        Args:
            symptoms_text: Free-text symptoms description.
            procedure_type: Type of procedure (general, diagnostic, therapeutic).

        Returns:
            List of matched procedural code dictionaries with evidence.
        """
        if not symptoms_text or not isinstance(symptoms_text, str):
            return []

        text = symptoms_text.lower()
        results: List[Dict[str, Any]] = []

        for entry in self._cpt_hcpcs_entries:
            # Filter by procedure type if specified
            if procedure_type != "general" and entry.get("procedure_type") != procedure_type:
                continue

            matched_keywords = [kw for kw in entry["keywords"] if kw.lower() in text]
            score = len(matched_keywords)
            if score == 0:
                continue
            confidence = min(0.35 + 0.15 * score, 0.90)
            results.append(
                {
                    "code": entry["code"],
                    "description": entry["description"],
                    "code_type": entry["code_type"],
                    "evidence": entry["evidence"],
                    "matched_keywords": matched_keywords,
                    "confidence": round(confidence, 2),
                }
            )

        results.sort(key=lambda item: item["confidence"], reverse=True)
        return results[:10]  # Limit to top 10 results

