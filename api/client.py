import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any
from datetime import datetime
try:
    from ..core.models import APICall
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.models import APICall

logger = logging.getLogger(__name__)

class PokemonAPIClient:
    """Enhanced Pokemon API client with comprehensive endpoint support"""
    
    def __init__(self):
        self.base_url = "https://pokeapi.co/api/v2"
        self.session = None
        self.api_calls = []
        self.rate_limit = 0.5  # seconds between calls
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, retries: int = 3) -> Dict[str, Any]:
        """Make HTTP request to Pokemon API with retry logic"""
        start_time = time.time()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(retries):
            try:
                await asyncio.sleep(self.rate_limit)  # Rate limiting
                
                async with self.session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        duration = time.time() - start_time
                        
                        # Record API call
                        api_call = APICall(
                            endpoint=endpoint,
                            url=url,
                            method="GET",
                            response_data=data,
                            timestamp=datetime.now().isoformat(),
                            duration_seconds=duration
                        )
                        self.api_calls.append(api_call)
                        
                        logger.info(f"API call successful: {endpoint} ({duration:.2f}s)")
                        return data
                    elif response.status == 404:
                        logger.warning(f"Resource not found: {endpoint}")
                        return {}
                    else:
                        logger.warning(f"API call failed: {endpoint} - Status {response.status}")
                        if attempt < retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        return {}
            except Exception as e:
                logger.error(f"API request error (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {}
        
        return {}
    
    # Core Pokemon endpoints
    async def get_pokemon(self, name_or_id: str) -> Dict[str, Any]:
        logger.debug(f"🐛 CALLED: get_pokemon('{name_or_id}')")
        result = await self._make_request(f"/pokemon/{name_or_id}")
        logger.debug(f"🐛 RESULT: get_pokemon('{name_or_id}') -> {len(str(result))} chars")
        return result
    
    async def get_pokemon_species(self, name_or_id: str) -> Dict[str, Any]:
        logger.debug(f"🧬 CALLED: get_pokemon_species('{name_or_id}')")
        result = await self._make_request(f"/pokemon-species/{name_or_id}")
        logger.debug(f"🧬 RESULT: get_pokemon_species('{name_or_id}') -> {len(str(result))} chars")
        return result
    
    async def get_pokemon_form(self, name_or_id: str) -> Dict[str, Any]:
        logger.debug(f"🔄 CALLED: get_pokemon_form('{name_or_id}')")
        result = await self._make_request(f"/pokemon-form/{name_or_id}")
        logger.debug(f"🔄 RESULT: get_pokemon_form('{name_or_id}') -> {len(str(result))} chars")
        return result
    
    # Type system endpoints
    async def get_type(self, type_name: str) -> Dict[str, Any]:
        logger.debug(f"⚡ CALLED: get_type('{type_name}')")
        result = await self._make_request(f"/type/{type_name}")
        logger.debug(f"⚡ RESULT: get_type('{type_name}') -> {len(str(result))} chars")
        return result
    
    # Move system endpoints
    async def get_move(self, move_name: str) -> Dict[str, Any]:
        logger.debug(f"⚔️ CALLED: get_move('{move_name}')")
        result = await self._make_request(f"/move/{move_name}")
        logger.debug(f"⚔️ RESULT: get_move('{move_name}') -> {len(str(result))} chars")
        return result
    
    async def get_move_category(self, category_id: str) -> Dict[str, Any]:
        logger.debug(f"📂 CALLED: get_move_category('{category_id}')")
        result = await self._make_request(f"/move-category/{category_id}")
        logger.debug(f"📂 RESULT: get_move_category('{category_id}') -> {len(str(result))} chars")
        return result
    
    # Ability endpoints
    async def get_ability(self, ability_name: str) -> Dict[str, Any]:
        logger.debug(f"✨ CALLED: get_ability('{ability_name}')")
        result = await self._make_request(f"/ability/{ability_name}")
        logger.debug(f"✨ RESULT: get_ability('{ability_name}') -> {len(str(result))} chars")
        return result
    
    # Classification endpoints
    async def get_pokemon_color(self, color_name: str) -> Dict[str, Any]:
        logger.debug(f"🎨 CALLED: get_pokemon_color('{color_name}')")
        result = await self._make_request(f"/pokemon-color/{color_name}")
        logger.debug(f"🎨 RESULT: get_pokemon_color('{color_name}') -> {len(str(result))} chars")
        return result
    
    async def get_pokemon_shape(self, shape_name: str) -> Dict[str, Any]:
        logger.debug(f"🔵 CALLED: get_pokemon_shape('{shape_name}')")
        result = await self._make_request(f"/pokemon-shape/{shape_name}")
        logger.debug(f"🔵 RESULT: get_pokemon_shape('{shape_name}') -> {len(str(result))} chars")
        return result
    
    async def get_pokemon_habitat(self, habitat_name: str) -> Dict[str, Any]:
        logger.debug(f"🏞️ CALLED: get_pokemon_habitat('{habitat_name}')")
        result = await self._make_request(f"/pokemon-habitat/{habitat_name}")
        logger.debug(f"🏞️ RESULT: get_pokemon_habitat('{habitat_name}') -> {len(str(result))} chars")
        return result
    
    # Generation and game data
    async def get_generation(self, generation_id: str) -> Dict[str, Any]:
        logger.debug(f"📅 CALLED: get_generation('{generation_id}')")
        result = await self._make_request(f"/generation/{generation_id}")
        logger.debug(f"📅 RESULT: get_generation('{generation_id}') -> {len(str(result))} chars")
        return result
    
    async def get_pokedex(self, pokedex_id: str) -> Dict[str, Any]:
        logger.debug(f"📖 CALLED: get_pokedex('{pokedex_id}')")
        result = await self._make_request(f"/pokedex/{pokedex_id}")
        logger.debug(f"📖 RESULT: get_pokedex('{pokedex_id}') -> {len(str(result))} chars")
        return result
    
    # Location endpoints
    async def get_location(self, location_id: str) -> Dict[str, Any]:
        logger.debug(f"🗺️ CALLED: get_location('{location_id}')")
        result = await self._make_request(f"/location/{location_id}")
        logger.debug(f"🗺️ RESULT: get_location('{location_id}') -> {len(str(result))} chars")
        return result
    
    async def get_location_area(self, area_id: str) -> Dict[str, Any]:
        logger.debug(f"📍 CALLED: get_location_area('{area_id}')")
        result = await self._make_request(f"/location-area/{area_id}")
        logger.debug(f"📍 RESULT: get_location_area('{area_id}') -> {len(str(result))} chars")
        return result
    
    async def get_region(self, region_id: str) -> Dict[str, Any]:
        logger.debug(f"🌍 CALLED: get_region('{region_id}')")
        result = await self._make_request(f"/region/{region_id}")
        logger.debug(f"🌍 RESULT: get_region('{region_id}') -> {len(str(result))} chars")
        return result
    
    # Evolution endpoints
    async def get_evolution_chain(self, chain_id: str) -> Dict[str, Any]:
        logger.debug(f"🔗 CALLED: get_evolution_chain('{chain_id}')")
        result = await self._make_request(f"/evolution-chain/{chain_id}")
        logger.debug(f"🔗 RESULT: get_evolution_chain('{chain_id}') -> {len(str(result))} chars")
        return result
    
    async def get_evolution_trigger(self, trigger_id: str) -> Dict[str, Any]:
        logger.debug(f"⭐ CALLED: get_evolution_trigger('{trigger_id}')")
        result = await self._make_request(f"/evolution-trigger/{trigger_id}")
        logger.debug(f"⭐ RESULT: get_evolution_trigger('{trigger_id}') -> {len(str(result))} chars")
        return result
    
    # Breeding and genetics
    async def get_egg_group(self, group_name: str) -> Dict[str, Any]:
        logger.debug(f"🥚 CALLED: get_egg_group('{group_name}')")
        result = await self._make_request(f"/egg-group/{group_name}")
        logger.debug(f"🥚 RESULT: get_egg_group('{group_name}') -> {len(str(result))} chars")
        return result
    
    async def get_gender(self, gender_id: str) -> Dict[str, Any]:
        logger.debug(f"⚥ CALLED: get_gender('{gender_id}')")
        result = await self._make_request(f"/gender/{gender_id}")
        logger.debug(f"⚥ RESULT: get_gender('{gender_id}') -> {len(str(result))} chars")
        return result
    
    async def get_nature(self, nature_name: str) -> Dict[str, Any]:
        logger.debug(f"🧠 CALLED: get_nature('{nature_name}')")
        result = await self._make_request(f"/nature/{nature_name}")
        logger.debug(f"🧠 RESULT: get_nature('{nature_name}') -> {len(str(result))} chars")
        return result
    
    async def get_characteristic(self, char_id: str) -> Dict[str, Any]:
        logger.debug(f"🎯 CALLED: get_characteristic('{char_id}')")
        result = await self._make_request(f"/characteristic/{char_id}")
        logger.debug(f"🎯 RESULT: get_characteristic('{char_id}') -> {len(str(result))} chars")
        return result
    
    async def get_growth_rate(self, rate_name: str) -> Dict[str, Any]:
        logger.debug(f"📈 CALLED: get_growth_rate('{rate_name}')")
        result = await self._make_request(f"/growth-rate/{rate_name}")
        logger.debug(f"📈 RESULT: get_growth_rate('{rate_name}') -> {len(str(result))} chars")
        return result
    
    # Items and berries
    async def get_item(self, item_name: str) -> Dict[str, Any]:
        logger.debug(f"🎒 CALLED: get_item('{item_name}')")
        result = await self._make_request(f"/item/{item_name}")
        logger.debug(f"🎒 RESULT: get_item('{item_name}') -> {len(str(result))} chars")
        return result
    
    async def get_berry(self, berry_name: str) -> Dict[str, Any]:
        logger.debug(f"🍓 CALLED: get_berry('{berry_name}')")
        result = await self._make_request(f"/berry/{berry_name}")
        logger.debug(f"🍓 RESULT: get_berry('{berry_name}') -> {len(str(result))} chars")
        return result
    
    async def get_berry_flavor(self, flavor_name: str) -> Dict[str, Any]:
        logger.debug(f"👅 CALLED: get_berry_flavor('{flavor_name}')")
        result = await self._make_request(f"/berry-flavor/{flavor_name}")
        logger.debug(f"👅 RESULT: get_berry_flavor('{flavor_name}') -> {len(str(result))} chars")
        return result
    
    # Contest system
    async def get_contest_type(self, contest_type: str) -> Dict[str, Any]:
        logger.debug(f"🏆 CALLED: get_contest_type('{contest_type}')")
        result = await self._make_request(f"/contest-type/{contest_type}")
        logger.debug(f"🏆 RESULT: get_contest_type('{contest_type}') -> {len(str(result))} chars")
        return result
    
    async def get_contest_effect(self, effect_id: str) -> Dict[str, Any]:
        logger.debug(f"✨ CALLED: get_contest_effect('{effect_id}')")
        result = await self._make_request(f"/contest-effect/{effect_id}")
        logger.debug(f"✨ RESULT: get_contest_effect('{effect_id}') -> {len(str(result))} chars")
        return result
    
    # Stats and mechanics
    async def get_stat(self, stat_name: str) -> Dict[str, Any]:
        logger.debug(f"📊 CALLED: get_stat('{stat_name}')")
        result = await self._make_request(f"/stat/{stat_name}")
        logger.debug(f"📊 RESULT: get_stat('{stat_name}') -> {len(str(result))} chars")
        return result
    
    async def get_pokeathlon_stat(self, stat_name: str) -> Dict[str, Any]:
        logger.debug(f"🏃 CALLED: get_pokeathlon_stat('{stat_name}')")
        result = await self._make_request(f"/pokeathlon-stat/{stat_name}")
        logger.debug(f"🏃 RESULT: get_pokeathlon_stat('{stat_name}') -> {len(str(result))} chars")
        return result
    
    # Encounter methods
    async def get_encounter_method(self, method_name: str) -> Dict[str, Any]:
        logger.debug(f"👁️ CALLED: get_encounter_method('{method_name}')")
        result = await self._make_request(f"/encounter-method/{method_name}")
        logger.debug(f"👁️ RESULT: get_encounter_method('{method_name}') -> {len(str(result))} chars")
        return result
    
    async def get_encounter_condition(self, condition_name: str) -> Dict[str, Any]:
        logger.debug(f"🌙 CALLED: get_encounter_condition('{condition_name}')")
        result = await self._make_request(f"/encounter-condition/{condition_name}")
        logger.debug(f"🌙 RESULT: get_encounter_condition('{condition_name}') -> {len(str(result))} chars")
        return result