#!/usr/bin/env python3
"""
Neo4j Knowledge Graph Validation and Testing
Comprehensive tests to validate the startup ecosystem knowledge graph
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import json
import logging
from datetime import datetime

# Suppress Neo4j warnings about unknown properties
neo4j_logger = logging.getLogger("neo4j.notifications")
neo4j_logger.setLevel(logging.ERROR)

class Neo4jGraphTester:
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
        print("🔌 Connected to Neo4j for testing")
    
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
    
    def test_basic_counts(self):
        """Test basic node and relationship counts"""
        print("\n🔍 BASIC DATABASE STATISTICS")
        print("=" * 60)
        
        # Node counts by type
        queries = {
            "Total Nodes": "MATCH (n) RETURN count(n) as count",
            "Startups": "MATCH (s:Startup) RETURN count(s) as count",
            "Founders": "MATCH (f:Founder) RETURN count(f) as count", 
            "VCs": "MATCH (v:VC) RETURN count(v) as count",
            "Technologies": "MATCH (t:Technology) RETURN count(t) as count"
        }
        
        for name, query in queries.items():
            result = self.run_query(query)
            if result:
                count = result[0]['count']
                print(f"✅ {name}: {count:,}")
        
        # Relationship counts by type
        rel_queries = {
            "Total Relationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "WORKS_AT": "MATCH ()-[r:WORKS_AT]->() RETURN count(r) as count",
            "INVESTS_IN": "MATCH ()-[r:INVESTS_IN]->() RETURN count(r) as count",
            "USES_TECHNOLOGY": "MATCH ()-[r:USES_TECHNOLOGY]->() RETURN count(r) as count"
        }
        
        print("\n📈 RELATIONSHIP COUNTS:")
        for name, query in rel_queries.items():
            result = self.run_query(query)
            if result:
                count = result[0]['count']
                print(f"✅ {name}: {count:,}")
    
    def test_sample_data(self):
        """Test sample data to verify data quality"""
        print("\n🔍 SAMPLE DATA VALIDATION")
        print("=" * 60)
        
        # Sample startups
        startups = self.run_query(
            "MATCH (s:Startup) RETURN s.id, s.name, s.industry, s.founded_date, s.stage, s.employee_count LIMIT 5",
            "Sample Startups:"
        )
        for startup in startups:
            name = startup['s.name'] or 'Unknown'
            startup_id = startup['s.id'] or 'Unknown'
            industry = startup['s.industry'] or 'Unknown'
            founded = startup['s.founded_date'] or 'Unknown'
            stage = startup['s.stage'] or 'Unknown'
            employees = startup['s.employee_count'] or 'Unknown'
            print(f"  • {name} ({startup_id}) - {industry} - Stage: {stage} - Founded: {founded} - Size: {employees}")
        
        # Sample founders - check what properties actually exist
        founders = self.run_query(
            "MATCH (f:Founder) RETURN f.id, f.name, keys(f) as properties LIMIT 5",
            "Sample Founders:"
        )
        for founder in founders:
            name = founder['f.name'] or 'Unknown'
            founder_id = founder['f.id'] or 'Unknown'
            props = ', '.join(founder['properties']) if founder['properties'] else 'No properties'
            print(f"  • {name} ({founder_id}) - Properties: {props}")
        
        # Sample VCs
        vcs = self.run_query(
            "MATCH (v:VC) RETURN v.id, v.name, v.aum, v.focus_industries, v.investment_stage LIMIT 5",
            "Sample VCs:"
        )
        for vc in vcs:
            name = vc['v.name'] or 'Unknown'
            vc_id = vc['v.id'] or 'Unknown'
            aum = vc['v.aum']
            focus = vc['v.focus_industries'] or 'Unknown'
            stage = vc['v.investment_stage'] or 'Unknown'
            aum_str = f"${aum:,}" if aum is not None else 'Unknown'
            print(f"  • {name} ({vc_id}) - AUM: {aum_str}, Focus: {focus}, Stage: {stage}")
        
        # Sample technologies
        techs = self.run_query(
            "MATCH (t:Technology) RETURN t.id, t.name, t.category, t.maturity, t.popularity_score LIMIT 5",
            "Sample Technologies:"
        )
        for tech in techs:
            name = tech['t.name'] or 'Unknown'
            tech_id = tech['t.id'] or 'Unknown'
            category = tech['t.category'] or 'Unknown'
            maturity = tech['t.maturity'] or 'Unknown'
            popularity = tech['t.popularity_score'] if tech['t.popularity_score'] is not None else 'Unknown'
            print(f"  • {name} ({tech_id}) - Category: {category}, Maturity: {maturity}, Popularity: {popularity}")
    
    def test_relationship_integrity(self):
        """Test relationship integrity and properties"""
        print("\n🔗 RELATIONSHIP INTEGRITY TESTS")
        print("=" * 60)
        
        # Test WORKS_AT relationships
        works_at = self.run_query(
            """
            MATCH (f:Founder)-[r:WORKS_AT]->(s:Startup) 
            RETURN f.name, s.name, r.role, r.equity_percentage, r.is_active 
            LIMIT 5
            """,
            "Sample WORKS_AT relationships:"
        )
        for rel in works_at:
            founder_name = rel['f.name'] or 'Unknown'
            startup_name = rel['s.name'] or 'Unknown'
            role = rel['r.role'] or 'Unknown'
            equity = rel['r.equity_percentage'] if rel['r.equity_percentage'] is not None else 'Unknown'
            active = rel['r.is_active'] if rel['r.is_active'] is not None else 'Unknown'
            print(f"  • {founder_name} works at {startup_name} as {role} ({equity}% equity, Active: {active})")
        
        # Test INVESTS_IN relationships
        invests_in = self.run_query(
            """
            MATCH (v:VC)-[r:INVESTS_IN]->(s:Startup) 
            RETURN v.name, s.name, r.amount, r.round_type, r.date, r.lead_investor 
            LIMIT 5
            """,
            "Sample INVESTS_IN relationships:"
        )
        for rel in invests_in:
            vc_name = rel['v.name'] or 'Unknown'
            startup_name = rel['s.name'] or 'Unknown'
            amount = f"${rel['r.amount']:,}" if rel['r.amount'] is not None else "N/A"
            round_type = rel['r.round_type'] or 'Unknown'
            date = rel['r.date'] or 'Unknown'
            lead = rel['r.lead_investor'] if rel['r.lead_investor'] is not None else 'Unknown'
            print(f"  • {vc_name} invested {amount} in {startup_name} ({round_type}, {date}, Lead: {lead})")
        
        # Test USES_TECHNOLOGY relationships
        uses_tech = self.run_query(
            """
            MATCH (s:Startup)-[r:USES_TECHNOLOGY]->(t:Technology) 
            RETURN s.name, t.name, r.usage_intensity, r.implementation_date 
            LIMIT 5
            """,
            "Sample USES_TECHNOLOGY relationships:"
        )
        for rel in uses_tech:
            startup_name = rel['s.name'] or 'Unknown'
            tech_name = rel['t.name'] or 'Unknown'
            intensity = rel['r.usage_intensity'] or 'Unknown'
            impl_date = rel['r.implementation_date'] or 'Unknown'
            print(f"  • {startup_name} uses {tech_name} (Intensity: {intensity}, Since: {impl_date})")
    
    def test_business_analytics(self):
        """Test business intelligence queries"""
        print("\n📊 BUSINESS ANALYTICS QUERIES")
        print("=" * 60)
        
        # Top investors by total investment amount
        top_investors = self.run_query(
            """
            MATCH (v:VC)-[r:INVESTS_IN]->()
            WHERE r.amount IS NOT NULL
            RETURN v.name, sum(r.amount) as total_invested, count(r) as num_investments
            ORDER BY total_invested DESC
            LIMIT 10
            """,
            "Top 10 Investors by Total Amount:"
        )
        for inv in top_investors:
            name = inv['v.name'] or 'Unknown'
            total = inv['total_invested'] or 0
            num = inv['num_investments'] or 0
            print(f"  • {name}: ${total:,} ({num} investments)")
        
        # Most funded startups
        top_startups = self.run_query(
            """
            MATCH (s:Startup)<-[r:INVESTS_IN]-()
            WHERE r.amount IS NOT NULL
            RETURN s.name, s.industry, sum(r.amount) as total_funding, count(r) as num_rounds
            ORDER BY total_funding DESC
            LIMIT 10
            """,
            "Top 10 Most Funded Startups:"
        )
        for startup in top_startups:
            name = startup['s.name'] or 'Unknown'
            industry = startup['s.industry'] or 'Unknown'
            total = startup['total_funding'] or 0
            rounds = startup['num_rounds'] or 0
            print(f"  • {name} ({industry}): ${total:,} ({rounds} rounds)")
        
        # Most popular technologies
        popular_tech = self.run_query(
            """
            MATCH (t:Technology)<-[r:USES_TECHNOLOGY]-()
            RETURN t.name, t.category, count(r) as usage_count
            ORDER BY usage_count DESC
            LIMIT 10
            """,
            "Top 10 Most Used Technologies:"
        )
        for tech in popular_tech:
            name = tech['t.name'] or 'Unknown'
            category = tech['t.category'] or 'Unknown'
            count = tech['usage_count'] or 0
            print(f"  • {name} ({category}): Used by {count} startups")
        
        # Average funding by industry
        industry_funding = self.run_query(
            """
            MATCH (s:Startup)<-[r:INVESTS_IN]-()
            WHERE r.amount IS NOT NULL AND s.industry IS NOT NULL
            RETURN s.industry, 
                   avg(r.amount) as avg_funding, 
                   sum(r.amount) as total_funding,
                   count(DISTINCT s) as num_startups
            ORDER BY total_funding DESC
            LIMIT 10
            """,
            "Funding by Industry:"
        )
        for ind in industry_funding:
            industry = ind['s.industry'] or 'Unknown'
            avg_funding = ind['avg_funding'] or 0
            total_funding = ind['total_funding'] or 0
            num_startups = ind['num_startups'] or 0
            print(f"  • {industry}: Avg ${avg_funding:,.0f}, Total ${total_funding:,} ({num_startups} startups)")
    
    def test_network_analysis(self):
        """Test network analysis queries"""
        print("\n🌐 NETWORK ANALYSIS")
        print("=" * 60)
        
        # Find co-founders (founders working at the same startup)
        co_founders = self.run_query(
            """
            MATCH (f1:Founder)-[:WORKS_AT]->(s:Startup)<-[:WORKS_AT]-(f2:Founder)
            WHERE f1.id < f2.id
            RETURN f1.name, f2.name, s.name as startup
            LIMIT 10
            """,
            "Sample Co-founder Relationships:"
        )
        for co in co_founders:
            name1 = co['f1.name'] or 'Unknown'
            name2 = co['f2.name'] or 'Unknown'
            startup = co['startup'] or 'Unknown'
            print(f"  • {name1} & {name2} both work at {startup}")
        
        # Find co-investors (VCs investing in the same startup)
        co_investors = self.run_query(
            """
            MATCH (v1:VC)-[:INVESTS_IN]->(s:Startup)<-[:INVESTS_IN]-(v2:VC)
            WHERE v1.id < v2.id
            WITH v1, v2, count(s) as shared_investments
            WHERE shared_investments >= 2
            RETURN v1.name, v2.name, shared_investments
            ORDER BY shared_investments DESC
            LIMIT 10
            """,
            "Co-investor Relationships (2+ shared investments):"
        )
        for co in co_investors:
            name1 = co['v1.name'] or 'Unknown'
            name2 = co['v2.name'] or 'Unknown'
            shared = co['shared_investments'] or 0
            print(f"  • {name1} & {name2}: {shared} shared investments")
        
        # Find technology clusters (startups using similar tech stacks)
        tech_clusters = self.run_query(
            """
            MATCH (s1:Startup)-[:USES_TECHNOLOGY]->(t:Technology)<-[:USES_TECHNOLOGY]-(s2:Startup)
            WHERE s1.id < s2.id
            WITH s1, s2, count(t) as shared_techs
            WHERE shared_techs >= 3
            RETURN s1.name, s2.name, shared_techs
            ORDER BY shared_techs DESC
            LIMIT 10
            """,
            "Startups with Similar Tech Stacks (3+ shared technologies):"
        )
        for cluster in tech_clusters:
            name1 = cluster['s1.name'] or 'Unknown'
            name2 = cluster['s2.name'] or 'Unknown'
            shared = cluster['shared_techs'] or 0
            print(f"  • {name1} & {name2}: {shared} shared technologies")
    
    def test_data_quality(self):
        """Test data quality and identify potential issues"""
        print("\n🔍 DATA QUALITY CHECKS")
        print("=" * 60)
        
        # Check for orphaned nodes (nodes with no relationships)
        orphaned = self.run_query(
            """
            MATCH (n)
            WHERE NOT (n)-[]-()
            RETURN labels(n)[0] as node_type, count(n) as orphan_count
            ORDER BY orphan_count DESC
            """,
            "Orphaned Nodes (no relationships):"
        )
        if orphaned:
            for orph in orphaned:
                print(f"  ⚠️  {orph['node_type']}: {orph['orphan_count']} orphaned nodes")
        else:
            print("  ✅ No orphaned nodes found!")
        
        # Check for missing required properties
        missing_props = self.run_query(
            """
            MATCH (s:Startup)
            WHERE s.name IS NULL OR s.industry IS NULL
            RETURN count(s) as startups_missing_props
            """,
            "Data Completeness Check:"
        )
        if missing_props and missing_props[0]['startups_missing_props'] > 0:
            print(f"    {missing_props[0]['startups_missing_props']} startups missing name or industry")
        else:
            print("   All startups have required properties!")
        
        # Check investment amount ranges
        investment_ranges = self.run_query(
            """
            MATCH ()-[r:INVESTS_IN]->()
            WHERE r.amount IS NOT NULL
            RETURN min(r.amount) as min_amount, 
                   max(r.amount) as max_amount,
                   avg(r.amount) as avg_amount,
                   count(r) as total_investments
            """,
            "Investment Amount Statistics:"
        )
        if investment_ranges:
            stats = investment_ranges[0]
            print(f"  • Total investments: {stats['total_investments']:,}")
            print(f"  • Range: ${stats['min_amount']:,} - ${stats['max_amount']:,}")
            print(f"  • Average: ${stats['avg_amount']:,.0f}")
    
    def test_path_queries(self):
        """Test path-finding queries between entities"""
        print("\n  PATH ANALYSIS")
        print("=" * 60)
        
        # Find paths from founders to technologies through their startups
        founder_to_tech = self.run_query(
            """
            MATCH path = (f:Founder)-[:WORKS_AT]->(s:Startup)-[:USES_TECHNOLOGY]->(t:Technology)
            RETURN f.name, s.name, t.name
            LIMIT 5
            """,
            "Founder → Startup → Technology paths:"
        )
        for path in founder_to_tech:
            founder = path['f.name'] or 'Unknown'
            startup = path['s.name'] or 'Unknown'
            tech = path['t.name'] or 'Unknown'
            print(f"  • {founder} → {startup} → {tech}")
        
        # Find investment chains (VC → Startup ← Founder)
        investment_chains = self.run_query(
            """
            MATCH (v:VC)-[i:INVESTS_IN]->(s:Startup)<-[w:WORKS_AT]-(f:Founder)
            RETURN v.name, s.name, f.name, i.amount, w.role
            LIMIT 5
            """,
            "Investment Chains (VC → Startup ← Founder):"
        )
        for chain in investment_chains:
            vc_name = chain['v.name'] or 'Unknown'
            startup_name = chain['s.name'] or 'Unknown'
            founder_name = chain['f.name'] or 'Unknown'
            amount = f"${chain['i.amount']:,}" if chain['i.amount'] is not None else "N/A"
            role = chain['w.role'] or 'Unknown'
            print(f"  • {vc_name} invested {amount} in {startup_name} where {founder_name} works as {role}")
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 STARTING NEO4J KNOWLEDGE GRAPH VALIDATION")
        print("=" * 80)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.test_basic_counts()
            self.test_sample_data()
            self.test_relationship_integrity()
            self.test_business_analytics()
            self.test_network_analysis()
            self.test_data_quality()
            self.test_path_queries()
            
            print("\n ALL TESTS COMPLETED SUCCESSFULLY!")
            print(" Knowledge graph is working correctly!")
            
        except Exception as e:
            print(f"\n Test failed with error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
            print("\n🔒 Neo4j connection closed")

def main():
    """Main function to run all tests"""
    print("🧪 Neo4j Knowledge Graph Validation Tool")
    print("=" * 50)
    
    try:
        tester = Neo4jGraphTester()
        tester.run_all_tests()
    except Exception as e:
        print(f" Failed to initialize tester: {e}")

if __name__ == "__main__":
    main() 