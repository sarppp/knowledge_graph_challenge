#!/usr/bin/env python3
"""
Simple Neo4j Knowledge Graph Importer
Clean implementation for importing startup ecosystem JSON data to Neo4j
"""

import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleNeo4jImporter:
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
        logger.info("🔌 Connected to Neo4j")
    
    def test_connection(self):
        """Test the Neo4j connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("✅ Neo4j connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
            return False
    
    def clear_database(self):
        """Clear all nodes and relationships"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("🧹 Database cleared")
    
    def get_node_counts(self):
        """Get current node and relationship counts"""
        with self.driver.session() as session:
            # Count nodes
            node_result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = node_result.single()['total_nodes']
            
            # Count relationships
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as total_rels")
            total_rels = rel_result.single()['total_rels']
            
            # Count by type
            startup_count = session.run("MATCH (s:Startup) RETURN count(s) as count").single()['count']
            founder_count = session.run("MATCH (f:Founder) RETURN count(f) as count").single()['count']
            vc_count = session.run("MATCH (v:VC) RETURN count(v) as count").single()['count']
            tech_count = session.run("MATCH (t:Technology) RETURN count(t) as count").single()['count']
            
            return {
                'total_nodes': total_nodes,
                'total_relationships': total_rels,
                'startups': startup_count,
                'founders': founder_count,
                'vcs': vc_count,
                'technologies': tech_count
            }
    
    def create_constraints(self):
        """Create uniqueness constraints"""
        constraints = [
            "CREATE CONSTRAINT startup_id IF NOT EXISTS FOR (s:Startup) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT founder_id IF NOT EXISTS FOR (f:Founder) REQUIRE f.id IS UNIQUE", 
            "CREATE CONSTRAINT vc_id IF NOT EXISTS FOR (v:VC) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT tech_id IF NOT EXISTS FOR (t:Technology) REQUIRE t.id IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✅ Created constraint: {constraint.split()[2]}")
                except Exception as e:
                    logger.warning(f"Constraint already exists or failed: {e}")
    
    def import_entities(self, entities):
        """Import all entities to Neo4j"""
        logger.info(f"📥 Importing {len(entities)} entities...")
        
        # Group entities by type
        entity_groups = {}
        for entity_id, entity_data in entities.items():
            entity_type = entity_data['type']
            if entity_type not in entity_groups:
                entity_groups[entity_type] = []
            
            # Add the entity with its ID
            entity_with_id = entity_data['properties'].copy()
            entity_with_id['id'] = entity_id
            entity_groups[entity_type].append(entity_with_id)
        
        # Import each entity type
        for entity_type, entity_list in entity_groups.items():
            self._import_entity_batch(entity_type, entity_list)
    
    def _import_entity_batch(self, entity_type, entities):
        """Import a batch of entities of the same type"""
        # Map entity types to Neo4j labels
        label_map = {
            'startup': 'Startup',
            'founder': 'Founder', 
            'vc': 'VC',
            'technology': 'Technology'
        }
        
        label = label_map.get(entity_type, entity_type.title())
        
        # Create Cypher query
        query = f"""
        UNWIND $entities AS entity
        CREATE (n:{label})
        SET n = entity
        """
        
        with self.driver.session() as session:
            session.run(query, entities=entities)
        
        logger.info(f"✅ Imported {len(entities)} {label} entities")
    
    def import_relationships(self, relationships):
        """Import all relationships to Neo4j"""
        logger.info(f"🔗 Importing {len(relationships)} relationships...")
        
        # Group relationships by type
        rel_groups = {}
        for rel in relationships:
            rel_type = rel['type']
            if rel_type not in rel_groups:
                rel_groups[rel_type] = []
            rel_groups[rel_type].append(rel)
        
        # Import each relationship type
        for rel_type, rel_list in rel_groups.items():
            self._import_relationship_batch(rel_type, rel_list)
    
    def _import_relationship_batch(self, rel_type, relationships):
        """Import a batch of relationships of the same type"""
        
        # Create Cypher query
        query = f"""
        UNWIND $relationships AS rel
        MATCH (source {{id: rel.source}})
        MATCH (target {{id: rel.target}})
        CREATE (source)-[r:{rel_type}]->(target)
        SET r = rel.properties
        """
        
        with self.driver.session() as session:
            session.run(query, relationships=relationships)
        
        logger.info(f"✅ Imported {len(relationships)} {rel_type} relationships")
    
    def import_knowledge_graph(self, json_file_path):
        """Import complete knowledge graph from JSON file"""
        logger.info(f"📂 Loading knowledge graph from {json_file_path}")
        
        # Load JSON data
        with open(json_file_path, 'r') as f:
            kg_data = json.load(f)
        
        entities = kg_data.get('entities', {})
        relationships = kg_data.get('relationships', [])
        
        logger.info(f"📊 Found {len(entities)} entities and {len(relationships)} relationships")
        
        # Create constraints first
        logger.info("🔧 Creating constraints...")
        self.create_constraints()
        
        # Import entities
        self.import_entities(entities)
        
        # Import relationships
        self.import_relationships(relationships)
        
        # Show final statistics
        stats = self.get_node_counts()
        logger.info("🎉 Import completed successfully!")
        logger.info(f"📊 Final counts:")
        logger.info(f"   • Total nodes: {stats['total_nodes']}")
        logger.info(f"   • Total relationships: {stats['total_relationships']}")
        logger.info(f"   • Startups: {stats['startups']}")
        logger.info(f"   • Founders: {stats['founders']}")
        logger.info(f"   • VCs: {stats['vcs']}")
        logger.info(f"   • Technologies: {stats['technologies']}")
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("🔒 Neo4j connection closed")

def main():
    """Main function to run the import"""
    print("🚀 Simple Neo4j Knowledge Graph Importer")
    print("=" * 50)
    
    try:
        # Initialize importer
        importer = SimpleNeo4jImporter()
        
        # Test connection
        if not importer.test_connection():
            print("❌ Failed to connect to Neo4j. Check your .env file.")
            return
        
        # Check if data already exists
        stats = importer.get_node_counts()
        if stats['total_nodes'] > 0:
            print(f"⚠️  Database already contains {stats['total_nodes']} nodes")
            response = input("Clear database and reimport? (y/N): ")
            if response.lower() == 'y':
                importer.clear_database()
            else:
                print("Import cancelled.")
                return
        
        # Import the knowledge graph
        importer.import_knowledge_graph('startup_knowledge_graph.json')
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
    finally:
        if 'importer' in locals():
            importer.close()

if __name__ == "__main__":
    main() 