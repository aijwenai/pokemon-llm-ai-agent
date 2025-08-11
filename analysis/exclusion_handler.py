import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ExclusionHandler:
    """Multi-layer exclusion processing system"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def process_exclusions(self, query_analysis: Dict[str, Any], api_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process all types of exclusions in the correct order"""
        
        exclusions = query_analysis.get('exclusions', {})
        
        if not exclusions.get('has_exclusions', False):
            return {
                'filtered_results': api_results,
                'exclusions_applied': [],
                'items_excluded': 0
            }
        
        print("🚫 Processing exclusions...")
        
        # Stage 1: Explicit name exclusions
        stage1_results = await self._apply_explicit_exclusions(
            api_results, exclusions.get('explicit_exclusions', [])
        )
        
        # Stage 2: Attribute-based exclusions  
        stage2_results = await self._apply_attribute_exclusions(
            stage1_results, exclusions.get('attribute_exclusions', [])
        )
        
        # Stage 3: Semantic exclusions (LLM-powered)
        final_results = await self._apply_semantic_exclusions(
            stage2_results, exclusions.get('semantic_exclusions', []), query_analysis
        )
        
        return {
            'filtered_results': final_results,
            'exclusions_applied': [
                'explicit_names', 'attribute_based', 'semantic_filtering'
            ],
            'exclusion_details': exclusions
        }
    
    async def _apply_explicit_exclusions(self, results: Dict[str, Any], exclusions: List[str]) -> Dict[str, Any]:
        """Remove explicitly named Pokemon"""
        if not exclusions:
            return results
            
        excluded_names = set(name.lower() for name in exclusions)
        filtered_results = {}
        
        for endpoint, data in results.items():
            if isinstance(data, list):
                filtered_data = []
                for item in data:
                    pokemon_name = self._extract_pokemon_name(item)
                    if pokemon_name and pokemon_name.lower() not in excluded_names:
                        filtered_data.append(item)
                filtered_results[endpoint] = filtered_data
            else:
                filtered_results[endpoint] = data
        
        print(f"   ✅ Explicit exclusions applied: {len(exclusions)} names excluded")
        return filtered_results
    
    async def _apply_attribute_exclusions(self, results: Dict[str, Any], exclusions: List[str]) -> Dict[str, Any]:
        """Remove Pokemon based on attributes"""
        if not exclusions:
            return results
        
        filtered_results = {}
        
        for endpoint, data in results.items():
            if isinstance(data, list):
                filtered_data = []
                for item in data:
                    should_exclude = False
                    
                    for exclusion in exclusions:
                        if self._matches_attribute_exclusion(item, exclusion):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        filtered_data.append(item)
                
                filtered_results[endpoint] = filtered_data
            else:
                filtered_results[endpoint] = data
        
        print(f"   ✅ Attribute exclusions applied: {len(exclusions)} criteria")
        return filtered_results
    
    async def _apply_semantic_exclusions(self, results: Dict[str, Any], exclusions: List[str], query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply semantic exclusions using LLM"""
        if not exclusions:
            return results
        
        print("   🧠 Applying semantic exclusions with LLM...")
        
        system_prompt = """You are a Pokemon filtering expert. Apply semantic exclusion criteria to filter Pokemon data.

            Semantic exclusions might include subjective terms like:
            - "too common/popular"
            - "too weak/strong" 
            - "not cool enough"
            - "overused in competitive"
            - "too simple design"

            Use your knowledge of Pokemon to make reasonable judgments."""

        filtered_results = {}
        
        for endpoint, data in results.items():
            if isinstance(data, list) and data:
                # Prepare Pokemon data for LLM analysis
                pokemon_data = []
                for item in data:
                    pokemon_name = self._extract_pokemon_name(item)
                    if pokemon_name:
                        pokemon_data.append({
                            'name': pokemon_name,
                            'types': self._extract_types(item),
                            'stats': self._extract_stats(item),
                            'abilities': self._extract_abilities(item)
                        })
                
                if pokemon_data:
                    user_prompt = f"""
                        Original Query Context: {query_analysis.get('primary_intents', [])}

                        Semantic Exclusion Criteria: {exclusions}

                        Pokemon to Filter:
                        {json.dumps(pokemon_data[:20], indent=2, ensure_ascii=False)}

                        Return JSON with Pokemon that should be KEPT (not excluded):
                        {{
                            "retained_pokemon": ["pokemon1", "pokemon2", ...],
                            "exclusion_reasoning": {{
                                "excluded_pokemon": ["pokemon3", "pokemon4"],
                                "reasons": ["too_common", "overused_design", ...]
                            }}
                        }}
                        """

                    try:
                        response = await self.llm.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            response_format={"type": "json_object"}
                        )
                        
                        semantic_result = json.loads(response.choices[0].message.content)
                        retained_names = set(name.lower() for name in semantic_result.get("retained_pokemon", []))
                        
                        # Filter the original data
                        filtered_data = []
                        for item in data:
                            pokemon_name = self._extract_pokemon_name(item)
                            if pokemon_name and pokemon_name.lower() in retained_names:
                                filtered_data.append(item)
                        
                        filtered_results[endpoint] = filtered_data
                        
                    except Exception as e:
                        logger.error(f"Semantic exclusion failed: {e}")
                        filtered_results[endpoint] = data
                else:
                    filtered_results[endpoint] = data
            else:
                filtered_results[endpoint] = data
        
        print(f"   ✅ Semantic exclusions applied: {len(exclusions)} criteria")
        return filtered_results
    
    def _extract_pokemon_name(self, pokemon_data: Dict[str, Any]) -> Optional[str]:
        """Extract Pokemon name from various data structures"""
        if 'name' in pokemon_data:
            return pokemon_data['name']
        elif 'pokemon' in pokemon_data and 'name' in pokemon_data['pokemon']:
            return pokemon_data['pokemon']['name']
        elif 'species' in pokemon_data and 'name' in pokemon_data['species']:
            return pokemon_data['species']['name']
        return None
    
    def _extract_types(self, pokemon_data: Dict[str, Any]) -> List[str]:
        """Extract Pokemon types"""
        types = []
        if 'types' in pokemon_data:
            for type_info in pokemon_data['types']:
                if 'type' in type_info and 'name' in type_info['type']:
                    types.append(type_info['type']['name'])
        return types
    
    def _extract_stats(self, pokemon_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract Pokemon base stats"""
        stats = {}
        if 'stats' in pokemon_data:
            for stat_info in pokemon_data['stats']:
                if 'stat' in stat_info and 'name' in stat_info['stat']:
                    stat_name = stat_info['stat']['name']
                    stat_value = stat_info.get('base_stat', 0)
                    stats[stat_name] = stat_value
        return stats
    
    def _extract_abilities(self, pokemon_data: Dict[str, Any]) -> List[str]:
        """Extract Pokemon abilities"""
        abilities = []
        if 'abilities' in pokemon_data:
            for ability_info in pokemon_data['abilities']:
                if 'ability' in ability_info and 'name' in ability_info['ability']:
                    abilities.append(ability_info['ability']['name'])
        return abilities
    
    def _matches_attribute_exclusion(self, pokemon_data: Dict[str, Any], exclusion: str) -> bool:
        """Check if Pokemon matches an attribute exclusion"""
        exclusion_lower = exclusion.lower()
        
        # Type exclusions
        types = self._extract_types(pokemon_data)
        if any(exclusion_lower in type_name.lower() for type_name in types):
            return True
        
        # Legendary/Mythical checks
        if 'legendary' in exclusion_lower:
            if pokemon_data.get('is_legendary', False):
                return True
        
        if 'mythical' in exclusion_lower:
            if pokemon_data.get('is_mythical', False):
                return True
        
        # Size-based exclusions
        if 'large' in exclusion_lower or 'big' in exclusion_lower:
            height = pokemon_data.get('height', 0)
            weight = pokemon_data.get('weight', 0)
            if height > 20 or weight > 1000:  # Large Pokemon threshold
                return True
        
        return False