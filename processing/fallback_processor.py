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

class FallbackQueryProcessor:
    """Handles queries that fall into fallback categories"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.token_manager = TokenManager()
    
    async def handle_fallback_query(self, query: str, analysis: Dict[str, Any], api_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process fallback category queries with token management"""
        
        fallback_category = analysis.get("fallback_intents", [])
        
        if not fallback_category:
            return await self._handle_general_fallback(query, api_results)
        
        primary_fallback = fallback_category[0]
        
        # Apply token management to API results
        compressed_results = self._compress_api_results_for_fallback(api_results)
        
        if "misc_unsupported" in primary_fallback:
            return await self._handle_unsupported_query(query)
        elif "misc_unclear" in primary_fallback:
            return await self._handle_unclear_query(query, compressed_results)
        elif "misc_hypothetical" in primary_fallback:
            return await self._handle_hypothetical_query(query, compressed_results)
        elif "misc_calculation" in primary_fallback:
            return await self._handle_calculation_query(query, compressed_results)
        elif "misc_pokemon_lore" in primary_fallback:
            return await self._handle_lore_query(query, compressed_results)
        else:
            return await self._handle_general_fallback(query, compressed_results)
    
    def _compress_api_results_for_fallback(self, api_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compress API results for fallback processing"""
        
        if not api_results:
            return {}
        
        # Check if compression is needed
        results_size = self.token_manager.count_tokens(json.dumps(api_results, ensure_ascii=False))
        
        if results_size <= 20000:  # Reasonable size for fallback processing
            return api_results
        
        print(f"   🗜️ Compressing API results for fallback: {results_size} tokens")
        
        # Apply compression
        compressed = self.token_manager.compress_data_hierarchically(
            api_results, 
            target_tokens=15000  # Leave room for prompt and response
        )
        
        compressed_size = self.token_manager.count_tokens(json.dumps(compressed, ensure_ascii=False))
        print(f"   ✅ Compressed to {compressed_size} tokens")
        
        return compressed
    
    async def _handle_unsupported_query(self, query: str) -> Dict[str, Any]:
        """Handle unsupported queries gracefully"""
        
        system_prompt = """You are a Pokemon assistant. The user's query is beyond current system capabilities. 

Provide a helpful response that:
1. Acknowledges the interesting question
2. Explains why it can't be fully answered
3. Suggests related questions that could be answered
4. Offers relevant Pokemon knowledge as consolation"""

        user_prompt = f'User asked: "{query}"\n\nProvide a helpful fallback response.'

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return {
            "response_type": "unsupported_graceful",
            "answer": response.choices[0].message.content,
            "suggested_alternatives": [
                "Try asking about specific Pokemon characteristics",
                "Ask for team building recommendations",
                "Inquire about Pokemon locations or evolution methods"
            ]
        }
    
    async def _handle_hypothetical_query(self, query: str, api_results: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hypothetical or theoretical questions"""
        
        system_prompt = """You are a Pokemon theorist and strategist. Answer hypothetical questions using available data and logical reasoning.

Base your analysis on:
- Real Pokemon data provided
- Game mechanics knowledge
- Strategic considerations
- Theoretical scenarios

Clearly state assumptions and limitations."""

        user_prompt = f"""
Hypothetical Query: "{query}"

Available Data:
{json.dumps(api_results, indent=2, ensure_ascii=False)}

Provide a thoughtful theoretical analysis."""

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return {
            "response_type": "hypothetical_analysis",
            "answer": response.choices[0].message.content,
            "confidence": "theoretical",
            "data_sources": list(api_results.keys())
        }
    
    async def _handle_calculation_query(self, query: str, api_results: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calculation-based queries"""
        
        system_prompt = """You are a Pokemon mathematics and statistics expert. Answer calculation-based questions using provided data and mathematical analysis.

Focus on:
- Statistical analysis of Pokemon data
- Mathematical calculations
- Comparative analysis
- Probability assessments"""

        user_prompt = f"""
Calculation Query: "{query}"

Available Data:
{json.dumps(api_results, indent=2, ensure_ascii=False)}

Provide detailed mathematical analysis."""

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return {
            "response_type": "calculation_analysis",
            "answer": response.choices[0].message.content,
            "analysis_type": "mathematical"
        }
    
    async def _handle_unclear_query(self, query: str, api_results: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unclear queries"""
        
        system_prompt = """You are a Pokemon query interpreter. The user's question is unclear but you have some Pokemon data. 

Try to:
1. Interpret what they might be asking
2. Provide the most relevant information from available data
3. Ask clarifying questions to better understand their intent"""

        user_prompt = f"""
Unclear Query: "{query}"

Available Data:
{json.dumps(api_results, indent=2, ensure_ascii=False)}

Interpret and provide the best possible response."""

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return {
            "response_type": "unclear_interpretation",
            "answer": response.choices[0].message.content,
            "clarification_suggested": True
        }
    
    async def _handle_lore_query(self, query: str, api_results: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Pokemon lore and story-related queries"""
        
        system_prompt = """You are a Pokemon lore expert. Use the provided Pokemon data to answer questions about Pokemon stories, descriptions, and world-building.

Focus on:
- Pokedex entries and descriptions
- Pokemon habitats and behaviors  
- Evolutionary relationships
- Regional variants and their meanings
- Pokemon mythology and legends"""

        user_prompt = f"""
Lore Query: "{query}"

Pokemon Data Available:
{json.dumps(api_results, indent=2, ensure_ascii=False)}

Provide rich lore-based insights using this data."""

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return {
            "response_type": "lore_exploration",
            "answer": response.choices[0].message.content,
            "lore_sources": "pokedex_entries_and_species_data"
        }
    
    async def _handle_general_fallback(self, query: str, api_results: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general fallback cases"""
        
        system_prompt = """You are a Pokemon research assistant. The user's query doesn't fit standard categories, but you have some relevant data.

Provide the best possible answer using available information, and clearly explain:
- What data you found
- How it relates to their question  
- What limitations exist
- What additional research might help"""

        user_prompt = f"""
Query: "{query}"

Available Data:
{json.dumps(api_results, indent=2, ensure_ascii=False)}

Provide the best possible response using this data."""

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return {
            "response_type": "general_fallback",
            "answer": response.choices[0].message.content,
            "data_completeness": "partial"
        }