"""
Pokemon Deep Research Agent

A comprehensive Pokemon research system using intelligent query analysis,
strategic API calls, and LLM-powered synthesis.

Package Structure:
- core: Data classes and models
- api: External API interactions and token management
- analysis: Query analysis, intent mapping, and exclusion handling
- processing: Query processing and fallback handling
- research: Main orchestration logic
- reporting: Report generation and visualization
"""

# Core components
from .core.models import ResearchStep, APICall, ResearchReport

# API components
from .api.client import PokemonAPIClient
from .api.token_manager import TokenManager

# Analysis components
from .analysis.query_analyzer import LLMQueryAnalyzer
from .analysis.endpoint_mapper import IntentEndpointMapper
from .analysis.exclusion_handler import ExclusionHandler

# Processing components
from .processing.fallback_processor import FallbackQueryProcessor

# Research components
from .research.agent import DeepResearchAgent

# Reporting components
from .reporting.visualizer import AdvancedReportVisualizer

__version__ = "2.0.0"
__author__ = "Pokemon Research Team"

__all__ = [
    'ResearchStep',
    'APICall', 
    'ResearchReport',
    'PokemonAPIClient',
    'TokenManager',
    'LLMQueryAnalyzer',
    'IntentEndpointMapper',
    'ExclusionHandler',
    'FallbackQueryProcessor',
    'DeepResearchAgent',
    'AdvancedReportVisualizer'
]