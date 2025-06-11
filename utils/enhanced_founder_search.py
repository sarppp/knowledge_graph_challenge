#!/usr/bin/env python3
"""
Enhanced Founder Search System
Allows users to search for founders similar to any founder and compare:
1. LLM-generated Cypher query results
2. Your similarity algorithm results
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from neo4j import GraphDatabase
from query_system import IntelligentQuerySystem
from similarity_analysis import StartupSimilarityAnalyzer
import pandas as pd

class EnhancedFounderSearch:
    def __init__(self):
        # Setup Neo4j connection
        load_dotenv()
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USER", "neo4j") 
        password = os.getenv("NEO4J_PASSWORD")
        database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        self.driver = GraphDatabase.driver(
            uri, 
            auth=(username, password),
            notifications_min_severity='WARNING'
        )
        
        # Initialize both systems
        self.query_system = IntelligentQuerySystem(self.driver, database)
        self.similarity_analyzer = StartupSimilarityAnalyzer('startup_knowledge_graph.json')
        
    def get_founder_background(self, founder_name):
        """Get a founder's background information"""
        with self.driver.session() as session:
            result = session.run(
                'MATCH (f:Founder {name: $name}) RETURN f.name, f.previous_company, f.domain_expertise, f.technical_background, f.education_level, f.university, f.years_experience',
                name=founder_name
            )
            founder_data = result.single()
            return founder_data.data() if founder_data else None
    
    def get_available_founders(self, limit=20):
        """Get a list of available founders for the user to choose from"""
        with self.driver.session() as session:
            result = session.run('MATCH (f:Founder) RETURN f.name ORDER BY f.name LIMIT $limit', limit=limit)
            return [record['f.name'] for record in result]
    
    def llm_similar_founders(self, founder_name):
        """Get similar founders using LLM/Cypher query"""
        question = f"Find founders with similar backgrounds to {founder_name}"
        
        try:
            result = self.query_system.query(question)
            if isinstance(result, pd.DataFrame) and not result.empty:
                return result.to_dict('records')
            else:
                return f"LLM Error: {result}"
        except Exception as e:
            return f"LLM Error: {e}"
    
    def algorithm_similar_founders(self, founder_name):
        """Get similar founders using your similarity algorithm"""
        try:
            result = self.similarity_analyzer.find_similar_founders_to(founder_name, top_n=10)
            return result
        except Exception as e:
            return f"Algorithm Error: {e}"
    
    def compare_similarities(self, target_founder, llm_results, algo_results):
        """Compare the LLM results with algorithm results"""
        print(f"\n🔍 SIMILARITY COMPARISON FOR: {target_founder}")
        print("=" * 70)
        
        # Get target founder's background
        target_background = self.get_founder_background(target_founder)
        if target_background:
            print(f"\n📊 TARGET FOUNDER BACKGROUND:")
            for key, value in target_background.items():
                print(f"   {key}: {value}")
        
        print(f"\n🤖 LLM RESULTS:")
        if isinstance(llm_results, list):
            print("   (Note: LLM may not use true similarity calculation)")
            for i, founder in enumerate(llm_results[:5], 1):
                print(f"   {i}. {founder.get('f.name', 'Unknown')}")
                # Check actual similarities
                founder_bg = self.get_founder_background(founder.get('f.name', ''))
                if founder_bg and target_background:
                    similarities = self._calculate_manual_similarity(target_background, founder_bg)
                    print(f"      Actual similarities: {similarities}")
        else:
            print(f"   {llm_results}")
        
        print(f"\n🎯 YOUR ALGORITHM RESULTS:")
        if isinstance(algo_results, list):
            for i, founder in enumerate(algo_results[:5], 1):
                print(f"   {i}. {founder['founder']} (similarity: {founder['similarity']:.3f})")
                print(f"      Matching attributes: {founder['matching_attributes']}/{founder['total_compared']}")
        else:
            print(f"   {algo_results}")
        
        print(f"\n✅ ACCURACY CHECK:")
        if isinstance(algo_results, list) and isinstance(llm_results, list):
            algo_names = [f['founder'] for f in algo_results[:5]]
            llm_names = [f.get('f.name', '') for f in llm_results[:5]]
            
            overlap = set(algo_names) & set(llm_names)
            print(f"   Overlap between LLM and Algorithm: {len(overlap)}/5 founders")
            if overlap:
                print(f"   Common founders: {list(overlap)}")
            else:
                print(f"   No common founders - LLM may not be using similarity correctly!")
        
    def _calculate_manual_similarity(self, target_bg, founder_bg):
        """Manually calculate similarities for verification"""
        similarities = []
        
        if target_bg.get('f.university') == founder_bg.get('f.university') and target_bg.get('f.university'):
            similarities.append("same university")
        if target_bg.get('f.domain_expertise') == founder_bg.get('f.domain_expertise'):
            similarities.append("same domain expertise")
        if target_bg.get('f.technical_background') == founder_bg.get('f.technical_background'):
            similarities.append("same technical background")
        if target_bg.get('f.education_level') == founder_bg.get('f.education_level'):
            similarities.append("same education level")
        if target_bg.get('f.previous_company') == founder_bg.get('f.previous_company'):
            similarities.append("same previous company")
            
        return similarities if similarities else ["No clear similarities"]
    
    def interactive_search(self):
        """Interactive search interface"""
        print("🔍 ENHANCED FOUNDER SIMILARITY SEARCH")
        print("=" * 50)
        
        # Show available founders
        founders = self.get_available_founders(20)
        print(f"\n📋 Available founders (first 20):")
        for i, founder in enumerate(founders, 1):
            print(f"   {i:2d}. {founder}")
        
        while True:
            print(f"\n💬 Enter a founder name (or 'quit' to exit):")
            founder_name = input("   > ").strip()
            
            if founder_name.lower() in ['quit', 'exit', 'q']:
                break
                
            if not founder_name:
                continue
                
            # Check if founder exists
            background = self.get_founder_background(founder_name)
            if not background:
                print(f"   ❌ Founder '{founder_name}' not found. Try exact spelling.")
                continue
            
            print(f"\n🔄 Searching for founders similar to '{founder_name}'...")
            
            # Get results from both systems
            llm_results = self.llm_similar_founders(founder_name)
            algo_results = self.algorithm_similar_founders(founder_name)
            
            # Compare and display results
            self.compare_similarities(founder_name, llm_results, algo_results)
            
            input("\nPress Enter to continue...")
    
    def close(self):
        """Close database connection"""
        self.driver.close()

def main():
    """Main function"""
    search_system = EnhancedFounderSearch()
    
    try:
        search_system.interactive_search()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        search_system.close()

if __name__ == "__main__":
    main() 