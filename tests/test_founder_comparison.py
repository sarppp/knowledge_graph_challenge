#!/usr/bin/env python3
"""
Simple test to demonstrate LLM vs Similarity Algorithm comparison
"""

import sys
import os

# Add parent directory to path so we can import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from enhanced_founder_search import EnhancedFounderSearch

def quick_test():
    """Quick test with a few founders"""
    
    search_system = EnhancedFounderSearch()
    
    # Test with a few founders
    test_founders = ["David Norman", "Austin Li", "Mark Spears"]
    
    print("🧪 QUICK COMPARISON TEST")
    print("=" * 50)
    
    for founder in test_founders:
        print(f"\n🔍 Testing with: {founder}")
        
        # Check if founder exists
        background = search_system.get_founder_background(founder)
        if not background:
            print(f"   ❌ Founder '{founder}' not found")
            continue
            
        print(f"   ✅ Found {founder}")
        
        # Get results from both systems
        print(f"   🔄 Getting LLM results...")
        llm_results = search_system.llm_similar_founders(founder)
        
        print(f"   🔄 Getting algorithm results...")
        algo_results = search_system.algorithm_similar_founders(founder)
        
        # Show quick comparison
        print(f"\n   📊 QUICK COMPARISON:")
        if isinstance(llm_results, list) and len(llm_results) > 0:
            print(f"   🤖 LLM top result: {llm_results[0].get('f.name', 'Unknown')}")
        else:
            print(f"   🤖 LLM error: {llm_results}")
            
        if isinstance(algo_results, list) and len(algo_results) > 0:
            print(f"   🎯 Algorithm top result: {algo_results[0]['founder']} (similarity: {algo_results[0]['similarity']:.3f})")
        else:
            print(f"   🎯 Algorithm error: {algo_results}")
        
        print(f"   " + "-" * 40)
    
    search_system.close()
    print(f"\n✅ Test complete!")

if __name__ == "__main__":
    quick_test() 