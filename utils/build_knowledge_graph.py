import pandas as pd
import json
import networkx as nx
from collections import defaultdict

# Load all data
startups = pd.read_csv('data/startup_ecosystem_startups.csv')
founders = pd.read_csv('data/startup_ecosystem_founders.csv')
investments = pd.read_csv('data/startup_ecosystem_investments.csv')
technologies = pd.read_csv('data/startup_ecosystem_technologies.csv')
vcs = pd.read_csv('data/startup_ecosystem_vcs.csv')
founder_startup = pd.read_csv('data/startup_ecosystem_founder_startup.csv')
startup_tech = pd.read_csv('data/startup_ecosystem_startup_tech.csv')

# Create knowledge graph
kg = {
    "entities": {},
    "relationships": []
}

print("Building Knowledge Graph...")

# Add Startups
for _, startup in startups.iterrows():
    kg["entities"][startup['id']] = {
        "type": "startup",
        "properties": startup.to_dict()
    }

# Add Founders
for _, founder in founders.iterrows():
    kg["entities"][founder['id']] = {
        "type": "founder",
        "properties": founder.to_dict()
    }

# Add VCs
for _, vc in vcs.iterrows():
    kg["entities"][vc['id']] = {
        "type": "vc",
        "properties": vc.to_dict()
    }

# Add Technologies
for _, tech in technologies.iterrows():
    kg["entities"][tech['id']] = {
        "type": "technology",
        "properties": tech.to_dict()
    }

# Add Founder-Startup relationships
for _, rel in founder_startup.iterrows():
    kg["relationships"].append({
        "source": rel['founder_id'],
        "target": rel['startup_id'],
        "type": "WORKS_AT",
        "properties": {
            "role": rel['role'],
            "equity_percentage": rel['equity_percentage'],
            "is_active": rel['is_active']
        }
    })

# Add Investment relationships
for _, inv in investments.iterrows():
    kg["relationships"].append({
        "source": inv['vc_id'],
        "target": inv['startup_id'],
        "type": "INVESTS_IN",
        "properties": {
            "round_type": inv['round_type'],
            "amount": inv['amount'],
            "date": inv['date'],
            "valuation": inv['valuation'],
            "lead_investor": inv['lead_investor']
        }
    })

# Add Startup-Technology relationships
for _, tech_rel in startup_tech.iterrows():
    kg["relationships"].append({
        "source": tech_rel['startup_id'],
        "target": tech_rel['technology_id'],
        "type": "USES_TECHNOLOGY",
        "properties": {
            "usage_intensity": tech_rel['usage_intensity'],
            "implementation_date": tech_rel['implementation_date']
        }
    })

print(f"Knowledge Graph created with:")
print(f"- {len(kg['entities'])} entities")
print(f"- {len(kg['relationships'])} relationships")

# Save as JSON
with open('startup_knowledge_graph.json', 'w') as f:
    json.dump(kg, f, indent=2, default=str)

print("Saved knowledge graph to 'startup_knowledge_graph.json'")

# Example: Show startup_79 relationships
startup_79_rels = [r for r in kg['relationships'] if r['source'] == 'startup_79' or r['target'] == 'startup_79']
print(f"\nStartup_79 has {len(startup_79_rels)} relationships:")
for rel in startup_79_rels[:5]:  # Show first 5
    print(f"  {rel['source']} --{rel['type']}--> {rel['target']}") 