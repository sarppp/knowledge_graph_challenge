#!/usr/bin/env python3
"""
Similarity Analysis for Startup Ecosystem Knowledge Graph
Fast and simple similarity functions using NetworkX
"""

import json
import networkx as nx
from collections import defaultdict, Counter
import pandas as pd

class StartupSimilarityAnalyzer:
    def __init__(self, json_file_path):
        """Initialize with knowledge graph JSON file"""
        self.graph = nx.Graph()
        self.entities = {}
        self.load_data(json_file_path)
    
    def load_data(self, json_file_path):
        """Load knowledge graph into NetworkX"""
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        self.entities = data['entities']
        
        # Add nodes
        for entity_id, entity_data in self.entities.items():
            self.graph.add_node(entity_id, **entity_data['properties'], type=entity_data['type'])
        
        # Add edges
        for rel in data['relationships']:
            self.graph.add_edge(rel['source'], rel['target'], 
                              type=rel['type'], **rel.get('properties', {}))
        
        print(f" Loaded graph: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
    
    def startup_similarity_by_technology(self):
        """Find startups with similar technology stacks"""
        startup_techs = defaultdict(set)
        
        for node in self.graph.nodes():
            if self.graph.nodes[node].get('type') == 'startup':
                for neighbor in self.graph.neighbors(node):
                    if self.graph.nodes[neighbor].get('type') == 'technology':
                        startup_techs[node].add(neighbor)
        
        similarities = []
        startup_list = list(startup_techs.keys())
        
        for i in range(len(startup_list)):
            for j in range(i+1, len(startup_list)):
                s1, s2 = startup_list[i], startup_list[j]
                techs1, techs2 = startup_techs[s1], startup_techs[s2]
                
                if techs1 and techs2:
                    jaccard = len(techs1 & techs2) / len(techs1 | techs2)
                    if jaccard > 0:
                        similarities.append({
                            'startup1': self.graph.nodes[s1].get('name', s1),
                            'startup2': self.graph.nodes[s2].get('name', s2),
                            'similarity': jaccard,
                            'shared_techs': len(techs1 & techs2),
                            'total_techs': len(techs1 | techs2)
                        })
        
        return sorted(similarities, key=lambda x: x['similarity'], reverse=True)
    
    def vc_similarity_by_investments(self):
        """Find VCs with similar investment patterns"""
        vc_startups = defaultdict(set)
        
        for node in self.graph.nodes():
            if self.graph.nodes[node].get('type') == 'vc':
                for neighbor in self.graph.neighbors(node):
                    if self.graph.nodes[neighbor].get('type') == 'startup':
                        vc_startups[node].add(neighbor)
        
        similarities = []
        vc_list = list(vc_startups.keys())
        
        for i in range(len(vc_list)):
            for j in range(i+1, len(vc_list)):
                v1, v2 = vc_list[i], vc_list[j]
                startups1, startups2 = vc_startups[v1], vc_startups[v2]
                
                if startups1 and startups2:
                    jaccard = len(startups1 & startups2) / len(startups1 | startups2)
                    if jaccard > 0:
                        similarities.append({
                            'vc1': self.graph.nodes[v1].get('name', v1),
                            'vc2': self.graph.nodes[v2].get('name', v2),
                            'similarity': jaccard,
                            'shared_investments': len(startups1 & startups2),
                            'total_investments': len(startups1 | startups2)
                        })
        
        return sorted(similarities, key=lambda x: x['similarity'], reverse=True)
    
    def founder_similarity_by_background(self):
        """Find founders with similar backgrounds"""
        founders = [n for n in self.graph.nodes() if self.graph.nodes[n].get('type') == 'founder']
        similarities = []
        
        for i in range(len(founders)):
            for j in range(i+1, len(founders)):
                f1, f2 = founders[i], founders[j]
                f1_data = self.graph.nodes[f1]
                f2_data = self.graph.nodes[f2]
                
                similarity_score = 0
                comparisons = 0
                
                # Compare university
                if f1_data.get('university') and f2_data.get('university'):
                    comparisons += 1
                    if f1_data['university'] == f2_data['university']:
                        similarity_score += 1
                
                # Compare domain expertise
                if f1_data.get('domain_expertise') and f2_data.get('domain_expertise'):
                    comparisons += 1
                    if f1_data['domain_expertise'] == f2_data['domain_expertise']:
                        similarity_score += 1
                
                # Compare technical background
                if f1_data.get('technical_background') and f2_data.get('technical_background'):
                    comparisons += 1
                    if f1_data['technical_background'] == f2_data['technical_background']:
                        similarity_score += 1
                
                if comparisons > 0:
                    final_similarity = similarity_score / comparisons
                    if final_similarity > 0:
                        similarities.append({
                            'founder1': f1_data.get('name', f1),
                            'founder2': f2_data.get('name', f2),
                            'similarity': final_similarity,
                            'matching_attributes': similarity_score,
                            'total_compared': comparisons
                        })
        
        return sorted(similarities, key=lambda x: x['similarity'], reverse=True)
    
    def get_top_similar_entities(self, entity_type='startup', top_n=10):
        """Get top N most similar entities"""
        if entity_type == 'startup':
            return self.startup_similarity_by_technology()[:top_n]
        elif entity_type == 'vc':
            return self.vc_similarity_by_investments()[:top_n]
        elif entity_type == 'founder':
            return self.founder_similarity_by_background()[:top_n]
    
    def run_all_similarity_analysis(self):
        """Run complete similarity analysis"""
        print(" STARTUP ECOSYSTEM SIMILARITY ANALYSIS")
        print("=" * 60)
        
        # Startup similarities
        print("\n TOP 10 MOST SIMILAR STARTUPS (by technology):")
        startup_sims = self.get_top_similar_entities('startup', 10)
        for i, sim in enumerate(startup_sims[:10], 1):
            print(f"{i:2d}. {sim['startup1']} ↔ {sim['startup2']}")
            print(f"    Similarity: {sim['similarity']:.3f} | Shared techs: {sim['shared_techs']}")
        
        # VC similarities
        print("\n TOP 10 MOST SIMILAR VCs (by investment patterns):")
        vc_sims = self.get_top_similar_entities('vc', 10)
        for i, sim in enumerate(vc_sims[:10], 1):
            print(f"{i:2d}. {sim['vc1']} ↔ {sim['vc2']}")
            print(f"    Similarity: {sim['similarity']:.3f} | Shared investments: {sim['shared_investments']}")
        
        # Founder similarities
        print("\n TOP 10 MOST SIMILAR FOUNDERS (by background):")
        founder_sims = self.get_top_similar_entities('founder', 10)
        for i, sim in enumerate(founder_sims[:10], 1):
            print(f"{i:2d}. {sim['founder1']} ↔ {sim['founder2']}")
            print(f"    Similarity: {sim['similarity']:.3f} | Matching attributes: {sim['matching_attributes']}/{sim['total_compared']}")

    def find_similar_startups_to(self, target_startup_name, top_n=5):
        """Find startups most similar to a specific startup"""
        # Find the target startup
        target_id = None
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'startup' and node_data.get('name', '').lower() == target_startup_name.lower():
                target_id = node_id
                break
        
        if not target_id:
            return f"Startup '{target_startup_name}' not found"
        
        # Get target's technologies
        target_techs = set()
        for neighbor in self.graph.neighbors(target_id):
            if self.graph.nodes[neighbor].get('type') == 'technology':
                target_techs.add(neighbor)
        
        if not target_techs:
            return f"No technologies found for '{target_startup_name}'"
        
        # Calculate similarities with other startups
        similarities = []
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'startup' and node_id != target_id:
                # Get this startup's technologies
                startup_techs = set()
                for neighbor in self.graph.neighbors(node_id):
                    if self.graph.nodes[neighbor].get('type') == 'technology':
                        startup_techs.add(neighbor)
                
                if startup_techs:
                    jaccard = len(target_techs & startup_techs) / len(target_techs | startup_techs)
                    if jaccard > 0:
                        similarities.append({
                            'startup': node_data.get('name', node_id),
                            'similarity': jaccard,
                            'shared_techs': len(target_techs & startup_techs),
                            'total_techs': len(target_techs | startup_techs)
                        })
        
        return sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:top_n]
    
    def find_similar_founders_to(self, target_founder_name, top_n=5):
        """Find founders most similar to a specific founder"""
        # Find the target founder
        target_id = None
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'founder' and node_data.get('name', '').lower() == target_founder_name.lower():
                target_id = node_id
                break
        
        if not target_id:
            return f"Founder '{target_founder_name}' not found"
        
        target_data = self.graph.nodes[target_id]
        similarities = []
        
        # Compare with other founders
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'founder' and node_id != target_id:
                similarity_score = 0
                comparisons = 0
                
                # Compare university
                if target_data.get('university') and node_data.get('university'):
                    comparisons += 1
                    if target_data['university'] == node_data['university']:
                        similarity_score += 1
                
                # Compare domain expertise
                if target_data.get('domain_expertise') and node_data.get('domain_expertise'):
                    comparisons += 1
                    if target_data['domain_expertise'] == node_data['domain_expertise']:
                        similarity_score += 1
                
                # Compare technical background
                if target_data.get('technical_background') and node_data.get('technical_background'):
                    comparisons += 1
                    if target_data['technical_background'] == node_data['technical_background']:
                        similarity_score += 1
                
                if comparisons > 0:
                    final_similarity = similarity_score / comparisons
                    if final_similarity > 0:
                        similarities.append({
                            'founder': node_data.get('name', node_id),
                            'similarity': final_similarity,
                            'matching_attributes': similarity_score,
                            'total_compared': comparisons
                        })
        
        return sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:top_n]
    
    def find_similar_vcs_to(self, target_vc_name, top_n=5):
        """Find VCs most similar to a specific VC"""
        # Find the target VC
        target_id = None
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'vc' and node_data.get('name', '').lower() == target_vc_name.lower():
                target_id = node_id
                break
        
        if not target_id:
            return f"VC '{target_vc_name}' not found"
        
        # Get target's investments
        target_investments = set()
        for neighbor in self.graph.neighbors(target_id):
            if self.graph.nodes[neighbor].get('type') == 'startup':
                target_investments.add(neighbor)
        
        if not target_investments:
            return f"No investments found for '{target_vc_name}'"
        
        # Calculate similarities with other VCs
        similarities = []
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'vc' and node_id != target_id:
                # Get this VC's investments
                vc_investments = set()
                for neighbor in self.graph.neighbors(node_id):
                    if self.graph.nodes[neighbor].get('type') == 'startup':
                        vc_investments.add(neighbor)
                
                if vc_investments:
                    jaccard = len(target_investments & vc_investments) / len(target_investments | vc_investments)
                    if jaccard > 0:
                        similarities.append({
                            'vc': node_data.get('name', node_id),
                            'similarity': jaccard,
                            'shared_investments': len(target_investments & vc_investments),
                            'total_investments': len(target_investments | vc_investments)
                        })
        
        return sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:top_n]

def main():
    """Main function"""
    print(" Startup Ecosystem Similarity Analysis")
    print("=" * 50)
    
    try:
        analyzer = StartupSimilarityAnalyzer('startup_knowledge_graph.json')
        analyzer.run_all_similarity_analysis()
    except Exception as e:
        print(f" Error: {e}")

if __name__ == "__main__":
    main() 