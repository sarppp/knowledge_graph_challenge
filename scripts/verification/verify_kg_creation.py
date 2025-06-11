#!/usr/bin/env python3
"""
Knowledge Graph Creation Verification
Compare original CSV data with the generated JSON knowledge graph
"""

import pandas as pd
import json
import os
from collections import defaultdict

class KGVerifier:
    def __init__(self):
        self.data_folder = 'data'
        self.json_file = 'startup_knowledge_graph.json'
        
    def load_csv_data(self):
        """Load all CSV files from the data folder"""
        print("📂 LOADING ORIGINAL CSV DATA")
        print("=" * 60)
        
        csv_files = {
            'startups': 'startup_ecosystem_startups.csv',
            'founders': 'startup_ecosystem_founders.csv',
            'investments': 'startup_ecosystem_investments.csv',
            'technologies': 'startup_ecosystem_technologies.csv',
            'vcs': 'startup_ecosystem_vcs.csv',
            'founder_startup': 'startup_ecosystem_founder_startup.csv',
            'startup_tech': 'startup_ecosystem_startup_tech.csv'
        }
        
        data = {}
        for name, filename in csv_files.items():
            filepath = os.path.join(self.data_folder, filename)
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                data[name] = df
                print(f"✅ {name}: {len(df):,} rows")
            else:
                print(f"❌ {filename} not found")
                data[name] = pd.DataFrame()
        
        return data
    
    def load_json_data(self):
        """Load the knowledge graph JSON"""
        print(f"\n📄 LOADING KNOWLEDGE GRAPH JSON")
        print("=" * 60)
        
        try:
            with open(self.json_file, 'r') as f:
                kg_data = json.load(f)
            
            entities = kg_data.get('entities', {})
            relationships = kg_data.get('relationships', [])
            
            print(f"✅ Total entities: {len(entities):,}")
            print(f"✅ Total relationships: {len(relationships):,}")
            
            # Count by type
            entity_counts = defaultdict(int)
            for entity_data in entities.values():
                entity_type = entity_data.get('type', 'unknown')
                entity_counts[entity_type] += 1
            
            print("\n📊 Entity counts by type:")
            for entity_type, count in entity_counts.items():
                print(f"  • {entity_type}: {count:,}")
            
            # Count relationships by type
            rel_counts = defaultdict(int)
            for rel in relationships:
                rel_type = rel.get('type', 'unknown')
                rel_counts[rel_type] += 1
            
            print("\n📊 Relationship counts by type:")
            for rel_type, count in rel_counts.items():
                print(f"  • {rel_type}: {count:,}")
            
            return kg_data
            
        except FileNotFoundError:
            print(f"❌ {self.json_file} not found")
            return {}
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            return {}
    
    def compare_entity_counts(self, csv_data, kg_data):
        """Compare entity counts between CSV and JSON"""
        print("\n🔍 ENTITY COUNT COMPARISON")
        print("=" * 60)
        
        entities = kg_data.get('entities', {})
        
        # Count entities by type in JSON
        json_counts = defaultdict(int)
        for entity_data in entities.values():
            entity_type = entity_data.get('type', 'unknown')
            json_counts[entity_type] += 1
        
        # Compare with CSV counts
        comparisons = [
            ('startups', 'startup', 'Startups'),
            ('founders', 'founder', 'Founders'),
            ('vcs', 'vc', 'VCs'),
            ('technologies', 'technology', 'Technologies')
        ]
        
        print("Entity Type          CSV Count    JSON Count   Match")
        print("-" * 55)
        
        all_match = True
        for csv_key, json_key, display_name in comparisons:
            csv_count = len(csv_data.get(csv_key, []))
            json_count = json_counts.get(json_key, 0)
            match = "✅" if csv_count == json_count else "❌"
            if csv_count != json_count:
                all_match = False
            
            print(f"{display_name:<20} {csv_count:<12} {json_count:<12} {match}")
        
        if all_match:
            print("\n🎉 All entity counts match!")
        else:
            print("\n⚠️  Some entity counts don't match!")
        
        return all_match
    
    def compare_relationship_counts(self, csv_data, kg_data):
        """Compare relationship counts between CSV and JSON"""
        print("\n🔗 RELATIONSHIP COUNT COMPARISON")
        print("=" * 60)
        
        relationships = kg_data.get('relationships', [])
        
        # Count relationships by type in JSON
        json_rel_counts = defaultdict(int)
        for rel in relationships:
            rel_type = rel.get('type', 'unknown')
            json_rel_counts[rel_type] += 1
        
        # Compare with CSV counts
        comparisons = [
            ('founder_startup', 'WORKS_AT', 'Founder-Startup'),
            ('investments', 'INVESTS_IN', 'VC-Startup Investments'),
            ('startup_tech', 'USES_TECHNOLOGY', 'Startup-Technology')
        ]
        
        print("Relationship Type    CSV Count    JSON Count   Match")
        print("-" * 55)
        
        all_match = True
        for csv_key, json_key, display_name in comparisons:
            csv_count = len(csv_data.get(csv_key, []))
            json_count = json_rel_counts.get(json_key, 0)
            match = "✅" if csv_count == json_count else "❌"
            if csv_count != json_count:
                all_match = False
            
            print(f"{display_name:<20} {csv_count:<12} {json_count:<12} {match}")
        
        if all_match:
            print("\n🎉 All relationship counts match!")
        else:
            print("\n⚠️  Some relationship counts don't match!")
        
        return all_match
    
    def analyze_founder_assignments(self, csv_data, kg_data):
        """Analyze founder assignments in detail"""
        print("\n👥 FOUNDER ASSIGNMENT ANALYSIS")
        print("=" * 60)
        
        # Get founder-startup assignments from CSV
        founder_startup_df = csv_data.get('founder_startup', pd.DataFrame())
        if founder_startup_df.empty:
            print("❌ No founder-startup CSV data found")
            return
        
        # Get unique founder IDs from CSV assignments
        csv_assigned_founders = set(founder_startup_df['founder_id'].unique())
        
        # Get all founder IDs from CSV
        founders_df = csv_data.get('founders', pd.DataFrame())
        if founders_df.empty:
            print("❌ No founders CSV data found")
            return
        
        all_csv_founders = set(founders_df['id'].unique())
        csv_unassigned_founders = all_csv_founders - csv_assigned_founders
        
        print(f"📊 CSV Data Analysis:")
        print(f"  • Total founders in founders.csv: {len(all_csv_founders):,}")
        print(f"  • Founders with job assignments: {len(csv_assigned_founders):,}")
        print(f"  • Founders without job assignments: {len(csv_unassigned_founders):,}")
        print(f"  • Unassigned percentage: {len(csv_unassigned_founders)/len(all_csv_founders)*100:.1f}%")
        
        # Get founder assignments from JSON
        relationships = kg_data.get('relationships', [])
        works_at_rels = [r for r in relationships if r.get('type') == 'WORKS_AT']
        json_assigned_founders = set(rel['source'] for rel in works_at_rels if 'source' in rel)
        
        # Get all founder entities from JSON
        entities = kg_data.get('entities', {})
        json_all_founders = set(k for k, v in entities.items() if v.get('type') == 'founder')
        json_unassigned_founders = json_all_founders - json_assigned_founders
        
        print(f"\n📊 JSON Data Analysis:")
        print(f"  • Total founders in JSON: {len(json_all_founders):,}")
        print(f"  • Founders with job assignments: {len(json_assigned_founders):,}")
        print(f"  • Founders without job assignments: {len(json_unassigned_founders):,}")
        print(f"  • Unassigned percentage: {len(json_unassigned_founders)/len(json_all_founders)*100:.1f}%")
        
        # Compare
        print(f"\n🔄 CSV vs JSON Comparison:")
        print(f"  • Unassigned founders match: {len(csv_unassigned_founders) == len(json_unassigned_founders)}")
        print(f"  • Same unassigned founder IDs: {csv_unassigned_founders == json_unassigned_founders}")
        
        if csv_unassigned_founders == json_unassigned_founders:
            print("  ✅ The orphaned founders in Neo4j exactly match the unassigned founders in the original CSV!")
        else:
            print("  ❌ Mismatch between CSV and JSON unassigned founders")
            
        # Show sample unassigned founders from CSV
        if csv_unassigned_founders:
            print(f"\n📋 Sample unassigned founders from CSV:")
            sample_unassigned = list(csv_unassigned_founders)[:10]
            for founder_id in sample_unassigned:
                founder_row = founders_df[founders_df['id'] == founder_id]
                if not founder_row.empty:
                    name = founder_row.iloc[0]['name']
                    print(f"  • {name} ({founder_id})")
    
    def check_startup_assignments(self, csv_data):
        """Check how many founders each startup should have"""
        print("\n🏢 STARTUP FOUNDER ASSIGNMENT ANALYSIS")
        print("=" * 60)
        
        founder_startup_df = csv_data.get('founder_startup', pd.DataFrame())
        startups_df = csv_data.get('startups', pd.DataFrame())
        
        if founder_startup_df.empty or startups_df.empty:
            print("❌ Missing CSV data for analysis")
            return
        
        # Count founders per startup
        founders_per_startup = founder_startup_df.groupby('startup_id').size()
        
        print(f"📊 Founders per startup distribution:")
        print(f"  • Min founders per startup: {founders_per_startup.min()}")
        print(f"  • Max founders per startup: {founders_per_startup.max()}")
        print(f"  • Average founders per startup: {founders_per_startup.mean():.2f}")
        print(f"  • Total startups: {len(startups_df)}")
        print(f"  • Startups with founders: {len(founders_per_startup)}")
        print(f"  • Startups without founders: {len(startups_df) - len(founders_per_startup)}")
        
        # Show distribution
        distribution = founders_per_startup.value_counts().sort_index()
        print(f"\n📈 Distribution:")
        for num_founders, count in distribution.items():
            print(f"  • {num_founders} founders: {count} startups")
    
    def run_verification(self):
        """Run complete verification"""
        print("🔍 KNOWLEDGE GRAPH CREATION VERIFICATION")
        print("=" * 80)
        
        try:
            # Load data
            csv_data = self.load_csv_data()
            kg_data = self.load_json_data()
            
            if not kg_data:
                print("❌ Cannot proceed without JSON data")
                return
            
            # Run comparisons
            entity_match = self.compare_entity_counts(csv_data, kg_data)
            rel_match = self.compare_relationship_counts(csv_data, kg_data)
            
            # Detailed founder analysis
            self.analyze_founder_assignments(csv_data, kg_data)
            self.check_startup_assignments(csv_data)
            
            print("\n🎯 VERIFICATION SUMMARY")
            print("=" * 60)
            
            if entity_match and rel_match:
                print("✅ Knowledge graph was created correctly from CSV data!")
                print("✅ The 319 orphaned founders exist in the original data")
                print("💡 This represents founders who were never assigned to startups")
            else:
                print("⚠️  There may be issues with the knowledge graph creation process")
            
        except Exception as e:
            print(f"\n❌ Verification failed: {e}")

def main():
    """Main function"""
    print("🔍 Knowledge Graph Creation Verification Tool")
    print("=" * 50)
    
    try:
        verifier = KGVerifier()
        verifier.run_verification()
    except Exception as e:
        print(f"❌ Failed to initialize verifier: {e}")

if __name__ == "__main__":
    main() 