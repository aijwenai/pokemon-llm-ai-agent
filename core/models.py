from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ResearchStep:
    """Represents a single step in the research process"""
    step_number: int
    description: str
    action_type: str  # "intent_analysis", "endpoint_selection", "api_call", "exclusion_filtering", "semantic_analysis", "synthesis"
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    reasoning: str
    timestamp: str
    duration_seconds: float

@dataclass
class APICall:
    """Represents an API call made during research"""
    endpoint: str
    url: str
    method: str
    response_data: Any
    timestamp: str
    duration_seconds: float

@dataclass
class ResearchReport:
    """Final research report structure"""
    query: str
    research_goal: str
    intent_analysis: Dict[str, Any]
    endpoint_strategy: Dict[str, Any]
    exclusions_applied: Dict[str, Any]
    methodology: str
    steps_taken: List[ResearchStep]
    api_calls_made: List[APICall]
    key_findings: List[str]
    conclusion: str
    recommendations: List[str]
    confidence_score: float
    timestamp: str
    total_duration: float
    advantages_over_simple_llm: List[str]