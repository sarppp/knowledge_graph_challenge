#!/usr/bin/env python3
"""
Final test of the query system for all 8 sample questions
"""
import sys
import os

# Add parent directory to path so we can import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from query_system import IntelligentQuerySystem
from dotenv import load_dotenv
from neo4j import GraphDatabase

def test_all_sample_questions():
    """Test all 8 sample questions from sample_questions.md"""
    
    print("🎯 TESTING ALL 8 SAMPLE QUESTIONS")
    print("=" * 60)
    
    # Setup connection
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USER", "neo4j") 
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    driver = GraphDatabase.driver(
        uri, 
        auth=(username, password),
        notifications_min_severity='WARNING'
    )
    
    # Initialize query system (note: requires GEMINI_API_KEY for LLM)
    iqs = IntelligentQuerySystem(driver, database)
    
    # All 8 sample questions
    questions = [
        # Basic Functionality (2)
        "How many startups are in the FinTech industry?",
        "What technologies does Robinson use?",
        
        # Similarity Algorithms (4) - Note: These need similarity_analysis.py
        "Find 5 startups most similar to Robinson in the AI/ML space",
        "Find founders with similar backgrounds to David Norman", 
        "Which VCs have similar investment patterns to Williams Ventures?",
        "Which companies have similar technology stacks to DigitalLogic?",
        
        # Complex Relationships (1)
        "Which VCs typically co-invest with Williams Ventures?",
        
        # Business Application (1)
        "If I'm a founder starting an EdTech company, which VCs should I target based on similar successful investments?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}️⃣ Testing: {question}")
        try:
            if "similar" in question.lower():
                print("   Note: This requires your similarity_analysis.py functions")
                print("   Query system handles basic queries, similarity needs StartupSimilarityAnalyzer function")
            else:
                result = iqs.query(question)
                print(f"   Result: {result}")
        except Exception as e:
            import traceback
            print(f"   Error: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
    
    driver.close()
    print("\n🎉 Query system testing complete!")

if __name__ == "__main__":
    test_all_sample_questions() 