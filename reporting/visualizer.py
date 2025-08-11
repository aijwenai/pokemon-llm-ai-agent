import logging
try:
    from ..core.models import ResearchReport
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.models import ResearchReport

logger = logging.getLogger(__name__)

class AdvancedReportVisualizer:
    """Enhanced report visualization with comprehensive analysis display"""
    
    @staticmethod
    def create_comprehensive_report(report: ResearchReport) -> str:
        """Create detailed research report showing the complete deep research process"""
        
        # Safe access to report attributes with fallbacks
        def safe_get(obj, attr, default="Unknown"):
            """Safely get attribute from object"""
            try:
                value = getattr(obj, attr, default)
                if value is None:
                    return default
                return value
            except Exception:
                return default
        
        def safe_len(obj, default=0):
            """Safely get length of object"""
            try:
                return len(obj) if obj else default
            except Exception:
                return default
        
        def safe_format(value, format_str="{}", default="N/A"):
            """Safely format a value"""
            try:
                if value is None:
                    return default
                return format_str.format(value)
            except Exception:
                return default
        
        # Build report with safe access
        report_text = f"""
{'='*100}
🔬 POKEMON DEEP RESEARCH AGENT - COMPREHENSIVE REPORT
{'='*100}

📋 RESEARCH OVERVIEW
────────────────────────────────────────────────────────────────────────────────────────────────────
Query: {safe_get(report, 'query')}
Research Goal: {safe_get(report, 'research_goal')}
Completed: {safe_get(report, 'timestamp')}
Total Duration: {safe_format(safe_get(report, 'total_duration'), '{:.2f} seconds')}
Confidence Score: {safe_format(safe_get(report, 'confidence_score'), '{:.1%}')}

{'='*100}
🧠 INTELLIGENT ANALYSIS PROCESS
{'='*100}

🎯 INTENT CLASSIFICATION RESULTS:"""
        
        # Safely access nested intent analysis
        try:
            intent_analysis = safe_get(report, 'intent_analysis', {})
            primary_intents = intent_analysis.get('primary_intents', []) if isinstance(intent_analysis, dict) else []
            fallback_intents = intent_analysis.get('fallback_intents', []) if isinstance(intent_analysis, dict) else []
            query_structure = intent_analysis.get('query_structure', {}) if isinstance(intent_analysis, dict) else {}
            
            report_text += f"""
Primary Intents: {', '.join(primary_intents) if primary_intents else 'None detected'}
Fallback Categories: {', '.join(fallback_intents) if fallback_intents else 'None needed'}
Query Complexity: {query_structure.get('complexity', 'unknown') if isinstance(query_structure, dict) else 'unknown'}
Requires Fallback: {intent_analysis.get('requires_fallback', False) if isinstance(intent_analysis, dict) else False}

🔍 ENTITY EXTRACTION RESULTS:
"""
            
            # Safely handle entities
            entities = intent_analysis.get('entities', {}) if isinstance(intent_analysis, dict) else {}
            if isinstance(entities, dict):
                for entity_type, entity_list in entities.items():
                    if entity_list and isinstance(entity_list, list):
                        report_text += f"• {entity_type.replace('_', ' ').title()}: {', '.join(str(e) for e in entity_list)}\n"
            
        except Exception as e:
            logger.warning(f"Error accessing intent analysis: {e}")
            report_text += "\nIntent analysis data unavailable\n"
        
        # Safely access exclusions
        try:
            exclusions = intent_analysis.get('exclusions', {}) if isinstance(intent_analysis, dict) else {}
            report_text += f"""
🚫 EXCLUSION ANALYSIS:
Has Exclusions: {exclusions.get('has_exclusions', False) if isinstance(exclusions, dict) else False}
"""
            
            if isinstance(exclusions, dict) and exclusions.get('has_exclusions'):
                for exclusion_type, exclusion_list in exclusions.items():
                    if exclusion_list and isinstance(exclusion_list, list) and exclusion_type != 'has_exclusions':
                        report_text += f"• {exclusion_type.replace('_', ' ').title()}: {', '.join(str(e) for e in exclusion_list)}\n"
        except Exception as e:
            logger.warning(f"Error accessing exclusions: {e}")
        
        # Safely access endpoint strategy
        try:
            endpoint_strategy = safe_get(report, 'endpoint_strategy', {})
            endpoints = endpoint_strategy.get('endpoints', []) if isinstance(endpoint_strategy, dict) else []
            
            report_text += f"""
{'='*100}
🎯 ENDPOINT STRATEGY OPTIMIZATION
{'='*100}

📡 SELECTED ENDPOINTS: {safe_len(endpoints)}
{chr(10).join(f'• {endpoint}' for endpoint in endpoints) if endpoints else '• No endpoints recorded'}

⚡ STRATEGY EFFICIENCY: {endpoint_strategy.get('efficiency', 'unknown') if isinstance(endpoint_strategy, dict) else 'unknown'}
📊 COVERAGE ASSESSMENT: {endpoint_strategy.get('coverage', 'unknown') if isinstance(endpoint_strategy, dict) else 'unknown'}

🧠 OPTIMIZATION REASONING:
"""
            
            reasoning = endpoint_strategy.get('reasoning', []) if isinstance(endpoint_strategy, dict) else []
            if reasoning and isinstance(reasoning, list):
                report_text += chr(10).join(f'• {reason}' for reason in reasoning)
            else:
                report_text += "• Optimization reasoning not available"
                
        except Exception as e:
            logger.warning(f"Error accessing endpoint strategy: {e}")
        
        # Safely access research steps
        try:
            steps_taken = safe_get(report, 'steps_taken', [])
            report_text += f"""
{'='*100}
📋 DETAILED RESEARCH PROCESS ({safe_len(steps_taken)} steps)
{'='*100}
"""
            
            if steps_taken and isinstance(steps_taken, list):
                for step in steps_taken:
                    if hasattr(step, 'step_number'):
                        report_text += f"""
Step {safe_get(step, 'step_number')}: {safe_get(step, 'description')}
┌─ Action Type: {safe_get(step, 'action_type')}
├─ Duration: {safe_format(safe_get(step, 'duration_seconds'), '{:.2f} seconds')}
├─ Reasoning: {safe_get(step, 'reasoning')}
└─ Timestamp: {safe_get(step, 'timestamp')}
{'─'*80}
"""
            else:
                report_text += "No research steps recorded\n"
                
        except Exception as e:
            logger.warning(f"Error accessing research steps: {e}")
        
        # Safely access API calls
        try:
            api_calls = safe_get(report, 'api_calls_made', [])
            total_api_time = sum(getattr(call, 'duration_seconds', 0) for call in api_calls if hasattr(call, 'duration_seconds'))
            avg_duration = total_api_time / len(api_calls) if api_calls else 0
            
            report_text += f"""
{'='*100}
📡 API INTERACTION SUMMARY ({safe_len(api_calls)} calls)
{'='*100}

Total API Calls: {safe_len(api_calls)}
Total API Time: {safe_format(total_api_time, '{:.2f} seconds')}
Average Call Duration: {safe_format(avg_duration, '{:.2f} seconds')}

API CALLS MADE:
"""
            
            if api_calls and isinstance(api_calls, list):
                for i, api_call in enumerate(api_calls, 1):
                    endpoint = safe_get(api_call, 'endpoint')
                    duration = safe_format(safe_get(api_call, 'duration_seconds'), '{:.2f}s')
                    report_text += f"{i:2d}. {endpoint} ({duration})\n"
            else:
                report_text += "No API calls recorded\n"
                
        except Exception as e:
            logger.warning(f"Error accessing API calls: {e}")
        
        # Safely access exclusions applied
        try:
            exclusions_applied = safe_get(report, 'exclusions_applied', {})
            report_text += f"""
{'='*100}
🚫 EXCLUSION PROCESSING RESULTS
{'='*100}

Exclusions Applied: {', '.join(exclusions_applied.get('exclusions_applied', [])) if isinstance(exclusions_applied, dict) else 'None'}
"""
            
            if isinstance(exclusions_applied, dict) and 'exclusion_details' in exclusions_applied:
                exclusion_details = exclusions_applied['exclusion_details']
                if isinstance(exclusion_details, dict):
                    report_text += f"""
Exclusion Processing Stages:
• Explicit Name Exclusions: {safe_len(exclusion_details.get('explicit_exclusions', []))} items
• Attribute-Based Exclusions: {safe_len(exclusion_details.get('attribute_exclusions', []))} criteria  
• Semantic Exclusions: {safe_len(exclusion_details.get('semantic_exclusions', []))} criteria
"""
        except Exception as e:
            logger.warning(f"Error accessing exclusions applied: {e}")
        
        # Safely access key findings and recommendations
        try:
            key_findings = safe_get(report, 'key_findings', 'No key findings recorded')
            recommendations = safe_get(report, 'recommendations', 'No recommendations recorded')
            advantages = safe_get(report, 'advantages_over_simple_llm', 'No advantages recorded')
            
            report_text += f"""
{'='*100}
🔑 KEY RESEARCH FINDINGS
{'='*100}
"""
            
            if key_findings and isinstance(key_findings, list):
                for i, finding in enumerate(key_findings, 1):
                    report_text += f"{i}. {finding}\n"
            else:
                report_text += "No key findings recorded\n"
            
            report_text += f"""
{'='*100}
📝 COMPREHENSIVE CONCLUSION
{'='*100}
{safe_get(report, 'conclusion')}

{'='*100}
💡 ACTIONABLE RECOMMENDATIONS
{'='*100}
"""
            
            if recommendations and isinstance(recommendations, list):
                for i, rec in enumerate(recommendations, 1):
                    report_text += f"{i}. {rec}\n"
            else:
                report_text += "No recommendations provided\n"
            
            report_text += f"""
{'='*100}
🆚 ADVANTAGES OVER SIMPLE LLM QUERIES
{'='*100}

This deep research approach provides several key advantages:
"""
            
            if advantages and isinstance(advantages, list):
                for advantage in advantages:
                    report_text += f"✅ {advantage}\n"
            else:
                report_text += "✅ Uses real-time API data instead of training knowledge\n"
                report_text += "✅ Provides systematic research methodology\n"
                report_text += "✅ Offers transparent decision-making process\n"
                
        except Exception as e:
            logger.warning(f"Error accessing findings and recommendations: {e}")
        
        # Add final summary
        report_text += f"""
{'='*100}
📊 RESEARCH METHODOLOGY SUMMARY
{'='*100}

{safe_get(report, 'methodology')}

🔬 RESEARCH QUALITY METRICS:
• Intent Classification Accuracy: AI-powered semantic analysis
• Entity Extraction Completeness: Multi-category entity recognition
• Endpoint Selection Efficiency: LLM-optimized strategy
• Data Collection Thoroughness: {safe_len(safe_get(report, 'api_calls_made', []))} targeted API calls
• Exclusion Processing Sophistication: Multi-layer filtering including semantic analysis
• Synthesis Quality: Evidence-based LLM analysis
• Total Processing Time: {safe_format(safe_get(report, 'total_duration'), '{:.2f} seconds')}
• Confidence Score: {safe_format(safe_get(report, 'confidence_score'), '{:.1%}')}

{'='*100}
"""
        
        return report_text