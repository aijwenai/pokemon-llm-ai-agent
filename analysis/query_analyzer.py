import json
import logging
from typing import Dict, Any
try:
    from ..api.token_manager import TokenManager
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from api.token_manager import TokenManager

logger = logging.getLogger(__name__)

class LLMQueryAnalyzer:
    """LLM-powered query analysis with token management"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.token_manager = TokenManager()
        self.known_intents = [
            "team_building", "battle_analysis", "pokemon_filtering",
            "type_effectiveness", "evolution_info", "breeding_info", 
            "location_finding", "item_usage", "competition_strategy",
            "stat_comparison", "move_analysis", "ability_research",
            "lore_inquiry", "collection_tracking", "discovery_exploration"
        ]
        
        self.fallback_categories = {
            "misc_pokemon_lore": "Pokemon world, stories, legends related",
            "misc_game_mechanics": "Game mechanics, hidden elements related", 
            "misc_trivia": "Trivia, interesting facts related",
            "misc_meta_gaming": "Game external information, development history related",
            "misc_community": "Community, player culture related",
            "misc_calculation": "Complex calculations, mathematical analysis related",
            "misc_hypothetical": "Hypothetical, theoretical questions",
            "misc_unclear": "Unclear intent queries",
            "misc_unsupported": "Queries that current system cannot handle"
        }
    
    async def analyze_query_comprehensive(self, query: str) -> Dict[str, Any]:
        """Comprehensive query analysis including intents, entities, and exclusions"""
        
        system_prompt = f"""You are a Pokemon query analysis expert. Analyze the user's query comprehensively.

Known Intent Categories:
{json.dumps(self.known_intents, ensure_ascii=False)}

Fallback Categories:
{json.dumps(self.fallback_categories, indent=2, ensure_ascii=False)}

Analyze the query for:
1. For intents, you must choose one or more from known and fallback categories.
2. Entities (Pokemon names, types, colors, abilities, etc.)
3. Exclusion conditions (explicit or implicit)
4. Query complexity and structure
5. Required research approach

Return detailed JSON analysis."""

        user_prompt = f"""
Analyze this Pokemon query comprehensively:

Query: "{query}"

Return JSON with complete analysis:
{{
    "primary_intents": ["list of main intents"],
    "fallback_intents": ["list of fallback categories if needed"],
    "requires_fallback": boolean,
    "confidence_scores": {{"intent": confidence_value}},
    
    "entities": {{
        "pokemon_names": ["explicit Pokemon names"],
        "types": ["Pokemon types mentioned"],
        "colors": ["colors mentioned"],
        "abilities": ["abilities mentioned"],
        "locations": ["locations mentioned"],
        "items": ["items mentioned"],
        "moves": ["moves mentioned"],
        "generations": ["generation references"],
        "size_descriptors": ["size-related terms"],
        "rarity_indicators": ["rarity terms"]
    }},
    
    "exclusions": {{
        "has_exclusions": boolean,
        "explicit_exclusions": ["things to explicitly exclude"],
        "attribute_exclusions": ["attribute-based exclusions"],
        "semantic_exclusions": ["semantic/subjective exclusions"],
        "processing_stages": ["which stages handle which exclusions"]
    }},
    
    "query_structure": {{
        "complexity": "simple/medium/complex/multi_step",
        "has_comparisons": boolean,
        "has_conditions": boolean,
        "subqueries": ["broken down sub-questions if complex"]
    }},
    
    "research_requirements": {{
        "estimated_api_calls": "rough estimate",
        "critical_endpoints": ["most important endpoints needed"],
        "optional_endpoints": ["nice-to-have endpoints"],
        "research_depth": "surface/moderate/deep"
    }}
}}
"""

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        logger.debug(f"Initial intent analysis: {response.choices[0].message.content}")
        return json.loads(response.choices[0].message.content)