#!/usr/bin/env python3
"""
Test script to demonstrate specific similarity queries for sample questions
to test if similarity_analysis.py is working correctly.
Namely;
- "Find 5 startups most similar to [specific company] in the AI/ML space"
- "Find founders with similar backgrounds to [specific founder name]"
- "Which VCs have similar investment patterns to [specific VC]?"
- "Which companies have similar technology stacks to [specific company]?"
"""

import sys
import os

# Add parent directory to path so we can import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from similarity_analysis import StartupSimilarityAnalyzer

def test_specific_queries():
    """Test the specific similarity queries from sample_questions.md"""
    
    print("🚀 TESTING SPECIFIC SIMILARITY QUERIES")
    print("=" * 60)
    
    # Initialize analyzer (JSON file is in parent directory)
    json_path = os.path.join(parent_dir, 'startup_knowledge_graph.json')
    analyzer = StartupSimilarityAnalyzer(json_path)
    
    # Test 1: Find startups similar to a specific company
    print("\n1️⃣ Find 5 startups most similar to 'Robinson':")
    result = analyzer.find_similar_startups_to('Robinson', top_n=5)
    if isinstance(result, list):
        for i, sim in enumerate(result, 1):
            print(f"   {i}. {sim['startup']} (similarity: {sim['similarity']:.3f})")
            print(f"      Shared techs: {sim['shared_techs']}/{sim['total_techs']}")
    else:
        print(f"   {result}")
    
    # Test 2: Find founders similar to a specific founder
    print("\n2️⃣ Find founders similar to 'David Norman':")
    result = analyzer.find_similar_founders_to('David Norman', top_n=5)
    if isinstance(result, list):
        for i, sim in enumerate(result, 1):
            print(f"   {i}. {sim['founder']} (similarity: {sim['similarity']:.3f})")
            print(f"      Matching attributes: {sim['matching_attributes']}/{sim['total_compared']}")
    else:
        print(f"   {result}")
    
    # Test 3: Find VCs similar to a specific VC
    print("\n3️⃣ Find VCs with similar investment patterns to 'Williams Ventures':")
    result = analyzer.find_similar_vcs_to('Williams Ventures', top_n=5)
    if isinstance(result, list):
        for i, sim in enumerate(result, 1):
            print(f"   {i}. {sim['vc']} (similarity: {sim['similarity']:.3f})")
            print(f"      Shared investments: {sim['shared_investments']}/{sim['total_investments']}")
    else:
        print(f"   {result}")
    
    # Test 4: Another startup similarity example
    print("\n4️⃣ Find companies with similar technology stacks to 'DigitalLogic':")
    result = analyzer.find_similar_startups_to('DigitalLogic', top_n=5)
    if isinstance(result, list):
        for i, sim in enumerate(result, 1):
            print(f"   {i}. {sim['startup']} (similarity: {sim['similarity']:.3f})")
            print(f"      Shared techs: {sim['shared_techs']}/{sim['total_techs']}")
    else:
        print(f"   {result}")

if __name__ == "__main__":
    test_specific_queries() 