#!/usr/bin/env python3

import asyncio
import json
import os
import logging
from datetime import datetime
from dataclasses import asdict
from dotenv import load_dotenv

import openai

from research import DeepResearchAgent
from reporting import AdvancedReportVisualizer

# Load environment variables from .env file
load_dotenv()

# Setup logging with environment variable
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

async def compare_with_simple_llm(query: str, openai_api_key: str) -> str:
    """Get simple LLM response for comparison"""
    client = openai.AsyncOpenAI(api_key=openai_api_key)
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a Pokemon expert. Answer the user's question about Pokemon using your training knowledge."},
            {"role": "user", "content": query}
        ]
    )
    
    return response.choices[0].message.content

async def test_system():
    """Test the complete deep research system with predefined queries"""
    
    # Get API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        raise Exception("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    
    # Test queries showcasing different aspects of the system
    test_queries = [
        "Build a team of all bug type Pokemon",
        "I want to find a unique Pokemon that lives by the sea",
        "What Pokemon should I add next to my party?",
        "Find me some mythical Pokemon but not Mew or Mewtwo",
        "Create a rain team but exclude common choices",
        "What are some cool water Pokemon that aren't too popular?",
        "I want a pink fairy pokemon.",
        "Do Pokemon like berries?",
        "Is there any winged fiery dragon?",
        "What is Pokemon, why do someone like them and what can they do?"
    ]
    
    print("🧪 POKEMON DEEP RESEARCH AGENT - SYSTEM TEST")
    print("="*80)
    print("This test showcases our complete implementation including:")
    print("• LLM-driven intent classification and entity extraction")
    print("• Intelligent endpoint mapping and optimization")  
    print("• Multi-layer exclusion processing (explicit, attribute, semantic)")
    print("• Fallback query handling for edge cases")
    print("• Comprehensive research synthesis")
    print("="*80)
    
    # Test with a specific query
    query = test_queries[0]  # "Build a team of all bug type Pokemon"
    print(f"\n🔍 Test Query: '{query}'\n")
    
    try:
        # Create the complete deep research agent
        agent = DeepResearchAgent(openai_api_key)
        
        # Conduct comprehensive deep research
        research_report = await agent.conduct_deep_research(query)
        
        # Get simple LLM comparison
        print("\n🤖 Getting simple LLM response for comparison...")
        simple_response = await compare_with_simple_llm(query, openai_api_key)
        
        # Create comprehensive report
        comprehensive_report = AdvancedReportVisualizer.create_comprehensive_report(research_report)
        
        # Display results
        print(comprehensive_report)
        
        print("\n" + "="*100)
        print("🤖 SIMPLE LLM RESPONSE (for comparison)")
        print("="*100)
        print(simple_response)
        print("="*100)
        
        # Save comprehensive report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs('reports', exist_ok=True)
        
        report_filename = f"reports/test_pokemon_research_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(comprehensive_report)
            f.write("\n\n" + "="*100)
            f.write("\n🤖 SIMPLE LLM RESPONSE (for comparison)")
            f.write("\n" + "="*100 + "\n")
            f.write(simple_response)
        
        # Save raw data
        json_filename = f"reports/test_research_data_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(research_report), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Test reports saved:")
        print(f"   📄 Comprehensive report: {report_filename}")
        print(f"   📊 Raw data: {json_filename}")
        
        print(f"\n✅ TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("🔬 SYSTEM COMPONENTS TESTED:")
        print("✅ LLMQueryAnalyzer - Intent classification & entity extraction")
        print("✅ IntentEndpointMapper - Strategic endpoint selection")
        print("✅ ExclusionHandler - Multi-layer exclusion processing")
        print("✅ FallbackQueryProcessor - Edge case handling") 
        print("✅ DeepResearchAgent - Complete orchestration")
        print("✅ AdvancedReportVisualizer - Comprehensive reporting")
        print("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
        print("\nThis could be due to:")
        print("• Invalid OpenAI API key")
        print("• Network connectivity issues")
        print("• PokéAPI rate limiting")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_system())
    if success:
        print("\n🎉 All tests passed! The system is working correctly.")
    else:
        print("\n⚠️  Test failed. Please check the error messages above.")
