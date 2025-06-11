"""
Test file for all sample questions using the Intelligent Query System
"""

import sys
import os

# Add parent directory to Python path to find query_system module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from dotenv import load_dotenv
from query_system import IntelligentQuerySystem

def run_all_tests():
    """Run all sample questions through the query system"""
    
    # Load environment and connect to Neo4j
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USER", "neo4j") 
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not uri or not password:
        raise ValueError("Please set NEO4J_URI and NEO4J_PASSWORD in your .env file")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # Initialize query system
    query_system = IntelligentQuerySystem(driver, database)
    
    # All questions from sample_questions.md
    questions = [
        # Basic Functionality
        "How many startups are in the FinTech industry?",
        "What technologies does Robinson use?",
        
        # Similarity Algorithms  
        "Find 5 startups most similar to TechCorp in the AI/ML space",
        "Find founders with similar backgrounds to David Norman",
        "Which VCs have similar investment patterns to Alpha Ventures?",
        "Which companies have similar technology stacks to DataFlow Inc?",
        
        # Complex Relationships
        "Which VCs typically co-invest with Williams Ventures?",
        
        # Business Application
        "If I'm a founder starting an EdTech company, which VCs should I target based on similar successful investments?"
    ]
    
    print("🚀 Running all sample questions...\n")
    print("="*80)
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. QUESTION: {question}")
        print("-" * 60)
        
        try:
            result = query_system.query(question)
            
            if hasattr(result, 'to_string'):
                print(result.to_string(index=False))
            else:
                print(result)
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 60)
    
    # Close connection
    driver.close()
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    run_all_tests() 