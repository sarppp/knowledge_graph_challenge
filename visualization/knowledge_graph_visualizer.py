#!/usr/bin/env python3
"""
Interactive Knowledge Graph Visualizer
Creates beautiful network visualizations using pyvis with similarity analysis
"""

import json
import networkx as nx
from pyvis.network import Network
from collections import defaultdict, Counter
import colorsys
import math

class KnowledgeGraphVisualizer:
    def __init__(self, json_file_path):
        """Initialize with knowledge graph JSON file"""
        self.json_file_path = json_file_path
        self.entities = {}
        self.relationships = []
        self.graph = nx.Graph()
        self.load_data()
        
    def load_data(self):
        """Load knowledge graph data"""
        with open(self.json_file_path, 'r') as f:
            data = json.load(f)
        
        self.entities = data['entities']
        self.relationships = data['relationships']
        
        # Build NetworkX graph for analysis
        for entity_id, entity_data in self.entities.items():
            self.graph.add_node(entity_id, **entity_data['properties'], type=entity_data['type'])
        
        for rel in self.relationships:
            self.graph.add_edge(rel['source'], rel['target'], 
                              type=rel['type'], **rel.get('properties', {}))
        
        print(f"📊 Loaded: {len(self.entities)} entities, {len(self.relationships)} relationships")
    
    def get_entity_stats(self):
        """Get statistics about entities"""
        stats = defaultdict(int)
        for entity_data in self.entities.values():
            stats[entity_data['type']] += 1
        return dict(stats)
    
    def get_node_color_and_shape(self, entity_type):
        """Get color and shape for different entity types"""
        styles = {
            'startup': {'color': '#FF6B6B', 'shape': 'dot', 'size': 25},
            'founder': {'color': '#4ECDC4', 'shape': 'triangle', 'size': 20},
            'vc': {'color': '#45B7D1', 'shape': 'square', 'size': 30},
            'technology': {'color': '#96CEB4', 'shape': 'diamond', 'size': 15}
        }
        return styles.get(entity_type, {'color': '#FECA57', 'shape': 'dot', 'size': 20})
    
    def get_edge_color(self, relationship_type):
        """Get color for different relationship types"""
        colors = {
            'FOUNDED': '#FF6B6B',
            'WORKS_AT': '#4ECDC4', 
            'INVESTED_IN': '#45B7D1',
            'USES_TECHNOLOGY': '#96CEB4',
            'SIMILAR_TO': '#FF9FF3'
        }
        return colors.get(relationship_type, '#95A5A6')
    
    def calculate_startup_similarities(self, threshold=0.2):
        """Calculate startup similarities based on shared technologies"""
        startup_techs = defaultdict(set)
        
        # Build startup-technology mapping
        for entity_id, entity_data in self.entities.items():
            if entity_data['type'] == 'startup':
                for rel in self.relationships:
                    if (rel['source'] == entity_id and 
                        rel['type'] == 'USES_TECHNOLOGY' and
                        self.entities[rel['target']]['type'] == 'technology'):
                        startup_techs[entity_id].add(rel['target'])
        
        similarities = []
        startup_list = list(startup_techs.keys())
        
        for i in range(len(startup_list)):
            for j in range(i+1, len(startup_list)):
                s1, s2 = startup_list[i], startup_list[j]
                techs1, techs2 = startup_techs[s1], startup_techs[s2]
                
                if techs1 and techs2:
                    jaccard = len(techs1 & techs2) / len(techs1 | techs2)
                    if jaccard >= threshold:
                        similarities.append({
                            'startup1': s1,
                            'startup2': s2,
                            'similarity': jaccard,
                            'shared_techs': len(techs1 & techs2)
                        })
        
        return similarities
    
    def create_network_visualization(self, 
                                   include_similarities=True,
                                   similarity_threshold=0.3,
                                   max_nodes=200,
                                   output_file='knowledge_graph.html'):
        """Create interactive network visualization"""
        
        # Initialize pyvis network
        net = Network(
            height="800px", 
            width="100%", 
            bgcolor="#1a1a1a",
            font_color="white",
            notebook=False
        )
        
        # Configure physics
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100},
            "barnesHut": {
              "gravitationalConstant": -80000,
              "springConstant": 0.001,
              "springLength": 200
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 200
          }
        }
        """)
        
        # Add nodes with limits to avoid overwhelming visualization
        entity_counts = defaultdict(int)
        added_nodes = 0
        
        print(f"🎨 Creating visualization...")
        
        for entity_id, entity_data in self.entities.items():
            if added_nodes >= max_nodes:
                break
                
            entity_type = entity_data['type']
            if entity_counts[entity_type] >= max_nodes // 4:  # Limit each type
                continue
                
            style = self.get_node_color_and_shape(entity_type)
            
            # Create hover info
            properties = entity_data['properties']
            title = f"<b>{entity_type.upper()}</b><br>"
            title += f"ID: {entity_id}<br>"
            
            if 'name' in properties:
                title += f"Name: {properties['name']}<br>"
            if 'industry' in properties:
                title += f"Industry: {properties['industry']}<br>"
            if 'funding_stage' in properties:
                title += f"Funding Stage: {properties['funding_stage']}<br>"
            if 'university' in properties:
                title += f"University: {properties['university']}<br>"
                
            net.add_node(
                entity_id,
                label=properties.get('name', entity_id)[:20],
                title=title,
                color=style['color'],
                shape=style['shape'],
                size=style['size'],
                font={'size': 12, 'color': 'white'}
            )
            
            entity_counts[entity_type] += 1
            added_nodes += 1
        
        # Add original relationships
        added_edges = 0
        for rel in self.relationships:
            if rel['source'] in [node['id'] for node in net.nodes] and \
               rel['target'] in [node['id'] for node in net.nodes]:
                
                edge_color = self.get_edge_color(rel['type'])
                
                net.add_edge(
                    rel['source'],
                    rel['target'],
                    label=rel['type'],
                    color=edge_color,
                    width=2,
                    title=f"Relationship: {rel['type']}"
                )
                added_edges += 1
        
        # Add similarity connections if requested
        if include_similarities:
            print(f"🔍 Calculating similarities...")
            similarities = self.calculate_startup_similarities(similarity_threshold)
            
            for sim in similarities[:20]:  # Limit similarity edges
                if sim['startup1'] in [node['id'] for node in net.nodes] and \
                   sim['startup2'] in [node['id'] for node in net.nodes]:
                    
                    net.add_edge(
                        sim['startup1'],
                        sim['startup2'],
                        label=f"Similar ({sim['similarity']:.2f})",
                        color='#FF9FF3',
                        width=1,
                        dashes=True,
                        title=f"Similarity: {sim['similarity']:.3f}<br>Shared technologies: {sim['shared_techs']}"
                    )
                    added_edges += 1
        
        # Add legend as HTML
        legend_html = """
        <div style="position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.8); 
                    color: white; padding: 15px; border-radius: 10px; font-family: Arial;">
            <h3>🌐 Knowledge Graph Legend</h3>
            <div style="margin: 5px 0;"><span style="color: #FF6B6B;">●</span> Startups</div>
            <div style="margin: 5px 0;"><span style="color: #4ECDC4;">▲</span> Founders</div>
            <div style="margin: 5px 0;"><span style="color: #45B7D1;">■</span> VCs</div>
            <div style="margin: 5px 0;"><span style="color: #96CEB4;">♦</span> Technologies</div>
            <div style="margin: 5px 0;"><span style="color: #FF9FF3;">--</span> Similarities</div>
            <br>
            <small>Total Nodes: {total_nodes} | Total Edges: {total_edges}</small>
        </div>
        """.format(total_nodes=added_nodes, total_edges=added_edges)
        
        # Save the visualization
        net.save_graph(output_file)
        
        # Add legend to the HTML file
        with open(output_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Insert legend before closing body tag
        html_content = html_content.replace('</body>', f'{legend_html}</body>')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Visualization saved as {output_file}")
        print(f"📊 Stats: {added_nodes} nodes, {added_edges} edges")
        
        return output_file
    
    def create_focused_visualization(self, focus_entity_type='startup', output_file='focused_graph.html'):
        """Create a focused visualization around specific entity type"""
        
        net = Network(height="800px", width="100%", bgcolor="#1a1a1a", font_color="white")
        
        # Get all entities of focus type
        focus_entities = [eid for eid, edata in self.entities.items() 
                         if edata['type'] == focus_entity_type]
        
        # Get their direct neighbors
        connected_entities = set(focus_entities)
        for rel in self.relationships:
            if rel['source'] in focus_entities:
                connected_entities.add(rel['target'])
            if rel['target'] in focus_entities:
                connected_entities.add(rel['source'])
        
        # Add nodes
        for entity_id in connected_entities:
            if entity_id in self.entities:
                entity_data = self.entities[entity_id]
                style = self.get_node_color_and_shape(entity_data['type'])
                
                # Highlight focus entities
                if entity_data['type'] == focus_entity_type:
                    style['size'] *= 1.5
                    style['color'] = '#FFD93D'  # Golden highlight
                
                net.add_node(
                    entity_id,
                    label=entity_data['properties'].get('name', entity_id)[:15],
                    color=style['color'],
                    shape=style['shape'],
                    size=style['size']
                )
        
        # Add edges
        for rel in self.relationships:
            if (rel['source'] in connected_entities and 
                rel['target'] in connected_entities):
                
                net.add_edge(
                    rel['source'],
                    rel['target'],
                    color=self.get_edge_color(rel['type']),
                    width=2
                )
        
        net.save_graph(output_file)
        print(f"✅ Focused visualization ({focus_entity_type}) saved as {output_file}")
        
        return output_file

    def create_top_connected_visualization(self, top_n=30, output_file='top_connected_graph.html'):
        """Create a fast visualization showing only the most connected entities"""
        
        # Calculate node degrees (connections)
        node_degrees = defaultdict(int)
        for rel in self.relationships:
            node_degrees[rel['source']] += 1
            node_degrees[rel['target']] += 1
        
        # Get top connected nodes by type
        top_nodes_by_type = defaultdict(list)
        for entity_id, degree in node_degrees.items():
            if entity_id in self.entities:
                entity_type = self.entities[entity_id]['type']
                top_nodes_by_type[entity_type].append((entity_id, degree))
        
        # Sort and limit each type
        selected_nodes = set()
        for entity_type, nodes_with_degree in top_nodes_by_type.items():
            sorted_nodes = sorted(nodes_with_degree, key=lambda x: x[1], reverse=True)
            # Take top 8 of each type
            for node_id, degree in sorted_nodes[:8]:
                selected_nodes.add(node_id)
        
        # Create network
        net = Network(
            height="700px", 
            width="100%", 
            bgcolor="#1a1a1a",
            font_color="white"
        )
        
        # Add selected nodes
        for entity_id in selected_nodes:
            entity_data = self.entities[entity_id]
            style = self.get_node_color_and_shape(entity_data['type'])
            
            # Size based on connections
            degree = node_degrees[entity_id]
            style['size'] = min(50, max(15, degree * 2))
            
            properties = entity_data['properties']
            title = f"<b>{entity_data['type'].upper()}</b><br>"
            title += f"Connections: {degree}<br>"
            if 'name' in properties:
                title += f"Name: {properties['name']}<br>"
            
            net.add_node(
                entity_id,
                label=properties.get('name', entity_id)[:15],
                title=title,
                color=style['color'],
                shape=style['shape'],
                size=style['size']
            )
        
        # Add edges between selected nodes only
        for rel in self.relationships:
            if rel['source'] in selected_nodes and rel['target'] in selected_nodes:
                net.add_edge(
                    rel['source'],
                    rel['target'],
                    color=self.get_edge_color(rel['type']),
                    width=2,
                    title=f"Relationship: {rel['type']}"
                )
        
        # Configure for faster rendering
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 50},
            "barnesHut": {
              "gravitationalConstant": -30000,
              "springConstant": 0.01,
              "springLength": 100
            }
          }
        }
        """)
        
        net.save_graph(output_file)
        print(f"✅ Top connected visualization saved as {output_file}")
        print(f"    Showing {len(selected_nodes)} most connected entities")
        
        return output_file

    def get_industry_color(self, industry):
        """Get color based on startup industry"""
        industry_colors = {
            'fintech': '#FF6B6B',      # Red
            'healthcare': '#4ECDC4',   # Teal
            'education': '#45B7D1',    # Blue
            'ecommerce': '#96CEB4',    # Green
            'enterprise': '#FECA57',   # Yellow
            'gaming': '#FF9FF3',       # Pink
            'social': '#54A0FF',       # Light Blue
            'travel': '#5F27CD',       # Purple
            'food': '#FF9F43',         # Orange
            'retail': '#10AC84',       # Dark Green
            'media': '#EE5A6F',        # Rose
            'automotive': '#C44569',   # Dark Pink
            'real estate': '#F8B500',  # Golden
            'sports': '#3C6382',       # Dark Blue
            'fashion': '#A55EEA'       # Lavender
        }
        
        if industry and industry.lower() in industry_colors:
            return industry_colors[industry.lower()]
        
        # Generate a color based on industry string hash if not in predefined
        if industry:
            hash_val = abs(hash(industry.lower())) % 360
            # Convert HSV to RGB for consistent bright colors
            import colorsys
            rgb = colorsys.hsv_to_rgb(hash_val/360, 0.7, 0.9)
            return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        
        return '#95A5A6'  # Default gray

    def get_similarity_edge_color(self, similarity):
        """Get edge color based on similarity strength"""
        if similarity >= 0.8:
            return '#FF1744'  # Strong red for very high similarity
        elif similarity >= 0.6:
            return '#FF5722'  # Orange-red for high similarity
        elif similarity >= 0.4:
            return '#FF9800'  # Orange for medium similarity
        elif similarity >= 0.3:
            return '#FFC107'  # Yellow for moderate similarity
        else:
            return '#4CAF50'  # Green for lower similarity

    def create_similarity_only_visualization(self, similarity_threshold=0.4, output_file='similarity_graph.html'):
        """Create a fast visualization showing only similarity connections"""
        
        # Calculate similarities
        similarities = self.calculate_startup_similarities(similarity_threshold)
        
        if not similarities:
            print(f"No similarities found above threshold {similarity_threshold}")
            return None
        
        # Get unique startups in similarities
        startup_nodes = set()
        for sim in similarities:
            startup_nodes.add(sim['startup1'])
            startup_nodes.add(sim['startup2'])
        
        # Create network
        net = Network(
            height="650px", 
            width="100%", 
            bgcolor="#1a1a1a",
            font_color="white"
        )
        
        # Collect industries for legend
        industries_used = set()
        
        # Add startup nodes with industry-based colors
        for startup_id in startup_nodes:
            if startup_id in self.entities:
                entity_data = self.entities[startup_id]
                properties = entity_data['properties']
                
                # Get startup's technologies for tooltip
                tech_count = sum(1 for rel in self.relationships 
                               if rel['source'] == startup_id and rel['type'] == 'USES_TECHNOLOGY')
                
                # Get industry and color
                industry = properties.get('industry', 'Unknown')
                industries_used.add(industry)
                node_color = self.get_industry_color(industry)
                
                # Size based on number of similarities
                similarity_count = sum(1 for sim in similarities 
                                     if sim['startup1'] == startup_id or sim['startup2'] == startup_id)
                node_size = max(20, min(40, 15 + similarity_count * 3))
                
                title = f"<b>STARTUP</b><br>"
                title += f"Name: {properties.get('name', startup_id)}<br>"
                title += f"Industry: {industry}<br>"
                title += f"Technologies: {tech_count}<br>"
                title += f"Similarities: {similarity_count}<br>"
                if 'funding_stage' in properties:
                    title += f"Stage: {properties['funding_stage']}<br>"
                
                net.add_node(
                    startup_id,
                    label=properties.get('name', startup_id)[:15],
                    title=title,
                    color=node_color,
                    shape='dot',
                    size=node_size,
                    borderWidth=2,
                    borderColor='white'
                )
        
        # Add similarity edges with strength-based colors
        for sim in similarities[:20]:  # Increased to top 20 similarities
            edge_color = self.get_similarity_edge_color(sim['similarity'])
            edge_width = max(1, sim['similarity'] * 6)
            
            # Make edge style based on similarity strength
            edge_style = "solid" if sim['similarity'] >= 0.5 else "dashed"
            
            net.add_edge(
                sim['startup1'],
                sim['startup2'],
                label=f"{sim['similarity']:.2f}",
                color=edge_color,
                width=edge_width,
                dashes=(edge_style == "dashed"),
                title=f"Similarity: {sim['similarity']:.3f}<br>Shared technologies: {sim['shared_techs']}<br>Strength: {'High' if sim['similarity'] >= 0.6 else 'Medium' if sim['similarity'] >= 0.4 else 'Moderate'}"
            )
        
        # Enhanced physics for better layout
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100},
            "forceAtlas2Based": {
              "gravitationalConstant": -80,
              "springConstant": 0.05,
              "springLength": 150,
              "damping": 0.4
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 200
          }
        }
        """)
        
        net.save_graph(output_file)
        
        # Add colorful legend to HTML
        industry_legend = ""
        for industry in sorted(industries_used):
            color = self.get_industry_color(industry)
            industry_legend += f'<div style="margin: 3px 0;"><span style="color: {color};">●</span> {industry.title()}</div>'
        
        legend_html = f"""
        <div style="position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.9); 
                    color: white; padding: 15px; border-radius: 10px; font-family: Arial; max-height: 400px; overflow-y: auto;">
            <h3>Startup Similarity Network</h3>
            <h4>Industries:</h4>
            {industry_legend}
            <br>
            <h4>Edge Colors (Similarity):</h4>
            <div style="margin: 3px 0;"><span style="color: #FF1744;">—</span> Very High (0.8+)</div>
            <div style="margin: 3px 0;"><span style="color: #FF5722;">—</span> High (0.6+)</div>
            <div style="margin: 3px 0;"><span style="color: #FF9800;">—</span> Medium (0.4+)</div>
            <div style="margin: 3px 0;"><span style="color: #FFC107;">—</span> Moderate (0.3+)</div>
            <div style="margin: 3px 0;"><span style="color: #4CAF50;">—</span> Lower</div>
            <br>
            <small>Nodes: {len(startup_nodes)} | Edges: {len(similarities[:20])}</small>
        </div>
        """
        
        # Add legend to HTML file
        with open(output_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        html_content = html_content.replace('</body>', f'{legend_html}</body>')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Colorful similarity visualization saved as {output_file}")
        print(f"    Showing {len(startup_nodes)} startups with {len(similarities[:20])} similarity connections")
        print(f"    Industries represented: {len(industries_used)}")
        
        return output_file

def main():
    """Main function"""
    print("🚀 Knowledge Graph Visualizer")
    print("=" * 50)
    
    try:
        # Initialize visualizer
        viz = KnowledgeGraphVisualizer('startup_knowledge_graph.json')
        
        # Show statistics
        stats = viz.get_entity_stats()
        print(f"📈 Entity Statistics:")
        for entity_type, count in stats.items():
            print(f"   • {entity_type.title()}: {count}")
        
        print("\nCreating visualizations...")
        
        # Create main visualization (reduced size for speed)
        main_file = viz.create_network_visualization(
            include_similarities=True,
            similarity_threshold=0.3,
            max_nodes=100,
            output_file='startup_knowledge_graph.html'
        )
        
        # Create fast top-connected entities visualization
        top_connected_file = viz.create_top_connected_visualization(
            output_file='top_connected_graph.html'
        )
        
        # Create similarity-only visualization
        similarity_file = viz.create_similarity_only_visualization(
            similarity_threshold=0.3,
            output_file='similarity_graph.html'
        )
        
        print(f"\nVisualizations created!")
        print(f"   • Main graph: {main_file}")
        print(f"   • Top connected: {top_connected_file}")
        print(f"   • Similarities only: {similarity_file}")
        print(f"\nOpen the HTML files in your browser to explore the interactive networks!")
        print(f"The top_connected and similarity graphs are much faster to load!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 