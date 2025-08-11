import json
import tiktoken
from typing import Dict, Any

class TokenManager:
    """Manages token counting and data compression for LLM interactions"""
    
    def __init__(self, model="gpt-4o"):
        self.model = model
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except Exception:
            # Fallback to a common encoding if model-specific encoding is not available
            self.encoder = tiktoken.get_encoding("cl100k_base")
        
        # Conservative limits to leave room for response
        self.max_tokens = 120000  # Leave 8k tokens for response
        self.compression_threshold = 100000  # Start compressing at 100k tokens
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        try:
            return len(self.encoder.encode(str(text)))
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(str(text)) // 4
    
    def count_message_tokens(self, messages: list) -> int:
        """Count total tokens in a message list"""
        total = 0
        for message in messages:
            # Count tokens for role and content
            total += self.count_tokens(message.get("role", ""))
            total += self.count_tokens(message.get("content", ""))
            total += 4  # Overhead per message
        return total
    
    def compress_data_hierarchically(self, data: dict, target_tokens: int) -> dict:
        """Compress data using hierarchical strategies"""
        
        current_tokens = self.count_tokens(json.dumps(data, ensure_ascii=False))
        
        if current_tokens <= target_tokens:
            return data
        
        print(f"   📊 Data compression needed: {current_tokens} → {target_tokens} tokens")
        
        # Strategy 1: Remove large raw API responses
        compressed = self._remove_large_api_responses(data.copy())
        current_tokens = self.count_tokens(json.dumps(compressed, ensure_ascii=False))
        
        if current_tokens <= target_tokens:
            print(f"   ✅ Compression successful with API response removal")
            return compressed
        
        # Strategy 2: Summarize nested data structures
        compressed = self._summarize_nested_data(compressed)
        current_tokens = self.count_tokens(json.dumps(compressed, ensure_ascii=False))
        
        if current_tokens <= target_tokens:
            print(f"   ✅ Compression successful with data summarization")
            return compressed
        
        # Strategy 3: Create high-level summary
        compressed = self._create_high_level_summary(data, target_tokens)
        print(f"   ✅ Compression successful with high-level summary")
        return compressed
    
    def _remove_large_api_responses(self, data: dict) -> dict:
        """Remove large raw API response data, keep only summaries"""
        
        def clean_pokemon_data(pokemon_data):
            """Extract only essential info from Pokemon data"""
            if not isinstance(pokemon_data, dict):
                return str(pokemon_data)
            
            essential = {
                'name': pokemon_data.get('name', 'unknown'),
                'id': pokemon_data.get('id', 0),
                'types': [t.get('type', {}).get('name', '') for t in pokemon_data.get('types', [])],
                'height': pokemon_data.get('height', 0),
                'weight': pokemon_data.get('weight', 0),
                'base_experience': pokemon_data.get('base_experience', 0)
            }
            
            # Add basic stats if available
            if 'stats' in pokemon_data:
                essential['stats'] = {
                    stat['stat']['name']: stat['base_stat'] 
                    for stat in pokemon_data['stats'][:6]  # Only main stats
                }
            
            return essential
        
        def clean_type_data(type_data):
            """Extract only essential info from type data"""
            if not isinstance(type_data, dict):
                return str(type_data)
            
            essential = {
                'name': type_data.get('name', 'unknown'),
                'pokemon_count': len(type_data.get('pokemon', [])),
                'damage_relations': type_data.get('damage_relations', {}),
                'sample_pokemon': [
                    p['pokemon']['name'] for p in type_data.get('pokemon', [])[:5]
                ]
            }
            
            return essential
        
        cleaned_data = {}
        
        for key, value in data.items():
            if 'pokemon_' in key and isinstance(value, dict):
                cleaned_data[key] = clean_pokemon_data(value)
            elif 'type_' in key and isinstance(value, dict):
                cleaned_data[key] = clean_type_data(value)
            elif isinstance(value, dict) and len(json.dumps(value)) > 10000:
                # For other large objects, keep only basic structure
                cleaned_data[key] = {
                    'data_type': type(value).__name__,
                    'size': f"Large object with {len(value)} keys" if hasattr(value, 'keys') else 'Large object',
                    'sample_keys': list(value.keys())[:5] if hasattr(value, 'keys') else []
                }
            else:
                cleaned_data[key] = value
        
        return cleaned_data
    
    def _summarize_nested_data(self, data: dict) -> dict:
        """Summarize nested data structures to reduce token count"""
        
        def summarize_list(lst, max_items=3):
            """Summarize a list to first few items plus count"""
            if not isinstance(lst, list) or len(lst) <= max_items:
                return lst
            
            return {
                'items': lst[:max_items],
                'total_count': len(lst),
                'summary': f'List with {len(lst)} items (showing first {max_items})'
            }
        
        def summarize_dict(d, max_keys=5):
            """Summarize a dict to first few keys plus metadata"""
            if not isinstance(d, dict) or len(d) <= max_keys:
                return d
            
            keys = list(d.keys())
            summarized = {k: d[k] for k in keys[:max_keys]}
            summarized['_summary'] = f'Dict with {len(d)} keys (showing first {max_keys})'
            return summarized
        
        summarized = {}
        
        for key, value in data.items():
            if isinstance(value, list):
                summarized[key] = summarize_list(value)
            elif isinstance(value, dict):
                summarized[key] = summarize_dict(value)
            else:
                summarized[key] = value
        
        return summarized
    
    def _create_high_level_summary(self, original_data: dict, target_tokens: int) -> dict:
        """Create a high-level summary when other compression methods aren't enough"""
        
        summary = {
            'data_overview': {
                'total_sources': len(original_data),
                'data_types': list(set(key.split('_')[0] for key in original_data.keys())),
                'source_breakdown': {}
            },
            'key_findings': [],
            'compression_note': f'Data compressed due to size (target: {target_tokens} tokens)'
        }
        
        # Count different types of data
        for key in original_data.keys():
            data_type = key.split('_')[0]
            summary['data_overview']['source_breakdown'][data_type] = \
                summary['data_overview']['source_breakdown'].get(data_type, 0) + 1
        
        # Extract key findings from different data types
        pokemon_found = []
        types_found = []
        
        for key, value in original_data.items():
            if 'pokemon_' in key and isinstance(value, dict):
                name = value.get('name', key)
                types = [t.get('type', {}).get('name', '') for t in value.get('types', [])]
                pokemon_found.append(f"{name} ({'/'.join(types)})")
            elif 'type_' in key and isinstance(value, dict):
                name = value.get('name', key)
                pokemon_count = len(value.get('pokemon', []))
                types_found.append(f"{name} type ({pokemon_count} Pokemon)")
        
        if pokemon_found:
            summary['key_findings'].append(f"Pokemon analyzed: {', '.join(pokemon_found[:10])}")
            if len(pokemon_found) > 10:
                summary['key_findings'].append(f"... and {len(pokemon_found) - 10} more Pokemon")
        
        if types_found:
            summary['key_findings'].append(f"Types analyzed: {', '.join(types_found)}")
        
        return summary