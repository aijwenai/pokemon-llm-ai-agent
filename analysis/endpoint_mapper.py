import json
import logging
from typing import Dict, Any, Set

logger = logging.getLogger(__name__)


class IntentEndpointMapper:
    """Maps intents to optimal Pokemon API endpoints"""

    def __init__(self):
        # 🔧 add valid endpoints list to prevent LLM from generating fake endpoints
        self.valid_endpoints = [
            '/pokemon', '/pokemon-species', '/pokemon-form',
            '/type', '/move', '/move-category', '/ability',
            '/pokemon-color', '/pokemon-shape', '/pokemon-habitat',
            '/generation', '/pokedex', '/location', '/location-area', '/region',
            '/evolution-chain', '/evolution-trigger',
            '/egg-group', '/gender', '/nature', '/characteristic', '/growth-rate',
            '/item', '/berry', '/berry-flavor',
            '/contest-type', '/contest-effect',
            '/stat', '/pokeathlon-stat',
            '/encounter-method', '/encounter-condition'
        ]

        self.intent_endpoint_map = {
            'team_building': {
                'primary': ['/type', '/pokemon'],
                'secondary': ['/ability', '/move', '/nature', '/stat'],
                'conditional': {
                    'competitive': ['/nature', '/ability', '/move-category'],
                    'casual': ['/pokemon-species', '/pokemon-color'],
                    'themed': ['/pokemon-color', '/pokemon-shape', '/generation']
                }
            },

            'pokemon_filtering': {
                'primary': ['/pokemon'],
                'filters': {
                    'color': ['/pokemon-color'],
                    'type': ['/type'],
                    'ability': ['/ability'],
                    'size': ['/pokemon-species'],
                    'generation': ['/generation'],
                    'location': ['/location', '/location-area', '/pokemon-habitat'],
                    'rarity': ['/pokemon-species'],
                    'gender': ['/gender'],
                    'shape': ['/pokemon-shape']
                }
            },

            'battle_analysis': {
                'primary': ['/type', '/pokemon', '/move'],
                'secondary': ['/ability', '/stat', '/nature'],
                'advanced': ['/move-category']
            },

            'evolution_info': {
                'primary': ['/evolution-chain', '/pokemon-species'],
                'secondary': ['/item', '/location', '/gender'],
                'triggers': ['/evolution-trigger']
            },

            'breeding_info': {
                'primary': ['/pokemon-species', '/egg-group'],
                'secondary': ['/gender', '/growth-rate', '/nature'],
                'items': ['/item']
            },

            'location_finding': {
                'primary': ['/location', '/location-area'],
                'secondary': ['/pokemon-habitat', '/region'],
                'conditions': ['/encounter-method', '/encounter-condition']
            },

            'competition_strategy': {
                'primary': ['/contest-type', '/contest-effect'],
                'secondary': ['/berry', '/berry-flavor', '/nature'],
                'advanced': ['/pokeathlon-stat']
            },

            'stat_comparison': {
                'primary': ['/pokemon', '/stat'],
                'secondary': ['/nature', '/characteristic'],
                'advanced': ['/growth-rate']
            },

            'move_analysis': {
                'primary': ['/move', '/move-category'],
                'secondary': ['/pokemon'],
                'learning': ['/pokemon']
            },

            'ability_research': {
                'primary': ['/ability'],
                'secondary': ['/pokemon'],
                'context': ['/generation']
            }
        }

        self.fallback_endpoint_strategies = {
            "misc_pokemon_lore": {
                "primary": ["/pokemon-species", "/pokedex"],
                "secondary": ["/generation", "/pokemon"],
                "strategy": "comprehensive_species_data"
            },

            "misc_game_mechanics": {
                "primary": ["/pokemon", "/move", "/ability", "/item"],
                "secondary": ["/type", "/stat", "/nature"],
                "strategy": "broad_game_data"
            },

            "misc_trivia": {
                "primary": ["/pokemon-species", "/pokemon-color", "/pokemon-shape"],
                "secondary": ["/generation", "/pokedex", "/characteristic"],
                "strategy": "categorical_exploration"
            },

            "misc_calculation": {
                "primary": ["/pokemon", "/stat", "/type", "/move"],
                "secondary": ["/nature", "/ability", "/growth-rate"],
                "strategy": "numerical_analysis"
            },

            "misc_hypothetical": {
                "primary": ["/pokemon", "/type", "/move", "/ability"],
                "secondary": ["/stat", "/nature", "/item"],
                "strategy": "scenario_modeling"
            }
        }

    async def generate_endpoint_strategy(self, analysis_result: Dict[str, Any], llm_client) -> Dict[str, Any]:
        """Generate intelligent endpoint selection strategy"""

        intents = analysis_result.get('primary_intents', [])
        entities = analysis_result.get('entities', {})
        fallback_intents = analysis_result.get('fallback_intents', [])
        requires_fallback = analysis_result.get('requires_fallback', False)

        # Start with intent-based endpoints
        endpoint_strategy = {
            'immediate_endpoints': set(),
            'conditional_endpoints': {},
            'supplementary_endpoints': set(),
            'strategy_reasoning': [],
            'execution_order': []
        }

        if requires_fallback and fallback_intents:
            # Handle fallback scenarios
            for fallback_intent in fallback_intents:
                if fallback_intent in self.fallback_endpoint_strategies:
                    strategy = self.fallback_endpoint_strategies[fallback_intent]
                    endpoint_strategy['immediate_endpoints'].update(strategy['primary'])
                    endpoint_strategy['supplementary_endpoints'].update(strategy.get('secondary', []))
                    endpoint_strategy['strategy_reasoning'].append(
                        f"Fallback strategy: {strategy['strategy']} for {fallback_intent}"
                    )
        else:
            # Handle normal intents
            for intent in intents:
                if intent in self.intent_endpoint_map:
                    mapping = self.intent_endpoint_map[intent]
                    endpoint_strategy['immediate_endpoints'].update(mapping.get('primary', []))
                    endpoint_strategy['supplementary_endpoints'].update(mapping.get('secondary', []))
                    endpoint_strategy['strategy_reasoning'].append(
                        f"Intent '{intent}' requires {mapping.get('primary', [])}"
                    )

        # Add entity-specific endpoints
        entity_endpoints = self._get_entity_endpoints(entities)
        endpoint_strategy['immediate_endpoints'].update(entity_endpoints)
        logger.debug(f"immediate Endpoints: {endpoint_strategy['immediate_endpoints']}")
        logger.debug(f"supplementary Endpoints: {endpoint_strategy['supplementary_endpoints']}")

        # Use LLM to optimize endpoint selection
        optimized_strategy = await self._llm_optimize_endpoints(
            endpoint_strategy, analysis_result, llm_client
        )

        return optimized_strategy

    def _get_entity_endpoints(self, entities: Dict[str, Any]) -> Set[str]:
        """Get endpoints based on detected entities"""
        endpoints = set()

        entity_endpoint_map = {
            'pokemon_names': ['/pokemon', '/pokemon-species'],
            'types': ['/type'],
            'colors': ['/pokemon-color'],
            'abilities': ['/ability'],
            'locations': ['/location', '/location-area', '/pokemon-habitat'],
            'items': ['/item'],
            'moves': ['/move'],
            'generations': ['/generation']
        }

        for entity_type, entity_list in entities.items():
            if entity_list and entity_type in entity_endpoint_map:
                endpoints.update(entity_endpoint_map[entity_type])

        return endpoints

    async def _llm_optimize_endpoints(self, strategy: Dict[str, Any], analysis: Dict[str, Any], llm_client) -> Dict[
        str, Any]:
        """Use LLM to optimize endpoint selection strategy"""

        system_prompt = f"""You are a Pokemon API optimization expert. Given the current endpoint strategy, optimize it for efficiency and completeness.

            CRITICAL CONSTRAINT: You can ONLY use these valid endpoints:
            {self.valid_endpoints}

            DO NOT create, suggest, or include ANY endpoints not in this list.

            Consider:
            - Removing redundant endpoints
            - Adding missing critical endpoints from the valid list
            - Optimizing the execution order  
            - Balancing comprehensive coverage with API efficiency

            All endpoints in your response MUST be from the valid list above."""

        user_prompt = f"""
            Query Analysis:
            {json.dumps(analysis, indent=2, ensure_ascii=False)}

            Current Endpoint Strategy:
            {json.dumps({k: list(v) if isinstance(v, set) else v for k, v in strategy.items()}, indent=2, ensure_ascii=False)}

            Valid Endpoints Available:
            {self.valid_endpoints}

            Optimize this strategy and return JSON:
            {{
                "optimized_endpoints": ["final list of endpoints to call - MUST be from valid list"],
                "execution_order": ["order to execute endpoints - MUST be from valid list"],
                "optimization_reasoning": ["why these changes were made"],
                "estimated_efficiency": "high/medium/low",
                "coverage_assessment": "comprehensive/adequate/minimal"
            }}

            REMEMBER: Only use endpoints from the valid list. Do not create new ones."""

        try:
            response = await llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )

            optimization = json.loads(response.choices[0].message.content)

            # 🔧 security check: check if the endpoints are valid
            optimized_endpoints = optimization.get('optimized_endpoints', [])
            execution_order = optimization.get('execution_order', [])

            # filter invalid endpoints
            valid_optimized = [ep for ep in optimized_endpoints if ep in self.valid_endpoints]
            valid_execution = [ep for ep in execution_order if ep in self.valid_endpoints]

            if len(valid_optimized) != len(optimized_endpoints):
                logger.warning(
                    f"LLM generated invalid endpoints, filtered {len(optimized_endpoints) - len(valid_optimized)} invalid ones")

            # if no endpoint after filtering, use fallback
            if not valid_optimized:
                logger.warning("No valid endpoints after filtering, using fallback strategy")
                valid_optimized = ['/pokemon', '/type']
                valid_execution = ['/type', '/pokemon']

            return {
                'endpoints': valid_optimized,
                'execution_order': valid_execution,
                'reasoning': optimization.get('optimization_reasoning', ['Endpoint optimization applied']),
                'efficiency': optimization.get('estimated_efficiency', 'medium'),
                'coverage': optimization.get('coverage_assessment', 'adequate'),
                'original_strategy': strategy,
                'validation_applied': True
            }

        except Exception as e:
            logger.error(f"LLM optimization failed: {e}")

            # Fallback to basic strategy
            all_endpoints = list(strategy['immediate_endpoints']) + list(strategy['supplementary_endpoints'])
            valid_fallback = [ep for ep in all_endpoints if ep in self.valid_endpoints]

            if not valid_fallback:
                valid_fallback = ['/pokemon', '/type']  # basic fallback

            return {
                'endpoints': valid_fallback,
                'execution_order': valid_fallback,
                'reasoning': ['Fallback strategy due to LLM optimization failure'],
                'efficiency': 'medium',
                'coverage': 'basic',
                'original_strategy': strategy,
                'fallback_applied': True
            }