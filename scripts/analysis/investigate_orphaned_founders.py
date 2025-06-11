#!/usr/bin/env python3
"""
Investigate Orphaned Founders
Analysis script to understand why some founders have no relationships
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

# Suppress Neo4j warnings
neo4j_logger = logging.getLogger("neo4j.notifications")
neo4j_logger.setLevel(logging.ERROR)

class OrphanedFounderInvestigator:
    def __init__(self):
        load_dotenv()
        
        # Get Neo4j credentials from environment
        self.uri = os.getenv('NEO4J_URI')
        self.username = os.getenv('NEO4J_USER', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        if not self.uri or not self.password:
            raise ValueError("Please set NEO4J_URI and NEO4J_PASSWORD in your .env file")
        
        # Connect to Neo4j
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        print("🔌 Connected to Neo4j for investigation")
    
    def run_query(self, query, description="", params=None):
        """Run a Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                records = list(result)
                if description:
                    print(f"\n📊 {description}")
                    print("-" * 50)
                return records
        except Exception as e:
            print(f"❌ Error running query: {e}")
            return []
    
    def analyze_orphaned_founders(self):
        """Analyze orphaned founders in detail"""
        print("\n🔍 ORPHANED FOUNDERS ANALYSIS")
        print("=" * 60)
        
        # Get sample orphaned founders
        orphaned_founders = self.run_query(
            """
            MATCH (f:Founder)
            WHERE NOT (f)-[]-()
            RETURN f.id, f.name, keys(f) as properties
            LIMIT 10
            """,
            "Sample Orphaned Founders:"
        )
        
        for founder in orphaned_founders:
            name = founder['f.name'] or 'Unknown'
            founder_id = founder['f.id'] or 'Unknown'
            props = ', '.join(founder['properties']) if founder['properties'] else 'No properties'
            print(f"  • {name} ({founder_id}) - Properties: {props}")
        
        # Count total orphaned vs connected founders
        total_stats = self.run_query(
            """
            MATCH (f:Founder)
            OPTIONAL MATCH (f)-[r]-()
            WITH f, count(r) as rel_count
            RETURN 
                sum(CASE WHEN rel_count = 0 THEN 1 ELSE 0 END) as orphaned_count,
                sum(CASE WHEN rel_count > 0 THEN 1 ELSE 0 END) as connected_count,
                count(f) as total_founders
            """,
            "Founder Connection Statistics:"
        )
        
        if total_stats:
            stats = total_stats[0]
            print(f"  • Total Founders: {stats['total_founders']:,}")
            print(f"  • Connected Founders: {stats['connected_count']:,}")
            print(f"  • Orphaned Founders: {stats['orphaned_count']:,}")
            print(f"  • Orphaned Percentage: {(stats['orphaned_count']/stats['total_founders']*100):.1f}%")
    
    def check_original_json_data(self):
        """Check the original JSON data to understand the source"""
        print("\n📂 CHECKING ORIGINAL JSON DATA")
        print("=" * 60)
        
        try:
            with open('startup_knowledge_graph.json', 'r') as f:
                kg_data = json.load(f)
            
            entities = kg_data.get('entities', {})
            relationships = kg_data.get('relationships', [])
            
            # Count founders in JSON
            founder_entities = {k: v for k, v in entities.items() if v.get('type') == 'founder'}
            print(f"📊 Founders in JSON: {len(founder_entities):,}")
            
            # Count WORKS_AT relationships in JSON
            works_at_rels = [r for r in relationships if r.get('type') == 'WORKS_AT']
            print(f"📊 WORKS_AT relationships in JSON: {len(works_at_rels):,}")
            
            # Get unique founder IDs from WORKS_AT relationships
            founders_with_jobs = set()
            for rel in works_at_rels:
                if 'source' in rel:
                    founders_with_jobs.add(rel['source'])
            
            print(f"📊 Unique founders with jobs: {len(founders_with_jobs):,}")
            
            # Find founders without jobs
            all_founder_ids = set(founder_entities.keys())
            founders_without_jobs = all_founder_ids - founders_with_jobs
            
            print(f"📊 Founders without jobs in JSON: {len(founders_without_jobs):,}")
            print(f"📊 This matches orphaned founders: {len(founders_without_jobs) == 319}")
            
            # Show sample founders without jobs
            print("\n📋 Sample founders without jobs in JSON:")
            sample_orphaned = list(founders_without_jobs)[:10]
            for founder_id in sample_orphaned:
                founder_data = founder_entities[founder_id]
                name = founder_data.get('properties', {}).get('name', 'Unknown')
                print(f"  • {name} ({founder_id})")
                
        except FileNotFoundError:
            print("❌ startup_knowledge_graph.json not found")
        except Exception as e:
            print(f"❌ Error reading JSON: {e}")
    
    def check_works_at_relationships(self):
        """Analyze the WORKS_AT relationships to understand the pattern"""
        print("\n🔗 WORKS_AT RELATIONSHIP ANALYSIS")
        print("=" * 60)
        
        # Check if all WORKS_AT relationships have founders as source
        works_at_analysis = self.run_query(
            """
            MATCH (f:Founder)-[r:WORKS_AT]->(s:Startup)
            RETURN count(r) as total_works_at,
                   count(DISTINCT f) as unique_founders_working,
                   count(DISTINCT s) as unique_startups_with_founders
            """,
            "WORKS_AT Relationship Statistics:"
        )
        
        if works_at_analysis:
            stats = works_at_analysis[0]
            print(f"  • Total WORKS_AT relationships: {stats['total_works_at']:,}")
            print(f"  • Unique founders working: {stats['unique_founders_working']:,}")
            print(f"  • Unique startups with founders: {stats['unique_startups_with_founders']:,}")
        
        # Check founder-to-startup ratio
        startup_founder_ratio = self.run_query(
            """
            MATCH (s:Startup)
            OPTIONAL MATCH (s)<-[:WORKS_AT]-(f:Founder)
            WITH s, count(f) as founder_count
            RETURN avg(founder_count) as avg_founders_per_startup,
                   min(founder_count) as min_founders,
                   max(founder_count) as max_founders,
                   sum(CASE WHEN founder_count = 0 THEN 1 ELSE 0 END) as startups_without_founders
            """,
            "Startup-Founder Distribution:"
        )
        
        if startup_founder_ratio:
            stats = startup_founder_ratio[0]
            print(f"  • Average founders per startup: {stats['avg_founders_per_startup']:.2f}")
            print(f"  • Min founders per startup: {stats['min_founders']}")
            print(f"  • Max founders per startup: {stats['max_founders']}")
            print(f"  • Startups without founders: {stats['startups_without_founders']}")
    
    def check_data_generation_pattern(self):
        """Check if this is a data generation artifact"""
        print("\n🎲 DATA GENERATION PATTERN ANALYSIS")
        print("=" * 60)
        
        # Check if orphaned founders have different properties
        orphaned_vs_connected = self.run_query(
            """
            MATCH (f:Founder)
            OPTIONAL MATCH (f)-[r]-()
            WITH f, count(r) as rel_count
            WITH 
                CASE WHEN rel_count = 0 THEN 'orphaned' ELSE 'connected' END as status,
                f
            RETURN status, 
                   count(f) as founder_count,
                   collect(f.id)[0..5] as sample_ids
            ORDER BY status
            """,
            "Orphaned vs Connected Founder IDs:"
        )
        
        for row in orphaned_vs_connected:
            status = row['status']
            count = row['founder_count']
            samples = row['sample_ids']
            print(f"  • {status.title()} founders: {count:,}")
            print(f"    Sample IDs: {samples}")
        
        # Check if there's a pattern in the IDs
        orphaned_id_pattern = self.run_query(
            """
            MATCH (f:Founder)
            WHERE NOT (f)-[]-()
            WITH f.id as founder_id
            ORDER BY founder_id
            RETURN collect(founder_id)[0..20] as first_20_orphaned_ids,
                   collect(founder_id)[-20..] as last_20_orphaned_ids
            """,
            "Orphaned Founder ID Patterns:"
        )
        
        if orphaned_id_pattern:
            pattern = orphaned_id_pattern[0]
            print(f"  • First 20 orphaned IDs: {pattern['first_20_orphaned_ids']}")
            print(f"  • Last 20 orphaned IDs: {pattern['last_20_orphaned_ids']}")
    
    
    def run_investigation(self):
        """Run complete investigation"""
        print("🕵️ ORPHANED FOUNDERS INVESTIGATION")
        print("=" * 80)
        
        try:
            self.analyze_orphaned_founders()
            self.check_original_json_data()
            self.check_works_at_relationships()
            self.check_data_generation_pattern()
            
            print("\n🎯 INVESTIGATION COMPLETE!")
            
        except Exception as e:
            print(f"\n❌ Investigation failed: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
            print("\n🔒 Neo4j connection closed")

def main():
    """Main function"""
    print("🕵️ Orphaned Founder Investigation Tool")
    print("=" * 50)
    
    try:
        investigator = OrphanedFounderInvestigator()
        investigator.run_investigation()
    except Exception as e:
        print(f"❌ Failed to initialize investigator: {e}")

if __name__ == "__main__":
    main() 