import asyncio
import json
import random
import time
import logging
import openai
from typing import Dict, Any
from datetime import datetime
from dataclasses import asdict

try:
    from ..core.models import ResearchStep, ResearchReport
    from ..analysis import LLMQueryAnalyzer, IntentEndpointMapper, ExclusionHandler
    from ..processing import FallbackQueryProcessor
    from ..api.client import PokemonAPIClient
    from ..api.token_manager import TokenManager
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.models import ResearchStep, ResearchReport
    from analysis import LLMQueryAnalyzer, IntentEndpointMapper, ExclusionHandler
    from processing import FallbackQueryProcessor
    from api.client import PokemonAPIClient
    from api.token_manager import TokenManager

logger = logging.getLogger(__name__)


from typing import Dict, List, Any, Callable, Set, Optional
from dataclasses import dataclass
import asyncio


# In agent.py, move all new class definitions to the top of the file, before the DeepResearchAgent class:

@dataclass
class EndpointConfig:
    """Configuration for a single endpoint"""
    endpoint_path: str
    client_method: str
    entity_key: str = None
    default_samples: List[str] = None
    requires_id: bool = False
    description: str = ""
    emoji: str = "📡"


@dataclass
class FilterResult:
    """Filter result"""
    pokemon_names: Set[str]
    pokemon_species_names: Set[str]
    source_endpoint: str
    filter_type: str


@dataclass
class SmartEndpointConfig:
    """Smart endpoint configuration"""
    endpoint_path: str
    client_method: str
    return_type: str  # 'pokemon' | 'pokemon_species' | 'other'
    filter_capability: str  # 'primary_filter' | 'secondary_filter' | 'detail_only'
    entity_key: str = None
    pokemon_path: str = None  # Path to pokemon in returned data
    default_samples: List[str] = None
    description: str = ""
    emoji: str = "📡"


class OptimizedPokemonRegistry:
    """Optimized Pokemon API registry"""

    def __init__(self):
        self.endpoints = self._initialize_smart_endpoints()

    @staticmethod
    @staticmethod
    def _initialize_smart_endpoints() -> Dict[str, SmartEndpointConfig]:
        """Initialize smart endpoint configuration"""
        return {
            '/pokemon-color': SmartEndpointConfig(
                endpoint_path='/pokemon-color',
                client_method='get_pokemon_color',
                return_type='pokemon_species',
                filter_capability='primary_filter',
                entity_key='colors',
                pokemon_path='pokemon_species',
                default_samples=['red', 'blue', 'green'],
                description="Filter Pokemon by color",
                emoji="🎨"
            ),
            '/pokemon-shape': SmartEndpointConfig(
                endpoint_path='/pokemon-shape',
                client_method='get_pokemon_shape',
                return_type='pokemon_species',
                filter_capability='primary_filter',
                entity_key='shapes',
                pokemon_path='pokemon_species',
                default_samples=['1', '2', '3'],
                description="Filter Pokemon by shape",
                emoji="🔵"
            ),
            '/pokemon-habitat': SmartEndpointConfig(
                endpoint_path='/pokemon-habitat',
                client_method='get_pokemon_habitat',
                return_type='pokemon_species',
                filter_capability='primary_filter',
                entity_key='locations',
                pokemon_path='pokemon_species',
                default_samples=['sea', 'forest', 'mountain'],
                description="Filter Pokemon by habitat",
                emoji="🏞️"
            ),
            '/generation': SmartEndpointConfig(
                endpoint_path='/generation',
                client_method='get_generation',
                return_type='pokemon_species',
                filter_capability='primary_filter',
                entity_key='generations',
                pokemon_path='pokemon_species',
                default_samples=['1', '2', '3'],
                description="Filter Pokemon by generation",
                emoji="📅"
            ),
            '/egg-group': SmartEndpointConfig(
                endpoint_path='/egg-group',
                client_method='get_egg_group',
                return_type='pokemon_species',
                filter_capability='primary_filter',
                pokemon_path='pokemon_species',
                default_samples=['1', '2', '3'],
                description="Filter Pokemon by egg group",
                emoji="🥚"
            ),

            # 🔍 Primary filters - return pokemon
            '/type': SmartEndpointConfig(
                endpoint_path='/type',
                client_method='get_type',
                return_type='pokemon',
                filter_capability='primary_filter',
                pokemon_path='pokemon.pokemon.name',  # Nested path
                entity_key='types',
                default_samples=['fire', 'water', 'grass', 'electric'],
                description="Filter Pokemon by type",
                emoji="⚡"
            ),
            '/ability': SmartEndpointConfig(
                endpoint_path='/ability',
                client_method='get_ability',
                return_type='pokemon',
                filter_capability='primary_filter',
                entity_key='abilities',
                pokemon_path='pokemon.pokemon.name',
                default_samples=['levitate', 'intimidate', 'sturdy'],
                description="Filter Pokemon by ability",
                emoji="✨"
            ),
            '/move': SmartEndpointConfig(
                endpoint_path='/move',
                client_method='get_move',
                return_type='pokemon',
                filter_capability='secondary_filter',
                entity_key='moves',
                pokemon_path='learned_by_pokemon.name',
                default_samples=['tackle', 'thunderbolt', 'surf'],
                description="Filter Pokemon by move",
                emoji="⚔️"
            ),

            # 📋 Detail data endpoints - not used for filtering
            '/pokemon': SmartEndpointConfig(
                endpoint_path='/pokemon',
                client_method='get_pokemon',
                return_type='detail',
                filter_capability='detail_only',
                description="Pokemon detailed battle data",
                emoji="🐛"
            ),
            '/pokemon-species': SmartEndpointConfig(
                endpoint_path='/pokemon-species',
                client_method='get_pokemon_species',
                return_type='detail',
                filter_capability='detail_only',
                description="Pokemon species detailed information",
                emoji="🧬"
            ),

            # 🔗 Evolution related endpoints
            '/evolution-chain': SmartEndpointConfig(
                endpoint_path='/evolution-chain',
                client_method='get_evolution_chain',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3', '4'],
                description="Pokemon evolution chain",
                emoji="🔗"
            ),
            '/evolution-trigger': SmartEndpointConfig(
                endpoint_path='/evolution-trigger',
                client_method='get_evolution_trigger',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Evolution trigger conditions",
                emoji="⭐"
            ),

            # 🏞️ Location related endpoints
            '/location': SmartEndpointConfig(
                endpoint_path='/location',
                client_method='get_location',
                return_type='other',
                filter_capability='secondary_filter',
                entity_key='locations',
                default_samples=['1', '2', '3'],
                description="Game locations",
                emoji="🗺️"
            ),
            '/location-area': SmartEndpointConfig(
                endpoint_path='/location-area',
                client_method='get_location_area',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Location areas",
                emoji="📍"
            ),
            '/region': SmartEndpointConfig(
                endpoint_path='/region',
                client_method='get_region',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Game regions",
                emoji="🌍"
            ),

            # 🎒 Item related endpoints
            '/item': SmartEndpointConfig(
                endpoint_path='/item',
                client_method='get_item',
                return_type='pokemon',
                filter_capability='secondary_filter',
                entity_key='items',
                pokemon_path='held_by_pokemon.pokemon.name',
                default_samples=['poke-ball', 'master-ball', 'potion'],
                description="Game items",
                emoji="🎒"
            ),
            '/berry': SmartEndpointConfig(
                endpoint_path='/berry',
                client_method='get_berry',
                return_type='other',
                filter_capability='secondary_filter',
                entity_key='berries',
                default_samples=['cheri', 'chesto', 'pecha'],
                description="Pokemon berries",
                emoji="🍓"
            ),
            '/berry-flavor': SmartEndpointConfig(
                endpoint_path='/berry-flavor',
                client_method='get_berry_flavor',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Berry flavors",
                emoji="👅"
            ),

            # 🏆 Contest related endpoints
            '/contest-type': SmartEndpointConfig(
                endpoint_path='/contest-type',
                client_method='get_contest_type',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['cool', 'beauty', 'cute'],
                description="Contest types",
                emoji="🏆"
            ),
            '/contest-effect': SmartEndpointConfig(
                endpoint_path='/contest-effect',
                client_method='get_contest_effect',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Contest effects",
                emoji="✨"
            ),

            # 👁️ Encounter related endpoints
            '/encounter-method': SmartEndpointConfig(
                endpoint_path='/encounter-method',
                client_method='get_encounter_method',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Encounter methods",
                emoji="👁️"
            ),
            '/encounter-condition': SmartEndpointConfig(
                endpoint_path='/encounter-condition',
                client_method='get_encounter_condition',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Encounter conditions",
                emoji="🌙"
            ),

            # 🎮 Game related endpoints
            '/pokedex': SmartEndpointConfig(
                endpoint_path='/pokedex',
                client_method='get_pokedex',
                return_type='pokemon_species',
                filter_capability='primary_filter',
                pokemon_path='pokemon_entries.pokemon_species.name',
                default_samples=['1', '2'],  # National, Kanto
                description="Pokemon Pokedex",
                emoji="📖"
            ),

            # 🧬 Breeding and genetics endpoints
            '/gender': SmartEndpointConfig(
                endpoint_path='/gender',
                client_method='get_gender',
                return_type='pokemon_species',
                filter_capability='secondary_filter',
                pokemon_path='pokemon_species_details.pokemon_species.name',
                default_samples=['1', '2', '3'],
                description="Gender",
                emoji="⚥"
            ),
            '/growth-rate': SmartEndpointConfig(
                endpoint_path='/growth-rate',
                client_method='get_growth_rate',
                return_type='pokemon_species',
                filter_capability='secondary_filter',
                pokemon_path='pokemon_species.name',
                default_samples=['1', '2', '3'],
                description="Growth rate",
                emoji="📈"
            ),
            '/characteristic': SmartEndpointConfig(
                endpoint_path='/characteristic',
                client_method='get_characteristic',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Characteristic",
                emoji="🎯"
            ),

            # 🔧 Auxiliary data endpoints
            '/nature': SmartEndpointConfig(
                endpoint_path='/nature',
                client_method='get_nature',
                return_type='other',
                filter_capability='secondary_filter',
                entity_key='natures',
                default_samples=['adamant', 'modest', 'timid'],
                description="Pokemon nature",
                emoji="🧠"
            ),
            '/stat': SmartEndpointConfig(
                endpoint_path='/stat',
                client_method='get_stat',
                return_type='other',
                filter_capability='secondary_filter',
                entity_key='stats',
                default_samples=['hp', 'attack', 'defense'],
                description="Pokemon stats",
                emoji="📊"
            ),
            '/pokeathlon-stat': SmartEndpointConfig(
                endpoint_path='/pokeathlon-stat',
                client_method='get_pokeathlon_stat',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Pokemon pokeathlon stats",
                emoji="🏃"
            ),

            # 📂 Move related endpoints
            '/move-category': SmartEndpointConfig(
                endpoint_path='/move-category',
                client_method='get_move_category',
                return_type='other',
                filter_capability='secondary_filter',
                default_samples=['1', '2', '3'],
                description="Move category",
                emoji="📂"
            ),
        }


class SmartExecutionStrategy:
    """Smart execution strategy"""

    def __init__(self):
        self.registry = OptimizedPokemonRegistry()
        self.filter_cache = {}

    async def execute_smart_strategy(self, strategy: Dict[str, Any], analysis: Dict[str, Any],
                                     api_client) -> Dict[str, Any]:
        """Execute smart strategy - use all fields of SmartEndpointConfig"""

        endpoints = strategy.get('endpoints', [])
        entities = analysis.get('entities', {})
        intents = analysis.get('primary_intents', [])

        print("🧠 Executing Smart Strategy (Enhanced Version)...")

        # Use filter_capability for intelligent classification
        primary_filter_endpoints = []
        secondary_filter_endpoints = []
        detail_endpoints = []
        
        for endpoint_name in endpoints:
            config = self.registry.endpoints.get(endpoint_name)
            if config:
                if config.filter_capability == 'primary_filter':
                    primary_filter_endpoints.append(endpoint_name)
                elif config.filter_capability == 'secondary_filter':
                    secondary_filter_endpoints.append(endpoint_name)
                elif config.filter_capability == 'detail_only':
                    detail_endpoints.append(endpoint_name)

        # Intelligent sorting: Primary filter -> Secondary filter -> Detail data
        prioritized_endpoints = primary_filter_endpoints + secondary_filter_endpoints + detail_endpoints

        print(f"   📊 Prioritized by capability: Primary({len(primary_filter_endpoints)}) -> Secondary({len(secondary_filter_endpoints)}) -> Detail({len(detail_endpoints)})")
        print(f"   🎯 Execution order: {prioritized_endpoints}")

        tasks = []
        task_configs = []  

        for endpoint_name in prioritized_endpoints[:15]:  
            config = self.registry.endpoints.get(endpoint_name)

            if not config:
                continue

            client_method = getattr(api_client, config.client_method, None)
            if not client_method:
                continue

            # Get data - optimize based on return_type
            data_to_process = []
            if config.entity_key and config.entity_key in entities:
                entity_values = entities[config.entity_key]
                if entity_values:
                    # Adjust sample size based on return_type
                    if config.return_type == 'pokemon_species':
                        data_to_process = entity_values[:2]  # pokemon_species endpoint usually returns more data
                    elif config.return_type == 'pokemon':
                        data_to_process = entity_values[:3]  # pokemon endpoint
                    else:
                        data_to_process = entity_values[:4]  # other endpoints
                    print(f"      🎯 Found entities for {config.entity_key} ({config.return_type}): {data_to_process}")
            else:
                print(f"      ⚠️ No entities found for {config.entity_key}, available: {list(entities.keys())}")

            if not data_to_process and config.default_samples:
                # Adjust default sample size based on return_type
                if config.return_type == 'pokemon_species':
                    max_samples = 3  # Fewer samples because returned data is richer
                elif config.return_type == 'pokemon':
                    max_samples = 4  # Medium sample size
                else:
                    max_samples = 5  # Other types can have more samples
                    
                if len(config.default_samples) > 500:
                    data_to_process = random.sample(config.default_samples, min(max_samples, 15))
                else:
                    data_to_process = config.default_samples[:max_samples]
                    
            print(f"      📦 Processing {len(data_to_process)} items for {endpoint_name} ({config.return_type})")
            
            # Create tasks
            for data_item in data_to_process:
                tasks.append(client_method(data_item))
                task_configs.append({
                    'config': config,
                    'endpoint': endpoint_name,
                    'data_item': data_item,
                    'key': f"{endpoint_name.lstrip('/')}_{data_item}"
                })

        print(f"   📡 Executing {len(tasks)} smart API calls...")

        # Execute tasks
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        success_count = 0

        # Intelligent result processing - use pokemon_path to extract related data
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                print(f"   ❌ Task failed: {task_configs[i]['key']}")
            elif result:
                config_info = task_configs[i]
                config = config_info['config']
                
                # Use pokemon_path to extract Pokemon related data
                processed_result = self._extract_pokemon_data_by_path(result, config)
                
                results[config_info['key']] = processed_result
                success_count += 1
                print(f"   ✅ {config_info['endpoint']} -> {config.return_type} data extracted")

        print(f"   ✅ Smart strategy complete: {success_count} successful with intelligent data extraction")
        logger.debug(f"executing smart strategy results: {results}")
        return results
    
    def _extract_pokemon_data_by_path(self, api_response: Dict[str, Any], config: SmartEndpointConfig) -> Dict[str, Any]:
        """Extract Pokemon data based on SmartEndpointConfig's pokemon_path"""
        
        if not config.pokemon_path:
            # If there is no pokemon_path, return the summary of the original response
            return self._create_basic_summary(api_response, config)
        
        try:
            logger.debug(f"🔍 Extracting Pokemon data using path: {config.pokemon_path}")
            logger.debug(f"🔍 API response keys: {list(api_response.keys()) if isinstance(api_response, dict) else 'Not a dict'}")
            
            # Parse pokemon_path and extract data intelligently
            path_parts = config.pokemon_path.split('.')
            
            # Special handling for common Pokemon API path patterns
            pokemon_data = self._traverse_pokemon_path(api_response, path_parts, config.endpoint_path)
            
            if pokemon_data is None:
                logger.debug(f"⚠️ Pokemon path traversal failed for {config.endpoint_path}")
                return self._create_basic_summary(api_response, config)
            
            # Create structured result
            extracted_result = {
                'endpoint_type': config.endpoint_path,
                'return_type': config.return_type,
                'filter_capability': config.filter_capability,
                'pokemon_data_extracted': True,
                'original_data_summary': {
                    'name': api_response.get('name'),
                    'id': api_response.get('id'),
                    'total_fields': len(api_response) if isinstance(api_response, dict) else 0
                }
            }
            
            # Process Pokemon data based on return_type, including API context information
            if config.return_type == 'pokemon_species':
                if isinstance(pokemon_data, list):
                    extracted_result['pokemon_species_names'] = [
                        item.get('name') if isinstance(item, dict) else str(item) 
                        for item in pokemon_data[:15]  
                    ]
                    extracted_result['pokemon_species_count'] = len(pokemon_data)
                else:
                    extracted_result['pokemon_species_data'] = pokemon_data
                
                # Add API context information for answering more complex questions
                extracted_result['api_context'] = self._extract_api_context(api_response, 'pokemon_species')
                    
            elif config.return_type == 'pokemon':
                if isinstance(pokemon_data, list):
                    # Intelligent extraction of pokemon names
                    extracted_names = []
                    for item in pokemon_data[:15]:  
                        if isinstance(item, dict):
                            # Try multiple possible name paths
                            name = (item.get('name') or 
                                   item.get('pokemon', {}).get('name') if isinstance(item.get('pokemon'), dict) else None or
                                   str(item))
                            extracted_names.append(name)
                        else:
                            extracted_names.append(str(item))
                    
                    extracted_result['pokemon_names'] = extracted_names
                    extracted_result['pokemon_count'] = str(len(pokemon_data))
                    logger.debug(f"✅ Extracted {len(extracted_names)} Pokemon names: {extracted_names[:5]}...")
                else:
                    extracted_result['pokemon_data'] = pokemon_data
                
                # Add API context information for answering more complex questions  
                extracted_result['api_context'] = self._extract_api_context(api_response, 'pokemon')
            else:
                extracted_result['other_data'] = pokemon_data
            
            return extracted_result
            
        except Exception as e:
            # Extraction failed, return basic summary
            logger.warning(f"Pokemon data extraction failed for {config.endpoint_path}: {e}")
            return self._create_basic_summary(api_response, config)
    
    def _traverse_pokemon_path(self, api_response: Dict[str, Any], path_parts: List[str], endpoint_path: str) -> Any:
        """Intelligent traversal of Pokemon path, handling arrays and nested structures"""
        
        current_data = api_response
        logger.debug(f"🔍 Starting path traversal for {endpoint_path}: {' -> '.join(path_parts)}")
        
        try:
            for i, part in enumerate(path_parts):
                logger.debug(f"🔍 Step {i+1}: Accessing '{part}' from {type(current_data).__name__}")
                
                if isinstance(current_data, dict):
                    # Dictionary type: directly access key
                    if part in current_data:
                        current_data = current_data[part]
                        logger.debug(f"✅ Found '{part}' in dict, now have {type(current_data).__name__}")
                    else:
                        logger.debug(f"❌ Key '{part}' not found in dict keys: {list(current_data.keys())[:5]}...")
                        return None
                        
                elif isinstance(current_data, list):
                    # Array type: need to traverse each element in the array to extract data
                    logger.debug(f"📋 Processing list of {len(current_data)} items")
                    
                    if i == len(path_parts) - 1:
                        # This is the last path part, extract from each array item
                        extracted_items = []
                        for item in current_data[:15]:  
                            if isinstance(item, dict) and part in item:
                                extracted_items.append(item[part])
                        logger.debug(f"✅ Extracted {len(extracted_items)} items from array")
                        return extracted_items
                    else:
                        # Not the last path, need to continue traversing all items
                        # Collect all valid intermediate results, then continue processing remaining path
                        intermediate_items = []
                        for item in current_data[:15]:  
                            if isinstance(item, dict) and part in item:
                                intermediate_items.append(item[part])
                        
                        if not intermediate_items:
                            logger.debug(f"❌ No array items contain '{part}'")
                            return None
                        
                        logger.debug(f"✅ Found {len(intermediate_items)} intermediate items for '{part}'")
                        
                        # If there is only one result, continue processing directly
                        if len(intermediate_items) == 1:
                            current_data = intermediate_items[0]
                            logger.debug(f"✅ Single intermediate item, continuing with {type(current_data).__name__}")
                        else:
                            # Multiple results, need to process remaining path for each result
                            remaining_path = path_parts[i+1:]
                            logger.debug(f"🔀 Multiple items ({len(intermediate_items)}), processing remaining path: {remaining_path}")
                            
                            all_results = []
                            for intermediate_item in intermediate_items:
                                if remaining_path:
                                    # Recursively process remaining path, directly pass in intermediate item instead of wrapping in a dictionary
                                    sub_result = self._traverse_pokemon_path(intermediate_item, remaining_path, endpoint_path)
                                    if sub_result is not None:
                                        if isinstance(sub_result, list):
                                            all_results.extend(sub_result)
                                        else:
                                            all_results.append(sub_result)
                                else:
                                    # No remaining path, return this item directly
                                    all_results.append(intermediate_item)
                            
                            logger.debug(f"✅ Collected {len(all_results)} final results from multiple paths")
                            return all_results if all_results else None
                else:
                    # Neither dictionary nor array, cannot continue traversing
                    logger.debug(f"❌ Cannot traverse '{part}' from {type(current_data).__name__}")
                    return None
            
            logger.debug(f"✅ Path traversal complete, final result: {type(current_data).__name__}")
            return current_data
            
        except Exception as e:
            logger.warning(f"Path traversal failed for {endpoint_path}: {e}")
            return None
    
    def _extract_api_context(self, api_response: Dict[str, Any], return_type: str) -> str:
        """Extract API response context information, limited to 200-300 characters"""
        try:
            if not isinstance(api_response, dict):
                return str(api_response)[:250]
            
            context_parts = []
            char_limit = 300
            
            # Extract different key information based on return_type
            if return_type == 'pokemon':
                # For Pokemon type, extract type-related information
                if 'name' in api_response:
                    context_parts.append(f"Type: {api_response['name']}")
                    
                if 'damage_relations' in api_response:
                    damage_relations = api_response['damage_relations']
                    if 'super_effective_against' in damage_relations:
                        effective_against = [t['name'] for t in damage_relations['super_effective_against'][:3]]
                        if effective_against:
                            context_parts.append(f"Super effective against: {', '.join(effective_against)}")
                    
                    if 'weak_to' in damage_relations or 'double_damage_from' in damage_relations:
                        weak_to = damage_relations.get('double_damage_from', damage_relations.get('weak_to', []))
                        weak_names = [t['name'] for t in weak_to[:3]]
                        if weak_names:
                            context_parts.append(f"Weak to: {', '.join(weak_names)}")
                
                # Extract Pokemon list information
                if 'pokemon' in api_response:
                    pokemon_list = api_response['pokemon']
                    if pokemon_list:
                        sample_pokemon = []
                        for p in pokemon_list[:5]:
                            if isinstance(p, dict) and 'pokemon' in p:
                                sample_pokemon.append(p['pokemon'].get('name', ''))
                        if sample_pokemon:
                            context_parts.append(f"Includes Pokemon: {', '.join(sample_pokemon)}")
            
            elif return_type == 'pokemon_species':
                # For Pokemon species, extract color, habitat, etc.
                if 'name' in api_response:
                    context_parts.append(f"Category: {api_response['name']}")
                
                # Extract species list
                if 'pokemon_species' in api_response:
                    species_list = api_response['pokemon_species']
                    if species_list:
                        sample_species = []
                        for s in species_list[:5]:
                            if isinstance(s, dict):
                                sample_species.append(s.get('name', ''))
                        if sample_species:
                            context_parts.append(f"Includes species: {', '.join(sample_species)}")
                
                # Extract descriptive information
                if 'id' in api_response:
                    context_parts.append(f"ID: {api_response['id']}")
            
            # Extract generic information
            if 'generation' in api_response and isinstance(api_response['generation'], dict):
                gen_name = api_response['generation'].get('name', '')
                if gen_name:
                    context_parts.append(f"Generation: {gen_name}")
            
            # Merge information and limit length
            if context_parts:
                full_context = '; '.join(context_parts)
                if len(full_context) > char_limit:
                    return full_context[:char_limit-3] + "..."
                return full_context
            else:
                # If there is no specific information, return generic summary
                response_str = str(api_response)
                if len(response_str) > char_limit:
                    return response_str[:char_limit-3] + "..."
                return response_str
                
        except Exception as e:
            logger.debug(f"API context extraction failed: {e}")
            # Return simplified response summary when failed
            return str(api_response)[:250]
    
    def _create_basic_summary(self, api_response: Dict[str, Any], config: SmartEndpointConfig) -> Dict[str, Any]:
        """Create basic summary for endpoints without pokemon_path"""
        return {
            'endpoint_type': config.endpoint_path,
            'return_type': config.return_type,
            'filter_capability': config.filter_capability,
            'pokemon_data_extracted': False,
            'summary': {
                'name': api_response.get('name'),
                'id': api_response.get('id'),
                'description': config.description,
                'data_size': len(api_response) if isinstance(api_response, dict) else 0
            }
        }


class PokemonEndpointRegistry:
    """Pokemon API Endpoint registry"""

    def __init__(self):
        self.endpoints = self._initialize_endpoints()
        self.llm_mappings = self._initialize_llm_mappings()

    def _initialize_endpoints(self) -> Dict[str, EndpointConfig]:
        """Initialize all available endpoint configurations"""
        return {
            # core Pokemon data
            '/pokemon': EndpointConfig(
                endpoint_path='/pokemon',
                client_method='get_pokemon',
                entity_key='pokemon_names',
                default_samples=[str(i) for i in range(1, 1000)],  # First 50 Pokemon
                description="Pokemon basic data",
                emoji="🐛"
            ),
            '/pokemon-species': EndpointConfig(
                endpoint_path='/pokemon-species',
                client_method='get_pokemon_species',
                entity_key='pokemon_names',
                default_samples=[str(i) for i in range(1, 1000)],
                description="Pokemon species information",
                emoji="🧬"
            ),
            '/pokemon-form': EndpointConfig(
                endpoint_path='/pokemon-form',
                client_method='get_pokemon_form',
                entity_key='pokemon_names',
                default_samples=['1', '25'],
                description="Pokemon form information",
                emoji="🔄"
            ),

            # type system
            '/type': EndpointConfig(
                endpoint_path='/type',
                client_method='get_type',
                entity_key='types',
                default_samples=['fire', 'water', 'grass', 'electric'],
                description="Pokemon type information",
                emoji="⚡"
            ),

            # move system
            '/move': EndpointConfig(
                endpoint_path='/move',
                client_method='get_move',
                entity_key='moves',
                default_samples=['tackle', 'thunderbolt', 'surf', 'fly'],
                description="Pokemon move information",
                emoji="⚔️"
            ),
            '/move-category': EndpointConfig(
                endpoint_path='/move-category',
                client_method='get_move_category',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Move category",
                emoji="📂"
            ),

            # ability system
            '/ability': EndpointConfig(
                endpoint_path='/ability',
                client_method='get_ability',
                entity_key='abilities',
                default_samples=['levitate', 'intimidate', 'sturdy', 'overgrow'],
                description="Pokemon ability",
                emoji="✨"
            ),

            # color system
            '/pokemon-color': EndpointConfig(
                endpoint_path='/pokemon-color',
                client_method='get_pokemon_color',
                entity_key='colors',
                default_samples=['red', 'blue', 'green', 'yellow'],
                description="Pokemon color classification",
                emoji="🎨"
            ),
            '/pokemon-shape': EndpointConfig(
                endpoint_path='/pokemon-shape',
                client_method='get_pokemon_shape',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Pokemon shape classification",
                emoji="🔵"
            ),
            '/pokemon-habitat': EndpointConfig(
                endpoint_path='/pokemon-habitat',
                client_method='get_pokemon_habitat',
                entity_key='locations',
                default_samples=['sea', 'forest', 'mountain', 'cave'],
                description="Pokemon habitat",
                emoji="🏞️"
            ),

            # generation and game data
            '/generation': EndpointConfig(
                endpoint_path='/generation',
                client_method='get_generation',
                entity_key='generations',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Pokemon generation information",
                emoji="📅"
            ),
            '/pokedex': EndpointConfig(
                endpoint_path='/pokedex',
                client_method='get_pokedex',
                default_samples=['1', '2'],
                requires_id=True,
                description="Pokemon pokedex",
                emoji="📖"
            ),

            # location system
            '/location': EndpointConfig(
                endpoint_path='/location',
                client_method='get_location',
                entity_key='locations',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Game location",
                emoji="🗺️"
            ),
            '/location-area': EndpointConfig(
                endpoint_path='/location-area',
                client_method='get_location_area',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Location area",
                emoji="📍"
            ),
            '/region': EndpointConfig(
                endpoint_path='/region',
                client_method='get_region',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Game region",
                emoji="🌍"
            ),

            # evolution system
            '/evolution-chain': EndpointConfig(
                endpoint_path='/evolution-chain',
                client_method='get_evolution_chain',
                default_samples=['1', '2', '3', '4'],
                requires_id=True,
                description="Evolution chain",
                emoji="🔗"
            ),
            '/evolution-trigger': EndpointConfig(
                endpoint_path='/evolution-trigger',
                client_method='get_evolution_trigger',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Evolution trigger condition",
                emoji="⭐"
            ),

            # egg and genetic system
            '/egg-group': EndpointConfig(
                endpoint_path='/egg-group',
                client_method='get_egg_group',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Egg group",
                emoji="🥚"
            ),
            '/gender': EndpointConfig(
                endpoint_path='/gender',
                client_method='get_gender',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Gender",
                emoji="⚥"
            ),
            '/nature': EndpointConfig(
                endpoint_path='/nature',
                client_method='get_nature',
                entity_key='natures',
                default_samples=['adamant', 'modest', 'timid', 'jolly'],
                description="Pokemon nature",
                emoji="🧠"
            ),
            '/characteristic': EndpointConfig(
                endpoint_path='/characteristic',
                client_method='get_characteristic',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Individual characteristics",
                emoji="🎯"
            ),
            '/growth-rate': EndpointConfig(
                endpoint_path='/growth-rate',
                client_method='get_growth_rate',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Growth rate",
                emoji="📈"
            ),

            # item system
            '/item': EndpointConfig(
                endpoint_path='/item',
                client_method='get_item',
                entity_key='items',
                default_samples=['poke-ball', 'master-ball', 'potion', 'rare-candy'],
                description="Game items",
                emoji="🎒"
            ),
            '/berry': EndpointConfig(
                endpoint_path='/berry',
                client_method='get_berry',
                entity_key='berries',
                default_samples=['cheri', 'chesto', 'pecha', 'rawst'],
                description="Pokemon berries",
                emoji="🍓"
            ),
            '/berry-flavor': EndpointConfig(
                endpoint_path='/berry-flavor',
                client_method='get_berry_flavor',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Berry flavor",
                emoji="👅"
            ),

            # contest system
            '/contest-type': EndpointConfig(
                endpoint_path='/contest-type',
                client_method='get_contest_type',
                default_samples=['cool', 'beauty', 'cute', 'smart', 'tough'],
                description="Contest type",
                emoji="🏆"
            ),
            '/contest-effect': EndpointConfig(
                endpoint_path='/contest-effect',
                client_method='get_contest_effect',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Contest effect",
                emoji="✨"
            ),

            # stat system
            '/stat': EndpointConfig(
                endpoint_path='/stat',
                client_method='get_stat',
                entity_key='stats',
                default_samples=['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed'],
                description="Pokemon stats",
                emoji="📊"
            ),
            '/pokeathlon-stat': EndpointConfig(
                endpoint_path='/pokeathlon-stat',
                client_method='get_pokeathlon_stat',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Pokemon pokeathlon stats",
                emoji="🏃"
            ),

            # encounter system
            '/encounter-method': EndpointConfig(
                endpoint_path='/encounter-method',
                client_method='get_encounter_method',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Encounter method",
                emoji="👁️"
            ),
            '/encounter-condition': EndpointConfig(
                endpoint_path='/encounter-condition',
                client_method='get_encounter_condition',
                default_samples=['1', '2', '3'],
                requires_id=True,
                description="Encounter condition",
                emoji="🌙"
            ),
        }

    def _initialize_llm_mappings(self) -> Dict[str, str]:
        """Initialize LLM-generated endpoint name to real endpoint mapping"""
        return {
            # team suggestions related
            'team_suggestions': '/type',
            'team_building': '/type',
            'team_composition': '/type',

            # popularity and statistics
            'popularity_statistics': '/pokemon',
            'usage_statistics': '/pokemon',
            'pokemon_stats': '/stat',

            # move effectiveness related
            'move_effectiveness': '/move',
            'battle_mechanics': '/move',
            'move_analysis': '/move',

            # type related
            'type_effectiveness': '/type',
            'type_analysis': '/type',
            'synergistic_combinations': '/type',

            # evolution related
            'evolution_paths': '/evolution-chain',
            'evolution_analysis': '/evolution-chain',

            # habitat related
            'habitat_analysis': '/pokemon-habitat',
            'location_analysis': '/location',

            # ability related
            'ability_analysis': '/ability',
            'ability_effectiveness': '/ability',

            # item related
            'item_analysis': '/item',
            'item_effectiveness': '/item',

            # generation related
            'generation_data': '/generation',
            'generation_analysis': '/generation',

            # pokedex related
            'pokedex_data': '/pokedex',
            'pokedex_analysis': '/pokedex',

            # nature related
            'nature_analysis': '/nature',
            'personality_analysis': '/nature',

            # contest related
            'contest_data': '/contest-type',
            'contest_analysis': '/contest-type',

            # berry related
            'berry_analysis': '/berry',
            'berry_data': '/berry',
        }

    def get_endpoint_config(self, endpoint_name: str) -> EndpointConfig:
        """Get endpoint configuration"""
        # Standardize endpoint name
        clean_name = endpoint_name.lstrip('/')
        standard_name = f"/{clean_name}"

        # direct match
        if standard_name in self.endpoints:
            return self.endpoints[standard_name]

        # LLM mapping match
        if clean_name in self.llm_mappings:
            mapped_endpoint = self.llm_mappings[clean_name]
            return self.endpoints[mapped_endpoint]

        # return None if not found
        return None

    def get_all_endpoints(self) -> List[str]:
        """Get all available endpoints"""
        return list(self.endpoints.keys())

    def get_endpoints_by_category(self) -> Dict[str, List[str]]:
        """Organize endpoints by category"""
        categories = {
            "core data": ['/pokemon', '/pokemon-species', '/pokemon-form'],
            "battle system": ['/type', '/move', '/ability', '/stat'],
            "classification system": ['/pokemon-color', '/pokemon-shape', '/pokemon-habitat'],
            "generation data": ['/generation', '/pokedex'],
            "location system": ['/location', '/location-area', '/region'],
            "evolution system": ['/evolution-chain', '/evolution-trigger'],
            "egg and genetic system": ['/egg-group', '/gender', '/nature', '/characteristic', '/growth-rate'],
            "item system": ['/item', '/berry', '/berry-flavor'],
            "contest system": ['/contest-type', '/contest-effect'],
            "encounter system": ['/encounter-method', '/encounter-condition'],
            "other": ['/move-category', '/pokeathlon-stat']
        }
        return categories


class DeepResearchAgent:
    """Main orchestrator implementing the complete deep research process"""

    def __init__(self, openai_api_key: str):
        self.llm_client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.query_analyzer = LLMQueryAnalyzer(self.llm_client)
        self.endpoint_mapper = IntentEndpointMapper()
        self.exclusion_handler = ExclusionHandler(self.llm_client)
        self.fallback_processor = FallbackQueryProcessor(self.llm_client)
        self.research_steps = []
        self.start_time = None

    async def conduct_deep_research(self, user_query: str) -> ResearchReport:
        """Main deep research orchestration method"""

        self.start_time = time.time()
        print(f"\n🔬 POKEMON DEEP RESEARCH AGENT")
        print("="*80)
        print(f"Query: '{user_query}'")
        print("="*80)

        try:
            # Step 1: Comprehensive Query Analysis
            print("\n📊 Step 1: Comprehensive Query Analysis")
            step_start = time.time()

            query_analysis = await self.query_analyzer.analyze_query_comprehensive(user_query)

            step = ResearchStep(
                step_number=1,
                description="LLM-powered comprehensive query analysis",
                action_type="intent_analysis",
                inputs={"user_query": user_query},
                outputs=query_analysis,
                reasoning="Deep analysis of intents, entities, exclusions, and research requirements",
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - step_start
            )
            self.research_steps.append(step)

            print(f"   🎯 Primary Intents: {query_analysis.get('primary_intents', [])}")
            print(f"   🔍 Entities Found: {len([e for entities in query_analysis.get('entities', {}).values() for e in entities])}")
            print(f"   🚫 Has Exclusions: {query_analysis.get('exclusions', {}).get('has_exclusions', False)}")
            print(f"   📈 Complexity: {query_analysis.get('query_structure', {}).get('complexity', 'unknown')}")

            # Step 2: Intelligent Endpoint Strategy Generation
            print("\n🎯 Step 2: Intelligent Endpoint Strategy Generation")
            step_start = time.time()

            endpoint_strategy = await self.endpoint_mapper.generate_endpoint_strategy(
                query_analysis, self.llm_client
            )

            step = ResearchStep(
                step_number=2,
                description="LLM-optimized endpoint selection strategy",
                action_type="endpoint_selection",
                inputs=query_analysis,
                outputs=endpoint_strategy,
                reasoning="Strategic endpoint selection based on intents and entities",
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - step_start
            )
            self.research_steps.append(step)

            print(f"   📡 Selected Endpoints: {len(endpoint_strategy.get('endpoints', []))}")
            logger.debug(f"Chosen endpoints: {endpoint_strategy.get('endpoints', [])}")
            print(f"   ⚡ Efficiency Rating: {endpoint_strategy.get('efficiency', 'unknown')}")
            print(f"   📋 Coverage: {endpoint_strategy.get('coverage', 'unknown')}")

            # Step 3: Strategic API Data Collection
            print("\n📡 Step 3: Strategic API Data Collection")
            step_start = time.time()

            async with PokemonAPIClient() as api_client:
                api_results = await self._execute_endpoint_strategy(
                    endpoint_strategy, query_analysis, api_client
                )
                # get statistics in async with block
                api_calls_count = len(api_client.api_calls)
                data_sources_count = len(api_results)

            step = ResearchStep(
                step_number=3,
                description="Execute optimized API calls",
                action_type="api_call",
                inputs=endpoint_strategy,
                outputs={"api_calls_made": api_calls_count, "data_collected": True},
                reasoning="Systematic data collection following LLM-optimized strategy",
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - step_start
            )
            self.research_steps.append(step)

            print(f"   ✅ API Calls Made: {api_calls_count}")
            print(f"   💾 Data Sources: {data_sources_count}")

            # Step 4: Multi-Layer Exclusion Processing
            print("\n🚫 Step 4: Multi-Layer Exclusion Processing")
            step_start = time.time()
            exclusion_results = await self.exclusion_handler.process_exclusions(
                query_analysis, api_results
            )
            logger.debug("API results: {}".format(api_results))
            step = ResearchStep(
                step_number=4,
                description="Apply intelligent exclusion filtering",
                action_type="exclusion_filtering",
                inputs={"raw_data": api_results, "exclusions": query_analysis.get('exclusions', {})},
                outputs=exclusion_results,
                reasoning="Multi-stage exclusion processing including semantic filtering",
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - step_start
            )
            self.research_steps.append(step)

            filtered_results = exclusion_results['filtered_results']
            logger.debug("filtered results: {}".format(filtered_results))

            # Step 5: Fallback Processing (if needed)
            if query_analysis.get('requires_fallback', False):
                print("\n🔄 Step 5: Fallback Query Processing")
                step_start = time.time()

                fallback_results = await self.fallback_processor.handle_fallback_query(
                    user_query, query_analysis, filtered_results
                )

                step = ResearchStep(
                    step_number=5,
                    description="Handle fallback query category",
                    action_type="fallback_processing",
                    inputs={"query": user_query, "analysis": query_analysis},
                    outputs=fallback_results,
                    reasoning="Specialized handling for fallback query categories",
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=time.time() - step_start
                )
                self.research_steps.append(step)

            # Step 6: Comprehensive Research Synthesis
            print("\n🧠 Final Step: Comprehensive Research Synthesis")
            step_start = time.time()

            synthesis_results = await self._synthesize_research_findings(
                user_query, query_analysis, endpoint_strategy,
                filtered_results, exclusion_results
            )
            logger.debug("synthesis_results is {}".format(synthesis_results))
            logger.debug("synthesis_results is {}".format(synthesis_results))
            step = ResearchStep(
                step_number=len(self.research_steps) + 1,
                description="LLM synthesis of all research findings",
                action_type="synthesis",
                inputs={"all_research_data": "comprehensive_context"},
                outputs=synthesis_results,
                reasoning="Intelligent synthesis combining all research stages",
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - step_start
            )
            self.research_steps.append(step)

            # Create comprehensive research report
            total_duration = time.time() - self.start_time
            # logger.debug(f"query analysis is like: {query_analysis}")
            report = ResearchReport(
                query=user_query,
                research_goal=query_analysis.get('primary_intents', ['general_inquiry'])[0] if query_analysis.get('primary_intents', ['general_inquiry']) else None,
                intent_analysis=query_analysis,
                endpoint_strategy=endpoint_strategy,
                exclusions_applied=exclusion_results,
                methodology="LLM-driven iterative deep research with multi-layer processing",
                steps_taken=self.research_steps,
                api_calls_made=api_client.api_calls,
                key_findings=synthesis_results.get('key_findings', []),
                conclusion=synthesis_results.get('comprehensive_conclusion', ''),
                recommendations=synthesis_results.get('actionable_recommendations', []),
                confidence_score=synthesis_results.get('confidence_score', 0.8),
                timestamp=datetime.now().isoformat(),
                total_duration=total_duration,
                advantages_over_simple_llm=synthesis_results.get('advantages_over_simple_llm', [])
            )

            print(f"\n✅ Deep Research Complete! ({total_duration:.2f}s)")
            print(f"📊 Research Steps: {len(self.research_steps)}")
            print(f"📡 API Calls: {len(api_client.api_calls)}")
            print(f"🎯 Confidence: {report.confidence_score:.1%}")

            return report

        except Exception as e:
            logger.error(f"Deep research failed: {e}")
            raise e

    async def _execute_endpoint_strategy(self, strategy: Dict[str, Any], analysis: Dict[str, Any],
                                         api_client: PokemonAPIClient) -> Dict[str, Any]:
        """Execute endpoint strategy using smart approach"""

        print("   🧠 Using Smart Execution Strategy...")

        try:
            smart_strategy = SmartExecutionStrategy()
            results = await smart_strategy.execute_smart_strategy(strategy, analysis, api_client)

            if len(results) > 0:
                print(f"   ✅ Smart strategy succeeded: {len(results)} data sources")
                return results
            else:
                print("   ⚠️ Smart strategy returned no results, using fallback...")
                return await self._execute_fallback_strategy(strategy, analysis, api_client)

        except Exception as e:
            print(f"   ❌ Smart strategy failed: {e}")
            print("   🔄 Using basic fallback strategy...")
            return await self._execute_fallback_strategy(strategy, analysis, api_client)

    async def _get_pokemon_by_type(self, api_client: PokemonAPIClient, type_name: str) -> Dict[str, Any]:
        """Get Pokemon data for a specific type (for team building)"""
        try:
            # first get type data
            type_data = await api_client.get_type(type_name)
            if not type_data or 'pokemon' not in type_data:
                return {}

            # get the first 5 Pokemon of the type
            pokemon_list = type_data['pokemon'][:5]
            pokemon_data = {}

            for pokemon_ref in pokemon_list:
                pokemon_name = pokemon_ref['pokemon']['name']
                pokemon_info = await api_client.get_pokemon(pokemon_name)
                if pokemon_info:
                    pokemon_data[pokemon_name] = pokemon_info
                await asyncio.sleep(0.1)  # simple rate limiting

            return {f'{type_name}_type_pokemon': pokemon_data}
        except Exception as e:
            logger.warning(f"Failed to get Pokemon for type {type_name}: {e}")
            return {}
    async def _synthesize_research_findings(self, query: str, analysis: Dict[str, Any],
                                          strategy: Dict[str, Any], results: Dict[str, Any],
                                          exclusions: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to synthesize all research findings into insights with token management"""

        print("   📊 Preparing data for LLM synthesis...")

        # Initialize token manager
        token_manager = TokenManager()

        # Extract relevant summaries instead of full JSON data
        def extract_relevant_summary(data):
            """Extract only relevant information for LLM synthesis, avoiding noise"""
            if not isinstance(data, dict):
                return {"data_type": "unknown", "content": str(data)[:200]}
            
            summary = {}
            all_pokemon_names = set()
            all_pokemon_species_names = set()
            
            for key, value in data.items():
                if not value:  # Skip empty values
                    continue
                    
                try:
                    # Handle our specific API result format from smart execution
                    if isinstance(value, dict) and any(field in value for field in ['endpoint_type', 'pokemon_data_extracted', 'return_type']):
                        # This is one of our API result objects
                        endpoint_summary = {
                            "endpoint": value.get('endpoint_type', 'unknown'),
                            "return_type": value.get('return_type', 'unknown'),
                            "success": value.get('pokemon_data_extracted', False),
                            "context": value.get('api_context', '')[:200] if value.get('api_context') else ''
                        }
                        
                        # Extract Pokemon names
                        if 'pokemon_names' in value and value['pokemon_names']:
                            endpoint_summary['pokemon_names'] = value['pokemon_names'][:15]  # Limit for readability
                            all_pokemon_names.update(value['pokemon_names'])
                        
                        # Extract Pokemon species names
                        if 'pokemon_species_names' in value and value['pokemon_species_names']:
                            endpoint_summary['pokemon_species_names'] = value['pokemon_species_names'][:15]
                            all_pokemon_species_names.update(value['pokemon_species_names'])
                        
                        # Add count information
                        if 'pokemon_count' in value:
                            endpoint_summary['count'] = value['pokemon_count']
                        elif 'pokemon_species_count' in value:
                            endpoint_summary['count'] = value['pokemon_species_count']
                        
                        summary[key] = endpoint_summary
                    
                    # Handle traditional Pokemon API patterns (fallback)
                    elif 'pokemon' in key.lower():
                        if isinstance(value, dict):
                            # Extract pokemon basic info
                            pokemon_info = {
                                "name": value.get('name', 'unknown'),
                                "types": [t.get('type', {}).get('name') for t in value.get('types', [])],
                                "abilities": [a.get('ability', {}).get('name') for a in value.get('abilities', [])][:3],
                                "height": value.get('height'),
                                "weight": value.get('weight')
                            }
                            summary[key] = {k: v for k, v in pokemon_info.items() if v}
                        elif isinstance(value, list) and value:
                            # Extract pokemon list
                            pokemon_names = []
                            for item in value[:10]:  # Limit to first 10
                                if isinstance(item, dict):
                                    name = item.get('name') or item.get('pokemon', {}).get('name')
                                    if name:
                                        pokemon_names.append(name)
                                        all_pokemon_names.add(name)
                            summary[key] = pokemon_names
                    
                    elif 'species' in key.lower():
                        if isinstance(value, dict):
                            species_info = {
                                "name": value.get('name', 'unknown'),
                                "color": value.get('color', {}).get('name'),
                                "habitat": value.get('habitat', {}).get('name'),
                                "generation": value.get('generation', {}).get('name')
                            }
                            summary[key] = {k: v for k, v in species_info.items() if v}
                        elif isinstance(value, list) and value:
                            species_names = [item.get('name', 'unknown') for item in value[:10]]
                            all_pokemon_species_names.update(species_names)
                            summary[key] = species_names
                    
                    elif 'type' in key.lower() and isinstance(value, dict):
                        type_info = {
                            "name": value.get('name'),
                            "pokemon_count": len(value.get('pokemon', [])),
                            "sample_pokemon": [p.get('pokemon', {}).get('name') for p in value.get('pokemon', [])[:5]]
                        }
                        summary[key] = {k: v for k, v in type_info.items() if v}
                    
                    elif isinstance(value, dict):
                        # Generic dict handling - extract name and key fields
                        basic_info = {
                            "name": value.get('name'),
                            "id": value.get('id'),
                            "count": len(value) if len(value) < 50 else f"large_object_{len(value)}_fields"
                        }
                        summary[key] = {k: v for k, v in basic_info.items() if v}
                    
                    elif isinstance(value, list):
                        # Handle lists by showing count and sample
                        if len(value) > 10:
                            summary[key] = {
                                "type": "list",
                                "count": len(value),
                                "sample": value[:3] if value else []
                            }
                        else:
                            summary[key] = value
                    
                    else:
                        # Simple values
                        if isinstance(value, str) and len(value) > 200:
                            summary[key] = value[:200] + "..."
                        else:
                            summary[key] = value
                            
                except Exception as e:
                    # If extraction fails, provide minimal info
                    summary[key] = {"extraction_error": str(e)[:100]}
            
            # Add intersection analysis if we have Pokemon from multiple sources
            if len(summary) > 1:  # More than one endpoint result
                pokemon_sets = {}
                species_sets = {}
                
                for key, value in summary.items():
                    if isinstance(value, dict):
                        if 'pokemon_names' in value:
                            pokemon_sets[key] = set(value['pokemon_names'])
                        if 'pokemon_species_names' in value:
                            species_sets[key] = set(value['pokemon_species_names'])
                
                # Find intersections
                intersections = {}
                if len(pokemon_sets) > 1:
                    all_keys = list(pokemon_sets.keys())
                    for i in range(len(all_keys)):
                        for j in range(i + 1, len(all_keys)):
                            key1, key2 = all_keys[i], all_keys[j]
                            intersection = pokemon_sets[key1] & pokemon_sets[key2]
                            if intersection:
                                intersections[f"{key1}_&_{key2}"] = list(intersection)
                
                if len(species_sets) > 1:
                    all_keys = list(species_sets.keys())
                    for i in range(len(all_keys)):
                        for j in range(i + 1, len(all_keys)):
                            key1, key2 = all_keys[i], all_keys[j]
                            intersection = species_sets[key1] & species_sets[key2]
                            if intersection:
                                intersections[f"{key1}_species_&_{key2}_species"] = list(intersection)
                
                if intersections:
                    summary['INTERSECTION_ANALYSIS'] = intersections
            
            return summary

        # Extract relevant summaries instead of raw data
        try:
            clean_analysis = extract_relevant_summary(analysis) if isinstance(analysis, dict) else {"primary_intents": analysis.get('primary_intents', [])}
            clean_strategy = extract_relevant_summary(strategy) if isinstance(strategy, dict) else {"endpoints": strategy.get('endpoints', [])}
            clean_results = extract_relevant_summary(results) if isinstance(results, dict) else {"data_sources": len(results)}
            clean_exclusions = extract_relevant_summary(exclusions) if isinstance(exclusions, dict) else {"exclusions_applied": exclusions.get('exclusions_applied', [])}
        except Exception as e:
            logger.error(f"Error extracting data for synthesis: {e}")
            # Fallback to simplified data
            clean_analysis = {"primary_intents": analysis.get('primary_intents', []) if isinstance(analysis, dict) else []}
            clean_strategy = {"endpoints": strategy.get('endpoints', []) if isinstance(strategy, dict) else []}
            clean_results = {"data_sources": len(results) if isinstance(results, dict) else 0}
            clean_exclusions = {"exclusions_applied": exclusions.get('exclusions_applied', []) if isinstance(exclusions, dict) else []}

        # Create comprehensive research context
        research_context = {
            "query": query,
            "analysis": clean_analysis,
            "strategy": clean_strategy,
            "results": clean_results,
            "exclusions": clean_exclusions
        }

        # Check token count and compress if necessary
        context_tokens = token_manager.count_tokens(json.dumps(research_context, ensure_ascii=False))
        print(f"   📏 Research context tokens: {context_tokens}")

        if context_tokens > token_manager.compression_threshold:
            print(f"   🗜️ Compressing research context...")
            research_context = token_manager.compress_data_hierarchically(
                research_context,
                target_tokens=50000  # Leave plenty of room for prompts and response
            )
            compressed_tokens = token_manager.count_tokens(json.dumps(research_context, ensure_ascii=False))
            print(f"   ✅ Compressed to {compressed_tokens} tokens")

        system_prompt = """You are a Pokemon research synthesizer. Combine all research findings into comprehensive insights.

Create a synthesis that demonstrates the value of this deep research approach over simple LLM queries.

Focus on:
- Concrete findings from real API data
- Strategic insights and recommendations
- Evidence-based conclusions
- Comparative advantages of this methodology

Note: If data appears compressed or summarized, work with what's available and note any limitations."""

        user_prompt = f"""
Original Query: "{query}"

Research Context (may be compressed due to size):
{json.dumps(research_context, indent=2, ensure_ascii=False)}

Synthesize comprehensive findings in JSON:
{{
    "key_findings": ["List of major discoveries that related to user's question from the research and your knowledge base"],
    "comprehensive_conclusion": "Answer user's question based on evidence and your knowledge base and include example pokemons",
    "actionable_recommendations": ["Giving specific recommendations for solving user's question in a logical way"],
    "confidence_score": 0.0-1.0,
    "evidence_summary": "Summary of evidence gathered",
    "advantages_over_simple_llm": ["How this research is superior to asking ChatGPT"],
    "research_quality_assessment": "Assessment of research thoroughness",
    "data_limitations": "Any limitations due to data compression or processing"
}}
"""

        # Check final message token count
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        total_tokens = token_manager.count_message_tokens(messages)
        print(f"   📨 Total message tokens: {total_tokens}")

        if total_tokens > token_manager.max_tokens:
            print(f"   ⚠️ Message still too long ({total_tokens} tokens), creating ultra-compressed summary...")

            # Ultra-compression: Create minimal context
            ultra_summary = {
                "query": query,
                "data_sources_count": len(clean_results),
                "intents_identified": clean_analysis.get('primary_intents', []),
                "endpoints_used": clean_strategy.get('endpoints', []),
                "key_data_types": list(set(key.split('_')[0] for key in clean_results.keys())),
                "compression_level": "ultra_high"
            }

            user_prompt = f"""
Original Query: "{query}"

Ultra-Compressed Research Summary:
{json.dumps(ultra_summary, indent=2, ensure_ascii=False)}

Based on this summary, provide research synthesis in JSON format:
{{
    "key_findings": ["General findings based on data collected"],
    "comprehensive_conclusion": "Conclusion based on available summary",
    "actionable_recommendations": ["General recommendations"],
    "confidence_score": 0.7,
    "evidence_summary": "Research conducted with {ultra_summary['data_sources_count']} data sources",
    "advantages_over_simple_llm": ["Used real Pokemon API data", "Systematic research approach"],
    "research_quality_assessment": "Good quality research with comprehensive data collection",
    "data_limitations": "Analysis based on compressed data due to size constraints"
}}
"""

            messages[1]["content"] = user_prompt
            final_tokens = token_manager.count_message_tokens(messages)
            print(f"   ✅ Ultra-compressed to {final_tokens} tokens")

        try:
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"}
            )

            synthesis_result = json.loads(response.choices[0].message.content)
            print(f"   ✅ LLM synthesis completed successfully")
            return synthesis_result

        except Exception as e:
            logger.error(f"Error in research synthesis: {e}")
            print(f"   ❌ LLM synthesis failed: {e}")

            # Fallback synthesis if LLM call fails
            fallback_summary = {
                "key_findings": [
                    f"Successfully analyzed query with comprehensive data collection",
                    f"Collected data from {len(clean_results)} API sources",
                    f"Applied systematic research methodology"
                ],
                "comprehensive_conclusion": f"Research completed successfully for query: '{query}'. The system demonstrated comprehensive Pokemon data analysis using strategic API calls and intelligent processing.",
                "actionable_recommendations": [
                    "Use the collected Pokemon data for informed decision making",
                    "Consider the research methodology for future Pokemon queries",
                    "Review the API sources used for data verification"
                ],
                "confidence_score": 0.85,
                "evidence_summary": f"Gathered data from {len(clean_results)} Pokemon API endpoints with systematic analysis",
                "advantages_over_simple_llm": [
                    "Used real-time Pokemon API data instead of training knowledge",
                    "Applied systematic research methodology with documented steps",
                    "Implemented intelligent data processing and filtering",
                    "Provided transparent documentation of all data sources and decisions"
                ],
                "research_quality_assessment": "High quality research with comprehensive data collection and systematic analysis",
                "data_limitations": "Synthesis generated using fallback mechanism due to API issues"
            }

            return fallback_summary
    
    async def _execute_fallback_strategy(self, strategy: Dict[str, Any], analysis: Dict[str, Any],
                                       api_client: PokemonAPIClient) -> Dict[str, Any]:
        """Execute fallback strategy using the original registry system"""
        print("   🔄 Using Original Fallback Strategy...")
        
        # use the original registry system as fallback
        registry = PokemonEndpointRegistry()
        
        endpoints = strategy.get('endpoints', [])
        execution_order = strategy.get('execution_order', endpoints)
        entities = analysis.get('entities', {})
        
        tasks = []
        task_keys = []
        
        print(f"   📡 Fallback executing {len(execution_order)} endpoints...")
        
        for endpoint_name in execution_order[:5]:  # limit the number to avoid too many calls
            config = registry.get_endpoint_config(endpoint_name)
            
            if not config:
                continue
                
            if not hasattr(api_client, config.client_method):
                continue
                
            client_method = getattr(api_client, config.client_method)
            
            # get the data to process
            data_to_process = []
            
            if config.entity_key and config.entity_key in entities:
                entity_values = entities[config.entity_key]
                if entity_values:
                    data_to_process = entity_values[:2]  # limit to 2 samples
            
            if not data_to_process and config.default_samples:
                # data_to_process = config.default_samples  # no limit for default samples
                if len(config.default_samples) > 500:
                    # randomly choose 5 samples
                    data_to_process = random.sample(config.default_samples, 5)
                else:
                    data_to_process = config.default_samples
            
            # create tasks
            for data_item in data_to_process:
                try:
                    task = client_method(data_item)
                    tasks.append(task)
                    task_keys.append(f"fallback_{endpoint_name.lstrip('/')}_{data_item}")
                except Exception as e:
                    logger.warning(f"Failed to create fallback task for {data_item}: {e}")
        
        # emergency fallback
        if not tasks:
            print("   ⚠️ No valid fallback tasks, adding minimal data collection")
            fallback_config = registry.get_endpoint_config('/pokemon')
            for pokemon_id in ['1', '25']:
                tasks.append(getattr(api_client, fallback_config.client_method)(pokemon_id))
                task_keys.append(f"emergency_pokemon_{pokemon_id}")
        
        # execute tasks
        print(f"   📡 Executing {len(tasks)} fallback API calls...")
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        success_count = 0
        
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                logger.warning(f"Fallback task failed: {task_keys[i]} - {result}")
            elif result:
                results[task_keys[i]] = result
                success_count += 1
        
        print(f"   ✅ Fallback strategy complete: {success_count}/{len(tasks)} successful")
        return results