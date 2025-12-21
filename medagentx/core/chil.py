"""
Contextual Health Intelligence Layer (CHIL) for MedAgentX v2.0

Context fusion layer that ingests:
- Geography (coarse, privacy-safe)
- Weather (temperature, humidity)
- Seasonality
- Lifestyle signals (diet, activity)
- Temporal history

Rules:
- No diagnosis
- Only correlation and risk amplification
- Fully deterministic
- All logic auditable
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeographicContext:
    """Geographic context (privacy-safe, coarse-grained)."""
    region: str  # e.g., "north_america", "europe", "asia"
    country: Optional[str] = None  # Optional country code
    climate_zone: Optional[str] = None  # e.g., "temperate", "tropical", "arid"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "region": self.region,
            "country": self.country,
            "climate_zone": self.climate_zone,
        }


@dataclass
class WeatherContext:
    """Weather context."""
    temperature_celsius: Optional[float] = None
    humidity_percent: Optional[float] = None
    air_quality_index: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "temperature_celsius": self.temperature_celsius,
            "humidity_percent": self.humidity_percent,
            "air_quality_index": self.air_quality_index,
            "timestamp": self.timestamp,
        }


@dataclass
class LifestyleContext:
    """Lifestyle signals."""
    diet_type: Optional[str] = None  # e.g., "vegetarian", "mediterranean", "standard"
    activity_level: Optional[str] = None  # e.g., "sedentary", "moderate", "active"
    sleep_hours: Optional[float] = None
    stress_level: Optional[str] = None  # e.g., "low", "moderate", "high"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "diet_type": self.diet_type,
            "activity_level": self.activity_level,
            "sleep_hours": self.sleep_hours,
            "stress_level": self.stress_level,
        }


@dataclass
class TemporalContext:
    """Temporal context."""
    season: Optional[str] = None  # "spring", "summer", "fall", "winter"
    month: Optional[int] = None  # 1-12
    day_of_week: Optional[int] = None  # 0-6 (Monday=0)
    time_of_day: Optional[str] = None  # "morning", "afternoon", "evening", "night"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "season": self.season,
            "month": self.month,
            "day_of_week": self.day_of_week,
            "time_of_day": self.time_of_day,
        }


@dataclass
class ContextualIntelligence:
    """Contextual intelligence output."""
    risk_amplifiers: List[str] = field(default_factory=list)  # Risk factors amplified by context
    correlations: List[str] = field(default_factory=list)  # Correlations observed
    contextual_insights: List[str] = field(default_factory=list)  # Context-based insights
    confidence: float = 0.5  # Confidence in contextual analysis
    evidence: List[str] = field(default_factory=list)  # Evidence supporting insights
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "risk_amplifiers": self.risk_amplifiers,
            "correlations": self.correlations,
            "contextual_insights": self.contextual_insights,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


class ContextualHealthIntelligenceLayer:
    """
    Contextual Health Intelligence Layer.
    
    Fuses multiple context sources to provide risk amplification
    and correlation insights (NOT diagnosis).
    """
    
    def __init__(self):
        """Initialize CHIL."""
        self.audit_log: List[Dict[str, Any]] = []
    
    def analyze(
        self,
        clinical_data: Dict[str, Any],
        geographic: Optional[GeographicContext] = None,
        weather: Optional[WeatherContext] = None,
        lifestyle: Optional[LifestyleContext] = None,
        temporal: Optional[TemporalContext] = None,
    ) -> ContextualIntelligence:
        """
        Analyze clinical data with contextual information.
        
        Args:
            clinical_data: Clinical data (symptoms, conditions, etc.)
            geographic: Geographic context
            weather: Weather context
            lifestyle: Lifestyle context
            temporal: Temporal context
            
        Returns:
            ContextualIntelligence with risk amplifiers and correlations
        """
        intelligence = ContextualIntelligence()
        
        # Analyze geographic context
        if geographic:
            geo_insights = self._analyze_geographic(geographic, clinical_data)
            intelligence.risk_amplifiers.extend(geo_insights.get("risk_amplifiers", []))
            intelligence.correlations.extend(geo_insights.get("correlations", []))
            intelligence.contextual_insights.extend(geo_insights.get("insights", []))
            intelligence.evidence.extend(geo_insights.get("evidence", []))
        
        # Analyze weather context
        if weather:
            weather_insights = self._analyze_weather(weather, clinical_data)
            intelligence.risk_amplifiers.extend(weather_insights.get("risk_amplifiers", []))
            intelligence.correlations.extend(weather_insights.get("correlations", []))
            intelligence.contextual_insights.extend(weather_insights.get("insights", []))
            intelligence.evidence.extend(weather_insights.get("evidence", []))
        
        # Analyze lifestyle context
        if lifestyle:
            lifestyle_insights = self._analyze_lifestyle(lifestyle, clinical_data)
            intelligence.risk_amplifiers.extend(lifestyle_insights.get("risk_amplifiers", []))
            intelligence.correlations.extend(lifestyle_insights.get("correlations", []))
            intelligence.contextual_insights.extend(lifestyle_insights.get("insights", []))
            intelligence.evidence.extend(lifestyle_insights.get("evidence", []))
        
        # Analyze temporal context
        if temporal:
            temporal_insights = self._analyze_temporal(temporal, clinical_data)
            intelligence.risk_amplifiers.extend(temporal_insights.get("risk_amplifiers", []))
            intelligence.correlations.extend(temporal_insights.get("correlations", []))
            intelligence.contextual_insights.extend(temporal_insights.get("insights", []))
            intelligence.evidence.extend(temporal_insights.get("evidence", []))
        
        # Calculate confidence (deterministic)
        intelligence.confidence = self._calculate_confidence(intelligence)
        
        # Audit
        self._audit("analyze", {
            "geographic": geographic.to_dict() if geographic else None,
            "weather": weather.to_dict() if weather else None,
            "lifestyle": lifestyle.to_dict() if lifestyle else None,
            "temporal": temporal.to_dict() if temporal else None,
            "intelligence": intelligence.to_dict(),
        })
        
        return intelligence
    
    def _analyze_geographic(
        self,
        geographic: GeographicContext,
        clinical_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze geographic context (deterministic rules)."""
        insights = {
            "risk_amplifiers": [],
            "correlations": [],
            "insights": [],
            "evidence": [],
        }
        
        # Example deterministic rules
        if geographic.region == "tropical":
            insights["correlations"].append("Tropical regions may have higher prevalence of vector-borne diseases")
            insights["evidence"].append(f"Geographic region: {geographic.region}")
        
        if geographic.climate_zone == "arid":
            insights["risk_amplifiers"].append("Arid climate may increase dehydration risk")
            insights["evidence"].append(f"Climate zone: {geographic.climate_zone}")
        
        return insights
    
    def _analyze_weather(
        self,
        weather: WeatherContext,
        clinical_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze weather context (deterministic rules)."""
        insights = {
            "risk_amplifiers": [],
            "correlations": [],
            "insights": [],
            "evidence": [],
        }
        
        # Temperature-based rules
        if weather.temperature_celsius is not None:
            if weather.temperature_celsius > 35:
                insights["risk_amplifiers"].append("High temperature may increase heat-related risk")
                insights["evidence"].append(f"Temperature: {weather.temperature_celsius}°C")
            elif weather.temperature_celsius < 0:
                insights["risk_amplifiers"].append("Low temperature may increase cold-related risk")
                insights["evidence"].append(f"Temperature: {weather.temperature_celsius}°C")
        
        # Humidity-based rules
        if weather.humidity_percent is not None:
            if weather.humidity_percent > 80:
                insights["correlations"].append("High humidity may correlate with respiratory discomfort")
                insights["evidence"].append(f"Humidity: {weather.humidity_percent}%")
        
        # Air quality rules
        if weather.air_quality_index is not None:
            if weather.air_quality_index > 100:
                insights["risk_amplifiers"].append("Poor air quality may amplify respiratory symptoms")
                insights["evidence"].append(f"Air quality index: {weather.air_quality_index}")
        
        return insights
    
    def _analyze_lifestyle(
        self,
        lifestyle: LifestyleContext,
        clinical_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze lifestyle context (deterministic rules)."""
        insights = {
            "risk_amplifiers": [],
            "correlations": [],
            "insights": [],
            "evidence": [],
        }
        
        # Activity level
        if lifestyle.activity_level == "sedentary":
            insights["risk_amplifiers"].append("Sedentary lifestyle may correlate with certain health risks")
            insights["evidence"].append(f"Activity level: {lifestyle.activity_level}")
        
        # Sleep
        if lifestyle.sleep_hours is not None:
            if lifestyle.sleep_hours < 6:
                insights["risk_amplifiers"].append("Insufficient sleep may amplify fatigue-related symptoms")
                insights["evidence"].append(f"Sleep hours: {lifestyle.sleep_hours}")
        
        # Stress
        if lifestyle.stress_level == "high":
            insights["risk_amplifiers"].append("High stress may correlate with various symptom presentations")
            insights["evidence"].append(f"Stress level: {lifestyle.stress_level}")
        
        return insights
    
    def _analyze_temporal(
        self,
        temporal: TemporalContext,
        clinical_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze temporal context (deterministic rules)."""
        insights = {
            "risk_amplifiers": [],
            "correlations": [],
            "insights": [],
            "evidence": [],
        }
        
        # Seasonal patterns
        if temporal.season:
            if temporal.season == "winter":
                insights["correlations"].append("Winter season may correlate with respiratory and flu-like symptoms")
                insights["evidence"].append(f"Season: {temporal.season}")
            elif temporal.season == "spring":
                insights["correlations"].append("Spring season may correlate with allergy-related symptoms")
                insights["evidence"].append(f"Season: {temporal.season}")
        
        return insights
    
    def _calculate_confidence(self, intelligence: ContextualIntelligence) -> float:
        """Calculate confidence in contextual analysis (deterministic)."""
        # Base confidence
        confidence = 0.5
        
        # Increase confidence if we have multiple context sources
        context_count = sum([
            len(intelligence.risk_amplifiers) > 0,
            len(intelligence.correlations) > 0,
            len(intelligence.evidence) > 0,
        ])
        
        if context_count >= 2:
            confidence = 0.7
        if context_count >= 3:
            confidence = 0.8
        
        return min(1.0, confidence)
    
    def _audit(self, event: str, data: Dict[str, Any]) -> None:
        """Log CHIL event to audit log."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **data,
        })

